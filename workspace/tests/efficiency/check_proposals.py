#!/usr/bin/env python3
"""Validate and rank efficiency proposals against the admission rules in CONTEXT.md.

Input:  proposals JSON (proposal-template.json shape) and the usage digest it cites.
Output: a ranked Markdown table on stdout, then errors and warnings; exit 0 if valid, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KINDS = {"tool": ("workspace/scripts/", ".py"), "hook": ("workspace/hooks/", ".py"), "shared-file": ("workspace/shared/", "")}
HOOK_EVENTS = {"PreToolUse", "PostToolUse", "PostToolUseFailure", "UserPromptSubmit", "SessionStart", "SessionEnd",
               "Stop", "SubagentStart", "SubagentStop", "PreCompact", "PostCompact", "Notification", "PermissionRequest"}
REQUIRED = ["id", "name", "kind", "summary", "replaces", "evidence", "trigger", "input", "output", "language",
            "location", "tokens_saved_per_use", "uses_per_week", "estimate_basis", "test_plan", "risks"]
VAGUE = re.compile(r"\b(analy[sz]e|understand|figure out|as needed|etc\.?|somehow|appropriate(ly)?|relevant info)\b", re.I)
PLACEHOLDER = re.compile(r"short-kebab-name|tool \| hook|Exact arguments|Exact stdout|One sentence: what|\.py \| workspace/")


def digest_ids(digest: dict) -> set[str]:
    ids = set()
    for v in digest.values():
        if isinstance(v, list):
            ids.update(e["id"] for e in v if isinstance(e, dict) and "id" in e)
    return ids


def check(data: dict, ids: set[str], ws_root: Path) -> tuple[list[dict], list[str], list[str]]:
    errors, warnings, valid = [], [], []
    props = data.get("proposals")
    if not isinstance(props, list):
        return [], ["'proposals' must be a list"], []
    if not 5 <= len(props) <= 12:
        errors.append(f"expected 5–12 proposals, got {len(props)}")
    if not isinstance(data.get("rejected"), list):
        errors.append("'rejected' must be a list (it may be empty)")
    seen_ids, seen_names = set(), set()
    for p in props:
        pid = p.get("id", "?")
        e = []
        for f in REQUIRED:
            if p.get(f) in (None, "", []):
                e.append(f"missing {f}")
        if PLACEHOLDER.search(json.dumps(p)):
            e.append("still contains template placeholder text")
        if pid in seen_ids or p.get("name") in seen_names:
            e.append("duplicate id or name")
        seen_ids.add(pid); seen_names.add(p.get("name"))
        kind = p.get("kind")
        if kind not in KINDS:
            e.append(f"kind must be one of {sorted(KINDS)}")
        else:
            prefix, ext = KINDS[kind]
            loc = str(p.get("location", ""))
            if not loc.startswith(prefix) or (ext and not loc.endswith(ext)):
                e.append(f"location for a {kind} must be {prefix}*{ext}")
            elif (ws_root / loc).exists():
                warnings.append(f"{pid}: {loc} already exists; say how it extends the existing file")
        if p.get("language") != "python":
            e.append("language must be 'python'")
        if kind == "hook" and str(p.get("trigger", "")).split(":")[0].strip() not in HOOK_EVENTS:
            e.append(f"hook trigger must start with a hook event ({', '.join(sorted(HOOK_EVENTS))})")
        ev = p.get("evidence") if isinstance(p.get("evidence"), list) else []
        unknown = [x for x in ev if x not in ids]
        if not ev or unknown:
            e.append(f"evidence must cite digest ids; unknown: {unknown or 'none cited'}")
        for f in ("input", "output"):
            text = str(p.get(f, ""))
            if len(text) < 25 or VAGUE.search(text):
                e.append(f"{f} is too short or vague: must be a concrete, machine-checkable contract")
        for f in ("tokens_saved_per_use", "uses_per_week"):
            if not isinstance(p.get(f), (int, float)) or p.get(f) <= 0:
                e.append(f"{f} must be a positive number")
        if not re.search(r"\d", str(p.get("estimate_basis", ""))):
            e.append("estimate_basis must show the arithmetic from digest counts")
        if e:
            errors.extend(f"{pid}: {m}" for m in e)
        else:
            valid.append(p)
    return valid, errors, warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("proposals", type=Path)
    ap.add_argument("--digest", type=Path, required=True)
    ap.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[3],
                    help="project root containing workspace/ (for duplicate checks)")
    a = ap.parse_args(argv)
    try:
        data = json.loads(a.proposals.read_text())
        ids = digest_ids(json.loads(a.digest.read_text()))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    valid, errors, warnings = check(data, ids, a.workspace_root)
    ranked = sorted(valid, key=lambda p: -(p["tokens_saved_per_use"] * p["uses_per_week"]))
    print("| Rank | Id | Name | Kind | Tokens/use | Uses/week | Score (tokens/week) |")
    print("|---|---|---|---|---|---|---|")
    for i, p in enumerate(ranked, 1):
        print(f"| {i} | {p['id']} | {p['name']} | {p['kind']} | {p['tokens_saved_per_use']:,} | {p['uses_per_week']:g} | "
              f"{int(p['tokens_saved_per_use'] * p['uses_per_week']):,} |")
    total = sum(p["tokens_saved_per_use"] * p["uses_per_week"] for p in ranked)
    print(f"\nValid: {len(valid)}/{len(data.get('proposals', []))} · rejected ideas recorded: {len(data.get('rejected', []))} · "
          f"estimated saving: {int(total):,} tokens/week")
    for w in warnings:
        print(f"warning: {w}")
    for err in errors:
        print(f"error: {err}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
