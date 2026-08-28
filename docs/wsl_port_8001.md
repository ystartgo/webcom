# WSL 環境開通 Port 8001 並啟動 Daemon / 本機 Shell (WSL) 終端
> 繁體中文 ・ [English](#-english)

當使用者在 **Webcom 終端機** 切換到「Local Shell (WSL)」通訊協定，或你想在 WSL 裡面跑 Daemon（FastAPI, Port 8001）、並讓 **Windows 上的瀏覽器能直接存取 `http://127.0.0.1:8001`**，請照本文件操作。

---

## 0. 先確認你的環境

```powershell
# Windows 端執行，列出已安裝的發行版
wsl -l -v
```

預期輸出要有一個 state = `Running` 的 distro，例如 `Ubuntu-22.04` 或 `Debian`。尚未安裝者，先在系統管理員 PowerShell 執行：

```powershell
wsl --install -d Ubuntu-22.04
# 重開機後設定 username/password，再回來繼續
```

> ✅ **建議使用 WSL 2**（`VERSION = 2`）。若顯示 1，請升級：
> `wsl --set-version Ubuntu-22.04 2`

---

## 1. 在 WSL 裡安裝 Python 3.10+ 與本專案依賴

> 💡 先確認 WSL 內是否已經有 python：進 WSL 後先執行 `which python3 ; python3 --version`，
> 如果出現 `python3: command not found`（本機目前的 Debian 就是這個狀態），代表尚未安裝，務必先做 apt install。

先把 webcom 專案掛載進去（Windows 端 `C:\Apps\Webcom` 在 WSL 裡會是 `/mnt/c/Apps/Webcom`）。也建議複製一份到 Linux 原生檔案系統，效能會好很多：

```bash
# ===== WSL 內執行 =====
# 0) [必要] 先裝系統層級的 python / pip / venv / 基本連線工具
#    （Debian / Ubuntu 都通用；若你用其他發行版請換成對應套件管理員）
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv python3-dev \
                    openssh-client telnet iputils-ping curl file \
                    iproute2 procps   # iproute2=ss 指令；procps=ps/pgrep
# (選用) 後端 Serial/SSH 用到的系統函式庫 (Paramiko/PySerial 編譯相依)
sudo apt install -y libffi-dev libssl-dev build-essential

# 1) (選用但強烈推薦) 把專案複製到 Linux 家目錄，IO 比 /mnt/c 快 10~30x
mkdir -p ~/workspace
if [ -d /mnt/c/Apps/Webcom ]; then
  cp -r /mnt/c/Apps/Webcom/* ~/workspace/webcom/ 2>/dev/null || true
fi
cd ~/workspace/webcom   # 或直接用 cd /mnt/c/Apps/Webcom (跳過複製)

# 2) 建立虛擬環境 + 安裝 Python 依賴
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 2. 啟動 Daemon（Port 8001）

### 方式 A：推薦 — 直接用腳本啟動（含 systemd / nohup 當守護程序）

```bash
# ===== WSL 內執行 =====
cd ~/workspace/webcom
chmod +x scripts/start_daemon_wsl.sh

# 前景執行（除錯用，可直接看 log）
./scripts/start_daemon_wsl.sh

# 背景執行 + 寫入 logs/daemon_wsl.log
nohup ./scripts/start_daemon_wsl.sh > logs/daemon_wsl.log 2>&1 &
echo $! > logs/daemon_wsl.pid
```

### 方式 B：裸指令

```bash
source .venv/bin/activate
python3 -u daemon.py                         # 預設 0.0.0.0:8001
# 或綁定所有介面（讓區網其他電腦也能連）
python3 -u -m uvicorn daemon:app --host 0.0.0.0 --port 8001
```

啟動後 **Windows 端** 應該就能直接開：
👉 **<http://127.0.0.1:8001>**（WSL2 自動 localhost forwarding 已預設開啟）

> 🧪 若不通，先在 WSL 裡自己 `curl http://127.0.0.1:8001/docs` 看看能不能拿到 FastAPI Swagger 文件。能拿到但 Windows 端拿不到 → 跳到第 4 節「防火牆 / localhost 轉送」。

---

## 3. Webcom 終端設定「Local Shell (WSL)」

Daemon 啟動在 WSL 後：

1. 打開 Webcom 介面 → 左上角 Protocol 下拉，選 **Local Shell (WSL)**。
2. 按 `Apply Conn`，系統會呼叫 Daemon 內的 `/api/shell/spawn` 路由，以 Daemon 執行身分（即 WSL 裡的使用者帳號）fork 一個 bash/zsh login shell。
3. 左側終端就會直接進入 WSL 環境，`pwd` 看到的是 WSL 家目錄或你專案路徑。

> 🔐 權限注意：Local Shell 等同直接獲得你在 WSL 中的使用者權限；若以 root 跑 Daemon，等同 root shell，請謹慎使用。

---

## 4. 遇到問題：Port 8001 在 Windows 端連不到 WSL

WSL2 雖然自動做 localhost forwarding，但有時 Windows 防火牆 / VPN / WSL localhostRelease 或 IPv6 優先會把它擋掉。照順序排查：

### 4-1. 先開 WSL2 的「鏡像網路模式」（Windows 11 22H2+ 支援，最穩）

> 💡 **先確認你是不是已經開了鏡像模式**：在 Windows 檢查 `%USERPROFILE%\.wslconfig`，如果內容已經有
> `networkingMode=Mirrored`（本機目前就是這個狀態，連 `[experimental] hostAddressLoopback=true` 都已設定），
> 就 **不要重複編輯**，直接跳到下面「`wsl --shutdown` 重啟」即可。

在 **Windows 端** 建立或編輯 `%USERPROFILE%\.wslconfig`，把下面內容完整貼上（所有選項皆為選擇性，標註 `# optional`）：

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true          # optional: 讓 WSL 與 Windows 共用 DNS（公司網路有 DNS 綁定的話建議開）
firewall=true              # optional: 繼承 Windows 防火牆規則
autoProxy=true             # optional: 繼承 Windows 的 proxy 設定
# localhostForwarding=true   # 在 mirrored 模式下預設就是 on，可不寫

[experimental]
# 讓 WSL 裡面也可以連回 Windows 本機的 localhost (例如你在 Windows 跑 LM Studio，WSL 內就能用 127.0.0.1:1234 連)
hostAddressLoopback=true

[interop]
# ⚡ 如果你一直看到 wsl: Failed to translate 'D:\...PortableApps\...Scripts' 的雜訊警告，
# 把下面這行註解拿掉，就不會把 Windows 的 PATH 匯入 WSL，也不會再噴警告。
# 副作用：在 WSL 裡不能直接 code . / explorer.exe . 等直接叫 Windows 程式。
# appendWindowsPath=false
```

> ⚠️ 任何對 `.wslconfig` 的修改都要 `wsl --shutdown` 後重啟才生效。

然後 **PowerShell (系統管理員)**：

```powershell
wsl --shutdown
# 等 5 秒再重新進入 wsl，將發行版取代為你自己的名稱（例如 Debian / Ubuntu-22.04）
wsl -d <你的發行版名稱，例如 Debian>
```

### 4-2. Windows 防火牆允許 Port 8001（若你想給區網其他機器存取）

```powershell
# PowerShell (系統管理員)
New-NetFirewallRule -DisplayName "Webcom Daemon 8001 (WSL)" `
  -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow -Profile Any
```

### 4-3. 手動 portproxy（僅 NAT 模式的最後手段 — **mirrored 模式不需要也不建議做**）

> 🛑 如果你在 4-1 已經切換到 `networkingMode=mirrored`，這一節 **整個跳過**。
> mirrored 模式下 WSL 與 Windows 共用同一組 IP，直接用 `127.0.0.1:8001` 或 Windows 真實區網 IP 就能連。

```powershell
# Step 1: Windows 端查 WSL instance 的 IP（僅 NAT 模式會需要；mirrored 模式不需要）
# 將 <DISTRO> 取代為 wsl -l -v 裡顯示的名稱，例如 Debian / Ubuntu-22.04
wsl -d <DISTRO> -- bash -c "hostname -I | awk '{print \$1}'"
# 輸出範例 172.30.186.211

# Step 2: PowerShell(Admin) 把 Windows 的 0.0.0.0:8001 導到 WSL_IP:8001
$wslIp = (wsl -d <DISTRO> -- bash -c "hostname -I | awk '{print `$1}'").Trim()
netsh interface portproxy add v4tov4 listenport=8001 listenaddress=0.0.0.0 `
    connectport=8001 connectaddress=$wslIp

# 查看轉送規則
netsh interface portproxy show all
```

