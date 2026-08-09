# PR-30c round 1 — adversarial review of `re_validate.py` docstrings

Slice: `src/pdsfile/holdings_maintenance/pds3/re_validate.py` at commit `3bddc99`
(work tree `/seti/all_repos/rms-pdsfile-pr30c/work`), base `0f5d9ae`
(`/seti/all_repos/rms-pdsfile-pr30c/base`). One module docstring, 18 function
docstrings, 39 parameters. No executable statement changed:
`diff -u base/... work/...` shows additions of docstring text and the header comment
block only.

Interpreter `/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3), `PYTHONPATH=<tree>/src`.
Scratch scripts live in
`/tmp/claude-1000/-seti-all-repos-rms-pdsfile/dfcbd487-f45d-4153-ac36-d47039b697dd/scratchpad/x/`.
Nothing under `src/`, `tests/`, `scripts/` or `pyproject.toml` was modified.

**Counts.** 15 findings: 5 **disproved**, 9 **misleading**, 1 **code defect adjacent**
(a documented guarantee the code does not keep, F15). By category: 8 are relationship
claims, 3 are exceptions from somewhere other than a `raise`, 1 is a boundary/count
claim, 3 are other false or incomplete statements.

---

## 1. Module docstring — "every validation the other PDS3 maintenance tools offer" — DISPROVED

> "Re-run every validation the other PDS3 maintenance tools offer, one volume at a time."

and, two sentences later:

> "This one is the scheduler over **all of them**."

**What I did.** Read the import block (work `re_validate.py:72-78`); it names exactly
five siblings: `pdsarchives`, `pdschecksums`, `pdsdependency`, `pdsinfoshelf`,
`pdslinkshelf`. Then:

```
$ grep -rn "^TASKS\|'validate'" src/pdsfile/holdings_maintenance/pds3/pdsindexshelf.py
80:TASKS = _indexshelf_common.index_tasks(SPEC)
86:validate = TASKS['validate']
$ grep -n "scripts" -A 12 pyproject.toml     # [project.scripts], 11 entries
```

**What the code does.** `pdsindexshelf` is a PDS3 maintenance tool in this package, it
exports a `validate` task under exactly the name the other four use, and `re_validate`
neither imports nor calls it. `shelf_consistency_check.py` is a second PDS3 maintenance
tool offering a check that is never run. `pyproject.toml` installs eleven console
scripts; `re_validate` drives five of them. The index shelves of a volume's metadata
tables are never re-validated by this tool.

**Consequence: disproved.** The summary line is the one sentence a reader takes away,
and it promises coverage the module does not have. "Every validation the other tools
offer" is five of six PDS3 validations; "the scheduler over all of them" is a scheduler
over five of eleven installed tools.

---

## 2. `validate_one_volume` — "skip the rest of its own group" — DISPROVED

> "A test that raises does skip the rest of its own group, because the exception is
> caught around the whole sequence rather than around each test."

**What I did.** `scratchpad/x/t_skip.py`: a temporary tree with all five volume-type
directories present, all five test flags true, the five sibling modules replaced by
recording stubs, and the checksum stub raising `RuntimeError` on its first call.

**What the code does.** Exactly one call was made:

```
calls made (in order):
   ('checksums', '/tmp/.../holdings/volumes/V_xxx/V_001')
returned: ('/tmp/.../V_001_re-validate_2026-01-01T00-00-00.log', 1, 0)
```

Nineteen calls would otherwise have been made (5 checksums + 5 archives + 5 infoshelves
+ 3 linkshelves + 1 dependency; the two archive groups find no `.tar.gz` in this tree).
The `try` at line 179 wraps the entire sequence, so the raise skips **every remaining
test of the volume**, not "the rest of its own group": the archive test for `volumes`,
the four other volume types, both archive groups, the info shelf and link shelf group,
and the dependency check.

**Consequence: disproved.** The sentence's own justification — "caught around the whole
sequence rather than around each test" — implies the stronger fact, so the clause it is
attached to contradicts it. A reader budgeting for partial results after a failure would
plan for one group lost and get the whole volume.

The neighbouring claims in the same paragraph are correct and I confirmed them: the
raising test still counts as performed (`tests_performed` reached 1), and the caller sees
the failure only as a fatal in the returned counts (`fatal == 1`).

---

## 3. `report_missing_volumes` — "Where more than one tree qualifies" — DISPROVED

> "Which trees a key's logs were written against is recovered from the logs themselves
> ... Where more than one tree **qualifies**, one error is logged per tree, in sorted
> order, so a volume that has been dropped from two trees is reported twice."

**What I did.** `scratchpad/x/t_missing.py`: one key with two logs, one recording
`/treeA/holdings/volumes/V_xxx/V_001` and one recording
`/treeB/holdings/volumes/V_xxx/V_001`, with `holdings_abspaths = {'/treeA/holdings'}`.

**What the code does.**

```
  ERROR: ('Missing volume', '/treeA/holdings/volumes/V_xxx/V_001')
  ERROR: ('Missing volume', '/treeB/holdings/volumes/V_xxx/V_001')
