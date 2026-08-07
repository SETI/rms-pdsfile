# PR-27 validation — migrate the indexshelf and linkshelf pairs onto the core

Base `2265393` (`rewrite`). Every number below names the command that produced it.
Nothing is inherited unless it says so.

Both worktrees are venv-less and the main checkout carries an editable install, so
every command set `PYTHONPATH=$PWD/src`, and the tree was proved rather than
assumed:

```
$ cd /seti/all_repos/rms-pdsfile-pr27/work
$ PYTHONPATH=$PWD/src python -c "import pdsfile; print(pdsfile.__file__)"
/seti/all_repos/rms-pdsfile-pr27/work/src/pdsfile/__init__.py
```

## 1. What changed

Four tools become thin: a `ToolSpec`, a task table, and a `main()` that calls a
driver. Their shared code goes into two new family modules; the pds3 `REPAIRS`
table goes into a data module of its own.

`wc -l`, base and head:

| module | base | head |
|---|---:|---:|
| `_common.py` | 337 | 370 |
| `_archives_common.py` | 242 | 242 |
| `_shelf_common.py` | 539 | 523 |
| `_indexshelf_common.py` | — | 617 |
| `_linkshelf_common.py` | — | 712 |
| `pds3/pdsindexshelf.py` | 548 | 52 |
| `pds4/pds4indexshelf.py` | 538 | 56 |
| `pds3/pdslinkshelf.py` | 1,730 | 471 |
| `pds4/pds4linkshelf.py` | 1,224 | 524 |
| `pds3/linkshelf_repairs.py` | — | 555 |
| **total** | **5,158** | **4,122** |

The four tool modules go from 4,040 lines to 1,103. Every module in the table is
under deviation (3)'s 1,000-line limit; one module in `holdings_maintenance/` is
still over it and this PR does not touch it — `pds3/pdsdependency.py`, 1,165 lines
at both revisions. Deferred entry 66 named three modules over the limit; two of the
three are `pdslinkshelf.py` and `pds4linkshelf.py`, and this PR brings both under.

## 2. Three drivers, and why the index shelf tools needed the third

`_common.run_main` exits; `_shelf_common.run_selection_main` returns.
`_indexshelf_common.run_index_main` is new and exits.

**The link shelf pair runs on `run_main`.** Their targets are unit directories with
no file selection, their log path is one fixed method with a `_links` suffix, and
they end in `sys.exit(status)` — which is exactly what `run_main` does. Two things
had to move for the fit, both enumerated in §5: the task name in the log header
loses its quotes, and `set_log_dirs` is now called by the driver rather than by
each `main()`.

**The index shelf pair does not fit either.** Measured against `run_main`, three of
their four differences are data and one is not:

| difference | data? |
|---|---|
| the positional is `table`, not a unit | yes — `ToolSpec.unit` |
| `log_path_for_index` takes no suffix | yes — the driver reads `spec.log_path_method` and passes `spec.log_suffix` only when it is non-empty |
| per-target handlers go in the tool's own log directory, not the target's | no field — a rule this driver states, and the reason it is a driver rather than a flag |
| a backup copy of a table is logged and skipped, per target | **no** |

The last one is the one that decides it. The skip has to happen **inside** the log
hierarchy: `logger.error('Backup file skipped', …)` is what makes the run's exit
status 1, and an error logged before the top-level `logger.open()` is at a level
that never gets closed and so is never counted. Moving the check into
`expand_target` — the only data-shaped place `run_main` offers — would therefore
change the tool's **exit code**, which is frozen. Keeping it where it is inside a
shared `run_main` needs a boolean saying "this tool skips backups", which is
precisely the shrug-flag the data-only `ToolSpec` rule forbids. PR-26 set the
precedent for the alternative when `run_selection_main` was added for the same kind
of reason.

`ToolSpec.index_ext`, declared by PR-25 and read nowhere, is now read: it is what
makes one `index_targets()` serve both flavors (`*.tab` / `*.csv`, and the
`No .tab files in directory:` message). So are `log_path_method` and `log_suffix`,
which this driver honours rather than hardcoding.

**What the third driver costs, measured.** With docstrings stripped,
`run_index_main` is 67 lines against `run_main`'s 66, and 45 of them are
line-identical — 67% duplication, the same trade PR-26 made for
`run_selection_main`. Of the four ways the two drivers differ, two are forced (the
backup skip, and the log directory) and **two are preservation**: the index tools
write `Task "initialize" for` with quotes, which is what both of them wrote at the
base and what `run_main` does not write, and they pass the logger to the task
explicitly, which is what `pds4indexshelf` did. Unifying either would have cost a
log line these tools have always written, or a `run_main` change reaching the
archives pair. Recorded so the count is four rather than one.

