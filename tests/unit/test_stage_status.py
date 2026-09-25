"""
Tests for stage_status module.
"""

import json
import tempfile
import unittest
from pathlib import Path
import shutil
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from stage_status import collect, main


class TestStageStatusCollect(unittest.TestCase):
    """Tests for the collect function."""

    def setUp(self):
        """Set up demo fixtures for testing."""
        # Use the demo fixtures directly
        self.demo_root = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        self.demo_project = self.demo_root / "icm-project"

        self.assertTrue(self.demo_root.exists(), f"Demo root {self.demo_root} does not exist")
        self.assertTrue(self.demo_project.exists(), f"Demo project {self.demo_project} does not exist")

    def test_collect_returns_list_of_dicts(self):
        """Collect should return a list of task dicts."""
        result = collect(self.demo_root, self.demo_project)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

        for task in result:
            self.assertIn("task", task)
            self.assertIn("tier", task)
            self.assertIn("tier_suggested", task)
            self.assertIn("can_proceed", task)
            self.assertIn("artifacts", task)
            self.assertIsInstance(task["artifacts"], list)

    def test_demo_ui_can_proceed(self):
        """demo-ui should have can_proceed true (T3, plan is non-blocking)."""
        result = collect(self.demo_root, self.demo_project)

        demo_ui = next((t for t in result if t["task"] == "demo-ui"), None)
        self.assertIsNotNone(demo_ui, "demo-ui task not found")

        self.assertTrue(demo_ui["can_proceed"], "demo-ui should have can_proceed true")
        self.assertEqual(demo_ui["tier"], "T3", "demo-ui should have tier T3")

    def test_demo_hw_cannot_proceed(self):
        """demo-hw should have can_proceed false (T4, blocking plan)."""
        result = collect(self.demo_root, self.demo_project)

        demo_hw = next((t for t in result if t["task"] == "demo-hw"), None)
        self.assertIsNotNone(demo_hw, "demo-hw task not found")

        self.assertFalse(demo_hw["can_proceed"], "demo-hw should have can_proceed false")
        self.assertEqual(demo_hw["tier"], "T4", "demo-hw should have tier T4")

    def test_demo_led_awaiting_user_tier_selection(self):
        """demo-led should be awaiting user with 'select tier'."""
        result = collect(self.demo_root, self.demo_project)

        demo_led = next((t for t in result if t["task"] == "demo-led"), None)
        self.assertIsNotNone(demo_led, "demo-led task not found")

        # Find the brief artifact
        brief = next(
            (a for a in demo_led["artifacts"] if a["checkpoint"] == "C1"),
            None
        )
        self.assertIsNotNone(brief, "demo-led brief not found")

        self.assertEqual(demo_led["tier"], "", "demo-led should have empty tier")
        self.assertEqual(demo_led["tier_suggested"], "T2", "demo-led should have T2 suggested")
        self.assertEqual(brief["awaiting"], "user", "demo-led brief should be awaiting user")
        self.assertEqual(brief["reason"], "select tier", "demo-led reason should be 'select tier'")

    def test_demo_fw_has_orchestrator_approvable_plan(self):
        """demo-fw should have a plan (C5) awaiting orchestrator at T2."""
        result = collect(self.demo_root, self.demo_project)

        demo_fw = next((t for t in result if t["task"] == "demo-fw"), None)
        self.assertIsNotNone(demo_fw, "demo-fw task not found")

        self.assertEqual(demo_fw["tier"], "T2", "demo-fw should have tier T2")

        # Find the plan artifact
        plan = next(
            (a for a in demo_fw["artifacts"] if a["checkpoint"] == "C5"),
            None
        )
        self.assertIsNotNone(plan, "demo-fw plan not found")

        # At T2, C5 can be approved by orchestrator
        self.assertEqual(plan["awaiting"], "orchestrator", "demo-fw plan should be awaiting orchestrator")

    def test_artifacts_have_required_fields(self):
        """Each artifact should have all required fields."""
        result = collect(self.demo_root, self.demo_project)

        required_fields = [
            "path", "stage", "checkpoint", "status", "author", "approver",
            "open_questions", "awaiting", "blocking", "reason", "mtime"
        ]

        for task in result:
            for artifact in task["artifacts"]:
                for field in required_fields:
                    self.assertIn(field, artifact, f"Missing field '{field}' in artifact")

    def test_blocking_logic_for_t3_plan(self):
        """At T3, C5 (plan) should not be blocking."""
        result = collect(self.demo_root, self.demo_project)

        demo_ui = next((t for t in result if t["task"] == "demo-ui"), None)
        self.assertIsNotNone(demo_ui, "demo-ui task not found")

        plan = next(
            (a for a in demo_ui["artifacts"] if a["checkpoint"] == "C5"),
            None
        )
        self.assertIsNotNone(plan, "demo-ui plan not found")

        # T3, C5 is non-blocking, so blocking should be False
        self.assertFalse(plan["blocking"], "demo-ui plan should not be blocking at T3")
        self.assertIn("non-blocking", plan["reason"].lower(), "reason should mention non-blocking")

    def test_blocking_logic_for_t4_plan(self):
        """At T4, C5 (plan) should be blocking."""
        result = collect(self.demo_root, self.demo_project)

        demo_hw = next((t for t in result if t["task"] == "demo-hw"), None)
        self.assertIsNotNone(demo_hw, "demo-hw task not found")

        plan = next(
            (a for a in demo_hw["artifacts"] if a["checkpoint"] == "C5"),
            None
        )
        self.assertIsNotNone(plan, "demo-hw plan not found")

        # T4, C5 is blocking
        self.assertTrue(plan["blocking"], "demo-hw plan should be blocking at T4")


class TestStageStatusCLI(unittest.TestCase):
    """Tests for the CLI interface."""

    def setUp(self):
        """Set up demo fixtures for testing."""
        self.demo_root = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        self.demo_project = self.demo_root / "icm-project"

    def test_main_with_json_output(self):
        """Main should support --json output."""
        argv = [
            "--root", str(self.demo_root),
            "--project", str(self.demo_project),
            "--json"
        ]

        # Capture stdout
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            result = main(argv)

        self.assertEqual(result, 0, "main should return 0 on success")

        output = f.getvalue()
        data = json.loads(output)

        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)

    def test_main_with_markdown_output(self):
        """Main should support Markdown (default) output."""
        argv = [
            "--root", str(self.demo_root),
            "--project", str(self.demo_project),
        ]

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            result = main(argv)

        self.assertEqual(result, 0, "main should return 0 on success")

        output = f.getvalue()
        self.assertIn("Task", output)
        self.assertIn("Tier", output)
        self.assertIn("demo-ui", output)

    def test_main_with_awaiting_filter(self):
        """Main should support --awaiting filter."""
        argv = [
            "--root", str(self.demo_root),
            "--project", str(self.demo_project),
            "--json",
            "--awaiting", "user"
        ]

        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            result = main(argv)

        self.assertEqual(result, 0, "main should return 0 on success")

        output = f.getvalue()
        data = json.loads(output)

        # All artifacts in the result should have awaiting == "user"
        for task in data:
            for artifact in task["artifacts"]:
                self.assertEqual(artifact["awaiting"], "user",
                    "Filtered result should only have awaiting='user' artifacts")


if __name__ == "__main__":
    unittest.main()
