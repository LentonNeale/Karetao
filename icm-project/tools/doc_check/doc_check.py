#!/usr/bin/env python3
"""Karetao documentation check (standard library only). Run from the repo root.

Scans Documentation/**/*.md, Arm_Sensor_Hub/Documentation/*.md,
RaspberryPi_Sensor_Hub/Documentation/*.md, README.md and CLAUDE.md ("the trees").

Checks (--only name):
  term     out-of-scope terms (EKF, ROS 2, trajectory, guess, assum*, ...) outside the
           contexts listed in allowed.toml
  numbers  no bare units (Hz, ms, cm, ...) in SYSTEM_REQUIREMENTS.md; values live in the register
  paths    docs/project and 99_ARCHIVE only where provenance is stated
  links    every relative markdown link resolves
  prm      every PRM-XXX-nn reference is defined in PARAMETER_REGISTER.md

Output: one line per finding, "path:line: check: detail". Exit 0 clean, 1 findings.
"""
import argparse
import fnmatch
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
TERMS = re.compile(
    r"EKF|ROS ?2|ros2_control|MoveIt|500 Hz|PL/SIL|PL or SIL|\bCTO\b|"
    r"system decision authority|differential|trajectory|estimator|guess|assum[a-z]*",
    re.I)
REQUIREMENTS = "Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md"
REGISTER = "Documentation/06_CONFIGURATION/PARAMETER_REGISTER.md"
UNITS = re.compile(r"[0-9]+ ?(?:Hz|MHz|Mbps|kbps|ms|µs|us|cm|s)\b")
CONSTANTS = re.compile(r"512-byte|490-byte|CRC-32|11-bit|64-bit|18-byte|24-byte|Mode 0")
STALE = re.compile(r"docs/project|99_ARCHIVE")
STALE_OK = {"Documentation/00_INDEX.md", "CLAUDE.md", "Documentation/CHARTER_ALIGNMENT_PLAN.md"}
LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
PRM = re.compile(r"PRM-[A-Z]+-[0-9]+")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")


def doc_files():
    files = sorted(ROOT.glob("Documentation/**/*.md"))
    files += sorted(ROOT.glob("Arm_Sensor_Hub/Documentation/*.md"))
    files += sorted(ROOT.glob("RaspberryPi_Sensor_Hub/Documentation/*.md"))
    files += [ROOT / "README.md", ROOT / "CLAUDE.md"]
    return [f for f in files if f.is_file()]


def lines_with_heading(path):
    """Yield (line number, text, nearest preceding heading); headings in code fences are ignored."""
    heading, fenced = "", False
    for n, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if text.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and (m := HEADING.match(text)):
            heading = m.group(1)
        yield n, text, heading


def norm(term):
    return term.lower().replace(" ", "")


# A line that names a non-goal as such, or records provenance, is an allowed context
# (CHARTER_ALIGNMENT_PLAN.md section 3, item 1 and item 7).
CONTEXT_MARKERS = ("non-goal", "withdrawn", "deferred", "not now", "no rating", "no pl or sil",
                   "inspired by", "git history", "reconciled from", "provenance", "legacy")


def in_marked_context(line):
    low = line.lower()
    return any(k in low for k in CONTEXT_MARKERS)


def is_allowed(rules, rel, term, heading, line):
    if in_marked_context(line):
        return True
    for r in rules:
        if not fnmatch.fnmatch(rel, r["path"]):
            continue
        if "heading" in r and r["heading"].lower() not in heading.lower():
            continue
        if "terms" in r and not any(fnmatch.fnmatch(norm(term), norm(t)) for t in r["terms"]):
            continue
        return True
    return False


def check_terms(files):
    rules = tomllib.loads((HERE / "allowed.toml").read_text(encoding="utf-8")).get("allowed", [])
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        for n, text, heading in lines_with_heading(f):
            for m in TERMS.finditer(text):
                if not is_allowed(rules, rel, m.group(0), heading, text):
                    yield rel, n, f"'{m.group(0)}' outside an allowed context"


def check_numbers(files):
    path = ROOT / REQUIREMENTS
    if not path.is_file():
        yield REQUIREMENTS, 0, "file not found"
        return
    for n, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for m in UNITS.finditer(CONSTANTS.sub("", text)):
            yield REQUIREMENTS, n, f"numeric value '{m.group(0)}' belongs in the parameter register"


def check_paths(files):
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        if rel in STALE_OK:
            continue
        for n, text in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if in_marked_context(text):
                continue
            for m in STALE.finditer(text):
                yield rel, n, f"stale path '{m.group(0)}'"


def check_links(files):
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        for n, text in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in LINK.finditer(text):
                target = m.group(1)
                if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target):  # http:, https:, mailto:, ...
                    continue
                target = target.split("#", 1)[0].replace("%20", " ")
                if target and not (f.parent / target).exists():
                    yield rel, n, f"broken link '{m.group(1)}'"


def check_prm(files):
    reg = ROOT / REGISTER
    defined = set()
    if reg.is_file():
        for text in reg.read_text(encoding="utf-8").splitlines():
            if m := re.match(r"\|\s*(PRM-[A-Z]+-[0-9]+)", text):
                defined.add(m.group(1))
    else:
        yield REGISTER, 0, "register not found"
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        for n, text in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in PRM.finditer(text):
                if m.group(0) not in defined:
                    yield rel, n, f"{m.group(0)} is not defined in the register"


CHECKS = {"term": check_terms, "numbers": check_numbers, "paths": check_paths,
          "links": check_links, "prm": check_prm}


def main():
    ap = argparse.ArgumentParser(description="Karetao documentation check")
    ap.add_argument("--only", choices=CHECKS, help="run one check")
    ap.add_argument("--quiet", action="store_true", help="print no findings, only the exit code")
    args = ap.parse_args()
    files = doc_files()
    total = 0
    for name in [args.only] if args.only else CHECKS:
        for rel, n, detail in CHECKS[name](files):
            total += 1
            if not args.quiet:
                print(f"{rel}:{n}: {name}: {detail}")
    if not args.quiet:
        print(f"doc_check: {total} finding(s)" if total else "doc_check: clean")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
