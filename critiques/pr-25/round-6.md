# PR-25 adversarial review — round 6

**Reviewed:** `git diff 540447f..01a083d` (the output-relaxation round, 1,428
changed lines over 25 files) with `git diff ab1fa3b..01a083d` (5,806 lines) for
context, branch `pr-25-common-core` at `01a083d`.
**Reviewer:** a fresh no-context opus-class subagent, pointed at (1) whether any
output change slipped through unattributed, (2) the `move_old` collapse, (3) the
time-tag race at all fifteen sites and the set→list change, and (4) the
`re_validate.py` unfreeze sweep.
**Verdict returned:** `goal met, with record corrections` — **3 Major, 6 Minor**.
Every finding is in the evidence prose or a test docstring; **no defect was found
in the shipped behavior of `src/`**, and the round's central claim — 100 differing
output lines in two classes and nothing else — reproduced under an independent
harness that is 24 invocations larger than the author's and covers three tools the
author's gate does not.

## How this round was worked

Nothing below is taken from the record. Each claim was re-derived:

- **The output gate.** A harness written from scratch
  (`scratchpad/rev6/harness.py`, `compare.py`) builds a disposable disk from the
  real testing holdings, runs **56** invocations of **eleven** tools out of
  `/seti/all_repos/rms-pdsfile-pr25/prev/src` and out of `.../work/src`
  (`PYTHONHASHSEED=0`, `TZ=UTC`, pinned mtimes), and captures stdout, stderr,
  exit code, every log file written, and every artifact under both holdings
  roots. Every differing line was then classified mechanically.
- **The merge.** The three pre-collapse bodies at `540447f` read statement by
  statement against `move_old` + `next_version_dest` at head, and probed with
  **twelve** mutations of the merged function plus two negative controls.
- **The race.** `grep` at both heads; the twelve modules that reach
  `log_paths_for` enumerated; seven mutations of `log_paths_for` and the pin.
- **The unfreeze.** A repo-wide grep for `re_validate`, the ratchet parsed with
  `tomllib` at three heads, ruff re-run at three heads with `per-file-ignores`
  emptied.
- **The numbers.** Line/statement counts re-derived with `ast`; the suite
  collected and run at base and head, with and without holdings; every
  `<file>.py:<n>` citation in the record extracted mechanically and resolved
  against head.

## Findings

