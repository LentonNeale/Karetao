"""
Review and approval management for ICM artifacts.

Handles artifact review actions including approvals, comments, questions, and tier selection.
"""

import argparse
import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import icmlib
import checkpoint_policy


def cmd_approve(args):
    """Approve an artifact."""
    root = args.root
    project = args.project
    artifact_path = Path(args.artifact)

    # Check path is inside outputs
    try:
        artifact_path = icmlib.check_inside_outputs(root, artifact_path)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not artifact_path.exists():
        print(f"error: artifact not found: {artifact_path}", file=sys.stderr)
        return 1

    # Get the header and check tier
    header = icmlib.read_header(artifact_path)
    task = icmlib.task_of(artifact_path, header)
    tier = icmlib.task_tier(root, task)

    # Check open questions
    num_open_questions = icmlib.open_questions(artifact_path)
    if num_open_questions > 0:
        print(f"error: cannot approve with {num_open_questions} open question(s)", file=sys.stderr)
        return 1

    # An agent may not approve over the User's request for changes; the author must revise first.
    if header.get("status") == "changes-requested":
        try:
            approver_kind = icmlib.parse_identity(args.as_identity)[0]
        except ValueError:
            approver_kind = ""
        if approver_kind == "agent":
            print("error: changes were requested; the author must revise before an agent can approve", file=sys.stderr)
            return 1

    # Get checkpoint
    cp = icmlib.checkpoint_of(artifact_path)
    if not cp:
        print(f"error: artifact has no checkpoint", file=sys.stderr)
        return 1

    # Get author
    author = header.get("author", "")
    if not author:
        print(f"error: artifact has no author", file=sys.stderr)
        return 1

    # Check permissions using may_approve
    allowed, reason = checkpoint_policy.may_approve(cp, tier, author, args.as_identity)
    if not allowed:
        print(f"error: {reason}", file=sys.stderr)
        return 1

    # Validate that the approver is a user or authorized agent
    try:
        kind, name, model = icmlib.parse_identity(args.as_identity)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    # Check role for user/helper
    if kind in ("user", "helper"):
        people = icmlib.load_people(project)
        if name not in people or people[name] != kind:
            print(f"error: {args.as_identity} has unknown or wrong role", file=sys.stderr)
            return 1

    # Update status and approver
    icmlib.write_header(artifact_path, {
        "status": "approved",
        "approver": args.as_identity,
        "approved_at": icmlib.now_iso(),
    })

    # Append review entry
    icmlib.append_review(artifact_path, "approve", args.as_identity, "")

    return 0


def cmd_request_changes(args):
    """Request changes on an artifact."""
    root = args.root
    project = args.project
    artifact_path = Path(args.artifact)

    # Check path is inside outputs
    try:
        artifact_path = icmlib.check_inside_outputs(root, artifact_path)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not artifact_path.exists():
        print(f"error: artifact not found: {artifact_path}", file=sys.stderr)
        return 1

    # Check role
    try:
        kind, name, _ = icmlib.parse_identity(args.as_identity)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if kind != "user":
        print("error: only users can request changes", file=sys.stderr)
        return 1

    people = icmlib.load_people(project)
    if name not in people or people[name] != "user":
        print(f"error: {args.as_identity} is not a user", file=sys.stderr)
        return 1

    # Update status
    icmlib.write_header(artifact_path, {"status": "changes-requested"})

    # Append review entry
    icmlib.append_review(artifact_path, "request-changes", args.as_identity, args.text)

    return 0


def cmd_comment(args):
    """Add a comment to an artifact."""
    root = args.root
    project = args.project
    artifact_path = Path(args.artifact)

    # Check path is inside outputs
    try:
        artifact_path = icmlib.check_inside_outputs(root, artifact_path)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not artifact_path.exists():
        print(f"error: artifact not found: {artifact_path}", file=sys.stderr)
        return 1

    # Check role
    try:
        kind, name, _ = icmlib.parse_identity(args.as_identity)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if kind not in ("user", "agent"):
        print("error: only users and agents can comment", file=sys.stderr)
        return 1

    # For users, check they exist in people.md
    if kind == "user":
        people = icmlib.load_people(project)
        if name not in people or people[name] != "user":
            print(f"error: {args.as_identity} is not a user", file=sys.stderr)
            return 1

    # Append review entry (doesn't change status)
    icmlib.append_review(artifact_path, "comment", args.as_identity, args.text)

    return 0


