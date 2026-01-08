# 🎯 Step 2 核心功能 - 完成總結

## ✅ 已建立的檔案

### 📦 資料模型（7 個）

| 檔案 | 說明 |
|------|------|
| `models/lottery_type.py` | 彩種定義（威力彩/大樂透/今彩539） |
| `models/series.py` | 系列團 + 邀請碼 |
| `models/member.py` | 系列團成員 |
| `models/group.py` | 單期團 + 每期貢獻記錄 |
| `models/ticket.py` | 彩券 |
| `models/ledger.py` | 帳本 + 事件日誌 + 快照 |
| `models/__init__.py` | 模組導出 |

### 📋 Schema（3 個）

| 檔案 | 說明 |
|------|------|
| `schemas/series.py` | 系列團/邀請碼/成員 Schema |
| `schemas/group.py` | 單期團/彩券/結算 Schema |
| `schemas/__init__.py` | 模組導出 |

### ⚙️ 服務層（4 個）

| 檔案 | 說明 |
|------|------|
| `services/series_service.py` | 系列團服務（建立/加入/邀請/加碼） |
| `services/group_service.py` | 單期團 + 彩券 + 對獎服務 |
| `services/settlement_service.py` | 結算服務 |
| `services/__init__.py` | 模組導出 |

### 🔌 API 端點（2 個新增）

| 檔案 | 說明 |
|------|------|
| `api/v1/series.py` | 系列團 API |
| `api/v1/groups.py` | 單期團/彩券/結算 API |

---

## 🔌 新增 API 端點

### 系列團 API
| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/v1/series` | 建立系列團 |
| GET | `/api/v1/series` | 取得我參與的系列團 |
| GET | `/api/v1/series/{id}` | 取得系列團詳情 |
| PUT | `/api/v1/series/{id}` | 更新系列團 |
| POST | `/api/v1/series/{id}/end` | 結束系列團 |
| POST | `/api/v1/series/{id}/invitations` | 建立邀請碼 |
| POST | `/api/v1/series/join` | 透過邀請碼加入 |
| GET | `/api/v1/series/{id}/members` | 取得成員列表 |
| POST | `/api/v1/series/{id}/members/me/topup` | 加碼 |

### 單期團 API
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/lottery-types` | 取得所有彩種 |
| POST | `/api/v1/series/{id}/groups` | 開新期 |
| GET | `/api/v1/series/{id}/groups` | 取得單期團列表 |
| GET | `/api/v1/groups/{id}` | 取得單期團詳情 |
| POST | `/api/v1/groups/{id}/lock` | 鎖定集資 |
| POST | `/api/v1/groups/{id}/purchase` | 記錄購買 |
| POST | `/api/v1/groups/{id}/draw` | 輸入開獎結果 |
| POST | `/api/v1/groups/{id}/check-tickets` | 對獎所有彩券 |

### 彩券 API
| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/v1/groups/{id}/tickets` | 新增彩券 |
| GET | `/api/v1/groups/{id}/tickets` | 取得彩券列表 |
| PUT | `/api/v1/tickets/{id}` | 更新彩券 |

### 結算 API
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/groups/{id}/settlement-preview` | 結算預覽 |
| POST | `/api/v1/groups/{id}/settle` | 執行結算 |

---

## 🎰 支援彩種

| 代碼 | 名稱 | 每注價格 | 開獎時間 |
|------|------|----------|----------|
| `power` | 威力彩 | $100 | 週一、週四 20:30 |
| `super` | 大樂透 | $50 | 週二、週五 20:30 |
| `daily539` | 今彩539 | $50 | 每天 20:30 |

---

## 📊 對獎邏輯

### 威力彩
```
頭獎: 6+1 (累積獎金)
貳獎: 6+0 ($150,000)
參獎: 5+1 ($20,000)
肆獎: 5+0 ($4,000)
伍獎: 4+1 ($800)
陸獎: 4+0 ($400)
柒獎: 3+1 ($200)
捌獎: 2+1 ($100)
普獎: 1+1 ($100)
```

### 大樂透
```
頭獎: 6 (累積獎金)
貳獎: 5+特 ($150,000)
參獎: 5 ($25,000)
肆獎: 4+特 ($12,500)
伍獎: 4 ($2,000)
陸獎: 3+特 ($1,000)
柒獎: 2+特 ($400)
普獎: 3 ($400)
```

---

## 💰 結算公式

```
有效貢獻 = 份額 × (總花費 / 總資金池)
貢獻比例 = 有效貢獻 / 所有成員有效貢獻總和
滾入金額 = 份額 - 有效貢獻
獎金份額 = 總獎金(扣稅後) × 貢獻比例
結算後份額 = 滾入 + 獎金
```

**稅率**：總獎金 > $5,000 扣 20%

---

## 🚀 部署步驟

### 1. 解壓縮到專案目錄
```bash
# 在專案根目錄
unzip sela-step2.zip -d app/
```

### 2. 更新 app/main.py
將 `app_main.py` 的內容合併到現有的 `app/main.py`

### 3. 更新 models/__init__.py
合併新的模型導出

### 4. 推送部署
```bash
git add .
git commit -m "feat: Step 2 核心功能完成"
git push
```

---

## ⏭️ Step 3 預覽

Step 3 將實作金流管理：
- 加碼/減碼申請流程（PoolChangeRequest）
- 銀行帳戶管理
- 智慧配對（同行優先）
- 統計報表
- 個人彩券記錄（私人）
