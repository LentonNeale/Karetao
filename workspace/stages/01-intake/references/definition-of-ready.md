# Definition of Ready

A brief is **ready** when each of the eleven items below is answered specifically. Write "none" or "unknown" explicitly; never leave an item blank.

| # | Item | Ready when… | Not ready (example) |
|---|---|---|---|
| 1 | Goal | One sentence stating the **outcome**: what changes for the user or the system. An action verb alone isn't enough | "Improve timing", "migrate the docs" |
| 2 | Type | New work · change to existing work · question/research · bug | — |
| 3 | Where | The component(s) or document area, named from `PROJECT.md` / `authority.md` | "the firmware somewhere" |
| 4 | Why now | The trigger or problem, and what happens if it isn't done | — |
| 5 | Done when | 2–6 observable acceptance criteria, each checkable by a test, measurement, review or document | "works properly" |
| 6 | Constraints | Must-keep behaviour, interfaces, safety or performance limits, deadlines | — |
| 7 | Out of scope | At least one thing this request explicitly does **not** cover | — |
| 8 | Related | Known issue numbers, register or decision IDs, or documents (or "unknown, orchestrator to search") | — |
| 9 | Priority | High / Medium / Low. Offer the three with a recommended default; don't leave it open-ended | — |
| 10 | Evidence | What the user will accept as proof (host test, hardware measurement, doc review…), and whether any figure must be **measured** rather than theoretical or calculated | "it works", or a number with no source |
| 11 | Delivery | Where the result goes: files only · commit (with a drafted message) · branch + PR · merge · publish; and which steps need the user's approval first, especially any push | "push it" with no branch or approval named |

## Status values

- `ready`: all eleven items are satisfied.
- `ready-with-gaps`: the user chose to send it early; every missing item is listed under *Gaps*.
- `draft`: still in conversation.
