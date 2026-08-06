# PR-25a validation record — `main()`, tests and eleven bug fixes for `re_validate.py`

Owner instruction, verbatim: *"Go ahead and bring revalidate up to the current
standards of other cli programs"*.

Base commit `02f07a8`. Every number below was measured at that commit and at this
branch's head with the command line quoted beside it, in the two worktrees
`/seti/all_repos/rms-pdsfile-pr25a/base` (detached at `02f07a8`) and
`/seti/all_repos/rms-pdsfile-pr25a/work`. Neither worktree has a venv, so every
run sets `PYTHONPATH=$PWD/src` and every run's tree was proved rather than assumed:

```
$ cd <tree> && PYTHONPATH=$PWD/src <venv>/bin/python -c \
    "import pdsfile; print(pdsfile.__file__)"
/seti/all_repos/rms-pdsfile-pr25a/base/src/pdsfile/__init__.py
```

Where a number is inherited from an earlier record rather than re-measured here,
it says so in the line that carries it. Section 12 lists the three places that
applies.

---

## 1. What changed

| File | Change |
|---|---|
| `src/pdsfile/holdings_maintenance/pds3/re_validate.py` | rewritten around `main(argv=None)`; eleven bugs fixed |
| `src/pdsfile/holdings_maintenance/_common.py` | `resolve_log_root()` extracted from `run_main`, and `run_main` now calls it |
| `tests/holdings_maintenance/test_re_validate.py` | new, 73 test ids, `holdings_free` |
| `tests/holdings_maintenance/__init__.py` | the "deliberately not covered" note, which said the file was frozen |
| `pyproject.toml` | ratchet entry ten codes → two, and the header prose it falsified |
| `.cursor/rules/pdsfile_overrides.mdc` | deviations (4) and (6) |
| `plans/2026-07-25-modernization-plan.md` | PR-25a added to Phase 6; ground rule 7, the PR-13 note, PR-28's closing sentence and the issue-#85 row |

`re-validate` is **not** added to `[project.scripts]` (plan §8.4). `python -m
pdsfile.holdings_maintenance.pds3.re_validate` remains the only invocation, and it
is the one the tests drive.

---

## 2. The bug table

The brief supplied ten hypotheses found by reading. Each was reproduced before
being acted on; the reproduction script is quoted with each. Measurement also
found an eleventh the brief did not predict (B11), and corrected the brief's
classification of three others.

Two controls back the claims below, both in §2.12: `scratchpad/negative_control.py`
asserts all eleven bugs are still present in the base module, and
`scratchpad/mutate.sh` reinstates each one in a copy of the head tree and shows
which test catches it. The second is the one that establishes the tests are not
vacuous; the first only establishes that there was something to fix.

### 2.1 B1 — `--previews` is parsed and never read — **reproduced**

`re_validate.py:545-546` at base reads `if args.calibrated: voltypes +=
['previews']`. `grep -n 'args.previews'` over the base file returns nothing.

Running the base file's option-derivation block verbatim (source lines 431-583)
under a controlled `sys.argv`:

| command line | base `voltypes` | head `voltypes` |
|---|---|---|
| `--previews` | `['volumes','calibrated','diagrams','metadata','previews']` | `['previews']` |
| `--volumes --previews` | `['volumes']` | `['volumes','previews']` |
| `--calibrated` | `['calibrated','previews']` | `['calibrated']` |

Two distinct wrong behaviors: `--previews` alone selected nothing, fell through to
the "no volume type named" default and so behaved exactly like `--all`; and
`--previews` beside another type was silently dropped. Fixed by reading
`args.previews`. Pinned by `test_previews_flag_selects_previews`,
`test_previews_is_not_dropped_beside_another_volume_type` and
`test_calibrated_does_not_also_select_previews`.

### 2.2 B2 — the missing-volume report can never fire — **reproduced, twice**

Static, by AST: the `if volume_abspath == '':` statement at base `:705` has body
`[Continue(706), Assign(708), Expr(709)]`. The two statements that fill
`holdings_for_key` sit after the `continue` in the same block.

Behaviorally, against a synthetic holdings root and log tree
(`make_scenario2.py`) holding one volume that exists and one that has a log but no
directory:

```
$ python -m pdsfile.holdings_maintenance.pds3.re_validate \
      --batch-status --log <ROOT>/logs <ROOT>/holdings
base:  1          COCIRS_5xxx/COCIRS_5401  modified , last validated 2026-01-02, duration 0:00:12
head:  2026-08-06 12:14:43 | pds.validation || ERROR | Missing volume: volumes/COCIRS_5xxx/COCIRS_9999
       1          COCIRS_5xxx/COCIRS_5401  modified , last validated 2026-01-02, duration 0:00:12
```

The real test holdings cannot exercise this branch at all: the tool intersects each
log's own holdings prefix against the **realpath** of the command-line root, and
that realpath contains spaces on this machine, which `volume_abspath_from_log`
truncates because it recovers the path as the last whitespace-separated token of
the first log line. That is a real limitation of the log format, it is
pre-existing, and this PR does not change it — it is filed as deferred observation
107.

