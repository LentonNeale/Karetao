# Onboarding questionnaire

Read this when the user types `setup`. Ask every question below in a single message; the user
answers all of them at once. Then replace each placeholder across the files listed, and scan the
whole workspace for any `{{...}}` still left.

### Q1: How many findings may a review list at most?
- Placeholder: `{{MAX_FINDINGS}}`
- Files: `stages/02-review/CONTEXT.md`, `stages/03-check/CONTEXT.md`
- Default: `12`

## After onboarding

Tell the user which files changed, and point them at CONTEXT.md to start a run.
