# PR-25 adversarial review — round 5

**Reviewed:** `git diff b84fe75..24b92e4` (the owner-ruling round, 1,608 lines)
with `git diff ab1fa3b..24b92e4` (3,581 lines) for context, branch
`pr-25-common-core` at `24b92e4`.
**Reviewer:** a fresh no-context opus-class subagent, pointed specifically at
(1) the `move_old_<kind>()` merge and (2) whether §11.5's time-tag test is a real
control, and told to break things rather than read them.
**Verdict returned:** `goal not met` — **3 Major, 7 Minor**. Every Major is in
the evidence prose or a test docstring; **no defect was found in the shipped
behavior of `src/`**, and the two things the round was pointed at both survived
direct attack.

## How this round was worked

Nothing below is taken from the record. Each claim was re-derived:

- **The merge.** Every moved function was extracted with `ast` from
  `b84fe75` and from `24b92e4` and diffed line by line against *both* pre-move
  copies (`scratchpad/rev5/extract.py`, 10 pairwise diffs).
- **The "hard stop".** `pdslogger` 3.2.1 was imported and the two call shapes
  measured directly, with `replace_root` active.
- **The time-tag fix.** A full pristine copy of the tree was made (the
  `pythonpath = [".", "src"]` in `pyproject.toml` means a scratch `PYTHONPATH`
  does *not* reach pytest — the first attempt to break the fix passed 10/10 for
  that reason), and the fix was then broken **eleven** different ways.
- **The `force=True` decision.** Reverted three different ways; the control was
  itself attacked by forcing the shelf movers.
- **The gate.** `scratchpad/` is not in the repository and none of the seven
  harness scripts the record names exists on this machine, so §5.2's headline
  claim was **re-run from scratch** under an independent harness: 15 invocations
  of the six moved-from pds3 tools against the real `HSTN0_7176` volume, from
  `b84fe75` and from `24b92e4`.
- **The numbers.** Line/statement counts re-derived with `ast`; ruff re-run at
  both heads with `per-file-ignores` emptied; the ratchet parsed and counted; the
  suite collected at both heads with and without holdings; every `<file>.py:<n>`
  citation in the three records extracted mechanically and checked against head.

## Findings

