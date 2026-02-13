#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA Bug #5 修復：開獎記錄完全空白
日期：2026-02-13
檔案：static/lottery.html, static/admin_lottery.html

問題：API 回傳 { items: [...] }，前端讀 data.draws → 永遠 undefined
修復：data.draws → data.items（兩個檔案都要改）
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = [
    os.path.join(BASE, "static", "lottery.html"),
    os.path.join(BASE, "static", "admin_lottery.html"),
]

total_changes = 0

for filepath in FILES:
    filename = os.path.basename(filepath)
    if not os.path.exists(filepath):
        print(f"  ⚠️  找不到: {filepath}")
        continue

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # data.draws → data.items
    count = content.count("data.draws")
    if count > 0:
        content = content.replace("data.draws", "data.items")
        total_changes += count
        print(f"  ✅ {filename}: data.draws → data.items ({count} 處)")
    else:
        print(f"  ⏭️  {filename}: 未找到 data.draws（可能已修正）")

    if content != original:
        backup = filepath + ".bak"
        with open(backup, "w", encoding="utf-8") as f:
            f.write(original)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

if total_changes == 0:
    print("\n⚠️  無變更")
else:
    print(f"\n🎉 Bug #5 修復完成！共 {total_changes} 處")
    print("   • lottery.html: 開獎歷史記錄可正常顯示")
    print("   • admin_lottery.html: 管理員近期開獎可正常顯示")
