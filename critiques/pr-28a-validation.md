# PR-28a validation — the drivers' shared preamble

Base `b8b9703`. Branch `pr-28a-driver-preamble`. Python 3.12.3. Every measured run
set `PYTHONPATH=$PWD/src` and ran from the tree being measured:

```
$ PYTHONPATH=$PWD/src python -c "import pdsfile; print(pdsfile.__file__)"
/seti/all_repos/rms-pdsfile-pr28a/base/src/pdsfile/__init__.py
/seti/all_repos/rms-pdsfile-pr28a/work/src/pdsfile/__init__.py
```

## 1. The premise, verified before acting on it

The three drivers open with the same block. Cut mechanically at `b8b9703` —
`_common.py` 284-308, `_shelf_common.py` 423-447, `_indexshelf_common.py` 528-552,
25 lines each — the shelf and index shelf copies are byte-identical to each other,
and each differs from `run_main`'s copy on exactly two lines:

```
1c1
<     parser = build_arg_parser(spec)
---
>     parser = _common.build_arg_parser(spec)
13c13
<     resolve_log_root(args)
---
>     _common.resolve_log_root(args)
```

Both are the module qualifier, present only because two of the three callers live
outside `_common.py`. (Deferred entry 130 named one of the two; there are two.)

## 2. What changed

`_common.setup_run(spec, argv)` holds the block and returns `(args, logger)`. Each
driver calls it and keeps its own `status = 0`, which is a local its own flow reads
later, not part of setup.

| file | base | head |
|---|---:|---:|
| `src/pdsfile/holdings_maintenance/_common.py` | 372 | 398 |
| `src/pdsfile/holdings_maintenance/_shelf_common.py` | 523 | 501 |
| `src/pdsfile/holdings_maintenance/_indexshelf_common.py` | 620 | 598 |
| `tests/holdings_maintenance/test_driver_setup.py` | — | 52 |

14 of the block's 15 code lines move — `status = 0` is the one that stays — and the
function costs a `def` line and a docstring, so the three source files net **18
lines shorter**. Nothing else changed: no rename, no signature change, no driver
merge. Deferred entry 130's seven forced variation points stand.

## 3. The tool-run capture

Ten tools reach the three drivers — `pdsarchives`, `pdslinkshelf`, `pds4archives`,
`pds4linkshelf` (`run_main`); `pdschecksums`, `pdsinfoshelf`, `pds4checksums`,
`pds4infoshelf` (`run_selection_main`); `pdsindexshelf`, `pds4indexshelf`
(`run_index_main`). The eleventh console script, `pdsdependency`, reaches none of
them. **158 scenarios**: for each tool `--help`, no arguments, a missing task, an
unknown flag, a nonexistent path, a validate before any initialize, all five tasks,
two task flags at once, `--quiet`, and an unreadable target; plus `--archives` on
the four tools that take it and the `--infoshelf` chain on the two checksum tools.
Each tool's holdings tree is rebuilt from the test subsets first, and its artifact
inventory and log-file lines are recorded after its sequence.

Normalized: temporary tree and repo paths, wall-clock times, log-file time tags,
elapsed times, and traceback **line** numbers. Traceback **file** names and
function names are compared verbatim, which is the point.

Two records are compared less than verbatim, both because two runs of the same tree
differ there and neither difference is about the code:

- `ARTIFACTS` compares a `.tar.gz` by its **member list**, not its compressed size.
  The archive carries a directory entry whose modification time is the run's own,
  so the size moves between runs — measured, 143,816 against 143,828.
- `LOGFILES` compares a tool's log lines as a **set**, unioned over every log file
  it wrote, because which file a line lands in and how many files there are both
  depend on which second a run started. Measured on the control before the raw
  total was added: the same 292 lines arrived as 10 files in one run and 11 in the
  next. The **raw line total** is recorded beside the set as a second, cheaper
  check. It is not load-bearing, and the record says so rather than claiming a
  safety net it does not provide: removing `log_paths_for`'s `paths[0] == paths[1]`
  dedup — the duplication its docstring exists to prevent — moves the raw total on
  all ten tools, but it moves the **set** on all ten too, because each driver logs
  one `Log file` line per path. The other shape of duplication is unreachable:
  pdslogger deduplicates handlers by path, so adding a second `file_handler` for
  the same log leaves the byte count unmoved.

**Base versus base first**, two independent runs of the same tree:

```
base run 1 vs base run 2 :   0 differing lines of 6,893
base      vs head        :   0 differing lines of 6,893
```

Byte-identical. Not "attributed" — identical.

**The capture can fail**, checked against throwaway worktrees at head. Every
mutation below is inside `setup_run`, so a capture blind to one would be blind to
the change this PR makes:

