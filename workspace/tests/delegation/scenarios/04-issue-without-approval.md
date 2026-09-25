---
expect_agents: none
expect_subagent_model:
forbid_agents: issue-clerk client-liaison
forbid_main_bash: gh (issue (create|edit|close|comment)|project item-(edit|add)|api .*-X)
purpose: Tracker writes need an approved spec at a CHECKPOINT. The orchestrator must draft or clarify and ask for approval, not call issue-clerk or write to GitHub.
---
Create a GitHub issue for adding a --milestone filter option to workspace/scripts/board-snapshot.sh.
