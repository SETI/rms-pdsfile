# PR-25a adversarial review — round 2

A second fresh reviewer, no prior context, given the diff, both worktrees, the
validation record and round 1's record. It was told what round 1 had already
covered and pointed at what round 1 had explicitly **not** covered: the `--mode s`
pass, a real interactive validation run, `pyroma`/clean-install, the inherited
REST-group ratchet totals, the new test module's own quality, stub fidelity, and
round 1's own additions — which were written after round 1 reviewed and had never
been read by anyone but their author.

Result: **1 Major, 11 Minor, 2 Deferred.** All accepted; one Minor accepted with a
correction to its arithmetic.

---

## Major

### M1 — the misspelling mutation was vacuous, and hid one uncovered site of six

**Finding.** §2.13's mutation row for the misspelling replaced **all six sites at
once**. An all-sites mutation cannot distinguish "all six are covered" from "one is
covered" — and one was not. The `volume_tree` fixture created no `.tar.gz`, so
`glob.glob` returned `[]` in both `archives-` loops and
`re_validate.py:181`, `logger.open('Infoshelf re-validation for', abspath)`, was
never reached. The reviewer measured it directly: reinstating **that site alone**
left **73/73 green**.

The misspelling fix is an output change claimed under ground rule 9 — *"each with
a test"* — and the record asserted the coverage flatly in two places. Two further
single-site mutations were also undetected for the same fixture reason.

**Disposition: accepted, fixed.** This is the round's finding and it is the same
class of error as round 1's M1, one level down: round 1 fixed "the bugs are not
pinned", and this fixes "the *evidence that they are pinned* was itself
aggregated in a way that could not fail".

- The fixture gained `add_tarballs()`, which creates one archive tarball per volume
  type, and the misspelling test calls it.
- That test now asserts on each of the six sites **by name**, and on both tarball
  sites **by path**, so it cannot silently cover four.
- A new test asserts every per-volume-type line names *its own* directory, across
  all five types and all three that have link shelves.
- `scratchpad/mutate2.sh` now mutates **one site at a time**. All six single-site
  mutations fail a test; the table is record §2.14.

One correction to the finding: the reviewer's third undetected mutation,
`tarpaths[0]` → `tarpaths[-1]`, is an **equivalent mutant**, not an uncovered
defect. With one tarball per directory — which the code's own comment states is the
expectation — the two indices select the same element, so no test can distinguish
them and none should. That is recorded in §2.14 rather than papered over.

---

## Minor

| # | Finding | Disposition |
|---|---|---|
| m1 | §7.1 calls both `--help` changes "forced by commonality", but the strings replaced were *near*-copies, not identical, so this is a reword-by-adoption rather than a move | **accepted, fixed.** The record now says so plainly. The rule still licenses it — keeping the old wording while sharing the constant needs a per-tool override parameter, which is exactly what the data-only rule forbids — but "forced" was doing work the evidence did not support |
| m2 | §2.8 still read "Deleted" for `MAX_INFO`, contradicting §2.3 and §11.1, which round 1 updated | **accepted, fixed.** §2.8 now records it as restored, and as the one row in the bug table that is an observation rather than a fix |
| m3 | §5 said the freeze "permits deleting `key_from_log_path` and adding **six** functions" — wrong on both counts after round 1 | **accepted, fixed.** Measured `grep -c '^def '`: 9 at base, 18 at head. Nine added, none removed; all nine named |
| m4 | the plan entry's "eleven bugs … four forced by the move into a function scope" — only two read a module global, and the record says so in bold in §2.4 and §2.5 | **accepted, fixed.** The plan now says ten fixed and two forced, and describes B8 as a finding recorded rather than removed |
| m5 | "18 rendered lines in a default run" is wrong | **accepted, fixed, with my own measurement rather than the reviewer's.** One `open`/`close` pair renders three lines, two carrying the text. Driving `validate_one_volume` over a full five-volume-type tree with tarballs, the six sites fire **28** times. The number is tree-dependent, so the record now states the mechanism and gives the measured figure for a named tree, and says the site is the right unit for the enumeration |
| m6 | `validate_one_volume`'s `(fatal, errors)` return positions were pinned by nothing — `StubLogger.close()` returned `(0,0,0,0)` and the batch test's stub was symmetric | **accepted, fixed.** `StubLogger` takes a `close_result`, defaulting to zeros, and a new test drives `(7, 5, 3, 1)` and asserts `(fatal, errors) == (7, 5)`. Swapping the return positions now fails |
| m7 | `PROGNAME` was pinned by nothing, and it names the log subdirectory rule 2 protects | **accepted, fixed.** The fixture records `log_paths_for`'s keyword arguments; a new test asserts `dir='re-validate'`, the method name and the suffix. A second asserts `main`'s error handler goes to `<log root>/re-validate` |
| m8 | `main()`'s `--quiet` branch and its `if args.log:` handler branch were entered by no test | **accepted, fixed.** `StubBatchLogger` records handlers; two new tests cover both branches both ways |
| m9 | `_common.resolve_log_root`'s environment branch — the reason the function exists — was exercised by no test in the repository | **accepted, fixed.** Three tests, on the helper directly: explicit `--log`, the environment fallback, and neither. Deleting the `os.environ` lookup now fails two tests |
| m10 | `_common.py`'s new docstring said "the three states" and named two; the record repeated it | **accepted, fixed.** Two states: a path, or `None` |
| m11 | `run_interactive` and `run_batch` could ignore their `argv` parameter and read `sys.argv` undetected; round 1's test pinned only the handoff | **accepted, fixed.** Two tests set `sys.argv` to a sentinel and assert the log opens with the passed argv and never the sentinel |

