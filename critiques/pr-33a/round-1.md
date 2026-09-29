# PR-33a round 1 — full diff

Reviewer: a fresh, no-context subagent given the owner's four instructions, the §2
ground rules, §6.1/§6.2, the §6.6 progressive-compliance schedule, the exact diff
`git diff feat/api-stubs..fix/archive-infoshelf-rebuild` (9 files at `6ccc03a`), and
read access to the repository and the holdings roots (read-only), with the central
instructions that (a) every command in the two examples be verified against the real
parsers and every diagram edge against `pdsdependency.py`'s rule table, (b) the
script fix be proved complete and the regression test proved non-hollow, and (c) any
remaining sentence documenting a defect as behavior be hunted down. It made no
edits.

The reviewer independently reproduced: the fixed script's end-to-end run over a
scratch `metadata/EBROCC_xxxx` tree with a stale archive-info-shelf seed (exit 0,
all seven products, seed replaced); the delete/rebuild correspondence and the order
against every rule at `pdsdependency.py:610-697`; the necessity of the deletion-shape
correction (the real `_infoshelf-archives-metadata/` holds files, not directories,
and all five tools' `--initialize` refuse an existing product — each refusal
verified at its source line, two by running); the negative control (2 failed /
1 passed pre-fix, 3 passed post-fix, reproduced from
`git show feat/api-stubs:...`); the diagram's seven edges one-to-one against the
rule table plus an `mmdc` render; all four PDS4 example commands against a scratch
copy of the 212M cassini bundle set; the claimed PDS4 limits (the
`checksums-archives-bundles/<set>_md5.txt` rejection reproduced live at
`BUNDLESET_PLUS_REGEX`, no `pds4dependency` console script); the full ns suite
(1208/34), the Sphinx gate (0 problem lines both builds, 78/78), ruff on the new
file, the untouched frozen files, LF endings, no absolute holdings path, and the
register arithmetic (375−28−119−21+8=215).

Verdict: **goal met** — zero Major, five Minor, two Deferred (both already recorded
as observations 4062 and 4063, which the reviewer judged correctly recorded).

## Minor findings, and their resolutions

**m1. An unwrapped 137-character line from an edit splice**
(`user_guide_concepts.rst:196`). **Fixed:** the paragraph is rewrapped to the
file's column discipline.

**m2. The PDS4 example's fourth command exits 1 on the very bundle set it names**
— `pds4linkshelf` writes the shelf, then exits 1 on the bundle's own recurring
published-data error, and a reader following the example verbatim would meet the
nonzero exit unwarned. **Fixed:** one sentence after the example states that the
shelf is written and the exit status carries a fact about the published data,
pointing at the pds4linkshelf page, which shows that error as the bundle's own.
The wording follows the measured error text ("does not point to the file beside
it"); the file exists and the label fails to reference it.

**m3. The set-equality test pins consistency, not the product set** — deleting a
deletion and its rebuild together would keep the two sets equal. **Fixed:**
`METADATA_PRODUCTS` lists the seven products and both the deleted set and the
rebuilt set are asserted equal to it, not merely to each other.

**m4. The validation record's §9 cited a round record that did not yet exist.**
**Fixed:** this file is that record, and the §9 table now carries the round's real
counts; rows are added only for rounds that have run.

**m5. "Deletes the volume set's entries" is inexact for versioned sets** — the
pre-existing `checksums-archives-metadata/${VOLSET}_*` glob also catches versioned
siblings' files, which the rebuild does not restore. **Rebutted, not fixed:** the
reviewer's own finding notes the prose can only become exact once the glob is
narrowed, and the owner constrained this fix not to change what the script deletes.
The precise statement of the overreach is observation 4063, which awaits the
owner's call on the one-line narrowing; putting it in the user guide instead would
describe a defect as behavior, which is the instruction this PR exists to enforce.
The sentence stays at the summary level that is true of every unversioned tree, and
becomes exactly true everywhere the moment the glob is narrowed.
