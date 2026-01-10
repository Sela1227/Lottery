# 🔔 SELA 樂透一路發 - Web Push 推播通知

## 📅 更新日期
2026-01-10

## 📦 更新內容

實作瀏覽器原生 Web Push 推播通知功能：
- 用戶訂閱/取消推播
- 通知設定管理
- 多裝置支援
- 測試通知發送

---

## 🆚 為什麼選擇 Web Push

| 方案 | 優點 | 缺點 |
|------|------|------|
| LINE Notify | 簡單 | ❌ 已於 2025/3/31 停止服務 |
| LINE Messaging API | 功能豐富 | 需要官方帳號、有免費額度限制 |
| **Web Push** ✅ | 瀏覽器原生、免費、不依賴第三方 | 需要 HTTPS |

---

## 🛠️ 設定步驟

### 1. 安裝套件

在 `requirements.txt` 加入：

```
pywebpush>=1.14.0
cryptography>=41.0.0
```

### 2. 生成 VAPID 金鑰

```bash
python scripts/generate_vapid.py
```

執行後會顯示：
```
VAPID_PUBLIC_KEY=BGxxxxxxxx...
VAPID_PRIVATE_KEY=xxxxxxxx...
VAPID_EMAIL=admin@your-domain.com
```

### 3. 設定 Railway 環境變數

```env
VAPID_PUBLIC_KEY=BGxxxxxxxx...
VAPID_PRIVATE_KEY=xxxxxxxx...
VAPID_EMAIL=admin@your-domain.com
```

### 4. 執行資料庫遷移

```bash
python scripts/migrate_webpush.py
```

---

## 📡 API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/notify/settings` | 取得通知設定 |
| PUT | `/api/v1/notify/settings` | 更新通知設定 |
| POST | `/api/v1/notify/subscribe` | 訂閱推播 |
| DELETE | `/api/v1/notify/subscribe` | 取消訂閱 |
| GET | `/api/v1/notify/subscriptions` | 列出訂閱裝置 |
| DELETE | `/api/v1/notify/subscriptions/{id}` | 刪除特定訂閱 |
| POST | `/api/v1/notify/test` | 發送測試通知 |

---

## 🗄️ 資料庫

### 新增表：push_subscriptions

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | SERIAL | 主鍵 |
| user_id | INTEGER | 用戶 ID |
| endpoint | TEXT | 推播端點 URL |
| p256dh_key | VARCHAR(255) | 加密金鑰 |
| auth_key | VARCHAR(255) | 認證金鑰 |
| device_name | VARCHAR(100) | 裝置名稱 |
| is_active | BOOLEAN | 是否啟用 |
| created_at | TIMESTAMP | 建立時間 |
| last_used_at | TIMESTAMP | 最後使用時間 |

### users 表新增欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| notify_draw_reminder | BOOLEAN | 開獎提醒 |
| notify_win_alert | BOOLEAN | 中獎通知 |
| notify_settlement | BOOLEAN | 結算通知 |

---

## 📱 用戶操作流程

```
設定頁面 → 點擊「啟用推播通知」
    ↓
瀏覽器詢問通知權限
    ↓
用戶點擊「允許」
    ↓
建立訂閱，儲存到資料庫
    ↓
發送歡迎通知
    ↓
顯示「已啟用」狀態
```

---

## 🔧 後端工具函式

```python
from app.api.v1.notify import (
    send_draw_reminder,      # 開獎提醒
    send_win_notification,   # 中獎通知
    send_settlement_notification,  # 結算通知
    send_broadcast           # 系統公告
)

# 範例：發送開獎提醒
await send_draw_reminder(db, "威力彩", "2026-01-10")

# 範例：發送中獎通知
await send_win_notification(db, user_id=1, series_name="好運團", period=5, prize=10000)
```

---

## 🗂️ 檔案清單

```
step10_webpush.zip
├── app/
│   ├── config.py                  # 更新：VAPID 設定
│   ├── main.py                    # 更新：註冊 notify router
│   ├── models/
│   │   └── push_subscription.py   # 新增：訂閱模型
│   ├── services/
│   │   └── web_push.py            # 新增：Web Push 服務
│   └── api/v1/
│       └── notify.py              # 新增：通知 API
├── scripts/
│   ├── migrate_webpush.py         # 新增：資料庫遷移
│   └── generate_vapid.py          # 新增：VAPID 金鑰生成
├── static/
│   ├── settings.html              # 更新：通知設定 UI
│   └── sw.js                      # 新增：Service Worker
├── requirements_add.txt           # 新增套件
└── docs/
    └── STEP10_WEBPUSH_20260110.md
```

---

## 🚀 部署步驟

### 1. 本地生成 VAPID 金鑰

```bash
pip install pywebpush cryptography
python scripts/generate_vapid.py
```

### 2. 設定環境變數

在 Railway 加入：
- `VAPID_PUBLIC_KEY`
- `VAPID_PRIVATE_KEY`
- `VAPID_EMAIL`

### 3. 更新套件

在 `requirements.txt` 加入：
```
pywebpush>=1.14.0
cryptography>=41.0.0
```

### 4. 解壓縮並部署

```bash
cd /Users/sela/Documents/Python/線上威力彩
unzip -o ~/Downloads/step10_webpush.zip

# 執行遷移（本地測試）
python scripts/migrate_webpush.py

# 提交部署
git add .
git commit -m "feat: Web Push 推播通知"
git push
```

---

## ✅ 驗證方式

1. 登入系統，進入「設定」頁面
2. 點擊「啟用推播通知」
3. 允許瀏覽器通知權限
4. 應收到「通知已啟用」的推播訊息
5. 點擊「發送測試通知」再次驗證

---

## ⚠️ 注意事項

1. **HTTPS 必要**：Web Push 只能在 HTTPS 網站使用（localhost 例外）
2. **瀏覽器支援**：Chrome, Firefox, Edge, Safari 都支援
3. **iOS Safari 限制**：需要 iOS 16.4+ 且需要安裝為 PWA
4. **金鑰安全**：VAPID 私鑰不要公開
5. **訂閱過期**：瀏覽器可能會清除訂閱，需要處理重新訂閱

---

## 🔮 後續整合

待整合到其他功能：

1. **開獎同步後** → 呼叫 `send_draw_reminder()`
2. **對獎完成** → 呼叫 `send_win_notification()`
3. **結算完成** → 呼叫 `send_settlement_notification()`
4. **管理員後台** → 新增「發送公告」功能

---

*Web Push 推播通知整合完成！🔔*
