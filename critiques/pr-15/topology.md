# PR-15 execution topology

Recorded per plan §6.7 ("Record the chosen topology in `critiques/`").

The four-level nesting is collapsed from the top, which §6.7 prescribes as the
fallback ("collapse levels from the **top**, never the bottom"):

| Level | Who |
|---|---|
| Top-level coordinator | the interactive session |
| Phase-5 coordinator | the interactive session (same context) |
| **PR-executor for PR-15** | a dedicated subagent — carries implementation + the §6.6 loop end to end |
| §6.6 adversarial reviewer | one fresh, no-context opus-class subagent **per round**, spawned by the PR-executor |

What is preserved: exactly one PR-executor subagent for this PR, and under it a
new reviewer per round that receives no implementation conversation, no executor
reasoning and no prior round records — only the PR-15 section of the plan, the
Phase-5 preamble, §2, §6.1/§6.2 and the §6.6 rules including the progressive
`.cursor/rules` compliance schedule, the exact `git diff origin/rewrite...HEAD`,
and read access to the repo at HEAD and to the real holdings.

PR-15 is the base of a stacked series
(`plans/2026-07-26-addendum-phase5-stacked-prs.md`), so its parent branch is
`rewrite` and the diff handed to each reviewer is against `origin/rewrite`.
PR-16 and PR-17 branch off this one in turn.

Rounds are recorded in `critiques/pr-15/round-<k>.md`; gate evidence is in
`critiques/phase5-validation.md` (the phase file, per the Phase-5 preamble —
PR-15 creates it and PR-16/PR-17 append).