| # | Severity | Finding |
|---|---|---|
| **M1** | **Major** | **Four test docstrings at the reviewed commit describe the design this PR removed.** At `24b92e4`, `tests/holdings_maintenance/test_pds3_checksums.py:167-171` (and `test_pds4_checksums.py:181-185`, `test_pds3_infoshelf.py:255-258`, `test_pds3_linkshelf.py:157-160`) read *"It reads the module-level LOGDIRS list that main() fills in, so a tool whose main() shadows that list with a local versions nothing."* At that commit `LOGDIRS` lives in `_common`, `main()` calls `_common.set_log_dirs(logfiles)`, and no tool has a shadowing local — the sentence describes a state the PR abolished. Ground rule: comments describe current state only. §10 and §10.1's comment audits covered the two archives modules, the six tool modules, `_common.py`, `pdsfile.py` and `_derived_paths.py`; these four files were never in scope, which is how it survived four review rounds. Verified against a pristine `git archive 24b92e4`. **A working-tree edit fixing exactly this is present but uncommitted** (`git status` shows those four files modified), so the defect is in the commit, not in the author's understanding |
| **M2** | **Major** | **"the one place in the tree that builds the pair" is false, is contradicted inside the same commit, and the false sentence is also in the code.** `critiques/phase6-validation.md:834` and addendum §7 both describe `_common.log_paths_for` that way, and `tests/core/test_log_path_timetag.py:132` repeats it as a class docstring. Measured: `grep -c "place='parallel'"` over `src/` returns **15 sites in 11 files**; the two-call pair is built in `pdschecksums.py:783,791`, `pdsinfoshelf.py:819,827`, `pdslinkshelf.py:1670`, `pds4checksums.py:755,763`, `pds4infoshelf.py:800,808`, `pds4linkshelf.py:1163`, `pdsindexshelf.py:489`, `pds4indexshelf.py:475`, `pdsdependency.py:1122` and `re_validate.py:56`. Deferred entry 99 — added in this same commit — enumerates them. **Demonstrated live** under a one-second-per-reading clock: `_common.log_paths_for(pdsarchives.SPEC, …)` returns 1 path; the expression copied verbatim from `pdschecksums.py:783-789` returns 2, tagged `12-00-01` and `12-00-02`. Two consequences the record does not state: (a) the PR edits six of those files in this very commit, adjacent to the unfixed lines; (b) the indexshelf pair's *explicit* dedupe `if logfiles[0] == logfiles[1]: logfiles = logfiles[:-1]` is defeated by precisely this race, so those two tools write one run's log twice into one directory. Addendum §7's mitigation — "The nine tools PR-26 and PR-27 migrate inherit the fix" — is also wrong: the plan's own PR-25 entry says `pdsdependency` is "**left as a standalone tool this phase**", and `re_validate.py` is frozen by ground rule 7, so at least two of the eleven sites are not scheduled to inherit anything |
| **M3** | **Major** | **Systematic stale line citations, under an explicit claim of re-measurement.** The PR-25 section opens *"**Every number in this section was re-measured at the final commit** … Nothing here is carried over from the earlier rounds."* Extracting every `<file>.py:<n>` citation from `phase6-validation.md`, the addendum and the PR-25 deferred entries and checking each at head: **at least 22 are stale**, and **three point past the end of the file**. Table below |
| m1 | Minor | **§6's growth arithmetic is off by one, and entry 98 disagrees with it.** `_common.py` is 676 lines against `b84fe75`'s 486, so it grew **190**. §6 splits that as "151 lines … and **38 lines** for everything else": 151 + 38 = 189. Measured: head lines 1–525 (everything above the new banner) minus 486 = **39**. Deferred entry 98, in the same commit, correctly says `+39`. The statement half (93 + 10 = 103) is exact |
| m2 | Minor | **"moved verbatim" is not what happened.** §6.1 says `move_old_info`/`move_old_links` "are **byte-identical**, so each moved verbatim", and the plan says "moved verbatim, one copy". Measured: each differs from **both** pre-move copies in two lines — `LOGNAME` → `INFOSHELF_LOGNAME`/`LINKSHELF_LOGNAME` (value-preserving, disclosed in §6.1) and `'%03d' % new_version` → `f'{new_version:03d}'` (a rewrite, disclosed in §9 and in `pyproject.toml`, but not where the verbatim claim is made). `move_old_checksums` differs in those two plus the signature and the two `force=True`. The record's *comparison of the twins* is exactly right; it is the word "verbatim" about the move that is not |
| m3 | Minor | **The pin does not restore the class dict, and the docstring says it does.** `_derived_paths.py:219-220`: "restored on the way out, so a block that raises leaves nothing behind". Measured: `'_LOG_TIMETAG' in vars(Pds3File)` is `False` before the first pin and `True` (value `None`) after — the `finally` writes `previous` onto the class, creating a shadow that was not there. Consequence, measured: after one pin on `Pds3File`, a pin taken on `PdsFile` reaches `Pds4File` but **no longer reaches `Pds3File`**. Inert today because `log_paths_for` always pins `spec.pdsfile_cls`; it becomes live the moment any caller pins `type(pdsdir)`, which would make that rule subclass permanently immune to flavor-level pins. (The class-global pin is also not thread-safe; no in-tree caller is threaded) |
| m4 | Minor | **The "hard stop" is real but is doing more rhetorical work than it earns.** The pdslogger difference was measured and is exactly as claimed: `logger.info(noun + ' moved to', dest)` renders `… moved to: logs/x_v001.pickle` and `logger.info(noun + ' moved to ' + dest)` renders `… moved to /root/holdings/logs/x_v001.pickle` — the two-argument form both inserts `': '` and puts the path through `replace_root`. Not collapsing the three functions is therefore right. But **18 non-blank lines are identical across all three movers** after normalizing nothing but the variable names (the existence guard, the basename/splitext pair, the whole `for log_dir in LOGDIRS` version-numbering block, the `shutil.copy`, the `from_logged` latch) — three copies, in the one section of the one file whose stated purpose is one copy each. Deferred entry 100's last paragraph concedes this; §6.1's prose, which is what a reader of the evidence record sees, presents the stop as covering the whole question. Sub-plan §2 forbids "a **boolean flag** whose only job is to re-create one side's quirk"; the same document admits "a **tuple** of handler factories" as data, and a per-kind emitter is the same shape — so the rule is not as decisive here as §6.1 implies |
| m5 | Minor | **`ToolSpec` became unhashable and §7 does not say so.** `@dataclass` with the default `eq=True, frozen=False` sets `__hash__ = None`; measured, `hash(pdsarchives.SPEC)` now raises `TypeError: unhashable type: 'ToolSpec'` where at `ab1fa3b` it hashed by identity. §7 says the conversion is "Fifteen field annotations, no other change to what the spec holds". Nothing in-tree hashes a spec or puts one in a set, so it is inert — but it is a real semantic change and a generated `__eq__`/`__repr__` came with it |
| m6 | Minor | **§7: "the two pds4 tools also rebuild an archives path by concatenating it back" — four tools do.** `pds4checksums.py:680` and `pds4infoshelf.py:726` build `'/pds4-holdings/archives-'`, and `pdschecksums.py:708` and `pdsinfoshelf.py:745` build `'/holdings/archives-'` identically. (Also worth noting: the rebuilt literal *contains* the field's value rather than being it, so a later `spec.holdings_sentinel` substitution needs `+ 'archives-'`) |
| m7 | Minor | **The Phase-6 gate's evidence is not re-derivable from the branch.** §3, §5.1, §5.2, §8 and §11.5 attribute their numbers to `scratchpad/compare_runs.py`, `tool_run_diff.sh`, `compare_toolruns.py`, `shelf_run_diff.sh`, `compare_runs3.py`, `parser_probe.py` and `versioning_probe.py`. `git ls-files | grep scratchpad` is empty, there is no `scratchpad/` directory in the worktree, and `find` over all four trees finds none of the seven files. Earlier rounds evidently had them (round 4 quotes raw traceback frames out of the captures), so this is durability rather than fabrication — but a reviewer at this head cannot re-derive "32 of 32 / 76 of 76" or "4,005 / 4,009" from anything the branch contains. I re-ran §5.2 independently instead (below) and it held |

### M3 in detail — the stale citations

Measured at `24b92e4`. Three are past EOF.

| Cited as | Where | Actual at head |
|---|---|---|
| `_common.py:206-209` | §5.1, addendum §5 (handler factories at log root) | 246 |
| `_common.py:211` | §10 (the reworded comment) | 249 |
| `_common.py:229` | entry 99 (the archives set literal) | 199–200 |
| `_common.py:239-240` | §5.1, addendum §5 (per-target factories) | 277 |
| `_common.py:280-283` | entry 92 (the four `*_LIMITS`) | 317–320 |
| `_derived_paths.py:207` | entry 93 (`_log_path_for`) | **236** — moved by this PR's own edit |
| `pdsarchives.py:239` / `pds4archives.py:259` | entry 92 (`file_log_level`) | 241 / 261 |
| `pdschecksums.py:55`, `pdsinfoshelf.py:45` | §13 entry 88 (`B006`) | 37, 42 |
| `pdschecksums.py:750` | §7, addendum §5, entry 101 | 697 |
| `pdschecksums.py:836,844` | entry 99 | 783, 791 |
| `pdschecksums.py:873` | §9 (the `'Task "' + args.task` spelling) | 815/818 — **file is 869 lines** |
| `pdschecksums.py:917` | §13 entry 83 (the live `proceed` read) | 862 — **past EOF** |
| `pdsinfoshelf.py:775` / `:860,868` | §7, addendum §5, entry 99, entry 101 | 734 / 819, 827 |
| `pdslinkshelf.py:1717,1720` | entries 93, 99 | 1670, 1673 |
| `pds4checksums.py:722,733` / `:808,816` | §7, addendum §5, entries 99, 101 | 669, 680 / 755, 763 |
| `pds4infoshelf.py:756,767` / `:841,849` | §7, addendum §5, entries 99, 101 | 715, 726 / 800, 808 |
| `pds4linkshelf.py:1210` | entry 99 | 1163 |
| `pds4linkshelf.py:1271` | §13 entry 89 (the bare `_`) | 1222 — **file is 1229 lines** |

Correct at head, and checked: `pdsdependency.py:1107,1122`; `pdsindexshelf.py:459,461,464,473,489`; `pds4indexshelf.py:445,447,450,459,475`; `re_validate.py:56,102`; `pdsarchives.py:41-43,217`; `pds4archives.py:105`; `pdscache.py:324`. Every one of the stale citations is in a file this PR shortened, so the pattern is mechanical: the six-module move renumbered them and only the untouched files' citations survived.

## What was attacked and did not break

This is the part that matters for judging whether the work is sound, and most of
what the round did.

### (1) The `move_old_<kind>()` merge — the twin-identity claims are exact

Each moved function extracted with `ast` and diffed against both pre-move copies:

- `move_old_info` (pds3) vs `move_old_info` (pds4): **byte-identical**. As claimed.
- `move_old_links` (pds3) vs (pds4): **byte-identical**. As claimed.
- `move_old_checksums`: differs in **exactly two** things — `def …(check_path, *, logger=None)` vs `(check_path, logger=None)`, and `force=True` on the two `logger.info` lines. As claimed, to the character.
- `hashfile`: pds3 `f = open(...)` with a `while` loop and no close; pds4 the `with`/`iter` form. As claimed; the merged copy is byte-identical to the pds4 twin.

The merged copies then differ from their sources only as m2 records
(`*_LOGNAME`, the f-string), and `f'{n:03d}'` is `'%03d' % n` for every `int`.

### (2) The time-tag fix — eleven mutations, every one caught

Run in a full pristine copy of the tree (`tests/core/test_log_path_timetag.py`,
10 ids):

| Mutation | Result |
|---|---|
| B1 reader ignores the pin (`cls._log_timetag()` unconditionally) | **8 failed, 2 passed** — reproduces §11.5's claim exactly |
| B2 context manager is a bare `yield` | 8 failed |
| B3 pin written onto the root class instead of `cls` | **10 failed** |
| B4 `finally` sets `None` instead of `previous` | 1 failed (`test_nesting_restores_the_outer_tag`) |
| B5 no `finally` at all | 6 failed |
| B6 `log_paths_for` drops the `with` | 4 failed |
| B7 reader looks the pin up on the root class | 9 failed |
| B8 reader re-reads the clock while pretending to honour the pin | 8 failed |
| B9 `_LOG_TIMETAG = ''` instead of `None` | 3 failed |
| B10 `log_paths_for` pins `PdsFile` instead of `spec.pdsfile_cls` | 2 failed |
| B11 restore moved out of `finally` (leaks on a raise) | 3 failed |

No mutation passed. The two ids that survive B1 are the release-on-exit and
release-on-raise pair, exactly as §11.5 says, and they are the two that catch B5
and B11 — so the suite has no dead id. B10 is the interesting one: it fails only
the pds3 parametrizations, and the reason is m3's shadowing (`Pds4File` still
inherits the base pin, `Pds3File` does not once it has been pinned once). That is
how m3 was found; the test suite noticed the symptom without naming the cause.

