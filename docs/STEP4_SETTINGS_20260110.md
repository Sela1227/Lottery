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
│   ├── dashboard.html         # 儀表板 (完整更新：開獎卡片+首登彈窗+設定入口)
│   └── settings.html          # 設定頁面 (全新)
└── docs/
    └── STEP4_SETTINGS_20260110.md    # 本說明檔
```

---

## 🚀 部署步驟

### 1. 解壓縮

```bash
unzip -o sela_step4_settings.zip -d 線上威力彩/
```

### 2. Git 提交

```bash
cd 線上威力彩
git add .
git commit -m "feat: Step 4-1 設定頁面、首次登入、開獎卡片"
git push
```

完成！本次更新已包含完整的 `dashboard.html`，無需手動修改。

---

## 🎯 新功能說明

### 1. 開獎資訊小卡片

在 Dashboard 最上方顯示威力彩和大樂透最新開獎號碼。

```
┌──────────────────┐  ┌──────────────────┐
│ 🎯 威力彩  01/09 │  │ 🎰 大樂透  01/09 │
│ ⚪⚪⚪⚪⚪⚪ | 🔴 │  │ ⚪⚪⚪⚪⚪⚪ | 🟡 │
│ 💰 頭獎   3.2 億 │  │ 💰 頭獎   1.5 億 │
└──────────────────┘  └──────────────────┘
```

- 橘色卡片 = 威力彩（6+1 號碼）
- 藍色卡片 = 大樂透（6+特別號）
- 資料來源：`/api/v1/lottery/latest`（即時爬取 pilio.idv.tw）

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
