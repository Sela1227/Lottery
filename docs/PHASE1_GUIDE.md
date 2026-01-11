# Phase 1：成員異動功能開發指南

> **版本**：1.0.0  
> **日期**：2026-01-11  
> **預估工時**：3-4 天  
> **狀態**：📦 開發包已準備

---

## 📋 功能概述

Phase 1 實現成員的減碼和退出功能，採用**彈性模式**（所有集資都支援）。

| 功能 | 說明 | 權限 |
|------|------|------|
| 申請減碼 | 成員申請減少份額 | 一般成員 |
| 申請退出 | 成員申請退出集資 | 一般成員（非管理員） |
| 取消申請 | 申請人取消自己的申請 | 申請人 |
| 審核申請 | 管理員審核減碼/退出申請 | 集資管理員 |

### 業務規則

**減碼限制**
- 減碼金額必須大於 0
- 減碼後份額至少保留 50 元
- 同時只能有一個待審核申請

**退出限制**
- 集資管理員無法退出（需先轉移權限）
- 退出將結清所有份額
- 同時只能有一個待審核申請

**審核流程**
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
└── migrate_phase1.py          # 資料庫遷移

static/js/
└── member-requests.js         # 前端 JavaScript
```

### 需修改檔案

```
app/main.py                    # 註冊新 router
static/series-detail.html      # 添加減碼/退出 UI
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
    pool_share_before NUMERIC(14, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    reason TEXT,
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_note TEXT,
    actual_amount NUMERIC(14, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

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
| GET | `/api/v1/member-requests/my` | 我的申請 |

### 管理員端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/member-requests/series/{id}` | 集資所有申請 |
| GET | `/api/v1/member-requests/series/{id}/pending-count` | 待審核數量 |
| POST | `/api/v1/member-requests/{id}/review` | 審核申請 |

### 請求範例

**申請減碼**
```json
POST /api/v1/member-requests/series/1/reduce
{
    "amount": 500,
    "reason": "資金調度需要"
}
```

**審核申請**
```json
POST /api/v1/member-requests/1/review
{
    "approved": true,
    "note": "已確認"
}
```

---

## 🎨 前端整合

### 1. 新增 CSS 樣式

在 `series-detail.html` 的 `<style>` 區塊添加：

```css
/* 待審核申請卡片 */
.pending-request-card {
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 12px;
    padding: 12px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.pending-badge {
    background: var(--warning);
    color: white;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
}

/* 成員操作按鈕 */
.member-action-btns { display: flex; gap: 8px; margin-top: 12px; }
.btn-warning { background: var(--warning); color: white; }
.btn-danger { background: var(--error); color: white; }
.btn-success { background: var(--success); color: white; }

/* 異動申請列表 */
.request-item {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}
.request-item.pending { background: rgba(245, 158, 11, 0.05); }
.request-item.approved { background: rgba(22, 163, 74, 0.05); }
.request-item.rejected { background: rgba(220, 38, 38, 0.05); }

.request-type-badge.reduce { background: rgba(37, 99, 235, 0.1); color: var(--info); }
.request-type-badge.withdraw { background: rgba(220, 38, 38, 0.1); color: var(--error); }
```

### 2. 添加操作按鈕

在「加碼」按鈕後添加：

```html
<button class="btn btn-secondary btn-warning" onclick="showReduceModal()">📉 減碼</button>
<button class="btn btn-secondary btn-danger" onclick="showWithdrawModal()">🚪 退出</button>
```

### 3. 添加 Tab（管理員專用）

```javascript
${isAdmin ? '<div class="tab" data-tab="requests">異動申請</div>' : ''}
```

### 4. 添加減碼 Modal

```html
<div class="modal-overlay" id="reduce-modal">
    <div class="modal">
        <div class="modal-header">
            <h2 class="modal-title">📉 申請減碼</h2>
            <button class="modal-close" onclick="closeModal('reduce-modal')">✕</button>
        </div>
        <div class="modal-body">
            <div class="form-group">
                <label class="form-label">目前份額</label>
                <div class="info-value" id="reduce-current-share">$0</div>
            </div>
            <div class="form-group">
                <label class="form-label">減碼金額(元)</label>
                <input type="number" class="form-input" id="reduce-amount" min="50" step="50">
                <p class="form-hint">減碼後份額至少需保留 50 元</p>
            </div>
            <div class="form-group">
                <label class="form-label">原因(選填)</label>
                <textarea class="form-input" id="reduce-reason" rows="2"></textarea>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal('reduce-modal')">取消</button>
            <button class="btn btn-primary" onclick="submitReduceRequest()">送出申請</button>
        </div>
    </div>
</div>
```

### 5. 添加退出 Modal

```html
<div class="modal-overlay" id="withdraw-modal">
    <div class="modal">
        <div class="modal-header">
            <h2 class="modal-title">🚪 申請退出</h2>
            <button class="modal-close" onclick="closeModal('withdraw-modal')">✕</button>
        </div>
        <div class="modal-body">
            <div class="warning-box" style="background: rgba(220, 38, 38, 0.1); border: 1px solid rgba(220, 38, 38, 0.3); border-radius: 10px; padding: 16px; margin-bottom: 20px;">
                <p style="color: var(--error); font-weight: 600;">⚠️ 注意事項</p>
                <ul style="color: var(--text-secondary); font-size: 14px; padding-left: 20px;">
                    <li>退出後將結清所有份額</li>
                    <li>進行中的期數需等待結算後才能退款</li>
                    <li>退出需經管理員審核</li>
                </ul>
            </div>
            <div class="form-group">
                <label class="form-label">將退還金額</label>
                <div class="info-value" id="withdraw-share-display" style="font-size: 24px; color: var(--sela-orange);">$0</div>
            </div>
            <div class="form-group">
                <label class="form-label">原因(選填)</label>
                <textarea class="form-input" id="withdraw-reason" rows="2"></textarea>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal('withdraw-modal')">取消</button>
            <button class="btn btn-danger" onclick="submitWithdrawRequest()">確認申請退出</button>
        </div>
    </div>
</div>
```

### 6. 引入 JavaScript

```html
<script src="/static/js/member-requests.js"></script>
```

---

## 📊 帳本記錄格式

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
cp phase1/app/models/member_request.py app/models/
cp phase1/app/schemas/member_request.py app/schemas/
cp phase1/app/services/member_service.py app/services/
cp phase1/app/api/v1/member_requests.py app/api/v1/
cp phase1/scripts/migrate_phase1.py scripts/
mkdir -p static/js && cp phase1/static/js/member-requests.js static/js/
```

### 2. 更新 app/main.py

```python
from app.api.v1.member_requests import router as member_requests_router
application.include_router(member_requests_router, prefix="/v1")
```

### 3. 執行遷移

```bash
python scripts/migrate_phase1.py
```

### 4. 部署

```bash
git add .
git commit -m "feat: Phase 1 成員異動功能"
git push
```

---

## ✅ 測試驗證

### 減碼功能
- [ ] 點擊「減碼」按鈕
- [ ] 輸入金額，送出申請
- [ ] 確認狀態顯示「待審核」
- [ ] 管理員核准申請
- [ ] 確認份額已減少
- [ ] 確認帳本有記錄

### 退出功能
- [ ] 點擊「退出」按鈕
- [ ] 確認警告訊息
- [ ] 送出申請
- [ ] 管理員核准申請
- [ ] 確認成員已退出
- [ ] 確認帳本有記錄

### 取消/拒絕功能
- [ ] 申請後點擊「取消申請」
- [ ] 確認可以重新申請
- [ ] 管理員拒絕申請
- [ ] 確認可以重新申請

---

## ⚠️ 注意事項

1. **進行中的期數**：退出時資金可能被鎖定，需等待結算
2. **管理員轉移**：管理員無法退出，需先轉移權限
3. **併發問題**：使用資料庫層級檢查防止重複申請

---

*SELA 樂透一路發 © 2026*
