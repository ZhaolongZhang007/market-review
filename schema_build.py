#!/usr/bin/env python3
"""Compile config/insights_schema.json into a real JSON Schema for the API.

The repo's schema file is a home-grown contract (`root.fields[...]` with
`maxLength` / `min` / `maxItems` / `pattern`). Anthropic's structured outputs
accept only a subset of JSON Schema, so this module does three things:

  KEEP     type / required / enum / const / additionalProperties:false
           → the API *enforces* these; the model cannot violate them.
  STRIP    maxLength / minLength / min / max / pattern / maxItems / minItems
           → the API ignores them, so leaving them in would be a lie. They are
             handed to normalize.py instead (bounds_table), which enforces them
             deterministically after the response comes back.
  UPGRADE  turn stripped constraints into things the API *can* enforce:
             tradingDate            → const (kills date drift for good)
             masters[].name         → enum from config/masters.json
             sectorReads[].name     → enum from today's hotSectors
             stock name fields      → enum from today's UNIVERSE
                                      (板块龙头 ∪ 涨停梯队 ∪ 龙虎榜)

Everything an object contains is marked `required` at every level: the API then
guarantees a fully-shaped document (empty arrays / "—" are still allowed), which
means the front-end never has to guard for a missing key.

    from schema_build import build_api_schema
    api_schema, bounds, universe = build_api_schema(schema, market, masters_cfg)
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# JSON Schema keywords Anthropic's structured outputs do NOT support. If any of
# these survive into the compiled schema we have silently lost a guarantee, so
# assert_api_safe() raises instead of shipping a schema that only looks strict.
FORBIDDEN_KEYWORDS = frozenset({
    "maxLength", "minLength",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    "pattern",
    "maxItems", "minItems", "uniqueItems",
})

# An enum is only useful if it has real breadth. A 3-name universe would force
# the model to name the same stock everywhere, which is worse than free text.
MIN_UNIVERSE = 8
MIN_SECTORS = 3

# Fields that should be constrained to the day's tradeable universe.
UNIVERSE_PATHS = (
    "stockPool[].name",
    "masters[].picks[]",
    "consensus.picks[].name",
)
# These two legitimately reference indices too ("科创50 与 中证2000 背离"), so they
# get the universe *plus* index / global-market names. Constraining them to
# stocks only would delete the 指数背离 observation entirely.
UNIVERSE_EXT_PATHS = (
    "abnormalMoves[].items[]",
    "eventReads[].impactedStocks[]",
)


def load_config():
    """Convenience loader used by the CLI paths."""
    schema = json.loads((ROOT / "config/insights_schema.json").read_text(encoding="utf-8"))
    masters = json.loads((ROOT / "config/masters.json").read_text(encoding="utf-8"))
    return schema, masters


# --------------------------------------------------------------------------
# universe
# --------------------------------------------------------------------------

def build_universe(market):
    """Every stock name the model is allowed to name today, in priority order.

    板块龙头 → 涨停梯队龙头 → 龙虎榜. Order matters only for readability of the
    generated enum; duplicates are dropped keeping first appearance.
    """
    names = []

    def add(value):
        if isinstance(value, str):
            value = value.strip()
            # update_data.py pads `leaders` with descriptive filler such as
            # "成交额前排" / "趋势核心股" — those are not tradeable names.
            if value and value not in names and not _is_filler(value):
                names.append(value)

    for sector in market.get("hotSectors") or []:
        for leader in (sector.get("leaders") or [])[:3]:
            add(leader)
    for item in (market.get("sentiment") or {}).get("limitUpLeaders") or []:
        add(item.get("name"))
    for item in market.get("lhb") or []:
        add(item.get("name"))
    return names


_FILLER = ("成交额前排", "趋势核心股", "核心股", "龙头股", "--", "—", "暂无")


def _is_filler(value):
    return value in _FILLER


def build_universe_ext(market, universe):
    """Universe + index / global-market names, for the two fields that need them."""
    names = list(universe)
    for key in ("indices", "globalMarkets"):
        for item in market.get(key) or []:
            name = (item.get("name") or "").strip()
            if name and name not in names:
                names.append(name)
    return names


# --------------------------------------------------------------------------
# compiler
# --------------------------------------------------------------------------

class _Compiler:
    def __init__(self, enums, const_values, notes, include_descriptions=True):
        self.enums = enums                  # path -> list[str]
        self.const_values = const_values    # path -> str
        self.notes = notes
        self.bounds = {}
        self.include_descriptions = include_descriptions

    # -- bounds bookkeeping -------------------------------------------------
    def _record(self, path, **kwargs):
        entry = self.bounds.setdefault(path, {})
        entry.update({k: v for k, v in kwargs.items() if v is not None})

    # -- entry point --------------------------------------------------------
    def compile_root(self, root_spec):
        fields = root_spec.get("fields") or {}
        properties = {}
        for key, spec in fields.items():
            properties[key] = self.compile_field(key, spec)
        # Every root section is required: the dashboard renders all of them and
        # an absent key is indistinguishable from a rendering bug. Empty arrays
        # remain legal, so this costs the model nothing when it has nothing to say.
        required = sorted(set(root_spec.get("required") or []) | set(fields))
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    def compile_field(self, path, spec):
        kind = spec.get("type")
        if kind == "object":
            return self._object(path, spec)
        if kind == "array":
            return self._array(path, spec)
        if kind == "number":
            return self._number(path, spec)
        return self._string(path, spec)

    # -- leaf types ---------------------------------------------------------
    def _describe(self, node, spec):
        desc = spec.get("desc") if isinstance(spec, dict) else None
        if desc and self.include_descriptions:
            node["description"] = desc
        return node

    def _string(self, path, spec):
        node = {"type": "string"}
        # STRIP → bounds_table
        self._record(path,
                     maxLength=spec.get("maxLength"),
                     minLength=spec.get("minLength"),
                     pattern=spec.get("pattern"))
        # UPGRADE / KEEP
        if path in self.const_values:
            node["const"] = self.const_values[path]
            self._record(path, const=True)
        elif path in self.enums:
            node["enum"] = list(self.enums[path])
            self._record(path, enum=True)
        elif spec.get("enum"):
            node["enum"] = list(spec["enum"])
            self._record(path, enum=True)
        return self._describe(node, spec)

    def _number(self, path, spec):
        self._record(path, min=spec.get("min"), max=spec.get("max"))
        return self._describe({"type": "number"}, spec)

    def _array(self, path, spec):
        self._record(path, maxItems=spec.get("maxItems"), minItems=spec.get("minItems"))
        item_spec = spec.get("items")
        item_path = f"{path}[]"
        if isinstance(item_spec, dict):
            items = self._object(item_path, item_spec)
        else:
            # declared as "string" (tags / picks / shortTerm …)
            items = self._string(item_path, {"type": "string"})
        return self._describe({"type": "array", "items": items}, spec)

    def _object(self, path, spec):
        fields = spec.get("fields") or {}
        properties = {}
        for key, sub in fields.items():
            properties[key] = self.compile_field(f"{path}.{key}" if path else key, sub)
        node = {
            "type": "object",
            "properties": properties,
            # Same rationale as compile_root: shape is fully determined.
            "required": sorted(set(spec.get("required") or []) | set(fields)),
            "additionalProperties": False,
        }
        return self._describe(node, spec)


# --------------------------------------------------------------------------
# self-check
# --------------------------------------------------------------------------

def assert_api_safe(node, path="root"):
    """Fail loudly if the compiled schema still contains something the API drops.

    This is the guard against the worst failure mode of this whole design:
    believing a constraint is enforced when the API silently ignored it.
    """
    if isinstance(node, list):
        for i, item in enumerate(node):
            assert_api_safe(item, f"{path}[{i}]")
        return
    if not isinstance(node, dict):
        return

    leftovers = FORBIDDEN_KEYWORDS & set(node)
    if leftovers:
        raise ValueError(
            f"schema_build 自检失败：{path} 仍带有 API 不支持的关键字 {sorted(leftovers)}。"
            " 这些约束会被 API 静默忽略，必须剥离并交给 normalize.py 执行。"
        )

    if node.get("type") == "object":
        if node.get("additionalProperties") is not False:
            raise ValueError(
                f"schema_build 自检失败：{path} 是 object 但缺少 additionalProperties:false，"
                " 模型可以塞进任意额外字段。"
            )
        if not isinstance(node.get("properties"), dict):
            raise ValueError(f"schema_build 自检失败：{path} 是 object 但没有 properties。")
        for key, sub in node["properties"].items():
            assert_api_safe(sub, f"{path}.{key}")
        for key in node.get("required") or []:
            if key not in node["properties"]:
                raise ValueError(f"schema_build 自检失败：{path}.required 含未定义字段 {key!r}。")

    if node.get("type") == "array":
        assert_api_safe(node.get("items"), f"{path}[]")

    for key in ("anyOf", "allOf", "oneOf"):
        if key in node:
            assert_api_safe(node[key], f"{path}.{key}")

    if "enum" in node:
        if not node["enum"]:
            raise ValueError(f"schema_build 自检失败：{path}.enum 为空，模型将无法给出任何合法值。")
        if len(set(node["enum"])) != len(node["enum"]):
            raise ValueError(f"schema_build 自检失败：{path}.enum 含重复项。")

    return True


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

def collect_bounds(insights_schema, notes=None):
    """bounds_table only — no market needed (used by the clipboard path)."""
    compiler = _Compiler({}, {}, notes if notes is not None else [])
    compiler.compile_root(insights_schema["root"])
    return compiler.bounds


def build_api_schema(insights_schema, market, masters_cfg, notes=None):
    """Return (api_schema, bounds_table, universe).

    `notes` (optional list) collects human-readable remarks about constraints
    that had to be downgraded — e.g. a universe too small to be worth an enum.
    """
    if notes is None:
        notes = []

    universe = build_universe(market)
    universe_ext = build_universe_ext(market, universe)
    master_names = [m["name"] for m in masters_cfg.get("masters", []) if m.get("name")]
    sector_names = []
    for sector in market.get("hotSectors") or []:
        name = (sector.get("name") or "").strip()
        if name and name not in sector_names:
            sector_names.append(name)
    trading_date = market.get("tradingDate")

    enums = {}
    const_values = {}

    if trading_date:
        const_values["tradingDate"] = trading_date
    else:
        notes.append("market.json 缺少 tradingDate：tradingDate 退回普通 string，日期一致性只能靠 normalize 兜底。")

    if master_names:
        enums["masters[].name"] = master_names
    else:
        notes.append("config/masters.json 没有可用名字：masters[].name 退回普通 string。")

    if len(sector_names) >= MIN_SECTORS:
        enums["sectorReads[].name"] = sector_names
    else:
        notes.append(f"板块列表只有 {len(sector_names)} 项（<{MIN_SECTORS}）：sectorReads[].name 退回普通 string。")

    if len(universe) >= MIN_UNIVERSE:
        for path in UNIVERSE_PATHS:
            enums[path] = universe
        for path in UNIVERSE_EXT_PATHS:
            enums[path] = universe_ext
    else:
        notes.append(
            f"UNIVERSE 只有 {len(universe)} 个标的（<{MIN_UNIVERSE}）："
            f"{'、'.join(UNIVERSE_PATHS + UNIVERSE_EXT_PATHS)} 全部退回普通 string，"
            " 模型可能点到数据里没有的个股，请人工复核。"
        )

    compiler = _Compiler(enums, const_values, notes)
    api_schema = compiler.compile_root(insights_schema["root"])
    assert_api_safe(api_schema)
    return api_schema, compiler.bounds, universe


def main():  # pragma: no cover - manual inspection helper
    import sys

    market = json.loads((ROOT / "market.json").read_text(encoding="utf-8"))
    schema, masters = load_config()
    notes = []
    api_schema, bounds, universe = build_api_schema(schema, market, masters, notes)
    print(json.dumps(api_schema, ensure_ascii=False, indent=2))
    print(f"\n# universe({len(universe)}): {'、'.join(universe)}", file=sys.stderr)
    print(f"# bounds({len(bounds)} 条)", file=sys.stderr)
    for note in notes:
        print(f"# 注意：{note}", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