```

Lines 1110-1118: `if not (holdings_abspaths & holdings_for_key): continue` tests
qualification **once for the whole key**, and the loop that follows iterates over all of
`holdings_for_key`, qualifying or not. Trees the run was never asked about are reported.

**Consequence: disproved.** The docstring's first paragraph ("a key whose logs all came
from some other tree is not this run's business") sets up a filter the loop does not
apply per tree, and the sentence quoted asserts the filter is per tree. A batch run over
one holdings tree logs "Missing volume" errors naming a different tree — which, per
`run_batch`, become error mail.

---

## 4. `run_interactive` — "which every path out of this function reaches" — DISPROVED

> "Raises:
>     SystemExit: from ``sys.exit()``, **which every path out of this function reaches**."

**What I did.**

```
$ PYTHONPATH=src python -m pdsfile.holdings_maintenance.pds3.re_validate /etc
...
  File ".../_path_utils.py", line 139, in logical_path_from_abspath
    raise ValueError('Not compatible with a logical path: ', abspath)
ValueError: ('Not compatible with a logical path: ', '/etc')
exit=1
```

**What the code does.** `from_abspath` at line 989 raises before the loop reaches any
`sys.exit()`. The `except (Exception, KeyboardInterrupt)` at line 1009 re-raises, so that
path does not reach line 1017 either.

**Consequence: disproved, and self-contradicting.** The same `Raises:` block goes on to
document two paths out that do not reach `sys.exit()` — the `ValueError` entry says so
explicitly ("before any of the above") and the `KeyboardInterrupt` entry says the
exception is "re-raised rather than turned into a status".

---

## 5. `get_log_info` — "The message distinguishes the cases" — DISPROVED

> "ValueError: for a file this cannot summarize -- one that is empty or whose first
> record has no field separator, one whose first record names a different logger, one
> with only a single record, and one whose second record is not the modification time.
> **The message distinguishes the cases**, and every caller here treats them alike."

**What I did.** Read lines 428-447.

**What the code does.** Four listed cases, three distinct messages:

| case | line | message |
|---|---|---|
| empty file | 429 | `'Empty log file: ' + log_path` |
| first record has no `\|` | 433 | `'Empty log file: ' + log_path` |
| first record names another logger | 437 | `'Not a re-validate log file'` |
| only one record | 442 | `'Not a re-validate log file'` |
| second record is not the modtime | 445 | `'Missing modification time'` |

The docstring already merges the first two into one listed case, so it knows they share a
message; it lists the third and fourth separately, and those two are indistinguishable
from the message. A one-record log and a log written by another tool's logger cannot be
told apart.

**Consequence: disproved.**

---

## 6. `validate_one_volume` Returns — "the parallel one when a log root is configured" — MISLEADING

> "Returns:
>     tuple: (log path, fatal count, error count). The log path is the last of the one or
>     two written, **which is the parallel one when a log root is configured**."

**What I did.** Ran `_common.log_paths_for` on a real volume with and without a log root:

```
--- no log root ---
['/seti/opus/pdsdata/logs/re-validate/COCIRS_0xxx/COCIRS_0010_re-validate_...log']
--- with log root '/somewhere/logroot' ---
['/somewhere/logroot/re-validate/COCIRS_0xxx/COCIRS_0010_re-validate_...log',
 '/seti/opus/pdsdata/logs/re-validate/COCIRS_0xxx/COCIRS_0010_re-validate_...log']
