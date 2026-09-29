# PR-16 — adversarial review round 1

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent (§6.6 step 2), given only
the PR-16 section of the plan, the Phase-5 preamble, §2 ground rules, §6.1/§6.2,
the §6.6 rules including the progressive `.cursor/rules` schedule, the exact
`git diff origin/pr-15-latent-bug-fixes...HEAD`, and read access to the repo at
HEAD, to the consumer repos and to the real holdings. It was told explicitly that
the PR is stacked and that PR-15's changes are out of scope.
**Diff reviewed:** `origin/pr-15-latent-bug-fixes`(`1a5d85c`)`...HEAD`(`3df19d9`)
**Verdict: goal not met** — **1 Major**, 4 Minor, 2 Deferred.

## What the reviewer independently re-ran

Not a paper review: it reproduced the gate evidence rather than reading it off
the record.

| Check | Reviewer's result |
|---|---|
| Byte-for-byte move (its own AST extraction, both trees) | all 10 functions + `FILE_BYTE_UNITS` + `_GLOB_CACHE_SIZE` identical |
| The constant sweep, re-implemented from scratch | reproduced the record's table exactly, including the decorator pass |
| `dump_public_api.py`, both trees via `git archive` | byte-identical, 733,876 bytes each; freeze test passes; the four prohibited files untouched |
| Full-data evidence — re-derived both outcome sets from the raw junit XML with its own reduction script | ns 859 ids, s 558 ids, sets identical on both sides, matching PR-15 §3b |
| Record staleness (junit timestamps vs commit and file mtimes) | runs postdate the last `src/pdsfile/` change |
| Ruff ratchet, every code in `pdsfile.py`'s entry, under the **project** config | parent E701×16 / F841×7 → head 14+2 / 6+1; totals identical, no code droppable |
| F401 / re-export form; `glob` and `math` present in the manifest as `module` | 0 hits, no `noqa`; keeping them bound was required |
| Runtime identity of all re-exported names; a legacy pickle of `pdsfile.pdsfile repair_case` | same objects; pickle still loads |
| Confidentiality grep over all six changed files | clean |
| Consumer smoke A and the three known B failures | same outcome as baseline |
| Packaging (`include = ["pdsfile*"]`), LF, trailing newline | clean |

## Findings

### Major 1 — a reference to the moved code's namespace was not updated

`tests/core/test_pdsfile_path_resolution.py:91` patched `glob` on
`pdsfile.pdsfile`, the module `abspath_for_logical_path` used to live in. After
the move the function resolves `glob` through `pdsfile._path_utils`, so the stub
reached nothing and the last-resort MacOS branch ran against the real
filesystem. The test still passed — on this machine, and only because
`/Library/WebServer/Documents/holdings*` does not exist here. On the platform
that branch exists for it would fail, and the module is marked
`holdings_free` with a docstring promising it reads no real tree.

The reviewer measured it both ways and noted why §6.2 could not catch it: an
outcome-set diff compares pass/fail, so it is structurally blind to a test that
has stopped testing.

**Accepted and fixed** (`37d4246`). The patch now targets
`abspath_for_logical_path.__globals__` — the namespace the function itself
resolves through, whichever module that is — so it stays attached when PR-17 and
later PRs move code again. The now-unused `pdsfile_module` import was dropped.

Verified by simulating the machine the branch exists for, i.e. making the real
`glob.glob` return a hit:

| stub site | result |
|---|---|
| none | resolves to the stub root — the test would fail |
| `pdsfile.pdsfile.glob` (the old site) | resolves to the stub root — the test would fail |
| `abspath_for_logical_path.__globals__` (the new site) | `ValueError: No holdings directory` — passes for the right reason |

The general lesson — an extraction sweep must ask who *patches* a moved module's
globals, not only which globals the code *reads* — is recorded as deferred entry
29, since it applies to every later extraction PR.

