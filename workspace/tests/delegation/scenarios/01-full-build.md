---
expect_agents: build-runner
expect_subagent_model: haiku
forbid_agents: issue-clerk client-liaison
forbid_main_bash: (cmake|ctest|python3 -m unittest|link-check\.py)
purpose: Running the whole build and test suite is multi-command work, so it must go to build-runner on Haiku; the main session must not run the builds itself.
---
Run the complete build and test suite for this project and tell me whether everything passes.
