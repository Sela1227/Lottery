# SELA 樂透一路發 - Step 2 前端 UI

## 📁 目錄結構

```
sela_step2/
├── main.py                          # 主入口（更新版，含新頁面路由）
├── static/
│   ├── dashboard.html               # 儀表板（更新版）
│   ├── series.html                  # 系列團列表頁
│   ├── series-detail.html           # 系列團詳情頁
│   ├── group-detail.html            # 單期團詳情頁
│   └── coming-soon.html             # 佔位頁面
└── app/
    └── api/
        └── v1/
            └── lottery_types.py     # 彩種 API
```

## 🔧 整合步驟

### 1. 備份現有檔案
```bash
cp main.py main.py.backup
cp -r static static.backup
```

### 2. 複製新檔案
```bash
# 複製靜態頁面（覆蓋 dashboard.html）
cp sela_step2/static/*.html static/

# 複製主入口（覆蓋）
cp sela_step2/main.py .

# 複製彩種 API
cp sela_step2/app/api/v1/lottery_types.py app/api/v1/
```

### 3. 註冊彩種 API 路由

在 `app/api/v1/__init__.py` 中加入：
```python
from app.api.v1 import lottery_types

# 在 router 註冊
router.include_router(lottery_types.router)
```

或在 `app/main.py` 中加入：
```python
from app.api.v1 import lottery_types

app.include_router(lottery_types.router, prefix="/v1")
```

### 4. 重啟服務
```bash
# 本地開發
python main.py

# Railway 部署
git add .
git commit -m "feat: Step 2 前端 UI 完成"
git push
```

---

## ✨ 新增頁面路由

| 路徑 | 頁面 | 說明 |
|------|------|------|
| `/series` | series.html | 系列團列表 |
| `/series/{id}` | series-detail.html | 系列團詳情 |
| `/group/{id}` | group-detail.html | 單期團詳情 |
| `/statistics` | coming-soon.html | 統計報表（Step 3） |
| `/wallet` | coming-soon.html | 錢包（Step 3） |
| `/personal` | coming-soon.html | 個人彩券（Step 3） |
| `/settings` | coming-soon.html | 設定（Step 4） |

---

## 🎯 功能清單

### ✅ 系列團列表 `/series`
- 查看已加入的系列團
- 建立新系列團
- 使用邀請碼加入
- 統計資訊顯示

### ✅ 系列團詳情 `/series/{id}`
- 完整資訊顯示
- 成員列表與份額
- 管理員：開新期、產生邀請碼
- 成員：加碼功能
- 單期團記錄

### ✅ 單期團詳情 `/group/{id}`
- 進度追蹤（5 階段）
- 彩券管理
- 開獎號碼輸入
- 自動對獎
- 結算預覽與執行
- 中獎號碼高亮

---

## 📋 使用的 API 端點

確保後端有以下 API：

```
GET  /api/v1/lottery-types          # 彩種列表
GET  /api/v1/series                  # 我的系列團
POST /api/v1/series                  # 建立系列團
GET  /api/v1/series/{id}             # 系列團詳情
GET  /api/v1/series/{id}/groups      # 單期團列表
POST /api/v1/series/{id}/groups      # 開新期
GET  /api/v1/series/{id}/members     # 成員列表
POST /api/v1/series/{id}/invitations # 產生邀請碼
POST /api/v1/series/join             # 加入系列團
POST /api/v1/series/{id}/members/me/topup  # 加碼

GET  /api/v1/groups/{id}             # 單期團詳情
GET  /api/v1/groups/{id}/tickets     # 彩券列表
POST /api/v1/groups/{id}/tickets     # 新增彩券
POST /api/v1/groups/{id}/lock        # 鎖定集資
POST /api/v1/groups/{id}/purchase    # 記錄購買
POST /api/v1/groups/{id}/draw        # 輸入開獎號碼
POST /api/v1/groups/{id}/check-tickets    # 對獎
GET  /api/v1/groups/{id}/settlement-preview  # 結算預覽
POST /api/v1/groups/{id}/settle      # 執行結算
```

---

## 🎨 設計規範

- **主色**：#F26522 (SELA Orange)
- **字體**：Noto Sans TC
- **圓角**：16px (卡片), 10px (按鈕)
- **陰影**：rgba(242, 101, 34, 0.08)

---

**版本**：2.0.0 | **日期**：2025-01-09
