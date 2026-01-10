# 🎰 更新包：彩券開獎資訊同步

## 📅 更新日期：2026-01-10

## 🆕 新增功能

### 開獎資訊同步
- 自動從 pilio.idv.tw 抓取最新開獎號碼
- 支援威力彩、大樂透、今彩539
- 顯示累積獎金（威力彩、大樂透）
- 管理員專用同步功能

## 📦 包含檔案

```
main.py                           # 覆蓋（加入 /admin/lottery 路由）
requirements.txt                  # 覆蓋（加入 beautifulsoup4）
app/
├── main.py                       # 覆蓋（註冊 lottery API）
├── api/v1/
│   ├── __init__.py               # 覆蓋（導出 lottery_router）
│   └── lottery.py                # 新增（開獎資訊 API）
└── services/
    ├── __init__.py               # 新增
    └── lottery_crawler.py        # 新增（爬蟲服務）
static/
├── admin.html                    # 覆蓋（加入開獎同步連結）
└── admin_lottery.html            # 新增（開獎同步頁面）
```

## 🔌 API 端點

| 方法 | 路徑 | 說明 | 權限 |
|------|------|------|------|
| GET | `/api/v1/lottery/latest` | 取得所有彩種最新開獎 | 登入 |
| GET | `/api/v1/lottery/latest/{type}` | 取得特定彩種最新開獎 | 登入 |
| GET | `/api/v1/lottery/history/{type}` | 取得開獎歷史 | 登入 |
| POST | `/api/v1/lottery/sync` | 同步開獎資訊 | 管理員 |

### 彩種代碼
- `power` - 威力彩
- `super` - 大樂透
- `daily539` - 今彩539

## 🚀 部署步驟

```bash
# 1. 解壓縮到專案根目錄（覆蓋）
unzip sela_lottery_sync.zip -d 線上威力彩/

# 2. 推送到 Railway
cd 線上威力彩
git add .
git commit -m "feat: 新增開獎資訊同步功能"
git push

# Railway 會自動重新部署
```

## 📱 使用方式

1. 登入系統
2. 進入「管理後台」
3. 點擊「🎰 開獎資訊同步」
4. 點擊「立即同步」按鈕
5. 等待同步完成，頁面會顯示最新開獎號碼

## ⚠️ 注意事項

- 資料來源為 pilio.idv.tw（非官方網站）
- 建議在開獎後 10-30 分鐘再進行同步
- 累積獎金可能有延遲，以台彩官網為準
- 同步功能僅限管理員使用

## 🔧 技術說明

- 使用 BeautifulSoup4 解析 HTML
- 支援 Big5 編碼（pilio 網站編碼）
- 請求超時設定 10 秒
- 錯誤處理完整，不會因爬蟲失敗而影響系統
