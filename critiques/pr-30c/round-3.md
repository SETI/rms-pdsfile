# PR-30c round 3 — second independent read of `re_validate.py`

Scope: `src/pdsfile/holdings_maintenance/pds3/re_validate.py` in the frozen tree at
`d7bcff3`. One module docstring, 18 function docstrings, 39 parameters. No executable
statement changed in this PR; every defect below is a defect in the prose except where
marked **code defect**, which means the prose describes machinery the code does not have.

Everything was measured against the frozen tree with
`PYTHONPATH=/seti/all_repos/rms-pdsfile-pr30c/work/src` and
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3), holdings at
`/seti/opus/pdsdata/holdings`. Scratch scripts live under the session scratchpad; nothing
under `src/`, `tests/`, `scripts/` or `pyproject.toml` was touched. `pytest
tests/holdings_maintenance/test_re_validate.py` → 86 passed.

Attribution is `git blame -w`. `afd800ea` is the correction commit; `309d51b8` is the
original docstring commit; `c9e3d21d`/`a6f39495` are pre-existing lines.

---

## Findings

### F1. `get_log_info` — the fatal-record scan cannot fire. **Code defect.**

> "The rest is a scan for three markers -- an error record, a fatal record, and the
> elapsed time the closing record carries." (lines 413–414)
>
> "A log with no elapsed time at all is reported as fatal whether or not it holds a fatal
> record, because a run that never wrote a closing record did not finish." (lines 418–419)

**Blame: `309d51b8` — original prose.** Round 1 and its correction both left this
paragraph alone; so did the correction that rewrote the `Raises:` block six lines below
it.

**What I did.** Built a real `pdslogger.PdsLogger` under `LOGNAME`, attached a real
`file_handler`, and logged one `error()`, one `fatal()`, one `exception()`, then read the
file back. Then reproduced exactly the shape `validate_one_volume` writes when a test
raises — nested `open`, the test's `finally` closing its tier, the volume handler's
`except Exception: logger.exception(e)`, the volume `finally` closing the log — and fed
that log to `get_log_info()`.

**What the code actually does.** The scan is

```python
error |= ('| ERROR |' in rec)
fatal |= ('| FATAL |' in rec)
```

`pdslogger` renders `logger.fatal(...)` as `| CRITICAL |` and `logger.exception(...)` as
`| EXCEPTION |`. `FATAL` is only an *alias name* in `_DEFAULT_LEVEL_NAME_ALIASES`
(`'fatal' → 'critical'`); the rendered text comes from `_DEFAULT_LEVEL_NAMES`, where
`logging.CRITICAL` is `'critical'`. `logger.log('fatal', ...)` also renders `CRITICAL`.
The string `| FATAL |` does not occur in any log this tool can write:

```
volume-level close (fatal, errors, warnings, tests) = (1, 0, 0, 2)
get_log_info -> elapsed = 0:00:00.000881
                had_error = False
                had_fatal = False
"| FATAL |" in the log file: False
```

So the returned `fatal` flag is `True` **if and only if** `elapsed is None`. The
"whether or not it holds a fatal record" clause describes a discrimination the scan never
makes, and "three markers" is two markers and a dead string.

This is not cosmetic. `validate_one_volume` correctly returns `fatal=1` to the batch
driver, which prints and mails an error line — but the *log* it wrote records the failure
as `| EXCEPTION |`, so the next batch run reads that same log back as a clean, completed
validation with neither an error nor a fatal. Three further sentences inherit the
mistake:

- `get_all_log_info` (lines 493–494, `309d51b8`): "takes the first log that summarizes
  cleanly, **is not fatal**, and names a volume whose own key matches". In practice the
  second test is "has an elapsed time".
- `get_all_log_info` (lines 420–421, on `get_log_info`): "it is how batch mode's
  scheduler is kept from treating one as a completed validation" — true only for the
  interrupted-run case, not for a validation that blew up and still closed its log.
