# 🎰 團購彩券系統 (Lottery Group)

> 一個專為彩券團購設計的完整解決方案，支援多期連續跟團、資金池管理、自動結算分配

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-repo/lottery-group)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)](https://www.python.org/)

---

## 📋 目錄

- [專案概述](#專案概述)
- [核心特色](#核心特色)
- [系統架構](#系統架構)
- [功能模組](#功能模組)
- [資料庫設計](#資料庫設計)
- [API 設計](#api-設計)
- [開發階段規劃](#開發階段規劃)
- [技術棧](#技術棧)
- [Flet 0.70+ 注意事項](#flet-070-注意事項)
- [Railway 部署](#railway-部署)
- [LINE Login 整合](#line-login-整合)
- [安裝與部署](#安裝與部署)
- [使用指南](#使用指南)
- [未來擴充](#未來擴充)
- [附錄](#附錄)

---

## 專案概述

### 背景

傳統彩券團購面臨的問題：
- 💸 每期重新收款，管理繁瑣
- 📊 佔比計算複雜，容易出錯
- 📝 無完整記錄，難以追溯
- 🤝 獎金分配不透明

### 解決方案

本系統採用「**系列團**」概念，將多期連續的團購視為一個整體：
- 一次加入，持續參與
- 資金池自動滾動
- 獎金按佔比精確分配
- 完整記錄，永久可查

### 核心概念

```
┌─────────────────────────────────────────────────────────────────┐
│                        系列團 (Series)                          │
│                    「不中不休 A 隊」                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   第1期          第2期          第3期          第4期            │
│  ┌─────┐       ┌─────┐       ┌─────┐       ┌─────┐           │
│  │威力彩│  →   │大樂透│  →   │威力彩│  →   │大樂透│  → ...    │
│  │$1400│       │$1350│       │$1400│       │$1420│           │
│  └─────┘       └─────┘       └─────┘       └─────┘           │
│     ↓             ↓             ↓             ↓               │
│   中$200        沒中          中$550        沒中              │
│     ↓             ↓             ↓             ↓               │
│  滾入下期  →   滾入下期  →   滾入下期  →   滾入下期           │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│  資金池持續滾動，直到達成結束條件或管理員決定結束               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心特色

### 🎯 雙模式支援

| 模式 | 說明 | 適用場景 |
|------|------|----------|
| **死戰到底** | 資金池只進不出，不中獎就一直玩 | 親友小團、信任度高 |
| **彈性模式** | 允許中途減碼或退出 | 公開團、人數較多 |

### 💰 智慧資金池

- **自動滾入**：未用完的資金自動滾入下期
- **精確佔比**：依實際貢獻計算，支援多次加碼
- **即時更新**：加碼/減碼後立即反映

### 📊 完整記錄

- **帳本系統**：所有金流異動完整記錄
- **事件日誌**：所有操作行為可追溯
- **期快照**：每期結算時保存完整狀態
- **可重建**：從原始記錄可還原任意時間點

### 🔔 智慧提醒

- 集資截止提醒
- 開獎結果通知
- 結算完成通知
- 異動申請審核通知

### 📱 多端支援

- Web 響應式介面
- LINE 通知整合
- PDF 報表匯出

---

## 系統架構

### 整體架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Web App   │  │  Mobile App │  │  LINE Bot   │            │
│  │   (React)   │  │  (PWA/RN)   │  │  (Webhook)  │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         └─────────────────┼─────────────────┘                  │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                             │
│                     (Nginx / Traefik)                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Server                        │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │
│  │  │  Auth   │  │ Series  │  │ Member  │  │ Ticket  │    │   │
│  │  │   API   │  │   API   │  │   API   │  │   API   │    │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │
│  │  │ Request │  │Settlement│  │ Export  │  │ Notify  │    │   │
│  │  │   API   │  │   API   │  │   API   │  │   API   │    │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Service Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Series    │  │   Member    │  │  Settlement │            │
│  │   Service   │  │   Service   │  │   Service   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Ledger    │  │   Export    │  │   Notify    │            │
│  │   Service   │  │   Service   │  │   Service   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ PostgreSQL  │  │    Redis    │  │    MinIO    │            │
│  │  (Primary)  │  │   (Cache)   │  │  (Storage)  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### 程式結構

```
lottery-group/
│
├── .project-meta.json        # SELA 專案元資料（必要）
├── package.json              # Railway 偵測用
├── nixpacks.toml             # Nixpacks 建置設定
├── railway.json              # Railway 部署設定
├── requirements.txt          # Python 依賴
├── README.md                 # 專案說明
├── CHANGELOG.md              # 版本變更紀錄
├── .env.example              # 環境變數範例
├── .gitignore
│
├── main.py                   # Flet 主入口
│
├── app/                      # FastAPI 後端
│   ├── main.py               # FastAPI 入口
│   ├── config.py             # 系統設定
│   │
│   ├── api/                  # API 路由層
│   │   └── v1/
│   │       ├── auth.py           # LINE 認證 API
│   │       ├── users.py          # 用戶 API
│   │       ├── series.py         # 系列團 API
│   │       ├── groups.py         # 單期團 API
│   │       ├── members.py        # 成員 API
│   │       ├── tickets.py        # 彩券 API
│   │       ├── requests.py       # 異動申請 API
│   │       ├── settlements.py    # 結算 API
│   │       ├── bank_accounts.py  # 銀行帳戶 API
│   │       ├── personal_lottery.py # 個人彩券 API
│   │       ├── exports.py        # 匯出 API
│   │       └── notifications.py  # 通知 API
│   │
│   ├── models/               # 資料庫模型
│   │   ├── user.py
│   │   ├── series.py
│   │   ├── group.py
│   │   ├── member.py
│   │   ├── ticket.py
│   │   ├── request.py
│   │   ├── ledger.py
│   │   ├── bank_account.py
│   │   ├── personal_lottery.py
│   │   └── ...
│   │
│   ├── schemas/              # Pydantic 資料結構
│   │   └── ...
│   │
│   ├── services/             # 業務邏輯層
│   │   ├── auth/                 # 認證服務
│   │   │   ├── line_auth.py      # LINE Login
│   │   │   └── jwt_service.py    # JWT 處理
│   │   ├── series/               # 系列團服務
│   │   ├── member/               # 成員服務
│   │   ├── settlement/           # 結算服務
│   │   ├── ledger/               # 帳本服務
│   │   ├── notification/         # 通知服務
│   │   ├── export/               # 匯出服務
│   │   └── ...
│   │
│   ├── core/                 # 核心模組
│   │   ├── database.py           # 資料庫連線
│   │   ├── security.py           # 安全相關
│   │   ├── permissions.py        # 權限控制
│   │   └── exceptions.py         # 自訂例外
│   │
│   └── utils/                # 工具函式
│       └── ...
│
├── ui/                       # Flet 前端
│   ├── __init__.py
│   ├── main.py               # UI 入口
│   ├── theme.py              # SELA 主題設定
│   │
│   ├── components/           # 共用元件
│   │   ├── header.py
│   │   ├── sidebar.py
│   │   ├── dialogs.py
│   │   └── ...
│   │
│   ├── pages/                # 頁面
│   │   ├── login.py              # 登入頁
│   │   ├── dashboard.py          # 儀表板
│   │   ├── series/               # 系列團頁面
│   │   │   ├── list.py
│   │   │   ├── detail.py
│   │   │   └── create.py
│   │   ├── group/                # 單期團頁面
│   │   ├── member/               # 成員頁面
│   │   ├── ticket/               # 彩券頁面
│   │   ├── personal/             # 個人彩券
│   │   ├── settings/             # 設定頁面
│   │   └── ...
│   │
│   └── services/             # API 呼叫服務
│       ├── api_client.py
│       ├── auth_service.py
│       └── ...
│
├── migrations/               # 資料庫遷移
│   ├── v1.0.0_initial.sql
│   └── ...
│
├── scripts/                  # 腳本
│   ├── init_db.py
│   ├── migrate.py
│   ├── seed_data.py
│   ├── backup_full.py
│   └── ...
│
├── tests/                    # 測試
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── docs/                     # 文件
    └── ...
```

---

## 功能模組

### 模組一覽

| 模組 | 說明 | 優先級 |
|------|------|--------|
| [用戶管理](#1-用戶管理) | 註冊、登入、個人資料 | P0 |
| [系列團管理](#2-系列團管理) | 建立、設定、狀態管理 | P0 |
| [單期團管理](#3-單期團管理) | 開新期、集資、購買 | P0 |
| [成員管理](#4-成員管理) | 加入、佔比、資金池 | P0 |
| [彩券管理](#5-彩券管理) | 上傳、對獎、記錄 | P0 |
| [異動申請](#6-異動申請) | 加碼、減碼、審核 | P0 |
| [結算系統](#7-結算系統) | 獎金計算、分配、滾入 | P0 |
| [帳本系統](#8-帳本系統) | 金流記錄、事件日誌 | P0 |
| [銀行帳戶](#9-銀行帳戶) | 常用帳戶、智慧配對 | P1 |
| [個人彩券](#10-個人彩券) | 私人記錄、統計（管理員不可見） | P1 |
| [通知系統](#11-通知系統) | 提醒、推播 | P1 |
| [匯出備份](#12-匯出備份) | PDF報表、資料備份 | P1 |
| [統計報表](#13-統計報表) | 圖表、分析 | P2 |

---

### 1. 用戶管理

#### 功能清單
- [ ] 用戶註冊（Email / 手機）
- [ ] 登入認證（JWT）
- [ ] 第三方登入（Google / LINE）
- [ ] 個人資料管理
- [ ] 密碼重設
- [ ] 登出

#### 資料模型
```
User
├── id: int (PK)
├── email: string (unique)
├── phone: string (unique, nullable)
├── password_hash: string
├── display_name: string
├── nickname: string (nullable)
├── avatar_url: string (nullable)
├── status: enum (active, suspended, deleted)
├── email_verified: boolean
├── phone_verified: boolean
├── wallet_balance: decimal (錢包餘額)
├── created_at: datetime
└── updated_at: datetime
```

---

### 2. 系列團管理

#### 功能清單
- [ ] 建立系列團
- [ ] 設定允許彩種
- [ ] 設定提領政策（死戰到底/彈性模式）
- [ ] 設定結束條件
- [ ] 邀請成員
- [ ] 結束系列團

#### 資料模型
```
GroupSeries
├── id: int (PK)
├── name: string
├── allowed_lottery_types: json (["power", "super", ...])
├── withdrawal_policy: enum (flexible, no_withdraw)
├── end_condition: json (nullable)
│   ├── type: enum (jackpot, periods, manual)
│   ├── jackpot_threshold: int (中頭獎就結束)
│   └── max_periods: int (最多幾期)
├── status: enum (active, paused, ended)
├── total_periods: int
├── current_pool: decimal
├── total_invested: decimal
├── total_prize: decimal
├── creator_id: int (FK -> users)
├── created_at: datetime
├── ended_at: datetime (nullable)
└── end_reason: string (nullable)
```

#### 結束條件類型
| 類型 | 說明 |
|------|------|
| `jackpot` | 中頭獎後結束 |
| `periods` | 達到指定期數後結束 |
| `manual` | 管理員手動結束 |

---

### 3. 單期團管理

#### 功能清單
- [ ] 開始新一期
- [ ] 選擇彩種與期數
- [ ] 顯示頭獎資訊（輔助選擇）
- [ ] 設定集資截止時間
- [ ] 鎖定集資
- [ ] 記錄購買資訊
- [ ] 上傳彩券
- [ ] 開獎對獎
- [ ] 執行結算

#### 資料模型
```
Group (單期團)
├── id: int (PK)
├── series_id: int (FK -> group_series)
├── period_number: int (第幾期)
├── lottery_type_id: int (FK -> lottery_types)
├── draw_term: string (台彩期數，如 "113000098")
├── draw_date: date
├── draw_time: time
│
├── status: enum
│   ├── collecting (集資中)
│   ├── locked (已鎖定)
│   ├── purchased (已購買)
│   ├── drawn (已開獎)
│   └── settled (已結算)
│
├── collection_deadline: datetime
├── locked_at: datetime (nullable)
├── purchased_at: datetime (nullable)
├── drawn_at: datetime (nullable)
├── settled_at: datetime (nullable)
│
├── total_pool: decimal (本期資金池)
├── total_spent: decimal (實際購買金額)
├── total_tickets: int (購買注數)
├── total_carryover: decimal (滾入下期金額)
├── total_prize: decimal (中獎總額)
├── total_prize_after_tax: decimal (扣稅後)
│
├── winning_numbers: json (開獎號碼)
├── choice_reason: string (選擇此彩種的原因)
│
├── created_at: datetime
└── updated_at: datetime
```

#### 狀態流程
```
collecting → locked → purchased → drawn → settled
    ↓
 (可加碼)    (購買中)   (等開獎)   (對獎)   (結束)
```

---

### 4. 成員管理

#### 功能清單
- [ ] 加入系列團
- [ ] 查看個人佔比
- [ ] 查看資金池份額
- [ ] 查看歷史參與記錄

#### 資料模型
```
GroupMember
├── id: int (PK)
├── series_id: int (FK -> group_series)
├── user_id: int (FK -> users)
├── role: enum (admin, member)
├── status: enum (active, exited)
│
├── pool_share: decimal (目前資金池份額)
├── current_ratio: decimal (目前佔比)
│
├── total_invested: decimal (累計投入)
├── total_prize_received: decimal (累計獲得獎金)
│
├── joined_at: datetime
├── exited_at: datetime (nullable)
└── exit_reason: string (nullable)
```

#### 佔比計算公式
```
成員佔比 = 成員有效份額 / 全部成員有效份額總和

有效份額 = 購買前的資金池份額（含本期加碼，扣除本期減碼）
```

---

### 5. 彩券管理

#### 功能清單
- [ ] 上傳彩券照片
- [ ] 輸入彩券號碼
- [ ] 自動/手動對獎
- [ ] 記錄中獎結果
- [ ] 查看彩券歷史

#### 資料模型
```
Ticket
├── id: int (PK)
├── group_id: int (FK -> groups)
├── ticket_index: int (第幾張)
│
├── image_url: string (彩券照片)
├── numbers: json (號碼)
│   [
│     {"first_zone": [1,5,12,23,31,38], "second_zone": 2},
│     {"first_zone": [3,8,15,22,28,35], "second_zone": 5}
│   ]
│
├── bet_count: int (注數)
├── cost: decimal (金額)
│
├── is_checked: boolean (是否已對獎)
├── checked_at: datetime
├── prize_level: string (中獎等級)
├── prize_amount: decimal (中獎金額)
│
├── is_redeemed: boolean (是否已兌獎)
├── redeemed_at: datetime
├── redeemed_amount: decimal (實際兌換金額)
│
├── created_at: datetime
└── updated_at: datetime
```

#### 支援彩種
| 代碼 | 名稱 | 每注價格 | 開獎時間 |
|------|------|----------|----------|
| `power` | 威力彩 | $100 | 週一、四 20:30 |
| `super` | 大樂透 | $50 | 週二、五 20:30 |
| `daily539` | 今彩539 | $50 | 每日 20:30 |
| `3star` | 3星彩 | $25 | 每日 12:30, 20:30 |
| `4star` | 4星彩 | $25 | 每日 12:30, 20:30 |

---

### 6. 異動申請

#### 功能清單
- [ ] 申請加碼
- [ ] 申請減碼（彈性模式）
- [ ] 申請退出（彈性模式）
- [ ] 上傳轉帳憑證
- [ ] 管理員審核
- [ ] 申請狀態追蹤

#### 資料模型
```
PoolChangeRequest
├── id: int (PK)
├── series_id: int (FK -> group_series)
├── group_id: int (FK -> groups) (申請時的期數)
├── user_id: int (FK -> users)
│
├── request_type: enum (topup, withdraw, exit)
├── amount: decimal
├── status: enum
│   ├── pending_proof (待上傳憑證)
│   ├── pending_review (待審核)
│   ├── approved (已通過)
│   ├── rejected (已退回)
│   ├── completed (已完成)
│   └── cancelled (已取消)
│
├── payment_source: enum (wallet, bank_transfer)
├── proof_image_url: string (轉帳憑證)
│
├── user_bank_account_id: int (用戶收款帳戶，減碼用)
├── series_bank_account_id: int (系列團帳戶)
│
├── reviewed_by: int (FK -> users)
├── reviewed_at: datetime
├── review_note: string
│
├── effective_from_period: int (生效期數)
│
├── created_at: datetime
└── updated_at: datetime
```

#### 申請流程

**加碼流程：**
```
申請加碼 → 上傳憑證 → 管理員審核 → 通過 → 資金池增加
                           ↓
                         退回 → 重新上傳
```

**減碼流程（彈性模式）：**
```
申請減碼 → 管理員審核 → 通過 → 本期結算後退款
                 ↓
               退回 → 取消申請
```

---

### 7. 結算系統

#### 功能清單
- [ ] 計算各成員佔比
- [ ] 計算獎金分配
- [ ] 計算滾入金額
- [ ] 執行結算
- [ ] 建立期快照

#### 結算流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        結算流程                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1️⃣ 確認開獎結果                                                │
│     └─ 所有彩券已對獎                                           │
│                                                                 │
│  2️⃣ 計算基礎數據                                                │
│     ├─ 總資金池 = Σ 各成員份額                                  │
│     ├─ 總支出 = 實際購買金額                                    │
│     ├─ 總滾入 = 總資金池 - 總支出                               │
│     └─ 總獎金 = Σ 各彩券中獎金額                                │
│                                                                 │
│  3️⃣ 計算各成員佔比                                              │
│     ├─ 有效份額 = 購買前份額（含本期加碼，扣除本期減碼）        │
│     └─ 佔比 = 有效份額 / Σ 所有成員有效份額                     │
│                                                                 │
│  4️⃣ 分配滾入                                                    │
│     └─ 成員滾入 = 總滾入 × 成員佔比                             │
│                                                                 │
│  5️⃣ 分配獎金                                                    │
│     └─ 成員獎金 = 總獎金（扣稅後） × 成員佔比                   │
│                                                                 │
│  6️⃣ 更新資金池                                                  │
│     └─ 新份額 = 滾入份額 + 獎金份額                             │
│                                                                 │
│  7️⃣ 處理減碼/退出申請                                          │
│     └─ 依申請金額退款                                           │
│                                                                 │
│  8️⃣ 建立期快照                                                  │
│     └─ 保存完整結算資料                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 獎金稅率
| 獎金範圍 | 稅率 |
|----------|------|
| ≤ $5,000 | 0% |
| > $5,000 | 20% |

---

### 8. 帳本系統

#### 功能清單
- [ ] 記錄所有金流異動
- [ ] 記錄所有操作事件
- [ ] 支援餘額查詢
- [ ] 支援歷史回溯
- [ ] 餘額驗證與重建

#### 資料模型

**帳本記錄：**
```
UserLedger
├── id: bigint (PK)
├── user_id: int (FK -> users)
├── account_type: enum (wallet, pool)
├── series_id: int (FK, nullable, pool 專用)
│
├── transaction_type: enum
│   ├── deposit (儲值)
│   ├── withdraw (提領)
│   ├── transfer_out (轉出)
│   ├── transfer_in (轉入)
│   ├── pool_join (加入資金池)
│   ├── pool_topup (加碼)
│   ├── pool_withdraw (減碼)
│   ├── pool_purchase (購買扣除)
│   ├── pool_carryover (滾入)
│   ├── pool_prize (獎金分配)
│   └── adjustment (調整)
│
├── amount: decimal (正=增加，負=減少)
├── balance_after: decimal (交易後餘額)
│
├── reference_type: string
├── reference_id: int
├── details: json
├── note: string
│
└── created_at: datetime
```

**事件日誌：**
```
EventLog
├── id: bigint (PK)
├── event_type: string
├── category: string
├── actor_id: int (誰執行)
├── actor_type: enum (user, admin, system)
├── target_type: string
├── target_id: int
├── user_id: int
├── series_id: int
├── group_id: int
├── event_data: json
├── result: enum (success, failed)
├── error_message: string
├── ip_address: inet
└── created_at: datetime
```

#### 設計原則

```
┌─────────────────────────────────────────────────────────────────┐
│  帳本系統設計原則                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1️⃣ 只增不改（Append-Only）                                     │
│     • 所有記錄只新增，不修改、不刪除                            │
│     • 錯誤用「沖銷」方式處理                                    │
│                                                                 │
│  2️⃣ 雙重記錄                                                    │
│     • 帳本記錄：金流異動                                        │
│     • 事件日誌：操作行為                                        │
│                                                                 │
│  3️⃣ 可重建                                                      │
│     • 餘額 = 所有交易金額的加總                                 │
│     • 可還原任意時間點的狀態                                    │
│                                                                 │
│  4️⃣ 完整快照                                                    │
│     • 每期結算時保存完整狀態                                    │
│     • 方便快速查詢                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 9. 銀行帳戶

#### 功能清單
- [ ] 新增常用帳戶
- [ ] 編輯/刪除帳戶
- [ ] 設定預設帳戶（收款/付款）
- [ ] 智慧配對（同銀行優先）
- [ ] 顯示手續費預估
- [ ] 記錄使用次數

#### 智慧配對邏輯

```
配對優先順序：
1. 同銀行（免手續費）
2. 數位銀行（有免費跨轉額度）
3. 一般銀行（按手續費排序）

介面範例：
┌─────────────────────────────────────────────────────────┐
│ 加碼 $500 - 選擇轉帳方式                                │
├─────────────────────────────────────────────────────────┤
│ ⭐ 推薦：同銀行轉帳（免手續費）                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ● 我的玉山 → 團收款玉山                             │ │
│ │   手續費：$0 ✨                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ 其他選項                                                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ○ 我的 LINE Bank → 團收款玉山                       │ │
│ │   手續費：$0（本月免費額度 85/88）                  │ │
│ │ ○ 我的台新 → 團收款玉山                             │ │
│ │   手續費：$15                                       │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### 資料模型
```
UserBankAccount
├── id: int (PK)
├── user_id: int (FK -> users)
├── bank_code: string
├── bank_name: string
├── account_number: string
├── account_name: string
├── account_type: enum (receive, pay, both)
├── is_default_receive: boolean
├── is_default_pay: boolean
├── nickname: string
├── status: enum (active, disabled)
├── use_count: int
├── last_used_at: datetime
└── created_at: datetime
```

---

### 10. 個人彩券

> **🔒 重要：此模組完全私人，管理員及其他用戶無法查看**

#### 功能清單
- [ ] 記錄個人購買
- [ ] 記錄彩券號碼
- [ ] 上傳彩券照片
- [ ] 手動/自動對獎
- [ ] 標記已兌獎
- [ ] 個人統計報表
- [ ] 與團購合併統計
- [ ] 標籤分類
- [ ] 匯出記錄

#### 使用情境

```
┌─────────────────────────────────────────────────────────┐
│ 🎫 我的個人彩券                             🔒 僅自己可見 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 📊 統計摘要                                             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │         個人購買      團購        合計              │ │
│ │ 總投入   $12,500     $8,600      $21,100            │ │
│ │ 總獎金   $4,200      $6,350      $10,550            │ │
│ │ 投報率   33.6%       73.8%       50.0%              │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ 📜 購買記錄                                             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 2024/12/30 🔴威力彩 113000098                       │ │
│ │ 2 張 × $100 = $200                                  │ │
│ │ ⏳ 尚未對獎               [📷看彩券] [🎯對獎]       │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ 2024/12/27 🟢大樂透 113000045                       │ │
│ │ 5 張 × $50 = $250  🏷️生日幸運號                    │ │
│ │ 🎉 中獎 $400（普獎×4）✅已兌獎                      │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### 隱私保護

| 資料 | 本人 | 管理員 | 其他成員 |
|------|------|--------|----------|
| 個人購買記錄 | ✅ | ❌ | ❌ |
| 個人統計 | ✅ | ❌ | ❌ |
| 合併報表 | ✅ | ❌ | ❌ |

**重要：此模組完全私人，管理員無法查看**

#### 資料模型
```
PersonalLotteryRecord
├── id: int (PK)
├── user_id: int (FK -> users)
├── lottery_type_code: string
├── lottery_type_name: string
├── draw_term: string
├── draw_date: date
├── ticket_count: int
├── cost_per_ticket: decimal
├── total_cost: decimal
├── purchase_location: string
├── numbers: json
├── ticket_image_urls: json
├── is_checked: boolean
├── winning_numbers: json
├── prize_amount: decimal
├── prize_detail: json
├── is_redeemed: boolean
├── tags: json
├── note: string
├── status: enum (active, archived)
└── created_at: datetime
```

---

### 11. 通知系統

#### 功能清單
- [ ] 應用內通知
- [ ] LINE 推播
- [ ] Email 通知
- [ ] 自訂提醒
- [ ] 通知偏好設定

#### 通知類型
| 類型 | 說明 | 預設 |
|------|------|------|
| 集資截止提醒 | 截止前 N 小時 | 開啟 |
| 開獎結果通知 | 開獎後推播 | 開啟 |
| 結算完成通知 | 結算後推播 | 開啟 |
| 申請審核通知 | 審核結果 | 開啟 |
| 新期開始通知 | 開新期時 | 開啟 |
| 頭獎達標提醒 | 頭獎超過門檻 | 可選 |

---

### 12. 匯出備份

#### 功能清單
- [ ] 系列團完整報告 (PDF)
- [ ] 個人對帳單 (PDF)
- [ ] 單期報告 (PDF)
- [ ] 原始資料匯出 (CSV/JSON)
- [ ] 個人完整備份
- [ ] 自動定期備份

#### 匯出內容

**系列團報告包含：**
- 基本資訊總覽
- 成員列表與佔比
- 歷史期數明細
- 統計圖表

**個人對帳單包含：**
- 所有交易明細
- 投入/獎金統計
- 期數參與記錄

---

### 13. 統計報表

#### 功能清單
- [ ] 系列團整體統計
- [ ] 成員排行榜
- [ ] 彩種分析
- [ ] 投報率趨勢
- [ ] 月度/年度報表

---

## 資料庫設計

### ER Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    users    │     │group_series │     │   groups    │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id (PK)     │──┐  │ id (PK)     │──┐  │ id (PK)     │
│ email       │  │  │ name        │  │  │ series_id   │──┐
│ display_name│  │  │ policy      │  │  │ period_num  │  │
│ wallet_bal  │  │  │ creator_id  │──┘  │ lottery_id  │  │
└─────────────┘  │  │ status      │     │ status      │  │
                │  └─────────────┘     │ total_pool  │  │
                │         │            └─────────────┘  │
                │         │                   │         │
                │         ▼                   │         │
                │  ┌─────────────┐            │         │
                │  │group_members│            │         │
                │  ├─────────────┤            │         │
                └─→│ user_id     │            │         │
                   │ series_id   │←───────────┘         │
                   │ pool_share  │                      │
                   │ ratio       │                      │
                   └─────────────┘                      │
                          │                            │
                          ▼                            │
                   ┌─────────────┐              ┌─────────────┐
                   │  requests   │              │   tickets   │
                   ├─────────────┤              ├─────────────┤
                   │ user_id     │              │ group_id    │←─┘
                   │ series_id   │              │ numbers     │
                   │ type        │              │ prize_amt   │
                   │ amount      │              └─────────────┘
                   └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │ user_ledger │
                   ├─────────────┤
                   │ user_id     │
                   │ account_type│
                   │ trans_type  │
                   │ amount      │
                   │ balance_aft │
                   └─────────────┘
```

### 資料表清單

| 表名 | 說明 | 優先級 |
|------|------|--------|
| `users` | 用戶 | P0 |
| `group_series` | 系列團 | P0 |
| `groups` | 單期團 | P0 |
| `group_members` | 成員 | P0 |
| `tickets` | 彩券 | P0 |
| `lottery_types` | 彩種 | P0 |
| `pool_change_requests` | 異動申請 | P0 |
| `user_ledger` | 帳本 | P0 |
| `event_log` | 事件日誌 | P0 |
| `period_snapshots` | 期快照 | P0 |
| `user_bank_accounts` | 銀行帳戶 | P1 |
| `series_bank_accounts` | 系列團帳戶 | P1 |
| `banks` | 銀行資料 | P1 |
| `personal_lottery_records` | 個人彩券 | P1 |
| `notifications` | 通知 | P1 |
| `reminders` | 提醒 | P1 |
| `export_logs` | 匯出記錄 | P1 |
| `backup_logs` | 備份記錄 | P1 |
| `db_migrations` | 遷移記錄 | P0 |
| `system_config` | 系統設定 | P0 |

### 向後相容設計原則

```
┌─────────────────────────────────────────────────────────────────┐
│  資料庫向後相容原則                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ 允許的操作                                                  │
│     • 新增表（CREATE TABLE IF NOT EXISTS）                      │
│     • 新增欄位（ADD COLUMN IF NOT EXISTS）                      │
│     • 新增索引（CREATE INDEX IF NOT EXISTS）                    │
│     • 新增欄位必須有 DEFAULT 值                                 │
│                                                                 │
│  ❌ 禁止的操作                                                  │
│     • 刪除欄位（DROP COLUMN）                                   │
│     • 修改欄位類型（ALTER COLUMN TYPE）                         │
│     • 重新命名欄位（RENAME COLUMN）                             │
│     • 刪除表（DROP TABLE）                                      │
│                                                                 │
│  💡 棄用欄位處理                                                │
│     • 不刪除，只標記為 deprecated                               │
│     • 在程式碼中停止使用                                        │
│     • 保留資料以供回顧                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## API 設計

### API 版本策略

- 使用 URL 路徑版本：`/api/v1/...`
- 主要版本變更時新增路由（v2）
- 舊版本保持向後相容

### API 端點一覽

#### 認證 (Auth)
| Method | Endpoint | 說明 |
|--------|----------|------|
| POST | `/api/v1/auth/register` | 註冊 |
| POST | `/api/v1/auth/login` | 登入 |
| POST | `/api/v1/auth/logout` | 登出 |
| POST | `/api/v1/auth/refresh` | 刷新 Token |
| POST | `/api/v1/auth/reset-password` | 重設密碼 |

#### 用戶 (Users)
| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/api/v1/me` | 取得個人資料 |
| PUT | `/api/v1/me` | 更新個人資料 |
| GET | `/api/v1/me/wallet` | 取得錢包餘額 |
| GET | `/api/v1/me/series` | 取得參與的系列團 |

#### 系列團 (Series)
| Method | Endpoint | 說明 |
|--------|----------|------|
| POST | `/api/v1/series` | 建立系列團 |
| GET | `/api/v1/series` | 列出系列團 |
| GET | `/api/v1/series/{id}` | 取得系列團詳情 |
| PUT | `/api/v1/series/{id}` | 更新系列團 |
| POST | `/api/v1/series/{id}/invite` | 邀請成員 |
| POST | `/api/v1/series/{id}/end` | 結束系列團 |
| GET | `/api/v1/series/{id}/lottery-options` | 取得可選彩種 |
| POST | `/api/v1/series/{id}/periods` | 開始新一期 |

#### 單期團 (Groups)
| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/api/v1/groups/{id}` | 取得單期詳情 |
| POST | `/api/v1/groups/{id}/lock` | 鎖定集資 |
| POST | `/api/v1/groups/{id}/purchase` | 記錄購買 |
| POST | `/api/v1/groups/{id}/draw` | 記錄開獎 |
| POST | `/api/v1/groups/{id}/settle` | 執行結算 |

#### 成員 (Members)
| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/api/v1/series/{id}/members` | 列出成員 |
| GET | `/api/v1/series/{id}/members/me` | 取得自己的成員資訊 |
| POST | `/api/v1/series/{id}/join` | 加入系列團 |
| POST | `/api/v1/series/{id}/exit` | 退出系列團 |

#### 彩券 (Tickets)
| Method | Endpoint | 說明 |
|--------|----------|------|
| POST | `/api/v1/groups/{id}/tickets` | 上傳彩券 |
| GET | `/api/v1/groups/{id}/tickets` | 列出彩券 |
| PUT | `/api/v1/tickets/{id}` | 更新彩券 |
| POST | `/api/v1/tickets/{id}/check` | 對獎 |

#### 異動申請 (Requests)
| Method | Endpoint | 說明 |
|--------|----------|------|
| POST | `/api/v1/series/{id}/requests` | 建立申請 |
| GET | `/api/v1/series/{id}/requests` | 列出申請 |
| GET | `/api/v1/requests/{id}` | 取得申請詳情 |
| POST | `/api/v1/requests/{id}/proof` | 上傳憑證 |
| POST | `/api/v1/requests/{id}/approve` | 審核通過 |
| POST | `/api/v1/requests/{id}/reject` | 審核退回 |
| POST | `/api/v1/requests/{id}/cancel` | 取消申請 |

#### 銀行帳戶 (Bank Accounts)
| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/api/v1/me/bank-accounts` | 列出帳戶 |
| POST | `/api/v1/me/bank-accounts` | 新增帳戶 |
| PUT | `/api/v1/me/bank-accounts/{id}` | 更新帳戶 |
| DELETE | `/api/v1/me/bank-accounts/{id}` | 刪除帳戶 |
| GET | `/api/v1/series/{id}/transfer-matches` | 取得轉帳配對 |

#### 個人彩券 (Personal Lottery)
| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/api/v1/me/personal-lottery` | 列出記錄 |
| POST | `/api/v1/me/personal-lottery` | 新增記錄 |
| PUT | `/api/v1/me/personal-lottery/{id}` | 更新記錄 |
| DELETE | `/api/v1/me/personal-lottery/{id}` | 刪除記錄 |
| POST | `/api/v1/me/personal-lottery/{id}/result` | 記錄開獎結果 |
| GET | `/api/v1/me/personal-lottery/statistics` | 取得統計 |

#### 匯出 (Exports)
| Method | Endpoint | 說明 |
|--------|----------|------|
| POST | `/api/v1/series/{id}/export/report` | 匯出系列團報告 |
| POST | `/api/v1/series/{id}/export/statement` | 匯出個人對帳單 |
| POST | `/api/v1/groups/{id}/export/report` | 匯出單期報告 |
| POST | `/api/v1/me/export/backup` | 匯出個人備份 |
| GET | `/api/v1/me/exports` | 列出匯出記錄 |
| GET | `/api/v1/exports/{id}/download` | 下載檔案 |

#### 通知 (Notifications)
| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/api/v1/me/notifications` | 列出通知 |
| PUT | `/api/v1/me/notifications/{id}/read` | 標記已讀 |
| PUT | `/api/v1/me/notifications/read-all` | 全部已讀 |
| GET | `/api/v1/me/notification-settings` | 取得通知設定 |
| PUT | `/api/v1/me/notification-settings` | 更新通知設定 |

---

## 開發階段規劃

### 階段總覽

```
┌─────────────────────────────────────────────────────────────────┐
│                        開發階段總覽                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 0: 基礎建設          2 週                               │
│  ════════════════════════════════════════════                  │
│  • 專案初始化                                                   │
│  • 資料庫設計與建立                                             │
│  • 基礎 API 框架                                                │
│  • 認證系統                                                     │
│                                                                 │
│  Phase 1: 核心功能          4 週                               │
│  ════════════════════════════════════════════                  │
│  • 系列團 CRUD                                                  │
│  • 成員管理                                                     │
│  • 彩券管理                                                     │
│  • 異動申請                                                     │
│  • 結算系統                                                     │
│  • 帳本系統                                                     │
│                                                                 │
│  Phase 2: 進階功能          3 週                               │
│  ════════════════════════════════════════════                  │
│  • 銀行帳戶管理                                                 │
│  • 個人彩券記錄                                                 │
│  • 通知系統                                                     │
│  • 匯出備份                                                     │
│                                                                 │
│  Phase 3: 優化與上線        2 週                               │
│  ════════════════════════════════════════════                  │
│  • 效能優化                                                     │
│  • 安全強化                                                     │
│  • 測試完善                                                     │
│  • 部署上線                                                     │
│                                                                 │
│  Phase 4: 持續迭代          持續                               │
│  ════════════════════════════════════════════                  │
│  • 統計報表                                                     │
│  • 前端優化                                                     │
│  • 新功能開發                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Phase 0: 基礎建設（2 週）

#### 第 1 週
- [ ] 專案結構建立
- [ ] 開發環境設定（Docker、VSCode）
- [ ] 資料庫設計確認
- [ ] 建立基礎資料表
- [ ] Migration 系統建立

#### 第 2 週
- [ ] FastAPI 專案初始化
- [ ] 資料庫連線設定
- [ ] JWT 認證系統
- [ ] 用戶 CRUD API
- [ ] 基礎中介軟體（日誌、錯誤處理）
- [ ] API 文件（Swagger）

#### 交付物
- [x] 可運行的 API Server
- [x] 用戶註冊/登入功能
- [x] API 文件
- [x] Docker 開發環境

---

### Phase 1: 核心功能（4 週）

#### 第 3 週 - 系列團與成員
- [ ] 系列團 CRUD
- [ ] 彩種資料設定
- [ ] 成員加入/退出
- [ ] 佔比計算邏輯
- [ ] 單期團建立

#### 第 4 週 - 集資與購買
- [ ] 開新期流程
- [ ] 集資截止管理
- [ ] 異動申請（加碼）
- [ ] 鎖定集資
- [ ] 購買記錄

#### 第 5 週 - 彩券與開獎
- [ ] 彩券上傳
- [ ] 號碼輸入
- [ ] 對獎邏輯
- [ ] 獎金計算
- [ ] 彩種獎金結構

#### 第 6 週 - 結算系統
- [ ] 結算流程實作
- [ ] 滾入計算
- [ ] 獎金分配
- [ ] 帳本記錄
- [ ] 期快照
- [ ] 異動申請（減碼）處理

#### 交付物
- [x] 完整的系列團生命週期
- [x] 單期團從建立到結算
- [x] 資金池計算準確
- [x] 帳本完整記錄

---

### Phase 2: 進階功能（3 週）

#### 第 7 週 - 銀行帳戶與配對
- [ ] 用戶銀行帳戶管理
- [ ] 系列團收款帳戶
- [ ] 智慧配對邏輯
- [ ] 轉帳資訊顯示

#### 第 8 週 - 個人彩券與通知
- [ ] 個人彩券記錄 CRUD
- [ ] 個人統計計算
- [ ] 通知系統架構
- [ ] 提醒排程
- [ ] LINE Notify 整合

#### 第 9 週 - 匯出備份
- [ ] PDF 產生器
- [ ] 報表模板
- [ ] 匯出 API
- [ ] 自動備份機制
- [ ] 備份驗證

#### 交付物
- [x] 銀行帳戶智慧配對
- [x] 個人彩券完整功能
- [x] 通知系統運作
- [x] PDF 報表匯出
- [x] 自動備份機制

---

### Phase 3: 優化與上線（2 週）

#### 第 10 週 - 優化與測試
- [ ] 效能優化
- [ ] 資料庫索引調整
- [ ] API 回應時間優化
- [ ] 單元測試覆蓋
- [ ] 整合測試
- [ ] E2E 測試

#### 第 11 週 - 安全與部署
- [ ] 安全性檢查
- [ ] 權限驗證完善
- [ ] 敏感資料加密
- [ ] 生產環境設定
- [ ] CI/CD 設定
- [ ] 監控告警設定
- [ ] 正式上線

#### 交付物
- [x] 完整測試覆蓋
- [x] 生產環境部署
- [x] 監控系統
- [x] 上線文件

---

### Phase 4: 持續迭代（持續）

#### 功能擴充
- [ ] 統計報表與圖表
- [ ] 成員排行榜
- [ ] 彩種分析
- [ ] 手機 APP
- [ ] 進階自動化

#### 優化項目
- [ ] 前端體驗優化
- [ ] 效能持續優化
- [ ] 新彩種支援
- [ ] 多語系支援

---

## 技術棧

### 後端 (Backend)
| 技術 | 用途 | 版本 |
|------|------|------|
| Python | 程式語言 | 3.11+ |
| FastAPI | API 框架 | 0.109+ |
| SQLAlchemy | ORM | 2.0+ |
| Pydantic | 資料驗證 | 2.5+ |
| PostgreSQL | 資料庫 | 15+ |
| Redis | 快取/佇列 | 7+ |

### 前端 (Frontend)
| 技術 | 用途 | 版本 |
|------|------|------|
| Flet | Python UI 框架 | 0.70+ |
| Flet Web | Web 部署 | - |

### 部署 (Deployment)
| 技術 | 用途 |
|------|------|
| Railway | 雲端部署平台 |
| Nixpacks | 建置工具 |
| PostgreSQL (Railway) | 資料庫服務 |

### 認證 (Authentication)
| 技術 | 用途 |
|------|------|
| LINE Login | 主要登入方式 |
| JWT | Token 管理 |

### 開發工具
| 工具 | 用途 |
|------|------|
| Git | 版本控制 |
| GitHub Actions | CI/CD |
| pytest | 測試框架 |
| Black | 程式碼格式化 |
| Ruff | Linting |

---

## Flet 0.70+ 注意事項

### FilePicker 重大變更

```python
# 舊版 (0.69-)
picker = ft.FilePicker(on_result=callback)
page.overlay.append(picker)

# 新版 (0.70+)
picker = ft.FilePicker()
page.services.append(picker)

# 必須使用 async/await + page.run_task()
def _browse(self, e):
    async def _open():
        path = await self._picker.get_directory_path()
        if path:
            self.path_field.value = path
            self._page.update()
    self._page.run_task(_open)
```

### 其他 API 變更

```python
# 對話框
page.open(dialog)   # 開啟
page.close(dialog)  # 關閉

# Checkbox 回調
# 舊版: e.control.value
# 新版: e.data == "true"

# 啟動程式
ft.run(main)  # 不是 ft.app(target=main)
```

### Flet 遷移檢查清單
- [ ] FilePicker 構造函數移除所有參數
- [ ] `page.overlay.append()` → `page.services.append()`
- [ ] FilePicker 方法改用 async/await + `page.run_task()`
- [ ] Checkbox `e.control.value` → `e.data == "true"`
- [ ] `ft.app()` → `ft.run()`

---

## Railway 部署

### 專案結構

```
lottery-group/
├── package.json          # 根目錄（Railway 偵測用）
├── nixpacks.toml         # Nixpacks 建置設定
├── railway.json          # Railway 部署設定
├── requirements.txt      # Python 依賴
├── main.py               # Flet 入口點
├── app/                  # FastAPI 後端
│   ├── main.py
│   └── ...
└── ui/                   # Flet 前端
    ├── main.py
    └── ...
```

### Railway 設定檔

**railway.json（首次部署，含 migrate）**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "python scripts/migrate.py && python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**railway.json（正常運行）**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**nixpacks.toml**
```toml
[phases.setup]
nixPkgs = ["python311", "postgresql"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "python main.py"
```

**package.json（讓 Railway 偵測專案）**
```json
{
  "name": "lottery-group",
  "version": "1.0.0",
  "private": true,
  "engines": { "node": ">=20.0.0" }
}
```

### Railway 環境變數

```env
# 資料庫（Railway 自動提供）
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# JWT
JWT_SECRET=your-secret-key-at-least-32-chars
JWT_EXPIRES_IN=7d

# LINE Login
LINE_CHANNEL_ID=your-channel-id
LINE_CHANNEL_SECRET=your-channel-secret
LINE_CALLBACK_URL=https://your-app.railway.app/auth/line/callback

# 應用程式
APP_ENV=production
PORT=8000
```

### 部署檢查清單

**首次部署**
- [ ] 根目錄有 package.json、nixpacks.toml、railway.json
- [ ] startCommand 包含 migrate
- [ ] Railway 環境變數已設定
- [ ] LINE Login 回調 URL 已設定

**部署成功後**
- [ ] 移除 startCommand 中的 migrate
- [ ] 重新 push

### 常見錯誤

| 錯誤訊息 | 原因 | 解法 |
|---------|------|------|
| `Failed to generate build plan` | 根目錄缺少 package.json | 建立根目錄 package.json |
| `relation "users" does not exist` | 沒執行 migration | startCommand 加入 migrate |
| `getaddrinfo ENOTFOUND` | Build 階段無法連 DB | 改在 startCommand 執行 migrate |

---

## LINE Login 整合

### LINE Developers 設定

1. 建立 LINE Login Channel
2. 設定 Callback URL：`https://your-app.railway.app/auth/line/callback`
3. 取得 Channel ID 和 Channel Secret

### 登入流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   用戶      │     │   系統      │     │   LINE      │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │  1. 點擊登入      │                   │
       │──────────────────>│                   │
       │                   │                   │
       │  2. 重導向        │                   │
       │<──────────────────│                   │
       │                   │                   │
       │  3. LINE 登入頁面 │                   │
       │───────────────────────────────────────>│
       │                   │                   │
       │  4. 授權同意      │                   │
       │<───────────────────────────────────────│
       │                   │                   │
       │  5. Callback + Code                   │
       │──────────────────>│                   │
       │                   │                   │
       │                   │  6. 換取 Token    │
       │                   │──────────────────>│
       │                   │                   │
       │                   │  7. Token + Profile│
       │                   │<──────────────────│
       │                   │                   │
       │  8. JWT Token     │                   │
       │<──────────────────│                   │
       │                   │                   │
```

### 實作範例

```python
# app/services/auth/line_auth.py
import httpx
from app.config import settings

class LineAuthService:
    AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
    TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
    PROFILE_URL = "https://api.line.me/v2/profile"
    
    def get_auth_url(self, state: str) -> str:
        """產生 LINE 授權 URL"""
        params = {
            "response_type": "code",
            "client_id": settings.LINE_CHANNEL_ID,
            "redirect_uri": settings.LINE_CALLBACK_URL,
            "state": state,
            "scope": "profile openid",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"
    
    async def get_token(self, code: str) -> dict:
        """用授權碼換取 Token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.LINE_CALLBACK_URL,
                    "client_id": settings.LINE_CHANNEL_ID,
                    "client_secret": settings.LINE_CHANNEL_SECRET,
                }
            )
            return response.json()
    
    async def get_profile(self, access_token: str) -> dict:
        """取得用戶資料"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            return response.json()
```

---

## 安裝與部署

### 本地開發環境

#### 1. Clone 專案
```bash
git clone https://github.com/your-repo/lottery-group.git
cd lottery-group
```

#### 2. 建立虛擬環境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 3. 安裝依賴
```bash
pip install -r requirements.txt
```

#### 4. 環境設定
```bash
cp .env.example .env
# 編輯 .env 設定資料庫等參數
```

#### 5. 初始化資料庫
```bash
python scripts/init_db.py
python scripts/seed_data.py
```

#### 6. 啟動開發伺服器
```bash
# 啟動 Flet Web
flet run main.py --web --port 8000

# 或啟動 FastAPI（僅 API）
uvicorn app.main:app --reload
```

### Railway 部署

#### 1. 準備部署檔案
確保專案根目錄有以下檔案：
- `package.json`
- `nixpacks.toml`
- `railway.json`
- `requirements.txt`

#### 2. 連結 Railway
```bash
# 安裝 Railway CLI
npm install -g @railway/cli

# 登入
railway login

# 連結專案
railway link
```

#### 3. 設定環境變數
在 Railway Dashboard 設定：
- `DATABASE_URL`（新增 PostgreSQL 服務後自動產生）
- `JWT_SECRET`
- `LINE_CHANNEL_ID`
- `LINE_CHANNEL_SECRET`
- `LINE_CALLBACK_URL`

#### 4. 部署
```bash
# 推送到 Railway
railway up

# 或透過 Git 自動部署
git push origin main
```

#### 5. 首次部署後
修改 `railway.json`，移除 migrate 指令：
```json
{
  "deploy": {
    "startCommand": "python main.py"
  }
}
```

### 環境變數說明

```env
# ===== 資料庫 =====
DATABASE_URL=postgresql://user:pass@host:5432/lottery

# ===== JWT 認證 =====
JWT_SECRET=your-secret-key-at-least-32-characters-long
JWT_EXPIRES_IN=7d

# ===== LINE Login =====
LINE_CHANNEL_ID=1234567890
LINE_CHANNEL_SECRET=abcdef1234567890
LINE_CALLBACK_URL=https://your-app.railway.app/auth/line/callback

# ===== 應用程式 =====
APP_NAME=Lottery Group
APP_ENV=production
PORT=8000
DEBUG=false

# ===== 檔案儲存 =====
UPLOAD_DIR=/uploads
EXPORT_DIR=/exports
BACKUP_DIR=/backups

# ===== LINE Notify（通知用） =====
LINE_NOTIFY_TOKEN=your-notify-token
```

### 資料庫初始化

Railway 的 PostgreSQL 會自動提供 `DATABASE_URL`。首次部署時：

1. 在 Railway 新增 PostgreSQL 服務
2. 連結到應用程式
3. 確保 `railway.json` 的 startCommand 包含 migrate
4. 部署後移除 migrate 指令

---

## 使用指南

### 快速開始

#### 1. 建立系列團
管理員建立一個新的系列團，設定名稱、允許彩種、提領政策。

#### 2. 邀請成員
透過邀請連結或直接添加，讓成員加入系列團。

#### 3. 成員入金
成員加入時投入初始金額，之後可透過加碼增加份額。

#### 4. 開始新期
管理員選擇彩種，設定集資截止時間，開始新一期。

#### 5. 購買彩券
集資截止後，管理員購買彩券並上傳照片和號碼。

#### 6. 等待開獎
系統自動或手動記錄開獎結果。

#### 7. 執行結算
對獎完成後，執行結算，系統自動計算分配並更新資金池。

#### 8. 下一期
資金自動滾入下期，開始新的循環。

---

## 未來擴充

### 短期（1-3 個月）
- [ ] 手機 APP（React Native）
- [ ] 統計圖表視覺化
- [ ] 自動開獎結果抓取
- [ ] 批次對獎功能

### 中期（3-6 個月）
- [ ] 公開團功能
- [ ] 團搜尋與加入
- [ ] 團評價系統
- [ ] 進階權限管理

### 長期（6-12 個月）
- [ ] AI 選號建議
- [ ] 社群功能
- [ ] 多國彩券支援
- [ ] 區塊鏈驗證

---

## 附錄

### A. 彩種獎金結構

#### 威力彩
| 獎項 | 對中 | 獎金 |
|------|------|------|
| 頭獎 | 6+1 | 累積獎金 |
| 貳獎 | 6+0 | $150,000 |
| 參獎 | 5+1 | $20,000 |
| 肆獎 | 5+0 | $4,000 |
| 伍獎 | 4+1 | $800 |
| 陸獎 | 4+0 | $400 |
| 柒獎 | 3+1 | $200 |
| 捌獎 | 2+1 | $100 |
| 普獎 | 1+1 | $100 |

#### 大樂透
| 獎項 | 對中 | 獎金 |
|------|------|------|
| 頭獎 | 6 | 累積獎金 |
| 貳獎 | 5+特 | $150,000 |
| 參獎 | 5 | $25,000 |
| 肆獎 | 4+特 | $12,500 |
| 伍獎 | 4 | $2,000 |
| 陸獎 | 3+特 | $1,000 |
| 柒獎 | 2+特 | $400 |
| 普獎 | 3 | $400 |

### B. 常見問題

#### Q: 佔比如何計算？
A: 佔比 = 您的有效份額 / 所有成員有效份額總和。有效份額為購買前的資金池份額。

#### Q: 獎金如何分配？
A: 獎金按佔比分配。若總獎金超過 $5,000，需扣除 20% 稅金後再分配。

#### Q: 可以中途退出嗎？
A: 若系列團為「彈性模式」，可申請減碼或退出；若為「死戰到底」，則不可中途提領。

#### Q: 資料會保存多久？
A: 所有資料永久保存，可隨時匯出備份。

### C. 核心演算法

#### 佔比計算
```python
def calculate_ratio(member_share: Decimal, total_pool: Decimal) -> Decimal:
    """
    佔比 = 成員份額 / 總資金池
    """
    if total_pool == 0:
        return Decimal('0')
    return member_share / total_pool
```

#### 有效貢獻計算
```python
def calculate_effective_contribution(
    member_share: Decimal,
    total_pool: Decimal,
    total_spent: Decimal
) -> Decimal:
    """
    有效貢獻 = 成員份額 × (總花費 / 總資金池)
    
    例如：
    - 成員份額：$500
    - 總資金池：$2,000
    - 實際購買：$1,400
    - 有效貢獻 = $500 × ($1,400 / $2,000) = $350
    """
    if total_pool == 0:
        return Decimal('0')
    spending_ratio = total_spent / total_pool
    return member_share * spending_ratio
```

#### 滾入計算
```python
def calculate_carryover(
    member_share: Decimal,
    effective_contribution: Decimal
) -> Decimal:
    """
    滾入 = 成員份額 - 有效貢獻
    
    例如：
    - 成員份額：$500
    - 有效貢獻：$350
    - 滾入：$150
    """
    return member_share - effective_contribution
```

#### 獎金分配
```python
def distribute_prize(
    effective_contribution: Decimal,
    total_spent: Decimal,
    total_prize: Decimal
) -> Decimal:
    """
    獎金份額 = (有效貢獻 / 總花費) × 總獎金
    
    例如：
    - 有效貢獻：$350
    - 總花費：$1,400
    - 總獎金：$4,000
    - 獎金份額 = ($350 / $1,400) × $4,000 = $1,000
    """
    if total_spent == 0:
        return Decimal('0')
    return (effective_contribution / total_spent) * total_prize
```

#### 結算後新份額
```python
def calculate_new_share(
    carryover: Decimal,
    prize_share: Decimal
) -> Decimal:
    """
    新份額 = 滾入 + 獎金份額
    
    例如：
    - 滾入：$150
    - 獎金份額：$1,000
    - 新份額：$1,150
    """
    return carryover + prize_share
```

#### 完整結算範例
```
【第 5 期結算】

資金池：$2,000
購買：14 注 × $100 = $1,400
中獎：$4,000（扣稅後 $3,200）

成員 A（份額 $500，佔比 25%）
├── 有效貢獻 = $500 × ($1,400 / $2,000) = $350
├── 滾入 = $500 - $350 = $150
├── 獎金 = ($350 / $1,400) × $3,200 = $800
└── 結算後份額 = $150 + $800 = $950

成員 B（份額 $800，佔比 40%）
├── 有效貢獻 = $800 × 0.7 = $560
├── 滾入 = $800 - $560 = $240
├── 獎金 = ($560 / $1,400) × $3,200 = $1,280
└── 結算後份額 = $240 + $1,280 = $1,520

成員 C（份額 $700，佔比 35%）
├── 有效貢獻 = $700 × 0.7 = $490
├── 滾入 = $700 - $490 = $210
├── 獎金 = ($490 / $1,400) × $3,200 = $1,120
└── 結算後份額 = $210 + $1,120 = $1,330

驗證：
- 總有效貢獻 = $350 + $560 + $490 = $1,400 ✓
- 總滾入 = $150 + $240 + $210 = $600 ✓
- 總獎金分配 = $800 + $1,280 + $1,120 = $3,200 ✓
- 新資金池 = $950 + $1,520 + $1,330 = $3,800 ✓
```

---

### D. 設計原則

#### 資料庫設計原則

##### 1. 只增不改 (Additive Only)
```
✅ 允許的操作：
- CREATE TABLE（新增表）
- ADD COLUMN（新增欄位，必須有 DEFAULT）
- CREATE INDEX（新增索引）

❌ 禁止的操作：
- DROP TABLE（刪除表）
- DROP COLUMN（刪除欄位）
- ALTER COLUMN TYPE（修改類型）
- RENAME COLUMN（重新命名）
```

##### 2. 向後相容
```sql
-- 正確：新增欄位有預設值
ALTER TABLE users ADD COLUMN IF NOT EXISTS 
    notification_enabled BOOLEAN DEFAULT true;

-- 錯誤：新增欄位沒有預設值
ALTER TABLE users ADD COLUMN 
    notification_enabled BOOLEAN NOT NULL;
```

##### 3. 棄用而非刪除
```sql
-- 舊欄位標記為 deprecated，但不刪除
-- 程式碼中停止使用
-- 文件中標記

COMMENT ON COLUMN users.old_field IS 
    'DEPRECATED since v1.2.0 - use new_field instead';
```

##### 4. 完整記錄
- 所有金流記錄在 `user_ledger`
- 所有操作記錄在 `event_log`
- 每期結算建立 `period_snapshots`
- 餘額可從帳本重新計算

#### 系統升級策略

```
┌─────────────────────────────────────────────────────────────────┐
│                      升級流程                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【升級前】                                                      │
│  □ 確認 Migration 向後相容                                      │
│  □ 測試環境完整測試                                              │
│  □ 建立資料庫備份                                                │
│  □ 準備回滾計畫                                                  │
│                                                                 │
│  【升級中】                                                      │
│  □ 執行 Migration（不停機）                                      │
│  □ 部署新版程式                                                  │
│  □ 健康檢查                                                      │
│                                                                 │
│  【升級後】                                                      │
│  □ 監控錯誤日誌                                                  │
│  □ 功能測試                                                      │
│  □ 確認 Migration 狀態                                          │
│                                                                 │
│  【回滾（如需要）】                                              │
│  □ 部署舊版程式（資料庫不需回滾，因為向後相容）                  │
│  □ 確認系統恢復正常                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### E. 備份策略

#### 備份類型

| 類型 | 頻率 | 保留時間 | 說明 |
|------|------|----------|------|
| 完整備份 | 每日 02:00 | 90 天 | pg_dump 完整備份 |
| 增量備份 | 每 6 小時 | 30 天 | 只備份變更 |
| 即時備份 | 升級前 | 永久 | Migration 前自動建立 |

#### 備份驗證

```python
# 每日自動驗證備份完整性
def verify_backup(backup_id: int) -> bool:
    backup = get_backup(backup_id)
    
    # 1. 檢查檔案存在
    if not os.path.exists(backup.file_path):
        return False
    
    # 2. 驗證 checksum
    current_checksum = calculate_sha256(backup.file_path)
    if current_checksum != backup.checksum:
        return False
    
    # 3. 嘗試還原到測試庫（可選）
    return True
```

#### 使用者資料匯出

用戶可自行匯出的資料：
- **PDF 報告**：系列團報告、對帳單、個人記錄
- **CSV 資料**：原始交易記錄
- **JSON 備份**：完整資料備份

---

### F. 權限設計

#### 角色定義

| 角色 | 說明 | 權限 |
|------|------|------|
| `super_admin` | 系統管理員 | 全部權限 |
| `series_creator` | 系列團建立者 | 管理所建立的系列團 |
| `series_admin` | 系列團管理員 | 管理被授權的系列團 |
| `member` | 一般成員 | 參與、查看自己的資料 |

#### 資源權限

```python
# 系列團層級
can_view_series(user, series)      # 成員可查看
can_edit_series(user, series)      # 管理員可編輯
can_manage_members(user, series)   # 管理員可管理成員
can_start_period(user, series)     # 管理員可開新期
can_approve_requests(user, series) # 管理員可審核申請

# 個人資料
can_view_personal(user, owner)     # 只有本人可查看
# 個人彩券記錄：管理員不可見
```

---

### G. API 狀態碼

| 代碼 | 說明 | 範例 |
|------|------|------|
| 200 | 成功 | GET 請求成功 |
| 201 | 建立成功 | POST 建立資源成功 |
| 400 | 請求錯誤 | 參數格式錯誤 |
| 401 | 未認證 | Token 無效或過期 |
| 403 | 權限不足 | 無權限存取此資源 |
| 404 | 找不到 | 資源不存在 |
| 409 | 衝突 | 狀態不允許此操作 |
| 422 | 驗證失敗 | 業務邏輯驗證失敗 |
| 500 | 伺服器錯誤 | 系統內部錯誤 |

#### 錯誤回應格式

```json
{
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

---

### H. 詞彙表

| 中文 | 英文 | 說明 |
|------|------|------|
| 系列團 | Series | 長期合作的團體單位 |
| 單期團 | Group / Period | 單一期的購買 |
| 資金池 | Pool | 團體共同資金 |
| 份額 | Share | 成員在資金池中的金額 |
| 佔比 | Ratio | 成員份額佔總池的比例 |
| 加碼 | Top-up | 增加份額 |
| 減碼 | Withdraw | 減少份額 |
| 滾入 | Carryover | 未花完自動滾入下期 |
| 有效貢獻 | Effective Contribution | 實際用於購買的金額 |
| 帳本 | Ledger | 金流記錄 |
| 快照 | Snapshot | 某時間點的完整狀態 |
| 死戰到底 | No-withdraw Mode | 資金只進不出模式 |
| 彈性模式 | Flexible Mode | 允許減碼/退出模式 |

---

### I. 開發檢查清單

#### 新功能開發
- [ ] 需求確認
- [ ] 資料表設計（遵循只增不改）
- [ ] API 設計
- [ ] Service 實作
- [ ] 單元測試
- [ ] 整合測試
- [ ] 文件更新
- [ ] Code Review

#### 資料庫變更
- [ ] Migration 檔案建立
- [ ] 確認向後相容
- [ ] 測試環境驗證
- [ ] 備份確認
- [ ] 正式環境執行
- [ ] 驗證狀態

#### 上線檢查
- [ ] 功能測試通過
- [ ] 效能測試通過
- [ ] 安全性檢查
- [ ] 備份完成
- [ ] 監控設定
- [ ] 回滾計畫準備

---

### J. 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| 0.1.0 | 2024-12-30 | 初始規劃文件 |
| - | - | Phase 1 開發中 |

---

### K. 開發路線圖

```
2024 Q4                    2025 Q1                    2025 Q2
───────────────────────────────────────────────────────────────►

[Phase 0: 基礎建設]
     ██████████
     2 週
     
          [Phase 1: 核心功能]
               ████████████████████████████
               4 週
               
                              [Phase 2: 進階功能]
                                   ████████████████████
                                   3 週
                                   
                                             [Phase 3: 優化上線]
                                                  ████████████
                                                  2 週

里程碑：
─────────────────────────────────────────────────────────────
 ↑           ↑                    ↑              ↑
基礎完成   核心功能完成       進階功能完成    正式上線
```

---

### L. SELA 專案規範

#### .project-meta.json（必要）
```json
{
  "$schema": "project-meta-v1",
  "name": "lottery-group",
  "version": "1.0.0",
  "type": "web",
  "status": "active",
  "description": "團購彩券系統 - Flet Web + FastAPI + Railway",
  "tags": ["Flet", "FastAPI", "Railway", "LINE Login", "PostgreSQL"],
  "created_at": "2024-12-30",
  "docs": {
    "readme": "README.md",
    "changelog": "CHANGELOG.md"
  },
  "scripts": {
    "dev": "flet run main.py --web --port 8000",
    "api": "uvicorn app.main:app --reload",
    "migrate": "python scripts/migrate.py"
  },
  "deployment": {
    "platform": "railway",
    "database": "postgresql"
  }
}
```

#### 必備檔案
```
project-root/
├── .project-meta.json    # 專案元資料（必要）
├── README.md             # 專案說明（必要）
├── CHANGELOG.md          # 版本變更紀錄（必要）
└── .gitignore            # Git 忽略規則
```

#### Git Commit 格式
```
<type>: <subject>

type: feat | fix | docs | style | refactor | test | chore
```

#### 分支命名
| 類型 | 格式 | 範例 |
|------|------|------|
| 功能 | `feature/<name>` | `feature/user-login` |
| 修復 | `fix/<name>` | `fix/header-overflow` |
| 發布 | `release/<version>` | `release/1.2.0` |

---

### M. SELA 品牌規範

#### 色彩（不可更改）
```python
BRAND_ORANGE = "#FA7A35"      # SELA 企業識別色（愛馬仕橘）

# 輔助色
GREY_LIGHT = ft.Colors.GREY_50           # 左側面板背景
BLUE_GREY_LIGHT = ft.Colors.BLUE_GREY_50 # 右側面板背景
BLUE_GREY_700 = ft.Colors.BLUE_GREY_700  # 標題文字
```

#### 字型
```python
FONT_FAMILY = "Microsoft JhengHei UI"  # 主要 UI 字型
FONT_MONOSPACE = "Consolas"            # 等寬字型
```

#### LOGO 規範（🚫 不可更改樣式）
```python
LOGO_TEXT = "SELA"
LOGO_COLOR = "#FA7A35"            # 不可更改
LOGO_WEIGHT = ft.FontWeight.BOLD  # 不可更改
# 僅尺寸可隨螢幕調整：36-56px
```

#### UI 尺寸規範

**螢幕支援**
- 最低標準：1440 × 900
- 核心原則：以小螢幕為基準設計

**對話框尺寸（固定值）**
```python
DIALOG_SMALL = (350, 280)     # 確認刪除
DIALOG_NORMAL = (400, 380)    # 新增/編輯
DIALOG_LARGE = (420, 450)     # 含時間欄位
# ⚠️ 對話框絕對不要超過：寬度 450、高度 480
```

**主視窗佈局**
```
┌─────────────────────────────────────────────────────────┐
│  [Tab1] [Tab2] [Tab3] ...                               │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐      │
│  │   左側面板 (expand=2)│  │  右側面板 (expand=1) │      │
│  │   GREY_50 背景       │  │  BLUE_GREY_50 背景   │      │
│  └─────────────────────┘  └─────────────────────┘      │
├─────────────────────────────────────────────────────────┤
│  [操作按鈕列]                                            │
└─────────────────────────────────────────────────────────┘
```

#### UI 元件規範

**必須使用 `dense=True`**
```python
ft.TextField(label="欄位", dense=True, ...)
ft.Dropdown(label="選項", dense=True, ...)
```

**必須設定 scroll**
```python
ft.Column([...], scroll=ft.ScrollMode.AUTO)
```

---

## 授權

MIT License

---

## 聯絡方式

- Email: your-email@example.com
- GitHub: https://github.com/your-repo/lottery-group

---

*最後更新：2024-12-30*
