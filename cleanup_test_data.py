#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA - 清理測試資料
清除已刪除（ENDED）且未開過期（total_periods=0）的集資相關資料

使用方式：
  python cleanup_test_data.py          # 乾跑（只顯示不刪）
  python cleanup_test_data.py --apply  # 實際刪除
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
        # 找出已刪除且未開期的集資
        dead_series = db.query(GroupSeries).filter(
            GroupSeries.status == SeriesStatus.ENDED,
            GroupSeries.total_periods == 0
        ).all()
        
        if not dead_series:
            print("✅ 沒有需要清理的測試資料")
            return
        
        print(f"找到 {len(dead_series)} 個已刪除且未開期的集資:")
        for s in dead_series:
            print(f"  - ID={s.id} name=\"{s.name}\" created={s.created_at}")
        
        series_ids = [s.id for s in dead_series]
        
        # 計算影響
        ledger_count = db.query(UserLedger).filter(
            UserLedger.series_id.in_(series_ids)
        ).count()
        
        member_count = db.query(GroupMember).filter(
            GroupMember.series_id.in_(series_ids)
        ).count()
        
        print(f"\n將清除:")
        print(f"  - {ledger_count} 筆帳本記錄")
        print(f"  - {member_count} 筆成員記錄")
        print(f"  - {len(dead_series)} 筆集資記錄")
        
        if dry_run:
            print("\n⚠️  乾跑模式，未實際刪除")
            print("要實際執行請加 --apply:")
            print("  python cleanup_test_data.py --apply")
        else:
            # 實際刪除（順序重要：ledger -> member -> series）
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
            print("\n✅ 清理完成！")
    
    except Exception as e:
        db.rollback()
        print(f"\n❌ 錯誤: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    cleanup(dry_run=dry_run)
