# 🎰 SELA 樂透一路發 - Step 4-1 設定頁面、首次登入、開獎資訊

## 📦 本次更新內容

### 新增功能

| 功能 | 說明 | 路徑 |
|------|------|------|
| **設定頁面** | 個人資料設定（暱稱、Email、電話） | `/settings` |
| **首次登入引導** | 新用戶登入後彈出設定暱稱對話框 | Dashboard 彈窗 |
| **開獎資訊小卡** | Dashboard 最上方顯示威力彩、大樂透最新開獎 | Dashboard |

---

## 🗂️ 檔案清單

```
sela_step4_settings.zip
├── main.py                    # 根目錄主程式 (更新 /settings 路由)
├── app/api/v1/
│   └── auth.py                # 認證 API (新增 is_new 參數)
├── static/
│   ├── index.html             # 登入頁 (處理 new 參數)
│   ├── settings.html          # 設定頁面 (全新)
│   ├── dashboard_welcome_patch.html       # Dashboard 首次登入補丁
│   └── dashboard_lottery_cards_patch.html # Dashboard 開獎卡片補丁
└── docs/
    └── STEP4_SETTINGS_20260110.md    # 本說明檔
```

---

## 🚀 部署步驟

### 1. 解壓縮

```bash
unzip -o sela_step4_settings.zip -d 線上威力彩/
```

### 2. 手動修改 dashboard.html

開啟 `static/dashboard.html`，按照 `dashboard_welcome_patch.html` 的說明進行修改：

#### 2.1 新增歡迎彈窗 HTML

在 `</main>` 標籤後面，`join-modal` 之前，加入：

```html
<!-- 首次登入歡迎彈窗 -->
<div class="modal-overlay" id="welcome-modal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); align-items: center; justify-content: center; z-index: 1100;">
    <div style="background: #fff; border-radius: 24px; width: 90%; max-width: 380px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
        <div style="background: linear-gradient(135deg, #F26522, #ff8a50); padding: 32px 24px; text-align: center; color: white;">
            <div style="font-size: 48px; margin-bottom: 12px;">🎉</div>
            <h2 style="font-size: 22px; font-weight: 700; margin-bottom: 8px;">歡迎加入 SELA！</h2>
            <p style="font-size: 14px; opacity: 0.9;">設定您的暱稱，讓夥伴更容易認識您</p>
        </div>
        <div style="padding: 24px;">
            <div style="margin-bottom: 20px;">
                <label style="display: block; font-size: 13px; color: #666; margin-bottom: 6px;">LINE 名稱</label>
                <input type="text" id="welcome-display-name" disabled style="width: 100%; padding: 12px 14px; border: 1px solid #e0e0e0; border-radius: 10px; font-size: 15px; background: #f5f5f5; color: #999;">
            </div>
            <div style="margin-bottom: 24px;">
                <label style="display: block; font-size: 13px; color: #666; margin-bottom: 6px;">設定暱稱 <span style="color: #999;">(選填)</span></label>
                <input type="text" id="welcome-nickname" placeholder="輸入您想使用的暱稱" maxlength="50" style="width: 100%; padding: 12px 14px; border: 1px solid #e0e0e0; border-radius: 10px; font-size: 15px;">
                <p style="font-size: 12px; color: #999; margin-top: 6px;">留空將使用 LINE 名稱</p>
            </div>
            <div style="display: flex; gap: 12px;">
                <button onclick="skipWelcome()" style="flex: 1; padding: 14px; border: 1px solid #e0e0e0; background: #fff; border-radius: 12px; font-size: 14px; cursor: pointer;">稍後設定</button>
                <button onclick="saveWelcomeNickname()" style="flex: 1; padding: 14px; border: none; background: #F26522; color: #fff; border-radius: 12px; font-size: 14px; font-weight: 600; cursor: pointer;">確認</button>
            </div>
        </div>
        <div style="padding: 0 24px 20px; text-align: center;">
            <p style="font-size: 12px; color: #999;">💡 之後可在「設定」頁面修改</p>
        </div>
    </div>
</div>
```

#### 2.2 新增 JavaScript 函數

在 `<script>` 區塊中加入：

```javascript
// ===== 首次登入相關函數 =====
function checkFirstLogin(user) {
    const isNewUser = localStorage.getItem('is_new_user');
    if (isNewUser === '1') {
        localStorage.removeItem('is_new_user');
        showWelcomeModal(user);
    }
}

function showWelcomeModal(user) {
    document.getElementById('welcome-display-name').value = user.display_name;
    document.getElementById('welcome-nickname').value = '';
    document.getElementById('welcome-modal').style.display = 'flex';
    setTimeout(() => document.getElementById('welcome-nickname').focus(), 300);
}

function closeWelcomeModal() {
    document.getElementById('welcome-modal').style.display = 'none';
}

function skipWelcome() {
    closeWelcomeModal();
    showToast('歡迎加入！隨時可在設定中修改暱稱', 'success');
}

async function saveWelcomeNickname() {
    const nickname = document.getElementById('welcome-nickname').value.trim();
    if (!nickname) { skipWelcome(); return; }
    
    try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(`${API_BASE}/users/me`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ nickname: nickname })
        });
        if (!res.ok) { const err = await res.json(); throw new Error(err.detail || '儲存失敗'); }
        
        const updatedUser = await res.json();
        const displayName = updatedUser.nickname || updatedUser.display_name;
        document.getElementById('user-name').textContent = displayName;
        document.getElementById('welcome-name').textContent = displayName;
        
        closeWelcomeModal();
        showToast(`歡迎 ${displayName}！祝您好運 🍀`, 'success');
    } catch (e) { showToast(e.message, 'error'); }
}
```