## 3. What is shared, and what stayed in the tools

`_indexshelf_common.py` holds the whole of both index shelf tools except their
specs: `generate_indexdict`, `write_indexdict`, `load_indexdict`,
`validate_indexdict`, the five tasks, `index_targets` and `run_index_main`. The
two flavors differed only in the `PdsFile` class, the table extension, the handler
set, and the text differences enumerated in §5.

`_linkshelf_common.py` holds `LinkInfo`, `link_text_of`, `read_links`,
`locate_nonlocal_link`, `locate_link_with_path`, `load_links`, `write_linkdict`,
`validate_links`, the five tasks and `link_targets`. **`generate_links` stays in
each tool** — 346 lines in pds3 and 437 in pds4, and the one function where a PDS3
label and a PDS4 label genuinely say different things — and each tool names its own
in its spec. So does the pattern that recognizes a label's reference to its data
file (`ToolSpec.link_target_regex`): `^ *\^?\w+ *= *…` for PDS3,
`^ *<file_name>…</file_name>` for PDS4.

Measured before any of it was written, with an AST walk over both modules and
`difflib.SequenceMatcher` on each function's source: every link shelf function
except `generate_links` scored 0.95 or better between the two flavors, and
`generate_links` scored 0.82. That is the seam.

### The `REPAIRS` move, and the asymmetry that is deliberate

`pds3/linkshelf_repairs.py` is the table and nothing else. Content-unchanged,
proved two ways:

```
$ sed -n '36,571p' <base>/src/.../pds3/pdslinkshelf.py | md5sum
f2ba87b0154b970a7249411e6c653869
$ sed -n '20,555p' <head>/src/.../pds3/linkshelf_repairs.py | md5sum
f2ba87b0154b970a7249411e6c653869
```

536 lines, byte-identical. And the *parsed* structure, canonicalized so that it does
not depend on object identity (a `TranslatorByDict`'s `repr` carries its address,
which is why the naive hash differs between two runs of the same tree):

```python
def canonical(obj):
    if isinstance(obj, translator.TranslatorByDict):
        return ('ByDict', canonical(obj.dict), canonical(obj.path_translator))
    if isinstance(obj, translator.TranslatorByRegex):
        return ('ByRegex', canonical(obj.tuples))
    if isinstance(obj, (list, tuple)):
        return tuple(canonical(o) for o in obj)
    if isinstance(obj, dict):
        return tuple(sorted((canonical(k), canonical(v)) for k, v in obj.items()))
    if hasattr(obj, 'pattern') and hasattr(obj, 'flags'):
        return ('regex', obj.pattern, obj.flags)
    return repr(obj)

text = repr(canonical(pdslinkshelf.REPAIRS))
print(len(pdslinkshelf.REPAIRS.tuples), hashlib.sha256(text.encode()).hexdigest(),
      len(text))
```

```
base: 141 a95ed0d2d23080f8e0f03c66b8275cbc99e220c68b2fe84047d00777b3031c62 33116
head: 141 a95ed0d2d23080f8e0f03c66b8275cbc99e220c68b2fe84047d00777b3031c62 33116
```

141 top-level entries, same canonical fingerprint. The new module adds `import re`
and `import translator` above the table, because the table's flags are `re.I`; no
line of the table itself changed.

**`pds4linkshelf`'s `REPAIRS` gets no data module, deliberately.** It is
`translator.TranslatorByRegex([])` — one line, empty, read once. A file for it would
be symmetry for its own sake. The asymmetry is a decision, not an oversight.

## 4. Deferred entries 3 and 4

### Entry 4 — fixed

`pds4linkshelf --update` raised `AttributeError: 'tuple' object has no attribute
'linktext'` against any existing shelf. `generate_links()` is handed the loaded
shelf as `old_links`; its values are the plain tuples that were pickled, and the
"identify labels for files" loop dereferenced `info.linktext` on them. The pds3
twin never had the bug because it has no such loop.

The fix is one accessor, `_linkshelf_common.link_text_of(info)`, returning
`info.linktext` for a `LinkInfo` and `info[1]` for a tuple — the same idiom the
merge step three hundred lines below already uses (`isinstance(item, LinkInfo)`).