The fix itself was also read for correctness: `cls = type(self)` at
`_derived_paths.py:260` means a rule-subclass instance finds the flavor's pin
through the MRO (`test_the_pin_reaches_a_rule_subclass_of_the_pinned_class`
covers it, and `Pds3File.SUBCLASSES['ASTROM_xxxx']` really is a subclass);
`log_paths_for` builds its set **inside** the `with`, so nothing escapes; the pin
cannot leak across flavors because `Pds3File` and `Pds4File` are siblings;
`copy()` is an instance operation and cannot carry class state; and the `or`
fallback means a cleared pin reads the clock rather than producing an empty tag.

### (3) The `force=True` decision — it cannot pass with the behavior reverted

`tests/holdings_maintenance/test_common_versioning.py`, 39 ids:

| Mutation | Result |
|---|---|
| both `force=True` removed (the pds4 behavior) | `1 failed, 38 passed` — `test_the_checksum_move_still_reports` |
| only the "moved from" line reverted | same 1 failed |
| only the "moved to" line reverted | same 1 failed |
| **control attacked**: `force=True` *added* to both shelf movers | `2 failed` — both `test_a_shelf_move_is_silenced_by_the_same_cap` params |

So the `{'info': 0}` cap is live and is proven live by a test in the same class,
and the assertion is on the *rendered* text (`'Checksum file moved to: '`, with
the colon pdslogger inserts). The versioning tests have teeth too:
`new_version = 1` (never advance) fails 3 ids, and `shutil.copy` → `shutil.move`
fails 1.

