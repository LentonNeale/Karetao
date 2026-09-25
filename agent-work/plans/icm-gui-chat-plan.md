```
issue: none yet
task: icm-gui-chat
stage: 04-implement
status: draft
author: agent:orchestrator/opus
```

# icm-gui-chat — Implementation plan

**Source brief:** `stages/01-intake/output/icm-gui-chat-brief.md`.

**Branch:** `icm-gui-prototype`, with `main` merged in first.

**Suggested tier:** T3. Brief, plan and evidence don't block progress; the brief-template change (C4-like) does.

## Layout (agreed)

```
┌──────────────────────────────┬────────────┐
│ Queue · Pipeline · Helper …  │ Liaison    │  right-hand side panel, ~360 px, collapsible
│  (current tab content)       │ you / liaison messages, input box
├──────────────────────────────┴────────────┤
│ Orchestrator ▾   [New conversation]       │  bottom panel, collapsible, drag to resize
│ streamed text · tool lines · Allow/Deny   │
│ [type…]                                   │
└───────────────────────────────────────────┘
```

For Helpers, both panels are read-only: no input box and no buttons.

## How it works

```
browser ──EventSource GET /chat/<panel>/events?since=N──► server ──(reader thread)── claude -p (stream-json)
browser ──fetch POST /chat/<panel>/send|permission|new──► server ──stdin JSON──────► claude
                                                           │
                                                           └─ append-only event log: ROOT/.icm-gui/chat/<panel>.jsonl
```

- `<panel>` is `liaison` or `orchestrator`.
- **Probe result (Karetao field test, Claude Code 2.1.282):** permission prompts reach the host only with `--permission-prompt-tool stdio` **and** `--permission-prompts host`; they then arrive as `control_request`/`can_use_tool` and are answered with `control_response`/`allow`. Without `stdio`, writes are silently denied, and `result` still says `success` with `permission_denials: N`, so the GUI must surface `permission_denials`. Unknown event types (`thinking_tokens`, `rate_limit_event`) must be tolerated. The fallback in WP3 is therefore not needed.
- **One long-lived CLI process per panel:**
  ```
  claude -p --input-format stream-json --output-format stream-json --verbose --include-partial-messages --permission-prompts host --permission-prompt-tool stdio [--resume <id>] …
  ```
  It runs with `cwd` = ICM_ROOT, the parent of the workspace, the same as `liaison.sh`.
- **Liaison:** run `scripts/liaison.sh -p` plus the stream-json flags above. `liaison.sh` on `main` runs headless when there's no terminal or when given `-p`, and passes extra arguments through, so it stays the single source of the liaison's restrictions (Haiku, disallowed tools, writes allowed only to `stages/01-intake/output/`).
- **Denials:** a `result` can say `success` while `permission_denials` > 0 (seen when `stdio` is missing). Both panels show such denials as a warning line and never treat the turn as clean.
- **Orchestrator:** the default model and the project's own settings. The GUI adds **no** permission rules.
- **Session IDs** are stored in `ROOT/.icm-gui/chat/sessions.json` for `--resume`. `.icm-gui/` is gitignored.
- **The `claude` binary** comes from `$ICM_GUI_CLAUDE`, with `claude` as the default. Tests and `--demo` point it at `tests/fakes/fake_claude.py`.

---

## Waves

| Wave | WPs | Agent | Check |
|---|---|---|---|
| 0 | WP0 merge `main` · WP1 protocol spike and fixtures | orchestrator · sonnet | unit + smoke tests pass after the merge; `tests/fixtures/chat/PROTOCOL.md` exists |
| 1 | WP2 security (CSRF / Origin) · WP3 session manager · WP5 event → display mapping | sonnet · sonnet · haiku-dev | unit tests + smoke tests |
| 2 | WP4 chat endpoints + SSE · WP7 handoff button + template header | haiku-dev · haiku-dev | smoke tests |
| 3 | WP6 panels (HTML/CSS/JS) | haiku-dev | smoke tests + screenshots |
| 4 | WP8 smoke tests, demo wiring, walkthrough | haiku-dev | full tests; `gui.sh --demo --check` |

