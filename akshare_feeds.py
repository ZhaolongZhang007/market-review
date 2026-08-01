#!/usr/bin/env python3
"""AkShare-backed feeds for data the bare eastmoney endpoints don't expose.

Kept in its own module so akshare stays an optional dependency: if it isn't
installed the caller gets a "missing" result instead of a crash, and the rest
of update_data.py still runs on the stdlib-only path.
"""
import re
import socket
import time
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

SHANGHAI = ZoneInfo("Asia/Shanghai")


def _retry(fn, attempts=4, base_delay=1.5):
    last = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - network layer
            last = exc
            if attempt < attempts:
                time.sleep(base_delay * attempt)
    raise last


def available():
    try:
        import akshare  # noqa: F401
    except Exception:
        return False
    return True


def fetch_limit_ecosystem(date_str=None):
    """涨停 / 跌停 / 炸板 生态，使用东方财富官方股池口径。

    Returns a dict with counts plus the derived 连板高度 and 炸板率, or
    {"state": "missing"|"error"} when akshare is unavailable / all pools fail.

    Caliber note: counts come from 东财涨停股池 (stock_zt_pool_em) rather than
    "涨跌幅 >= 9.8%", which over-counts 20cm/30cm boards and near-limit moves.
    """
    try:
        import akshare as ak
    except Exception as exc:
        return {"state": "missing", "detail": f"akshare 未安装：{exc}"}

    date_str = date_str or datetime.now(SHANGHAI).strftime("%Y%m%d")
    result = {"state": "live", "sampleDate": date_str, "caliber": "东方财富涨停股池口径"}
    errors = []

    def pool(fn, label):
        try:
            return _retry(lambda: fn(date=date_str))
        except Exception as exc:
            errors.append(f"{label}: {type(exc).__name__}")
            return None

    zt = pool(ak.stock_zt_pool_em, "涨停池")
    dt = pool(ak.stock_zt_pool_dtgc_em, "跌停池")
    zb = pool(ak.stock_zt_pool_zbgc_em, "炸板池")

    if zt is None and dt is None and zb is None:
        return {"state": "error", "detail": "；".join(errors) or "全部股池抓取失败"}

    if zt is not None:
        result["limitUp"] = int(len(zt))
        # 退市整理股天天涨停，会把连板高度顶到虚高，情绪判断上要剔除。
        tradable = _drop_delisting(zt)
        result["delistingExcluded"] = int(len(zt) - len(tradable))
        boards = _board_counts(tradable)
        if boards:
            result["maxBoard"] = int(max(boards))
            result["multiBoard"] = int(sum(1 for b in boards if b >= 2))
            result["boardLadder"] = _ladder(boards)
            result["consecutiveBoards"] = (
                f"最高{result['maxBoard']}板，2板以上{result['multiBoard']}只"
            )
        result["limitUpLeaders"] = _leaders(tradable)

    if dt is not None:
        result["limitDown"] = int(len(dt))

    if zb is not None:
        result["brokenBoard"] = int(len(zb))

    if zt is not None and zb is not None:
        sealed, broken = len(zt), len(zb)
        total = sealed + broken
        # 只有真有封住的涨停(sealed>0)时算炸板率才有意义；否则 broken/broken=100%
        # 是无意义的（盘前涨停池空、炸板池非空会得到 100%）。
        if sealed > 0 and total:
            rate = broken / total * 100
            result["breakRate"] = f"{rate:.1f}%"
            result["breakRateValue"] = round(rate, 1)

    if errors:
        result["state"] = "partial"
        result["detail"] = "；".join(errors)
    return result



# 乐咕乐股支持的指数（科创50 无数据）。
VALUATION_INDICES = ["上证50", "沪深300", "中证500", "中证1000", "创业板50"]


