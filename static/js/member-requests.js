/**
 * SELA 樂透一路發 - 成員異動申請模組
 * Phase 1: 減碼、退出功能
 */

// ==================== 全域變數 ====================
let pendingRequestsCount = 0;
let myPendingRequest = null;

// ==================== 載入函數 ====================

/**
 * 載入待審核申請數量（管理員用）
 */
async function loadPendingRequestsCount() {
    if (!isAdmin) return;
    
    try {
        const res = await apiGet(`/member-requests/series/${seriesId}/pending-count`);
        pendingRequestsCount = res.pending_count;
        updateRequestsBadge();
    } catch (e) {
        console.error('Failed to load pending requests count:', e);
    }
}

/**
 * 更新異動申請 Tab 的徽章
 */
function updateRequestsBadge() {
    const tab = document.querySelector('[data-tab="requests"]');
    if (tab && pendingRequestsCount > 0) {
        tab.innerHTML = `異動申請 <span class="badge">${pendingRequestsCount}</span>`;
    }
}

/**
 * 載入我的申請狀態
 */
async function loadMyRequestStatus() {
    try {
        const requests = await apiGet(`/member-requests/my?series_id=${seriesId}`);
        myPendingRequest = requests.find(r => r.status === 'pending');
        updateMyRequestUI();
    } catch (e) {
        console.error('Failed to load my requests:', e);
    }
}

/**
 * 更新我的申請狀態 UI
 */
function updateMyRequestUI() {
    const container = document.getElementById('my-request-status');
    if (!container) return;
    
    if (myPendingRequest) {
        container.innerHTML = `
            <div class="pending-request-card">
                <div class="pending-request-info">
                    <span class="pending-badge">⏳ 待審核</span>
                    <span>${myPendingRequest.request_type_display}申請</span>
                    ${myPendingRequest.amount ? `<span>$${Number(myPendingRequest.amount).toLocaleString()}</span>` : ''}
                </div>
                <button class="btn btn-sm btn-secondary" onclick="cancelMyRequest(${myPendingRequest.id})">取消申請</button>
            </div>
        `;
        // 隱藏減碼退出按鈕
        const actionBtns = document.getElementById('member-action-btns');
        if (actionBtns) actionBtns.style.display = 'none';
    } else {
        container.innerHTML = '';
        const actionBtns = document.getElementById('member-action-btns');
        if (actionBtns) actionBtns.style.display = 'flex';
    }
}

/**
 * 載入異動申請列表（管理員用）
 */
