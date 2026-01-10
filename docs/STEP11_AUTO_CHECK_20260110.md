# SELA 樂透一路發 - 自動對獎與結算功能

## 🎯 功能說明

新增自動對獎與結算功能：
1. 管理員同步開獎資料後自動對獎所有待對獎的團
2. 支援對獎後自動結算，或手動分開執行

## 📦 檔案清單

```
app/
├── api/v1/
│   ├── check.py       # 新增：對獎與結算 API 端點
│   └── lottery.py     # 更新：sync 後自動對獎
├── services/
│   ├── auto_check.py  # 新增：自動對獎服務
│   └── auto_settle.py # 新增：自動結算服務
└── main.py            # 更新：加入 check_router
```

## 🚀 部署步驟

```bash
cd /Users/sela/Documents/Python/線上威力彩
unzip -o ~/Downloads/step11_auto_check_settle.zip
git add .
git commit -m "feat: 自動對獎與結算功能"
git push
```

## 🔧 API 端點

### 對獎 API

| 端點 | 說明 |
|------|------|
| `POST /api/v1/check/group` | 對獎單一團（可選自動結算） |
| `POST /api/v1/check/auto?auto_settle=true` | 自動對獎所有待對獎團 |
| `POST /api/v1/check/by-lottery` | 依彩種對獎 |
| `GET /api/v1/check/pending?status=purchased` | 查看待對獎團 |

### 結算 API

| 端點 | 說明 |
|------|------|
| `POST /api/v1/check/settle/group` | 結算單一團 |
| `POST /api/v1/check/settle/auto` | 自動結算所有已開獎團 |
| `POST /api/v1/check/settle/series/{id}` | 結算指定系列所有期 |
| `GET /api/v1/check/pending?status=drawn` | 查看待結算團 |

### 統計 API

```
GET /api/v1/check/stats
```
回傳：待對獎數、待結算數、已結算數、總獎金

## ⚙️ 運作流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  PURCHASED  │ ──▶ │   DRAWN     │ ──▶ │  SETTLED    │
│   已購買     │     │   已開獎     │     │   已結算     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
    自動對獎            自動結算           獎金分配
```

### 方式一：分開執行

1. **同步開獎** → 自動對獎 → 狀態變 `DRAWN`
2. **手動結算** → 分配獎金 → 狀態變 `SETTLED`

### 方式二：一鍵完成

```
POST /api/v1/check/auto?auto_settle=true
```
對獎後直接結算，一步到位

## 📊 結算邏輯

1. **計算有效貢獻**
   - 有效貢獻 = 份額 × (實際花費 / 總資金池)
   
2. **計算貢獻比例**
   - 比例 = 個人有效貢獻 / 總有效貢獻

3. **分配獎金**
   - 獎金份額 = 總獎金(扣稅後) × 比例
   - 滾入金額 = 份額 - 有效貢獻
   - 結算後份額 = 滾入 + 獎金

4. **記錄帳本**
   - 購買扣除 (`POOL_PURCHASE`)
   - 獎金分配 (`POOL_PRIZE`)

## 🔍 狀態說明

| 狀態 | 說明 | 下一步 |
|------|------|--------|
| `collecting` | 集資中 | 鎖定 |
| `locked` | 已鎖定 | 購買 |
| `purchased` | 已購買 | **對獎** |
| `drawn` | 已開獎 | **結算** |
| `settled` | 已結算 | 完成 |

## 💡 使用建議

- **日常運營**：使用 `POST /api/v1/check/auto?auto_settle=true` 一鍵完成
- **需要審核**：先對獎，確認結果後再手動結算
- **批量處理**：使用 `/settle/series/{id}` 處理整個系列
