# Issue tracker: GitHub

> Agent configuration for the mattpocock-skills plugin (`to-tickets`, `to-spec`, `triage`, `wayfinder`, `implement`, `code-review`). Not project documentation: `Documentation/**` is the only authority, and nothing here overrides `.github/ISSUE_CONTRACT.md` or `.github/ISSUE_FRAMEWORK.md`.

Issues and specs for this repo live as GitHub issues on `LentonNeale/Karetao`. Use the `gh` CLI for all operations. `gh` infers the repo from `git remote -v` when run inside this clone.

## Karetao rules that override the generic conventions

- **Titles** are action-oriented: `[SD-xx] Resolve ...`, `[LIVE-xx] Verify ...`, `[LIVE-xx] Implement ...`, or `Investigate ...` when no identifier exists (`ISSUE_CONTRACT.md`, Naming Convention).
- **Labels**: only the approved taxonomy in `ISSUE_CONTRACT.md` (`design`, `implementation`, `verification`, `safety`, `timing`, `communications`, `mechanical`, `configuration`; `estimation` is dormant). Labels describe the nature of the work, never workflow state. **Never create a label.** See `triage-labels.md` for how the triage roles fit this.
- **Decisions** go in `Documentation/07_DECISIONS/`, not in issue bodies. Link the issue to the record.
- **Reference** the `LIVE-xx` / `SD-xx` / `SYS-*` identifier the issue serves, when one exists.
- Work packages and sprint stories above the issue level live in `icm-project/lifecycle.json` and `icm-project/backlog.json` (the ICM Portal). A GitHub issue is the unit of trackable work; it does not replace those.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies. Add `--label` only from the approved set.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."` (approved labels only).
- **Close**: `gh issue close <number> --comment "..."`. Close when acceptance criteria are met, or as not planned / duplicate.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same states as issues, using the `gh pr` equivalents:

- **Read a PR**: `gh pr view <number> --comments` and `gh pr diff <number>` for the diff.
- **List external PRs for triage**: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments` then keep only `authorAssociation` of `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or `NONE` (drop `OWNER`/`MEMBER`/`COLLABORATOR`).
- **Comment / label / close**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh pr view 42` and fall back to `gh issue view 42`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue with a contract-compliant title. If the spec contains a technical decision, put the decision in `Documentation/07_DECISIONS/` (via the normal review path) and link it from the issue rather than deciding it in the issue body.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue holding the Notes / Decisions-so-far / Fog body. The generic skill labels it `wayfinder:map`; that label is **not approved** here, so instead title it `Wayfinder map: <effort>` and do not label it.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (`gh api` on the sub-issues endpoint). Where sub-issues aren't enabled, add the child to a task list in the map body and put `Part of #<map>` at the top of the child body. The generic `wayfinder:<type>` labels are not approved; write `Type: research|prototype|grilling|task` as the first line of the body instead. Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: GitHub's **native issue dependencies**. Add an edge with `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where `<blocker-db-id>` is the blocker's numeric **database id** (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, _not_ the `#number` or `node_id`). GitHub reports `issue_dependencies_summary.blocked_by` (open blockers only, the live gate). Where dependencies aren't available, fall back to a `Blocked by: #<n>, #<n>` line at the top of the child body. A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open children (`gh issue list --state open`, scoped to the map's sub-issues / task list), drop any with an open blocker (`issue_dependencies_summary.blocked_by > 0`, or an open issue in the `Blocked by` line) or an assignee; first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me`, the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far. A resolved decision that is architectural also goes into `Documentation/07_DECISIONS/` by Lenton.
