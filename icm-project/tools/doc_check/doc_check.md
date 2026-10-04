# doc_check

**Purpose.** Deterministic check that the Karetao documentation stays aligned with the project
charter. Standard-library Python 3.12, no third-party packages.

## What it checks

Over `Documentation/**/*.md`, `Arm_Sensor_Hub/Documentation/*.md`,
`RaspberryPi_Sensor_Hub/Documentation/*.md`, `README.md` and `CLAUDE.md`:

1. `term`: out-of-scope terms (EKF, ROS 2, ros2_control, MoveIt, 500 Hz, PL/SIL, CTO, system
   decision authority, differential, trajectory, estimator, guess, assum*) appear only in the
   allowed contexts in `allowed.toml`.
2. `numbers`: `SYSTEM_REQUIREMENTS.md` holds no bare numbers with units (Hz, ms, cm, ...), apart
   from the SPI contract constants (512-byte, 490-byte, CRC-32, 11-bit, 64-bit, 18-byte, 24-byte,
   Mode 0). Values belong in `PARAMETER_REGISTER.md`.
3. `paths`: `docs/project` and `99_ARCHIVE` appear only in `Documentation/00_INDEX.md`,
   `CLAUDE.md` and `Documentation/CHARTER_ALIGNMENT_PLAN.md`.
4. `links`: every relative markdown link resolves to a file or directory (anchors stripped).
5. `prm`: every `PRM-XXX-nn` reference is defined as a `| PRM-` table row in
   `Documentation/06_CONFIGURATION/PARAMETER_REGISTER.md`.

The allow-list is `icm-project/tools/doc_check/allowed.toml`.

## Usage

From the repo root:

```bash
python3 icm-project/tools/doc_check/doc_check.py                 # all checks
python3 icm-project/tools/doc_check/doc_check.py --only links    # term|numbers|paths|links|prm
python3 icm-project/tools/doc_check/doc_check.py --quiet         # exit code only
```

Findings print one per line as `path:line: <check>: <detail>`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | clean |
| 1 | one or more findings |

## Adding an allowed context

Append an entry to `allowed.toml`:

```toml
[[allowed]]
path = "Documentation/xx/FILE.md"   # relative to the repo root; globs allowed
heading = "Future"                  # optional: nearest preceding heading contains this text
terms = ["EKF"]                     # optional: only these terms (globs, spaces ignored)
```

Without `heading` the whole file is allowed; without `terms` every term is. Prefer a heading
scope over a whole-file entry, and add a comment saying why. "differential" is also allowed on
any line that says "deferred" or "non-goal".

## Portal

Listed in `[commands] verify` in `portal.toml`, so the Portal's Verify step runs it.
