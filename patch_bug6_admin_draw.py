#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA Bug #6 修復：新增管理員手動輸入開獎 API
日期：2026-02-13
檔案：app/api/v1/admin.py

問題：前端 POST /api/v1/admin/lottery/draw，但 endpoint 不存在
修復：在 admin.py 加入此 endpoint + 所需 import
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ADMIN_FILE = os.path.join(BASE, "app", "api", "v1", "admin.py")

if not os.path.exists(ADMIN_FILE):
    print(f"❌ 找不到: {ADMIN_FILE}")
    sys.exit(1)

with open(ADMIN_FILE, "r", encoding="utf-8") as f:
    content = f.read()

original = content
changes = 0

# ===== 檢查是否已存在 =====
if "/lottery/draw" in content:
    print("⏭️  /admin/lottery/draw endpoint 已存在，跳過")
    sys.exit(0)

# ===== 步驟 1：加入 import =====
# 需要 date 和 LotteryDraw
if "from datetime import datetime" in content and "date" not in content.split("from datetime import")[1].split("\n")[0]:
    content = content.replace(
        "from datetime import datetime",
        "from datetime import datetime, date"
    )
    changes += 1
    print("  ✅ 加入 date import")
elif "from datetime import datetime, date" in content:
    print("  ⏭️  date import 已存在")
else:
    # fallback: 在 datetime import 後面加
    content = content.replace(
        "from datetime import datetime",
        "from datetime import datetime, date"
    )
    changes += 1
    print("  ✅ 加入 date import (fallback)")

if "from app.models.lottery_draw import LotteryDraw" not in content:
    # 找到最後一個 from app.models 的 import，在後面加
    lines = content.split("\n")
    insert_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("from app.models."):
            insert_idx = i
    if insert_idx >= 0:
        lines.insert(insert_idx + 1, "from app.models.lottery_draw import LotteryDraw")
        content = "\n".join(lines)
        changes += 1
        print("  ✅ 加入 LotteryDraw import")
    else:
        print("  ⚠️  找不到 models import 位置")
else:
    print("  ⏭️  LotteryDraw import 已存在")

# ===== 步驟 2：加入 Schema =====
DRAW_SCHEMA = '''

class DrawInput(BaseModel):
    """管理員手動輸入開獎資料"""
    lottery_type: str
    draw_term: str
    draw_date: str
    numbers: dict
    jackpot: Optional[int] = 0
    second_prize: Optional[int] = 0

'''

# 在 # ==================== 系統總覽 之前加入 Schema
if "class DrawInput" not in content:
    # 找到系統總覽的標記
    markers = [
        "# ==================== 系統總覽",
        "# ==================== \xe7\xb3\xbb\xe7\xb5\xb1\xe7\xb8\xbd\xe8\xa6\xbd",
    ]
    inserted = False
    for marker in markers:
        if marker in content:
            content = content.replace(marker, DRAW_SCHEMA + marker)
            inserted = True
            break

    if not inserted:
        # fallback: 找 @router.get("/stats" 在前面插入
        if '@router.get("/stats"' in content:
            content = content.replace(
                '@router.get("/stats"',
                DRAW_SCHEMA + '@router.get("/stats"'
            )
            inserted = True

    if inserted:
        changes += 1
        print("  ✅ 加入 DrawInput Schema")
    else:
        print("  ⚠️  找不到 Schema 插入位置")
else:
    print("  ⏭️  DrawInput Schema 已存在")

