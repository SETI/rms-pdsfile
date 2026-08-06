# PR-25a adversarial review — round 3

A third fresh reviewer, no prior context, given the diff, both worktrees, the
validation record and both prior round records. It was told what rounds 1 and 2
covered and pointed at what neither reached: **the record as a single document**
after two rounds of edits had rewritten parts of it, the round records themselves,
the commit messages against the commits' contents, the `_common.py` change's safety
for the nine tools that do *not* go through `run_main`, the plan and `.cursor/rules`
edits against the tree as it now stands, and round 2's own test additions.

Result: **2 Major, 12 Minor, 2 Deferred.** Both Majors accepted and fixed. Eleven
Minors accepted; one rebutted.

Both Majors are the same shape, and it is the shape a third round was for: **the
code is right and the prose that describes it went stale.** Rounds 1 and 2 each
changed what is covered, and each updated the sections it was arguing about while
leaving the sections that merely mentioned the same fact.

---

## Major

### MJ-1 — the record says two exit-code sites are unpinned; both are pinned, and the same document says so elsewhere

**Finding.** §8's table marked sites 4 (interactive end-of-run status) and 9 (batch
mode's deliberate exit 0) "not pinned — needs a real run", and §13 repeated it.
Both are pinned: §2.13's own mutation table already carries a row for site 9, added
by round 1. The reviewer measured site 4 too — forcing `status = 1 if (fatal or
errors) else 0` to a constant fails a test.

§13 is the section a later maintainer reads to decide what to test next, so a false
"not covered" there is worse than a missing one: it invites duplicate work and
misstates the risk.

**Disposition: accepted, fixed, and the gap it exposed closed.** Site 9's row is
corrected. Site 4 was pinned only in the **0 direction** — a clean run exits 0 —
so a test was added for the other: `test_interactive_mode_exits_1_after_an_error`
drives a logger reporting one error and asserts exit 1. Verified in both
directions with my own mutations:

```
status = 1 (constant)  ->  1 failed, 84 passed
status = 0 (constant)  ->  1 failed, 84 passed
```

Site 3, the "Not a volume path" refusal, **is** genuinely unpinned — the one test
reaching that branch drives it in the false direction. §13 now says so, and only
that.

### MJ-2 — the test module's header states two things that are false, and one of them is the justification for how the module runs

**Finding.** `tests/holdings_maintenance/test_re_validate.py` opened with *"What is
deliberately not covered: validate_one_volume() and the batch driver loop"* — 680
lines above its own `validate_one_volume` section banner and the nine tests under
it. `tests/holdings_maintenance/__init__.py` and record §13 repeated it. The header
was true when written and round 1's commit falsified it; nothing updated it.

