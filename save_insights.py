#!/usr/bin/env python3
"""Parse a chat reply into insights.json.

Reads the clipboard by default, or a file / stdin. Tolerates the wrappers chat
UIs add (```json fences, a sentence of preamble, trailing commentary) and
refuses to write anything that fails schema validation — a half-valid file is
worse than no file, because the dashboard would render it as real analysis.

  python3 save_insights.py               # from clipboard
  python3 save_insights.py reply.txt     # from a file
  cat reply.txt | python3 save_insights.py -
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SHANGHAI = ZoneInfo("Asia/Shanghai")


def read_clipboard():
    for cmd in (["pbpaste"], ["xclip", "-selection", "clipboard", "-o"], ["wl-paste"]):
        try:
            result = subprocess.run(cmd, capture_output=True, check=True)
            return result.stdout.decode("utf-8", errors="replace")
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return ""


def extract_json(text):
    """Pull the first balanced JSON object out of arbitrary chat output.

    Handles: bare JSON, ```json fenced blocks, prose before/after, and nested
    braces inside string values (a naive rfind('}') would truncate those).
    """
    if not text or not text.strip():
        raise ValueError("输入为空")

    # Search fenced-block bodies first (the model's own delimiter), then the raw
    # text. In each region, try EVERY balanced {...} object and return the first
    # that parses to a dict. This tolerates: a stray '{' in preamble prose,
    # trailing commentary inside a fence, and multiple ``` blocks.
    regions = [body for body in re.findall(r"```[^\n]*\n(.*?)```", text, re.S)]
    regions.append(text)

    saw_object = False
    for region in regions:
        for candidate in _iter_balanced_objects(region):
            saw_object = True
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

    if text.find("{") == -1:
        raise ValueError("没找到 JSON 对象（输入里没有 '{'）")
    if not saw_object:
        raise ValueError("JSON 花括号不配平，回复可能被截断了——让模型重新输出完整 JSON")
    raise ValueError("找到了花括号但都无法解析为合法 JSON 对象——让模型只输出纯 JSON")


def _iter_balanced_objects(text):
    """Yield every top-level balanced {...} substring, ignoring braces in strings."""
    depth = 0
    start = None
    in_string = False
    escaped = False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    yield text[start:index + 1]
                    start = None


class Validator:
    def __init__(self, schema, masters_cfg):
        self.spec = schema["root"]
        self.master_names = {m["name"] for m in masters_cfg["masters"]}
        self.errors = []

    def fail(self, path, message):
        self.errors.append(f"{path}: {message}")

    def check(self, data):
        if not isinstance(data, dict):
            self.fail("root", "顶层必须是 JSON 对象")
            return
        for key in self.spec["required"]:
            if key not in data or data[key] in (None, "", [], {}):
                self.fail(key, "必填字段缺失或为空")
        for key, value in data.items():
            field = self.spec["fields"].get(key)
            if field:
                self._field(key, value, field)
        self._masters(data.get("masters"))
        return not self.errors

    def _field(self, path, value, spec):
        expected = spec.get("type")
        if expected == "string":
            if not isinstance(value, str):
                return self.fail(path, f"应为字符串，实际是 {type(value).__name__}")
            max_len = spec.get("maxLength")
            if max_len and len(value) > max_len:
                self.fail(path, f"长度超限：最多 {max_len} 字，实际 {len(value)} 字")
            min_len = spec.get("minLength")
            if min_len and len(value) < min_len:
                self.fail(path, f"长度不足：至少 {min_len} 字")
            pattern = spec.get("pattern")
            if pattern and not re.match(pattern, value):
                self.fail(path, f"格式不符（须匹配 {pattern}），实际 {value!r}")
        if expected == "number":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return self.fail(path, f"应为数字，实际是 {type(value).__name__}")
            if spec.get("min") is not None and value < spec["min"]:
                self.fail(path, f"不得小于 {spec['min']}，实际 {value}")
            if spec.get("max") is not None and value > spec["max"]:
                self.fail(path, f"不得大于 {spec['max']}，实际 {value}")
        if expected == "array":
            if not isinstance(value, list):
                return self.fail(path, f"应为数组，实际是 {type(value).__name__}")
            if spec.get("maxItems") and len(value) > spec["maxItems"]:
                self.fail(path, f"最多 {spec['maxItems']} 项，实际 {len(value)} 项")
            if spec.get("minItems") and len(value) < spec["minItems"]:
                self.fail(path, f"至少 {spec['minItems']} 项，实际 {len(value)} 项")
            item_spec = spec.get("items")
            if isinstance(item_spec, dict):
                for i, item in enumerate(value):
                    self._object(f"{path}[{i}]", item, item_spec)
            elif item_spec == "string":
                # 元素声明为 string（tags/picks/shortTerm…）时逐个校验类型，
                # 否则 [null, 123, {...}] 会蒙混过关，前端渲染出 null。
                for i, item in enumerate(value):
                    if not isinstance(item, str):
                        self.fail(f"{path}[{i}]", f"数组元素应为字符串，实际是 {type(item).__name__}")
        if expected == "object":
            self._object(path, value, spec)
        if spec.get("enum") and value not in spec["enum"]:
            self.fail(path, f"取值须为 {spec['enum']} 之一，实际 {value!r}")

    def _object(self, path, value, spec):
        if not isinstance(value, dict):
            return self.fail(path, f"应为对象，实际是 {type(value).__name__}")
        for key in spec.get("required", []):
            if key not in value or value[key] in (None, ""):
                self.fail(f"{path}.{key}", "必填字段缺失或为空")
        for key, sub in (spec.get("fields") or {}).items():
            if key in value:
                self._field(f"{path}.{key}", value[key], sub)

    def _masters(self, masters):
        """Catch invented personas — the most likely hallucination in this prompt."""
        if not isinstance(masters, list):
            return
        for i, item in enumerate(masters):
            if isinstance(item, dict):
                name = item.get("name")
                if name and name not in self.master_names:
                    self.fail(f"masters[{i}].name", f"'{name}' 不在 config/masters.json 名单里")


