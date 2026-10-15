"""Tests for tools/stack_depth.py against small hand-written .ci call graphs."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

_TOOL = Path(__file__).resolve().parents[2] / "tools" / "stack_depth.py"
_spec = importlib.util.spec_from_file_location("stack_depth", _TOOL)
stack_depth = importlib.util.module_from_spec(_spec)
sys.modules["stack_depth"] = stack_depth  # dataclasses look the module up while it loads
_spec.loader.exec_module(stack_depth)

ALLOWANCE = stack_depth.SWITCH_ALLOWANCE_BYTES


def node(title, size=None, kind="static"):
    label = f"{title.rsplit(':', 1)[-1]}\\n/src/x.c:1:1"
    if size is not None:
        label += f"\\n{size} bytes ({kind})"
    return f'node: {{ title: "{title}" label: "{label}" }}'


def edge(source, target, line=10):
    return f'edge: {{ sourcename: "{source}" targetname: "{target}" label: "/src/app/x.c:{line}:5" }}'


class StackDepthTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.ci = self.dir / "build"
        self.ci.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, lines, stack_words=128, entry="Entry", config="", ci_name="a.c.ci"):
        (self.ci / ci_name).write_text('graph: { title: "a.c"\n' + "\n".join(lines) + "\n}\n")
        ioc = self.dir / "a.ioc"
        ioc.write_text(f"FREERTOS.Tasks01=main,24,{stack_words},{entry},Default,NULL,Dynamic,NULL,NULL\n")
        cfg = self.dir / "a.cfg"
        cfg.write_text(config)
        return ioc, cfg

    def run_tool(self, *args, freertos_config=None, **kwargs):
        ioc, cfg = self.write(*args, **kwargs)
        results = stack_depth.analyse(ioc, freertos_config, stack_depth.ci_files(None, self.ci), cfg)
        return results[0] if freertos_config is None else results

    def test_allowance_covers_the_fp_frame_alignment_word_and_the_context_save(self):
        self.assertEqual(ALLOWANCE, (26 + 1 + 9 + 16) * 4)

    def test_deepest_branch_is_summed_and_the_allowance_added(self):
        r = self.run_tool([node("Entry", 16), node("Shallow", 8), node("Deep", 40), node("Leaf", 24),
                           edge("Entry", "Shallow"), edge("Entry", "Deep"), edge("Deep", "Leaf")])
        self.assertEqual(r.depth, 16 + 40 + 24)
        self.assertEqual(r.total, 80 + ALLOWANCE)
        self.assertEqual([s.split(" ")[0] for s in r.path], ["Entry", "Deep", "Leaf"])
        self.assertTrue(r.ok)

    def test_stack_too_small_fails(self):
        words = (16 + ALLOWANCE) // 4  # one word short of the 20-byte frame plus the allowance
        r = self.run_tool([node("Entry", 20)], stack_words=words)
        self.assertEqual(r.problems, [])
        self.assertFalse(r.ok)

    def test_recursion_is_a_problem(self):
        r = self.run_tool([node("Entry", 8), node("A", 8), edge("Entry", "A"), edge("A", "A")])
        self.assertTrue(any("recursion" in p for p in r.problems))
        self.assertFalse(r.ok)

    def test_unresolved_function_pointer_is_a_problem(self):
        r = self.run_tool([node("Entry", 8), edge("Entry", "__indirect_call", line=42)])
        self.assertTrue(any("x.c:42" in p for p in r.problems), r.problems)
        self.assertFalse(r.ok)

    def test_function_pointer_resolved_to_targets_or_none(self):
        lines = [node("Entry", 8), node("Callback", 100), edge("Entry", "__indirect_call", line=42)]
        resolved = self.run_tool(lines, config="indirect Entry 1 Callback\n")
        never_set = self.run_tool(lines, config="indirect Entry 1 none\n")
        self.assertEqual((resolved.depth, never_set.depth), (108, 8))
        self.assertTrue(resolved.ok and never_set.ok)

    def test_site_count_must_match(self):
        """A new function-pointer call in a listed caller must not inherit the old entry."""
        lines = [node("Entry", 8), edge("Entry", "__indirect_call", line=42),
                 edge("Entry", "__indirect_call", line=50)]
        r = self.run_tool(lines, config="indirect Entry 1 none\n")
        self.assertTrue(any("call graph has 2" in p for p in r.problems), r.problems)
        self.assertFalse(r.ok)

    def test_a_group_covers_a_call_inlined_into_another_caller(self):
        """Release: Dispatch is inlined into Process, so the site moves caller."""
        config = "indirect Dispatch,Process 1 none\n"
        debug = self.run_tool([node("Entry", 8), node("Process", 8), node("Dispatch", 8),
                               edge("Entry", "Process"), edge("Process", "Dispatch"),
                               edge("Dispatch", "__indirect_call")], config=config)
        release = self.run_tool([node("Entry", 8), node("Process", 16),
                                 edge("Entry", "Process"), edge("Process", "__indirect_call")], config=config)
        self.assertTrue(debug.ok, debug.problems)
        self.assertTrue(release.ok, release.problems)

    def test_library_function_needs_a_size(self):
        lines = [node("Entry", 8), node("memset"), edge("Entry", "memset")]
        missing = self.run_tool(lines)
        sized = self.run_tool(lines, config="external memset 12\n")
        self.assertTrue(any("memset" in p for p in missing.problems))
        self.assertEqual(sized.depth, 20)
        self.assertTrue(sized.ok)

    def test_weak_definition_titled_by_file_is_found(self):
        r = self.run_tool([node("Entry", 8), node("HAL_GetTick"), node("/src/hal.c:HAL_GetTick", 4),
                           edge("Entry", "HAL_GetTick")])
        self.assertEqual(r.depth, 12)
        self.assertEqual(r.problems, [])

    def test_deeper_strong_override_of_a_weak_callback_is_counted(self):
        """HAL calls its own weak copy by file title; the linked App override is deeper."""
        r = self.run_tool([node("Entry", 8), node("/src/hal.c:HAL_Callback", 16), node("HAL_Callback", 24),
                           node("AppWork", 100), edge("Entry", "/src/hal.c:HAL_Callback"),
                           edge("HAL_Callback", "AppWork")])
        self.assertEqual(r.depth, 8 + 24 + 100)
        self.assertEqual(r.problems, [])

    def test_unbounded_dynamic_frame_is_a_problem(self):
        r = self.run_tool([node("Entry", 8, kind="dynamic")])
        self.assertTrue(any("dynamically sized" in p for p in r.problems))
        bounded = self.run_tool([node("Entry", 8, kind="dynamic,bounded")])
        self.assertEqual(bounded.problems, [])

    def test_missing_entry_function_is_a_problem(self):
        r = self.run_tool([node("Other", 8)], entry="Entry")
        self.assertFalse(r.ok)

    def test_kernel_idle_and_timer_tasks_are_checked(self):
        config_h = self.dir / "FreeRTOSConfig.h"
        config_h.write_text("#define configMINIMAL_STACK_SIZE ((uint16_t)128)\n"
                            "#define configUSE_TIMERS 1\n#define configTIMER_TASK_STACK_DEPTH 256\n")
        results = self.run_tool([node("Entry", 8), node("/src/tasks.c:prvIdleTask", 40),
                                 node("/src/timers.c:prvTimerTask", 80)], freertos_config=config_h)
        sizes = {r.task.name: (r.task.stack_bytes, r.depth) for r in results}
        self.assertEqual(sizes["IDLE"], (512, 40))
        self.assertEqual(sizes["Tmr Svc"], (1024, 80))
        config_h.write_text("#define configMINIMAL_STACK_SIZE 128\n#define configUSE_TIMERS 0\n"
                            "#define configTIMER_TASK_STACK_DEPTH 256\n")
        results = self.run_tool([node("Entry", 8), node("/src/tasks.c:prvIdleTask", 40)],
                                freertos_config=config_h)
        self.assertNotIn("Tmr Svc", {r.task.name for r in results})

    def test_objects_list_reads_only_linked_objects(self):
        """A .ci left behind by a removed source must not enter the graph."""
        self.write([node("Entry", 8)])
        (self.ci / "removed.c.ci").write_text(
            'graph: { title: "removed.c"\n' + node("Entry", 999) + "\n}\n")
        (self.ci / "a.c.obj").write_text("")
        objects = self.dir / "objects.txt"
        objects.write_text(f"{self.ci / 'a.c.obj'}\n{self.dir / 'startup.s.obj'}\n")
        files = stack_depth.ci_files(objects, None)
        self.assertEqual(files, [self.ci / "a.c.ci"])  # the assembly object has no call graph
        objects.write_text(f"{self.ci / 'missing.c.obj'}\n")
        with self.assertRaises(ValueError):
            stack_depth.ci_files(objects, None)

    def test_report_file_is_written_only_on_a_pass(self):
        ioc, cfg = self.write([node("Entry", 8)])
        stamp = self.dir / "stamp.txt"
        args = ["--ioc", str(ioc), "--ci-dir", str(self.ci), "--config", str(cfg), "--report", str(stamp)]
        self.assertEqual(stack_depth.main(args), 0)
        self.assertTrue(stamp.exists())
        ioc.write_text("FREERTOS.Tasks01=main,24,1,Entry,Default,NULL,Dynamic,NULL,NULL\n")
        self.assertEqual(stack_depth.main(args), 1)
        self.assertFalse(stamp.exists())

    def test_a_caller_in_two_entries_is_an_error(self):
        """Otherwise one entry's targets would silently replace the other's."""
        ioc, cfg = self.write([node("Entry", 8)],
                              config="indirect Entry 1 Deep\nindirect Other,Entry 1 none\n")
        with self.assertRaises(ValueError) as caught:
            stack_depth.load_config(cfg)
        self.assertIn("line 1", str(caught.exception))
        self.assertEqual(stack_depth.main(["--ioc", str(ioc), "--ci-dir", str(self.ci), "--config", str(cfg)]), 2)

    def test_unreadable_config_line_is_an_error(self):
        ioc, cfg = self.write([node("Entry", 8)], config="indirect Entry none\n")  # no site count
        self.assertEqual(stack_depth.main(["--ioc", str(ioc), "--ci-dir", str(self.ci), "--config", str(cfg)]), 2)


if __name__ == "__main__":
    unittest.main()
