#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA 修復：series-detail.html logo 爆圖
日期：2026-02-13

問題：header 缺少 display:flex，logo 沒有尺寸限制
"""
import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE, "static", "series-detail.html")

if not os.path.exists(FILE):
    print(f"找不到 {FILE}")
    sys.exit(1)

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

with open(FILE + ".bak", "w", encoding="utf-8") as f:
    f.write(content)

changes = 0

# Fix 1: header 缺少 display:flex 和 background
old_header = ".header { padding: 12px 20px; justify-content: space-between; position: sticky; }"
new_header = """.header { padding: 12px 20px; justify-content: space-between; position: sticky; display: flex; align-items: center; background: linear-gradient(135deg, var(--sela-orange, #F26522), var(--sela-orange-dark, #D85A1E)); top: 0; z-index: 100; }
        .logo { width: 36px; height: 36px; border-radius: 8px; object-fit: cover; }
        .page-title, .header a, .header span { color: white; }
        .back-btn { color: var(--text-primary); }"""

if old_header in content:
    content = content.replace(old_header, new_header)
    changes += 1
    print("  Fix 1: header + logo styles")

# Fix 2: Also fix $$0 double dollar issue if present
old_dd = "$${formatMoney("
new_dd = "${formatMoney("
count = content.count(old_dd)
if count > 0:
    content = content.replace(old_dd, new_dd)
    changes += 1
    print(f"  Fix 2: $$ double dollar ({count}x)")

# Fix 3: desktop header padding
if "@media (min-width: 700px)" not in content and ".header" in content:
    # Add after .header definition
    insert_after = ".back-btn { color: var(--text-primary); }"
    if insert_after in content:
        content = content.replace(insert_after, insert_after + """
        @media (min-width: 900px) {
            .header { padding: 12px calc((100% - 800px) / 2 + 20px); }
        }""")
        changes += 1
        print("  Fix 3: desktop header padding")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

if changes == 0:
    print("無變更")
else:
    print(f"\n完成！共 {changes} 項修復")
    print("\n部署：")
    print("   git add static/series-detail.html")
    print('   git commit -m "fix: series-detail logo爆圖+header樣式"')
    print("   git push")