> ⚠️ NAT 模式下 WSL IP **每次重開 WSL 會換**，建議直接切到 mirrored 模式（4-1）比較省事。

---

## 5. 常見問題 FAQ

| 症狀 | 可能原因 / 解法 |
|---|---|
| WSL 中 `python3 daemon.py` 正常，但 Windows 瀏覽器 `127.0.0.1:8001` ERR_CONNECTION_REFUSED | 90% 是 WSL network 模式不是 mirrored → 先做 4-1；若仍不行再做 4-3 portproxy（但 mirrored 模式就不用 4-3）|
| Daemon 啟動成功，Local Shell (WSL) 按 Apply Conn 後一直閒置 | 檢查 Daemon 是否真的 listen 0.0.0.0:8001 → `ss -ltnp \| grep :8001`；若只 listen 127.0.0.1 改以 `--host 0.0.0.0` 啟動 |
| `pip install pyserial paramiko` 失敗 | 在 WSL 中先 `sudo apt install -y build-essential libffi-dev libssl-dev`，再重跑 pip |
| 切到 mirrored 模式後 SSH 連不到 WSL IP | mirrored 模式下 Windows / WSL 共用同一個 IP；直接用 Windows 的 IP + 對應的防火牆規則即可，不要再查 WSL 自己的 `hostname -I` |
| 每次開機後 WSL 的 Daemon 就停了 | 見第 6 節「systemd 開機自啟」；若不想改 WSL 設定，也可以用 Windows 的工作排程器呼叫 `wsl.exe -d ... -e /path/to/script` |
| `python3: command not found` | WSL 預設常沒裝 Python。用 `sudo apt install python3 python3-pip python3-venv iproute2 procps` 先裝好再繼續（本文 §1 已更新為先做這一步）|
| 每次執行 wsl 指令都出現一堆 `wsl: Failed to translate 'D:\\USBOX_MYTOOLS\\...\Scripts'` 雜訊 | 這是 WSL 嘗試把 Windows PATH 中無效的 DrvFs 路徑翻譯成 Linux 路徑的警告，**不影響功能**。要消除它：在 `.wslconfig` 的 `[interop]` 加 `appendWindowsPath=false`（見 §4-1 的範例），然後 `wsl --shutdown` 重啟。|
| `wsl: Failed to attach disk ...` 或啟動 WSL 時當掉 | PortableApps / 防毒軟體常會鎖住 WSL 的 ext4.vhdx 檔。先結束所有 wsl → 工作管理員殺掉 WSL 行程 → 重新 `wsl -d Debian` 即可。|

