# PR-23 execution topology

Recorded per plan §6.7 ("Record the chosen topology in `critiques/`").

The four-level nesting is collapsed from the top, which §6.7 prescribes as the
fallback ("collapse levels from the **top**, never the bottom"):

| Level | Who |
|---|---|
| Top-level coordinator | the interactive session |
| Phase-5 coordinator | the interactive session (same context) |
| **PR-executor for PR-23** | a dedicated subagent — carries implementation + the §6.6 loop end to end |
| §6.6 adversarial reviewer | one fresh, no-context opus-class subagent **per round**, spawned by the PR-executor |

What is preserved: exactly one PR-executor subagent for this PR, and under it a
new reviewer per round that receives no implementation conversation, no executor
reasoning and no prior round records — only the PR-23 section of the plan, the
Phase-5 preamble, the `2026-08-03` owner-decisions addendum (which is what makes
this a `ruff check`-only PR), §2, §6.1/§6.2 and the §6.6 rules including the
progressive `.cursor/rules` compliance schedule, the exact diff, and read access
to the repo at HEAD and to the real holdings.

**PR-23 is not stacked** (owner, 2026-08-03,
`plans/2026-08-03-addendum-pr23-24-owner-decisions.md` decision 4). It branches
from `rewrite` @ `96e5960` and opens against `rewrite`, so the diff handed to
every reviewer is `git diff origin/rewrite...HEAD` — the whole diff, with no
parent-branch subtraction of the kind PR-16 … PR-22 needed. PR-24 begins only
after this merges.

Rounds are recorded in `critiques/pr-23/round-<k>.md`; gate evidence is in
`critiques/phase5-validation.md`, the phase file, per the Phase-5 preamble.

**Full-data record regeneration.** Every round of this PR is expected to touch
`src/pdsfile/`, so §6.6 step 5's regeneration rule applies by default: the
full-data run and its baseline diff are regenerated before each new reviewer
unless that round changed only records, plans or `pyproject.toml`, and each round
record says which.
