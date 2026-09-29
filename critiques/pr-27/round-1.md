# PR-27 adversarial review — round 1

Two independent reviews ran against the same head: the §6.6 fresh no-context
adversarial reviewer, and CodeRabbit on PR #125. This file records both, the
resolution of every finding, and the rebuttals.

## CodeRabbit (PR #125, first pass)

Five inline findings plus one outside-diff finding, all filed as Trivial. Every
one was answered on its own thread.

| # | finding | resolution |
|---|---|---|
| 1 | `_indexshelf_common.py:282` — the `index_dict is None` checks are unreachable | **rebutted**, deferred entry 126 |
| 2 | `_indexshelf_common.py:584` — no fallback when the tool subdirectory is absent from the log path | **rebutted**, deferred entry 127 |
| 3 | `_linkshelf_common.py:462` — `validate_links` empties both input dictionaries and does not say so | **fixed** in `8b3c939` |
| 4 | `_linkshelf_common.py:638` — `link_update` drops `limits` when it falls back to `link_initialize` | **fixed** in `8b3c939`, and it was five more sites than reported |
| 5 | `test_re_validate.py:1450` — cover all four migrated task namespaces | **covered elsewhere** in `8b3c939` |
| 6 | `pds4linkshelf.py:336-347` (outside diff) — guard the loop against a non-list value from `old_links` | **rebutted**, deferred entry 128 |

### 1 — unreachable `None` checks. Rebutted.

Correct that they are unreachable: `generate_indexdict()` returns a two-tuple or
raises. Both flavors carried the branch before this PR (`pdsindexshelf.py:224`,
`pds4indexshelf.py:221` at `2265393`), so merging them forced no choice.

This PR *did* remove one dead branch — a `move_old()` in
`pdslinkshelf.initialize` sitting after a guard that returns when the shelf file
exists — and enumerated it. The distinction is the one that decides both cases:
that branch was in only **one** of the two flavors, so the merge had to pick;
this one is in **both**, so the merge picks nothing, and removing it is a cleanup
rather than a consequence of the migration.

### 2 — the log-directory `rpartition`. Rebutted.

The line is the two base tools'
`logfile.rpartition('/pdsindexshelf/')[0] + '/pdsindexshelf'`
(`pdsindexshelf.py:497-498`, `pds4indexshelf.py:483-484` at `2265393`)
generalized over `spec.progname`, not new code. It is deliberately not
`os.path.split(logfile)[0]`, which the other two drivers use: `log_path_for_index`
builds a path carrying the table's whole logical path, so splitting would put a
copy of the tool's error handler in every per-table directory.

The suggested fallback has nothing to fall back from. `log_paths_for` is called
with `dir=spec.progname`, a non-empty constant, and `_derived_paths._log_path_for`
appends `[subdir.rstrip('/'), '/']` after a log root that always ends in `/`, so
the built path always contains `/<progname>/`.

### 3 — `validate_links` mutates its inputs. Fixed.

It deletes from both dictionaries as it goes, which is exactly how the last two
loops know what each side lacks. The docstring now says so, says why, and says a
caller needing either afterwards has to pass a copy.

### 4 — `limits` dropped on the fallback. Fixed, and wider than reported.

Measured at the base rather than taken as read: twelve fallback call sites, three
in each of the four tools. **Three** of the six pds3 ones dropped `limits`
(`pdsindexshelf.reinitialize`, `pdsindexshelf.repair`, `pdslinkshelf.update`) and
all six pds4 ones had no `limits` parameter to pass. The six shared tasks now
forward it. Enumerated as change 11 in `pr-27-validation.md`.
Invisible from the command line, where the driver never passes limits; visible to
a library caller that does.

### 5 — cover all four migrated namespaces. Covered, elsewhere.

Extending the `re_validate` test would have blurred what it is for: it pins the
seven calls `validate_one_volume` makes, against the real modules rather than the
`SimpleNamespace` stubs every other test in that module installs. The other three
tools are not among its callees.

The class the finding points at is real, so it is pinned where it belongs.
`tests/holdings_maintenance/test_shelf_common.py` gains two parametrized tests
over all four migrated tools:

- `test_each_migrated_tool_still_carries_its_five_task_names` — each name exists,
  is that tool's own table entry, and binds `(target, logger=, limits=)`.
