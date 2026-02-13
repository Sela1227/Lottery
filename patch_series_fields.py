#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA 修復：series.html 欄位名不匹配 + 返回鍵位置
日期：2026-02-13

問題：
  1. $undefined/注 → lt.price 應為 lt.price_per_bet
  2. undefined 彩種 → s.lottery_type_name 應為 s.lottery_types[0] 映射
  3. NaN% → s.my_ratio 不存在，需計算
  4. $$0 → formatMoney 已含 $，不需額外加
  5. s.my_share → 應為 s.my_pool_share
  6. s.total_pool → 應為 s.current_pool
  7. 返回鍵電腦版太遠 → header 加 max-width
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SERIES_FILE = os.path.join(BASE, "static", "series.html")

if not os.path.exists(SERIES_FILE):
    print(f"\u26a0\ufe0f  找不到 {SERIES_FILE}")
    sys.exit(1)

with open(SERIES_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Backup
with open(SERIES_FILE + ".bak", "w", encoding="utf-8") as f:
    f.write(content)

changes = 0

# === Fix 1: lt.price → lt.price_per_bet ===
old = '${lt.price}/'
new = '${lt.price_per_bet}/'
if old in content:
    content = content.replace(old, new)
    changes += 1
    print("  \u2705 Fix 1: lt.price → lt.price_per_bet")

# === Fix 2: lottery_type_name → lottery_types mapping ===
# Add LOTTERY_NAME_MAP and fix the card rendering
old_info = "${s.lottery_type_name || s.lottery_type}"
new_info = "${LOTTERY_NAMES[s.lottery_types?.[0]] || s.lottery_types?.[0] || '?'}"
if old_info in content:
    content = content.replace(old_info, new_info)
    changes += 1
    print("  \u2705 Fix 2: lottery_type_name → lottery_types mapping")

# Add LOTTERY_NAMES map after LOTTERY_PRICES (must be before Fix 2 reference)
old_prices = "const LOTTERY_PRICES = { 'power': 100, 'super': 50, 'daily539': 50 };"
new_prices = """const LOTTERY_PRICES = { 'power': 100, 'super': 50, 'daily539': 50 };
        const LOTTERY_NAMES = { 'power': '\u5a01\u529b\u5f69', 'super': '\u5927\u6a02\u900f', 'daily539': '\u4eca\u5f69539' };"""
if old_prices in content:
    content = content.replace(old_prices, new_prices)
    changes += 1
    print("  \u2705 Fix 2b: Added LOTTERY_NAMES map")

# === Fix 3: NaN% → safe ratio calculation ===
old_ratio = "${(s.my_ratio * 100).toFixed(1)}%"
new_ratio = "${s.current_pool > 0 ? ((s.my_pool_share / s.current_pool) * 100).toFixed(1) : '0.0'}%"
if old_ratio in content:
    content = content.replace(old_ratio, new_ratio)
    changes += 1
    print("  \u2705 Fix 3: NaN% → safe ratio calculation")

# === Fix 4 + 5: $$0 and my_share → my_pool_share ===
# series-stat-value lines
old_share = "$${formatMoney(s.my_share)}"
new_share = "${formatMoney(s.my_pool_share)}"
count = content.count(old_share)
if count > 0:
    content = content.replace(old_share, new_share)
    changes += 1
    print(f"  \u2705 Fix 4+5: $$formatMoney(my_share) → formatMoney(my_pool_share) ({count}x)")

# === Fix 6: total_pool → current_pool ===
old_pool = "$${formatMoney(s.total_pool)}"
new_pool = "${formatMoney(s.current_pool)}"
if old_pool in content:
    content = content.replace(old_pool, new_pool)
    changes += 1
    print("  \u2705 Fix 6: $$formatMoney(total_pool) → formatMoney(current_pool)")

# Also fix the stats calculation
old_stats_invested = "totalInvested += s.my_share || 0;"
new_stats_invested = "totalInvested += Number(s.my_pool_share) || 0;"
if old_stats_invested in content:
    content = content.replace(old_stats_invested, new_stats_invested)
    changes += 1
    print("  \u2705 Fix: stats totalInvested uses my_pool_share")

old_stats_prize = "totalPrize += s.my_prize || 0;"
new_stats_prize = "totalPrize += Number(s.total_prize) || 0;"
if old_stats_prize in content:
    content = content.replace(old_stats_prize, new_stats_prize)
    changes += 1
    print("  \u2705 Fix: stats totalPrize uses total_prize")

# Fix the stats display (also has $$ issue)
old_stat_inv = "setText('stat-invested', '$' + formatMoney(totalInvested));"
new_stat_inv = "setText('stat-invested', formatMoney(totalInvested));"
if old_stat_inv in content:
    content = content.replace(old_stat_inv, new_stat_inv)
    changes += 1
    print("  \u2705 Fix: stat-invested remove extra $")

old_stat_prize = "setText('stat-prize', '$' + formatMoney(totalPrize));"
new_stat_prize = "setText('stat-prize', formatMoney(totalPrize));"
if old_stat_prize in content:
    content = content.replace(old_stat_prize, new_stat_prize)
    changes += 1
    print("  \u2705 Fix: stat-prize remove extra $")

# === Fix 7: Header max-width for desktop back button ===
# Make header contents centered on wide screens
old_header_style = """.header {
            background: linear-gradient(135deg, var(--sela-orange), var(--sela-orange-dark));
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow-md);
        }"""
new_header_style = """.header {
            background: linear-gradient(135deg, var(--sela-orange), var(--sela-orange-dark));
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow-md);
            max-width: 800px;
            margin: 0 auto;
        }
        body > .header {
            max-width: none;
        }
        .header-inner {
            max-width: 600px;
            margin: 0 auto;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }"""

# Instead of complex CSS, wrap header content in an inner div via JS
# Simpler approach: just limit header with padding on desktop
old_header_css = """.header {
            background: linear-gradient(135deg, var(--sela-orange), var(--sela-orange-dark));
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow-md);
        }"""

new_header_css = """.header {
            background: linear-gradient(135deg, var(--sela-orange), var(--sela-orange-dark));
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow-md);
        }
        @media (min-width: 700px) {
            .header { padding: 12px calc((100% - 600px) / 2 + 16px); }
        }"""

if old_header_css in content:
    content = content.replace(old_header_css, new_header_css)
    changes += 1
    print("  \u2705 Fix 7: Header padding on desktop (back button closer)")

# Write
with open(SERIES_FILE, "w", encoding="utf-8") as f:
    f.write(content)

if changes == 0:
    print("\n\u26a0\ufe0f  無變更")
else:
    print(f"\n完成！共 {changes} 項修復")
    print("\n部署：")
    print("   git add static/series.html")
    print('   git commit -m "fix: series頁面欄位名修正+返回鍵位置"')
    print("   git push")
