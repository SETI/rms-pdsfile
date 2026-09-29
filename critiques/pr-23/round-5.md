# PR-23 — adversarial review round 5 (post-revision)

**Date:** 2026-08-03
**Reviewer:** a fifth fresh, no-context opus-class subagent
**Diff reviewed:** `git diff origin/rewrite...HEAD` at `204fd38` (3,317 lines),
with the four corrections isolated as `git diff f59ec05..HEAD` (822 lines)
**Verdict returned:** **`goal not met`** — **2 Major**, 6 Minor, 3 Deferred

Rounds 1–4 ran on the PR as originally executed and closed clean at round 4. The
owner then gave four corrections (see `plans/2026-08-03-pr-23-subplan.md` §12).
This is **one** fresh round over the corrected branch, told what the four
corrections were. It is not a fifth round of the original loop and does not
breach §6.6's hard cap of four: that loop terminated at `0a7dc60`, and the
corrections restart the obligation to review what changed.

Both Majors are in comment and docstring text that **correction 3 itself
introduced**, which is the correction that rewrites comments. Neither is in
behavior. The reviewer's own summary: "Every measurable gate I could re-derive
independently passes — the ruff work, the ratchet shrink, the seven reverts, the
four logging conversions, the API freeze, the MRO, the §6.2 id sets, record
freshness."

## Major findings

### M1 — `src/pdsfile/pdsfile.py:79–81`: correction 3 replaced a true sentence with a false one

The module docstring had read "…and `tests/api/api_manifest.json` — which records
names and kinds, never the defining class — is unchanged." Correction 3 had to
remove the manifest reference, and the replacement generalised it to "…and a
caller cannot tell which module defines any of them."

That is disprovable in one line. The reviewer ran, at head:

```
PdsFile.opus_products.__module__        -> pdsfile._opus
PdsFile.log_path_for_bundle.__module__  -> pdsfile._derived_paths
pdsfile.pdsfile._clean_join.__module__  -> pdsfile._path_utils
```

`__module__`, `__qualname__`, `inspect.getsourcefile` and every traceback name
the defining module — and the paragraph nine lines above in the same docstring
tells the reader that two tests inspect exactly that structure, so the docstring
contradicted itself.

**Resolved** in `374dcdd`. The sentence now says what is true: nothing a caller
imports or calls has moved or been renamed, and the split does show in
`__module__`, `__qualname__` and `__mro__`. Written to the same three lines, so
no line number in `pdsfile.py` moves.

**This is the correction's own rule failing on its first application.** "Restate
in terms of the code" is only safe when the restatement is checked against the
code; a weaker general claim is not automatically a safer one.

### M2 — `tests/api/test_mixin_collisions.py:74`: the PR adds a banned `plans/` reference

Commit `62e3aad` added a code comment ending
"(plans/2026-07-27-addendum-phase5-mixin-base-order.md)". Correction 3's sweep
covered `src/` only, but the rule is about code comments, so it reaches `tests/`
— and the PR writes that very rule into the plan in the same diff.

The reviewer counted 36 further `plans/`/`critiques/` lines across 15 files under
`tests/`; **all are pre-existing** and out of this PR's scope. This one is a `+`
line in this PR's own diff.

**Resolved** in `374dcdd`: the parenthetical is dropped. The MRO claim it
decorated is unchanged and independently verified (`rev3_mro_base.txt` vs
`rev3_mro_work.txt` are identical).

## Minor findings