Fixed by dedenting the two statements. Pinned by `test_missing_volume_is_reported`,
with `test_missing_volume_in_another_tree_is_not_reported` and
`test_missing_volume_with_only_empty_logs_is_not_reported` as the controls that
keep it from passing by reporting everything.

### 2.3 B3 — `key_from_log_path` reads an undefined name — **reproduced**

```
>>> mod.key_from_log_path('/logs/VS_1xxx/VOL_0001_re-validate_x.log')
NameError: name 'abspath' is not defined
```

It resolved at base only because the module-level program bound `abspath` as a
global; called before that point, or from anywhere at all under a `main()`, it
raises. `grep -rn key_from_log_path` over `src/ tests/ scripts/` returns **only its
own definition** — nothing in the repository calls it.

**Fixed, not deleted.** It was deleted in this PR's first draft, on the reasoning
that nothing can depend on a function whose every call raises. Round 1 of review
was right that ground rule 9 says what it says — *"Nothing is deleted for being
'probably dead'"* — so the function is restored, reading its own `log_path`
parameter, and pinned by `test_key_from_log_path` and
`test_key_from_log_path_agrees_with_the_key_get_all_log_info_builds`. The second
of those is the one that shows the fix is the intended one: it returns the same key
`get_all_log_info` derives inline for the same log file.

### 2.4 B4 — the dependency log line names a leaked loop variable — **reproduced**

`abspath` is loaded at base `:180` and `:182`; its `Store` sites in the same
function are `:82,:109,:111,:112,:116,:130,:158,:160,:161,:165` — every one of them
a per-voltype or per-tarball path from an earlier loop.

Driven with stubs for the five sibling tools and `glob.glob` returning `[]` (the
common case: no archive tarballs present), the base function calls

```
logger.open('Dependency re-validation for', [])
```

— `abspath` holds the **empty list** left by `abspath = glob.glob(abspath)` at
`:161`. Rendering that through a real `PdsLogger` shows what the log actually said:

| value of `abspath` | when | rendered line |
|---|---|---|
| `[]` | a full run with no archive tarballs present | `Dependency re-validation for` |
| a `.tar.gz` path | a full run with tarballs present | `Dependency re-validation for: …/archives-previews/VS_1xxx/VOL_0001.tar.gz` |
| the last existing voltype directory | `-D` alone, so the archive-infoshelf loop never runs | `Dependency re-validation for: …/previews/VS_1xxx/VOL_0001` |
| `pdsdir.abspath` (the intent) | — | `Dependency re-validation for: …/volumes/VS_1xxx/VOL_0001` |

So in all three reachable shapes the line named no path at all, or named a
different file from the one the test was about. Fixed
by logging `pdsdir.abspath`. **This changes two log lines**; it is enumerated in
§7 as a defect fix under ground rule 9, not as a rewording.

**The brief classified B4 as forced by G1. It is not.** `abspath` is a local of
`validate_one_volume`, which was already a function at base; the move into a
`main()` does not touch it. It is an ordinary ground-rule-9 fix.

### 2.5 B5 — `validate_one_volume` returns a leaked loop variable — **reproduced**

`logfile`'s only `Store` sites are `:61` (the `for` target) and `:62` (its
reassignment by `.replace('/volumes/','/')`), and the function returns it. With two
log paths it returns the **second** — the parallel one — in its mutated form:

```
log_paths_for gave: [<...>/default/volumes/VOL_0001_re-validate_x.log,
                     <...>/parallel/volumes/VOL_0001_re-validate_x.log]
returned logfile  :  <...>/parallel/VOL_0001_re-validate_x.log
```

**Behavior deliberately preserved.** The value is what batch mode prints in its
error messages, and which of the two paths it should name is not a question this PR
can answer from evidence. The list is now built once and the function returns
`logfiles[-1]` explicitly, which is the same value with no leak.

**The brief classified B5 as forced by G1. It is not** — same reason as B4.

### 2.6 B6 — `validate_one_volume` reads a module global — **reproduced**

An AST scan of the base function for names it loads and never binds returns
`checksums` among them, read at `:107`. Called with the global unbound:

```
logger.exception: NameError name 'checksums' is not defined
```

At base the global existed (assigned at `:552`/`:560`) and happened to equal
`args.checksums` (`:570`), so the bug was invisible. **This one is genuinely forced
by G1**: under a `main()` the name is a local of `main()` and the read raises on
every run. Note the failure mode is quiet — the `except Exception` at `:190`
catches it, logs it and continues, so the archive-checksum block would simply have
stopped running. Fixed by reading `args.checksums`.

### 2.7 B7 — a one-line log raises `IndexError` — **reproduced**

```
>>> mod.get_log_info(<a log with one record>)
IndexError: list index out of range
```

