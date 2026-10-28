# 台南大學實驗室監控系統

以 Flask、SQLite 與本機前端資源建置的實驗室工安監控原型，包含會員申請／審核、警示與稽核管理，以及按鈕觸發的 OpenCV 鏡頭串流。安全率與初始化事件明確標示為示範資料；攝影機資源清單不代表實體設備已連線。

## 執行環境

- Python 3.12 以上版本（Windows 可使用已安裝的 Python 3.14）。
- Node.js 及 npm 僅在要重建 Tailwind CSS 時需要；一般執行網站不需要 Node.js。
- SQLite 由 Python 內建 `sqlite3` 提供。第一次啟動會建立或版本升級 `instance/calendar.sqlite`；既有資料庫升級前會建立 SQLite 備份。
- Python 相依版本鎖定於 `requirements.txt`；離線執行的 Vue、Axios、Bootstrap、SweetAlert2 與建置後 CSS 存放在 `app/static/`。

## Windows 安裝與啟動

在 PowerShell 專案根目錄執行：

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

開啟 `.env`，將 `SECRET_KEY` 換成隨機值。可用以下指令產生後手動貼入，避免將正式密鑰寫入指令歷程：

```powershell
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

啟動網站：

```powershell
.\start.ps1
```

預設以非 Debug 模式啟動於 <http://127.0.0.1:5000>。開發時才使用 `.\start.ps1 -Development`；也可用 `.\start.ps1 -Port 8000` 指定連接埠。直接以 `.venv\Scripts\python.exe app.py` 啟動時，Debug 仍預設關閉。

`start.ps1` 優先使用專案 `.venv` Python，能避免系統 Python 與 IDE 使用不同直譯器而發生 `ModuleNotFoundError: No module named 'flask'`。若仍出現該錯誤，請確認 `python` 使用的是 `.venv\Scripts\python.exe`，並用同一個執行檔安裝 `requirements.txt`。

初次建立資料庫時預設管理者為 `admin`／`admin@123`，首次登入會要求變更密碼。新會員（包括申請管理者角色者）都要經管理者審核後才能登入。現有資料庫不會重設管理者密碼或自動補回已刪除的示範事件。

## 前端 CSS 重建

前端依賴版本鎖定在 `frontend/package-lock.json`。在有網路的建置環境執行：

```powershell
Set-Location frontend
npm ci
npm run build
Set-Location ..
```

Tailwind CSS 會掃描所有 Flask 模板與頁面 JavaScript，輸出到 `app/static/css/video-tailwind.css`；Tailwind Preflight 已停用以避免覆蓋 Bootstrap。Vue、Axios、Bootstrap 5.3、SweetAlert2 與網站 CSS 皆由本機靜態路徑提供，執行網站時不需 CDN 或外網。

## 設定

`.env.example` 列出常用環境變數：`SECRET_KEY`、`DATABASE`、`CAMERA_INDEX` 與 `SESSION_COOKIE_SECURE`。正式環境設定 `APP_ENV=production`，必須提供私有隨機 `SECRET_KEY`；HTTPS 部署時設定 `SESSION_COOKIE_SECURE=1`。`.env` 已排除於 Git 與 Docker 建置內容之外。

OpenCV 預設使用 `CAMERA_INDEX=0`。鏡頭頁面載入時只查詢狀態，使用者按「啟動鏡頭」後才開啟裝置。Docker 容器只有在主機平台額外提供攝影機裝置及權限時才能使用實體鏡頭；容器中的資源登錄本身不會連接鏡頭。

既有 Docker Compose 容器名稱為 `MyCam`；在已設定 `.env` 的情況下，可由專案根目錄執行 `docker compose up --build -d`。正式部署請設定 `APP_ENV=production`、強隨機 `SECRET_KEY`，並在 TLS Proxy 後將 `SESSION_COOKIE_SECURE=1`。

## API 與主要頁面

- `/`：工安監控首頁；已核准會員可讀取 SQLite 監控摘要。
- `/login`、`/register`：會員登入及註冊。註冊以 Vue／Axios 呼叫 API，所有狀態變更使用 Session CSRF Token。
- `/admin`：管理者會員審核、實驗室／攝影機資源、警示及稽核管理。
- `/video`：登入後的 OpenCV 鏡頭狀態與串流操作；只有按下啟動後才取得影像。
- `/api/v1/auth/*`：註冊、登入、登出及密碼操作。
- `/api/v1/monitoring`：已核准會員讀取警示、稽核、資源與統計。
- `/api/v1/admin/users`、`/api/v1/admin/laboratories`、`/api/v1/admin/cameras`、`/api/v1/admin/alerts`、`/api/v1/admin/audits`：管理操作 API。

管理操作須具管理者權限且帶有 `X-CSRF-Token`。一般會員不可呼叫管理寫入 API。

## 目錄導覽

```text
app.py                         Flask 啟動入口
app/__init__.py                Application Factory 與 Blueprint 註冊
app/controllers/               MVC、API、鏡頭路由及安全檢查
app/services/                  業務驗證與使用案例
app/repositories/              SQLite 查詢、交易、migration 與持久化
app/templates/                 Jinja 頁面
app/static/vendor/             Vue、Axios、Bootstrap、SweetAlert2 本機資源
app/static/js/                 各頁 Vue 與共用 Axios
app/static/css/                網站及 Tailwind 編譯產物
frontend/                      Tailwind 設定、輸入 CSS、lock file
tests/                         SQLite migration、會員、工安及鏡頭測試
docs/                          系統與操作文件
```

## 驗證

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

測試涵蓋資料升級與保留、身分／審核／CSRF 權限、警示與稽核狀態持久化、資源管理及鏡頭啟停與失敗狀態。桌面／手機瀏覽器呈現及實體鏡頭仍需在目標電腦與實際設備上驗收。

## AI 影像辨識

`/video` 提供手動 AI 影像辨識，使用目前 OpenCV JPEG 影格檢查安全帽、反光背心與場所圍籬。辨識 API 為 `/api/v1/vision/analyze`，只有已核准會員可使用；明確 `fail` 才會建立或更新工安警訊，`unknown` 不會直接視為危險。AI 結果僅供安全檢查輔助，不取代人工判斷。

設定以下環境變數後，伺服器會呼叫 Ollama `/api/chat`：

```text
OLLAMA_BASE_URL=
OLLAMA_API_KEY=
OLLAMA_MODEL=gemma4:31b-cloud
OLLAMA_TIMEOUT_SECONDS=30
OLLAMA_MAX_IMAGE_BYTES=4194304
```

`OLLAMA_API_KEY` 只能放在未納入版本控制的 `.env` 或秘密管理服務，不能寫入原始碼、文件或日志。Ollama 無法使用時，本機 `/video` 影像串流仍可維持運作。
