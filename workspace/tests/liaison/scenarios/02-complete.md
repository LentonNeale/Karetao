---
expect_brief: ready
expect_output_contains: ""
purpose: A request that already meets all eleven Definition of Ready items must produce a brief with status ready.
---
I'd like a change to `workspace/scripts/board-snapshot.sh`.

- Goal: add a `--milestone "<name>"` option so the snapshot shows only issues in that milestone.
- Type: change to existing work.
- Where: the ICM workspace scripts, specifically `workspace/scripts/board-snapshot.sh`.
- Why now: I review one milestone at a time, and the full table is too long to scan. Without this, I filter by eye and miss items.
- Done when:
  1. `board-snapshot.sh --milestone "M2 — Motion and Safety Gate"` lists only the open issues in M2.
  2. Combining it with `--all` also includes closed issues in that milestone.
  3. An unknown milestone name prints an error and exits 1.
  4. With no option, the output is unchanged.
- Constraints: bash and jq only; keep the current table columns and order.
- Out of scope: filtering by any other field (Status, Priority, and so on).
- Related: none known.
- Priority: Low.
- Evidence: I'll run the four cases above by hand and check the output (measured, not theoretical).
- Delivery: commit on a branch with a drafted message and open a PR; ask me before pushing.

Everything is decided. Show the brief and write it without waiting for another confirmation from me.