| # | Finding | Resolution |
|---|---|---|
| m1 | Six of the forty permanent sites carry stale line numbers, in three records — correction 3 shifted lines after the tables were written | **fixed**: re-derived with `ruff` at head. `pdscache.py` −1 (`322→321`, `325→324`, `623→622`), `_derived_paths.py` +1 (`263/280/296 → 264/281/297`), `_index_rows.py` +2 (`162→164`). Corrected in sub-plan §4/§5, `pdsfile_overrides.mdc` (4) and this record. §8's deferred-64 citation now names both the head and the `96e5960` numbering, since entry 64 itself uses the latter |
| m2 | `phase5-validation.md`'s "154 → 33. 121 fixed, 33 permanent." headline and the sub-plan §11 rows are superseded with no forward pointer | **fixed**: explicit supersession markers added at both, pointing at the revision section's 154 → 40 / 114 fixed |
| m3 | Deferred 79's subpackage logging count does not reproduce — the reviewer's sweep gave 98, not 96 | **fixed by disclosure**: the exact AST predicate is now stated in deferred 79 and in this record. The core figure (34, and its per-file split) reproduced exactly for the reviewer; the executor re-derived 96 under three predicate variants including a superset one and could not reach 98, and the two extra sites were not identified, so the subpackage figure is marked ±2. Nothing the entry asks for turns on it |
| m4 | Sub-plan §8's banner count is 34, not 32 | **fixed**: re-measured over indented `#`-only lines in the fifteen modules — `96e5960` `{80: 34, 90: 4, 84: 2}`, head `{80: 40}`. The six-outlier claim and the normalization were both right |
| m5 | Two off-by-one site references in the revision record (`pdscache.py:74`, `pdsviewable.py:6–8`) | **fixed** to `:73` and `:7–9`, plus deferred 79's `pdscache.py:600`/`:611` → `:599`/`:610` |
| m6 | `pyproject.toml:175, :235` still name the frozen surface; flagged for confirmation rather than asserted as a defect | **fixed by making it explicit**: correction 4 exempts `pyproject.toml` until the rewrite finishes, and the plan's PR-37 deliverable now lists the freeze/manifest language alongside `plans/`, `critiques/` and PR numbers as what must go before the merge to `main` |

## Deferred findings

| # | Finding | Disposition |
|---|---|---|
| d1 | The lazy logging form changes one error path: under `PdsLogger` with **no handler**, a value containing a literal `%` makes the eager spelling raise `TypeError` and emit nothing while the lazy form logs correctly. The reviewer reproduced this independently | Already disclosed in sub-plan §12.2 and in this record. Required by correction 2, unreachable for the four actual values, and no text any working spelling emits changes. No new entry |
| d2 | `_path_utils.py:87, :112, :130` prose `IOError` → `OSError` is accurate but required by no ruff rule | Already owned by deferred entry **77** |
| d3 | Deferred **78** (`MemcachedCache.unblock` releases a lock it does not own when no logger is configured) — the reviewer re-derived the four-way truth table and confirms the `SIM102` collapse is exactly equivalent and should stay | Entry 78 stands as written. No change |

## What the reviewer re-derived rather than trusted

- **Violation counts**: 154 at `96e5960`, 40 at head with the template select set
  and no `per-file-ignores` — 41 if the generated, `.gitignore`d `_version.py` is
  in the glob, whose extra hit is setuptools-scm's `RUF022`. Matches the record.
- **The ratchet is a genuine per-file shrink**: 14 entries / 78 slots → 11 / 14,
  and no file's head set contains a code its `96e5960` set did not. **No stale
  entries** — every one of the 14 head slots fires at least once under the
  no-ignores derivation. `grep -rn noqa src/ tests/` → zero.
- **The seven reverts are byte-identical**, checked against `git show
  origin/rewrite:<file>`, whitespace included, plus the two `+` concatenations
  that were never converted. `grep '\[\*' src/pdsfile/*.py` → zero hits.
- **The four logging conversions**: read `pdslogger`'s implementation
  (`_FORMAT_ARG_FINDER = re.compile(r'%[^\(]')`, `log()`, `_format_message`, both
  `_logger_log` paths), then ran an independent probe — 7 values × 2 spellings ×
  2 output paths. Identical on the handler path in every case; identical on the
  no-handler path except the literal-`%` case (d1). Confirmed exactly four
  `UP031` sites were logging and the other nine are exception messages left as
  f-strings.
