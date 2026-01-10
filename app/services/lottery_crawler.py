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
    PILIO_URLS = {
        "power": "https://www.pilio.idv.tw/lto/list.asp",
        "super": "https://www.pilio.idv.tw/ltobig/list.asp",
        "daily539": "https://www.pilio.idv.tw/lto539/list.asp",
    }
    
    # 樂透雲（有累積獎金）
    LOTTO8_URL = "https://www.lotto-8.com/"
    
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
    
    def _fetch_jackpots_from_lotto8(self) -> Dict[str, Optional[int]]:
        """從樂透雲抓取累積獎金"""
        jackpots = {"power": None, "super": None}
        
        try:
            # 威力彩頁面
            power_html = self._fetch_page("https://www.lotto-8.com/listlto.asp")
            if power_html:
                # 找累積獎金 - 格式可能是 "4.8 億" 或 "48000萬"
                soup = BeautifulSoup(power_html, "html.parser")
                text = soup.get_text()
                
                # 嘗試多種格式
                match = re.search(r'累積[^0-9]*([\d.]+)\s*億', text)
                if match:
                    jackpots["power"] = int(float(match.group(1)) * 100000000)
                else:
                    match = re.search(r'([\d,]+)\s*萬', text)
                    if match:
                        jackpots["power"] = int(match.group(1).replace(',', '')) * 10000
            
            # 大樂透頁面
            super_html = self._fetch_page("https://www.lotto-8.com/listltobig.asp")
            if super_html:
                soup = BeautifulSoup(super_html, "html.parser")
                text = soup.get_text()
                
                match = re.search(r'累積[^0-9]*([\d.]+)\s*億', text)
                if match:
                    jackpots["super"] = int(float(match.group(1)) * 100000000)
                else:
                    match = re.search(r'([\d,]+)\s*萬', text)
                    if match:
                        jackpots["super"] = int(match.group(1).replace(',', '')) * 10000
                        
        except Exception as e:
            logger.error(f"從樂透雲抓取累積獎金失敗: {e}")
        
        return jackpots
    
    def _fetch_jackpots_from_pilio(self) -> Dict[str, Optional[int]]:
        """從 pilio 主頁抓取累積獎金（備用）"""
        jackpots = {"power": None, "super": None}
        
        try:
            html = self._fetch_page("https://www.pilio.idv.tw/", encoding="big5")
            if not html:
                return jackpots
            
            # 不用 BeautifulSoup，直接用正則在原始 HTML 中搜索
            # 格式: 頭彩累積金額NT: 4.8億
            
            # 威力彩
            match = re.search(r'威力彩.*?(\d+\.?\d*)\s*億', html, re.DOTALL)
            if match:
                jackpots["power"] = int(float(match.group(1)) * 100000000)
            
            # 大樂透
            match = re.search(r'大樂透.*?(\d+\.?\d*)\s*億', html, re.DOTALL)
            if match:
                jackpots["super"] = int(float(match.group(1)) * 100000000)
                
        except Exception as e:
            logger.error(f"從 pilio 抓取累積獎金失敗: {e}")
        
        return jackpots
    
    def _parse_pilio_numbers(self, html: str, lottery_type: str) -> List[Dict]:
        """解析 pilio 開獎號碼"""
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
    
    def _try_taiwanlottery_package(self) -> Dict[str, Any]:
        """嘗試使用 taiwanlottery 套件"""
        result = {"power": None, "super": None, "daily539": None}
        
        try:
            from TaiwanLottery import TaiwanLotteryCrawler
            crawler = TaiwanLotteryCrawler()
            
            # 威力彩
            power_data = crawler.super_lotto()
            if power_data:
                result["power"] = [{
                    "draw_date": str(d.get("date", "")),
                    "numbers": {
                        "first_zone": d.get("numbers", [])[:6],
                        "second_zone": d.get("special", 0)
                    }
                } for d in power_data if d.get("numbers")]
            
            # 大樂透
            super_data = crawler.lotto649()
            if super_data:
                result["super"] = [{
                    "draw_date": str(d.get("date", "")),
                    "numbers": {
                        "main": d.get("numbers", [])[:6],
                        "special": d.get("special", 0)
                    }
                } for d in super_data if d.get("numbers")]
            
            # 今彩539
            daily_data = crawler.daily_cash()
            if daily_data:
                result["daily539"] = [{
                    "draw_date": str(d.get("date", "")),
                    "numbers": d.get("numbers", [])[:5]
                } for d in daily_data if d.get("numbers")]
                
        except Exception as e:
            logger.warning(f"taiwanlottery 套件失敗: {e}")
        
        return result
    
    def fetch_all(self) -> Dict[str, Any]:
        """抓取所有彩種資料"""
        
        # 1. 先抓累積獎金
        jackpots = self._fetch_jackpots_from_lotto8()
        
        # 備用: pilio
        if not jackpots.get("power") or not jackpots.get("super"):
            pilio_jackpots = self._fetch_jackpots_from_pilio()
            if not jackpots.get("power"):
                jackpots["power"] = pilio_jackpots.get("power")
            if not jackpots.get("super"):
                jackpots["super"] = pilio_jackpots.get("super")
        
        # 2. 抓開獎號碼 - 優先使用 taiwanlottery 套件
        draws_data = self._try_taiwanlottery_package()
        
        # 備用: pilio
        if not draws_data.get("power"):
            html = self._fetch_page(self.PILIO_URLS["power"], encoding="big5")
            if html:
                draws_data["power"] = self._parse_pilio_numbers(html, "power")
        
        if not draws_data.get("super"):
            html = self._fetch_page(self.PILIO_URLS["super"], encoding="big5")
            if html:
                draws_data["super"] = self._parse_pilio_numbers(html, "super")
        
        if not draws_data.get("daily539"):
            html = self._fetch_page(self.PILIO_URLS["daily539"], encoding="big5")
            if html:
                draws_data["daily539"] = self._parse_pilio_numbers(html, "daily539")
        
        # 3. 組裝結果
        return {
            "updated_at": datetime.now().isoformat(),
            "super_lotto": {
                "lottery_type": "power",
                "lottery_name": "威力彩",
                "jackpot": jackpots.get("power"),
                "draws": draws_data.get("power", [])
            } if draws_data.get("power") else None,
            "lotto649": {
                "lottery_type": "super",
                "lottery_name": "大樂透",
                "jackpot": jackpots.get("super"),
                "draws": draws_data.get("super", [])
            } if draws_data.get("super") else None,
            "daily_cash": {
                "lottery_type": "daily539",
                "lottery_name": "今彩539",
                "jackpot": 8000000,
                "draws": draws_data.get("daily539", [])
            } if draws_data.get("daily539") else None,
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
