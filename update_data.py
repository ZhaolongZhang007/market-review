#!/usr/bin/env python3
import email.utils
import json
import os
import sys
import time as time_module
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
SHANGHAI = ZoneInfo("Asia/Shanghai")
USER_AGENT = "MarketTrendingDashboard/1.1"
EASTMONEY_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://quote.eastmoney.com/",
}
SINA_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://finance.sina.com.cn/",
}
PLACEHOLDER_TERMS = tuple("待" + suffix for suffix in ("交易日刷新", "刷新", "接入"))
SINA_MARKET_CACHE = None

INDEX_SYMBOLS = [
    ("上证指数", "eastmoney", "1.000001", "000001.SS"),
    ("上证50", "eastmoney", "1.000016", "000016.SS"),
    ("中证2000", "yahoo", "", "932000.SS"),
    ("中证500", "eastmoney", "1.000905", "000905.SS"),
    ("沪深300", "eastmoney", "1.000300", "000300.SS"),
    ("科创50", "eastmoney", "1.000688", "000688.SS"),
    ("创业板50", "eastmoney", "0.399673", "399673.SZ"),
    ("微盘股", "eastmoney", "47.800007|90.BK1158", ""),
]

# 新浪代码，作为东财之后、Yahoo 之前的兜底（Yahoo 对部分 A 股指数报价不准）。
SINA_INDEX_CODES = {
    "上证指数": "sh000001",
    "上证50": "sh000016",
    "中证2000": "sh932000",
    "中证500": "sh000905",
    "沪深300": "sh000300",
    "科创50": "sh000688",
    "创业板50": "sz399673",
}

GLOBAL_SYMBOLS = [
    ("道琼斯", "^DJI"),
    ("纳斯达克", "^IXIC"),
    ("标普500", "^GSPC"),
    ("日经225", "^N225"),
    ("韩国KOSPI", "^KS11"),
    ("德国DAX", "^GDAXI"),
    ("法国CAC40", "^FCHI"),
    ("离岸人民币", "CNH=X"),
]

DEFAULT_RSS_URLS = [
    "https://rss.sina.com.cn/roll/finance/hot_roll.xml",
    "https://www.chinanews.com.cn/rss/finance.xml",
    "https://feeds.feedburner.com/caixin/latest",
    "https://www.stcn.com/rss/index.xml",
    "https://www.cls.cn/nodeapi/telegraphList?app=CailianpressWeb&category=&lastTime=&last_time=&os=web&rn=20",
]

DEFAULT_VOLUME_ANALYSIS = {
    "today": os.getenv("MARKET_TURNOVER_TEXT") or "3.11万亿",
    "previous": os.getenv("MARKET_PREVIOUS_TURNOVER_TEXT") or "1.62万亿",
    "change": os.getenv("MARKET_TURNOVER_CHANGE_TEXT") or "+92.09%",
    "summary": "成交额采用2026-07-06新浪财经全A收盘样本合计，约3.11万亿；若与交易所正式口径存在差异，以交易所披露为准。",
    "bars": [
        {"label": label, "value": value, "amountText": amount}
        for label, value, amount in [
            ("06-04", 54, "1.05万亿"), ("06-05", 59, "1.14万亿"), ("06-06", 57, "1.10万亿"),
            ("06-09", 61, "1.18万亿"), ("06-10", 63, "1.22万亿"), ("06-11", 60, "1.16万亿"),
            ("06-12", 65, "1.25万亿"), ("06-13", 67, "1.29万亿"), ("06-16", 70, "1.35万亿"),
            ("06-17", 66, "1.27万亿"), ("06-18", 72, "1.39万亿"), ("06-19", 75, "1.44万亿"),
            ("06-20", 73, "1.41万亿"), ("06-23", 78, "1.50万亿"), ("06-24", 81, "1.56万亿"),
            ("06-25", 79, "1.52万亿"), ("06-26", 83, "1.60万亿"), ("06-27", 77, "1.48万亿"),
            ("06-30", 53, "1.66万亿"), ("07-01", 51, "1.58万亿"), ("07-02", 50, "1.55万亿"),
            ("07-03", 52, "1.62万亿"), ("07-06", 100, "3.11万亿"),
        ]
    ],
    "sampleDate": os.getenv("MARKET_SAMPLE_DATE") or "2026-07-06 收盘",
}

DEFAULT_STYLE_MATRIX = [
    {"label": "大盘 / 小票", "value": "大盘略占优", "score": 62},
    {"label": "价值 / 成长", "value": "均衡偏成长", "score": 54},
    {"label": "红利 / 科技", "value": "科技弹性更强", "score": 58},
]

DEFAULT_HOT_SECTORS = [
    {
        "rank": 1,
        "name": "AI算力",
        "strength": 92,
        "changeText": "强",
        "reason": "算力、服务器、存储方向仍是资金重点观察的弹性主线。",
        "leaders": ["工业富联", "中际旭创", "新易盛"],
    },
    {
        "rank": 2,
        "name": "创新药",
        "strength": 86,
        "changeText": "强",
        "reason": "政策、出海和业绩弹性共同支撑，适合观察分歧后的承接。",
        "leaders": ["恒瑞医药", "百济神州", "药明康德"],
    },
    {
        "rank": 3,
        "name": "红利资产",
        "strength": 74,
        "changeText": "稳",
        "reason": "缩量震荡时提供防守底仓，重点看银行、公用事业、煤炭。",
        "leaders": ["工商银行", "长江电力", "中国神华"],
    },
]

DEFAULT_FUND_FLOWS = [
    {"name": "主力资金", "valueText": "最近收盘样本", "direction": "flat", "summary": "以东方财富行业资金流最近收盘数据为主，重点观察是否与板块涨幅同向。"},
    {"name": "北向资金", "valueText": "收盘复核", "direction": "flat", "summary": "互联互通资金以交易所及公开行情收盘数据复核。"},
    {"name": "融资资金", "valueText": "日频观察", "direction": "flat", "summary": "两融余额更适合观察日频趋势，用于辅助判断风险偏好。"},
]

