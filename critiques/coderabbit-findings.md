# CodeRabbit findings backlog

Running log of CodeRabbit review findings that are **out of scope for the PR
that surfaced them** but worth fixing later. The modernization Phase-2 PRs are
mechanical moves; CodeRabbit reviews every file that appears in a move diff, so
it flags **pre-existing** bugs in the moved code. None of these were introduced
by the move — they already existed on `main`.

Most live in the holdings-maintenance tools, which are untested (issue #82). The
natural home for these fixes is a dedicated maintenance-tools quality pass (with
tests), not a mechanical move PR. Verify each against current code before fixing;
some may already be moot.

---

## From PR #97 (PR-06 — tools moved into the package), 2026-07-24

CodeRabbit review profile ASSERTIVE, 17 actionable findings. Line numbers are as
of the moved files under `src/pdsfile/holdings_maintenance/`. (Inline comments
failed to post on GitHub; captured here from the two review-summary bodies.)

### 🔴 Critical

1. **`pds3/shelf_consistency_check.py:60-64` — `NameError` on the exact
   condition the script detects.** The missing-`.lbl` branch does `error += 1`,
   but the counter used everywhere else is `errors`. The undefined name raises
   `NameError` and aborts the whole traversal the moment an index shelf without a
   matching `.lbl` is found — i.e. it crashes precisely when it should report.
   Fix: use `errors`.

### 🟠 Major

2. **`pds3/crlf.py:51-61` — unguarded division by `len(content)` crashes on
   empty files.** The binary-file threshold check divides by the decoded length
   with no empty-content guard → `ZeroDivisionError`. Guard the empty case before
   dividing; keep non-empty classification unchanged.

3. **`pds3/crlf.py:114-121` — repaired-files summary line skipped when >1 file
   is repaired.** The nfiles summary only prints the repaired message for exactly
   one repair. Print it for any nonzero repair count; keep the singular/plural
   wording for exactly one.

4. **`pds3/pdschecksums.py:367-369` (`validate_pairs`) and
   `pds3/pdslinkshelf.py:1373-1374` (`validate_links`) — `return` inside a
   `finally` swallows exceptions.** Keep `logger.close()` in `finally` but move
   the `return` after the block so raised exceptions propagate.

5. **`pds3/pdschecksums.py:914-919` — `os.system(' '.join(sys.argv))` in the
   `--infoshelf` chaining flow.** Shell-joining argv is an injection/quoting
   hazard. Build an argument list (dropping `--infoshelf`/`-i`), run via
   `subprocess.run` without a shell, and propagate its return code through
   `sys.exit`.

6. **`pds3/pdsdependency.py:191-199` — backup-file skip is unreachable and uses
   an undefined name.** The `BACKUP_FILENAME`/`" copy"` check is over-indented
   into the dot-underscore branch (so it never runs in the file loop before the
   modtime update), and it references `abspath` where the loop variable is
   `absfile`. Dedent into the loop and use `absfile`.

7. **`pds4/pds4archives.py:216-218` — bare `raise` with no active exception.**
   In the no-archive-paths branch, a bare `raise` outside an `except` yields a
   misleading `RuntimeError: No active exception to re-raise`. Raise an explicit
   exception after logging, preserving the message.

8. **`pds4/pds4checksums.py:887-892` — wrong token in `--infoshelf` chaining.**
   The subprocess argv transform must set `sys.argv[0]` to `pds4infoshelf`
   (currently it does not substitute correctly), so the chain invokes the wrong
   entry point. Fix the `pds4checksums` → `pds4infoshelf` replacement.

### 🟡 Minor

9. **`pds3/pdsarchives.py:230-234` — tarfile not closed on error.** Use a
   `with tarfile.open(...)` context manager; drop the manual `f.close()`.

10. **`pds3/pdschecksums.py:43-50` — `hashfile` never closes its file handle.**
    Wrap the read in a context manager.

11. **`pds3/pdschecksums.py:289-307` — checksum file not closed via context
    manager.** Use `with open(check_path, 'w')`; drop the manual `f.close()`.

12. **`pds3/crlf.py:51-61` — use `latin_1`, not `latin8`, for byte-identity
    decode/encode.** `latin_1` maps bytes 0–255 to code points directly;
    `latin8` (ISO-8859-14) does not, so byte classification and round-trip are
    subtly wrong.

13. **`pds3/copy_documents.sh:22-27` — copy is not idempotent.** Unlike
    `copy_shelves.sh`, it never removes an existing
    `$DEST_HOLDINGS/documents/$VOLSET` before `cp -r`, so a re-run nests the
    source inside the old copy. `rm -rf` the destination first.

14. **`pds3/copy_shelves.sh:23-26` — misleading missing-directory message.** The
    error reports `$DEST_HOLDINGS/$TYPE/$VOLSET` though only `$DEST_HOLDINGS/$TYPE`
    is validated. Report the path actually checked.

15. **`pds3/create_fake_volumes_for_metadata.sh:5-24` — `exit -1` and unquoted
    `realpath` arg.** Use `exit 1` for all validation failures; quote `"$1"` when
    passing to `realpath` so paths with spaces work.

16. **`pds3/update_holdings_for_new_metadata.sh:35-40` — wrapper runs relative
    `python <tool>.py` filenames.** Invoke the installed console scripts
    (`pdsarchives`, `pdschecksums`, `pdsinfoshelf`, `pdsindexshelf`,
    `pdslinkshelf`) instead of relative filenames; keep arguments/order. (More
    relevant now that the tools are a proper package with entry points.)

17. **`pds3/pdsdata-sync-volset-metadata.sh:29-45` (+ `…-versions.sh:31-47`,
    `…-previews.sh:30-46`) — duplicated remount/EXIT-trap boilerplate.** The
    safety-critical "remount `pdsdata-production` read-write, trap EXIT to remount
    read-only" block is copy-pasted across several sync scripts. Extract to one
    sourced helper so future fixes apply everywhere at once.

## From PR #100 (PR-08 — rule-module tests extracted), 2026-07-25

CodeRabbit review profile ASSERTIVE, 19 actionable findings. PR-08 moved the
inline rule-module tests to `tests/rules/pds{3,4}/` **verbatim** (behavior-
preserving), so every finding below is a **pre-existing** test-quality issue that
came along with the move — none was introduced by PR-08, and all are confirmed
present on `origin/rewrite`. They are deliberately **not** fixed in PR-08 (that
would break the verbatim/behavior-preservation guarantee and could surface real
masked failures the owner deferred). Natural home: a dedicated rule-test quality
pass (relates to #37 / the deferred additive-coverage follow-up). Line numbers
are as of the extracted files under `tests/rules/`. Verify each before fixing.

Findings that are about PR-08 *itself* (its new README / sub-plan doc, and the
docstring-coverage pre-merge check) are handled separately and are **not** in
this backlog.

### 🔴 Critical

1. **`tests/rules/pds3/test_coiss_xxxx.py` (`test_opus_id_to_primary_logical_path`,
   ~L288-299) — filter loop clears the list it iterates, so every downstream
   assertion is dead.** `product_pdsfiles = []` is rebound immediately *before*
   the `for pdsf in product_pdsfiles:` loop that is supposed to populate the
   filtered list, so the loop body never runs and the list stays empty. The
   viewset/version/associated assertions (~L306-324) then iterate nothing — the
   test silently validates only the opus_id round-trip. Fix: filter into a
   separate list. **Re-enabling the assertions may surface real failures that
   were masked.** (Verified pre-existing on `origin/rewrite`
   `COISS_xxxx.py`. COCIRS/CORSS use list comprehensions and are not affected,
   but audit every `test_opus_id_to_primary_logical_path` when fixing.)

### 🟠 Major

2. **`tests/rules/pds3/test_cocirs_xxxx.py` (~L155-161) — `fpx` derived from a
   leaked loop variable.** `parts = pdsf.abspath.split('_FP')` uses `pdsf`, whose
   value is whatever a prior loop last bound — not `test_pdsf`, the file under
   test. Depends on iteration order; `NameError` if the product list is empty,
   `IndexError` if that path has no `_FP`. Fix: derive from `test_pdsf` and guard
   the split.

3. **`tests/rules/pds3/test_hstxx_xxxx.py` (~L74-83) — duplicated viewset
   validation loop.** Lines 80-83 repeat 76-79 verbatim (`for viewset in
   pdsf.all_viewsets…: assert viewable.abspath in opus_id_abspaths`), doubling
   the work with no added coverage. Remove the second loop.

### 🟡 Minor

4. **`tests/rules/pds3/test_cocirs_xxxx.py` (~L44-47) — unused `trimmed` in the
   failure message.** The assert prints raw `abspaths` while a computed `trimmed`
   (holdings-relative) is discarded; use `trimmed` to match
   `test_associations_to_diagrams`.

5. **`tests/rules/pds3/test_covims_0xxx.py` (~L212-217) — un-parametrized
   round-trip over ~170 paths.** One test loops all paths, stops at the first
   failure, and reports no case identity. Parametrize with
   `@pytest.mark.parametrize('file_path', TESTS)` (or at least add `file_path` to
   the assert message, as `test_go_0xxx.py` does).

### 🔵 Trivial / design

6. **`tests/rules/pds3/test_coiss_xxxx.py` (~L24-30) — skip decision reads
   golden-file content instead of holdings-bundle presence.**
   `_coiss_opus_products_golden_references_pds4_reproj` opens the committed golden
   and greps `_PDS4_REPROJ_BUNDLE_MARKERS`, so a regenerated golden silently
   re-enables/disables the case. Gate on whether the PDS4 reproj bundle exists in
   the holdings tree instead (the TODO anticipates removal).

7. **`tests/rules/pds3/test_coiss_xxxx.py` (~L267-278) — silent `continue` hides
   skipped cases.** Deferred paths leave no record in the report; use per-path
   parametrization or an explicit skip so deferred coverage is visible.

8. **`tests/rules/pds3/test_ebrocc_xxxx.py` (~L12-16) &
   `test_nhxxxx_xxxx.py` (~L12-14) — explanatory comment sits *inside* the
   `@pytest.mark.parametrize(` call**, between the decorator open and the argnames
   string, obscuring the signature. Move each note above the decorator.

9. **`tests/rules/pds3/test_go_0xxx.py` (~L328-331) — duplicate test tuples.**
   Two identical pairs (`GO_0019/REDO/C3/JUPITER/C0368441600R.LBL` and
   `…/E6/IO/C0383655111R.LBL`) double the work; keep one of each.

10. **`tests/rules/pds3/test_nhxxxx_xxxx.py` (~L163-169) — hex-code substitution
    operates on the whole abspath.** `test_pdsf.abspath.split('0x')[1]` and
    `.replace(hex_code, alt_hex_code)` act on the full path, so any `0x…` in the
    holdings root or a parent dir yields the wrong `alt_abspath`. Derive from
    `pdsf.basename` and rebuild the path.

11. **`tests/rules/pds3/test_vg_28xx.py` (~L77-82) — duplicate entry**
    `VG_2803/U_RINGS/EASYDATA/KM00_25/RU4P2XEI.TAB` (appears twice).

12. **`tests/rules/pds3/test_vgiss_xxxx.py` (~L56-143) — ~10 consecutive
    duplicate `TESTS` pairs.** Each re-runs a full `opus_products()` +
    `associated_abspaths()` sweep for no added coverage; dedupe to cut runtime.

13. **`tests/rules/pds3/test_vgiss_xxxx.py` (~L287-288) — magic `filepath[6]`
    index** for the volume-set. Derive from the path's first component/prefix
    (e.g. `filepath.split('/')[0][:7] + 'xxx'`) so it survives prefix-length
    changes.

14. **`tests/rules/pds4/test_uranus_occs_earthbased.py` (~L76-110) — 35-line
    stale commented-out OPUS-products block.** Internally inconsistent
    (`product_pds4files` vs `product_pdsfiles`; pds3-only `volumes` category) so
    it won't run if uncommented. Replace with a short TODO + issue reference for
    the deferred coverage. (CodeRabbit offered to open a tracking issue.)

### Style — already ratcheted; the formatting phase (PR-23/24) will resolve

15. **Ruff `E701` one-line `if …: continue`** in `test_corss_8xxx.py` (L249,
    L255), `test_couvis_0xxx.py` (L82-93), `test_covims_8xxx.py` (L80). These are
    in the per-file-ignore ratchet, so the lint gate passes today; splitting them
    is routine ratchet-shrinking for the formatting phase.

16. **Blank line between `@pytest.mark.parametrize` and `def`** in the three pds4
    test modules (cosmetic; reads as an orphaned decorator).
