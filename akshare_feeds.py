#!/usr/bin/env python3
"""AkShare-backed feeds for data the bare eastmoney endpoints don't expose.

Kept in its own module so akshare stays an optional dependency: if it isn't
installed the caller gets a "missing" result instead of a crash, and the rest
of update_data.py still runs on the stdlib-only path.
"""
import re
import time
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


if __name__ == "__main__":
    import json
    import sys

    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(fetch_limit_ecosystem(date_arg), ensure_ascii=False, indent=2))