### (4) §5.2 re-run from scratch, since its harness is gone

Fifteen invocations of `pdschecksums`, `pdsinfoshelf` and `pdslinkshelf` —
`--initialize`, `--validate`, `--reinitialize` twice, and `--log <root>` runs of
`--reinitialize` and `--repair` — against a `cp -a` copy of the real
`HSTN0_7176` volume on a fixed temporary disk, `PYTHONHASHSEED=0`, one second
between invocations, run from `b84fe75` and from `24b92e4`. Normalizing only the
wall clock, the elapsed times, the disk path, the source-tree path, the log time
tag, and the order of consecutive `Log file:` / `… moved to` runs:

| | `b84fe75` | `24b92e4` | identical |
|---|---:|---:|---|
| stdout captures | 15 | 15 | **15 of 15** |
| normalized log lines | 823 | 823 | **0 diff hunks** |
| exit codes | 15 × 0 | 15 × 0 | same |
| versioned files produced | 11 | 11 | same set |

The run reaches all four moved functions: `hashfile` on every checksum file,
`move_old_checksums` ten times (including the `--log` shape where `LOGDIRS` holds
two directories and the file is versioned into both), and `move_old_info` /
`move_old_links` writing `_v001`/`_v002` `.pickle` **and** `.py` pairs — the
unconditional sidecar `shutil.copy` that had never been reachable in the pds3
tools. Nothing differs. §5.2's claim, for the pds3 half, is independently
confirmed.