#### 2.3 修改 checkAuth 函數

在 `updateUI(user)` 後面加入一行：

```javascript
checkFirstLogin(user);  // 新增這一行
```

#### 2.4 (選用) 新增設定入口按鈕

在快速操作區塊 `.actions` 中加入：

```html
<a href="/settings" class="action-btn settings">
    <div class="action-icon">⚙️</div>
    <div class="action-title">設定</div>
    <div class="action-desc">個人資料與通知</div>
</a>
```

CSS：
```css
.action-btn.settings {
    background: linear-gradient(135deg, #607D8B, #455A64);
    border: none; color: #fff; box-shadow: 0 8px 24px rgba(96, 125, 139, 0.3);
}
.action-btn.settings:hover { box-shadow: 0 12px 32px rgba(96, 125, 139, 0.4); }
.action-btn.settings .action-desc { color: rgba(255,255,255,0.85); }
```

### 3. Git 提交

```bash
cd 線上威力彩
git add .
git commit -m "feat: Step 4-1 設定頁面與首次登入引導"
git push
```

---

## 🎯 新功能說明

### 1. 開獎資訊小卡片

在 Dashboard 最上方顯示威力彩和大樂透最新開獎號碼。

#### 部署方式

開啟 `static/dashboard.html`，按照 `dashboard_lottery_cards_patch.html` 說明：

**2.5 新增開獎卡片 HTML（在 `<main>` 後、`.hero` 前）**

```html
<!-- 最新開獎資訊 -->
<div class="lottery-cards" id="lottery-cards">
    <div class="lottery-card power loading-card">
        <div class="lottery-card-header">
            <span class="lottery-icon">🎯</span>
            <span class="lottery-name">威力彩</span>
        </div>
        <div class="lottery-numbers">載入中...</div>
    </div>
    <div class="lottery-card super loading-card">
        <div class="lottery-card-header">
            <span class="lottery-icon">🎰</span>
            <span class="lottery-name">大樂透</span>
        </div>
        <div class="lottery-numbers">載入中...</div>
    </div>
</div>
```

**2.6 新增 CSS（完整樣式見 patch 檔案）**

**2.7 新增 JavaScript 函數**

```javascript
// 載入最新開獎資訊
async function loadLotteryInfo() { ... }

// 渲染開獎卡片
function renderLotteryCards(lotteries) { ... }

// 渲染號碼球
function renderLotteryNumbers(numbers, type) { ... }
```

**2.8 修改 checkAuth() 加入 loadLotteryInfo()**

```javascript
updateUI(user);
checkFirstLogin(user);
loadLotteryInfo();  // <-- 新增
loadDashboardData();
```

#### 顯示效果

```
┌──────────────────┐  ┌──────────────────┐
│ 🎯 威力彩  01/09 │  │ 🎰 大樂透  01/09 │
│ ⚪⚪⚪⚪⚪⚪ | 🔴 │  │ ⚪⚪⚪⚪⚪⚪ | 🟡 │
│ 💰 頭獎   3.2 億 │  │ 💰 頭獎   1.5 億 │
└──────────────────┘  └──────────────────┘
```

---

### 2. 設定頁面 `/settings`

- 顯示用戶頭像與角色
- 修改暱稱、Email、電話
- 通知設定預留（LINE Notify 待實作）
- 登出功能

### 3. 首次登入流程

```
LINE 登入 → auth callback (is_new=1) → index.html (儲存標記) 
→ dashboard (檢查標記) → 彈出歡迎設定框 → 用戶可設定或跳過
```

### API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/users/me` | 取得當前用戶資料 |
| PUT | `/api/v1/users/me` | 更新用戶資料 |

**PUT /api/v1/users/me 請求範例：**
```json
{
    "nickname": "小明",
    "email": "example@mail.com",
    "phone": "0912345678"
}
```

---

## 📊 專案進度更新

| 階段 | 狀態 | 完成度 |
|------|------|--------|
| Step 1: 核心基礎設施 | ✅ 完成 | 100% |
| Step 2: 團購流程 | ✅ 完成 | 100% |
| Step 3: 統計與錢包 | ✅ 完成 | 100% |
| Step 4: 進階功能 | 🔄 進行中 | 40% |

### Step 4 進度

- [x] 設定頁面
- [x] 首次登入引導
- [x] Dashboard 開獎資訊卡片
- [ ] LINE Notify 整合
- [ ] 開獎提醒通知
- [ ] 中獎通知推播

**整體進度：約 90%**

---

*Step 4-1 完成！🎉*
