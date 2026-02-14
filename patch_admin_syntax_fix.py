#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA Hotfix: admin.html JS 語法錯誤
問題：patch_5bugs_v2 注入的 adminEndSeries/adminDeleteSeries 
     反引號被 Python 轉義成 \\` 和 \\${}
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ADMIN = os.path.join(BASE, "static", "admin.html")

if not os.path.exists(ADMIN):
    print("admin.html not found")
    exit(1)

with open(ADMIN, "r", encoding="utf-8") as f:
    c = f.read()
orig = c

# 方案：直接替換壞掉的函數為正確的
broken_funcs = r"""
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

fixed_funcs = """
        async function adminEndSeries(id, name) {
            if (!confirm('確定要強制結束「' + name + '」？')) return;
            try {
                await api('/admin/series/' + id + '/end', { method: 'POST' });
                showToast('已結束', 'success');
                loadSeries();
            } catch (e) { showToast(e.message || '操作失敗', 'error'); }
        }
        
        async function adminDeleteSeries(id, name) {
            if (!confirm('確定要刪除「' + name + '」？此操作無法復原！')) return;
            if (!confirm('再次確認：刪除後所有資料將永久消失')) return;
            try {
                await api('/admin/series/' + id, { method: 'DELETE' });
                showToast('已刪除', 'success');
                loadSeries();
                loadStats();
            } catch (e) { showToast(e.message || '操作失敗', 'error'); }
        }"""

if broken_funcs in c:
    c = c.replace(broken_funcs, fixed_funcs)
    print("Fix 1: 修正反引號轉義 (exact match)")
else:
    # Try fixing all escaped backticks in the file
    if '\\`' in c or '\\${' in c:
        # Only fix within the admin functions area
        import re
        # Replace \` with ` and \${ with ${
        c = c.replace('\\`', '`')
        c = c.replace('\\${', '${')
        print("Fix 1: 修正反引號轉義 (global replace)")
    else:
        print("No escaped backticks found - may already be fixed")

# Also apply the api() fix from hotfix patch
if "async function api(url, opts = {}) {" in c:
    import re
    api_match = re.search(
        r'async function api\(url, opts = \{}\)\s*\{.*?return response\.json\(\);\s*\}',
        c, re.DOTALL
    )
    if api_match and "opts.method" not in api_match.group(0):
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
                throw new Error(data.detail || 'API 錯誤');
            }
            return response.json();
        }"""
        c = c[:api_match.start()] + new_api + c[api_match.end():]
        print("Fix 2: 修正 api() 支援 method/body")

if c != orig:
    with open(ADMIN, "w", encoding="utf-8") as f:
        f.write(c)
    print("\n完成！")
    print("   git add static/admin.html")
    print('   git commit -m "hotfix: admin.html JS 語法錯誤"')
    print("   git push")
else:
    print("No changes needed")
