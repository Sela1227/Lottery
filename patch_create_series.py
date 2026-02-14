#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA 修復：建立集資 422 錯誤
日期：2026-02-14

問題：前端 createSeries() 送的欄位名跟 API SeriesCreate schema 不匹配
  前端送: { name, lottery_type, share_amount, initial_amount }
  API 要: { name, allowed_lottery_types: [...], initial_pool_share }
"""
import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE, "static", "series.html")

if not os.path.exists(FILE):
    print(f"找不到 {FILE}")
    sys.exit(1)

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

original = content
changes = 0

# Fix: createSeries request body
old_body = """await apiPost('/series', {
                    name,
                    lottery_type: lotteryType,
                    share_amount: shareAmount,
                    initial_amount: initialAmount
                });"""

new_body = """await apiPost('/series', {
                    name,
                    allowed_lottery_types: [lotteryType],
                    initial_pool_share: initialAmount
                });"""

if old_body in content:
    content = content.replace(old_body, new_body)
    changes += 1
    print("  Fix 1: createSeries request body field names")

# Fix: joinSeries request body
old_join = "await apiPost('/series/join', { invitation_code: code, initial_amount: amount });"
new_join = "await apiPost('/series/join', { code: code, initial_pool_share: amount });"
if old_join in content:
    content = content.replace(old_join, new_join)
    changes += 1
    print("  Fix 2: joinSeries request body field names")

if content != original:
    with open(FILE + ".bak2", "w", encoding="utf-8") as f:
        f.write(original)
    with open(FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n完成！{changes} 項修復")
    print("\n部署：")
    print("   git add static/series.html")
    print('   git commit -m "fix: createSeries 欄位名修正 (422 error)"')
    print("   git push")
else:
    print("未找到匹配 - 可能已修正或格式不同")
    print("請手動檢查 series.html 中的 createSeries 函數")