The guard `if len(recs) < 1` at `:259` is dead — `if not recs` at `:246` already
covers it — and `recs[1]` at `:262` is unguarded. The intended guard is `< 2`.
This matters beyond the exception type: `get_all_log_info` catches `ValueError` and
skips the log, but does not catch `IndexError`, so one truncated log aborted the
whole batch scan. Fixed; pinned by `test_get_log_info_rejects_a_one_line_log` and
`test_get_all_log_info_skips_a_malformed_log_without_raising`.

### 2.8 B8 — `MAX_INFO` is dead — **reproduced**

`grep -c MAX_INFO` over the base file returns 1, its own assignment. Deleted.

### 2.9 B9 — `type(to_addr) == str` — **reproduced**

`type(Address('a')) == str` is `False` for `class Address(str)`, so a `str`
subclass took the list branch and was split into its characters — one `sendmail`
per letter. Fixed with `isinstance`; pinned by
`test_format_email_accepts_a_string_subclass`.

### 2.10 B10 — the commented-out `sys.exit(status)` — **reproduced**

Base `:826-828` holds `#     sys.exit(status)` above a live `sys.exit(0)` whose
comment ends "Does this help??". **Behavior kept exactly**: batch mode still exits
0. The commented-out line is gone and the comment now states the current reason
rather than asking a question. `status` was then unused, and inside a function
would have been an `F841`, so its assignment is gone too and the `logger.close()`
result is discarded as `_`, which is the spelling `_common.py` already uses.

### 2.11 B11 — a changed volume is listed twice — **reproduced; not in the brief**

Found while measuring the `--batch-status` output diff. At base `:379-384`:

```python
modified_holdings = [holdings_dict[info[1]] for info in modified_holdings]

for (_, key) in modified_holdings:      # <- these are now (abspath, modtime)
    if key in log_dict:
        del log_dict[key]
```

After the comprehension, `modified_holdings` holds `(abspath, modtime)` pairs, so
`key` binds a **modification time**, never a `log_dict` key, and the deletion never
happens. A volume that is both changed since its last run and previously logged
therefore appears in `modified_holdings` **and** in `current_log_info`.

In isolation:

```
modified_holdings : [('/h/holdings/volumes/VS_1xxx/VOL_0001', 'new')]
current_log_info  : ['/h/holdings/volumes/VS_1xxx/VOL_0001', ...]
listed in both    : {'/h/holdings/volumes/VS_1xxx/VOL_0001'}
```

Against the real test holdings it is visible in `--batch-status` output as one
volume printed on two lines, once as "not previously validated" and once as "last
validated 2026-01-02" (§7). In batch mode proper, that volume would be validated
twice in one run, and the run's time budget spent on it twice.

This is also the `RUF051` site the ratchet asks to clean, so the block had to be
touched regardless. Fixed by keeping the keys and the pairs in separate names.
Pinned by `test_a_changed_volume_is_not_also_listed_as_validated`.

### 2.12 The negative control

The head test module **cannot** be run against the base module: importing the base
module parses whatever is in `sys.argv`, so pytest collection dies before a test
runs —

```
INTERNALERROR> File ".../re_validate.py", line 533, in <module>
INTERNALERROR>   args = parser.parse_args()
INTERNALERROR> SystemExit: 2
```

— which is itself the sharpest statement of G1 available. The per-bug negative
control (`scratchpad/negative_control.py`) therefore loads the base module's
**library half** (everything above the `# Executable program` banner) and asserts
each bug is still there:

```
$ python negative_control.py <base tree>
B1  PRESENT  --volumes --previews -> ['volumes']
B2  PRESENT  the `if volume_abspath == ""` block is [Continue, Assign, Expr]
B3  PRESENT  NameError: name 'abspath' is not defined
B6  PRESENT  `checksums` is read at line 107 and never bound in the function
B4  PRESENT  the dependency block logs bare `abspath` at lines [180, 182]
B5  PRESENT  returns the loop variable `logfile`, whose only binding is the for statement at line 61
B7  PRESENT  IndexError: list index out of range
B8  PRESENT  MAX_INFO appears exactly once in the file, at its assignment
B9  PRESENT  type(Address("a")) == str is False, ...
B10 PRESENT  the commented-out sys.exit(status) and the "Does this help??" comment
B11 PRESENT  listed in both lists: ['/h/holdings/volumes/VS_1xxx/VOL_0001']

all eleven present at base: True
```

### 2.13 The mutation control

Round 1 of review made the right objection to §2.12: showing a bug exists at base
says nothing about whether the *new tests* catch it. `scratchpad/mutate.sh` answers
that directly. It copies the head worktree — a copy is required, because
`pyproject.toml`'s `pythonpath = [".", "src"]` beats `PYTHONPATH`, so editing an
out-of-tree `src` is silently ignored — reinstates exactly one defect, and reruns
the new test module.

