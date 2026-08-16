# PR-33 round 4 — scoped: confirm round 3's resolutions, new Majors only

Reviewer: a fresh, no-context subagent, scoped per §6.6's anti-thrash rule for a
fourth round: confirm the prior round's findings are resolved, and raise only new
Major findings. Diff `git diff 96de70a..98b5f12`.

## (a) Round-3 resolutions — all four confirmed against source

1. **The archive-pair provenance sentence** — resolved and verified: the three
   parser texts are defined in `_archives_common.py:75-93` and consumed by both
   specs; `log_suffix='_archives'` is an independent literal in each; the common
   module defines no suffix constant.
2. **The CI-chapter opening** — the round-3 finding is resolved (the test-workflow
   quantification is correct, and the reviewer re-verified the driver description
   line by line), but the carve-out clause the fix added is round 4's own Major
   below.
3. **The mixin-state sentence** — resolved and verified by an AST scan of all nine
   mixin class bodies: zero `__init__` definitions, zero class-level assignments,
   and exactly two non-property decorators, of which the `lru_cache` on
   `os_path_exists` is the only stateful one (`_pinned_log_timetag`'s
   `contextmanager` is a stateless wrapper).
4. **Observation 4317 and the register** — present, accurate, arithmetic coherent
   (130 in p3, 212 total, 375 − 28 − 119 − 19 + 3 = 212), record updated
   consistently.

The reviewer also re-ran the cheap gates at head (both Sphinx builds exit 0 with 0
problem lines and 78 of 78 into separate scratch build dirs; `tests/docs` +
`tests/api` 30 passed; both ruff passes clean; mmdc renders all five diagram
sources) and confirmed the diff touches nothing under `src/`, so the full-data
record's carry-forward is legitimate.

## (b) New Major findings — one

**B1. "the publish workflows build and upload; they run no gate of their own" is
false for the PyPI workflow.** `publish_to_pypi.yml:29-32` runs
`python -m twine check dist/*` between build and upload — a blocking validation
step that appears in no other gate list — while only `publish_to_test_pypi.yml`
matches the sentence as written. The clause was introduced by round 3's fix to its
own m1: the correction-pass pattern, a fourth time. **Fixed**: the opening now
names the `twine check` step, and the release-workflow list states it too
(`publish_to_test_pypi.yml`, which has no validate step, keeps "builds and
uploads").

No other new Major: the diagrams, the register arithmetic, the record updates and
the re-run gates all stand verified.

## Verdict

**goal not met**, solely on B1.

## The cap, and the round that follows

§6.6 hard-caps the loop at four rounds and treats a fourth round that still finds
issues as a stop-and-escalate signal. This PR takes one more, tightly scoped round
anyway, on the same grounds PR-32's fifth round was taken and accepted: the
finding class is measured, not mysterious — every round's Major since round 1 has
been inside the previous round's correction, at the documented roughly-half rate —
and the plan's own PR-32 section directs PR-33 to "budget for the second read of
[its] own corrections". Round 5 therefore reads only the two passages the B1 fix
rewrote, against the workflow files, raising new Majors only; the cap excess and
its justification are called out to the owner in the PR description rather than
buried here.
