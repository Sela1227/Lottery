# 🏗️ SELA 樂透一路發 - 程式結構優化分析

> 分析日期：2026-01-26
> 分析範圍：完整系統架構

---

## 📊 現況總覽

```
線上集資系統/
├── app/
│   ├── api/v1/          # 15 個 API 模組
│   ├── models/          # 10 個資料模型
│   ├── schemas/         # 4 個 Schema 檔案（但實際 Schema 分散各處）
│   ├── services/        # 11 個服務類別
│   └── core/            # 2 個核心模組
├── static/              # 14 個 HTML + 2 個 JS
├── scripts/             # 8 個腳本
└── docs/                # 4 個文件
```

---

## 🔴 高優先級問題

### 1. Schema 定義位置不一致

**問題描述**：
- 部分 Schema 定義在獨立的 `schemas/` 目錄 ✅
- 部分 Schema 直接定義在 API 檔案中 ❌

| API 檔案 | Schema 位置 | 狀態 |
|----------|------------|:----:|
| users.py | schemas/user.py | ✅ |
| series.py | schemas/series.py | ✅ |
| groups.py | schemas/group.py | ✅ |
| **statistics.py** | 直接定義在 API 中 | ❌ |
| **wallet.py** | 直接定義在 API 中 | ❌ |
| **personal.py** | 直接定義在 API 中 | ❌ |
| **achievements.py** | 直接定義在 API 中 | ❌ |
| **admin.py** | 直接定義在 API 中 | ❌ |
| **stats.py** | 直接定義在 API 中 | ❌ |

**影響**：
- 難以維護和重用 Schema
- 違反單一職責原則
- 無法從 `schemas/__init__.py` 統一匯出

**建議**：
```
schemas/
├── __init__.py
├── user.py          # 已有
├── series.py        # 已有
├── group.py         # 已有
├── member_request.py # 已有
├── wallet.py        # 新增：從 api/wallet.py 抽出
├── statistics.py    # 新增：從 api/statistics.py 抽出
├── personal.py      # 新增：從 api/personal.py 抽出
├── achievement.py   # 新增：從 api/achievements.py 抽出
├── admin.py         # 新增：從 api/admin.py 抽出
└── lottery.py       # 新增：整合開獎相關 Schema
```

---

### 2. Service 層不完整

**問題描述**：
- 有些功能有獨立 Service，有些直接在 API 層處理複雜邏輯

| 功能模組 | 是否有 Service | 複雜度 |
|---------|:-------------:|:------:|
| 用戶管理 | ✅ UserService | 低 |
| 系列團 | ✅ SeriesService | 高 |
| 單期團 | ✅ GroupService | 高 |
| 結算 | ✅ SettlementService | 高 |
| **錢包** | ❌ 無 | 中 |
| **統計** | ❌ 無 | 高 |
| **成就** | ❌ 無 | 中 |
| **管理員** | ❌ 無 | 中 |

**影響**：
- API 層過於臃腫（直接包含 db.query）
- 商業邏輯難以測試
- 重複的查詢邏輯無法重用

**建議**：新增以下 Service
```
services/
├── wallet_service.py      # 錢包相關邏輯
├── statistics_service.py  # 統計計算邏輯
├── achievement_service.py # 成就檢查與解鎖
└── admin_service.py       # 管理員操作邏輯
```

---

### 3. 前端程式碼高度重複

**問題描述**：

| 重複項目 | 重複次數 | 說明 |
|---------|:-------:|------|
| CSS `:root` 變量 | **14 次** | 每個 HTML 都重新定義 |
| `apiGet/apiPost` | **22 次** | API 調用函數重複定義 |
| `showToast` | **7 次** | Toast 提示函數重複 |
| `checkAuth` | **~10 次** | 登入驗證重複 |

**影響**：
- 維護困難（改一處要改多處）
- 樣式不一致（如 settings.html 風格不同）
- 程式碼膨脹

**建議**：抽取共用模組
```
static/
├── css/
│   └── common.css       # 共用 CSS 變量與基礎樣式
├── js/
│   ├── api.js           # API 調用工具
│   ├── auth.js          # 認證相關
│   ├── utils.js         # 工具函數（toast, format 等）
│   └── member-requests.js
└── [頁面].html
```

---

## 🟡 中優先級問題

### 4. 命名容易混淆

| 現有命名 | 功能 | 建議改名 |
|---------|------|---------|
| stats.py | 號碼統計（冷熱號） | `number_analysis.py` |
| statistics.py | 個人統計報表 | `user_statistics.py` |
| stats.html | 號碼統計頁面 | `number-analysis.html` |
| statistics.html | 個人統計頁面 | `user-statistics.html` |

---

### 5. 常量重複定義

**問題描述**：
```python
# 在 lottery.py 定義
LOTTERY_NAMES = {"power": "威力彩", "super": "大樂透", ...}

# 在 stats.py 又定義一次
LOTTERY_NAMES = {"power": "威力彩", "super": "大樂透", ...}
```

