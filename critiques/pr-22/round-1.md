# PR-22 — adversarial review round 1

**Date:** 2026-07-28
**Reviewer:** a fresh, no-context opus-class subagent (§6.6), given the PR-22
section of the plan, the Phase-5 preamble and mixin mechanics including the
alphabetical base-order rule and the note that the preamble's illustration on this
branch is stale, §2, §6.1/§6.2/§6.4, deferred observation 42, the progressive
`.cursor/rules` compliance schedule, the exact diff
`git diff pr-21-preload...HEAD`, and read access to the repo at HEAD, to the real
holdings and to both consumer repos.
**Diff reviewed:** HEAD `32d50e7` ("docs: record the PR-22 validation evidence and
topology").
**Verdict:** **goal met** — 0 Major, 8 Minor, 3 Deferred.

## What the reviewer re-derived independently

It took the record's word for nothing. It reproduced the moved blob's MD5
`a49cd663…` from the parent's two line ranges; compared all 68 definitions and the
53,113-byte total; counted class-level `Assign` targets (61 → 61, mixin 0); ran a
`symtable` free-variable sweep (7 names, 0 unresolved); checked that no
module-level name was lost from `pdsfile.pdsfile` by AST **and** by runtime
`hasattr`; re-ran `scripts/dump_public_api.py` on both tips (733,876 bytes, MD5
`442428da…`, empty stderr); re-parsed the recorded junit XMLs and recomputed all
three set diffs; re-read the coverage provenance (71 vs 72 measured files);
checked the record's freshness against the last `src/` commit; re-derived every
per-code ratchet count and the converse entry-removed runs, plus the phase union
(15) against `rewrite`'s `pdsfile.py` entry (25); ran **its own** dead-code sweep
over `rewrite`'s 6,304-line `pdsfile.py` and got the identical eight lines;
re-counted every line figure at every boundary and the §19 decomposition;
dumped `PdsFile`'s body banner by banner against the stay-list; re-derived the
state contract (114 names) and the 41-slot write set; re-measured the mixin and
hierarchy figures; reproduced the PR-15 bug-1 negative control and the
`ICON_SET_BY_TYPE` control; re-ran consumer smoke Check A; and **broke the new
back-import check both ways on a copy of the tree** to confirm it is not vacuous.

Everything above reproduced. The findings below are all in text.

## Major

**None.**

## Minor — all eight accepted, all eight fixed

### Minor 1 — the lazy-property shape is stated, not measured, and is wrong for 24 of the 64

`src/pdsfile/pdsfile.py`'s module docstring said "64 lazy properties, **each**
deriving a value on first access, keeping it in an `_X_filled` slot and writing
the object back to the cache"; `src/pdsfile/_properties.py`'s class docstring said
"Sixty-four of the sixty-eight members are lazy properties **with the same
shape**".

**Re-measured by the executor before fixing, and the finding reproduces exactly.**
Of the 64 properties, **40** write an underscore-prefixed slot and **39** call
`self._recache()`; the remaining **24** hold no slot and derive their value on
every access — `is_documents`, `filespec`, `absolute_or_logical_path`, `is_label`,
`url`, `anchor`, `extension`, `parent_logical_path`, `size_bytes`, `modtime`,
`checksum`, `width`, `height`, `alt`, `icon_type`, `linked_abspaths`,
`label_abspath`, `data_abspaths`, `iconset_open`, `iconset_closed`,
`multipage_view_allowed`, `continuous_view_allowed`, `has_neighbor_rule`,
`all_version_abspaths`.

This is the finding that matters, and it is exactly the defect class §15 of the
record is about: the derivation the executor ran checked *name coverage* in both
directions and never checked this sentence, because the sentence is a claim about
control flow rather than about names. Both docstrings now give the measured split,
name all 24, and name the one property (`filename_keylen`) that fills a slot
without the `_recache()` call.

**A first attempt at the fix introduced a second stated-not-measured claim** — "most
of which are one-line compositions of a slot some other property fills" — which
was measured before committing and is **false**: 8 of the 24 are a single `return`
statement and 16 are not. The committed text says so.

### Minor 2 — "these eleven" describes ten imports

`src/pdsfile/pdsfile.py:83` and `:103`. The re-export block holds `bisect`,
`datetime`, `fnmatch`, `functools`, `glob`, `math`, `numbers`, `pickle`, `PIL`,
`time` — **ten**. The parent said "eight" for eight; this PR added `datetime` and
`PIL` and wrote eleven. Both occurrences now say ten.

### Minor 3 — the destination line range of the moved blob was wrong

`critiques/phase5-validation.md` §5.1(a) said the moved text occupies
`_properties.py`'s lines **110–1666**. Searching every offset for the blob's MD5
finds exactly one match, and it was at **120–1676** when the reviewer looked. The
figure was measured on an earlier draft and not re-measured after the class
docstring was rewritten — the "re-measure again if a later commit could have moved
it" rule, missed. After this round's docstring corrections the blob is at
**130–1686**, and the record now says so.

### Minor 4 — off-by-one in the "what moved" table

`critiques/phase5-validation.md` §5 labelled the parent range `675–2034` as "**64**
lazy properties … plus `_repair_width_height`". Measured: that range holds **63**
properties plus `_repair_width_height` = 64 statements; the 64th property,
`all_version_abspaths`, is in the `2037–2230` row. As written the two rows summed
to 69 moved statements rather than 68. Corrected to 63.

### Minor 5 — §5.1(c)'s enumeration is short by two of the seven lines it enumerates

The subsection says that of the 37 definitions left in `PdsFile`'s body, 34 are
byte-identical and the three that differ do so "**only** by the five commented-out
lines §7 removes", with a diff of five `-` lines and zero `+`. All of that is
literally true, and the reviewer reproduced it — but §7 removes **seven** lines
from `pdsfile.py`. The other two trail the `return` in `is_bundle_dir` and
`is_bundle_file`, so they fall outside every definition's AST span and are
invisible to a definition-level comparison. A subsection whose stated purpose is
"enumerated rather than waved at" has to say that, and now does.

### Minor 6 — `_recache` is read at 47 sites, not 46

`critiques/phase5-validation.md` §5.2 said "**46** sites … always through `self.`
or through a sibling PdsFile object". 46 is the `self._recache` count; the
`pdsf._recache()` call in `all_versions` — which the same subsection discusses two
paragraphs earlier — makes **47**. Corrected, with the breakdown.

### Minor 7 — three inventory slips in the module docstring's module map

`src/pdsfile/pdsfile.py`'s decomposition map called `_opus.py`'s two constructors
"the two OPUS-id constructors"; `from_filespec` resolves a bundle-name **file
specification** through `FILESPEC_TO_BUNDLESET` and never touches an OPUS ID,
which `_opus.py`'s own header and PR-19's record both say. It also omitted
`_needs_glob` and `_GLOB_CACHE_SIZE` from `_path_utils.py`'s list, and called
`_preload.py`'s module constants "the lifetime constants" although
`DICTIONARY_CACHE_LIMIT` and `HAS_PYLIBMC` are there too. All three fixed.

### Minor 8 — the back-import probe had no subprocess timeout

`tests/api/test_mixin_import_isolation.py`. A mixin module that blocks at import
time — a lock, a socket, a read from stdin — would hang the gate rather than fail
it, in a job with no other watchdog. `subprocess.run(..., timeout=60)` added, with
a comment saying why.

## Deferred — three, appended to `critiques/deferred-observations.md`

| # | Entry | Owner |
|---|---|---|
| 62 | `filename_keylen` fills its slot without calling `_recache()` — the same consequence as PR-15's bug 1, though not the same defect; byte-identical through this move, so out of scope here and needing a regression test first | unassigned (a future bug-fix PR) |
| 63 | The back-import guard covers the nine mixin modules and not `_path_utils.py`, which `pdsfile.py` also imports at module level. Entry 42 asks for "a mixin module", so this is a widening rather than a gap; `_path_utils.py` is measured clean today | whichever PR next edits the mixin harness (with entry 53) |
| 64 | Six lines of commented-out `MemcachedCache.get_multi` code remain in `pdscache.py`, which is outside PR-22's declared dead-code scope and inside the pylibmc support ground rule 9 protects; the commented-out call is also the evidence for the workaround comment above it | owner decision, then PR-23 |

None was taken up, per the scope rule in the Phase-5 briefs (a Deferred finding is
deferred unless it is inside the PR's stated deliverables).

## Consequences for the record

Minors 1, 2, 7 and 8 changed files under `src/pdsfile/` and `tests/`, so by §6.6
step 5 the full-data record was **regenerated** before round 2 rather than carried
forward. Minors 3, 4, 5 and 6 are corrections to
`critiques/phase5-validation.md` itself.

**Eight findings, eight in text: four in docstrings under `src/pdsfile/`, three in
the validation record, one a missing subprocess timeout in a new test. None in the
extracted code** — the same result PR-19, PR-20 and PR-21 each produced, and the
strongest evidence available that a 1,557-line mechanical move is clean.