| # | Severity | Finding |
|---|---|---|
| **M1** | **Major** | **`pyproject.toml` and `.cursor/rules/pdsfile_overrides.mdc` disagree about the ratchet inside one commit, and the `.mdc` — the document the next shrink is measured against — is the one that is wrong.** `pyproject.toml:165-166`, edited in this very commit, reads "PR-25 removed **nineteen** more, so the group now measures **2,258** over 58 entries"; `phase6-validation.md` §9 agrees (REST 2,277 → **2,258**). `.cursor/rules/pdsfile_overrides.mdc:94-95` still reads "PR-25 shrank that set by **eighteen**, to **2,259** over **58 entries**", and its enumeration in the next four lines is 14 `UP031` + 3 `N806` + 1 `SIM115` = **18**, with no mention of the `C405`. Measured, `per-file-ignores` emptied, over `src/pdsfile tests scripts`: `ab1fa3b` **2,316** → `540447f` **2,298** → `01a083d` **2,297**. The delta over the PR is **19**, and the nineteenth is exactly the `C405` this round removed. The commit's whole purpose in that file was to re-state the `re_validate.py` rows; the paragraph four lines above them was left at the previous round's figure |
| **M2** | **Major** | **§11.5's control claim is wrong at head and contradicts §3 in the same document.** `phase6-validation.md:1047`: "Run against the unfixed reader … **8 of the 12 ids fail**. The four that pass assert only the pin's own bookkeeping". `tests/core/test_log_path_timetag.py` holds **17** ids, which is what §3's own table says (8 + 5 + 4). Measured, `_log_path_for` reverted to `parts += ['_', cls._log_timetag()]` in a pristine copy: **13 failed, 4 passed** of 17. The "four that pass" half is exactly right; the "8 of the 12" is the figure from before `TestTheIndexshelfDedupe` (4 ids) and `test_the_default_place_comes_first` (1 id) were added *in this round*. The PR-25 section opens by promising every number in it was re-measured at the final commit |
| **M3** | **Major** | **The stale-citation class recurs for the third consecutive round, under the same re-measurement claim, with one citation past EOF.** Round 5's M3 forced a correction pass; this round added `from pdsfile.holdings_maintenance import _common` to four more modules and collapsed 24 lines out of `_common.py`, which shifted every citation below again. Measured at `01a083d` — table below — **at least ten distinct citations in `phase6-validation.md` and the addendum resolve to the wrong line**, and `pdschecksums.py:862` is **past the end of a 857-line file** (it was corrected from `:917` to `:862` last round and has gone stale again). The mechanism is now demonstrably systematic rather than accidental: it will recur on the next round unless the citations are generated rather than typed |
| m1 | Minor | **"Eleven maintenance tools" is twelve, and the sentence that says so is arithmetically self-contradictory — in the code.** `tests/core/test_log_path_timetag.py:227-228`: "All **eleven** maintenance tools reach it — the archives pair through `run_main` and the other **ten** directly". 2 + 10 = 12. Measured: `grep -rln "_common.log_paths_for\|_common.run_main" src/pdsfile/holdings_maintenance/` returns **12** tool modules (7 pds3 + 5 pds4; `re_validate.py` is one of them). The same undercount is in `phase6-validation.md:112` ("the one helper all **eleven** tools call"), `:1131` and addendum `:379` ("**nine of the eleven** tools built a `set`" — measured: **ten of twelve**, since the archives pair got its set from `_common.log_paths_for`), and addendum `:244`. This is the same sentence round 5's M2 forced a correction to; the false half was fixed and a new false number put in its place |
| m2 | Minor | **§11.5 opens "Measured at this head" over `540447f` numbers and contradicts itself two paragraphs later.** `phase6-validation.md:1011`: "**Measured at this head**, `grep -n "place='parallel'" src/` reports **15 sites**: `_common.py:200`, which is fixed, and **14 in ten tool modules**, which are not"; then `:1029`: "**That was the state at `540447f`**." Verified: those fifteen line numbers are exact at `540447f` and none of the fourteen exists at head, where the grep returns **one** site at `_common.py:208`. Deferred entry 99 carries the same mislabel ("Measured at PR-25's head"). The facts are right; the tense is not, and a reader checking `_common.py:200` at head finds a blank line |
| m3 | Minor | **The output gate's scope is four tools short of the round's file scope, under a ruling whose own words are "a differing line that cannot be attributed is still a defect".** §5 defines the gate as §5.1 (the archives pair) plus §5.2/§5.3 (the six checksum/infoshelf/linkshelf tools). This round also edits `pdsindexshelf.py`, `pds4indexshelf.py`, `pdsdependency.py` and `re_validate.py` — each gained the `_common` import and had its log-path construction replaced, and the two indexshelf modules **lost their explicit dedupe block**, which is the one place in the tree where the round removed code that was doing the job by hand. None of the four is in either gate. I ran the three that can be run (25 of my 56 invocations) and found nothing unattributed; `re_validate.py` is exercised by no gate and no test, which the record itself says |
| m4 | Minor | **The `force=True` change is unreachable from any command line, so §5.3's equal line counts cannot speak to it.** Measured: `pdslogger` 3.2.1 has `limits={}` as the default on both `PdsLogger.__init__` and `open()`, and 300 unforced `logger.info` calls in a default scope emit 300 lines with no suppression marker. Every `move_old` call site sits at the top level of a task function, outside any `logger.open(..., limits=...)`; the `limits` dicts the six tools carry are passed to `generate_*`/`write_*`, never around the move. So change 2 is inert in-tree today and only `TestReportingUnderAnInfoCap` can see it. Worth saying because §5.3's "**The line counts are equal** … no message was added, none was dropped" reads as covering all six changes, and for this one it is silent rather than confirming |
| m5 | Minor | **`move_old`'s existence guard is the one statement of the merged function no test reaches.** Deleting `if not os.path.exists(path): return` leaves **70 of 70** unit ids passing. It is defensive rather than load-bearing — `pdschecksums.reinitialize`/`repair` return earlier when the file is absent, and the three shelf tools guard the call site with `if os.path.exists(...)` — so this is a coverage gap, not a regression. It is the only one: eleven other mutations of the same function were all caught |
| m6 | Minor | **§10.1's comment count was not re-measured after this round added a comment.** "`_common.py` gained one section banner and **five** comment lines for the new section". Measured with `tokenize` at head: the versioning section carries the banner plus **nine** comment lines — the round added a three-line comment inside `move_old` (which is correct, current-state prose with no plan or PR reference, and is the right thing to have written). Small, but it is in the audit whose whole point is that comment inventory is tracked |

