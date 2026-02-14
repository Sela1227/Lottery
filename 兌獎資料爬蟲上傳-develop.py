#!/usr/bin/env python3
"""
SELA 樂透一路發 - 本地歷史資料爬取上傳腳本 v2
資料來源：
  主要 → 台灣彩券官方 API (api.taiwanlottery.com)
  備用 → 中信彩券部 (lotto.ctbcbank.com)

⚠️ 此腳本必須在「本地電腦」執行

用法：
  python 兌獎資料爬蟲上傳-v2.py                        # 抓取當月+上月
  python 兌獎資料爬蟲上傳-v2.py --months 3             # 最近3個月
  python 兌獎資料爬蟲上傳-v2.py --year 2026 --month 1  # 指定月份
  python 兌獎資料爬蟲上傳-v2.py --dry-run              # 只抓取不上傳
  python 兌獎資料爬蟲上傳-v2.py --save-json data.json  # 儲存 JSON
"""
import sys
import ssl
import json
import argparse
import requests
from datetime import date
from requests.adapters import HTTPAdapter

# 關閉 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ==================== 設定 ====================

API_BASE = "https://lottery-develop.up.railway.app"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzcxNTUyNDE1LCJpYXQiOjE3NzA5NDc2MTUsImRpc3BsYXlfbmFtZSI6IlNlbGEiLCJyb2xlIjoiYWRtaW4ifQ.V_bZZD_1zxPST9WztwfRsA2sc0q5WOhyWZs9qFsWt34"

TLC_API_BASE = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://www.taiwanlottery.com",
    "Referer": "https://www.taiwanlottery.com/",
}


# ==================== SSL 修復（Python 3.13 對台彩憑證過嚴） ====================

class UnsafeSSLAdapter(HTTPAdapter):
    """完全跳過 SSL 驗證的 Adapter（解決台彩 Missing Subject Key Identifier）"""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        # Python 3.13 額外需要這個
        try:
            ctx.options &= ~ssl.OP_ENABLE_MIDDLEBOX_COMPAT
        except:
            pass
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def create_tlc_session():
    """建立能連台灣彩券 API 的 session"""
    session = requests.Session()
    session.headers.update(HEADERS)
    adapter = UnsafeSSLAdapter()
    session.mount("https://api.taiwanlottery.com", adapter)
    session.mount("https://www.taiwanlottery.com", adapter)
    return session


# ==================== 工具函式 ====================

def parse_api_date(date_str: str) -> str:
    """解析日期，支援民國年 (115/02/12) 與西元年"""
    if not date_str:
        return None
    # 移除時間部分 "2026-02-12T00:00:00" → "2026-02-12"
    date_str = date_str.strip().split("T")[0]
    parts = date_str.replace("-", "/").split("/")
    if len(parts) == 3:
        try:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            if year < 200:
                year += 1911
            return date(year, month, day).isoformat()
        except (ValueError, TypeError):
            pass
    return None


def parse_jackpot(value) -> int:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        clean = value.replace(",", "").replace(" ", "").replace("$", "").replace("NT", "")
        try:
            return int(clean)
        except ValueError:
            return None
    return None


def format_jackpot(value) -> str:
    if not value:
        return ""
    if value >= 100000000:
        return f"  💰{value / 100000000:.1f}億"
    elif value >= 10000:
        return f"  💰{value / 10000:.0f}萬"
    return f"  💰{value}"


def get_month_list(months_back=2, year=None, month=None):
    if year and month:
        return [(year, month)]
    result = []
    today = date.today()
    for i in range(months_back):
        y, m = today.year, today.month - i
        while m <= 0:
            m += 12
            y -= 1
        result.append((y, m))
    return result


# ==================== 方法一：台灣彩券官方 API ====================

def tlc_request(session, url: str) -> dict:
    """透過自訂 SSL session 發送請求"""
    try:
        resp = session.get(url, timeout=15, verify=False)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return None


def fetch_power_api(session, year, month):
    url = f"{TLC_API_BASE}/SuperLotto638Result?period&month={year}-{month:02d}&pageSize=50"
    data = tlc_request(session, url)
    if not data:
        return None  # None = 連線失敗，[] = 沒資料

    results = []
    for item in data.get("content", {}).get("superLotto638Res", []):
        numbers = item.get("drawNumberSize", [])
        if len(numbers) < 7:
            continue
        draw_date = parse_api_date(item.get("lotteryDate", ""))
        if not draw_date:
            continue
        period = item.get("period", "")
        first_zone = [int(n) for n in numbers[:6]]
        second_zone = int(numbers[6])
        jp_assign = item.get("super638JackpotAssign", {})
        jp = (jp_assign.get("prize", 0) or 0) + (jp_assign.get("lastPrize", 0) or 0) or None
        results.append({
            "lottery_type": "power",
            "draw_term": str(period) if period else f"power_{draw_date}",
            "draw_date": draw_date,
            "numbers": {"first_zone": first_zone, "second_zone": second_zone},
            "jackpot": jp
        })
        print(f"    ✔ {draw_date} 期{period}: {first_zone} + {second_zone}{format_jackpot(jp)}")
    return results