- **`ruff format` was not run**: `ruff format --check src/pdsfile/*.py` still
  reports 14 files would be reformatted (2,239 changed lines at head, 2,296 at
  base), `ENABLE_RUFF_FORMAT` still defaults false, no `# fmt:` guard anywhere.
- **Behavior equivalence read line by line across the whole diff**, not just the
  corrections: all 20 `UP024`, the 3 `E721`, the 9 `F841` (both effectful RHSs
  kept as `_ = …`, and `_` confirmed unread later in both scopes), `SIM102`/
  `SIM114` short-circuit order at every site, all 3 `SIM103` as `return bool(…)`,
  `B020` in `PdsViewSet.append`, the 3 `RUF015` in `pdsviewable` (all guarded
  non-empty), both `B905`, `A001` `tuple`→`pair`, `SIM118`, `E713`, `UP015`,
  `N806`, `C405`, all 7 `F541`. "Every emitted log string and exception string is
  character-identical." The six commented-out `get_multi` lines (entry 64) are
  untouched.
- **§6.2 evidence**: all four junit files carry `errors="0" failures="0"`; an
  independent `<testcase>` recount matches 892/34 and 558/3 on both sides;
  `setdiff.py` re-run gives 0/0/0 in both modes. Record freshness checked by
  timestamp against the last `src/pdsfile/` commit.
- **§6.1, MRO, non-vacuity, no-holdings, consumer smoke**: manifest dumps
  identical at 733,876 bytes; MRO identical for all three classes;
  `measured_files.txt` lists all fifteen in-scope modules; 92 passed / 800
  skipped; rms-opus 4/4 with 0 failures and rms-viewmaster 5 ok / the same 3
  failures.
- **Scope**: 27 files changed, each required by the sub-plan's commit sequence or
  by one of the four corrections. The `test_mixin_collisions.py` edit is
  authorised by the Phase-5 mixin-base-order addendum, its replacement assertion
  is strictly stronger and non-vacuous, and the test id is unchanged.

**Taken on faith:** the reviewer did not re-run the full-data suite (§6.6 forbids
it) and did not read rounds 1–4. `MemcachedCache` could not be exercised
(`pylibmc` absent), so `pdscache.py`'s `E721`, `RUF015`, `A001` and `UP031` sites
rest on reading plus the executor's differential probe, which the reviewer did
not re-execute.

## Regeneration after this round

M1 changed `src/pdsfile/pdsfile.py`, so §6.6's regeneration rule applies and the
full-data record was regenerated at `374dcdd` rather than carried forward:

| Gate | Result at `374dcdd` |
|---|---|
| §6.2 `--mode ns` | 892 ids both sides, 858 passed / 34 skipped both sides, **0/0/0** |
| §6.2 `--mode s` | 558 ids both sides, 555 passed / 3 skipped both sides, **0/0/0** |
| non-vacuity | all fifteen in-scope modules in `measured_files()` |
| no holdings | 92 passed / 800 skipped; `run-all-checks.sh` green throughout |
| API freeze | fresh dumps, 733,876 bytes each, `diff` **empty** |
| MRO | identical for `PdsFile`, `Pds3File`, `Pds4File` |
| `ruff check src/pdsfile tests scripts` | clean; no-ignores derivation still **40** |
| consumer smoke | A 4/4, 0 failures; B 5 ok / the same 3 failures |

## Round tally, all five rounds

**1 Major from rounds 1–4 plus 2 Major here; 21 Minor from rounds 1–4 plus 6
here.** Of the 30 findings, **six were in code** — four from rounds 1–3 (a
tautological assertion, two one-character idiom mismatches, one comment above the
wrong import) and the two Majors here, both of which are comment/docstring text
introduced by a correction whose whole subject is comment text. **No round found
a defect in the behavior of the code this PR changed.**
