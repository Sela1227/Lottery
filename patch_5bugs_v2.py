#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA 5合1修復
日期：2026-02-14

Bug 1: $$ 雙重錢號 + NaN% — 全面掃描所有 HTML
Bug 2: stats.html n.gap → n.missing (undefined期)
Bug 3: dashboard.html 移除「加入集資」快速操作
Bug 4: dashboard.html header 加開獎同步(admin only)
Bug 5: admin.html 移除號碼統計 + 集資管理加按鈕 + admin.py 加API
"""
import os, sys, re, glob

BASE = os.path.dirname(os.path.abspath(__file__))
total = 0

def count(label, n=1):
    global total
    total += n
    print(f"  {label}")


# =====================================================================
# Bug 1: 全面修 $$ 雙重錢號
# =====================================================================
print("\n=== Bug 1: $$ 雙重錢號 ===")

html_files = glob.glob(os.path.join(BASE, "static", "*.html"))
for filepath in sorted(html_files):
    name = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c

    # Pattern: $${formatMoney(xxx)} → ${formatMoney(xxx)}
    # formatMoney() 已回傳 "$1,200"，不需要再加 $
    fixes = 0

    # Replace $${ with ${ only when followed by formatMoney
    pattern = r'\$\$\{formatMoney\('
    replacement = '${formatMoney('
    new_c = re.sub(pattern, replacement, c)
    fixes += len(re.findall(pattern, c))

    # Also fix: '$' + formatMoney(...) → formatMoney(...)  (formatMoney already has $)
    # Pattern: '$' + formatMoney  or  "$" + formatMoney
    new_c = re.sub(r"'\\\$'\s*\+\s*formatMoney", "formatMoney", new_c)
    new_c = re.sub(r'"\$"\s*\+\s*formatMoney', "formatMoney", new_c)

    # Fix: setText('xxx', '$' + formatMoney(val))  → setText('xxx', formatMoney(val))
    new_c = re.sub(r"setText\(([^,]+),\s*'\$'\s*\+\s*formatMoney\(", r"setText(\1, formatMoney(", new_c)

    if new_c != c:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_c)
        count(f"{name}: {fixes} 處 $$ 修正")
    c = new_c

    # Fix NaN% in statistics - protect division by zero
    if name == "statistics.html":
        orig2 = c
        # roi_percent might be NaN when invested is 0
        # Find patterns like: ${roi >= 0 ? '+' : ''}... and protect
        c = re.sub(
            r"const roi = [^;]*;",
            lambda m: m.group(0).rstrip(';') + ' || 0;' if '|| 0' not in m.group(0) else m.group(0),
            c
        )
        # Fix: ${(p.roi_percent || 0).toFixed(1)}%  or similar NaN patterns
        c = re.sub(
            r'\$\{roi(?!_)',
            '${(isFinite(roi) ? roi : 0)',
            c
        )
        if c != orig2:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(c)
            count(f"{name}: NaN% 保護")


# =====================================================================
# Bug 2: stats.html — n.gap → n.missing
# =====================================================================
print("\n=== Bug 2: stats.html undefined期 ===")
STATS = os.path.join(BASE, "static", "stats.html")
if os.path.exists(STATS):
    with open(STATS, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c

    if "n.gap}" in c:
        c = c.replace("${n.gap}", "${n.missing}")
        with open(STATS, "w", encoding="utf-8") as f:
            f.write(c)
        count("n.gap → n.missing")
    else:
        print("  already patched or not found")


# =====================================================================
# Bug 3: dashboard.html — 移除「加入集資」
# =====================================================================
print("\n=== Bug 3: 移除加入集資按鈕 ===")
DASH = os.path.join(BASE, "static", "dashboard.html")
if os.path.exists(DASH):
    with open(DASH, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c

    # Remove the 加入集資 action button (using regex for encoding flexibility)
    join_pattern = re.compile(
        r'\s*<a[^>]*onclick="event\.preventDefault\(\);\s*showJoinModal\(\);"[^>]*>.*?</a>',
        re.DOTALL
    )
    new_c = join_pattern.sub('', c)
    if new_c != c:
        c = new_c
        with open(DASH, "w", encoding="utf-8") as f:
            f.write(c)
        count("移除加入集資按鈕")
    else:
        print("  already removed or not found")


# =====================================================================
# Bug 4: dashboard.html — header 加開獎同步 (admin only)
# =====================================================================
print("\n=== Bug 4: 首頁 header 加開獎同步 ===")
if os.path.exists(DASH):
    with open(DASH, "r", encoding="utf-8") as f:
        c = f.read()

    if "admin-sync-btn" not in c:
        # Add sync button in header (hidden by default, shown for admin)
        # Find the logout button area in header
        logout_pattern = re.compile(
            r'(<a[^>]*class="logout-btn"[^>]*>[^<]*</a>)'
        )
        match = logout_pattern.search(c)
        if match:
            sync_btn = '<a href="/admin/lottery" class="sync-btn" id="admin-sync-btn" style="display:none;">🎰 同步</a>\n            '
            c = c[:match.start()] + sync_btn + c[match.start():]

            # Add CSS for sync button
            sync_css = """
        .sync-btn { padding: 6px 14px; background: var(--sela-orange); color: white; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; white-space: nowrap; }
        .sync-btn:hover { opacity: 0.9; }"""
            c = c.replace("</style>", sync_css + "\n    </style>", 1)

            # Show sync button for admin in init
            show_admin = "if (isAdmin) {"
            if show_admin in c:
                # Find the block and add sync btn show
                admin_block_match = re.search(r'if \(isAdmin\) \{[^}]*\}', c)
                if admin_block_match:
                    block = admin_block_match.group(0)
                    if "admin-sync-btn" not in block:
                        new_block = block.replace(
                            "if (isAdmin) {",
                            "if (isAdmin) {\n                    const syncBtn = $('admin-sync-btn'); if (syncBtn) syncBtn.style.display = '';"
                        )
                        c = c.replace(block, new_block)

            with open(DASH, "w", encoding="utf-8") as f:
                f.write(c)
            count("header 加開獎同步按鈕 (admin)")
        else:
            # Try alternate header structure
            header_right_pattern = re.compile(r'(<div class="header-right">)')
            match2 = header_right_pattern.search(c)
            if match2:
                sync_html = '<a href="/admin/lottery" class="sync-btn" id="admin-sync-btn" style="display:none;">\U0001f3b0 同步</a>'
                c = c.replace(match2.group(0), match2.group(0) + '\n                ' + sync_html)

                sync_css = """
        .sync-btn { padding: 6px 14px; background: var(--sela-orange); color: white; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; white-space: nowrap; }
        .sync-btn:hover { opacity: 0.9; }"""
                c = c.replace("</style>", sync_css + "\n    </style>", 1)

                show_admin = "if (isAdmin) {"
                if show_admin in c:
                    admin_block_match = re.search(r'if \(isAdmin\) \{[^}]*\}', c)
                    if admin_block_match:
                        block = admin_block_match.group(0)
                        if "admin-sync-btn" not in block:
                            new_block = block.replace(
                                "if (isAdmin) {",
                                "if (isAdmin) {\n                    const syncBtn = $('admin-sync-btn'); if (syncBtn) syncBtn.style.display = '';"
                            )
                            c = c.replace(block, new_block)

                with open(DASH, "w", encoding="utf-8") as f:
                    f.write(c)
                count("header 加開獎同步按鈕 (admin) v2")
            else:
                print("  header structure not matched")
    else:
        print("  already has sync button")


# =====================================================================
# Bug 5a: admin.html — 移除號碼統計 + 集資加管理按鈕
# =====================================================================
print("\n=== Bug 5a: admin.html 調整 ===")
ADMIN = os.path.join(BASE, "static", "admin.html")
if os.path.exists(ADMIN):
    with open(ADMIN, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c
    ch = 0

    # 5a-1: 移除號碼統計快速操作
    stats_link = re.compile(
        r'\s*<a[^>]*href="/stats"[^>]*class="action-btn"[^>]*>.*?</a>',
        re.DOTALL
    )
    new_c = stats_link.sub('', c)
    if new_c != c:
        c = new_c
        ch += 1
        count("移除號碼統計快速操作")

    # 5a-2: 集資列表加管理按鈕
    # Replace the current series list item rendering
    old_series_item = """list.innerHTML = series.slice(0, 10).map(s => `
                    <div class="list-item">
                        <div class="item-info">
                            <div class="item-name">${s.name}</div>
                            <div class="item-detail">"""

    if old_series_item in c:
        new_series_render = """list.innerHTML = series.slice(0, 10).map(s => `
                    <div class="list-item">
                        <div class="item-info">
                            <div class="item-name"><a href="/series/${s.id}" style="color:inherit;text-decoration:none;">${s.name}</a></div>
                            <div class="item-detail">"""
        c = c.replace(old_series_item, new_series_render)
        ch += 1
        count("集資名稱加連結")

    # Replace badge with badge + buttons
    old_badge = """<span class="item-badge ${s.status === 'active' ? 'badge-active' : 'badge-closed'}">
                            ${s.status === 'active' ? '\u9032\u884c\u4e2d' : '\u5df2\u7d50\u675f'}
                        </span>
                    </div>"""
    new_badge = """<div class="item-actions">
                            <span class="item-badge ${s.status === 'active' ? 'badge-active' : 'badge-closed'}">${s.status === 'active' ? '\u9032\u884c\u4e2d' : '\u5df2\u7d50\u675f'}</span>
                            ${s.status === 'active' ? `<button class="btn-sm btn-secondary" onclick="adminEndSeries(${s.id}, '${s.name}')">\u7d50\u675f</button>` : ''}
                            <button class="btn-sm btn-danger" onclick="adminDeleteSeries(${s.id}, '${s.name}')">\u522a\u9664</button>
                        </div>
                    </div>"""

    if old_badge in c:
        c = c.replace(old_badge, new_badge)
        ch += 1
        count("集資加管理按鈕")
    else:
        # Try regex
        badge_re = re.compile(
            r'<span class="item-badge \$\{s\.status[^"]*">\s*\$\{s\.status[^}]*\}\s*</span>\s*</div>',
            re.DOTALL
        )
        match = badge_re.search(c)
        if match:
            c = c[:match.start()] + new_badge + c[match.end():]
            ch += 1
            count("集資加管理按鈕 (regex)")

    # 5a-3: 加入 adminEndSeries / adminDeleteSeries JS 函數
    if "async function adminEndSeries" not in c:
        admin_funcs = """
        async function adminEndSeries(id, name) {
            if (!confirm(\`確定要強制結束「\${name}」？\`)) return;
            try {
                await api(\`/admin/series/\${id}/end\`, { method: 'POST' });
                showToast('已結束', 'success');
                loadSeries();
            } catch (e) { showToast(e.message || '操作失敗', 'error'); }
        }
        
        async function adminDeleteSeries(id, name) {
            if (!confirm(\`確定要刪除「\${name}」？此操作無法復原！\`)) return;
            if (!confirm('再次確認：刪除後所有資料將永久消失')) return;
            try {
                await api(\`/admin/series/\${id}\`, { method: 'DELETE' });
                showToast('已刪除', 'success');
                loadSeries();
                loadStats();
            } catch (e) { showToast(e.message || '操作失敗', 'error'); }
        }"""

        # Insert before init()
        init_marker = "async function init() {"
        if init_marker in c:
            c = c.replace(init_marker, admin_funcs + "\n\n        " + init_marker)
            ch += 1
            count("加入 adminEndSeries/adminDeleteSeries")

    # 5a-4: 修正 api() helper 支援 method 參數
    # Current: async function api(url) { ... fetch('/api/v1' + url, { headers... })
    old_api = "async function api(url) {"
    new_api = "async function api(url, opts = {}) {"
    if old_api in c and "opts" not in c:
        c = c.replace(old_api, new_api)
        # Also update fetch call to merge opts
        old_fetch = re.search(
            r"const r = await fetch\('/api/v1' \+ url, \{ headers: \{ 'Authorization': 'Bearer ' \+ getToken\(\) \} \}\);",
            c
        )
        if old_fetch:
            c = c.replace(
                old_fetch.group(0),
                "const r = await fetch('/api/v1' + url, { ...opts, headers: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json', ...(opts.headers || {}) } });"
            )
            ch += 1
            count("api() helper 支援 method 參數")

    if c != orig:
        with open(ADMIN + ".bak6", "w", encoding="utf-8") as f:
            f.write(orig)
        with open(ADMIN, "w", encoding="utf-8") as f:
            f.write(c)
else:
    print("  admin.html not found")


# =====================================================================
# Bug 5b: admin.py — 加 force-end / delete API
# =====================================================================
print("\n=== Bug 5b: admin.py 加 API ===")
ADMIN_PY = os.path.join(BASE, "app", "api", "v1", "admin.py")
if os.path.exists(ADMIN_PY):
    with open(ADMIN_PY, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c

    if "admin_end_series" not in c:
        # Find a good injection point - after list_all_series or before logs
        inject_marker = '@router.get("/logs"'
        if inject_marker not in c:
            inject_marker = '@router.post("/broadcast"'

        new_endpoints = '''

@router.post("/series/{series_id}/end")
async def admin_end_series(
    series_id: int,
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """\u7ba1\u7406\u54e1\u5f37\u5236\u7d50\u675f\u96c6\u8cc7"""
    series = db.query(GroupSeries).filter(GroupSeries.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="\u96c6\u8cc7\u4e0d\u5b58\u5728")
    if series.status == SeriesStatus.ENDED:
        raise HTTPException(status_code=400, detail="\u96c6\u8cc7\u5df2\u7d50\u675f")
    
    series.status = SeriesStatus.ENDED
    series.end_reason = "\u7ba1\u7406\u54e1\u5f37\u5236\u7d50\u675f"
    
    # \u6a19\u8a18\u6240\u6709\u6210\u54e1\u70ba EXITED
    db.query(GroupMember).filter(
        GroupMember.series_id == series_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).update({"status": MemberStatus.EXITED}, synchronize_session=False)
    
    db.commit()
    return {"success": True, "message": f"\u96c6\u8cc7\u300c{series.name}\u300d\u5df2\u5f37\u5236\u7d50\u675f"}


@router.delete("/series/{series_id}")
async def admin_delete_series(
    series_id: int,
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """\u7ba1\u7406\u54e1\u522a\u9664\u96c6\u8cc7\uff08\u8edf\u522a\u9664 + \u6e05\u5e33\u672c\uff09"""
    series = db.query(GroupSeries).filter(GroupSeries.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="\u96c6\u8cc7\u4e0d\u5b58\u5728")
    
    # \u672a\u958b\u904e\u671f\u7684\u6e05\u5e33\u672c
    if series.total_periods == 0:
        db.query(UserLedger).filter(UserLedger.series_id == series_id).delete(synchronize_session=False)
    
    # \u8edf\u522a\u9664
    series.status = SeriesStatus.ENDED
    series.end_reason = "\u7ba1\u7406\u54e1\u522a\u9664"
    
    db.query(GroupMember).filter(
        GroupMember.series_id == series_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).update({"status": MemberStatus.EXITED}, synchronize_session=False)
    
    db.commit()
    return {"success": True, "message": f"\u96c6\u8cc7\u300c{series.name}\u300d\u5df2\u522a\u9664"}


'''

        if inject_marker in c:
            c = c.replace(inject_marker, new_endpoints + inject_marker)
        else:
            # Append to end of file
            c = c.rstrip() + "\n" + new_endpoints

        # Ensure imports
        if "UserLedger" not in c:
            # Add import
            if "from app.models.member import" in c:
                c = c.replace(
                    "from app.models.member import",
                    "from app.models.ledger import UserLedger\nfrom app.models.member import"
                )

        with open(ADMIN_PY + ".bak6", "w", encoding="utf-8") as f:
            f.write(orig)
        with open(ADMIN_PY, "w", encoding="utf-8") as f:
            f.write(c)
        count("admin.py: 加入 force-end + delete API")
    else:
        print("  already has admin series endpoints")
else:
    print("  admin.py not found")


# =====================================================================
# Summary
# =====================================================================
print(f"\n{'='*50}")
print(f"Total: {total} fixes")
print(f"{'='*50}")
if total > 0:
    print("\nGit:")
    print("   git add static/ app/api/v1/admin.py")
    print('   git commit -m "fix: $$\u96d9\u91cd\u9322\u865f+undefined\u671f+\u79fb\u9664\u52a0\u5165\u96c6\u8cc7+\u540c\u6b65\u6309\u9215+\u7ba1\u7406\u529f\u80fd"')
    print("   git push")
