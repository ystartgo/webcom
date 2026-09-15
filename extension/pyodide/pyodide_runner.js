/**
 * Webcom Pyodide Runner Module
 * 提供高階、Promise 架構的瀏覽器端 WebAssembly Python 執行介面
 * 支援主線程直接執行或 Web Worker 非阻塞背景執行
 */

(function(root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.WebcomPyodide = factory();
    }
}(typeof self !== 'undefined' ? self : this, function() {

    const DEFAULT_CDN_URL = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/';
    let workerInstance = null;
    let pendingRequests = new Map();
    let requestIdCounter = 1;
    let localPyodideInstance = null;
    let localPyodidePromise = null;

    /**
     * 偵測當前執行環境是否為 Chrome 擴充功能
     */
    function isChromeExtension() {
        return typeof chrome !== 'undefined' && chrome.runtime && !!chrome.runtime.id;
    }

    /**
     * 取得最佳 Pyodide IndexURL (優先本機/擴充功能內部路徑，次選 CDN)
     */
    function getPyodideIndexURL(customUrl) {
        if (customUrl) return customUrl;
        if (isChromeExtension()) {
            try {
                return chrome.runtime.getURL('pyodide/dist/');
            } catch (e) { }
        }
        return DEFAULT_CDN_URL;
    }

    /**
     * 取得或建立 Web Worker 實例
     */
    function getWorker(customUrl) {
        if (workerInstance) return workerInstance;

        let workerPath = 'pyodide/pyodide.worker.js';
        if (isChromeExtension()) {
            try { workerPath = chrome.runtime.getURL('pyodide/pyodide.worker.js'); } catch (e) { }
        }

        workerInstance = new Worker(workerPath);
        workerInstance.onmessage = (e) => {
            const data = e.data || {};
            const req = pendingRequests.get(data.id);
            if (!req) return;

            if (data.type === 'stdout' && typeof req.onStdout === 'function') {
                req.onStdout(data.chunk);
                return;
            }
            if (data.type === 'stderr' && typeof req.onStderr === 'function') {
                req.onStderr(data.chunk);
                return;
            }

            if (data.status === 'success' || data.status === 'ready') {
                pendingRequests.delete(data.id);
                req.resolve(data);
            } else if (data.status === 'error') {
                pendingRequests.delete(data.id);
                req.reject(new Error(data.error || 'Pyodide execution failed'));
            }
        };

        workerInstance.onerror = (err) => {
            console.error('[WebcomPyodide Worker Error]', err);
        };

        return workerInstance;
    }

    /**
     * 主線程 Pyodide 初始化 (Fallback 當 Web Worker 不可用時)
     */
    async function getDirectPyodide(indexURL) {
        if (localPyodideInstance) return localPyodideInstance;
        if (localPyodidePromise) return localPyodidePromise;

        const base = indexURL || getPyodideIndexURL();
        localPyodidePromise = (async () => {
            if (!window.loadPyodide) {
                await new Promise((resolve, reject) => {
                    const s = document.createElement('script');
                    s.src = base.endsWith('/') ? base + 'pyodide.js' : base + '/pyodide.js';
                    s.onload = resolve;
                    s.onerror = () => reject(new Error('無法載入 Pyodide 核心腳本: ' + s.src));
                    document.head.appendChild(s);
                });
            }
            localPyodideInstance = await window.loadPyodide({ indexURL: base });
            return localPyodideInstance;
        })();

        return localPyodidePromise;
    }

    /**
     * 執行 Python 程式碼
     * @param {string} code - Python 程式碼
     * @param {object} options - 執行選項 { useWorker, onStdout, onStderr, indexURL }
     */
    async function runPython(code, options = {}) {
        const useWorker = options.useWorker !== false; // 預設使用 Worker 避免卡頓
        const indexURL = getPyodideIndexURL(options.indexURL);

        if (useWorker && typeof Worker !== 'undefined') {
            try {
                const worker = getWorker(indexURL);
                const id = 'py_' + (++requestIdCounter);
                return await new Promise((resolve, reject) => {
                    pendingRequests.set(id, {
                        resolve,
                        reject,
                        onStdout: options.onStdout,
                        onStderr: options.onStderr
                    });
                    worker.postMessage({ id, action: 'run', code, indexURL });
                });
            } catch (workerErr) {
                console.warn('[WebcomPyodide] Worker execution failed, falling back to direct thread:', workerErr);
            }
        }

        // 直接在主線程執行
        const py = await getDirectPyodide(indexURL);
        let stdoutChunks = [];
        let stderrChunks = [];

        py.setStdout({
            batched: (msg) => {
                stdoutChunks.push(msg);
                if (typeof options.onStdout === 'function') options.onStdout(msg);
            }
        });
        py.setStderr({
            batched: (msg) => {
                stderrChunks.push(msg);
                if (typeof options.onStderr === 'function') options.onStderr(msg);
            }
        });

        const startTime = performance.now();
        try {
            const result = await py.runPythonAsync(code);
            const duration = Math.round(performance.now() - startTime);
            return {
                status: 'success',
                returncode: 0,
                stdout: stdoutChunks.join('\n'),
                stderr: stderrChunks.join('\n'),
                result: result !== undefined ? String(result) : null,
                duration,
                engine: 'pyodide'
            };
        } catch (err) {
            return {
                status: 'error',
                returncode: 1,
                stdout: stdoutChunks.join('\n'),
                stderr: (stderrChunks.length > 0 ? stderrChunks.join('\n') + '\n' : '') + (err.message || String(err)),
                error: err.message || String(err),
                engine: 'pyodide'
            };
        }
    }

    return {
        version: '1.0.0',
        runPython,
        getPyodideIndexURL,
        isChromeExtension
    };
}));
