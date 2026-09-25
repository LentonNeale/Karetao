# Efficiency test — tools, hooks and shared files

A recurring test of the ICM workspace. The agent team reviews how the User's past requests were actually handled, and proposes **Python tools, Claude Code hooks and shared files** that would have handled the same work with fewer tokens. Run it after significant workspace changes and compare runs over time.

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Usage digest | `results/digest.json` (made by `extract_usage.py`, run locally) | Full; it's compact by design | What the work actually cost: token totals, tool calls, Bash shapes, sequences, re-reads, large outputs, subagents. Cite pattern ids (`T*`, `B*`, `S*`, `R*`, `L*`, `A*`) |
| Existing tooling | `workspace/scripts/`, `workspace/agents/`, `.claude/settings*.json` hooks | Names and one-line purposes | Don't re-propose what exists; extend it instead |
| Workspace rules | `workspace/CLAUDE.md` | Operating rules, delegation table | Proposals must fit the ICM model and delegation policy |
| Proposal format | `proposal-template.json` | Full | The required fields |

The digest holds no conversation text. Don't try to read raw transcripts; the digest is the only input about past work.

## Process

1. Read the digest and identify the most expensive patterns first. Context re-reads (`cache_read`) usually dwarf tool output, so look for what grows the context: large results, repeated reads of the same file, long exploratory command chains.
2. For each candidate, check the admission rules below. Drop anything that fails them, and note why in `rejected`.
3. Write each proposal in the template's shape. Estimate the tokens saved per use and the uses per week, **from the digest's counts**. Show the arithmetic in `estimate_basis`.
4. Prefer, in order: a **shared file** that answers a recurring question once (for example a generated index); a **tool** (a Python script the agent calls instead of many shell and read steps); a **hook** that stops waste automatically (for example trimming or refusing oversized outputs).
5. Rank by `score = tokens_saved_per_use × uses_per_week`. Keep 5–12 proposals.
6. Run `python3 check_proposals.py results/proposals.json --digest results/digest.json` and fix any errors it reports.

**Admission rules.** A proposal is only valid if:
- its input and output are concrete and machine-checkable (arguments, files, formats), with no "analyse" or "understand" steps;
- it can be written in Python 3.10+ using the standard library (plus `gh`, `git` or `jq` called as subprocesses);
- it's deterministic: the same input gives the same output, and no model is needed inside it;
- it cites at least one digest pattern id as evidence;
- it's generic, or configured through `icm-project/`, so it works in any project using this workspace.

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Proposals | `results/proposals.json` | `proposal-template.json` shape: `proposals[]` and `rejected[]` |
| Summary | `results/summary.md` | A ranked table (id · name · kind · score), the top three explained in plain language, and any digest gaps that limited the analysis |

`results/` is gitignored. Only generic proposals may be copied into shared reports; never copy project file names or content.