**The pin, inverted.** `test_pds4_linkshelf.test_update_is_broken_and_repair_is_the_working_path`
asserted the broken behaviour. Before:

```python
    run = support.run_tool(shelved_tree, 'pds4linkshelf', '--update',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert "'tuple' object has no attribute 'linktext'" in run.output, run.describe()
```

After, as `test_update_picks_up_a_new_file`:

```python
    run = support.run_tool(shelved_tree, 'pds4linkshelf', '--update',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert "'tuple' object has no attribute 'linktext'" not in run.output, run.describe()
    assert 'extra_added_by_tests' in support.sidecar_text(shelved_tree.path(SIDECAR))
```

Two tests were added beside it rather than folded into it, because "does not raise"
is a weak thing to assert: `test_repair_also_picks_up_a_new_file` covers the other
route to the same shelf, and `test_update_and_repair_agree_on_the_shelved_links`
asserts the merged shelf equals the rebuilt one. Without the third, the merge could
drop or duplicate an entry and still leave `--validate` clean, because `--validate`
compares the shelf against a fresh scan of the same tree.

**Those three tests pin that the update completes and agrees with a rebuild; they
do not pin what the accessor returns.** Probed rather than assumed: with
`link_text_of` replaced by `return ''`, all three still pass. The loop that reads
it only assigns a label when a *newly appeared* file's basename matches a link in
an *already shelved* label — and every file a shelved label links to is itself
already shelved, so on `--update` it is skipped before the loop is reached. The
loop is *entered* for every candidate basename, which is why the `AttributeError`
fired; its assignment is not reachable from any state the declared PDS4 subset can
produce.

So the accessor's value is pinned directly, in
`test_shelf_common.TestLinkTextOf` — a freshly found link reads as its link text, a
shelved tuple reads as its link text, the two shapes of one link read the same, and
a repaired `linkname` does not change what is read (what gets pickled is
`linktext`). Negative control: `return ''` fails three of those four, and the fourth
is the one that compares the two shapes and so cannot discriminate a constant.

### Entry 3 — scoped, not fixed, and its diagnosis corrected

The entry says `generate_indexdict()` builds a `pdstable.PdsTable` from
`pdsf.label_abspath`, "a PDS3 detached-label reader". **That is not what `PdsTable`
is.** Measured at the base:

```python
>>> import inspect, pdstable
>>> 'self._is_pds4_lbl = is_pds4_label(label_file)' in inspect.getsource(pdstable.PdsTable.__init__)
True
```

`PdsTable.__init__` dispatches on `is_pds4_label()` and builds a `Pds4TableInfo` for
a PDS4 label. There is no wrong reader to replace. The two failures are two
different things, and neither is in `pds4indexshelf`:

**`uranus_occs_earthbased`: the tables have no label at all.**

```
label_abspath = ''        for .../uranus_occ_u0_kao_91cm_rings_index.csv
FileNotFoundError: File does not exist: <cwd>
```

There is nothing for any reader to read. Shelving these would mean deciding that a
PDS4 index shelf is built from the `.csv`'s own header row instead of from a label
— a decision about the PDS4 metadata contract, not a repair. And it would not be
enough: the *consumer* has the same shape. `_index_rows.py`'s `child_of_index()`
builds `pdstable.PdsTable(label_file=self.label_abspath, …)` to turn a shelved row
number into a row, so a shelf built without a label could not be read back. Any fix
spans the tool and the core.

**`cassini_uvis_solarocc_beckerjarmak2023`: the label is stale.** `PdsTable` parses
its `.xml` correctly as PDS4. The `ValueError: row count mismatch` is a real
disagreement between the label and the file:

```
label rows        : 41        file data records  : 41
label header_bytes: 885       actual header len  : 1074
label fields      : 35        header columns     : 41
```

The label declares a 885-byte header and 35 fields; the file's header line is 1,074
bytes and carries 41 columns. `PdsTable` seeks 885 bytes in, lands in the middle of
line 1, and reads 42 lines where the label says 41. Repairing that is a data fix (or
a `pdstable` change), not a `pdsfile` one.

**So entry 3 stays open, re-scoped.** No shelf-building change would have made
either bundle set shelvable, and one of the two failures is not a software defect at
all. `test_pds4_indexshelf.test_initialize_cannot_read_a_pds4_index` stays as it is;
its docstring and the module header, which repeated the wrong diagnosis, are
corrected. Deferred entry 3 is rewritten with the measurements above.

