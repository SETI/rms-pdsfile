# PR-31 round 2 — the gate, the CI wiring, and whether the two correspond

Reviewer: a fresh, no-context subagent, scoped to `scripts/run-all-checks.sh`,
`scripts/gen_ruff_ratchet.py`, `.github/workflows/run-tests.yml` and the correspondence
`environment.mdc` sections 2 and 3 require. It was told to answer the CI question from
the job log rather than from the script, and to copy the tree for any experiment. Tree at
`8840ebb`, base `8f8d825`; `git status --porcelain` empty at both ends of the round.

**Counts.** 5 defects, 7 observations, 8 suspicions tested and disproved.

---

## The CI question, answered from the log

Job `93209650343`, "Lint and holdings-free tests (3.13)", `ubuntu-latest`, conclusion
`success`, all four steps `success`. The reviewer quoted the Sphinx section verbatim and
then looked for the vacuity signature: `grep -c "no targets are out of date"` is **0** in
both lint jobs, and both builds in both jobs report `7 source files that are out of date`
and `[new config] 7 added`. No step was skipped and neither log holds an `##[error]`.

The 3.10 leg runs the same gate on **Sphinx 8.1.3** and `myst-parser 4.0.1`; the 3.13 leg
on 9.1.0 and 5.1.0. Both pass.

## The defects, and what was done about each

**1. Parallel mode could abort the gate before either build ran. FIXED by deletion.**
`pages=$(find docs/api ... | wc -l)` and `modules=$(grep -rh ... | wc -l)` both end in
`wc -l`, which always exits 0 -- so it was `set -o pipefail` that propagated `find`'s or
`grep`'s failure into the assignment and `set -e` that killed the shell. Sequential mode
survived it (bash suspends errexit inside a function called as `if ! f`), parallel mode --
the default -- did not. Measured by the reviewer with `docs/api` moved aside: sequential
ran both builds and named both failures; parallel ran **neither build**, wrote no status
file, and degraded to the unnamed summary. Both assignments are gone: the gate now takes
its module count from the build's own output. Re-measured in parallel mode with `docs/api`
missing: both builds run, both fail with 79 problem lines, and both are named.

**2. The pass line's "6 files" was wrong. FIXED by deletion.** The 78 entries live in
five files; `pages` counted every `.rst` under `docs/api`, including the `toctree` page
that carries no directives.

**3. Neither number in the pass line was derived from the build. FIXED.** Both counts came
from `find`/`grep` over the source tree before either build ran, and "0 warnings" was a
constant. The reviewer demonstrated the consequence with `MAKEFLAGS=-n`, which makes
`make` print its recipe and do nothing: the gate reported `✓ Sphinx build passed: 0
warnings under -W and under -n -W, over 78 automodule entries in 6 files under docs/api`
and exited 0 over a `docs/_build` that did not exist. **This is the finding this PR is
most in debt to**, because the whole point of the PR is a gate that cannot pass
vacuously. The gate now accepts a build only if it exited 0, wrote its HTML, and printed
the coverage line `conf.py` emits, and the pass line quotes the measured problem counts
and that line. Re-measured: `MAKEFLAGS=-n` now gives `✗ Sphinx warnings-as-errors build
exited 0 but reported no API-reference coverage`, exit 1.

**4. The third corner of the script/CI/AI triangle was not brought into step. FIXED.**
`environment.mdc` requires the script, CI, and the AI to run the set the script enables.
`.cursor/skills/run-all-checks/SKILL.md` still described a one-build docs gate in three
places. While `ENABLE_SPHINX` was false that drift was inert; flipping it to true made it
live, and an agent following the skill would have run `-W` only -- precisely the build
that misses unresolved cross-references. All three places now describe both builds and
the separate `BUILDDIR`. The reviewer also found the skill's `-c` description ("Only
ruff, mypy, pytest") stale, which predates this PR; it is corrected in the same edit.
`CONTRIBUTING.md` (bare invocation) and the workflow (`--sequential`) both take the
default-all branch and so both get the gate: that half already corresponded.

**5. A `make clean` failure was reported as a warnings-build failure, and the header
comment omitted `make clean`. FIXED.** `make clean` now runs as its own step with its own
message and its own status-file entry, and the header comment describes all three
commands.

## The observations

**6. The job log carries no evidence of the flags**, because `docs/Makefile` prefixes its
recipe with `@`. The only in-log evidence is the script's own strings. Left as it is: the
`@` is the stock Sphinx Makefile's, and the script now prints the measured coverage line,
which cannot be produced without the build having run.

**7. The two matrix legs gate two different Sphinx majors, unpinned** (8.1.3 and 9.1.0
against `sphinx>=7`). Breadth is a strength; the cost is that a Sphinx release adding one
warning turns the gate red on an unrelated PR.

**8. `make` is an undeclared prerequisite.** The gate fails safely and names both builds
when it is absent (`exit 127`), but nothing in `pyproject.toml` or `CONTRIBUTING.md`
mentions it.

**9. Network dependency, twice per run**, owned and documented in `conf.py`, bounded by
`intersphinx_timeout = 30`.

**10. The job name, "Lint and holdings-free tests", no longer describes the job**, which
now also runs two documentation builds. It is the branch-protection check name, so
renaming it is the owner's call.

**11. `-c -s` is the habitual local command in six validation records and does not run
the docs gate.** That is correct behavior -- Sphinx is in the `-d` scope -- but the habit
now skips a gate CI runs.

**12. Gate cost:** four Sphinx builds per PR event, about 20 s of the 3.13 job's 50 s.

## The eight suspicions that were tested and disproved

The nitpicky build does not go stale on a repeat run (`make clean` empties `_build`
including `_build/nitpicky`, and a pass requires the clean to have happened); the
separate-`BUILDDIR` comment is not post-hoc rationalization but a reproduced trap; both
statuses are genuinely read, and the second build still runs after the first fails; the
pass line cannot print while something failed; the un-`.PHONY` `html` target does not
no-op even with a file named `docs/html` present; adding `docs` to `RUFF_TARGETS` does not
race with `make clean` (the HTML holds no `.py` files and `docs/_build/` is gitignored);
a missing venv is handled in both modes; and no workflow change was needed -- the log
shows the `docs` extra arriving from the local tree through `rms-pdsfile[docs]`
(`Obtaining file:///home/runner/work/rms-pdsfile/rms-pdsfile`), not from PyPI.

## What the reviewer could not verify

That `-W` and `-n` were actually passed in CI, since the `@`-prefixed recipe hides the
command line; the four self-hosted data jobs, still in progress at review time (they do
not run this gate); whether ReadTheDocs builds this tree; whether `docs/api` can reach the
zero-`automodule` state at all; whether the owner intends `-c` to stay Sphinx-free; and
whether `.cursor/skills/` is editable by this PR or vendored boilerplate.