def fetch_super_api(session, year, month):
    url = f"{TLC_API_BASE}/Lotto649Result?period&month={year}-{month:02d}&pageSize=50"
    data = tlc_request(session, url)
    if not data:
        return None

    results = []
    for item in data.get("content", {}).get("lotto649Res", []):
        numbers = item.get("drawNumberSize", [])
        if len(numbers) < 7:
            continue
        draw_date = parse_api_date(item.get("lotteryDate", ""))
        if not draw_date:
            continue
        period = item.get("period", "")
        main_numbers = [int(n) for n in numbers[:6]]
        special = int(numbers[6])
        jp_assign = item.get("jackpotAssign", {})
        jp = (jp_assign.get("prize", 0) or 0) + (jp_assign.get("lastPrize", 0) or 0) or None
        results.append({
            "lottery_type": "super",
            "draw_term": str(period) if period else f"super_{draw_date}",
            "draw_date": draw_date,
            "numbers": {"main": main_numbers, "special": special},
            "jackpot": jp
        })
        print(f"    ✔ {draw_date} 期{period}: {main_numbers} + {special}{format_jackpot(jp)}")
    return results


def fetch_daily539_api(session, year, month):
    url = f"{TLC_API_BASE}/Daily539Result?period&month={year}-{month:02d}&pageSize=50"
    data = tlc_request(session, url)
    if not data:
        return None

    results = []
    for item in data.get("content", {}).get("daily539Res", []):
        numbers = item.get("drawNumberSize", [])
        if len(numbers) < 5:
            continue
        draw_date = parse_api_date(item.get("lotteryDate", ""))
        if not draw_date:
            continue
        period = item.get("period", "")
        draw_numbers = [int(n) for n in numbers[:5]]
        results.append({
            "lottery_type": "daily539",
            "draw_term": str(period) if period else f"daily539_{draw_date}",
            "draw_date": draw_date,
            "numbers": {"numbers": draw_numbers},
            "jackpot": 8000000
        })
        print(f"    ✔ {draw_date} 期{period}: {draw_numbers}")
    return results


# ==================== 方法二（備用）：中信彩券部 HTML 爬蟲 ====================