| mutation applied to the head tree | result |
|---|---|
| *(none — the baseline)* | **73 passed** |
| B1 `if args.previews:` → `if args.calibrated:` | 4 failed, 69 passed |
| B2 re-indent the two `holdings_for_key` lines under the `continue` | 1 failed, 72 passed |
| B3 `log_path.split('/')` → `abspath.split('/')` | 2 failed, 71 passed |
| B4 `pdsdir.abspath` → `abspath` in both dependency lines | 2 failed, 71 passed |
| B5 `return (logfiles[-1], …)` → `logfiles[0]` | 1 failed, 72 passed |
| B6 `args.checksums and args.archives` → `checksums and args.archives` | 3 failed, 70 passed |
| B7 `if len(recs) < 2:` → `< 1` | 2 failed, 71 passed |
| B9 `isinstance(to_addr, str)` → `type(to_addr) == str` | 1 failed, 72 passed |
| B11 iterate `modified_holdings` instead of `modified_keys` | 2 failed, 71 passed |
| the misspelling: `re-validation for` → `re-validatation for` | 4 failed, 69 passed |
| exit site 8: bare `sys.exit()` → `sys.exit(0)` | 1 failed, 72 passed |
| exit site 9: `sys.exit(0)` → `sys.exit(1)` | 1 failed, 72 passed |
| `main`: drop the `if argv is None` fallback | 1 failed, 72 passed |
| G1: drop the `if __name__ == '__main__'` guard | collection dies, `INTERNALERROR> SystemExit: 2` |

**Every mutation is caught.** The first draft of this PR failed three of these
rows — B4, B5 and B6 left 62/62 green — which is what round 1 found and what the
`validate_one_volume` test group (§9) was added to fix. B8 and B10 have no row: B8
is a constant that is now restored rather than removed, and B10's behavior *is*
exit site 9.

The two rows that fail four tests rather than one are the ones whose defect is
visible from more than one angle, which is the intended redundancy.

---

## 3. The gaps G1-G8

| # | Gap | Verified at `02f07a8` | Disposition |
|---|---|---|---|
| G1 | no `main()` | `import` with `sys.argv=['re_validate.py']` raises `SystemExit(1)` after printing `Missing volume path` | `main(argv=None)` + `__main__` guard |
| G2 | private `LOGROOT_ENV` | `:30` duplicates `_common.py:25` | import from `_common` |
| G3 | hand-built `--log` help | `:441-448` vs `_common.py:121-125` | `_common.LOG_HELP`; §7 |
| G4 | hand-built `--quiet` help | `:480-481` vs `_common.py:127` | `_common.QUIET_HELP`; §7 |
| G5 | duplicated log-root block | `:586-590` vs `_common.py:244-248` | extracted; §11 |
| G6 | header names `re-validate.py` | `:2-9` | rewritten to the module's real name and the `python -m` line |
| G7 | no test of any kind | `tests/holdings_maintenance/__init__.py:14` | 73 ids |
| G8 | ten-code ratchet entry, `C405` with no site | `pyproject.toml:238`; 25 findings, no `C405` among them | two codes |

`build_arg_parser`/`run_main`/`ToolSpec` were **not** forced onto this tool, per
the brief: it has no five-task flag set, no `task` dest, its positional is
`nargs='*'` not `'+'`, and its driver loop is nothing like `run_main`'s.

---

## 4. Behavior-preservation evidence

The gate is the per-test pass/fail **set**, diffed against the base run, with a
newly-passing id as much a flag as a newly-failing one.

```
$ cd <tree> && PYTHONPATH=$PWD/src PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings \
    PDS4_HOLDINGS_DIR=/seti/opus/pdsdata/pds4-holdings PDSFILE_TEST_HOLDINGS=full \
    <venv>/bin/python -m pytest tests/api/ tests/core/ tests/holdings_maintenance/ \
    tests/pds3file/ tests/rules/pds3/ tests/pds4file/ tests/rules/pds4/ \
    --mode ns -rA -p no:randomly --junitxml=<...>.xml
```

| | base `02f07a8` | head |
|---|---|---|
| `--mode ns` | 935 passed, 34 skipped — **969 ids** | 1008 passed, 34 skipped — **1042 ids** |
| `--mode s` (`tests/pds3file/ tests/rules/pds3/`) | 555 passed, 3 skipped — **558 ids** | 555 passed, 3 skipped — **558 ids** |

Diffing the two `ns` junit id sets:

```
added   : 73      all in tests.holdings_maintenance.test_re_validate, all passed
removed : 0
outcome changed on a shared id: 0
```

`--mode s`: 0 added, 0 removed, 0 outcome changes.
`tests/holdings_maintenance/` is deliberately absent from the `--mode s` pass, so
the new module adding nothing there is the expected result, not a missing run.

### Hosted lint / no-holdings gate

```
$ env -u PDS3_HOLDINGS_DIR -u PDS4_HOLDINGS_DIR -u PDSFILE_TEST_HOLDINGS \
      VENV=<venv> bash scripts/run-all-checks.sh -c -s
```

| | base `02f07a8` | head |
|---|---|---|
| pytest | 165 passed, 804 skipped | **238 passed, 804 skipped** |
| pyroma | 10/10 | 10/10 |
| ruff check, ruff indentation, API freeze, clean-install | pass | pass |

