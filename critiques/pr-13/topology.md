# PR-13 — execution topology

Recorded as §6.7 of `plans/2026-07-25-modernization-plan.md` requires.

Nesting was collapsed from the top, per the §6.7 fallback rule ("collapse levels
from the **top**, never the bottom"):

| Plan role | Who played it |
|---|---|
| Top-level coordinator | the interactive session |
| Phase-3 coordinator | the interactive session (same context) |
| PR-executor for PR-13 | a dedicated subagent — carried the PR end to end |
| §6.6 adversarial reviewer | one fresh, no-context subagent per round, spawned by the PR-executor and never reused |

What remained spawned is exactly what §6.7 requires to remain spawned: one
PR-executor subagent for the PR, and under it a new no-context reviewer per
review round.

Each reviewer received only: the PR-13 section of the plan, the Phase-3 context,
ground rules §2, §6.1/§6.2, the §6.6 progressive-compliance schedule, the exact
diff (`git diff origin/rewrite...HEAD` with the base SHA stated), and read access
to the repo and the holdings roots. No reviewer received the implementation
reasoning or any prior round.

Round records: `round-1.md`, `round-2.md`, … in this directory.
