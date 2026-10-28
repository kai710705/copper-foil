# 工作區開發憲法

本文件適用於本工作區及所有子目錄。新增或修改程式時，必須遵守以下規範；使用者明確提出的最新需求優先於本文件。對話、註解及專案文件原則上使用繁體中文。

完整的 Flask MVC、Web API 與前端分層細則，請依任務讀取 [.codex/skills/python-flask-skills/SKILL.md](.codex/skills/python-flask-skills/SKILL.md) 及其 `references/` 漸進式參考文件。本文件保留工作區層級的憲法；Skill 文件提供可重用的 agent 執行規範。

## 一、基本技術規格

- 後端使用 Python 與 Flask，支援 MVC 網站及 Web API。
- 以 `app.py` 作為啟動入口；採用 Application Factory 與 Blueprint 組織應用程式。
- 後端必須遵守關注分離，明確區分 Repository、Service、MVC Controller 與 Web API Controller。
- 前端 View Page 使用 Vue 3 JavaScript 實作 MVVM、Axios 實作 AJAX、Bootstrap 5.3 實作 RWD、SweetAlert2 實作對話盒。
- 使用 Tailwind CSS 實作櫥窗玻璃霧狀視覺風格（Glassmorphism）。
- 前端採離線架構，禁止使用 CDN；執行時所需的 JavaScript、CSS、字型、圖示與圖片必須由本機提供。

## 二、後端分層與責任

依賴方向為 `Controller → Service → Repository → 資料庫`。禁止逆向依賴；MVC Controller 與 Web API Controller 應共用 Service 的業務邏輯。

### Repository

- 負責資料存取、查詢、持久化與資料映射。
- 不得處理 HTTP 請求、回應、模板或業務決策。
- 資料庫查詢必須使用參數化查詢或 ORM，禁止拼接使用者輸入產生 SQL。
- 明確管理連線、交易、提交、回滾與資源釋放；需要跨 Repository 的交易時，由 Service 協調交易邊界。

### Service

- 負責業務規則、業務驗證、使用案例與交易協調。
- 透過 Repository 取得及保存資料，不直接撰寫資料庫查詢。
- 不依賴 Flask 的 `request`、`session`、`render_template` 或 HTTP 回應物件。
- 以一般 Python 資料或明確的資料模型作為輸入及輸出，讓 MVC 與 API 可重用。

### MVC Controller

- 負責網站路由、解析請求、輸入格式驗證、呼叫 Service，以及渲染 View 或重新導向。
- 不得直接存取資料庫或承載業務邏輯。
- 表單成功提交後原則上採用 Post/Redirect/Get，避免重新整理造成重複提交。

### Web API Controller

- 負責 API 路由、解析請求、輸入格式驗證、呼叫 Service，以及回傳 JSON 與 HTTP 狀態碼。
- 不得直接存取資料庫或承載業務邏輯。
- API 路由統一使用 `/api/v1/` 前綴，HTTP 方法與資源語意保持一致。
- 成功回應採 `{ "data": ... }`；錯誤回應採 `{ "error": { "code": "...", "message": "...", "details": ... } }`。
- 正確使用 200、201、204、400、401、403、404、409、500 等狀態碼；204 不包含回應本文。
- 不得將例外堆疊、SQL、密碼或內部敏感資訊傳回用戶端。

### View 與資料模型

- Jinja 模板負責頁面結構，Vue 負責前端狀態與互動；View 不得存取資料庫或實作後端業務規則。
- 明確區分持久化模型與 API 輸出欄位，避免直接序列化敏感欄位。

## 三、建議目錄結構

```text
app.py
app/
  __init__.py                 # Application Factory
  config.py                  # 環境設定
  extensions.py              # 共用擴充套件初始化
  models/                    # 資料模型
  repositories/              # 資料存取
  services/                  # 業務邏輯
  controllers/
    mvc/                     # MVC Blueprint
    api/                     # Web API Blueprint
  templates/                 # Jinja View Page
    layouts/
    components/
  static/
    vendor/                  # 本機第三方前端資源
    css/                     # 編譯完成的 CSS 與自訂樣式
    js/                      # Vue 頁面與 Axios 呼叫
    images/
    fonts/
frontend/                    # Tailwind 原始樣式及建置設定
tests/
requirements.txt
.env.example
README.md
```

