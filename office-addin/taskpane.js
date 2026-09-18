/**
 * Webcom Office Add-in Taskpane Logic
 * 負責內嵌對話、模型調度、圖表自動繪製、與 Webcom 對話紀錄雙向聯動
 */

let chatHistory = [];
let isGenerating = false;

// 預設配置：可連接 Webcom Daemon 或本機 LM Studio 或遠端 OpenAI
const addinConfig = {
    apiEndpoint: localStorage.getItem('webcom_addin_endpoint') || 'http://127.0.0.1:8001/v1/chat/completions',
    apiKey: localStorage.getItem('webcom_addin_key') || '',
    model: localStorage.getItem('webcom_addin_model') || 'auto',
    systemPrompt: `你是一個專業的微軟 Office 智慧協作助理 (Webcom for Office)。
你可以直接協助使用者讀取、分析、編修 Word 文件、Excel 試算表或 PowerPoint 簡報。
當使用者要求繪製圖表時，你可以：
1. 回應標準 JSON 圖表定義 (包裹在 ```chart JSON 區塊內)，格式範例：
\`\`\`chart
{
  "type": "bar", // bar, line, pie
  "title": "2026 第一季營收統計",
  "categories": ["一月", "二月", "三月"],
  "series": [
    { "name": "實績", "data": [120, 200, 150] }
  ]
}
\`\`\`
2. 若在 Excel 環境，亦可提供直接寫入儲存格的指引與矩陣資料。
回答請條理清晰、專業並隨時準備協助修改文件內容。`
};

document.addEventListener('DOMContentLoaded', async () => {
    // 1. 初始化微軟 Office.js 橋接器
    const initRes = await window.OfficeBridge.init();
    updateHostBadge(initRes.host);

    // 2. 綁定按鈕事件
    setupEventListeners();

    // 3. 載入儲存的 API 設定
    document.getElementById('input-endpoint').value = addinConfig.apiEndpoint;
    document.getElementById('input-key').value = addinConfig.apiKey;
    document.getElementById('input-model').value = addinConfig.model;
});

function updateHostBadge(host) {
    const badge = document.getElementById('host-badge');
    if (!badge) return;
    badge.textContent = host;
    if (host === 'Word') {
        badge.className = 'px-2 py-0.5 rounded text-[10px] font-bold bg-blue-900/60 text-blue-300 border border-blue-700/60';
    } else if (host === 'Excel') {
        badge.className = 'px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-900/60 text-emerald-300 border border-emerald-700/60';
    } else if (host === 'PowerPoint') {
        badge.className = 'px-2 py-0.5 rounded text-[10px] font-bold bg-orange-900/60 text-orange-300 border border-orange-700/60';
    } else {
        badge.className = 'px-2 py-0.5 rounded text-[10px] font-bold bg-gray-800 text-gray-400 border border-gray-700';
    }
}

function setupEventListeners() {
    // 送出訊息
    const btnSend = document.getElementById('btn-send');
    const inputMsg = document.getElementById('input-user-msg');
    btnSend.addEventListener('click', handleSendMessage);
    inputMsg.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // 快捷鍵：讀取文件選取內容注入對話框
    document.getElementById('btn-read-selection')?.addEventListener('click', async () => {
        const text = await window.OfficeBridge.getSelectedContent();
        if (text) {
            inputMsg.value = `【以下為我選取的文件內容】：\n${text}\n\n請幫我分析並潤飾這段內容。`;
            inputMsg.focus();
            showToast('已成功帶入選取內容！');
        } else {
            showToast('目前未選取任何內容', true);
        }
    });

    // 對話紀錄聯動：匯出 (.json) 完全相容 Webcom
    document.getElementById('btn-export-chat')?.addEventListener('click', exportChatForWebcom);

    // 對話紀錄聯動：匯入 (.json)
    const fileImport = document.getElementById('file-import-chat');
    document.getElementById('btn-import-chat')?.addEventListener('click', () => {
        fileImport?.click();
    });
    fileImport?.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            importChatFromWebcom(e.target.files[0]);
            e.target.value = '';
        }
    });

    // 清空對話
    document.getElementById('btn-clear-chat')?.addEventListener('click', () => {
        chatHistory = [];
        document.getElementById('chat-container').innerHTML = '';
        showToast('對話已清空');
    });

    // 設定摺疊面板
    document.getElementById('btn-toggle-settings')?.addEventListener('click', () => {
        const panel = document.getElementById('settings-panel');
        panel.classList.toggle('hidden');
    });
    document.getElementById('btn-save-settings')?.addEventListener('click', () => {
        addinConfig.apiEndpoint = document.getElementById('input-endpoint').value.trim();
        addinConfig.apiKey = document.getElementById('input-key').value.trim();
        addinConfig.model = document.getElementById('input-model').value.trim();
        localStorage.setItem('webcom_addin_endpoint', addinConfig.apiEndpoint);
        localStorage.setItem('webcom_addin_key', addinConfig.apiKey);
        localStorage.setItem('webcom_addin_model', addinConfig.model);
        document.getElementById('settings-panel').classList.add('hidden');
        showToast('設定已儲存');
    });
}

