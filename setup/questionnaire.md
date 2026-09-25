# Project onboarding questionnaire

Run once per project, after `setup/install.sh`. The main session asks these questions and writes the answers into `../icm-project/`. Each answer has exactly one home, shown in brackets.

1. What is the project, and what are its components (folders, repos, subtrees)? [`PROJECT.md`]
2. Which interfaces or formats are implemented in more than one place and must stay in lockstep? [`PROJECT.md`]
3. Which documents are authoritative, and for which subjects? Is there a decision register or issue contract? [`authority.md`]
4. Which GitHub owner, repo and project board number? [`github.env`]
5. What are the title conventions, approved labels, milestones and board fields (with options)? [`github.md`]
6. Is there a register that mirrors issues? Which columns may the clerk change? [`github.md`]
7. What are the build and test commands for each component, and from which directory? Is any of them flaky? [`build.md`] Which tools do those commands need, and which apt packages provide them? [`deps.txt`]
8. What counts as system-level verification, and who grants it? [`authority.md`]
9. Should work be pushed directly to the default branch or through PRs? [`github.md`]
