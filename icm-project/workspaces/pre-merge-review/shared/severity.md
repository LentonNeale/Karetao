# Severity

| Severity | Meaning | Example |
|---|---|---|
| `blocker` | Do not merge: it breaks what the brief asked for, loses data, or leaves the project unable to run | A required feature from the brief is missing; a function called but never written |
| `major` | Merge only after a fix: a real defect or a clear gap against the plan or the design | A design point that was accepted is not implemented; an error path that crashes |
| `minor` | Worth fixing, safe to merge: small defects, unclear names, missing tests for a small change | A new function with no test; a misleading comment |
| `note` | Information for the reader, not a defect | A change that goes beyond the brief but is harmless; a follow-up to consider |

Rules: pick the lowest severity that is honest; a finding with no file or line you read is a
`note` at most; never use `blocker` for style.
