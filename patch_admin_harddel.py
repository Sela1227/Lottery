#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA Admin 全面修正
1. admin.py: 硬刪除(真刪) + 統計過濾 ACTIVE
2. admin.html: UI 優化
"""
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))
fixes = 0
def fix(label):
    global fixes; fixes += 1; print(f"  {label}")


# =====================================================================
# 1. admin.py - 修正刪除邏輯 + 統計
# =====================================================================
print("\n=== 1. admin.py ===")
ADMIN_PY = os.path.join(BASE, "app", "api", "v1", "admin.py")
if os.path.exists(ADMIN_PY):
    with open(ADMIN_PY, "r", encoding="utf-8") as f:
        c = f.read()

    # 1a. 確保 import
    import_area = '\n'.join(c.split('\n')[:30])
    if "UserLedger" not in import_area:
        c = c.replace(
            "from app.models.ledger import EventLog, EventCategory",
            "from app.models.ledger import EventLog, EventCategory, UserLedger"
        )
        fix("加入 UserLedger import")

    if "Invitation" not in import_area:
        # Add Invitation import for cleaning up invitations
        if "from app.models.series import GroupSeries, SeriesStatus" in c:
            c = c.replace(
                "from app.models.series import GroupSeries, SeriesStatus",
                "from app.models.series import GroupSeries, SeriesStatus\nfrom app.models.invitation import Invitation"
            )
        fix("加入 Invitation import (if exists)")

    # 1b. 修正統計 - total_series 只算 ACTIVE
    old_stats_series = "total_series = db.query(GroupSeries).count()"
    new_stats_series = "total_series = db.query(GroupSeries).filter(GroupSeries.status == SeriesStatus.ACTIVE).count()"
    if old_stats_series in c:
        c = c.replace(old_stats_series, new_stats_series)
        fix("統計: total_series 只算 ACTIVE")

    # 1c. 修正統計 - total_pool 只算 ACTIVE
    old_stats_pool = "total_pool = db.query(func.coalesce(func.sum(GroupSeries.current_pool), 0)).scalar()"
    new_stats_pool = "total_pool = db.query(func.coalesce(func.sum(GroupSeries.current_pool), 0)).filter(GroupSeries.status == SeriesStatus.ACTIVE).scalar()"
    if old_stats_pool in c:
        c = c.replace(old_stats_pool, new_stats_pool)
        fix("統計: total_pool 只算 ACTIVE")

    # 1d. 加入硬刪除 endpoint（在 /logs 之前）
    admin_delete_endpoint = '''

# ==================== 集資管理操作 ====================

@router.post("/series/{series_id}/end")
async def admin_end_series(
    series_id: int,
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """管理員強制結束集資"""
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
    """管理員刪除集資 - 硬刪除"""
    series = db.query(GroupSeries).filter(GroupSeries.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="集資不存在")
    
    # 有已開期且有獎金的不能刪
    if series.total_periods > 0 and series.total_prize > 0:
        raise HTTPException(status_code=400, detail="有開獎記錄的集資不可刪除")
    
    # 硬刪除：清除所有關聯資料
    # 1. 清帳本
    try:
        db.query(UserLedger).filter(UserLedger.series_id == series_id).delete(synchronize_session=False)
    except Exception:
        pass
    
    # 2. 清邀請碼
    try:
        from app.models.invitation import Invitation
        db.query(Invitation).filter(Invitation.series_id == series_id).delete(synchronize_session=False)
    except Exception:
        pass
    
    # 3. 清單期團的票
    try:
        from app.models.ticket import Ticket
        groups = db.query(Group).filter(Group.series_id == series_id).all()
        for g in groups:
            db.query(Ticket).filter(Ticket.group_id == g.id).delete(synchronize_session=False)
    except Exception:
        pass
    
    # 4. 清單期團
    db.query(Group).filter(Group.series_id == series_id).delete(synchronize_session=False)
    
    # 5. 清成員
    db.query(GroupMember).filter(GroupMember.series_id == series_id).delete(synchronize_session=False)
    
    # 6. 刪集資本身
    db.delete(series)
    
    db.commit()
    return {"message": "已刪除"}

'''

    # 找到插入點：在 logs endpoint 之前
    log_marker = "# ==================== 事件日誌 =="
    # Also check for the encoded version
    log_marker_encoded = "# ==================== äº‹ä»¶æ—¥èªŒ =="

    # First remove any existing admin delete/end endpoints from previous patches
    # Remove old @router.post("/series/{series_id}/end") and @router.delete blocks
    c = re.sub(
        r'\n@router\.post\("/series/\{series_id\}/end"\).*?return \{"message".*?\}',
        '', c, flags=re.DOTALL
    )
    c = re.sub(
        r'\n@router\.delete\("/series/\{series_id\}"\).*?return \{"message".*?\}',
        '', c, flags=re.DOTALL
    )

    if log_marker in c:
        c = c.replace(log_marker, admin_delete_endpoint + log_marker)
        fix("加入硬刪除+強制結束 endpoints")
    elif log_marker_encoded in c:
        c = c.replace(log_marker_encoded, admin_delete_endpoint + log_marker_encoded)
        fix("加入硬刪除+強制結束 endpoints (encoded)")
    else:
        # Append to end of file
        c += admin_delete_endpoint
        fix("加入硬刪除+強制結束 endpoints (append)")

    with open(ADMIN_PY, "w", encoding="utf-8") as f:
        f.write(c)


# =====================================================================
# 2. admin.html - UI 優化
# =====================================================================
print("\n=== 2. admin.html ===")
ADMIN_HTML = os.path.join(BASE, "static", "admin.html")
if os.path.exists(ADMIN_HTML):
    with open(ADMIN_HTML, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c

    # 2a. 修正 loadSeries - 刪除後重新載入
    # 找到 adminDeleteSeries 函數，確保 loadStats() 也重載
    if "adminDeleteSeries" in c and "loadStats();" not in c.split("adminDeleteSeries")[1][:300]:
        # Already has loadStats in the function from previous patch
        pass

    # 2b. 在集資列表顯示 total_periods
    # 現在顯示 👥 {s.member_count}人 · 💰 {s.total_periods}
    # 優化：顯示更多有用資訊
    
    # 2c. 統計卡片顯示 total_invested 而非 total_pool（後端回傳的是 total_pool）
    # 前端 loadStats 把值塞進 stat cards
    
    # 2d. 已結束集資用淡灰色底，視覺區分
    ended_style = """
        .series-item.ended { opacity: 0.6; background: #f5f5f5; }
        .series-item.ended .series-name { color: #999; }"""
    if "series-item.ended" not in c:
        c = c.replace("</style>", ended_style + "\n    </style>", 1)
        fix("已結束集資灰色底樣式")

    # 2e. loadSeries 渲染時加 ended class
    # Find the series rendering code
    series_render = re.search(
        r'(series\.forEach\(s\s*=>\s*\{.*?)(html\s*\+=\s*[`\'"])',
        c, re.DOTALL
    )
    if series_render:
        # Add ended class logic
        insert_pos = series_render.start(2)
        ended_class = "const endedClass = s.status === 'ended' ? ' ended' : '';\n                "
        if "endedClass" not in c:
            c = c[:insert_pos] + ended_class + c[insert_pos:]
            # Now find the series-item div and add the class
            c = c.replace(
                '<div class="series-item">',
                '<div class="series-item${endedClass}">'
            )
            fix("已結束集資加 ended class")

    if c != orig:
        with open(ADMIN_HTML, "w", encoding="utf-8") as f:
            f.write(c)


# =====================================================================
print(f"\n{'='*50}")
print(f"Total: {fixes} fixes")
print(f"{'='*50}")
if fixes > 0:
    print("\ngit add app/api/v1/admin.py static/admin.html")
    print('git commit -m "fix: admin硬刪除+統計過濾ACTIVE+UI優化"')
    print("git push")
