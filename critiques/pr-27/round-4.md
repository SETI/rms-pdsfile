# PR-27 adversarial review — round 4 (scoped, and the §6.6 cap)

One fresh no-context opus-class reviewer, briefed for the fourth-round rule:
confirm the prior rounds' findings are resolved, raise only **new Major**
findings. **Verdict: `goal not met` — "narrowly, and in the evidence rather than
the code, for the fourth round running."** Three Major, seven Deferred. Every
finding was accepted; none was rebutted.

**This is the hard cap.** §6.6 says a fourth round that still finds issues is a
mis-scope signal and all four round records go to the owner. They do. What the
owner is being asked to weigh is set out at the end of this file.

## What reproduced

The reviewer re-derived, with its own implementations of each stated method: the
whole `wc -l` table and both totals; the four-tool total; the `pdsdependency`
exception; the shared-code figure, its rate, the projection gap and the three
per-pair percentages; the split addition; every ratchet number including the
per-file decomposition; the `REPAIRS` md5 from both `sed` ranges; **both driver
duplication measurements**; §5's addition, §7.2's per-cause table and its 32-row
per-record table, all three at 594; both suites re-run at base and head, id for id;
`run-all-checks -c -s`; the frozen files; the 158 / 96 / 17 census; every §4
measurement; and deferred entries 66, 113, 114, 123 and 130. All exact.

It also diffed every function now in the two family modules against **both** base
originals by AST and found every difference accounted for, checked the
`handler_factories` sets per flavor as a likely merge trap and found them right,
and reproduced **all five** of the record's negative controls.

## M1 — §3's similarity figure does not reproduce. Fixed.

§3 said "every link shelf function except `generate_links` scored 0.95 or better".
Six of the thirteen do not, and five of them sit *below* `generate_links`:

```
1.000 locate_link_with_path   1.000 LinkInfo        1.000 read_links
0.998 load_links              0.998 write_linkdict  0.979 locate_nonlocal_link
0.947 validate_links          0.905 update          0.894 repair
0.877 validate                0.825 generate_links  0.760 reinitialize
0.666 initialize
```

The full distribution is now in §3 in place of the summary. The seam is where it
was drawn, but the ratio is not what shows it: the five task functions score low
because pds4's are shorter — they thread no `limits` — which is a difference in how
much they say, not in what they do. §3 now says that, and points at the
line-by-line diff against both originals as what actually settled it.

## M2 — the stale figure came back, in the sentence asserting it could not. Fixed.

`round-1.md` claimed "the current figures everywhere are 1,348, 33.4%, short by
600; no earlier figure survives in any record". The tree says **1,349** and
**601** — `dbe4160` took `_indexshelf_common.py` from 619 to 620 lines, `15e9347`
re-took the figure in the validation record, the plan and four deferred entries,
and missed the round record. That is CodeRabbit's second-pass finding recurring
inside its own resolution.

Fixed by removing the copy rather than correcting it. The live measurement is in
`pr-27-validation.md` §6 and nowhere else; the plan and entry 123 repeat it and are
checked against the tree mechanically. A round record that carries its own copy of
a number the tree can move is a trap — which is the lesson three rounds took to
learn, and this is the fourth telling.

## M3 — §10 mis-stated which round changed source. Fixed.

§10 said round 3 changed no source. `dbe4160` — a round-3 fix — changed
`_common.py` and `_indexshelf_common.py`, and is the PR's last change under
`src/pdsfile/`. §6.6's staleness test is "generated before the PR's last change
under `src/pdsfile/`", so the section that exists to date the gate records was
reasoning from a false premise about the very commit that dates them.

Corrected, and it now says what the change was — comments and a docstring, so no
transcript line could move by it — and that the transcript was re-taken after it
anyway, which is what makes the claim checkable rather than argued.

## Deferred findings

Two were fixed rather than deferred, because both are things this PR argues for:

- **The backup skip's exit code had no test**, and it is the decisive justification
  for the third driver existing. `test_pds3_indexshelf.test_a_backup_copy_of_a_table_is_skipped_and_reported`
  now pins it: the skip is reported at ERROR, the run exits 1, and the backup gets
  no shelf while its siblings do. Negative control: downgrading the call to
  `logger.warning` fails it.
- **`link_targets`'s filtering had no test**, and it is the one target-expansion
  behaviour this PR deliberately changed, on 17 real unit sets.
  `test_pds3_linkshelf.test_a_unit_set_target_shelves_its_units_and_skips_a_file_beside_them`
  pins it. Negative control: returning the children unfiltered fails it.

The rest are recorded:

- The stale test name in §7.1 and `round-2.md` (renamed by round 3's own fix).
  Fixed.
- Two more moved behaviours pinned only by the out-of-repo transcript —
  `index_repair`'s re-dating branch and entry 127's log-directory computation.
  Deferred entry 132, with the mutation probe that shows it.
- Deferred entry 131 under-stated its population: four more eager-`%` logging calls
  sit in the two new shared modules, and ruff flags none of them, so a sweep
  following the ratchet alone would miss them. Entry 131 extended.
- `index_reinitialize` takes pds4's comment over pds3's mangled one — the one
  comment in the migration where the merge had to choose. Deferred entry 133.

## What the owner is being asked

Four rounds, thirty findings, and **not one Major in the code**. Every round
verified the migration independently — moved-function equivalence against both
originals, the freeze, the ratchet, both data suites id for id, the negative
controls — and every round's Majors were in the evidence: a measurement taken over
the wrong population, an enumeration that had drifted from its own table, a
duplication figure invalidated by a previous round's fix, and a summary statistic
that never held.

The pattern is one thing, not four: **a record edit invalidating a number in the
same document, and the invalidation not being noticed because nothing checked it.**
That is now checked mechanically — every reproducible number in the validation
record, the plan's PR-27 entry and deferred entries 66, 114, 123 and 130 is
verified against the tree — and the ordering rule is written down in §10. What is
*not* fixed is that the check is a scratch script rather than something in the
repository, which is the shape of round 2's m4 and is the honest reason a fifth
round might still find a number.

So the question for the owner is whether four rounds of evidence-only Majors on a
refactor whose code three independent reviewers found sound is a mis-scope of this
PR, or a missing tool. This executor's reading is the second: the PR is one
migration and the record is one document, and what kept failing was that the
document had no gate while the code had five.
