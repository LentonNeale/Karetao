"""
Helper task management for ICM prototype.

Provides HelperStore interface, JsonStore implementation, and CLI.
"""

import argparse
import json
import sys
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import icmlib


class HelperStore(ABC):
    """Abstract interface for helper task storage."""

    @abstractmethod
    def list(self, task=None) -> list[dict]:
        """
        List tasks, optionally filtered by task.
        Returns sorted list of task dicts.
        """
        pass

    @abstractmethod
    def get(self, task_id) -> dict:
        """Get a single task by id."""
        pass

    @abstractmethod
    def add(self, fields) -> dict:
        """
        Add a new task.
        Returns the stored task with its id.
        """
        pass

    @abstractmethod
    def update(self, task_id, fields) -> dict:
        """
        Update a task.
        Returns the updated task.
        """
        pass


class JsonStore(HelperStore):
    """JSON file-based helper task store with atomic writes."""

    def __init__(self, path: Path, root: Path):
        self.path = Path(path)
        self.root = Path(root)

    def _read_tasks(self) -> list[dict]:
        """Read all tasks from file."""
        try:
            with open(self.path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_tasks(self, tasks: list[dict]) -> None:
        """Atomically write tasks to file."""
        # The file is created on the first write, so viewing tasks never writes (field feedback F6).
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Use a temporary file in the same directory for atomic write
        temp_fd, temp_path = tempfile.mkstemp(dir=self.path.parent)
        try:
            with open(temp_fd, "w") as f:
                json.dump(tasks, f)
            # Atomic rename
            Path(temp_path).replace(self.path)
        except Exception:
            Path(temp_path).unlink(missing_ok=True)
            raise

    def _sort_tasks(self, tasks: list[dict]) -> list[dict]:
        """Sort tasks according to the contract."""
        # Priority: High, Medium, Low
        priority_rank = {"High": 0, "Medium": 1, "Low": 2}

        # Tier: T4, T3, T2, T1, empty
        tier_rank = {"T4": 0, "T3": 1, "T2": 2, "T1": 3, "": 4}

        def sort_key(task):
            task_id = task.get("id", "")
            task_name = task.get("task", "")
            priority = task.get("priority", "Medium")
            blocks = task.get("blocks_approval", False)
            created = task.get("created", "")

            # Get tier for this task
            tier = icmlib.task_tier(self.root, task_name)

            return (
                priority_rank.get(priority, 99),
                -int(blocks),  # true (1) becomes -1, false (0) becomes 0
                tier_rank.get(tier, 99),
                created,
            )

        return sorted(tasks, key=sort_key)

    def list(self, task=None) -> list[dict]:
        """List tasks, optionally filtered by task."""
        tasks = self._read_tasks()
        if task:
            tasks = [t for t in tasks if t.get("task") == task]
        return self._sort_tasks(tasks)

    def get(self, task_id) -> dict:
        """Get a single task by id."""
        tasks = self._read_tasks()
        for task in tasks:
            if task.get("id") == task_id:
                return task
        raise ValueError(f"task {task_id} not found")

    def add(self, fields) -> dict:
        """Add a new task."""
        tasks = self._read_tasks()

        # Generate new id
        max_id = 0
        for task in tasks:
            task_id = task.get("id", "")
            if task_id.startswith("H"):
                try:
                    max_id = max(max_id, int(task_id[1:]))
                except ValueError:
                    pass
        new_id = f"H{max_id + 1}"

        # Create task record
        task = dict(fields)
        task["id"] = new_id
        if "created" not in task:
            task["created"] = icmlib.now_iso()
        if "status" not in task:
            task["status"] = "todo"

        tasks.append(task)
        self._write_tasks(tasks)
        return task

    def update(self, task_id, fields) -> dict:
        """Update a task."""
        tasks = self._read_tasks()
        for i, task in enumerate(tasks):
            if task.get("id") == task_id:
                task.update(fields)
                self._write_tasks(tasks)
                return task
        raise ValueError(f"task {task_id} not found")


def get_store(root: Path = None, project: Path = None) -> JsonStore:
    """Get the helper task store."""
    if root is None:
        root = icmlib.default_root()
    if project is None:
        project = icmlib.default_project(root)

    root = Path(root)
    store_path = root / "stages" / "05-verify" / "output" / "helper-tasks.json"
    return JsonStore(store_path, root)


def cmd_list(args, store):
    """List helper tasks."""
    tasks = store.list(task=args.task)

    if args.json:
        print(json.dumps(tasks))
    else:
        # Print as table
        if not tasks:
            print("No tasks")
            return 0

        # Simple text output
        for task in tasks:
            priority = task.get("priority", "")
            task_name = task.get("task", "")
            criterion = task.get("criterion", "")
            title = task.get("title", "")
            status = task.get("status", "")
            blocks = "blocks" if task.get("blocks_approval") else ""

            print(f"{task['id']} [{status}] {priority} {blocks} {task_name}/{criterion}: {title}")

    return 0


def cmd_add(args, store):
    """Add a new helper task (users and agents only)."""
    # Get the current user
    identity_str = args.as_identity
    kind, name, _ = icmlib.parse_identity(identity_str)

    if kind == "helper":
        print("error: helpers cannot add tasks", file=sys.stderr)
        return 1

    fields = {
        "task": args.task,
        "title": args.title,
        "instructions": args.instructions,
        "priority": args.priority,
        "criterion": args.criterion,
        "blocks_approval": args.blocks_approval.lower() == "true",
    }

    task = store.add(fields)
    print(json.dumps(task))
    return 0


def cmd_start(args, store):
    """Start a task (set assignee)."""
    # Get the current user as assignee
    identity_str = args.as_identity
    kind, name, _ = icmlib.parse_identity(identity_str)

    if kind != "helper":
        print("error: only helpers can start tasks", file=sys.stderr)
        return 1

    task = store.update(args.id, {"assignee": name, "status": "doing"})
    print(json.dumps(task))
    return 0


def cmd_done(args, store):
    """Mark a task as done."""
    # Get the current user as assignee
    identity_str = args.as_identity
    kind, name, _ = icmlib.parse_identity(identity_str)

    if kind != "helper":
        print("error: only helpers can mark tasks as done", file=sys.stderr)
        return 1

    fields = {
        "status": "done",
        "assignee": name,
        "result": args.result,
    }

    if args.path:
        fields["result_path"] = args.path

    task = store.update(args.id, fields)
    print(json.dumps(task))
    return 0


def cmd_block(args, store):
    """Block a task."""
    # Get the current user
    identity_str = args.as_identity
    kind, name, _ = icmlib.parse_identity(identity_str)

    if kind != "helper":
        print("error: only helpers can block tasks", file=sys.stderr)
        return 1

    task = store.update(args.id, {"status": "blocked", "blocked_reason": args.reason})
    print(json.dumps(task))
    return 0


def cmd_unblock(args, store):
    """Unblock a task."""
    # Get the current user
    identity_str = args.as_identity
    kind, name, _ = icmlib.parse_identity(identity_str)

    if kind != "user":
        print("error: only users can unblock tasks", file=sys.stderr)
        return 1

    task = store.update(args.id, {"status": "todo", "blocked_reason": ""})
    print(json.dumps(task))
    return 0


def main(argv=None) -> int:
    """CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Helper task management")
    parser.add_argument("--root", type=Path, default=None, help="Root directory")
    parser.add_argument("--project", type=Path, default=None, help="Project directory")
    parser.add_argument("--as", dest="as_identity", default="user:anonymous", help="User identity")

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # list command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--task", default=None, help="Filter by task")
    list_parser.add_argument("--json", action="store_true", help="JSON output")

    # add command
    add_parser = subparsers.add_parser("add", help="Add a task")
    add_parser.add_argument("--task", required=True, help="Task name")
    add_parser.add_argument("--title", required=True, help="Task title")
    add_parser.add_argument("--instructions", required=True, help="Task instructions")
    add_parser.add_argument("--priority", required=True, choices=["High", "Medium", "Low"])
    add_parser.add_argument("--criterion", required=True, help="Criterion (e.g., AC1)")
    add_parser.add_argument("--blocks-approval", required=True, help="Blocks approval (true/false)")

    # start command
    start_parser = subparsers.add_parser("start", help="Start a task")
    start_parser.add_argument("id", help="Task id")

    # done command
    done_parser = subparsers.add_parser("done", help="Mark task as done")
    done_parser.add_argument("id", help="Task id")
    done_parser.add_argument("--result", required=True, help="Result text")
    done_parser.add_argument("--path", default=None, help="Result file path")

    # block command
    block_parser = subparsers.add_parser("block", help="Block a task")
    block_parser.add_argument("id", help="Task id")
    block_parser.add_argument("--reason", required=True, help="Block reason")

    # unblock command
    unblock_parser = subparsers.add_parser("unblock", help="Unblock a task")
    unblock_parser.add_argument("id", help="Task id")

    args = parser.parse_args(argv)

    # Set defaults for root and project
    if args.root is None:
        args.root = icmlib.default_root()
    if args.project is None:
        args.project = icmlib.default_project(args.root)

    # Get store
    store = get_store(args.root, args.project)

    # Execute command
    if args.command == "list":
        return cmd_list(args, store)
    elif args.command == "add":
        return cmd_add(args, store)
    elif args.command == "start":
        return cmd_start(args, store)
    elif args.command == "done":
        return cmd_done(args, store)
    elif args.command == "block":
        return cmd_block(args, store)
    elif args.command == "unblock":
        return cmd_unblock(args, store)
    else:
        print("error: unknown command", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