Both rows were measured here, not inherited. The passed count rises by exactly the
73 new ids and the skipped count does not move, which is what `holdings_free`
means: the new module runs with no holdings at all.

### API freeze

`tests/api` is **26 passed**. The four prohibited files are byte-identical to
`02f07a8` (`git diff --stat 02f07a8..HEAD -- <file>` empty for each of
`tests/api/api_manifest.json`, `tests/api/manifest_allowlist.json`,
`scripts/dump_public_api.py`, `tests/api/test_api_freeze.py`).

---

## 5. The API freeze and this module

The manifest covers 43 modules, **none** under `holdings_maintenance`, so this
tool's own function names and signatures are free — which is what permits deleting
`key_from_log_path` and adding six functions. `log_path_for_volume` and its four
siblings **are** frozen and are untouched; `validate_one_volume` still reaches its
log paths through `_common.log_paths_for(pdsdir, 'log_path_for_volume', …)`.

---

## 6. The ratchet

```
$ <venv>/bin/python -m ruff check --config 'lint.per-file-ignores = {}' \
      --output-format concise src/pdsfile tests scripts | grep -c ':'
$ <venv>/bin/python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); \
      p=d['tool']['ruff']['lint']['per-file-ignores']; \
      print(len(p), sum(len(v) for v in p.values()))"
```

| | base `02f07a8` | head | delta |
|---|---|---|---|
| per-file-ignores **entries** | **69** | **69** | 0 — no new key |
| **code slots** | **193** | **185** | −8 |
| findings forgiven, whole tree | **2,297** | **2,280** | −17 |
| findings in `re_validate.py` | **25** | **8** | −17 |
| `re_validate.py` entry | 10 codes | `["RUF005", "UP031"]` | −8 |

**The brief said 70 entries. The measured count is 69**, by two independent
methods: `tomllib` on the parsed table, and `grep -cE '^"[^"]+" = \['` on the file.
The 193 code slots and the 2,297 findings both match the brief.

**Zero new keys and zero widens**, proved rather than asserted: the entry count is
unchanged at 69, every surviving code in the `re_validate.py` entry was already in
it, and no other entry was touched. The configured gate
(`ruff check src/pdsfile tests scripts`) is clean, and so is the preview
indentation gate (`ruff check --preview --select E111,E112,E113 src/pdsfile tests
scripts`).

### The eight codes dropped, each with its site

| code | base sites | why it is gone |
|---|---|---|
| `C405` | **none** | its `set([...])` went with PR-25's log-path fix; the entry kept a code with no site |
| `B007` | `:296` `dirs`, `:761` `had_errors` | renamed `_dirs`, `_had_errors` |
| `E701` | `:577-581` | the five `if x : tests.append(...)` one-liners are now two lines each |
| `E721` | `:414` | B9 |
| `I001` | `:11` | import block sorted; the five sibling imports are one parenthesized `from` |
| `RUF051` | `:384` | B11's block; now `log_dict.pop(key, None)` |
| `RUF059` | `:200`, `:357` ×4 | unread unpack targets underscore-prefixed |
| `UP034` | `:567` | the doubled parentheses around the `linkshelves` narrowing |

### The two codes kept, and why

- **`RUF005`** — head `:928`, `:932`, both `[batch_prefix] + messages +
  [batch_suffix]`. Permanent owner-chosen style exclusion; `x + [y]` is the
  spelling this project uses.
- **`UP031`** — six sites at head, classified against the standing rule
  (`plans/2026-08-04-pr-24-subplan.md` §4.1: permanently excluded on logging calls,
  on `file.write()`s emitting frozen sidecar formats and on hand-aligned column
  blocks; converted only for exception messages and `print()`s):

  | head site | what it is | disposition |
  |---|---|---|
  | `:211` | `logger.info('%d re-validation tests performed' % n, path, force=True)` | **logging call** — permanently excluded |
  | `:878` | `'%20s%-11s  modified %s, %s' % …` | **hand-aligned column block** — permanently excluded |
  | `:443` | the email `From:/To:/Subject:/Date:` block | plain `%` expression the rule does not reach |
  | `:862` | `batch_prefix` | plain `%` expression; feeds both a `print()` and the email body |
  | `:877` | `ps = 'last validated %s' % …` | plain `%` expression |
  | `:917` | `batch_suffix` | plain `%` expression; feeds both a `print()` and the email body |

  A seventh site, base `:444`, was the hand-copied `--log` help text and went with
  G3.

  The four "plain `%` expression" sites were **left alone deliberately**: converting
  them buys nothing on the ratchet (the code stays either way, on `:211` and `:878`
  alone) and each one is text that reaches a user, two of them through an emailed
  report this PR is not chartered to redesign. §11 records this as a decision the
  owner might make differently.

`:211` is *not* converted to the lazy form even though the house logging style is
`%`-args. The standing rule excludes logging calls, and the conversion is not free:
`pdslogger.PdsLogger.log` re-reads a lone positional argument as the keyword-only
`filepath` **only when the message contains no `%` pattern**, so
`logger.info('...%d...', n, path)` raises `TypeError` and the correct form needs an
explicit `filepath=`.

