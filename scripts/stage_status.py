"""
Stage status collection and reporting for ICM workflow.
"""

import argparse
import json
import sys
from pathlib import Path

# Import from icmlib and checkpoint_policy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from icmlib import (
    default_root, default_project, list_artifacts, read_header,
    checkpoint_of, open_questions
)
from checkpoint_policy import blocking, approver_needed


def collect(root, project):
    """
    Collect stage status for all tasks.
    Returns a list of dicts, one per task, sorted by task name.
    """
    root = Path(root)
    project = Path(project)

    # List all artifacts
    artifacts = list_artifacts(root)

    # First pass: extract all tasks and their tier/tier_suggested info
    task_info = {}  # task -> {tier, tier_suggested}

    for artifact_path in artifacts:
        header = read_header(artifact_path)
        task = header.get("task", "")
        if not task:
            continue

        if task not in task_info:
            task_info[task] = {"tier": "", "tier_suggested": ""}

        # If this is a brief (C1), get tier and tier_suggested
        if artifact_path.name.endswith("-brief.md"):
            task_info[task]["tier"] = header.get("tier", "")
            task_info[task]["tier_suggested"] = header.get("tier_suggested", "")

    # Group artifacts by task
    tasks = {}
    for artifact_path in artifacts:
        header = read_header(artifact_path)
        task = header.get("task", "")
        if not task:
            continue

        if task not in tasks:
            tasks[task] = {"artifacts": []}

        # Get stage from path: stages/NN-name/output/...
        parts = artifact_path.relative_to(root).parts
        stage = parts[1]  # NN-name

        checkpoint = checkpoint_of(artifact_path)

        # Determine status (from header)
        status = header.get("status", "draft")

        # Get author and approver
        author = header.get("author", "")
        approver = header.get("approver", "")

        # Count open questions
        question_count = open_questions(artifact_path)

        # Get mtime
        mtime = artifact_path.stat().st_mtime
        mtime_str = str(mtime)  # Will be converted to ISO string if needed

        # Get tier from our first pass
        tier = task_info.get(task, {}).get("tier", "")

        # Determine "awaiting" state
        awaiting = "none"
        reason = ""

        if status in ("approved", "applied"):
            awaiting = "none"
        elif checkpoint is None:
            awaiting = "none"
        elif status == "needs-clarification":
            awaiting = "agent"
            reason = "needs clarification"
        elif status == "changes-requested":
            awaiting = "agent"
            reason = "changes requested"
        elif tier == "":
            # Tier not selected yet
            if checkpoint == "C1":
                awaiting = "user"
                reason = "select tier"
        else:
            # Use approver_needed
            needed = approver_needed(checkpoint, tier, author)
            if needed == "none":
                awaiting = "none"
            else:
                awaiting = needed
                if needed == "user":
                    if blocking(checkpoint, tier):
                        reason = "user approval (blocking)"
                    else:
                        reason = "user approval (non-blocking)"
                elif needed == "orchestrator":
                    if blocking(checkpoint, tier):
                        reason = "orchestrator approval (blocking)"
                    else:
                        reason = "orchestrator approval (non-blocking)"

        # Determine "blocking" state
        if awaiting == "none":
            is_blocking = False
        else:
            is_blocking = blocking(checkpoint, tier)

        artifact_entry = {
            "path": str(artifact_path.relative_to(root)),
            "stage": stage,
            "checkpoint": checkpoint,
            "status": status,
            "author": author,
            "approver": approver,
            "open_questions": question_count,
            "awaiting": awaiting,
            "blocking": is_blocking,
            "reason": reason,
            "mtime": mtime_str,
        }

        tasks[task]["artifacts"].append(artifact_entry)

    # Build final output
    result = []
    for task in sorted(tasks.keys()):
        tier = task_info.get(task, {}).get("tier", "")
        tier_suggested = task_info.get(task, {}).get("tier_suggested", "")

        # Determine can_proceed
        can_proceed = not any(
            art["blocking"] for art in tasks[task]["artifacts"]
        )

        task_entry = {
            "task": task,
            "tier": tier,
            "tier_suggested": tier_suggested,
            "can_proceed": can_proceed,
            "artifacts": tasks[task]["artifacts"],
        }

        result.append(task_entry)

    return result


def main(argv=None):
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Collect and report ICM stage status"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=default_root(),
        help="Root directory (parent of stages/)",
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=None,
        help="Project directory (contains people.md)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (default: Markdown table)",
    )
    parser.add_argument(
        "--awaiting",
        choices=["user", "orchestrator", "agent"],
        help="Filter to artifacts awaiting a specific approver type",
    )

    args = parser.parse_args(argv)

    if args.project is None:
        args.project = default_project(args.root)

    # Collect status
    tasks = collect(args.root, args.project)

    # Filter by awaiting if requested
    if args.awaiting:
        filtered_tasks = []
        for task in tasks:
            filtered_artifacts = [
                art for art in task["artifacts"]
                if art["awaiting"] == args.awaiting
            ]
            if filtered_artifacts:
                task = dict(task)
                task["artifacts"] = filtered_artifacts
                filtered_tasks.append(task)
        tasks = filtered_tasks

    # Output
    if args.json:
        print(json.dumps(tasks, indent=2))
    else:
        # Print as Markdown table
        print("| Task | Tier | Can proceed | Artifact | Status | Awaiting | Reason |")
        print("|---|---|---|---|---|---|---|")
        for task in tasks:
            tier = task["tier"] or "—"
            can_proceed = "Yes" if task["can_proceed"] else "No"
            for art in task["artifacts"]:
                name = art["path"].rsplit("/", 1)[-1]
                print(f"| {task['task']} | {tier} | {can_proceed} | {name} | {art['status']} "
                      f"| {art['awaiting']} | {art.get('reason', '')} |")

    return 0


if __name__ == "__main__":
    sys.exit(main())