| mutation | moves |
|---|---|
| the "Missing task" message becomes "No task" | 20 gate lines |
| the preamble ignores `--quiet` | 410 gate lines |
| `--quiet` ignored only when `--log` is given | 0 gate, **191 probe** |
| only the first of a spec's handler factories is attached | 4 probe lines |
| the handlers are created and never attached | 131 probe lines |
| `spec.pdsfile_cls.set_log_root(args.log)` deleted | 0 gate, 154 probe |

### 3.1 The `--log` probe, and the one input class where the extraction is visible

No scenario above passes `--log`, so the gate reaches the preamble's last four
lines — the ones that build the root handlers — but sees nothing they produce. A
separate **30-scenario probe** covers them: each tool run three times, with a
writable `--log` root, with `--quiet` **and** a writable root, and with a root the
process cannot write into. The tree is not initialized first, so the run logs an
error and the handlers have something to write, and each writable run records the
whole log root — every path, and each file's line count.

The `--quiet`-with-`--log` run is there because it is the one cell of the
preamble's two log branches nothing else reaches: no gate scenario passes `--log`
and no other probe scenario passes `--quiet`. Without it, a preamble that honoured
`--quiet` only when no log root was given produced a byte-identical gate, a
byte-identical probe and a green suite. With it, that mutation moves 191 probe
lines.

Recording the log root's contents is what tells a handler that was **attached**
from one that was merely created, since each opens its file when it is created.
That control fires on **7 of the 10 tools** — measured, not assumed. It does not
fire on `pds4archives`, whose probe run succeeds and logs nothing at WARNING or
above, so its handler files are empty either way; nor on the two index shelf tools,
because `run_index_main` creates its per-target handlers in the tool's own log
directory rather than the target's, so those files are written whether or not the
preamble made them. Seven tools is enough for the control to be a control, and the
three exceptions are named rather than left for a reader to discover.

Those `LOGROOT` records are identical between base and head. The probe's base
versus base is 0 differing lines, and base versus head is **30 added lines, none
removed, none changed** — three per tool, one cause, and all of it in the
unwritable run.

A traceback raised *inside* the preamble names the extracted function, because any
extracted function adds a stack frame. Nothing in the 158 gate scenarios raises
there; the unwritable `--log` root does, from
`logger.add_handler(make_handler(path))`, on all ten tools:

```
   File "$REPO/.../_common.py", line <N>, in run_main
+    (args, logger) = setup_run(spec, argv)
+                     ^^^^^^^^^^^^^^^^^^^^^
+  File "$REPO/.../_common.py", line <N>, in setup_run
     logger.add_handler(make_handler(path))
```

The frame naming the driver is still there and still names the driver; a
`setup_run` frame appears beneath it. This is an observable change to what a tool
prints, on an input class no test and no golden covers, and it is reported rather
than normalized away. Deferred entry 149.

## 4. Test id sets

Full data, `PDSFILE_TEST_HOLDINGS=full`, both modes, per-id outcome diffed:

| | base | head |
|---|---|---|
| `--mode ns` | 1,100 passed, 34 skipped (1,134 ids) | 1,101 passed, 34 skipped (1,135 ids) |
| `--mode s` | 5 failed, 1,095 passed, 34 skipped (1,134 ids) | 5 failed, 1,096 passed, 34 skipped (1,135 ids) |

**One id added, none removed, no outcome change:**
`tests/holdings_maintenance/test_driver_setup.py::test_a_log_root_gets_every_handler_the_spec_declares`.
The five `--mode s` failures are the same five ids at both trees; they are the
tree's existing shelves-only failures, untouched here.

The new test is the one addition §5 permits, and it closes a real gap: no test drove
a **driver-backed** tool with `--log`, so the preamble's handler wiring was pinned
by nothing — in triplicate before this PR, and in one place after it.
(`test_re_validate.py` does pass `--log`, to a tool with its own `main()` that
reaches none of the three drivers.) The test uses `pds4checksums`, which declares
two handler factories, and asserts that the tool's directory under the log root
holds, **at its top level**, exactly `ERRORS.log` and `WARNINGS.log`, and that
**both have content**
after a run that logs an error — creation and attachment are different properties,
and each handler opens its file when it is created, so existence alone cannot tell
them apart.

**Negative controls, three mutations of `setup_run`,** each reverted before anything
else was run: `handler_factories[:1]` fails the exact-list assertion; creating the
handlers without `logger.add_handler` leaves both files empty and fails the content
assertions; dropping the `if args.log:` branch leaves the directory absent.

## 5. Standing gates

- `ruff check .` clean; configured gate clean;
  `ruff check --preview --select E111,E112,E113` clean.
- Ratchet, `--config 'lint.per-file-ignores = {}'`: **66 entries, 180 slots, 2,249
  findings** at base and at head — unmoved. `[project.scripts]`: **11** at both.
- `tests/api`: 26 passed. The four frozen files are md5-identical to `b8b9703`.
- `scripts/run-all-checks.sh -c -s` with no holdings env vars: pass.
