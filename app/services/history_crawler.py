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
    
    # 正確的 URL
    HISTORY_URLS = {
        "power": "https://www.lotto-8.com/Taiwan/listlto.asp",         # 威力彩
        "super": "https://www.lotto-8.com/Taiwan/listltobig.asp",      # 大樂透
        "daily539": "https://www.lotto-8.com/Taiwan/listlto539.asp",   # 今彩539
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
        """
        解析日期字串
        格式: DD/MM YY(星期) -> 例如 08/01 26(四) = 2026-01-08
        """
        if not date_str:
            return None
        
        try:
            # 移除星期部分
            date_str = re.sub(r'\([一二三四五六日]\)', '', date_str).strip()
            
            # 解析 DD/MM YY 格式
            match = re.match(r'(\d{1,2})/(\d{1,2})\s+(\d{2})', date_str)
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = 2000 + int(match.group(3))  # 26 -> 2026
                return date(year, month, day)
            
            return None
        except Exception as e:
            logger.debug(f"日期解析失敗: {date_str} - {e}")
            return None
    
    def _parse_numbers(self, num_str: str) -> List[int]:
        """
        解析號碼字串
        格式: 07, 17, 25, 26, 27, 33
        """
        numbers = []
        if not num_str:
            return numbers
        
        # 用逗號或空格分割
        parts = re.split(r'[,\s]+', num_str.strip())
        for part in parts:
            part = part.strip()
            if part.isdigit():
                numbers.append(int(part))
        
        return numbers
    
    def fetch_power_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        爬取威力彩歷史資料
        
        威力彩: 6個主號 (1-38) + 1個第二區 (1-8)
        表格格式: 日期 | 開獎號碼 | 第2區
        """
        results = []
        html = self._fetch_page(self.HISTORY_URLS["power"])
        if not html:
            logger.error("無法取得威力彩頁面")
            return results
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # 找到資料表格
            tables = soup.find_all("table")
            
            for table in tables:
                rows = table.find_all("tr")
                
                for row in rows:
                    if len(results) >= limit:
                        break
                    
                    cells = row.find_all("td")
                    if len(cells) < 3:
                        continue
                    
                    # 取得各欄位文字
                    date_text = cells[0].get_text(strip=True)
                    numbers_text = cells[1].get_text(strip=True)
                    second_zone_text = cells[2].get_text(strip=True)
                    
                    # 跳過標題列
                    if "日期" in date_text or "開獎" in date_text:
                        continue
                    
                    # 解析日期
                    draw_date = self._parse_date(date_text)
                    if not draw_date:
                        continue
                    
                    # 解析號碼
                    first_zone = self._parse_numbers(numbers_text)
                    if len(first_zone) != 6:
                        continue
                    
                    # 解析第二區
                    second_zone = None
                    if second_zone_text.isdigit():
                        second_zone = int(second_zone_text)
                    
                    if second_zone is None:
                        continue
                    
                    draw_term = f"power_{draw_date.isoformat()}"
                    
                    results.append({
                        "lottery_type": "power",
                        "draw_term": draw_term,
                        "draw_date": draw_date,
                        "numbers": {
                            "first_zone": first_zone,
                            "second_zone": second_zone
                        },
                        "jackpot": None
                    })
                    logger.info(f"威力彩 {draw_date}: {first_zone} + {second_zone}")
        
        except Exception as e:
            logger.error(f"解析威力彩歷史頁面失敗: {e}")
        
        logger.info(f"威力彩共爬取 {len(results)} 筆")
        return results
    
    def fetch_super_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        爬取大樂透歷史資料
        
        大樂透: 6個主號 (1-49) + 1個特別號
        表格格式: 日期 | 開獎號碼 | 特
        """
        results = []
        html = self._fetch_page(self.HISTORY_URLS["super"])
        if not html:
            logger.error("無法取得大樂透頁面")
            return results
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            tables = soup.find_all("table")
            
            for table in tables:
                rows = table.find_all("tr")
                
                for row in rows:
                    if len(results) >= limit:
                        break
                    
                    cells = row.find_all("td")
                    if len(cells) < 3:
                        continue
                    
                    date_text = cells[0].get_text(strip=True)
                    numbers_text = cells[1].get_text(strip=True)
                    special_text = cells[2].get_text(strip=True)
                    
                    # 跳過標題列
                    if "日期" in date_text or "開獎" in date_text:
                        continue
                    
                    draw_date = self._parse_date(date_text)
                    if not draw_date:
                        continue
                    
                    main_numbers = self._parse_numbers(numbers_text)
                    if len(main_numbers) != 6:
                        continue
                    
                    special = None
                    if special_text.isdigit():
                        special = int(special_text)
                    
                    if special is None:
                        continue
                    
                    draw_term = f"super_{draw_date.isoformat()}"
                    
                    results.append({
                        "lottery_type": "super",
                        "draw_term": draw_term,
                        "draw_date": draw_date,
                        "numbers": {
                            "main": main_numbers,
                            "special": special
                        },
                        "jackpot": None
                    })
                    logger.info(f"大樂透 {draw_date}: {main_numbers} + {special}")
        
        except Exception as e:
            logger.error(f"解析大樂透歷史頁面失敗: {e}")
        
        logger.info(f"大樂透共爬取 {len(results)} 筆")
        return results
    
    def fetch_daily539_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        爬取今彩539歷史資料
        
        今彩539: 5個號碼 (1-39)
        表格格式: 日期 | 開獎號碼
        """
        results = []
        html = self._fetch_page(self.HISTORY_URLS["daily539"])
        if not html:
            logger.error("無法取得今彩539頁面")
            return results
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            tables = soup.find_all("table")
            
            for table in tables:
                rows = table.find_all("tr")
                
                for row in rows:
                    if len(results) >= limit:
                        break
                    
                    cells = row.find_all("td")
                    if len(cells) < 2:
                        continue
                    
                    date_text = cells[0].get_text(strip=True)
                    numbers_text = cells[1].get_text(strip=True)
                    
                    # 跳過標題列
                    if "日期" in date_text or "開獎" in date_text:
                        continue
                    
                    draw_date = self._parse_date(date_text)
                    if not draw_date:
                        continue
                    
                    numbers = self._parse_numbers(numbers_text)
                    if len(numbers) != 5:
                        continue
                    
                    draw_term = f"daily539_{draw_date.isoformat()}"
                    
                    results.append({
                        "lottery_type": "daily539",
                        "draw_term": draw_term,
                        "draw_date": draw_date,
                        "numbers": {
                            "numbers": numbers
                        },
                        "jackpot": None
                    })
                    logger.info(f"今彩539 {draw_date}: {numbers}")
        
        except Exception as e:
            logger.error(f"解析今彩539歷史頁面失敗: {e}")
        
        logger.info(f"今彩539共爬取 {len(results)} 筆")
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
