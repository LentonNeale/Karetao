"""
Tests for scripts/review.py
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import review
import icmlib


class TestReviewCLI(unittest.TestCase):
    """Test review.py CLI and approval logic."""

    def setUp(self):
        """Set up a fresh test demo directory for each test."""
        # Copy demo fixtures to a temporary directory for each test
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        self.temp_dir = tempfile.mkdtemp(prefix="test_review_")
        self.demo_root = Path(self.temp_dir) / "demo"
        shutil.copytree(demo_src, self.demo_root)
        self.project = self.demo_root / "icm-project"

    def tearDown(self):
        """Clean up temporary directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_approve_success(self):
        """Test successful approval."""
        artifact = self.demo_root / "stages" / "01-intake" / "output" / "14-demo-fw-brief.md"

        # Set tier first
        review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "set-tier",
            str(artifact),
            "T2"
        ])

        # Now approve
        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "approve",
            str(artifact)
        ])
        self.assertEqual(result, 0)

        # Check header was updated
        header = icmlib.read_header(artifact)
        self.assertEqual(header["status"], "approved")
        self.assertEqual(header["approver"], "user:user1")
        self.assertIn("approved_at", header)

    def test_approve_with_open_question_fails(self):
        """Test that approving with an open question fails."""
        artifact = self.demo_root / "stages" / "02-issue-spec" / "output" / "12-demo-led-spec.md"

        # Add a question
        review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "ask",
            str(artifact),
            "--text", "What is the LED color?"
        ])

        # Set tier
        brief = self.demo_root / "stages" / "01-intake" / "output" / "10-demo-led-brief.md"
        review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "set-tier",
            str(brief),
            "T2"
        ])

        # Try to approve - should fail
        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "approve",
            str(artifact)
        ])
        self.assertEqual(result, 1)

    def test_approve_with_tier_unset_fails(self):
        """Test that approving with tier unset fails."""
        artifact = self.demo_root / "stages" / "01-intake" / "output" / "10-demo-led-brief.md"

        # Ensure tier is unset (already is by default)
        header = icmlib.read_header(artifact)
        self.assertEqual(header.get("tier", ""), "")

        # Try to approve - should fail because tier is not selected
        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "approve",
            str(artifact)
        ])
        self.assertEqual(result, 1)

    def test_helper_cannot_approve(self):
        """Test that helpers cannot approve."""
        artifact = self.demo_root / "stages" / "01-intake" / "output" / "14-demo-fw-brief.md"

        # Set tier
        review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "set-tier",
            str(artifact),
            "T2"
        ])

        # Try to approve as helper - should fail
        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "helper:helper1",
            "approve",
            str(artifact)
        ])
        self.assertEqual(result, 1)

    def test_request_changes(self):
        """Test request-changes command."""
        artifact = self.demo_root / "stages" / "02-issue-spec" / "output" / "12-demo-led-spec.md"

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "request-changes",
            str(artifact),
            "--text", "Need more details"
        ])
        self.assertEqual(result, 0)

        header = icmlib.read_header(artifact)
        self.assertEqual(header["status"], "changes-requested")

    def test_comment(self):
        """Test comment command."""
        artifact = self.demo_root / "stages" / "02-issue-spec" / "output" / "12-demo-led-spec.md"

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "comment",
            str(artifact),
            "--text", "This looks good"
        ])
        self.assertEqual(result, 0)

        reviews = icmlib.read_reviews(artifact)
        comment_entries = [r for r in reviews if r["kind"] == "comment"]
        self.assertEqual(len(comment_entries), 1)
        self.assertEqual(comment_entries[0]["text"], "This looks good")

    def test_ask_and_answer(self):
        """Test ask and answer flow."""
        artifact = self.demo_root / "stages" / "02-issue-spec" / "output" / "12-demo-led-spec.md"

        # Ask a question
        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "ask",
            str(artifact),
            "--text", "What color LED?"
        ])
        self.assertEqual(result, 0)

        header = icmlib.read_header(artifact)
        self.assertEqual(header["status"], "needs-clarification")

        # Answer the question
        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "agent:orchestrator/opus",
            "answer",
            str(artifact),
            "--text", "Red LED"
        ])
        self.assertEqual(result, 0)

        # Status should return to draft
        header = icmlib.read_header(artifact)
        self.assertEqual(header["status"], "draft")

    def test_ask_on_plan_fails(self):
        """Test that asking on a plan fails."""
        artifact = self.demo_root / "stages" / "04-implement" / "output" / "14-demo-fw-plan.md"

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "ask",
            str(artifact),
            "--text", "A question"
        ])
        self.assertEqual(result, 1)

    def test_set_tier_by_user(self):
        """Test that users can set tier."""
        brief = self.demo_root / "stages" / "01-intake" / "output" / "10-demo-led-brief.md"

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "set-tier",
            str(brief),
            "T3"
        ])
        self.assertEqual(result, 0)

        header = icmlib.read_header(brief)
        self.assertEqual(header["tier"], "T3")

    def test_set_tier_by_agent_fails(self):
        """Test that agents cannot set tier."""
        brief = self.demo_root / "stages" / "01-intake" / "output" / "10-demo-led-brief.md"

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "agent:orchestrator/opus",
            "set-tier",
            str(brief),
            "T3"
        ])
        self.assertEqual(result, 1)

    def test_suggest_tier(self):
        """Test suggest-tier command."""
        brief = self.demo_root / "stages" / "01-intake" / "output" / "10-demo-led-brief.md"

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "agent:orchestrator/opus",
            "suggest-tier",
            str(brief),
            "T2",
            "--text", "Suitable for team review"
        ])
        self.assertEqual(result, 0)

        header = icmlib.read_header(brief)
        self.assertEqual(header["tier_suggested"], "T2")

    def test_path_outside_outputs_fails(self):
        """Test that accessing paths outside output folders fails."""
        # Try to access a path outside the output folders
        bad_path = self.demo_root / "stages" / "etc" / "passwd"

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "comment",
            str(bad_path),
            "--text", "test"
        ])
        self.assertEqual(result, 1)

    def test_reopen_by_user(self):
        """Test that users can reopen artifacts approved by agents."""
        artifact = self.demo_root / "stages" / "01-intake" / "output" / "11-demo-docs-brief.md"

        # This artifact should have an agent as approver
        header = icmlib.read_header(artifact)
        self.assertEqual(header.get("status"), "approved")
        self.assertTrue(header.get("approver", "").startswith("agent:"))

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "reopen",
            str(artifact)
        ])
        self.assertEqual(result, 0)

        header = icmlib.read_header(artifact)
        self.assertEqual(header["status"], "draft")
        self.assertEqual(header.get("approver"), "")

    def test_reopen_user_approval_fails(self):
        """Test that reopening user-approved artifacts fails."""
        artifact = self.demo_root / "stages" / "01-intake" / "output" / "14-demo-fw-brief.md"

        # Set tier and approve as user
        review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "set-tier",
            str(artifact),
            "T2"
        ])

        review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "approve",
            str(artifact)
        ])

        # Try to reopen - should fail
        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user2",
            "reopen",
            str(artifact)
        ])
        self.assertEqual(result, 1)

    def test_artifact_not_found(self):
        """Test that nonexistent artifacts are handled."""
        artifact = self.demo_root / "stages" / "01-intake" / "output" / "99-nonexistent.md"

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "comment",
            str(artifact),
            "--text", "test"
        ])
        self.assertEqual(result, 1)

    def test_multiple_questions(self):
        """Test that multiple questions must all be answered."""
        artifact = self.demo_root / "stages" / "02-issue-spec" / "output" / "13-demo-docs-spec.md"

        # Ask two questions
        review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "ask",
            str(artifact),
            "--text", "Question 1?"
        ])

        review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "user:user1",
            "ask",
            str(artifact),
            "--text", "Question 2?"
        ])

        # Answer one
        review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "agent:orchestrator/opus",
            "answer",
            str(artifact),
            "--text", "Answer 1"
        ])

        # Status should still be needs-clarification
        header = icmlib.read_header(artifact)
        self.assertEqual(header["status"], "needs-clarification")

        # Answer the second
        review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "agent:orchestrator/opus",
            "answer",
            str(artifact),
            "--text", "Answer 2"
        ])

        # Now status should be draft
        header = icmlib.read_header(artifact)
        self.assertEqual(header["status"], "draft")

    def test_orchestrator_approve_haiku_plan_at_t2(self):
        """Test that orchestrator can approve a haiku plan at T2."""
        artifact = self.demo_root / "stages" / "04-implement" / "output" / "14-demo-fw-plan.md"
        brief = self.demo_root / "stages" / "01-intake" / "output" / "14-demo-fw-brief.md"

        # The brief should already be approved with T2
        header = icmlib.read_header(brief)
        self.assertEqual(header.get("tier"), "T2")

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "agent:orchestrator/opus",
            "approve",
            str(artifact)
        ])
        self.assertEqual(result, 0)

    def test_orchestrator_cannot_approve_spec_self(self):
        """Test that orchestrator cannot approve its own spec."""
        artifact = self.demo_root / "stages" / "02-issue-spec" / "output" / "13-demo-docs-spec.md"
        brief = self.demo_root / "stages" / "01-intake" / "output" / "11-demo-docs-brief.md"

        # Ensure brief is T1
        header = icmlib.read_header(brief)
        self.assertEqual(header.get("status"), "approved")
        self.assertEqual(header.get("tier"), "T1")

        # Try to approve the spec - should fail (self-approval)
        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "agent:orchestrator/opus",
            "approve",
            str(artifact)
        ])
        self.assertEqual(result, 1)

    def test_orchestrator_cannot_approve_at_t3(self):
        """Test that orchestrator cannot approve at T3."""
        artifact = self.demo_root / "stages" / "04-implement" / "output" / "15-demo-ui-plan.md"
        brief = self.demo_root / "stages" / "01-intake" / "output" / "15-demo-ui-brief.md"

        # Ensure brief is T3
        header = icmlib.read_header(brief)
        self.assertEqual(header.get("tier"), "T3")

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "agent:orchestrator/opus",
            "approve",
            str(artifact)
        ])
        self.assertEqual(result, 1)

    def test_agent_can_comment(self):
        """Test that agents can comment."""
        artifact = self.demo_root / "stages" / "02-issue-spec" / "output" / "12-demo-led-spec.md"

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "agent:orchestrator/opus",
            "comment",
            str(artifact),
            "--text", "Agent comment"
        ])
        self.assertEqual(result, 0)

        reviews = icmlib.read_reviews(artifact)
        agent_comments = [r for r in reviews if r["kind"] == "comment" and "agent:" in r["who"]]
        self.assertGreaterEqual(len(agent_comments), 1)

    def test_helper_cannot_comment(self):
        """Test that helpers cannot comment."""
        artifact = self.demo_root / "stages" / "02-issue-spec" / "output" / "12-demo-led-spec.md"

        result = review.main([
            "--root", str(self.demo_root),
            "--project", str(self.project),
            "--as", "helper:helper1",
            "comment",
            str(artifact),
            "--text", "Helper comment"
        ])
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
