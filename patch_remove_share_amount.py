#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA 修復：移除每份金額 + 投入金額需為彩種單價倍數
日期：2026-02-14

修改：
  [A] series.html - 移除「每份金額」欄位，初始份額加倍數驗證
  [B] series-detail.html - 加碼加倍數驗證
"""
import os, sys, re

BASE = os.path.dirname(os.path.abspath(__file__))
total = 0

# =====================================================================
# [A] series.html
# =====================================================================
print("\n=== [A] series.html ===")
SERIES = os.path.join(BASE, "static", "series.html")

if not os.path.exists(SERIES):
    print("  找不到 series.html")
else:
    with open(SERIES, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c
    ch = 0

    # A1: 移除「每份金額」整個 form-group（支援正常中文和 mojibake）
    share_patterns = [
        # 正常中文
        """<div class="form-group">
                    <label class="form-label">\u6bcf\u4efd\u91d1\u984d</label>
                    <input type="number" class="form-input" id="create-share" placeholder="100">
                    <div class="form-hint">\u9700\u70ba\u5f69\u7a2e\u50f9\u683c\u7684\u500d\u6578</div>
                </div>""",
    ]
    # Also try regex-based removal by finding the form-group containing create-share

    share_match = re.search(
        r'<div class="form-group">\s*<label[^>]*>[^<]*</label>\s*<input[^>]*id="create-share"[^>]*>\s*(?:<div[^>]*>[^<]*</div>\s*)?</div>',
        c, re.DOTALL
    )
    if share_match:
        c = c[:share_match.start()] + c[share_match.end():]
        ch += 1
        print("  A1: \u79fb\u9664\u300c\u6bcf\u4efd\u91d1\u984d\u300d\u6b04\u4f4d")
    else:
        for pat in share_patterns:
            if pat in c:
                c = c.replace(pat, "")
                ch += 1
                print("  A1: \u79fb\u9664\u300c\u6bcf\u4efd\u91d1\u984d\u300d\u6b04\u4f4d")
                break

    # A2: 初始份額加 hint - 用 regex 找到 create-amount 的 form-group
    amount_match = re.search(
        r'(<div class="form-group">\s*<label[^>]*>)[^<]*(</label>\s*<input[^>]*id="create-amount"[^>]*>)\s*</div>',
        c, re.DOTALL
    )
    if amount_match and 'create-amount-hint' not in c:
        old_block = amount_match.group(0)
        new_block = amount_match.group(1) + '\u60a8\u7684\u521d\u59cb\u6295\u5165\u91d1\u984d' + amount_match.group(2) + '\n                    <div class="form-hint" id="create-amount-hint">\u9700\u70ba\u5f69\u7a2e\u55ae\u50f9\u7684\u500d\u6578</div>\n                </div>'
        c = c.replace(old_block, new_block)
        ch += 1
        print("  A2: \u521d\u59cb\u4efd\u984d\u52a0 hint")

    # A3: createSeries 移除 shareAmount 引用，加倍數驗證
    # Step 1: 移除 shareAmount 相關行
    if "const shareAmount = parseInt($('create-share').value);" in c:
        c = c.replace("const shareAmount = parseInt($('create-share').value);\n", "")
        ch += 1
        print("  A3a: \u79fb\u9664 shareAmount")
    
    # Step 2: 修正驗證條件（移除 shareAmount 檢查）
    if "!shareAmount || !initialAmount" in c:
        c = c.replace("!shareAmount || !initialAmount", "!initialAmount")
        ch += 1
        print("  A3b: \u4fee\u6b63\u9a57\u8b49\u689d\u4ef6")
    
    # Step 3: 移除 share_amount 欄位（如果還在送）
    if "share_amount: shareAmount,\n" in c:
        c = c.replace("share_amount: shareAmount,\n", "")
        ch += 1
        print("  A3c: \u79fb\u9664 share_amount \u6b04\u4f4d")
    
    # Step 4: 在 apiPost 前注入倍數驗證（如果還沒有）
    if "% price !== 0" not in c:
        inject_before = "try {\n                await apiPost('/series'"
        validation = """// \u9a57\u8b49\u91d1\u984d\u662f\u5f69\u7a2e\u55ae\u50f9\u7684\u500d\u6578
            const price = LOTTERY_PRICES[lotteryType] || 100;
            if (initialAmount < price) {
                showToast(`\u6295\u5165\u91d1\u984d\u81f3\u5c11\u70ba $${price}`, 'error');
                return;
            }
            if (initialAmount % price !== 0) {
                showToast(`\u6295\u5165\u91d1\u984d\u9700\u70ba $${price} \u7684\u500d\u6578`, 'error');
                return;
            }
            
            try {\n                await apiPost('/series'"""
        if inject_before in c:
            c = c.replace(inject_before, validation)
            ch += 1
            print("  A3d: \u6ce8\u5165\u500d\u6578\u9a57\u8b49")

    # A4: 選擇彩種時動態更新 hint
    old_load_types_end = "} catch (e) { console.error('loadLotteryTypes:', e); }"
    new_load_types_end = """// \u9078\u64c7\u5f69\u7a2e\u6642\u66f4\u65b0 hint
                container.querySelectorAll('input[name="lottery-type"]').forEach(radio => {
                    radio.addEventListener('change', () => {
                        const p = LOTTERY_PRICES[radio.value] || 100;
                        const hint = $('create-amount-hint');
                        if (hint) hint.textContent = `\u9700\u70ba $${p} \u7684\u500d\u6578\uff08${radio.value === 'power' ? '\u5a01\u529b\u5f69' : radio.value === 'super' ? '\u5927\u6a02\u900f' : '\u4eca\u5f69539'} \u55ae\u50f9 $${p}/\u6ce8\uff09`;
                    });
                });
                // \u89f8\u767c\u9810\u8a2d
                const checked = container.querySelector('input[name="lottery-type"]:checked');
                if (checked) checked.dispatchEvent(new Event('change'));
            } catch (e) { console.error('loadLotteryTypes:', e); }"""
    if old_load_types_end in c:
        c = c.replace(old_load_types_end, new_load_types_end)
        ch += 1
        print("  A4: \u9078\u64c7\u5f69\u7a2e\u6642\u52d5\u614b\u66f4\u65b0 hint")

    if c != orig:
        with open(SERIES + ".bak3", "w", encoding="utf-8") as f:
            f.write(orig)
        with open(SERIES, "w", encoding="utf-8") as f:
            f.write(c)
        total += ch
        print(f"  \u2192 {ch} fixes")
    else:
        print("  already patched")


# =====================================================================
# [B] series-detail.html - 加碼驗證
# =====================================================================
print("\n=== [B] series-detail.html ===")
SD = os.path.join(BASE, "static", "series-detail.html")

if not os.path.exists(SD):
    print("  找不到 series-detail.html")
else:
    with open(SD, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c
    ch = 0

    # B1: topup 加倍數驗證
    old_topup = "async function topup() {"
    new_topup = """async function topup() {
            // 取得彩種單價
            const lotteryType = (currentSeries?.allowed_lottery_types || ['power'])[0];
            const PRICES = { 'power': 100, 'super': 50, 'daily539': 50 };
            const unitPrice = PRICES[lotteryType] || 100;"""
    if old_topup in c and "unitPrice" not in c:
        c = c.replace(old_topup, new_topup)
        ch += 1
        print("  B1: topup \u52a0\u5165\u55ae\u50f9\u8b8a\u6578")

    # B2: topup 金額驗證 - 替換硬編碼的 50 為 unitPrice
    old_topup_check = "if (amount < 50) {"
    new_topup_check = "if (amount < unitPrice || amount % unitPrice !== 0) {"
    if old_topup_check in c and "% unitPrice" not in c:
        c = c.replace(old_topup_check, new_topup_check)
        # 也更新錯誤訊息

        c = re.sub(
            r"showToast\('[^']*50[^']*',\s*'error'\)",
            "showToast(`加碼金額需為 $${unitPrice} 的倍數`, 'error')",
            c, count=1
        )
        ch += 1
        print("  B2: topup \u91d1\u984d\u500d\u6578\u9a57\u8b49")

    if c != orig:
        with open(SD + ".bak3", "w", encoding="utf-8") as f:
            f.write(orig)
        with open(SD, "w", encoding="utf-8") as f:
            f.write(c)
        total += ch
        print(f"  \u2192 {ch} fixes")
    else:
        print("  already patched")


# =====================================================================
print(f"\n{'='*50}")
print(f"Total: {total} fixes")
print(f"{'='*50}")
if total > 0:
    print("\nGit:")
    print("   git add static/series.html static/series-detail.html")
    print('   git commit -m "feat: \u79fb\u9664\u6bcf\u4efd\u91d1\u984d\u6b04\u4f4d\uff0c\u6295\u5165\u91d1\u984d\u9700\u70ba\u5f69\u7a2e\u55ae\u50f9\u500d\u6578"')
    print("   git push")