- `print_batch_status` (lines 1157–1159, `309d51b8`): "a note where that run logged an
  error". A volume whose every test raised gets no note, because `EXCEPTION` is not
  `ERROR` either.

Rating: **code defect**. The prose is an accurate description of the author's intent and
an inaccurate description of the program.

---

### F2. `build_parser` — "twelve of the fourteen" is eleven. **Disproved.**

> "That covers twelve of the fourteen tool modules in this subpackage; ``pdsdependency``
> carries its own copy of both texts, byte-identical today and tied to nothing, and
> ``crlf`` and ``shelf_consistency_check`` have neither option." (lines 765–768)

**Blame: `afd800ea` — written by the correction.**

**What I did.** Imported every module under `pdsfile.holdings_maintenance` and counted
the ones carrying a `SPEC`; built each `SPEC`'s parser through `_common.build_arg_parser`
and compared its `--log`/`--quiet` help text byte-for-byte against
`_common.LOG_HELP.format(...)` and `_common.QUIET_HELP`; did the same for
`re_validate.build_parser()`; and compared `pdsdependency`'s inline strings to the same
constants.

**What the code actually does.**

```
pds3.pdsarchives … pds4.pds4linkshelf  log/quiet shared: True  (10 modules, all SPEC-driven)
re_validate                            log/quiet shared: True
TOTAL modules using shared constants: 11
```

The subpackage has exactly fourteen tool modules (nine under `pds3` — `crlf`,
`pdsarchives`, `pdschecksums`, `pdsdependency`, `pdsindexshelf`, `pdsinfoshelf`,
`pdslinkshelf`, `re_validate`, `shelf_consistency_check` — plus the five under `pds4`;
`linkshelf_repairs.py` has no `main()` and no parser). The sentence's own semicolon names
three of them as not covered. 14 − 3 = 11, and 11 is what I measured. "Twelve" is
inconsistent both with the measurement and with the rest of its own sentence.

(The other reading — "this subpackage" = `pds3` — is worse: nine tool modules, six of
them covered.)

The rest of the sentence is right: `pdsdependency`'s `--log` and `--quiet` help strings
are byte-identical to `LOG_HELP.format(env=LOGROOT_ENV, progname='pdsdependency')` and
`QUIET_HELP`, and `crlf` and `shelf_consistency_check` declare neither option.

Rating: **disproved** (off by one).

---

### F3. `run_batch` — "the one way a batch run ends nonzero" is one of at least five, and the docstring lists three of the others itself. **Disproved.**

> "OSError: from ``send_email()``, if the mail relay cannot be reached. It is raised from
> the same ``finally`` that would have exited 0 and nothing catches it, so **an
> unreachable relay is the one way a batch run ends nonzero**." (lines 1230–1233)

**Blame: `afd800ea` — written by the correction.**

**What I did.** Ran `main()` in a subprocess under `--batch` for four command lines, with
`PDS_LOG_ROOT` unset, and read the process exit status.

**What the code actually does.**

```
no path                      exit=1  "No holdings path identified"
missing path                 exit=1  "Holdings path not found: /no/such/path"
not a holdings dir           exit=1  "Not a holdings directory: …/nothold"
valid holdings, no log root  exit=1  TypeError: expected str, bytes or os.PathLike …
```

