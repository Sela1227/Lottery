# SELA 樂透一路發 - 自動對獎功能

## 🎯 功能說明

新增自動對獎功能，管理員同步開獎資料後會自動對獎所有待對獎的團。

## 📦 檔案清單

```
app/
├── api/v1/
│   ├── check.py      # 新增：對獎 API 端點
│   └── lottery.py    # 更新：sync 後自動對獎
├── services/
│   └── auto_check.py # 新增：自動對獎服務
└── main.py           # 更新：加入 check_router
```

## 🔧 部署步驟

```bash
cd /Users/sela/Documents/Python/線上威力彩
unzip -o ~/Downloads/step11_auto_check.zip
git add .
git commit -m "feat: 自動對獎功能"
git push
```

## 🚀 API 端點

### 1. 手動對獎單一團
```
POST /api/v1/check/group
Body: {"group_id": 123}
```

### 2. 依彩種對獎
```
POST /api/v1/check/by-lottery
Body: {
  "lottery_type": "power",
  "draw_term": "power_2026-01-10"  // 或 "draw_date": "2026-01-10"
}
```

### 3. 自動對獎所有待對獎團
```
POST /api/v1/check/auto
```

### 4. 查看待對獎團
```
GET /api/v1/check/pending?lottery_type=power
```

### 5. 對獎統計
```
GET /api/v1/check/stats
```

## ⚙️ 運作流程

1. **管理員同步開獎** (`POST /api/v1/lottery/sync`)
   - 從 lotto-8.com 抓取最新開獎號碼
   - 儲存到 `lottery_draws` 表
   - **自動觸發對獎**（掃描所有 `PURCHASED` 狀態的團）

2. **對獎流程**
   - 根據 Group 的 `draw_term` 或 `draw_date` 查找對應的開獎號碼
   - 對每張彩券的每一注進行比對
   - 更新 `Ticket.prize_results` 和 `Ticket.prize_amount`
   - 更新 Group 狀態為 `DRAWN`
   - 計算扣稅後總獎金

## 📊 對獎邏輯

### 威力彩
- 第一區 6 碼 + 第二區 1 碼
- 頭獎：6+1（累積獎金）
- 貳獎：6+0 = 150,000
- ...

### 大樂透
- 主號 6 碼 + 特別號
- 頭獎：6+0（累積獎金）
- 貳獎：5+特 = 150,000
- ...

### 今彩539
- 5 碼選號
- 頭獎：5 中 = 8,000,000
- 貳獎：4 中 = 20,000
- ...

## 🔍 狀態流程

```
COLLECTING → LOCKED → PURCHASED → DRAWN → SETTLED
     集資中      已鎖定     已購買     已開獎    已結算
                                      ↑
                                  自動對獎
```