async function loadRequests() {
    const container = document.getElementById('tab-requests');
    if (!container) return;
    
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    try {
        const data = await apiGet(`/member-requests/series/${seriesId}`);
        
        if (data.requests.length === 0) {
            container.innerHTML = `
                <div class="section">
                    <div class="empty-state">
                        <div class="empty-icon">📋</div>
                        <p class="empty-text">目前沒有異動申請</p>
                    </div>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `
            <div class="section">
                <div class="request-list">
                    ${data.requests.map(r => `
                        <div class="request-item ${r.status}">
                            <div class="request-info">
                                <div class="request-header">
                                    <span class="request-user">${r.user_name}</span>
                                    <span class="request-type-badge ${r.request_type}">${r.request_type_display}</span>
                                    <span class="request-status-badge ${r.status}">${r.status_display}</span>
                                </div>
                                <div class="request-details">
                                    ${r.amount ? `<span>金額: $${Number(r.amount).toLocaleString()}</span>` : '<span>全額退出</span>'}
                                    <span>份額: $${Number(r.pool_share_before).toLocaleString()}</span>
                                    <span>${new Date(r.created_at).toLocaleDateString()}</span>
                                </div>
                                ${r.reason ? `<div class="request-reason">原因: ${r.reason}</div>` : ''}
                                ${r.review_note ? `<div class="request-review-note">審核備註: ${r.review_note}</div>` : ''}
                            </div>
                            ${r.status === 'pending' ? `
                                <div class="request-actions">
                                    <button class="btn btn-sm btn-success" onclick="approveRequest(${r.id})">✓ 核准</button>
                                    <button class="btn btn-sm btn-danger" onclick="showRejectModal(${r.id})">✕ 拒絕</button>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } catch (e) {
        container.innerHTML = `<div class="empty-state"><p class="empty-text">載入失敗: ${e.message}</p></div>`;
    }
}

// ==================== 申請操作 ====================

/**
 * 顯示減碼申請 Modal
 */
function showReduceModal() {
    if (myPendingRequest) {
        showToast('您已有待審核的申請', 'error');
        return;
    }
    document.getElementById('reduce-modal').classList.add('active');
}

/**
 * 顯示退出申請 Modal
 */
function showWithdrawModal() {
    if (myPendingRequest) {
        showToast('您已有待審核的申請', 'error');
        return;
    }
    // 顯示確認資訊
    const myShare = currentSeries?.my_pool_share || 0;
    document.getElementById('withdraw-share-display').textContent = `$${Number(myShare).toLocaleString()}`;
    document.getElementById('withdraw-modal').classList.add('active');
}

/**
 * 提交減碼申請
 */
async function submitReduceRequest() {
    const amount = parseFloat(document.getElementById('reduce-amount').value);
    const reason = document.getElementById('reduce-reason').value.trim();
    
    if (!amount || amount <= 0) {
        showToast('請輸入減碼金額', 'error');
        return;
    }
    
    try {
        await apiPost(`/member-requests/series/${seriesId}/reduce`, {
            amount: amount,
            reason: reason || null
        });
        
        closeModal('reduce-modal');
        showToast('減碼申請已送出，等待管理員審核', 'success');
        
        // 重新載入狀態
        loadMyRequestStatus();
        loadSeriesDetail();
        
        // 清空表單
        document.getElementById('reduce-amount').value = '';
        document.getElementById('reduce-reason').value = '';
    } catch (e) {
        showToast(e.message, 'error');
    }
}

/**
 * 提交退出申請
 */
async function submitWithdrawRequest() {
    const reason = document.getElementById('withdraw-reason').value.trim();
    
    // 確認對話框
    if (!confirm('確定要申請退出此集資嗎？此操作需經管理員審核。')) {
        return;
    }
    
    try {
        await apiPost(`/member-requests/series/${seriesId}/withdraw`, {
            reason: reason || null
        });
        
        closeModal('withdraw-modal');
        showToast('退出申請已送出，等待管理員審核', 'success');
        
        // 重新載入狀態
        loadMyRequestStatus();
        loadSeriesDetail();
        
        // 清空表單
        document.getElementById('withdraw-reason').value = '';
    } catch (e) {
        showToast(e.message, 'error');
    }
}

/**
 * 取消我的申請
 */
async function cancelMyRequest(requestId) {
    if (!confirm('確定要取消此申請嗎？')) {
        return;
    }
    
    try {
        await apiPost(`/member-requests/${requestId}/cancel`, {});
        showToast('申請已取消', 'success');
        myPendingRequest = null;
        updateMyRequestUI();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// ==================== 審核操作（管理員） ====================

/**
 * 核准申請
 */
async function approveRequest(requestId) {
    if (!confirm('確定要核准此申請嗎？核准後將立即執行減碼/退出。')) {
        return;
    }
    
    try {
        const res = await apiPost(`/member-requests/${requestId}/review`, {
            approved: true,
            note: null
        });
        
        showToast(res.message, 'success');
        loadRequests();
        loadPendingRequestsCount();
        loadSeriesDetail();
        loadMembers();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

/**
 * 顯示拒絕原因輸入框
 */
function showRejectModal(requestId) {
    currentRejectRequestId = requestId;
    document.getElementById('reject-note').value = '';
    document.getElementById('reject-modal').classList.add('active');
}

let currentRejectRequestId = null;

/**
 * 提交拒絕
 */
async function submitReject() {
    const note = document.getElementById('reject-note').value.trim();
    
    try {
        await apiPost(`/member-requests/${currentRejectRequestId}/review`, {
            approved: false,
            note: note || null
        });
        
        closeModal('reject-modal');
        showToast('已拒絕此申請', 'success');
        loadRequests();
        loadPendingRequestsCount();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// ==================== 初始化 ====================

/**
 * Phase 1 初始化
 */
function initPhase1() {
    loadMyRequestStatus();
    if (isAdmin) {
        loadPendingRequestsCount();
    }
}

// 在頁面載入後執行
document.addEventListener('DOMContentLoaded', function() {
    // 等待主要內容載入後再初始化 Phase 1
    setTimeout(initPhase1, 500);
});
