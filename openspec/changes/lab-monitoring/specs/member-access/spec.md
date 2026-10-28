# 會員存取規格差異

## Purpose

提供實驗室監控系統可驗證的帳號申請與登入流程，讓一般使用者與管理者只有在核准後才能存取受保護功能，並防止停用帳號沿用既有登入狀態操作資料。

## ADDED Requirements

### Requirement: 註冊角色與輸入驗證
系統 SHALL 接受帳號、Email、密碼與角色，角色僅允許 `user`、`admin`。新申請 SHALL 為 `pending`，密碼 SHALL 雜湊保存；無效輸入回傳 400，重複帳號或 Email 回傳 409。

#### Scenario: 管理者角色申請也需審核
- **WHEN** 訪客提交有效的管理者註冊資料
- **THEN** 系統建立待審核會員，不自動授予管理操作權限

#### Scenario: 非法角色
- **WHEN** 訪客傳入不在允許清單內的角色
- **THEN** 系統回傳 400，且不建立帳號

### Requirement: 核准後登入與登出
系統 SHALL 提供網頁登入及 `POST /api/v1/auth/login`，僅允許密碼正確且狀態為 `approved` 的會員登入。未核准或停用帳號 SHALL 被拒絕；登出 SHALL 清除登入狀態。

#### Scenario: 待審核帳號登入
- **WHEN** 待審核會員提供正確密碼
- **THEN** 系統拒絕登入，且不建立登入 Session

#### Scenario: 已核准帳號登入
- **WHEN** 已核准會員提交正確密碼
- **THEN** 系統建立登入狀態並回傳不含密碼雜湊的會員資訊

### Requirement: 持續授權與 CSRF 防護
系統 SHALL 每次查驗受保護功能的會員狀態及角色，不信任過期 Session 角色。未登入回傳 401，一般會員管理操作回傳 403；Cookie 認證的狀態變更請求 SHALL 驗證 CSRF Token。

#### Scenario: 已登入會員被停用
- **WHEN** 停用帳號以先前 Session 存取監控 API
- **THEN** 系統拒絕請求，不回傳監控資料

#### Scenario: 管理請求沒有 CSRF Token
- **WHEN** 已登入管理者提交缺少有效 CSRF Token 的資料變更
- **THEN** 系統回傳 403，資料保持原狀

### Requirement: 預設管理者與首次變更密碼
初始化 SHALL 建立已核准的 `admin`／`admin@123`，不重設既有管理者密碼。使用預設密碼登入的管理者 SHALL 先修改密碼，才可操作會員審核或其他管理功能。

#### Scenario: 首次登入預設帳號
- **WHEN** 管理者以預設密碼登入
- **THEN** 系統導向密碼變更，修改成功後才允許管理操作
