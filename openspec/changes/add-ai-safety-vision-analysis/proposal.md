# Proposal

## Why

現有 `/video` 已能透過 OpenCV 顯示 CAM 影像，但尚未能辨識工業安全風險或保存可追蹤的警訊。新增 Ollama Gemma 視覺辨識服務，讓系統針對安全帽、反光背心與場所圍籬提供 AI 輔助判定，並將明確不符合項目轉為工安警訊供後續處理。

## What Changes

- 新增伺服器端 Ollama Vision Client，使用環境變數設定 API 位址、API key、模型名稱與逾時時間。
- 新增影像辨識 Service，從既有 CameraService 取得影格，呼叫 Gemma 視覺模型並驗證結構化 JSON 結果。
- 新增三項工安檢核：安全帽、反光背心、場所邊界圍籬。
- 新增手動影像辨識流程，避免第一版直接引入高頻自動呼叫與成本失控。
- 新增辨識結果與警訊 Service，對明確 `fail` 建立或更新 `safety_alerts`，並避免同一事件重複建立警訊。
- 保存檢核狀態、信心分數、辨識摘要、模型資訊與處理時間；第一版不保存原始影像。
- 提供管理者查詢、確認與結案警訊的 API／頁面資料，沿用既有登入、授權與 CSRF 規則。
- 將 Ollama 連線失敗、逾時、非法 JSON 與 `unknown` 狀態明確區分，不把無法判斷誤報為危險。

## Capabilities

### New Capabilities

- `safety-vision-analysis`: 影像安全辨識、三項工安檢核、結構化結果驗證與辨識觸發流程。
- `ai-safety-alerts`: 將辨識結果轉成可追蹤的工安警訊、去重、查詢與處理狀態。

### Modified Capabilities

目前 `openspec list --specs` 沒有既有正式 capability，因此不修改既有規格；既有 `lab-monitoring` 是進行中的變更規劃，不作為本次 capability 的替代品。

## Impact

- 影響 `app/services`、`app/repositories`、`app/controllers`、`app/templates`、`app/static/js` 與 SQLite migration。
- 新增 Ollama／Gemma cloud API 的伺服器端整合與可測試的 HTTP client 邊界。
- 新增或調整 `safety_alerts` 欄位與索引，保留既有警訊資料相容性。
- 新增 API key、模型名稱、端點與 timeout 的環境設定；機密不得進入程式碼、報告或版本控制。
- 不改變既有 OpenCV MJPEG 串流協定；AI 辨識失敗不得阻塞 `/video` 的本機影像顯示。
- 第一版不包含自動固定間隔辨識、原始影像永久保存、通知推播、錄影或正式安全稽核取代。
