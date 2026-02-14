#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
緊急修復 v3：逐行掃描，刪除所有 admin_end/delete，最後加一份
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ADMIN_PY = os.path.join(BASE, "app", "api", "v1", "admin.py")

with open(ADMIN_PY, "r", encoding="utf-8") as f:
    lines = f.readlines()

result = []
i = 0
removed = 0

while i < len(lines):
    line = lines[i]
    s = line.strip()

    # 跳過集資管理操作 section header
    if '集資管理操作' in line and '====' in line:
        i += 1
        while i < len(lines) and lines[i].strip() == '':
            i += 1
        removed += 1
        continue

    # 跳過 @router.post("/series/{series_id}/end") + 整個函數
    if '@router.post("/series/{series_id}/end")' in s:
        i += 1
        while i < len(lines):
            ns = lines[i].strip()
            # 函數結束條件：遇到下一個 @router 或 section header 或頂層 def/class
            if ns and (ns.startswith('@router.') or ns.startswith('# ====') or 
                      (ns.startswith('async def ') and not lines[i].startswith('    ')) or
                      (ns.startswith('def ') and not lines[i].startswith('    '))):
                break
            i += 1
        removed += 1
        continue

    # 跳過 @router.delete("/series/{series_id}") + 整個函數
    if '@router.delete("/series/{series_id}")' in s:
        i += 1
        while i < len(lines):
            ns = lines[i].strip()
            if ns and (ns.startswith('@router.') or ns.startswith('# ====') or
                      (ns.startswith('async def ') and not lines[i].startswith('    ')) or
                      (ns.startswith('def ') and not lines[i].startswith('    '))):
                break
            i += 1
        removed += 1
        continue

    # 跳過獨立的 async def admin_end_series / admin_delete_series
    if ('def admin_end_series' in s or 'def admin_delete_series' in s) and not line.startswith('    '):
        i += 1
        while i < len(lines):
            ns = lines[i].strip()
            if ns and (ns.startswith('@') or ns.startswith('# ====') or
                      (ns.startswith('async def ') and not lines[i].startswith('    ')) or
                      (ns.startswith('def ') and not lines[i].startswith('    '))):
                break
            i += 1
        removed += 1
        continue

    result.append(line)
    i += 1

print(f"移除了 {removed} 個區塊")

# 組合
content = ''.join(result)

# 確保 imports
first_30 = content[:2000]
if 'UserLedger' not in first_30 and 'from app.models.ledger import' in first_30:
    content = content.replace(
        "from app.models.ledger import EventLog, EventCategory",
        "from app.models.ledger import EventLog, EventCategory, UserLedger"
    )
    print("修正 UserLedger import")

# 修正統計
if "total_series = db.query(GroupSeries).count()" in content:
    content = content.replace(
        "total_series = db.query(GroupSeries).count()",
        "total_series = db.query(GroupSeries).filter(GroupSeries.status == SeriesStatus.ACTIVE).count()"
    )
    print("修正 total_series 統計")
if "func.sum(GroupSeries.current_pool), 0)).scalar()" in content:
    content = content.replace(
        "func.sum(GroupSeries.current_pool), 0)).scalar()",
        "func.sum(GroupSeries.current_pool), 0)).filter(GroupSeries.status == SeriesStatus.ACTIVE).scalar()"
    )
    print("修正 total_pool 統計")

# 清理多餘空行
import re
content = re.sub(r'\n{4,}', '\n\n\n', content)

# 在最尾端附加唯一一份乾淨 endpoints
content = content.rstrip() + """


# ==================== 集資管理操作 ====================

@router.post("/series/{series_id}/end")
async def admin_end_series(
    series_id: int,
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    series = db.query(GroupSeries).filter(GroupSeries.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="集資不存在")
    if series.status == SeriesStatus.ENDED:
        raise HTTPException(status_code=400, detail="集資已結束")
    series.status = SeriesStatus.ENDED
    db.query(GroupMember).filter(
        GroupMember.series_id == series_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).update({"status": MemberStatus.EXITED}, synchronize_session=False)
    db.commit()
    return {"message": "已結束"}


@router.delete("/series/{series_id}")
async def admin_delete_series(
    series_id: int,
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    series = db.query(GroupSeries).filter(GroupSeries.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="集資不存在")
    if series.total_periods > 0 and series.total_prize > 0:
        raise HTTPException(status_code=400, detail="有開獎記錄不可刪除")
    try:
        db.query(UserLedger).filter(UserLedger.series_id == series_id).delete(synchronize_session=False)
    except Exception:
        pass
    groups = db.query(Group).filter(Group.series_id == series_id).all()
    for g in groups:
        try:
            from app.models.ticket import Ticket
            db.query(Ticket).filter(Ticket.group_id == g.id).delete(synchronize_session=False)
        except Exception:
            pass
    db.query(Group).filter(Group.series_id == series_id).delete(synchronize_session=False)
    db.query(GroupMember).filter(GroupMember.series_id == series_id).delete(synchronize_session=False)
    db.delete(series)
    db.commit()
    return {"message": "已刪除"}
"""

with open(ADMIN_PY, "w", encoding="utf-8") as f:
    f.write(content)

# 驗證
c1 = content.count('def admin_end_series')
c2 = content.count('def admin_delete_series')
print(f"\nadmin_end_series: {c1}x (需要 1)")
print(f"admin_delete_series: {c2}x (需要 1)")

if c1 == 1 and c2 == 1:
    print("✅ OK!")
else:
    print("❌ 仍有問題")

print("\ngit add app/api/v1/admin.py")
print('git commit -m "hotfix: admin.py 修復"')
print("git push")
