#!/usr/bin/env python3
"""Deterministic post-processing that makes boundary violations impossible.

The API can enforce shape (types, enums, required keys) but not size: every
`maxLength` / `maxItems` in config/insights_schema.json is invisible to it. So
instead of asking the model to count characters — and retrying (i.e. paying
again) when it miscounts — we fix the output here, in code:

  1. tradingDate is overwritten from market.json (never negotiated)
  2. whitespace is normalised (no NFKC — that would mangle 全角 punctuation)
  3. over-long arrays are de-duplicated, then cut from the TAIL
     (models put their best material first)
  4. over-long strings are cut at the last sentence boundary that fits
  5. consensus votes / agreementPct are RECOMPUTED from masters[].picks with
     the same algorithm the dashboard uses (app.js renderConsensus), so the
     number on screen can never disagree with the opinions above it

Anything it had to change lands in `qualityReport`, which is written into
insights.json — silent repairs are how you end up not noticing the model has
been degrading for a month.

    from normalize import normalize
    data, report = normalize(data, market, bounds_table, masters_cfg)
"""
from __future__ import annotations

import copy
import json
import re

# Cut points, best first. Full stops beat commas beat list separators.
SENTENCE_END = "。！？"
CLAUSE_END = "；，、"
CUT_CHARS = SENTENCE_END + CLAUSE_END

# If the last punctuation sits before this fraction of the limit, cutting there
# would throw away most of the sentence — hard-cut with an ellipsis instead.
MIN_CUT_RATIO = 0.6

# Trailing junk a model leaves when it stops mid-enumeration.
TRAILING_JUNK = "、／,，/ \t"

# Values that look like a code but carry no information — using them as a
# dedupe key would collapse the whole stockPool into one row.
PLACEHOLDERS = {"", "—", "--", "-", "－", "无", "n/a", "N/A", "null", "None", "0"}

# How to identify "the same item" inside each array. First non-placeholder key wins.
DEDUPE_KEYS = {
    "masters": ("name",),
    "stockPool": ("code", "name"),
    "sectorReads": ("name",),
    "consensus.picks": ("name",),
    "eventReads": ("title",),
    "abnormalMoves": ("type",),
}


# --------------------------------------------------------------------------
# text helpers
# --------------------------------------------------------------------------

def clean_text(value):
    """strip + fold internal newlines to a single space + drop trailing separators.

    Deliberately NOT unicodedata.normalize("NFKC", …): that rewrites １２３ and,
    worse, turns 全角 punctuation into half-width, which reads as broken Chinese.
    """
    if not isinstance(value, str):
        return value
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s*\n+\s*", " ", text)
    text = re.sub(r"[ \t　]{2,}", " ", text)
    text = text.strip()
    text = text.rstrip(TRAILING_JUNK).strip()
    return text


def smart_truncate(text, limit):
    """Cut `text` to `limit` characters at the nicest boundary available.

    Returns (text, was_truncated).
    """
    if not isinstance(text, str) or limit is None or limit < 2 or len(text) <= limit:
        return text, False

    head = text[:limit]
    best = -1
    for group in (SENTENCE_END, CLAUSE_END):
        best = max((head.rfind(ch) for ch in group), default=-1)
        if best >= 0:
            break
    if best >= int(limit * MIN_CUT_RATIO):
        return head[:best + 1].rstrip(TRAILING_JUNK), True
    return head[:limit - 1].rstrip(TRAILING_JUNK) + "…", True


def _is_placeholder(value):
    return not isinstance(value, str) or value.strip() in PLACEHOLDERS


# --------------------------------------------------------------------------
# normalizer
# --------------------------------------------------------------------------

class _Normalizer:
    def __init__(self, bounds, report):
        self.bounds = bounds or {}
        self.report = report

    def bound(self, path):
        return self.bounds.get(path) or {}

    def protected(self, path):
        spec = self.bound(path)
        return bool(spec.get("enum") or spec.get("const"))

    # -- walk ---------------------------------------------------------------
    def walk(self, value, path):
        if isinstance(value, dict):
            return {key: self.walk(sub, f"{path}.{key}" if path else key)
                    for key, sub in value.items()}
        if isinstance(value, list):
            items = self.shrink_array(value, path)
            return [self.walk(item, f"{path}[]") for item in items]
        if isinstance(value, str):
            return self.fix_string(value, path)
        return value

    # -- strings ------------------------------------------------------------
    def fix_string(self, value, path):
        if self.protected(path):
            # enum / const values are load-bearing: strip only, never reshape.
            return value.strip()
        text = clean_text(value)
        limit = self.bound(path).get("maxLength")
        if limit:
            text, cut = smart_truncate(text, limit)
            if cut:
                self.report["truncated"].append({"path": path, "limit": limit,
                                                 "was": len(value)})
        return text

    # -- arrays -------------------------------------------------------------
    def shrink_array(self, value, path):
        limit = self.bound(path).get("maxItems")
        keys = DEDUPE_KEYS.get(path)
        before = len(value)

        seen = set()
        deduped = []
        for item in value:
            key = self._dedupe_key(item, keys)
            if key is not None:
                if key in seen:
                    continue
                seen.add(key)
            deduped.append(item)
        duplicates = before - len(deduped)

        kept = deduped[:limit] if limit else deduped   # cut from the tail
        overflow = len(deduped) - len(kept)

        if duplicates or overflow:
            self.report["slicedArrays"][path] = {
                "before": before,
                "after": len(kept),
                "duplicates": duplicates,
                "overflow": overflow,
                "limit": limit,
            }
        return kept

    @staticmethod
    def _dedupe_key(item, keys):
        if isinstance(item, str):
            text = item.strip()
            return ("str", text) if text else None
        if isinstance(item, dict) and keys:
            for key in keys:
                value = item.get(key)
                if isinstance(value, str) and not _is_placeholder(value):
                    return (key, value.strip())
        return None


