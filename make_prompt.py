#!/usr/bin/env python3
"""Build the chat prompt that turns market.json facts into insights.json.

No LLM API involved: this writes prompt.txt (and copies it to the clipboard on
macOS). Paste it into any chat, then feed the reply to save_insights.py.
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SHANGHAI = ZoneInfo("Asia/Shanghai")


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def pct(value):
    return value if value not in (None, "") else "--"


def build_digest(market):
    """Compact, facts-only view of the trading day.

    Deliberately excludes anything previously generated (stockPool,
    tradingAdvice, events…) so the model can't launder yesterday's opinions
    back in as if they were data.
    """
    lines = []
    add = lines.append

    add(f"交易日：{market.get('tradingDateText') or market.get('tradingDate')}")
    add(f"行情状态：{market.get('marketStatus', '--')}｜两市成交额：{market.get('turnoverText', '--')}")

    status = market.get("fetchStatus") or {}
    stale = [k for k, v in status.items() if v.get("state") in ("stale", "partial", "fallback", "missing")]
    if stale:
        add("")
        add("⚠️ 数据新鲜度警告：以下板块本次未能抓到最新数据，可能沿用上一交易日的值——")
        for key in stale:
            info = status[key]
            add(f"  - {key}：{info.get('state')}｜{info.get('detail') or '无细节'}")
        add("  评论时请勿把上述板块的数字当作今日真实情况，必要时明确指出该项数据缺失。")

    add("")
    add("【指数】")
    for item in market.get("indices", []):
        flag = "（数据陈旧，非今日）" if item.get("stale") else ""
        add(f"  {item.get('name')}: {item.get('valueText')} {item.get('changeText')}{flag}")

    globals_ = market.get("globalMarkets", [])
    if globals_:
        add("")
        add("【外围市场】")
        for item in globals_:
            flag = "（数据陈旧）" if item.get("stale") else ""
            add(f"  {item.get('name')}: {item.get('valueText')} {item.get('changeText')}{flag}")

    sentiment = market.get("sentiment") or {}
    add("")
    add("【市场宽度与涨停生态】")
    add(f"  上涨 {sentiment.get('upCount', '--')} 家｜下跌 {sentiment.get('downCount', '--')} 家")
    add(f"  涨停 {sentiment.get('limitUp', '--')} 家｜跌停 {sentiment.get('limitDown', '--')} 家"
        f"｜炸板率 {sentiment.get('breakRate', '--')}")
    add(f"  连板情况：{sentiment.get('consecutiveBoards', '--')}")
    if sentiment.get("boardLadder"):
        ladder = "、".join(f"{k}板 {v}只" for k, v in sentiment["boardLadder"].items())
        add(f"  连板天梯：{ladder}")
    if sentiment.get("limitUpLeaders"):
        leaders = "、".join(
            f"{x.get('name')}({x.get('board')}板/{x.get('sector')})"
            for x in sentiment["limitUpLeaders"]
        )
        add(f"  涨停梯队龙头：{leaders}")
    add(f"  统计口径：{sentiment.get('limitCaliber', '--')}")

    volume = market.get("volumeAnalysis") or {}
    if volume:
        add("")
        add("【成交量】")
        add(f"  今日 {volume.get('today', '--')}｜上一交易日 {volume.get('previous', '--')}"
            f"｜变化 {volume.get('change', '--')}")

    sectors = market.get("hotSectors", [])
    if sectors:
        add("")
        add("【板块涨幅榜】（strength = 50 + 5×涨幅%，仅由涨幅线性换算，不含其他信息）")
        for item in sectors:
            leaders = "、".join(item.get("leaders", [])[:3])
            add(f"  {item.get('rank')}. {item.get('name')} {item.get('changeText')}"
                f"｜强度 {item.get('strength')}｜龙头 {leaders}")

    flows = market.get("fundFlows", [])
    if flows:
        add("")
        add("【主力资金流向】")
        for item in flows:
            add(f"  {item.get('name')}: {item.get('valueText')}｜{item.get('summary', '')}")

    valuations = market.get("valuations", [])
    if valuations:
        add("")
        add("【指数估值】（分位数由历史序列计算，非主观判断）")
        for item in valuations:
            parts = [f"  {item.get('name')}: PE(TTM) {pct(item.get('pe'))}｜PB {pct(item.get('pb'))}"]
            if item.get("pePercentile") is not None:
                parts.append(f"｜PE全历史分位 {item['pePercentile']}%")
            if item.get("pePercentile10y") is not None:
                parts.append(f"｜近10年分位 {item['pePercentile10y']}%")
            if item.get("stale"):
                parts.append("（数据陈旧，非今日）")
            elif item.get("asOf"):
                parts.append(f"｜数据日期 {item['asOf']}")
            add("".join(parts))

    lhb = market.get("lhb", [])
    if lhb:
        add("")
        add("【龙虎榜】")
        for item in lhb[:10]:
            add(f"  {item.get('name')} {item.get('changeText', '')}"
                f"｜净额 {item.get('netAmountText', '--')}｜{item.get('reason', '')}")

    return "\n".join(lines)


def build_prompt(market, masters_cfg, schema):
    digest = build_digest(market)
    roster = "\n".join(
        f"  - {m['name']}（{m['category']}）：{m['style']}"
        for m in masters_cfg["masters"]
    )
    trading_date = market.get("tradingDate")

    return f"""你是一名 A 股盘后复盘助手。下面是某个交易日的**客观盘面数据**，请据此生成一份结构化的复盘洞察。

