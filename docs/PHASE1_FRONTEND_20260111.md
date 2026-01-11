# Phase 1 前端整合 - 更新說明

> **更新日期**：2026-01-11  
> **版本**：Phase 1 v4 - 完整功能

---

## 🆕 v4 新增功能

### 1. 管理員減碼
- 管理員點擊「📉 減碼」按鈕可直接減碼
- **不需審核，立即執行**
- 管理員無法退出（需先轉移管理權限）

### 2. 刪除集資
- 當集資**只有管理員一人**時，顯示「🗑️ 刪除集資」按鈕
- 刪除會清除所有相關資料（邀請碼、申請記錄等）
- 需二次確認防止誤刪

### 3. 運作模式選項
- 建立集資時可選擇：
  - 🔄 **彈性模式**（預設）：允許減碼/退出
  - 🔒 **死戰到底**：只進不出

---

## 📋 修改概要

本次更新完成 Phase 1 成員異動功能的前端整合，讓用戶可以在集資詳情頁面申請減碼或退出。

---

## 🆕 新增功能

### 1. 成員異動按鈕（非管理員）

- **位置**：集資詳情頁面，操作按鈕區
- **條件**：僅在「彈性模式」集資中顯示
- **按鈕**：
  - 📉 申請減碼
  - 🚪 申請退出

### 2. 異動申請 Tab（管理員）

- **位置**：集資詳情頁面 Tab 列
- **功能**：顯示所有異動申請，支援審核
- **徽章**：顯示待審核數量

### 3. 我的申請狀態卡片

- **位置**：Info Card 下方
- **顯示**：待審核申請資訊
- **操作**：可取消申請

### 4. 新增 Modal

| Modal | 用途 |
|-------|------|
| reduce-modal | 申請減碼 |
| withdraw-modal | 申請退出 |
| reject-modal | 拒絕申請（管理員） |

---

## 🔧 修改內容

### series-detail.html 修改項目

#### CSS 新增樣式

```css
/* 運作模式徽章 */
.mode-badge { ... }
.mode-fixed { ... }
.mode-flexible { ... }

/* Tab 徽章 */
.tab .badge { ... }

/* 待審核申請卡片 */
.pending-request-card { ... }
.pending-badge { ... }

/* 申請列表 */
.request-list { ... }
.request-item { ... }
.request-type-badge { ... }
.request-status-badge { ... }

/* 新按鈕樣式 */
.btn-success { ... }
.btn-danger { ... }
.btn-warning { ... }
.member-actions { ... }
```

#### JavaScript 新增函數

```javascript
// Phase 1 變數
let pendingRequestsCount = 0;
let myPendingRequest = null;
let currentRejectRequestId = null;

// 初始化
initPhase1()

// 載入函數
loadPendingRequestsCount()
loadMyRequestStatus()
loadRequests()
loadSeriesDetail()

// UI 更新
updateRequestsBadge()
updateMyRequestUI()

// Modal 操作
showReduceModal()
showWithdrawModal()
showRejectModal(requestId)

// 申請操作
submitReduceRequest()
submitWithdrawRequest()
cancelMyRequest(requestId)

// 審核操作（管理員）
approveRequest(requestId)
submitReject()
```

#### HTML 新增區塊

```html
<!-- 我的申請狀態 -->
<div id="my-request-status"></div>

<!-- 成員操作按鈕（非管理員） -->
<div class="member-actions" id="member-action-btns">
    <button>💰 加碼</button>
    <button>📉 申請減碼</button>
    <button>🚪 申請退出</button>
</div>

<!-- 異動申請 Tab -->
<div class="tab" data-tab="requests">異動申請</div>
<div id="tab-requests" class="tab-content"></div>

<!-- 新 Modal -->
<div id="reduce-modal">...</div>
<div id="withdraw-modal">...</div>
<div id="reject-modal">...</div>
```

---

## 📡 API 端點對應

| 功能 | API 端點 | 方法 |
|------|----------|------|
| 申請減碼 | `/v1/member-requests/series/{id}/reduce` | POST |
| 申請退出 | `/v1/member-requests/series/{id}/withdraw` | POST |
| 取消申請 | `/v1/member-requests/{id}/cancel` | POST |
| 我的申請 | `/v1/member-requests/my?series_id={id}` | GET |
| 集資所有申請 | `/v1/member-requests/series/{id}` | GET |
| 審核申請 | `/v1/member-requests/{id}/review` | POST |

---

## ⚠️ 注意事項

### 1. API 預設回傳格式

前端預期 API 回傳格式如下：

```javascript
// GET /v1/member-requests/series/{id}
{
    "requests": [
        {
            "id": 1,
            "user_name": "用戶名",
            "request_type": "reduce" | "withdraw",
            "amount": 500,        // 減碼金額（退出時為 null）
            "pool_share_before": 1000,
            "reason": "原因",
            "status": "pending" | "approved" | "rejected",
            "review_note": "審核備註",
            "created_at": "2026-01-11T10:00:00Z"
        }
    ]
}

// GET /v1/member-requests/my
[
    {
        "id": 1,
        "request_type": "reduce",
        "amount": 500,
        "status": "pending",
        ...
    }
]

// POST /v1/member-requests/{id}/review
{
    "message": "已核准減碼申請"
}
```

### 2. 運作模式判斷

前端透過 `seriesData.withdrawal_policy` 判斷運作模式：

```javascript
const isFlexibleMode = s.withdrawal_policy === 'flexible';
```

- `withdrawal_policy === 'no_withdraw'`：死戰到底模式，不顯示減碼/退出按鈕
- `withdrawal_policy === 'flexible'`：彈性模式，顯示減碼/退出按鈕

⚠️ **注意**：後端 `member_service.py` 目前沒有檢查 `withdrawal_policy`，僅靠前端隱藏按鈕。建議後端也加上檢查。

### 3. 不再需要 member-requests.js

原本計畫引入獨立的 `static/js/member-requests.js`，但已將所有功能整合到 `series-detail.html` 中，避免額外的網路請求和維護複雜度。

---

## 🚀 部署步驟

1. 將 `series-detail.html` 上傳到 Railway 專案的 `static/` 資料夾
2. 確認 API 端點已部署並正常運作
3. 測試流程：
   - 建立彈性模式集資
   - 以成員身份申請減碼/退出
   - 以管理員身份審核申請

---

## ✅ 測試檢查清單

- [ ] 彈性模式集資顯示減碼/退出按鈕
- [ ] 死戰到底模式不顯示減碼/退出按鈕
- [ ] 可成功送出減碼申請
- [ ] 可成功送出退出申請
- [ ] 有待審核申請時隱藏操作按鈕
- [ ] 可取消待審核申請
- [ ] 管理員可看到異動申請 Tab
- [ ] 異動申請 Tab 顯示徽章
- [ ] 管理員可核准申請
- [ ] 管理員可拒絕申請並填寫原因
- [ ] 審核後成員列表更新

---

*SELA 樂透一路發 © 2026*