# --------------------------------------------------------------------------
# consensus
# --------------------------------------------------------------------------

def recompute_consensus(data, bounds):
    """Recount votes from masters[].picks — identical to app.js renderConsensus.

    Whatever the model wrote in consensus.picks[].votes / agreementPct is
    discarded: arithmetic is not something worth paying an LLM for, and a
    mismatch between the votes shown and the opinions above them is the kind of
    bug that quietly destroys trust in the whole page.
    """
    masters = data.get("masters")
    votes = {}
    order = []
    voters = 0
    if isinstance(masters, list):
        for entry in masters:
            if not isinstance(entry, dict):
                continue
            picks = [p.strip() for p in (entry.get("picks") or [])
                     if isinstance(p, str) and p.strip()]
            if picks:
                voters += 1
            for pick in picks:
                if pick not in votes:
                    order.append(pick)
                votes[pick] = votes.get(pick, 0) + 1

    voter_count = voters or 1
    top = max(votes.values()) if votes else 0
    agreement = int(round(top / voter_count * 100))
    agreement = max(0, min(100, agreement))

    consensus = data.get("consensus")
    if not isinstance(consensus, dict):
        consensus = {}
    previous = {
        "agreementPct": consensus.get("agreementPct"),
        "picks": len(consensus.get("picks") or []) if isinstance(consensus.get("picks"), list) else 0,
    }

    # keep any code the model (or the stock pool) already knew for a name
    codes = {}
    for item in consensus.get("picks") or []:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            code = item.get("code")
            if not _is_placeholder(code):
                codes[item["name"].strip()] = code.strip()
    for item in data.get("stockPool") or []:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            code = item.get("code")
            if not _is_placeholder(code) and item["name"].strip() not in codes:
                codes[item["name"].strip()] = code.strip()

    limit = (bounds.get("consensus.picks") or {}).get("maxItems") or 8
    ranked = sorted(order, key=lambda name: (-votes[name], order.index(name)))[:limit]
    consensus["picks"] = [
        {"name": name, "code": codes.get(name, "—"), "votes": votes[name]}
        for name in ranked
    ]
    consensus["agreementPct"] = agreement
    data["consensus"] = consensus

    return {
        "voters": voters,
        "topVotes": top,
        "agreementPct": agreement,
        "modelAgreementPct": previous["agreementPct"],
        "modelPickCount": previous["picks"],
    }


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

def normalize(data, market, bounds_table, masters_cfg=None, attempts=1):
    """Return (normalized_copy, quality_report). Never raises on bad content."""
    data = copy.deepcopy(data)
    report = {
        "truncated": [],
        "slicedArrays": {},
        "votesRecomputed": True,
        "attempts": attempts,
        "notes": [],
    }

    # 1. the date is a fact, not an opinion
    trading_date = (market or {}).get("tradingDate")
    if trading_date:
        if data.get("tradingDate") != trading_date:
            report["notes"].append(
                f"tradingDate 由 {data.get('tradingDate')!r} 强制改写为 {trading_date!r}")
        data["tradingDate"] = trading_date

    # 2-4. whitespace, de-dup + tail-cut arrays, sentence-aware string cuts
    normalizer = _Normalizer(bounds_table, report)
    data = normalizer.walk(data, "")

    # 5. derived numbers are computed, not clamped
    report["consensus"] = recompute_consensus(data, bounds_table or {})

    # tidy: report["truncated"] as plain paths is what the runbook reads
    report["truncatedDetail"] = report["truncated"]
    report["truncated"] = [item["path"] for item in report["truncatedDetail"]]
    return data, report


def summarize(report):
    """One-line human summary for the terminal."""
    parts = []
    if report.get("truncated"):
        parts.append(f"截断 {len(report['truncated'])} 处")
    sliced = report.get("slicedArrays") or {}
    if sliced:
        dropped = sum(v.get("duplicates", 0) + v.get("overflow", 0) for v in sliced.values())
        parts.append(f"数组裁剪 {len(sliced)} 个（共去掉 {dropped} 项）")
    consensus = report.get("consensus") or {}
    if consensus:
        model_pct = consensus.get("modelAgreementPct")
        if model_pct != consensus.get("agreementPct"):
            parts.append(f"agreementPct {model_pct} → {consensus.get('agreementPct')}")
    for note in report.get("notes") or []:
        parts.append(note)
    return "；".join(parts) if parts else "无需修正"


def main():  # pragma: no cover - manual check: feed it an existing insights.json
    import argparse
    from pathlib import Path

    import schema_build

    parser = argparse.ArgumentParser(description="对一份 insights JSON 跑一遍 normalize")
    parser.add_argument("path", nargs="?", default="insights.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    data = json.loads(Path(args.path).read_text(encoding="utf-8"))
    market = json.loads((root / "market.json").read_text(encoding="utf-8"))
    schema, masters = schema_build.load_config()
    bounds = schema_build.collect_bounds(schema)

    fixed, report = normalize(data, market, bounds, masters)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("\n摘要：" + summarize(report))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