def fetch_index_valuations(indices=None):
    """指数 PE/PB 及历史分位数。

    分位数是**算出来的**（当前值在全部历史里的百分位），不是手写的"中位偏低"。
    近10年分位另算一份，因为全历史会被早年的极端估值稀释。
    """
    try:
        import akshare as ak
    except Exception as exc:
        return {"state": "missing", "detail": f"akshare 未安装：{exc}", "items": []}

    items, errors = [], []
    for name in (indices or VALUATION_INDICES):
        try:
            pe_df = _retry(lambda: ak.stock_index_pe_lg(symbol=name))
            pb_df = _retry(lambda: ak.stock_index_pb_lg(symbol=name))
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}")
            continue

        entry = {"name": name}
        pe = _last_value(pe_df, "滚动市盈率")
        pb = _last_value(pb_df, "市净率")
        if pe is not None:
            entry["pe"] = f"{pe:.2f}x"
            entry["peValue"] = round(pe, 2)
            entry.update(_percentiles(pe_df, "滚动市盈率", pe, "pe"))
        if pb is not None:
            entry["pb"] = f"{pb:.2f}x"
            entry["pbValue"] = round(pb, 2)
            entry.update(_percentiles(pb_df, "市净率", pb, "pb"))

        as_of = _last_date(pe_df) or _last_date(pb_df)
        if as_of:
            entry["asOf"] = as_of
        if "pePercentile" in entry:
            entry["percentile"] = _percentile_label(entry["pePercentile"])
        entry["source"] = "乐咕乐股指数估值（akshare stock_index_pe_lg / pb_lg）"
        items.append(entry)

    if not items:
        return {"state": "error", "detail": "；".join(errors) or "全部估值抓取失败", "items": []}
    return {
        "state": "partial" if errors else "live",
        "detail": "；".join(errors),
        "items": items,
    }


def _last_value(df, column):
    if column not in df.columns or not len(df):
        return None
    try:
        return float(df[column].dropna().iloc[-1])
    except (IndexError, TypeError, ValueError):
        return None


def _last_date(df):
    if "日期" not in df.columns or not len(df):
        return None
    try:
        return str(df["日期"].iloc[-1])[:10]
    except (IndexError, TypeError):
        return None


def _percentiles(df, column, current, prefix):
    """当前值在历史序列中的百分位：全历史一份，近10年一份。"""
    out = {}
    if column not in df.columns:
        return out
    series = df[column].dropna()
    if not len(series):
        return out
    out[f"{prefix}Percentile"] = round(float((series <= current).sum()) / len(series) * 100, 1)

    if "日期" in df.columns:
        try:
            recent = df.tail(2430)[column].dropna()  # 约10年交易日
            if len(recent) > 250:
                out[f"{prefix}Percentile10y"] = round(float((recent <= current).sum()) / len(recent) * 100, 1)
        except Exception:
            pass
    return out


def _percentile_label(value):
    if value is None:
        return "--"
    if value >= 80:
        return f"高分位（{value}%）"
    if value >= 60:
        return f"中位偏上（{value}%）"
    if value >= 40:
        return f"中位附近（{value}%）"
    if value >= 20:
        return f"中低分位（{value}%）"
    return f"低分位（{value}%）"


def _drop_delisting(zt_df):
    """Exclude 退市整理股 (name contains 退) — they limit up daily and would
    otherwise dominate 最高板 without carrying any sentiment signal."""
    if "名称" not in zt_df.columns:
        return zt_df
    try:
        return zt_df[~zt_df["名称"].astype(str).str.contains("退", na=False)]
    except Exception:
        return zt_df


def _to_board_int(value):
    """连板数 → int. Handles numbers, "N板", and "首板"(=1).

    Text values used to raise and get silently dropped, which erased 首板 stocks
    from the ladder and skewed 最高板/2板以上 downward.
    """
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if text in ("首板", "首", "1板"):
        return 1
    match = re.match(r"^(\d+)\s*板", text)
    if match:
        return int(match.group(1))
    return None


def _board_counts(zt_df):
    """连板数 column is usually int-like but occasionally arrives as text."""
    if "连板数" not in zt_df.columns:
        return []
    counts = []
    for value in zt_df["连板数"].tolist():
        board = _to_board_int(value)
        if board is not None:
            counts.append(board)
    return counts


def _ladder(boards):
    """{连板高度: 家数}, e.g. {"1": 20, "2": 8, "3": 3} — the 连板天梯."""
    ladder = {}
    for board in boards:
        key = str(board)
        ladder[key] = ladder.get(key, 0) + 1
    return dict(sorted(ladder.items(), key=lambda kv: int(kv[0])))


def _leaders(zt_df, limit=6):
    """Highest 连板 stocks, i.e. the 龙头梯队 the dashboard talks about."""
    if not {"名称", "连板数"}.issubset(zt_df.columns):
        return []
    rows = []
    for _, row in zt_df.iterrows():
        rows.append({
            "name": str(row.get("名称", "")),
            "code": str(row.get("代码", "")),
            "board": _to_board_int(row.get("连板数")),
            "sector": str(row.get("所属行业", "")),
        })
    # Sort numerically — the raw column may be text ("首板"), so a pandas
    # sort_values would order lexically and mis-rank the 龙头梯队.
    rows.sort(key=lambda r: (r["board"] if r["board"] is not None else -1), reverse=True)
    return rows[:limit]