---

## 7. Output changes, enumerated and attributed

The Phase 6 rule: log and output text may move **only** where keeping it would
force duplication or a flag whose one job is to re-create one side's wording. Every
changed line is listed here.

### 7.1 `--help` — two changes, both forced by commonality

```
$ python -m pdsfile.holdings_maintenance.pds3.re_validate --help
```

diffed base against head — the complete diff, nothing else moved:

```
19,22c19,22
<                       variable "PDS_LOG_ROOT" is used. In addition, logs are
<                       written to the "logs" directory parallel to "holdings".
<                       Logs are created inside the "re-validate" subdirectory
<                       of each log root directory.
---
>                       variable "PDS_LOG_ROOT" is used. In addition, individual
>                       logs are written into the "logs" directory parallel to
>                       "holdings". Logs are created inside the "re-validate"
>                       subdirectory of each log root directory.
40c40
<   --quiet, -q         Do not log to the terminal.
---
>   --quiet, -q         Do not also log to the terminal.
```

That is the diff in full — two hunks, four lines against four and one against one.

Both are G3/G4: the tool's hand-built help strings were near-copies of
`_common.LOG_HELP` and `_common.QUIET_HELP`, and keeping them is exactly the
duplication the Phase 6 rule permits removing.

Rendered `--help` is a weak test of a parser, so the parser was also compared
structurally: every `argparse` action at base and at head, dumped as
`(option_strings, dest, nargs, const, default, type, choices, required, metavar,
action class, help)` and diffed. **All 22 actions match except the two `help`
strings above.**

### 7.2 `--batch-status` against the real test holdings — one line, B11

```
$ python -m pdsfile.holdings_maintenance.pds3.re_validate \
      --batch-status --log <logroot> /seti/opus/pdsdata/holdings
494d493
<  494          COCIRS_5xxx/COCIRS_5402  modified 2020-01-01, last validated 2026-01-02, duration 0:00:12
```

One line removed from 494. `COCIRS_5402` was printed twice — at line 10 as
"modified, not previously validated" and again at line 494 as "last validated" —
and now appears once. Attributed to **B11**; a defect fix under ground rule 9.

### 7.3 `--batch-status` against a synthetic tree — one line, B2

One line added, the `Missing volume` error quoted in §2.2. Attributed to **B2**.

### 7.4 The six `re-validatation` misspellings — fixed

Six sites, not four: base `:89`, `:98`, `:120`, `:137`, `:147`, `:169`, counted with
`grep -c`. All six are the first argument of a `logger.open()`.

Both safety checks the brief asked for were run:

- **Nothing parses these lines.** `get_log_info` keys on the first record's `|`
  fields, on `'Last modification'` in the second, and on `'| ERROR |'`,
  `'| FATAL |'` and `'Elapsed time = '` anywhere; `volume_abspath_from_log` reads
  only the first record; `get_all_log_info` keys on the **filename** pattern
  `_re-validate_`. None of them looks at these strings. Confirmed by reading all
  four functions and by `grep -rn 're-validatation'` over the whole repository,
  which returns **only these six sites** — no test, no golden, no script, no
  sibling tool mentions the misspelling.
- **No gate compares this tool's output.** It is in no golden, and `tests/` had no
  reference to the module at all before this PR.

Fixed. This is the one output change **not** attributable to commonality; it is
proposed under ground rule 9 as a defect. Six lines, `re-validatation` →
`re-validation`.

### 7.5 The two dependency log lines — B4

`:180`/`:182` at base logged a leaked loop variable, which in the common case was
the empty list and rendered as no path at all. They now log `pdsdir.abspath`.
Two lines; attributed to **B4**; §2.4 has the rendered before/after.

### 7.6 The one comment change — B10

`sys.exit(0)`'s comment no longer asks "Does this help??". Behavior unchanged.

### 7.7 What B1 changes about which events are logged

B1 is a fix to *option derivation*, so for the three command lines it corrects it
also changes which volume types a run walks — and therefore the `Volume types` INFO
line and the set of per-voltype `logger.open` events. `--previews` alone now opens
events for the previews tree instead of for all five; `--volumes --previews` now
opens them for two trees instead of one; `--calibrated` for one instead of two. No
message text changes; the run is doing what the flags asked for instead of
something else. Enumerated here because §7 is the section the output rule points
at, and §2.1 alone was not enough.

**With §7.1 to §7.7 accounted for, no other log line at any level changed. No event
was added, removed or moved between levels, and no log file's path or name
changed.** `_common.log_paths_for(…,
dir=PROGNAME)` with `PROGNAME = 're-validate'`, and the log root subdirectory is
still `re-validate`, both unchanged.

---

## 8. Exit codes

Enumerated from the base tree before anything was touched. There are **nine**
sites, not the eight the brief describes — the brief says "four sites" of
`sys.exit(1)` on a missing/invalid path, and there are **six**.

