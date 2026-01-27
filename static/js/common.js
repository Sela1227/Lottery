/**
 * SELA 樂透一路發 - 共用 JavaScript 模組 v2
 * 修復：防止無限重定向循環（特別是手機/LINE 內建瀏覽器）
 */

const API_BASE = '/api/v1';

// ==================== 防循環重定向機制 ====================

const REDIRECT_KEY = 'sela_redirect_count';
const REDIRECT_TIME_KEY = 'sela_redirect_time';
const MAX_REDIRECTS = 3;
const REDIRECT_RESET_MS = 5000; // 5 秒內超過 3 次重定向視為循環

/**
 * 安全重定向（防止無限循環）
 */
function safeRedirect(url) {
    const now = Date.now();
    const lastTime = parseInt(sessionStorage.getItem(REDIRECT_TIME_KEY) || '0');
    let count = parseInt(sessionStorage.getItem(REDIRECT_KEY) || '0');
    
    // 如果距離上次重定向超過 5 秒，重置計數
    if (now - lastTime > REDIRECT_RESET_MS) {
        count = 0;
    }
    
    count++;
    sessionStorage.setItem(REDIRECT_KEY, count.toString());
    sessionStorage.setItem(REDIRECT_TIME_KEY, now.toString());
    
    if (count > MAX_REDIRECTS) {
        console.error('偵測到重定向循環，已停止');
        sessionStorage.removeItem(REDIRECT_KEY);
        sessionStorage.removeItem(REDIRECT_TIME_KEY);
        // 清除可能有問題的 token
        localStorage.removeItem('access_token');
        // 顯示錯誤而非繼續循環
        document.body.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif;padding:20px;text-align:center;">
                <div style="font-size:48px;margin-bottom:20px;">⚠️</div>
                <h2 style="color:#F26522;margin-bottom:10px;">登入發生問題</h2>
                <p style="color:#666;margin-bottom:20px;">請重新登入或使用外部瀏覽器開啟</p>
                <a href="/" style="background:#F26522;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">返回首頁</a>
            </div>
        `;
        return false;
    }
    
    window.location.href = url;
    return true;
}

/**
 * 清除重定向計數（成功載入頁面後呼叫）
 */
function clearRedirectCount() {
    sessionStorage.removeItem(REDIRECT_KEY);
    sessionStorage.removeItem(REDIRECT_TIME_KEY);
}

// ==================== 工具函數 ====================

const $ = id => document.getElementById(id);

function getToken() {
    try {
        return localStorage.getItem('access_token');
    } catch (e) {
        // 某些瀏覽器可能限制 localStorage 存取
        console.error('無法存取 localStorage:', e);
        return null;
    }
}

function setToken(token) {
    try {
        localStorage.setItem('access_token', token);
        return true;
    } catch (e) {
        console.error('無法寫入 localStorage:', e);
        return false;
    }
}

function removeToken() {
    try {
        localStorage.removeItem('access_token');
    } catch (e) {
        console.error('無法清除 localStorage:', e);
    }
}

// ==================== 認證相關 ====================

/**
 * 檢查登入狀態（同步版本，只檢查 token 存在）
 */
function checkAuth() {
    const token = getToken();
    if (!token) {
        safeRedirect('/');
        return false;
    }
    return true;
}

/**
 * 檢查登入狀態並驗證 token（異步版本）
 * @returns {Promise<Object|null>} 用戶資料或 null
 */
async function checkAuthAndGetUser() {
    const token = getToken();
    if (!token) {
        safeRedirect('/');
        return null;
    }
    
    try {
        const user = await apiGet('/users/me');
        if (user) {
            clearRedirectCount(); // 成功驗證，清除重定向計數
            return user;
        }
        return null;
    } catch (e) {
        console.error('Token 驗證失敗:', e);
        removeToken();
        safeRedirect('/');
        return null;
    }
}

/**
 * 登出
 */
function logout() {
    if (confirm('確定要登出嗎？')) {
        removeToken();
        clearRedirectCount();
        window.location.href = '/';
    }
}

// ==================== API 呼叫 ====================

/**
 * GET 請求
 */
async function apiGet(url) {
    const token = getToken();
    try {
        const res = await fetch(`${API_BASE}${url}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.status === 401) {
            removeToken();
            safeRedirect('/');
            return null;
        }
        
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: '請求失敗' }));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        
        return await res.json();
    } catch (e) {
        if (e.message.includes('Failed to fetch') || e.message.includes('NetworkError')) {
            console.error('網路錯誤:', e);
            throw new Error('網路連線失敗，請檢查網路狀態');
        }
        throw e;
    }
}

