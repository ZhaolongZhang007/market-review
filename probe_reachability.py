#!/usr/bin/env python3
"""连通性探测：这台机器能否访问本项目依赖的中国财经数据源？

只读，不写文件、不改数据。本地和 GitHub Actions 上跑同一份，便于对比。

    python3 probe_reachability.py              # 只测裸 HTTP（无依赖）
    python3 probe_reachability.py --akshare    # 额外测 akshare（需已安装）
"""
import json
import ssl
import sys
import time
import urllib.error
import urllib.request

TIMEOUT = 20

EASTMONEY_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://quote.eastmoney.com/",
}
SINA_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://finance.sina.com.cn/",
}

# (标签, URL, headers, 判定响应是否真的有数据)
ENDPOINTS = [
    (
        "东财-指数报价 (push2)",
        "https://push2.eastmoney.com/api/qt/stock/get?fltt=2&invt=2&fields=f43,f170&secid=1.000001",
        EASTMONEY_HEADERS,
        lambda b: (json.loads(b).get("data") or {}).get("f43") is not None,
    ),
    (
        "东财-板块列表 (clist)",
        "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2&fields=f12,f14,f3",
        EASTMONEY_HEADERS,
        lambda b: bool((json.loads(b).get("data") or {}).get("diff")),
    ),
    (
        "东财-日线 (kline)",
        "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.000001&fields1=f1&fields2=f51,f53&klt=101&fqt=1&end=20500101&lmt=5",
        EASTMONEY_HEADERS,
        lambda b: bool(((json.loads(b).get("data") or {}).get("klines")) or []),
    ),
    (
        "新浪-实时行情 (hq.sinajs)",
        "https://hq.sinajs.cn/list=sh000001",
        SINA_HEADERS,
        lambda b: len(b.decode("gbk", "replace").split(",")) > 3,
    ),
    (
        "新浪-日线 K 线",
        "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"
        "?symbol=sh000001&scale=240&ma=no&datalen=5",
        SINA_HEADERS,
        lambda b: len(json.loads(b)) > 0,
    ),
    (
        "新浪-全A快照",
        "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
        "Market_Center.getHQNodeData?page=1&num=5&sort=symbol&asc=1&node=hs_a",
        SINA_HEADERS,
        lambda b: len(json.loads(b.decode("gbk", "replace"))) > 0,
    ),
    (
        "乐咕乐股 (akshare 估值源)",
        "https://legulegu.com/api/stock-data/market-ttm-lyr?token=&marketId=5",
        {"User-Agent": "Mozilla/5.0"},
        lambda b: len(b) > 50,
    ),
]


def probe(label, url, headers, verify):
    started = time.monotonic()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
        elapsed = time.monotonic() - started
        try:
            ok = verify(body)
        except Exception as exc:  # 连上了但内容不是预期结构
            return "SHAPE", f"HTTP {resp.status} 但解析失败: {type(exc).__name__}", elapsed, len(body)
        return ("OK" if ok else "EMPTY"), f"HTTP {resp.status}", elapsed, len(body)
    except urllib.error.HTTPError as exc:
        return "HTTP_ERR", f"HTTP {exc.code}", time.monotonic() - started, 0
    except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return "NET_ERR", f"{type(exc).__name__}: {str(reason)[:90]}", time.monotonic() - started, 0


def probe_akshare():
    print("\n" + "=" * 72)
    print("akshare 接口探测")
    print("=" * 72)
    try:
        import akshare as ak
    except Exception as exc:
        print(f"  akshare 导入失败: {exc}")
        return 1

    print(f"  akshare 版本: {getattr(ak, '__version__', '?')}")
    date = time.strftime("%Y%m%d")
    checks = [
        ("涨停股池", lambda: ak.stock_zt_pool_em(date=date)),
        ("跌停股池", lambda: ak.stock_zt_pool_dtgc_em(date=date)),
        ("炸板股池", lambda: ak.stock_zt_pool_zbgc_em(date=date)),
        ("指数PE(乐咕)", lambda: ak.stock_index_pe_lg(symbol="沪深300")),
        ("交易日历", lambda: ak.tool_trade_date_hist_sina()),
    ]
    failures = 0
    for label, fn in checks:
        started = time.monotonic()
        try:
            df = fn()
            elapsed = time.monotonic() - started
            n = len(df)
            status = "OK" if n > 0 else "EMPTY"
            if n == 0:
                failures += 1
            print(f"  [{status:8}] {label:14} {n:>6} 行  {elapsed:5.1f}s")
        except Exception as exc:
            failures += 1
            print(f"  [{'FAIL':8}] {label:14} {type(exc).__name__}: {str(exc)[:70]}")
    return failures


def main():
    print("=" * 72)
    print("裸 HTTP 端点探测")
    print("=" * 72)
    failures = 0
    for label, url, headers, verify in ENDPOINTS:
        status, detail, elapsed, size = probe(label, url, headers, verify)
        if status != "OK":
            failures += 1
        print(f"  [{status:8}] {label:26} {elapsed:5.1f}s {size:>7}B  {detail}")

    if "--akshare" in sys.argv:
        failures += probe_akshare()

    print("\n" + "=" * 72)
    if failures == 0:
        print("结论：全部可达 —— 这台机器可以跑数据抓取。")
    else:
        print(f"结论：{failures} 项失败 —— 这台机器不适合跑抓取，需要换执行环境。")
    print("=" * 72)
    # 探测脚本本身不应让 CI 变红：结论看输出。
    return 0


if __name__ == "__main__":
    sys.exit(main())
