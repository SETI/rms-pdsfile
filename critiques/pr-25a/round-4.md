# PR-25a adversarial review — round 4 (final)

A fourth fresh reviewer, no prior context, given the diff, both worktrees, the
record and all three prior round records. It was told this was the last round, that
all four documents were under review, and that the demonstrated failure mode across
rounds 1-3 is: **a fix lands, and prose elsewhere that mentioned the same fact goes
stale.** It was pointed first at round 3's own fixes, which nobody had read.

Result: **2 Major, 8 Minor, 2 Deferred.** All accepted; one Deferred promoted to a
recorded observation.

Both Majors were created by round 3's fix commit. That is the finding worth keeping:
in this PR, the highest-risk edit at any moment was the previous round's correction.

---

## Major

### MJ-1 — round 3's docstring fix shifted every line below it by two, and §6's line numbers with it

**Finding.** Round 3's m12 replaced one line of `print_batch_status`'s docstring
with three (`re_validate.py:789-791`). Everything below ~790 moved by +2, and §6's
head-site citations did not. Six of eight were wrong. Round 3 had verified those
same numbers "by line number" earlier in the same commit — it checked them, then
broke them.

**Disposition: accepted, fixed.** All eight re-measured from `ruff check` output
after the last code edit on the branch, not from reading:

```
:211 UP031   :443 UP031   :864 UP031   :879 UP031   :880 UP031   :919 UP031
:930 RUF005  :934 RUF005                                   Found 8 errors.
```

§6 now carries those, and opens by saying they were re-measured after the last code
edit and that three rounds of review had moved them. The underlying claims — 25 → 8
findings, `RUF005` ×2 and `UP031` ×6, no `C405` site at base — were correct
throughout and the reviewer re-derived them independently.

### MJ-2 — the "four functions that touch Pds3File" list was one short, and the missing one is `main`

**Finding.** Round 3's rewritten header said four functions under test construct a
`PdsFile`, and that *"everything else under test is genuinely pure over text, paths
and an argparse namespace"*. The four are right as far as they go — the reviewer
confirmed they are exactly the functions under test that call `from_abspath`, and
that excluding `get_volume_info` is correct because it is stubbed and never driven.

But `main` is under test through five direct callers and is in neither list, and it
calls `Pds3File.set_log_root` — a classmethod that writes `cls.LOG_ROOT_`
(`src/pdsfile/_derived_paths.py:194-206`). It does not *construct* a `PdsFile`, so
it fell through a rule phrased around construction. A test written to that rule
leaks process-wide state:

```
Pds3File.LOG_ROOT_ before: None
Pds3File.LOG_ROOT_ after : '/tmp/pytest-of-.../test_driving_main_without_stub0/'
```

Every existing `main` test does stub `re_validate.pdsfile`, and one of their
docstrings says why — so the knowledge was in the module and not in the header that
exists to carry it.

**Disposition: accepted, fixed.** Both headers and record §9 now say **five**, split
by what each does: four construct through `from_abspath`, and `main` writes class
state through `set_log_root`. The reviewer's secondary point is also taken — "every
test that reaches one of them stubs first" was false under the natural reading,
because two tests call `run_interactive` and one calls `print_batch_status` with no
stub and are safe only because they return before the construction. The header says
that explicitly now, as something to check rather than to copy.

---

## Minor

