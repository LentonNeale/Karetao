# Definition of Ready

A brief is **ready** when each item below is answered specifically. Write "none" or "unknown" explicitly; never leave an item blank.

| # | Item | Ready when… | Not ready (example) |
|---|---|---|---|
| 1 | Goal | One sentence saying what changes for the user or the system | "Improve timing" |
| 2 | Type | New work · change to existing work · question/research · bug | — |
| 3 | Where | The component(s) or document area, named from `PROJECT.md` / `authority.md` | "the firmware somewhere" |
| 4 | Why now | The trigger or problem, and what happens if it isn't done | — |
| 5 | Done when | 2–6 observable acceptance criteria, each checkable by a test, measurement, review or document | "works properly" |
| 6 | Constraints | Must-keep behaviour, interfaces, safety or performance limits, deadlines | — |
| 7 | Out of scope | At least one thing this request explicitly does **not** cover | — |
| 8 | Related | Known issue numbers, register or decision IDs, or documents (or "unknown, orchestrator to search") | — |
| 9 | Priority | High / Medium / Low, in the user's own judgment | — |
| 10 | Evidence | What the user will accept as proof: host test, hardware measurement, doc review… | — |

## Status values

- `ready`: all ten items are satisfied.
- `ready-with-gaps`: the user chose to send it early; every missing item is listed under *Gaps*.
- `draft`: still in conversation.
