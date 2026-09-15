document.getElementById('btn-request').addEventListener('click', async () => {
    try {
        if (!('serial' in navigator)) {
            alert('此環境不支援 Web Serial API');
            return;
        }
        const port = await navigator.serial.requestPort();
        if (chrome && chrome.runtime && chrome.runtime.sendMessage) {
            chrome.runtime.sendMessage({ action: 'serial_port_authorized' });
        }
        window.close();
    } catch (err) {
        if (err.name !== 'NotFoundError' && !String(err.message).includes('No port selected')) {
            alert('選取序列埠失敗: ' + err.message);
        }
    }
});

window.onload = () => {
    const btn = document.getElementById('btn-request');
    if (btn) btn.focus();
};
