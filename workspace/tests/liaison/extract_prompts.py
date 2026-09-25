#!/usr/bin/env python3
"""Extract the requester's own words from Claude Code transcripts, for analysing how requests are phrased.

Input:  transcript folders (default ~/.claude/projects/<folder for this project>); interactive sessions only.
Output: JSON Lines on stdout or --out, one record per prompt or question answer:
        {"session": "ab12cd34", "n": 3, "kind": "prompt"|"answer", "chars": int, "words": int,
         "interrupted_before": bool, "had_paste": bool, "text": str}
Pasted blocks, slash-command wrappers and system tags are removed, and text is capped at --max-chars.
The output contains the requester's words: keep it local (it is written under a gitignored results/ folder).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

STRIP = [
    (re.compile(r"<pasted_content[^>]*>.*?</pasted_content[^>]*>", re.S), " [PASTE] "),
    (re.compile(r"<system-reminder>.*?</system-reminder>", re.S), " "),
    (re.compile(r"<(command-name|command-message|command-args|local-command-stdout|local-command-caveat)>.*?</\1>", re.S), " "),
    (re.compile(r"<[a-z_-]+>|</[a-z_-]+>"), " "),
    (re.compile(r"The user (opened the file|selected the lines|is viewing)[^\n]*?(may or may not be related to the current task\.|\n)"), " "),
]
ANSWER = re.compile(r'"([^"]+)"="([^"]*)"')


def clean(text: str) -> tuple[str, bool]:
    had_paste = "<pasted_content" in text
    for pat, rep in STRIP:
        text = pat.sub(rep, text)
    return re.sub(r"\s+", " ", text).strip(), had_paste


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project-root", type=Path, default=Path.cwd())
    ap.add_argument("--transcripts", type=Path, action="append")
    ap.add_argument("--max-chars", type=int, default=1500)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    folders = a.transcripts or [Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(a.project_root.resolve()))]
    records = []
    for folder in folders:
        for f in sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime):
            sid, n, mode, interrupted = f.stem[:8], 0, None, False
            with open(f, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    try:
                        ev = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    mode = mode or ({"sdk-cli": "headless"}.get(ev.get("entrypoint"), "interactive") if ev.get("entrypoint") else None)
                    if ev.get("type") != "user" or ev.get("isMeta") or ev.get("isSidechain"):
                        continue
                    content = (ev.get("message") or {}).get("content")
                    items = []
                    if isinstance(content, str):
                        if content.startswith("[Request interrupted"):
                            interrupted = True
                            continue
                        items.append(("prompt", content))
                    elif isinstance(content, list):
                        for c in content:
                            if not isinstance(c, dict):
                                continue
                            if c.get("type") == "text" and not c.get("text", "").startswith("[Request interrupted"):
                                items.append(("prompt", c["text"]))
                            elif c.get("type") == "text":
                                interrupted = True
                            elif c.get("type") == "tool_result" and isinstance(c.get("content"), str) and "questions have been answered" in c["content"]:
                                items.append(("answer", "; ".join(f"{q} => {ans}" for q, ans in ANSWER.findall(c["content"]))))
                    for kind, raw in items:
                        text, had_paste = clean(raw) if kind == "prompt" else (raw, False)
                        if not text or text in ("[PASTE]",) and not had_paste:
                            continue
                        n += 1
                        records.append({"session": sid, "n": n, "kind": kind, "chars": len(text), "words": len(text.split()),
                                        "interrupted_before": interrupted, "had_paste": had_paste, "text": text[: a.max_chars]})
                        interrupted = False
            if mode == "headless":
                records = [r for r in records if r["session"] != sid]
    out = "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(out + "\n")
        print(f"{len(records)} records → {a.out}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