# ===== 步驟 3：加入 endpoint =====
ENDPOINT_CODE = '''

# ==================== 開獎管理 ====================

@router.post("/lottery/draw")
async def create_or_update_draw(
    data: DrawInput,
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """管理員手動輸入/更新開獎結果"""
    # 驗證彩種
    if data.lottery_type not in ["power", "super", "daily539"]:
        raise HTTPException(status_code=400, detail="不支援的彩種")

    # 驗證號碼
    numbers = data.numbers
    if data.lottery_type == "power":
        if not numbers.get("first_zone") or len(numbers["first_zone"]) != 6:
            raise HTTPException(status_code=400, detail="威力彩需要6個第一區號碼")
        if numbers.get("second_zone") is None:
            raise HTTPException(status_code=400, detail="威力彩需要第二區號碼")
    elif data.lottery_type == "super":
        if not numbers.get("main") or len(numbers["main"]) != 6:
            raise HTTPException(status_code=400, detail="大樂透需要6個主號碼")
        if numbers.get("special") is None:
            raise HTTPException(status_code=400, detail="大樂透需要特別號")
    else:
        if not numbers.get("numbers") or len(numbers["numbers"]) != 5:
            raise HTTPException(status_code=400, detail="今彩539需要5個號碼")

    # 解析日期
    try:
        draw_date_parsed = date.fromisoformat(data.draw_date)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="日期格式錯誤，請使用 YYYY-MM-DD")

    # 檢查是否已存在（依 lottery_type + draw_term）
    existing = db.query(LotteryDraw).filter(
        LotteryDraw.lottery_type == data.lottery_type,
        LotteryDraw.draw_term == data.draw_term
    ).first()

    if existing:
        # 更新
        existing.draw_date = draw_date_parsed
        existing.numbers = numbers
        existing.jackpot = data.jackpot
        db.commit()
        return {"message": f"已更新第 {data.draw_term} 期開獎結果", "action": "updated", "id": existing.id}
    else:
        # 新增
        draw = LotteryDraw(
            lottery_type=data.lottery_type,
            draw_term=data.draw_term,
            draw_date=draw_date_parsed,
            numbers=numbers,
            jackpot=data.jackpot
        )
        db.add(draw)
        db.commit()
        db.refresh(draw)
        return {"message": f"已新增第 {data.draw_term} 期開獎結果", "action": "created", "id": draw.id}
'''

if '@router.post("/lottery/draw")' not in content:
    # 在檔案最後（最後一個函式之後）加入
    # 找 broadcast endpoint 後面
    if "def send_broadcast" in content:
        # 找到 send_broadcast 函式結尾
        lines = content.split("\n")
        insert_idx = -1
        in_broadcast = False
        brace_depth = 0
        for i, line in enumerate(lines):
            if "def send_broadcast" in line:
                in_broadcast = True
            if in_broadcast:
                brace_depth += line.count("{") - line.count("}")
                # 找到 return 之後的行
                if "return" in line and brace_depth <= 0:
                    # 往下找到函式結束（下一個空行或裝飾器）
                    for j in range(i + 1, len(lines)):
                        stripped = lines[j].strip()
                        if stripped == "" or stripped.startswith("@") or stripped.startswith("#") or stripped.startswith("def "):
                            insert_idx = j
                            break
                    if insert_idx == -1:
                        insert_idx = len(lines)
                    break

        if insert_idx >= 0:
            # 在 broadcast 函式結束後插入（找到包含 } 的行之後）
            # 更簡單的方式：直接在文件末尾加
            content = content.rstrip() + "\n" + ENDPOINT_CODE + "\n"
            changes += 1
            print("  ✅ 加入 POST /admin/lottery/draw endpoint")
        else:
            content = content.rstrip() + "\n" + ENDPOINT_CODE + "\n"
            changes += 1
            print("  ✅ 加入 POST /admin/lottery/draw endpoint (末尾)")
    else:
        content = content.rstrip() + "\n" + ENDPOINT_CODE + "\n"
        changes += 1
        print("  ✅ 加入 POST /admin/lottery/draw endpoint (末尾)")
else:
    print("  ⏭️  endpoint 已存在")

if content == original:
    print("\n⚠️  無變更")
    sys.exit(0)

# 備份
backup = ADMIN_FILE + ".bak"
with open(backup, "w", encoding="utf-8") as f:
    f.write(original)
print(f"\n💾 備份: {backup}")

with open(ADMIN_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n🎉 Bug #6 修復完成！共 {changes} 項變更")
print("   • 新增 POST /api/v1/admin/lottery/draw endpoint")
print("   • 支援新增/更新開獎結果")
print("   • 含號碼驗證（各彩種球數檢查）")
print("   • 同期號自動更新而非報錯")
