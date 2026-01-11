# Phase 1 前端整合指南

## 需要修改的檔案

### 1. static/series-detail.html

#### 1.1 新增 CSS 樣式（在 `<style>` 區塊內添加）

```css
/* ===== Phase 1: 成員異動申請樣式 ===== */

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

.pending-request-info {
    display: flex;
    align-items: center;
    gap: 12px;
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
.member-action-btns {
    display: flex;
    gap: 8px;
    margin-top: 12px;
}

.btn-warning {
    background: var(--warning);
    color: white;
}

.btn-danger {
    background: var(--error);
    color: white;
}

.btn-success {
    background: var(--success);
    color: white;
}

/* 異動申請列表 */
.request-list {
    padding: 0;
}

.request-item {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
}

.request-item:last-child {
    border-bottom: none;
}

.request-item.pending {
    background: rgba(245, 158, 11, 0.05);
}

.request-item.approved {
    background: rgba(22, 163, 74, 0.05);
}

.request-item.rejected {
    background: rgba(220, 38, 38, 0.05);
}

.request-info {
    flex: 1;
}

.request-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.request-user {
    font-weight: 600;
}

.request-type-badge {
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
}

.request-type-badge.reduce {
    background: rgba(37, 99, 235, 0.1);
    color: var(--info);
}

.request-type-badge.withdraw {
    background: rgba(220, 38, 38, 0.1);
    color: var(--error);
}

.request-status-badge {
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
}

.request-status-badge.pending {
    background: rgba(245, 158, 11, 0.1);
    color: var(--warning);
}

.request-status-badge.approved {
    background: rgba(22, 163, 74, 0.1);
    color: var(--success);
}

.request-status-badge.rejected {
    background: rgba(220, 38, 38, 0.1);
    color: var(--error);
}

.request-details {
    font-size: 13px;
    color: var(--text-secondary);
    display: flex;
    gap: 16px;
}

.request-reason {
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 8px;
    font-style: italic;
}

.request-review-note {
    font-size: 13px;
    color: var(--info);
    margin-top: 4px;
}

.request-actions {
    display: flex;
    gap: 8px;
}

/* Tab 徽章 */
.tab .badge {
    background: var(--error);
    color: white;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    margin-left: 6px;
}
```

#### 1.2 在「加碼」按鈕後添加「減碼」和「退出」按鈕

找到這段程式碼：
```javascript
<button class="btn btn-secondary" onclick="showTopupModal()">💰 加碼</button>
```

改為：
```javascript
<button class="btn btn-secondary" onclick="showTopupModal()">💰 加碼</button>
<button class="btn btn-secondary btn-warning" onclick="showReduceModal()">📉 減碼</button>
<button class="btn btn-secondary btn-danger" onclick="showWithdrawModal()">🚪 退出</button>
```

#### 1.3 在 Tabs 中添加「異動申請」Tab（管理員專用）

找到 Tabs 的程式碼：
```javascript
${isAdmin ? '<div class="tab" data-tab="invites">邀請碼</div>' : ''}
```

改為：
```javascript
${isAdmin ? '<div class="tab" data-tab="invites">邀請碼</div>' : ''}
${isAdmin ? '<div class="tab" data-tab="requests">異動申請</div>' : ''}
```

#### 1.4 在 Tab Contents 中添加異動申請容器

找到：
```javascript
${isAdmin ? '<div id="tab-invites" class="tab-content"></div>' : ''}
```

改為：
```javascript
${isAdmin ? '<div id="tab-invites" class="tab-content"></div>' : ''}
${isAdmin ? '<div id="tab-requests" class="tab-content"></div>' : ''}
```

#### 1.5 在我的份額區塊下方添加申請狀態顯示區

在 `info-card` 結束前添加：
```html
<div id="my-request-status"></div>
<div id="member-action-btns" class="member-action-btns" style="display: none;">
    <!-- 按鈕由 JS 動態控制顯示 -->
</div>
```

#### 1.6 添加減碼申請 Modal

在其他 Modal 後面添加：
```html
<!-- 減碼申請 Modal -->
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
                <input type="number" class="form-input" id="reduce-amount" placeholder="輸入減碼金額" min="50" step="50">
                <p class="form-hint">減碼後份額至少需保留 50 元</p>
            </div>
            <div class="form-group">
                <label class="form-label">原因(選填)</label>
                <textarea class="form-input" id="reduce-reason" rows="2" placeholder="說明減碼原因..."></textarea>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal('reduce-modal')">取消</button>
            <button class="btn btn-primary" onclick="submitReduceRequest()">送出申請</button>
        </div>
    </div>
</div>
```

#### 1.7 添加退出申請 Modal