### M3 in detail — the stale citations

Measured at `01a083d`. Every one is in a file this round shifted.

| Cited as | Where | Actual at head |
|---|---|---|
| `_common.py:200` (the fixed `place='parallel'`) | §11.5 `:1011`, addendum `:270` | **208** |
| `_common.py:246-249` (handler factories at the log root) | addendum `:213` | **259-260** |
| `_common.py:249` (the reworded comment) | §10 `:851` | **262** |
| `_common.py:276-277` (per-target factories) | §5.1 `:256`, §14 `:1275`, addendum `:213` | **290-291** |
| `pdschecksums.py:815` (the `'Task "' + args.task` spelling) | §9 `:754` | **803**/**806** |
| `pdschecksums.py:862` (the live `proceed` read) | §13 entry 83 `:1178`, deferred `:2161,:2175` | **850** — **past EOF (857 lines)** |
| `pdsindexshelf.py:459,461,464,473` (`'.tab'`) | §7 `:683`, addendum `:201` | **460, 462, 465, 474** — all off by one |
| `pds4indexshelf.py:445,447,450,459` (`'.csv'`) | §7, addendum | **446, 448, 451, 460** — all off by one |
| `pds4linkshelf.py:1222` (the bare `_`) | §13 entry 89 `:1180` | **1217** |
| the fourteen `place='parallel'` tool sites | §11.5 `:1012-1015`, entry 99 | gone; those lines now hold other code (see m2) |

Correct at head, and checked: `pdschecksums.py:37,697,708`; `pdsinfoshelf.py:42,734,745`;
`pds4checksums.py:669,680`; `pds4infoshelf.py:715,726`; `pdsdependency.py:1107`;
`re_validate.py:102`; `pdsarchives.py:41`; `pds4archives.py:105`; `pdscache.py:324`.

## What was attacked and did not break

This is most of what the round did, and it is the part that decides whether the
work is sound.

### (1) The output gate, re-derived independently and larger

`scratchpad/rev6/harness.py` copies the real `HSTN0_7176` volume and metadata plus
the nine `uranus_occ_u0_kao_91cm` PDS4 files into a disposable disk with pinned
mtimes, then runs the same **56** invocations from `prev` and from `work`:
`pdschecksums`, `pdsinfoshelf`, `pdslinkshelf` (`--initialize`, `--validate`,
`--reinitialize` ×2, `--log <root> --reinitialize`, `--log <root> --repair`,
`--update`), the **bundleset branch** of `pdschecksums` and `pdsinfoshelf` against
a real `archives-volumes/` volset, both archives tools, both indexshelf tools,
`pdsdependency`, and the pds4 checksum/infoshelf/linkshelf trio. Normalizing only
the wall clock (including the copy embedded in message text), the elapsed times,
the disk path, the source-tree path and the log time tag:

| | `540447f` | `01a083d` | |
|---|---:|---:|---|
| invocations | 56 | 56 | **exit code identical in 56 of 56** |
| stdout+stderr byte-identical | — | — | **31 of 56** |
| normalized lines | **3,131** | **3,131** | **equal** |
| `Log file:` announcements | **74** | **74** | same paths; **order** differs in 7 |
| files written under `logs/` + `logroot/` | 68 distinct | 66 distinct | difference fully explained by same-second name collisions in *my* harness, not by the code |
| artifacts under both holdings roots | 36 | 36 | same set, same sizes |

Every differing line classified, **zero unattributed**:

| Class | Lines | What |
|---|---:|---|
| **A** | **40** | `… moved from: <DISK>/holdings/checksums-volumes/…` → `… moved from: checksums-volumes/…` — the path is now the filepath argument, so `replace_root` trims it |
| **B** | **14** | `Link shelf file moved to <path>` → `Link shelf file moved to: <path>` |
| — | 106 | traceback frame line numbers and `<traceback object at 0x…>` ids, from `pds4indexshelf`/`pds4archives` failing as expected on a metadata-only subset; the frames moved because the code moved |
| — | 6 | the `.tar.gz` md5, because gzip embeds the current mtime — reproduces between two runs of the *same* tree |
| | **0** | **unattributed** |

So §5.3's two classes really do account for everything, and they account for it
across three tools §5.3 does not cover. Specifically checked for and **not**
found: a message that disappeared, a message that appeared, a level that changed,
a summary count that changed, a log file whose name or path changed, and an exit
code that changed. The archives pair emits **zero** class-A and zero class-B
lines, as §5.3 says. `--help` was captured for all eleven tools from both trees
and is **byte-identical for all eleven**, so the frozen half of the ruling holds.

The only ordering change is the one the record discloses: seven `--log`
invocations emit the two `Log file:` lines (and the two `… moved to` lines) in the
other order at `540447f`. The set of paths is identical; nothing else moved.

### (2) The `move_old` collapse — statement by statement, and twelve mutations

Read against the three bodies at `540447f`:

- **Version numbering.** `next_version_dest` is `dest_template = log_dir + '/' + prefix + '_v???' + ext`, `lskip = len(ext)`, `int(version_path[-lskip-3:-lskip])`, `max + 1`, `'???'` → `f'{n:03d}'` — the same five statements all three shared, including the two pre-existing failure modes (`ext == ''` and a non-numeric `_v???` match) preserved unchanged.
- **Companions.** `CHECKSUM_FILE` `()`; `INFO_SHELF` `('.py',)`; `LINK_SHELF` `('.py', '.pickle')`, in that order, which is the order the old `move_old_links` copied them. `stem = path.rpartition('.')[0]` and `dest_stem = dest.rpartition('.')[0]` reproduce the old `.rpartition('.')[0] + ext` on both sides, so the link shelf's `.pickle` companion still resolves to the shelf file itself and is still copied twice to the one destination.
- **Order within the loop.** copy → "moved from" (once) → "moved to" → companions, in all three before and after.
- **Logger fallback.** `kind.logname` yields `CHECKSUMS_LOGNAME`/`INFOSHELF_LOGNAME`/`LINKSHELF_LOGNAME` for the three kinds, matching each old body.
- **Signature.** `move_old(path, kind, *, logger=None)`; every in-tree call site passes `logger=logger`.

Twelve mutations plus two negative controls, 70 unit ids each:

| Mutation | Result |
|---|---|
| R1 link shelf's "moved to" back to a concatenation behind a `kind is LINK_SHELF` branch | **3 failed** |
| R2 "moved from" back to the baked-in colon | 3 failed |
| R3 `force=True` dropped from both lines | 3 failed |
| R4 only the shelf kinds lose `force` (the pre-PR asymmetry) | 2 failed |
| R5 `LINK_SHELF` loses its `.pickle` companion | 1 failed |
| R6 `INFO_SHELF` loses its `.py` companion | 2 failed |
| R7 `CHECKSUM_FILE` gains a `.py` companion | 5 failed |
| R8 `next_version_dest` reuses the highest version | 3 failed |
| R9 `next_version_dest` starts at `000` | 6 failed |
| R10 `shutil.copy` → `shutil.move` | 6 failed |
| R11 `stem` from `os.path.splitext` | 70 passed — **equivalent**, not a hole |
| R12 the existence guard removed | 70 passed — **m5** |
| N1 (control) `place='default'` made implicit | 70 passed, as intended |
| N2 (control) companion copies moved above the log lines | 70 passed, as intended |

R1 is the load-bearing one and it also has teeth at the tool level: with R1
applied, `test_pds3_linkshelf.py::test_update_versions_the_shelf_file_it_replaces`
**fails** against real holdings. R2 and R3 leave all four holdings regression
tests green, which is the honest reading of the four updated assertions — see (5).

§6.2's arithmetic re-derived with `ast`: the three bodies are **22 + 25 + 29 = 76**
statements at `540447f`; `move_old` is **17** and `next_version_dest` **7** at
head. **24 against 76**, exactly as claimed.

### (3) The race, at all fifteen sites, and the set→list change

- `grep -n "place='parallel'" src/` returns **one** site, `_common.py:208`. At `540447f` it returned the fifteen the record lists, verified.
- **Twelve** tool modules reach `log_paths_for` — the ten directly and the archives pair through `run_main`. No `log_path_for_*` call survives anywhere else in `src/` outside `_derived_paths.py` and the pds3 aliases.
- **Every branch through `main()` reaches it.** `pdschecksums` and `pds4checksums` pick `log_path_for_bundle` vs `log_path_for_bundleset` from `volname`/`bundlename`; `pdsinfoshelf` picks `log_path_for_volume` vs `log_path_for_volset` — the same spellings the pre-collapse code used, including `pdschecksums`'s odd pds3-with-bundle-spelling. My harness exercised **both** branches of `pdschecksums` and `pdsinfoshelf` (volume target and a real `archives-volumes/` volset target) and both are byte-identical bar class A.
- **Nothing downstream depended on set semantics.** `grep -rn "logfiles\." src/` is empty: no `.add`, no set algebra, no membership test. Every consumer is `for logfile in logfiles` or `set_log_dirs(logfiles)`, whose body is a list comprehension. `re_validate` and `pdsdependency`, which each rewrite the path inside the loop, are unaffected by the type.
- **The list is strictly better than the set for `set_log_dirs`.** Under the old code two paths that differed only in the time tag landed in the **same** directory, so `LOGDIRS` held that directory twice and `move_old` versioned the file into it twice (`_v001` and `_v002` for one run). The dedupe now compares two paths built from one clock reading, so that cannot happen.
- Seven more mutations, all caught except the two that are genuinely equivalent: `log_paths_for` unpinned → **8 failed**; the dedupe removed → **4 failed**; returning a `set` → 1 failed; the order reversed → 1 failed; the pin restored unconditionally (round 5's m3) → 2 failed; the reader ignoring the pin → 13 failed. Pinning the root `PdsFile` instead of `type(pdsf)` → 70 passed, and reading the code that is correct: the `had_own`/`del` bookkeeping added before this round means no shadow survives a block, so the two are equivalent today.
- Round 5's m3 is **fixed**: `_pinned_log_timetag` now deletes the attribute when the class did not own one, and `test_the_pin_leaves_the_class_dictionary_as_it_found_it` and `test_a_flavor_pinned_once_still_sees_a_pin_taken_above_it` both fail against the unconditional restore. Round 5's M1 (the four test docstrings) is fixed and committed.

### (4) The `re_validate.py` unfreeze — the sweep, and the ratchet

Grepped `re_validate` across every `.md`, `.mdc`, `.toml`, `.yml`, `.py` in the
repository. Every **live** document is corrected: plan ground rule 7 and its four
other mentions, overrides deviation (6) and its six justification rows, the
`pyproject.toml` header, the PR-25 sub-plan, and this record. The residual hits are
in `plans/archive/`, `phase5-validation.md`, the PR-24 sub-plan, the PR-13
sub-plan and the round-1…5 critiques — historical records that describe the state
when they were written — and in the *statement* halves of deferred entries 99 and
102, each of which is followed by a `RESOLVED` paragraph in the same commit that
corrects it. **No live document still claims the file is frozen.** The one thing
the sweep did not reach is M1, which is about a ruff count rather than the freeze.

The ratchet, parsed with `tomllib`:

| | `ab1fa3b` | `540447f` | `01a083d` |
|---|---:|---:|---:|
| entries | 70 | 69 | **69** |
| code slots | 198 | 193 | **193** |

No new key, no widened value; the one removed key is `pds4archives.py`.
`_common.py`, `tests/core/test_log_path_timetag.py` and
`tests/holdings_maintenance/test_common_versioning.py` have **no entry** and report
**zero** findings with the ratchet emptied, so none needs one. `re_validate.py`'s
entry is **byte-identical to the base**: `['B007','C405','E701','E721','I001',
'RUF005','RUF051','RUF059','UP031','UP034']`. No finding in that file was
*fixed*; its `C405` disappeared as a side effect of the authorized race fix, which
the record states in three places. The per-code diff over the whole PR is exactly
`C405 1→0`, `N806 3→0`, `SIM115 3→2`, `UP031 140→126` — **19**, no other code
moved.

### (5) The four updated assertions

All four are assertions in tests **this PR itself added** (`git diff
ab1fa3b..01a083d -- tests/` removes **zero** lines), so nothing pre-existing was
touched. Measured which of the four the change forced:

- `test_pds3_linkshelf`: the old text was `'Link shelf file moved to '` **with a trailing space**, which cannot match `'… moved to: '`. **Forced**, and R1 proves it has teeth.
- `test_pds3_checksums`, `test_pds4_checksums`, `test_pds3_infoshelf`: the old texts were `'… moved to'` with no trailing space, which are substrings of the new output and would still pass. **Voluntary tightenings.**

Every one is strictly stronger than what it replaced, and the `'… moved from: '`
assertions were left alone and still pass. Nothing is papered over.

### (6) Everything else that was checked and held

- **Every number in §3, §6, §6.1, §6.2 and the section table is exact**, re-derived with `ast`: `pdsarchives` 565→**255** lines / 307→**137** statements, `pds4archives` 590→**275** / 316→**143**, `_common.py` **666**/**276** (676/316 at `540447f`), the six tools 6,751→**6,399** lines and 3,360→**3,162** statements from `b84fe75`, the versioning section 151→**127** lines and 93→**48** statements, and the section table 31+75+219+214+127 = **666** against measured banner boundaries.
- **Id arithmetic:** collected at both heads — `ab1fa3b` **892**, `01a083d` **966**. Full holdings run at head: **932 passed / 34 skipped**. Per class: `TestPinnedLogTimetag` 8, `TestLogPathsFor` 5, `TestTheIndexshelfDedupe` 4, `test_common_versioning` module level 43, `TestTheTwoLogLines` 6, `TestReportingUnderAnInfoCap` 4, plus the four regression tests. 8+5+4+43+6+4+4 = **74**. No-holdings run: **162 passed / 804 skipped**. Every figure to the id.
- **§11.6's five mutations reproduce exactly**: my R1/R2/R3/R13/R14 give 3/3/3/8/4 failures, the record's table gives 3/3/3/8/4.
- **API freeze:** `pytest tests/api/` passes 26 ids; none of `api_manifest.json`, `manifest_allowlist.json`, `dump_public_api.py`, `test_api_freeze.py` is in the PR diff.
- **Constraints:** `ruff check` and the preview `E111,E112,E113` gate both pass; `ruff format --check` still reports `_common.py` as unformatted, which is the proof it was not run; no golden or baseline in the diff; no `skip`/`xfail` added; no f-string logging call introduced (the six that exist in `pdsindexshelf`/`pds4indexshelf` predate the PR and are not in its diff); no `[*x, y]`; no plan/critique/PR/phase reference in any changed source or test file; no hard-coded holdings root in `src/`, `tests/` or `.github/`.
- **Comments:** a `tokenize` multiset diff of `_common.py` over `540447f..01a083d` shows exactly one reworded text (`move_old_*()` → `move_old()`, which had to change) and one new three-line comment inside `move_old`. Nothing else moved, and `hashfile`'s stack-overflow attribution travelled with the function.
- **`pdsdependency`'s announce-one-path-write-another quirk** (`logfile.replace('/volumes/', '/')` after the `Log file:` line) is identical on both sides — pre-existing, not this round's.

## Verdict

**The code is sound, and the round's headline claim is true.** An independent
harness 24 invocations larger than the author's, covering three tools the author's
gate does not, finds the same two classes of changed line and **nothing else** —
equal line counts, identical exit codes, identical log-file paths, identical
artifacts. The `move_old` collapse is a faithful merge: twelve mutations, eleven
caught, and the one that was not is a defensive guard no caller reaches. The race
is fixed at all fifteen sites, the set→list change breaks no consumer and removes
a real double-versioning bug, and the `re_validate.py` unfreeze sweep reached every
live document.

**The record is one round behind itself again.** M1 is the sharpest: the two
documents that carry the ratchet's shrink-only contract disagree by one finding
*inside the commit that edited one of them*, and it is the `.mdc` — the one the
next shrink is measured against — that is stale. M2 and M3 are the recurring
class: a control claim and ten-plus citations that were true at the previous head
and were not re-measured at this one, under a section heading that promises they
were. The mechanism is mechanical and so is the fix; three rounds of hand
correction have now failed to hold, and the citations should be generated.

None of the nine is a reason to distrust the migration. All nine are reasons the
record should be corrected before merge, and m1 is a one-word fix in a file that
ships.