| # | Finding | Disposition |
|---|---|---|
| m1 | §2.13 got an as-run annotation and §2.14 did not, while §2.13 asserted §2.14 "was run against the current module" — false, its baseline is 84 and the module is 85 | **accepted, fixed.** Both tables carry the annotation, and the false claim is gone |
| m2 | round 3's "(now 249)" / "(now 1,014)" annotations in `round-2.md` were off by one, falsified by round 3's own added test | **accepted, fixed.** The bare figures are gone; the note now points at record §4 as the single place current figures live, and says why — the first attempt at that note made itself stale within one commit |
| m3 | `round-3.md` quotes its own suite and gate figures as current, without the as-found note it had just written into `round-2.md` for the identical reason | **accepted, fixed.** Same treatment, applied to itself |
| m4 | commit `a93a6e3` says three tests use a subprocess; there were five even then | **accepted, not rewritten**, for the reason round 3 gave for the same commit: the correction belongs adjacent to the claim in history, not in place of it. Recorded here so the count is on the record |
| m5 | §7 never enumerated `' '.join(sys.argv)` → `' '.join(argv)` at `:687` and `:870`, although round 3's AST diff found it and `round-3.md` called that diff "the whole of §7" | **accepted, fixed.** New §7.7. The rendered output is identical whenever `main()` supplies the argv, which is every real invocation, but the rule asks for every changed source line that produces logged text |
| m6 | §9's group table still had nine rows after round 3 gave the `python -m` tests their own banner; the three ids were folded into "exit codes and `main`" | **accepted, fixed.** Ten rows, 16 + 3, still summing to 85 |
| m7 | after round 3's edit, §12's title "Numbers not measured at this head" no longer describes its contents | **accepted, fixed.** Retitled to what it now is: numbers whose provenance is something other than "I ran this at both commits" |
| m8 | `round-3.md`'s "there is no `import *` anywhere in the package" is false as written (`src/pdsfile/__init__.py:14,15`) | **accepted, fixed.** Scoped to `holdings_maintenance/`, which is what the argument needed |

---

## Deferred

- **Batch mode with no log root at all crashes.** `get_all_log_info(args.log)` with
  `args.log` None — which is what `resolve_log_root` leaves when neither `--log` nor
  `PDS_LOG_ROOT` is set — reaches `os.walk(None)` and raises `TypeError`. I
  reproduced it at both commits, identical, exit 1 both, so this PR neither causes
  nor fixes it. **Promoted to deferred observation 108** rather than left in a round
  record, with the note that the right repair is a decision about how the launch
  daemon should behave on a fresh install, not a one-liner.
- §7.2 and §7.3 remain non-reproducible from the record alone, as rounds 1 and 3
  both recorded. Unchanged: committing the scratch scripts is a convention change
  this PR should not make by itself.

---

## What this round confirmed, measured here

Round 3's fixes hold where they claim to: deleting the fixture's one
`monkeypatch.setattr(re_validate, 'pdsfile', …)` line still passes 85, so the stub
really is what makes the module safe; forcing the interactive status to a constant 1
fails one test and to a constant 0 fails the other, so §8's site-4 row is accurate
in both directions; site 3 genuinely is unpinned; §2.14's site-6 row still fails;
restoring `roots = set()` still produces `F841`. An AST scan confirms no unresolved
free name survives anywhere in the module.

It re-measured **the last figure in the record that was still inherited** — the
`--mode ns` base of 935 passed / 34 skipped — and confirmed it, along with head at
1,020 / 34, +85. Also re-derived here: the ratchet (69 entries, 193 → 185 slots,
2,297 → 2,280 findings, configured gate clean, `ruff format --check` still "would
reformat" all three files, so it was not run); the `2,280 − 39 = 2,241` cross-check,
with CORE's 39 derived as 40 less `_version.py`; all 21 `add_argument` calls
identical but for the two help strings; the `--help` diff exactly §7.1's two hunks;
an independent AST diff of all 48 `print`/`logger.*` calls at both commits, whose
complete difference is the six misspellings, the two `abspath` → `pdsdir.abspath`,
and the two `sys.argv` → `argv`; and rules 3 through 11.

Id provenance was checked by collecting at each commit: **62 → 73 → 84 → 85**.

**Not checked by this round:** §7.2/§7.3's output diffs; a real interactive
validation run (round 2 did that); `send_email`'s socket half; `pyroma` and
clean-install (rounds 2 and 3 did those); coverage; a full re-run of §2.13/§2.14.
