"""
Standard-library utilities for ICM artifact and workflow management.
"""

import os
import re
from datetime import datetime
from pathlib import Path


def default_root() -> Path:
    """Return the default root (parent of scripts/)."""
    return Path(__file__).resolve().parent.parent


def default_project(root: Path = None) -> Path:
    """Return the default project directory (ROOT/../icm-project)."""
    if root is None:
        root = default_root()
    return root.parent / "icm-project"


def check_inside_outputs(root: Path, path: Path) -> Path:
    """
    Verify that path is inside ROOT/stages/*/output/.
    Returns the normalized path; raises ValueError if outside.
    """
    root = Path(root).resolve()
    path = Path(path).resolve()

    # Check if path is within any output folder
    outputs_base = root / "stages"

    try:
        # path must be relative to root and within stages/*/output/
        path.relative_to(outputs_base)
    except ValueError:
        raise ValueError(f"path {path} is outside {outputs_base}")

    # Further check: must be in some stages/*/output/
    parts = path.relative_to(outputs_base).parts
    if len(parts) < 3 or parts[1] != "output":
        raise ValueError(f"path {path} is not in stages/*/output/")

    return path


def list_artifacts(root: Path = None) -> list[Path]:
    """List all artifacts (excluding -review.md), sorted."""
    if root is None:
        root = default_root()

    root = Path(root)
    artifacts = []

    output_dirs = (root / "stages").glob("*/output")
    for output_dir in output_dirs:
        if output_dir.is_dir():
            for md_file in output_dir.glob("*.md"):
                if not md_file.name.endswith("-review.md"):
                    artifacts.append(md_file)

    return sorted(artifacts)


def read_header(path: Path) -> dict:
    """
    Read the header (fenced code block) from an artifact.
    Returns a dict of key: value pairs.
    """
    path = Path(path)
    with open(path, "r") as f:
        content = f.read()

    # Find the first fenced code block
    match = re.match(r"^```\n(.*?)\n```", content, re.DOTALL)
    if not match:
        return {}

    header_text = match.group(1)
    header = {}

    for line in header_text.split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        header[key.strip()] = value.strip()

    return header


def write_header(path: Path, updates: dict) -> None:
    """Update the header in an artifact, preserving the rest of the file."""
    path = Path(path)

    with open(path, "r") as f:
        content = f.read()

    # Parse the existing header
    match = re.match(r"^```\n(.*?)\n```", content, re.DOTALL)
    if not match:
        # No header found; create one
        header_lines = [f"{k}: {v}" for k, v in updates.items()]
        new_header = "```\n" + "\n".join(header_lines) + "\n```\n"
        content = new_header + content
        with open(path, "w") as f:
            f.write(content)
        return

    # Update existing header
    header_text = match.group(1)
    existing = {}
    for line in header_text.split("\n"):
        line = line.strip()
        if line and ":" in line:
            key, value = line.split(":", 1)
            existing[key.strip()] = value.strip()

    # Apply updates
    existing.update(updates)

    # Reconstruct header
    header_lines = [f"{k}: {v}" for k, v in existing.items()]
    new_header = "```\n" + "\n".join(header_lines) + "\n```"

    # Replace the old header with the new one
    new_content = re.sub(r"^```\n.*?\n```", new_header, content, count=1, flags=re.DOTALL)

    with open(path, "w") as f:
        f.write(new_content)


def review_path(path: Path) -> Path:
    """Return the review file path for an artifact."""
    path = Path(path)
    # Replace .md with -review.md
    return path.parent / (path.stem + "-review.md")


def read_reviews(path: Path) -> list[dict]:
    """
    Read review entries from the review file.
    Returns a list of dicts with keys: ts, kind, who, text.
    """
    review_file = review_path(path)

    if not review_file.exists():
        return []

    reviews = []
    with open(review_file, "r") as f:
        content = f.read()

    # Parse entries: ### 2026-09-25T10:00:00Z | kind | who
    # followed by the text until the next entry or EOF
    pattern = r"^### (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) \| (\w+) \| (.+)$"

    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(pattern, line)
        if match:
            ts = match.group(1)
            kind = match.group(2)
            who = match.group(3)

            # Collect text until the next ### or EOF
            text_lines = []
            i += 1
            while i < len(lines) and not re.match(pattern, lines[i]):
                text_lines.append(lines[i])
                i += 1

            text = "\n".join(text_lines).strip()
            reviews.append({"ts": ts, "kind": kind, "who": who, "text": text})
        else:
            i += 1

    return reviews