def cmd_ask(args):
    """Ask a question on a brief or spec."""
    root = args.root
    project = args.project
    artifact_path = Path(args.artifact)

    # Check path is inside outputs
    try:
        artifact_path = icmlib.check_inside_outputs(root, artifact_path)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not artifact_path.exists():
        print(f"error: artifact not found: {artifact_path}", file=sys.stderr)
        return 1

    # Check that it's a brief or spec
    cp = icmlib.checkpoint_of(artifact_path)
    if cp not in ("C1", "C2"):
        print("error: can only ask on briefs and specs", file=sys.stderr)
        return 1

    # Check role
    try:
        kind, name, _ = icmlib.parse_identity(args.as_identity)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if kind != "user":
        print("error: only users can ask questions", file=sys.stderr)
        return 1

    people = icmlib.load_people(project)
    if name not in people or people[name] != "user":
        print(f"error: {args.as_identity} is not a user", file=sys.stderr)
        return 1

    # Update status to needs-clarification
    icmlib.write_header(artifact_path, {"status": "needs-clarification"})

    # Append review entry
    icmlib.append_review(artifact_path, "question", args.as_identity, args.text)

    return 0


def cmd_answer(args):
    """Answer a question on an artifact."""
    root = args.root
    project = args.project
    artifact_path = Path(args.artifact)

    # Check path is inside outputs
    try:
        artifact_path = icmlib.check_inside_outputs(root, artifact_path)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not artifact_path.exists():
        print(f"error: artifact not found: {artifact_path}", file=sys.stderr)
        return 1

    # Check role
    try:
        kind, name, _ = icmlib.parse_identity(args.as_identity)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if kind not in ("user", "agent"):
        print("error: only users and agents can answer", file=sys.stderr)
        return 1

    # For users, check they exist in people.md
    if kind == "user":
        people = icmlib.load_people(project)
        if name not in people or people[name] != "user":
            print(f"error: {args.as_identity} is not a user", file=sys.stderr)
            return 1

    # Append review entry
    icmlib.append_review(artifact_path, "answer", args.as_identity, args.text)

    # Check if all questions are answered, if so reset to draft
    num_open = icmlib.open_questions(artifact_path)
    if num_open == 0:
        icmlib.write_header(artifact_path, {"status": "draft"})

    return 0


def cmd_suggest_tier(args):
    """Suggest a tier for a brief."""
    root = args.root
    project = args.project
    brief_path = Path(args.brief)

    # Check path is inside outputs
    try:
        brief_path = icmlib.check_inside_outputs(root, brief_path)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not brief_path.exists():
        print(f"error: brief not found: {brief_path}", file=sys.stderr)
        return 1

    # Check that it's a brief
    cp = icmlib.checkpoint_of(brief_path)
    if cp != "C1":
        print("error: can only suggest tier on briefs", file=sys.stderr)
        return 1

    # Check role - only orchestrator
    try:
        kind, name, model = icmlib.parse_identity(args.as_identity)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if kind != "agent" or name != "orchestrator":
        print("error: only the orchestrator can suggest tier", file=sys.stderr)
        return 1

    # Update tier_suggested
    icmlib.write_header(brief_path, {"tier_suggested": args.tier})

    # Append review entry
    icmlib.append_review(brief_path, "tier-suggest", args.as_identity, args.text)

    return 0


def cmd_set_tier(args):
    """Set the tier for a brief."""
    root = args.root
    project = args.project
    brief_path = Path(args.brief)

    # Check path is inside outputs
    try:
        brief_path = icmlib.check_inside_outputs(root, brief_path)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not brief_path.exists():
        print(f"error: brief not found: {brief_path}", file=sys.stderr)
        return 1

    # Check that it's a brief
    cp = icmlib.checkpoint_of(brief_path)
    if cp != "C1":
        print("error: can only set tier on briefs", file=sys.stderr)
        return 1

    # Check role - only users
    try:
        kind, name, _ = icmlib.parse_identity(args.as_identity)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if kind != "user":
        print("error: only users can set tier", file=sys.stderr)
        return 1

    people = icmlib.load_people(project)
    if name not in people or people[name] != "user":
        print(f"error: {args.as_identity} is not a user", file=sys.stderr)
        return 1

    # Update tier
    icmlib.write_header(brief_path, {"tier": args.tier})

    # Append review entry
    icmlib.append_review(brief_path, "tier-set", args.as_identity, "")

    return 0


