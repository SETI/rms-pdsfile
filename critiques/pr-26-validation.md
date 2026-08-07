# PR-26 validation — checksums and infoshelf onto the core

Base `56b8823` (`rewrite` head). Every number below was measured at this PR's head
unless it is marked inherited. Holdings root for every data run:
`$PDS3_HOLDINGS_DIR` / `$PDS4_HOLDINGS_DIR`, with `PDSFILE_TEST_HOLDINGS=full`.
Every command was run with `PYTHONPATH=$PWD/src` inside the PR-26 worktree, and
the tree under measurement was proved rather than assumed (see §8).

## 1. What changed

Four commits, in this order:

1. `refactor: split _common into per-family modules` — `_common.py`'s archive
   section and its checksum/shelf section move out verbatim into
   `_archives_common.py` and `_shelf_common.py`. No behavior.
2. `refactor: migrate the checksums and infoshelf pairs onto the core` — the four
   tools' hand-rolled `main()` becomes `SPEC` + `TASKS` + a two-line `main()`.
3. `fix: the info shelf comparison, and how a chained run is executed` — six
   defects, each with a test.
4. `chore: pdsinfoshelf no longer needs the RUF059 ignore` — ratchet shrink.

## 2. The plan's bug list, verified at this PR's base before anything was touched

Every item was reproduced at `56b8823` first. The brief's table was correct in
every particular; two items were added to it.

| Item | Verified at base | Evidence |
|---|---|---|
| `LOGDIRS` shadowing | Already fixed by PR-25 | `_shelf_common.LOGDIRS` + `set_log_dirs()`; nothing owed |
| `checksum1 != checksum1` | **Live**, `pds3/pdsinfoshelf.py:392` | §2.1 |
| `abs(modtime1 != modtime2) > 1` | **Live**, `pds3/pdsinfoshelf.py:387` | §2.1 |
| Child count message `(count1, count1)` | **Live**, `pds3/pdsinfoshelf.py:384` | §2.2 |
| `os.system` → `subprocess.run` | **Live**, `pds3/pdschecksums.py:853` | §2.3 |
| `proceed` can be unbound | **New finding**, `pds3/pdschecksums.py:850` | §2.4 |

### 2.1 The two dead branches, shown together

At base, a `pdsinfoshelf --validate` run over a tree in which one file's **content
and modification time had both been changed** reported no problem at all:

```
$ pdsinfoshelf --validate <holdings>/volumes/HSTNx_xxxx/HSTN0_7176      # at 56b8823
... | INFO | File info matches: volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL
... | INFO | File info matches: volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01
...
exit 0, 0 ERROR messages
```

`N4BI01L4Q.LBL` is the file that was corrupted. Both branches that should have
caught it are dead: `checksum1 != checksum1` is always False, and `abs()` of a
bool is 0 or 1 and never `> 1`. The same run under pds4 reports four
`Modification time mismatch` errors and exits 1, which is why the two flavors
disagreed.

### 2.2 The child-count message

`logger.error('Child count mismatch %d %d' % (count1, count1), key)` — the branch
is right, the message names one side twice. PR-13 pinned the resulting line as
`Child count mismatch 7 7`; it now reads `Child count mismatch 7 6`, seven files
on disk against the six the shelf knows.

### 2.3 `os.system` versus `subprocess.run` — two differences, both measured

The plan calls this a modernization. It is not only that. Measured directly:

```
child exit 0: os.system->    0 (sys.exit gives 0); subprocess.run->0
child exit 1: os.system->  256 (sys.exit gives 0); subprocess.run->1
child exit 2: os.system->  512 (sys.exit gives 0); subprocess.run->2
child exit 7: os.system-> 1792 (sys.exit gives 0); subprocess.run->7
```

`os.system` returns a **wait status**, the exit code shifted left by eight.
`sys.exit()` truncates to the low byte, so **every** nonzero exit code of a
chained `pdsinfoshelf` run was reported by `pdschecksums` as success.

Second, `' '.join(new_list)` hands the command to a shell with no quoting:

```
argv                     = [python, exiter.py, '1', '/tmp/pr26 space dir/x']
os.system(' '.join(...)) -> child argv ['1', '/tmp/pr26', 'space', 'dir/x']
subprocess.run(argv)     -> child argv ['1', '/tmp/pr26 space dir/x']
```

