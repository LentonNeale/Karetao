"""Unit tests for the efficiency test's extractor and checker (python3 -m unittest discover -s workspace/tests/efficiency)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_proposals as cp  # noqa: E402
import extract_usage as eu  # noqa: E402


class BashShapeTests(unittest.TestCase):
    def test_subcommands_and_pipes(self):
        self.assertEqual(eu.bash_shapes("git status --short | head"), ["git status"])
        self.assertEqual(eu.bash_shapes("cd x && gh issue view 12 && python3 -m unittest -v"),
                         ["gh issue view", "python3 -m unittest"])

    def test_loops_vars_and_scripts(self):
        self.assertEqual(eu.bash_shapes("for f in a b; do grep -n x $f; done"), ["grep"])
        self.assertEqual(eu.bash_shapes("FOO=1 workspace/scripts/set-field.sh 42 Status Ready"), ["set-field.sh"])
        self.assertEqual(eu.bash_shapes("python3 - <<'EOF'\nprint(1)\nEOF"), ["python3 <stdin-script>"])

    def test_no_arguments_leak(self):
        shapes = eu.bash_shapes("gh issue create --title 'secret plan' --body x")
        self.assertEqual(shapes, ["gh issue create"])


class DigestTests(unittest.TestCase):
    def test_digest_has_no_text_and_counts_tools(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            lines = [
                {"type": "user", "entrypoint": "cli", "timestamp": "2026-01-01T00:00:00Z", "message": {"content": "my private request"}},
                {"type": "assistant", "message": {"model": "m", "usage": {"input_tokens": 1, "output_tokens": 2},
                 "content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "git log --oneline"}}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "abc123 private commit"}]}},
            ]
            (folder / "s1.jsonl").write_text("\n".join(json.dumps(x) for x in lines))
            out = folder / "digest.json"
            eu.main(["--project-root", d, "--transcripts", d, "--out", str(out)])
            text = out.read_text()
            self.assertNotIn("private", text)
            digest = json.loads(text)
            self.assertEqual(digest["bash_shapes"][0]["shape"], "git log")
            self.assertEqual(digest["user_prompts"]["count"], 1)


def proposal(**over):
    p = {"id": "P1", "name": "file-index", "kind": "tool", "summary": "Builds an index.", "replaces": "grep chains (B1)",
         "evidence": ["B1"], "trigger": "when locating a symbol", "input": "--symbol <name> (str); reads the git file list",
         "output": "JSON list of {path, line} on stdout; exit 1 if none found", "language": "python",
         "location": "workspace/scripts/file_index.py", "tokens_saved_per_use": 500, "uses_per_week": 20,
         "estimate_basis": "B1: 322 calls x ~330 tok", "test_plan": "unit tests incl. unknown symbol", "risks": "stale index"}
    p.update(over)
    return p


class CheckerTests(unittest.TestCase):
    ids = {"B1", "R1"}

    def run_check(self, props):
        return cp.check({"proposals": props, "rejected": []}, self.ids, Path("/nonexistent"))

    def test_valid_set_passes(self):
        props = [proposal(id=f"P{i}", name=f"n{i}") for i in range(5)]
        valid, errors, _ = self.run_check(props)
        self.assertEqual(errors, [])
        self.assertEqual(len(valid), 5)

    def test_rejects_non_python_vague_and_unknown_evidence(self):
        props = [proposal(id=f"P{i}", name=f"n{i}") for i in range(4)]
        props.append(proposal(id="P9", name="bad", language="bash", input="analyse the logs", evidence=["Z9"]))
        _, errors, _ = self.run_check(props)
        joined = " ".join(errors)
        self.assertIn("language must be 'python'", joined)
        self.assertIn("input is too short or vague", joined)
        self.assertIn("unknown: ['Z9']", joined)

    def test_hook_needs_event_and_location(self):
        props = [proposal(id=f"P{i}", name=f"n{i}") for i in range(4)]
        props.append(proposal(id="P9", name="h", kind="hook", trigger="whenever", location="workspace/scripts/h.py"))
        _, errors, _ = self.run_check(props)
        self.assertTrue(any("hook trigger must start" in e for e in errors))
        self.assertTrue(any("location for a hook" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
