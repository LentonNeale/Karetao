#!/usr/bin/env python3
"""Worst-case stack depth of each FreeRTOS task, from GCC's call-graph files.

The firmware is compiled with -fcallgraph-info=su, so every object file has a
.ci file beside it listing each function's stack frame and the calls it makes.
This tool joins them into one call graph and, for each task, adds the frames
along the deepest path from the task's entry function, plus the allowance for
what an exception and a context switch push onto the task's stack. The tasks
are the CubeMX .ioc rows (FREERTOS.TasksNN = name,priority,stack words,entry,...)
and the kernel's own idle and timer tasks, sized in FreeRTOSConfig.h.

It fails when a total exceeds the task's stack, or when the depth cannot be
known: recursion, a dynamically sized frame, a function-pointer call that
stack_depth.cfg does not account for, or a library function without a size.

Usage:
  stack_depth.py --ioc Arm_Sensor_Hub.ioc --freertos-config Core/Inc/FreeRTOSConfig.h \
                 --objects build/Debug/stack_objects.txt --config tools/stack_depth.cfg
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Bytes a task's stack must hold beyond its deepest call path, on a Cortex-M4F
# with the FPU in use and the FreeRTOS GCC/ARM_CM4F port:
# - the extended exception frame the core pushes when an interrupt or PendSV
#   preempts the task: r0-r3, r12, lr, pc, xPSR, s0-s15, FPSCR and a reserved
#   word (26 words), plus the padding word it adds when the stack pointer is not
#   8-byte aligned at entry (CCR.STKALIGN, set by default): 27 words;
# - the registers PendSV saves on the task stack in a context switch: r4-r11
#   and r14 (9 words), s16-s31 (16 words).
# Interrupt handlers and nested interrupts run on the main stack, not here.
EXCEPTION_FRAME_BYTES = (26 + 1) * 4
CONTEXT_SAVE_BYTES = (9 + 16) * 4
SWITCH_ALLOWANCE_BYTES = EXCEPTION_FRAME_BYTES + CONTEXT_SAVE_BYTES

INDIRECT = "__indirect_call"

# The kernel's tasks (tasks.c, timers.c) and the FreeRTOSConfig.h depth that
# CMSIS-RTOS2 gives each one (vApplicationGetIdleTaskMemory, ...TimerTaskMemory).
KERNEL_TASKS = (("IDLE", "prvIdleTask", "configMINIMAL_STACK_SIZE", None),
                ("Tmr Svc", "prvTimerTask", "configTIMER_TASK_STACK_DEPTH", "configUSE_TIMERS"))

_ITEM = re.compile(r'(node|edge): \{(.*)\}\s*$')
_FIELD = re.compile(r'(\w+)\s*:\s*"((?:[^"\\]|\\.)*)"')
_SIZE = re.compile(r'\\n(\d+) bytes \(([a-z,]+)\)')


@dataclass
class Function:
    name: str
    frame: int | None = None  # None: no frame information (defined elsewhere)
    kind: str = ""  # "static", "dynamic" or "dynamic,bounded" as GCC reports it
    calls: list[tuple[str, str]] = field(default_factory=list)  # (callee title, call site)


@dataclass
class Task:
    name: str
    stack_bytes: int
    entry: str


@dataclass
class Indirect:
    callers: tuple[str, ...]
    sites: int  # function-pointer call sites the callers hold together
    targets: tuple[str, ...]  # "none": the pointer is never set in this firmware


@dataclass
class Result:
    task: Task
    depth: int  # deepest call path, bytes
    path: list[str]
    problems: list[str]

    @property
    def total(self) -> int:
        return self.depth + SWITCH_ALLOWANCE_BYTES

    @property
    def ok(self) -> bool:
        return not self.problems and self.total <= self.task.stack_bytes


def short(title: str) -> str:
    """`/path/file.c:Func` (a file-local or weak function) or `Func` -> `Func`."""
    return title.rsplit(":", 1)[-1]


def site(label: str) -> str:
    """`/abs/path/App/Src/file.c:208:9` -> `file.c:208`."""
    return re.sub(r":\d+$", "", label.rsplit("/", 1)[-1])


def ci_files(objects: Path | None, ci_dir: Path | None) -> list[Path]:
    """The .ci files of the objects actually linked (one path per line in
    `objects`; a missing .ci is an error), or every .ci under `ci_dir`."""
    if objects is not None:
        files = []
        for line in objects.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            # Assembly (the startup file) has no call graph; it runs on the main
            # stack before the scheduler starts, never on a task stack.
            if Path(line).stem.endswith((".s", ".S")):
                continue
            ci = Path(line).with_suffix(".ci")
            if not ci.is_file():
                raise ValueError(f"no call graph for {line} (expected {ci}); "
                                 "is it compiled with -fcallgraph-info=su?")
            files.append(ci)
        return files
    # CMake's compiler-identification objects are not firmware.
    return sorted(p for p in ci_dir.rglob("*.ci") if "CompilerId" not in p.parts[-2])


def load_graph(files: list[Path]) -> dict[str, Function]:
    graph: dict[str, Function] = {}
    for path in files:
        for line in path.read_text(errors="replace").splitlines():
            match = _ITEM.match(line.strip())
            if not match:
                continue
            kind, body = match.groups()
            fields = dict(_FIELD.findall(body))
            if kind == "node":
                title = fields["title"]
                function = graph.setdefault(title, Function(title))
                size = _SIZE.search(fields.get("label", ""))
                if size:
                    frame = int(size.group(1))
                    if function.frame is None or frame > function.frame:
                        function.frame, function.kind = frame, size.group(2)
            else:
                caller = graph.setdefault(fields["sourcename"], Function(fields["sourcename"]))
                caller.calls.append((fields["targetname"], fields.get("label", "")))
    return graph


def load_config(path: Path | None) -> tuple[list[Indirect], dict[str, int]]:
    """`indirect <caller>[,<caller>...] <sites> <target>...` and `external <function> <bytes>`."""
    indirect: list[Indirect] = []
    external: dict[str, int] = {}
    caller_line: dict[str, int] = {}  # each caller may be in one entry only
    if path is None:
        return indirect, external
    for number, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        words = line.split()
        if words[0] == "indirect" and len(words) >= 4 and words[2].isdigit():
            callers = tuple(words[1].split(","))
            for caller in callers:
                if caller in caller_line:
                    raise ValueError(f"{path}:{number}: {caller} is already in the indirect entry on line "
                                     f"{caller_line[caller]}; one caller belongs to one entry, so merge them")
                caller_line[caller] = number
            indirect.append(Indirect(callers, int(words[2]), tuple(words[3:])))
        elif words[0] == "external" and len(words) == 3 and words[2].isdigit():
            external[words[1]] = int(words[2])
        else:
            raise ValueError(f"{path}:{number}: cannot read {raw.strip()!r}")
    return indirect, external


def config_defines(path: Path) -> dict[str, int]:
    """Integer #defines of FreeRTOSConfig.h: `#define configX ((uint16_t)128)` -> 128."""
    values = {}
    for line in path.read_text().splitlines():
        match = re.match(r"\s*#define\s+(\w+)\s+(.*)", line)
        if match:
            numbers = re.findall(r"\b(\d+)\b", match.group(2).split("/*")[0])
            if numbers:
                values[match.group(1)] = int(numbers[-1])
    return values


