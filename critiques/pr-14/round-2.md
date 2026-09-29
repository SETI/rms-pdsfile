# PR-14 — adversarial review round 2

**Date:** 2026-07-26
**Reviewer:** a second fresh opus-class subagent, no development context, no
knowledge of round 1.
**Input:** identical framing to round 1, against the updated
`git diff origin/rewrite...HEAD`.
**Verdict:** `goal not met` (1 Major, 6 Minor, 4 Deferred).

The reviewer independently reproduced the baseline (a worktree at
`origin/rewrite`), the no-holdings before/after, both freeze invocations, the
`--mode NS` usage error, the ratchet, the untouched self-hosted job, and the
confidentiality check — all confirmed. It additionally probed two stock-runner
hazards this executor had not: pyroma under a tagless/shallow
`setuptools_scm` version (exit 0, still 10/10) and the clean-install gate with no
holdings env vars set (passes — a condition it had never run in before).

## Major

### M1 — The newly-enabled pytest gate passes vacuously on a data machine

Valid, and the most important finding of the loop. §3.4 tells the operator to
export `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` and nothing more, but
`tests/support/holdings.py::resolve_holdings` only consults those two when
`PDSFILE_TEST_HOLDINGS=full`. So the exact environment §3.4 describes produced
**24 passed / 800 skipped** and a green `✓ SUCCESS` — 3% of the suite, reported
as a pass — which contradicts the deliverable's own wording ("with holdings env
vars it runs the full suite"). The failure mode did not exist before this PR
(`ENABLE_PYTEST=false`), and §2 requires a local full-data run after every
Phase 5/6 PR, which is next.

**Fixed.** `scripts/run-all-checks.sh` now selects `PDSFILE_TEST_HOLDINGS=full`
for its own invocation when both roots are exported and no selector is set, and
prints which run it is doing in every case. An explicit selector still wins;
`PDSFILE_TEST_DATA_DIR` is never set, so the mini flavor stays dormant (ground
rule 3); `tests/support/holdings.py` is untouched — the script uses PR-09's
selector exactly as `scripts/automated_tests/pdsfile_main_test.sh` already does.
The holdings variables are now documented in the script's `# Environment:`
header, so `--help` says so too.

Verified across all three environments (§3a of `critiques/pr-14/validation.md`):
both-roots-no-selector → `holdings: full`, 790/34; explicit selector →
`holdings: full`, 790/34; nothing set → `no holdings: holdings-free subset only`,
24/800.

## Minor

### m1 — The script runs `tests/`; the data driver runs a hand-maintained path list

**Rebutted.** The drift is real but predates this PR, and closing it means
editing `scripts/automated_tests/pdsfile_main_test.sh`, which the PR-14 bullet
explicitly forbids ("Keep the self-hosted full-data matrix exactly as it is") —
the reviewer offered this rebuttal itself. It is also the direction that matters
least: the whole-tree invocation this PR adds is precisely what would *catch* a
new top-level test directory the driver's list missed, and it now runs on every
PR (hosted, no holdings) and locally with holdings. Recorded here rather than
acted on.

### m2 — The plan's gate table and enabled-set line went stale

Valid and in scope: PR-14 is the PR that flips those gates, and the table's
`**Active** (PR-xx)` pattern shows it is maintained as gates land. Fixed —
`plans/2026-07-25-modernization-plan.md` now marks the hosted lint job
`**Active** (PR-14)` and lists pytest in the enabled set.

### m3 — `tests/api/conftest.py` marks a whole directory on a comment-only invariant

Partly valid. **Rebutted on the mechanism, fixed on the wording.** The suggested
alternative — per-module `pytestmark` — cannot be applied to the one module that
matters, because §6.4 forbids editing `tests/api/test_api_freeze.py`. And the
failure mode of the directory rule is the good one: a future test in
`tests/api/` that does need holdings **fails loudly on the first no-holdings
run** rather than silently skipping. The conftest now states that as a rule of
the directory, with the consequence spelled out.

### m4 — `item.path` compared unresolved

Valid, and the failure mode is the bad kind: through a symlinked checkout the
comparison would quietly stop matching and the freeze test would go back to
skipping on the hosted runner — lost coverage, not a red build. **Fixed:** both
sides are resolved.

### m5 — A commit message asserts something the final tree contradicts

Valid. Commit `626892a` described a change to deviation (7) that round 1 then
reverted. **Fixed:** the branch was re-committed from `origin/rewrite` so every
message describes the tree that is actually being proposed.

### m6 — The script header's "Code:" list omitted the clean-install gate

Valid, pre-existing, one word. **Fixed.**

## Deferred

| # | Item | Owner |
|---|---|---|
| 19 | `[tool.pytest.ini_options]` declares no `testpaths` (pre-existing, PR-03) | the `tests/pds{3,4}file/` restructure PR |

The reviewer also noted that the self-hosted leg runs neither `ruff` nor `pyroma`
nor a standalone api-freeze invocation, so "exact correspondence" holds at the
workflow level (the union of the two jobs) rather than per job. That is what the
PR-14 bullet asks for and is recorded in §8 of the validation file. It agreed the
"first proof comes from CI" statement is honest rather than hand-waving, and
re-confirmed the disposition of entries 8, 9, 12 and 13, including that nothing
of entry 8 is half-landed (`tests/holdings_maintenance/support.py` is not in the
diff).

On the round-1 rebuttal about the 291 unmarked data-suite tests, the reviewer
called reason 1 the weakest of the four and reasons 2 and 3 decisive. Noted; the
reasons are left as recorded, since the rebuttal does not rest on reason 1.