A holdings path containing a space is word-split. That is not hypothetical here:
deferred observation 107 records that this machine's holdings root resolves to a
path containing three spaces.

So this is **two** behavior changes, not a cosmetic modernization, and both are
enumerated in §4 and pinned by tests.

### 2.4 A sixth defect: `proceed` can be unbound

`pdschecksums`/`pds4checksums` assign `proceed` only inside the target loop, then
read it after. A command-line path that expands to no targets — an empty volume
set directory, which is a real state — leaves it unbound:

```
$ pdschecksums --validate <holdings>/volumes/EMPTYx_xxxx                 # at 56b8823
UnboundLocalError: cannot access local variable 'proceed' where it is not
associated with a value            (pdschecksums.py:850)
exit 1
```

`pdsinfoshelf` on the same input exits 0 with no traceback. Fixed by initializing
the result before the loop; the run now finishes quietly, as the infoshelf tools
already did.

## 3. The modtime comparison — the owner's ruling, implemented

Implemented once, in `_shelf_common.modtimes_agree()`, and called by both flavors.
It parses both times and allows a one-second difference, which is the convention
`_archives_common.validate_tuples` already applies to epoch seconds for the same
reason.

**The two traps in the brief, both measured rather than assumed:**

- **Python 3.10.** The stamps are space-separated, not `T`-separated. Measured on
  a real CPython 3.10.20 (`uv run --python 3.10`), not inferred from 3.12:
  `datetime.fromisoformat('2020-09-13 12:26:40.000000')` parses. `''` raises
  `ValueError` there too, which is why the helper falls back to string equality —
  `''` is the empty-directory sentinel.
- **The sidecars.** Nothing about what is *written* changed. The `.py` sidecar
  goldens are byte-identical (`tests/holdings_maintenance` is green, including
  `test_initialize_writes_the_expected_sidecar`, which compares the sidecar to its
  committed golden).

**The report still renders whole seconds.** The truncation was dropped from the
*comparison* only; the message keeps its original second-resolution wording. That
is safe rather than merely conservative: if two times are more than a second
apart their whole seconds must differ, so the message can never print the same
string twice. `test_every_reported_mismatch_renders_two_different_seconds` pins
it over a grid of offsets and separations.

**The pds4 verdict change, enumerated.** Both flavors truncated before comparing,
so pds4's working comparison was string equality on quantized values. Replacing
it changes pds4's results too:

- Nothing that passes today starts failing. If `floor(t1) == floor(t2)` then both
  lie in `[n, n+1)` so `|t1 - t2| < 1`; contrapositive, `|t1 - t2| > 1` forces
  the floors to differ. Every mismatch the new comparison reports, truncation
  reported too — the new mismatch set is a **strict subset** of the old.
- What changes: a pair less than a second apart that straddles a second boundary
  was reported as a mismatch and is not any more. `12:26:40.999999` versus
  `12:26:41.000001` — two microseconds apart, reported as different by
  truncation. That class is exactly the false positives.

A mutation probe confirms the new tests discriminate rather than merely pass:

| implementation | pinned cases it gets wrong |
|---|---|
| new (`modtimes_agree`) | 0 of 7 |
| old pds4 (truncated string equality) | 2 of 7 — the inclusive tolerance, and the boundary straddle |
| old pds3 (`abs(bool) > 1`) | 3 of 7 — over-tolerance, a minute apart, sentinel vs a real time |

## 4. Behavior changes, enumerated

Five, all of them intended, each with a test that fails at base and passes here.

| # | Change | Tools | Test |
|---|---|---|---|
| 1 | A content change is reported again (`checksum1 != checksum2`) | pds3 infoshelf | `test_corruption_is_detected_and_repaired[label_byte0_same_size]` |
| 2 | A modification-time change is reported again | pds3 infoshelf | `test_corruption_is_detected_and_repaired[label_mtime_plus_100]`, `test_modification_time_mismatch_reports_both_times` |
| 3 | The child-count message names both counts | pds3 infoshelf | `test_update_picks_up_a_new_file` |
| 4 | A chained run's exit code arrives intact, and its arguments are not word-split | pds3 checksums | `test_infoshelf_chain_reports_the_chained_run_exit_code`, `test_infoshelf_chain_passes_a_path_containing_spaces` |
| 5 | A path expanding to no targets finishes instead of raising | both checksums | `test_no_targets_leaves_no_unbound_state` |

