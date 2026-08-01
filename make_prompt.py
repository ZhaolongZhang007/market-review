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
1. **只使用上面给出的数据**。个股只能取自上面出现过的板块龙头、涨停梯队或龙虎榜名单，
   不得引入任何未在数据中出现的个股、板块、指数或数字。如果某项数据标注了"数据陈旧"
   或出现在新鲜度警告里，不要拿它当今日事实，可以在相应位置说明该数据缺失。
2. 每条点评都要落到具体数字或具体板块，禁止"注意风险""保持谨慎"这类空话。
3. `consensus.note` 里的票数说明要与 masters 里的实际点名一致：
   被点名最多的标的的得票数 ÷ 给出 picks 的大师人数 × 100 就是 agreementPct。
==========================================

================ 输出格式 ================
严格按以下结构输出。**下面示例的详略程度、句子长度就是期望的输出长度**，请照此写满；
但示例取自另一个交易日，其中的个股、板块、数字一律不得出现在你的输出里，
除非它们同样出现在今天的盘面数据中。

{json.dumps(schema_example(schema, trading_date), ensure_ascii=False, indent=2)}
==========================================

现在开始，直接输出 JSON："""


def schema_example(schema, trading_date):
    """A filled-in skeleton — models follow a concrete example far better than prose.

    Every string here is real prose from an accepted run, sized to roughly 85%
    of that field's cap. This matters more than it looks: models imitate the
    LENGTH of an example far more reliably than they obey a number in a rule
    ("最多 220 字"). The previous version used 10-character placeholders like
    "引用具体数字说明风格判定依据" against a 220-character cap, and got
    10-character answers. Keep these long; shortening them shortens the output.
    """
    return {
        "tradingDate": trading_date,
        "styleVerdict": {
            "title": "小票普涨、科创杀跌，电力设备接棒主线",
            "summary": (
                "上涨4259家对下跌1208家、跌停仅2家，中证2000+1.67%强于上证50-0.41%，风格明显偏中小市值；"
                "科创50-3.78%单独崩塌，与纳斯达克-1.70%共振。成交2.21万亿、放量23.41%，炸板率17.7%，"
                "涨停116家、最高6板，强势集中在输变电设备+8.72%、锂+7.30%、白银+6.58%三条线上。"
                "主力资金流本次未更新，微盘股为陈旧值，两项均不作为今日依据。"
            ),
            "tags": ["小票占优", "放量", "科创杀跌", "电力设备"],
        },
        "sectorReads": [
            {
                "name": "输变电设备",
                "reason": (
                    "+8.72%、强度93.6居首，龙头顺钠股份；同链条的电网设备+6.57%、线缆部件+7.04%、"
                    "配电设备+5.76%同步走强，并由长缆科技3板落地，是涨幅与连板高度双确认的方向。"
                ),
                "sustainability": "高",
            },
            {
                "name": "白银",
                "reason": (
                    "+6.58%、龙头盛达资源做到3板，兴业银锡龙虎榜净买2.64亿、4家机构买入，"
                    "属涨幅榜与真金白银封板、机构席位三重印证；贵金属资金流未更新，无法再作确认。"
                ),
                "sustainability": "中",
            },
        ],
        "masters": [
            {
                "name": "沃伦·巴菲特",
                "quote": (
                    "上证50 PE11.68x、近10年分位已到89.1%，沪深300分位85.7%——安全边际越来越薄；"
                    "输变电设备涨8.72%的热闹，与一门生意的长期现金流无关。"
                ),
                "tags": ["安全边际", "拒绝追高"],
                "picks": [],
            },
            {
                "name": "赵老哥",
                "quote": (
                    "只做最强的那一只：立新能源6板，天梯5板是空的、4板只有美利云一只，"
                    "资金合力全押在它身上；后排那101只首板一个都不碰。"
                ),
                "tags": ["最强龙头", "资金合力"],
                "picks": ["立新能源"],
            },
        ],
        "consensus": {
            "agreementPct": 25,
            "note": (
                "12位大师给出个股，立新能源3票最高（利弗莫尔、赵老哥、乔帮主），3÷12=25%，共识很弱。"
                "分歧明显：伍德在科创50-3.78%里加仓托伦斯，芒格用同一组数字论证不碰；"
                "另有5人因上证50分位89.1%、跌停仅2家而干脆不给个股。"
            ),
            "picks": [
                {"name": "立新能源", "code": "001258", "votes": 3},
                {"name": "盛达资源", "code": "000603", "votes": 1},
            ],
        },
        "tradingAdvice": {
            "summary": (
                "今日是放量普涨（成交2.21万亿、+23.41%，上涨4259家、跌停2家）叠加科创50-3.78%的结构性杀跌，"
                "资金从科创半导体撤向电力设备与有色。明日主攻电力设备链（输变电+8.72%、电网设备+6.57%，"
                "长缆科技3板）与贵金属（白银+6.58%，盛达资源3板、兴业银锡机构净买2.64亿）；"
                "主力资金流本次未更新，不得作为加仓依据。"
            ),
            "shortTerm": [
                "电力设备是涨幅与连板双确认的主线：盯长缆科技3板与顺钠股份，板块内首板数量继续扩张则可接力，明日无新增涨停则视为一日游。",
                "炸板率回落到17.7%、跌停仅2家，打板环境改善，可恢复接力；若炸板率重回30%以上立即改低吸或空仓。",
                "天梯5板缺档（6板1只、4板1只），立新能源孤高6板缺乏承接梯队，只做龙头不做卡位，断板当日出清。",
            ],
            "midTerm": [
                "上证50 PE11.68x（近10年分位89.1%）、沪深300 13.86x（85.7%）、中证500 29.53x（84.8%）三项分位均处高位，权重与中盘中线不宜整体加仓。",
                "创业板50 PE37.89x但全历史分位仅28.0%，是估值分位最低的宽基，中线可自下而上选个股而非追指数，注意PB仍有6.96x。",
                "锂+7.30%、能源金属+6.42%、电池化学品+5.68%构成完整链条，若后续出现连板个股可升级为中线跟踪，目前仅有单日涨幅支撑。",
            ],
            "riskControl": (
                "主力资金流本次未更新、数字与上一交易日完全重合，微盘股指数亦为陈旧值，二者一律不作决策输入；"
                "跌停仅2家、上涨4259家属情绪偏热区间，仓位不超过七成；立新能源6板高位不参与新买入，断板即视为主线终结；"
                "科创50-3.78%尚未止跌，科技类持仓单只亏损5%无条件止损。"
            ),
        },
        "stockPool": [
            {
                "code": "001258",
                "name": "立新能源",
                "sector": "电力",
                "action": "持有不加",
                "horizon": "短线",
                "logic": (
                    "全场最高票（3票），6板为唯一最高标，电力主线旗手，放量23.41%的环境下资金合力集中在它身上。"
                ),
                "risk": (
                    "天梯5板缺档、4板仅美利云1只，接力链条断裂，一旦断板没有承接盘，次日容易直接低开走弱。"
                ),
            },
            {
                "code": "002879",
                "name": "长缆科技",
                "sector": "电网设备",
                "action": "回踩关注",
                "horizon": "短线",
                "logic": (
                    "3板，同时是线缆部件（+7.04%）板块龙头，是板块涨幅榜与连板梯队重合度最高的一只个股。"
                ),
                "risk": (
                    "3板位置已不低，若输变电设备次日不能延续+8.72%的强度，容易高开低走变成情绪兑现的出货位。"
                ),
            },
        ],
        "abnormalMoves": [
            {
                "type": "逆势股",
                "items": ["托伦斯", "九安医疗", "万邦医药"],
                "note": (
                    "普涨中逆势杀跌：托伦斯-8.64%、龙虎榜1.23亿由3家机构卖出；九安医疗-10.00%、"
                    "3家机构卖出2491.52万；万邦医药-2.91%，西藏资金卖出858.12万。"
                ),
            }
        ],
        "eventReads": [
            {
                "type": "产业",
                "title": (
                    "电力设备链全面走强：输变电设备+8.72%、线缆部件+7.04%、电网设备+6.57%、"
                    "逆变器+5.93%、配电设备+5.76%五个细分同榜，并由长缆科技3板落地确认。"
                ),
                "impactedStocks": ["顺钠股份", "长缆科技", "德业股份"],
            }
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
