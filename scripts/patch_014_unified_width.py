#!/usr/bin/env python3
"""
SELA 樂透一路發 - Patch 014: 統一電腦版頁面寬度
解決電腦版各頁面忽大忽小的問題
"""

import os
import re

# 頁面寬度統一設定
# 一般頁面: 720px (平板) / 800px (桌面)
# 管理頁面: 960px (平板) / 1100px (桌面)

PAGES_CONFIG = {
    # 一般用戶頁面 - 統一 800px
    'static/dashboard.html': 800,
    'static/series.html': 800,
    'static/series-detail.html': 800,
    'static/group-detail.html': 800,
    'static/lottery.html': 800,
    'static/statistics.html': 800,
    'static/stats.html': 800,
    'static/wallet.html': 800,
    'static/personal.html': 800,
    'static/settings.html': 800,
    # 管理頁面 - 更寬
    'static/admin.html': 1000,
    'static/admin_lottery.html': 1000,
}

def update_page_width(filepath, target_width):
    """更新頁面的 max-width 設定"""
    if not os.path.exists(filepath):
        print(f"  ⚠️  找不到: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 替換 .main 的 max-width（各種可能的格式）
    # 1. .main { ... max-width: XXXpx ... }
    # 2. style 中的 max-width
    
    # 找到 <style> 區塊中的 .main 定義
    def replace_main_maxwidth(match):
        block = match.group(0)
        # 替換 max-width 值
        new_block = re.sub(
            r'max-width:\s*\d+px',
            f'max-width: {target_width}px',
            block
        )
        return new_block
    
    # 匹配 .main { ... } 區塊
    content = re.sub(
        r'\.main\s*\{[^}]*max-width:\s*\d+px[^}]*\}',
        replace_main_maxwidth,
        content,
        flags=re.DOTALL
    )
    
    # 也處理 inline style 中的 max-width（如果有的話）
    # <main class="main" style="max-width: XXXpx">
    content = re.sub(
        r'(<main[^>]*style="[^"]*?)max-width:\s*\d+px',
        rf'\1max-width: {target_width}px',
        content
    )
    
    if content == original:
        # 如果沒有找到需要替換的，檢查是否需要添加
        # 尋找 .main { 並添加 max-width
        if '.main {' in content and f'max-width: {target_width}px' not in content:
            # 在 .main { 後面添加 max-width
            content = re.sub(
                r'(\.main\s*\{)',
                rf'\1 max-width: {target_width}px; margin: 0 auto;',
                content,
                count=1
            )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ 已更新: {filepath} -> {target_width}px")
        return True
    else:
        print(f"  ⏭️  無需更新: {filepath}")
        return False

def add_responsive_style():
    """在 common.css 中添加響應式樣式（如果尚未存在）"""
    filepath = 'static/css/common.css'
    if not os.path.exists(filepath):
        print(f"  ⚠️  找不到 {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已有響應式設定
    if '@media (min-width: 768px)' in content and '.main' in content:
        print("  ⏭️  common.css 已有響應式設定")
        return False
    
    # 添加響應式樣式
    responsive_css = '''
/* ==================== 響應式寬度統一 ==================== */
/* Patch 014: 統一電腦版頁面寬度 */

.main {
    width: 100%;
    max-width: 100%;
    margin: 0 auto;
    padding: 16px;
    padding-top: 72px;
    padding-bottom: 100px;
}

/* 平板 */
@media (min-width: 768px) {
    .main {
        max-width: 720px;
        padding: 24px;
        padding-top: 80px;
        padding-bottom: 40px;
    }
}

/* 桌面 */
@media (min-width: 1024px) {
    .main {
        max-width: 800px;
    }
}

/* 管理頁面更寬 */
.main.admin-main {
    max-width: 100%;
}

@media (min-width: 768px) {
    .main.admin-main {
        max-width: 960px;
    }
}

@media (min-width: 1200px) {
    .main.admin-main {
        max-width: 1100px;
    }
}
'''
    
    content += responsive_css
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  ✅ 已更新 common.css 響應式設定")
    return True

def main():
    print("=" * 55)
    print("Patch 014: 統一電腦版頁面寬度")
    print("=" * 55)
    print()
    
    if not os.path.exists('static'):
        print("❌ 請在專案根目錄執行")
        return
    
    updated = 0
    
    # 更新 common.css
    print("📁 更新 common.css...")
    if add_responsive_style():
        updated += 1
    
    print()
    print("📁 更新各頁面...")
    
    for filepath, width in PAGES_CONFIG.items():
        if update_page_width(filepath, width):
            updated += 1
    
    print()
    print("=" * 55)
    print(f"完成！已更新 {updated} 個檔案")
    print("=" * 55)
    
    if updated > 0:
        print()
        print("📝 請執行:")
        print("git add static/")
        print('git commit -m "style: 統一電腦版頁面寬度 (800px/1000px)"')
        print("git push")

if __name__ == '__main__':
    main()
