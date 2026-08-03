# PR-18 execution topology

Recorded per plan §6.7 ("Record the chosen topology in `critiques/`").

The four-level nesting is collapsed from the top, which §6.7 prescribes as the
fallback ("collapse levels from the **top**, never the bottom"):

| Level | Who |
|---|---|
| Top-level coordinator | the interactive session |
| Phase-5 coordinator | the interactive session (same context) |
| **PR-executor for PR-18** | a dedicated subagent — carries implementation + the §6.6 loop end to end |
| §6.6 adversarial reviewer | one fresh, no-context opus-class subagent **per round**, spawned by the PR-executor |

What is preserved: exactly one PR-executor subagent for this PR, and under it a
new reviewer per round that receives no implementation conversation, no executor
reasoning and no prior round records — only the PR-18 section of the plan, the
Phase-5 preamble including the mixin mechanics and the alphabetical base-order
rule, §2, §6.1/§6.2 and the §6.6 rules including the progressive `.cursor/rules`
compliance schedule, the exact diff, and read access to the repo at HEAD and to
the real holdings.

PR-18 is the fourth of an eight-deep stack
(`plans/2026-07-27-addendum-phase5-stack-extension.md`, which this PR writes):
it branches off `pr-17-shelves-local-fs`, which branches off `pr-16-path-utils`,
which branches off `pr-15-latent-bug-fixes`, whose base is `rewrite`. Its GitHub
base is `pr-17-shelves-local-fs`, not `rewrite`. The diff handed to every
reviewer is therefore `git diff origin/pr-17-shelves-local-fs...HEAD` — a
reviewer shown the cumulative diff against `rewrite` would flag PR-15's bug
fixes and PR-16's and PR-17's extractions as scope creep and the round would be
wasted. No parent branch is rebased or force-pushed.

Rounds are recorded in `critiques/pr-18/round-<k>.md`; gate evidence is in
`critiques/phase5-validation.md` (the phase file, per the Phase-5 preamble).
