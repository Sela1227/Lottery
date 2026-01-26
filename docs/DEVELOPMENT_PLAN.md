# SELA 樂透一路發 - 待開發功能計劃表

> **版本**：1.1.0  
> **更新日期**：2026-01-11  
> **目前完成度**：約 60%

---

## 📊 總覽

| 階段 | 主題 | 功能數 | 預估工時 | 優先級 |
|:----:|------|:------:|:--------:|:------:|
| Phase 1 | 成員異動與模式設定 | 4 | 3-4 天 | 🔥 高 |
| Phase 2 | 個人彩券系統 | 5 | 4-5 天 | 🔥 高 |
| Phase 3 | 錢包與金流管理 | 6 | 5-6 天 | ⚡ 中 |
| Phase 4 | 匯出與進階功能 | 4 | 3-4 天 | 📋 低 |

---

## Phase 1：成員異動與模式設定

> **目標**：完善成員管理機制，支援彈性進出

### 1.1 運作模式設定

| 項目 | 說明 |
|------|------|
| **功能** | 集資建立時選擇運作模式 |
| **模式 A** | 🔒 死戰到底：只進不出，資金持續累積 |
| **模式 B** | 🔄 彈性模式：允許減碼或退出（需審核） |
| **影響範圍** | series 表新增 `mode` 欄位 |

**資料庫變更**
```sql
ALTER TABLE group_series ADD COLUMN mode VARCHAR(20) DEFAULT 'flexible';
-- 'fixed' = 死戰到底, 'flexible' = 彈性模式
```

**前端變更**
- series.html：建立集資時新增模式選擇
- series-detail.html：顯示目前模式

---

### 1.2 加碼功能（已有，需優化）

| 項目 | 說明 |
|------|------|
| **現狀** | 基本功能已實作 |
| **優化** | 加入付款憑證上傳、審核流程 |

---

### 1.3 減碼申請（🆕 新功能）

| 項目 | 說明 |
|------|------|
| **功能** | 成員申請減少份額 |
| **條件** | 僅「彈性模式」集資可用 |
| **流程** | 申請 → 管理員審核 → 執行減碼 → 記錄帳本 |
| **限制** | 不可減至 0（需用退出功能） |

**API 端點**
```
POST /api/v1/series/{id}/members/reduce
{
    "amount": 500,
    "reason": "資金調度"
}
```

**資料庫變更**
```sql
CREATE TABLE member_requests (
    id SERIAL PRIMARY KEY,
    series_id INTEGER REFERENCES group_series(id),
    user_id INTEGER REFERENCES users(id),
    request_type VARCHAR(20),  -- 'reduce', 'withdraw'
    amount DECIMAL(12,2),
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 1.4 退出申請（🆕 新功能）

| 項目 | 說明 |
|------|------|
| **功能** | 成員申請退出集資 |
| **條件** | 僅「彈性模式」集資可用 |
| **流程** | 申請 → 管理員審核 → 結算份額 → 移除成員 |
| **結算** | 退還目前份額金額（扣除進行中期數的鎖定金額） |

**API 端點**
```
POST /api/v1/series/{id}/members/withdraw
{
    "reason": "個人因素退出"
}
```

---

### 1.5 Phase 1 檔案清單

```
app/
├── models/
│   └── member_request.py      # 🆕 異動申請 Model
├── schemas/
│   └── member_request.py      # 🆕 異動申請 Schema
├── api/v1/
│   └── member_requests.py     # 🆕 異動申請 API
├── services/
│   └── member_service.py      # 🆕 成員服務（減碼/退出邏輯）
scripts/
└── migrate.py                 # 更新：新增表結構

static/
├── series.html                # 更新：建立時選擇模式
├── series-detail.html         # 更新：顯示模式、異動申請入口
└── member-requests.html       # 🆕 異動申請管理頁面
```

---

## Phase 2：個人彩券系統

> **目標**：提供完全私密的個人彩券記錄功能

### 2.1 個人彩券記錄（🆕 新功能）

| 項目 | 說明 |
|------|------|
| **功能** | 記錄個人購買的彩券（非團購） |
| **隱私** | 完全私密，僅本人可見 |
| **欄位** | 彩種、期數、號碼、購買金額、購買日期 |

**資料庫設計**
```sql
CREATE TABLE personal_tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    lottery_type VARCHAR(20),      -- power, super, daily539
    draw_term VARCHAR(20),          -- 期數
    numbers JSONB,                  -- 選號
    bet_amount DECIMAL(10,2),       -- 投注金額
    purchase_date DATE,
    prize_amount DECIMAL(12,2),     -- 中獎金額（對獎後填入）
    prize_checked BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 2.2 個人彩券新增

| 項目 | 說明 |
|------|------|
| **功能** | 新增個人彩券記錄 |
| **選號** | 支援手選 / 電腦選號 |
| **批量** | 支援一次新增多組號碼 |

