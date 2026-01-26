/**
 * SELA 樂透一路發 - 共用 JavaScript
 * 統一管理 API 呼叫、認證、Toast 提示等共用功能
 */

// ==================== 設定 ====================
const API_BASE = '/api/v1';

// ==================== 認證相關 ====================

/**
 * 取得 Token
 */
function getToken() {
    return localStorage.getItem('access_token');
}

/**
 * 檢查是否已登入，未登入則跳轉首頁
 * @returns {boolean}
 */
async function checkAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = '/';
        return false;
    }
    return true;
}

/**
 * 登出
 */
function logout() {
    if (confirm('確定要登出嗎？')) {
        localStorage.removeItem('access_token');
        window.location.href = '/';
    }
}

// ==================== API 呼叫 ====================

/**
 * GET 請求
 * @param {string} url - API 路徑（不含 /api/v1）
 * @returns {Promise<any>}
 */
async function apiGet(url) {
    const token = getToken();
    const res = await fetch(`${API_BASE}${url}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) {
        if (res.status === 401) {
            window.location.href = '/';
            return null;
        }
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || `API Error: ${res.status}`);
    }
    return res.json();
}

/**
 * POST 請求
 * @param {string} url - API 路徑
 * @param {object} data - 請求資料
 * @returns {Promise<any>}
 */
async function apiPost(url, data = {}) {
    const token = getToken();
    const res = await fetch(`${API_BASE}${url}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        if (res.status === 401) {
            window.location.href = '/';
            return null;
        }
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || `API Error: ${res.status}`);
    }
    return res.json();
}

/**
 * PUT 請求
 * @param {string} url - API 路徑
 * @param {object} data - 請求資料
 * @returns {Promise<any>}
 */
async function apiPut(url, data = {}) {
    const token = getToken();
    const res = await fetch(`${API_BASE}${url}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        if (res.status === 401) {
            window.location.href = '/';
            return null;
        }
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || `API Error: ${res.status}`);
    }
    return res.json();
}

/**
 * DELETE 請求
 * @param {string} url - API 路徑
 * @returns {Promise<any>}
 */
async function apiDelete(url) {
    const token = getToken();
    const res = await fetch(`${API_BASE}${url}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) {
        if (res.status === 401) {
            window.location.href = '/';
            return null;
        }
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || `API Error: ${res.status}`);
    }
    return res.json();
}

// ==================== Toast 提示 ====================

/**
 * 顯示 Toast 提示訊息
 * @param {string} message - 訊息內容
 * @param {string} type - 類型：'success' | 'error' | 'warning' | 'info'
 * @param {number} duration - 顯示時間（毫秒），預設 3000
 */
function showToast(message, type = 'info', duration = 3000) {
    // 嘗試找現有的 toast 元素
    let toast = document.getElementById('toast');
    
    // 如果沒有，動態建立
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

// ==================== 格式化工具 ====================

/**
 * 格式化金額顯示
 * @param {number} amount - 金額
 * @returns {string}
 */
function formatMoney(amount) {
    if (amount === null || amount === undefined) return '-';
    return amount.toLocaleString('zh-TW');
}

/**
 * 格式化日期顯示
 * @param {string} dateStr - ISO 日期字串
 * @param {boolean} showTime - 是否顯示時間
 * @returns {string}
 */
function formatDate(dateStr, showTime = false) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    };
    if (showTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }
    return date.toLocaleDateString('zh-TW', options);
}

/**
 * 格式化相對時間
 * @param {string} dateStr - ISO 日期字串
 * @returns {string}
 */
function formatRelativeTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return '剛剛';
    if (minutes < 60) return `${minutes} 分鐘前`;
    if (hours < 24) return `${hours} 小時前`;
    if (days < 7) return `${days} 天前`;
    
    return formatDate(dateStr);
}

// ==================== 彩種相關 ====================

/**
 * 彩種名稱對照
 */
const LOTTERY_NAMES = {
    'power': '威力彩',
    'super': '大樂透',
    'daily539': '今彩539'
};

/**
 * 取得彩種中文名稱
 * @param {string} type - 彩種代碼
 * @returns {string}
 */
function getLotteryName(type) {
    return LOTTERY_NAMES[type] || type;
}

/**
 * 彩種顏色對照
 */
