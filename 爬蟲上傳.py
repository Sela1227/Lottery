#!/usr/bin/env python3
"""
SELA 樂透一路發 - 本地歷史資料爬取上傳腳本 (Debug 版)
"""
import re
import requests
from datetime import date
from bs4 import BeautifulSoup


# ==================== 設定 ====================

API_BASE = "https://lottery-production-1edd.up.railway.app"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzY4NjQwNzM1LCJpYXQiOjE3NjgwMzU5MzUsImRpc3BsYXlfbmFtZSI6IlNlbGEiLCJyb2xlIjoiYWRtaW4ifQ.c9hZDfd_WwqtpHU6d6cyXwlGgnpG9Su3FtAqNi9tSTc"
LIMIT = 100


# ==================== 爬蟲 ====================

HISTORY_URLS = {
    "power": "https://www.lotto-8.com/Taiwan/listlto.asp",
    "super": "https://www.lotto-8.com/Taiwan/listltobig.asp", 
    "daily539": "https://www.lotto-8.com/Taiwan/listlto539.asp",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9",
}


def parse_date(date_str: str):
    """解析日期"""
    if not date_str:
        return None
    
    # 移除星期
    clean = re.sub(r'\([一二三四五六日]\)', '', date_str).strip()
    
    # 格式1: DD/MMYY (無空格) 例如 08/0126
    match = re.match(r'(\d{2})/(\d{2})(\d{2})', clean)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = 2000 + int(match.group(3))
        return date(year, month, day)
    
    # 格式2: DD/MM YY (有空格)
    match = re.match(r'(\d{1,2})/(\d{1,2})\s+(\d{2})', clean)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = 2000 + int(match.group(3))
        return date(year, month, day)
    
    return None


def parse_numbers(num_str: str) -> list:
    """解析號碼"""
    numbers = []
    if not num_str:
        return numbers
    
    parts = re.split(r'[,\s]+', num_str.strip())
    for part in parts:
        part = part.strip()
        if part.isdigit():
            numbers.append(int(part))
    
    return numbers