**API 端點**
```
POST /api/v1/personal/tickets
{
    "lottery_type": "power",
    "draw_term": "113115",
    "numbers": [
        {"first_zone": [1,5,12,23,31,38], "second_zone": 3}
    ],
    "bet_amount": 100,
    "purchase_date": "2026-01-11"
}
```

---

### 2.3 個人彩券對獎

| 項目 | 說明 |
|------|------|
| **功能** | 自動比對開獎號碼 |
| **觸發** | 開獎後自動對獎 / 手動觸發 |
| **結果** | 顯示中獎等級、獎金金額 |

**API 端點**
```
POST /api/v1/personal/tickets/{id}/check
GET /api/v1/personal/tickets/check-all?draw_term=113115
```

---

### 2.4 個人彩券統計

| 項目 | 說明 |
|------|------|
| **功能** | 個人投注統計分析 |
| **指標** | 總投注、總中獎、投報率、常選號碼 |

**API 端點**
```
GET /api/v1/personal/statistics
```

---

### 2.5 個人彩券列表與篩選

| 項目 | 說明 |
|------|------|
| **功能** | 查看所有個人彩券記錄 |
| **篩選** | 彩種、期數範圍、中獎狀態 |
| **排序** | 日期、金額 |

---

### 2.6 Phase 2 檔案清單

```
app/
├── models/
│   └── personal_ticket.py     # 🆕 個人彩券 Model
├── schemas/
│   └── personal_ticket.py     # 🆕 個人彩券 Schema
├── api/v1/
│   └── personal.py            # 更新：完整實作 API
├── services/
│   └── personal_service.py    # 🆕 個人彩券服務

static/
└── personal.html              # 更新：完整實作頁面
    ├── 彩券列表
    ├── 新增彩券 Modal
    ├── 對獎結果顯示
    └── 個人統計區塊
```

---

## Phase 3：錢包與金流管理

> **目標**：完善錢包功能，支援充值與提領

### 3.1 錢包餘額系統（優化現有）

| 項目 | 說明 |
|------|------|
| **現狀** | 基本顯示已實作 |
| **優化** | 區分「可用餘額」與「鎖定金額」 |

**餘額類型**
- **可用餘額**：可提領或轉移的金額
- **鎖定金額**：進行中期數的投注金額
- **集資份額**：各集資中的份額總和

---

### 3.2 銀行帳戶管理（🆕 新功能）

| 項目 | 說明 |
|------|------|
| **功能** | 用戶綁定銀行帳戶 |
| **欄位** | 銀行代碼、分行、帳號、戶名 |
| **用途** | 提領時使用 |
| **限制** | 每人最多綁定 3 個帳戶 |

**資料庫設計**
```sql
CREATE TABLE bank_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    bank_code VARCHAR(10),          -- 銀行代碼
    bank_name VARCHAR(50),          -- 銀行名稱
    branch_name VARCHAR(50),        -- 分行名稱
    account_number VARCHAR(20),     -- 帳號（加密儲存）
    account_name VARCHAR(50),       -- 戶名
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 3.3 充值功能（🆕 新功能）

| 項目 | 說明 |
|------|------|
| **功能** | 用戶申請充值到錢包 |
| **流程** | 申請 → 轉帳 → 上傳憑證 → 管理員審核 → 入帳 |
| **收款帳戶** | 系統設定的收款銀行帳戶 |

**資料庫設計**
```sql
CREATE TABLE wallet_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(20),               -- deposit, withdraw, transfer
    amount DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'pending',
    proof_image_url TEXT,           -- 憑證圖片
    bank_account_id INTEGER,        -- 提領用
    admin_note TEXT,
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**API 端點**
```
POST /api/v1/wallet/deposit
{
    "amount": 1000,
    "proof_image_url": "https://..."
}
```

---

### 3.4 提領功能（🆕 新功能）

| 項目 | 說明 |
|------|------|
| **功能** | 用戶申請提領錢包餘額 |
| **流程** | 申請 → 管理員審核 → 轉帳 → 完成 |
| **條件** | 餘額足夠、已綁定銀行帳戶 |
| **限制** | 單次最低 100 元 |

**API 端點**
```
POST /api/v1/wallet/withdraw
{
    "amount": 500,
    "bank_account_id": 1
}
```

---

### 3.5 轉帳功能（🆕 新功能）

| 項目 | 說明 |
|------|------|
| **功能** | 錢包餘額轉入集資份額 |
| **流程** | 選擇集資 → 輸入金額 → 即時轉入 |
| **反向** | 集資份額轉回錢包（需審核） |

---

### 3.6 交易記錄查詢

| 項目 | 說明 |
|------|------|
| **功能** | 查看所有錢包交易記錄 |
| **類型** | 充值、提領、轉帳、獎金入帳 |
| **篩選** | 類型、日期範圍、狀態 |

---

### 3.7 Phase 3 檔案清單