def append_review(path: Path, kind: str, who: str, text: str) -> None:
    """Append a review entry to the review file."""
    review_file = review_path(path)
    ts = now_iso()

    entry = f"### {ts} | {kind} | {who}\n{text}"

    if review_file.exists():
        with open(review_file, "a") as f:
            f.write("\n" + entry)
    else:
        with open(review_file, "w") as f:
            f.write(entry)


def open_questions(path: Path) -> int:
    """
    Count open questions (question entries - answer entries, never below 0).
    """
    reviews = read_reviews(path)
    questions = sum(1 for r in reviews if r["kind"] == "question")
    answers = sum(1 for r in reviews if r["kind"] == "answer")
    return max(0, questions - answers)


def checkpoint_of(path: Path) -> str | None:
    """
    Determine the checkpoint from the artifact filename.
    Returns checkpoint string (C1-C7) or None if no checkpoint.
    """
    path = Path(path)
    name = path.name

    # Map file endings to checkpoints
    endings = {
        "-brief.md": "C1",
        "-spec.md": "C2",
        "-design.md": "C3",
        "-docdiff.md": "C4",
        "-plan.md": "C5",
        "-evidence.md": "C6",
        "-closeout.md": "C7",
    }

    for ending, checkpoint in endings.items():
        if name.endswith(ending):
            return checkpoint

    return None


def load_people(project: Path = None) -> dict:
    """
    Load people from PROJECT/people.md.
    Returns dict mapping login -> role.
    """
    if project is None:
        project = default_project()

    project = Path(project)
    people_file = project / "people.md"

    if not people_file.exists():
        return {}

    people = {}
    with open(people_file, "r") as f:
        for line in f:
            line = line.strip()
            # Skip headers and empty lines
            if not line or line.startswith("|") and "login" in line:
                continue
            if line.startswith("|") and "---" in line:
                continue

            # Parse table rows: | login | role |
            if line.startswith("|"):
                parts = [p.strip() for p in line.split("|")]
                # Filter out empty parts from leading/trailing pipes
                parts = [p for p in parts if p]
                if len(parts) >= 2:
                    login = parts[0]
                    role = parts[1]
                    if login and role:
                        people[login] = role

    return people


def parse_identity(s: str) -> tuple[str, str, str]:
    """
    Parse an identity string.
    Returns (kind, name, model) or raises ValueError.

    Formats:
    - user:login
    - helper:login
    - agent:name/model
    """
    if not s or ":" not in s:
        raise ValueError(f"invalid identity: {s}")

    kind, rest = s.split(":", 1)

    if kind in ("user", "helper"):
        if "/" in rest:
            raise ValueError(f"invalid identity: {s}")
        return (kind, rest, "")
    elif kind == "agent":
        if "/" not in rest:
            raise ValueError(f"invalid identity: {s}")
        name, model = rest.rsplit("/", 1)
        return (kind, name, model)
    else:
        raise ValueError(f"invalid identity: {s}")


def model_rank(model: str) -> int:
    """Return the rank of a model."""
    ranks = {
        "haiku": 1,
        "sonnet": 2,
        "opus": 3,
    }
    return ranks.get(model, 99)


def find_brief(root: Path = None, task: str = None) -> Path | None:
    """
    Find the brief artifact for a task.
    Returns the path or None if not found.
    """
    if root is None:
        root = default_root()
    if task is None:
        return None

    root = Path(root)
    intake_output = root / "stages" / "01-intake" / "output"
    if not intake_output.exists():
        return None

    # The brief is the -brief.md whose header names this task (the file name may carry an issue prefix)
    for f in sorted(intake_output.glob("*-brief.md")):
        if read_header(f).get("task") == task:
            return f

    return None


def task_tier(root: Path = None, task: str = None) -> str:
    """
    Get the tier for a task from its brief.
    Returns the tier (T1-T4) or empty string if not set.
    """
    if task is None:
        return ""

    brief = find_brief(root, task)
    if not brief:
        return ""

    header = read_header(brief)
    return header.get("tier", "")


def now_iso() -> str:
    """Return the current time in ISO-8601 UTC format."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
