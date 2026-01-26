#!/usr/bin/env python3
"""
Patch 003: 修改 stats.py 使用 constants.py

在專案根目錄執行: python patch_003_stats.py
"""
import re

STATS_FILE = "app/api/v1/stats.py"

def apply_patch():
    # 讀取檔案
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 檢查是否已經套用過
    if "from app.constants import" in content and "NUMBER_RANGES" in content.split("from app.constants import")[1].split("\n")[0]:
        print("⚠️  此 patch 已經套用過，跳過")
        return False
    
    # 步驟 1: 新增 import
    old_import = "from app.models.lottery_draw import LotteryDraw"
    new_import = old_import + "\nfrom app.constants import NUMBER_RANGES, LOTTERY_NAMES"
    
    if old_import not in content:
        print("❌ 找不到預期的 import 行，請手動修改")
        return False
    
    content = content.replace(old_import, new_import)
    
    # 步驟 2: 刪除本地常量定義
    # 刪除 NUMBER_RANGES 定義
    pattern1 = r'\n*# 各彩種號碼範圍\nNUMBER_RANGES = \{[^}]+\}\n*'
    content = re.sub(pattern1, '\n\n', content)
    
    # 刪除 LOTTERY_NAMES 定義
    pattern2 = r'\nLOTTERY_NAMES = \{[^}]+\}\n*'
    content = re.sub(pattern2, '\n\n', content)
    
    # 清理多餘空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 寫回檔案
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Patch 003 套用成功！")
    print(f"   修改檔案: {STATS_FILE}")
    return True

def verify():
    """驗證修改是否成功"""
    try:
        from app.api.v1.stats import router
        print("✅ 驗證通過: stats.py 可正常載入")
        return True
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Patch 003: stats.py 使用 constants.py")
    print("=" * 50)
    
    if apply_patch():
        print("\n正在驗證...")
        verify()
    
    print("\n完成！")
