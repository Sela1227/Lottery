#!/usr/bin/env python3
"""
SELA 樂透一路發 - Patch 015: 統一 Header 返回鍵
1. 所有頁面返回鍵在右上角
2. stats.html (熱門號碼) 返回首頁 /dashboard
"""

import os
import re

# 標準 header 模板
HEADER_TEMPLATE = '''    <header class="header">
        <div class="header-left">
            <img src="/static/logo.jpg" alt="SELA" class="logo">
            <span class="brand">{title}</span>
        </div>
        <a href="{back}" class="back-btn">← 返回</a>
    </header>'''

# 頁面設定：(標題, 返回目標)
PAGES = {
    'static/series.html': ('我的集資', '/dashboard'),
    'static/series-detail.html': ('集資詳情', '/series'),
    'static/group-detail.html': ('單期團', '/series'),
    'static/lottery.html': ('開獎專區', '/dashboard'),
    'static/stats.html': ('號碼統計', '/dashboard'),  # 熱門號碼 -> 首頁
    'static/statistics.html': ('統計報表', '/dashboard'),
    'static/wallet.html': ('我的錢包', '/dashboard'),
    'static/personal.html': ('個人彩券', '/dashboard'),
    'static/settings.html': ('設定', '/dashboard'),
    'static/admin.html': ('管理後台', '/dashboard'),
}

def fix_page(filepath, title, back_target):
    if not os.path.exists(filepath):
        print(f"  ⚠️  找不到: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 檢查是否已正確
    correct = f'<a href="{back_target}" class="back-btn">← 返回</a>'
    if correct in content and '<div class="header-left">' in content:
        print(f"  ⏭️  已正確: {filepath}")
        return False
    
    # 匹配各種可能的 header 格式並替換
    patterns = [
        # 格式1: 返回鍵在左邊 <header><div class="header-left"><a class="back-btn">
        r'<header[^>]*class="header"[^>]*>\s*<div[^>]*class="header-left"[^>]*>\s*<a[^>]*class="back-btn"[^>]*>[^<]*</a>\s*[^<]*<[^/][^>]*>[^<]*</[^>]*>\s*</div>(?:\s*<div[^>]*class="header-right"[^>]*>.*?</div>)?\s*</header>',
        # 格式2: 沒有 header-left <header><a class="back-btn">...<h1>
        r'<header[^>]*class="header"[^>]*>\s*<a[^>]*class="back-btn"[^>]*>[^<]*</a>\s*<[^/][^>]*>[^<]*</[^>]*>\s*</header>',
        # 格式3: 標準格式但返回目標錯誤
        r'<header[^>]*class="header"[^>]*>\s*<div[^>]*class="header-left"[^>]*>\s*<img[^>]*>\s*<span[^>]*class="brand"[^>]*>[^<]*</span>\s*</div>\s*<a[^>]*href="[^"]*"[^>]*class="back-btn"[^>]*>[^<]*</a>\s*</header>',
    ]
    
    new_header = HEADER_TEMPLATE.format(title=title, back=back_target)
    
    for pattern in patterns:
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_header, content, flags=re.DOTALL)
            break
    
    # 如果還是沒改到，嘗試只修正返回目標
    if content == original:
        # 修正返回連結目標
        content = re.sub(
            r'(<a[^>]*href=")[^"]*("[^>]*class="back-btn")',
            rf'\g<1>{back_target}\g<2>',
            content
        )
        # 確保返回文字是 "← 返回"
        content = re.sub(
            r'(<a[^>]*class="back-btn"[^>]*>)[^<]*(</a>)',
            r'\g<1>← 返回\g<2>',
            content
        )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ 已修正: {filepath} -> {back_target}")
        return True
    
    print(f"  ℹ️  格式特殊，請手動檢查: {filepath}")
    return False

def main():
    print("=" * 55)
    print("Patch 015: 統一 Header 返回鍵")
    print("  - 返回鍵在右上角")
    print("  - 熱門號碼(stats) 返回首頁")
    print("=" * 55)
    print()
    
    if not os.path.exists('static'):
        print("❌ 請在專案根目錄執行")
        return
    
    updated = 0
    for filepath, (title, back) in PAGES.items():
        if fix_page(filepath, title, back):
            updated += 1
    
    print()
    print("=" * 55)
    print(f"完成！已更新 {updated} 個檔案")
    
    if updated > 0:
        print()
        print("📝 請執行:")
        print("git add static/")
        print('git commit -m "fix: 統一 Header 返回鍵位置"')
        print("git push")

if __name__ == '__main__':
    main()
