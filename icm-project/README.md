# icm-project

Karetao's own ICM material: the project-specific workspaces, tools, skills and references the
[ICM Portal](https://github.com/LentonNeale/icm_portal) works with. Generic, reusable
material stays in the shared ICM library's `icm/` folder (`~/Git_repos/icm_library/icm`); only things that hold Karetao facts live here.

| Folder | What goes in it | Made by |
|---|---|---|
| `workspaces/` | A Karetao workspace, or a `<name>.overlay/` folder of additions to a library workspace (`implement-step.overlay`, `pre-merge-review.overlay`: the reference routing rows and `shared/references.md`) | Management tab → Workspaces → Start guided add (`workspace_builder`) |
| `tools/` | A deterministic Python tool with its `.md` card, specific to Karetao | Management tab → Tools → Start guided add (`tool_builder`) |
| `skills/` | A Claude Code skill only Karetao uses | Management tab → Skills |
| `references/` | Reference folders: vendor datasheets and manuals, standards, interface notes | Management tab → References → Start guided add (`reference-intake`), or the Research tab |
| `research/` | Research notes saved from the Research tab | The Research tab's Save note |

`requester-profile.md` tells the Client Liaison how requests here are usually phrased.

## Running the Portal

```bash
cd ~/Git_repos/icm_portal
~/icm-portal/venv/bin/python -m icm_portal --project ~/Git_repos/Karetao
```

Settings are in `../portal.toml`. Run data (briefs, plans, designs, chats, logs) and the checklist
are kept outside the repo, in `~/icm-portal/data/karetao/`, and builds happen in a separate
worktree, never in this working copy.

## Privacy check

`forbidden-terms.txt` (untracked) lists Karetao terms that must never appear in the shared Portal
repo. Before pushing Portal or library changes, run from the icm_library repo (`~/Git_repos/icm_library`):

```bash
python3 scripts/check-project-facts.py --terms ~/Git_repos/Karetao/icm-project/forbidden-terms.txt
```
