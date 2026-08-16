# PR-33a validation — the archive info shelf rebuild, and the build-order DAG

Base: `feat/api-stubs`, first validated at `fa4a564` and re-validated in full
after merging its move to `0d322b3`. Branch: `fix/archive-infoshelf-rebuild`.
Owner-directed, 2026-08-16; the instruction and the freeze-boundary ruling are in
`plans/2026-08-16-addendum-update-holdings-script-fix.md`.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3, Sphinx 9.1.0,
sphinxcontrib-mermaid 2.1.0), with `PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and
`PDSFILE_TEST_HOLDINGS=full` in the environment where holdings are read. The real
holdings roots were **read only**; every tool run below ran against a scratch copy.

## 1. What changed

| | |
|---|---:|
| `src/` files changed | 1 (`update_holdings_for_new_metadata.sh` — a shell script; no Python) |
| script deletions corrected | 2 (`_infoshelf-archives-metadata`: directory form → `${VOLSET}_info.*` files; `checksums-archives-metadata`: `${VOLSET}_*` narrowed to the one rebuilt `${VOLSET}_metadata_md5.txt`) |
| script commands | 6 → 7 (`pdsinfoshelf --initialize` over `archives-metadata/` added), reordered |
| argument validation added | `VOLSET` must be one `[A-Za-z0-9_]+` path component before anything is removed |
| new test module | `tests/holdings_maintenance/test_update_holdings_script.py`, 4 tests, `holdings_free` |
| docs sections rewritten | 2 (concepts "The order in which they must be built"; shell-scripts script paragraph) |
| mermaid diagrams added | 1 (the dependency DAG, 8 nodes, 7 edges) |
| command examples added | 2 (PDS3: 7 commands; PDS4: 4 commands + the index-shelf form) |
| observations added | 2 (4062, 4063); 4063 then fixed here and discharged; register count 213 → 214 |
| plans addendum | 1 |

## 2. The defect, measured before fixing

The script deleted seven products and rebuilt six, and the seventh deletion was
itself a no-op:

* `_infoshelf-archives-metadata/` holds `<volset>_info.pickle`/`.py` **files at the
  category's top level** (verified against the real tree: no `<volset>/` directory
  exists there), so `rm -rf ".../_infoshelf-archives-metadata/$VOLSET"` removed
  nothing;
* no command ran `pdsinfoshelf` over `archives-metadata/`, so the shelf
  `pdsdependency.py`'s fifth general rule requires (`pdsdependency.py:647-654`,
  repair command `pdsinfoshelf --initialize <root>archives-metadata/<volset>`) was
  never rewritten either.

The two halves compound: because `pdsinfoshelf --initialize` **errors when the shelf
already exists** (`pdsinfoshelf.py:733-735`, and the error makes the exit status 1,
which `set -e` turns into script death), adding the rebuild without correcting the
deletion would have made the script fail on every volume set that has ever had an
archive info shelf. The deletion fix is therefore part of the bug fix, not a scope
widening: the deletion targets the same product it always named, in the shape that
exists. The corrected glob `${VOLSET}_info.*` does not match a versioned sibling's
`_v1.0_info.*`.

The pre-existing checksum deletion one line above it did overreach, and under the
owner's "fix bugs, never document them" ruling it is narrowed in this PR as well.
Measured against the real `checksums-archives-metadata/` directory rather than
reasoned from the pattern: with `VOLSET=COISS_1xxx` the old `${VOLSET}_*` glob
matches 4 files — the one `COISS_1xxx_metadata_md5.txt` the rebuild rewrites plus
3 versioned siblings (`_v1.0`, `_v1.1`, `_v1.2`) — and with `VOLSET=GO_0xxx` it
matches 6, five of them versioned. The rebuild, `pdschecksums --initialize` over
`archives-metadata/$VOLSET`, writes exactly
`checksums-archives-metadata/${VOLSET}_metadata_md5.txt`
(`checksum_path_and_lskip`, `pdsfile.py:1204-1206`, suffix empty for the
unversioned tree), and no command of the script reads or rebuilds any versioned
tree, so every versioned match was a file the run deletes and cannot restore. The
deletion is narrowed to that one literal name, which also removes the line's
unquoted expansion (Shellcheck SC2086).

The pre-fix ordering was also measured rather than assumed: the six old commands
satisfied every pairwise rule for the products they built — the old prose claim that
"the archive is written before the checksums the info shelf will read" implied a
violation that did not exist, since `pdsarchives` reads no checksum or shelf (its
only contact with them is rejecting checksum/archive paths on the command line). The
one violated rule was the fifth, via the missing product. The rewritten section
therefore states the constraint as the partial order it is.

## 3. The fix, verified end to end

`metadata/EBROCC_xxxx` (68K, one volume) was copied from the real root into a
scratch `holdings/` tree, with a stale two-file `_infoshelf-archives-metadata` seed
planted to prove the deletion fires. The fixed script ran from its own directory
with the venv on `PATH`:

    bash update_holdings_for_new_metadata.sh <scratch>/holdings EBROCC_xxxx
    → ALL COMPLETED WITH NO ERRORS, exit 0

All seven products existed afterward, the archive info shelf with real shelf content
replacing the seed. The seven newer-than relations were then verified by direct
mtime comparison over the scratch tree — the same predicate the dependency rules
encode (`pdsdependency` itself is keyed off `volumes/` paths, which a metadata-only
scratch tree does not have):

    PASS  checksums-metadata newer than metadata
    PASS  _infoshelf-metadata newer than checksums-metadata
    PASS  archives-metadata newer than metadata
    PASS  checksums-archives-metadata newer than archives-metadata
    PASS  _infoshelf-archives-metadata newer than checksums-archives-metadata
    PASS  _linkshelf-metadata newer than metadata
    PASS  _indexshelf-metadata newer than metadata tables

## 4. The regression test, and its negative control

`test_update_holdings_script.py` parses the script's text (no holdings, marked
`holdings_free`) and asserts four things: the deleted-product set and the
rebuilt-product set each equal the pinned seven-product list, with exactly one
deletion and one rebuild per product (equality in both directions because
`--initialize` aborts over a survivor, against the pinned list so that dropping a
deletion and its rebuild together still fails, and with cardinality so that a
duplicated line fails too); every command's inputs — the checksum file an info
shelf reads, and any deleted category a command targets — are rebuilt before the
command runs; a deletion under a flat category names exactly its category's
pinned target rather than a directory or a wider glob; and each flat-category
deletion, expanded as a glob over a directory listing modeled on the real
category contents, matches exactly the files its rebuild writes — so a versioned
sibling must survive. The parser asserts on any `rm` or `python` line it cannot
parse, and it parses both quoting shapes the script has had, so a reintroduced
wide glob fails on its semantics rather than its shape.

Negative control, measured by checking out each older script and re-running:

| script | outcome |
|---|---|
| pre-PR | **3 failed, 1 passed** — the set equality (`_infoshelf-archives-metadata` deleted, never rebuilt), the flat-category targets, and the deleted-equals-rebuilt glob expansion |
| infoshelf fix only (`d000d25`) | **2 failed, 2 passed** — both deletion-scope tests, on the wide `${VOLSET}_*` matching versioned siblings |
| head | **4 passed** |

The ordering test passes against all three, which is correct: the old order
satisfied every pairwise rule for the six products it built.

## 5. The diagram: validated outside Sphinx, because Sphinx does not parse it

The Sphinx builds treat a `.. mermaid::` body as opaque text. The diagram source was
validated with `mmdc` (mermaid-cli 10.9.2, `/usr/bin/mmdc`): it renders to an SVG,
and the SVG was read — all 8 node labels present, all 7 edges with the right tool
labels, topology `metadata → checksums → infoshelf`, `metadata → archives →
archive-checksums → archive-infoshelf`, `metadata → linkshelf`, `metadata →
indexshelf`. The source embedded in the built page
(`_build/html/user_guide/user_guide_concepts.html`, inside the extension's `<pre>`)
was extracted and compared: byte-identical to what `mmdc` rendered.

Every edge was derived from `pdsdependency.py`'s rule table, not from prose: the
five general rules (`pdsdependency.py:610-654`) give
`<type> → checksums-<type> → _infoshelf-<type>` and
`<type> → archives-<type> → checksums-archives-<type> → _infoshelf-archives-<type>`;
the link-shelf loop (`:656-665`, over volumes/metadata/calibrated) gives
`<type> → _linkshelf-<type>`; the index rule (`:689-697`) gives
`metadata → _indexshelf-metadata`. No other "newer" rule in the file relates two
products of one tree.

## 6. The command examples: every command verified by running it

**PDS3** (7 commands, the sequence the fixed script runs): verified by the §3 script
run, which executes exactly these commands over `metadata/$VOLSET` and
`archives-metadata/$VOLSET`.

**PDS4** (4 commands): each was run against a scratch `pds4-holdings/` tree holding
a full copy of the cassini_uvis_solarocc_beckerjarmak2023 bundle set (212M):

| command | outcome |
|---|---|
| `pds4checksums --initialize .../bundles/<set>` | exit 0, manifest written |
| `pds4infoshelf --initialize .../bundles/<set>` | exit 0, shelf written |
| `pds4archives --initialize .../bundles/<set>` | exit 0, `.tar.gz` written |
| `pds4linkshelf --initialize .../bundles/<set>` | shelf written; exit 1 from one data error (a document label pointing to a file the label misnames), the tool reporting published data correctly |

**The PDS4 example deliberately covers less of the graph**, and the limit was
measured, not assumed: every route to a PDS4 archive checksum or archive info shelf
dies at the same wall — `Pds4File.child` rejects
`checksums-archives-bundles/<set>_md5.txt` (`ValueError: Illegal bundle set
directory`), because `BUNDLESET_PLUS_REGEX` (`pds4file/__init__.py:121-123`) admits
no `_md5.txt` ending, where the PDS3 counterpart admits archive and checksum
endings. `pds4checksums --initialize` over `archives-bundles/<set>`,
`--initialize --archives` over `bundles/<set>`, and `pds4infoshelf` over
`archives-bundles/<set>` were each run and each crashed there (`--archives` on a
single bundle fails earlier: the archive resolves to a selection, which
`--initialize` refuses). Observation 4062 carries the full measurement; the concepts
chapter states the resulting scope without prescribing a workaround. There is also
no PDS4 counterpart of `pdsdependency` (`src/pdsfile/holdings_maintenance/pds4/`
has five tools; the console-script table has no `pds4dependency`), and PDS4 index
shelves are the pds4indexshelf page's documented data-dependent situation, which
the example section cross-references rather than restates.

## 7. Gates at head

`scripts/run-all-checks.sh` was run once, in full, with the holdings variables set,
and its output read end to end rather than tailed. Exit **0**. What each gate
measured:

| gate | measured |
|---|---|
| `ruff check` | All checks passed (both passes: configured rules, and the E111/E112/E113 indentation pass) |
| pytest (`--mode ns`, full holdings) | **1209 passed, 34 skipped** in 191 s — the base suite's 1205/34 plus exactly the 4 new test ids |
| pyroma | 10/10 |
| API freeze | 1 passed |
| clean install | all runtime modules import with no dev extras |
| stubtest | Success: no issues found in 79 modules |
| Sphinx `-W` | exit 0, **0 problem lines**, API reference 78 of 78 modules |
| Sphinx `-n -W` | exit 0, **0 problem lines**, API reference 78 of 78 modules |
| PyMarkdown | 2 files scanned, passed |

The two shelves-only suites, run separately in the same environment, match the
baseline exactly:

| suite | result |
|---|---|
| `tests/pds3file tests/rules/pds3 --mode s` | **555 passed, 3 skipped** |
| `tests/pds4file tests/rules/pds4 --mode s` | **123 passed, 31 skipped** |

The two greps the Sphinx gate cannot make were run against the built user guide at
head: `<strong>[^<]*``` and `–[a-z-]+` over
`_build/html/user_guide/*.html` — 0 hits each.

## 8. Standing rules

- The four frozen files (`tests/api/api_manifest.json`,
  `tests/api/manifest_allowlist.json`, `scripts/dump_public_api.py`,
  `tests/api/test_api_freeze.py`) and `pyproject.toml` are untouched:
  `git diff fa4a564 --name-only` names none of them.
- No golden or baseline was edited; no test was skipped or xfailed; the ratchet did
  not move; `ruff format` was not run. No Python under `src/` changed.
- The script's CLI, name and final echo are unchanged. Two deletions changed:
  each now removes exactly the files its own rebuild writes (§2, and the
  addendum). The volume-set argument is validated as one path component before
  anything is removed.
- No absolute holdings path appears in any committed file: the examples use
  `$PDS3_HOLDINGS_DIR`/`$PDS4_HOLDINGS_DIR` throughout.
- Line endings are LF in every added and changed file.
- Holdings were read-only throughout: every tool run was against a scratch copy
  under the session scratchpad.

## 9. The reviews

Every round a fresh no-context subagent; recorded in `critiques/pr-33a/round-<k>.md`.

| round | scope | findings |
|---|---|---:|
| 1 | full diff | 0 Major, 5 Minor, 2 Deferred — verdict goal met |
| 2 | full diff | 0 Major, 2 Minor, 2 Deferred — verdict goal met; one Minor inside round 1's own fix |
| 3 | scoped: the correction passages, clause by clause | 0 Major, 1 Minor — verdict goal met; the Minor inside round 2's own fix, in the record |
| 4 | scoped: round-3 resolution + new Majors only | **0 findings — goal met, loop terminates** |

The loop's totals: 0 Major, 8 Minor, 2 Deferred across four rounds, ending inside
§6.6's four-round cap. No round found a Major: the script fix, the diagram and the
examples were verified rather than faulted in every round, and every Minor after
round 1 was inside the previous round's own correction — the measured Phase 7
pattern (a correction pass introduces new defects at about half the rate of the
pass it corrects) holding at wrap-and-record level here, never at claim level. One
Minor was rebutted rather than fixed (round 1's m5: stating the versioned-sibling
glob overreach in the user guide would document a defect the owner had not yet
ruled on narrowing; observation 4063 was its record) and no later reviewer
re-raised it; the owner has since ruled, the glob is narrowed (§2), and the
observation is discharged. The other Deferred item, observation 4062, stays in
the register.

After the loop, CodeRabbit reviewed the PR and posted five findings. All five
were accepted and fixed: the two record inaccuracies (observation 4062's
overbroad "any archives-side target" lead; round-4.md's row count against the §9
table), the script's unvalidated `VOLSET` argument and unquoted expansions
(SC2086), and the two regression-test gaps — missing cardinality checks and a
prefix-only flat-target assertion, both closed by the §4 shape above.
