# Spec Delta

## Purpose

將影像辨識發現的明確工安違規轉為可追蹤、可去重、可由管理者處理的警訊資料，讓系統保留判定依據與後續處理歷程。

## ADDED Requirements

### Requirement: System SHALL create an alert for explicit safety failures
系統 SHALL 僅在安全帽、反光背心或場所圍籬被明確判定為 `fail` 時建立或更新工安警訊。

#### Scenario: A safety failure creates an open alert
- **WHEN** 有效辨識結果包含至少一項 `fail`
- **THEN** 系統保存警訊項目、摘要、信心分數、偵測時間、狀態 `open` 及來源資訊

#### Scenario: All checks pass
- **WHEN** 三項檢核皆為 `pass`
- **THEN** 系統不建立新的工安警訊

#### Scenario: Checks contain only unknown
- **WHEN** 三項檢核沒有 `fail` 且至少一項為 `unknown`
- **THEN** 系統保存辨識結果供查詢，但不建立危險警訊

### Requirement: Repeated observations SHALL not create duplicate open alerts
系統 SHALL 依攝影機、檢核項目、未結案狀態及合理時間窗口去重重複辨識結果。

#### Scenario: Same failure is observed repeatedly
- **WHEN** 同一攝影機在既有警訊仍為 `open` 時重複發現相同違規
- **THEN** 系統更新既有警訊的最近觀測資訊，不新增重複的 `open` 警訊

#### Scenario: Failure returns after resolution
- **WHEN** 相同檢核項目在既有警訊已結案後再次明確 `fail`
- **THEN** 系統建立新的 `open` 警訊並保留新偵測時間

### Requirement: Administrators SHALL be able to process alerts
系統 SHALL 允許具管理權限的使用者查詢警訊、標記已確認及完成處理；未授權使用者不得變更警訊狀態。

#### Scenario: Administrator resolves an open alert
- **WHEN** 管理者提交有效的處理狀態變更
- **THEN** 系統更新警訊狀態、處理者與處理時間

#### Scenario: Non-administrator attempts to resolve an alert
- **WHEN** 一般已核准會員嘗試變更警訊狀態
- **THEN** 系統拒絕請求且不修改警訊資料

### Requirement: Alert records SHALL not contain secrets or raw images by default
系統 SHALL 保存辨識摘要與必要的判定資料，但不得保存 API key；第一版 SHALL 不永久保存原始影像。

#### Scenario: Alert is persisted
- **WHEN** 系統建立或更新警訊
- **THEN** 資料庫只保存允許的辨識摘要、檢核狀態、信心分數、模型資訊與時間欄位

#### Scenario: External provider fails
- **WHEN** 外部辨識服務失敗
- **THEN** 系統不將認證標頭、API key 或內部例外堆疊寫入警訊或 API 回應
