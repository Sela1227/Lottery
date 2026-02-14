#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA 修復：刪團清帳本 + 查詢過濾 + 清舊測試資料
日期：2026-02-14

[A] series.py - delete_series: 未開期的集資刪除時清帳本
[B] wallet.py - get_transactions / get_transaction_summary: 排除已刪(未開期)集資
[B] statistics.py - get_overall_stats: 排除已刪(未開期)集資
[C] cleanup migration script (separate file)
"""
import os, sys, re

BASE = os.path.dirname(os.path.abspath(__file__))
total = 0

def save(filepath, content, original, label, changes):
    global total
    if content != original:
        with open(filepath + ".bak5", "w", encoding="utf-8") as f:
            f.write(original)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        total += changes
        print(f"  [{label}] {changes} fixes")
    else:
        print(f"  [{label}] already patched or not matched")


# =====================================================================
# [A] series.py - delete_series 清帳本
# =====================================================================
print("\n=== [A] series.py - delete_series ===")
SERIES_PY = os.path.join(BASE, "app", "api", "v1", "series.py")
if os.path.exists(SERIES_PY):
    with open(SERIES_PY, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c
    ch = 0

    # 確保有 import UserLedger
    if "from app.models.ledger import" not in c and "UserLedger" not in c:
        # Add import after existing imports
        import_marker = "from app.core.security import get_current_user_id"
        if import_marker in c:
            c = c.replace(
                import_marker,
                import_marker + "\nfrom app.models.ledger import UserLedger"
            )
            ch += 1
            print("  Added UserLedger import")

    # 在軟刪除前加入帳本清理（僅限 total_periods=0）
    old_soft_delete = """    # \u8edf\u522a\u9664\uff1a\u6a19\u8a18\u96c6\u8cc7\u70ba\u5df2\u7d50\u675f\uff0c\u6210\u54e1\u70ba\u5df2\u9000\u51fa
    series.status = SeriesStatus.ENDED
    member.status = MemberStatus.EXITED
    
    db.commit()"""

    new_soft_delete = """    # \u672a\u958b\u904e\u671f\u7684\u96c6\u8cc7\uff0c\u6e05\u9664\u5e33\u672c\u8a18\u9304\uff08\u6e2c\u8a66\u8cc7\u6599\uff09
    if series.total_periods == 0:
        db.query(UserLedger).filter(
            UserLedger.series_id == series_id
        ).delete(synchronize_session=False)
    
    # \u8edf\u522a\u9664\uff1a\u6a19\u8a18\u96c6\u8cc7\u70ba\u5df2\u7d50\u675f\uff0c\u6210\u54e1\u70ba\u5df2\u9000\u51fa
    series.status = SeriesStatus.ENDED
    member.status = MemberStatus.EXITED
    
    db.commit()"""

    if old_soft_delete in c:
        c = c.replace(old_soft_delete, new_soft_delete)
        ch += 1
        print("  delete_series: \u52a0\u5165\u5e33\u672c\u6e05\u7406")
    else:
        # Try regex match for mojibake
        pattern = re.compile(
            r'(    # [^\n]*\n    series\.status = SeriesStatus\.ENDED\n    member\.status = MemberStatus\.EXITED\n    \n    db\.commit\(\))'
        )
        match = pattern.search(c)
        if match and "total_periods == 0" not in c:
            replacement = """    # \u672a\u958b\u904e\u671f\u7684\u96c6\u8cc7\uff0c\u6e05\u9664\u5e33\u672c\u8a18\u9304\uff08\u6e2c\u8a66\u8cc7\u6599\uff09
    if series.total_periods == 0:
        db.query(UserLedger).filter(
            UserLedger.series_id == series_id
        ).delete(synchronize_session=False)
    