**Why Sonnet for WP1–WP3:**
- WP1 runs the real CLI and reads an undocumented stream.
- WP2 changes every POST route.
- WP3 is threading and subprocess lifetime.

The early Haiku work packages needed Sonnet rework at exactly this kind of boundary.

---

## Work packages

### WP0 — Merge `main` (orchestrator) · ~5k

`git merge origin/main` into `icm-gui-prototype` (a trial merge showed no conflicts). Run the unit and smoke tests. Commit.

### WP1 — Protocol spike and fixtures (sonnet, runs the real CLI with Haiku) · 80k

1. Write `tests/fakes/record_session.py`. It starts the CLI in stream-json mode:
   - in a temporary git repo;
   - with a **clean environment**: only PATH, HOME, LANG and the auth variables; no `CLAUDE_CODE_*` session variables inherited from a parent session;
   - with a script of user turns and permission answers.

   It records every stdout line and every stdin line with timestamps.
2. Record these scenarios with `--model haiku`:
   - **a) plain turn:** text only;
   - **b) permission allowed:** a Write outside any allow rule, answered with `allow`;
   - **c) permission denied:** the same, answered with `deny`;
   - **d) resume:** a second process with `--resume <id>` whose reply shows it remembers turn 1;
   - **e) liaison:** `--agent client-liaison` restrictions, where a Write inside `stages/01-intake/output/` is allowed and one outside is denied.
3. Write `tests/fixtures/chat/PROTOCOL.md`. It covers:
   - the exact event types seen, with trimmed examples;
   - the stdin message format for a user turn;
   - how a permission request arrives, and the exact response that allows or denies it. Try `--permission-prompts host` with and without `--permission-prompt-tool stdio`, and record which works;
   - where `session_id`, text deltas, tool uses and results are found;
   - what `result` carries (usage, cost).
   - **If host permission prompts can't be made to work**, say so plainly and document the `permission_denied` event, so the fallback in WP3 can be used.
4. Write `tests/fakes/fake_claude.py`. It's executable, accepts the same flags, and chooses a scenario from `$FAKE_CLAUDE_SCENARIO` or from the first user message (`/scenario b`). It replays the recorded stdout, waits for the matching stdin before continuing past a permission request, and emits a stable fake `session_id`.

**Owns:** `tests/fakes/**`, `tests/fixtures/chat/**`.

**Done:**
- the fake replays all 5 scenarios;
- `python3 tests/fakes/fake_claude.py --selftest` exits 0;
- the real recordings are committed, with anything secret-looking scrubbed.

### WP2 — Request hardening (sonnet) · 60k

Now that a POST can drive agents, harden the server:
- **`Host` check:** reject any request whose `Host` isn't `127.0.0.1:<port>` or `localhost:<port>`. This blocks DNS rebinding.
- **`Origin` check:** reject any POST whose `Origin` (or, failing that, `Referer`) isn't the same origin.
- **CSRF token:** each server start generates a random token (`secrets.token_urlsafe`). Every form carries it as a hidden field, fetch calls send it as an `X-ICM-Token` header, and a missing or wrong token returns 403.

Update every existing form (WP8–WP10 of the prototype) through one `csrf_field()` helper in `views.py`.

**Owns:** the dispatcher in `gui/server.py`, a `csrf_field()` helper and its uses in `gui/views.py`, and smoke tests:
- a cross-origin POST → 403;
- a missing token → 403;
- a wrong Host → 400;
- all existing action tests still pass.

### WP3 — Session manager `gui/chat.py` (sonnet) · 120k

`ChatSession(panel, root, ws_root, claude_bin, extra_args)` with these methods:
- `start(resume=True)`
- `send(text)`
- `answer_permission(request_id, allow: bool)`
- `new_conversation()` (stops the process, clears the stored ID, adds a `divider` event)
- `stop()`
- `events_since(n) -> list`
- `subscribe()` / `unsubscribe()` (a `queue.Queue` per SSE client)
- `state()` → `idle | running | waiting-permission | stopped | error`

