# SELA 樂透一路發 - 已完成功能總結

> **最後更新**：2026-01-11  
> **整體進度**：約 60%

---

## 📊 開發階段總覽

| 階段 | 狀態 | 完成度 | 說明 |
|:----:|:----:|:------:|------|
| Step 1 | ✅ 完成 | 100% | 核心基礎設施 |
| Step 2 | ✅ 完成 | 100% | 團購流程 |
| Step 3 | 🔄 部分 | 70% | 統計與錢包 |
| Step 4 | ⏳ 待開發 | 30% | 進階功能 |

---

## Step 1：核心基礎設施 ✅

### 認證系統
- LINE Login OAuth 2.0 整合
- JWT Token 驗證機制
- 首位用戶自動成為系統管理員

### 用戶管理
- 用戶資料模型（角色權限）
- 暱稱、Email、電話設定
- 管理員手動升降權

### 資料庫
- PostgreSQL 基礎架構
- 所有核心表格建立完成

---

## Step 2：團購流程 ✅

### 集資管理
| 功能 | 說明 |
|------|------|
| 建立集資 | 選擇彩種（單選）、設定份額 |
| 邀請碼 | 產生、加入、過期管理 |
| 成員管理 | 加入、加碼、份額追蹤 |
| 結束集資 | 結算並關閉 |

### 單期團管理
| 功能 | 說明 |
|------|------|
| 開新期 | 指定期數、截止時間 |
| 鎖定集資 | 停止新增貢獻 |
| 記錄購買 | 實際購買金額 |
| 彩券管理 | 新增/編輯號碼 |

### 開獎與結算
| 功能 | 說明 |
|------|------|
| 輸入開獎 | 手動輸入開獎號碼 |
| 對獎 | 自動比對所有彩券 |
| 結算預覽 | 計算分配比例 |
| 執行結算 | 分配獎金、記錄帳本 |

### 支援彩種

| 代碼 | 名稱 | 每注價格 | 開獎時間 |
|------|------|:--------:|----------|
| power | 威力彩 | $100 | 週一、週四 20:30 |
| super | 大樂透 | $50 | 週二、週五 20:30 |
| daily539 | 今彩539 | $50 | 每天 20:30 |

### 帳本系統
- 所有金流異動記錄
- 交易類型追蹤（加碼、購買、獎金等）
- 事件日誌與快照

---

## Step 3：統計與錢包 🔄

### 已完成 ✅

**錢包功能**
- 錢包概覽 API
- 集資份額明細
- 交易記錄查詢
- 前端頁面

**統計報表**
- 整體統計（ROI、投資、獎金）
- 月度趨勢圖
- 集資績效
- 中獎記錄
- 彩種分析

**個人彩券**
- 新增個人彩券記錄
- 手選/電腦選號
- 對獎功能
- 個人統計

**成就徽章系統**
- 14 種預設成就
- 進度追蹤
- 點數與排名

### 開獎資訊本地化 ✅

**lottery_draws 資料表**
- 儲存歷史開獎資料
- UPSERT 更新邏輯
- 累積獎金追蹤

**開獎同步**
- 資料來源：lotto-8.com
- 管理員手動同步
- localStorage 防止重複同步

**號碼統計 API**
- 熱門號碼分析
- 冷門號碼分析
- 遺漏期數統計

**前端開獎專區**
- 分頁顯示歷史開獎
- 彩種切換 Tab
- 開獎號碼視覺化

---

## Step 4：進階功能 ⏳

### 已完成 ✅

**設定頁面**
- 個人資料修改
- 通知設定預留
- 登出功能

**首次登入引導**
- 新用戶歡迎彈窗
- 設定暱稱提示

**Dashboard 開獎卡片**
- 威力彩/大樂透最新開獎
- 累積獎金顯示

**自動對獎與結算**
- 同步開獎後自動對獎
- 一鍵對獎+結算
- 批量處理 API

### 待開發 ⏳

- [ ] Web Push 推播通知
- [ ] 開獎提醒
- [ ] 中獎通知
- [ ] 結算通知

---

## 管理員後台 ✅

| 功能 | 路徑 | 說明 |
|------|------|------|
| 用戶管理 | `/admin` | 列表、停用、角色修改 |
| 集資管理 | `/admin` | 管理所有集資 |
| 事件日誌 | `/admin` | 系統事件記錄 |
| 開獎同步 | `/admin/lottery` | 同步開獎資訊 |

---

## 重要修正記錄

### 名稱統一
- 所有「系列團」「集資團」統一為「**集資**」
- 適用於所有頁面和 API 回應

### 彩種選擇
- 從多選改為單選
- 份額需為彩種價格的倍數

### 彩種初始化
- Dockerfile 啟動時執行 seed_data.py
- 確保 lottery_types 表有資料

---

## API 端點總覽

### 認證
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/auth/line/login` | LINE 登入 |
| GET | `/api/v1/auth/callback` | 登入回調 |
| GET | `/api/v1/users/me` | 當前用戶 |
| PUT | `/api/v1/users/me` | 更新資料 |

### 集資
| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/v1/series` | 建立集資 |
| GET | `/api/v1/series` | 我的集資 |
| GET | `/api/v1/series/{id}` | 集資詳情 |
| POST | `/api/v1/series/{id}/invitations` | 建立邀請碼 |
| POST | `/api/v1/series/join` | 加入集資 |
| POST | `/api/v1/series/{id}/members/me/topup` | 加碼 |

### 單期團
| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/v1/series/{id}/groups` | 開新期 |
| GET | `/api/v1/groups/{id}` | 期數詳情 |
| POST | `/api/v1/groups/{id}/lock` | 鎖定 |
| POST | `/api/v1/groups/{id}/purchase` | 購買 |
| POST | `/api/v1/groups/{id}/draw` | 開獎 |
| POST | `/api/v1/groups/{id}/settle` | 結算 |

### 彩券
| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/v1/groups/{id}/tickets` | 新增 |
| GET | `/api/v1/groups/{id}/tickets` | 列表 |
| PUT | `/api/v1/tickets/{id}` | 更新 |

### 統計
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/statistics/overall` | 整體統計 |
| GET | `/api/v1/statistics/monthly` | 月度統計 |
| GET | `/api/v1/statistics/series-performance` | 集資績效 |
| GET | `/api/v1/statistics/winning-records` | 中獎記錄 |

### 錢包
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/wallet/overview` | 概覽 |
| GET | `/api/v1/wallet/pool-shares` | 份額 |
| GET | `/api/v1/wallet/transactions` | 交易記錄 |

### 開獎
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/lottery/latest` | 最新開獎 |
| POST | `/api/v1/lottery/sync` | 同步開獎 |
| GET | `/api/v1/lottery/draws` | 歷史開獎 |
| GET | `/api/v1/lottery/stats/numbers` | 號碼統計 |

### 對獎結算
| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/v1/check/auto` | 自動對獎 |
| POST | `/api/v1/check/settle/auto` | 自動結算 |
| GET | `/api/v1/check/pending` | 待處理列表 |

---

## 資料庫表格

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

---

*SELA 樂透一路發 © 2026*
