"""
SELA 樂透一路發 - 歷史開獎資料爬蟲
資料來源：樂透雲 (lotto-8.com)
"""
import re
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, date

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HistoryCrawler:
    """歷史開獎資料爬蟲"""
    
    # 樂透雲歷史資料頁面
    HISTORY_URLS = {
        "power": "https://www.lotto-8.com/listltosuperlotto638.asp",      # 威力彩
        "super": "https://www.lotto-8.com/listltobig.asp",                 # 大樂透
        "daily539": "https://www.lotto-8.com/listltodailycash.asp",       # 今彩539
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9",
    }
    
    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """抓取網頁"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.encoding = "utf-8"
            return response.text
        except Exception as e:
            logger.error(f"抓取失敗 {url}: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """解析日期字串"""
        if not date_str:
            return None
        
        # 清理字串
        date_str = date_str.strip()
        
        for fmt in ['%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None
    
    def fetch_power_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        爬取威力彩歷史資料
        
        威力彩: 6個主號 (1-38) + 1個第二區 (1-8)
        """
        results = []
        html = self._fetch_page(self.HISTORY_URLS["power"])
        if not html:
            return results
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 找到資料表格 - 通常是 class 包含 "ltotable" 或 id 包含某些關鍵字
            table = soup.find("table", {"class": re.compile(r".*tab.*", re.I)})
            if not table:
                tables = soup.find_all("table")
                for t in tables:
                    if t.find("tr") and len(t.find_all("tr")) > 5:
                        table = t
                        break
            
            if not table:
                logger.warning("找不到威力彩歷史資料表格")
                return results
            
            rows = table.find_all("tr")
            count = 0
            
            for row in rows:
                if count >= limit:
                    break
                
                cells = row.find_all("td")
                if len(cells) < 8:  # 需要至少: 期數、日期、6個號碼、1個第二區
                    continue
                
                try:
                    # 第一欄通常是期數，第二欄是日期
                    term_text = cells[0].get_text(strip=True)
                    date_text = cells[1].get_text(strip=True)
                    
                    # 解析日期
                    draw_date = self._parse_date(date_text)
                    if not draw_date:
                        continue
                    
                    # 解析號碼 - 從剩餘的欄位取得
                    numbers = []
                    for cell in cells[2:]:
                        num_text = cell.get_text(strip=True)
                        if num_text.isdigit():
                            numbers.append(int(num_text))
                    
                    if len(numbers) >= 7:
                        # 期數格式: power_YYYY-MM-DD
                        draw_term = f"power_{draw_date.isoformat()}"
                        
                        results.append({
                            "lottery_type": "power",
                            "draw_term": draw_term,
                            "draw_date": draw_date,
                            "numbers": {
                                "first_zone": sorted(numbers[:6]),
                                "second_zone": numbers[6]
                            },
                            "jackpot": None  # 歷史資料通常沒有獎金
                        })
                        count += 1
                        logger.info(f"威力彩 {draw_date}: {numbers[:6]} + {numbers[6]}")
                
                except Exception as e:
                    logger.debug(f"解析威力彩列失敗: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"解析威力彩歷史頁面失敗: {e}")
        
        return results
    
    def fetch_super_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        爬取大樂透歷史資料
        
        大樂透: 6個主號 (1-49) + 1個特別號
        """
        results = []
        html = self._fetch_page(self.HISTORY_URLS["super"])
        if not html:
            return results
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 找表格
            table = soup.find("table", {"class": re.compile(r".*tab.*", re.I)})
            if not table:
                tables = soup.find_all("table")
                for t in tables:
                    if t.find("tr") and len(t.find_all("tr")) > 5:
                        table = t
                        break
            
            if not table:
                logger.warning("找不到大樂透歷史資料表格")
                return results
            
            rows = table.find_all("tr")
            count = 0
            
            for row in rows:
                if count >= limit:
                    break
                
                cells = row.find_all("td")
                if len(cells) < 8:
                    continue
                
                try:
                    term_text = cells[0].get_text(strip=True)
                    date_text = cells[1].get_text(strip=True)
                    
                    draw_date = self._parse_date(date_text)
                    if not draw_date:
                        continue
                    
                    numbers = []
                    for cell in cells[2:]:
                        num_text = cell.get_text(strip=True)
                        if num_text.isdigit():
                            numbers.append(int(num_text))
                    
                    if len(numbers) >= 7:
                        draw_term = f"super_{draw_date.isoformat()}"
                        
                        results.append({
                            "lottery_type": "super",
                            "draw_term": draw_term,
                            "draw_date": draw_date,
                            "numbers": {
                                "main": sorted(numbers[:6]),
                                "special": numbers[6]
                            },
                            "jackpot": None
                        })
                        count += 1
                        logger.info(f"大樂透 {draw_date}: {numbers[:6]} + {numbers[6]}")
                
                except Exception as e:
                    logger.debug(f"解析大樂透列失敗: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"解析大樂透歷史頁面失敗: {e}")
        
        return results
    
    def fetch_daily539_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        爬取今彩539歷史資料
        
        今彩539: 5個號碼 (1-39)
        """
        results = []
        html = self._fetch_page(self.HISTORY_URLS["daily539"])
        if not html:
            return results
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 找表格
            table = soup.find("table", {"class": re.compile(r".*tab.*", re.I)})
            if not table:
                tables = soup.find_all("table")
                for t in tables:
                    if t.find("tr") and len(t.find_all("tr")) > 5:
                        table = t
                        break
            
            if not table:
                logger.warning("找不到今彩539歷史資料表格")
                return results
            
            rows = table.find_all("tr")
            count = 0
            
            for row in rows:
                if count >= limit:
                    break
                
                cells = row.find_all("td")
                if len(cells) < 7:  # 期數、日期、5個號碼
                    continue
                
                try:
                    term_text = cells[0].get_text(strip=True)
                    date_text = cells[1].get_text(strip=True)
                    
                    draw_date = self._parse_date(date_text)
                    if not draw_date:
                        continue
                    
                    numbers = []
                    for cell in cells[2:]:
                        num_text = cell.get_text(strip=True)
                        if num_text.isdigit():
                            numbers.append(int(num_text))
                    
                    if len(numbers) >= 5:
                        draw_term = f"daily539_{draw_date.isoformat()}"
                        
                        results.append({
                            "lottery_type": "daily539",
                            "draw_term": draw_term,
                            "draw_date": draw_date,
                            "numbers": {
                                "numbers": sorted(numbers[:5])
                            },
                            "jackpot": 8000000  # 今彩539 固定頭獎 800萬
                        })
                        count += 1
                        logger.info(f"今彩539 {draw_date}: {numbers[:5]}")
                
                except Exception as e:
                    logger.debug(f"解析今彩539列失敗: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"解析今彩539歷史頁面失敗: {e}")
        
        return results
    
    def fetch_all_history(self, limit: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """爬取所有彩種的歷史資料"""
        return {
            "power": self.fetch_power_history(limit),
            "super": self.fetch_super_history(limit),
            "daily539": self.fetch_daily539_history(limit),
        }


# 單例模式
history_crawler = HistoryCrawler()
