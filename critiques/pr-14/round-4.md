# PR-14 — adversarial review round 4 (scoped)

**Date:** 2026-07-26
**Reviewer:** a fourth fresh opus-class subagent, no development context, no
knowledge of rounds 1-3.
**Scope:** §6.6's fourth-round rule — "confirm the prior round's findings are
resolved; raise only **new Major** findings". The reviewer was given the earlier
findings as claims to disprove, not as a narrative, and was told to verify
against the code rather than the records.
**Verdict:** `goal met` — **zero Major**, all six claims confirmed resolved.

## Part 1 — prior findings

| # | Claim | Status |
|---|---|---|
| 1 | The pytest gate can no longer pass vacuously | **resolved** |
| 2 | The API-freeze test runs with no holdings, without editing the frozen test | **resolved** |
| 3 | `--mode` hardening is complete and behavior-preserving | **resolved** |
| 4 | Deferred entry 8 is re-deferred, not half-landed | **resolved** |
| 5 | No commit message asserts anything the tree contradicts | **resolved** |
| 6 | The documentation-consistency fixes hold | **resolved** |

The reviewer re-derived rather than read, in the cases that matter:

- **(1)** It could not construct a green-but-vacuous environment. It confirmed
  the guard fires on **either** root, that a one-root environment fails with
  `ERROR: PDSFILE_TEST_HOLDINGS=full requires PDS4_HOLDINGS_DIR to be set`, and
  that the printed flavor cannot disagree with the session because the script
  calls `resolve_holdings()` in the same environment after the export. It probed
  the selector-set, empty-selector, nonexistent-root and dormant-`mini` cases;
  each lands on the branch the script prints.
- **(2)** Confirmed with `--trace-config` that the `--confcutdir=tests/api`
  invocation registers **only** `tests/api/conftest.py` (and rejects `--mode`,
  which is what the new comment claims), and then re-ran the whole thing
  **through a symlinked checkout** — still green, so the `resolve()` on both
  sides of the path comparison is load-bearing and works.
- **(3)** Re-enumerated every `--mode` call site and confirmed one consumer of
  `option.mode` repo-wide.
- **(4)** Confirmed no file under `tests/holdings_maintenance/` is in the diff
  and that `run_tool` is the plain form.

Corroborating checks it ran unprompted: frozen artifacts, `tests/golden/`,
`scripts/automated_tests/` and `run-tests-and-opus.yml` all absent from the diff;
ruff clean and the ratchet untouched; pyroma 10/10; no absolute holdings path;
`run-all-checks.sh` still mode `100755`; the new conftest is LF and covered by
`*.py text eol=lf`; and — for the full-data gate, without re-running it — that
`git diff --name-only origin/rewrite -- src/` is empty, so §6.6's staleness rule
is satisfied, with the recorded figures matching PR-13's baseline.

## Part 2 — new Major findings

**None.**

## Noted (non-blocking), and what was done

1. *The `# Environment:` header did not describe the either-root guard or the
   one-root hard failure.* **Fixed** — the header now says so, so `--help` is
   accurate.
2. *`.cursor/rules/pdsfile_overrides.mdc` said the self-hosted matrix "covers the
   two versions in between", understating it.* **Fixed** — it covers all four.
3. *`2>/dev/null || echo 'unresolved'` collapses any probe failure into "holdings
   selection is invalid".* Left as is. The scenario the note imagines — the probe
   failing while pytest runs green — cannot occur: `tests/conftest.py` imports
   `tests.support.holdings` at module level, so an import-time failure there is a
   collection error and the gate fails. A resolver `RuntimeError`, the realistic
   cause, is exactly what the message describes.
4. *`PDSFILE_TEST_DATA_DIR` pointing at a directory without `holdings/` +
   `pds4-holdings/` still yields a silent holdings-free green.* Left as is: those
   are PR-09's semantics on the dormant mini path, which ground rule 3 says to
   leave exactly as merged, and nothing sets that variable.

## Termination

Round 4 returns zero Major and no new un-rebutted Minor. Per §6.6 the loop is
converged and the PR may be opened. Rounds 1-3 are in `round-1.md`, `round-2.md`
and `round-3.md`; gate evidence is in `validation.md`.