def load_tasks(ioc: Path, freertos_config: Path | None) -> list[Task]:
    tasks = []
    for line in ioc.read_text().splitlines():
        match = re.match(r"FREERTOS\.Tasks\d+=(.*)", line.strip())
        if match:
            name, _priority, words, entry = match.group(1).split(",")[:4]
            tasks.append(Task(name, int(words) * 4, entry))  # CubeMX gives words; 4 bytes each
    if freertos_config is not None:
        defines = config_defines(freertos_config)
        for name, entry, depth, enabled in KERNEL_TASKS:
            if enabled is not None and not defines.get(enabled):
                continue
            if depth not in defines:
                raise ValueError(f"{freertos_config}: no value for {depth}")
            tasks.append(Task(name, defines[depth] * 4, entry))
    return tasks


def resolve(graph: dict[str, Function], name: str) -> str | None:
    """The graph title for a function name. A global definition wins. Otherwise a
    file-local one (GCC titles a weak definition, such as HAL_GetTick, by its file):
    the largest frame when several files define it, to stay on the safe side."""
    if name in graph and graph[name].frame is not None:
        return name
    local = [t for t in graph if short(t) == name and graph[t].frame is not None]
    if local:
        return max(local, key=lambda t: graph[t].frame)
    return name if name in graph else None


def check_indirect(graph: dict[str, Function], indirect: list[Indirect]) -> list[str]:
    """Every config entry must match the number of function-pointer call sites its
    callers hold, so a new callback cannot inherit an old entry unnoticed."""
    problems = []
    for entry in indirect:
        found = sum(1 for t, f in graph.items() if short(t) in entry.callers
                    for callee, _ in f.calls if callee == INDIRECT)
        if found != entry.sites:
            problems.append(f"config `indirect {','.join(entry.callers)} {entry.sites} ...` counts "
                            f"{entry.sites} function-pointer call site(s), the call graph has {found}: "
                            f"check the new or removed calls and update the entry")
    return problems


