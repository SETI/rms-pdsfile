# PR-32 round 1 — the ten spec-tool chapters and the driver chapter

Fresh no-context reviewer. Angle: does each chapter's claim about *this* tool hold for
*this* tool, or was it written for its twin? The five PDS3/PDS4 pairs differ in unit noun
and little else, which is where a sentence gets pasted across. Tree frozen at `5cefb3d`.

## Result

| | |
|---|---:|
| chapters read | 11 |
| chapters with no defect | 4 |
| defects | 11 |
| observations worth acting on | 10 |

The four clean chapters were `user_guide_pds4checksums`, `user_guide_pdslinkshelf`,
`user_guide_pds4linkshelf` and `user_guide_pds4indexshelf`.

**One of the eleven was introduced by the earlier correction pass** — D1, below — and
three more (D2, D4, D9) were raised independently by round 4 reading the same commit.

## Defects

1. **`user_guide_maintenance_tools.rst` and `user_guide_pdschecksums.rst` said a target
   may be "a unit's own archive or checksum file". The checksum half is false.**
   `_shelf_common.resolve_holdings_paths()` rejects any path whose holdings-relative part
   begins `checksums-`, before anything else happens: `pdschecksums` prints
   `No checksums for checksum files:` and exits 1, `pdsinfoshelf` prints
   `No infoshelves for checksum files:`. The archive half is correct — a `.tar.gz` is
   accepted as a selection. `user_guide_pds4checksums.rst` already omitted the clause,
   which is what made the difference visible. **Introduced by the correction pass.**
2. **`Invalid file for checksumming:` was quoted for all four programs.** The two info
   shelf programs print `Invalid file for an infoshelf:`; the string is
   `ToolSpec.invalid_file_message` and differs per program. Round 4 found this
   independently.
3. **`--initialize` is not refused before the run starts.** The chapter said a selection
   is refused up front and uniformly. Path resolution succeeds and the logs open first,
   and then the four programs diverge: the checksum pair raises `ValueError`, and the
   info shelf pair is meant to log the same message. Round 4 found this independently.
   The finishing pass measured the fourth case and found the chapters' account of it
   still wrong; see round 5.
4. **"The two driver families" covers 8 of the 10.** The index shelf pair is a third
   member of the traceback family, not a case of its own: `pdsindexshelf --validate /etc`
   ends in the same unhandled `ValueError` as the archive and link shelf programs. Round 4
   found this independently.
5. **`user_guide_pdsinfoshelf.rst:48` and `user_guide_pds4infoshelf.rst:48` still said
   "a single file inside a volume/bundle".** Only a *top-level* file is accepted. The
   three other pages had been narrowed; these two were missed. Round 4 found this
   independently as a survivor.
6. **A truncated `.tar.gz` raises `EOFError`, not `tarfile.ReadError`.** Only the
   zero-byte case gives `ReadError`. Measured at 100, 20 000, 50 000 and 55 000 bytes:
   `EOFError: Compressed file ended before the end-of-stream marker was reached` every
   time.
7. **The PDS3 archive program caps three phases at 100 `INFO` lines, not two.**
   `LOAD_DIRECTORY_INFO_LIMITS`, `READ_ARCHIVE_INFO_LIMITS` and `VALIDATE_TUPLES_LIMITS`
   are each `{'info': 100}`; the chapter named the walk and the comparison and omitted the
   read of the archive. Measured on a 156-file volume: three
   `100 INFO messages reported of 154/155/155 total` lines.
8. **"Every other program in this guide except `pds4checksums` exits 1 in that
   situation" is false for `crlf`**, whose `main()` ends in a literal `return 0`.
9. **`user_guide_pdsindexshelf.rst:128` said `re_validate` re-runs four validations.**
   `user_guide_re_validate.rst:4` says five, and five is right. Pre-existing rather than
   introduced. Round 4 found this independently as a survivor.
10. **Bare CamelCase in inline literals**, which `doc_python` section 5 asks to carry a
    role: ``ValueError`` in the driver chapter, ``ValueError: File selection…`` in
    `pdschecksums`, ``RuntimeError`` in `pds4archives`. The same pages use `:exc:` and
    `:mod:` elsewhere.
11. **`doc_user_guide` section 3 asks for a default for every option.** The five task
    flags carry none — they `store_const` into one `task` dest whose default is empty,
    which is what produces `Missing task` — and `-h`/`--help` appears in no options table
    on any of the eleven pages. Neither fact was stated.

## Observations worth acting on

1. `pds4archives`: "only one of them is quiet" about a target with no archives. Three of
   the five say nothing; what distinguishes `--update` is that it does no work.
2. `pds4archives`: "Every entry is then reported as `Missing from tar file`" — 191 of the
   archive's 192 members, not every one.
3. `--quiet` suppresses every nested level, including the per-target header and the
   `Log file:` lines, not only the per-file detail.
4. "A path that does not exist" gives the checksum and info shelf programs an `OSError`
   traceback rather than the message quoted, and the index shelf programs print a
   different path form.
5. `pdschecksums` does not say its `Written:` lines are `DEBUG`; the PDS4 twin does.
6. `n ERROR messages` is singular at 1, so a grep for the documented string misses it.
7. The pages never point at `installation`'s declaration of how transcripts were
   normalized.
8. `pds4linkshelf`'s fallback matches parsed link values, not any occurrence of the name
   in the label text.
9. The shipped sandbox is post-run state; no page says an `--initialize` example needs its
   product deleted first. Round 3 found the same thing from the other direction.
10. `pds4indexshelf` calls two bundle sets "available for testing" and only one is in the
    sandbox. The reviewer copied `uranus_occs_earthbased` in and both documented failures
    then reproduced exactly.

## What it could not verify

The Sphinx build, which would have dirtied the frozen tree, so cross-reference
*resolution* is spot-checked only. `pdschecksums`'s exit-status claim as it applies to
`show_opus_products` and `re_validate`. The forward-looking half of "141 patterns and
grows". The `pdsarchives`/`pdslinkshelf` log-name collision. And the PDS4 index shelf's
`.pickle`/`.py` pair, because no PDS4 index shelf can be built against either tree.

## Disposition

All eleven defects were applied by the finishing pass. Observations 1, 2, 3, 4, 5 and 8
were applied as well; 6, 7, 9 and 10 were not, and are the reason this record names them.
