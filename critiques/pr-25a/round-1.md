# PR-25a adversarial review — round 1

A fresh reviewer subagent with no prior context was given the diff
(`git diff 02f07a8..HEAD`), the two worktrees, the validation record, and the
eleven rules the PR is bound by. It was told to measure rather than take the
record's word, and that the record is itself under review.

It built a **mutation harness** the record did not have, and that is what makes
this round worth its cost: it reinstated each fixed bug in a copy of the head tree
and reran the new test module. Three mutations left the suite green.

Result: **2 Major, 10 Minor, 3 Deferred.** Both Majors are accepted and fixed. Of
the ten Minors, nine are accepted and fixed and one is partly rebutted.

---

## Major

### M1 — "eleven bugs, each with a test" was false; three fixes survived mutation

**Finding.** The plan entry and the commit message both claim each bug has a test.
Mutation showed B4, B5 and B6 reinstated with **62/62 still passing**. B3, B8, B10
and the six misspelling sites had no test either. Only five of eleven were pinned.
The record's §2.12 "negative control" is the wrong control for this claim: it shows
the bugs existed at base, which says nothing about whether the new tests catch
them.

**Disposition: accepted, fixed.** This is the finding of the round. The claim was
made from having *written* fixes, not from having measured that the tests fail
without them — which is the exact failure the brief warned about.

Added a `validate_one_volume` test group (6 ids) that drives the function over a
real temporary volume tree with the five sibling tools, the log-path helper and the
logger stubbed: two tests for B4 (plain and `--timeless`), one for B6 that builds a
real `.tar.gz` so the archive-checksum block is reached and asserts nothing was
logged as an exception, one for B5's returned path, one asserting no message
misspells `re-validation`, and one for the closing test count. Added
`test_key_from_log_path` ×2 (B3), `test_batch_mode_exits_0_even_after_a_fatal`
(B10 / exit site 9), and `test_main_uses_the_argv_it_is_given` /
`test_main_defaults_to_sys_argv`. 62 ids → **73**.

Then reran the harness as `scratchpad/mutate.sh`, on fourteen mutations. **Every one
now fails at least one test**; the table is §2.13 of the record. B8 has no mutation
row because the constant is restored rather than removed (see M2), and B10's
behavior is exit site 9, which does have a row.

### M2 — three deletions, under a ground rule that forbids deletion

**Finding.** Ground rule 9: *"Nothing is deleted for being 'probably dead.' Latent
bugs in existing code may be fixed … each with a test, but no feature removal."*
The PR deleted `key_from_log_path`, `MAX_INFO`, and — undisclosed anywhere in the
record — `roots = set()` at base `:623`.

**Disposition: accepted, fixed, with one deletion argued rather than reverted.**

- `key_from_log_path` — **restored**, with its bug fixed to read its own `log_path`
  parameter, and two tests. The second test is the one that shows the fix is the
  intended behavior rather than an invention: it asserts the function returns the
  same key `get_all_log_info` derives inline for the same log file. The original
  reasoning for deleting it — nothing can depend on a function that raises on every
  call — is real but is not what the rule says, and the rule is the owner's.
- `MAX_INFO` — **restored**, with a comment recording that it is read nowhere.
  Restoring it costs nothing: a module-level constant draws no ruff finding.
- `roots = set()` — **stays deleted, now disclosed** (record §11.1). This one the
  refactor forces: at module level ruff does not flag an unread assignment, but as
  a local of `run_interactive` it is an `F841`, and absorbing a new code would widen
  the ratchet, which is a hard prohibition. The choice is delete or widen. The
  record now says so instead of being silent.

---

## Minor

