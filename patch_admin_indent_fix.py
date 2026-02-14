#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
緊急修復：admin.py 重複 endpoints + IndentationError
策略：找到所有 admin_end_series/admin_delete_series，全刪，重新加一份乾淨的
"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
ADMIN_PY = os.path.join(BASE, "app", "api", "v1", "admin.py")

if not os.path.exists(ADMIN_PY):
    print("admin.py not found"); exit(1)

with open(ADMIN_PY, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Step 1: 找到並移除所有 admin_end_series / admin_delete_series 相關行
# 也移除「集資管理操作」section header
new_lines = []
skip_until_next_section = False
skip_func = False
i = 0

while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    # 跳過「集資管理操作」section header
    if '集資管理操作' in line:
        # Skip this line and any blank lines after
        i += 1
        while i < len(lines) and lines[i].strip() == '':
            i += 1
        continue
    
    # 跳過 admin_end_series 函數
    if '@router.post("/series/{series_id}/end")' in stripped:
        # Skip until next @router or section header
        i += 1
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith('@router.') or s.startswith('# ===='):
                break
            i += 1
        continue
    
    # 跳過 admin_delete_series 函數
    if '@router.delete("/series/{series_id}")' in stripped:
        i += 1
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith('@router.') or s.startswith('# ===='):
                break
            i += 1
        continue
    
    new_lines.append(line)
    i += 1

# Step 2: 確保 imports
content = ''.join(new_lines)
if 'UserLedger' not in content.split('\n')[0:30].__repr__():
    content = content.replace(
        "from app.models.ledger import EventLog, EventCategory",
        "from app.models.ledger import EventLog, EventCategory, UserLedger"
    )

# Step 3: 修正統計 (idempotent)
content = content.replace(
    "total_series = db.query(GroupSeries).count()",
    "total_series = db.query(GroupSeries).filter(GroupSeries.status == SeriesStatus.ACTIVE).count()"
)
content = content.replace(
    "total_pool = db.query(func.coalesce(func.sum(GroupSeries.current_pool), 0)).scalar()",
    "total_pool = db.query(func.coalesce(func.sum(GroupSeries.current_pool), 0)).filter(GroupSeries.status == SeriesStatus.ACTIVE).scalar()"
)

# Step 4: 插入乾淨的 endpoints (一份)
clean_endpoints = '''
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
        raise HTTPException(status_code=400, detail="有開獎記錄的集資不可刪除")
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


'''

# 找插入點：事件日誌 section 之前
inserted = False
for marker in ['# ==================== 事件日誌', '# ==================== \xe4\xba\x8b\xe4\xbb\xb6\xe6\x97\xa5\xe8\xaa\x8c']:
    if marker in content:
        content = content.replace(marker, clean_endpoints + marker)
        inserted = True
        break

if not inserted:
    # Try finding @router.get("/logs"
    if '@router.get("/logs"' in content:
        content = content.replace('@router.get("/logs"', clean_endpoints + '@router.get("/logs"')
        inserted = True

if not inserted:
    content += clean_endpoints

# Step 5: 清理多餘空行
content = re.sub(r'\n{4,}', '\n\n\n', content)

with open(ADMIN_PY, "w", encoding="utf-8") as f:
    f.write(content)

# Verify
count_end = content.count('def admin_end_series')
count_del = content.count('def admin_delete_series')
print(f"admin_end_series: {count_end}x (should be 1)")
print(f"admin_delete_series: {count_del}x (should be 1)")

if count_end == 1 and count_del == 1:
    print("✅ 修復成功！")
else:
    print("⚠️ 仍有重複，請手動檢查")

print("\ngit add app/api/v1/admin.py")
print('git commit -m "hotfix: admin.py 語法錯誤修復"')
print("git push")