logfiles[-1] = /seti/opus/pdsdata/logs/re-validate/COCIRS_0xxx/COCIRS_0010_re-validate_...log
```

**What the code does.** `_common.log_paths_for` builds `[place='default', place='parallel']`
and `_derived_paths._log_path_for` resolves `'default'` to the configured log root and
`'parallel'` to the `logs` directory beside holdings. So `logfiles[-1]` is **always** the
log beside the holdings tree, whether or not a log root is configured — the returned path
does not vary with configuration at all.

**Consequence: misleading.** Two problems. (a) The conditional "when a log root is
configured" implies the answer changes with configuration; it does not. (b) This module's
own module docstring frames the beside-holdings log as the base case and the log-root
copy as the addition ("in the ``re-validate`` subdirectory of a 'logs' directory beside
its holdings tree **and, when a log root is configured, in the same subdirectory under
that root as well**"), so within this file "the parallel one" reads as the log-root copy —
the opposite of what is returned. The word is only correct in `_common`'s vocabulary,
which this module's prose never introduces. It matters: this path is what `run_batch`
appends to the error line at line 1270 and mails, so a reader looking for a failed
volume's log goes to the wrong tree.

---

## 7. `find_modified_volumes` — "only one of them is scheduled" — MISLEADING

> "where two holdings trees of one run carry the same volume, the second one seen
> replaces the first and **only one of them is scheduled**."

**What I did.** `scratchpad/x/t_misc.py`, two trees carrying `V_xxx/V_001` with different
recorded dates and no logs:

```
modified: [('/t2/holdings/volumes/V_xxx/V_001', '2021-01-01 00:00:00'),
           ('/t2/holdings/volumes/V_xxx/V_001', '2021-01-01 00:00:00')]
