#!/usr/bin/env python3
"""快速測試台灣彩券 API 實際回傳內容"""
import ssl
import json
import requests
from requests.adapters import HTTPAdapter
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UnsafeSSLAdapter(HTTPAdapter):
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

session = requests.Session()
session.mount("https://api.taiwanlottery.com", UnsafeSSLAdapter())
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.taiwanlottery.com",
    "Referer": "https://www.taiwanlottery.com/",
})

BASE = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery"

# 測試三個 API
tests = [
    ("威力彩 2026-02", f"{BASE}/SuperLotto638Result?period&month=2026-02&pageSize=5"),
    ("威力彩 2026-01", f"{BASE}/SuperLotto638Result?period&month=2026-01&pageSize=5"),
    ("大樂透 2026-02", f"{BASE}/Lotto649Result?period&month=2026-02&pageSize=5"),
    ("今彩539 2026-02", f"{BASE}/Daily539Result?period&month=2026-02&pageSize=5"),
    ("威力彩 115-02 (民國)", f"{BASE}/SuperLotto638Result?period&month=115-02&pageSize=5"),
]

for name, url in tests:
    print(f"\n{'='*50}")
    print(f"🔍 {name}")
    print(f"   URL: {url}")
    print(f"{'='*50}")
    try:
        resp = session.get(url, timeout=15, verify=False)
        print(f"   HTTP: {resp.status_code}")
        print(f"   Content-Type: {resp.headers.get('content-type', '?')}")
        print(f"   長度: {len(resp.text)} bytes")
        
        # 嘗試 JSON
        try:
            data = resp.json()
            print(f"\n   📋 JSON 結構 (前 2000 字):")
            print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
        except:
            print(f"\n   📋 原始內容 (前 1000 字):")
            print(resp.text[:1000])
    except Exception as e:
        print(f"   ✗ {type(e).__name__}: {e}")

print("\n" + "="*50)
print("請把以上結果貼回給我")
