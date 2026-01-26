# SELA 樂透一路發 - 開發文件整合版

> **版本**：1.0.0  
> **更新日期**：2026-01-26  
> **目前完成度**：約 60%

---

## 目錄

1. [專案概述與技術架構](#一專案概述與技術架構)
2. [已完成功能總覽](#二已完成功能總覽)
3. [待開發功能計畫](#三待開發功能計畫)
4. [API 端點與資料庫](#四api-端點與資料庫)
5. [問題排解與最佳實踐](#五問題排解與最佳實踐)

---

## 一、專案概述與技術架構

### 1.1 專案簡介

**SELA 樂透一路發** 是一套線上彩券團購系統，解決傳統團購的計算繁瑣、金流不透明、成員管理混亂等問題。

| 特色 | 說明 |
|------|------|
| 🎯 精確分配 | 自動計算佔比，獎金分配到元 |
| 🔄 資金滾動 | 未用完的資金自動滾入下期 |
| 📊 完整記錄 | 每筆金流都有跡可循 |
| 🔒 隱私保護 | 個人彩券完全私密 |

### 1.2 核心概念

**集資（Group Series）**：長期合作的固定團體，類似「社團」概念
- 成員：30-50 人的親友團
- 彩種：威力彩、大樂透、今彩539（單選）
- 模式：死戰到底（只進不出）/ 彈性模式（允許減碼退出）

**單期團（Group）**：對應一期開獎的單次投注
- 資金池：所有成員投入的總金額
- 份額：個人在資金池中的金額
- 佔比：份額佔資金池的比例

**資金計算範例**：
```
資金池 $10,000
├── 老王：$3,000（30%）→ 有效貢獻：$2,100
├── 小李：$2,000（20%）→ 有效貢獻：$1,400
├── 阿美：$5,000（50%）→ 有效貢獻：$3,500
└── 購買 $7,000 → 滾入下期：$3,000
```

### 1.3 技術棧

| 層級 | 技術 | 說明 |
|------|------|------|
| 後端框架 | FastAPI | 0.109+ |
| 資料庫 | PostgreSQL | 15+，部署於 Railway |
| ORM | SQLAlchemy | 2.0+ |
| 前端 | HTMX + TailwindCSS | 響應式 UI |
| 圖床 | Cloudinary | 彩券照片上傳 |
| 部署 | Railway | GitHub 自動部署 |
| 認證 | LINE Login + JWT | OAuth 2.0 |

### 1.4 專案結構

```
sela-lottery/
├── app/
│   ├── api/v1/           # API 路由
│   ├── core/             # 資料庫、安全模組
│   ├── models/           # SQLAlchemy Models
│   ├── schemas/          # Pydantic Schemas
│   ├── services/         # 業務邏輯
│   └── main.py           # 入口
├── static/               # 前端頁面 (HTML)
├── scripts/              # 遷移、初始化腳本
├── docs/                 # 開發文件
├── Dockerfile
└── requirements.txt
```

### 1.5 支援彩種

| 代碼 | 名稱 | 每注價格 | 開獎時間 | 規格 |
|------|------|:--------:|----------|------|
| power | 威力彩 | $100 | 週一、四 20:30 | 38選6 + 8選1 |
| super | 大樂透 | $50 | 週二、五 20:30 | 49選6 + 特別號 |
| daily539 | 今彩539 | $50 | 每天 20:30 | 39選5 |

---

## 二、已完成功能總覽

### 2.1 開發階段進度

| 階段 | 狀態 | 完成度 | 說明 |
|:----:|:----:|:------:|------|
| Step 1 | ✅ 完成 | 100% | 核心基礎設施 |
| Step 2 | ✅ 完成 | 100% | 團購流程 |
| Step 3 | 🔄 部分 | 70% | 統計與錢包 |
| Step 4 | ⏳ 待開發 | 30% | 進階功能 |

### 2.2 Step 1-2：核心功能 ✅

**認證系統**
- LINE Login OAuth 2.0 整合
- JWT Token 驗證機制
- 首位用戶自動成為系統管理員

**集資管理**
- 建立集資（選擇彩種、設定份額）
- 邀請碼產生、加入、過期管理
- 成員加入、加碼、份額追蹤
- 結束集資（結算並關閉）

**單期團管理**
- 開新期（指定期數、截止時間）
- 鎖定集資（停止新增貢獻）
- 記錄購買（實際購買金額）
- 彩券管理（新增/編輯號碼）

**開獎與結算**
- 手動/自動輸入開獎號碼
- 自動對獎比對所有彩券
- 結算預覽（計算分配比例）
- 執行結算（分配獎金、記錄帳本）

### 2.3 Step 3：統計與錢包 🔄

**已完成 ✅**

| 功能 | 說明 |
|------|------|
| 錢包概覽 | 餘額、份額明細、交易記錄 |
| 統計報表 | ROI、月度趨勢、集資績效、中獎記錄 |
| 開獎資訊 | lottery_draws 表、lotto-8.com 同步、熱/冷號分析 |
| 個人彩券 | 新增記錄、手選/電腦選號、對獎功能 |
| 成就徽章 | 14 種預設成就、進度追蹤、排名 |

**前端開獎專區**
- 分頁顯示歷史開獎
- 彩種切換 Tab
- 開獎號碼視覺化

### 2.4 管理員後台 ✅

| 功能 | 路徑 | 說明 |
|------|------|------|
| 用戶管理 | `/admin` | 列表、停用、角色修改 |
| 集資管理 | `/admin` | 管理所有集資 |
| 事件日誌 | `/admin` | 系統事件記錄 |
| 開獎同步 | `/admin/lottery` | 同步開獎資訊 |

---

## 三、待開發功能計畫

### 3.1 總覽

| 階段 | 主題 | 功能數 | 預估工時 | 優先級 |
|:----:|------|:------:|:--------:|:------:|
| Phase 1 | 成員異動功能 | 3 | 3-4 天 | 🔥 高 |
| Phase 2 | 個人彩券系統 | 5 | 4-5 天 | 🔥 高 |
| Phase 3 | 錢包與金流管理 | 6 | 5-6 天 | ⚡ 中 |
| Phase 4 | 匯出與進階功能 | 4 | 3-4 天 | 📋 低 |

### 3.2 Phase 1：成員異動功能 📦 開發包已準備

**功能列表**

| 功能 | 說明 | 限制 |
|------|------|------|
| 減碼申請 | 成員申請減少份額 | 減碼後至少保留 50 元 |
| 退出申請 | 成員申請退出集資 | 管理員無法退出 |
| 申請審核 | 管理員審核申請 | 核准/拒絕（可填原因） |

**API 端點**

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/member-requests/series/{id}/reduce` | 申請減碼 |
| POST | `/member-requests/series/{id}/withdraw` | 申請退出 |
| POST | `/member-requests/{id}/cancel` | 取消申請 |
| POST | `/member-requests/{id}/review` | 審核申請 |

**資料庫變更**
```sql
CREATE TABLE member_requests (
    id SERIAL PRIMARY KEY,
    series_id INTEGER REFERENCES group_series(id),
    user_id INTEGER REFERENCES users(id),
    request_type VARCHAR(20),  -- 'reduce', 'withdraw'
    amount DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'pending',
    reviewed_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**檔案清單**
```
app/models/member_request.py
app/schemas/member_request.py
app/api/v1/member_requests.py
app/services/member_service.py
scripts/migrate_phase1.py
```

### 3.3 Phase 2：個人彩券系統

| 功能 | 說明 |
|------|------|
| 個人彩券記錄 | 完全私密的個人購買記錄 |
| 個人彩券新增 | 手選/電腦選號，支援批量 |
| 個人彩券對獎 | 自動/手動對獎 |
| 個人彩券統計 | 總投注、總中獎、投報率 |
| 個人彩券列表 | 篩選：彩種、期數、中獎狀態 |

### 3.4 Phase 3：錢包與金流管理

| 功能 | 說明 |
|------|------|
| 錢包餘額系統 | 區分「可用餘額」與「鎖定金額」 |
| 銀行帳戶管理 | 用戶綁定銀行帳戶（最多 3 個） |
| 充值功能 | 申請 → 轉帳 → 上傳憑證 → 審核 |
| 提領功能 | 申請 → 審核 → 轉帳（最低 100 元） |
| 轉帳功能 | 錢包餘額 ⇄ 集資份額 |
| 交易記錄 | 完整金流追蹤 |

### 3.5 Phase 4：匯出與進階功能

| 功能 | 說明 |
|------|------|
| 結算報告 PDF | 匯出單期結算明細 |
| 集資報告 PDF | 匯出集資完整報告 |
| 資料備份匯出 | 匯出個人資料（JSON/CSV） |
| 管理員資料匯出 | 匯出系統資料 |

### 3.6 已移除/暫緩功能

| 功能 | 原因 |
|------|------|
| 死戰到底模式 | 簡化設計，統一為彈性模式 |
| LINE Notify | 2025/3/31 已停止服務 |
| Web Push | 暫緩開發 |

---

## 四、API 端點與資料庫

### 4.1 API 端點總覽

**認證**
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/auth/line/login` | LINE 登入 |
| GET | `/api/v1/auth/callback` | 登入回調 |
| GET | `/api/v1/users/me` | 當前用戶 |
| PUT | `/api/v1/users/me` | 更新資料 |

**集資**
| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/v1/series` | 建立集資 |
| GET | `/api/v1/series` | 我的集資 |
| GET | `/api/v1/series/{id}` | 集資詳情 |
| POST | `/api/v1/series/{id}/invitations` | 建立邀請碼 |
| POST | `/api/v1/series/join` | 加入集資 |
| POST | `/api/v1/series/{id}/members/me/topup` | 加碼 |

**單期團**
| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/v1/series/{id}/groups` | 開新期 |
| GET | `/api/v1/groups/{id}` | 期數詳情 |
| POST | `/api/v1/groups/{id}/lock` | 鎖定 |
| POST | `/api/v1/groups/{id}/purchase` | 購買 |
| POST | `/api/v1/groups/{id}/draw` | 開獎 |
| POST | `/api/v1/groups/{id}/settle` | 結算 |

**彩券**
| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/v1/groups/{id}/tickets` | 新增 |
| GET | `/api/v1/groups/{id}/tickets` | 列表 |
| PUT | `/api/v1/tickets/{id}` | 更新 |

**統計與錢包**
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/statistics/overall` | 整體統計 |
| GET | `/api/v1/statistics/monthly` | 月度統計 |
| GET | `/api/v1/wallet/overview` | 錢包概覽 |
| GET | `/api/v1/wallet/transactions` | 交易記錄 |

**開獎**
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/lottery/latest` | 最新開獎 |
| POST | `/api/v1/lottery/sync` | 同步開獎 |
| GET | `/api/v1/lottery/draws` | 歷史開獎 |
| GET | `/api/v1/lottery/stats/numbers` | 號碼統計 |

### 4.2 資料庫表格

```
users                 用戶
lottery_types         彩種定義
lottery_draws         開獎記錄
group_series          集資
group_members         集資成員
groups                單期團
period_contributions  每期貢獻
tickets               彩券
user_ledger           帳本
event_logs            事件日誌
period_snapshots      快照
series_invitations    邀請碼
personal_tickets      個人彩券
achievements          成就定義
user_achievements     用戶成就
```

### 4.3 API 回應格式

**成功**
```json
{
    "success": true,
    "data": { ... },
    "message": "操作成功"
}
```

**錯誤**
```json
{
    "success": false,
    "error": {
        "code": "INSUFFICIENT_BALANCE",
        "message": "餘額不足"
    }
}
```

---

## 五、問題排解與最佳實踐

### 5.1 常見問題快速查詢

| 類別 | 問題 | 解法 |
|------|------|------|
| 編碼 | 中文亂碼 | `ftfy.fix_text()` |
| 資料庫 | 連線失敗 | 用 Python + psycopg2 直連 Railway |
| API | 路由 404 | 檢查 main.py 是否註冊 router |
| 部署 | Healthcheck 失敗 | 查看日誌找具體錯誤 |
| 安全 | 密碼曝光 | Railway 重新生成 credentials |

### 5.2 資料庫連線問題

**密碼特殊字元**
```
症狀：connection to server failed
解法：Railway PostgreSQL → Settings → Reset Credentials
```

**密碼不匹配**
```
症狀：FATAL: password authentication failed
解法：Web 服務 Variables 更新 DATABASE_URL
```

**連到 localhost**
```
症狀：connection to localhost refused
解法：確認 Web 服務有 DATABASE_URL 環境變數
```

**Python 直連範例**
```python
import psycopg2
conn = psycopg2.connect(
    host="metro.proxy.rlwy.net",
    port=19612,
    user="postgres",
    password="你的密碼",
    database="railway"
)
```

### 5.3 編碼問題

**UTF-8 修復**
```python
import ftfy
fixed = ftfy.fix_text(broken_content)
```

**爬蟲編碼**
```python
response = requests.get(url)
response.encoding = 'utf-8'
```

### 5.4 部署問題

**member_requests 表不存在**
```
症狀：relation "member_requests" does not exist
解法：更新 Dockerfile CMD 加入 migrate_phase1.py
```

```dockerfile
CMD ["sh", "-c", "python scripts/migrate.py && python scripts/migrate_phase1.py && python scripts/seed_data.py && python main.py"]
```

### 5.5 最佳實踐

**Railway 資料庫連線**
- 使用變數引用：`${{Postgres.DATABASE_URL}}`
- 內部連線用 `DATABASE_URL`
- 外部連線用 `DATABASE_PUBLIC_URL`

**開發流程**
- 更新說明 .md 檔放在 `docs/` 資料夾，檔名需區分（如 STEP3_20260110.md）
- 本地爬蟲腳本檔名用 `import_history.py`
- 避免手動 SQL 操作，所有資料庫變更透過 Python migrate 腳本 + Dockerfile CMD 自動執行

**Git 規範**
```
<type>: <subject>
type: feat | fix | docs | style | refactor | test | chore
範例：feat: 新增成員異動功能
```

### 5.6 品牌規範

```css
BRAND_ORANGE = "#FA7A35"  /* SELA 企業識別色 */
SUCCESS = "#4CAF50"
WARNING = "#FF9800"
ERROR = "#F44336"
```

---

## 附錄：稅金計算

| 獎金範圍 | 稅率 |
|----------|------|
| ≤ $5,000 | 免稅 |
| $5,001 - $2萬 | 扣 10% |
| > $2萬 | 扣 20% |

---

*SELA 樂透一路發 © 2026*