```

With equal dates the set collapses and only one entry appears.

**What the code does.** `holdings_dict[key]` is overwritten (line 626) so only the second
tree's path survives — that half is true. But `holdings_modtimes` is a set of
`(modtime, key)` pairs (line 627), so two trees with different dates contribute two
surviving pairs, `modified_keys` holds the key twice (line 636), and line 637 looks the
same `holdings_dict` entry up twice. The volume is scheduled — and validated — **twice**
in one batch run.

**Consequence: misleading.** "Only one of them is scheduled" is the reassuring reading
("the volume runs once"); the code runs it twice against the same path. The docstring is
right about *which* path and wrong about *how many times*.

---

## 8. `build_parser` — "read alike across every tool in the package" — MISLEADING

> "What it does share is the text of ``--log`` and ``--quiet``, taken from the same
> constants, **so those two options read alike across every tool in the package**."

**What I did.**

```
$ grep -rn "LOG_HELP\|QUIET_HELP" src/ | grep -v "_common.py:"
src/pdsfile/holdings_maintenance/pds3/re_validate.py:769: help=_common.LOG_HELP...
src/pdsfile/holdings_maintenance/pds3/re_validate.py:803: help=_common.QUIET_HELP)
$ grep -n -- "--log\|--quiet" src/pdsfile/holdings_maintenance/pds3/pdsdependency.py
1322:    parser.add_argument('--log', '-l', ...)
1333:    parser.add_argument('--quiet', '-q', ...)
$ grep -n add_argument src/.../crlf.py src/.../shelf_consistency_check.py
crlf.py: 'file', '--repair', '--verbose'
shelf_consistency_check.py: 'shelf_root', '--verbose'
```

I also reconstructed `pdsdependency`'s literal and compared it with
`_common.LOG_HELP.format(env=..., progname='pdsdependency')`: **IDENTICAL** today.

**What the code does.** `pdsdependency.py` is a tool in this package and builds both help
strings from its own literals (lines 1322-1334), against its own copy of `LOGROOT_ENV`
(line 60) — `_common.py`'s own module docstring says so at lines 23-26. `crlf.py` and
`shelf_consistency_check.py` have no `--log` or `--quiet` at all.

**Consequence: misleading.** The mechanism asserted ("taken from the same constants, so
...") does not hold across the package; the texts coincide because one tool duplicates
the wording by hand, which is exactly the arrangement that drifts. Of the fourteen tool
modules under `holdings_maintenance`, eleven take the constants, one duplicates them, and
two have neither option.

---

## 9. `run_interactive` — "no log written at all" — MISLEADING

> "Every path is checked before any of them is validated, and a bad one ends the run with
> a message and **no log written at all**."

**What I did.**

```
$ python -m pdsfile.holdings_maintenance.pds3.re_validate --log <lr> /nonexistent/path
Volume path not found: /nonexistent/path
exit=1
$ find <lr>
<lr>/re-validate
<lr>/re-validate/ERRORS.log        # 0 bytes
```

**What the code does.** `main()` line 1367 attaches `pdslogger.error_handler(path)` before
either mode function runs; `pdslogger.error_handler` is `file_handler(...)` (pdslogger
`__init__.py:2627`), which opens the file eagerly and creates the parents.

**Consequence: misleading.** No log *records* are written, which is the point being made,
but a log directory and an empty `ERRORS.log` are created under the configured log root
before the path check ever runs. A reader auditing a log tree for evidence of a run finds
one.

---

## 10. `main` Raises — argparse's `SystemExit` omitted — MISLEADING

> "Raises:
>     SystemExit: from ``run_interactive()`` or ``run_batch()``, each of which exits
>     rather than returning. Their docstrings give the statuses."

**What I did.**

```
$ python -m ...re_validate --nosuchflag  ; echo $?   -> 2
$ python -m ...re_validate --help        ; echo $?   -> 0
```

**What the code does.** `parser.parse_args(argv[1:])` at line 1349 exits with status 2 for
an unclassifiable command line and 0 for `--help`, before either mode function is reached.
The `Raises:` block names neither, and attributes `SystemExit` exclusively to the two mode
functions, whose docstrings therefore cannot "give the statuses" for these two.

The sibling `_common.setup_run()` documents exactly this case — "and from ``parse_args()``,
with status 0 for --help and 2 for a command line it cannot classify" — so the omission is
local to this module and inconsistent with the package's own convention.

**Consequence: misleading / incomplete.**

---

## 11. `run_batch` — "a run always validates at least one volume" — MISLEADING

> "The time limit is checked after each volume rather than before, **so a run always
> validates at least one volume** and always overruns by however long the last one took."

**What I did.** Empty holdings tree (`<tmp>/eh/holdings/volumes/`, no volumes) and an empty
log root:

```
Batch re-validate started at 2026-08-08 20:51:33 on <tmp>/eh/holdings
Timeout at 2026-08-08 20:51:33 after 0 minutes
exit=0
```

**What the code does.** `info` (line 1234) is empty when both `modified_holdings` and
`current_logs` are empty, and the `for` body never executes.

**Consequence: misleading.** The point being made — the limit is tested after, not before —
is correct; "always validates at least one volume" is not.

The same paragraph's boundary claim I checked and confirmed: `(now - start).seconds` is
bounded by 86399, so `> args.minutes*60` is unreachable at 1440 minutes (86400) and above,
and reachable at 1439 (86340). "A limit of 1,440 minutes or more is never reached" is
exact.

---

## 12. `run_batch`'s exit-status guarantee is defeated by the mail step — MISLEADING (guarantee not kept)

> module docstring: "**Its exit status is 0 even when the run logged errors**, because a
> nonzero status would cancel the launch daemon that schedules it."
> `run_batch`: "SystemExit: ... **The status is 0 even for a run that logged errors**".

Neither `run_batch`'s `Raises:` nor the module docstring mentions that `send_email()` runs
inside the `finally` (lines 1300-1312) and can raise, replacing the `sys.exit(0)` at line
1316.

**What I did.** `scratchpad/x/t_mailfail.py` — a batch run with `--email` set and
`send_email` stubbed to raise `OSError('mail host unreachable')`:

```
Timeout at 2026-08-08 20:54:32 after 0 minutes
RESULT: escaped with OSError mail host unreachable
```

**What the code does.** The exception propagates out of `run_batch` and out of `main()`;
the process ends in a traceback with status 1 — the exact outcome both sentences say must
not happen, and for a reason unrelated to what the run logged. `send_email`'s own docstring
documents it ("Nothing here catches it, so a batch run that cannot mail its report ends in
it, after the validations are done and the log is closed"), so the fact is in the file; it
is simply absent from the two places that state the guarantee and from `run_batch`'s
`Raises:`.

**Consequence: misleading — a documented invariant the code does not keep.** For a tool
whose stated design constraint is "never exit nonzero or the launch daemon cancels", an
undocumented nonzero exit on an unreachable mail relay is the consequential gap.

---

## 13. Module docstring — "everything ... comes from what it finds there rather than from anything stored elsewhere" — MISLEADING

> "Batch mode's schedule is those logs. It walks the log root -- the one place, not the
> directories beside the holdings trees -- and **every decision it makes about what to
> validate next comes from what it finds there rather than from anything stored
> elsewhere**."

**What I did.** Read `run_batch` lines 1212-1222 and `find_modified_volumes` lines 611-637.

**What the code does.** The schedule is built from two sources. `get_all_log_info(args.log)`
supplies the logs; `get_volume_info(holdings)` globs each holdings tree for
`volumes/*_*/*_*` and reads each volume's `date`; `find_modified_volumes` then computes
`holdings_modtimes - log_modtimes`. The modified set — the first and highest-priority part
of the schedule — cannot be computed from the log root alone, and the holdings dates are
"stored elsewhere" in every sense that matters. The next sentence ("a batch run against a
log root holding no logs treats every volume as never validated") is only true because the
holdings glob supplied "every volume".

**Consequence: misleading.** The intended point (there is no state file or database; the
logs are the record of what was validated) is true and worth saying; "every decision ...
comes from what it finds there" overstates it into something the code contradicts.

---

## 14. `volume_abspath_from_log` Raises — `UnicodeDecodeError` missing — MISLEADING

> "Raises:
>     OSError: from the ``open()`` of a log file that does not exist or cannot be read."

**What I did.** `scratchpad/x/t_unicode.py` — a `.log` file whose header record contains
byte `0xff`:

```
volume_abspath_from_log -> raised (UnicodeDecodeError, UnicodeError, ValueError, Exception)
  'utf-8' codec can't decode byte 0xff in position 55: invalid start byte
