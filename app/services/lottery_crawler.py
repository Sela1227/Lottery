"""
SELA 樂透一路發 - 彩券開獎資訊爬蟲服務
"""
import re
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LotteryCrawler:
    """彩券開獎資訊爬蟲"""
    
    # pilio 來源
    PILIO_MAIN = "https://www.pilio.idv.tw/"
    PILIO_URLS = {
        "power": "https://www.pilio.idv.tw/lto/list.asp",
        "super": "https://www.pilio.idv.tw/ltobig/list.asp",
        "daily539": "https://www.pilio.idv.tw/lto539/list.asp",
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9",
    }
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def _fetch_page(self, url: str, encoding: str = "utf-8") -> Optional[str]:
        """抓取網頁"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.encoding = encoding
            return response.text
        except Exception as e:
            logger.error(f"抓取失敗 {url}: {e}")
            return None
    
    def _fetch_jackpots_from_pilio_main(self) -> Dict[str, Optional[int]]:
        """
        從 pilio 主頁抓取累積獎金
        格式: "頭彩累積金額NT: 4.8億" 或 "頭彩累積金額NT: 1.1億"
        """
        jackpots = {"power": None, "super": None}
        
        try:
            html = self._fetch_page(self.PILIO_MAIN, encoding="utf-8")
            if not html:
                return jackpots
            
            # 威力彩: 找 "威力彩開獎號碼...頭彩累積金額NT: X.X億"
            power_match = re.search(
                r'威力彩開獎號碼.*?頭彩累積金額NT:\s*([\d.]+)億',
                html,
                re.DOTALL
            )
            if power_match:
                amount = float(power_match.group(1))
                jackpots["power"] = int(amount * 100000000)
                logger.info(f"威力彩累積獎金: {amount}億 = {jackpots['power']}")
            
            # 大樂透: 找 "大樂透開獎號碼...頭彩累積金額NT: X.X億"
            super_match = re.search(
                r'大樂透開獎號碼.*?頭彩累積金額NT:\s*([\d.]+)億',
                html,
                re.DOTALL
            )
            if super_match:
                amount = float(super_match.group(1))
                jackpots["super"] = int(amount * 100000000)
                logger.info(f"大樂透累積獎金: {amount}億 = {jackpots['super']}")
                
        except Exception as e:
            logger.error(f"從 pilio 主頁抓取累積獎金失敗: {e}")
        
        return jackpots
    
    def _parse_pilio_numbers(self, html: str, lottery_type: str) -> List[Dict]:
        """解析 pilio list.asp 開獎號碼"""
        draws = []
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            tables = soup.find_all("table")
            
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) < 2:
                        continue
                    
                    date_text = cells[0].get_text(strip=True)
                    
                    # 解析日期: "01/08 26(四)" -> 2026-01-08
                    date_match = re.search(r'(\d{2})/(\d{2})\s*(\d{2})', date_text)
                    if not date_match:
                        continue
                    
                    month = int(date_match.group(1))
                    day = int(date_match.group(2))
                    year = 2000 + int(date_match.group(3))
                    draw_date = f"{year}-{month:02d}-{day:02d}"
                    
                    # 解析號碼
                    numbers_text = cells[1].get_text(strip=True)
                    numbers = [int(n) for n in re.findall(r'\d+', numbers_text)]
                    
                    if lottery_type == "power" and len(cells) >= 3 and len(numbers) >= 6:
                        second_text = cells[2].get_text(strip=True)
                        second_match = re.search(r'\d+', second_text)
                        if second_match:
                            draws.append({
                                "draw_date": draw_date,
                                "numbers": {
                                    "first_zone": numbers[:6],
                                    "second_zone": int(second_match.group())
                                }
                            })
                    
                    elif lottery_type == "super" and len(cells) >= 3 and len(numbers) >= 6:
                        special_text = cells[2].get_text(strip=True)
                        special_match = re.search(r'\d+', special_text)
                        if special_match:
                            draws.append({
                                "draw_date": draw_date,
                                "numbers": {
                                    "main": numbers[:6],
                                    "special": int(special_match.group())
                                }
                            })
                    
                    elif lottery_type == "daily539" and len(numbers) >= 5:
                        draws.append({
                            "draw_date": draw_date,
                            "numbers": numbers[:5]
                        })
        
        except Exception as e:
            logger.error(f"解析開獎號碼失敗: {e}")
        
        return draws
    
    def fetch_all(self) -> Dict[str, Any]:
        """抓取所有彩種資料"""
        
        # 1. 從 pilio 主頁抓取累積獎金
        jackpots = self._fetch_jackpots_from_pilio_main()
        
        # 2. 從 pilio list.asp 抓取開獎號碼
        power_draws = []
        super_draws = []
        daily_draws = []
        
        # 威力彩
        html = self._fetch_page(self.PILIO_URLS["power"], encoding="big5")
        if html:
            power_draws = self._parse_pilio_numbers(html, "power")
        
        # 大樂透
        html = self._fetch_page(self.PILIO_URLS["super"], encoding="big5")
        if html:
            super_draws = self._parse_pilio_numbers(html, "super")
        
        # 今彩539
        html = self._fetch_page(self.PILIO_URLS["daily539"], encoding="big5")
        if html:
            daily_draws = self._parse_pilio_numbers(html, "daily539")
        
        # 3. 組裝結果
        return {
            "updated_at": datetime.now().isoformat(),
            "super_lotto": {
                "lottery_type": "power",
                "lottery_name": "威力彩",
                "jackpot": jackpots.get("power"),
                "draws": power_draws
            } if power_draws else None,
            "lotto649": {
                "lottery_type": "super",
                "lottery_name": "大樂透",
                "jackpot": jackpots.get("super"),
                "draws": super_draws
            } if super_draws else None,
            "daily_cash": {
                "lottery_type": "daily539",
                "lottery_name": "今彩539",
                "jackpot": 8000000,  # 固定 800 萬
                "draws": daily_draws
            } if daily_draws else None,
        }
    
    def get_latest(self, lottery_type: str) -> Optional[Dict[str, Any]]:
        """取得特定彩種最新一期"""
        all_data = self.fetch_all()
        
        type_map = {
            "power": "super_lotto",
            "super": "lotto649",
            "daily539": "daily_cash"
        }
        
        key = type_map.get(lottery_type)
        if not key or not all_data.get(key):
            return None
        
        data = all_data[key]
        if data and data.get("draws"):
            return {
                "lottery_type": data["lottery_type"],
                "lottery_name": data["lottery_name"],
                "jackpot": data["jackpot"],
                "latest_draw": data["draws"][0]
            }
        
        return None


# 全域實例
lottery_crawler = LotteryCrawler()