def fetch_from_ctbc() -> list:
    """從 lotto.ctbcbank.com 爬取最新一期開獎資料"""
    print("\n  🔄 使用備用來源：中信彩券部 (lotto.ctbcbank.com)")
    
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("    ⚠ 需要安裝 beautifulsoup4: pip install beautifulsoup4")
        return []

    try:
        resp = requests.get(
            "https://lotto.ctbcbank.com/result_all.htm",
            headers={"User-Agent": HEADERS["User-Agent"]},
            timeout=15
        )
        resp.encoding = "utf-8"
    except Exception as e:
        print(f"    ✗ 連線失敗: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    # 找到所有表格，解析開獎資料
    tables = soup.find_all("table")
    
    for table in tables:
        text = table.get_text()
        
        # === 威力彩 ===
        if "威力彩" in text and "第一區" in text:
            try:
                # 找期別和日期
                period_tag = table.find(string=lambda s: s and "期" in s and "/" in s)
                if not period_tag:
                    continue
                period_text = period_tag.strip()
                
                # 找所有球號 (通常在 class 含 ball 的元素裡)
                balls = []
                for tag in table.find_all(["span", "div", "td"]):
                    cls = " ".join(tag.get("class", []))
                    t = tag.get_text(strip=True)
                    if t.isdigit() and len(t) <= 2 and ("ball" in cls.lower() or "num" in cls.lower()):
                        balls.append(int(t))
                
                if len(balls) >= 7:
                    first_zone = sorted(balls[:6])
                    second_zone = balls[6]
                    
                    # 嘗試解析日期
                    import re
                    date_match = re.search(r'(\d{3})/(\d{2})/(\d{2})', period_text)
                    if date_match:
                        y = int(date_match.group(1)) + 1911
                        m = int(date_match.group(2))
                        d = int(date_match.group(3))
                        draw_date = date(y, m, d).isoformat()
                    else:
                        date_match = re.search(r'(\d{4})/(\d{2})/(\d{2})', period_text)
                        if date_match:
                            draw_date = date(int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))).isoformat()
                        else:
                            draw_date = date.today().isoformat()
                    
                    # 找期別號碼
                    term_match = re.search(r'(\d{9,})', period_text)
                    term = term_match.group(1) if term_match else f"power_{draw_date}"
                    
                    results.append({
                        "lottery_type": "power",
                        "draw_term": term,
                        "draw_date": draw_date,
                        "numbers": {"first_zone": first_zone, "second_zone": second_zone},
                        "jackpot": None
                    })
                    print(f"    ✔ 威力彩 {draw_date}: {first_zone} + {second_zone}")
            except Exception as e:
                print(f"    ⚠ 威力彩解析錯誤: {e}")

        # === 大樂透 ===
        if "大樂透" in text and "特別號" in text:
            try:
                balls = []
                for tag in table.find_all(["span", "div", "td"]):
                    cls = " ".join(tag.get("class", []))
                    t = tag.get_text(strip=True)
                    if t.isdigit() and len(t) <= 2 and ("ball" in cls.lower() or "num" in cls.lower()):
                        balls.append(int(t))
                
                if len(balls) >= 7:
                    main_numbers = sorted(balls[:6])
                    special = balls[6]
                    
                    import re
                    period_tag = table.find(string=lambda s: s and "期" in s and "/" in s)
                    period_text = period_tag.strip() if period_tag else ""
                    
                    date_match = re.search(r'(\d{3})/(\d{2})/(\d{2})', period_text)
                    if date_match:
                        y = int(date_match.group(1)) + 1911
                        draw_date = date(y, int(date_match.group(2)), int(date_match.group(3))).isoformat()
                    else:
                        draw_date = date.today().isoformat()
                    
                    term_match = re.search(r'(\d{9,})', period_text)
                    term = term_match.group(1) if term_match else f"super_{draw_date}"
                    
                    results.append({
                        "lottery_type": "super",
                        "draw_term": term,
                        "draw_date": draw_date,
                        "numbers": {"main": main_numbers, "special": special},
                        "jackpot": None
                    })
                    print(f"    ✔ 大樂透 {draw_date}: {main_numbers} + {special}")
            except Exception as e:
                print(f"    ⚠ 大樂透解析錯誤: {e}")

        # === 今彩539 ===
        if "今彩539" in text:
            try:
                balls = []
                for tag in table.find_all(["span", "div", "td"]):
                    cls = " ".join(tag.get("class", []))
                    t = tag.get_text(strip=True)
                    if t.isdigit() and len(t) <= 2 and ("ball" in cls.lower() or "num" in cls.lower()):
                        balls.append(int(t))
                
                if len(balls) >= 5:
                    draw_numbers = sorted(balls[:5])
                    
                    import re
                    period_tag = table.find(string=lambda s: s and "期" in s and "/" in s)
                    period_text = period_tag.strip() if period_tag else ""
                    
                    date_match = re.search(r'(\d{3})/(\d{2})/(\d{2})', period_text)
                    if date_match:
                        y = int(date_match.group(1)) + 1911
                        draw_date = date(y, int(date_match.group(2)), int(date_match.group(3))).isoformat()
                    else:
                        draw_date = date.today().isoformat()
                    
                    term_match = re.search(r'(\d{9,})', period_text)
                    term = term_match.group(1) if term_match else f"daily539_{draw_date}"
                    
                    results.append({
                        "lottery_type": "daily539",
                        "draw_term": term,
                        "draw_date": draw_date,
                        "numbers": {"numbers": draw_numbers},
                        "jackpot": 8000000
                    })
                    print(f"    ✔ 今彩539 {draw_date}: {draw_numbers}")
            except Exception as e:
                print(f"    ⚠ 今彩539解析錯誤: {e}")

    print(f"    共 {len(results)} 筆（備用來源僅提供最新一期）")
    return results


# ==================== 上傳 ====================

def upload_to_api(items: list) -> dict:
    print(f"\n📤 上傳 {len(items)} 筆資料到 {API_BASE}...")

    if not ACCESS_TOKEN:
        print("❌ 請先設定 ACCESS_TOKEN")
        return None

    try:
        response = requests.post(
            f"{API_BASE}/api/v1/lottery/batch-import",
            json={"items": items},
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=60
        )

        print(f"  HTTP 狀態: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result.get('message', '成功')}")
            return result
        elif response.status_code == 401:
            print("❌ Token 已過期，請重新登入取得新的 ACCESS_TOKEN")
            return None
        else:
            print(f"❌ 錯誤: {response.text[:300]}")
            return None
    except Exception as e:
        print(f"❌ 上傳失敗: {e}")
        return None