Corroborating: `ls /seti/opus/pdsdata/pds4-holdings/` shows `bundles diagrams
metadata previews` and no `_indexshelf-metadata/` — no PDS4 index shelf has ever
been built in this tree either.

## 5. Behavior changes, enumerated

Every one of these is a log or output **text** change except the last three.

1. **The link shelf task header loses its quotes.** `Task "validate" for:` becomes
   `Task validate for:`, in the `HEADER` line and the matching `SUMMARY | Completed:`
   line, for both flavors. Forced: `run_main` writes the unquoted form for the
   archives pair, and keeping both would need a format flag. The unquoted form was
   chosen over changing `run_main` because the archives tools are already migrated
   and validated, and `test_task_flags.task_announced()` already strips quotes so
   both forms parse. **226 lines of the transcript.**
2. **`pdsindexshelf` stops emitting a blank line before each target's header.** It
   passed `blankline=True` to `logger.open()`, which emits unconditionally; every
   other tool, including `pds4indexshelf`, emits one only when there is more than
   one target. The shared driver does the latter. Visible only in single-target runs,
   which is most of them. **16 lines.**
3. **`pdsindexshelf` adopts `pds4indexshelf`'s `Validation failed for:` line.** The
   pds4 flavor logged an ERROR naming the file before listing the per-key
   disagreements; the pds3 flavor did not. One shared `validate_indexdict` means one
   of them changes, and the line makes a failure attributable when a whole metadata
   directory is validated in one run. **2 lines, plus 6 message-count lines that
   follow it.**
4. **`pds4indexshelf` adopts `pdsindexshelf`'s key-mismatch indentation.** `\n    table:`
   / `\n    shelf:` rather than `\n table:` / `\n shelf:`, so the two values line up
   under the key. Not reached by any transcript scenario (no pds4 index can be
   shelved, see §4), so 0 lines there; it is a real change all the same.
5. **The two index shelf tools' `--log` help names the directory they use.** It said
   `Logs are created inside the "index" subdirectory`; they have always written into
   `pdsindexshelf/`. The shared `LOG_HELP` substitutes `progname`, so the text now
   says `"pdsindexshelf"`. **6 lines** (the sentence rewraps).
6. **The two index shelf tools no longer `print(sys.exc_info()[2])`.** That prints
   the `repr` of a traceback object — `<traceback object at 0x7f…>` — to stdout.
   PR-26 removed the same line from the two infoshelf tools. **3 lines.**
7. **A traceback inside any of these four tools names the shared driver's frames.**
   Unavoidable, and the same class PR-25 and PR-26 enumerated. **118 frame lines,
   92 source lines under them, 38 caret rows, 2 traceback headers.**
8. **`pds4linkshelf --update` succeeds where it raised** (entry 4). **67 lines**,
   including three `exit=1 → exit=0`.
9. **`pdslinkshelf.validate_links` no longer swallows an exception raised inside
   it.** pds3 ended `finally: return logger.close()`; a `return` in a `finally`
   discards the exception the `except` clause re-raised. pds4 assigned and returned
   after the block. The shared function takes pds4's form, which retires `B012` from
   `pdslinkshelf`'s ratchet entry. Not reachable by any scenario here — the function
   body only sorts and compares dictionaries — so 0 transcript lines.
10. **`pdslinkshelf.initialize` loses a dead `move_old` call.** It sat after a
    guard that returns when the shelf file exists, so it could only run if
    `generate_links` had created one; it does not. pds4 had no such call.
11. **`limits` now reaches the `initialize` fallback in all six places.** When
    `reinitialize`, `repair` or `update` finds no shelf file it falls back to
    `initialize`, and three of the six pds3 call sites dropped the caller's `limits`
    on the way (`pdsindexshelf.reinitialize` and `.repair`, `pdslinkshelf.update`);
    all four pds4 sites had no `limits` at all. The shared tasks pass it everywhere.
    Invisible from the command line, where the driver never passes limits; visible
    to a library caller that does.
12. **A command-line path that does not exist is now reported as an absolute path.**
    `run_main` calls `os.path.abspath()` before the existence check; the two link
    shelf `main()`s checked the raw string first. Reachable only with a relative
    path that does not exist. This is the behaviour PR-25 already gave the archives
    pair.

