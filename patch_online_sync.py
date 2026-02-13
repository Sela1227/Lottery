#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELA 重構：線上同步改用台灣彩券官方 API
日期：2026-02-13

修改檔案：
  1. app/services/lottery_crawler.py → 完整重寫，改用官方 API
  2. app/api/v1/lottery.py → 更新 sync 端點
  3. static/admin_lottery.html → 簡化為單一同步按鈕

效果：管理員在後台按「同步」就能直接抓最新開獎 + 歷史資料
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
changes = 0

# ===================================================================
# 1. 重寫 lottery_crawler.py
# ===================================================================
CRAWLER_FILE = os.path.join(BASE, "app", "services", "lottery_crawler.py")

NEW_CRAWLER = '''"""
SELA \u6a02\u900f\u4e00\u8def\u767c - \u5f69\u5238\u958b\u734e\u8cc7\u8a0a\u722c\u87f2\u670d\u52d9
\u8cc7\u6599\u4f86\u6e90\uff1a\u53f0\u7063\u5f69\u5238\u5b98\u65b9 API (api.taiwanlottery.com)
"""
import ssl
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, date

import requests
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)


class UnsafeSSLAdapter(HTTPAdapter):
    """\u8df3\u904e SSL \u9a57\u8b49\uff08\u53f0\u5f69\u6191\u8b49\u554f\u984c\uff09"""
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


class LotteryCrawler:
    """\u5f69\u5238\u958b\u734e\u8cc7\u8a0a - \u53f0\u7063\u5f69\u5238\u5b98\u65b9 API"""

    TLC_API = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Origin": "https://www.taiwanlottery.com",
        "Referer": "https://www.taiwanlottery.com/",
    }

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        adapter = UnsafeSSLAdapter()
        self.session.mount("https://api.taiwanlottery.com", adapter)

    def _api_get(self, url: str) -> Optional[dict]:
        try:
            resp = self.session.get(url, timeout=self.timeout, verify=False)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"\\u53f0\\u5f69 API \\u5931\\u6557: {url} -> {e}")
            return None

    def _parse_date(self, date_str: str) -> Optional[str]:
        if not date_str:
            return None
        date_str = date_str.strip().split("T")[0]
        parts = date_str.replace("-", "/").split("/")
        if len(parts) == 3:
            try:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                if y < 200:
                    y += 1911
                return date(y, m, d).isoformat()
            except (ValueError, TypeError):
                pass
        return None

    def fetch_power(self, year: int, month: int) -> List[dict]:
        url = f"{self.TLC_API}/SuperLotto638Result?period&month={year}-{month:02d}&pageSize=50"
        data = self._api_get(url)
        if not data:
            return []
        results = []
        for item in data.get("content", {}).get("superLotto638Res", []):
            numbers = item.get("drawNumberSize", [])
            if len(numbers) < 7:
                continue
            draw_date = self._parse_date(item.get("lotteryDate", ""))
            if not draw_date:
                continue
            period = item.get("period", "")
            jp_assign = item.get("super638JackpotAssign", {})
            jp = (jp_assign.get("prize", 0) or 0) + (jp_assign.get("lastPrize", 0) or 0) or None
            results.append({
                "lottery_type": "power",
                "draw_term": str(period) if period else f"power_{draw_date}",
                "draw_date": draw_date,
                "numbers": {"first_zone": [int(n) for n in numbers[:6]], "second_zone": int(numbers[6])},
                "jackpot": jp,
            })
        return results

    def fetch_super(self, year: int, month: int) -> List[dict]:
        url = f"{self.TLC_API}/Lotto649Result?period&month={year}-{month:02d}&pageSize=50"
        data = self._api_get(url)
        if not data:
            return []
        results = []
        for item in data.get("content", {}).get("lotto649Res", []):
            numbers = item.get("drawNumberSize", [])
            if len(numbers) < 7:
                continue
            draw_date = self._parse_date(item.get("lotteryDate", ""))
            if not draw_date:
                continue
            period = item.get("period", "")
            jp_assign = item.get("jackpotAssign", {})
            jp = (jp_assign.get("prize", 0) or 0) + (jp_assign.get("lastPrize", 0) or 0) or None
            results.append({
                "lottery_type": "super",
                "draw_term": str(period) if period else f"super_{draw_date}",
                "draw_date": draw_date,
                "numbers": {"main": [int(n) for n in numbers[:6]], "special": int(numbers[6])},
                "jackpot": jp,
            })
        return results

    def fetch_daily539(self, year: int, month: int) -> List[dict]:
        url = f"{self.TLC_API}/Daily539Result?period&month={year}-{month:02d}&pageSize=50"
        data = self._api_get(url)
        if not data:
            return []
        results = []
        for item in data.get("content", {}).get("daily539Res", []):
            numbers = item.get("drawNumberSize", [])
            if len(numbers) < 5:
                continue
            draw_date = self._parse_date(item.get("lotteryDate", ""))
            if not draw_date:
                continue
            period = item.get("period", "")
            results.append({
                "lottery_type": "daily539",
                "draw_term": str(period) if period else f"daily539_{draw_date}",
                "draw_date": draw_date,
                "numbers": {"numbers": [int(n) for n in numbers[:5]]},
                "jackpot": 8000000,
            })
        return results

    def fetch_current_month(self) -> List[dict]:
        """\\u6293\\u53d6\\u7576\\u6708\\u6240\\u6709\\u5f69\\u7a2e"""
        now = datetime.now()
        y, m = now.year, now.month
        all_items = []
        all_items.extend(self.fetch_power(y, m))
        all_items.extend(self.fetch_super(y, m))
        all_items.extend(self.fetch_daily539(y, m))
        return all_items

    def fetch_months(self, months_back: int = 2) -> List[dict]:
        """\\u6293\\u53d6\\u6700\\u8fd1 N \\u500b\\u6708"""
        all_items = []
        today = date.today()
        for i in range(months_back):
            y, m = today.year, today.month - i
            while m <= 0:
                m += 12
                y -= 1
            all_items.extend(self.fetch_power(y, m))
            all_items.extend(self.fetch_super(y, m))
            all_items.extend(self.fetch_daily539(y, m))
        return all_items

    # === \\u76f8\\u5bb9\\u820a\\u4ecb\\u9762 ===
    def fetch_all(self) -> Dict[str, Any]:
        """\\u76f8\\u5bb9\\u820a sync endpoint"""
        items = self.fetch_current_month()
        return {"items": items, "updated_at": datetime.now().isoformat()}

    def get_latest(self, lottery_type: str) -> Optional[Dict[str, Any]]:
        now = datetime.now()
        if lottery_type == "power":
            items = self.fetch_power(now.year, now.month)
        elif lottery_type == "super":
            items = self.fetch_super(now.year, now.month)
        elif lottery_type == "daily539":
            items = self.fetch_daily539(now.year, now.month)
        else:
            return None
        if not items:
            return None
        latest = items[0]
        names = {"power": "\\u5a01\\u529b\\u5f69", "super": "\\u5927\\u6a02\\u900f", "daily539": "\\u4eca\\u5f69539"}
        return {
            "lottery_type": lottery_type,
            "lottery_name": names.get(lottery_type, lottery_type),
            "jackpot": latest.get("jackpot"),
            "latest_draw": {
                "draw_date": latest["draw_date"],
                "draw_term": latest["draw_term"],
                "numbers": latest["numbers"],
            }
        }


lottery_crawler = LotteryCrawler()
'''