# ---------------------------------------------------------------------------
# 多源兜底
#
# push2.eastmoney.com / push2his.eastmoney.com 实测长期不稳定（本地与 GitHub
# Actions 机房都频繁 502 / RemoteDisconnected），而热点板块、行业资金流原本只挂
# 在 push2 上——它一挂那两块就永远沿用旧值。下面几个接口分别走同花顺
# (10jqka) 与新浪，主机与 push2 完全不同，实测两边都通。
#
# 同花顺接口偏慢（实测 13–34 秒），所以重试次数压到 2 次并单独加 socket 超时，
# 免得一次挂起把整个 update_data.py 拖死。
# ---------------------------------------------------------------------------

THS_TIMEOUT = 40          # 单次 socket 读写超时（秒）
SINA_SPOT_TIMEOUT = 30

_INDEX_SPOT_CACHE = None  # 新浪指数全量快照要翻 8 页、约 30 秒，整轮只取一次
_TRADE_DATES_CACHE = None


@contextmanager
def _socket_timeout(seconds):
    """akshare 内部用 requests 且大多数接口不传 timeout，只能用全局 socket 超时兜住。

    本模块是单线程调用，退出时恢复原值，不会影响 update_data.py 里的 urllib 调用
    （那些自己传了 timeout）。
    """
    previous = socket.getdefaulttimeout()
    socket.setdefaulttimeout(seconds)
    try:
        yield
    finally:
        socket.setdefaulttimeout(previous)


def _f(value):
    """单元格 → float / None（NaN、"--"、空串都算 None）。"""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number


def _s(value):
    text = str(value if value is not None else "").strip()
    return "" if text.lower() in ("", "nan", "none", "--") else text


def fetch_industry_board_ths(limit=12):
    """同花顺行业板块涨幅榜——东财 push2 clist 挂掉时的热点板块兜底。

    口径：同花顺二级行业（90 个），和东财的行业板块不是同一套分类，但同为"行业
    板块按当日涨幅排序"，展示口径一致。领涨股由接口直接给出，不需要编造。
    """
    try:
        import akshare as ak
    except Exception as exc:
        return {"state": "missing", "detail": f"akshare 未安装：{exc}", "items": []}

    try:
        with _socket_timeout(THS_TIMEOUT):
            df = _retry(ak.stock_board_industry_summary_ths, attempts=2, base_delay=2.0)
    except Exception as exc:
        return {"state": "error", "detail": f"{type(exc).__name__}: {exc}", "items": []}

    if df is None or not len(df) or "板块" not in getattr(df, "columns", []):
        return {"state": "error", "detail": "同花顺行业板块返回空或列名不符", "items": []}

    rows = []
    for row in df.to_dict("records"):
        name = _s(row.get("板块"))
        change = _f(row.get("涨跌幅"))
        if not name or change is None:
            continue
        rows.append({
            "name": name,
            "changePercent": change,
            "leader": _s(row.get("领涨股")),
            "leaderChange": _f(row.get("领涨股-涨跌幅")),
            "upCount": _f(row.get("上涨家数")),
            "downCount": _f(row.get("下跌家数")),
            "amountYi": _f(row.get("总成交额")),      # 单位：亿元
            "netInflowYi": _f(row.get("净流入")),     # 单位：亿元
        })

    if not rows:
        return {"state": "error", "detail": "同花顺行业板块无有效行", "items": []}

    # 不依赖接口自身的排序，自己按涨幅降序，保证和东财分支同一口径。
    rows.sort(key=lambda item: item["changePercent"], reverse=True)
    return {
        "state": "live",
        "source": "同花顺行业板块（akshare stock_board_industry_summary_ths）",
        "items": rows[:limit],
    }


