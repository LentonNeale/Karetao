"""
Unit tests for scripts/icmlib.py
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# Add scripts to path so icmlib can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import icmlib


class TestDefaultPaths(unittest.TestCase):
    """Test default_root and default_project functions."""

    def test_default_root(self):
        """default_root returns the workspace directory."""
        root = icmlib.default_root()
        self.assertTrue((root / "stages").exists())
        self.assertTrue((root / "scripts").exists())

    def test_default_project(self):
        """default_project returns icm-project directory."""
        root = icmlib.default_root()
        project = icmlib.default_project(root)
        self.assertEqual(project.name, "icm-project")
        self.assertEqual(project.parent, root.parent)


class TestCheckInsideOutputs(unittest.TestCase):
    """Test check_inside_outputs validation."""

    def setUp(self):
        """Create a temporary workspace structure."""
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        (self.root / "stages" / "01-test" / "output").mkdir(parents=True)
        (self.root / "stages" / "02-test" / "output").mkdir(parents=True)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_valid_path_inside_output(self):
        """Valid paths inside output folders are accepted."""
        valid_path = self.root / "stages" / "01-test" / "output" / "test.md"
        result = icmlib.check_inside_outputs(self.root, valid_path)
        self.assertEqual(result, valid_path.resolve())

    def test_invalid_path_outside_stages(self):
        """Paths outside stages/ raise ValueError."""
        invalid_path = self.root / "outside.md"
        with self.assertRaises(ValueError):
            icmlib.check_inside_outputs(self.root, invalid_path)

    def test_invalid_path_in_reference(self):
        """Paths in references/ (not output/) raise ValueError."""
        ref_path = self.root / "stages" / "01-test" / "references" / "test.md"
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        with self.assertRaises(ValueError):
            icmlib.check_inside_outputs(self.root, ref_path)


class TestListArtifacts(unittest.TestCase):
    """Test list_artifacts function."""

    def setUp(self):
        """Create a temporary workspace with artifacts."""
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

        # Create output directories with artifacts
        (self.root / "stages" / "01-intake" / "output").mkdir(parents=True)
        (self.root / "stages" / "02-spec" / "output").mkdir(parents=True)

        # Add artifacts
        (self.root / "stages" / "01-intake" / "output" / "test-brief.md").touch()
        (self.root / "stages" / "01-intake" / "output" / "test-brief-review.md").touch()
        (self.root / "stages" / "02-spec" / "output" / "test-spec.md").touch()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_list_artifacts_excludes_review_files(self):
        """list_artifacts excludes -review.md files."""
        artifacts = icmlib.list_artifacts(self.root)
        artifact_names = [a.name for a in artifacts]
        self.assertIn("test-brief.md", artifact_names)
        self.assertIn("test-spec.md", artifact_names)
        self.assertNotIn("test-brief-review.md", artifact_names)

    def test_list_artifacts_sorted(self):
        """list_artifacts returns results sorted."""
        artifacts = icmlib.list_artifacts(self.root)
        # Should be sorted by path
        self.assertEqual(artifacts, sorted(artifacts))


class TestHeaderFunctions(unittest.TestCase):
    """Test read_header and write_header functions."""

    def setUp(self):
        """Create a temporary artifact file."""
        self.tmpdir = tempfile.mkdtemp()
        self.artifact_path = Path(self.tmpdir) / "test.md"

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_read_header_from_artifact(self):
        """read_header parses the YAML header correctly."""
        content = """```
issue: #42
task: demo
status: draft
```

# Title

Some content."""
        self.artifact_path.write_text(content)

        header = icmlib.read_header(self.artifact_path)
        self.assertEqual(header["issue"], "#42")
        self.assertEqual(header["task"], "demo")
        self.assertEqual(header["status"], "draft")

    def test_read_header_empty_when_no_header(self):
        """read_header returns empty dict when no header."""
        content = "# Title\n\nSome content."
        self.artifact_path.write_text(content)

        header = icmlib.read_header(self.artifact_path)
        self.assertEqual(header, {})

    def test_write_header_updates_existing(self):
        """write_header updates existing header fields."""
        content = """```
issue: #42
task: demo
```

# Title"""
        self.artifact_path.write_text(content)

        icmlib.write_header(self.artifact_path, {"status": "approved"})

        header = icmlib.read_header(self.artifact_path)
        self.assertEqual(header["issue"], "#42")
        self.assertEqual(header["status"], "approved")
        self.assertIn("# Title", self.artifact_path.read_text())

    def test_write_header_preserves_body(self):
        """write_header preserves the artifact body."""
        body = "# Title\n\nSome important content."
        content = f"```\nissue: #42\n```\n\n{body}"
        self.artifact_path.write_text(content)

        icmlib.write_header(self.artifact_path, {"status": "ready"})

        result = self.artifact_path.read_text()
        self.assertIn("Some important content", result)


