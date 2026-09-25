```
issue: none yet
task: icm-gui-chat
stage: 01-intake
status: ready
author: agent:orchestrator/opus
tier_suggested: T3
tier:
```

# icm-gui-chat — Liaison chat panel and Orchestrator panel in the ICM GUI

## 1. Goal
Inside the GUI, the User can talk to the Client Liaison in a right-hand side panel, and drive the Orchestrator in a collapsible panel along the bottom of the window. Replies and tool activity stream live, and permission requests appear as Allow/Deny buttons. Helpers can read both conversations but can't type.

## 2. Type
New work (a feature added to the accepted icm-gui prototype).

## 3. Where
- `gui/`: a new session manager, chat endpoints, the panel layout and a small amount of plain JavaScript.
- `tests/`: a fake `claude` replayer, recorded protocol fixtures, and smoke tests.
- `stages/01-intake/references/brief-template.md`: new header keys, so that briefs the liaison writes show up correctly in the GUI. This is a workspace contract change.
- It runs the existing `client-liaison` agent, with the same restrictions as `scripts/liaison.sh`, and the orchestrator as the default main session.

## 4. Why now
Today the liaison runs in a separate tmux session and the orchestrator in another terminal. The User switches between three windows, and handing a brief over means typing `take brief <slug>` by hand. Putting both conversations in the GUI puts the whole flow on one screen: talk, get a brief, approve it, hand it over, watch the work.

## 5. Done when
1. **Liaison panel:** docked on the right on every User page.
   - Messages stream token by token.
   - The liaison runs as `--agent client-liaison --model haiku`, with Bash, web and subagent tools disallowed, and writes allowed only to `stages/01-intake/output/`.
   - A brief it writes appears in the Queue with "select tier" within one page refresh.
2. **Orchestrator panel:** along the bottom of every User page.
   - It can be collapsed and resized.
   - It streams assistant text, one-line tool-call summaries, and each turn's result with its token count and cost.
   - A tool call that needs permission shows **Allow once / Deny** buttons, and the session waits for the answer.
3. **Sessions survive a page reload and a server restart:**
   - The conversation is replayed from the GUI's event log.
   - The CLI session is resumed by its session ID.
   - **New conversation** starts a fresh one.
4. **Handoff:** on an approved brief, a **Send to orchestrator** button sends `take brief <slug>` to the Orchestrator panel. It's disabled until C1 is approved.
5. **Helpers:** they see both panels read-only, with no input box and no Allow/Deny buttons. Any POST they make to a chat endpoint returns 403.
6. **Security:** every POST, old and new, requires a matching `Origin`/`Host` for 127.0.0.1 and a per-server CSRF token. Tests show that a cross-origin POST is refused.
7. **Tested without tokens:** the smoke tests and the demo run against a fake `claude` that replays recorded protocol fixtures. One manual walkthrough step uses the real CLI.

## 6. Constraints
- **Python standard library only** on the server. Streaming uses Server-Sent Events. The browser code is plain JavaScript (EventSource and fetch) with no libraries and no build step.
- **Human control:**
  - Nothing the orchestrator does bypasses Claude Code's own permission system; unapproved tools are denied, never auto-allowed.
  - The CLAUDE.md checkpoints still apply inside the orchestrator session.
  - The GUI never adds `bypassPermissions`.
- **Only one of each:** one liaison session and one orchestrator session per GUI server. The GUI stays local-only (127.0.0.1).
- **Demo mode** uses the fake `claude` by default, because the demo data isn't laid out like a real workspace. Real chat runs in live mode against the real workspace.
- **Token budget (proposed):** about 0.75M to build (see the plan). Chat usage at runtime (Haiku liaison, Opus orchestrator) is billed as normal Claude Code usage and isn't part of this budget.

## 7. Out of scope
- A real embedded terminal (xterm.js or a pseudo-terminal).
- More than one concurrent session per panel, and multi-user shared sessions.
- Helpers chatting.
- Voice input and file attachments in chat.
- The Layer 0 rule change and storing Helper tasks as GitHub issues (still deferred from icm-gui).

## 8. Related
- icm-gui prototype (accepted 2026-09-25), branch `icm-gui-prototype`.
- `scripts/liaison.sh` on `main` (the tmux layout): the liaison's restrictions are taken from there.
- The new `main` agents (`python-dev`, `subject-expert`) need `../icm-project/`, which this workspace checkout doesn't have, so the plan uses `haiku-dev`.

## 9. Priority
Unknown. The User asked for this before the icm-gui pull request.

## 10. Evidence
- Smoke tests against the fake `claude`: streaming, permission Allow/Deny, reload replay, restart resume, Helper read-only, CSRF refusal, handoff.
- A recorded protocol fixture with a real permission request.
- One manual walkthrough step with the real CLI on the User's machine.

## Open questions
- Whether `--permission-prompts host` delivers `can_use_tool` requests over stdio in stream-json mode. The protocol check in the plan's WP1 answers this. If it doesn't, the fallback is to show the `permission_denied` event with an **Allow and retry** button, which resumes the session with that one allow rule added.
- Approving the brief-template header change (a workspace contract change).

## Gaps
- 9 Priority: not given.

## Revision log
- 2026-09-25 created from the conversation (Orchestrator panel: interactive; liaison: right-hand side panel; handoff through the Queue; Helpers read-only)