// ── 訊息處理與 LLM 串流/回應 ──
async function handleSendMessage() {
    const input = document.getElementById('input-user-msg');
    const text = input.value.trim();
    if (!text || isGenerating) return;

    input.value = '';
    appendMessage('user', text);
    chatHistory.push({ role: 'user', content: text, timestamp: new Date().toISOString() });

    isGenerating = true;
    document.getElementById('btn-send').disabled = true;

    // 建立 Assistant 占位氣泡
    const aiBubble = appendMessage('assistant', '<span class="animate-pulse text-indigo-400">正在思考與生成中...</span>');

    try {
        const msgs = [
            { role: 'system', content: addinConfig.systemPrompt },
            ...chatHistory.map(m => ({ role: m.role, content: m.content }))
        ];

        let endpoint = addinConfig.apiEndpoint;
        // 若輸入的是 base URL 則自動補上 /chat/completions
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
        const reply = data.choices?.[0]?.message?.content || '（無回應）';

        // 渲染 Markdown
        aiBubble.innerHTML = window.marked ? window.marked.parse(reply) : reply;
        chatHistory.push({ role: 'assistant', content: reply, timestamp: new Date().toISOString() });

        // 檢查是否含有圖表指令 (Chart parsing)
        processChartDirectives(aiBubble, reply);

        // 注入「插入到文件」快捷按鈕
        attachInsertActions(aiBubble, reply);

    } catch (err) {
        console.error('[Addin Send Error]', err);
        aiBubble.innerHTML = `<span class="text-rose-400 font-bold">⚠️ 連線失敗:</span> ${err.message}<br><span class="text-xs text-gray-400 mt-1 block">提示：請確認 Webcom Daemon (8001) 或 LM Studio 是否正在運作。</span>`;
    } finally {
        isGenerating = false;
        document.getElementById('btn-send').disabled = false;
        scrollToBottom();
    }
}

function appendMessage(role, contentHtml) {
    const container = document.getElementById('chat-container');
    const wrap = document.createElement('div');
    wrap.className = `flex flex-col gap-1.5 p-3 rounded-xl text-xs leading-relaxed ${role === 'user' ? 'msg-user ml-4' : 'msg-assistant mr-4'}`;
    
    const meta = document.createElement('div');
    meta.className = 'flex items-center justify-between text-[10px] text-gray-400 font-bold';
    meta.innerHTML = `<span>${role === 'user' ? '👤 閣下' : '🤖 Webcom AI'}</span><span>${new Date().toLocaleTimeString()}</span>`;

    const body = document.createElement('div');
    body.className = 'prose prose-invert prose-sm max-w-none break-words';
    body.innerHTML = contentHtml;

    wrap.appendChild(meta);
    wrap.appendChild(body);
    container.appendChild(wrap);
    scrollToBottom();
    return body;
}

// ── 圖表自動繪製引擎 (ECharts 集成) ──
function processChartDirectives(containerEl, replyText) {
    const chartRegex = /```chart\s*([\s\S]*?)\s*```/g;
    let match;
    while ((match = chartRegex.exec(replyText)) !== null) {
        try {
            const chartConfig = JSON.parse(match[1]);
            const chartBox = document.createElement('div');
            chartBox.className = 'chart-card mt-2.5';
            
            const chartHeader = document.createElement('div');
            chartHeader.className = 'flex items-center justify-between text-xs font-bold text-cyan-300 mb-2';
            chartHeader.innerHTML = `<span>📊 ${chartConfig.title || 'AI 自動生成圖表'}</span>`;
            
            const btnInsert = document.createElement('button');
            btnInsert.className = 'px-2 py-0.5 rounded text-[10px] bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition';
            btnInsert.textContent = '📥 插入圖表至文件';
            chartHeader.appendChild(btnInsert);

            const canvasWrap = document.createElement('div');
            canvasWrap.style.width = '100%';
            canvasWrap.style.height = '200px';

            chartBox.appendChild(chartHeader);
            chartBox.appendChild(canvasWrap);
            containerEl.appendChild(chartBox);

            // 初始化 ECharts
            if (window.echarts) {
                const myChart = echarts.init(canvasWrap, 'dark', { backgroundColor: '#0f172a' });
                const option = {
                    title: { text: chartConfig.title || '', textStyle: { color: '#f3f4f6', fontSize: 12 } },
                    tooltip: {},
                    grid: { top: 35, bottom: 25, left: 35, right: 15 },
                    xAxis: {
                        type: 'category',
                        data: chartConfig.categories || [],
                        axisLine: { lineStyle: { color: '#64748b' } },
                        axisLabel: { color: '#94a3b8', fontSize: 10 }
                    },
                    yAxis: {
                        type: 'value',
                        axisLine: { lineStyle: { color: '#64748b' } },
                        splitLine: { lineStyle: { color: '#1e293b' } },
                        axisLabel: { color: '#94a3b8', fontSize: 10 }
                    },
                    series: (chartConfig.series || []).map(s => ({
                        name: s.name,
                        type: chartConfig.type || 'bar',
                        data: s.data,
                        itemStyle: { color: '#6366f1' }
                    }))
                };
                myChart.setOption(option);

                // 綁定一鍵寫入 Office 文件
                btnInsert.addEventListener('click', async () => {
                    const base64 = myChart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#0f172a' });
                    const res = await window.OfficeBridge.insertImageBase64(base64);
                    if (res.success) {
                        showToast('✅ 已成功將圖表插入當前文件！');
                    } else {
                        showToast('❌ 插入失敗: ' + (res.error || '未知錯誤'), true);
                    }
                });
            }
        } catch (e) {
            console.warn('[Chart Parse Error]', e);
        }
    }
}

