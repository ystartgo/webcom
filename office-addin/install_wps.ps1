# Webcom 金山 WPS Office 增益集自動註冊腳本
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       Webcom 金山 WPS Office JS 增益集一鍵註冊工具       " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$wpsSrcDir = Join-Path $scriptDir "wps"
$ribbonSrc = Join-Path $wpsSrcDir "ribbon.xml"
$indexSrc = Join-Path $wpsSrcDir "index.html"

if (-not (Test-Path $ribbonSrc) -or -not (Test-Path $indexSrc)) {
    Write-Host "[錯誤] 找不到 WPS 增益集範本檔案 (wps\ribbon.xml 或 wps\index.html)！" -ForegroundColor Red
    exit 1
}

$appData = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::ApplicationData)
$targetDirs = @(
    (Join-Path $appData "kingsoft\wps\jsaddons"),
    (Join-Path $appData "kingsoft\wps_intl\addons")
)

$publishXmlContent = @"
<?xml version="1.0" encoding="UTF-8"?>
<jsplugins>
    <jspluginonline name="WebcomAI" url="https://127.0.0.1:8002/office-addin/wps/" type="wps" enable="true"/>
    <jspluginonline name="WebcomAIEt" url="https://127.0.0.1:8002/office-addin/wps/" type="et" enable="true"/>
    <jspluginonline name="WebcomAIWpp" url="https://127.0.0.1:8002/office-addin/wps/" type="wpp" enable="true"/>
</jsplugins>
"@

Write-Host "[1/3] 正在安裝 WPS 文字、表格、演示 JS 增益集至本機設定目錄..." -ForegroundColor Yellow
$installedCount = 0
foreach ($dir in $targetDirs) {
    try {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
        }
        
        # 寫入 publish.xml
        $pubFile = Join-Path $dir "publish.xml"
        [System.IO.File]::WriteAllText($pubFile, $publishXmlContent, [System.Text.Encoding]::UTF8)
        
        # 部署離線包目錄 WebcomAI_1.0.0 (含 ribbon.xml, index.html, main.js, taskpane.html, manifest.xml)
        $offlineDir = Join-Path $dir "WebcomAI_1.0.0"
        if (-not (Test-Path $offlineDir)) {
            New-Item -ItemType Directory -Force -Path $offlineDir | Out-Null
        }
        Copy-Item -Path (Join-Path $wpsSrcDir "*") -Destination $offlineDir -Recurse -Force
        
        Write-Host "  [OK] 已成功註冊至: $dir" -ForegroundColor Green
        $installedCount++
    } catch {
        Write-Host "  [!] 註冊 $dir 略過: $_" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "[2/3] 檢查本機 SSL 憑證受信任狀態 (view.yia.app / 127.0.0.1)..." -ForegroundColor Yellow
$certStatus = & certutil -store Root view.yia.app 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] SSL 憑證已加入 Windows 受信任清單，WPS 內嵌通訊無警告。" -ForegroundColor Green
} else {
    Write-Host "  [提示] 建議先右鍵以管理員身分執行一次 trust_cert.bat 以確保完全信任。" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[3/3] 檢查 Webcom 常駐後端 (HTTPS 8002)..." -ForegroundColor Yellow
$tcpConn = Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue
if ($tcpConn) {
    Write-Host "  [OK] Webcom 常駐後端 8002 埠運行中！" -ForegroundColor Green
} else {
    Write-Host "  [!] 注意: Webcom 常駐後端尚未啟動，請執行 python daemon.py。" -ForegroundColor Magenta
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  🎉 WPS Office 增益集安裝與設定全部就緒！" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "【如何啟用與使用】： - 請將 WPS 文字 (或 WPS 表格) 完全關閉後重新開啟。"
Write-Host "  1. 打開任一 WPS 文字或表格文件。"
Write-Host "  2. 上方功能區 (Ribbon) 會自動出現【Webcom AI】標籤頁！"
Write-Host "  3. 點擊【開啟 Webcom】按鈕，右側將立即展開 AI 智慧助理側邊欄！"
Write-Host ""
Write-Host "【手動即時開啟方式 (免重開 WPS)】："
Write-Host "  在 WPS 文字中按 Alt + F11 打開「WPS宏編輯器」，在下方立即視窗輸入："
Write-Host '    wps.CreateTaskPane("https://127.0.0.1:8002/office-addin/taskpane.html", "Webcom AI 智慧助理")' -ForegroundColor Yellow
Write-Host "  按下 Enter 即可立即在右側彈出側邊欄！"
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
