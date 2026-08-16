# PR-33 round 2 — full diff, deepest on chapters 1, 4, 4b, 5, 6, 7

Reviewer: a fresh, no-context subagent (no knowledge of round 1 beyond what the diff
itself carries), given the same plan sections and mandate as round 1, the exact diff
`git diff 96de70a..6d6bc8e`, and read access to the repository and holdings. It made
no edits.

It reproduced the cheap gates independently (both Sphinx builds exit 0 with 0
problem lines and 78 of 78; the five diagrams re-extracted and rendered with mmdc;
`tests/docs`/`tests/api` 30 passed; ruff clean; the deferred-351 greps 0 and 0; the
CDN measurement 71 of 107 with `mermaid@11.12.1`; record checkers 8 and 27 stale
unmoved; frozen files byte-identical; register arithmetic consistent), and it
verified the chapters this round was deepest on claim by claim: the layout tree
entry by entry, the extending-A skeleton against `RES_xxxx.py` statement for
statement and the test skeleton against the real helpers' signatures, the
extending-B spec block verbatim and the `REPAIRS` anatomy (141 entries, exactly 2
`re.I`, first-answer-wins, the three replacement shapes, the COCIRS example and its
`[56]` siblings), the resolver case by case, the golden mechanisms including the
tool-test failure message, and the CI chapter against all three workflow files and
both scripts.

Verdict: **goal not met** — 2 Major, 1 Minor, 0 new Deferred.

## Major findings, and their resolutions

Both were re-verified against the source before the fix.

**M1. The round-1 correction to the pair-spec comparison miscounted again: "nine
fields" includes `logname`, which does not differ.** `pdsarchives.py:59` and
`pds4archives.py:69` both set `LOGNAME = 'pds.validation.archives'` — each tool pair
shares its family's logger name. The differing set is eight: `progname`,
`pdsfile_cls` and `unit`; the three flavor fields; `log_path_method`; and the
handler tuple. **Fixed**: the passage now counts eight, names the three identity
fields explicitly, and states that the logger name is shared. This is the
correction-pass ratio holding again — round 1's fix to its own M1 introduced the
false count round 2 caught.

**M2. The scanner-behavior clause stated the wrong trigger for basename
truncation.** The guide said a directory-prefixed link is cut back to its basename
when the prefix "resolves nowhere"; in fact `pdslinkshelf.py:283-292` calls
`LinkInfo.remove_path()` whenever a matched repair does not answer the as-written
text and the text carries a slash — whether or not the prefixed path exists — and
the truncation is in place and stands even when nothing answers the basename form,
exactly as the `linkshelf_repairs` module docstring states. As written, the guide
told a repair author that a valid directory-prefixed link is safe in a matched
file. **Fixed**: the clause now states the real trigger, the in-place persistence,
and the no-match case.

## Minor findings, and their resolutions

**m1. The validation record's register parenthetical said 210 open** — stale after
round 1 added observation 4316; the register counts 211 and its arithmetic is
internally consistent. **Fixed**: the parenthetical now says 211 and attributes the
addition.

## What the reviewer could not verify

The full-data suite numbers and their base identity (evidence checked, runs not
repeated); the runner-environment and Viewmaster-deployment claims; the
exhaustiveness of the mixin docstrings' attribute enumerations; the record's
drafting-history claims.

## Gates after the fixes

The fixes touch one docs page and two record files. `sphinx-build -n -W` over the
corrected tree exits 0 with 0 problem lines and 78 of 78 modules; `tests/docs`
passes; the full-data record carries forward under §6.6 step 5 (no `src/` change at
any point in this PR).