const LOTTERY_COLORS = {
    'power': '#E53935',
    'super': '#1E88E5',
    'daily539': '#43A047'
};

/**
 * 取得彩種顏色
 * @param {string} type - 彩種代碼
 * @returns {string}
 */
function getLotteryColor(type) {
    return LOTTERY_COLORS[type] || '#666';
}

// ==================== 狀態相關 ====================

/**
 * 團狀態中文對照
 */
const GROUP_STATUS = {
    'preparing': '準備中',
    'open': '開放中',
    'closed': '已截止',
    'drawn': '已開獎',
    'settled': '已結算'
};

/**
 * 取得團狀態中文
 * @param {string} status
 * @returns {string}
 */
function getGroupStatus(status) {
    return GROUP_STATUS[status] || status;
}

/**
 * 交易類型中文對照
 */
const TRANSACTION_TYPES = {
    'contribution': '投注',
    'refund': '退款',
    'prize': '中獎',
    'carryover_in': '結轉轉入',
    'carryover_out': '結轉轉出',
    'deposit': '儲值',
    'withdraw': '提領',
    'transfer_in': '轉入',
    'transfer_out': '轉出',
    'adjustment': '調整'
};

/**
 * 取得交易類型中文
 * @param {string} type
 * @returns {string}
 */
function getTransactionType(type) {
    return TRANSACTION_TYPES[type] || type;
}

// ==================== DOM 工具 ====================

/**
 * 安全取得 DOM 元素
 * @param {string} id - 元素 ID
 * @returns {HTMLElement|null}
 */
function $(id) {
    return document.getElementById(id);
}

/**
 * 設定元素內容
 * @param {string} id - 元素 ID
 * @param {string} content - 內容
 */
function setText(id, content) {
    const el = $(id);
    if (el) el.textContent = content;
}

/**
 * 設定元素 HTML
 * @param {string} id - 元素 ID
 * @param {string} html - HTML 內容
 */
function setHtml(id, html) {
    const el = $(id);
    if (el) el.innerHTML = html;
}

/**
 * 顯示/隱藏元素
 * @param {string} id - 元素 ID
 * @param {boolean} show - 是否顯示
 */
function setVisible(id, show) {
    const el = $(id);
    if (el) el.style.display = show ? '' : 'none';
}

// ==================== Loading 狀態 ====================

/**
 * 顯示載入中
 * @param {string} containerId - 容器元素 ID
 */
function showLoading(containerId) {
    const container = $(containerId);
    if (container) {
        container.innerHTML = `
            <div class="loading">
                <div class="loading-spinner"></div>
            </div>
        `;
    }
}

/**
 * 顯示空狀態
 * @param {string} containerId - 容器元素 ID
 * @param {string} message - 訊息
 * @param {string} icon - 圖示 emoji
 */
function showEmpty(containerId, message = '暫無資料', icon = '📭') {
    const container = $(containerId);
    if (container) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">${icon}</div>
                <div class="empty-state-text">${message}</div>
            </div>
        `;
    }
}

/**
 * 顯示錯誤狀態
 * @param {string} containerId - 容器元素 ID
 * @param {string} message - 錯誤訊息
 */
function showError(containerId, message = '載入失敗') {
    const container = $(containerId);
    if (container) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">❌</div>
                <div class="empty-state-text">${message}</div>
            </div>
        `;
    }
}

// ==================== 裝置偵測 ====================

/**
 * 取得裝置名稱
 * @returns {string}
 */
function getDeviceName() {
    const ua = navigator.userAgent;
    if (/iPhone|iPad|iPod/.test(ua)) return 'iPhone/iPad';
    if (/Android/.test(ua)) return 'Android';
    if (/Windows/.test(ua)) return 'Windows';
    if (/Mac/.test(ua)) return 'Mac';
    return '未知裝置';
}

/**
 * 是否為行動裝置
 * @returns {boolean}
 */
function isMobile() {
    return /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
}

// ==================== URL 工具 ====================

/**
 * 取得 URL 參數
 * @param {string} name - 參數名稱
 * @returns {string|null}
 */
function getUrlParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

/**
 * 取得 URL 路徑中的 ID
 * 例如 /group/123 => 123
 * @returns {string|null}
 */
function getPathId() {
    const parts = window.location.pathname.split('/');
    return parts[parts.length - 1] || null;
}

console.log('✅ SELA common.js loaded');
