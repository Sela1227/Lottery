# FIX12 彩種初始化與集資團更名 - 2026-01-10

## 問題描述

建立集資團時彩種選項為空，無法選擇任何彩種。

## 問題原因

1. **Dockerfile 缺少 seed_data.py**：啟動時沒有執行彩種初始化腳本，導致 `lottery_types` 資料表為空
2. **lottery_types router 未註冊**：`app/main.py` 沒有 include `lottery_types_router`
3. **名稱更正**：「系列團」統一更名為「集資團」

## 修復內容

### 1. Dockerfile - 添加 seed_data.py 執行

**修改前**:
```
CMD ["sh", "-c", "python scripts/migrate.py && python scripts/set_admin.py && python main.py"]
```

**修改後**:
```
CMD ["sh", "-c", "python scripts/migrate.py && python scripts/seed_data.py && python scripts/set_admin.py && python main.py"]
```

### 2. app/main.py - 註冊 lottery_types router

新增：
```python
from app.api.v1.lottery_types import router as lottery_types_router
application.include_router(lottery_types_router, prefix="/v1")
```

### 3. static/series.html - 更名為集資團

| 位置 | 原本 | 修改後 |
|------|------|--------|
| 頁面標題 | 我的系列團 | 我的集資團 |
| 建立按鈕 | 建立系列團 | 建立集資團 |
| Modal 標題 | 建立系列團 | 建立集資團 |
| 表單標籤 | 系列團名稱 | 集資團名稱 |
| 空狀態標題 | 還沒有加入任何系列團 | 還沒有加入任何集資團 |
| 空狀態描述 | 建立一個新的系列團 | 建立一個新的集資團 |
| 驗證提示 | 請輸入系列團名稱 | 請輸入集資團名稱 |
| 成功提示 | 系列團建立成功 | 集資團建立成功 |
| 加入提示 | 成功加入系列團 | 成功加入集資團 |

## 更新檔案清單

```
Dockerfile          - 添加 seed_data.py 執行
app/main.py         - 註冊 lottery_types router
static/series.html  - 系列團更名為集資團
```

## 部署方式

1. 解壓縮 zip 檔案
2. 將檔案按照目錄結構覆蓋原檔案
3. 重新部署應用程式（Railway 會自動重建 Docker image）

## 測試驗證

1. 部署後檢查啟動 log，應該看到：
   - `🔑 初始化彩種資料...`
   - `✅ 威力彩 已建立` (或 `⭕ 威力彩 已存在,跳過`)
   - `✅ 大樂透 已建立`
   - `✅ 今彩539 已建立`

2. 進入「我的集資團」頁面
3. 點擊「建立集資團」按鈕
4. 確認彩種選項顯示：威力彩、大樂透、今彩539