And one that is a **relaxation on the flavor the plan describes as already
correct**, called out separately because the plan does not mention it:

| # | Change | Tools | Test |
|---|---|---|---|
| 6 | Two modification times under a second apart that straddle a second boundary no longer count as a mismatch | **pds4** infoshelf as well as pds3 | `test_pds4_infoshelf.py::test_modification_time_within_one_second_agrees`, plus `test_a_boundary_straddle_is_not_a_mismatch` |

**Change 6 is pinned on the pds4 tool deliberately, and that placement matters.**
The pds3 twin of that test cannot discriminate: pds3's comparison was dead at base,
so *no* modification-time mismatch was ever reported there and an assertion that
none is reported passes at base too. pds4 is the flavor whose truncation worked, so
it is the flavor where the change is visible. Run against base source, the pds4
test fails with exactly the false positive this change removes:

```
ERROR | Modification time mismatch "2020-09-13 12:28:31" "2020-09-13 12:28:30"
```

Two times 0.6 s apart, on opposite sides of a whole second. The pds3 test is kept
as a "still agrees" check and is marked below as non-discriminating rather than
being counted as evidence.

### Log and output text — every changed line

Two lines change. Both are forced by the migration in the sense the Phase 6 rule
requires: keeping either would need a flag whose only job is to reproduce one
side's wording.

1. **Traceback frames inside a tool's log and on stderr.** A traceback names the
   frames on the stack, and the driver is now a shared frame. `pdschecksums.py,
   in main / proceed = initialize(pdsdir, selection)` becomes
   `_shelf_common.py, in run_selection_main / proceed = tasks[task](pdsdir,
   selection)`, with the tool's own `main()` frame naming
   `result = _shelf_common.run_selection_main(SPEC, TASKS, sys.argv)`. Identical in
   kind to the one PR-25 enumerated for the archive tools. **Traceback file names
   were deliberately not normalized** in the comparison below, which is what makes
   this visible rather than hidden; only line numbers were.
2. **`print(sys.exc_info()[2])` is gone from both infoshelf tools.** It printed
   the repr of a traceback object — `<traceback object at 0x7f...>` — to stdout,
   next to the traceback the interpreter prints anyway. It occurred once in the
   122-record transcript below, in `pds3/archives/pdsinfoshelf/flag-initialize`.
   Keeping it would mean a flag on the shared driver whose only effect is to print
   a memory address for two of the four tools.

Nothing else moved: **all four tools' `--help` output is byte-identical** at base
and at head (3236, 3038, 3242 and 3044 characters), which is the check that the
shared help constants reproduce the hand-copied originals exactly.

## 5. The `_common.py` split — the measurement that triggered it

Deferred entry 98 fixed the structure and the trigger: one file with a section per
family, until the first family whose extraction takes `_common.py` past deviation
(3)'s 1,000-line limit, which splits it, the driver staying put.

**The measurement crossed, so the split happened.** With the shared checksum and
infoshelf code added and before any split:

```
$ wc -l src/pdsfile/holdings_maintenance/_common.py
1081 src/pdsfile/holdings_maintenance/_common.py
```

1,081 against a limit of 1,000. Deviation (3) names the module-length waiver list
explicitly and says the maintenance tools are **not** on it.

After the split:

```
$ wc -l src/pdsfile/holdings_maintenance/_common.py \
        src/pdsfile/holdings_maintenance/_archives_common.py \
        src/pdsfile/holdings_maintenance/_shelf_common.py
  339 _common.py
  241 _archives_common.py
  529 _shelf_common.py
 1109 total
```

`_common.py` keeps what every family shares — `ToolSpec`, `TASK_FLAGS`, the help
constants, `resolve_log_root`, `build_arg_parser`, `log_paths_for` and `run_main`.
`reject_checksum_and_archive_paths` went with the archive family, its only caller.