""" + match.group(1)
            c = c[:match.start()] + replacement + c[match.end():]
            ch += 1
            print("  delete_series: \u52a0\u5165\u5e33\u672c\u6e05\u7406 (regex)")

    save(SERIES_PY, c, orig, "A", ch)
else:
    print("  series.py not found")


# =====================================================================
# [B1] wallet.py - get_transactions 排除已刪未開期集資
# =====================================================================
print("\n=== [B1] wallet.py - transactions ===")
WALLET_PY = os.path.join(BASE, "app", "api", "v1", "wallet.py")
if os.path.exists(WALLET_PY):
    with open(WALLET_PY, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c
    ch = 0

    # 確保有 import GroupSeries, SeriesStatus
    if "SeriesStatus" not in c:
        if "from app.models.series import GroupSeries" in c:
            c = c.replace(
                "from app.models.series import GroupSeries",
                "from app.models.series import GroupSeries, SeriesStatus"
            )
            ch += 1
        elif "from app.models.series import" in c:
            # Already importing something from series
            pass
        else:
            import_marker = "from app.models.ledger import"
            if import_marker in c:
                line_end = c.index("\n", c.index(import_marker))
                c = c[:line_end+1] + "from app.models.series import GroupSeries, SeriesStatus\n" + c[line_end+1:]
                ch += 1

    # get_transactions: 排除已刪除(ENDED)且未開期(total_periods=0)的集資帳本
    # 在 query 建立後加入過濾
    old_query = "query = db.query(UserLedger).filter(UserLedger.user_id == user_id)"
    new_query = """# 排除已刪除且未開期的集資帳本（測試資料）
    deleted_series_ids = db.query(GroupSeries.id).filter(
        GroupSeries.status == SeriesStatus.ENDED,
        GroupSeries.total_periods == 0
    ).all()
    deleted_ids = [s[0] for s in deleted_series_ids]
    
    query = db.query(UserLedger).filter(UserLedger.user_id == user_id)
    if deleted_ids:
        query = query.filter(~UserLedger.series_id.in_(deleted_ids))"""
    
    if old_query in c and "deleted_series_ids" not in c:
        c = c.replace(old_query, new_query)
        ch += 1
        print("  get_transactions: \u52a0\u5165\u904e\u6ffe")

    # get_transaction_summary: 排除已刪未開期集資
    summary_marker = 'async def get_transaction_summary('
    if summary_marker in c and "deleted_zero_ids" not in c:
        # 在 total_invested (POOL_JOIN/POOL_TOPUP) 和 total_prize (POOL_PRIZE) 加過濾
        # 這兩個是 pool 帳本，才需要排除；DEPOSIT/WITHDRAW 是 wallet 帳本不影響
        
        # 加 helper 在函數開頭
        old_total_deposit = "    total_deposit = db.query("
        new_preamble = """    # 排除已刪除且未開期的集資
    _dead = [s[0] for s in db.query(GroupSeries.id).filter(
        GroupSeries.status == SeriesStatus.ENDED, GroupSeries.total_periods == 0
    ).all()]
    
    total_deposit = db.query("""
        # Find the position after the docstring
        docstring_end = c.find('"""', c.find(summary_marker) + 10)
        docstring_end = c.find('\n', docstring_end) + 1
        # Find first total_deposit after summary_marker
        td_pos = c.find(old_total_deposit, c.find(summary_marker))
        if td_pos > 0:
            c = c[:td_pos] + new_preamble + c[td_pos + len(old_total_deposit):]
            ch += 1
            print("  get_transaction_summary: 加入 helper")
        
            # 在 POOL_PRIZE query 加過濾
            old_prize_filter = """    total_prize = db.query(func.coalesce(func.sum(UserLedger.amount), 0)).filter(
        UserLedger.user_id == user_id,
        UserLedger.transaction_type == TransactionType.POOL_PRIZE
    ).scalar()"""
            new_prize_filter = """    _prize_q = db.query(func.coalesce(func.sum(UserLedger.amount), 0)).filter(
        UserLedger.user_id == user_id,
        UserLedger.transaction_type == TransactionType.POOL_PRIZE
    )
    if _dead:
        _prize_q = _prize_q.filter(~UserLedger.series_id.in_(_dead))
    total_prize = _prize_q.scalar()"""
            if old_prize_filter in c:
                c = c.replace(old_prize_filter, new_prize_filter)
                ch += 1
                print("  get_transaction_summary: total_prize 過濾")
            
            # 在 POOL_JOIN/POOL_TOPUP query 加過濾
            old_invested_filter = """    total_invested = db.query(func.coalesce(func.sum(UserLedger.amount), 0)).filter(
        UserLedger.user_id == user_id,
        UserLedger.transaction_type.in_([TransactionType.POOL_JOIN, TransactionType.POOL_TOPUP])
    ).scalar()"""
            new_invested_filter = """    _inv_q = db.query(func.coalesce(func.sum(UserLedger.amount), 0)).filter(
        UserLedger.user_id == user_id,
        UserLedger.transaction_type.in_([TransactionType.POOL_JOIN, TransactionType.POOL_TOPUP])
    )
    if _dead:
        _inv_q = _inv_q.filter(~UserLedger.series_id.in_(_dead))
    total_invested = _inv_q.scalar()"""
            if old_invested_filter in c:
                c = c.replace(old_invested_filter, new_invested_filter)
                ch += 1
                print("  get_transaction_summary: total_invested 過濾")

    save(WALLET_PY, c, orig, "B1", ch)
else:
    print("  wallet.py not found")


# =====================================================================
# [B2] statistics.py - overall stats 排除已刪未開期
# =====================================================================
print("\n=== [B2] statistics.py ===")
STATS_PY = os.path.join(BASE, "app", "api", "v1", "statistics.py")
if os.path.exists(STATS_PY):
    with open(STATS_PY, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c
    ch = 0

    # 確保有 import SeriesStatus
    if "SeriesStatus" not in c:
        if "from app.models.series import GroupSeries" in c:
            c = c.replace(
                "from app.models.series import GroupSeries",
                "from app.models.series import GroupSeries, SeriesStatus"
            )
            ch += 1

    # get_overall_stats: 排除已刪集資的 member 記錄
    old_members_query = """    members = db.query(GroupMember).filter(
        GroupMember.user_id == user_id
    ).all()"""
    new_members_query = """    # \u6392\u9664\u5df2\u522a\u9664\u4e14\u672a\u958b\u671f\u7684\u96c6\u8cc7
    deleted_zero_ids = [s[0] for s in db.query(GroupSeries.id).filter(
        GroupSeries.status == SeriesStatus.ENDED, GroupSeries.total_periods == 0
    ).all()]
    members_query = db.query(GroupMember).filter(GroupMember.user_id == user_id)
    if deleted_zero_ids:
        members_query = members_query.filter(~GroupMember.series_id.in_(deleted_zero_ids))
    members = members_query.all()"""
    
    if old_members_query in c and "deleted_zero_ids" not in c:
        c = c.replace(old_members_query, new_members_query)
        ch += 1
        print("  get_overall_stats: \u6392\u9664\u5df2\u522a\u96c6\u8cc7")
    else:
        # regex match for mojibake
        pattern = re.compile(
            r'(    members = db\.query\(GroupMember\)\.filter\(\s*GroupMember\.user_id == user_id\s*\)\.all\(\))'
        )
        match = pattern.search(c)
        if match and "deleted_zero_ids" not in c:
            c = c[:match.start()] + new_members_query + c[match.end():]
            ch += 1
            print("  get_overall_stats: \u6392\u9664\u5df2\u522a\u96c6\u8cc7 (regex)")

    save(STATS_PY, c, orig, "B2", ch)
else:
    print("  statistics.py not found")


# =====================================================================
# [C] 清舊測試資料腳本
# =====================================================================
print("\n=== [C] Cleanup script ===")
CLEANUP_SCRIPT = os.path.join(BASE, "cleanup_test_data.py")

cleanup_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA - \u6e05\u7406\u6e2c\u8a66\u8cc7\u6599
\u6e05\u9664\u5df2\u522a\u9664\uff08ENDED\uff09\u4e14\u672a\u958b\u904e\u671f\uff08total_periods=0\uff09\u7684\u96c6\u8cc7\u76f8\u95dc\u8cc7\u6599

\u4f7f\u7528\u65b9\u5f0f\uff1a
  python cleanup_test_data.py          # \u4e7e\u8dd1\uff08\u53ea\u986f\u793a\u4e0d\u522a\uff09
  python cleanup_test_data.py --apply  # \u5be6\u969b\u522a\u9664
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.series import GroupSeries, SeriesStatus
from app.models.member import GroupMember
from app.models.ledger import UserLedger

def cleanup(dry_run=True):
    db = SessionLocal()
    try:
        # \u627e\u51fa\u5df2\u522a\u9664\u4e14\u672a\u958b\u671f\u7684\u96c6\u8cc7
        dead_series = db.query(GroupSeries).filter(
            GroupSeries.status == SeriesStatus.ENDED,
            GroupSeries.total_periods == 0
        ).all()
        
        if not dead_series:
            print("\u2705 \u6c92\u6709\u9700\u8981\u6e05\u7406\u7684\u6e2c\u8a66\u8cc7\u6599")
            return
        
        print(f"\u627e\u5230 {len(dead_series)} \u500b\u5df2\u522a\u9664\u4e14\u672a\u958b\u671f\u7684\u96c6\u8cc7:")
        for s in dead_series:
            print(f"  - ID={s.id} name=\\"{s.name}\\" created={s.created_at}")
        
        series_ids = [s.id for s in dead_series]
        
        # \u8a08\u7b97\u5f71\u97ff
        ledger_count = db.query(UserLedger).filter(
            UserLedger.series_id.in_(series_ids)
        ).count()
        
        member_count = db.query(GroupMember).filter(
            GroupMember.series_id.in_(series_ids)
        ).count()
        
        print(f"\\n\u5c07\u6e05\u9664:")
        print(f"  - {ledger_count} \u7b46\u5e33\u672c\u8a18\u9304")
        print(f"  - {member_count} \u7b46\u6210\u54e1\u8a18\u9304")
        print(f"  - {len(dead_series)} \u7b46\u96c6\u8cc7\u8a18\u9304")
        
        if dry_run:
            print("\\n\u26a0\ufe0f  \u4e7e\u8dd1\u6a21\u5f0f\uff0c\u672a\u5be6\u969b\u522a\u9664")
            print("\u8981\u5be6\u969b\u57f7\u884c\u8acb\u52a0 --apply:")
            print("  python cleanup_test_data.py --apply")
        else:
            # \u5be6\u969b\u522a\u9664\uff08\u9806\u5e8f\u91cd\u8981\uff1aledger -> member -> series\uff09
            db.query(UserLedger).filter(
                UserLedger.series_id.in_(series_ids)
            ).delete(synchronize_session=False)
            
            db.query(GroupMember).filter(
                GroupMember.series_id.in_(series_ids)
            ).delete(synchronize_session=False)
            
            db.query(GroupSeries).filter(
                GroupSeries.id.in_(series_ids)
            ).delete(synchronize_session=False)
            
            db.commit()
            print("\\n\u2705 \u6e05\u7406\u5b8c\u6210\uff01")
    
    except Exception as e:
        db.rollback()
        print(f"\\n\u274c \u932f\u8aa4: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    cleanup(dry_run=dry_run)
'''

with open(CLEANUP_SCRIPT, "w", encoding="utf-8") as f:
    f.write(cleanup_code)
print("  Created cleanup_test_data.py")
print("    Dry run: python cleanup_test_data.py")
print("    Apply:   python cleanup_test_data.py --apply")


# =====================================================================
# Summary
# =====================================================================
print(f"\n{'='*50}")
print(f"Total backend fixes: {total}")
print(f"{'='*50}")
if total > 0:
    print("\nGit:")
    print("   git add app/api/v1/series.py app/api/v1/wallet.py app/api/v1/statistics.py cleanup_test_data.py")
    print('   git commit -m "fix: \u522a\u5718\u6e05\u5e33\u672c+\u67e5\u8a62\u904e\u6ffe\u5df2\u522a\u6e2c\u8a66\u96c6\u8cc7"')
    print("   git push")
    print("\n\u6e05\u7406\u820a\u8cc7\u6599\uff08\u90e8\u7f72\u5f8c\uff09:")
    print("   # \u5728 Railway console \u6216\u672c\u5730\u57f7\u884c")
    print("   python cleanup_test_data.py          # \u5148\u4e7e\u8dd1\u78ba\u8a8d")
    print("   python cleanup_test_data.py --apply  # \u5be6\u969b\u6e05\u9664")
