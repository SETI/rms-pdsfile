# PR-14 execution topology

Recorded per plan §6.7 ("Record the chosen topology in `critiques/`").

The four-level nesting is collapsed from the top, which §6.7 prescribes as the
fallback ("collapse levels from the **top**, never the bottom"):

| Level | Who |
|---|---|
| Top-level coordinator | the interactive session |
| Phase-4 coordinator | the interactive session (same context) |
| **PR-executor for PR-14** | a dedicated subagent — carries implementation + the §6.6 loop end to end |
| §6.6 adversarial reviewer | one fresh, no-context opus-class subagent **per round**, spawned by the PR-executor |

What is preserved: exactly one PR-executor subagent for this PR, and under it a
new reviewer per round that receives no implementation conversation, no executor
reasoning and no prior round records — only the PR-14 section of the plan, the
Phase-4 preamble, §2, the relevant §6.1/§6.2/§6.6 rules including the
progressive `.cursor/rules` compliance schedule, the exact
`git diff origin/rewrite...HEAD`, and read access to the repo at HEAD.

Rounds are recorded in `critiques/pr-14/round-<k>.md`; gate evidence is in
`critiques/pr-14/validation.md`.