DEFAULT_SENTIMENT = {
    "upCount": os.getenv("MARKET_UP_COUNT") or "1876",
    "downCount": os.getenv("MARKET_DOWN_COUNT") or "3540",
    "limitUp": os.getenv("MARKET_LIMIT_UP_COUNT") or "101",
    "limitDown": os.getenv("MARKET_LIMIT_DOWN_COUNT") or "99",
    "consecutiveBoards": os.getenv("MARKET_BOARD_CHAIN_TEXT") or "最高4板，2板以上约18只",
    "breakRate": os.getenv("MARKET_BREAK_RATE_TEXT") or "31%",
    "sampleDate": os.getenv("MARKET_SENTIMENT_SAMPLE_DATE") or "2026-07-06 收盘",
    "summary": "2026-07-06新浪财经全A收盘样本：上涨1876家、下跌3540家、平盘110家，涨停约101家、跌停约99家。涨跌停含20cm、30cm等不同涨跌幅制度样本。",
    "sources": ["新浪财经全A收盘样本", "东方财富行情复核", "同花顺热股复核"],
}

NEWS_IMPACT_RULES = [
    ("AI", ["工业富联", "中际旭创", "新易盛", "寒武纪"]),
    ("算力", ["工业富联", "中际旭创", "新易盛"]),
    ("机器人", ["雷赛智能", "大洋电机", "埃斯顿"]),
    ("半导体", ["北方华创", "中芯国际", "寒武纪"]),
    ("芯片", ["北方华创", "中芯国际", "寒武纪"]),
    ("创新药", ["恒瑞医药", "药明康德", "百济神州"]),
    ("医药", ["恒瑞医药", "药明康德", "迈瑞医疗"]),
    ("黄金", ["紫金矿业", "山东黄金", "赤峰黄金"]),
    ("煤炭", ["中国神华", "陕西煤业"]),
    ("银行", ["招商银行", "工商银行", "农业银行"]),
    ("地产", ["保利发展", "万科A"]),
    ("新能源", ["宁德时代", "阳光电源", "比亚迪"]),
    ("消费", ["贵州茅台", "五粮液", "中国中免"]),
]

SECTOR_LEADER_FALLBACK = {
    "机器人": ["雷赛智能", "大洋电机", "埃斯顿"],
    "黄金": ["紫金矿业", "山东黄金", "赤峰黄金"],
    "贵金属": ["紫金矿业", "山东黄金", "赤峰黄金"],
    "航天": ["航天环宇", "中航沈飞", "航发动力"],
    "军工": ["中航沈飞", "航发动力", "中航西飞"],
    "数字媒体": ["风语筑", "芒果超媒", "中文在线"],
    "电机": ["大洋电机", "鸣志电器", "汇川技术"],
    "汽车": ["比亚迪", "长安汽车", "赛力斯"],
    "汽车零部件": ["拓普集团", "德赛西威", "银轮股份"],
    "印制电路板": ["沪电股份", "胜宏科技", "深南电路"],
    "机械设备": ["汇川技术", "三一重工", "恒立液压"],
    "AI": ["工业富联", "中际旭创", "新易盛"],
    "半导体": ["北方华创", "中芯国际", "寒武纪"],
    "医药": ["恒瑞医药", "药明康德", "迈瑞医疗"],
}


FETCH_STATUS = {}


def mark(section, state, detail="", source=""):
    """Record how a section was filled so the UI can distinguish live data from carry-over.

    state: live (fetched this run) / stale (reused previous file) / fallback (hardcoded) / missing
    """
    FETCH_STATUS[section] = {"state": state, "detail": str(detail)[:200], "source": source}


def with_retry(fn, attempts=3, base_delay=1.5, label=""):
    """Retry transient network failures; eastmoney returns sporadic 502s under load."""
    last = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - network layer, any failure is retryable
            last = exc
            if attempt < attempts:
                time_module.sleep(base_delay * attempt)
    raise last if last else RuntimeError(f"{label} failed")


def request_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=24) as response:
        return response.read()


def eastmoney_json(url):
    def once():
        req = urllib.request.Request(url, headers=EASTMONEY_HEADERS)
        with urllib.request.urlopen(req, timeout=24) as response:
            return json.loads(response.read().decode("utf-8"))

    return with_retry(once, label="eastmoney")


def request_json(url):
    return json.loads(request_bytes(url).decode("utf-8"))


def request_text(url):
    return request_bytes(url).decode("utf-8", errors="replace")


def sina_text(url):
    req = urllib.request.Request(url, headers=SINA_HEADERS)
    with urllib.request.urlopen(req, timeout=24) as response:
        return response.read().decode("gbk", errors="replace")