---

## Deferred

- `pyproject.toml:239`'s inline `# x2, x6` broke the file's own `# xN: reason`
  convention and was unreadable without counting. **Fixed rather than deferred** —
  it now reads `# RUF005 x2, UP031 x6`.
- The per-volume-type `logger.open` *paths* could be pointed at the wrong directory
  with the suite green. **Fixed rather than deferred**, by
  `test_every_per_voltype_line_names_its_own_directory` (see M1).

---

## What this round independently confirmed

The reviewer re-derived the numbers record §12.1 flags as **inherited** — the ones
neither I nor round 1 measured — and they hold: REST group **2,258 → 2,241**,
exactly −17; whole tree 2,297 → 2,280; `re_validate.py` 25 → 8; CORE unchanged;
`.mdc`'s `UP031 = 124` correct for the REST scope, with the whole-tree 125's extra
site being `pdscache.py:324` in CORE. It also confirmed the new test module
contributes **zero** violations under the template select set with no
per-file-ignores, so the −17 conceals no new debt.

It closed all four of round 1's stated gaps:

- **`--mode s`, whole tree:** base `5 failed, 930 passed, 34 skipped`; head
  `5 failed, 1003 passed, 34 skipped`. The five failures are a byte-identical list
  and are **pre-existing at base** (`tests/pds4file/test_pds4file_blackbox.py`,
  `uranus_occ_u0_kao_91cm`). Worth recording: my own `--mode s` runs were scoped to
  `tests/pds3file/ tests/rules/pds3/`, per the automated-test script, and that
  scope is green at both commits. The whole-tree `--mode s` failures are outside
  both this PR's diff and that script's scope.
- **A real interactive validation run**, against a disposable tree built from
  `subsets.py`, at base and at head: exit 1 both, log-file tree identical, stderr
  identical, and stdout differing in exactly 22 lines — 20 from the misspelling and
  2 from B4, the latter independently confirming that the leaked `abspath` rendered
  no path at all. **Nothing unattributed.** This is the gate §9 of the brief asked
  for and that I had only run in `--batch-status` and `--help` form.
- **`pyroma` and clean-install:** 10/10, pass; hosted gate 238 passed / 804 skipped
  at head, matching my measurement exactly.

Two of this round's figures are of the tree **as the round found it**, before its
own eleven tests landed: the hosted gate's 238 and the whole-tree `--mode s` head
figure of 1,003 passed. They are left as measured rather than restated, because a
round record should say what that round saw. Record §4 carries the current
figures, and it is the only place that should — the first attempt at this note
quoted "now 249" and "now 1,014", and round 4 then added an eighty-fifth test and
made both stale on the spot.
- **`ruff format` was demonstrably not run:** `ruff format --check` still reports
  all three changed files as "would reformat".

**Stub fidelity**, which no one had checked: `StubLogger.open/info/error(msg,
path=None, **kw)` faithfully models `PdsLogger.open(title, *args, filepath='', …)`
for every call site in `validate_one_volume`, because all six messages are
`%`-free and the real logger therefore re-reads the lone positional as `filepath`.
`StubBatchLogger.add_root(root)` taking one list matches the real `add_root(*roots)`,
which flattens lists. The one substantive infidelity was the all-zero `close()`,
which is m6 and is fixed.

**Not checked by this round:** `--batch-status` against the real holdings and the
synthetic-tree B2 run (§7.2, §7.3) — the reviewer had no log tree to reproduce them
against; `send_email`'s socket half; coverage percentages.
