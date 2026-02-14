#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理重複開獎記錄
刪除 power_2026-01-26、super_2026-01-23 等非正規期號的重複資料
"""
import os
import sys

def main():
    print("🔧 檢查重複開獎記錄...")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("⚠️  DATABASE_URL 未設定，跳過清理")
        return

    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        print("⚠️  psycopg2 未安裝，跳過清理")
        return

    conn = psycopg2.connect(database_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 找出非正規期號
        cur.execute("""
            SELECT id, lottery_type, draw_term, draw_date
            FROM lottery_draws
            WHERE draw_term LIKE 'power_%%'
               OR draw_term LIKE 'super_%%'
               OR draw_term LIKE 'daily539_%%'
            ORDER BY lottery_type, draw_date
        """)
        irregular = cur.fetchall()

        if not irregular:
            print("✅ 無重複記錄，跳過")
            return

        print(f"📋 找到 {len(irregular)} 筆非正規期號")

        delete_ids = []

        for row in irregular:
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
                delete_ids.append(row['id'])
                print(f"  🗑️  刪除 {row['draw_term']} → 已有 {regular['draw_term']}")
            else:
                print(f"  ⏭️  保留 {row['draw_term']}（無對應正規期號）")

        if delete_ids:
            cur.execute("DELETE FROM lottery_draws WHERE id = ANY(%s)", (delete_ids,))
            conn.commit()
            print(f"✅ 已刪除 {len(delete_ids)} 筆重複記錄")
        else:
            print("✅ 無需刪除")

    except Exception as e:
        conn.rollback()
        print(f"⚠️  清理失敗（不影響啟動）: {e}")
    finally:
        cur.close()
        conn.close()

    print("🎉 清理完成!")

if __name__ == "__main__":
    main()