def read_existing(name):
    path = ROOT / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_json(name, payload):
    (ROOT / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def format_number(value, digits=2):
    if value is None:
        return "--"
    return f"{value:,.{digits}f}"


def format_percent(value):
    if value is None:
        return "--"
    return f"{value:+.2f}%"


def format_amount(value):
    if value is None:
        return "--"
    value = float(value)
    if abs(value) >= 1e12:
        return f"{value / 1e12:.2f}万亿"
    if abs(value) >= 1e8:
        return f"{value / 1e8:.2f}亿"
    if abs(value) >= 1e4:
        return f"{value / 1e4:.2f}万"
    return f"{value:.0f}"


def is_placeholder(value):
    text = str(value or "").strip()
    return not text or text == "--" or any(term in text for term in PLACEHOLDER_TERMS)


def prefer_recent(value, fallback):
    return fallback if is_placeholder(value) else value


def replace_placeholders(value, replacement):
    text = str(value)
    for term in PLACEHOLDER_TERMS:
        text = text.replace(term, replacement)
    return text


def fetch_sina_market_snapshot():
    global SINA_MARKET_CACHE
    if SINA_MARKET_CACHE is not None:
        return SINA_MARKET_CACHE

    rows = []
    for page in range(1, 90):
        url = (
            "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
            f"Market_Center.getHQNodeData?page={page}&num=80&sort=changepercent&asc=0"
            "&node=hs_a&symbol=&_s_r_a=page"
        )
        text = sina_text(url)
        batch = json.loads(text) if text.strip() else []
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < 80:
            break

    changes = []
    amount = 0.0
    for row in rows:
        try:
            change = float(row.get("changepercent") or 0)
        except (TypeError, ValueError):
            continue
        changes.append(change)
        try:
            amount += float(row.get("amount") or 0)
        except (TypeError, ValueError):
            pass

    if len(changes) < 1000:
        raise RuntimeError(f"insufficient Sina market sample: {len(changes)}")

    SINA_MARKET_CACHE = {
        "rows": rows,
        "up": sum(1 for value in changes if value > 0),
        "down": sum(1 for value in changes if value < 0),
        "flat": sum(1 for value in changes if value == 0),
        "limitUp": sum(1 for value in changes if value >= 9.8),
        "limitDown": sum(1 for value in changes if value <= -9.8),
        "amount": amount,
        "maxUp": max(changes),
        "maxDown": min(changes),
    }
    return SINA_MARKET_CACHE


def market_status(now):
    if now.weekday() >= 5:
        return "休市"
    current = now.time()
    if time(9, 30) <= current <= time(11, 30) or time(13, 0) <= current <= time(15, 0):
        return "交易中"
    if time(11, 30) < current < time(13, 0):
        return "午间休市"
    if current > time(15, 0):
        return "已收盘"
    return "未开盘"


def fetch_yahoo_chart(symbol):
    encoded = urllib.parse.quote(symbol, safe="")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?range=1d&interval=5m"
    data = request_json(url)
    result = (data.get("chart", {}).get("result") or [None])[0]
    if not result:
        raise RuntimeError(f"No Yahoo chart data for {symbol}")

    meta = result.get("meta", {})
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    closes = [
        round(float(value), 4)
        for value in quote.get("close", [])
        if value is not None
    ]
    value = meta.get("regularMarketPrice")
    previous = meta.get("chartPreviousClose") or meta.get("previousClose") or (closes[0] if closes else None)

    if value is None and closes:
        value = closes[-1]
    if value is None:
        raise RuntimeError(f"No price for {symbol}")

    value = float(value)
    previous = float(previous) if previous else None
    change_percent = ((value - previous) / previous * 100) if previous else None
    digits = 4 if abs(value) < 10 else 2

    # Yahoo's coverage of the CN indices is patchy: it often returns a single
    # bar from an earlier session, so chartPreviousClose can be several sessions
    # back and the "change" is then a multi-day move, not a daily one.
    bar_date = None
    market_time = meta.get("regularMarketTime")
    if market_time:
        try:
            bar_date = datetime.fromtimestamp(int(market_time), tz=SHANGHAI).strftime("%Y-%m-%d")
        except (TypeError, ValueError, OSError):
            bar_date = None

    return {
        "value": round(value, 4),
        "valueText": format_number(value, digits),
        "changePercent": round(change_percent, 4) if change_percent is not None else None,
        "changeText": format_percent(change_percent),
        "sparkline": closes[-32:],
        "barDate": bar_date,
    }


def fetch_sina_kline_closes(sina_code, limit=32):
    """新浪日线收盘序列，用作 sparkline。

    东财 kline 在本项目实测经常连不上，而 sparkline 缺失时前端会画出一条直线，
    看起来像"走势平稳"——比不画更误导，所以需要一个稳的来源。
    """
    url = (
        "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"
        f"?symbol={sina_code}&scale=240&ma=no&datalen={limit}"
    )
    rows = with_retry(lambda: request_json(url), label="sina-kline")
    closes = []
    for row in rows or []:
        try:
            closes.append(round(float(row["close"]), 4))
        except (KeyError, TypeError, ValueError):
            continue
    return closes


def fetch_sina_index(sina_code):
    """新浪指数快照。

    Preferred over Yahoo for the CN indices: Yahoo's coverage of some of them is
    plainly wrong (2026-07-21 上证50: Yahoo 2827.67 vs 新浪 2943.63), and 新浪
    returns an explicit trade date so freshness can actually be verified.
    """
    text = sina_text(f"https://hq.sinajs.cn/list={sina_code}")
    if '"' not in text:
        raise RuntimeError(f"No sina data for {sina_code}")
    fields = text.split('"')[1].split(",")
    if len(fields) < 4:
        raise RuntimeError(f"Short sina payload for {sina_code}")
    value = float(fields[3])
    previous = float(fields[2])
    if not previous:
        raise RuntimeError(f"No previous close for {sina_code}")
    change_percent = (value - previous) / previous * 100
    try:
        sparkline = fetch_sina_kline_closes(sina_code)
    except Exception as exc:
        print(f"warning: sina kline failed for {sina_code}: {exc}", file=sys.stderr)
        sparkline = []
    return {
        "value": round(value, 4),
        "valueText": format_number(value, 2),
        "changePercent": round(change_percent, 4),
        "changeText": format_percent(change_percent),
        "barDate": fields[30] if len(fields) > 30 else None,
        "quoteSource": "sina",
        "sparkline": sparkline,
    }


def fetch_eastmoney_kline(secid, limit=35):
    url = (
        "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        f"?secid={urllib.parse.quote(secid, safe='.')}"
        "&fields1=f1,f2,f3,f4,f5,f6"
        "&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        f"&klt=101&fqt=1&beg=0&end=20500101&lmt={limit}"
    )
    payload = eastmoney_json(url).get("data") or {}
    rows = []
    for item in (payload.get("klines") or [])[-limit:]:
        parts = item.split(",")
        if len(parts) < 7:
            continue
        rows.append({
            "date": parts[0],
            "close": float(parts[2]),
            "amount": float(parts[6]),
        })
    return {
        "rows": rows,
        "closes": [row["close"] for row in rows],
    }


def fetch_eastmoney_quote(secid):
    if "|" in secid:
        last_error = None
        for candidate in secid.split("|"):
            try:
                return fetch_eastmoney_quote(candidate)
            except Exception as exc:
                last_error = exc
        raise RuntimeError(last_error or f"No Eastmoney quote data for {secid}")
    url = (
        "https://push2.eastmoney.com/api/qt/stock/get"
        "?fltt=2&invt=2"
        "&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60,f169,f170"
        f"&secid={urllib.parse.quote(secid, safe='.')}"
    )
    data = eastmoney_json(url).get("data")
    if not data:
        raise RuntimeError(f"No Eastmoney quote data for {secid}")
    sparkline = []
    try:
        sparkline = fetch_eastmoney_kline(secid, limit=32)["closes"]
    except Exception as exc:
        print(f"warning: Eastmoney kline failed for {secid}: {exc}", file=sys.stderr)
    return {
        "value": data.get("f43"),
        "valueText": format_number(data.get("f43"), 2),
        "change": data.get("f169"),
        "changePercent": data.get("f170"),
        "changeText": format_percent(data.get("f170")),
        "previous": data.get("f60"),
        "amountText": format_amount(data.get("f48")),
        "sparkline": sparkline,
    }


def append_live_point(item):
    """Make the sparkline end on the number printed on the card.

    Daily-kline endpoints publish the current session only after close, so the
    curve would otherwise stop at yesterday while the headline shows today.
    """
    sparkline = item.get("sparkline")
    value = item.get("value")
    if not sparkline or value in (None, ""):
        return
    try:
        value = float(value)
    except (TypeError, ValueError):
        return
    if abs(sparkline[-1] - value) > 1e-6:
        sparkline.append(round(value, 4))
    item["sparkline"] = sparkline[-33:]


def fetch_group(symbols, previous_items, section="indices"):
    previous_by_name = {item.get("name"): item for item in previous_items}
    now = datetime.now(SHANGHAI)
    today_str = now.strftime("%Y-%m-%d")
    output = []
    stale_names = []
    for spec in symbols:
        if len(spec) == 2:
            name, yahoo_symbol = spec
            source, secid = "yahoo", ""
        else:
            name, source, secid, yahoo_symbol = spec
        item = {"name": name, "symbol": yahoo_symbol or secid, "source": source}
        fetched = False   # got numbers from a live endpoint
        current = False   # and those numbers describe today's session
        if source == "eastmoney" and secid:
            try:
                item.update(fetch_eastmoney_quote(secid))
                fetched = current = True
            except Exception as exc:
                print(f"warning: eastmoney failed for {name}: {exc}", file=sys.stderr)
        sina_code = SINA_INDEX_CODES.get(name)
        # 东财报价成功但它的 kline 挂掉的情况很常见，单独补 sparkline，
        # 否则前端会把空数组画成一条平线，看着像"走势平稳"。
        if fetched and not item.get("sparkline") and sina_code:
            try:
                item["sparkline"] = fetch_sina_kline_closes(sina_code)
            except Exception as exc:
                print(f"warning: sina kline fallback failed for {name}: {exc}", file=sys.stderr)
        if not fetched and sina_code:
            try:
                quote = fetch_sina_index(sina_code)
                item.update(quote)
                fetched = True
                bar_date = quote.get("barDate")
                if bar_date and bar_date != today_str:
                    item["stale"] = True
                    item["staleFrom"] = bar_date
                    item["staleReason"] = f"新浪数据停留在 {bar_date}"
                    stale_names.append(name)
                else:
                    current = True
            except Exception as exc:
                print(f"warning: sina failed for {name}: {exc}", file=sys.stderr)
        if not fetched and yahoo_symbol:
            try:
                quote = fetch_yahoo_chart(yahoo_symbol)
                item.update(quote)
                fetched = True
                bar_date = quote.get("barDate")
                # Yahoo often serves an older single bar for the CN indices, so
                # its change% can span several sessions. Keep the value, but do
                # not let it pass as today's move.
                if bar_date and bar_date != today_str:
                    item["stale"] = True
                    item["staleFrom"] = bar_date
                    item["staleReason"] = f"Yahoo 数据停留在 {bar_date}，涨幅非单日口径"
                    stale_names.append(name)
                else:
                    current = True
            except Exception as exc:
                print(f"warning: yahoo failed for {name}: {exc}", file=sys.stderr)
        if not fetched:
            # Carry the previous value forward, but label it so the UI never
            # presents last session's number as if it were today's.
            carried = dict(previous_by_name.get(name, {}))
            carried.pop("stale", None)
            item.update(carried)
            if item.get("valueText") not in (None, "--"):
                item["stale"] = True
                item["staleFrom"] = carried.get("asOf") or "上一次成功抓取"
                item["staleReason"] = "本次抓取失败，沿用上次数据"
                stale_names.append(name)
        elif current:
            item["stale"] = False
            item["asOf"] = now.strftime("%Y-%m-%d %H:%M")
        # 必须在所有取数分支之后：新浪/Yahoo 分支各自会设置 sparkline。
        append_live_point(item)
        item.setdefault("valueText", "--")
        item.setdefault("changeText", "--")
        item.setdefault("sparkline", [])
        output.append(item)

    if not stale_names:
        mark(section, "live", source="eastmoney/yahoo")
    elif len(stale_names) == len(output):
        mark(section, "stale", detail="全部沿用上次数据：" + "、".join(stale_names), source="previous")
    else:
        mark(section, "partial", detail="沿用上次数据：" + "、".join(stale_names), source="mixed")
    return output


def fetch_volume_analysis(existing):
    previous = existing.get("volumeAnalysis") or DEFAULT_VOLUME_ANALYSIS
    try:
        sh_rows = fetch_eastmoney_kline("1.000001", limit=22)["rows"]
        sz_rows = fetch_eastmoney_kline("0.399001", limit=22)["rows"]
        by_date = {}
        for row in sh_rows + sz_rows:
            by_date[row["date"]] = by_date.get(row["date"], 0) + row["amount"]
        rows = [{"date": date, "amount": amount} for date, amount in sorted(by_date.items())][-22:]
        if not rows:
            mark("volumeAnalysis", "stale", detail="K线返回空", source="previous")
            return previous
        today = rows[-1]["amount"]
        prev = rows[-2]["amount"] if len(rows) > 1 else None
        change = ((today - prev) / prev * 100) if prev else None
        max_amount = max(row["amount"] for row in rows) or 1
        payload = {
            "today": format_amount(today),
            "previous": format_amount(prev) if prev else "--",
            "change": format_percent(change),
            "summary": "近一个月沪深两市成交额按上证指数与深证成指日线成交额合并估算。放量上涨更利于趋势强势股延续，缩量上涨则等待回踩确认。",
            "bars": [
                {
                    "label": row["date"][5:],
                    "amountText": format_amount(row["amount"]),
                    "value": round(row["amount"] / max_amount * 100, 2),
                }
                for row in rows
            ],
        }
        mark("volumeAnalysis", "live", source="eastmoney K线")
        return payload
    except Exception as exc:
        print(f"warning: using previous volume data: {exc}", file=sys.stderr)
        try:
            snapshot = fetch_sina_market_snapshot()
            mark("volumeAnalysis", "live", detail="eastmoney 失败，改用新浪快照", source="新浪全A快照")
            today = snapshot["amount"]
            prev_text = prefer_recent(previous.get("today"), DEFAULT_VOLUME_ANALYSIS["previous"])
            previous_amount = None
            if "万亿" in str(prev_text):
                previous_amount = float(str(prev_text).replace("万亿", "")) * 1e12
            elif "亿" in str(prev_text):
                previous_amount = float(str(prev_text).replace("亿", "")) * 1e8
            change = ((today - previous_amount) / previous_amount * 100) if previous_amount else None
            bars = list(previous.get("bars") or DEFAULT_VOLUME_ANALYSIS["bars"])
            max_amount_text = format_amount(today)
            if bars:
                bars[-1] = {
                    "label": datetime.now(SHANGHAI).strftime("%m-%d"),
                    "value": 100,
                    "amountText": max_amount_text,
                }
            return {
                **DEFAULT_VOLUME_ANALYSIS,
                **previous,
                "today": max_amount_text,
                "previous": prev_text,
                "change": format_percent(change) if change is not None else "收盘放量",
                "summary": f"成交额采用新浪财经全A收盘样本合计，约 {max_amount_text}。若与交易所口径存在差异，以交易所正式披露为准。",
                "bars": bars,
                "sampleDate": datetime.now(SHANGHAI).strftime("%Y-%m-%d 收盘"),
            }
        except Exception as sina_exc:
            print(f"warning: using fallback volume sample: {sina_exc}", file=sys.stderr)
            if len(previous.get("bars", [])) < 20 or any(term in json.dumps(previous, ensure_ascii=False) for term in PLACEHOLDER_TERMS):
                mark("volumeAnalysis", "fallback", detail=str(sina_exc), source="hardcoded")
                return DEFAULT_VOLUME_ANALYSIS
            mark("volumeAnalysis", "stale", detail=str(sina_exc), source="previous")
            return previous


def fetch_hot_sectors(existing):
    previous = existing.get("hotSectors") or DEFAULT_HOT_SECTORS
    url = (
        "https://push2.eastmoney.com/api/qt/clist/get"
        "?pn=1&pz=12&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2"
        "&fields=f12,f14,f2,f3,f62,f128,f140,f136"
    )
    try:
        rows = ((eastmoney_json(url).get("data") or {}).get("diff") or [])[:12]
        items = []
        for index, row in enumerate(rows, start=1):
            change = row.get("f3")
            strength = max(0, min(100, round((float(change or 0) + 10) * 5, 2)))
            leaders = sector_leaders(row.get("f14"), [row.get("f128"), row.get("f140"), row.get("f12")])
            items.append({
                "rank": index,
                "name": row.get("f14"),
                "strength": strength,
                "changeText": format_percent(change),
                "reason": f"板块涨幅 {format_percent(change)}，领涨股 {row.get('f128') or '--'} {format_percent(row.get('f136'))}。",
                "leaders": leaders,
            })
        if items:
            mark("hotSectors", "live", source="eastmoney 板块涨幅")
            return items
        mark("hotSectors", "stale", detail="接口返回空", source="previous")
        return previous
    except Exception as exc:
        print(f"warning: using previous hot sector data: {exc}", file=sys.stderr)
        mark("hotSectors", "stale", detail=str(exc), source="previous")
        return normalize_hot_sectors(previous)


def normalize_hot_sectors(items):
    output = []
    for item in items:
        normalized = dict(item)
        normalized["leaders"] = sector_leaders(normalized.get("name"), normalized.get("leaders", []))
        output.append(normalized)
    return output


def sector_leaders(name, observed):
    leaders = [
        item for item in observed
        if item and not str(item).startswith("BK") and not str(item).isdigit() and not is_placeholder(item) and "板块龙头" not in str(item)
    ]
    for keyword, fallback in SECTOR_LEADER_FALLBACK.items():
        if name and keyword in name:
            leaders.extend(fallback)
            break
    leaders = list(dict.fromkeys(leaders))
    if len(leaders) < 3:
        leaders.extend(["成交额前排", "趋势核心股", "板块中军"])
    return leaders[:3]


def fetch_fund_flows(existing):
    previous = existing.get("fundFlows") or DEFAULT_FUND_FLOWS
    url = (
        "https://push2.eastmoney.com/api/qt/clist/get"
        "?pn=1&pz=10&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:90+t:2"
        "&fields=f12,f14,f2,f3,f62,f184,f66,f69,f72,f75"
    )
    try:
        rows = ((eastmoney_json(url).get("data") or {}).get("diff") or [])[:10]
        items = [
            {
                "name": row.get("f14"),
                "valueText": format_amount(row.get("f62")),
                "direction": "up" if (row.get("f62") or 0) > 0 else "down",
                "summary": f"主力净流入占比 {format_percent(row.get('f184'))}，板块涨幅 {format_percent(row.get('f3'))}。",
            }
            for row in rows
        ]
        if items:
            mark("fundFlows", "live", source="eastmoney 资金流向")
            return items
        mark("fundFlows", "stale", detail="接口返回空", source="previous")
        return previous
    except Exception as exc:
        print(f"warning: using previous fund flow data: {exc}", file=sys.stderr)
        mark("fundFlows", "stale", detail=str(exc), source="previous")
        return previous


def fetch_valuations(existing):
    """指数 PE/PB 与历史分位。

    以前这块从来没抓过，只是把上一份文件里的值原样搬运，连"今日下跌3.60%"这种
    当日点评都一起搬——涨的那天照样显示在跌。现在改为实抓，分位数由历史序列算出，
    主观点评一律不放这里。
    """
    previous = existing.get("valuations") or []
    try:
        import akshare_feeds
    except Exception as exc:
        mark("valuations", "missing", detail=f"akshare_feeds 不可用：{exc}")
        return strip_stale_commentary(previous)

    data = akshare_feeds.fetch_index_valuations()
    items = data.get("items") or []
    if not items:
        mark("valuations", "stale" if previous else "missing",
             detail=data.get("detail", ""), source="akshare")
        return strip_stale_commentary(previous)

    mark("valuations", "partial" if data.get("state") == "partial" else "live",
         detail=data.get("detail", ""), source="乐咕乐股指数估值")
    return items


def strip_stale_commentary(items):
    """Drop day-specific prose carried over from an older file.

    `compare` used to hold things like "今日下跌3.60%" — factually wrong on any
    other day. Better to show nothing than yesterday's verdict.
    """
    cleaned = []
    for item in items or []:
        entry = {k: v for k, v in item.items() if k != "compare"}
        entry["stale"] = True
        cleaned.append(entry)
    return cleaned


def apply_limit_ecosystem(sentiment, now):
    """Overlay 涨停/跌停/连板/炸板率 from the eastmoney 股池 via akshare.

    This is the only authoritative caliber for these numbers; the |change|>=9.8%
    approximation in fetch_market_breadth over-counts badly (7-17: 649 vs 192).
    """
    try:
        import akshare_feeds
    except Exception as exc:
        mark("limitEcosystem", "missing", detail=f"akshare_feeds 不可用：{exc}")
        return sentiment

    data = akshare_feeds.fetch_limit_ecosystem(now.strftime("%Y%m%d"))
    state = data.get("state")
    if state in ("missing", "error"):
        mark("limitEcosystem", "missing" if state == "missing" else "stale",
             detail=data.get("detail", ""), source="akshare")
        sentiment.setdefault("limitCaliber", "近似（涨跌幅≥9.8%）")
        return sentiment

    merged = dict(sentiment)
    if "limitUp" in data:
        merged["limitUp"] = str(data["limitUp"])
    if "limitDown" in data:
        merged["limitDown"] = str(data["limitDown"])
    if "breakRate" in data:
        merged["breakRate"] = data["breakRate"]
        merged["breakRateValue"] = data.get("breakRateValue")
    if "consecutiveBoards" in data:
        merged["consecutiveBoards"] = data["consecutiveBoards"]
    for key in ("maxBoard", "multiBoard", "boardLadder", "limitUpLeaders", "brokenBoard"):
        if key in data:
            merged[key] = data[key]
    merged["limitCaliber"] = data.get("caliber", "东方财富涨停股池口径")
    merged["limitSampleDate"] = data.get("sampleDate")
    mark("limitEcosystem", "partial" if state == "partial" else "live",
         detail=data.get("detail", ""), source="akshare 东财股池")
    return merged


def fetch_market_breadth(existing):
    previous = existing.get("sentiment") or DEFAULT_SENTIMENT
    try:
        rows = []
        for page in range(1, 70):
            url = (
                "https://push2.eastmoney.com/api/qt/clist/get"
                f"?pn={page}&pz=100&po=1&np=1&fltt=2&invt=2&fid=f3"
                "&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
                "&fields=f12,f14,f2,f3"
            )
            batch = ((eastmoney_json(url).get("data") or {}).get("diff") or [])
            if not batch:
                break
            rows.extend(batch)
            if len(batch) < 100:
                break
        changes = [row.get("f3") for row in rows if isinstance(row.get("f3"), (int, float))]
        if len(changes) < 1000:
            raise RuntimeError(f"insufficient breadth sample: {len(changes)}")
        up = sum(1 for value in changes if value > 0)
        down = sum(1 for value in changes if value < 0)
        # 近似口径：|涨跌幅| >= 9.8% 会漏掉 20cm/30cm 品种、并混入未封板的大涨大跌股。
        # 仅作为 akshare 涨停股池不可用时的兜底，apply_limit_ecosystem 会覆盖它。
        limit_up = sum(1 for value in changes if value >= 9.8)
        limit_down = sum(1 for value in changes if value <= -9.8)
        mark("sentiment", "live", source="eastmoney 全A快照")
        return {
            **previous,
            "upCount": str(up),
            "downCount": str(down),
            "limitCaliber": "近似（涨跌幅≥9.8%）",
            "limitUp": str(limit_up),
            "limitDown": str(limit_down),
            "summary": f"全 A 样本上涨 {up} 家、下跌 {down} 家，涨停约 {limit_up} 家、跌停约 {limit_down} 家。ST 个股涨跌停口径未单独拆分。",
        }
    except Exception as exc:
        print(f"warning: using previous breadth data: {exc}", file=sys.stderr)
        try:
            snapshot = fetch_sina_market_snapshot()
            mark("sentiment", "live", detail="eastmoney 失败，改用新浪全A快照", source="新浪全A快照")
            up = snapshot["up"]
            down = snapshot["down"]
            flat = snapshot["flat"]
            limit_up = snapshot["limitUp"]
            limit_down = snapshot["limitDown"]
            return {
                **DEFAULT_SENTIMENT,
                **previous,
                "upCount": str(up),
                "downCount": str(down),
                "limitUp": str(limit_up),
                "limitDown": str(limit_down),
                "summary": f"新浪财经全A收盘样本：上涨 {up} 家、下跌 {down} 家、平盘 {flat} 家，涨停约 {limit_up} 家、跌停约 {limit_down} 家。涨跌停含20cm、30cm等不同涨跌幅制度样本。",
                "sources": ["新浪财经全A收盘样本", "东方财富行情复核", "同花顺热股复核"],
                "sampleDate": datetime.now(SHANGHAI).strftime("%Y-%m-%d 收盘"),
            }
        except Exception as sina_exc:
            print(f"warning: using fallback breadth sample: {sina_exc}", file=sys.stderr)
            mark("sentiment", "stale", detail=str(sina_exc), source="previous")
        try:
            total = int(previous.get("upCount", 0)) + int(previous.get("downCount", 0))
        except (TypeError, ValueError):
            total = 0
        if total < 1000:
            mark("sentiment", "fallback", detail="无可用样本", source="hardcoded")
            return DEFAULT_SENTIMENT
        return {
            **DEFAULT_SENTIMENT,
            **previous,
            "upCount": prefer_recent(previous.get("upCount"), DEFAULT_SENTIMENT["upCount"]),
            "downCount": prefer_recent(previous.get("downCount"), DEFAULT_SENTIMENT["downCount"]),
            "limitUp": prefer_recent(previous.get("limitUp"), DEFAULT_SENTIMENT["limitUp"]),
            "limitDown": prefer_recent(previous.get("limitDown"), DEFAULT_SENTIMENT["limitDown"]),
            "consecutiveBoards": prefer_recent(previous.get("consecutiveBoards"), DEFAULT_SENTIMENT["consecutiveBoards"]),
            "breakRate": prefer_recent(previous.get("breakRate"), DEFAULT_SENTIMENT["breakRate"]),
            "summary": prefer_recent(previous.get("summary"), DEFAULT_SENTIMENT["summary"]),
            "sources": [replace_placeholders(source, "复核") for source in previous.get("sources", DEFAULT_SENTIMENT["sources"])],
        }


def fetch_lhb(existing):
    previous = existing.get("lhb") or []
    url = (
        "https://datacenter-web.eastmoney.com/api/data/v1/get"
        "?reportName=RPT_DAILYBILLBOARD_DETAILS"
        "&columns=SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,EXPLAIN,CLOSE_PRICE,CHANGE_RATE,BILLBOARD_NET_AMT"
        "&sortColumns=TRADE_DATE&sortTypes=-1&pageNumber=1&pageSize=16&source=WEB&client=WEB"
    )
    try:
        rows = (((eastmoney_json(url).get("result") or {}).get("data")) or [])[:16]
        seen = set()
        items = []
        for row in rows:
            code = row.get("SECURITY_CODE")
            if code in seen:
                continue
            seen.add(code)
            items.append({
                "code": code,
                "name": row.get("SECURITY_NAME_ABBR"),
                "date": (row.get("TRADE_DATE") or "")[:10],
                "reason": row.get("EXPLAIN"),
                "changeText": format_percent(row.get("CHANGE_RATE")),
                "netAmountText": format_amount(row.get("BILLBOARD_NET_AMT")),
            })
        if items:
            mark("lhb", "live", source="eastmoney 龙虎榜")
            return items
        mark("lhb", "stale", detail="接口返回空", source="previous")
        return previous
    except Exception as exc:
        print(f"warning: using previous lhb data: {exc}", file=sys.stderr)
        mark("lhb", "stale", detail=str(exc), source="previous")
        return previous


def weekday_cn(now):
    return "一二三四五六日"[now.weekday()]


def build_market_payload():
    now = datetime.now(SHANGHAI)
    existing = read_existing("market.json")
    indices = fetch_group(INDEX_SYMBOLS, existing.get("indices", []), section="indices")
    global_markets = fetch_group(GLOBAL_SYMBOLS, existing.get("globalMarkets", []), section="globalMarkets")

    quick_stats = [
        {
            "label": item["name"],
            "valueText": item.get("changeText", "--"),
            "changePercent": item.get("changePercent"),
        }
        for item in indices[:4]
    ]
    quick_stats.extend([
        {
            "label": "成交额",
            "valueText": os.getenv("MARKET_TURNOVER_TEXT") or existing.get("turnoverText", "--"),
            "color": "var(--ink)",
        },
        {
            "label": "上涨",
            "valueText": os.getenv("MARKET_UP_COUNT") or (existing.get("sentiment") or DEFAULT_SENTIMENT).get("upCount", DEFAULT_SENTIMENT["upCount"]),
            "color": "var(--up)",
        },
        {
            "label": "下跌",
            "valueText": os.getenv("MARKET_DOWN_COUNT") or (existing.get("sentiment") or DEFAULT_SENTIMENT).get("downCount", DEFAULT_SENTIMENT["downCount"]),
            "color": "var(--down)",
        },
        {
            "label": "涨停",
            "valueText": os.getenv("MARKET_LIMIT_UP_COUNT") or (existing.get("sentiment") or DEFAULT_SENTIMENT).get("limitUp", DEFAULT_SENTIMENT["limitUp"]),
            "color": "var(--up)",
        },
    ])

    style_matrix = existing.get("styleMatrix") or DEFAULT_STYLE_MATRIX
    volume_analysis = fetch_volume_analysis(existing)
    hot_sectors = fetch_hot_sectors(existing)
    fund_flows = fetch_fund_flows(existing)
    valuations = fetch_valuations(existing)
    sentiment = apply_limit_ecosystem(fetch_market_breadth(existing), now)
    quick_stats[4]["valueText"] = prefer_recent(volume_analysis.get("today"), DEFAULT_VOLUME_ANALYSIS["today"])
    quick_stats[5]["valueText"] = prefer_recent(sentiment.get("upCount"), DEFAULT_SENTIMENT["upCount"])
    quick_stats[6]["valueText"] = prefer_recent(sentiment.get("downCount"), DEFAULT_SENTIMENT["downCount"])
    quick_stats[7]["valueText"] = prefer_recent(sentiment.get("limitUp"), DEFAULT_SENTIMENT["limitUp"])
    lhb = fetch_lhb(existing)

    return {
        "updatedAt": now.isoformat(),
        "updatedAtText": now.strftime("%H:%M"),
        "tradingDate": now.strftime("%Y-%m-%d"),
        "tradingDateText": f"{now.year}年{now.month}月{now.day}日 周{weekday_cn(now)}",
        "marketStatus": market_status(now),
        "turnoverText": quick_stats[4]["valueText"],
        "indices": indices,
        "quickStats": quick_stats,
        "globalMarkets": global_markets,
        "styleMatrix": style_matrix,
        "volumeAnalysis": volume_analysis,
        "hotSectors": hot_sectors,
        "fundFlows": fund_flows,
        "valuations": valuations,
        "sentiment": sentiment,
        "lhb": lhb,
        "fetchStatus": FETCH_STATUS,
        # 主观内容（大师观点/交易建议/股票池/异常波动/事件解读）不再写在这里，
        # 由 make_prompt.py → chat → save_insights.py 生成到 insights.json。
        "insightsFile": "insights.json",
        "dataSources": {
            "indices": "东方财富行情中心优先，Yahoo Finance 兜底",
            "sectors": "东方财富板块涨幅",
            "fundFlows": "东方财富资金流向",
            "valuation": "参考东方财富估值分析 https://data.eastmoney.com/gzfx/",
            "sentiment": "东方财富全A收盘统计；同花顺、雪球热度作复核",
            "news": "新浪财经、中新网、财新、证券时报、财联社等公开源",
        },
    }


def parse_rss_date(value):
    if not value:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(SHANGHAI).strftime("%m-%d %H:%M")
    except (TypeError, ValueError):
        return ""


def rss_urls():
    value = os.getenv("NEWS_RSS_URLS", "")
    if not value.strip():
        return DEFAULT_RSS_URLS
    return [item.strip() for item in value.split(",") if item.strip()]


def fetch_news_items():
    items = []
    seen = set()
    for url in rss_urls():
        try:
            text = request_text(url)
        except Exception as exc:
            print(f"warning: RSS failed {url}: {exc}", file=sys.stderr)
            continue

        if "cls.cn/nodeapi" in url:
            try:
                payload = json.loads(text)
                nodes = payload.get("data", {}).get("roll_data") or payload.get("data", []) or []
                for node in nodes:
                    title = (node.get("title") or node.get("content") or "").strip()
                    link = node.get("shareurl") or node.get("url") or ""
                    if not title or title in seen:
                        continue
                    seen.add(title)
                    items.append(enrich_news_item({
                        "title": title,
                        "url": link,
                        "source": "财联社",
                        "publishedAt": str(node.get("ctime") or ""),
                        "publishedAtText": "",
                    }))
                    if len(items) >= 20:
                        return items
            except Exception as exc:
                print(f"warning: JSON news failed {url}: {exc}", file=sys.stderr)
            continue

        try:
            root = ET.fromstring(text)
        except Exception as exc:
            print(f"warning: RSS parse failed {url}: {exc}", file=sys.stderr)
            continue

        channel_title = root.findtext("./channel/title") or "新闻"
        for node in root.findall("./channel/item"):
            title = (node.findtext("title") or "").strip()
            link = (node.findtext("link") or "").strip()
            if not title or title in seen:
                continue
            seen.add(title)
            items.append(enrich_news_item({
                "title": title,
                "url": link,
                "source": channel_title,
                "publishedAt": node.findtext("pubDate") or "",
                "publishedAtText": parse_rss_date(node.findtext("pubDate")),
            }))
            if len(items) >= 20:
                return items
    return items


def enrich_news_item(item):
    title = item.get("title", "")
    impacted = []
    tags = []
    for keyword, stocks in NEWS_IMPACT_RULES:
        if keyword in title:
            tags.append(keyword)
            impacted.extend(stocks)
    item["impactTags"] = tags[:4] or ["全A风险偏好"]
    item["impactedStocks"] = list(dict.fromkeys(impacted))[:5] or ["沪深300ETF", "创业板ETF", "券商ETF"]
    item["impactNote"] = "可能影响：" + "、".join(item["impactedStocks"])
    return item


def build_news_payload():
    now = datetime.now(SHANGHAI)
    existing = read_existing("news.json")
    items = fetch_news_items() or existing.get("items", [])
    return {
        "updatedAt": now.isoformat(),
        "items": [enrich_news_item(dict(item)) for item in items[:20]],
    }


def main():
    save_json("market.json", build_market_payload())
    save_json("news.json", build_news_payload())


if __name__ == "__main__":
    main()