---

## 6. (進階) 以 systemd 開機自動啟動 Daemon

> 💡 **先確認你是否已經啟用 systemd**：進 WSL 執行 `ps -p 1 -o comm=`，如果輸出是 `systemd`
> （本機 Debian 目前就是這個狀態，因為 `/etc/wsl.conf` 裡已有 `[boot] systemd=true`），
> 就 **跳過下面建立 `/etc/wsl.conf` 的步驟**，直接從 user service 範本開始。

使用 WSL 0.67+ 並啟用 systemd（如果你還沒開才做）：

```bash
# /etc/wsl.conf (WSL 內，需 sudo)  ← 只有 ps -p 1 不是 systemd 時才需要新增
[boot]
systemd=true
```

再寫一個 user service：

```ini
# ~/.config/systemd/user/webcom-daemon.service
[Unit]
Description=Webcom Daemon (Port 8001 FastAPI)
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/workspace/webcom
Environment=PATH=%h/workspace/webcom/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=%h/workspace/webcom/.venv/bin/python -u %h/workspace/webcom/daemon.py
Restart=on-failure
RestartSec=3
StandardOutput=append:%h/workspace/webcom/logs/daemon_wsl.log
StandardError=append:%h/workspace/webcom/logs/daemon_wsl.log

[Install]
WantedBy=default.target
```

