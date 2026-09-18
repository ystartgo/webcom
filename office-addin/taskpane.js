/**
 * Webcom Office Add-in Taskpane Logic
 * 深度參考 Webcom index.html：具備離線韌性、全域函式直綁、對話雙向聯動、圖表自動繪製
 */

let chatHistory = [];
let isGenerating = false;

// 預設配置：連接 Webcom Daemon (支援 8002 / 8001) 或 LM Studio / OpenAI
const addinConfig = {
    apiEndpoint: localStorage.getItem('webcom_addin_endpoint') || (window.location.protocol.startsWith('http') ? (window.location.origin + '/v1/chat/completions') : 'https://127.0.0.1:8002/v1/chat/completions'),
    apiKey: localStorage.getItem('webcom_addin_key') || '',
    model: localStorage.getItem('webcom_addin_model') || 'auto',
    systemPrompt: `你是一個專業的微軟 Office 智慧協作助理 (Webcom for Office)。
你可以直接協助使用者讀取、分析、編修 Word 文件、Excel 試算表或 PowerPoint 簡報。
當使用者要求繪製圖表時，你可以回應標準 JSON 圖表定義 (包裹在 ```chart JSON 區塊內)，格式範例：
\`\`\`chart
{
  "type": "bar",
  "title": "2026 第一季營收統計",
  "categories": ["一月", "二月", "三月"],
  "series": [
    { "name": "實績", "data": [120, 200, 150] }
  ]
}
\`\`\`
回答請條理清晰、專業並隨時準備協助修改文件內容。`
};

// ── 1. 頁面初始化 (不阻塞、零依賴、全域函式隨時可用) ──
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Webcom Add-in] DOMContentLoaded fired. Initializing...');

    // 載入儲存的設定
    const epEl = document.getElementById('input-endpoint');
    const keyEl = document.getElementById('input-key');
    const modelEl = document.getElementById('input-model');
    if (epEl) epEl.value = addinConfig.apiEndpoint;
    if (keyEl) keyEl.value = addinConfig.apiKey;
    if (modelEl) modelEl.value = addinConfig.model;

    // 渲染 Lucide 圖示
    if (window.lucide && window.lucide.createIcons) {
        window.lucide.createIcons();
    }

    // 非同步初始化 Office.js 橋接器 (超時 1 秒自動降級至 Web 預覽，不卡介面)
    if (window.OfficeBridge && window.OfficeBridge.init) {
        window.OfficeBridge.init(updateHostBadge).then((res) => {
            updateHostBadge(res.host);
        }).catch(() => {
            updateHostBadge('Web 模式');
        });
    } else {
        updateHostBadge('Web 模式');
    }
});

function updateHostBadge(host) {
    const badge = document.getElementById('host-badge');
    if (!badge) return;
    if (host === 'Word') {
        badge.textContent = 'Word 模式';
        badge.className = 'px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-900/60 text-blue-300 border border-blue-700/60';
    } else if (host === 'Excel') {
        badge.textContent = 'Excel 模式';
        badge.className = 'px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-900/60 text-emerald-300 border border-emerald-700/60';
    } else if (host === 'PowerPoint') {
        badge.textContent = 'PPT 模式';
        badge.className = 'px-1.5 py-0.5 rounded text-[10px] font-bold bg-orange-900/60 text-orange-300 border border-orange-700/60';
    } else {
        badge.textContent = 'Web 模式';
        badge.className = 'px-1.5 py-0.5 rounded text-[10px] font-bold bg-gray-800 text-gray-300 border border-gray-700';
    }
}

// ── 2. 全域函式 (保證 HTML 中的 onclick 100% 隨點隨執行) ──

