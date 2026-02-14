#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA: 快速操作卡片配色 v3
- 水平漸層 (to right)
- 左側稍深，右側粉彩亮色
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.join(BASE, "static", "dashboard.html")

if not os.path.exists(DASH):
    print("dashboard.html not found"); exit(1)

with open(DASH, "r", encoding="utf-8") as f:
    c = f.read()

replacements = [
    # === 我的集資 (primary): 深霧藍→淺天藍 ===
    ('linear-gradient(135deg, var(--sela-orange), var(--sela-orange-dark))',
     'linear-gradient(to right, #4A6D8C, #A8D8EA)'),
    ('linear-gradient(135deg, #0891B2, #06B6D4)',
     'linear-gradient(to right, #4A6D8C, #A8D8EA)'),
    ('linear-gradient(135deg, #475569, #64B5F6)',
     'linear-gradient(to right, #4A6D8C, #A8D8EA)'),
    ('linear-gradient(135deg, #5B7FA6, #A8D8EA)',
     'linear-gradient(to right, #4A6D8C, #A8D8EA)'),
    ('rgba(242, 101, 34, 0.3)', 'rgba(74, 109, 140, 0.2)'),
    ('rgba(242, 101, 34, 0.4)', 'rgba(74, 109, 140, 0.3)'),
    ('rgba(8, 145, 178, 0.3)', 'rgba(74, 109, 140, 0.2)'),
    ('rgba(8, 145, 178, 0.4)', 'rgba(74, 109, 140, 0.3)'),
    ('rgba(71, 85, 105, 0.25)', 'rgba(74, 109, 140, 0.2)'),
    ('rgba(71, 85, 105, 0.35)', 'rgba(74, 109, 140, 0.3)'),
    ('rgba(91, 127, 166, 0.2)', 'rgba(74, 109, 140, 0.2)'),
    ('rgba(91, 127, 166, 0.3)', 'rgba(74, 109, 140, 0.3)'),

    # === 我的錢包 (wallet): 深翡翠→薄荷 ===
    ('linear-gradient(135deg, #16A34A, #15803D)',
     'linear-gradient(to right, #3D8B6E, #A8E6CF)'),
    ('linear-gradient(135deg, #2D6A4F, #74C69D)',
     'linear-gradient(to right, #3D8B6E, #A8E6CF)'),
    ('linear-gradient(135deg, #4A9B7F, #A8E6CF)',
     'linear-gradient(to right, #3D8B6E, #A8E6CF)'),
    ('rgba(22, 163, 74, 0.3)', 'rgba(61, 139, 110, 0.2)'),
    ('rgba(22, 163, 74, 0.4)', 'rgba(61, 139, 110, 0.3)'),
    ('rgba(45, 106, 79, 0.25)', 'rgba(61, 139, 110, 0.2)'),
    ('rgba(45, 106, 79, 0.35)', 'rgba(61, 139, 110, 0.3)'),
    ('rgba(74, 155, 127, 0.2)', 'rgba(61, 139, 110, 0.2)'),
    ('rgba(74, 155, 127, 0.3)', 'rgba(61, 139, 110, 0.3)'),

    # === 統計報表 (stats-btn): 深玫瑰→粉紅 ===
    ('linear-gradient(135deg, #2563EB, #1D4ED8)',
     'linear-gradient(to right, #A25A6E, #F8B4C8)'),
    ('linear-gradient(135deg, #1E3A5F, #5B9BD5)',
     'linear-gradient(to right, #A25A6E, #F8B4C8)'),
    ('linear-gradient(135deg, #C06C84, #F8B4C8)',
     'linear-gradient(to right, #A25A6E, #F8B4C8)'),
    ('rgba(37, 99, 235, 0.3)', 'rgba(162, 90, 110, 0.2)'),
    ('rgba(37, 99, 235, 0.4)', 'rgba(162, 90, 110, 0.3)'),
    ('rgba(30, 58, 95, 0.25)', 'rgba(162, 90, 110, 0.2)'),
    ('rgba(30, 58, 95, 0.35)', 'rgba(162, 90, 110, 0.3)'),
    ('rgba(192, 108, 132, 0.2)', 'rgba(162, 90, 110, 0.2)'),
    ('rgba(192, 108, 132, 0.3)', 'rgba(162, 90, 110, 0.3)'),

    # === 彩券專區 (lottery): 深駝→粉黃 ===
    ('linear-gradient(135deg, #DC2626, #EF4444)',
     'linear-gradient(to right, #A67C52, #FFEAA7)'),
    ('linear-gradient(135deg, #E11D48, #FB7185)',
     'linear-gradient(to right, #A67C52, #FFEAA7)'),
    ('linear-gradient(135deg, #7F1D1D, #E8998D)',
     'linear-gradient(to right, #A67C52, #FFEAA7)'),
    ('linear-gradient(135deg, #C4956A, #FFEAA7)',
     'linear-gradient(to right, #A67C52, #FFEAA7)'),
    ('rgba(220, 38, 38, 0.3)', 'rgba(166, 124, 82, 0.2)'),
    ('rgba(225, 29, 72, 0.3)', 'rgba(166, 124, 82, 0.2)'),
    ('rgba(127, 29, 29, 0.25)', 'rgba(166, 124, 82, 0.2)'),
    ('rgba(196, 149, 106, 0.2)', 'rgba(166, 124, 82, 0.2)'),

    # === 號碼統計 (number-stats): 深紫藤→淡紫 ===
    ('linear-gradient(135deg, #7C3AED, #8B5CF6)',
     'linear-gradient(to right, #6A5A96, #C3AED6)'),
    ('linear-gradient(135deg, #4C1D95, #A78BFA)',
     'linear-gradient(to right, #6A5A96, #C3AED6)'),
    ('linear-gradient(135deg, #7E6BAD, #C3AED6)',
     'linear-gradient(to right, #6A5A96, #C3AED6)'),
    ('rgba(124, 58, 237, 0.3)', 'rgba(106, 90, 150, 0.2)'),
    ('rgba(124, 58, 237, 0.4)', 'rgba(106, 90, 150, 0.3)'),
    ('rgba(76, 29, 149, 0.25)', 'rgba(106, 90, 150, 0.2)'),
    ('rgba(76, 29, 149, 0.35)', 'rgba(106, 90, 150, 0.3)'),
    ('rgba(126, 107, 173, 0.2)', 'rgba(106, 90, 150, 0.2)'),
    ('rgba(126, 107, 173, 0.3)', 'rgba(106, 90, 150, 0.3)'),

    # === 設定 (settings): 深青石→淺青 ===
    ('linear-gradient(135deg, #607D8B, #455A64)',
     'linear-gradient(to right, #567D8A, #B8D8D8)'),
    ('linear-gradient(135deg, #37474F, #90A4AE)',
     'linear-gradient(to right, #567D8A, #B8D8D8)'),
    ('linear-gradient(135deg, #6B8F9E, #B8D8D8)',
     'linear-gradient(to right, #567D8A, #B8D8D8)'),
    ('rgba(96, 125, 139, 0.3)', 'rgba(86, 125, 138, 0.2)'),
    ('rgba(96, 125, 139, 0.4)', 'rgba(86, 125, 138, 0.3)'),
    ('rgba(55, 71, 79, 0.25)', 'rgba(86, 125, 138, 0.2)'),
    ('rgba(55, 71, 79, 0.35)', 'rgba(86, 125, 138, 0.3)'),
    ('rgba(107, 143, 158, 0.2)', 'rgba(86, 125, 138, 0.2)'),
    ('rgba(107, 143, 158, 0.3)', 'rgba(86, 125, 138, 0.3)'),

    # === 管理後台 (admin): 深靛→薰衣草 ===
    ('linear-gradient(135deg, #6366F1, #4F46E5)',
     'linear-gradient(to right, #4A55A2, #B39DDB)'),
    ('linear-gradient(135deg, #312E81, #818CF8)',
     'linear-gradient(to right, #4A55A2, #B39DDB)'),
    ('linear-gradient(135deg, #5C6BC0, #B39DDB)',
     'linear-gradient(to right, #4A55A2, #B39DDB)'),
    ('rgba(99, 102, 241, 0.3)', 'rgba(74, 85, 162, 0.2)'),
    ('rgba(99, 102, 241, 0.4)', 'rgba(74, 85, 162, 0.3)'),
    ('rgba(49, 46, 129, 0.25)', 'rgba(74, 85, 162, 0.2)'),
    ('rgba(49, 46, 129, 0.35)', 'rgba(74, 85, 162, 0.3)'),
    ('rgba(92, 107, 192, 0.2)', 'rgba(74, 85, 162, 0.2)'),
    ('rgba(92, 107, 192, 0.3)', 'rgba(74, 85, 162, 0.3)'),
]

count = 0
for old, new in replacements:
    if old in c:
        c = c.replace(old, new)
        count += 1

if count > 0:
    with open(DASH, "w", encoding="utf-8") as f:
        f.write(c)
    print(f"OK! {count} color updates")
else:
    print("No matching colors found")
