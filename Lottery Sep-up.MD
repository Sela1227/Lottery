# SELA 樂透一路發

> **版本**：1.0.0  
> **更新日期**：2026-01-11  
> **專案類型**：Web 應用（團購彩券系統）

---

## 目錄

1. [專案概述](#一-專案概述)
2. [核心概念](#二-核心概念)
3. [功能模組](#三-功能模組)
4. [系統架構](#四-系統架構)
5. [資料庫設計](#五-資料庫設計)
6. [核心演算法](#六-核心演算法)
7. [API 設計](#七-api-設計)
8. [開發階段](#八-開發階段)
9. [部署指南](#九-部署指南)
10. [設計規範](#十-設計規範)
11. [附錄](#十一-附錄)

---

## 一、專案概述

### 1.1 背景與動機

傳統彩券團購面臨多項問題：
- 手動計算繁瑣且容易出錯
- 金流記錄不透明
- 跨期追蹤困難
- 成員進出管理混亂

**SELA 樂透一路發** 是一套完整的線上彩券團購系統，解決上述痛點，讓團購彩券變得簡單、透明、有趣。

### 1.2 目標用戶

- 規模：30-50 人的親友團
- 特色：邀請制、封閉式群組
- 彩種：威力彩、大樂透、今彩539

### 1.3 核心特色

| 特色 | 說明 |
|------|------|
| 🎯 精確分配 | 自動計算佔比，獎金分配到元 |
| 🔄 資金滾動 | 未用完的資金自動滾入下期 |
| 📊 完整記錄 | 每筆金流都有跡可循 |
| 🔒 隱私保護 | 個人彩券完全私密 |
| 🎮 遊戲化 | 成就系統、統計分析 |

---

## 二、核心概念

### 2.1 系列團（Group Series）

長期合作的固定團體，類似「社團」的概念。

```
系列團「財神團」
├── 成員：老王、小李、阿美...（共 10 人）
├── 彩種：威力彩
├── 模式：死戰到底（只進不出）
└── 週期：每週一、四開獎日
```

### 2.2 單期團（Group）

系列團下的單次投注，對應一期開獎。

```
第 113114 期（2026/01/13）
├── 資金池：$5,000
├── 購買金額：$3,500
├── 彩券張數：35 張
└── 狀態：等待開獎
```

### 2.3 資金池（Pool）

所有成員投入的資金總和，採「佔比制」計算權益。

```
資金池 $10,000
├── 老王：$3,000（30%）
├── 小李：$2,000（20%）
├── 阿美：$5,000（50%）
└── 
購買彩券 $7,000 後：
├── 老王有效貢獻：$2,100
├── 小李有效貢獻：$1,400
├── 阿美有效貢獻：$3,500
└── 滾入下期：$3,000
```

### 2.4 運作模式

**死戰到底模式**
- 只進不出，資金持續累積
- 適合長期合作的核心團隊
- 中獎後自動滾入下期

**彈性模式**
- 允許減碼或退出
- 需經管理員審核
- 適合較鬆散的團體

---

## 三、功能模組

### 3.1 功能架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                      SELA 樂透一路發                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  P0 核心功能                                             │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │    │
│  │  │用戶管理 │ │系列團   │ │單期團   │ │成員管理 │        │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │    │
│  │  │彩券管理 │ │對獎系統 │ │結算引擎 │ │帳本記錄 │        │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  P1 進階功能                                             │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │    │
│  │  │錢包系統 │ │銀行帳戶 │ │個人彩券 │ │通知推播 │        │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  P2 加值功能                                             │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │    │
│  │  │統計報表 │ │成就系統 │ │匯出備份 │ │管理後台 │        │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 功能清單

#### P0 核心功能（必要）

| 模組 | 功能 | 說明 |
|------|------|------|
| 用戶管理 | LINE Login | OAuth 2.0 第三方登入 |
| | JWT 認證 | Token-based 身份驗證 |
| | 角色權限 | 管理員 / 一般成員 |
| 系列團 | 建立系列 | 設定名稱、彩種、模式 |
| | 成員邀請 | 邀請碼 / 連結加入 |
| | 權限設定 | 管理員指派、權限控制 |
| 單期團 | 開團 | 設定期數、截止時間 |
| | 集資 | 成員繳款、憑證上傳 |
| | 購票 | 記錄彩券號碼、照片 |
| 成員管理 | 入金審核 | 管理員確認付款 |
| | 份額計算 | 自動計算佔比 |
| | 異動申請 | 加碼 / 減碼 / 退出 |
| 彩券管理 | 選號 | 手選 / 電腦選號 |
| | 照片上傳 | Cloudinary 圖床 |
| | 號碼記錄 | 結構化儲存 |
| 對獎系統 | 自動爬蟲 | 抓取開獎號碼 |
| | 即時對獎 | 比對中獎結果 |
| | 稅金計算 | 自動扣稅 |
| 結算引擎 | 佔比計算 | 精確到小數點 |
| | 獎金分配 | 按比例分發 |
| | 滾入處理 | 未用資金轉下期 |
| 帳本記錄 | 金流追蹤 | 每筆進出都記錄 |
| | 餘額重建 | 可從帳本還原 |

#### P1 進階功能（重要）

| 模組 | 功能 | 說明 |
|------|------|------|
| 錢包系統 | 餘額顯示 | 各系列團餘額 |
| | 充值 | 銀行轉帳入金 |
| | 提領 | 獎金提現 |
| 銀行帳戶 | 帳戶管理 | 新增 / 編輯 / 刪除 |
| | 智慧配對 | 推薦免手續費轉帳 |
| 個人彩券 | 私人記錄 | 完全私密 |
| | 對獎查詢 | 個人購買對獎 |
| 通知推播 | Web Push | 瀏覽器推播 |
| | LINE Notify | LINE 訊息通知 |

#### P2 加值功能（優化）

| 模組 | 功能 | 說明 |
|------|------|------|
| 統計報表 | 號碼分析 | 熱門 / 冷門號碼 |
| | 投報率 | 投入 vs 獲利 |
| 成就系統 | 徽章獎勵 | 遊戲化激勵 |
| | 排行榜 | 積分排名 |
| 匯出備份 | PDF 報告 | 結算明細匯出 |
| | 資料備份 | JSON / CSV |
| 管理後台 | 系統設定 | 彩種設定、通知 |
| | 用戶管理 | 權限調整 |

---

## 四、系統架構

### 4.1 技術棧

| 層級 | 技術 | 版本 |
|------|------|------|
| 後端框架 | FastAPI | 0.109+ |
| 資料庫 | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0+ |
| 驗證 | Pydantic | 2.5+ |
| 前端 | HTMX + TailwindCSS | - |
| 圖床 | Cloudinary | - |
| 部署 | Railway | - |
| 認證 | LINE Login + JWT | - |

### 4.2 專案結構

```
線上威力彩/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py          # 認證
│   │       ├── users.py         # 用戶
│   │       ├── series.py        # 系列團
│   │       ├── groups.py        # 單期團
│   │       ├── lottery.py       # 彩券資料
│   │       ├── wallet.py        # 錢包
│   │       ├── personal.py      # 個人彩券
│   │       ├── statistics.py    # 統計
│   │       ├── achievements.py  # 成就
│   │       ├── notify.py        # 通知
│   │       ├── admin.py         # 管理
│   │       └── health.py        # 健康檢查
│   ├── core/
│   │   ├── database.py          # 資料庫連線
│   │   └── security.py          # 安全模組
│   ├── models/
│   │   ├── user.py              # 用戶模型
│   │   ├── series.py            # 系列團
│   │   ├── group.py             # 單期團
│   │   ├── member.py            # 成員
│   │   ├── ticket.py            # 彩券
│   │   ├── lottery_draw.py      # 開獎記錄
│   │   ├── ledger.py            # 帳本
│   │   └── personal.py          # 個人彩券
│   ├── services/
│   │   ├── auth/
│   │   │   ├── line_auth.py     # LINE 登入
│   │   │   └── user_service.py  # 用戶服務
│   │   ├── lottery_crawler.py   # 彩券爬蟲
│   │   ├── settlement_service.py # 結算服務
│   │   ├── auto_check.py        # 自動對獎
│   │   ├── line_notify.py       # LINE 通知
│   │   └── web_push.py          # Web Push
│   ├── schemas/
│   │   ├── user.py
│   │   ├── series.py
│   │   └── group.py
│   ├── config.py                # 設定檔
│   └── main.py                  # 入口
├── static/                      # 靜態檔案
│   ├── index.html               # 首頁
│   ├── dashboard.html           # 儀表板
│   ├── series.html              # 系列團
│   ├── lottery.html             # 彩券資料
│   ├── wallet.html              # 錢包
│   ├── personal.html            # 個人彩券
│   ├── statistics.html          # 統計
│   ├── settings.html            # 設定
│   └── admin.html               # 管理後台
├── scripts/
│   ├── migrate.py               # 資料庫遷移
│   └── seed_data.py             # 初始資料
├── docs/                        # 文件
├── tests/                       # 測試
├── .project-meta.json           # 專案元資料
├── requirements.txt             # Python 依賴
├── Dockerfile
├── railway.json                 # Railway 設定
└── README.md
```

### 4.3 架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client                                  │
│              (Browser / LINE LIFF / Mobile)                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Railway Platform                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Server                          │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │                   API Routes                         │  │  │
│  │  │   /api/v1/auth  /api/v1/series  /api/v1/groups ...  │  │  │
│  │  └─────────────────────────┬───────────────────────────┘  │  │
│  │                            │                               │  │
│  │  ┌─────────────────────────▼───────────────────────────┐  │  │
│  │  │                    Services                          │  │  │
│  │  │  AuthService  LotteryService  SettlementService ... │  │  │
│  │  └─────────────────────────┬───────────────────────────┘  │  │
│  │                            │                               │  │
│  │  ┌─────────────────────────▼───────────────────────────┐  │  │
│  │  │               SQLAlchemy Models                      │  │  │
│  │  │   User  Series  Group  Member  Ticket  Ledger ...   │  │  │
│  │  └─────────────────────────┬───────────────────────────┘  │  │
│  └────────────────────────────┼───────────────────────────────┘  │
│                               │                                   │
│  ┌────────────────────────────▼───────────────────────────────┐  │
│  │                    PostgreSQL                               │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │Cloudinary│   │LINE Login│   │ lotto-8  │
    │ (圖床)   │   │ (OAuth)  │   │ (爬蟲)   │
    └──────────┘   └──────────┘   └──────────┘
```

---

## 五、資料庫設計

### 5.1 ER Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   users     │       │group_series │       │   groups    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │──┐    │ id (PK)     │──┐    │ id (PK)     │
│ line_id     │  │    │ name        │  │    │ series_id   │──┐
│ name        │  │    │ lottery_type│  │    │ draw_term   │  │
│ is_admin    │  │    │ mode        │  │    │ status      │  │
│ created_at  │  │    │ creator_id  │──┘    │ total_pool  │  │
└─────────────┘  │    │ created_at  │       │ total_spent │  │
                │    └─────────────┘       │ total_prize │  │
                │           │              │ created_at  │  │
                │           │              └─────────────┘  │
                │           ▼                     │         │
                │    ┌─────────────┐              │         │
                └───▶│group_members│◀─────────────┘         │
                     ├─────────────┤                        │
                     │ id (PK)     │                        │
                     │ group_id    │                        │
                     │ user_id     │                        │
                     │ pool_share  │                        │
                     │ status      │                        │
                     └─────────────┘                        │
                            │                               │
                            ▼                               │
                     ┌─────────────┐              ┌─────────────┐
                     │  tickets    │              │lottery_draws│
                     ├─────────────┤              ├─────────────┤
                     │ id (PK)     │              │ id (PK)     │
                     │ group_id    │◀─────────────│lottery_type │
                     │ numbers     │              │ draw_term   │
                     │ is_winner   │              │ draw_date   │
                     │ prize_amount│              │ numbers     │
                     └─────────────┘              │ jackpot     │
                                                  └─────────────┘
```

### 5.2 主要資料表

#### users（用戶）
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    line_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    picture_url TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### group_series（系列團）
```sql
CREATE TABLE group_series (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    lottery_type VARCHAR(20) NOT NULL,  -- power/super/daily539
    mode VARCHAR(20) DEFAULT 'flexible', -- flexible/committed
    status VARCHAR(20) DEFAULT 'active',
    creator_id INTEGER REFERENCES users(id),
    invite_code VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### groups（單期團）
```sql
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    series_id INTEGER REFERENCES group_series(id),
    draw_term VARCHAR(20) NOT NULL,     -- 期數
    draw_date DATE,
    status VARCHAR(20) DEFAULT 'collecting',
    total_pool DECIMAL(12,2) DEFAULT 0,
    total_spent DECIMAL(12,2) DEFAULT 0,
    total_prize DECIMAL(12,2) DEFAULT 0,
    prize_after_tax DECIMAL(12,2) DEFAULT 0,
    settled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### group_members（團員）
```sql
CREATE TABLE group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id),
    user_id INTEGER REFERENCES users(id),
    pool_share DECIMAL(12,2) DEFAULT 0,          -- 目前份額
    pool_share_before_purchase DECIMAL(12,2),    -- 購買前快照
    effective_contribution DECIMAL(12,2),         -- 有效貢獻
    carryover_amount DECIMAL(12,2),              -- 滾入金額
    prize_share DECIMAL(12,2),                   -- 獎金份額
    status VARCHAR(20) DEFAULT 'active',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, user_id)
);
```

#### tickets（彩券）
```sql
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id),
    numbers JSONB NOT NULL,              -- 號碼（結構化）
    image_url TEXT,                      -- 照片連結
    cost DECIMAL(8,2) DEFAULT 100,       -- 單價
    is_winner BOOLEAN DEFAULT FALSE,
    prize_tier VARCHAR(50),              -- 獎項等級
    prize_amount DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### lottery_draws（開獎記錄）
```sql
CREATE TABLE lottery_draws (
    id SERIAL PRIMARY KEY,
    lottery_type VARCHAR(20) NOT NULL,
    draw_term VARCHAR(50) NOT NULL,
    draw_date DATE NOT NULL,
    numbers JSONB NOT NULL,
    jackpot BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lottery_type, draw_term)
);
```

#### user_ledger（帳本）
```sql
CREATE TABLE user_ledger (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    series_id INTEGER REFERENCES group_series(id),
    group_id INTEGER REFERENCES groups(id),
    type VARCHAR(20) NOT NULL,           -- deposit/withdraw/prize/carryover
    amount DECIMAL(12,2) NOT NULL,
    balance_after DECIMAL(12,2),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 六、核心演算法

### 6.1 佔比計算

每位成員在資金池中的權重：

```
佔比 = 個人份額 / 總資金池
```

### 6.2 結算公式

```
有效貢獻 = 個人份額 × (本期購買金額 / 總資金池)
滾入金額 = 個人份額 - 有效貢獻
獎金分配 = (有效貢獻 / 本期購買金額) × 扣稅後獎金
新份額 = 滾入金額 + 獎金分配
```

### 6.3 完整範例

**情境**：
- 資金池：$2,000
- 購買金額：$1,400
- 中獎獎金：$4,000（扣稅後 $3,200）

**成員分佈**：
| 成員 | 份額 | 佔比 |
|------|------|------|
| A | $500 | 25% |
| B | $800 | 40% |
| C | $700 | 35% |
| **合計** | **$2,000** | **100%** |

**結算計算**：

| 成員 | 有效貢獻 | 滾入 | 獎金分配 | 新份額 |
|------|----------|------|----------|--------|
| A | $500 × (1400/2000) = $350 | $150 | $350/1400 × 3200 = $800 | $950 |
| B | $800 × (1400/2000) = $560 | $240 | $560/1400 × 3200 = $1,280 | $1,520 |
| C | $700 × (1400/2000) = $490 | $210 | $490/1400 × 3200 = $1,120 | $1,330 |
| **合計** | **$1,400** | **$600** | **$3,200** | **$3,800** |

**驗證**：
- ✅ 總有效貢獻 = 購買金額 ($1,400)
- ✅ 總滾入 = 資金池 - 購買金額 ($600)
- ✅ 總獎金 = 扣稅後獎金 ($3,200)
- ✅ 新資金池 = 總滾入 + 總獎金 ($3,800)

### 6.4 程式碼實作

```python
from decimal import Decimal, ROUND_DOWN

def calculate_settlement(group):
    """計算單期結算"""
    total_pool = group.total_pool
    total_spent = group.total_spent
    prize_after_tax = group.prize_after_tax
    
    results = []
    
    for member in group.members:
        share = member.pool_share
        ratio = share / total_pool
        
        # 有效貢獻
        effective = (share * total_spent / total_pool).quantize(
            Decimal('0.01'), rounding=ROUND_DOWN
        )
        
        # 滾入
        carryover = share - effective
        
        # 獎金
        if total_spent > 0:
            prize = (effective / total_spent * prize_after_tax).quantize(
                Decimal('0.01'), rounding=ROUND_DOWN
            )
        else:
            prize = Decimal('0')
        
        # 新份額
        new_share = carryover + prize
        
        results.append({
            'user_id': member.user_id,
            'effective_contribution': effective,
            'carryover_amount': carryover,
            'prize_share': prize,
            'new_pool_share': new_share
        })
    
    return results
```

---

## 七、API 設計

### 7.1 API 版本

- 目前版本：`/api/v1`
- 未來擴充：`/api/v2`

### 7.2 認證方式

```
Authorization: Bearer <JWT_TOKEN>
```

### 7.3 主要端點

#### 認證
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | /api/v1/auth/line | LINE OAuth 登入 |
| GET | /api/v1/auth/callback | OAuth 回調 |
| GET | /api/v1/auth/me | 取得當前用戶 |

#### 系列團
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | /api/v1/series | 列出系列團 |
| POST | /api/v1/series | 建立系列團 |
| GET | /api/v1/series/{id} | 取得詳情 |
| PUT | /api/v1/series/{id} | 更新系列團 |
| POST | /api/v1/series/{id}/join | 加入系列團 |

#### 單期團
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | /api/v1/groups | 列出單期團 |
| POST | /api/v1/groups | 建立單期團 |
| GET | /api/v1/groups/{id} | 取得詳情 |
| POST | /api/v1/groups/{id}/tickets | 新增彩券 |
| POST | /api/v1/groups/{id}/settle | 執行結算 |

#### 彩券資料
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | /api/v1/lottery/draws | 取得開獎記錄 |
| POST | /api/v1/lottery/sync | 同步最新開獎 |
| GET | /api/v1/lottery/stats | 號碼統計 |

### 7.4 回應格式

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
        "message": "餘額不足",
        "details": {
            "required": 500,
            "available": 300
        }
    }
}
```

### 7.5 狀態碼

| 代碼 | 說明 |
|------|------|
| 200 | 成功 |
| 201 | 建立成功 |
| 400 | 請求錯誤 |
| 401 | 未認證 |
| 403 | 權限不足 |
| 404 | 找不到資源 |
| 409 | 資源衝突 |
| 422 | 驗證失敗 |
| 500 | 伺服器錯誤 |

---

## 八、開發階段

### 8.1 完成進度

| 階段 | 內容 | 狀態 |
|------|------|------|
| Step 1 | 基礎架構、LINE 登入、JWT | ✅ 100% |
| Step 2 | 系列團、單期團、成員、彩券 | ✅ 100% |
| Step 3 | 結算、對獎、彩券資料爬蟲 | ✅ 100% |
| Step 4 | 設定頁面 | ✅ 100% |
| Step 8 | 問題修復、UI 優化 | ✅ 100% |
| Step 9 | 統計頁面、成就系統 | ✅ 100% |
| Step 10 | Web Push、LINE Notify | ✅ 100% |
| Step 11 | 自動對獎 | ✅ 100% |

### 8.2 待開發

| 功能 | 優先級 | 說明 |
|------|--------|------|
| 錢包系統 | P1 | 餘額、充值、提領 |
| 銀行帳戶 | P1 | 智慧配對轉帳 |
| 個人彩券 | P1 | 私人記錄功能 |
| 異動申請 | P1 | 加碼/減碼/退出 |
| PDF 匯出 | P2 | 結算報告匯出 |

---

## 九、部署指南

### 9.1 Railway 部署

#### 必備檔案

```
project-root/
├── railway.json          # Railway 設定
├── requirements.txt      # Python 依賴
├── Dockerfile           # 容器設定
└── main.py              # 入口
```

#### railway.json

```json
{
    "$schema": "https://railway.app/railway.schema.json",
    "build": {
        "builder": "DOCKERFILE"
    },
    "deploy": {
        "startCommand": "python main.py",
        "restartPolicyType": "ON_FAILURE",
        "restartPolicyMaxRetries": 10
    }
}
```

#### 環境變數

```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
JWT_SECRET_KEY=your-secret-key-at-least-32-chars
LINE_CHANNEL_ID=your-line-channel-id
LINE_CHANNEL_SECRET=your-line-channel-secret
LINE_REDIRECT_URI=https://your-app.railway.app/api/v1/auth/callback
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

### 9.2 部署檢查清單

**首次部署**
- [ ] Railway 環境變數已設定
- [ ] PostgreSQL 資料庫已建立
- [ ] 執行資料庫 migration
- [ ] LINE Login 設定正確

**部署後**
- [ ] 健康檢查通過 (`/api/v1/health`)
- [ ] LINE 登入測試成功
- [ ] 資料庫連線正常

### 9.3 常見錯誤

| 錯誤 | 原因 | 解法 |
|------|------|------|
| `relation "users" does not exist` | 沒執行 migration | 執行 `python scripts/migrate.py` |
| `JWT decode error` | Token 過期或無效 | 重新登入取得新 Token |
| `LINE callback error` | Redirect URI 不符 | 檢查 LINE Console 設定 |

---

## 十、設計規範

### 10.1 SELA 品牌規範

#### 色彩（不可更改）

```python
BRAND_ORANGE = "#FA7A35"      # SELA 企業識別色（愛馬仕橘）

# 輔助色
GREY_LIGHT = "#FAFAFA"        # 淺灰背景
BLUE_GREY = "#607D8B"         # 標題文字
SUCCESS = "#4CAF50"           # 成功
WARNING = "#FF9800"           # 警告
ERROR = "#F44336"             # 錯誤
```

#### LOGO 規範

```
🚫 不可更改：
- 顏色必須是 #FA7A35
- 字重必須是 BOLD
- 文字必須是 "SELA"

✅ 可調整：
- 尺寸（36-56px）
```

### 10.2 專案元資料

每個 SELA 專案必須有 `.project-meta.json`：

```json
{
    "$schema": "project-meta-v1",
    "name": "sela-lottery",
    "version": "1.0.0",
    "type": "web",
    "status": "active",
    "description": "SELA 樂透一路發 - 線上彩券團購系統",
    "tags": ["FastAPI", "PostgreSQL", "HTMX"],
    "created_at": "2025-12-25",
    "docs": {
        "readme": "README.md",
        "changelog": "CHANGELOG.md"
    }
}
```

### 10.3 Git 規範

#### Commit 格式

```
<type>: <subject>

type: feat | fix | docs | style | refactor | test | chore
```

#### 範例

```
feat: 新增 LINE Notify 通知功能
fix: 修正結算時佔比計算錯誤
docs: 更新 API 文件
```

---

## 十一、附錄

### A. 彩種規格

#### 威力彩（Power Lottery）
- 第一區：38 選 6
- 第二區：8 選 1
- 開獎日：週一、四
- 頭獎起始：$1 億

#### 大樂透（Super Lottery）
- 一般號：49 選 6
- 特別號：從剩餘 43 號抽 1
- 開獎日：週二、五
- 頭獎起始：$1 億

#### 今彩539
- 號碼：39 選 5
- 開獎日：每日
- 頭獎固定：$800 萬

### B. 稅金計算

| 獎金範圍 | 稅率 |
|----------|------|
| ≤ $5,000 | 免稅 |
| $5,001 - $2萬 | 扣 10% |
| > $2萬 | 扣 20% |

### C. 詞彙表

| 名詞 | 說明 |
|------|------|
| 系列團 | 長期合作的固定團體 |
| 單期團 | 對應單次開獎的投注 |
| 資金池 | 所有成員投入的總金額 |
| 份額 | 個人在資金池中的金額 |
| 佔比 | 份額佔資金池的比例 |
| 有效貢獻 | 實際用於購買彩券的金額 |
| 滾入 | 未用完滾到下期的金額 |
| 帳本 | 記錄所有金流的表 |

### D. 開發檢查清單

#### 新功能開發
- [ ] 建立資料庫 Model
- [ ] 建立 API Schema
- [ ] 實作 Service 邏輯
- [ ] 建立 API 路由
- [ ] 更新前端頁面
- [ ] 撰寫測試
- [ ] 更新文件

#### 上線前檢查
- [ ] 資料庫 migration 準備好
- [ ] 環境變數確認
- [ ] API 測試通過
- [ ] 前端功能測試
- [ ] 錯誤處理完整

---

## 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| 1.0.0 | 2026-01-11 | 初版發布 |

---

*SELA 樂透一路發 © 2026*
