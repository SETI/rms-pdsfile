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
| `src/pdsfile/holdings_maintenance/_common.py` | 372 | 397 |
| `src/pdsfile/holdings_maintenance/_shelf_common.py` | 523 | 501 |
| `src/pdsfile/holdings_maintenance/_indexshelf_common.py` | 620 | 598 |
| `tests/holdings_maintenance/test_driver_setup.py` | — | 47 |

14 code lines move; the function costs a `def` line and a docstring, so the three
source files net 19 lines shorter. Nothing else changed: no rename, no signature
change, no driver merge. Deferred entry 130's seven forced variation points stand.

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
function names are compared verbatim, which is the point. `.tar.gz` files are
compared as their member lists rather than their compressed size, because the
archive carries a directory entry whose modification time is the run's own.

**Base versus base first**, two independent runs of the same tree:

```
base run 1 vs base run 2 :   0 differing lines of 6,893
base      vs head        :   0 differing lines of 6,893
```

Byte-identical. Not "attributed" — identical.

### 3.1 One input class where the extraction is visible, found deliberately

Any extracted function adds a stack frame, so a traceback raised *inside* the
preamble would name it. Nothing in the 158 scenarios raises there, so a separate
**20-scenario probe** went looking: each tool run twice with `--log`, once at a
writable root and once at a root the process cannot write into. The unwritable case
raises `PermissionError` from `logger.add_handler(make_handler(path))` — the
preamble's last line — on all ten tools.

Base-versus-base control on the probe: 0 differing lines. Base versus head: **30
added lines, none removed, none changed**, three per tool and one cause:

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

The new test is the one addition §5 permits, and it closes a real gap: no test in
the suite drove a maintenance tool with `--log`, so the preamble's handler wiring
was pinned by nothing — in triplicate before this PR, and in one place after it. It
uses `pds4checksums`, which declares two handler factories, and asserts both
`WARNINGS.log` and `ERRORS.log` appear under the log root. **Negative control:**
with `spec.handler_factories[:1]` substituted in `setup_run`, the test fails; the
mutation was reverted before anything else was run.

## 5. Standing gates

- `ruff check .` clean; configured gate clean;
  `ruff check --preview --select E111,E112,E113` clean.
- Ratchet, `--config 'lint.per-file-ignores = {}'`: **66 entries, 180 slots, 2,249
  findings** at base and at head — unmoved. `[project.scripts]`: **11** at both.
- `tests/api`: 26 passed. The four frozen files are md5-identical to `b8b9703`.
- `scripts/run-all-checks.sh -c -s` with no holdings env vars: pass.
