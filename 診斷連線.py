#!/usr/bin/env python3
"""連線診斷腳本 - 測試各種資料來源"""
import sys
print(f"Python: {sys.version}")
print(f"平台: {sys.platform}")
print()

import requests

TARGETS = [
    ("台灣彩券官方 API", "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/SuperLotto638Result?period&month=2026-02&pageSize=3"),
    ("台灣彩券官網", "https://www.taiwanlottery.com/"),
    ("中信彩券部", "https://lotto.ctbcbank.com/result_all.htm"),
    ("樂透雲 lotto-8", "https://www.lotto-8.com/Taiwan/main.asp"),
    ("Google (基本連線)", "https://www.google.com/"),
    ("SELA API", "https://lottery-develop.up.railway.app/api/v1/health"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-TW,zh;q=0.9",
}

for name, url in TARGETS:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, verify=True)
        size = len(resp.content)
        ct = resp.headers.get("content-type", "")[:40]
        print(f"✔ {name}")
        print(f"  HTTP {resp.status_code} | {size} bytes | {ct}")
        
        # 如果是 JSON，顯示一部分
        if "json" in ct.lower():
            try:
                data = resp.json()
                total = data.get("content", {}).get("totalSize", "?")
                print(f"  JSON 內容: totalSize={total}")
            except:
                pass
    except requests.exceptions.SSLError as e:
        print(f"✗ {name}")
        print(f"  SSL 錯誤: {e}")
    except requests.exceptions.ProxyError as e:
        print(f"✗ {name}")
        print(f"  Proxy 錯誤: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"✗ {name}")
        print(f"  連線失敗: {e}")
    except requests.exceptions.Timeout:
        print(f"✗ {name}")
        print(f"  逾時 (10秒)")
    except Exception as e:
        print(f"✗ {name}")
        print(f"  {type(e).__name__}: {e}")
    print()

print("─" * 50)
print("請把以上結果貼回給我，我會根據結果調整腳本")
