/**
 * Pyodide Web Worker - 獨立線程 Python 執行器
 * 負責在背景 Web Worker 中加載 Pyodide 並執行 Python 程式碼，捕獲 stdout/stderr，避免阻塞主線程 UI
 */

let pyodide = null;
let isInitializing = false;

async function initPyodide(indexURL) {
    if (pyodide) return pyodide;
    if (isInitializing) {
        while (isInitializing) {
            await new Promise(r => setTimeout(r, 50));
        }
        return pyodide;
    }

    isInitializing = true;
    try {
        const pyodideBase = indexURL || 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/';
        importScripts(pyodideBase + 'pyodide.js');
        pyodide = await loadPyodide({
            indexURL: pyodideBase
        });
        isInitializing = false;
        return pyodide;
    } catch (err) {
        isInitializing = false;
        throw err;
    }
}

self.onmessage = async (e) => {
    const { id, action, code, indexURL, packages } = e.data || {};

    if (action === 'init') {
        try {
            await initPyodide(indexURL);
            self.postMessage({ id, status: 'ready', message: 'Pyodide initialized successfully.' });
        } catch (err) {
            self.postMessage({ id, status: 'error', error: err.message || String(err) });
        }
        return;
    }

    if (action === 'loadPackage') {
        try {
            const py = await initPyodide(indexURL);
            if (packages && packages.length > 0) {
                await py.loadPackage(packages);
            }
            self.postMessage({ id, status: 'success', message: 'Packages loaded successfully.' });
        } catch (err) {
            self.postMessage({ id, status: 'error', error: err.message || String(err) });
        }
        return;
    }

    if (action === 'run') {
        try {
            const py = await initPyodide(indexURL);
            let stdoutChunks = [];
            let stderrChunks = [];

            py.setStdout({
                batched: (str) => {
                    stdoutChunks.push(str);
                    self.postMessage({ id, type: 'stdout', chunk: str });
                }
            });

            py.setStderr({
                batched: (str) => {
                    stderrChunks.push(str);
                    self.postMessage({ id, type: 'stderr', chunk: str });
                }
            });

            const startTime = performance.now();
            const result = await py.runPythonAsync(code);
            const duration = Math.round(performance.now() - startTime);

            self.postMessage({
                id,
                status: 'success',
                returncode: 0,
                stdout: stdoutChunks.join('\n'),
                stderr: stderrChunks.join('\n'),
                result: result !== undefined ? String(result) : null,
                duration
            });
        } catch (err) {
            self.postMessage({
                id,
                status: 'error',
                returncode: 1,
                error: err.message || String(err),
                stderr: err.message || String(err)
            });
        }
    }
};
