# 實驗室監控系統正式變更提案

## Why

現有工安監控原型尚缺少可追溯的會員審核、完整管理操作與一致的身分防護。將歸檔需求正式納入 OpenSpec，補齊可驗收的核心流程，避免以示範資料或編譯成功誤認功能完成。

## What Changes

- 建立一般使用者與管理者註冊、核准後登入、停用後失效及預設管理者密碼變更流程。
- 新增會員審核歷程，記錄操作者、時間及狀態變更。
- 提供實驗室與攝影機資源管理、工安警示處理、稽核建立與改善追蹤。
- 將首頁與管理者儀表板統一為繁體中文離線 Vue、Axios、Bootstrap、SweetAlert2 與 Tailwind 介面。
- 以 SQLite migration 保留既有會員與監控資料，保留舊行事曆資料；沿用現有 CAM 功能並進行回歸驗證。
- 不新增真實影像辨識、錄影、通知服務或 RTSP／WebRTC。

## Capabilities

### New Capabilities

- `member-access`：註冊、核准後登入、Session 授權與預設密碼變更。
- `member-review`：管理者審核、停用及審核歷程。
- `safety-monitoring`：工安首頁、資源管理、警示與儀表板。
- `safety-audits`：稽核紀錄建立、改善期限與狀態追蹤。
- `offline-web`：離線前端技術棧、繁體中文、RWD 與玻璃霧面風格。

### Modified Capabilities

無。`openspec list --specs` 確認目前沒有正式主規格；已有程式不代表已有 OpenSpec capability。

## Impact

影響 `app/controllers`、`app/services`、`app/repositories`、SQLite schema、模板、前端建置、測試及操作文件。補齊 `/api/v1/auth/login`、會員審核、警示與稽核 API，讓監控資料存取受已核准帳號保護。現有資料庫 `instance/calendar.sqlite` 與 `/video` 保留，Docker 與 CAM 設備傳入另按既有操作限制驗證。

來源：`changes/archive/2026-10-06-lab-monitoring/spec.md` 與其歸檔紀錄。原始歸檔完整保留。本變更所有任務需逐項實作及驗證，不預先標記完成。