The second false claim is the serious one. The header justified running in-process
— the module's one deviation from this directory's subprocess convention — on the
grounds that *"none of them constructs a PdsFile"*. Measured false: four functions
under test call `pdsfile.Pds3File.from_abspath`. The reviewer proved the module is
safe for a different reason by deleting the fixture's `monkeypatch.setattr(
re_validate, 'pdsfile', …)` line — still **84 passed**, with real `Pds3File`
objects built from the temp tree and nothing noticing.

So the module is safe because every test that reaches one of those four **stubs the
class**, which is an invariant a future test must maintain, not a property of the
code that holds automatically. The header was telling a future author that the
`PdsFile.CACHE` hazard does not apply here. It does.

**Disposition: accepted, fixed.** Both headers rewritten. They now name the four
functions that do construct a `PdsFile`, say that every test reaching one replaces
the class with a stub first, and state plainly that a new test which forgets to
inherits the cache hazard in full. Record §13's bullet is rewritten the same way.

---

## Minor

| # | Finding | Disposition |
|---|---|---|
| m1 | the record's preamble said both controls are "in §2.12"; `mutate.sh` is §2.13, and §2.14 — the single-site table that actually establishes non-vacuity — was not mentioned at all | **accepted, fixed.** All three controls named, with what each does and does not establish |
| m2 | the test module header still said "the **two** exceptions … use a subprocess"; there are five | **accepted, fixed** as part of MJ-2's rewrite. Round 1 fixed this count in the record and not in the file the record describes |
| m3 | commit `3b87d66` says "Ten more tests, 73 -> 84"; eleven were added | **accepted, fixed.** That commit is amended |
| m4 | commit `a93a6e3` says "Each of the eleven fixed bugs has a test", false against its own contents | **accepted, not rewritten.** The claim was wrong when written and that is what round 1 found. The very next commit, `1bf10ca`, opens "the tests did not pin three of the eleven fixes", so a `git log` reader meets the correction immediately after the claim. Rewriting a merged-into-branch history to hide a wrong claim is worse than leaving the correction adjacent to it |
| m5 | `round-2.md`'s hosted-gate figure (238) and whole-tree `--mode s` figure (1,003) predate that round's own eleven tests | **accepted, annotated rather than restated.** A round record should say what that round saw. A note now says both are as-found and points at record §4 for current figures |
| m6 | §12 lists the REST-group totals as "not measured at this head", but rounds 2 and 3 both re-derived them | **accepted, fixed.** §12 now says they were inherited when written, that two rounds have since re-derived them independently and both got 2,258 → 2,241, and that round 3 cross-checked it as 2,280 − 39 (CORE). It stays in §12 because I did not measure it |
| m7 | §4 said round 2 ran "the whole tree" and then quoted `pytest tests/pds4file/`, a subset | **accepted, fixed.** The prose now distinguishes the round's whole-`tests/` run from the `tests/pds4file/` subset I re-measured |
| m8 | §2.13's table is captioned at 73 ids while the module is at 85 | **accepted, annotated.** The table now says its counts are as-run at 73 and understated, that it was not re-run because a mutation cannot change direction when tests are added, and that §2.14 is the table run against the current module |
| m9 | `[sys.executable, '-m', '…', *args]` is the `[*x, y]` spelling rule 8 names | **rebutted.** `.cursor/rules/pdsfile_overrides.mdc` deviation (4) settles this explicitly: the rule is about *ruff's rewrite of a concatenation*, "not a claim that no `[*x, y]` exists in the tree", and converting a directly-written unpacking into `x + [y]` **manufactures** a `RUF005` that a file with no per-file-ignores entry cannot absorb without widening the ratchet. `support.py:200` is named there as such a site, left alone for that reason. These two are the same case. The reviewer flagged it as the owner's call and as something a `grep '\[\*'` finds — both fair; the answer is already written down |
| m10 | three end-to-end `python -m` tests sat under the `_common` log-root banner | **accepted, fixed.** They have their own banner now |
| m11 | "corrected the brief's classification of **three** others" — only two are named | **accepted, fixed.** Two: B4 and B5 |
| m12 | `print_batch_status`'s docstring said "with status 0", erasing the bare-`sys.exit()`-vs-`sys.exit(0)` distinction §8 is at pains to preserve | **accepted, fixed.** The docstring now says it is `sys.exit()` with no argument, that its code is `None` and its status 0, and that it is not the same call as the `sys.exit(0)` ending a batch run |

---

## Deferred

- **§7.2 and §7.3 cannot be reproduced from the record alone.** §7.2's `<logroot>`
  is never named and §7.3's synthetic tree comes from `scratchpad/make_scenario2.py`,
  which is in neither worktree. These are the only base-vs-head evidence *against
  data* for the B11 and B2 output changes. Round 1 accepted the same point (m7) and
  answered it by inlining the mutation table; this is the residue. Not blocking:
  both changes are pinned by unit tests all three rounds verified, and round 2
  independently reproduced the B4 half of the output diff on a real interactive run
  it built itself. Recorded here rather than fixed, because committing scratch
  scripts is a convention change this PR should not make on its own.
- **Deferred observations 105-107** were unreviewed by rounds 1 and 2. Round 3 read
  all three against the tree and confirmed each: `_TOP_MODULES` at
  `scripts/check_runtime_imports.py:27-35`, the nine surviving `LOGROOT_ENV`
  definitions, and the last-whitespace-token path recovery.

---

## What this round independently confirmed

The reviewer AST-diffed **every argument of every `print()` and `logger.*()` call**
between base and head — a check neither earlier round ran, and the sharpest
available test of rule 2. The complete set of differences is: the six misspelling
strings, the two `abspath` → `pdsdir.abspath` (B4), and the two `' '.join(sys.argv)`
→ `' '.join(argv)`. **Nothing else.** That is the whole of §7, independently
derived from the syntax tree rather than from a run.

It also verified §11.1's single deletion is forced rather than chosen: restoring
`roots = set()` as a local of `run_interactive` does produce `F841` under the
configured gate.

And it closed the one question about blast radius that neither earlier round
answered directly: the `_common.py` change is additive plus one call-site
substitution inside `run_main`, there is no `import *` anywhere in the package, no
name collision, and `_common` is in no manifest — so the nine tools that keep their
own log-root block are untouched by construction, not merely by test.

Re-measured and clean: the ratchet at both commits, including every one of §6's
eight dropped-code sites and six kept `UP031` sites by line number, and the `.mdc`'s
corrected REST-scope counts (`UP031` 124, `I001` 4, `B007` 1, `RUF059` 1, `RUF005`
4); the nine `sys.exit` sites one to one; `--help`; `--mode ns` at head (1,019
passed); the hosted gate (249 passed / 804 skipped); rules 4, 5, 7, 9, 10, 11;
`ruff format` demonstrably not run. An AST scan of the head confirmed **no
surviving analogue of B6** — no function has an unresolved free name — so that
class of defect is structurally closed rather than merely fixed in one place.

**Not checked by this round:** `send_email`'s socket half; coverage percentages; a
full re-run of §2.13/§2.14's mutation tables (it ran four of its own); `--mode ns`
at base, which it took from §4 and round 1 on trust.
