# Requester profile (LentonNeale)

Read by `client-liaison` at the start of every conversation. Built on 2026-09-25 from 236 typed prompts and 10 question answers in 13 interactive sessions (`workspace/tests/liaison/extract_prompts.py` plus an analysis). The rates below come from a manual read of 35 new-work and review requests, so treat them as directional. Re-run the analysis when habits change.

## Reliably provided (don't re-ask)

- Exact terminal output, error text and tracebacks, pasted verbatim (about 1 in 5 short prompts).
- Wiring and pin tables when hardware is involved.
- File and document references (`@path`) when the file is already open.
- Hardware and environment changes, volunteered as they happen ("st-link reconnected", "installed gh").
- Clear answers to numbered options; the **(recommended)** option is usually accepted.

## Often missing: ask proactively

| Gap | When it shows up | Question to ask |
|---|---|---|
| Done when (missing in ~30/35) | Almost every new-work or review request | "When this is finished, what will you check to know it worked?" Offer 2–3 concrete criteria to pick from. |
| Out of scope (~33/35) | Every request | "Is anything explicitly *not* part of this? (recommended: …)" |
| Priority (35/35) | Every request | Offer High / Medium / Low with a recommended default and a one-line reason. |
| Why now (~30/35) | New work | "What prompted this now?" Accept a one-line answer. |
| Evidence (~31/35) | Anything involving figures, hardware or tests | "Should the result be measured on hardware, host-tested, or is a calculated or theoretical figure acceptable?" |
| Where (~16/35 missing, ~10/35 vague) | "the docs", "the project", "this" | Name the likely components from `PROJECT.md` as options. |
| "Resolved" for review or audit requests | "review…", "resolve conflicts…", "check…" | "Should I *fix* what I find, or *report* it for you to decide?" |

## Often vague: ask for the concrete form

| Vague form | Ask for |
|---|---|
| A goal that is only a verb ("migrate the docs", "fix the conflicts") | The outcome: "when done, … will be true" |
| Git verbs used loosely (push, merge, branch, PR sometimes swapped) | The exact steps as options: commit only · push branch · open PR · merge to main · publish to Karetao_Consulting |
| "update the docs" | Which documents (status docs, requirements, interfaces, component docs) |
| A number offered as evidence | Measured (how, on what) or theoretical |

## Unstated expectations: confirm up front

These surface late in most multi-step sessions. Ask about them in the first brief for any request that changes files.

| Expectation | Question to ask |
|---|---|
| A commit message is drafted for him (8+ sessions) | "I'll have a commit message drafted; OK?" (recommended: yes) |
| Work is delivered to GitHub: branch, PR, merge, sometimes a subtree publish (7+ sessions) | "How should this be delivered?" with the Delivery options, recommended: branch + PR, approval before any push |
| No hardware-validation claims from software-only or theoretical results (3 sessions, corrected after the fact) | "Any figures will be labelled measured or theoretical; hardware validation is claimed only from bench evidence. Agree?" |
| Status and authority docs updated as part of "done" (2+ sessions) | "Should the status and authority documents be updated when this is done?" |
| Work delegated to cheaper models where possible (a standing preference) | Don't ask; note it for the orchestrator in *Constraints*. |

## Phrasing guide

| Phrase or spelling | Means |
|---|---|
| "go ahead", "proceed", "continue", "option 2", "use suggestion" | Approve the plan or option just shown; restate it in one line, then proceed |
| "can you …" | A plain request |
| A bare paste with no question | "Here's what happened: tell me what it means or what to do next." Ask which. |
| "CAn", "HOw" | Can, How (a caps-lock slip, not emphasis) |
| "Liasion" | Liaison (this agent) |
| confrimed / confim · erroe · Exlpain · Mannually · remeber · resaerch · seperate · informatiokn · accidently · requied · effiecent / efficent · highrical · revove · optikon · magenets | confirmed · error · Explain · Manually · remember · research · separate · information · accidentally · required · efficient · hierarchical · remove · option · magnets |
