# Coverage mode, round 4 — scoped

Reviewer: a fresh, no-context subagent, given the §6.6 scoped-fourth-round instruction —
confirm the prior rounds' findings are resolved and raise only **new Major** findings, with
anything merely Minor going to Deferred. It was told which pattern the first three rounds
kept finding (a true claim resting on a reason that is not the real one, or a control that
cannot fail) and asked specifically whether it had been eliminated or had merely moved.
Diff: `git diff 02dd774..75ee804`. It made no edits.

It reproduced at HEAD: the 13-id module at 12.47s against the recorded 12.49s, 20 data
files, `pdsarchives.py` at 82%, `has_arcs: False`, and **no stray data file** after the
report — the round-3 m3 fix, confirmed by measurement rather than by reading. The new test
module at 11 passed, with none of its children writing into the project root. The register
at 8/0/15/131/50 = 204. `bash -n`, ruff, LF, no absolute holdings path outside `critiques/`,
`.gitignore` coverage. All three coverage strings the record quotes verbatim, present in
the installed 7.13.3. CI untouched.

It walked every round-2 and round-3 finding and found all of them resolved in substance —
including that round 3's new `or` for `COVERAGE_PROCESS_CONFIG` introduces no false-kill
path, and that the round-2 verdict-line fix parses both report shapes correctly, which it
checked by driving the real code over a live line-only `TOTAL`.

Verdict: **goal not met** — two new Major, both in this evidence document, both the same
pattern, neither in the mechanism.

## Major findings, and their resolutions

**M1. The guard section still quoted the line round 3's m1 had corrected.** Round 3's fix
went into the script and not into the record, so the record simultaneously quoted a string
the program cannot emit and re-asserted the falsehood the fix removed — that a zero-child
total is "the same one `--coverage` produces". It is not: that run is still line-only where
`--coverage` is branch, 60% against 56% on this PR's own figures. This is round 2's M4 in
kind, one round later, from the same cause: a rename applied in one place of two.
**Fixed:** the record carries the live text and says why the line says what it says. The
reviewer also checked the record's five other quoted `print_*` strings against the script
and found them exact; the script's line, at 172 characters the longest in the file, is now
two.

**M2. The paragraph that fixed round 3's M1(b) rested on a new false universal.**
"`ToolTree.env` … is the only one that puts `SUBPROCESS_GUARD_DIR` on `PYTHONPATH`" is
false three times over: `test_readonly_roots.py:73` and `:141` do, and so does this PR's own
`test_subprocess_coverage.py:62`. The table beneath it was verified correct line by line,
so the blind spot was not understated — but the sentence a reader would use to reason about
any *new* subprocess site pointed the wrong way, implying the guard-probe children are
outside the fail-closed guarantee when they are inside it. **Fixed:** the claim is scoped to
tool children, the three probe-child sites are named as deliberately inside the guarantee,
and the enumeration is retitled "all nine tool children".

Two of the reviewer's Deferred items were the same species and were fixed with them: the
reconciliation section still said the hook keys on `COVERAGE_PROCESS_START` alone, and the
baseline paragraph's file list named eight of the fifteen changed files while the claim it
supported — nothing under `src/` — was true of all of them.

## The cap

§6.6 sets a hard cap of four rounds and says that a fourth round which still finds
something is a mis-scope signal, to be brought to the owner with all the round records
rather than answered with a fifth round. **That is what has happened, and no fifth round was
run.** What the owner is being asked to weigh:

* Both round-4 Majors are in `critiques/coverage-mode-validation.md` and neither touches the
  delivered mechanism. The reviewer states this explicitly and confirmed every earlier
  finding resolved.
* But they are the *same defect class* the loop has found in all four rounds — a true claim
  supported by a reason that is not the real one — which is exactly what a mis-scope signal
  is supposed to surface. Three of the four rounds found it in a paragraph that a previous
  round had just rewritten.
* The reading that fits the evidence: the mechanism converged after round 2, and what has
  not converged is this document's habit of explaining a measured result with an unmeasured
  reason. Each instance was real and each was worth fixing.
