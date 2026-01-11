# 問題排除記錄 - 2026-01-11

## 問題 1：資料庫連線失敗 - 密碼特殊字元

### 症狀
```
connection to server on socket "@!#@S@postgres-d66g.railway.internal/.s.PGSQL.5432" failed
```

### 原因
Railway PostgreSQL 密碼包含特殊字元（`!#$@`），在 URL 中未正確編碼。

### 解決方案
1. 到 PostgreSQL 服務 → Settings → Reset Credentials（產生不含特殊字元的密碼）
2. 或手動 URL encode 特殊字元：`!` → `%21`、`#` → `%23`、`@` → `%40`

---

## 問題 2：資料庫連線失敗 - 密碼不匹配

### 症狀
```
FATAL: password authentication failed for user "postgres"
```

### 原因
重設密碼後，Web 服務的 `DATABASE_URL` 環境變數沒有同步更新。

### 解決方案
1. 從 PostgreSQL 服務 → Variables → 複製 `DATABASE_URL`
2. 到 Web 服務 → Variables → 更新 `DATABASE_URL`
3. 或使用變數引用：`${{Postgres.DATABASE_URL}}`

---

## 問題 3：資料庫連線失敗 - 連到 localhost

### 症狀
```
connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```

### 原因
Web 服務的 `DATABASE_URL` 環境變數不存在，程式使用預設值 `localhost`。

### 解決方案
1. 確認 Web 服務的 Variables 有 `DATABASE_URL`
2. 如果沒有，新增並連結到 PostgreSQL 的 `DATABASE_URL`

---

## 問題 4：變數連結被覆蓋

### 症狀
在 PostgreSQL 服務修改變數時出現警告：
```
Warning: Database configuration change
This will manually change an environment variable without updating the actual database configuration.
```

### 原因
在 PostgreSQL 服務（而非 Web 服務）修改 `DATABASE_URL`，破壞了服務間的連結。

### 解決方案
- **永遠在 Web 服務修改 `DATABASE_URL`**，不要在 PostgreSQL 服務修改
- 如果連結被破壞，刪除 Web 服務的變數並重新用 Add Reference 建立

---

## 問題 5：匯入腳本指向錯誤環境

### 症狀
```
✅ 匯入完成：新增 0 筆，略過 90 筆（已存在）
```
但資料庫實際只有 1 筆。

### 原因
腳本的 `API_BASE` 指向舊的/錯誤的部署環境（如 develop 分支）。

### 解決方案
確認腳本中的 `API_BASE` 指向正確的網址：
```python
API_BASE = "https://你的正確網址.up.railway.app"
```

---

## 問題 6：爬蟲腳本編碼問題

### 症狀
Python 檔案中文顯示亂碼，如 `SELA æ¨‚é€ä¸€è·¯ç™¼`

### 原因
UTF-8 被重複編碼（double UTF-8 encoding）

### 解決方案
使用 ftfy 修復：
```python
import ftfy
fixed_content = ftfy.fix_text(broken_content)
```

---

## 最佳實踐

### Railway 資料庫連線
1. 使用變數引用而非硬編碼：`${{Postgres.DATABASE_URL}}`
2. 內部連線用 `DATABASE_URL`（private networking）
3. 外部連線用 `DATABASE_PUBLIC_URL`

### 環境分離
1. 不同分支部署到不同環境（main/develop）
2. 腳本中明確標註 `API_BASE` 指向哪個環境
3. 測試前確認連線目標

### 密碼管理
1. 避免密碼包含特殊字元
2. 密碼曝光後立即重設
3. 使用環境變數，不要寫在程式碼中

---

*SELA 樂透一路發 © 2026*
