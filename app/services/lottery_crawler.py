"""
SELA 樂透一路發 - 彩券開獎資訊爬蟲服務
資料來源：台灣彩券官方 API (api.taiwanlottery.com)
"""
import ssl
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, date

import requests
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)


class UnsafeSSLAdapter(HTTPAdapter):
    """跳過 SSL 驗證（台彩憑證問題）"""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.options &= ~ssl.OP_ENABLE_MIDDLEBOX_COMPAT
        except:
            pass
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


class LotteryCrawler:
    """彩券開獎資訊 - 台灣彩券官方 API"""

    TLC_API = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Origin": "https://www.taiwanlottery.com",
        "Referer": "https://www.taiwanlottery.com/",
    }

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        adapter = UnsafeSSLAdapter()
        self.session.mount("https://api.taiwanlottery.com", adapter)

    def _api_get(self, url: str) -> Optional[dict]:
        try:
            resp = self.session.get(url, timeout=self.timeout, verify=False)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"\u53f0\u5f69 API \u5931\u6557: {url} -> {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[str]:
        if not date_str:
            return None
        date_str = date_str.strip().split("T")[0]
        parts = date_str.replace("-", "/").split("/")
        if len(parts) == 3:
            try:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                if y < 200:
                    y += 1911
                return date(y, m, d).isoformat()
            except (ValueError, TypeError):
                pass
        return None

    def fetch_power(self, year: int, month: int) -> List[dict]:
        url = f"{self.TLC_API}/SuperLotto638Result?period&month={year}-{month:02d}&pageSize=50"
        data = self._api_get(url)
        if not data:
            return []
        results = []
        for item in data.get("content", {}).get("superLotto638Res", []):
            numbers = item.get("drawNumberSize", [])
            if len(numbers) < 7:
                continue
            draw_date = self._parse_date(item.get("lotteryDate", ""))
            if not draw_date:
                continue
            period = item.get("period", "")
            jp_assign = item.get("super638JackpotAssign", {})
            jp = (jp_assign.get("prize", 0) or 0) + (jp_assign.get("lastPrize", 0) or 0) or None
            results.append({
                "lottery_type": "power",
                "draw_term": str(period) if period else f"power_{draw_date}",
                "draw_date": draw_date,
                "numbers": {"first_zone": [int(n) for n in numbers[:6]], "second_zone": int(numbers[6])},
                "jackpot": jp,
            })
        return results

    def fetch_super(self, year: int, month: int) -> List[dict]:
        url = f"{self.TLC_API}/Lotto649Result?period&month={year}-{month:02d}&pageSize=50"
        data = self._api_get(url)
        if not data:
            return []
        results = []
        for item in data.get("content", {}).get("lotto649Res", []):
            numbers = item.get("drawNumberSize", [])
            if len(numbers) < 7:
                continue
            draw_date = self._parse_date(item.get("lotteryDate", ""))
            if not draw_date:
                continue
            period = item.get("period", "")
            jp_assign = item.get("jackpotAssign", {})
            jp = (jp_assign.get("prize", 0) or 0) + (jp_assign.get("lastPrize", 0) or 0) or None
            results.append({
                "lottery_type": "super",
                "draw_term": str(period) if period else f"super_{draw_date}",
                "draw_date": draw_date,
                "numbers": {"main": [int(n) for n in numbers[:6]], "special": int(numbers[6])},
                "jackpot": jp,
            })
        return results

    def fetch_daily539(self, year: int, month: int) -> List[dict]:
        url = f"{self.TLC_API}/Daily539Result?period&month={year}-{month:02d}&pageSize=50"
        data = self._api_get(url)
        if not data:
            return []
        results = []
        for item in data.get("content", {}).get("daily539Res", []):
            numbers = item.get("drawNumberSize", [])
            if len(numbers) < 5:
                continue
            draw_date = self._parse_date(item.get("lotteryDate", ""))
            if not draw_date:
                continue
            period = item.get("period", "")
            results.append({
                "lottery_type": "daily539",
                "draw_term": str(period) if period else f"daily539_{draw_date}",
                "draw_date": draw_date,
                "numbers": {"numbers": [int(n) for n in numbers[:5]]},
                "jackpot": 8000000,
            })
        return results

    def fetch_current_month(self) -> List[dict]:
        """\u6293\u53d6\u7576\u6708\u6240\u6709\u5f69\u7a2e"""
        now = datetime.now()
        y, m = now.year, now.month
        all_items = []
        all_items.extend(self.fetch_power(y, m))
        all_items.extend(self.fetch_super(y, m))
        all_items.extend(self.fetch_daily539(y, m))
        return all_items

    def fetch_months(self, months_back: int = 2) -> List[dict]:
        """\u6293\u53d6\u6700\u8fd1 N \u500b\u6708"""
        all_items = []
        today = date.today()
        for i in range(months_back):
            y, m = today.year, today.month - i
            while m <= 0:
                m += 12
                y -= 1
            all_items.extend(self.fetch_power(y, m))
            all_items.extend(self.fetch_super(y, m))
            all_items.extend(self.fetch_daily539(y, m))
        return all_items

    # === \u76f8\u5bb9\u820a\u4ecb\u9762 ===
    def fetch_all(self) -> Dict[str, Any]:
        """\u76f8\u5bb9\u820a sync endpoint"""
        items = self.fetch_current_month()
        return {"items": items, "updated_at": datetime.now().isoformat()}

    def get_latest(self, lottery_type: str) -> Optional[Dict[str, Any]]:
        now = datetime.now()
        if lottery_type == "power":
            items = self.fetch_power(now.year, now.month)
        elif lottery_type == "super":
            items = self.fetch_super(now.year, now.month)
        elif lottery_type == "daily539":
            items = self.fetch_daily539(now.year, now.month)
        else:
            return None
        if not items:
            return None
        latest = items[0]
        names = {"power": "\u5a01\u529b\u5f69", "super": "\u5927\u6a02\u900f", "daily539": "\u4eca\u5f69539"}
        return {
            "lottery_type": lottery_type,
            "lottery_name": names.get(lottery_type, lottery_type),
            "jackpot": latest.get("jackpot"),
            "latest_draw": {
                "draw_date": latest["draw_date"],
                "draw_term": latest["draw_term"],
                "numbers": latest["numbers"],
            }
        }


lottery_crawler = LotteryCrawler()