/**
 * POST 請求
 */
async function apiPost(url, data) {
    const token = getToken();
    try {
        const res = await fetch(`${API_BASE}${url}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (res.status === 401) {
            removeToken();
            safeRedirect('/');
            return null;
        }
        
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: '請求失敗' }));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        
        return await res.json();
    } catch (e) {
        if (e.message.includes('Failed to fetch') || e.message.includes('NetworkError')) {
            throw new Error('網路連線失敗，請檢查網路狀態');
        }
        throw e;
    }
}

/**
 * PUT 請求
 */
async function apiPut(url, data) {
    const token = getToken();
    const res = await fetch(`${API_BASE}${url}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    
    if (res.status === 401) {
        removeToken();
        safeRedirect('/');
        return null;
    }
    
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '請求失敗' }));
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    
    return await res.json();
}

/**
 * DELETE 請求
 */
async function apiDelete(url) {
    const token = getToken();
    const res = await fetch(`${API_BASE}${url}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (res.status === 401) {
        removeToken();
        safeRedirect('/');
        return null;
    }
    
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '請求失敗' }));
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    
    // DELETE 可能沒有回應 body
    const text = await res.text();
    return text ? JSON.parse(text) : null;
}

// ==================== UI 工具 ====================

/**
 * 顯示 Toast 通知
 */
function showToast(message, type = 'info') {
    // 移除現有的 toast
    const existingToast = document.querySelector('.toast.show');
    if (existingToast) {
        existingToast.classList.remove('show');
    }
    
    let toast = $('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    
    toast.textContent = message;
    toast.className = `toast ${type}`;
    
    // 強制重排以確保動畫生效
    toast.offsetHeight;
    toast.classList.add('show');
    
    setTimeout(() => toast.classList.remove('show'), 3000);
}

/**
 * 格式化金額
 */
function formatMoney(amount) {
    return '$' + Number(amount || 0).toLocaleString();
}

/**
 * 格式化日期
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`;
}

/**
 * 格式化日期時間
 */
function formatDateTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const pad = n => n.toString().padStart(2, '0');
    return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

// ==================== 狀態文字轉換 ====================

const STATUS_TEXT = {
    active: '進行中',
    paused: '已暫停',
    closed: '已結束',
    collecting: '集資中',
    locked: '已鎖定',
    purchased: '已購買',
    drawn: '已開獎',
    settled: '已結算',
    cancelled: '已取消',
    pending: '待開獎',
    won: '已中獎',
    lost: '未中獎'
};

function getStatusText(status) {
    return STATUS_TEXT[status] || status;
}

// ==================== 頁面初始化輔助 ====================

/**
 * 安全的頁面初始化包裝器
 * 用法: safeInit(async () => { ... your init code ... });
 */
function safeInit(initFn) {
    const doInit = async () => {
        try {
            await initFn();
        } catch (e) {
            console.error('頁面初始化錯誤:', e);
            // 不要在錯誤時自動重定向，避免循環
        }
    };
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', doInit);
    } else {
        doInit();
    }
}

// ==================== 匯出（如果使用模組） ====================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        API_BASE, $, getToken, setToken, removeToken,
        checkAuth, checkAuthAndGetUser, logout,
        apiGet, apiPost, apiPut, apiDelete,
        showToast, formatMoney, formatDate, formatDateTime,
        getStatusText, safeInit, safeRedirect, clearRedirectCount
    };
}
