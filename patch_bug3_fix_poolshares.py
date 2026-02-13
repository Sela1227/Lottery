#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA Bug #3 補丁：修復被誤改的 loadPoolShares
日期：2026-02-13
檔案：static/wallet.html

問題：v2 patch 的正則太寬，把 loadPoolShares 的空值檢查也改成
      data.transactions，但 pool-shares API 回傳的是純陣列。
"""
import os
import re
import sys

WALLET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "wallet.html")

if not os.path.exists(WALLET_FILE):
    print(f"❌ 找不到: {WALLET_FILE}")
    sys.exit(1)

with open(WALLET_FILE, "r", encoding="utf-8") as f:
    content = f.read()

original = content
changes = 0

# loadPoolShares 裡被誤改的空值檢查
# 特徵：後面接著 data.map(p =>（不是 tx =>）
# 找到 loadPoolShares 區塊裡的錯誤檢查並修回
pattern = re.compile(
    r"(async function loadPoolShares\(\)\s*\{.*?)"
    r"if\s*\(\s*!data\s*\|\|\s*!data\.transactions\s*\|\|\s*data\.transactions\.length\s*===\s*0\s*\)",
    re.DOTALL
)

match = pattern.search(content)
if match:
    old_check = "if (!data || !data.transactions || data.transactions.length === 0)"
    new_check = "if (!data || data.length === 0)"
    # 只替換第一個出現（loadPoolShares 裡的那個）
    # 找到這個錯誤行的位置
    pos = match.end() - len("if (!data || !data.transactions || data.transactions.length === 0)")
    # 用更精準的方式：找 loadPoolShares 函式內的那一行
    content = pattern.sub(
        lambda m: m.group(1) + "if (!data || data.length === 0)",
        content,
        count=1
    )
    changes += 1
    print("✅ [1] 修復 loadPoolShares 空值檢查（還原為 data.length）")
else:
    # 也可能是直接字串替換能命中
    # 找 loadPoolShares 函式，在裡面把 data.transactions 改回 data
    lines = content.split('\n')
    in_pool_shares = False
    new_lines = []
    for i, line in enumerate(lines):
        if 'function loadPoolShares' in line:
            in_pool_shares = True
        if in_pool_shares and 'function loadTransactions' in line:
            in_pool_shares = False
        
        if in_pool_shares and '!data.transactions' in line and 'data.transactions.length' in line:
            old_line = line
            line = line.replace(
                '!data || !data.transactions || data.transactions.length === 0',
                '!data || data.length === 0'
            )
            if line != old_line:
                changes += 1
                print(f"✅ [1] L{i+1}: 修復 loadPoolShares 空值檢查")
        
        new_lines.append(line)
    
    if changes > 0:
        content = '\n'.join(new_lines)
    else:
        print("⏭️  [1] loadPoolShares 空值檢查已正確，無需修改")

if content == original:
    print("\n⚠️  無變更")
    sys.exit(0)

with open(WALLET_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n🎉 補丁完成！共 {changes} 處修正")
print("   • loadPoolShares: data.transactions → data（還原為純陣列檢查）")
print("   • loadTransactions: 維持上次修正不變")
print("\n📌 部署後請開瀏覽器 F12 → Console，看有無紅字錯誤，貼給我")