13. **A link shelf run over a unit set whose only other child is a file loses one
    blank line.** `link_targets()` filters a unit set's non-directory children out
    of the target list, where the old `main()`s kept them in the list and skipped
    them in the loop; the blank line between targets is emitted when there is more
    than one target, so a set holding one unit directory plus a readme drops from
    two targets to one and the line goes. **2 lines** of the transcript, in the
    `pds3-link-metadata-volset` scenario.

    **This was first measured over the wrong population and reported as a
    non-event.** The first count — "0 of 54 unit sets have a non-directory child" —
    covered `volumes`, `calibrated` and pds4 `bundles`. It left out `metadata`,
    which is one of the three voltypes a link shelf run is pointed at
    (`re_validate.py:44` `LINKSHELF_VOLTYPES`, and
    `update_holdings_for_new_metadata.sh:40` runs `pdslinkshelf --initialize` on
    `metadata/$VOLSET` directly). Re-measured over every category `link_targets`
    accepts, on the same two roots:

    | category | unit sets | with a non-directory child | where the blank line moves |
    |---|---:|---:|---:|
    | `holdings/volumes` | 52 | 0 | 0 |
    | `holdings/calibrated` | 6 | 0 | 0 |
    | `holdings/metadata` | 96 | 96 | 17 |
    | `pds4-holdings/bundles` | 2 | 0 | 0 |
    | `pds4-holdings/metadata` | 2 | 0 | 0 |
    | **total** | **158** | **96** | **17** |

    Every `metadata/*` unit set carries an `AAREADME.txt`, and 17 of them hold
    exactly one unit directory beside it, so the change happens on 17 real targets
    of a documented workflow in this tree. The transcript did not cover a metadata
    unit set at all; a 27th scenario was added (`pds3-link-metadata-volset`, an
    `AAREADME.txt` beside the unit directory), and the two lines above are what it
    reports. This is the same trade `pdsarchives.archive_targets()` has made since
    PR-25.

### Four more differences in merged code, all measured to be no-ops

Enumerated for completeness, since "every changed line" is the rule:

- `validate_links` uses `isinstance(dirinfo, list)` where pds3 wrote
  `type(dirinfo) is list`. Both values are plain `list`s built by `load_links` and
  `generate_links`, never a subclass, so the two tests agree on every value this
  code sees. pds4 already wrote `isinstance`.
- `validate_infodict` is renamed `validate_indexdict`. It never validated an info
  dict; it is called from `index_validate` only, and `holdings_maintenance` carries
  no frozen API surface.
- `run_index_main` passes `logger=logger` to the task where the base
  `pdsindexshelf.main()` passed none. `PdsLogger.get_logger(LOGNAME)` returns the
  instance `PdsLogger(LOGNAME)` registered, and both use the same name, so the task
  received the same object either way. Verified:
  `PdsLogger('x') is PdsLogger.get_logger('x')` is `True`.
- `_common.set_log_dirs` is **not** called by `run_index_main`. It was, briefly;
  nothing in the index shelf family calls `move_old` — `write_indexdict` writes
  directly — so the list would have been written and never read. Dropped as dead.

## 6. The split, by measurement

Deferred entry 98 settled the structure (one module per family) and the trigger (the
first family whose extraction takes a module past deviation (3)'s 1,000 lines splits
it). The shared code was written into `_shelf_common.py` first, and measured:

```
$ wc -l src/pdsfile/holdings_maintenance/_shelf_common.py
1827
```

1,827 against a limit of 1,000, so it split. After the split:

```
$ wc -l src/pdsfile/holdings_maintenance/_*.py
   242 _archives_common.py
   370 _common.py
   617 _indexshelf_common.py
   712 _linkshelf_common.py
   523 _shelf_common.py
```

(523 + 617 + 712 = 1,852 rather than 1,827: the two new modules each gained an
11-line header and an import block.)

### The re-derived rate, and why it should not be used again

Entry 98's rate was 18.5% — the archives family contributed 214 lines of shared code
out of a 1,155-line pair. PR-26's executor reported the projection ran high and asked
PR-27 to re-derive it. It re-derives to something else again:

| PR | pair lines at that PR's base | shared code added | rate |
|---|---:|---:|---:|
| PR-25 (archives) | 1,155 | 214 | 18.5% |
| PR-26 (checksums + infoshelf) | 3,445 | 415 | 12.0% |
| PR-27 (indexshelf + linkshelf) | 4,040 | 1,329 | 32.9% |

PR-26's numbers are inherited from entry 98 and `critiques/pr-26-validation.md`
(`_common.py` 666 → 1,081 with the shared code in it). PR-27's are `wc -l` above.

