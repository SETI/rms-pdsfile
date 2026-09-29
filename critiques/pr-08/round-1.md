# PR-08 adversarial review — round 1

Fresh, no-context Opus reviewer subagent (§6.6), scoped to
`origin/rewrite...pr-08-extract-rule-tests`. Charged adversarially to prove the
mechanical rule-test extraction was NOT behavior-preserving, that the freeze was
broken, that production code was lost, or that a gate was only claimed.

## Reviewer verdict: **goal met** — zero Major, two Minor.

The reviewer AST-compared every moved test function + helper across all 16
modules (byte/AST-identical, none dropped/added), regenerated the manifest diff
(194 diffs, all removals, every one matched by the new category, zero
production names removed), ran the clean-install gate (independently confirming
every rule module imports with `pytest` blocked via a `meta_path` blocker),
confirmed api-freeze passes hermetically and that `--confcutdir=tests` (the old
value) correctly FAILS — validating the move to `--confcutdir=tests/api` — and
confirmed no production code was lost in COISS / COVIMS_0xxx / cassini_iss /
cassini_vims / the pds4 skip marker.

## Major
None.

## Minor — both FIXED this round

**M1. Three pds4 rule modules grew an `F401` ratchet entry (production ratchet
must only shrink).** After the test move, `PRIMARY_FILESPEC_LIST` (imported at
line 9 of `cassini_iss_fring_mosaics_rsfrench2025.py`,
`cassini_uvis_solarocc_beckerjarmak2023.py`, `uranus_occs_earthbased.py`) is no
longer referenced in-module — it was used only by the extracted test — yet it is
a **frozen public name** (`api_manifest.json`), so the import must stay or the
freeze breaks (its removal is not in category #2). The first cut suppressed the
resulting F401 by adding it to each file's ratchet entry, i.e. a production-file
ratchet GROWTH.
**Fix:** rewrote each import as the explicit re-export idiom `from
.<…>_primary_filespec import PRIMARY_FILESPEC_LIST as PRIMARY_FILESPEC_LIST`
(ruff/pyflakes treat the redundant alias as an intentional re-export → no F401),
then dropped `F401` from all three ratchet entries. Verified: `ruff check
--select F401 --config "lint.per-file-ignores = {}"` on the three files → clean;
the frozen name still binds (`len(PRIMARY_FILESPEC_LIST) == 772`); api-freeze
still passes. Net ratchet effect on these files is now shrink-only.

**M2. `VG_28xx.py` was flipped CRLF→LF across the whole file.** The rule module
is the repo's only CRLF-terminated source; the extraction script read it in text
mode and rewrote it with `\n`, normalizing all 1105 lines and ballooning the
diff of an otherwise 88-line test-section removal.
**Fix:** rewrote the production region (lines 1..1017) preserving the original
CRLF terminators, from the `origin/rewrite` blob. The file is CRLF again and a
byte-diff vs `origin/rewrite` is now exactly the 88-line test-section removal.
(No `.gitattributes` / `core.autocrlf` in play, so this sticks.)

## Deferred (non-blocking) — appended to `critiques/deferred-observations.md`
- Sub-plan prose error (not a code defect): the sub-plan says "COISS keeps
  `import os` (production use at line 1031)", but old line 1031 is inside
  `test_opus_id_to_primary_logical_path()` — COISS's `os` was entirely
  test-only. The implementation is correct (COISS rule module has no `import os`
  and no `os.` reference; ruff clean); only the plan's prose is wrong.
- `test_api_freeze.py::_is_forgiven` never reads a category's `pr` field, so
  §6.1's "activates only from its named PR" is not code-enforced. Pre-existing
  in the PR-02 checker (unchanged here); the new allowlist entry carries
  `"pr": "PR-08"` for provenance regardless.
- PR-07's "`helper.py` double-import (resolved in PR-08)" note is **not** closed
  by this PR: the owner's split narrowed PR-08 to rule-test extraction only (no
  `testpaths`, no restructure of `tests/pds{3,4}file/`), and those modules still
  use `from .helper import …`. Re-deferred to whichever PR adds `testpaths` /
  the pds{3,4}file test restructure.

## Re-verification after the fixes (both touch `src/pdsfile/`)
- `ruff check src/pdsfile tests scripts` → clean.
- api-freeze hermetic → passes; `import pdsfile` + frozen name resolve.
- Limited holdings (`/seti/opus/pdsdata`): `--mode ns` 679 passed / 34 skipped;
  `--mode s` 555 passed / 3 skipped — unchanged from before the fixes.