| # | base site | condition | status | pinned by |
|---|---|---|---|---|
| 1 | `:614` | interactive, no volume named | 1 | `test_interactive_mode_with_no_path_exits_1` |
| 2 | `:619` | interactive, volume path does not exist | 1 | `test_interactive_mode_with_a_missing_path_exits_1` |
| 3 | `:629` | interactive, not a volume path | 1 | not pinned — needs a `Pds3File` (§13) |
| 4 | `:654` | interactive, end of run | 1 if fatal or errors, else 0 | not pinned — needs a real run (§13) |
| 5 | `:664` | batch, no holdings path named | 1 | `test_batch_mode_with_no_path_exits_1`, and `test_the_program_exits_1_in_batch_mode_with_no_holdings` end to end |
| 6 | `:670` | batch, holdings path does not exist | 1 | `test_batch_mode_with_a_missing_path_exits_1` |
| 7 | `:677` | batch, not a holdings directory | 1 | `test_batch_mode_with_a_non_holdings_path_exits_1` |
| 8 | `:741` | `--batch-status`, after printing | bare `sys.exit()` → 0 | `test_batch_status_exits_0` |
| 9 | `:827` | batch mode, end of run | `sys.exit(0)` always | not pinned — needs a real run (§13) |

Every one is unchanged. Site 8 is still a **bare** `sys.exit()` and site 9 still a
`sys.exit(0)`: the two produce the same status but are not the same call, and both
are kept as the author wrote them. `test_batch_status_exits_0` asserts
`exc.value.code is None`, which is what distinguishes them.

End to end, `python -m …` with no arguments exits 1 printing `Missing volume path`,
and `--help` exits 0 — both pinned.

---

## 9. The test module

`tests/holdings_maintenance/test_re_validate.py`, `pytestmark =
pytest.mark.holdings_free`, **73 ids, all passing**.

**73 ids** after round 1 of review, which added eleven. It runs **in-process**,
which deviates from every sibling module in the directory.
The sibling convention exists because `PdsFile.CACHE` is keyed by logical path and
the session preloads the real tree, so an in-process call would resolve a
temporary-tree path back to the real tree. That reason does not apply here: every
function under test is pure over text, paths and an argparse namespace, and none
constructs a `PdsFile`. The module header says so, and so does the directory's
`__init__.py`.

Five tests use a subprocess anyway, and only these five: the two import-inertness
tests, which need an interpreter that has not imported the module yet, and the
three end-to-end `python -m` cases.

The group counts below were taken from `pytest --collect-only`, not from reading:

| group | ids | what they pin |
|---|---|---|
| import inertness | 2 | importing parses no command line and calls no `sys.exit` (G1); importing registers no `pds.validation` logger and sets no log root |
| option derivation | 20 | B1 ×3; `--all`/`--full` defaults; `--all` overriding a narrower set; one-flag selection; the `dependencies &= 'volumes' in voltypes` and `linkshelves &= …` narrowing, the latter over each of the three volume types a link shelf exists for; `--timeless` surviving only with `--dependencies`; the derived values landing back on `args`; and that two derivations do not share a list |
| log parsing | 19 | `get_log_info` on good, error, fatal, truncated, empty, one-line (B7), other-tool and no-modification-line logs; `volume_abspath_from_log` on good and empty; `key_from_volume_abspath`; `key_from_log_path` (B3), including that it agrees with the key the batch scan derives inline; `get_all_log_info` over a `tmp_path` tree — newest-wins, FATAL fallback, the path-disagreement branch, non-log files, and a malformed log not aborting the scan (B7) |
| `find_modified_volumes` | 6 | modified, unmodified, missing, the tree-relocation redirect, oldest-first ordering, and B11 |
| missing-volume report | 3 | B2, plus the two controls that keep it honest |
| `validate_one_volume` | 6 | B4 ×2 (plain and `--timeless`), B6, B5, the six misspelling sites, and the closing test count — all driven over a real temporary volume tree with the five sibling tools and the logger stubbed |
| the email message | 4 | built without a socket: one address as a string, a `str` subclass (B9), a list, and the exact header block |
| exit codes and `main` | 13 | §8, plus that `main(argv)` parses and forwards the argv it is given and defaults to `sys.argv` |

`send_email` was split: `format_email(to_addr, subject, message, date=None)` builds
the recipients and the message text and is what the tests call; `send_email` opens
the `SMTP` connection and calls it. **No test opens a socket.**

---

## 10. What `_common.py` gained, and why (G5)

`resolve_log_root(args)` — five lines, previously written twice among the files
this PR touches, and eleven times across the package:

```python
if args.log == '':
    try:
        args.log = os.environ[LOGROOT_ENV]
    except KeyError:
        args.log = None
```

The owner's rule is to decide by volume — *"Only a little, put in same file. A lot
put in a separate file."* — and `_common.py` already exists, so the question is
only whether to share at all. The PR-25 data-only rule says do not share a function
if sharing needs a boolean flag whose one job is to re-create one side's quirk.
**It needs no flag**: the two copies were character-for-character identical, both
mutate `args.log` in place, and both leave the same three-state result (a path, or
`None`). Shared.