Entry 98's rate projected **748** lines for these two pairs; the measurement is
**1,329** — the projection is short by 581 lines, 44% of the measurement. It ran
high for PR-26 and short for PR-27, which is the point:
the fraction of a pair that can be shared is not a property of the migration, it is a
property of how alike the two flavors of that particular tool happen to be. The index
shelf pair was almost identical (56.8% of its 1,086 lines became shared code); the
link shelf pair was not (24.1% of 2,954, or 29.4% with the `REPAIRS` table excluded
from the denominator, because it moved somewhere else entirely).

**What it means for PR-28:** nothing, and not because the rate is unusable. PR-28
(`crlf`, `shelf_consistency_check`, `show_opus_products`) has no pds3/pds4 pair at
all — none of those three tools has a twin — so there is no family module to size and
no split to trigger. The rate is worth recording only so that the next PR that does
migrate a pair measures its own instead of projecting.

### Deferred entry 114, re-measured

Entry 114 asked PR-27 to re-measure whether `_shelf_common.py` still serves two
disjoint audiences. It does, and now less so: at 523 lines it holds the versioning
helpers (`move_old`, `VersionedFile`, the three kinds, `next_version_dest`,
`hashfile`) that six tools reach regardless of driver, plus `run_selection_main` and
its two path helpers, which four tools use. The link shelf tools now reach it for
`LINKSHELF_LOGNAME`, `LINK_SHELF`, `move_old` and `UNIT_LOG_PATH_METHOD` only. The
seam entry 114 named is still there and still under half the limit; nothing forces a
second split.

## 7. Gates

### 7.1 Full data suite

Command lines exactly as `scripts/automated_tests/pdsfile_main_test.sh` runs them,
plus `-rA --junitxml`, with `PYTHONPATH=$PWD/src`, at base and head:

```
pytest tests/api/ tests/core/ tests/holdings_maintenance/ tests/pds3file/ \
       tests/rules/pds3/ tests/pds4file/ tests/rules/pds4/ --mode ns -rA --junitxml=…
pytest tests/pds3file/ tests/rules/pds3/ --mode s -rA --junitxml=…
```

| | base | head |
|---|---|---|
| `--mode ns` | 1,079 ids — 1,045 passed, 34 skipped | 1,094 ids — 1,060 passed, 34 skipped |
| `--mode s` | 558 ids — 555 passed, 3 skipped | 558 ids — 555 passed, 3 skipped |

The comparison is of the per-test **id-to-outcome map**, parsed out of the two
`junitxml` files, not of counts:

- **`--mode s`: identical.** Same 558 ids, same outcome for every one.
- **`--mode ns`: no outcome changed for any id present in both runs — zero.** A
  newly-passing test would have been as much of a flag as a newly-failing one; there
  were neither.
- **1 id removed**, deliberate:
  `test_pds4_linkshelf::test_update_is_broken_and_repair_is_the_working_path`, the
  entry-4 pin, inverted in §4.
- **16 ids added**, all passing: the inverted pin as
  `test_update_picks_up_a_new_file`, the two tests added beside it
  (`test_repair_also_picks_up_a_new_file`,
  `test_update_and_repair_agree_on_the_shelved_links`),
  `test_re_validate::test_the_sibling_tools_really_accept_what_this_module_calls_them_with`
  (§7.4), eight parameter cases of the two `test_shelf_common.py` tests over the
  four migrated tools, and the four `TestLinkTextOf` tests. The last twelve came
  out of the round-1 reviews (`critiques/pr-27/round-1.md`, CodeRabbit finding 5
  and reviewer finding m3).

The base figures were measured here, not inherited; they match the ones PR-26
reported (1,079 and 558) exactly.

### 7.2 Real runs of all four tools

81 records — three per scenario (`SCENARIO`, `LOGFILES`, `ARTIFACTS`) over 27
scenarios, covering every task of every one of the four tools against a disposable
copy of the byte-verified subsets `tests/holdings_maintenance/subsets.py` declares:
`--initialize`, a second `--initialize`, `--validate` clean, `--validate` over a
corrupted target, `--repair`, `--validate` again, a cancelled `--repair`, a
`--repair` after the source is touched, `--reinitialize`, `--update` with a new
file, a cancelled `--update`, `--update` over a whole metadata directory, two task
flags at once, a unit-set target, a **metadata** unit-set target carrying a
readme, a metadata-directory target, a backup-named copy of a table, `--help`, a
missing task, a checksums path, an archives path, a non-metadata path, a non-table
file, and a nonexistent path.

