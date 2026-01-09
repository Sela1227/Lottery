# 🎯 Step 2 核心功能 - 完成總結

## ✅ 已建立的檔案

### 📦 資料模型(7 個)

| 檔案 | 說明 |
|------|------|
| `models/lottery_type.py` | 彩種定義(威力彩/大樂透/今彩539) |
| `models/series.py` | 系列團 + 邀請碼 |
| `models/member.py` | 系列團成員 |
| `models/group.py` | 單期團 + 每期貢獻記錄 |
| `models/ticket.py` | 彩券 |
| `models/ledger.py` | 帳本 + 事件日誌 + 快照 |
| `models/__init__.py` | 模組導出 |

### 📋 Schema(3 個)

| 檔案 | 說明 |
|------|------|
| `schemas/series.py` | 系列團/邀請碼/成員 Schema |
| `schemas/group.py` | 單期團/彩券/結算 Schema |
| `schemas/__init__.py` | 模組導出 |

### ⚙️ 服務層(4 個)

| 檔案 | 說明 |
|------|------|
| `services/series_service.py` | 系列團服務(建立/加入/邀請/加碼) |
| `services/group_service.py` | 單期團 + 彩券 + 對獎服務 |
| `services/settlement_service.py` | 結算服務 |
| `services/__init__.py` | 模組導出 |

### 🔌 API 端點(2 個新增)

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