```

**What the code does.** `open(log_path)` is text mode with the default encoding, so
`readline()` raises `UnicodeDecodeError` on a log that is not valid UTF-8. That is not an
`OSError`; the only caller, `report_missing_volumes` (line 1102), does not catch it, and
`report_missing_volumes`'s own `Raises:` names only `OSError` "from
``volume_abspath_from_log()``". A batch run therefore dies mid-report on one corrupted log
in the tree.

`get_log_info` is covered by accident on the same input — `UnicodeDecodeError` is a
`ValueError` subclass, so `get_all_log_info`'s `except ValueError: continue` (line 525)
skips such a file, which I confirmed returns `([], {...})` rather than raising. That makes
the asymmetry easy to miss: the same corrupt file is survivable in one path and fatal in
the other, and neither docstring says so.

**Consequence: misleading (missing `Raises:` entry in two docstrings).**

---

## 15. `build_parser` Returns — the enumeration omits three of twenty-one arguments — MISLEADING

> "Returns:
>     argparse.ArgumentParser: The parser, holding the positional paths, the two shared
>     options, the mode options, the two email options, the five test flags and the five
>     volume-type flags."

**What I did.** Counted `add_argument` calls in lines 763-852: 21. Mapped them onto the
enumeration: positional (1) + `--log`/`--quiet` (2) + mode options `--batch`, `--minutes`,
`--batch-status` (3) + `--email`/`--error-email` (2) + five test flags (5) + five
volume-type flags (5) = **18**.

**What the code does.** `--full`, `--all` and `--timeless` are in the parser and in no
category the sentence names. The module docstring elsewhere fixes "the five test flags" as
`--checksums --archives --info --links --dependencies` and "the five volume-type flags" as
the five directory trees, so `--full` and `--all` cannot be folded into either count, and
`--timeless` is neither a mode nor a test nor a volume type.

**Consequence: misleading.** A `Returns:` written as a complete inventory that is missing
three entries — including `--timeless`, which `derive_options` and `validate_one_volume`
both read.

---

## Claims I could not verify

1. **"It fixes nothing -- every task it calls is a validation, and a failure is logged
   rather than repaired."** (module docstring). I confirmed the five call sites reach
   functions named `validate`/`test`, and that `pdslinkshelf.validate` is
   `TASKS['validate']` (`pdslinkshelf.py:582`). I did **not** audit the bodies of
   `pdschecksums.validate`, `pdsarchives.validate`, `pdsinfoshelf.validate`,
   `_linkshelf_common.link_validate` or `pdsdependency.test` for writes to holdings — that
   is five modules outside my slice and several thousand lines. What stopped me was scope,
   not the code being unreadable; someone with a scratch holdings copy could settle it by
   running a full re-validate under `strace -e trace=file` or by snapshotting mtimes.

2. **"so a change in what one of them validates changes what this reports without any
   change here."** (module docstring, last paragraph). I found one counterexample I could
   not rate. `pdsdependency` reports through two channels: the logger, and
   `PdsDependency.COMMANDS_TO_TYPE`, a class-level list of repair commands
   (`pdsdependency.py:177`, appended at 459-460 and 485-486). `grep -rn COMMANDS_TO_TYPE
   src/` shows the only reader is `pdsdependency.main()` at line 1458. `re_validate` never
   reads or clears it, so the half of `pdsdependency`'s report that its own CLI prints is
   silently accumulated and dropped in a re-validate run, and grows for the life of the
   process across a batch run. Whether that falsifies the sentence depends on whether
   "what this reports" means the log alone; I could not settle the intent, so I am not
   scoring it.

3. **`get_volume_info`'s date format claim** — "a display string of the form
   ``YYYY-MM-DD HH:MM:SS`` ... and the empty string where there is no recorded
   modification time". I confirmed the format from the source of the `date` property
   (`_properties.py:1141`, `strftime('%Y-%m-%d %H:%M:%S')`), but **all 493 volumes in
   `/seti/opus/pdsdata/holdings` return the empty string**, so I could not observe a
   non-empty value end to end. That also means I could not exercise
   `find_modified_volumes` or `print_batch_status` against real, differing dates: with
   every date equal to `''`, `holdings_modtimes - log_modtimes` degenerates. The related
   claim "It is compared as a string everywhere it is used, which that format makes safe"
   is true of the format but untested here for the empty-string case, which sorts before
   every real date and so puts date-less volumes first in the modified list.

4. **`get_all_log_info`: "Within a key the paths come out in chronological order ... and
   one volume's logs under one log root are all in one directory."** I confirmed the
   mechanism structurally — `LOGFILE_TIME_FMT = '%Y-%m-%dT%H-%M-%S'` (`pdsfile.py:250`) is
   most-significant-first, `files.sort()` sorts within one directory, and the `place='default'`
   path carries no holdings-tree component (`<logroot>/re-validate/<volset>/<vol>_...log`),
   so two trees do land in one directory. What I could not test is the real case: there are
   no `_re-validate_` logs anywhere under `/seti/opus/pdsdata` (`find /seti/opus/pdsdata/logs`
   finds no such directory), so I have no production log tree to walk. If a site ever
   configures two nested log roots, or another tool writes a `.log` containing
   `_re-validate_` under the same root, the "one directory" premise fails and the
   chronological claim with it; I could not rule that out.

5. **`send_email` `Raises:` split.** The docstring assigns `OSError` to `connect()` and
   `smtplib.SMTPException` to `sendmail()`/`quit()`. `smtplib.connect()` can also raise
   `SMTPConnectError`/`SMTPServerDisconnected`, both `SMTPException` subclasses, so the
   split is not clean. I did not verify this against the real relay — I declined to open a
   connection to `list.seti.org:25` from this machine — so I am listing it here rather than
   as a finding.

6. **`validate_one_volume`: "where more than one archive file matches, the first the glob
   returns is the one validated."** True of `tarpaths[0]`, but I could not construct the
   multi-match case: no `archives-*` directory in the test holdings contains two `.tar.gz`
   files for one volume. The claim is about `glob.glob` ordering, which is unspecified, and
   the docstring correctly declines to name an order.

7. **Whether the two `logger.close()` counts include nested tests' records.** I confirmed
   they do (`scratchpad/x/t_counts.py`: an error logged inside a nested level makes the
   enclosing close return `(0, 1, 0, 1)`), so "the volume's own, from the close of the
   volume's log rather than of any test's" is right about *where* the counts are read. I
   could not decide whether "the volume's own" is meant to exclude the tests' records — it
   does not — so I left it unscored rather than guess at the intent.

---

## Claims I checked and confirmed

These are the load-bearing ones that survived.

- **Test order** (`validate_one_volume`): checksums+archives per voltype, then archive
  checksums, then infoshelf+linkshelf per voltype, then archive infoshelves, then the
  dependency check — a voltype directory is visited twice. Confirmed against lines 187-294
  and against the stub run in `t_skip.py`.
- **Two-flag groups**: archive checksums need `args.checksums and args.archives` (line 213),
  archive infoshelves need `args.infoshelves and args.archives` (line 261). Confirmed.
- **A raising test still counts as performed**, and the exception is logged and swallowed:
  `tests_performed == 1` and `logger.exception` produces `fatal == 1` at close
  (`t_logger.py`: `close() -> (1, 0, 0, 2)`).
- **Handlers attached for the duration of the call and removed on return**: confirmed in
  `t_logger4.py` (`handlers after close = []`) and end to end in `t_first_record.py`, where
  the run-level records that follow the volume's close do **not** appear in the volume's log
  file.
- **The volume log's first record is `Re-validate <abspath>` and its second is
  `Last modification:`**: confirmed by running `validate_one_volume` under an already-open
  run level (`t_first_record.py`); `get_log_info` and `volume_abspath_from_log` both parse
  the produced file correctly.
- **`volume_abspath_from_log` returns `''` for an empty log**, and a path containing a space
  is truncated at its last space — both follow from `parts[-1].strip().split(' ')[-1]`.
- **`key_from_log_path` has no caller in this module**: `grep -rn key_from_log_path src/`
  matches only the definition; `tests/holdings_maintenance/test_re_validate.py:465`
  (`test_key_from_log_path_agrees_with_the_key_get_all_log_info_builds`) is what holds the
  grouping to it. Both halves of that sentence are true.
- **`MAX_INFO` is read nowhere**: `grep -rn MAX_INFO src/ tests/ scripts/` matches only the
  definition at line 84. (Pre-existing comment, not this PR's.)
- **`TypeError` from a batch run with no log root**: reproduced end to end —
  `os.walk(None)` → `TypeError: expected str, bytes or os.PathLike object, not NoneType`,
  raised at `re_validate.py:504` via `run_batch:1212`. `_common.resolve_log_root` does leave
  `None` when neither `--log` nor `PDS_LOG_ROOT` is set (`_common.py:286-290`).
- **The 1,440-minute boundary**: `timedelta.seconds ≤ 86399 < 86400 = 1440*60`, so the limit
  is unreachable at 1440 and above and reachable at 1439. Exact as written.
- **`derive_options`**: naming none of a group selects all of it; `--all` and `--full` do the
  same; `--info`/`--links` parse into `info`/`links` and are left holding what the command
  line said while the derived values go to `infoshelves`/`linkshelves`; `--timeless` survives
  only with the dependency test. All confirmed by `t_derive.py`, including the narrowing:
  `--previews --links` yields `tests=[]` and `--diagrams --dependencies` yields `tests=[]`.
- **Abbreviations are enabled here and disabled in exactly two sibling tools**:
  `grep -rn allow_abbrev src/` matches only `shelf_consistency_check.py:61` and
  `crlf.py:154`. `--dep` resolves; `--a` is rejected as ambiguous with exit 2.
- **"the ten specification driven tools"**: `grep -rn "^SPEC = " src/pdsfile/holdings_maintenance/`
  returns exactly ten, five under `pds3/` and five under `pds4/`, and `_common.TASK_FLAGS`
  holds exactly five task flags.
- **`run_interactive`'s `Raises:` correctly omits `OSError` from `from_abspath`**:
  `must_exist` defaults to `False` (`pdsfile.py:1770`), so only the `ValueError` path is
  reachable — unlike `_common.run_main`, which documents both because it checks existence
  itself.
- **`print_batch_status` exits with `sys.exit()` and no argument** (code `None`, process
  status 0), which is a different call from the `sys.exit(0)` at line 1316. Confirmed by
  reading lines 1161 and 1316.
- **Batch mode is entered by `--batch` or `--batch-status`** (line 1369), as `main`'s
  docstring says. The module docstring's "**Batch mode**, selected by ``--batch``" is
  incomplete on this point but not contradicted, since it goes on to describe
  `--batch-status` separately.
- **Log layout**: the beside-holdings log is `<disk>/logs/re-validate/<volset>/<volname>_re-validate_<tag>.log`
  and the log-root copy is `<logroot>/re-validate/<volset>/...`; the category component is
  dropped by `f.replace('/volumes/','/')` at line 165, which is exactly the shape
  `key_from_log_path` and `get_all_log_info` read back.