Normalization: temporary paths, the tree path, wall-clock timestamps, log-file time
tags, elapsed times, the "out of date N days/minutes" delta, traceback **line
numbers**, and the address inside `<traceback object at 0x…>`. Traceback **file
names** were deliberately left alone.

**A base-versus-base control was run first.** The first attempt found 2 of the
records differing — both `SCENARIO` records of `pds4indexshelf`, and both because
`print(sys.exc_info()[2])` writes a traceback object's `repr`, which carries its
memory address. That is not a code difference; it is the line change 6 above,
found by the control rather than by reading. With that address normalized:

```
base run 1 vs base run 2 :   0 of 81 records differ
base      vs head        :  32 of 81 records differ
```

**Every changed line attributed — 594 lines, none unattributed.** The classifier is
in the scratch harness and prints its own residue; the residue is zero.

| lines | cause |
|---:|---|
| 242 | the link shelf task header loses its quotes (change 1) |
| 118 | traceback frame naming the shared core (change 7) |
| 92 | the source line a traceback shows under one of those frames |
| 73 | `pds4linkshelf --update` merges instead of raising (entry 4) |
| 38 | caret rows under those frames |
| 10 | the blank line `pdsindexshelf` no longer emits (change 2) |
| 6 | message counts following a line above |
| 6 | the index shelf `--log` help naming its real directory (change 5) |
| 3 | the removed `print(sys.exc_info()[2])` (change 6) |
| 2 | `pdsindexshelf` adopting `Validation failed for:` (change 3) |
| 2 | the blank line a link shelf run drops for a unit set with one unit and a file (change 13) |
| 2 | traceback headers, gone with the exception they reported |

An earlier pass of this classifier put all 16 blank-line differences under change
2. Six of them are in the `pds4-link-update` record, where the run stops raising
and so runs to the end, and two more are change 13 — so the honest split is 10 / 6
/ 2 rather than 16 / 0 / 0. Corrected here rather than left standing, because a
blank line attributed to the wrong cause is exactly the kind of defect this table
exists to prevent.

**`ARTIFACTS`: 1 of 27 records differs, and it is the fix.**
`pds4-link-update.ARTIFACTS` gains the new file's entry in the sidecar
(`"data/rings/u0_kao_91cm_extra.txt" : "",`), the shelf grows from 914 to 952 bytes
and its sidecar from 961 to 1,029, and the superseded pair is versioned into the
log directory as `…_links_v001.pickle` / `…_links_v001.py`. The other 26 artifact
records are byte-identical: nothing else these tools write changed.

### 7.3 The rest

- **`scripts/run-all-checks.sh -c -s`, with no holdings variables set** and
  `VENV=/seti/all_repos/rms-pdsfile/venv`: all checks passed. The pytest gate
  reported `no holdings: holdings-free subset only` and `268 passed, 814 skipped`;
  ruff check, ruff indentation, pyroma, API freeze and the clean-install gate all
  passed.
- **`pytest tests/api --mode ns`: 26 passed.** The four frozen files are
  byte-identical to `2265393` (`git diff --quiet 2265393 -- <path>` for each).
- **Ruff, configured gate:** `ruff check src/pdsfile tests scripts` and
  `ruff check --preview --select E111,E112,E113 src/pdsfile tests scripts` both
  clean.
- **`bandit` and `vulture` were not run.** They are permanently disabled and not
  installed.

## 8. Ratchet

Command lines, at base and at head:

```
$ python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb'));
             p=d['tool']['ruff']['lint']['per-file-ignores'];
             print(len(p), sum(len(v) for v in p.values()))"
$ ruff check --config 'lint.per-file-ignores = {}' src/pdsfile tests scripts
```

| | base | head |
|---|---:|---:|
| entries | 69 | 67 |
| code slots | 184 | 181 |
| findings with the ignores disabled | 2,271 | 2,250 |

**Three slots retired, and which was measured per file** with
`ruff check --config 'lint.per-file-ignores = {}' --statistics <file>`:

| file | base entry | head |
|---|---|---|
| `pds3/pdsindexshelf.py` | `['UP031']` | entry gone — 0 findings |
| `pds4/pds4indexshelf.py` | `['UP031']` | entry gone — 0 findings |
| `pds3/pdslinkshelf.py` | `['B012', 'UP031']` | `['UP031']` — 10 UP031, 0 B012 |
| `pds4/pds4linkshelf.py` | `['UP031']` | unchanged — 14 UP031 |

`B012` went with `validate_links`'s `return` inside a `finally` (change 9). The
`UP031` that remain are all inside the two `generate_links` functions, which stay in
the tool modules.