**The brief's projection was wrong in size and right in conclusion.** It projected
~312 and ~325 shared lines from the two pairs (~1,318 total) by applying the
archive family's 18.5% extraction rate to the pairs' line counts. The actual
shared addition was ~400 lines, not ~637: these pairs are mostly domain functions
(`generate_checksums`, `read_checksums`, `write_checksums`, `validate_pairs`,
`generate_infodict`, …) that stay in their tool modules, so a smaller fraction of
them is extractable than the archive pair's. The conclusion held anyway — 1,081
crosses 1,000 — but the projection should not be reused for PR-27 without
re-deriving it.

## 6. Gates

| Gate | Result |
|---|---|
| Full-data `--mode ns` | see §7 |
| Full-data `--mode s` | see §7 |
| `run-all-checks.sh -c -s`, no holdings env vars | **All checks passed** (ruff, pytest 264 passed / 812 skipped, pyroma 10/10, API freeze, clean-install) |
| `tests/api` | 26 passed |
| The four frozen files | byte-identical to `56b8823` (§8) |
| `ruff check .` (configured) | All checks passed |
| `ruff check --preview --select E111,E112,E113 .` | All checks passed |
| Ratchet arithmetic | §9 |
| Four-tool run at base and head | §7 |
| `bandit`/`vulture` | `ENABLE_*=false` and not installed. **Not run.** Nothing is claimed about them. |

The hosted lint/no-holdings figure moved from the baseline of 250 passed / 804
skipped, which was **re-measured at base and confirmed exactly** rather than
inherited. Head is 264 passed / 812 skipped, and the whole difference is
accounted for: `test_shelf_common.py` adds 14 holdings-free tests (+14 passed),
and eight new holdings-dependent tests skip without a tree (+8 skipped) — four in
`test_pds3_checksums.py`, two in `test_pds3_infoshelf.py`, one in
`test_pds4_checksums.py` and one in `test_pds4_infoshelf.py`.

## 7. Data runs

### 7.1 Full-data suite

Command lines exactly as `scripts/automated_tests/pdsfile_main_test.sh` runs them,
plus `-rA --junitxml`, at base and at head, with `PYTHONPATH=$PWD/src`:

```
pytest tests/api/ tests/core/ tests/holdings_maintenance/ tests/pds3file/ \
       tests/rules/pds3/ tests/pds4file/ tests/rules/pds4/ --mode ns -rA --junitxml=…
pytest tests/pds3file/ tests/rules/pds3/ --mode s -rA --junitxml=…
```

| | base | head |
|---|---|---|
| `--mode ns` | 1,054 ids — 1,020 passed, 34 skipped | 1,074 ids — 1,040 passed, 34 skipped |
| `--mode s` | 558 ids — 555 passed, 3 skipped | 558 ids — 555 passed, 3 skipped |

The comparison is of the **per-test id-to-outcome map**, not of counts:

- **`--mode s`: identical.** Same 558 ids, same outcome for every one. No id added,
  none removed, none changed.
- **`--mode ns`: no outcome changed for any id present in both runs — zero.** A
  newly-passing test would have been as much of a flag as a newly-failing one;
  there were neither.
- **2 ids removed**, both deliberate:
  `test_pds3_infoshelf::test_known_undetected_corruption[label_byte0_same_size]`
  and `[label_mtime_plus_100]`. These are the two PR-13 wrote to be inverted; the
  same two corruptions now appear as
  `test_corruption_is_detected_and_repaired[…]`, asserting the opposite.
- **22 ids added**, all passing: 14 in the new `test_shelf_common.py`, 4 chain and
  no-target tests in `test_pds3_checksums.py`, 4 in `test_pds3_infoshelf.py` (the
  two re-homed corruptions plus two new modification-time tests).

The base figures match the ones the brief inherited (1,054 and 558) exactly.

### 7.2 Real runs of all four tools

122 records — every task of every one of the four tools against real holdings, at
base and at head: `--initialize`, a second `--initialize`, `--validate` clean,
`--validate` over a corrupted file, `--repair`, `--validate` again, a cancelled
`--repair`, `--update`, a cancelled `--update`, `--reinitialize`, two task flags
at once, a unit-set target, an invalid file target, `--help`, a missing task, a
non-holdings path, a checksums path, a nonexistent path, `--archives` in both
positions, an archive file as a single-file selection, and the `--infoshelf`
chain in four states. Log files and text artifacts were captured too.

