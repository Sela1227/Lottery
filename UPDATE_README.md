# 📊 更新包：統計報表功能

## 📅 更新日期：2026-01-10

## 📦 包含檔案

```
main.py                           # 覆蓋（/statistics 指向新頁面）
app/
├── main.py                       # 覆蓋（註冊 statistics API）
└── api/v1/
    ├── __init__.py               # 覆蓋（導出 statistics_router）
    └── statistics.py             # 新增（統計報表 API）
static/
├── dashboard.html                # 覆蓋（統計報表按鈕改為可用）
└── statistics.html               # 新增（統計報表頁面）
```

## 🚀 部署步驟

```bash
# 1. 解壓縮到專案根目錄（覆蓋）

# 2. 推送
git add .
git commit -m "feat: 新增統計報表功能"
git push

# 3. 等待 Railway 部署完成
```

## ✨ 功能說明

### 📈 投資報酬率 (ROI)
- 大型卡片顯示整體 ROI
- 正報酬顯示綠色、負報酬顯示紅色
- 顯示獲利/虧損金額

### 📊 統計數據
- 累計投資金額
- 累計獎金收入
- 中獎率（有獎期數 / 參與期數）
- 參與期數

### 📈 月度趨勢
- 最近 6 個月投資 vs 獎金長條圖
- 視覺化呈現收支趨勢

### 🎰 系列團績效
- 各系列團 ROI 排名
- 投資金額、獎金、目前份額
- 參與期數

### 🎉 中獎記錄
- 歷史中獎清單
- 顯示我的獎金份額
- 開獎日期、彩種

### 🎫 彩種分析
- 各彩種參與次數
- 各彩種投資報酬率
- 找出最幸運的彩種

## 🔗 新增 API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/v1/statistics/overall` | 整體統計 |
| GET | `/api/v1/statistics/series-performance` | 系列團績效 |
| GET | `/api/v1/statistics/winning-records` | 中獎記錄 |
| GET | `/api/v1/statistics/monthly` | 月度統計 |
| GET | `/api/v1/statistics/by-lottery-type` | 彩種分析 |

## 🎨 儀表板變更

| 按鈕 | 顏色 | 狀態 |
|------|------|------|
| 🎰 我的系列團 | 橘色 | 可用 |
| 💰 我的錢包 | 綠色 | 可用 |
| 📊 統計報表 | **藍色** | ✨可用 |
| 🎫 加入系列團 | 白色 | 可用 |
| 🔧 管理後台 | 紫色 | 僅管理員 |

## 📱 使用方式

1. 登入後點擊儀表板的「📊 統計報表」
2. 或直接訪問 `/statistics`
3. 可查看 ROI、趨勢圖、系列團績效、中獎記錄

## ⚠️ 注意事項

- 統計數據來自 `GroupMember`、`PeriodContribution`、`UserLedger` 表
- 需要有參與系列團、完成結算才會有數據
- ROI 計算公式：(累計獎金 - 累計投資) / 累計投資 × 100%