- `test_each_migrated_tool_binds_its_own_spec_into_its_tasks` — each table entry
  is the family function with that tool's own `SPEC` bound in, and the spec's
  `PdsFile` class matches the flavor.

Negative control: rebinding `pds4indexshelf`'s table to `pdsindexshelf`'s spec
fails the second test for that tool and nothing else (`1 failed, 24 passed`).

### 6 — guard against a non-list `old_links` value. Rebutted.

The finding says itself that it "cannot reach Line 342 today"; the reachability
was then measured rather than assumed. Keys reaching that loop are filtered to
`local_labels_abspath`, the `.xml`/`.lblx` files of the current directory. Every
one of those is put into `linkinfo_dict` with a **list** value by the loop above
(both extensions are in `EXTS_WO_LABELS`), and the merge preserves it: a key in
`linkinfo_dict` keeps its list, and only a key in neither `linkinfo_dict` nor
`label_dict` becomes `''`. A label path with a string value is not a state this
code can produce or read back.

The fix in this PR does not worsen it either: a string value raised
`AttributeError` on `.linktext` before and would raise `IndexError` on `info[1]`
after — the same unreachable branch. Adding an `isinstance` guard means adding a
branch no test can reach on a behaviour-preserving refactor.

## §6.6 adversarial reviewer

One fresh no-context opus-class reviewer, given the plan's PR-27 entry, the ground
rules, the exact diff, and read access to both worktrees and the real holdings.
**Verdict: `goal met`, conditional on M1.** One Major, nine Minor, two Deferred.

The reviewer independently reproduced the `wc -l` table, the frozen-file hashes,
the ratchet arithmetic (including that the retired ignores are provably dead and
that the 2,271 → 2,250 drop decomposes to exactly −20 `UP031` and −1 `B012`), the
`REPAIRS` content-unchanged proof, the record's internal arithmetic, and the
`re_validate` negative control; diffed every moved function against **both** base
originals; and confirmed `--help` is byte-identical for all four tools apart from
the one enumerated `--log` change.

### M1 (Major) — the one "measured and did not happen" claim was measured over the wrong population. Fixed.

The claim was "0 of 54 unit sets have a non-directory child, so no line of the
transcript moves". The 54 was `volumes` + `calibrated` + pds4 `bundles`. It left
out `metadata`, which is one of the three voltypes a link shelf run is pointed at
(`re_validate.py:44` `LINKSHELF_VOLTYPES`; `update_holdings_for_new_metadata.sh:40`
runs `pdslinkshelf --initialize` on `metadata/$VOLSET`). Every `metadata/*` unit set
carries an `AAREADME.txt`.

Re-measured over every category `link_targets` accepts: **158 unit sets, 96 with a
non-directory child, 17 where the blank line moves.** The finding is right and the
consequence is worse than a wrong number — the transcript covered no metadata unit
set at all, so the gate could not have seen it.

Resolved three ways: a 27th scenario (`pds3-link-metadata-volset`) was added to the
transcript and the two lines it produces are now enumerated as change 13; deferred
entry 124 is rewritten with the true population; and the item moved out of the
"did not happen" section into §5's list.

**A second error surfaced while fixing it.** With the new scenario in place, the
classifier's 16 blank-line differences split 10 / 6 / 2: ten are change 2, **six are
in the `pds4-link-update` record**, where the run stops raising and so runs to the
end, and two are change 13. The earlier table put all sixteen under change 2. That
is the same class of defect M1 names — a line attributed rather than measured — and
it is corrected in the record with the correction shown rather than silently
absorbed.

### m2 — the `REPAIRS` hash citation is not reproducible. Fixed.

`sed -n '18,553p'` was the range before `import re` was added to the data module;
`20,555` is what yields `f2ba87b0…`. Claim true, citation wrong. Corrected.

### m3 — the entry-4 pin is weaker than §4 claimed. Fixed.

Reproduced: with `link_text_of` replaced by `return ''`, all seven tests in
`test_pds4_linkshelf.py` still pass. The reason, established rather than assumed:
the loop that reads the accessor only assigns a label when a *newly appeared*
file's basename matches a link in an *already shelved* label, and every file a
shelved label links to is itself already shelved, so on `--update` it is skipped
before the loop is reached. The loop is entered — which is why the `AttributeError`
fired — but its assignment is unreachable from any state the declared subset can
produce. A probe confirmed the obvious construction does not help either: with the
`.tab` removed before `--initialize`, the label shelves an **empty** link list.

