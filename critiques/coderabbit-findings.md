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
