# PR-14 — adversarial review round 3

**Date:** 2026-07-26
**Reviewer:** a third fresh opus-class subagent, no development context, no
knowledge of rounds 1-2.
**Input:** identical framing, against the updated
`git diff origin/rewrite...HEAD`.
**Verdict:** `goal met` — **zero Major**, 6 Minor, 6 Deferred.

The reviewer independently re-derived the baseline and the no-holdings
before/after, ran both freeze invocations (including under `-n 1 --dist
loadscope`), re-checked the ratchet, the untouched self-hosted job and
`run-tests-and-opus.yml`, confirmed confidentiality, and spot-checked the
full-data figures against JUnit artifacts on disk (`tests="824" skipped="34"`
and `tests="558" skipped="3"` → 790/34 and 555/3, matching PR-13's baseline).
It confirmed every PR-14 bullet delivered and entries 8/9/12/13 correctly
disposed, with nothing of entry 8 half-landed.

## Minor

### m1 — The anti-vacuous-pass guard only fired when *both* roots were exported

Valid, and the counterexample was reproduced: one root exported and the other
missing gave `no holdings: holdings-free subset only`, 24/800, `✓ SUCCESS` — the
same silent 3% run the guard was added to eliminate. **Fixed:** the guard now
fires when **either** root is present, so a half-configured environment reaches
`_resolve_full` and fails the session by name. Verified:

```text
Running pytest (-n 1; holdings selection is invalid, pytest will report it)...
ERROR: PDSFILE_TEST_HOLDINGS=full requires PDS4_HOLDINGS_DIR to be set
✗ Pytest failed   ✗ FAILURE - 1 check(s) failed
```

### m2 — The shell guard re-derived the resolver's policy and could print a wrong answer

Valid: the shell never consulted `PDSFILE_TEST_DATA_DIR`, so with the dormant
mini flavor resolvable the script would have printed "no holdings" while the
session ran `mini`. **Fixed:** the script now asks `resolve_holdings()` for the
flavor and prints that, so the log cannot disagree with the session. The shell
retains only the script-local *policy* (a root present and no selector ⇒ full),
not a second copy of the resolution. Verified against the dormant path:
resolver `mini` → script prints `holdings: mini`.

### m3 — A comment in `run-all-checks.sh` carried a rationale this PR itself falsifies

Valid: it said `--confcutdir=tests/api` exists because `tests/conftest.py`
"requires holdings env vars to import", untrue since PR-09. **Fixed:** the
comment now gives the real reason (no session options, no holdings resolution, no
preload), matching the one in `tests/api/conftest.py`.

### m4 — The hosted job has no floor on how many tests actually ran

Valid observation, **rebutted as out of scope and deferred.** It asks for a new
enforcement mechanism no PR-14 bullet requests. The specific regression it
imagines — the path predicate silently ceasing to match — is the one round 2
already hardened (both sides of the comparison resolved), and each PR's §6.2
record pins the expected no-holdings counts, so a drop is visible at review.
Recorded as **entry 20** of `critiques/deferred-observations.md`, owned by
PR-37 or any earlier PR that edits the lint job.

### m5 — The script does not reproduce CI, because CI also runs a `--mode s` pass

Valid and worth recording; **fixed by documenting, not by changing the runs.**
Adding a second pass to the script is not available: the self-hosted `s` pass is
pds3-only, and a whole-tree `--mode s` run has five pre-existing pds4 failures
(recorded under "From PR-08" in `critiques/deferred-observations.md`), so the
script cannot simply run `--mode s tests`. And editing the data driver is
forbidden by the PR-14 bullet. The asymmetry is now stated in the script's
`# Environment:` header, at the pytest gate, in deviation (8), and in §8 of
`critiques/pr-14/validation.md`.

### m6 — Dropping the Windows classifier while keeping macOS, on a rationale that fits both

Valid: the commit said the classifier "claimed support that is not tested",
which condemns macOS equally. The real criterion is support, not CI coverage.
**Fixed:** the commit message and deviation (8) now say the package is *not
supported* on Windows, and §8a of the validation file records that macOS is a
supported platform whose matrix entries are commented out rather than deleted,
so it keeps its classifier deliberately.

## Deferred

| # | Item | Owner |
|---|---|---|
| 20 | The hosted job stays green if a regression skips everything | PR-37 or the next PR editing the lint job |
| 21 | `scripts/dump_public_api.py` and `tests/api/test_api_freeze.py` cite the archived v1 plan; both are §6.4-frozen | owner-blessed touch-up of the frozen files |

The reviewer re-raised, as already-recorded deferred items, entries 16-19 from
earlier rounds, and noted that §3.4 prerequisite 3
(`critiques/baselines/consumer-smoke-baseline.md`) is still missing and due
before Phase 5. That is a coordinator/operator task explicitly outside PR-14 —
it is being captured on a separate branch — and is reported upward rather than
actioned here.
