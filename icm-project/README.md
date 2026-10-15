# icm-project

Karetao's own ICM material: the project-specific tools, references and research notes that the
repository's skills work with. Generic, reusable material stays in the shared ICM library's `icm/`
folder (`~/Git_repos/icm_library/icm`); only things that hold Karetao facts live here.

| Folder | What goes in it |
|---|---|
| `tools/` | A deterministic Python tool with its `.md` card, specific to Karetao: `doc_check` (documentation rules), `issue_graph` (open issues, dependencies, board Status and order) |
| `references/` | Reference folders: vendor datasheets and manuals, standards, interface notes. `ROUTING.md` says which note to read for which code area |
| `research/` | Research and tutored-walk notes (`/work-issue` writes `<issue>-<slug>.md` here) |
| `workspaces/` | Drafted GitHub command sets from reviews (`gh-commands.sh` plus body files), run by Lenton after reading them |

`requester-profile.md` says how requests for Karetao are usually phrased.

## Working method

Work is tracked as GitHub issues on `LentonNeale/Karetao` under the issue contract
(`.github/ISSUE_CONTRACT.md`): milestones are the stages (Stage 0 Foundation, Stages 1 to 5 named
after the charter goals), blocking is recorded with native issue dependencies, and the Karetao
Engineering Project board holds Status and order. Two repository skills drive it:

- `/next-issue`: reads the dependency graph, refreshes board Status and order, lists what is Ready.
- `/work-issue <n>`: works one issue in learning mode, then runs the story loop (worktree, build,
  checks, review, hold for Lenton, commit on his word).

The ICM Portal and its work-package Map (`lifecycle.json`, `backlog.json`) were retired on
2026-10-15. Both files remain in git history (`git show 247cf35:icm-project/backlog.json`); stories
migrate into issues stage by stage from there. Portal run data stayed outside the repo in
`~/icm-portal/data/karetao/` as an archive; its three gate records (WP7 Architecture pass, WP2
Verification pass) are process events, not technical decisions, so nothing was carried into
`Documentation/07_DECISIONS/`.

## Privacy check

`forbidden-terms.txt` (untracked) lists Karetao terms that must never appear in the shared library
repo. Before pushing library changes, run from `~/Git_repos/icm_library`:

```bash
python3 scripts/check-project-facts.py --terms ~/Git_repos/Karetao/icm-project/forbidden-terms.txt
```
