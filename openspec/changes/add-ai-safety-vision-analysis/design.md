# Design

## Context

現有 `/video` 使用 `CameraService` 與 OpenCV 取得影格並輸出 MJPEG；既有 `MonitoringService` 可查詢與處理 `safety_alerts`。本變更需在不阻塞本機影像串流的前提下，加入外部 Ollama 視覺辨識與可追蹤警訊寫入。

## Goals / Non-Goals

**Goals:**

- 建立可測試的 Ollama client 與影像辨識 Service。
- 將三項工安檢核轉成驗證過的結構化結果。
- 由 Service 控制警訊建立、去重、查詢與狀態處理。
- 透過環境變數保護 endpoint、API key、模型與 timeout。
- 保留既有 OpenCV MJPEG 串流，即使 AI 服務不可用也能顯示本機影像。

**Non-Goals:**

- 不保存原始影像、不做錄影、不提供推播通知。
- 不在第一版加入固定間隔自動辨識。
- 不把 AI 判定當成正式工安稽核或取代人工判斷。
- 不新增多 worker 或跨程序攝影機協調。

## Decisions

### 1. 以手動辨識作為第一版觸發方式

第一版由已核准使用者在 `/video` 頁面明確觸發辨識，降低 Ollama cloud 呼叫成本、避免每個影格重複建立警訊，也讓端到端行為容易驗證。固定間隔辨識可在後續變更中加入。

### 2. 以獨立 Ollama client 隔離外部 API

Ollama client 只處理認證、請求格式、timeout、HTTP 錯誤與回應解析；不直接決定工安警訊。`OLLAMA_API_KEY` 僅由伺服器環境取得，不傳給前端或寫入日志。

### 3. VisionAnalysisService 與 SafetyAlertService 分離

影像辨識負責「看見什麼」，警訊 Service 負責「是否形成工安事件及如何保存」。兩者分離可讓模型替換、規則調整與測試不互相綁定。

### 4. 以 `unknown` 作為安全的不可判定狀態

影像不足時不能推論為違規，也不能推論為通過。只有 `fail` 進入警訊建立規則；`unknown` 可保留於辨識結果或回應中供人工確認。

### 5. 先沿用既有 open/resolved，再保留狀態擴充點

為降低既有資料與 API 破壞，第一版沿用目前 `open -> resolved` 流程。資料欄位與 Service 邊界應保留未來加入 `acknowledged` 的空間，不在本次偷偷改變既有管理頁行為。

### 6. 以資料庫去重鍵防止重複警訊

警訊 Service 會以攝影機、檢核項目、未結案狀態及時間窗口判斷重複事件；Repository 使用參數化查詢與交易，避免多次辨識產生無限重複資料。

## Risks / Trade-offs

- [模型誤判] -> 顯示信心分數與 AI 輔助標示，保留人工確認，不保存為絕對安全結論。
- [外部服務中斷] -> 設定 timeout，辨識失敗只回報服務狀態，不阻塞 CameraService。
- [JSON 格式不穩定] -> 後端做 schema 驗證，非法輸出不建立警訊。
- [SQLite 並行寫入] -> 由 Service 控制交易，Repository 使用去重查詢與資料庫約束。
- [API key 洩漏] -> 只使用環境變數，不記錄認證標頭，不回傳外部錯誤原文。
- [影像隱私] -> 第一版不保存原始影像，只保存最小必要的辨識摘要。

## Migration Plan

1. 先備份 SQLite，檢查現有 `safety_alerts` 結構與資料完整性。
2. 以可重複執行的 migration 新增必要的辨識摘要、模型資訊、信心分數、去重及時間欄位。
3. 以環境變數設定 Ollama endpoint、API key、模型與 timeout；缺少設定時服務應能啟動，但辨識端點回傳明確不可用狀態。
4. 先部署手動辨識 API 與 Service 單元測試，再整合 `/video` 頁面。
5. 以假 Ollama client 驗證正常回應、非法 JSON、timeout、`pass`、`fail`、`unknown` 與重複警訊流程。
6. 回滾時停止辨識請求，保留新增資料，還原相容版本程式與資料庫備份；不刪除既有警訊。

## Confirmed External API Contract

- Ollama Vision REST API 使用 `POST /api/chat`。
- request body 使用 `model`、`messages`、`stream: false`，影像放在 user message 的 `images` Base64 陣列。
- response content 位於 `message.content`；本系統仍需自行驗證其中的 JSON。
- cloud 認證由環境設定注入 Bearer token，不在設計或測試中保存實際 token。
- 依據：Ollama 官方 Vision 文件與 Chat API 文件（`https://docs.ollama.com/capabilities/vision`、`https://docs.ollama.com/api/chat`）。

## Open Questions

- 三項檢核的最低信心門檻尚未定案，預設值不應直接寫死為安全保證。
- 場所圍籬是否需要管理者在畫面上設定邊界區域，仍需依實際攝影機角度確認。
