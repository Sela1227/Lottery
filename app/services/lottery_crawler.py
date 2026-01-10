"""
SELA 樂透一路發 - 彩券開獎資訊爬蟲服務
"""
import re
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LotteryCrawler:
    """彩券開獎資訊爬蟲"""
    
    # 資料來源
    SOURCES = {
        "super_lotto": {
            "url": "https://www.pilio.idv.tw/lto/list.asp",
            "name": "威力彩",
            "code": "power"
        },
        "lotto649": {
            "url": "https://www.pilio.idv.tw/ltobig/list.asp",
            "name": "大樂透",
            "code": "super"
        },
        "daily_cash": {
            "url": "https://www.pilio.idv.tw/lto539/list.asp",
            "name": "今彩539",
            "code": "daily539"
        }
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def fetch_page(self, url: str) -> Optional[str]:
        """抓取網頁內容"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.encoding = "big5"  # pilio 使用 big5 編碼
            return response.text
        except Exception as e:
            logger.error(f"抓取網頁失敗: {url}, 錯誤: {e}")
            return None
    
    def parse_jackpot(self, soup: BeautifulSoup) -> Optional[int]:
        """解析累積獎金"""
        try:
            # 尋找包含「頭彩獎金累積」的文字
            text = soup.get_text()
            match = re.search(r'頭彩獎金累積[：:]\s*([\d.]+)\s*億', text)
            if match:
                amount = float(match.group(1))
                return int(amount * 100000000)  # 轉換為元
            return None
        except Exception as e:
            logger.error(f"解析累積獎金失敗: {e}")
            return None
    
    def parse_super_lotto(self, html: str) -> Dict[str, Any]:
        """解析威力彩"""
        soup = BeautifulSoup(html, "html.parser")
        result = {
            "lottery_type": "power",
            "lottery_name": "威力彩",
            "jackpot": self.parse_jackpot(soup),
            "draws": []
        }
        
        try:
            # 找到開獎號碼表格
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 3:
                        date_text = cells[0].get_text(strip=True)
                        numbers_text = cells[1].get_text(strip=True)
                        second_zone = cells[2].get_text(strip=True)
                        
                        # 解析日期 (格式: 01/08 26(四))
                        date_match = re.match(r'(\d{2})/(\d{2})\s*(\d{2})', date_text)
                        if date_match and numbers_text:
                            month = int(date_match.group(1))
                            day = int(date_match.group(2))
                            year = 2000 + int(date_match.group(3))
                            
                            # 解析號碼
                            numbers = [int(n.strip()) for n in numbers_text.split(",") if n.strip().isdigit()]
                            second = int(second_zone) if second_zone.isdigit() else None
                            
                            if numbers and second is not None:
                                result["draws"].append({
                                    "draw_date": f"{year}-{month:02d}-{day:02d}",
                                    "numbers": {
                                        "first_zone": numbers,
                                        "second_zone": second
                                    }
                                })
        except Exception as e:
            logger.error(f"解析威力彩失敗: {e}")
        
        return result
    
    def parse_lotto649(self, html: str) -> Dict[str, Any]:
        """解析大樂透"""
        soup = BeautifulSoup(html, "html.parser")
        result = {
            "lottery_type": "super",
            "lottery_name": "大樂透",
            "jackpot": self.parse_jackpot(soup),
            "draws": []
        }
        
        try:
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 3:
                        date_text = cells[0].get_text(strip=True)
                        numbers_text = cells[1].get_text(strip=True)
                        special = cells[2].get_text(strip=True)
                        
                        date_match = re.match(r'(\d{2})/(\d{2})\s*(\d{2})', date_text)
                        if date_match and numbers_text:
                            month = int(date_match.group(1))
                            day = int(date_match.group(2))
                            year = 2000 + int(date_match.group(3))
                            
                            numbers = [int(n.strip()) for n in numbers_text.split(",") if n.strip().isdigit()]
                            special_num = int(special) if special.isdigit() else None
                            
                            if numbers and special_num is not None:
                                result["draws"].append({
                                    "draw_date": f"{year}-{month:02d}-{day:02d}",
                                    "numbers": {
                                        "main": numbers,
                                        "special": special_num
                                    }
                                })
        except Exception as e:
            logger.error(f"解析大樂透失敗: {e}")
        
        return result
    
    def parse_daily_cash(self, html: str) -> Dict[str, Any]:
        """解析今彩539"""
        soup = BeautifulSoup(html, "html.parser")
        result = {
            "lottery_type": "daily539",
            "lottery_name": "今彩539",
            "jackpot": 8000000,  # 固定頭獎 800 萬
            "draws": []
        }
        
        try:
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        date_text = cells[0].get_text(strip=True)
                        numbers_text = cells[1].get_text(strip=True)
                        
                        date_match = re.match(r'(\d{2})/(\d{2})\s*(\d{2})', date_text)
                        if date_match and numbers_text:
                            month = int(date_match.group(1))
                            day = int(date_match.group(2))
                            year = 2000 + int(date_match.group(3))
                            
                            numbers = [int(n.strip()) for n in numbers_text.split(",") if n.strip().isdigit()]
                            
                            if numbers:
                                result["draws"].append({
                                    "draw_date": f"{year}-{month:02d}-{day:02d}",
                                    "numbers": numbers
                                })
        except Exception as e:
            logger.error(f"解析今彩539失敗: {e}")
        
        return result
    
    def fetch_super_lotto(self) -> Optional[Dict[str, Any]]:
        """抓取威力彩"""
        html = self.fetch_page(self.SOURCES["super_lotto"]["url"])
        if html:
            return self.parse_super_lotto(html)
        return None
    
    def fetch_lotto649(self) -> Optional[Dict[str, Any]]:
        """抓取大樂透"""
        html = self.fetch_page(self.SOURCES["lotto649"]["url"])
        if html:
            return self.parse_lotto649(html)
        return None
    
    def fetch_daily_cash(self) -> Optional[Dict[str, Any]]:
        """抓取今彩539"""
        html = self.fetch_page(self.SOURCES["daily_cash"]["url"])
        if html:
            return self.parse_daily_cash(html)
        return None
    
    def fetch_all(self) -> Dict[str, Any]:
        """抓取所有彩種"""
        return {
            "updated_at": datetime.now().isoformat(),
            "super_lotto": self.fetch_super_lotto(),
            "lotto649": self.fetch_lotto649(),
            "daily_cash": self.fetch_daily_cash()
        }
    
    def get_latest(self, lottery_type: str) -> Optional[Dict[str, Any]]:
        """取得特定彩種最新一期"""
        if lottery_type == "power":
            data = self.fetch_super_lotto()
        elif lottery_type == "super":
            data = self.fetch_lotto649()
        elif lottery_type == "daily539":
            data = self.fetch_daily_cash()
        else:
            return None
        
        if data and data.get("draws"):
            latest = data["draws"][0]
            return {
                "lottery_type": data["lottery_type"],
                "lottery_name": data["lottery_name"],
                "jackpot": data["jackpot"],
                "latest_draw": latest
            }
        return None


# 全域實例
lottery_crawler = LotteryCrawler()
