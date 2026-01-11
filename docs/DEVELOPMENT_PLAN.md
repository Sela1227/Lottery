# SELA 樂透一路發 - 待開發功能計劃表

> **版本**：1.2.0  
> **更新日期**：2026-01-11  
> **目前完成度**：約 60%

---

## 📊 總覽

| 階段 | 主題 | 功能數 | 預估工時 | 優先級 | 狀態 |
|:----:|------|:------:|:--------:|:------:|:----:|
| Phase 1 | 成員異動功能 | 3 | 3-4 天 | 🔥 高 | 📦 已備 |
| Phase 2 | 個人彩券系統 | 5 | 4-5 天 | 🔥 高 | ⏳ |
| Phase 3 | 錢包與金流管理 | 6 | 5-6 天 | ⚡ 中 | ⏳ |
| Phase 4 | 匯出與進階功能 | 4 | 3-4 天 | 📋 低 | ⏳ |

---

## Phase 1：成員異動功能 ✅ 開發包已準備

> **目標**：完善成員管理機制，支援減碼與退出  
> **詳細指南**：`docs/PHASE1_GUIDE.md`

### 功能列表

| 功能 | 說明 | 限制 |
|------|------|------|
| 減碼申請 | 成員申請減少份額 | 減碼後至少保留 50 元 |
| 退出申請 | 成員申請退出集資 | 管理員無法退出 |
| 申請審核 | 管理員審核申請 | 核准/拒絕（可填原因） |

### API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/member-requests/series/{id}/reduce` | 申請減碼 |
| POST | `/member-requests/series/{id}/withdraw` | 申請退出 |
| POST | `/member-requests/{id}/cancel` | 取消申請 |
| POST | `/member-requests/{id}/review` | 審核申請 |

---

## Phase 2：個人彩券系統

> **目標**：提供完全私密的個人彩券記錄功能

### 功能列表

| 功能 | 說明 |
|------|------|
| 個人彩券記錄 | 記錄個人購買的彩券（非團購），完全私密 |
| 個人彩券新增 | 手選/電腦選號，支援批量新增 |
| 個人彩券對獎 | 自動/手動對獎，顯示中獎等級與獎金 |
| 個人彩券統計 | 總投注、總中獎、投報率、常選號碼 |
| 個人彩券列表 | 篩選：彩種、期數範圍、中獎狀態 |

### 檔案清單

```
app/models/personal_ticket.py
app/schemas/personal_ticket.py
app/api/v1/personal.py
app/services/personal_service.py
static/personal.html
```

---

## Phase 3：錢包與金流管理

> **目標**：完善錢包功能，支援充值與提領

### 功能列表

| 功能 | 說明 |
|------|------|
| 錢包餘額系統 | 區分「可用餘額」與「鎖定金額」 |
| 銀行帳戶管理 | 用戶綁定銀行帳戶（最多 3 個） |
| 充值功能 | 申請 → 轉帳 → 上傳憑證 → 審核 → 入帳 |
| 提領功能 | 申請 → 審核 → 轉帳 → 完成（最低 100 元） |
| 轉帳功能 | 錢包餘額 ⇄ 集資份額 |
| 交易記錄 | 充值、提領、轉帳、獎金入帳 |

### 檔案清單

```
app/models/bank_account.py
app/models/wallet_transaction.py
app/schemas/bank_account.py
app/schemas/wallet_transaction.py
app/api/v1/wallet.py
app/services/wallet_service.py
static/wallet.html
static/bank-accounts.html
```

---

## Phase 4：匯出與進階功能

> **目標**：提供報表匯出與資料備份

### 功能列表

| 功能 | 說明 |
|------|------|
| 結算報告 PDF | 匯出單期結算明細 |
| 集資報告 PDF | 匯出集資完整報告 |
| 資料備份匯出 | 匯出個人所有資料（JSON/CSV） |
| 管理員資料匯出 | 匯出系統資料（僅管理員） |

### 檔案清單

```
app/api/v1/export.py
app/services/pdf_service.py
app/services/export_service.py
app/templates/settlement_report.html
app/templates/series_report.html
```

---

## 📅 開發時程

| 階段 | 預估時間 | 里程碑 |
|:----:|:--------:|--------|
| Phase 1 | 3-4 天 | 成員異動功能完成 |
| Phase 2 | 4-5 天 | 個人彩券系統上線 |
| Phase 3 | 5-6 天 | 錢包功能完整 |
| Phase 4 | 3-4 天 | 匯出功能完成 |
| **總計** | **15-19 天** | **功能 100% 完成** |

---

## 🗑️ 已移除/暫緩功能

| 功能 | 原因 |
|------|------|
| 死戰到底模式 | 簡化設計，統一為彈性模式 |
| LINE Notify | 2025/3/31 已停止服務 |
| Web Push | 暫緩開發 |

---

## 📝 資料庫變更總覽

### Phase 1
```sql
CREATE TABLE member_requests (...);
```

### Phase 2
```sql
CREATE TABLE personal_tickets (...);
```

### Phase 3
```sql
CREATE TABLE bank_accounts (...);
CREATE TABLE wallet_transactions (...);
```

---

## ✅ 完成條件檢查清單

### Phase 1
- [ ] 可申請減碼
- [ ] 可申請退出
- [ ] 可取消申請
- [ ] 管理員可審核
- [ ] 帳本正確記錄

### Phase 2
- [ ] 可新增個人彩券
- [ ] 支援手選/電腦選號
- [ ] 可自動對獎
- [ ] 顯示個人統計

### Phase 3
- [ ] 可綁定銀行帳戶
- [ ] 可申請充值
- [ ] 可申請提領
- [ ] 交易記錄完整

### Phase 4
- [ ] 可匯出結算報告 PDF
- [ ] 可匯出集資報告 PDF
- [ ] 可匯出個人資料

---

*SELA 樂透一路發 © 2026*
