# Onboarding questionnaire

Read this when the user types `setup`. Ask every question below in a single message; the user
answers all of them at once. Then replace each placeholder across the files listed, and scan the
whole workspace for any `{{...}}` still left.

### Q1: How many places may the locate stage list at most?
- Placeholder: `{{MAX_LOCATIONS}}`
- Files: `stages/01-locate/CONTEXT.md`
- Default: `8`

### Q2: How many lines make a file too long to read whole?
- Placeholder: `{{WHOLE_FILE_LINES}}`
- Files: `stages/01-locate/CONTEXT.md`, `stages/02-change/CONTEXT.md`
- Default: `400`

## After onboarding

Tell the user which files changed, and point them at CONTEXT.md to start a run.