Measured: `grep -rn LOGROOT_ENV src/` finds the constant defined in **nine** other
tool modules, each above its own copy of this block. Only two tools reach it
through `run_main` today (`grep -rln '_common.run_main' src/` returns
`pdsarchives.py` and `pds4archives.py`); PR-26 and PR-27 migrate the rest, and each
one they migrate collapses another copy onto this helper. So the helper is not
sharing-for-two — it is the eleventh copy declining to be written.

The cost is that `run_main` changed, and both tools on it go through `run_main`.
That is covered by the id-set diff in §4: 0 outcome changes across 969 shared ids,
which includes all of `tests/holdings_maintenance/`.

G2-G4 needed no decision — they are constants already sitting in `_common.py`, and
the tool now imports them.

---

## 11. Decisions the owner might make differently

1. **`key_from_log_path` and `MAX_INFO` are kept, not deleted** (§2.3, §2.8).
   Both are unreachable — the function raises on every call, the constant is read
   nowhere — and the first draft deleted both. Ground rule 9 says *"Nothing is
   deleted for being 'probably dead'"*, so both are restored: the function with its
   bug fixed and two tests, the constant as it was, with a comment saying it is
   unread. If the owner reads ground rule 9 as being about *features* rather than
   about every name, both could go.

   One deletion **is** in the diff and cannot be undone: `roots = set()`, base
   `:623`, an interactive-mode local that was assigned and never read. At module
   level ruff does not flag it; as a local of `run_interactive` it is an `F841`,
   and absorbing a new code would widen the ratchet, which is prohibited. So the
   refactor forces the choice between deleting it and widening. It is deleted.
2. **G5 was shared** (§10). The alternative reading of "only a little, put in same
   file" is that five lines are too few to move and the tool should keep its own
   copy. Sharing it means `run_main` — the path all eleven migrated tools take —
   changed in a PR whose subject is a twelfth tool.
3. **The four plain-`%` `UP031` sites were left alone** (§6). Converting them
   changes no gate result either way; leaving them keeps this PR out of an emailed
   report's wording.
4. **B5's returned log path was preserved, not corrected** (§2.5). It returns the
   *parallel* log path where a reader might expect the default one. That is a
   behavior question the evidence does not settle, so nothing was changed.
5. **The six `re-validatation` fixes** (§7.4) are the one output change not forced
   by commonality. Both safety checks passed, but it is a judgement call and it is
   flagged rather than buried.
6. **`ALL_VOLTYPES` and `LINKSHELF_VOLTYPES` are new module constants** naming two
   literals that each appear once. They make the domain facts findable; they also
   add two names to a module the owner may prefer to keep literal.

---

## 12. Numbers not measured at this head

Three, all of them flagged where they appear:

1. The **REST-group** totals in `pyproject.toml`'s ratchet header and in
   `pdsfile_overrides.mdc` (2,258 over 58 entries / 179 code slots before this PR;
   2,241 / 58 / 171 after) are **inherited** from the PR-24 and PR-25 records. What
   was measured here is the **delta**: `re_validate.py` alone went from 25 findings
   to 8 and from 10 code slots to 2, and no other file's entry moved. The group
   totals follow by arithmetic from a base this PR did not re-derive, because
   re-deriving them means reconstructing PR-24's file partition.
2. The **whole-tree** figures in §6 — 69 entries, 193→185 slots, 2,297→2,280
   findings — **were** measured at both commits, and 69 contradicts the brief's 70.
3. No line count of any file is cited anywhere in this record, deliberately: the
   Phase 6 record's line counts were found stale on 2026-08-06 and are being
   corrected separately.

---

## 13. What is not covered

- `validate_one_volume`'s body and the batch driver loop. They call the five
  sibling tools against a real volume; those tools have their own test modules, and
  driving them again from here would duplicate that at high cost. The functions
  around them — option derivation, log parsing, the missing-volume report, the exit
  codes — are covered.
- `get_volume_info`. It globs a real holdings tree and builds a `Pds3File` per
  volume, so it cannot run in a `holdings_free` module.
- Exit-code sites 3, 4 and 9 (§8). Site 3 needs a real `Pds3File`; 4 and 9 need a
  completed validation run.
- `send_email`'s socket half. Deliberate: no test opens a socket.
- `scripts/check_runtime_imports.py` still covers seven core modules only and not
  the tool modules. Out of scope by the brief; filed as deferred observation 105.
- The `--batch-status` **output format** is pinned by nothing:
  `test_batch_status_exits_0` drives `print_batch_status([], [])` and asserts the
  exit and that nothing is printed, not the two `%`-format column layouts. The
  base-vs-head run diff in §7.2 is what covers the format for this PR, and it is
  not a standing regression test. Building one means a `Pds3File` per row, so it
  belongs with the holdings-backed tool tests rather than in a `holdings_free`
  module.