**建議**：建立常量模組
```python
# app/constants.py
LOTTERY_NAMES = {
    "power": "威力彩",
    "super": "大樂透",
    "daily539": "今彩539"
}

NUMBER_RANGES = {
    "power": {"first_zone": (1, 38), "second_zone": (1, 8)},
    "super": {"main": (1, 49), "special": (1, 49)},
    "daily539": {"numbers": (1, 39)},
}

LOTTERY_PRICES = {
    "power": 100,
    "super": 50,
    "daily539": 50
}
```

---

### 6. 錯誤處理不一致

**問題描述**：
- 有些地方直接 `raise HTTPException`
- 有些地方用自定義錯誤類別
- 錯誤訊息格式不統一

**建議**：建立統一的異常處理
```python
# app/exceptions.py
class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

class NotFoundError(AppException):
    def __init__(self, resource: str):
        super().__init__("NOT_FOUND", f"{resource}不存在", 404)

class ForbiddenError(AppException):
    def __init__(self, message: str = "沒有權限"):
        super().__init__("FORBIDDEN", message, 403)
```

---

## 🟢 低優先級問題

### 7. 遷移腳本混亂

**現況**：
```
scripts/
├── migrate.py           # 主要遷移
├── migrate_phase1.py    # Phase 1 遷移
├── migrate_notify.py    # LINE Notify 遷移
└── migrate_webpush.py   # Web Push 遷移
```

**建議**：
- 短期：整合所有遷移到 `migrate.py`，已執行過的可歸檔
- 長期：導入 Alembic 做正規版本控制

---

### 8. 測試目錄為空

**現況**：`tests/__init__.py` 存在但沒有測試

**建議**：逐步補充測試
```
tests/
├── __init__.py
├── conftest.py          # pytest fixtures
├── test_api/
│   ├── test_auth.py
│   ├── test_series.py
│   └── test_groups.py
└── test_services/
    ├── test_settlement.py
    └── test_auto_check.py
```

---

## 📋 重構優先順序建議

| 順序 | 項目 | 工作量 | 影響範圍 | 風險 |
|:---:|------|:-----:|:-------:|:---:|
| 1 | 抽取前端共用 CSS/JS | 中 | 全部頁面 | 低 |
| 2 | Schema 整理 | 低 | API 層 | 低 |
| 3 | 建立常量模組 | 低 | 後端 | 低 |
| 4 | 新增缺失的 Service | 中 | API 層 | 中 |
| 5 | 統一錯誤處理 | 中 | 全系統 | 中 |
| 6 | 命名重構 | 低 | 路由 | 中 |
| 7 | 整合遷移腳本 | 低 | 部署 | 低 |
| 8 | 補充測試 | 高 | 無 | 低 |

---

## 🎯 建議的目標架構

```
線上集資系統/
├── app/
│   ├── api/
│   │   └── v1/              # API 層：只做路由、驗證、呼叫 Service
│   ├── models/              # 資料模型（維持現狀）
│   ├── schemas/             # 所有 Pydantic Schema
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── series.py
│   │   ├── group.py
│   │   ├── wallet.py        # 新增
│   │   ├── statistics.py    # 新增
│   │   ├── achievement.py   # 新增
│   │   └── lottery.py       # 新增
│   ├── services/            # 商業邏輯層
│   │   ├── wallet_service.py     # 新增
│   │   ├── statistics_service.py # 新增
│   │   └── ...
│   ├── core/
│   │   ├── database.py
│   │   ├── security.py
│   │   └── exceptions.py    # 新增：統一異常
│   ├── constants.py         # 新增：全域常量
│   └── main.py
├── static/
│   ├── css/
│   │   └── common.css       # 新增：共用樣式
│   ├── js/
│   │   ├── api.js           # 新增：API 工具
│   │   ├── auth.js          # 新增：認證工具
│   │   └── utils.js         # 新增：通用工具
│   └── [pages].html
├── tests/                   # 完善測試
└── scripts/
    └── migrate.py           # 整合後的遷移腳本
```

---

## ⏱️ 預估工時

| 項目 | 預估時間 |
|------|:-------:|
| 前端共用模組抽取 | 4-6 小時 |
| Schema 整理 | 2-3 小時 |
| 常量模組建立 | 1 小時 |
| Service 層補充 | 6-8 小時 |
| 錯誤處理統一 | 3-4 小時 |
| 命名重構 | 2 小時 |
| **總計** | **18-24 小時** |

---

## 💡 立即可做的快速改善

1. **建立 `app/constants.py`** - 集中管理常量（1小時）
2. **建立 `static/css/common.css`** - 統一 CSS 變量（2小時）
3. **修正 settings.html 樣式** - 已完成 ✅
4. **修正 UserResponse 缺少 is_admin** - 已完成 ✅
