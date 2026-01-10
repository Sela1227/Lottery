"""
SELA 樂透一路發 - 彩券開獎資訊爬蟲服務
資料來源：樂透雲 (lotto-8.com)
"""
import re
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LotteryCrawler:
    """彩券開獎資訊爬蟲 - 使用樂透雲資料來源"""
    
    # 樂透雲主頁 - 包含所有彩種的最新開獎資訊
    LOTTO8_MAIN = "https://www.lotto-8.com/Taiwan/main.asp"
    
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
    
    def _parse_lotto8_main(self, html: str) -> Dict[str, Any]:
        """
        解析樂透雲主頁，一次取得所有彩種資料
        
        格式範例：
        威力彩
        累積彩金NT: 480000000
        2026/01/08 最新開獎號
        07 | 17 | 25 | 26 | 27 | 33 | 03
        """
        result = {
            "power": {"jackpot": None, "date": None, "numbers": None},
            "super": {"jackpot": None, "date": None, "numbers": None},
            "daily539": {"jackpot": 8000000, "date": None, "numbers": None},
        }
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 取得所有表格
            tables = soup.find_all("table")
            
            for table in tables:
                text = table.get_text()
                
                # === 威力彩 ===
                if "威力彩" in text and "累積彩金NT" in text:
                    # 累積獎金 - 匹配數字後面跟空白或換行
                    jackpot_match = re.search(r'累積彩金NT:\s*(\d+)(?=[\s\n])', text)
                    if jackpot_match:
                        result["power"]["jackpot"] = int(jackpot_match.group(1))
                        logger.info(f"威力彩累積獎金: {result['power']['jackpot']}")
                    
                    # 日期
                    date_match = re.search(r'(\d{4}/\d{2}/\d{2})\s*最新開獎號', text)
                    if date_match:
                        date_str = date_match.group(1).replace("/", "-")
                        result["power"]["date"] = date_str
                    
                    # 號碼 - 從表格 td 中找
                    cells = table.find_all("td")
                    numbers = []
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        if cell_text.isdigit() and len(cell_text) <= 2:
                            numbers.append(int(cell_text))
                    
                    if len(numbers) >= 7:
                        result["power"]["numbers"] = {
                            "first_zone": numbers[:6],
                            "second_zone": numbers[6]
                        }
                        logger.info(f"威力彩號碼: {result['power']['numbers']}")
                
                # === 大樂透 ===
                elif "大樂透" in text and "累積彩金NT" in text:
                    # 累積獎金 - 匹配數字後面跟空白或換行
                    jackpot_match = re.search(r'累積彩金NT:\s*(\d+)(?=[\s\n])', text)
                    if jackpot_match:
                        result["super"]["jackpot"] = int(jackpot_match.group(1))
                        logger.info(f"大樂透累積獎金: {result['super']['jackpot']}")
                    
                    # 日期
                    date_match = re.search(r'(\d{4}/\d{2}/\d{2})\s*最新開獎號', text)
                    if date_match:
                        date_str = date_match.group(1).replace("/", "-")
                        result["super"]["date"] = date_str
                    
                    # 號碼
                    cells = table.find_all("td")
                    numbers = []
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        if cell_text.isdigit() and len(cell_text) <= 2:
                            numbers.append(int(cell_text))
                    
                    if len(numbers) >= 7:
                        result["super"]["numbers"] = {
                            "main": numbers[:6],
                            "special": numbers[6]
                        }
                        logger.info(f"大樂透號碼: {result['super']['numbers']}")
                
                # === 今彩539 ===
                elif "今彩539" in text and "最新開獎號" in text and "累積彩金" not in text:
                    # 日期
                    date_match = re.search(r'(\d{4}/\d{2}/\d{2})\s*最新開獎號', text)
                    if date_match:
                        date_str = date_match.group(1).replace("/", "-")
                        result["daily539"]["date"] = date_str
                    
                    # 號碼
                    cells = table.find_all("td")
                    numbers = []
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        if cell_text.isdigit() and len(cell_text) <= 2:
                            numbers.append(int(cell_text))
                    
                    if len(numbers) >= 5:
                        result["daily539"]["numbers"] = numbers[:5]
                        logger.info(f"今彩539號碼: {result['daily539']['numbers']}")
        
        except Exception as e:
            logger.error(f"解析樂透雲主頁失敗: {e}")
        
        return result
    
    def fetch_all(self) -> Dict[str, Any]:
        """抓取所有彩種資料"""
        
        # 從樂透雲主頁一次抓取所有資料
        html = self._fetch_page(self.LOTTO8_MAIN)
        if not html:
            return {"updated_at": datetime.now().isoformat()}
        
        data = self._parse_lotto8_main(html)
        
        # 組裝結果
        result = {
            "updated_at": datetime.now().isoformat(),
        }
        
        # 威力彩
        if data["power"]["numbers"]:
            result["super_lotto"] = {
                "lottery_type": "power",
                "lottery_name": "威力彩",
                "jackpot": data["power"]["jackpot"],
                "draws": [{
                    "draw_date": data["power"]["date"],
                    "numbers": data["power"]["numbers"]
                }]
            }
        
        # 大樂透
        if data["super"]["numbers"]:
            result["lotto649"] = {
                "lottery_type": "super",
                "lottery_name": "大樂透",
                "jackpot": data["super"]["jackpot"],
                "draws": [{
                    "draw_date": data["super"]["date"],
                    "numbers": data["super"]["numbers"]
                }]
            }
        
        # 今彩539
        if data["daily539"]["numbers"]:
            result["daily_cash"] = {
                "lottery_type": "daily539",
                "lottery_name": "今彩539",
                "jackpot": data["daily539"]["jackpot"],
                "draws": [{
                    "draw_date": data["daily539"]["date"],
                    "numbers": data["daily539"]["numbers"]
                }]
            }
        
        return result
    
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
