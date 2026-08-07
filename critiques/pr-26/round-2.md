# PR-26 adversarial review — round 2

Two fresh no-context reviewer subagents, run against `edb055a` and re-checked at
`aabf981`. One was pointed at the **behavioral correctness of the refactor**, the
other at **whether the fixes are correct and the tests are real**. Both were told
about the measurement trap in deferred entry 110, and both were told that a
reviewer reporting nothing may simply have looked at too little.

Between them they ran 125 differential scenarios with a base-versus-base control,
a full mutation campaign (each fix reverted in a scratch tree and the suite
re-run), and a `--help` comparison across all twelve tools rather than the four
this PR migrates.

## Neither found an unintended behavior change in the migration

That is the finding the round was for, and both reached it by measurement rather
than by reading alone. Reviewer A's 125 scenarios reduce entirely to the
enumerated changes; its base-versus-base control isolated the one scenario that
was log-timetag noise. Reviewer B reverted each fix individually and confirmed
that exactly the expected test fails each time, with no fix landing untested.

Two of reviewer B's checks are worth repeating because they validate round 1
rather than this PR: at `edb055a`, reverting the **pds4** `modtimes_agree` call
site left the entire suite green — the pds4 half of behavior change 6 could have
been deleted unnoticed — and the pds3 tolerance test passed even when
`validate_infodict` was sabotaged to report a checksum mismatch for every file.
Round 1's changes closed both.

## Findings acted on

| # | Finding | Action |
|---|---|---|
| A-F1 | `subprocess.run` **raises** where `os.system` returned a status, for a chained command that cannot be executed. Also: no shell interpretation at all, and SIGINT is no longer ignored in the parent | Enumerated. §2.3 now says this is **four** behavior changes in one line, not two |
| A-F2 | `re_validate --infoshelves` calls `pdsinfoshelf.validate()` directly, so the fixed comparison changes what the **scheduled, error-mailing** tool reports | Enumerated in its own section. Verified independently: `re_validate.py:152,183` call it, `:933` mails on error |
| A-F3 / B-F7 | The log-path alias test recorded only `kwargs` and discarded `parts` — the one thing that differs between a bundle and a bundle-set path. Vacuous for its stated purpose | **Fixed.** `RecordingPdsFile` records `(parts(), kwargs)`, and a third assertion proves the two kinds differ. The mutation that defeated it now fails it |
| A-F4 / B-F6 | `ToolTree.env` passed the ambient environment through, so a tool subprocess imported whichever `pdsfile` was installed | **Fixed** at the shared seam rather than only in the new helper: `env` now pins `PYTHONPATH` to `REPO_ROOT/src`. Recorded as deferred 121 |
| B-F1 | `modtimes_agree`'s `try` did not cover the subtraction, so a tz-aware/naive pair or a non-string raised `TypeError` — contradicting its own docstring | **Fixed.** The subtraction is inside the `try`, which now catches `TypeError` too |
| B-F2, B-F3 | The record's "strict subset" and "never two identical strings" claims are false **as stated**, because they hold on the parse path and not on the string fallback | **Record corrected.** Both are now scoped to the values `generate_infodict` emits, with the unreachability stated rather than implied |
| B-F4 | The inclusive tolerance means an **exactly** one-second change is reported as no change, so the removed class is not purely false positives | **Record corrected**, and recorded as deferred 120. The `<=` form is kept: it is what the plan prescribes and what `validate_tuples` already uses |
| A-F5 | The module header named the indexshelf tools, which do not use `_shelf_common`; `LOGDIRS`' comment said `main()` fills it in, which is no longer true for four of six tools; three test docstrings said the same on lines this PR had already edited | **Fixed**, all five |
| A-F7 | Four blank lines in `_common.py` where a function was removed, one too few in `_archives_common.py` | **Fixed.** `E303,E305` clean on all three modules, matching base |

## Findings recorded rather than acted on

- **A-F7 (forward)**: `run_selection_main` reads `args.archives` unconditionally,
  and none of the four tools PR-27 migrates declares `--archives`; and
  `build_arg_parser` now `.format()`s every extra argument's help, so a literal
  `{` would raise. Both are latent — every current caller supplies the flag and a
  formattable help string — and guarding them now would be speculative generality
  for a caller that does not exist. Left for PR-27 to hit deliberately.
- **B-F5**: the pds4 `--infoshelf` chain is a silent no-op and nothing pins it.
  Already deferred 109; the observation that no test pins it is fair, but pinning
  a defect the owner has an open decision on would have to be inverted with the
  fix.

## What the round changed about the evidence, not just the code

Three of the eight findings were about **the record over-claiming**, not about the
code being wrong: two universal statements that hold only over the produced data,
and a characterization of the removed mismatch class that was tidier than the
truth. All three are now scoped. The one that mattered most is the exact
one-second case: the PR description said the change "removes false positives
only", and that is not quite true — an exact whole-second shift is a real change
that is now tolerated, which on pds4 is a detection the old code made.

The base probe was also redone. The `PYTHONPATH=<base>/src` form used in round 1
was half valid — pytest's own `pythonpath` setting wins for in-process imports —
and both reviewers hit that independently. The probe now copies the head's test
files into a base tree and runs pytest **from there**, which pins itself correctly
because `REPO_ROOT` derives from the test file's location. It reproduces the same
nine failures, so round 1's conclusion stands; the method it stood on did not.

## Gates after the round

`ruff check .` clean; `ruff check --preview --select E111,E112,E113 .` clean;
`E303,E305` clean on the three shared modules, matching base;
`tests/holdings_maintenance/` + `tests/api/` **304 passed**; the suite is now green
with **no** `PYTHONPATH` set, which it was not before — that run previously
reported seven failures belonging to a different tree.
