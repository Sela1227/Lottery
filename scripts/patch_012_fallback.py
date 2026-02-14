#!/usr/bin/env python3
"""
SELA 樂透一路發 - Patch 012: 穩定性優化
為所有頁面添加備援函數，防止 common.js 載入失敗

使用方式：
    cd /path/to/sela-lottery
    python scripts/patch_012_fallback.py
"""

import os
import re

# 備援函數模板
FALLBACK_FUNCTIONS = '''
        // ==================== 備援函數（防止 common.js 載入失敗）====================
        if (typeof $ === 'undefined') window.$ = id => document.getElementById(id);
        if (typeof setText === 'undefined') window.setText = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
        if (typeof setHtml === 'undefined') window.setHtml = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };
        if (typeof getToken === 'undefined') window.getToken = () => { try { return localStorage.getItem('access_token'); } catch(e) { return null; } };
        if (typeof removeToken === 'undefined') window.removeToken = () => { try { localStorage.removeItem('access_token'); } catch(e) {} };
        if (typeof checkAuth === 'undefined') window.checkAuth = () => { if (!getToken()) { window.location.href = '/'; return false; } return true; };
        if (typeof apiGet === 'undefined') window.apiGet = async (url) => { const r = await fetch('/api/v1' + url, { headers: { 'Authorization': 'Bearer ' + getToken() } }); if (!r.ok) throw new Error('API Error'); return r.json(); };
        if (typeof apiPost === 'undefined') window.apiPost = async (url, data) => { const r = await fetch('/api/v1' + url, { method: 'POST', headers: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || 'API Error'); } return r.json(); };
        if (typeof apiPut === 'undefined') window.apiPut = async (url, data) => { const r = await fetch('/api/v1' + url, { method: 'PUT', headers: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || 'API Error'); } return r.json(); };
        if (typeof apiDelete === 'undefined') window.apiDelete = async (url) => { const r = await fetch('/api/v1' + url, { method: 'DELETE', headers: { 'Authorization': 'Bearer ' + getToken() } }); if (!r.ok) throw new Error('API Error'); return r.json(); };
        if (typeof showToast === 'undefined') window.showToast = (msg, type) => { const t = document.getElementById('toast'); if (t) { t.textContent = msg; t.className = 'toast ' + (type||'info') + ' show'; setTimeout(() => t.classList.remove('show'), 3000); } else { console.log('[Toast]', type, msg); alert(msg); } };
        if (typeof formatMoney === 'undefined') window.formatMoney = (n) => Number(n||0).toLocaleString();
        if (typeof formatDate === 'undefined') window.formatDate = (d) => { if (!d) return ''; const dt = new Date(d); return dt.getFullYear() + '/' + (dt.getMonth()+1) + '/' + dt.getDate(); };
        if (typeof getStatusText === 'undefined') window.getStatusText = (s) => ({ active:'進行中', paused:'已暫停', closed:'已結束', collecting:'集資中', locked:'已鎖定', purchased:'已購買', drawn:'已開獎', settled:'已結算' }[s] || s);
'''

# 需要處理的檔案列表（排除 index.html 和 admin.html，它們已自包含）
FILES_TO_PATCH = [
    'static/dashboard.html',
    'static/series.html',
    'static/series-detail.html',
    'static/group-detail.html',
    'static/settings.html',
    'static/statistics.html',
    'static/stats.html',
    'static/wallet.html',
    'static/personal.html',
    'static/lottery.html',
]

# 已自包含或特殊處理的檔案
SKIP_FILES = [
    'static/index.html',       # 登入頁，已自包含
    'static/admin.html',       # 需要特別處理
    'static/admin_lottery.html',  # 已自包含
]

def has_fallback(content):
    """檢查是否已有備援函數"""
    return '備援函數' in content or "typeof $ === 'undefined'" in content

def add_fallback_to_file(filepath):
    """為檔案添加備援函數"""
    if not os.path.exists(filepath):
        print(f"  ⚠️  檔案不存在: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已有備援函數
    if has_fallback(content):
        print(f"  ⏭️  已有備援函數: {filepath}")
        return False
    
    # 尋找 common.js 引用後的 <script> 標籤
    # 模式: <script src="/static/js/common.js"></script>\n    <script>
    pattern = r'(<script src="/static/js/common\.js"></script>\s*\n\s*<script>)'
    
    if not re.search(pattern, content):
        print(f"  ⚠️  找不到 common.js 引用: {filepath}")
        return False
    
    # 插入備援函數
    replacement = r'\1' + FALLBACK_FUNCTIONS
    new_content = re.sub(pattern, replacement, content, count=1)
    
    # 寫回檔案
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  ✅ 已添加備援函數: {filepath}")
    return True

def main():
    print("=" * 60)
    print("SELA 樂透一路發 - Patch 012: 穩定性優化")
    print("為所有頁面添加備援函數")
    print("=" * 60)
    print()
    
    # 確認在專案根目錄
    if not os.path.exists('static'):
        print("❌ 錯誤：請在專案根目錄執行此腳本")
        print("   cd /path/to/sela-lottery")
        print("   python scripts/patch_012_fallback.py")
        return
    
    patched = 0
    skipped = 0
    errors = 0
    
    print("📁 處理檔案...")
    print()
    
    for filepath in FILES_TO_PATCH:
        try:
            if add_fallback_to_file(filepath):
                patched += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ❌ 錯誤 {filepath}: {e}")
            errors += 1
    
    print()
    print("=" * 60)
    print(f"完成！已修補: {patched}, 跳過: {skipped}, 錯誤: {errors}")
    print("=" * 60)
    print()
    
    if patched > 0:
        print("📝 請執行以下指令提交變更：")
        print()
        print("git add static/")
        print('git commit -m "fix(patch-012): 穩定性優化 - 為所有頁面添加備援函數"')
        print("git push")
    else:
        print("✅ 所有檔案都已是最新狀態")

if __name__ == '__main__':
    main()
