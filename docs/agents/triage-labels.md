# Triage Labels

> Agent configuration for the mattpocock-skills plugin. Not project documentation; `.github/ISSUE_CONTRACT.md` is the authority on labels.

The skills speak in terms of five canonical triage **state** roles and two **category** roles. Karetao's issue contract says labels describe the nature of the work and **never** workflow state, and forbids inventing labels (`ISSUE_CONTRACT.md`, rule 6 and "Label selection"). So the state roles have **no label** here.

## State roles

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | _(none, not approved)_ | Maintainer needs to evaluate this issue  |
| `needs-info`               | _(none, not approved)_ | Waiting on reporter for more information |
| `ready-for-agent`          | _(none, not approved)_ | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | _(none, not approved)_ | Requires human implementation            |
| `wontfix`                  | _(none, not approved)_ | Will not be actioned                     |

**How to record state without labels.** When a skill says "apply the `<role>` triage label":

1. Do **not** run `gh label create` or add an unapproved label.
2. Put the state as the first line of the triage comment: `> Triage state: ready-for-agent`.
3. For `wontfix`, close the issue as not planned (`gh issue close <n> --reason "not planned"`).
4. If the issue is managed in the Karetao Engineering Project, its Project `Status` field is the work-tracking state (`ISSUE_CONTRACT.md`, rule 9); set that if asked, and never present it as a requirement.

**To use real labels instead**, Lenton adds the five strings to the Approved Labels table in `ISSUE_CONTRACT.md`, creates them with `gh label create`, and edits the right-hand column above. Until then an agent must not do this on its own.

## Category roles

| Role in mattpocock/skills | Label in our tracker | Note |
| ------------------------- | -------------------- | ---- |
| `bug`                     | the nature-of-work label that fits (`implementation`, `communications`, `timing`, `safety`, `configuration`, `mechanical`) | There is no `bug` label; pick by what is broken. |
| `enhancement`             | `design` for a design question or decision; `implementation` for agreed build work; `verification` for test or evidence work | There is no `enhancement` label. |

Multiple labels on one issue are fine. Leave an issue unlabeled rather than invent a label.
