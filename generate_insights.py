#!/usr/bin/env python3
"""无人值守生成 insights.json —— 调用 Claude API，取代 daily.sh 里的人工粘贴。

分层防御（每层管上一层管不了的事）：

  1. API 层  output_config.format 强制 JSON 结构；tradingDate 用 const、
             大师名和个股用 enum 锁死。结构性错误在这一层变成不可能。
  2. 确定性层 normalize.py 把 API 管不了的边界（字数上限、数组条数、
             派生数字）修成合规——**截断接受，不重试**。
  3. 断言层  Validator 在 normalize 之后跑。此时再报错说明是我们的 bug，
             不是模型输出差，所以硬失败。

花钱的重试只留给三件事：截断、拒答、传输错误，且**每天最多 2 次调用**。

    python3 generate_insights.py            # 正常生成
    python3 generate_insights.py --dry-run  # 不调 API，只验证 prompt 和 schema

环境变量：ANTHROPIC_API_KEY（必需）、ANTHROPIC_MODEL（默认 claude-sonnet-5）
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import normalize
import schema_build
from make_prompt import build_prompt
from save_insights import Validator

ROOT = Path(__file__).resolve().parent
SHANGHAI = ZoneInfo("Asia/Shanghai")

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

# 硬上限。一天最多两次调用——重试是无人值守下最容易失控的成本项，
# 指数退避循环会在没人看着的时候把账单翻几倍。
MAX_CALLS = 2

# 首次尝试：32000 足够容纳 schema 打满的输出（约 8–13k）加上 thinking。
# 上限高不额外花钱（按实际生成量计费），但截断要重付一整次。
FIRST = {"max_tokens": 32000, "effort": "medium"}
RETRY = {"max_tokens": 64000, "effort": "low"}

# 美元 / 百万 token。仅用于日志里的成本提示，不影响逻辑。
PRICING = {
    "claude-opus-5": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),   # 2026-08-31 前有 $2/$10 优惠价
    "claude-haiku-4-5": (1.0, 5.0),
}


def load_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def estimate_cost(usage):
    rate_in, rate_out = PRICING.get(MODEL, (0.0, 0.0))
    cost = (usage.input_tokens * rate_in + usage.output_tokens * rate_out) / 1_000_000
    return cost


def describe_usage(usage):
    return (f"输入 {usage.input_tokens:,} tok｜输出 {usage.output_tokens:,} tok"
            f"｜约 ${estimate_cost(usage):.3f}")


def call_model(client, messages, api_schema, knobs):
    """一次 API 调用。返回 (response, text)；text 在被截断时为 None。"""
    # max_tokens 这么大必须流式——SDK 会拒绝它预估会超时的非流式请求。
    with client.messages.stream(
        model=MODEL,
        max_tokens=knobs["max_tokens"],
        output_config={
            "effort": knobs["effort"],
            "format": {"type": "json_schema", "schema": api_schema},
        },
        messages=messages,
    ) as stream:
        response = stream.get_final_message()

    # 解析前先看 stop_reason。结构化输出下，完整响应的第一个 text block
    # 一定是合法 JSON；被截断的不是，硬解析会得到误导性的报错。
    if response.stop_reason in ("max_tokens", "refusal"):
        return response, None

    text = next((b.text for b in response.content if b.type == "text"), None)
    return response, text


def build_schema(market, insights_schema, masters_cfg, simple=False):
    """simple=True 时退掉 universe enum，用于 grammar 过大时降级。"""
    notes = []
    if simple:
        # 不传 market 的龙头名单，universe 为空 → 相关字段退回普通 string
        stripped = dict(market)
        stripped["hotSectors"] = []
        stripped["lhb"] = []
        api_schema, bounds, universe = schema_build.build_api_schema(
            insights_schema, stripped, masters_cfg, notes)
    else:
        api_schema, bounds, universe = schema_build.build_api_schema(
            insights_schema, market, masters_cfg, notes)
    schema_build.assert_api_safe(api_schema)
    return api_schema, bounds, universe, notes


def write_error(attempts, reason):
    payload = {
        "failedAt": datetime.now(SHANGHAI).isoformat(),
        "model": MODEL,
        "reason": reason,
        "attempts": attempts,
    }
    (ROOT / "insights.error.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    dry_run = "--dry-run" in sys.argv

    market = load_json("market.json")
    insights_schema = load_json("config/insights_schema.json")
    masters_cfg = load_json("config/masters.json")

    trading_date = market.get("tradingDate")
    print(f"交易日 {trading_date}｜模型 {MODEL}")

    api_schema, bounds, universe, notes = build_schema(market, insights_schema, masters_cfg)
    prompt = build_prompt(market, masters_cfg, insights_schema)
    print(f"schema 编译通过｜universe {len(universe)} 个标的｜边界 {len(bounds)} 条"
          f"｜prompt {len(prompt):,} 字符")
    for note in notes:
        print(f"  · {note}")

    if dry_run:
        print("\n[dry-run] 不调用 API。")
        (ROOT / "prompt.txt").write_text(prompt, encoding="utf-8")
        (ROOT / "api_schema.debug.json").write_text(
            json.dumps(api_schema, ensure_ascii=False, indent=2), encoding="utf-8")
        print("已写出 prompt.txt 与 api_schema.debug.json 供检查。")
        return 0

    try:
        import anthropic
    except ImportError:
        print("✗ 未安装 anthropic SDK：pip install anthropic")
        return 1
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("✗ 未设置 ANTHROPIC_API_KEY")
        return 1

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": prompt}]
    attempts = []
    knobs = FIRST
    total_cost = 0.0

    for call in range(1, MAX_CALLS + 1):
        print(f"\n── 第 {call}/{MAX_CALLS} 次调用"
              f"（max_tokens={knobs['max_tokens']}, effort={knobs['effort']}）")
        try:
            response, text = call_model(client, messages, api_schema, knobs)
        except Exception as exc:
            detail = f"{type(exc).__name__}: {str(exc)[:200]}"
            print(f"  ✗ 调用失败：{detail}")
            attempts.append({"call": call, "outcome": "api_error", "detail": detail})

            # grammar 过大是 400，重试同样的 schema 只会再失败一次。
            # 降级成不带 universe enum 的 schema 再试。
            if "grammar" in str(exc).lower() and call < MAX_CALLS:
                print("  → schema 编译过大，降级为不含 universe enum 的版本重试")
                api_schema, bounds, universe, _ = build_schema(
                    market, insights_schema, masters_cfg, simple=True)
                continue
            if call < MAX_CALLS:
                knobs = RETRY
                continue
            write_error(attempts, "API 调用连续失败")
            return 1

        cost = estimate_cost(response.usage)
        total_cost += cost
        print(f"  stop_reason={response.stop_reason}｜{describe_usage(response.usage)}")

        # ── 桶 C：截断 / 拒答 → 唯一值得花钱重试的情况 ──────────
        if text is None:
            reason = response.stop_reason
            print(f"  ✗ {'输出被截断' if reason == 'max_tokens' else '模型拒答'}")
            attempts.append({"call": call, "outcome": reason})
            if call < MAX_CALLS:
                knobs = RETRY
                # 点名上次的具体缺陷。保持 messages[0] 逐字节不变。
                messages = [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "（上次输出未完成）"},
                    {"role": "user", "content":
                     "上次输出因超长被截断。请压缩每条 logic / quote 到更短，"
                     "确保 JSON 完整闭合，其余要求不变。"}
                    if reason == "max_tokens" else
                    {"role": "user", "content": "请基于给定的盘面数据重新输出完整 JSON。"},
                ]
                continue
            write_error(attempts, f"两次调用均未产出完整输出（{reason}）")
            return 1

        # ── 桶 A：软边界 → normalize 确定性修好，绝不重试 ────────
        data = json.loads(text)
        data, report = normalize.normalize(data, market, bounds, masters_cfg, attempts=call)
        print(f"  归一化：{normalize.summarize(report)}")

        # ── 桶 B：结构/语义错 → 走了 API schema 就不该发生 ──────
        # 到这一步还失败，说明 schema 编译或 normalize 有 bug，
        # 重试只是花钱重犯同一个错。硬失败。
        validator = Validator(insights_schema, masters_cfg)
        validator.check(data)
        if validator.errors:
            print(f"  ✗ 归一化后仍未通过校验（{len(validator.errors)} 处）——"
                  f"这是 schema_build/normalize 的 bug，不是模型问题：")
            for err in validator.errors[:8]:
                print(f"      · {err}")
            attempts.append({"call": call, "outcome": "validator_failed",
                             "errors": validator.errors[:20]})
            write_error(attempts, "归一化后校验失败（内部 bug）")
            return 1

        now = datetime.now(SHANGHAI)
        data["generatedAt"] = now.isoformat()
        data["generatedAtText"] = now.strftime("%Y-%m-%d %H:%M")
        data["generator"] = f"api:{MODEL}"
        data["qualityReport"] = report

        (ROOT / "insights.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "insights.error.json").unlink(missing_ok=True)

        masters = data.get("masters") or []
        pool = data.get("stockPool") or []
        print(f"\n✅ 已写入 insights.json")
        print(f"   交易日 {data.get('tradingDate')}｜大师观点 {len(masters)} 条｜"
              f"股票池 {len(pool)} 只")
        print(f"   风格判定：{(data.get('styleVerdict') or {}).get('title', '--')}")
        print(f"   本次成本约 ${total_cost:.3f}（{call} 次调用）")
        return 0

    write_error(attempts, "超出调用预算")
    return 1


if __name__ == "__main__":
    sys.exit(main())
