# 🔄 更新包：管理員自動設定（v3 自動化版）

## 📅 更新日期：2026-01-09

## 📦 包含檔案

```
Dockerfile                    # 覆蓋（加入自動設定管理員）
scripts/
└── set_admin.py              # 新增（管理員設定腳本）
app/services/auth/
└── user_service.py           # 覆蓋（第一用戶自動為管理員）
```

## 🚀 部署步驟

### 只需要 3 步：

```bash
# 1. 解壓縮到專案根目錄（覆蓋）

# 2. 推送
git add .
git commit -m "feat: 自動設定管理員"
git push

# 3. 等待 Railway 部署完成，自動生效！
```

## ✨ 功能說明

1. **Dockerfile**：每次部署時自動執行 `set_admin.py`
2. **set_admin.py**：將第一個用戶設為管理員（如果還沒有管理員）
3. **user_service.py**：未來新系統的第一個用戶會自動成為管理員

## 📋 部署日誌會顯示

```
🔧 SELA 管理員設定工具
========================================
✅ 資料庫連線成功
✅ 成功將 XXX (ID: 1) 設為系統管理員
```

## ⚠️ 注意

- 腳本會在每次部署時執行，但只會設定一次（已是管理員會跳過）
- 如果要換管理員，可以手動在 Railway Shell 執行：
  ```bash
  python scripts/set_admin.py --user-id=2
  ```