啟用：

```bash
systemctl --user daemon-reload
systemctl --user enable --now webcom-daemon
# 避免登出就 killed (Debian/Ubuntu 預設需要)
sudo loginctl enable-linger $USER
```

---

---

<a id="-english"></a>
# WSL: How to Open Port 8001 & Run the Daemon + Local Shell (WSL) Terminal

Use this guide when you switch Webcom Terminal's protocol to **Local Shell (WSL)** or if you want to run the FastAPI daemon inside WSL (port 8001) and still reach it from **the browser on the Windows host at `http://127.0.0.1:8001`**.

---

## 0. Verify your WSL installation first

```powershell
# run on Windows, shows distros + WSL version
wsl -l -v
```

You should see at least one distro with state `Running`, e.g. `Ubuntu-22.04` or `Debian`. If none:

```powershell
# Admin PowerShell
wsl --install -d Ubuntu-22.04
# reboot, create a UNIX username/password, then return here.
```

> ✅ **WSL 2 strongly recommended** (`VERSION = 2`). If you see `1`, upgrade:
> `wsl --set-version Ubuntu-22.04 2`

---

## 1. Install Python 3.10+ and project deps inside WSL

> 💡 Always verify python first: run `which python3 ; python3 --version` inside WSL.
> If you get `python3: command not found` (the state of the Debian distro on this machine right now)
> you MUST install Python at the system level *before* trying to create a venv.

Your Windows folder `C:\Apps\Webcom` is auto-mounted at `/mnt/c/Apps/Webcom` in WSL.
We **strongly recommend** you copy the repo to the Linux native filesystem for 10~30× faster IO:

```bash
# ===== run inside WSL =====
# 0) [required] install system python + pip + venv + basic networking/diag tools first
#    (works for Debian & Ubuntu; adapt package names for other distros)
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv python3-dev \
                    openssh-client telnet iputils-ping curl file \
                    iproute2 procps     # iproute2 = `ss` cmd; procps = `ps/pgrep` cmds
# (optional) system libs used by Paramiko / PySerial native builds
sudo apt install -y libffi-dev libssl-dev build-essential

# 1) (optional but strongly recommended) copy repo to the native Linux FS
mkdir -p ~/workspace
if [ -d /mnt/c/Apps/Webcom ]; then
  cp -r /mnt/c/Apps/Webcom/* ~/workspace/webcom/ 2>/dev/null || true
fi
cd ~/workspace/webcom   # or skip copy and:  cd /mnt/c/Apps/Webcom

# 2) create venv + install Python deps
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 2. Launch the Daemon on Port 8001

### Option A (recommended) — bundled launcher script with nohup/systemd friendly mode

```bash
# ===== inside WSL =====
cd ~/workspace/webcom
chmod +x scripts/start_daemon_wsl.sh

# foreground (for debugging, live log)
./scripts/start_daemon_wsl.sh

# background + log to file
nohup ./scripts/start_daemon_wsl.sh > logs/daemon_wsl.log 2>&1 &
echo $! > logs/daemon_wsl.pid
```

### Option B — bare commands

```bash
source .venv/bin/activate
python3 -u daemon.py                                # default 0.0.0.0:8001
# or explicitly bind all interfaces so LAN devices can reach it too
python3 -u -m uvicorn daemon:app --host 0.0.0.0 --port 8001
```

Once running, open on **Windows**:
👉 **<http://127.0.0.1:8001>** (WSL2 localhost forwarding is enabled by default)

> 🧪 Smoke test: inside WSL run `curl http://127.0.0.1:8001/docs`. If WSL can see the FastAPI Swagger JSON but Windows cannot → jump to §4 *Firewall / localhost forwarding issues*.

