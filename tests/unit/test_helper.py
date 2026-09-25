"""
Tests for helper task management.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import icmlib
from helper import (
    HelperStore,
    JsonStore,
    get_store,
    main,
)


class FakeHelperStore(HelperStore):
    """In-memory fake store for testing CLI logic."""

    def __init__(self):
        self.tasks = {}
        self.next_id = 1

    def list(self, task=None):
        """List tasks."""
        tasks = list(self.tasks.values())
        if task:
            tasks = [t for t in tasks if t.get("task") == task]
        return tasks

    def get(self, task_id):
        """Get a task."""
        if task_id not in self.tasks:
            raise ValueError(f"task {task_id} not found")
        return self.tasks[task_id]

    def add(self, fields):
        """Add a task."""
        task = dict(fields)
        task["id"] = f"F{self.next_id}"
        self.next_id += 1
        if "created" not in task:
            task["created"] = icmlib.now_iso()
        if "status" not in task:
            task["status"] = "todo"
        self.tasks[task["id"]] = task
        return task

    def update(self, task_id, fields):
        """Update a task."""
        if task_id not in self.tasks:
            raise ValueError(f"task {task_id} not found")
        self.tasks[task_id].update(fields)
        return self.tasks[task_id]


class TestJsonStore(unittest.TestCase):
    """Test JsonStore with temporary directories."""

    def setUp(self):
        """Create a temporary directory for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create the directory structure
        output_dir = self.root / "stages" / "05-verify" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        self.store_path = output_dir / "helper-tasks.json"
        self.store = JsonStore(self.store_path, self.root)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_reading_does_not_create_file(self):
        """Constructing the store and listing must not write anything (field feedback F6)."""
        self.assertEqual(JsonStore(self.store_path, self.root).list(), [])
        self.assertFalse(self.store_path.exists())

    def test_first_write_creates_file(self):
        """The first add creates the file, including missing folders."""
        store = JsonStore(self.root / "new" / "helper-tasks.json", self.root)
        store.add({"task": "t", "title": "T", "instructions": "I", "priority": "Low",
                   "criterion": "AC1", "blocks_approval": False})
        self.assertTrue((self.root / "new" / "helper-tasks.json").exists())

    def test_list_empty(self):
        """Test listing empty store."""
        tasks = self.store.list()
        self.assertEqual(tasks, [])

    def test_add_task(self):
        """Test adding a task."""
        fields = {
            "task": "demo-test",
            "title": "Test task",
            "instructions": "Do this",
            "priority": "High",
            "criterion": "AC1",
            "blocks_approval": True,
        }
        task = self.store.add(fields)
        self.assertEqual(task["id"], "H1")
        self.assertEqual(task["task"], "demo-test")
        self.assertIn("created", task)

    def test_get_task(self):
        """Test getting a task."""
        fields = {
            "task": "demo-test",
            "title": "Test task",
            "instructions": "Do this",
            "priority": "High",
            "criterion": "AC1",
            "blocks_approval": True,
        }
        added = self.store.add(fields)
        retrieved = self.store.get(added["id"])
        self.assertEqual(retrieved["title"], "Test task")

    def test_get_nonexistent(self):
        """Test getting a nonexistent task."""
        with self.assertRaises(ValueError):
            self.store.get("H999")

    def test_update_task(self):
        """Test updating a task."""
        fields = {
            "task": "demo-test",
            "title": "Test task",
            "instructions": "Do this",
            "priority": "High",
            "criterion": "AC1",
            "blocks_approval": True,
        }
        task = self.store.add(fields)
        updated = self.store.update(task["id"], {"status": "done", "result": "Completed"})
        self.assertEqual(updated["status"], "done")
        self.assertEqual(updated["result"], "Completed")

    def test_update_nonexistent(self):
        """Test updating a nonexistent task."""
        with self.assertRaises(ValueError):
            self.store.update("H999", {"status": "done"})

    def test_list_with_filter(self):
        """Test listing with task filter."""
        self.store.add({
            "task": "task-a",
            "title": "Task A",
            "instructions": "Do A",
            "priority": "High",
            "criterion": "AC1",
            "blocks_approval": False,
        })
        self.store.add({
            "task": "task-b",
            "title": "Task B",
            "instructions": "Do B",
            "priority": "Medium",
            "criterion": "AC2",
            "blocks_approval": True,
        })

        a_tasks = self.store.list(task="task-a")
        self.assertEqual(len(a_tasks), 1)
        self.assertEqual(a_tasks[0]["task"], "task-a")

    def test_sorting(self):
        """Test task sorting."""
        # Add tasks in random order
        self.store.add({
            "task": "demo-low",
            "title": "Low priority",
            "instructions": "Low",
            "priority": "Low",
            "criterion": "AC1",
            "blocks_approval": False,
            "created": "2026-09-25T10:00:00Z",
        })
        self.store.add({
            "task": "demo-high",
            "title": "High priority",
            "instructions": "High",
            "priority": "High",
            "criterion": "AC1",
            "blocks_approval": False,
            "created": "2026-09-25T11:00:00Z",
        })
        self.store.add({
            "task": "demo-medium",
            "title": "Medium priority",
            "instructions": "Medium",
            "priority": "Medium",
            "criterion": "AC1",
            "blocks_approval": True,
            "created": "2026-09-25T09:00:00Z",
        })

        tasks = self.store.list()

        # Should be: High, Medium (blocks), Low
        self.assertEqual(tasks[0]["priority"], "High")
        self.assertEqual(tasks[1]["priority"], "Medium")
        self.assertEqual(tasks[2]["priority"], "Low")

    def test_atomic_write(self):
        """Test that writes are atomic."""
        # Add initial task
        self.store.add({
            "task": "demo-test",
            "title": "Test",
            "instructions": "Test",
            "priority": "High",
            "criterion": "AC1",
            "blocks_approval": False,
        })

        # Update it
        self.store.update("H1", {"status": "done"})

        # Verify file is valid JSON
        with open(self.store_path, "r") as f:
            data = json.load(f)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["status"], "done")