def fetch_power_history(limit: int = 30) -> list:
    """爬取威力彩"""
    print("🔴 爬取威力彩...")
    results = []
    
    try:
        response = requests.get(HISTORY_URLS["power"], headers=HEADERS, timeout=20)
        response.encoding = "utf-8"
        print(f"  HTTP 狀態: {response.status_code}")
        print(f"  內容長度: {len(response.text)} bytes")
        
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")
        print(f"  找到 {len(tables)} 個表格")
        
        for ti, table in enumerate(tables):
            rows = table.find_all("tr")
            print(f"  表格 {ti}: {len(rows)} 列")
            
            for ri, row in enumerate(rows):
                if len(results) >= limit:
                    break
                
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue
                
                date_text = cells[0].get_text(strip=True)
                numbers_text = cells[1].get_text(strip=True)
                second_zone_text = cells[2].get_text(strip=True)
                
                # Debug: 顯示前幾筆原始資料
                if ri < 5:
                    print(f"    列 {ri}: [{date_text}] [{numbers_text}] [{second_zone_text}]")
                
                # 跳過標題
                if "日期" in date_text or "開獎" in date_text or "威力彩" in numbers_text:
                    continue
                
                draw_date = parse_date(date_text)
                if not draw_date:
                    if ri < 5:
                        print(f"      -> 日期解析失敗")
                    continue
                
                first_zone = parse_numbers(numbers_text)
                if len(first_zone) != 6:
                    if ri < 5:
                        print(f"      -> 號碼數量錯誤: {len(first_zone)}")
                    continue
                
                # 第二區可能是 "03" 這種格式
                second_zone = None
                sz_clean = second_zone_text.strip().lstrip('0') or '0'
                if second_zone_text.strip().isdigit():
                    second_zone = int(second_zone_text.strip())
                
                if second_zone is None:
                    if ri < 5:
                        print(f"      -> 第二區解析失敗: '{second_zone_text}'")
                    continue
                
                results.append({
                    "lottery_type": "power",
                    "draw_term": f"power_{draw_date.isoformat()}",
                    "draw_date": draw_date.isoformat(),
                    "numbers": {
                        "first_zone": first_zone,
                        "second_zone": second_zone
                    },
                    "jackpot": None
                })
                print(f"  ✓ {draw_date}: {first_zone} + {second_zone}")
    
    except Exception as e:
        print(f"  ✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"  共 {len(results)} 筆")
    return results


def fetch_super_history(limit: int = 30) -> list:
    """爬取大樂透"""
    print("🔵 爬取大樂透...")
    results = []
    
    try:
        response = requests.get(HISTORY_URLS["super"], headers=HEADERS, timeout=20)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                if len(results) >= limit:
                    break
                
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue
                
                date_text = cells[0].get_text(strip=True)
                numbers_text = cells[1].get_text(strip=True)
                special_text = cells[2].get_text(strip=True)
                
                if "日期" in date_text or "開獎" in date_text or "大樂透" in numbers_text:
                    continue
                
                draw_date = parse_date(date_text)
                if not draw_date:
                    continue
                
                main_numbers = parse_numbers(numbers_text)
                if len(main_numbers) != 6:
                    continue
                
                if not special_text.strip().isdigit():
                    continue
                special = int(special_text.strip())
                
                results.append({
                    "lottery_type": "super",
                    "draw_term": f"super_{draw_date.isoformat()}",
                    "draw_date": draw_date.isoformat(),
                    "numbers": {
                        "main": main_numbers,
                        "special": special
                    },
                    "jackpot": None
                })
                print(f"  ✓ {draw_date}: {main_numbers} + {special}")
    
    except Exception as e:
        print(f"  ✗ 錯誤: {e}")
    
    print(f"  共 {len(results)} 筆")
    return results


def fetch_daily539_history(limit: int = 30) -> list:
    """爬取今彩539"""
    print("🟢 爬取今彩539...")
    results = []
    
    try:
        response = requests.get(HISTORY_URLS["daily539"], headers=HEADERS, timeout=20)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                if len(results) >= limit:
                    break
                
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue
                
                date_text = cells[0].get_text(strip=True)
                numbers_text = cells[1].get_text(strip=True)
                
                if "日期" in date_text or "開獎" in date_text or "今彩" in numbers_text:
                    continue
                
                draw_date = parse_date(date_text)
                if not draw_date:
                    continue
                
                numbers = parse_numbers(numbers_text)
                if len(numbers) != 5:
                    continue
                
                results.append({
                    "lottery_type": "daily539",
                    "draw_term": f"daily539_{draw_date.isoformat()}",
                    "draw_date": draw_date.isoformat(),
                    "numbers": {
                        "numbers": numbers
                    },
                    "jackpot": None
                })
                print(f"  ✓ {draw_date}: {numbers}")
    
    except Exception as e:
        print(f"  ✗ 錯誤: {e}")
    
    print(f"  共 {len(results)} 筆")
    return results


def upload_to_api(items: list) -> dict:
    """上傳到 API"""
    print(f"\n📤 上傳 {len(items)} 筆資料...")
    
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
            print(f"✅ {result['message']}")
            return result
        else:
            print(f"❌ 錯誤: {response.text[:200]}")
            return None
    
    except Exception as e:
        print(f"❌ 上傳失敗: {e}")
        return None


def main():
    print("=" * 50)
    print("SELA 樂透一路發 - 歷史資料匯入工具 (Debug)")
    print("=" * 50)
    print()
    
    all_items = []
    all_items.extend(fetch_power_history(LIMIT))
    all_items.extend(fetch_super_history(LIMIT))
    all_items.extend(fetch_daily539_history(LIMIT))
    
    print(f"\n📊 總共爬取 {len(all_items)} 筆資料")
    
    if not all_items:
        print("❌ 沒有爬取到任何資料")
        return
    
    result = upload_to_api(all_items)
    
    if result:
        print("\n" + "=" * 50)
        print("✅ 完成！")
        print("=" * 50)


if __name__ == "__main__":
    main()
