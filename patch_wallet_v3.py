#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA 錢包頁面綜合修復 v3
日期：2026-02-13
檔案：static/wallet.html

修復項目：
  1. $$ 雙錢號 → common.js formatMoney 已帶 $，移除重複
  2. 佔比 10000% → API 已回傳百分比，移除重複 ×100
  3. 交易記錄載入失敗 → 整個函式防禦性重寫 + 詳細 log
"""
import os
import sys

WALLET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "wallet.html")

if not os.path.exists(WALLET_FILE):
    print(f"❌ 找不到: {WALLET_FILE}")
    sys.exit(1)

with open(WALLET_FILE, "r", encoding="utf-8") as f:
    content = f.read()

original = content
changes = 0

# ===== 修復 1: setText 裡多餘的 '$' + formatMoney =====
old = "'$' + formatMoney("
new = "formatMoney("
count = content.count(old)
if count > 0:
    content = content.replace(old, new)
    changes += count
    print(f"  ✅ 移除 setText 多餘 $ ({count} 處)")

# ===== 修復 2: template literal 裡 >$${formatMoney → >${formatMoney =====
old = ">$${formatMoney("
new = ">${formatMoney("
count = content.count(old)
if count > 0:
    content = content.replace(old, new)
    changes += count
    print(f"  ✅ 移除 pool-amount 多餘 $ ({count} 處)")

# tx-amount: '}$${formatMoney(' → '}${formatMoney('
old = "}$${formatMoney("
new = "}${formatMoney("
count = content.count(old)
if count > 0:
    content = content.replace(old, new)
    changes += count
    print(f"  ✅ 移除 tx-amount 多餘 $ ({count} 處)")

# ===== 修復 3: 佔比 (p.ratio * 100).toFixed(1) → p.ratio.toFixed(1) =====
old = "(p.ratio * 100).toFixed(1)"
new = "p.ratio.toFixed(1)"
count = content.count(old)
if count > 0:
    content = content.replace(old, new)
    changes += count
    print(f"  ✅ 修復佔比計算 ({count} 處)")

# ===== 修復 4: 篩選按鈕值 =====
for old_val, new_val in [("filterTx('topup')", "filterTx('pool_topup')"),
                          ("filterTx('prize')", "filterTx('pool_prize')"),
                          ("filterTx('purchase')", "filterTx('pool_purchase')")]:
    count = content.count(old_val)
    if count > 0:
        content = content.replace(old_val, new_val)
        changes += count
        print(f"  ✅ {old_val} → {new_val} ({count} 處)")

# ===== 修復 5: ?type= → ?transaction_type= =====
for old, new in [("?type=${currentFilter}", "?transaction_type=${currentFilter}"),
                  ("?type=' + currentFilter", "?transaction_type=' + currentFilter")]:
    count = content.count(old)
    if count > 0:
        content = content.replace(old, new)
        changes += count
        print(f"  ✅ ?type= → ?transaction_type= ({count} 處)")

# ===== 修復 6: 用 brace counting 替換整個 loadTransactions =====
FUNC_MARKER = "async function loadTransactions()"
NEW_FUNC = '''async function loadTransactions() {
            try {
                const url = currentFilter === 'all'
                    ? '/wallet/transactions'
                    : '/wallet/transactions?transaction_type=' + currentFilter;
                console.log('[wallet] loadTransactions url:', url);
                const data = await apiGet(url);
                console.log('[wallet] transactions response:', JSON.stringify(data).substring(0, 200));
                const list = $('tx-list');
                if (!list) { console.error('[wallet] tx-list element not found'); return; }
                const txList = (data && data.transactions) ? data.transactions : [];
                if (txList.length === 0) {
                    list.innerHTML = '<div class="empty-state"><div class="empty-icon">\\u{1F4DC}</div><p>尚無交易記錄</p></div>';
                    return;
                }
                let html = '';
                for (const tx of txList) {
                    const amt = parseFloat(tx.amount) || 0;
                    const isPositive = amt > 0;
                    const sign = isPositive ? '+' : '';
                    const cls = isPositive ? 'positive' : 'negative';
                    const typeName = tx.transaction_type_display || tx.transaction_type || '';
                    const dateStr = formatDate(tx.created_at);
                    html += '<div class="tx-item">'
                        + '<div class="tx-info">'
                        + '<div class="tx-type">' + typeName + '</div>'
                        + '<div class="tx-date">' + dateStr + '</div>'
                        + '</div>'
                        + '<div class="tx-amount ' + cls + '">' + sign + formatMoney(Math.abs(amt)) + '</div>'
                        + '</div>';
                }
                list.innerHTML = html;
                console.log('[wallet] rendered', txList.length, 'transactions');
            } catch (e) {
                console.error('[wallet] loadTransactions error:', e);
                const list = $('tx-list');
                if (list) list.innerHTML = '<div class="empty-state">載入失敗: ' + (e.message || e) + '</div>';
            }
        }'''

idx = content.find(FUNC_MARKER)
if idx >= 0:
    brace_start = content.index("{", idx)
    depth = 0
    func_end = -1
    for i in range(brace_start, len(content)):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                func_end = i + 1
                break

    if func_end > 0:
        old_func = content[idx:func_end]
        content = content[:idx] + NEW_FUNC + content[func_end:]
        changes += 1
        print(f"  ✅ 替換整個 loadTransactions ({len(old_func)} → {len(NEW_FUNC)} chars)")
    else:
        print(f"  ⚠️  找到 loadTransactions 但無法定位結尾")
else:
    print(f"  ⚠️  找不到 loadTransactions 函式")

if content == original:
    print("\n⚠️  無變更")
    sys.exit(0)

# 備份
backup = WALLET_FILE + ".bak"
with open(backup, "w", encoding="utf-8") as f:
    f.write(original)
print(f"\n💾 備份: {backup}")

with open(WALLET_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n🎉 修復完成！共 {changes} 處變更")
print("   • $$ → $ (formatMoney 已帶 $)")
print("   • 佔比 ×100 移除")
print("   • loadTransactions 完整重寫 + console.log 除錯")
print("\n📌 部署後開 F12 Console 看 [wallet] 開頭的 log")