---

## 3. Configure the Webcom "Local Shell (WSL)" Terminal

Once the Daemon runs inside WSL:

1. Open Webcom → top-left **Protocol** dropdown → pick **Local Shell (WSL)**.
2. Click **Apply Conn**. Webcom calls the Daemon's `/api/shell/spawn` route, which forks a `bash`/`zsh` login shell under the *same UNIX user that started the daemon*.
3. The left-hand terminal connects straight into WSL — `pwd` shows the WSL home or your project directory.

> 🔐 Permissions notice: *Local Shell (WSL)* gives the browser the same rights as the WSL user running the daemon. If you run the daemon as `root`, you are giving the browser a root shell — use with care.

---

## 4. Troubleshooting: Windows can't reach `127.0.0.1:8001` inside WSL

WSL2 auto-forwards `localhost` to the VM, but Windows Firewall, VPN software, IPv6 precedence or a disabled localhost forwarding often block it. Try in order:

### 4-1. Enable WSL2 mirrored networking (Win11 22H2+, most reliable)

> 💡 **Check if you already have mirrored mode first.** Open `%USERPROFILE%\.wslconfig` on the Windows side.
> If you already see `networkingMode=Mirrored` (as on this host, which also sets
> `[experimental] hostAddressLoopback=true`), **do NOT rewrite the file** — skip straight to the
> `wsl --shutdown` restart step below.

On **Windows**, create/edit `%USERPROFILE%\.wslconfig` (all flags are optional; each marked `# optional`):

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true          # optional: share DNS resolution with Windows (corp DNS setups)
firewall=true              # optional: inherit Windows Firewall rules
autoProxy=true             # optional: inherit Windows proxy settings
# localhostForwarding=true   # default on in mirrored mode; no need to write explicitly

[experimental]
# Lets processes *inside WSL* also connect back to services on the Windows localhost.
# Example: if you run LM Studio on Windows at 127.0.0.1:1234, WSL can reach it too.
hostAddressLoopback=true

[interop]
# ⚡ If you keep seeing noisy warnings:  wsl: Failed to translate 'D:\...PortableApps\...\Scripts'
# uncomment the line below. WSL will stop inheriting the Windows PATH entirely and the
# warnings vanish.  Trade-off: commands like  `code .`  /  `explorer.exe .`  inside WSL
# will no longer launch Windows apps.
# appendWindowsPath=false
```

> ⚠️ Any change to `.wslconfig` requires `wsl --shutdown` to take effect.

Then from **Admin PowerShell**:

```powershell
wsl --shutdown
# wait ~5 s, then re-enter — replace <YOUR_DISTRO_NAME> with what  wsl -l -v  shows (Debian / Ubuntu-22.04 / etc.)
wsl -d <YOUR_DISTRO_NAME>
```

### 4-2. Allow port 8001 through Windows Firewall (only needed if you share Daemon over the LAN)

```powershell
# Admin PowerShell
New-NetFirewallRule -DisplayName "Webcom Daemon 8001 (WSL)" `
  -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow -Profile Any
```

### 4-3. Manual `portproxy` (last-resort fallback under NAT mode only — **NOT needed when using mirrored mode**)

> 🛑 If you already switched to `networkingMode=mirrored` in §4-1, **SKIP this entire section**.
> Under mirrored mode, WSL and Windows share the same network stack; just connect to
> `http://127.0.0.1:8001` or to the real LAN IP of the Windows host.