def deepest(graph: dict[str, Function], root: str, indirect: list[Indirect],
            external: dict[str, int]) -> tuple[int, list[str], list[str]]:
    problems: list[str] = []
    memo: dict[str, tuple[int, list[str]]] = {}
    active: list[str] = []
    groups = {caller: entry for entry in indirect for caller in entry.callers}

    def deeper(a: tuple[int, list[str]], b: tuple[int, list[str]]) -> tuple[int, list[str]]:
        return b if b[0] > a[0] else a

    def visit(title: str) -> tuple[int, list[str]]:
        if title in memo:
            return memo[title]
        if title in active:
            cycle = " -> ".join(short(t) for t in active[active.index(title):] + [title])
            problems.append(f"recursion: {cycle}")
            return 0, []
        function = graph.get(title)
        name = short(title)
        if function is None or function.frame is None:
            other = resolve(graph, name)
            if other is not None and other != title and graph[other].frame is not None:
                memo[title] = visit(other)
                return memo[title]
            if name in external:
                memo[title] = (external[name], [f"{name} (external, {external[name]} B)"])
            else:
                problems.append(f"no frame size for {name}: add `external {name} <bytes>` to the config")
                memo[title] = (0, [name])
            return memo[title]
        if "dynamic" in function.kind and "bounded" not in function.kind:
            problems.append(f"{name} has a dynamically sized frame")
        active.append(title)
        best: tuple[int, list[str]] = (0, [])
        for callee, label in function.calls:
            if callee != INDIRECT:
                best = deeper(best, visit(callee))
                continue
            entry = groups.get(name)
            if entry is None:
                problems.append(f"unresolved function-pointer call in {name} ({site(label)}): "
                                f"add `indirect {name} <sites> <target>...` to the config")
                continue
            for target in entry.targets:
                if target == "none":
                    continue
                resolved = resolve(graph, target)
                if resolved is None:
                    problems.append(f"indirect target {target} (from {name}) is not in the call graph")
                    continue
                best = deeper(best, visit(resolved))
        active.pop()
        own = (function.frame + best[0], [f"{name} ({function.frame} B)"] + best[1])
        # A file-titled node may be a weak definition that a global one overrides at
        # link time (HAL callbacks, MspInit). The .ci files cannot say which one is
        # linked, so take the deeper of the two.
        if title != name and name in graph and graph[name].frame is not None:
            strong = visit(name)
            if strong[0] > own[0]:
                own = (strong[0], strong[1][:1] + [f"(deeper than the weak {name})"] + strong[1][1:])
        memo[title] = own
        return own

    depth, path = visit(root)
    return depth, path, sorted(set(problems))


def analyse(ioc: Path, freertos_config: Path | None, files: list[Path], config: Path | None) -> list[Result]:
    graph = load_graph(files)
    indirect, external = load_config(config)
    config_problems = check_indirect(graph, indirect)
    results = []
    for task in load_tasks(ioc, freertos_config):
        root = resolve(graph, task.entry)
        if root is None:
            results.append(Result(task, 0, [], [f"entry function {task.entry} is not in the call graph"]))
            continue
        depth, path, problems = deepest(graph, root, indirect, external)
        results.append(Result(task, depth, path, sorted(set(problems + config_problems))))
    return results


def report(results: list[Result]) -> str:
    lines = []
    for r in results:
        verdict = "OK" if r.ok else "FAIL"
        lines.append(f"{verdict} task {r.task.name}: deepest path {r.depth} B + switch allowance "
                     f"{SWITCH_ALLOWANCE_BYTES} B = {r.total} B of {r.task.stack_bytes} B "
                     f"(headroom {r.task.stack_bytes - r.total} B)")
        lines.extend(f"    {step}" for step in r.path)
        lines.extend(f"  problem: {p}" for p in r.problems)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--ioc", type=Path, required=True)
    parser.add_argument("--freertos-config", type=Path,
                        help="FreeRTOSConfig.h, for the kernel's idle and timer task stacks")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--objects", type=Path, help="file listing the linked object files, one per line")
    source.add_argument("--ci-dir", type=Path, help="read every .ci file under this directory")
    parser.add_argument("--config", type=Path, help="function-pointer calls and library function sizes")
    parser.add_argument("--report", type=Path,
                        help="also write the report here, only when every task passes (a build stamp)")
    args = parser.parse_args(argv)
    try:
        results = analyse(args.ioc, args.freertos_config, ci_files(args.objects, args.ci_dir), args.config)
    except (OSError, ValueError) as error:
        print(f"stack_depth: {error}", file=sys.stderr)
        return 2
    if not results:
        print("stack_depth: no tasks found", file=sys.stderr)
        return 2
    text = report(results)
    print(text)
    passed = all(r.ok for r in results)
    if args.report is not None:
        if passed:
            args.report.write_text(text + "\n")
        elif args.report.exists():
            args.report.unlink()  # no stale pass left behind for the next build to trust
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