**The three shared modules and the new data module carry no entry at all**:
`_common.py`, `_shelf_common.py`, `_indexshelf_common.py`, `_linkshelf_common.py`
and `pds3/linkshelf_repairs.py` each report 0 findings with the ignores disabled.
Five `%`-format sites that moved into shared modules were rewritten as f-strings
rather than ratcheted, since a new per-file-ignores key is a widen: three `%d`
writes in `write_indexdict`, `LinkInfo.__str__`, and one `%4d` write in
`write_linkdict`. Each was checked to render identically — the row indices are
Python `int`s, measured, not assumed.

### 7.4 What the gates did not catch, and what now does

The migration left the four thin modules with a task **table** and no task
**names**, and `re_validate.validate_one_volume()` calls `pdslinkshelf.validate()`
by name. The full `--mode ns` suite ran green in that state — **1,047 passed, 34
skipped** — and so did `run-all-checks -c -s`.

Nothing in the suite could have caught it. Every test that drives
`validate_one_volume` replaces all five sibling tools with `SimpleNamespace` stubs
(`test_re_validate.py:807`), which is what lets those tests run without holdings and
is also what makes them silent about whether the real functions exist.

Fixed two ways. Each module binds its five tasks under the names it carries them as
a library, and `test_re_validate.py` gains
`test_the_sibling_tools_really_accept_what_this_module_calls_them_with`, which binds
each of the seven calls `validate_one_volume` makes — `inspect.signature(fn).bind(…)`
— against the **real** modules rather than the stubs.

Negative control, so the new test is not vacuous: with
`validate = TASKS['validate']` commented out of `pdslinkshelf.py`,
`pytest tests/holdings_maintenance/test_re_validate.py` reports `1 failed, 85
passed`, and the one failure is that test. Restored, it is `86 passed`.

This is the second time a stubbed collaborator has hidden a real break in this
subsystem; recorded as deferred entry 122.

## 9. Decisions the owner might make differently

1. **The link shelf task header lost its quotes rather than `run_main` gaining
   them.** The other way round — quoting in `run_main` — would have changed the two
   archives tools' log lines instead, and made all ten migrated tools agree. It was
   rejected because the archives pair is already migrated and validated and this PR
   should not move its output, but "all ten agree" is a real argument the other way.
2. **`LOGDIRS` and `set_log_dirs` moved from `_shelf_common.py` to `_common.py`.**
   `run_main` now serves a family that versions the file it replaces, so it has to
   record where the log went, and `_common.py` cannot import `_shelf_common.py`
   (that import runs the other way). The alternative was a `ToolSpec` callable that
   the driver calls per target — a hook, not data. Four `monkeypatch` targets in
   `test_common_versioning.py` moved with it.
3. **The five task functions are exposed as module names in all four tools**, not
   only in `pdslinkshelf` where `re_validate` needs one. Symmetry within a pair, and
   these modules describe themselves as "library and main program"; the alternative
   is to expose only what is called and let the four modules differ.
4. **Entry 3 is deferred rather than fixed**, on the measurements in §4. If the
   owner reads the uranus case as "the tool should read the `.csv` header directly",
   that is implementable — but it also needs `_index_rows.child_of_index()` to stop
   going through `label_abspath`, or the shelf it writes cannot be read back.
5. **`KNOWN_MISSING_LABELS` stayed in `pdslinkshelf.py`.** It is 45 lines of the
   same kind of data as `REPAIRS`, and it could reasonably join
   `linkshelf_repairs.py`. The plan names only `REPAIRS`, and 45 lines does not earn
   a file on the owner's volume rule, so it stayed.
6. **`BACKUP_FILENAME` is still defined in both link shelf tools** even though
   `_common.py` has the same constant, because each tool's own `generate_links`
   reads it. Two of entry 113's ten copies did go — both index shelf tools defined
   one and neither thin module does — so that entry is at eight, not ten. The sweep
   itself is still open and this PR did not do it.


## 10. When each record was taken

Round 1 changed source under `src/pdsfile/` twice — CodeRabbit's findings 3 and 4,
then the adversarial reviewer's m5 and m6 — so §6.6's regeneration rule applies
twice. The `--mode ns` run, the `--mode s` run and the 81-record tool transcript
above were **all re-taken at the final head**, not carried forward, and the
base-versus-base control was re-run with them.
The `--mode ns` id count moved from 1,079 at the base to 1,094 with the sixteen
added tests, still with zero outcome changes for any id present in both runs.