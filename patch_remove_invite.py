#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA: series-detail.html 移除邀請功能
- 移除「產生邀請碼」按鈕
- 移除「邀請碼」Tab
- 移除 invite modal
- 移除相關 JS 函數
"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
SD = os.path.join(BASE, "static", "series-detail.html")

if not os.path.exists(SD):
    print("series-detail.html not found"); exit(1)

with open(SD, "r", encoding="utf-8") as f:
    c = f.read()
orig = c
fixes = 0

def fix(label):
    global fixes; fixes += 1; print(f"  {label}")

# 1. 移除 invite modal HTML
invite_modal = re.compile(
    r'\s*<!-- Invite Modal -->.*?</div>\s*</div>\s*</div>\s*(?=\s*<!-- Topup Modal)',
    re.DOTALL
)
new_c = invite_modal.sub('\n    \n    ', c)
if new_c != c:
    c = new_c; fix("移除 invite modal HTML")

# 2. 移除「產生邀請碼」按鈕 from admin-actions
# Pattern: <button class="btn btn-secondary" onclick="showInviteModal()">🎫 產生邀請碼</button>
invite_btn = re.compile(r'<button class="btn btn-secondary" onclick="showInviteModal\(\)">[^<]*</button>')
new_c = invite_btn.sub('', c)
if new_c != c:
    c = new_c; fix("移除產生邀請碼按鈕")

# 3. 移除「邀請碼」Tab
# '<div class="tab" data-tab="invites">邀請碼</div>'
invite_tab = re.compile(r"""<div class="tab" data-tab="invites">[^<]*</div>""")
new_c = invite_tab.sub('', c)
if new_c != c:
    c = new_c; fix("移除邀請碼 Tab")

# 4. 移除 tab-invites div
# '<div id="tab-invites" class="tab-content"></div>'
invite_tab_content = re.compile(r"""<div id="tab-invites" class="tab-content"></div>""")
new_c = invite_tab_content.sub('', c)
if new_c != c:
    c = new_c; fix("移除 tab-invites div")

# 5. 移除 loadInvitations() 呼叫
# "if (isAdmin) loadInvitations();" or "loadInvitations();"
c = c.replace(' if (isAdmin) loadInvitations();', '')
c = c.replace('loadInvitations();', '')
fix("移除 loadInvitations 呼叫")

# 6. 移除 showInviteModal 函數
c = re.sub(r'\s*function showInviteModal\(\)\s*\{[^}]*\}', '', c)
fix("移除 showInviteModal")

# 7. 移除 createInvitation 函數
c = re.sub(r'\s*async function createInvitation\(\)\s*\{.*?\}\s*\}', '', c, flags=re.DOTALL)
# Be more careful - match until the next function
create_inv = re.compile(r'\s*async function createInvitation\(\) \{[^\n]*\n\s*\}', re.DOTALL)
new_c = create_inv.sub('', c)
if new_c != c:
    c = new_c; fix("移除 createInvitation")

# 8. 移除 loadInvitations 函數
load_inv = re.compile(r'\s*async function loadInvitations\(\) \{.*?\n\s*\}', re.DOTALL)
new_c = load_inv.sub('', c)
if new_c != c:
    c = new_c; fix("移除 loadInvitations 函數")

# 9. 清理 currentInvitation 變數
c = c.replace(', currentInvitation = null', '')
c = c.replace('currentInvitation = null, ', '')
c = c.replace('currentInvitation = null;', '')

if c != orig:
    with open(SD, "w", encoding="utf-8") as f:
        f.write(c)
    print(f"\n完成！{fixes} 處修改")
    print("\ngit add static/series-detail.html")
    print('git commit -m "refactor: 移除邀請碼功能"')
    print("git push")
else:
    print("No changes made")