```powershell
# Step 1: on Windows, query the WSL VM IP (NAT mode only; not needed with mirrored mode)
# Replace <DISTRO> with the name shown by  wsl -l -v  e.g. Debian / Ubuntu-22.04
wsl -d <DISTRO> -- bash -c "hostname -I | awk '{print \$1}'"
# example output 172.30.186.211

# Step 2: Admin PowerShell — forward Windows 0.0.0.0:8001 to WSL_IP:8001
$wslIp = (wsl -d <DISTRO> -- bash -c "hostname -I | awk '{print `$1}'").Trim()
netsh interface portproxy add v4tov4 listenport=8001 listenaddress=0.0.0.0 `
    connectport=8001 connectaddress=$wslIp

# verify forward rule
netsh interface portproxy show all
```

> ⚠️ In NAT mode the WSL IP **changes on every `wsl --shutdown`**. Mirrored mode (§4-1) avoids this entirely — switch over when possible.

---

## 5. FAQ

| Symptom | Likely cause / fix |
|---|---|
| `python3 daemon.py` works in WSL, but Windows browser hits ERR_CONNECTION_REFUSED on 127.0.0.1:8001 | 90% = WSL2 networkingMode != mirrored → apply §4-1; if still dead use §4-3 portproxy (skip §4-3 if mirrored) |
| Daemon boots, but Apply Conn on "Local Shell (WSL)" hangs forever | Check `ss -ltnp \| grep :8001` inside WSL — if it only listens on 127.0.0.1 restart with `uvicorn daemon:app --host 0.0.0.0 --port 8001` |
| `pip install pyserial paramiko` fails | `sudo apt install -y build-essential libffi-dev libssl-dev` first |
| After switching to mirrored mode, SSH into WSL IP stops working | Mirrored mode shares Windows' IP stack. Use *Windows IP* + §4-2 firewall rule; don't try `hostname -I` of WSL |
| Daemon dies on every Windows reboot | Use §6 systemd user service, or create a Windows Task Scheduler entry running `wsl.exe -d ... -e /path/to/script` |
| `python3: command not found` when entering WSL | Stock Debian/Ubuntu WSL images often ship without Python. Fix: `sudo apt install python3 python3-pip python3-venv iproute2 procps` (already reflected in §1 order) |
| Every `wsl` invocation prints spam like `wsl: Failed to translate 'D:\\USBOX_MYTOOLS\\...\Scripts'` | WSL tries to translate invalid Windows PATH entries; it is **harmless**. To silence the noise, add `appendWindowsPath=false` under `[interop]` in `%USERPROFILE%\.wslconfig` (see §4-1 sample) then `wsl --shutdown`. |
| `wsl: Failed to attach disk ...` or WSL fails to start at all | PortableApps suites / antivirus often lock the WSL ext4.vhdx backing file. Kill all WSL processes in Task Manager, close PortableApp launchers, then retry `wsl -d <distro>`. |

---

## 6. (Advanced) Autostart Daemon via WSL systemd

> 💡 **Check if systemd is already enabled first.** Inside WSL run `ps -p 1 -o comm=`. If the output is `systemd`
> (as on this host's Debian distro, because `/etc/wsl.conf` already contains `[boot] systemd=true`),
> **SKIP the `/etc/wsl.conf` creation step below** and go straight to the user-service template.

Requires WSL 0.67+ with systemd enabled (only do this if `ps -p 1` is NOT systemd):

```bash
# /etc/wsl.conf (inside WSL, sudo needed)  ← only create this if PID 1 is NOT systemd yet
[boot]
systemd=true
```

Create a user service:

```ini
# ~/.config/systemd/user/webcom-daemon.service
[Unit]
Description=Webcom Daemon (Port 8001 FastAPI)
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/workspace/webcom
Environment=PATH=%h/workspace/webcom/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=%h/workspace/webcom/.venv/bin/python -u %h/workspace/webcom/daemon.py
Restart=on-failure
RestartSec=3
StandardOutput=append:%h/workspace/webcom/logs/daemon_wsl.log
StandardError=append:%h/workspace/webcom/logs/daemon_wsl.log

[Install]
WantedBy=default.target
```

Enable it:

```bash
systemctl --user daemon-reload
systemctl --user enable --now webcom-daemon
# prevent systemd from killing user services on logout (Debian/Ubuntu)
sudo loginctl enable-linger $USER
```