// 發送訊息
window.handleSendMessage = async function() {
    const input = document.getElementById('input-user-msg');
    if (!input) return;
    const text = input.value.trim();
    if (!text || isGenerating) return;

    input.value = '';
    appendMessage('user', text);
    chatHistory.push({ role: 'user', content: text, timestamp: new Date().toISOString() });

    isGenerating = true;
    const btnSend = document.getElementById('btn-send');
    if (btnSend) btnSend.disabled = true;

    // 建立 Assistant 占位訊息
    const aiBubble = appendMessage('assistant', '<span class="animate-pulse text-indigo-400 font-mono">正在分析與生成中...</span>');

    try {
        const msgs = [
            { role: 'system', content: addinConfig.systemPrompt },
            ...chatHistory.map(m => ({ role: m.role, content: m.content }))
        ];

        let endpoint = addinConfig.apiEndpoint;
        if (!endpoint.endsWith('/chat/completions')) {
            endpoint = endpoint.replace(/\/+$/, '') + '/chat/completions';
        }

        const headers = { 'Content-Type': 'application/json' };
        if (addinConfig.apiKey) {
            headers['Authorization'] = `Bearer ${addinConfig.apiKey}`;
        }

        const payload = {
            model: addinConfig.model || 'local-model',
            messages: msgs,
            temperature: 0.7,
            stream: false
        };

        const res = await fetch(endpoint, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${await res.text()}`);
        }

        const data = await res.json();
        const reply = data.choices?.[0]?.message?.content || '（無回應內容）';

        // 渲染 Markdown (相容無 marked 環境)
        aiBubble.innerHTML = window.marked ? window.marked.parse(reply) : escapeHtml(reply);
        chatHistory.push({ role: 'assistant', content: reply, timestamp: new Date().toISOString() });

        // 圖表解析與操作按鈕注入
        processChartDirectives(aiBubble, reply);
        attachInsertActions(aiBubble, reply);

    } catch (err) {
        console.error('[Addin Error]', err);
        aiBubble.innerHTML = `<span class="text-rose-400 font-bold">⚠️ 連線失敗:</span> ${err.message}<br><span class="text-[10px] text-gray-400 mt-1 block">提示：請確認 Webcom 常駐程式 (8002/8001) 正在執行中。</span>`;
    } finally {
        isGenerating = false;
        if (btnSend) btnSend.disabled = false;
        scrollToBottom();
        if (window.lucide && window.lucide.createIcons) window.lucide.createIcons();
    }
};

// 快捷注入提示詞
window.quickPrompt = function(promptText) {
    const input = document.getElementById('input-user-msg');
    if (!input) return;
    input.value = promptText;
    input.focus();
    showToast('已帶入快捷指令');
};

// 讀取當前選取內容
window.readDocumentSelection = async function() {
    const input = document.getElementById('input-user-msg');
    if (!input) return;
    if (window.OfficeBridge && window.OfficeBridge.getSelectedContent) {
        const text = await window.OfficeBridge.getSelectedContent();
        if (text) {
            input.value = `【以下為我選取的文件內容】：\n${text}\n\n請幫我分析並潤飾這段內容。`;
            input.focus();
            showToast('已成功帶入選取內容！');
        } else {
            showToast('目前未選取任何內容', true);
        }
    } else {
        input.value = `請幫我分析這段文字...`;
        input.focus();
        showToast('已啟動分析提示');
    }
};

// 開關設定面板
window.toggleSettingsPanel = function() {
    const panel = document.getElementById('settings-panel');
    if (!panel) return;
    panel.classList.toggle('hidden');
};

// 儲存設定
window.saveSettings = function() {
    const ep = document.getElementById('input-endpoint')?.value.trim();
    const key = document.getElementById('input-key')?.value.trim();
    const model = document.getElementById('input-model')?.value.trim();

    if (ep) {
        addinConfig.apiEndpoint = ep;
        localStorage.setItem('webcom_addin_endpoint', ep);
    }
    addinConfig.apiKey = key || '';
    localStorage.setItem('webcom_addin_key', addinConfig.apiKey);
    addinConfig.model = model || 'auto';
    localStorage.setItem('webcom_addin_model', addinConfig.model);

    document.getElementById('settings-panel')?.classList.add('hidden');
    showToast('設定已儲存！');
};

// 清空對話紀錄
window.clearChatHistory = function() {
    chatHistory = [];
    const container = document.getElementById('chat-container');
    if (container) {
        container.innerHTML = `
            <div id="welcome-card" class="p-3.5 bg-gray-900/60 border border-gray-800/80 rounded-2xl space-y-2 text-center text-xs text-gray-400 py-6">
                <span>💬 對話已清空，請隨時在下方輸入新的指令。</span>
            </div>
        `;
    }
    showToast('對話紀錄已清空');
};

// 匯出對話紀錄 (完全相容 Webcom 主介面 chat_history_*.json)
window.exportChatForWebcom = function() {
    if (chatHistory.length === 0) {
        showToast('目前無對話紀錄可匯出', true);
        return;
    }

    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const timestamp = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;

    const exportData = {
        app: "Webcom Dual-Engine Console",
        source: "Webcom Office Add-in",
        version: "1.0.10",
        exportTimestamp: now.toISOString(),
        engineMode: "api",
        totalMessages: chatHistory.length,
        messages: chatHistory.map(m => ({
            role: m.role,
            content: m.content,
            timestamp: m.timestamp || new Date().toISOString()
        }))
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json;charset=utf-8' });
    const fileName = `chat_history_office_${timestamp}.json`;
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(a.href);
    }, 1500);

    showToast(`📁 已匯出對話紀錄 [${fileName}]！`);
};

// 觸發匯入對話紀錄
window.triggerChatImport = function() {
    document.getElementById('file-import-chat')?.click();
};

window.handleChatFileSelected = function(e) {
    if (e.target.files && e.target.files[0]) {
        const file = e.target.files[0];
        const reader = new FileReader();
        reader.onload = (evt) => {
            try {
                const data = JSON.parse(evt.target.result);
                let msgs = [];
                if (Array.isArray(data)) msgs = data;
                else if (Array.isArray(data.messages)) msgs = data.messages;

                if (msgs.length === 0) throw new Error('檔案內無訊息');

                const container = document.getElementById('chat-container');
                if (container) container.innerHTML = '';
                chatHistory = [];

                msgs.forEach(m => {
                    const role = m.role || 'user';
                    const content = m.content || '';
                    if (content) {
                        chatHistory.push({ role, content, timestamp: m.timestamp || new Date().toISOString() });
                        appendMessage(role, window.marked ? window.marked.parse(content) : escapeHtml(content));
                    }
                });

                showToast(`✅ 成功匯入 ${msgs.length} 則對話！`);
            } catch (err) {
                showToast('❌ 匯入失敗: ' + err.message, true);
            }
        };
        reader.readAsText(file);
        e.target.value = '';
    }
};

// ── 輔助渲染函式 ──
function appendMessage(role, contentHtml) {
    const container = document.getElementById('chat-container');
    if (!container) return null;

    // 移除初始歡迎卡片
    const welcome = document.getElementById('welcome-card');
    if (welcome) welcome.remove();

    const wrap = document.createElement('div');
    wrap.className = `flex flex-col gap-1.5 p-3 rounded-2xl text-xs leading-relaxed transition-all ${
        role === 'user'
            ? 'bg-gradient-to-r from-purple-950/40 to-indigo-950/40 border border-purple-800/40 ml-5 text-purple-100 shadow-sm'
            : 'bg-gray-900/80 border border-gray-800 mr-5 text-gray-100 shadow-sm'
    }`;

    const meta = document.createElement('div');
    meta.className = 'flex items-center justify-between text-[10px] text-gray-400 font-bold';
    meta.innerHTML = `<span>${role === 'user' ? '👤 閣下' : '🤖 Webcom AI'}</span><span>${new Date().toLocaleTimeString()}</span>`;

    const body = document.createElement('div');
    body.className = 'prose prose-invert prose-sm max-w-none break-words leading-relaxed';
    body.innerHTML = contentHtml;

    wrap.appendChild(meta);
    wrap.appendChild(body);
    container.appendChild(wrap);
    scrollToBottom();
    return body;
}

function processChartDirectives(containerEl, replyText) {
    const chartRegex = /```chart\s*([\s\S]*?)\s*```/g;
    let match;
    while ((match = chartRegex.exec(replyText)) !== null) {
        try {
            const chartConfig = JSON.parse(match[1]);
            const chartBox = document.createElement('div');
            chartBox.className = 'mt-2.5 p-2.5 bg-gray-950/90 border border-cyan-800/50 rounded-xl shadow-md';
            
            const chartHeader = document.createElement('div');
            chartHeader.className = 'flex items-center justify-between text-xs font-bold text-cyan-300 mb-2';
            chartHeader.innerHTML = `<span>📊 ${chartConfig.title || 'AI 自動生成圖表'}</span>`;
            
            const btnInsert = document.createElement('button');
            btnInsert.className = 'px-2 py-0.5 rounded-lg text-[10px] bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition cursor-pointer active:scale-95 shadow-sm';
            btnInsert.textContent = '📥 插入圖表至文件';
            chartHeader.appendChild(btnInsert);

            const canvasWrap = document.createElement('div');
            canvasWrap.style.width = '100%';
            canvasWrap.style.height = '180px';

            chartBox.appendChild(chartHeader);
            chartBox.appendChild(canvasWrap);
            containerEl.appendChild(chartBox);

            // 若需 echarts 則動態載入
            ensureECharts().then((echarts) => {
                const myChart = echarts.init(canvasWrap, 'dark', { backgroundColor: '#0b0f19' });
                const option = {
                    title: { text: chartConfig.title || '', textStyle: { color: '#f3f4f6', fontSize: 11 } },
                    tooltip: {},
                    grid: { top: 30, bottom: 25, left: 35, right: 15 },
                    xAxis: {
                        type: 'category',
                        data: chartConfig.categories || [],
                        axisLine: { lineStyle: { color: '#64748b' } },
                        axisLabel: { color: '#94a3b8', fontSize: 9 }
                    },
                    yAxis: {
                        type: 'value',
                        axisLine: { lineStyle: { color: '#64748b' } },
                        splitLine: { lineStyle: { color: '#1e293b' } },
                        axisLabel: { color: '#94a3b8', fontSize: 9 }
                    },
                    series: (chartConfig.series || []).map(s => ({
                        ...s,
                        type: chartConfig.type || 'bar',
                        itemStyle: { color: '#6366f1' }
                    }))
                };
                myChart.setOption(option);

                btnInsert.addEventListener('click', async () => {
                    const base64 = myChart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#0b0f19' });
                    if (window.OfficeBridge && window.OfficeBridge.insertImageBase64) {
                        const res = await window.OfficeBridge.insertImageBase64(base64);
                        if (res.success) showToast('✅ 圖表已成功插入當前文件！');
                        else showToast('❌ 插入失敗: ' + (res.error || ''), true);
                    }
                });
            }).catch(() => {
                canvasWrap.innerHTML = `<div class="p-3 text-[10px] text-gray-400">（圖表繪製組件於此環境略過）</div>`;
            });

        } catch (e) {
            console.warn('[Chart Parse Error]', e);
        }
    }
}

function ensureECharts() {
    return new Promise((resolve, reject) => {
        if (window.echarts) return resolve(window.echarts);
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js';
        script.onload = () => resolve(window.echarts);
        script.onerror = () => reject(new Error('ECharts load failed'));
        document.head.appendChild(script);
    });
}

function attachInsertActions(bubbleEl, rawText) {
    const actionRow = document.createElement('div');
    actionRow.className = 'flex items-center gap-1.5 mt-2.5 pt-2 border-t border-gray-800/80 text-[10px] select-none';

    const btnInsertAfter = document.createElement('button');
    btnInsertAfter.className = 'px-2 py-1 rounded-lg bg-gray-800/90 hover:bg-gray-700 text-indigo-300 font-bold border border-indigo-700/50 flex items-center gap-1 cursor-pointer active:scale-95 transition';
    btnInsertAfter.innerHTML = `<span>📥 寫入游標處</span>`;
    btnInsertAfter.addEventListener('click', async () => {
        const clean = rawText.replace(/```[\s\S]*?```/g, '').trim() || rawText;
        if (window.OfficeBridge && window.OfficeBridge.insertText) {
            const res = await window.OfficeBridge.insertText(clean, { replace: false });
            if (res.success) showToast('已成功寫入文件！');
            else showToast('寫入失敗: ' + (res.error || ''), true);
        }
    });

    const btnReplace = document.createElement('button');
    btnReplace.className = 'px-2 py-1 rounded-lg bg-gray-800/90 hover:bg-gray-700 text-amber-300 font-bold border border-amber-700/50 flex items-center gap-1 cursor-pointer active:scale-95 transition';
    btnReplace.innerHTML = `<span>🔄 取代選取</span>`;
    btnReplace.addEventListener('click', async () => {
        const clean = rawText.replace(/```[\s\S]*?```/g, '').trim() || rawText;
        if (window.OfficeBridge && window.OfficeBridge.insertText) {
            const res = await window.OfficeBridge.insertText(clean, { replace: true });
            if (res.success) showToast('已成功取代選取文字！');
            else showToast('取代失敗: ' + (res.error || ''), true);
        }
    });

    actionRow.appendChild(btnInsertAfter);
    actionRow.appendChild(btnReplace);
    bubbleEl.appendChild(actionRow);
}

function scrollToBottom() {
    const container = document.getElementById('chat-container');
    if (container) container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.showToast = function(msg, isError = false) {
    const existing = document.getElementById('addin-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'addin-toast';
    toast.className = `fixed bottom-14 left-1/2 -translate-x-1/2 px-3 py-1.5 rounded-xl text-xs font-bold shadow-2xl z-50 transition-all transform duration-200 pointer-events-none ${
        isError ? 'bg-rose-900/90 text-rose-200 border border-rose-700' : 'bg-indigo-900/90 text-indigo-200 border border-indigo-700'
    }`;
    toast.textContent = msg;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 2200);
};