Behaviour:
- **Starting:** start the process lazily on the first `send`.
- **Reading:** one reader thread per process. Append every stdout event, *and every user message sent*, to `ROOT/.icm-gui/chat/<panel>.jsonl` as `{"n": seq, "ts": …, "dir": "in"|"out", "event": {…}}`, then fan it out to subscribers.
- **Session ID:** store the `session_id` from the init event in `sessions.json`.
- **Permissions:** record pending requests; `answer_permission` writes the response in the exact format from `PROTOCOL.md`. If WP1 found that host prompts don't work, implement the fallback instead: on `permission_denied`, record a pending "allow and retry" item; answering `allow` restarts the process with `--resume` plus that one rule added to `--settings`, then sends "Permission granted for <tool>; please retry."
- **Crashes:** if the process exits unexpectedly, emit an `error` event with the last 20 stderr lines and move to `stopped`. The next `send` restarts it with `--resume`.
- **Thread safety:** a single lock around the process, the log and the pending permissions. Never hold the lock while blocking on a pipe.
- **Registry:** a module-level `get_session(panel, …)` so the server holds exactly one session per panel.

**Owns:** `gui/chat.py`, `tests/unit/test_chat.py` (every test runs against `fake_claude.py` in temporary directories and covers each scenario, restart-resume and crash recovery).

### WP4 — Chat endpoints (haiku-dev) · 80k

Register these routes in a new `# --- chat (WP4) ---` block in `gui/server.py`:

| Route | Roles | What it does |
|---|---|---|
| `GET /chat/<panel>/events?since=N` | users, helpers | Server-Sent Events: first replays `events_since(N)`, then streams live events. Each SSE message is `id: <n>` plus `data: <json of the display item>` (mapped by WP5). Sends a `: keepalive` comment every 15 s. Unsubscribes when the client disconnects. |
| `GET /chat/<panel>/state` | users, helpers | JSON `{"state": …, "pending_permissions": [...]}` |
| `POST /chat/<panel>/send` | users | Form `text`, max 20 000 characters. Returns 202. |
| `POST /chat/<panel>/permission` | users | Form `request_id`, `decision=allow\|deny`. Returns 204. |
| `POST /chat/<panel>/new` | users | Starts a new conversation. Returns 204. |

Rules:
- An unknown `<panel>` returns 404; Helper POSTs return 403 through `ROLE_ALLOWED`.
- The server needs `daemon_threads = True`, and each SSE handler must stop cleanly on `BrokenPipeError`.

**Owns:** the WP4 block, plus smoke tests using the fake:
- send, then receive the streamed text;
- a permission request, then allow, then the turn completes;
- a Helper sees events but gets 403 on a POST.

### WP5 — Event → display mapping (haiku-dev) · 70k

`gui/chat_display.py`: `to_display(record) -> dict | None`, a pure function built from `PROTOCOL.md`.

Display items:

| `kind` | Fields |
|---|---|
| `user` | `text` |
| `text-delta` | `text` |
| `text` | `text` (a full assistant message) |
| `tool` | `name`, `summary` (≤120 characters, e.g. `Read stages/…/x.md`, `Bash: git status`) |
| `tool-result` | `ok`, `summary` |
| `permission` | `request_id`, `tool`, `summary` |
| `result` | `tokens`, `cost_usd`, `duration_s` |
| `error` | `text` |
| `divider` | — |

Return `None` for noise: status, rate-limit and hook events.

**Owns:** `gui/chat_display.py`, `tests/unit/test_chat_display.py` (feeds every recorded fixture line through it; there must be no exceptions, and the expected items appear for each scenario).

### WP6 — Panels UI (haiku-dev) · 90k

- **`shared_layout`:** gains the right-hand liaison panel and the bottom orchestrator panel for users and helpers (Helpers get no input box or buttons). The page body becomes a CSS grid:
  ```
  grid-template-areas: "main side" "bottom bottom"
  ```
  At widths under 900 px, the side panel collapses into a toggle button.
