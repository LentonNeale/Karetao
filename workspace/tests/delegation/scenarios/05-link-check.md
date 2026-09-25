---
expect_agents: none
expect_subagent_model:
forbid_agents: issue-clerk client-liaison doc-checker build-runner
forbid_main_bash: python3 +(-|/tmp/)
purpose: Mechanical checks that a script already does must be run directly ("scripts before models"), not delegated and not re-implemented.
---
Check the documentation for broken links, and tell me whether every document named in icm-project/authority.md exists.
