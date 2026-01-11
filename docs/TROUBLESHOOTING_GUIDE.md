# SELA 樂透一路發 - 問題排解指南

> **最後更新**：2026-01-11  
> **技術棧**：FastAPI + PostgreSQL + HTMX + TailwindCSS + Railway

---

## 快速查詢

| 類別 | 常見問題 | 快速解法 |
|------|----------|----------|
| 編碼 | 中文亂碼 | `ftfy.fix_text()` |
| 資料庫 | 連線失敗 | 用 Python + psycopg2 直連 Railway |
| API | 路由 404 | 檢查 main.py 是否註冊 router |
| API | Import 錯誤 | grep 搜尋正確的函數位置 |
| 部署 | Healthcheck 失敗 | 查看日誌找具體錯誤 |
| 前端 | 術語不統一 | sed 批量替換 |
| 安全 | 密碼曝光 | Railway 重新生成 credentials |

---

## 1. 編碼問題

### 1.1 中文字元亂碼

**問題**：從 bundle.txt 提取的檔案中文顯示為亂碼。

**解法**：使用 ftfy 修復 double UTF-8 encoding：

```python
import ftfy

with open('file.html', 'r', encoding='utf-8') as f:
    content = f.read()

fixed = ftfy.fix_text(content)

with open('file_fixed.html', 'w', encoding='utf-8') as f:
    f.write(fixed)
```

### 1.2 爬蟲編碼問題

**解法**：指定 response 編碼：

```python
response = requests.get(url)
response.encoding = 'utf-8'
content = response.text
```

---

## 2. 資料庫問題

### 2.1 本地無法連接 Railway PostgreSQL

**問題**：`connection to server at "localhost" failed: Connection refused`

**方案 A：Python 直連**

```python
import psycopg2

conn = psycopg2.connect(
    host="metro.proxy.rlwy.net",  # Railway host
    port=19612,                    # Railway port
    user="postgres",
    password="你的密碼",
    database="railway"
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("你的 SQL")
cur.close()
conn.close()
```

**方案 B：Railway Query 介面**

Railway Dashboard → PostgreSQL → Database tab → Query 介面

### 2.2 資料表不存在

**問題**：`relation "lottery_types" does not exist`

**解法**：確保 Dockerfile 包含初始化：

```dockerfile
CMD ["sh", "-c", "python scripts/migrate.py && python scripts/seed_data.py && python main.py"]
```

---

## 3. API 路由問題

### 3.1 路由未註冊

**問題**：API 端點回傳 404。

**解法**：在 `app/main.py` 註冊 router：

```python
from app.api.v1.lottery_types import router as lottery_types_router
application.include_router(lottery_types_router, prefix="/v1")
```

### 3.2 導入路徑錯誤

**問題**：`ImportError: cannot import name 'xxx'`

**解法**：搜尋正確的函數位置：

```bash
grep -r "def get_current_user" app/
```

### 3.3 API 回傳格式不一致

**建議格式**：

```python
@router.get("/items")
async def get_items():
    return {"success": True, "data": items}
```

---

## 4. 部署問題

### 4.1 Railway Healthcheck 失敗

**檢查項目**：
1. 查看 Railway 部署日誌
2. 確保 health 端點存在：
```python
@router.get("/health")
async def health_check():
    return {"status": "healthy"}
```
3. 確認環境變數設定正確

### 4.2 靜態檔案 404

**解法**：在 main.py 掛載靜態檔案：

```python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
```

### 4.3 ZIP 中文檔名問題

**解法**：使用英文資料夾名稱，或指定編碼解壓：

```bash
unzip -O UTF-8 file.zip
```

---

## 5. 前端問題

### 5.1 術語不統一

**解法**：批量替換：

```bash
sed -i 's/系列團/集資/g' static/*.html
sed -i 's/集資團/集資/g' static/*.html
```

### 5.2 彩種選擇多選改單選

**解法**：checkbox 改為 radio：

```html
<!-- 舊 -->
<input type="checkbox" name="lottery_types" value="power">

<!-- 新 -->
<input type="radio" name="lottery_type" value="power" required>
```

### 5.3 動態金額驗證

```javascript
const prices = { 'power': 100, 'super': 50, 'daily539': 50 };

function validateAmount(amount, lotteryType) {
    const price = prices[lotteryType];
    return amount % price === 0;
}
```

---

## 6. 安全問題

### 6.1 資料庫密碼曝光

**立即處理**：
1. Railway Dashboard → PostgreSQL
2. Settings → Reset Credentials

**預防**：使用 `.env` 檔案（加入 `.gitignore`）

### 6.2 JWT Secret 安全

**生成強密鑰**：

```python
import secrets
print(secrets.token_urlsafe(32))
```

---

## 常用除錯指令

### 查看 Railway 日誌

```bash
cat logs.json | python3 -c "
import json,sys
for d in json.load(sys.stdin):
    print(d.get('message',''))
"
```

### 搜尋錯誤

```bash
cat logs.json | python3 -c "
import json,sys
for d in json.load(sys.stdin):
    if 'error' in d.get('message','').lower():
        print(d.get('message',''))
"
```

### 檢查表是否存在

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

---

## 開發流程建議

### Git 分支流程

```bash
git checkout -b feature/member-requests
git commit -m "feat: 成員異動功能"
git push origin feature/member-requests

git checkout main
git merge feature/member-requests
git push
```

### 文件版本管理

```
docs/
├── STEP1_SUMMARY.md
├── FIX12_LOTTERY_TYPES_20260110.md
└── PHASE1_README_20260111.md
```

---

*SELA 樂透一路發 © 2026*