def cmd_reopen(args):
    """Reopen an artifact."""
    root = args.root
    project = args.project
    artifact_path = Path(args.artifact)

    # Check path is inside outputs
    try:
        artifact_path = icmlib.check_inside_outputs(root, artifact_path)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if not artifact_path.exists():
        print(f"error: artifact not found: {artifact_path}", file=sys.stderr)
        return 1

    # Check role - only users
    try:
        kind, name, _ = icmlib.parse_identity(args.as_identity)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if kind != "user":
        print("error: only users can reopen", file=sys.stderr)
        return 1

    people = icmlib.load_people(project)
    if name not in people or people[name] != "user":
        print(f"error: {args.as_identity} is not a user", file=sys.stderr)
        return 1

    # Check that the approver is an agent
    header = icmlib.read_header(artifact_path)
    approver = header.get("approver", "")
    if not approver:
        print("error: artifact was not approved", file=sys.stderr)
        return 1

    try:
        kind, _, _ = icmlib.parse_identity(approver)
    except ValueError:
        print("error: invalid approver identity in artifact", file=sys.stderr)
        return 1

    if kind != "agent":
        print("error: can only reopen if approved by an agent", file=sys.stderr)
        return 1

    # Clear approver and reset status
    icmlib.write_header(artifact_path, {
        "status": "draft",
        "approver": "",
        "approved_at": "",
    })

    # Append review entry
    icmlib.append_review(artifact_path, "reopen", args.as_identity, "")

    return 0


def main(argv=None) -> int:
    """CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="ICM artifact review")
    parser.add_argument("--root", type=Path, default=None, help="Root directory")
    parser.add_argument("--project", type=Path, default=None, help="Project directory")
    parser.add_argument("--as", dest="as_identity", default="user:anonymous", help="User identity")

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # approve command
    approve_parser = subparsers.add_parser("approve", help="Approve an artifact")
    approve_parser.add_argument("artifact", help="Artifact path")

    # request-changes command
    request_changes_parser = subparsers.add_parser("request-changes", help="Request changes")
    request_changes_parser.add_argument("artifact", help="Artifact path")
    request_changes_parser.add_argument("--text", required=True, help="Change request text")

    # comment command
    comment_parser = subparsers.add_parser("comment", help="Add a comment")
    comment_parser.add_argument("artifact", help="Artifact path")
    comment_parser.add_argument("--text", required=True, help="Comment text")

    # ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a question")
    ask_parser.add_argument("artifact", help="Brief or spec path")
    ask_parser.add_argument("--text", required=True, help="Question text")

    # answer command
    answer_parser = subparsers.add_parser("answer", help="Answer a question")
    answer_parser.add_argument("artifact", help="Artifact path")
    answer_parser.add_argument("--text", required=True, help="Answer text")

    # suggest-tier command
    suggest_tier_parser = subparsers.add_parser("suggest-tier", help="Suggest a tier")
    suggest_tier_parser.add_argument("brief", help="Brief path")
    suggest_tier_parser.add_argument("tier", choices=["T1", "T2", "T3", "T4"], help="Suggested tier")
    suggest_tier_parser.add_argument("--text", required=True, help="Suggestion reason")

    # set-tier command
    set_tier_parser = subparsers.add_parser("set-tier", help="Set the tier")
    set_tier_parser.add_argument("brief", help="Brief path")
    set_tier_parser.add_argument("tier", choices=["T1", "T2", "T3", "T4"], help="Tier to set")

    # reopen command
    reopen_parser = subparsers.add_parser("reopen", help="Reopen an artifact")
    reopen_parser.add_argument("artifact", help="Artifact path")

    args = parser.parse_args(argv)

    # Set defaults for root and project
    if args.root is None:
        args.root = icmlib.default_root()
    if args.project is None:
        args.project = icmlib.default_project(args.root)

    # Check for unknown identity
    try:
        kind, name, _ = icmlib.parse_identity(args.as_identity)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    # Execute command
    if args.command == "approve":
        return cmd_approve(args)
    elif args.command == "request-changes":
        return cmd_request_changes(args)
    elif args.command == "comment":
        return cmd_comment(args)
    elif args.command == "ask":
        return cmd_ask(args)
    elif args.command == "answer":
        return cmd_answer(args)
    elif args.command == "suggest-tier":
        return cmd_suggest_tier(args)
    elif args.command == "set-tier":
        return cmd_set_tier(args)
    elif args.command == "reopen":
        return cmd_reopen(args)
    else:
        print("error: unknown command", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
