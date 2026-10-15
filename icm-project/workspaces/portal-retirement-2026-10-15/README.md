# Portal retirement: migrating Stage 0 and Stage 1 stories to GitHub issues

`gh-commands.sh` creates the milestone `Stage 0 — Foundation`, one issue for each open backlog story of work packages WP9 (Stage 0, 12 stories) and WP10 (Stage 1, 17 stories), and the native issue dependencies between them and the existing open issues. It has **not been run**.

## How to use it

1. Read `gh-commands.sh` and the `body-Bnn.md` files. Each body follows `.github/ISSUE_FRAMEWORK.md` (Context, Scope, Acceptance Criteria, Verification / Evidence, References). Its first line is the origin line, the only place the story id appears.
2. Prerequisites: `gh` logged in as `AIKaretao` with repo scope (`gh auth status`), and the milestones `Stage 1` to `Stage 4` already existing (the script checks `Stage 1 — Fitted encoders` and refuses to run if `Stage 0 — Foundation` already exists). Run it once: `bash gh-commands.sh`. A second run would create duplicates.
3. Each issue number is captured into `ISSUE_Bnn` as it is created, so the dependency edges at the end use the real numbers. A dependency is POSTed with the blocker's database id (`dbid()`), per `docs/agents/issue-tracker.md` ("Blocking").
4. Set the board Status by hand (the comment block at the end of the script): `Ready` for an issue with no open blocker, `Backlog` otherwise. Order within the milestone is the priority; the creation order in the script is only a suggestion.

## Stories, titles, labels, milestones and blockers

Blocked by is read from the story text (see the citations in the script). Story ids appear only here and in each body's origin line.

| Story | Proposed title | Labels | Milestone | Blocked by |
|---|---|---|---|---|
| B55 | Implement shared golden-frame vectors asserted by the C and Python SPI suites | verification, communications | Stage 0 — Foundation | - |
| B56 | Verify the MksServo codec against the MKS manual by restoring its host tests | verification, communications | Stage 0 — Foundation | - |
| B57 | Implement the evidence-record tool with firmware VERSION identity and Pi commit | implementation, verification | Stage 0 — Foundation | - |
| B58 | Update the host-test harness: NDEBUG guard, CAN TX log, deeper I2C scripts, real time_service | verification | Stage 0 — Foundation | - |
| B59 | Remove dead Pi tests and the TIME_SYNC echo decoder | implementation, verification | Stage 0 — Foundation | - |
| B60 | Update CI: doc_check job, lockstep cross-triggers, map upload, warnings as errors, pinned toolchain | implementation | Stage 0 — Foundation | - |
| B61 | Implement one firmware parameter header and one Pi config module mirroring the parameter register | implementation, configuration | Stage 0 — Foundation | - |
| B62 | Update Pi packaging and fix small SPI adapter defects | implementation | Stage 0 — Foundation | B130 |
| B63 | Implement doc_check extensions: matrix trace, retired IDs, section references, index coverage | implementation | Stage 0 — Foundation | - |
| B64 | Remove dead and duplicated firmware code, including the ISR mutex-give async I2C path | implementation | Stage 0 — Foundation | - |
| B130 | Implement the Pi ExchangeSession with a firmware-rules fake and a process-wide Sequencer | implementation, communications | Stage 0 — Foundation | B55 |
| B134 | Implement a build-time check of the main (interrupt) stack depth | implementation | Stage 0 — Foundation | - |
| B128 | Implement the latest-value store that owns sample and feedback ageing and the coherent snapshot copy | implementation, timing | Stage 1 — Fitted encoders | - |
| B65 | Implement GET_SNAPSHOT answered with a correlated SNAPSHOT of sensor and motor records | implementation, communications | Stage 1 — Fitted encoders | B128 |
| B132 | Update the SPI response path so spi_protocol.c validates and builds every response and the service is transport only | implementation, communications | Stage 1 — Fitted encoders | B128, B65 |
| B133 | Implement the AS5600 sample in two bus reads with a typed magnet condition | implementation, timing | Stage 1 — Fitted encoders | B128 |
| B66 | Update the SPI service re-arm, stall and NSS-resync handling | implementation, communications | Stage 1 — Fitted encoders | B132 |
| B67 | Implement DATA_READY armed-then-assert on the STM32 with a fresh-edge wait on the Pi | implementation, communications | Stage 1 — Fitted encoders | B66, B132 |
| B68 | Implement the Pi snapshot logger and probe output for Stage 1 evidence | implementation, communications | Stage 1 — Fitted encoders | B65, B130 |
| B69 | Update sequence seeding across processes and add a host resync rule | implementation, communications | Stage 1 — Fitted encoders | B130 |
| B70 | Define the GET request payload and padding rule and apply them on both sides | design, implementation, communications | Stage 1 — Fitted encoders | B132 |
| B71 | Implement the snapshot flags bit and SPI transport counters | implementation, communications | Stage 1 — Fitted encoders | B65 |
| B73 | Implement sensor path hardening: bus recovery, bring-up retry, timeout diagnostics | implementation | Stage 1 — Fitted encoders | B133 |
| B74 | Update the sensor policy: magnet warnings, processed-angle source, sweep counter | implementation, configuration | Stage 1 — Fitted encoders | B133 |
| B77 | Update ENCODER_BENCH_PROCEDURE to cover SYS-ENC-002 and link it from the index and matrix | verification | Stage 1 — Fitted encoders | - |
| B78 | Remove data_ready_analysis.py and its unbased verdicts | implementation | Stage 1 — Fitted encoders | - |

## Edges to and from existing issues

Graph v1 among the existing open issues: 18 edges (see the script). New issues block existing ones: #66 by B128 and B132; #42 by B55, B130 and B132; #63 by B132; #61 by B55. Stories in later work packages (B81, B88, B89, B93, B94, B100, B108, B111, B126, B131) are listed as comments marked "pending migration".

## Points for review

- B68 mentions decision SD-09 (the Pi owns measurement history) only as context. It is a settled decision, so the title has no `[SD-xx]` prefix.

Changes after Lenton's review (2026-10-15 evening): B72, B75 and B76 are not created; #66 already carries them and gets an origin line. Edge #63 <- B55 added (named in #63's own criteria).