class TestReviewFunctions(unittest.TestCase):
    """Test review file functions."""

    def setUp(self):
        """Create a temporary artifact file."""
        self.tmpdir = tempfile.mkdtemp()
        self.artifact_path = Path(self.tmpdir) / "test.md"
        self.review_path = self.artifact_path.with_stem(self.artifact_path.stem) / ".." / (self.artifact_path.stem + "-review.md")

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_review_path_construction(self):
        """review_path returns correct review file path."""
        result = icmlib.review_path(self.artifact_path)
        self.assertTrue(result.name.endswith("-review.md"))

    def test_append_and_read_reviews(self):
        """append_review and read_reviews work together."""
        icmlib.append_review(self.artifact_path, "comment", "user:alice", "Good work!")

        reviews = icmlib.read_reviews(self.artifact_path)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["kind"], "comment")
        self.assertEqual(reviews[0]["who"], "user:alice")
        self.assertEqual(reviews[0]["text"], "Good work!")

    def test_read_reviews_empty_when_no_review_file(self):
        """read_reviews returns empty list when review file doesn't exist."""
        reviews = icmlib.read_reviews(self.artifact_path)
        self.assertEqual(reviews, [])

    def test_multiple_review_entries(self):
        """read_reviews handles multiple entries."""
        icmlib.append_review(self.artifact_path, "question", "user:alice", "Is this right?")
        icmlib.append_review(self.artifact_path, "answer", "agent:bot/haiku", "Yes.")

        reviews = icmlib.read_reviews(self.artifact_path)
        self.assertEqual(len(reviews), 2)
        self.assertEqual(reviews[0]["kind"], "question")
        self.assertEqual(reviews[1]["kind"], "answer")


class TestOpenQuestions(unittest.TestCase):
    """Test open_questions function."""

    def setUp(self):
        """Create a temporary artifact file."""
        self.tmpdir = tempfile.mkdtemp()
        self.artifact_path = Path(self.tmpdir) / "test.md"

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_open_questions_count(self):
        """open_questions counts questions minus answers."""
        icmlib.append_review(self.artifact_path, "question", "user:alice", "Q1?")
        icmlib.append_review(self.artifact_path, "question", "user:alice", "Q2?")
        icmlib.append_review(self.artifact_path, "answer", "agent:bot/haiku", "A1.")

        count = icmlib.open_questions(self.artifact_path)
        self.assertEqual(count, 1)

    def test_open_questions_never_negative(self):
        """open_questions never goes below 0."""
        icmlib.append_review(self.artifact_path, "answer", "agent:bot/haiku", "A1.")

        count = icmlib.open_questions(self.artifact_path)
        self.assertEqual(count, 0)


class TestCheckpointOf(unittest.TestCase):
    """Test checkpoint_of function."""

    def test_checkpoint_from_brief(self):
        """checkpoint_of returns C1 for brief."""
        self.assertEqual(icmlib.checkpoint_of("test-brief.md"), "C1")

    def test_checkpoint_from_spec(self):
        """checkpoint_of returns C2 for spec."""
        self.assertEqual(icmlib.checkpoint_of("test-spec.md"), "C2")

    def test_checkpoint_from_design(self):
        """checkpoint_of returns C3 for design."""
        self.assertEqual(icmlib.checkpoint_of("test-design.md"), "C3")

    def test_checkpoint_from_docdiff(self):
        """checkpoint_of returns C4 for docdiff."""
        self.assertEqual(icmlib.checkpoint_of("test-docdiff.md"), "C4")

    def test_checkpoint_from_plan(self):
        """checkpoint_of returns C5 for plan."""
        self.assertEqual(icmlib.checkpoint_of("test-plan.md"), "C5")

    def test_checkpoint_from_evidence(self):
        """checkpoint_of returns C6 for evidence."""
        self.assertEqual(icmlib.checkpoint_of("test-evidence.md"), "C6")

    def test_checkpoint_from_closeout(self):
        """checkpoint_of returns C7 for closeout."""
        self.assertEqual(icmlib.checkpoint_of("test-closeout.md"), "C7")

    def test_checkpoint_none_for_other_files(self):
        """checkpoint_of returns None for files without checkpoint."""
        self.assertIsNone(icmlib.checkpoint_of("test.md"))
        self.assertIsNone(icmlib.checkpoint_of("readme.txt"))