Normalization: temporary paths, wall-clock timestamps, log-file time tags, elapsed
times, and traceback **line numbers**. Traceback **file names** were deliberately
left alone.

**A base-versus-base control was run first**, because a transcript that differs
from itself cannot attribute anything. The first control found 9 of 122 records
differing — all of them `LOGFILES` records. That is not a code difference: a log
file's name carries a one-second time tag, so which file a given line lands in
depends on which second a run happened to start, and the records accumulate across
a scenario. Rather than argue that noise away, the comparison was made
deterministic: `LOGFILES` records are compared as the **set of log lines**, which
removes the "which file" nondeterminism while still comparing every line.
`SCENARIO` and `ARTIFACTS` records are compared verbatim.

Under that comparison the control is clean, which is what licenses attributing
everything else:

```
base run 1 vs base run 2 :   0 of 122 records differ
base      vs head        :  18 of 122 records differ  (SCENARIO 14, LOGFILES 4,
                                                       ARTIFACTS 0)
```

**Every changed line, attributed — 170 lines, none unattributed:**

| lines | cause |
|---|---|
| 98 | traceback frame naming the shared driver instead of the tool's `main()` |
| 31 | the caret rows under those frames |
| 12 | a modification-time mismatch now reported (the fixed comparison) |
| 9 | an INFO/NORMAL message count following the lines above |
| 8 | an exit code (below) |
| 7 | an ERROR message count following the lines above |
| 4 | a `File info matches` line that was a false match and is gone |
| 1 | the removed `print(sys.exc_info()[2])` |

**The eight exit-code lines are four scenarios:**

```
pds3/chain/initialize           0 -> 1
pds3/chain/repair               0 -> 1
pds3/chain/validate             0 -> 1     the chained run's failure now reported
pds3/pdsinfoshelf/validate-corrupt  0 -> 1  the corruption is now detected
```

The first three are `os.system` → `subprocess.run`: the chained `pdsinfoshelf`
run fails, and its exit code now reaches the caller instead of being truncated to
zero. The fourth is the headline fix working end to end on real holdings — the run
that reported `File info matches` for a corrupted file at base reports the
mismatch and exits 1 at head.

**`ARTIFACTS`: 0 of the artifact records differ.** Nothing about what these tools
*write* changed — not one md5 table, not one `.py` sidecar byte. That is the check
the brief's second modtime trap asks for.

## 8. Proving which tree was measured

The worktrees have no venv of their own and the main checkout carries an editable
install, so every command above set `PYTHONPATH=$PWD/src`, and the tree was
verified rather than assumed:

```
$ PYTHONPATH=$PWD/src python -c "import pdsfile; print(pdsfile.__file__)"
/seti/all_repos/rms-pdsfile-pr26/work/src/pdsfile/__init__.py
```

**One trap worth recording, because it invalidated a probe before it was caught.**
`PYTHONPATH=<other tree>/src` does **not** redirect pytest's in-process imports in
this repo: `pyproject.toml` sets `pythonpath = [".", "src"]`, and pytest prepends
those to `sys.path` ahead of `PYTHONPATH`. Measured from inside a test:

```
sys.path[:5] = ['<work>/tests', '<work>', '<work>/src', '<work>', '<base>/src']
```

So a differential probe run that way exercises **head** code for in-process tests
and **base** code only for tests that shell out to a subprocess. The first pass of
the base probe in §10 was wrong for exactly this reason and was redone.

Frozen files, unchanged:

```
$ git diff --stat 56b8823 HEAD -- tests/api/api_manifest.json \
      tests/api/manifest_allowlist.json scripts/dump_public_api.py \
      tests/api/test_api_freeze.py
(empty)
```

## 9. Ratchet

Measured at base and at head with the same three commands.

| | base `56b8823` | head |
|---|---|---|
| entries | 69 | 69 |
| code slots | 185 | **184** |
| findings under `--config 'lint.per-file-ignores = {}'` | 2,280 | **2,271** |

```
$ python -m ruff check . --config 'lint.per-file-ignores = {}'
$ python - <<'EOF'
import tomllib, pathlib
pfi = tomllib.loads(pathlib.Path('pyproject.toml').read_text()
                    )['tool']['ruff']['lint']['per-file-ignores']
print('entries:', len(pfi), ' code slots:', sum(len(v) for v in pfi.values()))
EOF
```

