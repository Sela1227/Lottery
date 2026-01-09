# 🔄 更新包：管理員設定功能 (修正版)

## 📅 更新日期：2026-01-09

## 📦 包含檔案

```
scripts/
└── set_admin.py              # 管理員設定腳本 (新增)

app/services/auth/
└── user_service.py           # 用戶服務 (覆蓋)
```

## 🚀 部署步驟

### 1. 解壓縮並覆蓋
將 zip 解壓縮後，直接覆蓋到專案根目錄。

### 2. 推送到 Railway
```bash
git add .
git commit -m "feat: 新增管理員設定功能"
git push
```

### 3. 執行管理員設定（二選一）

**方法 A：Railway CLI**
```bash
railway run python scripts/set_admin.py
```

**方法 B：Railway Console**
在 Railway Dashboard → 你的服務 → 點擊 "..." → "Open Shell"
```bash
python scripts/set_admin.py
```

## 📋 腳本使用說明

```bash
# 將第一個用戶設為管理員
python scripts/set_admin.py

# 指定用戶 ID
python scripts/set_admin.py --user-id=1

# 列出所有用戶
python scripts/set_admin.py --list
```

## ✨ 功能說明

1. **set_admin.py**：手動設定管理員的腳本工具
2. **user_service.py**：更新後，未來第一個註冊的用戶會自動成為管理員

## 🐛 修正內容

- 修正 `ImportError: cannot import name 'user_service'` 錯誤
- 補上遺漏的全域實例 `user_service = UserService()`
