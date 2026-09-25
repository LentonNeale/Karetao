#!/usr/bin/env python3
"""Summarise Claude Code transcripts into an anonymised usage digest for the efficiency test.

Input:  one or more transcript folders (default: ~/.claude/projects/<folder for this project>),
        each holding <session>.jsonl files and <session>/subagents/*.jsonl.
Output: a JSON digest (stdout or --out) with counts only. It contains no prompt or response text, no
        command arguments beyond a normalised "shape", and no paths outside the project (shown as
        <external>). Every pattern has a stable id (T*, B*, S*, R*, L*, A*) that proposals must cite.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SUBCOMMAND_TOOLS = {"git", "gh", "cmake", "ctest", "claude", "npm", "pip", "pip3", "docker", "systemctl", "apt-get", "sudo"}
SAFE = re.compile(r"^[A-Za-z0-9_.+-]+$")
SHELL_KEYWORDS = {"for", "do", "done", "while", "until", "if", "then", "else", "elif", "fi", "case", "esac", "time", "timeout", "!"}


def project_dir_name(root: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(root.resolve()))


def bash_shapes(command: str) -> list[str]:
    """Normalise a shell command into shapes like 'git status', 'python3 -m unittest', 'grep'."""
    first_line = command.strip().splitlines()[0] if command.strip() else ""
    shapes = []
    for seg in re.split(r"&&|\|\||;", first_line):
        words = seg.split("|", 1)[0].strip().split()  # the command before any pipe; filters after it aren't separate work
        if words and words[0] in ("for", "while", "until", "case", "select"):
            continue  # loop/case header; its body arrives as later segments
        while words and (("=" in words[0] and not words[0].startswith("-")) or words[0] in SHELL_KEYWORDS):
            words = words[1:]  # skip VAR=value prefixes and loop/if keywords
        if not words or words[0] in ("cd", "echo", "printf", "true", "(", "{", "}", ")"):
            continue
        w0 = os.path.basename(words[0].strip("()'\""))
        if not SAFE.match(w0):
            continue
        shape = w0
        rest = [w for w in words[1:] if not w.startswith("-")]
        if w0 in ("python", "python3"):
            if "-m" in words and words.index("-m") + 1 < len(words):
                shape = f"{w0} -m {words[words.index('-m') + 1]}"
            elif words[1:] and words[1] == "-":
                shape = f"{w0} <stdin-script>"
            elif rest:
                shape = f"{w0} {os.path.basename(rest[0])}" if SAFE.match(os.path.basename(rest[0])) else f"{w0} <script>"
        elif w0 in SUBCOMMAND_TOOLS and rest and SAFE.match(rest[0]):
            shape = f"{w0} {rest[0]}"
            if w0 in ("gh", "sudo") and len(rest) > 1 and SAFE.match(rest[1]):
                shape += f" {rest[1]}"
        shapes.append(shape)
    return shapes or ["<other>"]


def rel_path(p: str, root: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(root.resolve()))
    except (ValueError, OSError):
        return "<external>"


def result_chars(content) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(c.get("text", "")) for c in content if isinstance(c, dict))
    return 0


def usage_add(acc: dict, usage: dict) -> None:
    for k_out, k_in in (("input", "input_tokens"), ("cache_read", "cache_read_input_tokens"),
                        ("cache_create", "cache_creation_input_tokens"), ("output", "output_tokens")):
        acc[k_out] += int(usage.get(k_in) or 0)
    acc["messages"] += 1


def new_usage() -> dict:
    return {"input": 0, "cache_read": 0, "cache_create": 0, "output": 0, "messages": 0}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project-root", type=Path, default=Path.cwd(), help="project root (paths are made relative to it)")
    ap.add_argument("--transcripts", type=Path, action="append",
                    help="transcript folder(s); default ~/.claude/projects/<project-root as folder name>")
    ap.add_argument("--include-headless", action="store_true", help="count headless (sdk-cli) sessions in the patterns")
    ap.add_argument("--top", type=int, default=25, help="entries per list")
    ap.add_argument("--out", type=Path, help="write the digest here instead of stdout")
    a = ap.parse_args(argv)
    root = a.project_root
    folders = a.transcripts or [Path.home() / ".claude" / "projects" / project_dir_name(root)]

    tokens_by_model = defaultdict(new_usage)
    tokens_by_mode = defaultdict(new_usage)
    tools = defaultdict(lambda: {"calls": 0, "result_chars": 0, "sessions": set()})
    shapes = defaultdict(lambda: {"calls": 0, "result_chars": 0, "sessions": set()})
    reads = defaultdict(lambda: {"reads": 0, "result_chars": 0, "sessions": set(), "per_session": Counter()})
    seqs = defaultdict(lambda: {"count": 0, "sessions": set()})
    large = []
    agents = defaultdict(lambda: {"spawns": 0})
    modes = Counter()
    prompts = {"count": 0, "chars": 0}
    dates = []
    n_sub = 0

    for folder in folders:
        for main_file in sorted(folder.glob("*.jsonl")):
            sid = main_file.stem[:8]
            files = [(main_file, False)] + [(f, True) for f in sorted((folder / main_file.stem / "subagents").glob("*.jsonl"))]
            mode = None
            steps = []
            pending = {}
            for path, is_sub in files:
                n_sub += is_sub
                with open(path, encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        try:
                            ev = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if mode is None and ev.get("entrypoint"):
                            mode = "headless" if ev["entrypoint"] == "sdk-cli" else "interactive"
                        if ev.get("timestamp") and not is_sub:
                            dates.append(ev["timestamp"][:10])
                        msg = ev.get("message") or {}
                        if ev.get("type") == "assistant":
                            model = msg.get("model") or "unknown"
                            if msg.get("usage"):
                                usage_add(tokens_by_model[model], msg["usage"])
                                usage_add(tokens_by_mode[mode or "unknown"], msg["usage"])
                            for c in msg.get("content") or []:
                                if not isinstance(c, dict) or c.get("type") != "tool_use":
                                    continue
                                name, inp = c.get("name", "?"), c.get("input") or {}
                                keys = [f"{name}"]
                                if name == "Bash":
                                    keys = [f"Bash:{s}" for s in bash_shapes(inp.get("command", ""))]
                                elif name in ("Agent", "Task"):
                                    at = inp.get("subagent_type", "general-purpose")
                                    agents[at]["spawns"] += 1
                                    keys = [f"Agent:{at}"]
                                elif name in ("Read", "Edit", "Write") and inp.get("file_path"):
                                    keys = [f"{name}:{rel_path(inp['file_path'], root)}"] if name == "Read" else [name]
                                pending[c.get("id")] = (name, keys, inp, is_sub, model)
                                if not is_sub:
                                    steps.append(keys[0])
                        elif ev.get("type") == "user":
                            content = msg.get("content")
                            if isinstance(content, str) and not is_sub and not ev.get("isMeta"):
                                prompts["count"] += 1
                                prompts["chars"] += len(content)
                            for c in content if isinstance(content, list) else []:
                                if not isinstance(c, dict) or c.get("type") != "tool_result":
                                    continue
                                name, keys, inp, sub, model = pending.pop(c.get("tool_use_id"), (None, [], {}, False, ""))
                                if not name:
                                    continue
                                chars = result_chars(c.get("content"))
                                if mode == "headless" and not a.include_headless:
                                    continue
                                tools[name]["calls"] += 1
                                tools[name]["result_chars"] += chars
                                tools[name]["sessions"].add(sid)
                                if name == "Bash":
                                    for k in keys:
                                        s = shapes[k[5:]]
                                        s["calls"] += 1
                                        s["result_chars"] += chars // max(1, len(keys))
                                        s["sessions"].add(sid)
                                if name == "Read" and inp.get("file_path"):
                                    r = reads[rel_path(inp["file_path"], root)]
                                    r["reads"] += 1
                                    r["result_chars"] += chars
                                    r["sessions"].add(sid)
                                    r["per_session"][sid] += 1
                                large.append((chars, keys[0] if keys else name))
            modes[mode or "unknown"] += 1
            if mode == "headless" and not a.include_headless:
                continue
            short = [s if s.startswith(("Bash:", "Agent:")) else s.split(":")[0] for s in steps]
            for n in (2, 3):
                seen_here = set()
                for i in range(len(short) - n + 1):
                    gram = tuple(short[i:i + n])
                    if len(set(gram)) == 1 and gram[0] in ("Read", "Edit", "Grep", "Glob"):
                        continue
                    seqs[gram]["count"] += 1
                    seqs[gram]["sessions"].add(sid)

    def top(d, key, n, prefix, fields):
        items = sorted(d.items(), key=lambda kv: -kv[1][key])[:n]
        return [{"id": f"{prefix}{i + 1}", **fields(k, v)} for i, (k, v) in enumerate(items)]

    tok = lambda chars: chars // 4
    digest = {
        "schema": "icm-efficiency-digest/1",
        "source": {"sessions": sum(modes.values()), "by_mode": dict(modes), "subagent_transcripts": n_sub,
                   "date_range": [min(dates), max(dates)] if dates else [], "patterns_include_headless": a.include_headless},
        "user_prompts": {"count": prompts["count"], "avg_chars": prompts["chars"] // max(1, prompts["count"])},
        "tokens_by_model": dict(tokens_by_model),
        "tokens_by_mode": dict(tokens_by_mode),
        "tools": top(tools, "calls", a.top, "T", lambda k, v: {"tool": k, "calls": v["calls"], "result_tokens_est": tok(v["result_chars"]), "sessions": len(v["sessions"])}),
        "bash_shapes": top(shapes, "calls", a.top + 15, "B", lambda k, v: {"shape": k, "calls": v["calls"], "result_tokens_est": tok(v["result_chars"]), "sessions": len(v["sessions"])}),
        "sequences": [s for s in top({k: v for k, v in seqs.items() if v["count"] >= 3}, "count", a.top, "S",
                                     lambda k, v: {"steps": list(k), "count": v["count"], "sessions": len(v["sessions"])})],
        "repeated_reads": top({k: v for k, v in reads.items() if v["reads"] >= 2}, "reads", a.top, "R",
                              lambda k, v: {"file": k, "reads": v["reads"], "sessions": len(v["sessions"]),
                                            "max_reads_one_session": max(v["per_session"].values()), "result_tokens_est": tok(v["result_chars"])}),
        "large_results": [{"id": f"L{i + 1}", "source": src, "result_tokens_est": tok(ch)} for i, (ch, src) in enumerate(sorted(large, reverse=True)[:15])],
        "subagents": top(agents, "spawns", a.top, "A", lambda k, v: {"agent": k, "spawns": v["spawns"]}),
    }
    text = json.dumps(digest, indent=1)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text + "\n")
        print(f"digest written: {a.out} ({len(text)} chars)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
