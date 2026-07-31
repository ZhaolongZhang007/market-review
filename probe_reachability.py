#!/usr/bin/env python3
"""连通性探测 v2：这台机器能否拿到本项目需要的全部数据？

v1 发现：GitHub 机房访问 push2.eastmoney.com 全部 502，但 akshare 正常。
v2 要回答的问题是——akshare 能否替掉 update_data.py 里所有走裸 urllib 的东财请求？

只读，不写文件、不改数据。

    python3 probe_reachability.py              # 只测裸 HTTP（无依赖）
    python3 probe_reachability.py --akshare    # 测 akshare 替代方案（关键）
"""
import json
import os
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

# (标签, URL, headers, 判定函数, 是否关键)
# 关键=这条挂了就必须换方案；非关键=有替代路径
ENDPOINTS = [
    # push2 vs push2delay —— 本地实测同一 IP 只换 Host：push2 全 502，
    # push2delay 正常返回。这里在 GitHub 机房再验一次。
    ("东财 push2 报价",
     "https://push2.eastmoney.com/api/qt/stock/get?fltt=2&invt=2&fields=f43,f170&secid=1.000001",
     EASTMONEY_HEADERS,
     lambda b: (json.loads(b).get("data") or {}).get("f43") is not None, False),
    ("东财 push2delay 报价",
     "https://push2delay.eastmoney.com/api/qt/stock/get?fltt=2&invt=2&fields=f43,f170&secid=1.000001",
     EASTMONEY_HEADERS,
     lambda b: (json.loads(b).get("data") or {}).get("f43") is not None, True),
    ("东财 push2 板块",
     "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2&fields=f12,f14,f3",
     EASTMONEY_HEADERS,
     lambda b: bool((json.loads(b).get("data") or {}).get("diff")), False),
    ("东财 push2delay 板块",
     "https://push2delay.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2&fields=f12,f14,f3",
     EASTMONEY_HEADERS,
     lambda b: bool((json.loads(b).get("data") or {}).get("diff")), True),
    ("东财 push2his 日线",
     "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.000001&fields1=f1&fields2=f51,f53&klt=101&fqt=1&end=20500101&lmt=5",
     EASTMONEY_HEADERS,
     lambda b: bool(((json.loads(b).get("data") or {}).get("klines")) or []), False),
    ("新浪 实时行情",
     "https://hq.sinajs.cn/list=sh000001",
     SINA_HEADERS,
     lambda b: len(b.decode("gbk", "replace").split(",")) > 3, True),
    ("新浪 日线K线",
     "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol=sh000001&scale=240&ma=no&datalen=5",
     SINA_HEADERS,
     lambda b: len(json.loads(b)) > 0, True),
    ("新浪 全A快照",
     "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
     "Market_Center.getHQNodeData?page=1&num=5&sort=symbol&asc=1&node=hs_a",
     SINA_HEADERS,
     lambda b: len(json.loads(b.decode("gbk", "replace"))) > 0, True),
]


def probe(url, headers, verify):
    started = time.monotonic()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
        elapsed = time.monotonic() - started
        try:
            ok = verify(body)
        except Exception as exc:
            return "SHAPE", f"HTTP {resp.status} 解析失败 {type(exc).__name__}", elapsed
        return ("OK" if ok else "EMPTY"), f"HTTP {resp.status}", elapsed
    except urllib.error.HTTPError as exc:
        return "HTTP_ERR", f"HTTP {exc.code}", time.monotonic() - started
    except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return "NET_ERR", f"{type(exc).__name__}: {str(reason)[:70]}", time.monotonic() - started


