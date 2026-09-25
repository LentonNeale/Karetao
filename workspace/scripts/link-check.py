#!/usr/bin/env python3
"""Report broken relative Markdown links in the project's tracked and untracked (non-ignored) files."""
import os
import re
import subprocess
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
files = subprocess.run(
    ["git", "-C", root, "ls-files", "-co", "--exclude-standard", "*.md"],
    capture_output=True, text=True, check=True,
).stdout.splitlines()

bad = []
for rel in files:
    path = os.path.join(root, rel)
    if not os.path.exists(path):
        continue
    with open(path, encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            for target in re.findall(r"\]\(([^)\s]+)\)", line):
                if re.match(r"[a-z]+:|#", target):
                    continue
                dest = os.path.normpath(os.path.join(os.path.dirname(path), target.split("#")[0]))
                if not os.path.exists(dest):
                    bad.append(f"{rel}:{n} -> {target}")

print("\n".join(bad) if bad else "no broken relative links")
sys.exit(1 if bad else 0)