The brief's figures were correct in every particular, including the four target
entries. One code retired: `pdsinfoshelf` no longer needs `RUF059`, which its
`main()` carried. The other three entries are unchanged, and each of their codes
was re-measured as still required:

| entry | base | head |
|---|---|---|
| `pds3/pdschecksums.py` | `B006 B012 SIM115 UP031` | unchanged; all four still fire |
| `pds3/pdsinfoshelf.py` | `B006 B012 RUF005 RUF015 RUF059 UP031` | **`RUF059` retired** |
| `pds4/pds4checksums.py` | `UP031` | unchanged |
| `pds4/pds4infoshelf.py` | `RUF005 RUF015 UP031` | unchanged |

No entry was widened and no key was added. The two new modules
(`_archives_common.py`, `_shelf_common.py`) carry **no** per-file-ignores entry:
they are clean under the configured gate. One line moved into `_shelf_common.py`
took the modern form on the way, because keeping `'_%s.tar.gz' % …` there would
have required a new ratchet key, which is a widen:

```python
basename += f'_{pdsdir.bundletype_[:-1]}.tar.gz'    # was '_%s.tar.gz' % …
```

The rendered filename is identical.

## 10. Test coverage of the fixes, probed rather than asserted

Every bug fix has a test. To show the tests are not vacuous, the head test files
were run against **base** source (subprocess tests only — see §8 for why the
in-process ones cannot be redirected this way):

```
$ PYTHONPATH=<base>/src:<work> pytest tests/holdings_maintenance/test_pds3_checksums.py \
      tests/holdings_maintenance/test_pds3_infoshelf.py \
      tests/holdings_maintenance/test_pds4_infoshelf.py \
      tests/holdings_maintenance/test_pds4_checksums.py
```

The nine that fail at base and pass at head, one per fix:

```
test_pds3_checksums.py::test_infoshelf_chain_reports_the_chained_run_exit_code
test_pds3_checksums.py::test_infoshelf_chain_passes_a_path_containing_spaces
test_pds3_checksums.py::test_no_targets_leaves_no_unbound_state
test_pds4_checksums.py::test_no_targets_leaves_no_unbound_state
test_pds3_infoshelf.py::test_corruption_is_detected_and_repaired[label_byte0_same_size]
test_pds3_infoshelf.py::test_corruption_is_detected_and_repaired[label_mtime_plus_100]
test_pds3_infoshelf.py::test_modification_time_mismatch_reports_both_times
test_pds3_infoshelf.py::test_update_picks_up_a_new_file
test_pds4_infoshelf.py::test_modification_time_within_one_second_agrees
```

**One test is deliberately kept although it does not discriminate**, and is not
counted as evidence for anything:
`test_pds3_infoshelf.py::test_modification_time_within_one_second_agrees` passes at
base as well, because pds3's comparison was dead there and so reported no
modification-time mismatch for any input. Its pds4 counterpart is the one that
carries the weight. Recorded rather than deleted, because "these two times still
agree" is worth asserting on both flavors now that both share the comparison.

One of these was **vacuous on its first draft and was rewritten**: the
space-in-the-path test originally aimed at a path that the tool rejected before
reaching the chain at all, so it passed at base too. It now builds a real tree
under a directory whose name contains spaces, initializes checksums in it, and
asserts that the chained run's logger name reaches the output — which it cannot if
a shell has split the path into four words.

`test_shelf_common.py` cannot be probed this way at all: `_shelf_common` does not
exist at base, so the module fails to import there. The mutation probe in §3 is
what stands in for it.

### The three tests PR-13 wrote to be inverted

`test_pds3_infoshelf.py` pinned two undetected corruptions and one wrong message
as current behavior, saying so in its module header: *"When the comparison is
fixed these assertions must be inverted — that is the point of pinning them."*
They are inverted here. The two `UNDETECTED_CORRUPTIONS` join
`DETECTED_CORRUPTIONS`; `Child count mismatch 7 7` becomes `7 6`. No test was
skipped, xfailed, or deleted, and no golden was edited.
