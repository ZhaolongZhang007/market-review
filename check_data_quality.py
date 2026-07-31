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
from datetime import datetime
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


def audit(market):
    """返回 (报告 dict, 问题列表)。"""
    problems = []
    status = market.get("fetchStatus") or {}
    today = datetime.now(SHANGHAI).strftime("%Y-%m-%d")

    trading_date = market.get("tradingDate")
    date_is_today = trading_date == today

    core_live = [s for s in CORE_SECTIONS if (status.get(s) or {}).get("state") in LIVE_STATES]
    core_dead = [s for s in CORE_SECTIONS if s not in core_live]
    aux_live = [s for s in AUX_SECTIONS if (status.get(s) or {}).get("state") in LIVE_STATES]

    # 脏值检查：0 或荒谬涨幅说明前面修好的防御被绕过了。
    dirty = []
    for item in market.get("indices") or []:
        value = item.get("value")
        change = item.get("changePercent")
        if value is not None and isinstance(value, (int, float)) and value <= 0:
            dirty.append(f"{item.get('name')} value={value}")
        if change is not None and isinstance(change, (int, float)) and abs(change) >= 30:
            dirty.append(f"{item.get('name')} change={change}%")

    sentiment = market.get("sentiment") or {}
    try:
        up = int(str(sentiment.get("upCount", 0)).replace(",", ""))
        down = int(str(sentiment.get("downCount", 0)).replace(",", ""))
    except (TypeError, ValueError):
        up = down = 0
    breadth_dead = (up + down) == 0

    if not date_is_today:
        problems.append(f"tradingDate={trading_date} 不是今天({today})")
    if core_dead:
        problems.append(f"核心板块未取到最新值：{'、'.join(core_dead)}")
    if dirty:
        problems.append(f"存在脏值：{'；'.join(dirty[:4])}")
    if breadth_dead:
        problems.append(f"涨跌家数为 0（上涨{up}/下跌{down}）")

    return {
        "tradingDate": trading_date,
        "today": today,
        "dateIsToday": date_is_today,
        "coreLive": core_live,
        "coreDead": core_dead,
        "auxLive": aux_live,
        "auxTotal": len(AUX_SECTIONS),
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
        # 发布门槛低：只要这轮抓取确实针对今天跑过就发。
        # 陈旧板块前端已有 stale 标注，发出去比空白页诚实。
        blocking = [p for p in problems if "不是今天" in p or "脏值" in p]
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