```html
<!-- 退出申請 Modal -->
<div class="modal-overlay" id="withdraw-modal">
    <div class="modal">
        <div class="modal-header">
            <h2 class="modal-title">🚪 申請退出</h2>
            <button class="modal-close" onclick="closeModal('withdraw-modal')">✕</button>
        </div>
        <div class="modal-body">
            <div class="warning-box" style="background: rgba(220, 38, 38, 0.1); border: 1px solid rgba(220, 38, 38, 0.3); border-radius: 10px; padding: 16px; margin-bottom: 20px;">
                <p style="color: var(--error); font-weight: 600; margin-bottom: 8px;">⚠️ 注意事項</p>
                <ul style="color: var(--text-secondary); font-size: 14px; padding-left: 20px; margin: 0;">
                    <li>退出後將結清您在此集資的所有份額</li>
                    <li>進行中的期數可能需要等待結算後才能退款</li>
                    <li>退出需經管理員審核</li>
                </ul>
            </div>
            <div class="form-group">
                <label class="form-label">將退還金額</label>
                <div class="info-value" id="withdraw-share-display" style="font-size: 24px; color: var(--sela-orange);">$0</div>
            </div>
            <div class="form-group">
                <label class="form-label">原因(選填)</label>
                <textarea class="form-input" id="withdraw-reason" rows="2" placeholder="說明退出原因..."></textarea>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal('withdraw-modal')">取消</button>
            <button class="btn btn-danger" onclick="submitWithdrawRequest()">確認申請退出</button>
        </div>
    </div>
</div>
```

#### 1.8 添加拒絕原因 Modal（管理員用）

```html
<!-- 拒絕原因 Modal -->
<div class="modal-overlay" id="reject-modal">
    <div class="modal">
        <div class="modal-header">
            <h2 class="modal-title">拒絕申請</h2>
            <button class="modal-close" onclick="closeModal('reject-modal')">✕</button>
        </div>
        <div class="modal-body">
            <div class="form-group">
                <label class="form-label">拒絕原因(選填)</label>
                <textarea class="form-input" id="reject-note" rows="3" placeholder="說明拒絕原因..."></textarea>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal('reject-modal')">取消</button>
            <button class="btn btn-danger" onclick="submitReject()">確認拒絕</button>
        </div>
    </div>
</div>
```

#### 1.9 引入 JavaScript 模組

在 `</body>` 前添加：
```html
<script src="/static/js/member-requests.js"></script>
```

#### 1.10 更新 Tab 切換邏輯

在 Tab 切換的事件處理中添加：
```javascript
if (tab.dataset.tab === 'requests') {
    loadRequests();
}
```

---

## 完整修改後的關鍵程式碼片段

### renderSeriesDetail 函數中的按鈕區塊

```javascript
${isAdmin ? `
<div class="admin-actions">
    <button class="btn btn-primary" onclick="showNewPeriodModal()">🎰 開新期</button>
    <button class="btn btn-secondary" onclick="showInviteModal()">🎫 產生邀請碼</button>
    <button class="btn btn-secondary" onclick="showTopupModal()">💰 加碼</button>
    <button class="btn btn-secondary" style="background: var(--warning); color: white;" onclick="showReduceModal()">📉 減碼</button>
    <button class="btn btn-secondary" style="background: var(--error); color: white;" onclick="showWithdrawModal()">🚪 退出</button>
</div>
` : `
<div class="admin-actions">
    <button class="btn btn-primary" onclick="showTopupModal()">💰 加碼</button>
    <button class="btn btn-secondary" style="background: var(--warning); color: white;" onclick="showReduceModal()">📉 減碼</button>
    <button class="btn btn-secondary" style="background: var(--error); color: white;" onclick="showWithdrawModal()">🚪 退出</button>
</div>
`}

<div id="my-request-status"></div>

<!-- Tabs -->
<div class="tabs">
    <div class="tab active" data-tab="periods">單期團記錄</div>
    <div class="tab" data-tab="members">成員 (${s.member_count})</div>
    ${isAdmin ? '<div class="tab" data-tab="invites">邀請碼</div>' : ''}
    ${isAdmin ? '<div class="tab" data-tab="requests">異動申請</div>' : ''}
</div>

<!-- Tab Contents -->
<div id="tab-periods" class="tab-content active"></div>
<div id="tab-members" class="tab-content"></div>
${isAdmin ? '<div id="tab-invites" class="tab-content"></div>' : ''}
${isAdmin ? '<div id="tab-requests" class="tab-content"></div>' : ''}
```

---

## 部署步驟

1. 複製 `app/models/member_request.py` 到專案
2. 複製 `app/schemas/member_request.py` 到專案
3. 複製 `app/services/member_service.py` 到專案
4. 複製 `app/api/v1/member_requests.py` 到專案
5. 更新 `app/main.py` 註冊新 router
6. 執行 `scripts/migrate_phase1.py` 建立資料表
7. 更新 `static/series-detail.html` 按照上述指南
8. 複製 `static/js/member-requests.js` 到專案
9. 重新部署