def main():
    args = sys.argv[1:]
    if args and args[0] == "-":
        raw = sys.stdin.read()
        origin = "stdin"
    elif args:
        raw = Path(args[0]).read_text(encoding="utf-8")
        origin = args[0]
    else:
        raw = read_clipboard()
        origin = "剪贴板"

    print(f"来源：{origin}（{len(raw)} 字符）")

    try:
        data = extract_json(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"\n❌ 解析失败：{exc}")
        print("提示：让模型重新输出一次，强调「只输出 JSON，不要任何解释文字」。")
        return 1

    schema = json.loads((ROOT / "config/insights_schema.json").read_text(encoding="utf-8"))
    masters_cfg = json.loads((ROOT / "config/masters.json").read_text(encoding="utf-8"))

    validator = Validator(schema, masters_cfg)
    validator.check(data)
    if validator.errors:
        print(f"\n❌ 校验未通过（{len(validator.errors)} 处），未写入文件：")
        for error in validator.errors:
            print(f"  · {error}")
        print("\n把上面的报错贴回 chat 让它修正，然后重新运行本脚本。")
        return 1

    # Date consistency: silently accepting a mismatched date is exactly the bug
    # that made the original tool show 7-17 commentary above 7-21 quotes.
    market_path = ROOT / "market.json"
    if market_path.exists():
        market = json.loads(market_path.read_text(encoding="utf-8"))
        market_date = market.get("tradingDate")
        if market_date and data.get("tradingDate") != market_date:
            print(f"\n⚠️  日期不一致：insights={data.get('tradingDate')}，market.json={market_date}")
            print("   仍会写入，但前端会在页面顶部挂出告警条。")

    now = datetime.now(SHANGHAI)
    data["generatedAt"] = now.isoformat()
    data["generatedAtText"] = now.strftime("%Y-%m-%d %H:%M")
    data["generator"] = "chat-paste"

    out = ROOT / "insights.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    masters = data.get("masters") or []
    pool = data.get("stockPool") or []
    print(f"\n✅ 已写入 {out}")
    print(f"   交易日 {data.get('tradingDate')}｜大师观点 {len(masters)} 条｜股票池 {len(pool)} 只")
    print(f"   风格判定：{(data.get('styleVerdict') or {}).get('title', '--')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
