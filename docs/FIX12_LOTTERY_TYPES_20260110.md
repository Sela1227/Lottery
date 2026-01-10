# FIX12 彩種初始化與集資功能優化 - 2026-01-10

## 問題描述

1. 建立集資時彩種選項為空
2. 名稱需統一為「集資」
3. 每次開團只能選一種彩種，份額單位需對應彩種價格

## 修復內容

### 1. Dockerfile - 添加 seed_data.py 執行

啟動時執行彩種初始化腳本。

**修改前**:
```
CMD ["sh", "-c", "python scripts/migrate.py && python scripts/set_admin.py && python main.py"]
```

**修改後**:
```
CMD ["sh", "-c", "python scripts/migrate.py && python scripts/seed_data.py && python scripts/set_admin.py && python main.py"]
```

### 2. app/main.py - 註冊 lottery_types router

```python
from app.api.v1.lottery_types import router as lottery_types_router
application.include_router(lottery_types_router, prefix="/v1")
```

### 3. static/series.html - 重大功能調整

#### 3.1 名稱統一為「集資」

| 原本 | 修改後 |
|------|--------|
| 我的系列團 / 我的集資團 | 我的集資 |
| 建立系列團 / 建立集資團 | 建立集資 |
| 系列團名稱 / 集資團名稱 | 集資名稱 |
| 成功加入系列團 / 成功加入集資團 | 成功加入集資 |

#### 3.2 彩種改為單選

- 從 checkbox（多選）改為 radio button（單選）
- 每個集資只能選擇一種彩種

#### 3.3 份額單位動態對應

選擇彩種後，初始份額會自動調整：

| 彩種 | 每注價格 | 份額單位 | 建議範圍 |
|------|----------|----------|----------|
| 威力彩 | 100 元 | 100 | 500~2000 元 |
| 大樂透 | 50 元 | 50 | 250~1000 元 |
| 今彩539 | 50 元 | 50 | 250~1000 元 |

- `min` 設為每注價格
- `step` 設為每注價格
- 預設值為 5 注金額
- 驗證份額必須是價格的倍數

## UI 變更

### 建立集資 Modal

1. **彩種選擇區**：改為 radio button 單選
   - 顯示彩種名稱
   - 顯示每注價格

2. **份額輸入區**：動態調整
   - 選擇彩種前顯示「請先選擇彩種」
   - 選擇後顯示建議金額範圍

## 更新檔案清單

```
Dockerfile          - 添加 seed_data.py 執行
app/main.py         - 註冊 lottery_types router
static/series.html  - 單選彩種、動態份額、名稱統一
```

## 部署方式

1. 解壓縮 zip 檔案
2. 將檔案按照目錄結構覆蓋原檔案
3. 重新部署應用程式

## 測試驗證

1. 進入「我的集資」頁面
2. 點擊「建立集資」
3. 確認彩種為單選（radio button）
4. 選擇威力彩 → 確認份額單位變為 100
5. 選擇大樂透 → 確認份額單位變為 50
6. 輸入非倍數金額 → 確認顯示錯誤提示
7. 成功建立集資 → 確認只有一種彩種標籤
