# SELA 樂透一路發 - Dockerfile
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 啟動指令：遷移 → 初始化彩種 → 設定管理員 → 啟動服務
CMD ["sh", "-c", "python scripts/migrate.py && python scripts/seed_data.py && python scripts/set_admin.py && python main.py"]