```
app/
├── models/
│   ├── bank_account.py        # 🆕 銀行帳戶 Model
│   └── wallet_transaction.py  # 🆕 錢包交易 Model
├── schemas/
│   ├── bank_account.py        # 🆕 銀行帳戶 Schema
│   └── wallet_transaction.py  # 🆕 錢包交易 Schema
├── api/v1/
│   └── wallet.py              # 更新：完整實作
├── services/
│   └── wallet_service.py      # 🆕 錢包服務

static/
├── wallet.html                # 更新：完整功能
│   ├── 餘額卡片（可用/鎖定/份額）
│   ├── 充值 Modal
│   ├── 提領 Modal
│   ├── 轉帳 Modal
│   └── 交易記錄列表
├── bank-accounts.html         # 🆕 銀行帳戶管理
└── admin.html                 # 更新：充值/提領審核
```

---

## Phase 4：匯出與進階功能

> **目標**：提供報表匯出與資料備份

### 4.1 結算報告 PDF 匯出（🆕 新功能）

| 項目 | 說明 |
|------|------|
| **功能** | 匯出單期結算明細 PDF |
| **內容** | 期數資訊、成員份額、購買明細、中獎結果、分配明細 |
| **格式** | A4 PDF，含 SELA Logo |

**API 端點**
```
GET /api/v1/groups/{id}/export/pdf
```

**技術方案**
- 使用 `reportlab` 或 `weasyprint` 生成 PDF
- 支援中文字型

---

### 4.2 集資報告 PDF 匯出（🆕 新功能）

| 項目 | 說明 |
|------|------|
| **功能** | 匯出集資完整報告 |
| **內容** | 集資資訊、成員列表、歷史期數、總統計 |
| **範圍** | 可選擇期數範圍 |

**API 端點**
```
GET /api/v1/series/{id}/export/pdf?from_term=113100&to_term=113120
```

---

### 4.3 資料備份匯出（🆕 新功能）

| 項目 | 說明 |
|------|------|
| **功能** | 匯出個人所有資料 |
| **格式** | JSON / CSV 可選 |
| **內容** | 參與集資、交易記錄、個人彩券 |

**API 端點**
```
GET /api/v1/users/me/export?format=json
GET /api/v1/users/me/export?format=csv
```

---

### 4.4 管理員資料匯出（🆕 新功能）

| 項目 | 說明 |
|------|------|
| **功能** | 管理員匯出系統資料 |
| **權限** | 僅系統管理員 |
| **內容** | 用戶列表、集資列表、交易記錄 |

**API 端點**
```
GET /api/v1/admin/export/users
GET /api/v1/admin/export/series
GET /api/v1/admin/export/transactions
```

---

### 4.5 Phase 4 檔案清單

```
app/
├── api/v1/
│   └── export.py              # 🆕 匯出 API
├── services/
│   ├── pdf_service.py         # 🆕 PDF 生成服務
│   └── export_service.py      # 🆕 資料匯出服務
├── templates/
│   ├── settlement_report.html # 🆕 結算報告模板
│   └── series_report.html     # 🆕 集資報告模板

static/
├── series-detail.html         # 更新：新增匯出按鈕
├── group-detail.html          # 更新：新增匯出按鈕
├── settings.html              # 更新：新增資料匯出
└── admin.html                 # 更新：新增管理員匯出

requirements.txt               # 更新：新增 reportlab/weasyprint
```

---

## 📅 開發時程建議

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
| LINE Notify | 不再使用此方案 |
| Web Push | 暫緩開發 |
| 智慧配對轉帳 | 併入 Phase 3 銀行帳戶，簡化實作 |

---

## 📝 資料庫變更總覽

### 新增表格
```sql
-- Phase 1
CREATE TABLE member_requests (...);

-- Phase 2
CREATE TABLE personal_tickets (...);

-- Phase 3
CREATE TABLE bank_accounts (...);
CREATE TABLE wallet_transactions (...);
```

### 修改表格
```sql
-- Phase 1
ALTER TABLE group_series ADD COLUMN mode VARCHAR(20) DEFAULT 'flexible';
```

---

## ✅ 檢查清單

### Phase 1 完成條件
- [ ] 集資可選擇運作模式
- [ ] 彈性模式集資可申請減碼
- [ ] 彈性模式集資可申請退出
- [ ] 管理員可審核異動申請
- [ ] 帳本正確記錄異動

### Phase 2 完成條件
- [ ] 可新增個人彩券記錄
- [ ] 支援手選/電腦選號
- [ ] 可自動對獎
- [ ] 顯示個人統計

### Phase 3 完成條件
- [ ] 可綁定銀行帳戶
- [ ] 可申請充值
- [ ] 可申請提領
- [ ] 管理員可審核充值/提領
- [ ] 交易記錄完整

### Phase 4 完成條件
- [ ] 可匯出結算報告 PDF
- [ ] 可匯出集資報告 PDF
- [ ] 可匯出個人資料
- [ ] 管理員可匯出系統資料

---

*SELA 樂透一路發 © 2026*
