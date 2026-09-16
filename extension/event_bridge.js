/**
 * Webcom Extension Event Bridge (Chrome Extension MV3 CSP 規範合規事件橋接器)
 * 解決 Chrome 擴充功能禁止 HTML 行內 onclick 等事件處理器的問題
 * 將 [data-on-click] 等宣告式標籤以嚴格、無 eval 的安全方式轉化為動態事件委派
 */

(function() {
    function executeActionString(expr, element, event) {
        if (!expr) return;
        // 分割多個陳述式 (以分號分割)
        const statements = expr.split(';').map(s => s.trim()).filter(Boolean);
        for (const stmt of statements) {
            // 1. 支援 document.getElementById('...')?.click() 模式
            const docClickMatch = stmt.match(/^document\.getElementById\(['"]([^'"]+)['"]\)(?:\?)?\.click\(\)$/);
            if (docClickMatch) {
                const el = document.getElementById(docClickMatch[1]);
                if (el) {
                    try { el.click(); } catch(err) { console.error('[EventBridge] Element click error:', err); }
                }
                continue;
            }

            // 2. 匹配函式呼叫格式：fnName(arg1, arg2...) 或 window.fnName(...)
            const match = stmt.match(/^([a-zA-Z0-9_$.]+)(?:\((.*)\))?$/);
            if (!match) continue;

            const fnPath = match[1];
            const rawArgsStr = match[2];

            // 解析函式對象 (支援 window.xxx 或頂層函式)
            let targetFn = window;
            const parts = fnPath.replace(/^window\./, '').split('.');
            for (const p of parts) {
                if (targetFn && targetFn[p] !== undefined) {
                    targetFn = targetFn[p];
                } else {
                    targetFn = null;
                    break;
                }
            }

            if (typeof targetFn !== 'function') {
                console.warn('[EventBridge] Function not found on window:', fnPath);
                continue;
            }

            let args = [];
            if (rawArgsStr !== undefined && rawArgsStr.trim() !== '') {
                // 解析簡易參數
                args = rawArgsStr.split(',').map(a => {
                    a = a.trim();
                    if (a === 'event') return event;
                    if (a === 'this') return element;
                    if (a === 'true') return true;
                    if (a === 'false') return false;
                    if (a === 'null') return null;
                    if (!isNaN(a) && a !== '') return Number(a);
                    if ((a.startsWith("'") && a.endsWith("'")) || (a.startsWith('"') && a.endsWith('"'))) {
                        return a.slice(1, -1);
                    }
                    return a;
                });
            }

            try {
                targetFn.apply(element, args);
            } catch (err) {
                console.error(`[EventBridge] Error executing ${fnPath}:`, err);
            }
        }
    }

    // 全域事件委派 (同時相容 data-on-click 與動態渲染之 onclick)
    document.addEventListener('click', function(e) {
        const target = e.target.closest('[data-on-click], [onclick]');
        if (target) {
            const expr = target.getAttribute('data-on-click') || target.getAttribute('onclick');
            if (expr) {
                executeActionString(expr, target, e);
            }
        }
    }, true);

    document.addEventListener('input', function(e) {
        const target = e.target.closest('[data-on-input]');
        if (target) {
            const expr = target.getAttribute('data-on-input');
            executeActionString(expr, target, e);
        }
    }, true);

    document.addEventListener('keydown', function(e) {
        const target = e.target.closest('[data-on-keydown]');
        if (target) {
            const expr = target.getAttribute('data-on-keydown');
            executeActionString(expr, target, e);
        }
    }, true);

    document.addEventListener('change', function(e) {
        const target = e.target.closest('[data-on-change]');
        if (target) {
            const expr = target.getAttribute('data-on-change');
            executeActionString(expr, target, e);
        }
    }, true);

    console.log('[EventBridge] Chrome Extension CSP safe event bridge initialized.');
})();