os.makedirs(os.path.dirname(CRAWLER_FILE), exist_ok=True)
if os.path.exists(CRAWLER_FILE):
    with open(CRAWLER_FILE, "r", encoding="utf-8") as f:
        backup_content = f.read()
    with open(CRAWLER_FILE + ".bak", "w", encoding="utf-8") as f:
        f.write(backup_content)

with open(CRAWLER_FILE, "w", encoding="utf-8") as f:
    f.write(NEW_CRAWLER)
changes += 1
print("  ✅ lottery_crawler.py 完整重寫（台灣彩券官方 API）")


# ===================================================================
# 2. 更新 sync endpoint（lottery.py 中的 sync_lottery_data）
# ===================================================================
LOTTERY_FILE = os.path.join(BASE, "app", "api", "v1", "lottery.py")

if os.path.exists(LOTTERY_FILE):
    with open(LOTTERY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 用 brace counting 找到 sync_lottery_data 函式並替換
    FUNC_MARKER = "async def sync_lottery_data("
    NEW_SYNC = '''async def sync_lottery_data(
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):
    """
    \u540c\u6b65\u6240\u6709\u5f69\u7a2e\u958b\u734e\u8cc7\u6599\uff08\u7ba1\u7406\u54e1\uff09
    \u5f9e\u53f0\u7063\u5f69\u5238\u5b98\u65b9 API \u6293\u53d6\u7576\u6708+\u4e0a\u6708\u8cc7\u6599
    """
    try:
        items = lottery_crawler.fetch_months(2)

        if not items:
            return SyncResult(
                success=False,
                message="\u7121\u6cd5\u9023\u7dda\u53f0\u7063\u5f69\u5238 API\uff0c\u8acb\u7a0d\u5f8c\u518d\u8a66",
                updated_at=datetime.now().isoformat()
            )

        imported = 0
        updated = 0
        skipped = 0

        for item in items:
            try:
                existing = db.query(LotteryDraw).filter(
                    LotteryDraw.lottery_type == item["lottery_type"],
                    LotteryDraw.draw_term == item["draw_term"]
                ).first()

                if existing:
                    changed = False
                    if item.get("jackpot") and existing.jackpot != item["jackpot"]:
                        existing.jackpot = item["jackpot"]
                        changed = True
                    if item.get("numbers") and existing.numbers != item["numbers"]:
                        existing.numbers = item["numbers"]
                        changed = True
                    if changed:
                        updated += 1
                    else:
                        skipped += 1
                    continue

                draw_date = parse_date(item["draw_date"])
                new_draw = LotteryDraw(
                    lottery_type=item["lottery_type"],
                    draw_term=item["draw_term"],
                    draw_date=draw_date,
                    numbers=item["numbers"],
                    jackpot=item.get("jackpot")
                )
                db.add(new_draw)
                imported += 1
            except Exception as e:
                logger.error(f"\u540c\u6b65\u55ae\u7b46\u5931\u6557 {item.get('draw_term')}: {e}")

        db.commit()

        # \u81ea\u52d5\u5c0d\u734e
        auto_check_result = None
        if HAS_AUTO_CHECK and (imported > 0 or updated > 0):
            try:
                auto_check_result = auto_check_service.auto_check_all_pending(db)
            except Exception as e:
                logger.error(f"\u81ea\u52d5\u5c0d\u734e\u5931\u6557: {e}")

        power_count = sum(1 for i in items if i["lottery_type"] == "power")
        super_count = sum(1 for i in items if i["lottery_type"] == "super")
        daily_count = sum(1 for i in items if i["lottery_type"] == "daily539")

        msg = f"\u540c\u6b65\u5b8c\u6210\uff01\u65b0\u589e {imported} \u7b46\u3001\u66f4\u65b0 {updated} \u7b46\u3001\u8df3\u904e {skipped} \u7b46\\n"
        msg += f"\u5a01\u529b\u5f69 {power_count} \u7b46\u3001\u5927\u6a02\u900f {super_count} \u7b46\u3001\u4eca\u5f69539 {daily_count} \u7b46"

        return SyncResult(
            success=True,
            message=msg,
            updated_at=datetime.now().isoformat(),
            auto_check_result=auto_check_result
        )

    except Exception as e:
        logger.error(f"\u540c\u6b65\u5931\u6557: {e}")
        return SyncResult(
            success=False,
            message=f"\u540c\u6b65\u5931\u6557: {str(e)}",
            updated_at=datetime.now().isoformat()
        )'''

    idx = content.find(FUNC_MARKER)
    if idx >= 0:
        # 找到裝飾器開頭
        decorator_start = content.rfind("@router.", 0, idx)
        if decorator_start < 0:
            decorator_start = idx

        # brace counting 找函式結尾
        brace_start = content.index("{", idx) if "{" in content[idx:idx+500] else -1
        # 用 try/except/return 的縮排來找結尾
        # 找下一個 @router 或 def 或文件結尾
        func_end = len(content)
        search_start = idx + 100
        for marker in ["@router.", "\ndef ", "\nasync def "]:
            pos = content.find(marker, search_start)
            if pos > 0 and pos < func_end:
                func_end = pos

        # 保留裝飾器
        decorator_line = content[decorator_start:idx]

        content = content[:decorator_start] + decorator_line + NEW_SYNC + "\n\n" + content[func_end:]
        changes += 1
        print("  ✅ sync_lottery_data 端點重寫")
    else:
        print("  ⚠️  找不到 sync_lottery_data，跳過")

    # 加入 logger import（如果沒有）
    if "import logging" not in content and "logger" in content:
        content = "import logging\n" + content
        # 在 import 後加 logger
        if "logger = logging.getLogger" not in content:
            content = content.replace("import logging\n", "import logging\nlogger = logging.getLogger(__name__)\n")
        changes += 1
        print("  ✅ 加入 logging import")

    with open(LOTTERY_FILE, "w", encoding="utf-8") as f:
        f.write(content)


# ===================================================================
# 3. 簡化 admin_lottery.html
# ===================================================================
ADMIN_LOTTERY = os.path.join(BASE, "static", "admin_lottery.html")

if os.path.exists(ADMIN_LOTTERY):
    with open(ADMIN_LOTTERY, "r", encoding="utf-8") as f:
        old_admin = f.read()
    with open(ADMIN_LOTTERY + ".bak", "w", encoding="utf-8") as f:
        f.write(old_admin)

    NEW_ADMIN_PAGE = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SELA - \u958b\u734e\u8cc7\u8a0a\u540c\u6b65</title>
    <style>
        :root { --sela-orange: #FA7A35; --sela-gradient: linear-gradient(135deg, #FA7A35, #FF9A5C); }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f5f5; color: #333; }
        .header { background: var(--sela-gradient); color: white; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 18px; }
        .back-btn { color: white; text-decoration: none; font-size: 14px; background: rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 8px; }
        .main { padding: 16px; max-width: 600px; margin: 0 auto; }
        .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .sync-btn { width: 100%; padding: 16px; background: var(--sela-gradient); color: white; border: none; border-radius: 12px; font-size: 18px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .sync-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .sync-btn .spinner { display: none; width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 1s linear infinite; }
        .sync-btn.loading .spinner { display: inline-block; }
        .sync-btn.loading .btn-text { display: none; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .result { margin-top: 16px; padding: 16px; border-radius: 10px; display: none; }
        .result.success { display: block; background: #f0fdf4; border: 1px solid #86efac; color: #166534; }
        .result.error { display: block; background: #fef2f2; border: 1px solid #fca5a5; color: #991b1b; }
        .result pre { white-space: pre-wrap; font-size: 14px; margin-top: 8px; }
        .section-title { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
        .info-text { font-size: 14px; color: #666; line-height: 1.6; }
        .draws-container { margin-top: 12px; }
        .draw-type { font-weight: 600; font-size: 15px; margin: 12px 0 6px; }
        .draw-type:first-child { margin-top: 0; }
        .draw-item { font-size: 14px; color: #555; padding: 4px 0; }
        .recent-title { display: flex; justify-content: space-between; align-items: center; }
    </style>
</head>
<body>
    <header class="header">
        <h1>📊 \u958b\u734e\u8cc7\u8a0a\u540c\u6b65</h1>
        <a href="/admin" class="back-btn">\u2190 \u8fd4\u56de\u7ba1\u7406</a>
    </header>

    <main class="main">
        <div class="card">
            <div class="section-title">\u540c\u6b65\u958b\u734e\u8cc7\u6599</div>
            <p class="info-text">\u5f9e\u53f0\u7063\u5f69\u5238\u5b98\u65b9 API \u6293\u53d6\u6700\u8fd1 2 \u500b\u6708\u7684\u958b\u734e\u865f\u78bc\u8207\u734e\u91d1\u8cc7\u6599\uff0c\u81ea\u52d5\u5132\u5b58\u4e26\u89f8\u767c\u5c0d\u734e\u3002</p>
            <button class="sync-btn" id="sync-btn" onclick="doSync()">
                <span class="spinner"></span>
                <span class="btn-text">🔄 \u7acb\u5373\u540c\u6b65</span>
                <span class="loading-text" style="display:none">\u540c\u6b65\u4e2d...</span>
            </button>
            <div class="result" id="result"></div>
        </div>

        <div class="card">
            <div class="recent-title">
                <span class="section-title">\u8cc7\u6599\u5eab\u73fe\u6709\u8cc7\u6599</span>
                <span id="draw-count" style="font-size:14px;color:#999;"></span>
            </div>
            <div class="draws-container" id="recent-draws">
                <div class="info-text">\u8f09\u5165\u4e2d...</div>
            </div>
        </div>
    </main>

    <script src="/static/js/common.js"></script>
    <script>
        function getToken() {
            return localStorage.getItem('token') || new URLSearchParams(location.search).get('token');
        }

        async function api(url, options = {}) {
            const token = getToken();
            const headers = { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', ...(options.headers || {}) };
            return fetch('/api/v1' + url, { ...options, headers });
        }

        async function doSync() {
            const btn = document.getElementById('sync-btn');
            const result = document.getElementById('result');
            btn.classList.add('loading');
            btn.querySelector('.btn-text').style.display = 'none';
            btn.querySelector('.loading-text').style.display = 'inline';
            btn.disabled = true;
            result.className = 'result';
            result.style.display = 'none';

            try {
                const resp = await api('/lottery/sync', { method: 'POST' });
                const data = await resp.json();

                if (resp.ok && data.success) {
                    result.className = 'result success';
                    result.innerHTML = '<strong>\u2705 ' + data.message.replace('\\n', '<br>') + '</strong>';
                    if (data.auto_check_result) {
                        result.innerHTML += '<pre>\u5c0d\u734e: ' + JSON.stringify(data.auto_check_result) + '</pre>';
                    }
                } else {
                    result.className = 'result error';
                    result.innerHTML = '<strong>\u274c ' + (data.message || data.detail || '\u540c\u6b65\u5931\u6557') + '</strong>';
                }
            } catch (e) {
                result.className = 'result error';
                result.innerHTML = '<strong>\u274c \u7db2\u8def\u932f\u8aa4: ' + e.message + '</strong>';
            } finally {
                btn.classList.remove('loading');
                btn.querySelector('.btn-text').style.display = 'inline';
                btn.querySelector('.loading-text').style.display = 'none';
                btn.disabled = false;
                loadRecentDraws();
            }
        }

        async function loadRecentDraws() {
            const container = document.getElementById('recent-draws');
            const countEl = document.getElementById('draw-count');
            try {
                let total = 0;
                let html = '';
                for (const [type, name] of [['power', '🔴 \u5a01\u529b\u5f69'], ['super', '🔵 \u5927\u6a02\u900f'], ['daily539', '🟢 \u4eca\u5f69539']]) {
                    const resp = await api('/lottery/history/' + type + '?limit=3');
                    if (!resp.ok) continue;
                    const data = await resp.json();
                    const items = data.items || [];
                    total += data.total_count || 0;
                    html += '<div class="draw-type">' + name + ' (' + (data.total_count || 0) + ' \u7b46)</div>';
                    if (items.length === 0) {
                        html += '<div class="draw-item">\u5c1a\u7121\u8cc7\u6599</div>';
                    } else {
                        for (const d of items) {
                            const jp = d.jackpot_display ? ' \u00b7 \u982d\u734e ' + d.jackpot_display : '';
                            html += '<div class="draw-item">' + (d.draw_term || '-') + ' \u00b7 ' + (d.draw_date || '') + jp + '</div>';
                        }
                    }
                }
                container.innerHTML = html;
                countEl.textContent = '\u5171 ' + total + ' \u7b46';
            } catch (e) {
                container.innerHTML = '<div class="info-text">\u8f09\u5165\u5931\u6557</div>';
            }
        }

        loadRecentDraws();
    </script>
</body>
</html>'''

    with open(ADMIN_LOTTERY, "w", encoding="utf-8") as f:
        f.write(NEW_ADMIN_PAGE)
    changes += 1
    print("  ✅ admin_lottery.html 簡化（單一同步按鈕）")
else:
    print(f"  ⚠️  找不到 {ADMIN_LOTTERY}")


print(f"\n🎉 完成！共 {changes} 項變更")
print("\n📌 部署步驟：")
print("   git add app/services/lottery_crawler.py app/api/v1/lottery.py static/admin_lottery.html")
print('   git commit -m "feat: 開獎同步改用台灣彩券官方API，管理頁面簡化"')
print("   git push")
print("\n   部署後到 /admin/lottery 按「立即同步」測試")
