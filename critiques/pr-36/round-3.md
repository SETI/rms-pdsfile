# PR-36 (reports half) round 3 — full diff

Reviewer: a fresh, no-context subagent with the same brief shape as the prior
rounds — the PR-36 plan entry with the reports-only scope, §2, §6.1-§6.2, §6.6
with the compliance schedule, the three SKILL.md files, the exact diff
`git diff 6525951..fb2d68d` (six files under `critiques/`, 2,514 insertions),
repo and register read access, and the recorded gate and coverage evidence —
directed at corners the earlier rounds may not have reached, and at
confirming every fix the two earlier round records claim is actually present.
It made no edits.

The reviewer independently reproduced: the scope and base; the full gate log
end to end; the suite and coverage evidence including the 34-skip
decomposition and every per-module percentage quoted anywhere in the reports;
its own AST sweeps for the encoding sites and docstring measurements; both
tool-pair diffs exactly; every TS defect site including both import-count
forms the report's grep cannot see; all the DOC drift sites; the round
records' own insertion counts; all 21 register entries behind the overlap
rows, the negative searches behind the "new" claims, and both previously
deferred staleness items (1000, 6404); and the presence of all nine
previously recorded fixes. The triage arithmetic recomputed by hand.

Verdict: **goal met** — zero Major, five Minor, two Deferred. All five Minors
were fixed; per §6.6 the fourth round is the scoped confirmation.

## Minor findings, and their resolutions

**m1. The user-guide chapter count was 18; the toctree has 19** — the
enumeration omitted `user_guide_installation`, a chapter the same section
discusses at length. **Fixed:** 19, with installation in the enumeration.

**m2. TS-11's COISS duplicate census was still incomplete**: a full duplicate
sweep over all 187 rows found a second pair, `N1454725799_1.IMG` at
`:106-107`, that neither the report, the triage row, nor fix-prompt step 6
mentioned — as written, step 6 would have left a duplicate in place. The
reviewer's sweep of `test_go_0xxx.py`'s table found exactly the two recorded
pairs, no more. **Fixed:** report, triage row and prompt step 6 now carry
both groups (and the dead function-local `import pdsfile.pds4file` at `:77`
the reviewer's Deferred bucket spotted in the same function). The executor
also aligned the TS-18 print-census wording in the report body and prompt
step 9 with the triage's corrected count of 12 live calls.

**m3. TS-10's line-range characterization overstated one range**:
"845-933 largely dark" is ~10 missed statements in a mostly covered span,
and two quoted ranges compressed covered lines. The compressed spans
reappeared in fix-prompt step 10 as targets. **Fixed:** TS-10 and step 10 now
quote the exact missing ranges from the evidence file.

**m4. The three documents weighted the filterwarnings finding three ways**
(test summary high-priority, CA-14 low, triage Medium) with no
reconciliation. **Fixed:** the triage's TS-17 row now names the disagreement
and states Medium as the reconciled weight.

**m5. The register cross-reference table was incomplete against its own
tally**: CA-02 is tallied as restating the register but had no table row
(CA-11's 1503 relation likewise). **Fixed:** both rows added.

## Deferred (recorded, no register edits in this PR)

- The plan's §2 enabled-gate list omits the stubtest gate PR #154 enabled —
  the DOC-12 drift class, in `plans/`, which no skill's scope covers. Added
  to the triage's register-grooming list.
- `test_coiss_xxxx.py:77` carries a dead function-local
  `import pdsfile.pds4file`. Folded into TS-11's census and fix-prompt step 6
  rather than left deferred, since the same fix pass touches those lines.

## Gates after the round's fixes

The fixes touch only record files under `critiques/` — nothing under `src/`,
`tests/`, `docs/` or configuration — so per §6.6 step 5 the full-data record
carries forward: the gate log (`run-all-checks.sh` green in full, ns 1234/34)
and the session's s-mode runs (555/3, 150/31) remain the evidence of record.