# ==================== 主程式 ====================

def main():
    parser = argparse.ArgumentParser(
        description="SELA 樂透一路發 - 開獎資料匯入 v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  %(prog)s                        抓取最近 2 個月並上傳
  %(prog)s --months 6             抓取最近 6 個月
  %(prog)s --year 2026 --month 1  只抓 2026 年 1 月
  %(prog)s --dry-run              只抓取不上傳
  %(prog)s --save-json data.json  另存 JSON 檔
        """
    )
    parser.add_argument("--months", type=int, default=2, help="抓取最近幾個月 (預設: 2)")
    parser.add_argument("--year", type=int, help="指定年份 (西元)")
    parser.add_argument("--month", type=int, help="指定月份")
    parser.add_argument("--dry-run", action="store_true", help="只抓取不上傳")
    parser.add_argument("--save-json", type=str, help="儲存 JSON 檔案路徑")
    parser.add_argument("--api-base", type=str, help="覆蓋 SELA API 網址")
    parser.add_argument("--token", type=str, help="覆蓋 JWT Token")
    args = parser.parse_args()

    global API_BASE, ACCESS_TOKEN
    if args.api_base:
        API_BASE = args.api_base
    if args.token:
        ACCESS_TOKEN = args.token

    print("=" * 55)
    print("  SELA 樂透一路發 - 開獎資料匯入工具 v2")
    print("  主要來源：台灣彩券官方 API")
    print("  備用來源：中信彩券部 HTML")
    print("=" * 55)
    print()

    month_list = get_month_list(
        months_back=args.months,
        year=args.year,
        month=args.month
    )
    print(f"📅 抓取月份: {', '.join(f'{y}/{m:02d}' for y, m in month_list)}")

    # ── 嘗試方法一：官方 API ──
    print(f"\n📡 嘗試台灣彩券官方 API...")
    session = create_tlc_session()
    
    all_items = []
    api_works = True

    for year, month in month_list:
        print(f"\n{'─' * 45}")
        print(f"📆 {year} 年 {month} 月")
        print(f"{'─' * 45}")

        print(f"  🔴 威力彩 {year}/{month:02d}")
        power = fetch_power_api(session, year, month)
        if power is None:
            print("    ✗ 官方 API 無法連線")
            api_works = False
            break
        all_items.extend(power)
        print(f"    共 {len(power)} 筆")

        print(f"  🔵 大樂透 {year}/{month:02d}")
        super_items = fetch_super_api(session, year, month)
        if super_items is None:
            api_works = False
            break
        all_items.extend(super_items)
        print(f"    共 {len(super_items)} 筆")

        print(f"  🟢 今彩539 {year}/{month:02d}")
        daily = fetch_daily539_api(session, year, month)
        if daily is None:
            api_works = False
            break
        all_items.extend(daily)
        print(f"    共 {len(daily)} 筆")

    # ── 方法一失敗 → 備用：中信彩券部 ──
    if not api_works:
        print("\n⚠️  官方 API 連線失敗（SSL 憑證問題），切換備用來源...")
        all_items = fetch_from_ctbc()

    # ── 摘要 ──
    power_count = sum(1 for i in all_items if i["lottery_type"] == "power")
    super_count = sum(1 for i in all_items if i["lottery_type"] == "super")
    daily_count = sum(1 for i in all_items if i["lottery_type"] == "daily539")

    print(f"\n{'═' * 45}")
    print(f"📊 總共抓取 {len(all_items)} 筆資料")
    print(f"   🔴 威力彩:  {power_count} 筆")
    print(f"   🔵 大樂透:  {super_count} 筆")
    print(f"   🟢 今彩539: {daily_count} 筆")
    print(f"{'═' * 45}")

    if not all_items:
        print("❌ 沒有抓取到任何資料")
        return

    if args.save_json:
        with open(args.save_json, "w", encoding="utf-8") as f:
            json.dump({"items": all_items}, f, ensure_ascii=False, indent=2)
        print(f"\n💾 已儲存到 {args.save_json}")

    if args.dry_run:
        print("\n🔍 Dry-run 模式，不上傳")
    else:
        result = upload_to_api(all_items)
        if result:
            print("\n" + "=" * 55)
            print("  ✅ 完成！開獎資料已更新")
            print("=" * 55)


if __name__ == "__main__":
    main()
