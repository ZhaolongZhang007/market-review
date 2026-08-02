#!/usr/bin/env python3
"""market.json 质量门禁。

存在的理由：update_data.py 吞掉所有异常且永远 exit 0——全网断了它也照样
写出一份沿用旧值的 market.json 并成功退出。没有这道门禁，CI 会永远是绿的，
而仪表盘悄悄冻结在几周前。

两道独立的闸：

    python3 check_data_quality.py --gate publish
        够不够格发布？（新鲜数据 + 陈旧数据都发，陈旧的前端有黄条标注；
        但如果连交易日期都不是今天，说明整轮抓取没起作用，不该发）

    python3 check_data_quality.py --gate insights
        值不值得花这次 API 调用？（喂给模型的数据太旧会产出自信的错误评论，
        既花钱又误导——宁可不生成，保留昨天的观点并让前端标注日期不符）

退出码 0=通过，1=不通过。
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SHANGHAI = ZoneInfo("Asia/Shanghai")

# 这些板块决定盘面结论；缺了它们生成的观点就是编的。
CORE_SECTIONS = ["indices", "sentiment", "limitEcosystem"]
# 这些是锦上添花，缺了页面照样有意义。
AUX_SECTIONS = ["hotSectors", "fundFlows", "volumeAnalysis", "valuations", "lhb"]

LIVE_STATES = {"live", "partial"}


def load():
    path = ROOT / "market.json"
    if not path.exists():
        return None, "market.json 不存在"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"market.json 解析失败：{exc}"


def resolve_expected_trading_day():
    """**独立**解析最近交易日，不读 market.json。

    这是这道闸能成立的前提：以前判据是 `market.tradingDate == 今天`，而
    tradingDate 正是 update_data.py 用 now() 写进去的——被检对象自己出具
    证明，判据恒真。全网断线那天 CI 照样绿。
    """
    today = datetime.now(SHANGHAI).strftime("%Y-%m-%d")
    try:
        sys.path.insert(0, str(ROOT))
        import akshare_feeds
        resolved = akshare_feeds.latest_trade_date(today)
        if resolved:
            return resolved, today, True
    except Exception:
        pass
    probe = datetime.now(SHANGHAI)
    while probe.weekday() >= 5:
        probe = probe - timedelta(days=1)
    return probe.strftime("%Y-%m-%d"), today, False


def audit(market):
    """返回 (报告 dict, 问题列表)。"""
    problems = []
    status = market.get("fetchStatus") or {}
    expected_day, today, calendar_trusted = resolve_expected_trading_day()

    trading_date = market.get("tradingDate")
    # 和独立解析出的交易日比对，而不是和"今天"比。
    date_is_today = trading_date == expected_day

    core_live = [s for s in CORE_SECTIONS if (status.get(s) or {}).get("state") in LIVE_STATES]
    core_dead = [s for s in CORE_SECTIONS if s not in core_live]
    aux_live = [s for s in AUX_SECTIONS if (status.get(s) or {}).get("state") in LIVE_STATES]

    # fallback 比 stale 严重得多：stale 是"旧但真实"，fallback 是 DEFAULT_* 里
    # 硬编码的虚构样本（上涨1876/成交3.11万亿）。以前两者同等对待，于是全网
    # 断线那天页面照常显示一份看起来很正常的假数据。
    fabricated = [s for s in CORE_SECTIONS + AUX_SECTIONS
                  if (status.get(s) or {}).get("state") in ("fallback", "missing")]

    # 脏值检查要覆盖 globalMarkets——KOSPI +17.91% 就是从这里漏掉的，
    # 而且不同标的量纲不同，用一个 30% 通吃会放过所有海外指数的异常。
    dirty = []
    for group, limit in (("indices", 12.0), ("globalMarkets", 12.0)):
        for item in market.get(group) or []:
            name = item.get("name")
            value = item.get("value")
            change = item.get("changePercent")
            cap = 3.0 if "人民币" in str(name) else limit   # 汇率日内波动量纲完全不同
            if isinstance(value, (int, float)) and value <= 0:
                dirty.append(f"{name} value={value}")
            if isinstance(change, (int, float)) and abs(change) >= cap:
                dirty.append(f"{name} change={change}%(上限{cap})")

    sentiment = market.get("sentiment") or {}
    try:
        up = int(str(sentiment.get("upCount", 0)).replace(",", ""))
        down = int(str(sentiment.get("downCount", 0)).replace(",", ""))
    except (TypeError, ValueError):
        up = down = 0
    breadth_dead = (up + down) == 0

    if not date_is_today:
        problems.append(f"tradingDate={trading_date}，独立解析的最近交易日是 {expected_day}")
    if core_dead:
        problems.append(f"核心板块未取到最新值：{'、'.join(core_dead)}")
    if fabricated:
        problems.append(f"以下板块在用硬编码占位数据（非真实行情）：{'、'.join(fabricated)}")
    if dirty:
        problems.append(f"存在脏值：{'；'.join(dirty[:4])}")
    if breadth_dead:
        problems.append(f"涨跌家数为 0（上涨{up}/下跌{down}）")
    if not calendar_trusted:
        problems.append("交易日历不可用，交易日判定为兜底推算")

    return {
        "tradingDate": trading_date,
        "expectedDay": expected_day,
        "today": today,
        "dateIsToday": date_is_today,
        "coreLive": core_live,
        "coreDead": core_dead,
        "auxLive": aux_live,
        "auxTotal": len(AUX_SECTIONS),
        "fabricated": fabricated,
        "dirty": dirty,
        "breadthDead": breadth_dead,
    }, problems


def main():
    gate = "publish"
    if "--gate" in sys.argv:
        idx = sys.argv.index("--gate")
        if idx + 1 < len(sys.argv):
            gate = sys.argv[idx + 1]

    market, err = load()
    if err:
        print(f"✗ {err}")
        return 1

    report, problems = audit(market)

    print(f"交易日期  : {report['tradingDate']}  (今天 {report['today']})")
    print(f"核心板块  : {len(report['coreLive'])}/{len(CORE_SECTIONS)} 取到最新值"
          f"  {'✓' if not report['coreDead'] else '✗ 缺:' + '、'.join(report['coreDead'])}")
    print(f"辅助板块  : {len(report['auxLive'])}/{report['auxTotal']} 取到最新值")
    if report["dirty"]:
        print(f"脏值      : {'；'.join(report['dirty'][:5])}")

    if gate == "publish":
        # 发布门槛低：陈旧板块前端有 stale 标注，发出去比空白页诚实。
        # 但三种情况绝不发布：交易日对不上（整轮没起作用）、有脏值、
        # 或核心板块在用硬编码假数据（比空白页更糟——它看起来是真的）。
        blocking = [p for p in problems
                    if "最近交易日是" in p or "脏值" in p or "硬编码占位数据" in p]
        ok = not blocking
        print(f"\n[publish] {'✓ 可以发布' if ok else '✗ 不发布'}")
        for p in blocking:
            print(f"    - {p}")
        return 0 if ok else 1

    if gate == "insights":
        # 生成门槛高：数据不够好就别花这次 API 钱。
        ok = not problems
        print(f"\n[insights] {'✓ 值得生成' if ok else '✗ 跳过生成（保留上一份观点）'}")
        for p in problems:
            print(f"    - {p}")
        return 0 if ok else 1

    print(f"✗ 未知门禁：{gate}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
