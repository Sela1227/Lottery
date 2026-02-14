#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA Bug 修復 - 4合1
日期：2026-02-14

Bug 1: 電腦版 header 過寬 → 所有頁面加 desktop padding
Bug 2: 首頁近期活動空的 → 沒開期時顯示集資本身
Bug 3: 集資詳情返回鍵比例不對 → 修正 back-btn 樣式
Bug 4: 加碼寫死 50 → 動態設定 min/step/hint
"""
import os, sys, re

BASE = os.path.dirname(os.path.abspath(__file__))
total = 0

def safe_patch(filepath, label):
    """Read file, return (content, original) or None if not found"""
    if not os.path.exists(filepath):
        print(f"  [{label}] {os.path.basename(filepath)}: not found")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return content

def save_file(filepath, content, original, label, changes):
    global total
    if content != original:
        with open(filepath + ".bak4", "w", encoding="utf-8") as f:
            f.write(original)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        total += changes
        print(f"  [{label}] {changes} fixes")
    else:
        print(f"  [{label}] already patched")


# =====================================================================
# Bug 1: Header 過寬 - 多頁面統一處理
# =====================================================================
print("\n=== Bug 1: Header desktop padding ===")

DESKTOP_HEADER_CSS = """
        @media (min-width: 900px) {
            .header { padding-left: calc((100vw - 800px) / 2 + 20px); padding-right: calc((100vw - 800px) / 2 + 20px); }
        }"""

header_pages = {
    "dashboard.html": os.path.join(BASE, "static", "dashboard.html"),
    "wallet.html": os.path.join(BASE, "static", "wallet.html"),
    "lottery.html": os.path.join(BASE, "static", "lottery.html"),
    "settings.html": os.path.join(BASE, "static", "settings.html"),
    "admin.html": os.path.join(BASE, "static", "admin.html"),
    "admin_lottery.html": os.path.join(BASE, "static", "admin_lottery.html"),
    "personal-tickets.html": os.path.join(BASE, "static", "personal-tickets.html"),
}

for name, path in header_pages.items():
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()
    if "min-width: 900px" in c or "min-width: 700px" in c:
        continue  # already has desktop media query
    
    # Find </style> and insert before it
    if "</style>" in c:
        orig = c
        c = c.replace("</style>", DESKTOP_HEADER_CSS + "\n    </style>", 1)
        if c != orig:
            with open(path, "w", encoding="utf-8") as f:
                f.write(c)
            total += 1
            print(f"  {name}: added desktop header padding")

# series.html and series-detail.html may already have it from previous patches
for name in ["series.html", "series-detail.html"]:
    path = os.path.join(BASE, "static", name)
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()
    if "min-width: 900px" in c or "min-width: 700px" in c:
        print(f"  {name}: already has desktop padding")


# =====================================================================
# Bug 2: 首頁近期活動 - 沒開期時顯示集資資訊
# =====================================================================
print("\n=== Bug 2: Dashboard recent activity ===")
DASH = os.path.join(BASE, "static", "dashboard.html")
c = safe_patch(DASH, "Bug2")
if c:
    orig = c
    ch = 0

    # 原本：recentGroups.length === 0 時顯示「尚無單期團」
    # 改為：顯示集資本身的資訊
    old_empty = """if (recentGroups.length === 0) {
                container.innerHTML = `<div class="empty-state"><div class="empty-icon">\U0001f4cb</div><h3 class="empty-title">\u5c1a\u7121\u55ae\u671f\u5718</h3><p class="empty-desc">\u7ba1\u7406\u54e1\u958b\u65b0\u671f\u5f8c\u6703\u986f\u793a\u5728\u9019\u88e1</p></div>`;
                return;
            }"""
    new_empty = """if (recentGroups.length === 0) {
                // \u6c92\u6709\u55ae\u671f\u5718\u6642\uff0c\u986f\u793a\u96c6\u8cc7\u672c\u8eab
                const LNAMES = { 'power': '\u5a01\u529b\u5f69', 'super': '\u5927\u6a02\u900f', 'daily539': '\u4eca\u5f69539' };
                container.innerHTML = seriesList.slice(0, 5).map(s => `
                    <a href="/series/${s.id}" class="activity-item">
                        <div class="activity-info">
                            <div class="activity-name">${s.name}</div>
                            <div class="activity-detail">${LNAMES[s.lottery_types?.[0]] || s.lottery_types?.[0] || ''} \u00b7 \u8cc7\u91d1\u6c60 $${Number(s.current_pool).toLocaleString()} \u00b7 ${s.member_count} \u4eba</div>
                        </div>
                        <span class="activity-status collecting">\u9032\u884c\u4e2d</span>
                    </a>
                `).join('');
                return;
            }"""
    
    if old_empty in c:
        c = c.replace(old_empty, new_empty)
        ch += 1
        print("  \u2192 \u6c92\u958b\u671f\u6642\u986f\u793a\u96c6\u8cc7\u8cc7\u8a0a")
    else:
        # Try with mojibake
        empty_match = re.search(
            r'if \(recentGroups\.length === 0\) \{\s*container\.innerHTML = `[^`]*empty-state[^`]*`;\s*return;\s*\}',
            c, re.DOTALL
        )
        if empty_match:
            c = c[:empty_match.start()] + new_empty + c[empty_match.end():]
            ch += 1
            print("  \u2192 \u6c92\u958b\u671f\u6642\u986f\u793a\u96c6\u8cc7\u8cc7\u8a0a (regex)")

    save_file(DASH, c, orig, "Bug2", ch)


# =====================================================================
# Bug 3: 集資詳情返回鍵
# =====================================================================
print("\n=== Bug 3: Series-detail back button ===")
SD = os.path.join(BASE, "static", "series-detail.html")
c = safe_patch(SD, "Bug3")
if c:
    orig = c
    ch = 0

    # 修正 back-btn 樣式 - 目前是 36x36 的小方塊放「← 返回」文字放不下
    # 改為正常的 pill button
    old_back = ".back-btn { width: 36px; height: 36px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-secondary); display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 18px; text-decoration: none; color: var(--text-primary); }"
    new_back = ".back-btn { padding: 8px 16px; border-radius: 8px; background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 14px; font-weight: 500; text-decoration: none; color: white; white-space: nowrap; gap: 4px; }"
    if old_back in c:
        c = c.replace(old_back, new_back)
        ch += 1
        print("  \u2192 back-btn \u6539\u70ba pill button")
    
    # 如果之前 patch 加了 .back-btn { color: var(--text-primary); } 重複定義，移除
    dup_back = "\n        .back-btn { color: var(--text-primary); }"
    if dup_back in c and "background: rgba(255,255,255,0.2)" in c:
        c = c.replace(dup_back, "")
        ch += 1
        print("  \u2192 \u79fb\u9664\u91cd\u8907 back-btn \u5b9a\u7fa9")

    # Bug 4: 加碼 modal - 動態設定 min/step/hint
    # 找到 showTopupModal 函數，加入動態設定
    old_show_topup = "function showTopupModal() { $('topup-modal').classList.add('active'); }"
    new_show_topup = """function showTopupModal() {
            // \u52d5\u614b\u8a2d\u5b9a\u5f69\u7a2e\u55ae\u50f9
            const lt = (currentSeries?.allowed_lottery_types || ['power'])[0];
            const PRICES = { 'power': 100, 'super': 50, 'daily539': 50 };
            const LNAMES = { 'power': '\u5a01\u529b\u5f69', 'super': '\u5927\u6a02\u900f', 'daily539': '\u4eca\u5f69539' };
            const p = PRICES[lt] || 100;
            const inp = $('topup-amount');
            if (inp) { inp.min = p; inp.step = p; inp.value = p; }
            const hint = document.querySelector('#topup-modal .form-hint');
            if (hint) hint.textContent = `\u9700\u70ba $${p} \u7684\u500d\u6578\uff08${LNAMES[lt] || lt} \u55ae\u50f9 $${p}/\u6ce8\uff09`;
            $('topup-modal').classList.add('active');
        }"""
    if old_show_topup in c:
        c = c.replace(old_show_topup, new_show_topup)
        ch += 1
        print("  \u2192 showTopupModal \u52d5\u614b\u8a2d\u5b9a min/step/hint")

    save_file(SD, c, orig, "Bug3+4", ch)


# =====================================================================
# Summary
# =====================================================================
print(f"\n{'='*50}")
print(f"Total: {total} fixes")
print(f"{'='*50}")
if total > 0:
    print("\nGit:")
    print("   git add static/")
    print('   git commit -m "fix: header\u904e\u5bec+\u8fd1\u671f\u6d3b\u52d5+\u8fd4\u56de\u9375+\u52a0\u78bc\u55ae\u50f9"')
    print("   git push")
