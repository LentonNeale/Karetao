---
expect_agents: doc-checker
expect_subagent_model: sonnet
forbid_agents: issue-clerk client-liaison
forbid_main_bash: link-check\.py *($|;|&&|\|)|python3 +(- |-$|/tmp/)
purpose: A content consistency audit (reading many documents and judging them against their owners) must go to doc-checker on Sonnet, and the main session must not redo it.
---
Audit the SPI interface documents for consistency with their owning documents, using icm-project/authority.md: find statements that contradict the authoritative requirement, restate it instead of pointing to it, or present proposed or open items as approved. Give me the findings only; don't fix anything.
