# PR-28a adversarial review — round 1

Reviewed at `4672e58`. **Nothing Major.** The reviewer byte-diffed the extracted
body against all three base blocks, read the three drivers end to end for
`args`/`logger`/`parser`/`status` liveness, ran ruff (full, and F401/F811/F841),
ran `tests/holdings_maintenance` at head, re-verified all four capture transcripts
by md5, and ran five mutations against the new test. Every finding was about what
the **evidence** covered, not about the extraction.

## Findings and disposition

**1. Minor — the test asserted existence, not attachment. Fixed.** A handler created
and never attached leaves the same file behind; the reviewer built that mutation and
the test passed. The test now runs against a tree nothing has initialized, so the run
logs an error, and asserts both handler files have **content**. Three negative
controls, each reverted:

| mutation of `setup_run` | test |
|---|---|
| pristine | 1 passed |
| `handler_factories[:1]` | 1 failed |
| `make_handler(path)` without `logger.add_handler` | 1 failed |
| the whole `if args.log:` branch dropped | 1 failed |

**2. Minor — two preamble lines are pinned by no test, and entry 150 named neither.
Fixed in the record.** Measured at `356e055`, not asserted: deleting
`spec.pdsfile_cls.set_log_root(args.log)`, and neutering the `if not args.quiet:`
guard, each leave `pytest tests/holdings_maintenance` against the full holdings at
**337 passed**, the same as the unmutated tree. Entry 150 now names both, says the
capture is what covers them, and keeps the `PDS_LOG_ROOT`-through-a-tool gap.

**3. Minor — the capture could not see the handler wiring at all. Fixed in the
harness.** No gate scenario passes `--log` (`grep -c '^ARGV:.*--log'` → 0 of 158),
and the probe recorded only stdout and stderr, so the equivalence case for the four
lines that build the root handlers rested entirely on the new test. The probe now
records the whole log root — every path, and each file's line count — and no longer
initializes first, so the run logs an error and an unattached handler is
distinguishable from an attached one. Base-versus-base is still 0. New mutation
control: `handler_factories[:1]` now moves **4 probe lines**. It is four rather than
five because `run_index_main` writes its per-target handlers into the tool's own log
directory, so `pds4indexshelf`'s root `ERRORS.log` appears either way — recorded in
the validation record.

**4. Minor — `LOGFILES` folds every log file into one set, and §3 did not say so.
Fixed both ways.** The set is necessary — the same 292 lines arrived as 10 files in
one control run and 11 in the next — but it cannot see duplication, which is the
failure `log_paths_for`'s docstring exists to prevent. The record now discloses the
normalization with that measurement, and the record itself carries the **raw line
total** beside the set, which is stable and does show duplication.

**5. Nit — one `expect()` in the checker asserted its own literal. Fixed.** The
`'**158 scenarios**'` needle could not fail on a wrong capture. It is replaced by a
needle for a claim the checker does derive, and the docstring now says why a
run-derived number must not get one.

**6. Nit — the test hard-codes the two log file names.** Addressed by the fix to
finding 1: the assertion is now an exact list, so a third factory added to the spec
fails it rather than passing unnoticed. Reading the names from `SPEC` itself was
rejected — it would import a `Pds4File`-touching module into the test process for no
gain.

**7. Nit — "no test drove a maintenance tool with `--log`" was false. Fixed.**
`test_re_validate.py` does; `re_validate` reaches none of the three drivers. The
record now says "driver-backed". The reviewer also found two more near-copies of the
preamble, in `re_validate.main` and `pdsdependency.main`, the latter re-inlining
`resolve_log_root`'s body and carrying a second `LOGROOT_ENV = 'PDS_LOG_ROOT'`. Out
of scope; recorded as deferred entry 151.
