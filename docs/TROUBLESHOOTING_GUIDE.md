# SELA 樂透一路發 - 開發問題與解決方案記錄

> **專案名稱**：SELA 樂透一路發（線上彩券集資系統）  
> **記錄日期**：2026-01-11  
> **技術棧**：FastAPI + PostgreSQL + HTMX + TailwindCSS + Railway

---

## 目錄

1. [編碼問題](#1-編碼問題)
2. [資料庫問題](#2-資料庫問題)
3. [API 路由問題](#3-api-路由問題)
4. [部署問題](#4-部署問題)
5. [前端問題](#5-前端問題)
6. [安全問題](#6-安全問題)
7. [開發流程問題](#7-開發流程問題)

---

## 1. 編碼問題

### 1.1 中文字元變成亂碼

**問題描述**  
從 bundle.txt 提取的 HTML/Python 檔案中，中文字元顯示為亂碼，如 `ç¶²ä¸Šå¨åŠ›å½©` 應為 `線上威力彩`。

**原因**  
UTF-8 編碼被重複編碼（double UTF-8 encoding）。

**解決方案**  
使用 `ftfy` 套件修復編碼：

```python
import ftfy

with open('file.html', 'r', encoding='utf-8') as f:
    content = f.read()

fixed_content = ftfy.fix_text(content)

with open('file_fixed.html', 'w', encoding='utf-8') as f:
    f.write(fixed_content)
```

**安裝**
```bash
pip install ftfy
```

---

### 1.2 爬蟲抓取資料編碼問題

**問題描述**  
從 lotto-8.com 爬取的彩券資料，中文顯示不正確。

**解決方案**  
確保 requests 回應使用正確編碼：

```python
import requests

response = requests.get(url)
response.encoding = 'utf-8'  # 強制指定編碼
content = response.text
```

---

## 2. 資料庫問題

### 2.1 本地無法連接 Railway PostgreSQL

**問題描述**  
執行本地 migration 腳本時出現：
```
connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```

**原因**  
- 本地沒有安裝 PostgreSQL
- 環境變數 `DATABASE_URL` 指向 localhost

**解決方案**

**方案 A：直接用 Python 連接 Railway**
```python
import psycopg2

conn = psycopg2.connect(
    host="metro.proxy.rlwy.net",  # Railway 提供的 host
    port=19612,                    # Railway 提供的 port
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

**方案 B：在 Railway Query 介面直接執行 SQL**  
1. Railway Dashboard → PostgreSQL 服務
2. Database tab → Connect → Public Network
3. 複製 psql 命令或使用 Query 介面

---

### 2.2 缺少 psycopg2 模組

**問題描述**  
```
ModuleNotFoundError: No module named 'psycopg2'
```

**解決方案**
```bash
pip install psycopg2-binary
```

---

### 2.3 缺少 psql 命令

**問題描述**  
```
zsh: command not found: psql
```

**解決方案**  
不需要安裝 psql，直接用 Python + psycopg2 執行 SQL（見 2.1 方案 A）。

---

### 2.4 資料表不存在

**問題描述**  
```
relation "lottery_types" does not exist
```

**原因**  
- 資料庫 migration 未執行
- seed_data.py 未執行

**解決方案**  
確保 Dockerfile 中包含所有必要的初始化腳本：

```dockerfile
CMD ["sh", "-c", "python scripts/migrate.py && python scripts/seed_data.py && python main.py"]
```

---

## 3. API 路由問題

### 3.1 路由未註冊

**問題描述**  
API 端點回傳 404，但程式碼存在。

**原因**  
Router 未在 `app/main.py` 中註冊。

**解決方案**  
在 `app/main.py` 添加 router：

```python
from app.api.v1.lottery_types import router as lottery_types_router

# 在 create_api_app() 中添加
application.include_router(lottery_types_router, prefix="/v1")
```

---

### 3.2 導入路徑錯誤

**問題描述**  
```
ImportError: cannot import name 'get_current_user' from 'app.core.security'
```

**原因**  
函數名稱或模組路徑不正確。

**解決方案**  
1. 搜尋正確的函數定義位置：
```bash
grep -r "def get_current_user" app/
```

2. 使用正確的導入：
```python
# 錯誤
from app.core.security import get_current_user

# 正確（本專案實際使用）
from app.core.security import get_current_user_id
```

3. 調整函數參數：
```python
# 錯誤
async def my_endpoint(current_user: User = Depends(get_current_user)):

# 正確
async def my_endpoint(user_id: int = Depends(get_current_user_id)):
```

---

### 3.3 API 回傳格式不一致

**問題描述**  
前端期望 `{ data: [...] }` 但後端回傳 `[...]`。

**解決方案**  
統一 API 回應格式：

```python
# 推薦格式
@router.get("/items")
async def get_items():
    items = [...]
    return {"success": True, "data": items}

# 或使用 Pydantic Response Model
class ListResponse(BaseModel):
    success: bool = True
    data: List[ItemResponse]
```

---

## 4. 部署問題

### 4.1 Railway 部署失敗 - Healthcheck

**問題描述**  
部署後服務無法啟動，healthcheck 失敗。

**原因**  
- 應用程式啟動錯誤
- 缺少必要的初始化步驟
- 環境變數未設定

**解決方案**  

1. 查看 Railway 部署日誌找出具體錯誤

2. 確保 Dockerfile 正確：
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 包含所有必要的初始化步驟
CMD ["sh", "-c", "python scripts/migrate.py && python scripts/seed_data.py && python main.py"]
```

3. 確保 health 端點存在：
```python
@router.get("/health")
async def health_check():
    return {"status": "healthy"}
```

---

### 4.2 靜態檔案無法存取

**問題描述**  
`/static/xxx.html` 回傳 404。

**解決方案**  
在 `main.py` 掛載靜態檔案：

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

---

### 4.3 ZIP 打包中文檔名問題

**問題描述**  
解壓縮 ZIP 時中文檔名變亂碼。

**解決方案**  
- 使用英文資料夾名稱打包
- 或指定編碼解壓：
```bash
unzip -O UTF-8 file.zip
```

---

## 5. 前端問題

### 5.1 術語不統一

**問題描述**  
頁面中混用「系列團」、「集資團」、「集資」等名稱。

**解決方案**  
統一使用「集資」：

| 原本 | 統一後 |
|------|--------|
| 系列團 | 集資 |
| 集資團 | 集資 |
| 參與團數 | 參與集資 |
| 系列團份額 | 集資份額 |

使用搜尋替換工具批量修改：
```bash
sed -i 's/系列團/集資/g' static/*.html
sed -i 's/集資團/集資/g' static/*.html
```

---

### 5.2 彩種選擇 - 多選改單選

**問題描述**  
建立集資時可以多選彩種，但業務邏輯要求單選。

**解決方案**  

1. HTML 從 checkbox 改為 radio：
```html
<!-- 舊：checkbox -->
<input type="checkbox" name="lottery_types" value="power">

<!-- 新：radio -->
<input type="radio" name="lottery_type" value="power" required>
```

2. JavaScript 驗證：
```javascript
const selected = document.querySelector('input[name="lottery_type"]:checked');
if (!selected) {
    alert('請選擇彩種');
    return;
}
```

---

### 5.3 動態金額計算

**問題描述**  
不同彩種價格不同，份額需要是彩種價格的倍數。

**解決方案**  

```javascript
const prices = {
    'power': 100,    // 威力彩 100 元
    'super': 50,     // 大樂透 50 元
    'daily539': 50   // 今彩539 50 元
};

// 監聽彩種變更
document.querySelectorAll('input[name="lottery_type"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        const price = prices[e.target.value];
        const input = document.getElementById('share-amount');
        input.min = price;
        input.step = price;
        input.value = price;
        document.getElementById('price-hint').textContent = 
            `每注 ${price} 元，需為 ${price} 的倍數`;
    });
});

// 提交時驗證
function validateAmount(amount, lotteryType) {
    const price = prices[lotteryType];
    if (amount % price !== 0) {
        alert(`金額必須是 ${price} 的倍數`);
        return false;
    }
    return true;
}
```

---

## 6. 安全問題

### 6.1 資料庫密碼意外曝光

**問題描述**  
在終端執行命令時，密碼被截圖或記錄。

**解決方案**  

1. 立即更換密碼：
   - Railway Dashboard → PostgreSQL 服務
   - Settings → Reset Credentials 或 Variables → 重新生成密碼

2. 預防措施：
   - 使用環境變數而非明文密碼
   - 使用 `.env` 檔案（加入 `.gitignore`）
   
```bash
# .env 檔案
DATABASE_URL=postgresql://user:password@host:port/db

# 執行時載入
export $(cat .env | xargs)
python script.py
```

---

### 6.2 JWT Secret 安全

**問題描述**  
JWT_SECRET_KEY 不夠強或意外曝光。

**解決方案**  

1. 生成強密鑰：
```python
import secrets
print(secrets.token_urlsafe(32))
```

2. 存放在環境變數，不要寫在程式碼中：
```python
import os
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
```

---

## 7. 開發流程問題

### 7.1 多人開發同步問題

**問題描述**  
本地修改與遠端部署版本不同步。

**解決方案**  

1. 使用 Git 版本控制
2. 建立開發分支流程：
```bash
# 功能開發
git checkout -b feature/member-requests
git commit -m "feat: 成員異動功能"
git push origin feature/member-requests

# 合併到主分支
git checkout main
git merge feature/member-requests
git push
```

---

### 7.2 部署包管理

**問題描述**  
每次修改都要打包、上傳、解壓、覆蓋，容易出錯。

**解決方案**  

1. 使用 Git + Railway 自動部署：
   - 連接 GitHub 倉庫
   - 推送即自動部署

2. 如果必須手動部署，建立標準流程：
```bash
# 打包腳本 pack.sh
#!/bin/bash
VERSION=$(date +%Y%m%d_%H%M)
zip -r "deploy_${VERSION}.zip" app/ static/ scripts/ main.py requirements.txt Dockerfile
echo "打包完成: deploy_${VERSION}.zip"
```

---

### 7.3 文件版本管理

**問題描述**  
更新文件沒有版本記錄，不知道改了什麼。

**解決方案**  

1. 文件命名加日期：
```
docs/
├── STEP1_SUMMARY.md
├── STEP2_SUMMARY.md
├── FIX12_LOTTERY_TYPES_20260110.md
└── PHASE1_README_20260111.md
```

2. 在文件頭部記錄版本：
```markdown
# 功能名稱

> **版本**：1.0.0  
> **更新日期**：2026-01-11  
> **作者**：開發團隊

## 更新記錄
- 2026-01-11：初版
- 2026-01-12：修正 XXX 問題
```

---

## 常用除錯指令

### 查看 Railway 日誌
```bash
# 下載日誌 JSON 後解析
cat logs.json | python3 -c "
import json,sys
data=json.load(sys.stdin)
for d in data:
    print(d.get('message',''))
"
```

### 搜尋錯誤
```bash
cat logs.json | python3 -c "
import json,sys
data=json.load(sys.stdin)
errors=[d.get('message','') for d in data if 'error' in d.get('message','').lower()]
print('\n'.join(errors))
"
```

### 本地連接 Railway DB
```python
import psycopg2
conn = psycopg2.connect(
    host="metro.proxy.rlwy.net",
    port=19612,
    user="postgres",
    password="YOUR_PASSWORD",
    database="railway"
)
```

### 檢查表是否存在
```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

---

## 總結

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

*SELA 樂透一路發 © 2026*
