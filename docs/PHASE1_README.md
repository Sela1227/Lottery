# Phase 1：成員異動功能 - 開發說明

> **版本**：1.0.0  
> **日期**：2026-01-11  
> **預估工時**：3-4 天

---

## 📋 功能概述

Phase 1 實現成員的減碼和退出功能，採用**彈性模式**（所有集資都支援減碼/退出）。

### 功能列表

| 功能 | 說明 | 權限 |
|------|------|------|
| 申請減碼 | 成員申請減少份額 | 一般成員 |
| 申請退出 | 成員申請退出集資 | 一般成員（非管理員） |
| 取消申請 | 申請人取消自己的申請 | 申請人 |
| 審核申請 | 管理員審核減碼/退出申請 | 集資管理員 |

### 業務規則

1. **減碼限制**
   - 減碼金額必須大於 0
   - 減碼後份額至少保留 50 元
   - 同時只能有一個待審核申請

2. **退出限制**
   - 集資管理員無法退出（需先轉移權限）
   - 退出將結清所有份額
   - 同時只能有一個待審核申請

3. **審核流程**
   - 核准後立即執行減碼/退出
   - 自動記錄帳本
   - 自動更新集資資金池

---

## 📁 檔案清單

### 新增檔案

```
app/
├── models/
│   └── member_request.py      # 異動申請 Model
├── schemas/
│   └── member_request.py      # 異動申請 Schema
├── api/v1/
│   └── member_requests.py     # 異動申請 API
├── services/
│   └── member_service.py      # 成員服務

scripts/
└── migrate_phase1.py          # Phase 1 資料庫遷移

static/
└── js/
    └── member-requests.js     # 前端 JavaScript 模組

docs/
├── PHASE1_README.md           # 本文件
└── PHASE1_FRONTEND_GUIDE.md   # 前端整合指南
```

### 需修改檔案

```
app/
└── main.py                    # 註冊新 router

static/
└── series-detail.html         # 添加減碼/退出 UI
```

---

## 🗄️ 資料庫設計

### member_requests 表

```sql
CREATE TABLE member_requests (
    id SERIAL PRIMARY KEY,
    series_id INTEGER NOT NULL REFERENCES group_series(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    request_type VARCHAR(20) NOT NULL,      -- 'reduce' | 'withdraw'
    amount NUMERIC(14, 2),                  -- 減碼金額（退出時為 NULL）
    pool_share_before NUMERIC(14, 2) NOT NULL,  -- 申請時的份額
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending/approved/rejected/cancelled
    reason TEXT,                            -- 申請原因
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_note TEXT,                       -- 審核備註
    actual_amount NUMERIC(14, 2),           -- 實際執行金額
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_member_requests_series ON member_requests(series_id);
CREATE INDEX idx_member_requests_user ON member_requests(user_id);
CREATE INDEX idx_member_requests_status ON member_requests(status);
```

---

## 🔌 API 端點

### 成員端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/v1/member-requests/series/{id}/reduce` | 申請減碼 |
| POST | `/api/v1/member-requests/series/{id}/withdraw` | 申請退出 |
| POST | `/api/v1/member-requests/{id}/cancel` | 取消申請 |
| GET | `/api/v1/member-requests/my` | 取得我的申請 |

### 管理員端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/member-requests/series/{id}` | 取得集資的所有申請 |
| GET | `/api/v1/member-requests/series/{id}/pending-count` | 取得待審核數量 |
| POST | `/api/v1/member-requests/{id}/review` | 審核申請 |

### 請求/回應範例

#### 申請減碼
```http
POST /api/v1/member-requests/series/1/reduce
Content-Type: application/json
Authorization: Bearer <token>

{
    "amount": 500,
    "reason": "資金調度需要"
}
```

#### 審核申請
```http
POST /api/v1/member-requests/1/review
Content-Type: application/json
Authorization: Bearer <token>

{
    "approved": true,
    "note": "已確認"
}
```

---

## 📊 帳本記錄

### 減碼記錄
```
transaction_type: POOL_WITHDRAW
amount: -500 (負數)
balance_after: 新份額
reference_type: member_request
reference_id: 申請 ID
note: "減碼申請 #1"
```

### 退出記錄
```
transaction_type: POOL_EXIT
amount: -全額 (負數)
balance_after: 0
reference_type: member_request
reference_id: 申請 ID
note: "退出申請 #1"
```

---

## 🚀 部署步驟

### 1. 複製檔案

```bash
# 複製 Model
cp phase1/app/models/member_request.py app/models/

# 複製 Schema
cp phase1/app/schemas/member_request.py app/schemas/

# 複製 Service
cp phase1/app/services/member_service.py app/services/

# 複製 API
cp phase1/app/api/v1/member_requests.py app/api/v1/

# 複製 Migration
cp phase1/scripts/migrate_phase1.py scripts/

# 複製 JS
mkdir -p static/js
cp phase1/static/js/member-requests.js static/js/
```

### 2. 更新 app/main.py

添加：
```python
from app.api.v1.member_requests import router as member_requests_router

# 在 include_router 區塊添加：
application.include_router(member_requests_router, prefix="/v1")
```

### 3. 更新前端

按照 `PHASE1_FRONTEND_GUIDE.md` 修改 `static/series-detail.html`

### 4. 執行遷移

```bash
python scripts/migrate_phase1.py
```

### 5. 重新部署

Railway 會自動重建並部署

---

## ✅ 測試驗證

### 1. 減碼功能
- [ ] 進入集資詳情頁面
- [ ] 點擊「減碼」按鈕
- [ ] 輸入金額，送出申請
- [ ] 確認申請狀態顯示「待審核」
- [ ] （管理員）進入異動申請 Tab
- [ ] 核准申請
- [ ] 確認份額已減少
- [ ] 確認帳本有記錄

### 2. 退出功能
- [ ] 進入集資詳情頁面
- [ ] 點擊「退出」按鈕
- [ ] 確認警告訊息
- [ ] 送出申請
- [ ] （管理員）核准申請
- [ ] 確認成員已退出
- [ ] 確認帳本有記錄

### 3. 取消功能
- [ ] 申請減碼
- [ ] 點擊「取消申請」
- [ ] 確認申請已取消
- [ ] 確認可以重新申請

### 4. 拒絕功能
- [ ] 申請減碼
- [ ] （管理員）點擊「拒絕」
- [ ] 輸入原因
- [ ] 確認申請已拒絕
- [ ] 確認可以重新申請

---

## 📝 注意事項

1. **進行中的期數**
   - 如果有進行中的期數，退出時資金可能被鎖定
   - 需等待期數結算後才能完全退出
   - 目前版本不處理此情況，建議在期數結算後再處理退出

2. **管理員轉移**
   - 管理員無法退出
   - 需先使用「轉移管理權限」功能（待開發）
   - 目前可由系統管理員手動調整

3. **併發問題**
   - 使用資料庫層級的檢查防止重複申請
   - 審核時會重新檢查成員狀態

---

*SELA 樂透一路發 © 2026*