================ 盘面数据（唯一事实来源）================
{digest}
========================================================

================ 大师人设名单 ================
请让下列人物分别以各自的交易风格点评当日盘面。每人只说自己风格关心的东西——
价值派不该讨论连板高度，情绪派不该讨论自由现金流。观点之间应当出现真实分歧，
不要让所有人都得出同一个结论。

{roster}
==============================================

================ 硬性要求 ================
1. **只使用上面给出的数据**。不得引入任何未在数据中出现的个股、板块、指数或数字。
   如果某项数据标注了"数据陈旧"或出现在新鲜度警告里，不要拿它当今日事实，
   可以在相应位置说明该数据缺失。
2. 每条点评都要落到具体数字或具体板块，禁止"注意风险""保持谨慎"这类空话。
3. `consensus.agreementPct` 必须由你自己在 masters 里的点名统计得出：
   被点名最多的标的的得票数 ÷ 给出 picks 的大师人数 × 100，四舍五入取整。
   不要凭感觉写一个好看的百分比。
4. `stockPool` 里的个股必须来自上面出现过的板块龙头、涨停梯队或龙虎榜名单。
5. 只输出 JSON，不要输出任何解释文字、不要用 markdown 代码块包裹。
6. `tradingDate` 必须严格填写为 "{trading_date}"。
==========================================

================ 输出格式 ================
严格按以下结构输出（字段含义见注释，实际输出不要带注释）：

{json.dumps(schema_example(schema, trading_date), ensure_ascii=False, indent=2)}
==========================================

现在开始，直接输出 JSON："""


def schema_example(schema, trading_date):
    """A filled-in skeleton — models follow a concrete example far better than prose."""
    return {
        "tradingDate": trading_date,
        "styleVerdict": {
            "title": "小票弱于权重，价值防守占优",
            "summary": "引用具体数字说明风格判定依据",
            "tags": ["防守", "缩量"],
        },
        "sectorReads": [
            {"name": "（来自板块涨幅榜的板块名）", "reason": "该板块走强/走弱的原因", "sustainability": "中"}
        ],
        "masters": [
            {
                "name": "（来自大师名单）",
                "quote": "以该大师口吻的一句点评，落到具体数字或板块",
                "tags": ["关键词1", "关键词2"],
                "picks": ["点名的标的"],
            }
        ],
        "consensus": {
            "agreementPct": 0,
            "note": "共识说明",
            "picks": [{"name": "标的名", "code": "代码", "votes": 0}],
        },
        "tradingAdvice": {
            "summary": "明日策略总结",
            "shortTerm": ["短线要点"],
            "midTerm": ["中线要点"],
            "riskControl": "风控纪律",
        },
        "stockPool": [
            {
                "code": "600000",
                "name": "标的名",
                "sector": "所属板块",
                "action": "回踩关注",
                "horizon": "短线",
                "logic": "入选逻辑",
                "risk": "风险点",
            }
        ],
        "abnormalMoves": [
            {"type": "逆势股", "items": ["个股名"], "note": "说明"}
        ],
        "eventReads": [
            {"type": "政策", "title": "事件描述", "impactedStocks": ["受影响标的"]}
        ],
    }


def copy_to_clipboard(text):
    for cmd in (["pbcopy"], ["xclip", "-selection", "clipboard"], ["wl-copy"]):
        try:
            subprocess.run(cmd, input=text.encode("utf-8"), check=True)
            return cmd[0]
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return None


def main():
    market = load("market.json")
    masters_cfg = load("config/masters.json")
    schema = load("config/insights_schema.json")

    prompt = build_prompt(market, masters_cfg, schema)
    out = ROOT / "prompt.txt"
    out.write_text(prompt, encoding="utf-8")

    tool = copy_to_clipboard(prompt)
    print(f"已写入 {out}（{len(prompt)} 字符）")
    if tool:
        print(f"已用 {tool} 复制到剪贴板，直接粘进 chat 即可。")
    else:
        print("未找到剪贴板工具，请手动打开 prompt.txt 复制。")
    print(f"行情日期：{market.get('tradingDate')}")

    status = market.get("fetchStatus") or {}
    stale = [k for k, v in status.items() if v.get("state") != "live"]
    if stale:
        print(f"注意：以下数据非本次实时抓取，已在 prompt 中标注 → {'、'.join(stale)}")
    print("\n拿到模型回复后运行：  python3 save_insights.py   （会读剪贴板）")


if __name__ == "__main__":
    sys.exit(main())