### (5) Everything else that was checked and held

- **The shared-`LOGDIRS`-across-tools question.** Searched the whole tree: the only cross-tool import that calls into another tool's module is `pdsinfoshelf` → `pdschecksums.checksum_dict` (and its pds4 twin), which never calls `move_old_*`; `re_validate.py` imports four tools but calls only their `validate`, and never calls `set_log_dirs`, so `LOGDIRS` stays empty there exactly as it did before. **No live leak.** The ordering `set_log_dirs` builds is the same set iteration the old in-loop `append` used.
- **The removed imports.** `shutil` ×6, `hashlib` ×2, `glob` ×2, as §6.1 says. `F401` is not in any of the six files' ratchet entries and `ruff check` passes, so nothing was stranded.
- **Ruff, re-measured with `per-file-ignores = {}` over `src/pdsfile tests scripts` at both heads:** total **2,316 → 2,298**; `UP031` **140 → 126**; `N806` **3 → 0**; `SIM115` **3 → 2**; the statistics diff shows **no other code moved**. `ruff check` passes; the preview `E111,E112,E113` gate passes. `_common.py`, `tests/core/test_log_path_timetag.py` and `tests/holdings_maintenance/test_common_versioning.py` report **zero** findings with the ratchet emptied, so none needs an entry and none has one.
- **The ratchet may only shrink:** parsed at all three heads — `ab1fa3b` 70 entries / 198 slots, `b84fe75` and `24b92e4` both 69 / 193. No new key, no widened value. The group split checks out: CORE is 11 entries / 14 slots (the eight `src/pdsfile/*.py` entries plus `pdscache`, `pdsfile`, `pdsviewable`), leaving REST at **58 entries / 179 code slots** and `2,259 + 39 = 2,298`, exactly as `pyproject.toml`'s header and deviation (4) now say. The `UP031` breakdown 40+24+49+6+6 = **125** matches the 126 measured less `pdscache.py:324`.
- **Line and statement counts, re-derived with `ast`:** every figure in §6, §6.1, the section table and entry 66 is **exact** — `pdsarchives` 565→260 / 307→140, `pds4archives` 590→280 / 316→146, `_common.py` 676 / 316, the six tools 6,751→6,457 lines and 3,360→3,166 statements line for line, the section table 31+72+208+214+151 = 676, the versioning section 93 statements, and entry 98's projection (214/1,155 = 18.5% over 1,711+1,782+2,964+1,094 ≈ 1,400).
- **Id arithmetic:** collected at both heads — `tests` 892 → **945**, `tests/holdings_maintenance` 111 → **154**, `tests/core` 43 → **53**. 10 + 39 + 4 = **53**. The two new files pass 49/49. With the holdings env unset: base **92 passed / 800 skipped**, head **141 passed / 804 skipped** — the record's figures to the id.
- **API freeze:** `pytest tests/api/` passes 26 ids; `_log_path_for` and `_LOG_TIMETAG` appear **zero** times in `api_manifest.json`; `consumer_used_private_names.json` is `[]`; the allowlist is untouched. Addendum §7's "154 entries" arithmetic is right — the manifest carries `log_path_for_bundle` 34, `log_path_for_bundleset` 34, `log_path_for_index` 34, `log_path_for_volume` 26, `log_path_for_volset` 26.
- **Constraints:** no `ruff format`; none of `tests/api/api_manifest.json`, `tests/api/manifest_allowlist.json`, `scripts/dump_public_api.py`, `tests/api/test_api_freeze.py` is in the PR diff; no golden or baseline touched; no `skip`/`xfail` added; no f-string in any logging call in the changed files; no `[*x, y]`; no plan/critique/PR/phase reference in any changed source or test file; no hard-coded holdings root introduced.
- **Python floor:** `@dataclass(kw_only=True)` and `Callable | None` evaluated in a class body both need 3.10; `requires-python = ">=3.10"` and CI runs 3.10. Fine, but exactly at the floor.
- **`ToolSpec` values:** `holdings_sentinel` and `index_ext` carry `'/holdings/'`/`'.tab'` and `'/pds4-holdings/'`/`'.csv'`, and those are the literals the five sentinel tools and the two indexshelf tools actually use (the indexshelf citations are the ones that are still correct at head). Construction is keyword-only, missing fields raise, the object is still mutable, and 15 fields are declared.

