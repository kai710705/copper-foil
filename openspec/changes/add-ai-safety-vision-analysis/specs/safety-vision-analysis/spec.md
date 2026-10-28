# Spec Delta

## Purpose

提供可追蹤的工業安全影像辨識能力，將攝影機影像轉換為安全帽、反光背心與場所圍籬的結構化檢核結果，並清楚區分通過、不符合與無法判斷。

## ADDED Requirements

### Requirement: System SHALL analyze a submitted camera image for defined safety checks
系統 SHALL 接受授權使用者要求分析的攝影機影像，並針對安全帽、反光背心及場所邊界圍籬產生辨識結果。

#### Scenario: Analyze a valid camera frame
- **WHEN** 已核准使用者提交有效且可讀取的影像
- **THEN** 系統回傳三項檢核結果、各項狀態、信心分數及整體摘要

#### Scenario: Camera frame is unavailable
- **WHEN** 使用者要求分析但目前沒有可用影格
- **THEN** 系統回傳可辨識的影像不可用錯誤，且不建立工安警訊

### Requirement: Each safety check SHALL distinguish pass, fail, and unknown
系統 SHALL 將每一項檢核限制為 `pass`、`fail` 或 `unknown`，並提供 0 到 1 的信心分數。

#### Scenario: Model returns an explicit failure
- **WHEN** 模型明確判定人員未戴安全帽、未穿反光背心或場所邊界未設置圍籬
- **THEN** 對應項目狀態為 `fail`，並可進入警訊判定流程

#### Scenario: Model cannot determine a check
- **WHEN** 影像遮擋、模糊或未涵蓋檢核範圍
- **THEN** 對應項目狀態為 `unknown`，且系統不得將其直接視為危險

### Requirement: Invalid vision output SHALL be rejected safely
系統 SHALL 驗證影像辨識回應的 JSON 結構、欄位、狀態與信心分數，非法結果不得被當作有效工安判定。

#### Scenario: Model returns invalid JSON
- **WHEN** 外部模型回傳無法解析的 JSON 或缺少必要欄位
- **THEN** 系統回傳辨識失敗狀態，且不寫入工安警訊

#### Scenario: Vision provider times out
- **WHEN** 外部模型超過設定的逾時時間仍未回應
- **THEN** 系統回傳服務不可用錯誤，且既有攝影機串流仍可繼續運作

### Requirement: Vision analysis SHALL be authorized and rate controlled
系統 SHALL 僅允許已核准帳號執行影像辨識，並限制單一使用者的辨識頻率與影像大小。

#### Scenario: Unapproved user requests analysis
- **WHEN** 未登入或未核准使用者呼叫影像辨識
- **THEN** 系統拒絕請求並不呼叫外部模型

#### Scenario: User exceeds analysis limit
- **WHEN** 使用者在限制時間內超過允許的辨識次數或影像大小
- **THEN** 系統拒絕請求並回傳可理解的限制錯誤