### Minor 2 — comments narrated the change instead of stating current state, and one carried a PR number

`pyproject.toml` ("Split off pdsfile.py's entry … PR-23 is where they get
fixed"), `src/pdsfile/pdsfile.py:10` ("Nothing below references glob or math
**any more**") and `:42` ("Path helpers, **extracted to** a private module"). The
reviewer noted that `grep -rn "PR-[0-9]"` over the source and config returned
exactly the one new line, so there was no precedent to lean on.

**Accepted and fixed** (`37d4246`): all three restated as standing facts, PR
reference removed.

### Minor 3 — the record's ruff procedure did not reproduce its own result

The record said `ruff check --isolated --select <code>`. `--isolated` drops
`line-length = 100`, so re-running it as written reports a third code (E501 at 88
columns) for the new module. The committed entry is nonetheless correct: under
the project config the file triggers exactly E701×2 and F841×1.

**Accepted and fixed**: §7 of the record now gives the exact command including
`--line-length 100 --target-version py310`, and says why.

### Minor 4 — the record claimed a provenance the baseline runs did not have

The Environment table said the baseline was measured in a `git worktree` at
`1a5d85c`, and the preamble said every run postdated the extraction commit. Both
were false for the two baseline runs: they were made in the main tree at
`e955a22` (a doc-only descendant whose `src/` is byte-identical to `1a5d85c`)
*before* the extraction. The measurement was sound; the description was not.

**Accepted, and fixed by re-measuring rather than by rewording.** Both baseline
passes were re-run inside the worktree, and both head passes were re-run after
the round-1 fix, so the record's provenance is now literally true. The re-run
also added something the first pass lacked: `coverage.CoverageData.measured_files()`
is now dumped after each pair of passes, so the record *proves* which tree's
source each run imported — the baseline measured the worktree's `pdsfile.py` and
no `_path_utils.py` (that file does not exist at `1a5d85c`), the head runs
measured the main tree's `pdsfile.py` **and** `_path_utils.py`. Without that, a
worktree run leaking into the main tree's editable install would have made the
whole comparison vacuous. Both set diffs are still empty.

### Minor 5 — `pdsfile.pdsfile._GLOB_CACHE_SIZE` stopped resolving

The one name lost from `pdsfile.pdsfile`'s namespace. Nothing breaks — it is
private, absent from the manifest and from the consumer baseline, and has no
other reference in the tree — but the Phase-5 preamble's re-export rule is
written without a public/private qualifier, and the record had resolved that
tension on the executor's own authority.

**Accepted and fixed** (`37d4246`) by taking the preamble literally: it is
carried in the re-export block. That is one line, freeze-invisible either way,
and it upgrades the claim to a checkable invariant — `sorted(vars(pdsfile.pdsfile))`
is now **45 names on each side, none lost and none gained**. The alternative the
reviewer offered (getting the qualifier written into the preamble) would have
been a plan change and therefore a §6.4 hard stop; this avoids it.

## Deferred (recorded, not fixed)

| # | Item |
|---|---|
| 29 | An extraction sweep must also ask which module namespaces the tests *patch* — the direction that produced Major 1. Owner: PR-17 onward |
| 30 | `repair_case` raises `UnboundLocalError` on a single-component path (`repair_case('/', Pds3File)`). Pre-existing, moved byte-for-byte, outside PR-15's enumerated list. Owner: PR-23 or whichever PR next edits the file |

Both appended to `critiques/deferred-observations.md`.

## Rebuttals

**None.** All five findings were accepted and fixed.

## Regeneration

The round's fixes touched `src/pdsfile/pdsfile.py`, so under §6.6 step 5 the
full-data record was regenerated before the next reviewer: both modes on both
trees, after commit `37d4246`. Both set diffs are empty; the API dump is still
byte-identical; `ruff` is clean; the no-holdings run is still 59 passed / 800
skipped; consumer smoke is still 4/4 and 5 ok / the same 3 failures.
