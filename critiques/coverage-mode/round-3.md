# Coverage mode, round 3 — full diff

Reviewer: a fresh, no-context subagent given the same brief as rounds 1 and 2, both
earlier round records, and an explicit charge to determine independently whether round 2's
four Major findings were genuinely resolved, whether the resolutions introduced anything
new, and whether either earlier round missed something both would have been well placed to
find. Diff: `git diff 02dd774..a17a6f6`. It made no edits.

The reviewer re-derived rather than re-read: 9,715 package statements and 3,542 branches;
4,310 tool-tree statements; **6,851** lines over 77 modules from its own import sweep, the
number round 2's fix put in the script; `tests/core` at 15% and 24%; the 13-id module at
12.54s against the recorded 12.49s, 20 data files, `pdsarchives.py` at 82%; the register at
204; 1279 collected = 1245 + 34; the `coverage/env.py` version gate verbatim; the default
posture; both refusal paths. It drove the real `_coverage_report` over both report shapes
and confirmed the new wording and the `$2`/`$4`/`$NF` parsing are right for each. It ran
four negative controls on the hook by hand, including removing the new `parallel` guard and
watching a child write an unsuffixed `.coverage` — the hazard that guard exists for, shown
to be real rather than argued.

Verdict: **goal not met** — one Major in two parts, eight Minor, five Deferred. Both parts
of the Major are in the evidence document, not in the mechanism.

## Major findings, and their resolutions

**M1(a). The record gave a false reason for a true observation, in a paragraph offered as
a negative control.** It said `crlf.py` and `re_validate.py` barely move because
`test_re_validate.py` "never ran a subprocess". It runs five: `run_module()` at
`test_re_validate.py:74`, called from `:1394`, `:1403` and `:1412`, and two direct
`subprocess.run` calls at `:150` and `:172`. `test_crlf.py` still runs two. The reviewer
measured the three `run_module()` ids under this mode: 4 data files, `re_validate.py` at
27%. This is the shape round 2 escalated as its own M2 — right conclusion, false reasoning,
control that cannot fail. **Fixed:** the record now states the measured reason (86 ids
already drive the module in process to 90%, so 27% from three subprocess ids adds nothing
visible) and drops the claim.

**M1(b). The blind-spot paragraph named one environment builder of two.**
`test_re_validate.py:64` has its own `subprocess_env()`, which puts `src` on `PYTHONPATH`
and not `SUBPROCESS_GUARD_DIR`, so its five children also fall outside the fail-closed
guarantee and would be unmeasured entirely on the declared `coverage>=7.0` floor. The
paragraph whose whole job is to say which children fall outside named roughly half of
them, and round 1's m5 had already expanded that same list once. **Fixed:** the paragraph
is now a table of both builders, all their call sites and all nine children, with the
guarantee stated once for both.

## Minor findings, and their resolutions

**m1.** The zero-children line said the total would then be "the same one `--coverage`
produces". It would not: the run is still line-only where `--coverage` is branch — 60%
against 56% on this PR's own figures, the four points round 2's M1 was about. **Fixed:**
the line now says the total covers the pytest process alone and is not comparable with
`--coverage`'s.

**m2.** Four documents credited `ToolTree.env` with delivering `COVERAGE_PROCESS_START`,
where on the shipped path the script sets it on the pytest process and the child inherits
it; the reviewer demonstrated the point by stubbing the helper out and getting an
indistinguishable run. The helper's real contribution is absolutization for a hand-set
relative variable, which is what its test pins. **Fixed** in the record; the test file
already said it, and `support.py`'s docstring leads with the absolutization.

**m3.** The `has_arcs()` read-back ran a plain `python -c` with `COVERAGE_PROCESS_START` in
its environment, so coverage's `.pth` started measuring it and every subprocess-mode run
left one uncombined data file behind. (`python -m coverage <verb>` does not, which is why
the other three commands were unaffected.) **Fixed:** that command now gets only
`COVERAGE_FILE`, and the comment says why.

**m4.** Entry 4214's older paragraph still told its reader that a standing answer "needs
`COVERAGE_PROCESS_START` plumbed into `ToolTree.env`", thirty lines above the section
saying it is built. **Fixed** with a forward pointer that also says what of that paragraph
remains open — the log-filename assertion no test makes.

**m5.** The arm table said 435 ids where the arm now collects 437, while its sibling table
carried an explicit note. **Fixed** with the same note.

**m6.** The `ROUND3_HEAD` / `ROUND3_RESULT` placeholders. **Fixed** by this round.

**m7.** The hook keyed on `COVERAGE_PROCESS_START` only, while coverage's own `.pth` also
acts on `COVERAGE_PROCESS_CONFIG` — so a run driven that way would get measurement with no
fail-closed guarantee and no `parallel` check. Nothing in the repository uses it. **Fixed:**
one `or`.

**m8.** Four over-long lines. The two in prose that wraps were **fixed**; the one in
`pdsfile_overrides.mdc` was left, because that file's existing lines run to 849 characters
and a 105-character line is its norm, not a leftover.

## Deferred

The same five as rounds 1 and 2, with one addition worth recording: coverage's
`${VAR-default}` substitution defaults only when the variable is *unset*, so an
exported-but-empty `PDSFILE_COVERAGE_BRANCH=` makes every coverage command fail with a
config error. It fails loudly rather than silently, nothing sets it, and guarding it
belongs with PR-37's coverage-posture work.

## What the reviewer confirmed rather than found

All four deliverables land. Round 2's four Major fixes are in place and correct. The
default posture is provable — the non-coverage `pytest_argv` expands byte-identically to
the old command line, the info line is textually unchanged, and a test pins the config.
`pdsfile_main_test.sh` passes no `-n` and sets neither variable, so its posture is
untouched. Three of the four hook tests have teeth, shown by the reviewer's own negative
controls; the fourth is vacuous about the hook's existence and its docstring says so,
because its job is the `None` branch. Nothing behaves differently on 3.11 or 3.13. The
register edit is consistent, follows the register's conventions and leaves the counts at
204. Both earlier round records describe what actually happened.
