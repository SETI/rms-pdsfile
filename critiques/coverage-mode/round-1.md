# Coverage mode, round 1 — full diff

Reviewer: a fresh, no-context subagent given the PR's goal and its four deliverables, the
constraints the executor was briefed with, plan §2 / §6.1 / §6.2 / §6.6 including the
progressive-compliance schedule, the `.cursor/rules` files, the exact diff
`git diff 02dd774..8d66ec3`, read access to the repository and to the holdings, and the
executor's evidence file to treat as a claim rather than a source. Its three central
mandates: prove the coverage mode measures less than it claims, prove the subprocess hook
does not fire, prove a recorded number was asserted rather than taken. It made no edits.

The reviewer independently reproduced, among others: the `-n 1` / `-n 0` coverage
difference on `tests/core` (15% and 24%, to the digit); the register counts (204 =
8/0/15/131/50); the new test module (9 passed); the 13-id module timings (11.00s against
12.89s, ratio holding within noise); the 20 data files that module writes; the default
posture from `coverage debug config` with no variables set (`branch: True`,
`parallel: False`, `source: pdsfile`); both refusal paths exiting 1; `bash -n`, ruff, LF
endings and the absence of any absolute holdings path outside `critiques/`; and the
record's arithmetic throughout. It then combined the 20 data files itself and confirmed
`pdsarchives.py` at 82% from that one module — the mechanism works end to end.

Verdict: **goal met** — zero Major, twelve Minor, five Deferred.

## Minor findings, and their resolutions

**m1. Two permanent documents attributed the measurement solely to this PR's hook.**
The reviewer proved that on the installed coverage a child with only `src/` on
`PYTHONPATH` — no `sitecustomize` reachable at all — still writes a data file, because
`site.main()` runs `.pth` files before `execsitecustomize()`, so `a1_coverage.pth` always
wins. The validation record said so; `docs/dev_guide/dev_guide_ci.rst` and
`tests/holdings_maintenance/__init__.py` did not, and they are what a developer debugging
a short report reads. **Fixed:** both now name the `.pth`, say it runs first from 7.10,
and say what the hook is for — failing closed, and working below that version. The
script's own header gained the same clause.

**m2. `env.update(subprocess_coverage_env())` was a no-op under both of its tests.**
`ToolTree.env` starts from a copy of `os.environ`, which already carries the variables,
so `test_a_tool_tree_environment_carries_them` and its negative twin passed with the
production line deleted — the reviewer demonstrated this by stubbing the helper to return
`{}`. The property only the helper supplies is the **absolute** form. **Fixed:** the test
is now `test_a_tool_tree_environment_absolutizes_them`, sets both variables *relative*
from a `chdir`ed working directory, and asserts the absolute values out; the negative
twin is renamed and its docstring says which failure it guards. Negative control run
after the fix: deleting `env.update(subprocess_coverage_env())` gives
`1 failed, 8 passed`, and restoring it gives `9 passed`.

**m3. `_coverage_kind` asserted the core where the rest of the function reads values
back.** It printed `core sysmon` on `hasattr(sys, 'monitoring')` alone, so a broken
`PDSFILE_COVERAGE_BRANCH` substitution would have printed `branch coverage, core sysmon`
— a combination that cannot exist on 3.12 — while the run silently paid 7.5x. **Fixed:**
the clause now requires both the measured `branch: False` and `sys.monitoring`, and each
of the two ways it can fail prints what will actually happen instead.

**m4. `COVERAGE_CORE` is a coverage setting the script names, contradicting its own
header** ("every measurement setting from `[tool.coverage.*]`"). **Fixed** by narrowing
the sentence rather than by routing a third variable through `pyproject.toml`: the header
now says the script names no source, omit or exclude, reaches `branch` and `parallel`
through the substituted variables, and names `COVERAGE_CORE` outright because it selects
the tracer rather than the measurement and coverage documents it as an environment
variable.

**m5. The record's blind-spot list was incomplete.** `no_holdings_env()` has three call
sites, not one, and one of them runs `show_opus_products` — a subprocess-driven program
this mode exists to measure. **Fixed:** the record names all four affected tests with
their call sites, and says the fail-closed guarantee does not reach them.

**m6. The new test module miscounted the programs** ("twelve of the thirteen"). The
repository's established count is fourteen (`user_guide_maintenance_tools.rst:4`).
**Fixed:** "twelve of the fourteen programs". Every other file in the diff was already
right.

**m7. `Coverage report passed` claimed a gate that does not exist** — there is no
`fail_under`. **Fixed:** the line is now `Coverage measured: …`, with a comment saying
why; the failed-check name `Code - Coverage report` is unchanged.

**m8. "1 pytest process + N subprocesses" counted children that are not tools** — the
freeze, mixin-isolation, docstring and guard-probe subprocesses inherit
`COVERAGE_PROCESS_START` too, which the record's own 320-against-308 pair shows.
**Fixed:** "measured children" in both the count line and the verdict, with the comment
naming the other children.

**m9. `dev_guide_ci.rst` quoted 60% → 81%, a pair `--coverage` never prints.** **Fixed:**
the guide now reads 56% → 81% and names the 60% line-only control as what separates the 4
denominator points from the 21 subprocess points.

**m10. History narration in a `pyproject.toml` comment** ("exactly as before"), against
`python.mdc`. **Fixed:** the sentence now says what the fallback is *for* — the data
gate's append-and-report, which needs one unsuffixed file.

**m11. An ambiguous sentence in entry 4214** — "the uninstrumented row already starts all
nineteen of them (the run writes 20 data files…)" switches referent mid-sentence.
**Fixed:** the measured rows write 20 files and the uninstrumented row runs the same ids
and writes none.

**m12. `critiques/coverage-mode-validation.md` still held the literal placeholder
`ADVERSARIAL_LOOP`.** **Fixed:** this file exists and the record's section is written.

## Deferred, and what was done with them

The reviewer's five Deferred items were all judged correct and left alone, except the
first, which it explicitly recommended keeping:

* the PyMarkdown row flip (`not yet` → `yes`) is scope creep but a true correction in a
  table this PR edits, and `environment.mdc` makes the script authoritative — **kept**;
* `pytest-cov` is a dev dependency nothing invokes — a dependency change, not this PR's;
* no `fail_under` and no `show_missing`, which `python_testing.mdc` §9 asks for — PR-37's;
* the SIGINT/SIGTERM traps do not erase coverage data, so an interrupted
  `--coverage-subprocess` leaves suffixed files behind. The reviewer confirmed there is no
  contamination path: the next subprocess-mode erase removes them, and plain `--coverage`
  and the data gate both read only the unsuffixed `.coverage`;
* an externally exported `PDSFILE_COVERAGE_PARALLEL` would change the data gate's posture.
  It fails loudly rather than silently, nothing in CI sets it, and guarding it is PR-37's
  coverage-posture work.