So the accessor's value is now pinned directly, in `test_shelf_common.TestLinkTextOf`
(four tests), and §4 says plainly what the three integration tests do and do not
pin. Negative control: `return ''` fails three of the four, the fourth being the one
that compares the two shapes and so cannot discriminate a constant.

### m4 — four unenumerated differences in merged code. Fixed.

`isinstance` for `type(...) is list`, the `validate_infodict` → `validate_indexdict`
rename, `run_index_main` passing `logger=logger` where base pds3 passed none, and
`limits` reaching the `initialize` fallback. All four are behaviour-neutral as
measured; §5 now says so rather than omitting them.

### m5 — dead `set_log_dirs` call. Fixed.

Nothing in the index shelf family calls `move_old` — `write_indexdict` writes
directly — so the list was written and never read. Call dropped.

### m6 — a declared-and-unread spec field, of the kind this PR criticizes. Fixed.

`run_index_main` hardcoded `'log_path_for_index'` while the index specs declared
`log_suffix=''` and no `log_path_method`. The driver now reads both: it takes the
method from the spec and passes the suffix only when it is non-empty, which is how
a spec says its log path takes none. The index specs declare
`log_path_method='log_path_for_index'`. §2's table row is now true rather than
aspirational.

### m7 — the 1,000-line claim was directory-wide and false. Fixed.

`pds3/pdsdependency.py` is 1,165 at both revisions. The sentence is scoped to the
modules in the table and names the exception. Deferred entry 66, which listed three
modules over the limit, is updated: two of the three are `pdslinkshelf.py` and
`pds4linkshelf.py` and this PR brings both under, leaving `pdsdependency.py` — which
has no pds3/pds4 twin, so the consolidation entry 66 was waiting on will never
reach it.

### m8 — entry 113 under-stated. Fixed.

Both index shelf tools defined `BACKUP_FILENAME` and neither thin module does, so
entry 113 is at eight copies, not ten. Both the entry and §9.6 corrected.

### m9 — the third driver is 67% duplicated and two of four differences are choices. Fixed by recording.

Measured independently and confirmed at the head this round reviewed: 45 of
`run_index_main`'s 67 stripped lines were line-identical with `run_main`'s 66. This
round's own m5 and m6 fixes then changed `run_index_main`, and round 3 found the
figure had not been re-derived; at the final head it is **44 of 69**, 64%. Two
differences are forced, two are preservation — the quoted task header both index
tools wrote at the base, and passing the logger explicitly. §2 now gives the count
as four, says which is which, and carries the re-derived measurement; deferred
entry 130 records that this is the second time the trade has been made and that a
third would be worth stopping for.

### m10 — plan/record mismatch. Fixed.

The plan said "six changes" against the record's list; it now says thirteen
enumerated changes and 594 lines. "78% low" is replaced by the unambiguous form:
the projection was short of the measurement.

Round 2 then found two things about this fix. The replacement had missed deferred
entry 123, and the figures it used were themselves stale, having been taken before
this round's own fixes grew both family modules. Round 4 then found that this
paragraph had restated the corrected figures and gone stale in turn.

**So it does not restate them.** The live measurement of the shared-code total, its
rate and the projection gap is in `critiques/pr-27-validation.md` §6 and nowhere
else; the plan's PR-27 entry and deferred entry 123 repeat it and are checked
against the tree mechanically. A round record that carries its own copy of a number
the tree can move is a trap, which is the lesson three rounds took to learn.

### d1, d2 — Deferred, recorded.

`pdsarchives`'s `log_suffix='_links'` is deferred entry 129 — and it is not a PR-25
transcription slip: the tool wrote `log_path_for_volume('_links', …)` before PR-25
too, so PR-25 preserved it faithfully. Entry 128's `IndexError` clause is corrected
to say what iterating a `str` actually does and why the non-raising case is the
worse one.

### Nothing rebutted

Every finding in this review was accepted. M1 in particular was a real hole in the
gate, not only in the prose: the transcript had no metadata unit-set scenario, so
no amount of re-reading the record would have found it.