// ── 輔助操作：一鍵插入純文字 / 取代選取 ──
function attachInsertActions(bubbleEl, rawText) {
    const actionRow = document.createElement('div');
    actionRow.className = 'flex items-center gap-1.5 mt-2.5 pt-2 border-t border-gray-800 text-[10px]';

    const btnInsertAfter = document.createElement('button');
    btnInsertAfter.className = 'px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-indigo-300 font-bold border border-indigo-700/50 flex items-center gap-1';
    btnInsertAfter.innerHTML = `<span>📥 寫入文件</span>`;
    btnInsertAfter.addEventListener('click', async () => {
        // 移除 Markdown 代碼標籤後寫入
        const clean = rawText.replace(/```[\s\S]*?```/g, '').trim() || rawText;
        const res = await window.OfficeBridge.insertText(clean, { replace: false });
        if (res.success) showToast('已寫入游標位置！');
        else showToast('寫入失敗: ' + (res.error || ''), true);
    });

    const btnReplace = document.createElement('button');
    btnReplace.className = 'px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-amber-300 font-bold border border-amber-700/50 flex items-center gap-1';
    btnReplace.innerHTML = `<span>🔄 取代選取</span>`;
    btnReplace.addEventListener('click', async () => {
        const clean = rawText.replace(/```[\s\S]*?```/g, '').trim() || rawText;
        const res = await window.OfficeBridge.insertText(clean, { replace: true });
        if (res.success) showToast('已取代選取文字！');
        else showToast('取代失敗: ' + (res.error || ''), true);
    });

    actionRow.appendChild(btnInsertAfter);
    actionRow.appendChild(btnReplace);
    bubbleEl.appendChild(actionRow);
}

// ── 雙向對話紀錄聯動：匯出給 Webcom ──
function exportChatForWebcom() {
    if (chatHistory.length === 0) {
        showToast('目前無對話紀錄可匯出', true);
        return;
    }

    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const timestamp = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;

    // 格式完全相容 Webcom 主應用的 chat_history_*.json
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

    showToast(`📁 已匯出對話紀錄 [${fileName}]，可直接在 Webcom 匯入！`);
}

// ── 雙向對話紀錄聯動：自 Webcom 匯入 ──
function importChatFromWebcom(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            let msgs = [];
            if (Array.isArray(data)) msgs = data;
            else if (Array.isArray(data.messages)) msgs = data.messages;
            else if (Array.isArray(data.chatHistory)) msgs = data.chatHistory;
            else throw new Error('無法辨識此對話格式');

            document.getElementById('chat-container').innerHTML = '';
            chatHistory = [];

            let count = 0;
            msgs.forEach(m => {
                if (!m || m.role === 'system') return;
                const role = m.role === 'user' ? 'user' : 'assistant';
                const content = typeof m.content === 'string' ? m.content : JSON.stringify(m.content);
                
                const bubble = appendMessage(role, window.marked ? window.marked.parse(content) : content);
                chatHistory.push({ role, content, timestamp: m.timestamp || new Date().toISOString() });
                
                if (role === 'assistant') {
                    processChartDirectives(bubble, content);
                    attachInsertActions(bubble, content);
                }
                count++;
            });

            showToast(`✅ 已自 Webcom 成功匯入 ${count} 則對話紀錄！`);
        } catch (err) {
            console.error('[Import Error]', err);
            showToast('匯入失敗: ' + err.message, true);
        }
    };
    reader.readAsText(file, 'utf-8');
}

function showToast(msg, isErr = false) {
    const t = document.createElement('div');
    t.className = `fixed bottom-4 left-4 right-4 z-50 p-2.5 rounded-lg text-xs font-bold shadow-xl flex items-center gap-2 transition-all ${isErr ? 'bg-rose-950/90 text-rose-200 border border-rose-600' : 'bg-indigo-950/90 text-indigo-200 border border-indigo-600'}`;
    t.innerHTML = `<span>${isErr ? '⚠️' : '✨'}</span> <span>${msg}</span>`;
    document.body.appendChild(t);
    setTimeout(() => {
        t.style.opacity = '0';
        setTimeout(() => t.remove(), 300);
    }, 3000);
}

function scrollToBottom() {
    const c = document.getElementById('chat-container');
    if (c) c.scrollTop = c.scrollHeight;
}