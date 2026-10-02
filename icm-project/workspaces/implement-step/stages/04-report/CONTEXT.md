# 04 Report

Gathers the card's facts into one short report; the reviewer reads this and little else. No model
runs here: the Portal writes it.

## Inputs

| Source | File/Location | Section/Scope | Why |
|---|---|---|---|
| Step | its id and title | Full | What was asked |
| Change answer | stage 02's `work_summary` and `notes` | Full | What the builder says it did |
| Locate output | `build/<step>/context.md` | Full | Where the change was aimed |
| Check result | `build/<step>/check.md` | Status and failures | Whether the checks passed |
| Tool | icm/tools/diff_summary.md | Run section | Documentation only: the Portal runs it; changes capped, no lock files or fixtures |

## Process

1. Write the headings in order: Step, Summary, Notes, Locations, Check, Changes.
2. Under Changes put the diff summary's stat and its capped diff; say if it was cut.

## Audit

| Check | Pass condition |
|---|---|
| Complete | All six headings are present |
| Bounded | The diff is no longer than the summary's limit |

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Card report | `build/<step>/card-report.md` in the run folder | Markdown, six headings |