def fetch_industry_fund_flow_ths(limit=10):
    """同花顺行业资金流（即时）——东财资金流 clist 挂掉时的兜底。

    金额列（流入资金 / 流出资金 / 净额）单位是**亿元**，这里统一换算成元返回，
    好让调用方直接套用现成的 format_amount()。
    """
    try:
        import akshare as ak
    except Exception as exc:
        return {"state": "missing", "detail": f"akshare 未安装：{exc}", "items": []}

    try:
        with _socket_timeout(THS_TIMEOUT):
            df = _retry(lambda: ak.stock_fund_flow_industry(symbol="即时"),
                        attempts=2, base_delay=2.0)
    except Exception as exc:
        return {"state": "error", "detail": f"{type(exc).__name__}: {exc}", "items": []}

    if df is None or not len(df) or "行业" not in getattr(df, "columns", []):
        return {"state": "error", "detail": "同花顺行业资金流返回空或列名不符", "items": []}

    rows = []
    for row in df.to_dict("records"):
        name = _s(row.get("行业"))
        net_yi = _f(row.get("净额"))
        if not name or net_yi is None:
            continue
        inflow_yi = _f(row.get("流入资金"))
        outflow_yi = _f(row.get("流出资金"))
        rows.append({
            "name": name,
            "net": net_yi * 1e8,
            "inflow": inflow_yi * 1e8 if inflow_yi is not None else None,
            "outflow": outflow_yi * 1e8 if outflow_yi is not None else None,
            "changePercent": _f(row.get("行业-涨跌幅")),
            "leader": _s(row.get("领涨股")),
            "companies": _f(row.get("公司家数")),
        })

    if not rows:
        return {"state": "error", "detail": "同花顺行业资金流无有效行", "items": []}

    # 接口按涨跌幅排序，但东财那条链是按主力净流入排序（fid=f62），这里对齐。
    rows.sort(key=lambda item: item["net"], reverse=True)
    return {
        "state": "live",
        "source": "同花顺行业资金流（akshare stock_fund_flow_industry）",
        "items": rows[:limit],
    }


def fetch_index_spot_sina(force=False):
    """新浪指数全量快照（562 个），作为 hq.sinajs.cn 之后的额外一档指数兜底。

    走的是 vip.stock.finance.sina.com.cn，和 hq.sinajs.cn 不是同一个入口，所以
    hq 挂掉时这条仍可能通。整轮缓存（含失败结果）：翻 8 页实测 30 秒上下，失败也
    没必要在同一轮里重试 7 次。
    """
    global _INDEX_SPOT_CACHE
    if _INDEX_SPOT_CACHE is not None and not force:
        return _INDEX_SPOT_CACHE

    try:
        import akshare as ak
    except Exception as exc:
        _INDEX_SPOT_CACHE = {"state": "missing", "detail": f"akshare 未安装：{exc}", "quotes": {}}
        return _INDEX_SPOT_CACHE

    try:
        with _socket_timeout(SINA_SPOT_TIMEOUT):
            df = _retry(ak.stock_zh_index_spot_sina, attempts=2, base_delay=2.0)
    except Exception as exc:
        _INDEX_SPOT_CACHE = {"state": "error", "detail": f"{type(exc).__name__}: {exc}", "quotes": {}}
        return _INDEX_SPOT_CACHE

    quotes = {}
    if df is not None and len(df) and "代码" in getattr(df, "columns", []):
        for row in df.to_dict("records"):
            code = _s(row.get("代码"))
            value = _f(row.get("最新价"))
            if not code or value is None or value <= 0:
                continue
            previous = _f(row.get("昨收"))
            # 自己按 最新价/昨收 反算涨跌幅，避免依赖接口列的口径；算不出来才用原列。
            if previous and previous > 0:
                change = (value - previous) / previous * 100
            else:
                change = _f(row.get("涨跌幅"))
            quotes[code] = {
                "name": _s(row.get("名称")),
                "value": value,
                "previous": previous,
                "changePercent": change,
            }

    if not quotes:
        _INDEX_SPOT_CACHE = {"state": "error", "detail": "新浪指数快照无有效行", "quotes": {}}
        return _INDEX_SPOT_CACHE

    _INDEX_SPOT_CACHE = {
        "state": "live",
        "source": "新浪指数全量快照（akshare stock_zh_index_spot_sina）",
        "quotes": quotes,
    }
    return _INDEX_SPOT_CACHE


def latest_trade_date(today=None):
    """<= today 的最近一个交易日，"YYYY-MM-DD"；取不到返回 None。

    给没有交易日字段的行情源（新浪指数全量快照只给价格）判定新鲜度用——不判断
    就只能一律当 stale，那这档兜底基本白加。
    """
    global _TRADE_DATES_CACHE
    if _TRADE_DATES_CACHE is None:
        try:
            import akshare as ak
            with _socket_timeout(SINA_SPOT_TIMEOUT):
                df = _retry(ak.tool_trade_date_hist_sina, attempts=2, base_delay=1.5)
            _TRADE_DATES_CACHE = sorted({str(value)[:10] for value in df["trade_date"].tolist()})
        except Exception:
            _TRADE_DATES_CACHE = []

    if not _TRADE_DATES_CACHE:
        return None
    today = today or datetime.now(SHANGHAI).strftime("%Y-%m-%d")
    past = [date for date in _TRADE_DATES_CACHE if date <= today]
    return past[-1] if past else None


if __name__ == "__main__":
    import json
    import sys

    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(fetch_limit_ecosystem(date_arg), ensure_ascii=False, indent=2))