可依專案規模調整檔案組織，但不得合併或模糊必要的分層責任。`app.py` 僅負責建立及啟動應用程式，不得堆放路由、SQL 或業務邏輯。

## 四、前端與離線規範

- Vue 使用 3.x 的 JavaScript 版本；不得未經需求變更改用其他 MVVM 框架或 TypeScript。
- AJAX 統一使用 Axios，集中設定 API 基底路徑、逾時、必要的 CSRF 標頭及錯誤處理。
- Bootstrap 固定採用 5.3.x，負責網格、斷點與響應式版面。
- SweetAlert2 負責提示、錯誤、成功訊息及操作確認；避免原生 `alert`、`confirm`、`prompt`。
- 所有第三方前端套件必須存放於 `static/vendor/` 或打包為本機靜態資源，記錄確切版本與授權。
- 禁止遠端 `<script>`、樣式表、字型、CSS `@import`、執行時套件下載或其他必需的外部資源。
- Tailwind CSS 必須在建置階段編譯成靜態 CSS，禁止使用 Tailwind Play CDN；建置結果需隨專案交付。
- Bootstrap 與 Tailwind 共存時，明確設定樣式載入順序；停用 Tailwind Preflight 或以可驗證的隔離方式避免覆蓋 Bootstrap 基礎樣式。
- 處理 Jinja 與 Vue 的模板語法衝突，例如設定 Vue 自訂 delimiters 或使用 `v-text`。
- 所謂離線是指無外網時，本機 Flask 與本機資料來源仍可提供完整頁面及操作；不代表 Flask 停止後仍可使用。PWA 或 Service Worker 須依額外需求實作。

## 五、視覺與互動規範

- 網站採櫥窗玻璃霧狀風格：半透明面板、背景模糊、柔和邊框與陰影，並維持清楚的文字層級。
- 使用 Tailwind 管理視覺樣式，Bootstrap 管理 RWD；必要的自訂 CSS 集中管理。
- 保持桌面、平板及手機版面可用，避免水平溢出與操作元素被遮擋。
- 文字需有足夠對比；提供鍵盤操作、可見焦點及表單標籤。
- 對不支援背景模糊的瀏覽器提供可讀的替代背景。
- 非同步操作需呈現載入、成功、失敗及空資料狀態，並防止重複提交。

## 六、設定與安全

- 設定與機密透過環境變數載入；提供 `.env.example`，不得將真實密碼、金鑰或 Token 寫入版本控制。
- 正式環境不得啟用 Flask debug 模式，使用適合部署環境的 WSGI Server。
- 後端必須驗證輸入，前端驗證僅作為使用體驗補充。
- 涉及身分與權限的功能，必須於後端執行授權檢查；不得僅依靠前端隱藏按鈕。
- 使用 Cookie 認證的狀態變更請求必須有 CSRF 防護；Session Cookie 依部署條件設定 HttpOnly、SameSite 與 Secure。
- 保留 Jinja 自動跳脫，避免將不可信資料直接交給 `v-html` 或標記為安全 HTML。
- 密碼必須使用適當的密碼雜湊；記錄例外時避免輸出敏感資料。

## 七、交付與驗證

- `README.md` 必須說明 Python 版本、依賴安裝、設定、資料庫初始化、前端建置及 `app.py` 啟動方式。
- Python 與前端依賴必須記錄可重現的版本；前端建置工具若使用套件管理器，需保留 lock file。
- 新增或修改功能時，驗證對應的 Service 規則、Repository 持久化，以及 MVC/API 的主要成功與失敗流程。
- 完成網站變更時，檢查實際頁面、RWD、瀏覽器錯誤，以及斷開外網後本機資源和功能是否正常。
- 不得僅以語法編譯成功或 HTTP GET 成功宣稱整個功能已完成；驗證應涵蓋變更涉及的實際操作。
- 交付時簡述變更內容、已執行的驗證與尚未驗證的項目。