- **`gui/static/chat.js`:** plain JavaScript, no libraries. For each panel it:
  - opens an EventSource with the last seen `id` (kept in `sessionStorage`, wrapped in try/catch);
  - renders display items: text deltas are appended into the current message; tool lines are muted and monospaced; permission items get **Allow once / Deny** buttons that POST and then disable themselves; result lines show `1,234 tokens · $0.012`;
  - auto-scrolls unless the user has scrolled up;
  - sends on Enter (Shift+Enter makes a new line), disabling Send while the state is `running`;
  - handles **New conversation** with a confirm();
  - makes the bottom panel collapsible and drag-resizable (height kept in `localStorage`, wrapped in try/catch);
  - sends every POST with the `X-ICM-Token` header from `<meta name="icm-token">`.
- **`style.css`:** panel styles for light and dark themes.

**Owns:** the `shared_layout` changes, `gui/static/chat.js`, the chat styles in `style.css`, and a smoke check that the panels and the token meta tag are present for a User and that Helpers get no input box. Screenshots are taken by the orchestrator.

### WP7 — Handoff and brief template (haiku-dev) · 40k

- **Artifact page:** on a `-brief.md` with `status: approved`, show **Send to orchestrator**. It POSTs to `/chat/orchestrator/send` with `take brief <slug>`, where `<slug>` is the file name minus `-brief.md`. For other briefs it's shown disabled, with the reason "approve the brief first".
- **`stages/01-intake/references/brief-template.md`:** add these header lines after `status:`:
  ```
  task: <slug>
  author: agent:client-liaison/haiku
  tier_suggested:
  tier:
  ```
  **This is a workspace contract change and needs the User's approval before it's committed.**
- **`gui/` fallback:** when a brief's header has no `task:`, derive it from the file name, so briefs written before the template change still group correctly.

**Owns:** a WP7 block in `server.py`/`views.py`, the template file, `icmlib.find_brief`/`stage_status` for the fallback, and tests.

### WP8 — Demo wiring, smoke tests, walkthrough (haiku-dev) · 60k

- `gui.sh --demo` sets `ICM_GUI_CLAUDE=tests/fakes/fake_claude.py` unless it's already set. `gui.sh --real-claude` overrides it.
- Add the chat scenarios to `tests/gui/smoke.py`: an end-to-end handoff, reload replay (reconnect with `since=N`), restart resume (a new server process resumes the stored session), and new conversation.
- Add steps 10–14 to `tests/gui/walkthrough.md`:
  - demo chat with the fake;
  - Allow/Deny;
  - handoff;
  - a Helper's read-only view;
  - **one real-CLI step in live mode** on the User's machine.

---

## Risks

| Risk | Mitigation |
|---|---|
| The permission protocol differs from what's expected | WP1 records the real behaviour first; WP3 has a documented fallback (**Allow and retry**). |
| A browser page drives agents with Bash/Write | WP2: Host and Origin checks plus a CSRF token on every POST; bound to localhost only; no permission bypass is ever added. |
| Leaked processes, or threads blocking the server | One process per panel, daemon threads, a lock never held on a blocking read, and crash and restart tests. |
| Orchestrator tokens in the chat | Every turn's result line shows tokens and cost; nothing auto-sends except the explicit handoff button. |
| Tests need the real CLI | Only WP1 and one manual walkthrough step do; everything else uses the fake replayer. |
| Haiku drift on the UI/JS | WP6 is isolated to the layout and static files; the orchestrator reviews screenshots before committing. |

## Token budget (build only)

| WP | Agent | Budget |
|---|---|---|
| WP0 | orchestrator | 5k |
| WP1 | sonnet (+ small Haiku CLI usage) | 80k |
| WP2 | sonnet | 60k |
| WP3 | sonnet | 120k |
| WP4 | haiku | 80k |
| WP5 | haiku | 70k |
| WP6 | haiku | 90k |
| WP7 | haiku | 40k |
| WP8 | haiku | 60k |
| Orchestrator reviews | opus | ~120k |
| **Total** | | **≈0.73M** (check in at 0.6M) |

## Token log

| WP | Budget | Used | Result |
|---|---|---|---|