class TestLoadPeople(unittest.TestCase):
    """Test load_people function."""

    def setUp(self):
        """Create a temporary people.md file."""
        self.tmpdir = tempfile.mkdtemp()
        self.project_path = Path(self.tmpdir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_load_people_from_markdown_table(self):
        """load_people parses Markdown table correctly."""
        people_content = """# People

| login | role |
|---|---|
| alice | user |
| bob | helper |
| carol | user |
"""
        (self.project_path / "people.md").write_text(people_content)

        people = icmlib.load_people(self.project_path)
        self.assertEqual(people["alice"], "user")
        self.assertEqual(people["bob"], "helper")
        self.assertEqual(people["carol"], "user")

    def test_load_people_empty_when_file_missing(self):
        """load_people returns empty dict when file doesn't exist."""
        people = icmlib.load_people(self.project_path)
        self.assertEqual(people, {})


class TestParseIdentity(unittest.TestCase):
    """Test parse_identity function."""

    def test_parse_user_identity(self):
        """parse_identity handles user:login format."""
        kind, name, model = icmlib.parse_identity("user:alice")
        self.assertEqual(kind, "user")
        self.assertEqual(name, "alice")
        self.assertEqual(model, "")

    def test_parse_helper_identity(self):
        """parse_identity handles helper:login format."""
        kind, name, model = icmlib.parse_identity("helper:bob")
        self.assertEqual(kind, "helper")
        self.assertEqual(name, "bob")
        self.assertEqual(model, "")

    def test_parse_agent_identity(self):
        """parse_identity handles agent:name/model format."""
        kind, name, model = icmlib.parse_identity("agent:orchestrator/opus")
        self.assertEqual(kind, "agent")
        self.assertEqual(name, "orchestrator")
        self.assertEqual(model, "opus")

    def test_parse_identity_invalid_format(self):
        """parse_identity raises ValueError for invalid formats."""
        with self.assertRaises(ValueError):
            icmlib.parse_identity("invalid")

        with self.assertRaises(ValueError):
            icmlib.parse_identity("user:alice/model")

        with self.assertRaises(ValueError):
            icmlib.parse_identity("agent:name")


class TestModelRank(unittest.TestCase):
    """Test model_rank function."""

    def test_model_rank_haiku(self):
        """model_rank returns 1 for haiku."""
        self.assertEqual(icmlib.model_rank("haiku"), 1)

    def test_model_rank_sonnet(self):
        """model_rank returns 2 for sonnet."""
        self.assertEqual(icmlib.model_rank("sonnet"), 2)

    def test_model_rank_opus(self):
        """model_rank returns 3 for opus."""
        self.assertEqual(icmlib.model_rank("opus"), 3)

    def test_model_rank_unknown(self):
        """model_rank returns 99 for unknown models."""
        self.assertEqual(icmlib.model_rank("unknown"), 99)


class TestFindBrief(unittest.TestCase):
    """Test find_brief function."""

    def setUp(self):
        """Create a temporary workspace with a brief."""
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        (self.root / "stages" / "01-intake" / "output").mkdir(parents=True)
        (self.root / "stages" / "01-intake" / "output" / "12-demo-brief.md").write_text("```\ntask: demo\n```\n")

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_find_brief_when_exists(self):
        """find_brief returns path when brief exists."""
        result = icmlib.find_brief(self.root, "demo")
        self.assertIsNotNone(result)
        self.assertTrue(result.exists())

    def test_find_brief_returns_none_when_not_found(self):
        """find_brief returns None when brief doesn't exist."""
        result = icmlib.find_brief(self.root, "nonexistent")
        self.assertIsNone(result)


class TestTaskTier(unittest.TestCase):
    """Test task_tier function."""

    def setUp(self):
        """Create a temporary workspace with a brief."""
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        (self.root / "stages" / "01-intake" / "output").mkdir(parents=True)

        brief_content = """```
task: demo
tier: T2
```

# Demo Brief"""
        (self.root / "stages" / "01-intake" / "output" / "demo-brief.md").write_text(brief_content)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_task_tier_when_set(self):
        """task_tier returns the tier when set."""
        tier = icmlib.task_tier(self.root, "demo")
        self.assertEqual(tier, "T2")

    def test_task_tier_empty_when_unset(self):
        """task_tier returns empty string when tier is not set."""
        # Add another brief without a tier
        brief_content = """```
task: other
```

# Other Brief"""
        (self.root / "stages" / "01-intake" / "output" / "other-brief.md").write_text(brief_content)

        tier = icmlib.task_tier(self.root, "other")
        self.assertEqual(tier, "")

    def test_task_tier_returns_empty_when_brief_not_found(self):
        """task_tier returns empty string when brief doesn't exist."""
        tier = icmlib.task_tier(self.root, "nonexistent")
        self.assertEqual(tier, "")


class TestNowIso(unittest.TestCase):
    """Test now_iso function."""

    def test_now_iso_format(self):
        """now_iso returns ISO-8601 UTC format."""
        result = icmlib.now_iso()
        # Should match format YYYY-MM-DDTHH:MM:SSZ
        self.assertRegex(result, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


if __name__ == "__main__":
    unittest.main()
