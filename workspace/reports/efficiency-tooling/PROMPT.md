# Prompt for the cloud development agent

Copy everything between the lines into the cloud agent's session on `LentonNeale/Karetao_Consulting`.

---

You are the software development team for `LentonNeale/Karetao_Consulting`, the shared ICM engineering workspace that projects mount as `workspace/`. In this repo, the workspace is the repo root.

Your task is to implement the efficiency tooling described in `reports/efficiency-tooling/REPORT.md`. The exact input/output contracts, test plans and risks for WP1–WP9 are in `reports/efficiency-tooling/proposals-run1.json`, which is the source of truth where the report summarises.

How to work:
1. Read `CLAUDE.md`, `CONTEXT.md`, the report and the proposals file before changing anything. Then post a short plan: work packages in the report's order, one PR each.
2. For each work package: create a branch `efficiency/wp<n>-<name>` from `main`, implement it, and add `tests/tools/test_<name>.py` covering every case in its `test_plan`, including the failure cases. Run `python3 -m unittest discover -s tests/tools` and `python3 -m unittest discover -s tests/efficiency`. Open a PR into `main` that states the contract, the test evidence and anything you deviated from, with the reason.
3. Hard rules:
   - Python 3.10+ standard library only; `git`, `gh` and `jq` only as subprocesses.
   - Deterministic, with no model calls.
   - Hooks fail open (any error → no output, exit 0) and stay under 200 ms.
   - Nothing project-specific: synthetic fixtures only; generated files are gitignored.
   - Hooks stay opt-in: none are enabled before WP11 ships.
4. Don't modify `gui/**`, `scripts/icmlib.py`, `scripts/review.py`, `scripts/helper.py`, `scripts/stage_status.py` or `scripts/checkpoint_policy.py`. Another agent owns them on the `icm-gui-prototype` branch.
5. Don't merge anything. The User approves and merges each PR. If a contract turns out to be wrong or impossible, stop that work package and explain in the PR rather than inventing a new contract.
6. If you have Claude Code subagents: delegate each fully specified work package to `python-dev` (Haiku) and review its diff yourself; do the hook wiring (WP11) yourself.

When finished, reply with a table: WP · PR link · tests added · deviations. List any work package you couldn't complete, and why.

---
