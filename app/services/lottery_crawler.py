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
    # 台彩官網：累積獎金（精確）
    # pilio：開獎號碼
    MAIN_PAGE = "https://www.pilio.idv.tw/"
    
    # 台彩官網 - 累積獎金
    TAIWANLOTTERY_URLS = {
        "power": "https://www.taiwanlottery.com/lotto/result/super_lotto638",
        "super": "https://www.taiwanlottery.com/lotto/result/lotto649",
    }
    
    SOURCES = {
        "super_lotto": {
            "list_url": "https://www.pilio.idv.tw/lto/list.asp",
            "name": "威力彩",
            "code": "power"
        },
        "lotto649": {
            "list_url": "https://www.pilio.idv.tw/ltobig/list.asp",
            "name": "大樂透",
            "code": "super"
        },
        "daily_cash": {
            "list_url": "https://www.pilio.idv.tw/lto539/list.asp",
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
    
    def parse_jackpot_from_home(self, html: str) -> Optional[int]:
        """從首頁解析累積獎金"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()
            
            # 嘗試多種格式匹配
            # pilio 首頁格式: "頭彩累積金額NT: 4.8億" 或 "頭彩累積金額 NT: 1 億元"
            patterns = [
                r'頭彩累積金額\s*NT[：:]\s*([\d.]+)\s*億',  # 格式1
                r'累積金額\s*NT[：:]\s*([\d.]+)\s*億',       # 格式2
                r'NT[：:]\s*([\d.]+)\s*億',                  # 簡化格式
                r'([\d.]+)\s*億元',                          # 最簡格式
                r'([\d.]+)億',                               # 無空格格式
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    amount = float(match.group(1))
                    return int(amount * 100000000)  # 轉換為元
            
            # 嘗試匹配萬元格式
            match = re.search(r'([\d,]+)\s*萬元', text)
            if match:
                amount_str = match.group(1).replace(',', '')
                return int(float(amount_str) * 10000)
            
            return None
        except Exception as e:
            logger.error(f"解析累積獎金失敗: {e}")
            return None
    
    def fetch_jackpot_from_taiwanlottery(self, lottery_type: str) -> Optional[int]:
        """從台彩官網抓取累積獎金"""
        if lottery_type not in self.TAIWANLOTTERY_URLS:
            return None
        
        try:
            url = self.TAIWANLOTTERY_URLS[lottery_type]
            response = self.session.get(url, timeout=self.timeout)
            response.encoding = "utf-8"
            html = response.text
            
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()
            
            # 台彩官網格式: "$0,445,667,415" 或 "$ 0,445,667,415"
            # 尋找 $ 後面的數字
            match = re.search(r'\$\s*([\d,]+)', text)
            if match:
                amount_str = match.group(1).replace(',', '')
                amount = int(amount_str)
                if amount > 0:
                    return amount
            
            # 備用：尋找「目前頭獎預估金額」後的數字
            match = re.search(r'目前頭獎預估金額.*?([\d,]+)', text, re.DOTALL)
            if match:
                amount_str = match.group(1).replace(',', '')
                return int(amount_str)
            
            return None
        except Exception as e:
            logger.error(f"從台彩官網抓取累積獎金失敗: {e}")
            return None
    
    def parse_all_jackpots_from_main(self, html: str) -> Dict[str, Optional[int]]:
        """從 pilio 主頁解析所有彩種的累積獎金"""
        jackpots = {
            "power": None,
            "super": None,
        }
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()
            
            # 威力彩格式: "威力彩開獎號碼...頭彩累積金額NT: 4.8億"
            power_match = re.search(r'威力彩.*?頭彩累積金額\s*NT[：:]\s*([\d.]+)\s*億', text, re.DOTALL)
            if power_match:
                jackpots["power"] = int(float(power_match.group(1)) * 100000000)
            
            # 大樂透格式: "大樂透開獎號碼...頭彩累積金額NT: 1億"
            super_match = re.search(r'大樂透.*?頭彩累積金額\s*NT[：:]\s*([\d.]+)\s*億', text, re.DOTALL)
            if super_match:
                jackpots["super"] = int(float(super_match.group(1)) * 100000000)
            
        except Exception as e:
            logger.error(f"解析主頁累積獎金失敗: {e}")
        
        return jackpots
    
    def parse_numbers_from_list(self, html: str, lottery_type: str) -> List[Dict]:
        """從 list.asp 解析開獎號碼"""
        draws = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 找到開獎號碼表格
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        date_text = cells[0].get_text(strip=True)
                        numbers_text = cells[1].get_text(strip=True)
                        
                        # 解析日期 (格式: 01/08 26(四) 或 01/08/26)
                        date_match = re.match(r'(\d{2})/(\d{2})\s*(\d{2})', date_text)
                        if not date_match:
                            date_match = re.match(r'(\d{2})/(\d{2})/(\d{2})', date_text)
                        
                        if date_match and numbers_text:
                            month = int(date_match.group(1))
                            day = int(date_match.group(2))
                            year = 2000 + int(date_match.group(3))
                            
                            # 解析號碼
                            numbers = [int(n.strip()) for n in re.findall(r'\d+', numbers_text)]
                            
                            if lottery_type == "power" and len(cells) >= 3:
                                # 威力彩: 6個主號 + 1個第二區
                                main_nums = numbers[:6] if len(numbers) >= 6 else numbers
                                second_text = cells[2].get_text(strip=True)
                                second_match = re.search(r'\d+', second_text)
                                second = int(second_match.group()) if second_match else None
                                
                                if main_nums and second is not None:
                                    draws.append({
                                        "draw_date": f"{year}-{month:02d}-{day:02d}",
                                        "numbers": {
                                            "first_zone": main_nums,
                                            "second_zone": second
                                        }
                                    })
                            
                            elif lottery_type == "super" and len(cells) >= 3:
                                # 大樂透: 6個主號 + 1個特別號
                                main_nums = numbers[:6] if len(numbers) >= 6 else numbers
                                special_text = cells[2].get_text(strip=True)
                                special_match = re.search(r'\d+', special_text)
                                special = int(special_match.group()) if special_match else None
                                
                                if main_nums and special is not None:
                                    draws.append({
                                        "draw_date": f"{year}-{month:02d}-{day:02d}",
                                        "numbers": {
                                            "main": main_nums,
                                            "special": special
                                        }
                                    })
                            
                            elif lottery_type == "daily539":
                                # 今彩539: 5個號碼
                                if len(numbers) >= 5:
                                    draws.append({
                                        "draw_date": f"{year}-{month:02d}-{day:02d}",
                                        "numbers": numbers[:5]
                                    })
        except Exception as e:
            logger.error(f"解析開獎號碼失敗: {e}")
        
        return draws
    
    def fetch_super_lotto(self, jackpots: Dict[str, Optional[int]] = None) -> Optional[Dict[str, Any]]:
        """抓取威力彩"""
        result = {
            "lottery_type": "power",
            "lottery_name": "威力彩",
            "jackpot": jackpots.get("power") if jackpots else None,
            "draws": []
        }
        
        # 從 list.asp 抓開獎號碼
        list_html = self.fetch_page(self.SOURCES["super_lotto"]["list_url"])
        if list_html:
            result["draws"] = self.parse_numbers_from_list(list_html, "power")
        
        return result if result["draws"] else None
    
    def fetch_lotto649(self, jackpots: Dict[str, Optional[int]] = None) -> Optional[Dict[str, Any]]:
        """抓取大樂透"""
        result = {
            "lottery_type": "super",
            "lottery_name": "大樂透",
            "jackpot": jackpots.get("super") if jackpots else None,
            "draws": []
        }
        
        # 從 list.asp 抓開獎號碼
        list_html = self.fetch_page(self.SOURCES["lotto649"]["list_url"])
        if list_html:
            result["draws"] = self.parse_numbers_from_list(list_html, "super")
        
        return result if result["draws"] else None
    
    def fetch_daily_cash(self) -> Optional[Dict[str, Any]]:
        """抓取今彩539"""
        result = {
            "lottery_type": "daily539",
            "lottery_name": "今彩539",
            "jackpot": 8000000,  # 固定頭獎 800 萬
            "draws": []
        }
        
        # 從 list.asp 抓開獎號碼
        list_html = self.fetch_page(self.SOURCES["daily_cash"]["list_url"])
        if list_html:
            result["draws"] = self.parse_numbers_from_list(list_html, "daily539")
        
        return result if result["draws"] else None
    
    def fetch_all(self) -> Dict[str, Any]:
        """抓取所有彩種"""
        # 優先從台彩官網抓取累積獎金（更精確）
        jackpots = {
            "power": self.fetch_jackpot_from_taiwanlottery("power"),
            "super": self.fetch_jackpot_from_taiwanlottery("super"),
        }
        
        # 如果台彩官網失敗，備用 pilio 主頁
        if not jackpots["power"] or not jackpots["super"]:
            main_html = self.fetch_page(self.MAIN_PAGE)
            if main_html:
                pilio_jackpots = self.parse_all_jackpots_from_main(main_html)
                if not jackpots["power"]:
                    jackpots["power"] = pilio_jackpots.get("power")
                if not jackpots["super"]:
                    jackpots["super"] = pilio_jackpots.get("super")
        
        return {
            "updated_at": datetime.now().isoformat(),
            "super_lotto": self.fetch_super_lotto(jackpots),
            "lotto649": self.fetch_lotto649(jackpots),
            "daily_cash": self.fetch_daily_cash()
        }
    
    def get_latest(self, lottery_type: str) -> Optional[Dict[str, Any]]:
        """取得特定彩種最新一期"""
        # 優先從台彩官網抓取累積獎金
        jackpots = {}
        if lottery_type in ["power", "super"]:
            jackpots[lottery_type] = self.fetch_jackpot_from_taiwanlottery(lottery_type)
            
            # 備用 pilio
            if not jackpots.get(lottery_type):
                main_html = self.fetch_page(self.MAIN_PAGE)
                if main_html:
                    pilio_jackpots = self.parse_all_jackpots_from_main(main_html)
                    jackpots[lottery_type] = pilio_jackpots.get(lottery_type)
        
        if lottery_type == "power":
            data = self.fetch_super_lotto(jackpots)
        elif lottery_type == "super":
            data = self.fetch_lotto649(jackpots)
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
