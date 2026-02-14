#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA: 快速操作卡片配色 v5
- 右端再收深，跨度更小更和諧
"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.join(BASE, "static", "dashboard.html")

if not os.path.exists(DASH):
    print("dashboard.html not found"); exit(1)

with open(DASH, "r", encoding="utf-8") as f:
    c = f.read()

old_gradients = {
    'primary': [
        'linear-gradient(135deg, var(--sela-orange), var(--sela-orange-dark))',
        'linear-gradient(135deg, #0891B2, #06B6D4)',
        'linear-gradient(135deg, #475569, #64B5F6)',
        'linear-gradient(135deg, #5B7FA6, #A8D8EA)',
        'linear-gradient(to right, #4A6D8C, #A8D8EA)',
        'linear-gradient(to right, #5A9BB5, #8EC8DB)',
    ],
    'wallet': [
        'linear-gradient(135deg, #16A34A, #15803D)',
        'linear-gradient(135deg, #2D6A4F, #74C69D)',
        'linear-gradient(135deg, #4A9B7F, #A8E6CF)',
        'linear-gradient(to right, #3D8B6E, #A8E6CF)',
        'linear-gradient(to right, #5AAE8C, #8BD4B4)',
    ],
    'stats-btn': [
        'linear-gradient(135deg, #2563EB, #1D4ED8)',
        'linear-gradient(135deg, #1E3A5F, #5B9BD5)',
        'linear-gradient(135deg, #C06C84, #F8B4C8)',
        'linear-gradient(to right, #A25A6E, #F8B4C8)',
        'linear-gradient(to right, #D4809A, #EDA8BC)',
    ],
    'lottery': [
        'linear-gradient(135deg, #DC2626, #EF4444)',
        'linear-gradient(135deg, #E11D48, #FB7185)',
        'linear-gradient(135deg, #7F1D1D, #E8998D)',
        'linear-gradient(135deg, #C4956A, #FFEAA7)',
        'linear-gradient(to right, #A67C52, #FFEAA7)',
        'linear-gradient(to right, #D4A96A, #E8CC98)',
    ],
    'number-stats': [
        'linear-gradient(135deg, #7C3AED, #8B5CF6)',
        'linear-gradient(135deg, #4C1D95, #A78BFA)',
        'linear-gradient(135deg, #7E6BAD, #C3AED6)',
        'linear-gradient(to right, #6A5A96, #C3AED6)',
        'linear-gradient(to right, #9882C2, #B8A6D6)',
    ],
    'settings': [
        'linear-gradient(135deg, #607D8B, #455A64)',
        'linear-gradient(135deg, #37474F, #90A4AE)',
        'linear-gradient(135deg, #6B8F9E, #B8D8D8)',
        'linear-gradient(to right, #567D8A, #B8D8D8)',
        'linear-gradient(to right, #7BA3AD, #A2C4CC)',
    ],
    'admin': [
        'linear-gradient(135deg, #6366F1, #4F46E5)',
        'linear-gradient(135deg, #312E81, #818CF8)',
        'linear-gradient(135deg, #5C6BC0, #B39DDB)',
        'linear-gradient(to right, #4A55A2, #B39DDB)',
        'linear-gradient(to right, #7B82C6, #A2A8DB)',
    ],
}

# v5: 右端收深
new_colors = {
    'primary':     ('linear-gradient(to right, #5A9BB5, #7BBACE)', (90, 155, 181)),
    'wallet':      ('linear-gradient(to right, #5AAE8C, #7DC4A4)', (90, 174, 140)),
    'stats-btn':   ('linear-gradient(to right, #D4809A, #E298AE)', (212, 128, 154)),
    'lottery':     ('linear-gradient(to right, #D4A96A, #DEBB85)', (212, 169, 106)),
    'number-stats':('linear-gradient(to right, #9882C2, #AD98D0)', (152, 130, 194)),
    'settings':    ('linear-gradient(to right, #7BA3AD, #94B8C0)', (123, 163, 173)),
    'admin':       ('linear-gradient(to right, #7B82C6, #9498D2)', (123, 130, 198)),
}

count = 0
for cls, olds in old_gradients.items():
    new_grad, _ = new_colors[cls]
    for old in olds:
        if old in c:
            c = c.replace(old, new_grad)
            count += 1

for cls, (_, (r, g, b)) in new_colors.items():
    pat = re.compile(rf'(\.action-btn\.{re.escape(cls)}\s*\{{[^}}]*box-shadow:\s*0 8px 24px\s*)rgba\([^)]+\)', re.DOTALL)
    c = pat.sub(rf'\g<1>rgba({r}, {g}, {b}, 0.2)', c)
    pat_h = re.compile(rf'(\.action-btn\.{re.escape(cls)}:hover\s*\{{[^}}]*box-shadow:\s*0 12px 32px\s*)rgba\([^)]+\)', re.DOTALL)
    c = pat_h.sub(rf'\g<1>rgba({r}, {g}, {b}, 0.3)', c)

with open(DASH, "w", encoding="utf-8") as f:
    f.write(c)
print(f"OK! {count} gradient updates")
