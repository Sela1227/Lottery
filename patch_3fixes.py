#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA 修復三件事
1. admin.html 移除開獎同步 + admin_lottery 返回→首頁
2. admin.py 加 UserLedger import (修刪除500)
3. dashboard.html 快速操作卡片改色（去橘）
"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
fixes = 0

def fix(label):
    global fixes
    fixes += 1
    print(f"  {label}")


# =====================================================================
# 1. admin.html 移除開獎同步快速操作
# =====================================================================
print("\n=== 1. admin.html 移除開獎同步 ===")
ADMIN = os.path.join(BASE, "static", "admin.html")
if os.path.exists(ADMIN):
    with open(ADMIN, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c

    # 移除整個 quick-actions div
    qa_pattern = re.compile(
        r'\s*<!-- [^\n]*-->\s*<div class="quick-actions">.*?</div>\s*',
        re.DOTALL
    )
    new_c = qa_pattern.sub('\n        ', c)
    if new_c != c:
        c = new_c
        fix("移除快速操作區塊")
    else:
        # Try without comment
        qa_pattern2 = re.compile(
            r'\s*<div class="quick-actions">.*?</div>\s*(?=\s*<!--|\s*<div class="section">)',
            re.DOTALL
        )
        new_c = qa_pattern2.sub('\n        ', c)
        if new_c != c:
            c = new_c
            fix("移除快速操作區塊 (v2)")

    # Also remove .quick-actions and .action-btn CSS if only used here
    c = re.sub(r'\s*\.quick-actions\s*\{[^}]*\}', '', c)

    if c != orig:
        with open(ADMIN, "w", encoding="utf-8") as f:
            f.write(c)


# =====================================================================
# 1b. admin_lottery.html 返回→首頁
# =====================================================================
print("\n=== 1b. admin_lottery 返回→首頁 ===")
ADMIN_LOT = os.path.join(BASE, "static", "admin_lottery.html")
if os.path.exists(ADMIN_LOT):
    with open(ADMIN_LOT, "r", encoding="utf-8") as f:
        c = f.read()
    if 'href="/admin"' in c:
        c = c.replace('href="/admin"', 'href="/dashboard"')
        with open(ADMIN_LOT, "w", encoding="utf-8") as f:
            f.write(c)
        fix("admin_lottery 返回→/dashboard")


# =====================================================================
# 2. admin.py 加 UserLedger import
# =====================================================================
print("\n=== 2. admin.py UserLedger import ===")
ADMIN_PY = os.path.join(BASE, "app", "api", "v1", "admin.py")
if os.path.exists(ADMIN_PY):
    with open(ADMIN_PY, "r", encoding="utf-8") as f:
        c = f.read()

    # 檢查 import 區（前30行）是否有 UserLedger
    import_area = '\n'.join(c.split('\n')[:30])
    if "UserLedger" not in import_area:
        # 現有: from app.models.ledger import EventLog, EventCategory
        old_import = "from app.models.ledger import EventLog, EventCategory"
        new_import = "from app.models.ledger import EventLog, EventCategory, UserLedger"
        if old_import in c:
            c = c.replace(old_import, new_import)
            with open(ADMIN_PY, "w", encoding="utf-8") as f:
                f.write(c)
            fix("admin.py: 加入 UserLedger import")
        else:
            # Try appending to existing ledger import line
            marker = "from app.models.ledger import"
            if marker in c:
                idx = c.index(marker)
                line_end = c.index("\n", idx)
                orig_line = c[idx:line_end]
                if "UserLedger" not in orig_line:
                    c = c.replace(orig_line, orig_line + ", UserLedger")
                    with open(ADMIN_PY, "w", encoding="utf-8") as f:
                        f.write(c)
                    fix("admin.py: 加入 UserLedger import (append)")
    else:
        print("  UserLedger already imported")


# =====================================================================
# 3. dashboard.html 快速操作卡片改色
# =====================================================================
print("\n=== 3. dashboard 快速操作卡片改色 ===")
DASH = os.path.join(BASE, "static", "dashboard.html")
if os.path.exists(DASH):
    with open(DASH, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c

    # 新配色方案（無橘色，與開獎卡同風格漸層）
    color_map = {
        # 我的集資: 青綠 teal
        '.action-btn.primary { background: linear-gradient(135deg, var(--sela-orange), var(--sela-orange-dark))':
            '.action-btn.primary { background: linear-gradient(135deg, #0891B2, #06B6D4)',
        '.action-btn.primary:hover { box-shadow: 0 12px 32px rgba(242, 101, 34, 0.4)':
            '.action-btn.primary:hover { box-shadow: 0 12px 32px rgba(8, 145, 178, 0.4)',
        'box-shadow: 0 8px 24px rgba(242, 101, 34, 0.3)':
            'box-shadow: 0 8px 24px rgba(8, 145, 178, 0.3)',

        # 彩券專區: 保持紅色，改為更柔和的玫紅
        '.action-btn.lottery { background: linear-gradient(135deg, #DC2626, #EF4444)':
            '.action-btn.lottery { background: linear-gradient(135deg, #E11D48, #FB7185)',
        'box-shadow: 0 8px 24px rgba(220, 38, 38, 0.3)':
            'box-shadow: 0 8px 24px rgba(225, 29, 72, 0.3)',
    }

    for old, new in color_map.items():
        if old in c:
            c = c.replace(old, new)

    # 加入與開獎卡同款的光暈效果
    overlay_css = """
        .action-btn.primary::before, .action-btn.wallet::before, .action-btn.stats-btn::before,
        .action-btn.lottery::before, .action-btn.number-stats::before, .action-btn.settings::before,
        .action-btn.admin::before {
            content: ''; position: absolute; top: -50%; right: -50%;
            width: 100%; height: 100%;
            background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 60%);
            pointer-events: none;
        }
        .action-btn.primary, .action-btn.wallet, .action-btn.stats-btn,
        .action-btn.lottery, .action-btn.number-stats, .action-btn.settings,
        .action-btn.admin { position: relative; overflow: hidden; }"""

    if "radial-gradient(circle, rgba(255,255,255,0.12)" not in c:
        # Insert before </style>
        c = c.replace("</style>", overlay_css + "\n    </style>", 1)

    if c != orig:
        with open(DASH, "w", encoding="utf-8") as f:
            f.write(c)
        fix("快速操作卡片改色（去橘+光暈）")


# =====================================================================
print(f"\n{'='*50}")
print(f"Total: {fixes} fixes")
print(f"{'='*50}")
if fixes > 0:
    print("\nGit:")
    print("   git add static/admin.html static/admin_lottery.html static/dashboard.html app/api/v1/admin.py")
    print('   git commit -m "fix: 移除admin同步+修刪除500+快速操作改色"')
    print("   git push")