The first three are `resolve_holdings_paths`'s `sys.exit(1)` — which the *immediately
preceding* entry in the very same `Raises:` block documents ("SystemExit: … with status 1
for an unusable path"). The fourth is `get_all_log_info`'s `TypeError`, which the
*immediately following* entry documents. `report_missing_volumes`'s `OSError` /
`UnicodeDecodeError` and `print_batch_status`'s `ValueError` are two more, all of them
raised before the mail block is ever reached.

Rating: **disproved.** The claim is refuted by its own two neighbours in the same block.

---

### F4. `run_batch` — a run with work to do does not necessarily overrun. **Misleading.**

> "The time limit is checked after each volume rather than before, so **a run that has
> anything to do overruns by however long its last volume took**, and a run whose
> schedule is empty validates nothing and reports a timeout anyway." (lines 1203–1205)

**Blame: `afd800ea` — written by the correction.** (The original said "a run always
validates at least one volume and always overruns"; the correction fixed the first half
and kept the second.)

**What I did.** Built a two-volume holdings tree with no logs, stubbed
`validate_one_volume` to return instantly, and ran `run_batch` with `--minutes 60`.

**What the code actually does.**

```
exit=0  volumes validated=2  wall seconds=0.013  limit=60 min
overran the limit? False
```

The check is `if (now - start).seconds > args.minutes*60: break`. A run that exhausts its
schedule before the limit exits without ever crossing it. "Overruns" is a property of a
run that *reaches* the limit, not of "a run that has anything to do". Even for a run that
does reach it, the overrun is the part of the last volume that fell past the limit, which
is at most — not equal to — how long that volume took.

Rating: **misleading.** The correction narrowed the false universal ("always") to a
smaller false universal.

---

### F5. `validate_one_volume` — "eighteen of nineteen" is the unit-test fixture's number, not a volume's. **Misleading.**

> "…so one failure early on can leave **eighteen of nineteen** tests unrun and still
> report the volume as done." (lines 147–148)

**Blame: `afd800ea` — written by the correction.** The commit message says the number
came from "a stub run".

**What I did.** Drove `validate_one_volume` with the four sibling `validate`s and
`pdsdependency.test` replaced by counters, real `os.path.exists` and real `glob.glob`,
over (a) a synthetic tree with all five volume-type directories, with and without archive
tarballs, and (b) five real volumes in `/seti/opus/pdsdata/holdings`.

**What the code actually does.**

```
all 5 voltypes, no tarballs   calls=19   "19 re-validation tests performed"
all 5 voltypes, tarballs      calls=29   "29 re-validation tests performed"
… fail on the first call      calls= 1   "1 re-validation test performed"

COISS_2xxx/COISS_2002  tests=16  voltypes=[volumes, calibrated, metadata, previews] archives=[]
COISS_1xxx/COISS_1001  tests=16  …
GO_0xxx/GO_0017        tests=12  voltypes=[volumes, metadata, previews]             archives=[]
VGISS_5xxx/VGISS_5101  tests=12  …
COCIRS_5xxx/COCIRS_5401 tests= 8  voltypes=[volumes, diagrams]                      archives=[]
```

The count is `3v + 2a + l + 1` (v = volume-type directories present, a = archive groups
with a matching `.tar.gz`, l = link-shelf types present). Nineteen is the value for
v=5, a=0, l=3 — exactly the shape of the `volume_tree` fixture in
`tests/holdings_maintenance/test_re_validate.py`, which builds all five volume-type
directories and no tarballs unless a test calls `add_tarballs()`. A fully populated volume
runs 29; the volumes in this project's own holdings run 8 to 16.

The docstring gives no configuration for the number, and the paragraph three sentences
earlier has already told the reader that archive groups are skipped when no `.tar.gz` is
found — so the reader has no way to know that nineteen presupposes exactly that skip
happening five times. The hedge "can" saves the sentence from being false; it does not
stop it reading as a fact about volumes.

Rating: **misleading.** A measurement of the stub reported as a property of the tool.

---

### F6. `run_batch` — "Whatever happens, the report is mailed" is false under `--batch-status`, which the paragraph above it describes. **Misleading.**

> "**Whatever happens**, the report is mailed from a ``finally``: a full report to each
> ``--email`` address…" (lines 1209–1211)

**Blame: `309d51b8` — original prose,** left untouched by the correction that rewrote the
paragraph directly above it.

**What I did.** Called `run_batch` twice with `args.email = ['a@b.c']` and `send_email`
replaced by a recorder — once with `batch_status=True`, once with `False`.

**What the code actually does.**

```
batch_status=True  -> SystemExit code=None  emails sent=0
batch_status=False -> SystemExit code=0     emails sent=1
```

`print_batch_status()` calls `sys.exit()` at line 1266, *before* the `try:` at 1283, so
the `finally` is never entered. The same is true of every failure while the schedule is
being built: `resolve_holdings_paths`'s `sys.exit(1)`, `get_all_log_info`'s `TypeError`,
`report_missing_volumes`'s `OSError`/`UnicodeDecodeError`. The paragraph immediately above
states the `--batch-status` case ("the run ends without validating anything") and the
paragraph immediately below states one of the exception cases, so the file contains the
counterexample twice over.

Rating: **misleading.**

---

### F7. `get_log_info` — "Three messages cover those four cases" presents an enumeration that its own new cross-reference contradicts. **Misleading.**

> "ValueError: for a file this cannot summarize -- one that is empty or whose first
> record has no field separator, one whose first record names a different logger, one
> with only a single record, and one whose second record is not the modification time.
> **Three messages cover those four cases**…" (lines 432–437)

**Blame: enumeration `309d51b8`; the "Three messages" sentence `afd800ea`.** The same
commit added, in `volume_abspath_from_log`, "The same file is survivable through
``get_log_info()``, whose caller catches ValueError and this is a subclass of it."

**What I did.** Wrote a log whose first record contains the bytes `\xff\xfe`, then called
`volume_abspath_from_log`, `get_log_info` and `get_all_log_info` on it.

**What the code actually does.**

```
volume_abspath_from_log -> UnicodeDecodeError | ValueError subclass: True
get_log_info            -> UnicodeDecodeError | caught by "except ValueError": True
get_all_log_info survived; info_list = []
```

The correction is right about the mechanism — `readlines()` raises `UnicodeDecodeError`,
`get_all_log_info`'s `except ValueError` swallows it — but it recorded that fifth
ValueError case only in the *other* function's docstring. `get_log_info`'s own block still
enumerates four cases and now asserts that three messages cover them, which reads as
exhaustive. The one case with no message at all, and the only one another docstring in the
file leans on, is missing.

Rating: **misleading.** Textbook "applied to three of the four places it belongs".

---

### F8. `run_batch` — the `finally` does not exit 0, and the OSError gloss under-describes its own exception type. **Misleading.**

> "It is raised from **the same ``finally`` that would have exited 0**…"
> "OSError: from ``send_email()``, **if the mail relay cannot be reached**." (lines
> 1230–1231)

**Blame: `afd800ea` — written by the correction.**

**What I did.** Read the control flow, then replaced `rv.SMTP` with a fake whose
`sendmail()` raises `smtplib.SMTPRecipientsRefused`, and ran `run_batch` to see what came
out.

**What the code actually does.** Two separate problems.

1. `sys.exit(0)` is at line 1352, *after* the whole `try/except/finally` (1283–1348). The
   `finally` never exits 0; it merely runs before control would reach the statement that
   does. The module docstring's version of the same idea — "the mail is sent from the same
   block that would exit 0" (line 37, also `afd800ea`) — has the same flaw.
2. `smtplib.SMTPException` **is a subclass of `OSError`** (`SMTPException → OSError →
   Exception`), which `send_email`'s own `Raises:` block lists separately as coming "from
   ``sendmail()`` or ``quit()``, if the host refuses the message or the session". So:

   ```
   propagated out of run_batch -> smtplib.SMTPRecipientsRefused | is OSError: True
   ```

   The very type `run_batch` documents also covers refusal, not just unreachability. The
   gloss "if the mail relay cannot be reached" is narrower than the entry it glosses, and
   narrower than what `send_email` two hundred lines above says the same call raises.

Rating: **misleading.**

---

### F9. Module docstring — the sweep of what is left out omits `crlf`. **Misleading.**

> "**Five is not all of them.** ``pdsindexshelf`` offers a validate task under the same
> name as the four it does call, and this tool neither imports nor runs it… **Nor is**
> ``shelf_consistency_check``, which is not task-shaped." (lines 14–17)

**Blame: `afd800ea` — written by the correction.**

**What I did.** Enumerated the package's tool modules and their validation entry points.
Confirmed the true parts first: `pdsindexshelf` does expose `validate = TASKS['validate']`
at module level, `re_validate`'s import block names only `pdsarchives`, `pdschecksums`,
`pdsdependency`, `pdsinfoshelf`, `pdslinkshelf`, and `shelf_consistency_check` has no task
table at all — only `build_arg_parser()` and `main()`.

**What is missing.** `crlf` is the third PDS3 validation in the package this tool does not
run, and it is not task-shaped either — its parser's own description begins "crlf:
Validate, and optionally repair, the CRLF line terminators of one or more files". The
"Nor is" construction reads as closing the list. If `shelf_consistency_check` qualifies
for the list on the grounds that it validates something other than a volume, `crlf`
qualifies on identical grounds.

Rating: **misleading.**

---

### F10. `main` — the `Raises:` block now propagates one of the three exceptions its callees document, not three. **Misleading (weakest of these).**

> "TypeError: from ``run_batch()`` when no log root is configured.
>  OSError: from ``run_batch()``, if its report cannot be mailed." (lines 1379–1380)

**Blame: the `OSError` line is `afd800ea`; the omissions are `309d51b8`.**

**What I did.** Cross-read every `Raises:` block in the file against `main()`'s.

**What the code actually does.** `run_interactive` documents `ValueError` (from
`from_abspath()`) and `KeyboardInterrupt`; `print_batch_status` documents `ValueError`;
`run_batch` documents `KeyboardInterrupt`. All four reach `main()`'s caller by exactly the
mechanism `main()` credits for `TypeError` and `OSError` — an uncaught propagation out of
the mode function. The correction walked up the call chain for `OSError` and stopped
there. The result is a block that is neither exhaustive nor obviously selective, in a file
whose other `Raises:` blocks are scrupulously exhaustive.

Rating: **misleading**, low severity. I record it because it is the same
propagate-to-one-of-several failure as F7 and F11 and the three together are the shape of
this correction pass.

---

### F11. `validate_one_volume` — "the volume's own file handler and error handler" is four handlers when a log root is configured. **Misleading.**

> "logger: The run's logger. **The volume's own file handler and error handler** are
> attached for the duration of this call and removed when it returns." (lines 160–161)

**Blame: `309d51b8` — original prose,** in the same docstring whose `Returns:` block the
correction rewrote *specifically* to distinguish the one-log-path case from the
two-log-path case.

**What I did.** Called `validate_one_volume` with `_common.log_paths_for` returning two
paths and a logger that records the `handler=` argument of `open()`.

**What the code actually does.**

```
two log paths -> handlers attached: 4
    ('file', …/root_logs/re-validate/VS_1xxx/V_re-validate_x.log)
    ('err',  …/root_logs/re-validate)
    ('file', …/holdings_logs/re-validate/VS_1xxx/V_re-validate_x.log)
    ('err',  …/holdings_logs/re-validate)
```

The loop builds one `file_handler` **and** one `error_handler` per log path, and the two
error handlers point at two different directories. Round 1's finding — that the returned
path is the second of two, and which one that is — was applied to the `Returns:` block and
not to the `Parameters:` entry twelve lines above it that describes the same pair.

Rating: **misleading.**

---

## Claims I could not verify

- **`get_volume_info`: "The date is the PdsFile object's own ``date``, a display string of
  the form ``YYYY-MM-DD HH:MM:SS``… and the empty string where there is no recorded
  modification time."** I ran `get_volume_info('/seti/opus/pdsdata/holdings')`: it found
  493 volumes and **every one of them returned `''`** (`date string lengths: {0}`). So I
  could confirm the empty-string branch by running it, but the `YYYY-MM-DD HH:MM:SS`
  branch only by reading `_properties.py:1124` (`self.modtime.strftime('%Y-%m-%d
  %H:%M:%S')`). The same gap stopped me exercising the batch scheduler's date comparison
  against real dates: on this holdings copy every `(date, key)` pair carries an empty
  date, so "which volumes have changed since they were last validated" can only be tested
  with synthetic input, which is what F.7-style checks used.
- **`send_email`: "which is what an internal mail relay accepts."** I did not contact
  `list.seti.org:25`. The code half (fixed host, port 25, no `starttls`, no `login`) is
  verified by reading; the claim about what the relay accepts is not a claim about this
  code and I have no way to test it here.
- **`get_all_log_info`: "one volume's logs under one log root are all in one directory."**
  True for the layout this tool writes (`<logroot>/re-validate/<volset>/…`, confirmed by
  building real paths through `_common.log_paths_for`). I could not rule out a log root
  that also contains some *other* directory whose basename is a volume set name, which
  would give one key logs from two directories and break the "chronological without
  sorting by time" argument. No such tree exists here to test against.
- **`volume_abspath_from_log`: "The path is recovered from the log's first record."** I
  verified this against a log written by a real `PdsLogger` with a real `file_handler`,
  not against a log written by a real end-to-end run of the tool — there are no
  `*_re-validate_*.log` files anywhere under `/seti/opus/pdsdata/logs`, and running the
  real validations over a real volume was out of scope for a docstring review. The record
  format is `pdslogger`'s, so I judge the risk low, but it is an inference.
- **The module docstring's "so the index shelves of a volume's metadata tables are never
  re-validated here."** I confirmed `pdsindexshelf.validate` exists and is not imported,
  and that its `SPEC` has `unit='table'`, `index_ext='.tab'`, and that the holdings tree
  carries `_indexshelf-metadata/`. I did not confirm that running it is work a volume-level
  re-validation *should* be doing, which is what the sentence implies.

---

## Claims I checked and confirmed

Each of these I tried to break and could not.

**From the correction commit `afd800ea`:**

1. *Module docstring, "Five is not all of them"* — `pdsindexshelf` does expose a
   module-level `validate` (line 86, `TASKS['validate']`), under the same name as the four
   `.validate` calls this tool makes; the import block does not name it;
   `shelf_consistency_check` has no task table. (Incomplete per F9, but every positive
   assertion in it holds.)
2. *`validate_one_volume`, "A test that raises skips every remaining test of the volume"* —
   the `try:` at line 191 wraps the whole sequence; a stub failing on the first call left
   `calls=1` and logged "1 re-validation test performed". Confirmed.
3. *`report_missing_volumes`, "The filter is applied once per key and the report is not
   filtered at all"* — with logs from `/h1` and `/h2` and a run asked only about `/h1`:
   two `Missing volume` errors, `/h1/…` and `/h2/…`. With a run asked only about `/h3`:
   none. Exactly as claimed.
4. *`run_interactive`, "SystemExit: from ``sys.exit()``, which is how this function returns
   when nothing raises"* — every non-raising path reaches a `sys.exit`; the `finally` at
   1039 computes `status` but the `sys.exit(status)` at 1043 is skipped when the `try`
   body raised. Confirmed by reading; the three `sys.exit(1)` paths confirmed by running.
5. *`get_log_info`, "Three messages cover those four cases, so a log naming another logger
   and a log with one record cannot be told apart"* — the four listed cases raise
   `'Empty log file: …'`, `'Not a re-validate log file'`, `'Not a re-validate log file'`,
   `'Missing modification time'`. Confirmed. (The enumeration's incompleteness is F7; the
   arithmetic in this sentence is right.)
6. *`validate_one_volume` `Returns:`, "always the copy beside the holdings tree… the
   log-root copy is built first and this is the other one"* — this is the sharpest
   correction in the commit and it is exactly right. `_common.log_paths_for` returns
   `[build(place='default'), build(place='parallel')]`; `_derived_paths._log_path_for`
   makes `'default'` the class log root and `'parallel'` the `logs/` directory beside
   holdings, with `'default'` falling back to `'parallel'` when no root is set (so the two
   are equal and only one is returned). Measured with a real `Pds3File`:

   ```
   log_root=None        → returned  /seti/opus/pdsdata/logs/re-validate/COISS_2xxx/…
   log_root=/tmp/LOGROOT→ [0] /tmp/LOGROOT/re-validate/…   [1] /seti/opus/pdsdata/logs/…
                          returned  /seti/opus/pdsdata/logs/re-validate/COISS_2xxx/…
   ```
7. *`find_modified_volumes`, "two trees whose copies carry different dates put that one
   path in the schedule twice"* — measured:

   ```
   different dates, no logs → modified = [('/h2/…/VOL_0001', '2026-02-02 …'),
                                          ('/h2/…/VOL_0001', '2026-02-02 …')]
   same dates,      no logs → modified = [('/h2/…/VOL_0001', '2026-01-01 …')]
   ```
   The `/h2` path (second seen, so the one the dictionary kept) appears twice, and
   `run_batch` iterates that list directly. Both halves of the claim hold, including the
   "different dates" precondition.
8. *`build_parser` `Returns:`, "holding 21 arguments: [enumeration]"* — the parser holds 22
   actions, of which one is argparse's automatic `-h/--help`; the enumeration names all 21
   the module declares, in the parser's own order, with none missing and none invented.
   Confirmed, with the note that "21 arguments" is 21 *declared* arguments.
9. *`run_interactive`, "A configured log root does get its ``re-validate`` directory and an
   empty ``ERRORS.log``, which ``main()`` creates before this is called"* — ran `main()`
   with `--log <tmp>` and a nonexistent volume path; exit 1, and
   `<tmp>/re-validate/ERRORS.log` exists at size 0. Confirmed.
10. *`main`, "SystemExit: from ``parse_args()``, with status 2 … and 0 for ``--help``"* —
    measured: `--help` → 0, `--no-such-option` → 2, `--minutes abc` → 2.
11. *`run_batch`, "a run whose schedule is empty validates nothing and reports a timeout
    anyway"* — an empty holdings tree printed `Timeout at … after 0 minutes`, mailed the
    report, and exited 0. Confirmed. (The other half of that sentence is F4.)
12. *Module docstring, "Batch mode's schedule comes from two places and no third … a batch
    run against a log root holding no logs treats every volume the glob found as never
    validated"* — with two volumes and an empty log root, both printed "not previously
    validated" and both were validated; with no log root at all, `os.walk(None)` raises
    `TypeError: expected str, bytes or os.PathLike object, not NoneType`, and the tool
    exits 1 on it. Confirmed.
13. *`volume_abspath_from_log` / `report_missing_volumes`, the `UnicodeDecodeError`
    entries* — confirmed as quoted in F7: the exception is raised, it is a `ValueError`
    subclass, `get_all_log_info` swallows it, `report_missing_volumes` does not, and
    `report_missing_volumes` is called before `run_batch`'s `try:`, so it does end the
    report.

**From the original docstrings (`309d51b8`), the half round 1 did not touch:**

14. *`validate_one_volume`* — the fixed test order (per-voltype checksum+archive; archive
    checksums; per-voltype infoshelf+linkshelf; archive infoshelves; dependency), "a volume
    type's directory is visited twice", the two two-flag groups, "skipped without a test
    being counted", "the first the glob returns", "every test is closed in a ``finally``",
    "what is caught is ``Exception``". All confirmed by reading and by the counter runs.
15. *`validate_one_volume`, "the caller sees the failure only as a fatal in the returned
    counts"* — `pdslogger`'s `exception` level is `logging.CRITICAL`, and `summarize()`
    counts `level >= CRITICAL` into the first return slot. Measured: `close()` returned
    `(1, 0, 0, 2)` after one swallowed `RuntimeError`. Confirmed. (What the *log file*
    records is F1.)
16. *`volume_abspath_from_log`, the space truncation* — measured:
    `'…| Re-validate /a b/holdings/volumes/VS_1xxx/VOL_0001'` →
    `'b/holdings/volumes/VS_1xxx/VOL_0001'`. Empty file → `''`. Confirmed.
17. *`key_from_volume_abspath` / `key_from_log_path` edges* — `'VOL'` → `'VOL'`;
    `'/x/VS_1xxx/whatever.log'` → `'VS_1xxx/whatever.log'`. Both as documented.
    `key_from_log_path` is called nowhere in `src/`; its only callers are two tests.
    Confirmed by grep.
18. *`get_all_log_info`, the walk, the key, the backwards search, the reorganized-tree
    test, "contributes nothing to the first result and still appears in the second"* —
    confirmed by reading against the real log-path shape
    (`<logroot>/re-validate/<volset>/<volname>_re-validate_<YYYY-MM-DDThh-mm-ss>.log`,
    most-significant-first, so `files.sort()` is chronological).
19. *`get_log_info`, the four fixed positions* — verified against a log written by a real
    `PdsLogger`: `parts[0]` is the timestamp, `parts[1].strip()` is `'pds.validation'`,
    `parts[-1]`'s last space-separated token is the volume path, `recs[1]` carries
    `Last modification:`. Round-trip through `get_log_info` returned every field correctly.
20. *`run_batch`, "so a limit of 1,440 minutes or more is never reached"* — `.seconds` is
    bounded by 86399 and `1440*60` is 86400, so `>` can never hold. Confirmed
    arithmetically and by `datetime.timedelta(days=1, seconds=-1).seconds == 86399`.
21. *`build_parser`, "the ten specification driven tools" and "the two tools here that
    switch them off"* — exactly ten modules carry a `SPEC`; exactly two,
    `crlf` and `shelf_consistency_check`, pass `allow_abbrev=False`. Both numbers correct.
22. *`derive_options`* — the `--info`/`--links` versus `infoshelves`/`linkshelves` naming
    split, the narrowing of `dependencies` to `'volumes' in voltypes` and `linkshelves` to
    `LINKSHELF_VOLTYPES`, and `timeless &= dependencies`. All confirmed by reading and by
    the module's own 86 passing tests.
23. *`resolve_holdings_paths`, "the rest of a batch run reads the raw arguments rather than
    these"* — `run_batch` passes `holdings_abspaths` (resolved) to `logger.add_root` and
    `report_missing_volumes`, and `args.volume` (raw) to `get_volume_info` and the batch
    prefix. Confirmed.
24. *`format_email`* — string wrapped, list passed through, `From/To/Subject/Date`, one
    blank line, no trailing newline, day-first default date. Confirmed by running.
25. *`print_batch_status`, "Its code is None and its process status is 0, which is not the
    same call as the ``sys.exit(0)``"* — confirmed: `SystemExit code=None` from the
    `--batch-status` path, `code=0` from the end of a batch run.

---

## Count

**11 findings. 8 of them are in sentences commit `afd800ea` wrote** (F2, F3, F4, F5, F7,
F8, F9, F10 — F10's attribution is the `OSError` line the correction added, on a block
whose omissions predate it). **3 are in original prose** (F1, F6, F11).

The one **code defect** (F1) is in original prose. The two highest-value prose findings
(F2, F3) are both in the correction, and F3 is refuted by the two entries that bracket it
in the same `Raises:` block. F7, F10 and F11 are all the same failure mode: a true finding
recorded in one of the two-to-four places in this file that state the same fact.