def probe_akshare():
    """关键测试：akshare 能否覆盖 update_data.py 的全部数据需求。"""
    print("\n" + "=" * 74)
    print("akshare 替代方案探测（关键）")
    print("=" * 74)
    try:
        import akshare as ak
    except Exception as exc:
        print(f"  akshare 导入失败: {exc}")
        return ["akshare 未安装"]

    print(f"  akshare {getattr(ak, '__version__', '?')}\n")
    date = time.strftime("%Y%m%d")

    # (标签, 调用, update_data.py 里对应的原始来源, 空结果是否可接受)
    checks = [
        ("指数行情",   lambda: ak.stock_zh_index_spot_em(symbol="上证系列指数"),
         "push2 stock/get", False),
        ("指数日线",   lambda: ak.index_zh_a_hist(symbol="000001", period="daily",
                                                  start_date="20260101"),
         "push2his kline", False),
        ("行业板块",   lambda: ak.stock_board_industry_name_em(),
         "push2 clist fs=m:90+t:2", False),
        ("板块资金流", lambda: ak.stock_sector_fund_flow_rank(
                            indicator="今日", sector_type="行业资金流"),
         "push2 clist fid=f62", False),
        ("全A快照",    lambda: ak.stock_zh_a_spot_em(),
         "push2 clist 70页循环", False),
        ("龙虎榜",     lambda: ak.stock_lhb_detail_em(start_date=date, end_date=date),
         "东财龙虎榜", True),
        ("涨停股池",   lambda: ak.stock_zt_pool_em(date=date), "push2ex", True),
        ("炸板股池",   lambda: ak.stock_zt_pool_zbgc_em(date=date), "push2ex", True),
        ("指数PE",     lambda: ak.stock_index_pe_lg(symbol="沪深300"), "乐咕乐股", False),
        ("交易日历",   lambda: ak.tool_trade_date_hist_sina(), "新浪", False),
    ]

    blockers = []
    for label, fn, origin, empty_ok in checks:
        started = time.monotonic()
        try:
            df = fn()
            elapsed = time.monotonic() - started
            n = len(df)
            if n > 0:
                status = "OK"
            elif empty_ok:
                status = "EMPTY?"      # 可能真的就是 0（如无跌停股）
            else:
                status = "EMPTY!"
                blockers.append(f"{label}（返回 0 行）")
            print(f"  [{status:7}] {label:10} {n:>6} 行 {elapsed:5.1f}s   ← 替代 {origin}")
        except Exception as exc:
            blockers.append(f"{label}（{type(exc).__name__}）")
            print(f"  [{'FAIL':7}] {label:10} {type(exc).__name__}: {str(exc)[:55]}")
    return blockers


def emit_summary(lines):
    """把结果写进 GitHub 的 job summary，省得翻日志。"""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    print("=" * 74)
    print("裸 HTTP 端点探测")
    print("=" * 74)
    critical_down = []
    rows = ["| 端点 | 结果 | 耗时 | 详情 |", "|---|---|---|---|"]
    for label, url, headers, verify, critical in ENDPOINTS:
        status, detail, elapsed = probe(url, headers, verify)
        tag = "关键" if critical else "可替代"
        if status != "OK" and critical:
            critical_down.append(label)
        icon = "✅" if status == "OK" else ("⚠️" if not critical else "❌")
        print(f"  [{status:8}] {label:20} [{tag:3}] {elapsed:5.1f}s  {detail}")
        rows.append(f"| {label} | {icon} {status} | {elapsed:.1f}s | {detail} |")

    blockers = []
    if "--akshare" in sys.argv:
        blockers = probe_akshare()

    print("\n" + "=" * 74)
    if critical_down:
        verdict = f"❌ 关键端点不可达：{'、'.join(critical_down)} —— 必须换执行环境"
    elif blockers:
        verdict = f"❌ akshare 无法覆盖：{'、'.join(blockers)}"
    else:
        verdict = "✅ 关键端点可达 + akshare 全覆盖 —— 这台机器可以跑全自动抓取"
    print(verdict)
    print("=" * 74)

    emit_summary(["## 数据源可达性探测", ""] + rows + ["", f"**{verdict}**"])

    # v1 的教训：这里以前永远 return 0，于是那个绿勾什么都不证明，
    # 还害我据此做了错误判断。有阻塞项就必须让这一步变红。
    return 1 if (critical_down or blockers) else 0


if __name__ == "__main__":
    sys.exit(main())
