# PR-25 adversarial review — round 4 (scoped)

§6.6 caps the loop at four rounds and makes the fourth a **scoped** re-review:
confirm the prior round's findings are resolved, and raise only **new Major**
findings.

**Reviewed:** `git diff ab1fa3b..58e90ec` (3,176 lines).
**Reviewer:** a fresh opus-class subagent, given round 3's findings and the fixes
claimed for each, and told explicitly not to spend the round on new Minors.
**Verdict returned:** `goal met` — **0 new Major**; all six round-3 findings
confirmed resolved.

## Round-3 findings

| # | Reviewer's confirmation |
|---|---|
| m1 | **Resolved.** The addendum reads 36/39/34/35; re-running `compare_toolruns.py` unmodified against the committed captures reproduces exactly `34 of 36`, `35 of 39` |
| m2 | **Resolved.** §13 says 92–99, and the base file ends at 91 while the head adds 92–99 and no more |
| m3 | **Resolved, and the new figures are correct.** Its own `tokenize` diff: 5 absent / 17 new against the trio, 18 absent / 0 new against the pair — exactly what §10 states |
| m4 | **Resolved.** Addendum §5 added and both documents say five. It checked the material half against the code: base `pds4archives.py` adds `warning_handler` then `error_handler` at both the log root and per target, and the head's tuple is consumed in that order at `_common.py:208-209` and `:239-240`. "A boolean would indeed not carry the order" |
| m5 | **Resolved.** Both captures print `No archives for checksum files: …` and `### exit: 1`, byte-identical across trees. "Every branch of `run_main` and `reject_checksum_and_archive_paths` is now reached by a capture" |
| m6 | **Resolved.** The `DISKNAME` regex matches the fixed disk path and `<DISK>` appears throughout the normalized output; §14 names rounds 1–4 |

## The two harness normalizations, audited rather than accepted

This was the round's real work, and it is worth recording in full because these
two normalizations are what every earlier number in §5 rests on.

- **Sorting each run of consecutive `Log file:` lines.** The reviewer re-ran the
  comparator with that step neutered and found it hides **exactly** a two-line
  swap of the `logs/…` and `logroot/…` paths in three stdout captures and six log
  blocks — no content, no counts, no positions. It then tested the stated
  justification directly: under `PYTHONHASHSEED=0`, `list({logs, logroot})[0]` for
  the *actual* strings flips purely as a function of the embedded time tag —
  **216 tags sampled, 114 putting `logs` first and 102 putting `logroot` first**.
  The order is genuinely not a function of the code.
- **Pairing log blocks by `(name, occurrence index)`.** For each of the **21**
  name groups it compared the index-paired identical count against the
  multiset-intersection maximum — the most lenient pairing that exists — and they
  are **equal in all 21** (the 5-block `_archives_<TIMETAG>_validate.log` group:
  4 either way; the 8-block `HSTN0_7176_links_…_validate.log` group: 8). So the
  pairing reports precisely the differences that no pairing could remove.

## Independent re-verification at the head

Full-data suite at head: `ns` 862 passed / 34 skipped (896), `s` 555 / 3 (558),
matching §3; `tests/holdings_maintenance` 115 and `tests/api` 26 at head against
111 and 26 at base — exactly +4 ids. `ruff check` clean with no `_common.py`
entry, the delta measured as 8 `UP031` + 3 `N806` = eleven, none added. The
captures were confirmed to come from the reviewed source: the raw frames name
`…/work/src/…/_common.py", line 253, in run_main` and `pds4archives.py", line
275, in main`, which are the committed lines. No consumer references a moved
name; `re_validate.py:102` still resolves; `pdsfile_overrides.mdc` does not
contain the reverted self-authorizing edit.

## New Major findings

**None.** The loop terminates here.

## The three Minors it declined to raise, fixed anyway

The reviewer named three record-prose defects in one closing sentence, under the
round's own instruction not to raise Minors. All three are the recurring
stale-evidence class, so all three were fixed:

1. §5's table repeated the base tree's normalized line count in **both** columns.
   The comparator only ever printed one; it now prints both, and the table reads
   **4,005 / 4,009**. The branch's four extra lines are the disclosed traceback
   frames themselves — two lines in each of the two captures that carry an
   outermost traceback — which §5 now says.
2. §12 pointed at the addendum's "§5" for the traceback consequence, which m4's
   new section pushed to §6. Corrected.
3. `pdsfile_overrides.mdc`'s `UP031` row breaks 131 down ending "6 in the frozen
   `re_validate.py`", where ruff reports **7** sites there. Measured: exactly one
   of the seven, `logger.info('%d re-validation tests performed' % …)`, is a
   logging call and is counted in that category, so the row's arithmetic is right
   and only its wording was ambiguous. The row now says so.

## Loop termination

Round 1: `goal not met` — 2 Major, 6 Minor. Rounds 2 and 3: `goal met`, 0 Major,
8 and 6 Minor, every one in the evidence prose and every one accepted. Round 4:
`goal met`, 0 new Major, all prior findings confirmed resolved. §6.6's
termination condition — a fresh reviewer returning zero Major and no new
un-rebutted Minor — is met.
