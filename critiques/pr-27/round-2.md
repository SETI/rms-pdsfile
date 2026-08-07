# PR-27 adversarial review — round 2

One fresh no-context opus-class reviewer, reviewing at `ec21961`, given the plan's
PR-27 entry, the ground rules, the exact diff, `critiques/pr-27/round-1.md` (with
instructions to treat every resolution in it as a claim to be checked), and read
access to both worktrees and the real holdings.

**Verdict: `goal not met` — "narrowly, and on the evidence rather than on the
code".** Two Major, nine Minor, three Deferred. Every finding was accepted; none
was rebutted.

The reviewer independently re-derived the equivalence of every moved function
three ways (base pds3, base pds4, head), the `REPAIRS` content-unchanged proof
without trusting the record's ranges, the ratchet decomposition per file, the
frozen files, `--help` byte-identity for all four tools, the completeness of the
`re_validate` call list, the id-set delta with `comm` on sorted id lists, and
three of the record's negative controls. It specifically hunted the two traps that
would break the merge — `locate_nonlocal_link`'s holdings sentinel and
`write_linkdict`'s per-flavor log level — and found both correctly carried as
data.

## M1 — §5's enumeration contradicted §7.2's measurement. Fixed.

Three items carried pre-correction counts: change 1 said 226 where the table said
242, change 2 said 16 where the table said 10, change 8 said 67 where the table
said 73. §5's items summed to 578 against a measured 594, and item 2 restated as
fact the exact figure the same document elsewhere called wrong.

Round 1's own M1 fix caused it: adding the 27th scenario moved 16 lines into
change 1, and splitting the blank lines by cause moved 6 into change 8, and the
table was updated while the enumeration was not.

Fixed, and made hard to repeat: the three counts are corrected, and §5 now closes
with the addition — `242 + 10 + (2 + 6) + 0 + 6 + 3 + (118 + 92 + 38 + 2) + 73 +
0 + 0 + 0 + 0 + 2 = 594` — so the two sections cannot drift without the arithmetic
failing.

## M2 — the `wc -l` table was stale by 21 lines, and the staleness had propagated. Already fixed, then completed.

The reviewer measured at `ec21961`; `566378d`, pushed while the review was
running, had already re-taken the table and the figures derived from it in
`pr-27-validation.md` and the plan. What it had **not** reached were the deferred
entries: entry 66 still said `_linkshelf_common.py` (712), entry 114 still said
617/712, and entry 123 still carried 32.9%, 1,329, 56.8%, 24.1% and the ambiguous
"78% low". All four are now regenerated from the same `wc -l`.

The reviewer's diagnosis of the cause is the one worth keeping: the commit that
rewrote 178 lines of the record did not re-take the table its own edits
invalidated.

## Minor findings, all fixed

- **m1** — the record said five `%`-format sites were converted to f-strings; it
  is eight. All eight are now enumerated, split into the four numeric ones (where
  `%d` and `:d` differ on a non-integer, so the operand type was measured) and the
  three `%s` ones (where both forms call `str()`), plus the two sites that were
  **not** converted and why.
- **m2** — round-1's "78% low" replacement had missed deferred entry 123.
- **m3** — `file_log_level` is declared by both index specs and read by neither.
  `ToolSpec`'s flavor-property carve-out now names all three such fields and says
  the index shelf tools read none of them directly.
- **m4** — "none unattributed" was not spot-checkable, because the classifier
  lives outside the repository. §7.2 now carries the **per-record changed-line
  count for all 32 differing records**, summing to 594, each reproducible with one
  `diff | grep -c`, plus the classifier's rules in prose.
- **m5** — change 9 is a control-flow change with nothing pinning it.
  `test_validate_links_propagates_an_exception_raised_inside_it` now pins it, with
  a `sort()` that raises to reach a branch no scenario can. Negative control:
  restoring the `finally: return` fails that test alone.
- **m6** — `run_main` now calls `set_log_dirs()` for the archives pair too.
  Enumerated as a no-op, with why it is kept rather than made conditional.
- **m7** — two parametrize arguments the first `test_shelf_common.py` test never
  read. It now takes only the tool.
- **m8** — three parameters left the index shelf library surface (`repair`'s
  unused `op`, `update`'s unused `selection`, and `logger` becoming keyword-only).
  Enumerated.
- **m9** — the update/repair agreement test compared only the human-readable
  sidecar. It now compares the unpickled shelves as well, and asserts the new file
  is in them, so an equality that held because both sides were empty would not
  pass.

## Deferred

- **d1** — the entry-4 fix left an eager `%` inside a logging call in
  `pds4linkshelf.generate_links`. Base code that the one-line fix edited in place;
  recorded as entry 131, to go with the `UP031` residue in the same two functions.
- **d2** — the third driver's 67% duplication: already deferred entry 130, and the
  reviewer independently agreed with the "two forced, two preservation" split.
- **d3** — deferred entry 122's general shape, correctly left open.

## Nothing rebutted

Both Majors were real and both were in the evidence rather than the code, which is
the failure mode this PR was briefed to watch for. M1 in particular was created by
round 1's own fix: correcting a measurement without re-deriving what depended on
it is the same defect one level up.

## CodeRabbit (PR #125, second pass)

Two findings, both on the records' internal consistency, both fixed in `d81c136`
and answered on their threads.

| # | finding | resolution |
|---|---|---|
| 1 | `pr-27-validation.md:330` — the limit-forwarding site count does not reconcile | **fixed**: it is twelve base sites, six shared, three pds3 droppers, six pds4 with no parameter — counted, with line citations |
| 2 | `pr-27-validation.md:463` — the shared-code measurement differs between records | **fixed**: the superseded 1,329 / 32.9% / short-by-581 figures are gone from `round-1.md` |

Finding 1 was a real miscount: "all four pds4 sites had no `limits`" should have
been six, three in each pds4 tool. Finding 2 is the same defect round 2's M2
named, one level further out — round 2 re-measured and updated the validation
record, the plan and three deferred entries, and left the old figures standing in
the round-1 record. There is now exactly one live measurement of each quantity,
and the only surviving mentions of the old ones are the two sentences that say
explicitly which figures were stale and when.
