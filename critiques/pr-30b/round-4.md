# PR-30b round 4 — the archive, link shelf and index shelf pairs, re-read

Reviewer: a fresh subagent with no context from this session or from any other round.
Tree frozen at `748eae4`; nothing under `src/` moved while it ran. It was given the
correction range `5acbf85..748eae4`, the seventeen claims those corrections make, and the
instruction to treat every one as unproven and to attribute each finding with `git blame`.

**All eight of `linkshelf_repairs`'s counted claims were re-measured and all eight held
again**, independently of round 2: 141 entries, 2 with `re.I`, 77 dictionary translators
and 64 nested regular-expression ones, 267 dictionary entries of which 24 map to the empty
string, 90 nested regex entries, and a comprehension over `range(0, 50)` with three
entries written out beside it. So did that the two index shelf modules are the two shortest
of the ten, that `holdings_sentinel` has exactly two readers, that nothing anywhere reads
an archive task's return value, and that `TranslatorByRegex.all()` returns matches in table
order, which is what makes "the one written earlier in this table wins" true.

## What it disproved: 6 claims, 5 of them in the corrections

**In the corrections:**

1. **"the label named it in a target position and the label's own name matches"**, the
   first of the two PDS3 grounds. The first-pass branch never reads `info.is_target`; that
   flag is consulted two lines below, in the *candidate* branch. Demonstrated with a
   `FOO.LBL` whose only mention of `FOO.IMG` is inside a prose `NOTE`, matched by the
   general pattern with `is_target=False`: the file is credited anyway. Only the second
   ground requires a target position.
2. **"a label that named the file in a ``<file_name>`` element"**, both of the PDS4 tool's
   first two grounds. Neither tests which pattern matched. Ground two compares
   `link_text_of(info) == basename` over every link the label yielded, general-pattern
   matches included. Demonstrated twice, with an `abc.xml` whose only mention of `foo.dat`
   is inside a `<comment>`: the log says "Label identified (by file_name tag)" and there is
   no `<file_name>` element in the file.
3. **"Those two carry ``re.I`` because they have to match a basename written in either
   case."** The count of two is right and the reason was invented. Measured against the
   published holdings -- all six `COUVIS_8xxx*` trees, 5,912 files walked -- each pattern
   matches exactly the same files with the flag and without it, because the only case that
   exists is the one the pattern already spells. The sentence this replaced was also wrong,
   in a different way: it called both entries lower-case and one is upper.
4. **"the per-link loop inside it therefore never runs."** The per-link loop is the outer
   one and it runs once per link the file yielded; what never runs is the loop over the
   matched repair entries inside it. The conclusion, that no link is looked up, is right.
5. **"the module docstring of the PDS3 tool lists the specification fields the two do not
   share."** Ten fields differ and that docstring names four.

**In the original prose:**

6. **"every other test in this function upper-cases first"**, in `pds4linkshelf`. Three
   tests in the same function do not: the ground-two credit itself compares
   `linktext == basename` exactly, and the collection inventory is both detected and
   matched case-sensitively. Demonstrated: a label naming `FOO.DAT` beside a real
   `foo.dat` is not credited by that path, and renaming a `collection_data.csv` to upper
   case makes the inventory disappear from the run.

## What it classed as misleading: 5, all in the corrections

* `pds4archives`'s "``validate()`` and ``repair()`` walk the whole directory tree first and
  only then find there is nothing to compare it with". True of `validate()` and reversed
  for `repair()`, which looks its archives up before it walks. The consequence holds for
  both; the sequencing was asserted for both from reading one.
* `pdslinkshelf`'s "a ``.LBL`` whose basename matches a file it never mentions is reported
  as a label that 'does not point to file'". Only where a label is required: the
  `EXTS_WO_LABELS` test sits above the phantom-label report, so a `.TXT` in that position
  produces neither error. Verified both ways.
* both link shelf modules' "The three other fields that differ by flavor". Nine differ. The
  count was raised from three to four by the correction without being measured.
* `pds4indexshelf`'s "of the four other PDS4 tools ... and the fifth does not read it
  either". A set of four has no fifth. The substance was right.
* `pds4linkshelf`'s "Before reporting that a file has no label". The collection-inventory
  gate suppresses the *ambiguous*-label error too. The function docstring said so and the
  module docstring narrowed it.

## What it could not verify: 5

Four are intent or history and are now written as description rather than as claim: why
the repair table sits apart from the tool, when a maintainer adds an entry, whether the
PDS4 asymmetry is deliberate, and whether a defect belongs to the rules or to the function.
The fifth is whether `re.I` was needed against some earlier published state of
`COUVIS_8xxx`, which no measurement of the tree as it stands can settle.

## Code defects, not documentation defects: 5

* **A freshly written PDS4 archive fails this tool's own `--validate`, for every installed
  rule table but one.** Round 2 measured three shapes; this round enumerated all seven
  installed tables and found **one** that round-trips. Reproduced end to end on a six-file
  copy of `cassini_uvis_solarocc_beckerjarmak2023`: `--initialize` then `--validate` gives
  18 errors, 9 "Missing from tar file" and 9 "Missing from directory", every path
  duplicated one bundle-set level deep. Entry 309 is widened to carry the seven-table
  count.
* three case-sensitivity defects in `pds4linkshelf`, which entry 304 now carries together:
  the substring test that collects a directory's labels, the exact comparison that credits
  one, and the collection inventory's detection and membership tests.
* `local_basenames[k]` indexed with a loop variable that escapes two nested loops and a
  directory boundary, in both link shelf tools. It cannot fire today, because the guard
  above it is only truthy on an iteration that set `k`; entry 312 records it.

## What the reviewer measured

All 143 lines the correction diff authored, about 60 distinct claim-sentences, covering all
seventeen enumerated claims; and the remaining ~890 docstring lines of the seven files.
6 disproved and 5 misleading, of which **5 and 5 are in the corrections**: 10 of its 11
documentation findings sit in the 14 per cent of the prose the first read rewrote.
