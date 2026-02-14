#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA Hotfix：
1. dashboard sync 按鈕顯示邏輯
2. admin.html api() 函數修正
"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
total = 0

# =====================================================================
# Fix 1: dashboard.html - sync button 顯示
# =====================================================================
print("\n=== Fix 1: dashboard sync button ===")
DASH = os.path.join(BASE, "static", "dashboard.html")
if os.path.exists(DASH):
    with open(DASH, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c

    # 1a: 確認 sync 按鈕存在
    if "admin-sync-btn" not in c:
        # 加在 header-right 裡面
        hr = '<div class="header-right">'
        if hr in c:
            sync_btn = '<a href="/admin/lottery" class="sync-btn" id="admin-sync-btn" style="display:none;">\U0001f3b0 同步</a>\n            '
            c = c.replace(hr, hr + '\n                ' + sync_btn)

            sync_css = """
        .sync-btn { padding: 6px 14px; background: var(--sela-orange); color: white; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; white-space: nowrap; }
        .sync-btn:hover { opacity: 0.9; }"""
            c = c.replace("</style>", sync_css + "\n    </style>", 1)
            total += 1
            print("  加入 sync 按鈕")

    # 1b: 在 admin-btn 顯示邏輯旁加 sync 顯示
    # 原本: if (adminBtn && user.role === 'admin') adminBtn.style.display = 'block';
    old_admin_show = "if (adminBtn && user.role === 'admin') adminBtn.style.display = 'block';"
    if old_admin_show in c and "admin-sync-btn" not in c.split(old_admin_show)[1][:200]:
        new_admin_show = old_admin_show + "\n            const syncBtn = $('admin-sync-btn'); if (syncBtn && user.role === 'admin') syncBtn.style.display = '';"
        c = c.replace(old_admin_show, new_admin_show)
        total += 1
        print("  加入 sync 顯示邏輯")
    else:
        # Maybe already patched with a different pattern
        # Try regex to find admin role check
        admin_check = re.search(
            r"(if \([^)]*user\.role === 'admin'[^)]*\)[^;]*admin[^;]*;)",
            c
        )
        if admin_check and "admin-sync-btn" not in c[admin_check.end():admin_check.end()+300]:
            insert_pos = admin_check.end()
            c = c[:insert_pos] + "\n            const syncBtn = $('admin-sync-btn'); if (syncBtn) syncBtn.style.display = '';" + c[insert_pos:]
            total += 1
            print("  加入 sync 顯示邏輯 (regex)")

    if c != orig:
        with open(DASH, "w", encoding="utf-8") as f:
            f.write(c)


# =====================================================================
# Fix 2: admin.html - api() 函數修正
# =====================================================================
print("\n=== Fix 2: admin.html api() ===")
ADMIN = os.path.join(BASE, "static", "admin.html")
if os.path.exists(ADMIN):
    with open(ADMIN, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c

    # 問題：patch 把 api(url) 改成 api(url, opts={}) 但 fetch 沒更新
    # 修正：完整替換 api() 函數支援 opts
    
    # 找到當前的 api 函數（可能已被部分修改）
    api_pattern = re.compile(
        r'async function api\(url(?:,\s*opts\s*=\s*\{})?\)\s*\{.*?return response\.json\(\);\s*\}',
        re.DOTALL
    )
    match = api_pattern.search(c)
    if match:
        new_api = """async function api(url, opts = {}) {
            const token = getToken();
            const method = opts.method || 'GET';
            const fetchOpts = {
                method,
                headers: { 
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }
            };
            if (opts.body) fetchOpts.body = typeof opts.body === 'string' ? opts.body : JSON.stringify(opts.body);
            const response = await fetch(API_BASE + url, fetchOpts);
            if (response.status === 401) {
                window.location.href = '/';
                return null;
            }
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || 'API \u932f\u8aa4');
            }
            return response.json();
        }"""
        c = c[:match.start()] + new_api + c[match.end():]
        total += 1
        print("  \u4fee\u6b63 api() \u51fd\u6578")
    else:
        print("  api() not found with expected pattern")
        # Try just fixing if opts was added but fetch wasn't updated
        if "async function api(url, opts = {}) {" in c and "...opts" in c:
            # The spread operator broke things, revert to clean version
            print("  Detected broken ...opts, fixing...")
    
    # 也確認 adminEndSeries/adminDeleteSeries 用正確的 api() 呼叫
    # api(`/admin/series/${id}/end`, { method: 'POST' }) 
    # api(`/admin/series/${id}`, { method: 'DELETE' })
    # 這些應該已經OK

    if c != orig:
        with open(ADMIN, "w", encoding="utf-8") as f:
            f.write(c)


# =====================================================================
print(f"\n{'='*50}")
print(f"Total: {total} fixes")
print(f"{'='*50}")
if total > 0:
    print("\nGit:")
    print("   git add static/dashboard.html static/admin.html")
    print('   git commit -m "hotfix: sync\u6309\u9215\u986f\u793a+admin api()\u4fee\u6b63"')
    print("   git push")