| # | Finding | Disposition |
|---|---|---|
| m3 | `pdsfile_overrides.mdc:125` — the `UP031` count column still read 125; its own enumeration now sums to 124, and the neighbouring `I001`, `B007` and `RUF059` rows were correctly decremented | **accepted, fixed.** Re-measured: `grep -c UP031` over the no-ignores run gives 126 at base, 125 at head. The row's own breakdown is what the column must match, and that is 124 |
| m4 | record §9's per-group id counts said 17 and 13 where `--collect-only` gives 20 and 10 | **accepted, fixed.** The counts are now taken from `pytest --collect-only`, and the table gained the `validate_one_volume` group M1 added. They sum to 73 |
| m5 | "Three tests use a subprocess anyway, and only these three", then names five | **accepted, fixed.** Five |
| m6 | §7.1 quoted an abridged `--help` hunk as "the complete diff" | **accepted, fixed.** The full hunk is now quoted. The reviewer had independently dumped all 22 `argparse` actions and found only the two help strings differ; that was its measurement, not mine, so I ran it myself (`scratchpad/dump_parser.py`) before putting it in the record — 22 actions at base, 22 at head, two `help` strings differ, nothing else |
| m7 | `negative_control.py` and `make_scenario2.py` are cited but exist in neither worktree, so §2.12 cannot be re-run | **accepted, fixed — and partly rebutted.** The house convention is to name scratch scripts by a `scratchpad/` path, which `critiques/phase6-validation.md:93,202,260,309,344` does five times; the record now follows it rather than naming a bare filename. But the reviewer's underlying point stands, so the strongest evidence — the mutation table — is inlined in §2.13 with each mutation spelled out, so it is reconstructible from the record alone |
| m8 | the plan said "six log lines", but six *sites* render 18 lines in a default run, one per applicable volume type | **accepted, fixed.** The plan now says "six log message sites … 18 rendered lines in a default run" |
| m9 | §7's closing "no other log line changed" is overbroad: B1 changes which volume types a run walks, so it changes the `Volume types` line and the set of per-voltype events | **accepted, fixed.** New §7.7 enumerates it, and the closing claim is now scoped to "with §7.1 to §7.7 accounted for" |
| m10 | `LINKSHELF_VOLTYPES` was introduced and used at one site while `derive_options` spelled the same fact out longhand — two places that can drift | **accepted, fixed.** `derive_options` now reads `any(voltype in voltypes for voltype in LINKSHELF_VOLTYPES)` |
| m11 | `main(argv=None)` deviates from all twelve siblings' `def main():` and no test passes a non-default argv | **accepted, fixed.** The signature is what the brief specified, so it stays; the gap was that nothing exercised it. Two tests now do, in-process, with everything main() reaches outside itself stubbed so no logger is built and no log root is set on the real class |
| m12 | §2.4's B4 table covered two of three reachable shapes; with `-D` alone the leaked `abspath` is the last existing voltype directory | **accepted, fixed.** The table has four rows now and names the condition each arises under |

---

## Deferred — accepted as deferred, no action

- `report_missing_volumes` still cannot fire against the real test holdings,
  because that root's realpath contains spaces and `volume_abspath_from_log`
  recovers the path as the last whitespace token. Already filed as deferred
  observation 107; the reviewer reproduced it independently.
- `--batch-status`'s output *format* is pinned by nothing — the exit-code test
  drives it with two empty lists. Added to record §13 as a known gap: a real
  format test needs a `Pds3File` per row and so belongs with the holdings-backed
  tool tests, not in a `holdings_free` module.
- `validate_one_volume`'s full body, the batch driver loop, `send_email`'s socket
  half and `get_volume_info` remain uncovered. Already disclosed in §13. Note M1
  narrowed the first of these considerably.

---

## Coverage of this round

The reviewer stated what it did not check, which is what makes the rest credible:
`--mode s` at base vs head (the PR touches nothing in that pass's scope), a real
interactive validation run (it would write into shared data), `pyroma` and the
clean-install leg, and the inherited REST-group totals, which record §12.1 already
flags as not re-derived.

It independently re-measured and confirmed: the ratchet arithmetic (69 → 69
entries, 193 → 185 slots, 2,297 → 2,280 findings, `re_validate.py` 25 → 8, `C405`
with no site at base); all 22 parser actions; all nine exit-code sites one to one;
the `--batch-status` run diff; the id-set diff (62 added, 0 removed, 0 outcome
changes); the four prohibited files byte-identical; no skips, xfails, inline
`noqa`, f-strings in logging calls, inline annotations, hardcoded holdings roots,
or new console-script name.

This was not a reviewer that found nothing.
