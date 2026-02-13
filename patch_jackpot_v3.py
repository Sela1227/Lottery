#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復兩個問題：
1. 爬蟲：大樂透 jackpot 欄位名 lotto649JackpotAssign → jackpotAssign
2. 後端：format_jackpot 的「億」「萬」亂碼
"""
import os
import sys
import re

BASE = os.path.dirname(os.path.abspath(__file__))
changes = 0

# ===== 修復 1：爬蟲大樂透 jackpot 欄位 =====
CRAWLER_FILE = os.path.join(BASE, "兌獎資料爬蟲上傳-develop.py")
if os.path.exists(CRAWLER_FILE):
    with open(CRAWLER_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    old = 'item.get("lotto649JackpotAssign", {})'
    new = 'item.get("jackpotAssign", {})'
    
    if old in content:
        content = content.replace(old, new)
        with open(CRAWLER_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        changes += 1
        print("  ✅ 爬蟲：lotto649JackpotAssign → jackpotAssign")
    elif new in content:
        print("  ⏭️  爬蟲已是 jackpotAssign")
    else:
        print("  ⚠️  爬蟲中找不到目標字串")
else:
    print(f"  ⚠️  找不到爬蟲檔案")

# ===== 修復 2：lottery.py format_jackpot 中文亂碼 =====
LOTTERY_FILE = os.path.join(BASE, "app", "api", "v1", "lottery.py")
if not os.path.exists(LOTTERY_FILE):
    print(f"  ❌ 找不到: {LOTTERY_FILE}")
    sys.exit(1)

# 用 bytes 讀取，避免編碼問題
with open(LOTTERY_FILE, "rb") as f:
    raw = f.read()

content = raw.decode("utf-8", errors="replace")

# 用正則找到整個 format_jackpot 函式並替換
# 匹配從 def format_jackpot 到下一個 def 或空行+def
pattern = re.compile(
    r'def format_jackpot\(amount.*?\n(?:.*?\n)*?(?=\ndef |\n\n)',
    re.MULTILINE
)

NEW_FORMAT_JACKPOT = '''def format_jackpot(amount) -> str:
    """格式化獎金顯示"""
    if amount is None:
        return None
    if amount >= 100000000:
        return f"{amount / 100000000:.1f} \u5104"
    elif amount >= 10000:
        return f"{amount / 10000:.0f} \u842c"
    else:
        return f"{amount:,}"
'''

match = pattern.search(content)
if match:
    content = content[:match.start()] + NEW_FORMAT_JACKPOT + content[match.end():]
    changes += 1
    print("  ✅ lottery.py：format_jackpot 中文修正（億/萬）")
else:
    # fallback：逐行找
    lines = content.split("\n")
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if "def format_jackpot(" in line:
            start_idx = i
        elif start_idx >= 0 and (line.strip() == "" or (line.startswith("def ") and i > start_idx)):
            end_idx = i
            break
    
    if start_idx >= 0:
        if end_idx < 0:
            end_idx = start_idx + 10
        new_lines = NEW_FORMAT_JACKPOT.rstrip().split("\n")
        lines[start_idx:end_idx] = new_lines
        content = "\n".join(lines)
        changes += 1
        print("  ✅ lottery.py：format_jackpot 中文修正（fallback）")
    else:
        print("  ⚠️  找不到 format_jackpot 函式")

# 寫回（確保 UTF-8）
with open(LOTTERY_FILE, "w", encoding="utf-8") as f:
    f.write(content)

# 驗證
with open(LOTTERY_FILE, "r", encoding="utf-8") as f:
    verify = f.read()
if "億" in verify and "萬" in verify:
    print("  ✅ 驗證通過：億/萬 正確寫入")
else:
    print("  ⚠️  驗證失敗：請手動確認 format_jackpot")

print(f"\n🎉 完成！共 {changes} 處變更")
print("\n📌 下一步：")
print("   1. 驗證爬蟲：python 兌獎資料爬蟲上傳-develop.py --dry-run --months 1")
print("   2. git add + commit + push 部署（修 format_jackpot 亂碼）")
print("   3. 重跑爬蟲上傳：python 兌獎資料爬蟲上傳-develop.py --months 3")