## Verdict

**The code is sound.** Both things this round was pointed at survived deliberate
attack: the merge collapses genuine duplication and forces nothing (the two shelf
movers' twins really are byte-identical, and the one divergence that had to be
decided is disclosed and pinned by a control that cannot go inert), and the
time-tag test is a real control — eleven independent mutations, eleven caught,
including four the record never tried. The §5.2 gate reproduces under an
independent harness. Every ruff, line, statement and id number in the record is
exact.

**The record is not sound**, in the same way rounds 1–4 kept finding and in one
new way. M3 is the recurring stale-evidence class at its largest yet — 22 stale
citations, three past EOF — under a sentence that explicitly promises they were
all re-measured; the mechanism is obvious in hindsight (the six-module move
renumbered every file it touched, and only the untouched files' citations
survived), which makes it cheap to fix and cheap to have prevented. M2 is worse
than a stale number: a headline claim that is false, contradicted by another
document in the same commit, and repeated in a test docstring — and its
consequence, that six tools this PR edits still carry the bug it fixes and two of
the eleven sites are not scheduled to inherit the fix at all, is a scoping
decision the owner should get to make with the true numbers in front of them. M1
is a straight ground-rule violation that four rounds of comment auditing missed
because the audit's own scope excluded the files.

None of the three is a reason to distrust the migration. All three are reasons
the record should be corrected before merge, and M1 is already fixed in the
working tree and only needs committing.