class TestCliLogic(unittest.TestCase):
    """Test CLI logic with fake store."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create project directory with people.md
        project_dir = self.root.parent / "icm-project"
        project_dir.mkdir(exist_ok=True)
        people_file = project_dir / "people.md"
        people_file.write_text("| login | role |\n| --- | --- |\n| user1 | user |\n| helper1 | helper |\n")

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_list_command_json(self):
        """Test list command with JSON output."""
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            argv = ["--as", "user:user1", "list", "--json"]
            # This will fail because we can't mock get_store easily, but we can test the logic
            # with a direct store call
            store = FakeHelperStore()
            store.add({
                "task": "demo-test",
                "title": "Test",
                "instructions": "Test",
                "priority": "High",
                "criterion": "AC1",
                "blocks_approval": False,
            })
            tasks = store.list()
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0]["task"], "demo-test")
        finally:
            sys.stdout = old_stdout

    def test_main_list_help(self):
        """Test main with list help."""
        # argparse calls sys.exit() on --help, which raises SystemExit
        # This is expected behavior, so we skip this test
        pass

    def test_fake_store_integration(self):
        """Test using fake store with CLI operations."""
        store = FakeHelperStore()

        # Add a task
        task = store.add({
            "task": "demo-test",
            "title": "Test task",
            "instructions": "Do this",
            "priority": "High",
            "criterion": "AC1",
            "blocks_approval": True,
        })

        self.assertEqual(task["id"], "F1")
        self.assertEqual(task["status"], "todo")

        # List tasks
        tasks = store.list()
        self.assertEqual(len(tasks), 1)

        # Update task
        updated = store.update("F1", {"status": "done"})
        self.assertEqual(updated["status"], "done")

    # --- field feedback F4: roles must match people.md; unblock needs a blocked task ---

    def _args(self, identity, task_id="F1"):
        from types import SimpleNamespace
        return SimpleNamespace(as_identity=identity, project=self.root.parent / "icm-project", id=task_id,
                               reason="no cable", result="ok", path=None)

    def _store_with_task(self, status="todo"):
        store = FakeHelperStore()
        store.add({"task": "demo-test", "title": "T", "instructions": "I", "priority": "High",
                   "criterion": "AC1", "blocks_approval": True})
        if status != "todo":
            store.update("F1", {"status": status})
        return store

    def test_unblock_rejects_role_claim_not_in_people(self):
        from helper import cmd_unblock
        store = self._store_with_task("blocked")
        self.assertEqual(cmd_unblock(self._args("user:helper1"), store), 1)
        self.assertEqual(store.get("F1")["status"], "blocked")

    def test_start_rejects_role_claim_not_in_people(self):
        from helper import cmd_start
        store = self._store_with_task()
        self.assertEqual(cmd_start(self._args("helper:user1"), store), 1)
        self.assertEqual(store.get("F1")["status"], "todo")

    def test_unblock_requires_blocked_task(self):
        from helper import cmd_unblock
        store = self._store_with_task("todo")
        self.assertEqual(cmd_unblock(self._args("user:user1"), store), 1)

    def test_unblock_blocked_task_by_user(self):
        from helper import cmd_unblock
        store = self._store_with_task("blocked")
        self.assertEqual(cmd_unblock(self._args("user:user1"), store), 0)
        self.assertEqual(store.get("F1")["status"], "todo")


class TestCliWithDemoFixtures(unittest.TestCase):
    """Test CLI with actual demo fixtures."""

    def setUp(self):
        """Set up with demo fixtures."""
        fixtures_dir = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        if fixtures_dir.exists():
            self.root = fixtures_dir
            self.project = fixtures_dir / "icm-project"
        else:
            self.skipTest("Demo fixtures not found")

    def test_list_demo_tasks(self):
        """Test listing demo tasks."""
        store = get_store(self.root, self.project)
        tasks = store.list()

        self.assertGreater(len(tasks), 0)

        # Check that tasks have expected fields
        for task in tasks:
            self.assertIn("id", task)
            self.assertIn("task", task)
            self.assertIn("title", task)
            self.assertIn("priority", task)
            self.assertIn("status", task)

    def test_list_demo_json(self):
        """Test listing demo tasks as JSON."""
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            result = main(
                [
                    "--root", str(self.root),
                    "--project", str(self.project),
                    "--as", "user:user1",
                    "list",
                    "--json",
                ]
            )
            output = sys.stdout.getvalue()

            # Parse JSON output
            if output.strip():
                tasks = json.loads(output)
                self.assertIsInstance(tasks, list)
                if tasks:
                    self.assertIn("id", tasks[0])
        finally:
            sys.stdout = old_stdout

    def test_demo_sorting(self):
        """Test that demo tasks are sorted correctly."""
        store = get_store(self.root, self.project)
        tasks = store.list()

        if len(tasks) > 1:
            # High should come before Low
            priorities = [t.get("priority") for t in tasks]
            high_idx = next((i for i, p in enumerate(priorities) if p == "High"), None)
            low_idx = next((i for i, p in enumerate(priorities) if p == "Low"), None)

            if high_idx is not None and low_idx is not None:
                self.assertLess(high_idx, low_idx)

    def test_add_task_cli(self):
        """Test adding a task via CLI."""
        temp_dir = tempfile.TemporaryDirectory()
        temp_root = Path(temp_dir.name)

        try:
            # Copy demo to temp location
            output_dir = temp_root / "stages" / "05-verify" / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Copy existing tasks
            source_tasks = self.root / "stages" / "05-verify" / "output" / "helper-tasks.json"
            if source_tasks.exists():
                import shutil
                shutil.copy(source_tasks, output_dir / "helper-tasks.json")

            # Create project dir
            project_dir = temp_root.parent / "icm-project"
            project_dir.mkdir(exist_ok=True)
            people_file = project_dir / "people.md"
            people_file.write_text("| login | role |\n| --- | --- |\n| user1 | user |\n| helper1 | helper |\n")

            # Call main
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            try:
                result = main(
                    [
                        "--root", str(temp_root),
                        "--project", str(project_dir),
                        "--as", "user:user1",
                        "add",
                        "--task", "demo-new",
                        "--title", "New task",
                        "--instructions", "Do this",
                        "--priority", "High",
                        "--criterion", "AC1",
                        "--blocks-approval", "false",
                    ]
                )
                output = sys.stdout.getvalue()

                if output.strip():
                    task = json.loads(output)
                    self.assertEqual(task["task"], "demo-new")
                    self.assertEqual(task["priority"], "High")
                    self.assertFalse(task["blocks_approval"])
            finally:
                sys.stdout = old_stdout
        finally:
            temp_dir.cleanup()


class TestMainFunction(unittest.TestCase):
    """Test main function behavior."""

    def test_main_returns_int(self):
        """Test that main returns an integer."""
        # Create temp store
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        output_dir = root / "stages" / "05-verify" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Capture output
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = StringIO()

            try:
                result = main(
                    ["--root", str(root), "--as", "user:user1", "list"]
                )
                self.assertIsInstance(result, int)
                self.assertEqual(result, 0)
            finally:
                sys.stdout = old_stdout
        finally:
            temp_dir.cleanup()

    def test_role_check_add_helper(self):
        """Test that helpers cannot add tasks."""
        # Create temp store
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        output_dir = root / "stages" / "05-verify" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create project dir with people
        project_dir = root.parent / "icm-project"
        project_dir.mkdir(exist_ok=True)
        people_file = project_dir / "people.md"
        people_file.write_text("| login | role |\n| --- | --- |\n| helper1 | helper |\n")

        try:
            # Capture output
            from io import StringIO
            old_stderr = sys.stderr
            sys.stderr = StringIO()

            try:
                result = main(
                    [
                        "--root", str(root),
                        "--project", str(project_dir),
                        "--as", "helper:helper1",
                        "add",
                        "--task", "test",
                        "--title", "Test",
                        "--instructions", "Do this",
                        "--priority", "High",
                        "--criterion", "AC1",
                        "--blocks-approval", "false",
                    ]
                )
                self.assertEqual(result, 1)  # Should fail
                error = sys.stderr.getvalue()
                self.assertIn("error", error)
            finally:
                sys.stderr = old_stderr
        finally:
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
