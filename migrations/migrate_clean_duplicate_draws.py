#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA 資料庫清理：移除重複開獎記錄
日期：2026-02-13

問題：lottery_draws 表中有兩種期號格式：
  - 正規：115000008
  - 非正規：power_2026-01-26, super_2026-01-23

同一天同一彩種的號碼完全相同，是重複匯入造成的。

處理邏輯：
  1. 找出 draw_term 含 power_/super_/daily539_ 前綴的記錄
  2. 如果同 lottery_type + draw_date 已有正規期號 → 刪除非正規的
  3. 如果沒有正規期號（只有非正規的）→ 保留但標記，不刪除

此腳本放在 app/migrations/ 並透過 Dockerfile CMD 自動執行
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL 環境變數未設定")
    print("   Railway 部署時會自動帶入，本地測試請手動設定")
    sys.exit(1)

def main():
    print("🔧 開始清理重複開獎記錄...")
    print("=" * 50)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 找出非正規期號的記錄（含 _ 前綴）
        cur.execute("""
            SELECT id, lottery_type, draw_term, draw_date, numbers
            FROM lottery_draws
            WHERE draw_term LIKE 'power_%'
               OR draw_term LIKE 'super_%'
               OR draw_term LIKE 'daily539_%'
            ORDER BY lottery_type, draw_date
        """)
        irregular = cur.fetchall()

        if not irregular:
            print("✅ 沒有非正規期號的記錄，無需清理")
            return

        print(f"📋 找到 {len(irregular)} 筆非正規期號記錄\n")

        delete_ids = []
        keep_ids = []

        for row in irregular:
            # 檢查同一天同一彩種是否有正規期號
            cur.execute("""
                SELECT id, draw_term
                FROM lottery_draws
                WHERE lottery_type = %s
                  AND draw_date = %s
                  AND draw_term NOT LIKE 'power_%%'
                  AND draw_term NOT LIKE 'super_%%'
                  AND draw_term NOT LIKE 'daily539_%%'
                LIMIT 1
            """, (row['lottery_type'], row['draw_date']))

            regular = cur.fetchone()

            if regular:
                # 有正規記錄 → 刪除非正規的
                delete_ids.append(row['id'])
                print(f"  🗑️  刪除: {row['draw_term']} ({row['draw_date']}) → 已有正規期號 {regular['draw_term']}")
            else:
                # 沒有正規記錄 → 保留
                keep_ids.append(row['id'])
                print(f"  ⏭️  保留: {row['draw_term']} ({row['draw_date']}) → 無對應正規期號")

        print(f"\n📊 結果: 刪除 {len(delete_ids)} 筆, 保留 {len(keep_ids)} 筆")

        if delete_ids:
            cur.execute(
                "DELETE FROM lottery_draws WHERE id = ANY(%s)",
                (delete_ids,)
            )
            conn.commit()
            print(f"\n✅ 已刪除 {len(delete_ids)} 筆重複記錄")
        else:
            print("\n✅ 無需刪除")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 清理失敗: {e}")
        raise
    finally:
        cur.close()
        conn.close()

    print("🎉 清理完成!")


if __name__ == "__main__":
    main()
