---
expect_agents: none
expect_subagent_model:
forbid_agents: issue-clerk client-liaison build-runner doc-checker
forbid_main_bash:
purpose: A one-file lookup must be answered directly; cold-starting a subagent for it wastes tokens.
---
What is the GH_PROJECT_NUMBER in icm-project/github.env?
