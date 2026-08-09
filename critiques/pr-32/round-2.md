# PR-32 round 2 — the five remaining programs and the four shared chapters

Fresh no-context reviewer, over `user_guide_re_validate`, `user_guide_show_opus_products`,
`user_guide_pdsdependency`, `user_guide_crlf`, `user_guide_shelf_consistency_check`,
`user_guide_concepts`, `user_guide_installation`, `user_guide_shell_scripts` and
`user_guide_appendix_file_formats`. `re_validate`'s twenty options are the largest single
option surface in the guide. Tree frozen at `5cefb3d`.

## Result

| | |
|---|---:|
| chapters read | 9 |
| defects | 12 |
| of those, introduced by the correction pass | 2 |
| observations worth acting on | 3 |
| claims checked and confirmed | 20 |

The reviewer also re-derived `critiques/pr-32/check_cli_coverage.py`'s subject
independently and confirmed the checker is clean: no missing option, no wrong short form,
no undocumented default.

## Defects

1. **The concepts chapter gave one path shape for the whole tree, and it is false for
   more than half the categories.** `<holdings root>/<category>/<unit set>/<unit>/<path
   inside the unit>` holds only for the bare volume types other than `documents`.
   `archives-`, `checksums-`, `_infoshelf-` and `_linkshelf-` put a *file* where those
   have the unit's directory; `checksums-archives-*` and `_infoshelf-archives-*` have no
   unit set directory either; `documents/` has no unit level at all; and
   `_indexshelf-metadata` is one level deeper than any of them. The appendix already
   contradicted the concepts page twice. **The highest-value finding of the four rounds**,
   on the page a reader reaches first.
2. **The `general` suite enumeration accounts for 18 of its 28 rules.** The chapter said
   three rules over each of five volume types plus three link shelf rules. The suite is
   *five* rules over each of five types — the checksum file, the info shelf, the archive,
   and then the checksum file and info shelf *of that archive* — plus the three link shelf
   rules. The page's own "Steps required" block proves the missing ten fire: it printed
   `pdschecksums --initialize $PDS3_HOLDINGS_DIR/archives-volumes/COUVIS_0xxx`.
   **Introduced by the correction pass.**
3. **`user_guide_shell_scripts.rst`: "The scripts say so when they finish" is true of two
   of six.** Only `pdsdata-sync-volset.sh` and `pdsdata-sync-volume.sh` print the
   `>>> NOTE:` about syncing the unversioned volume set as well.
4. **`user_guide_crlf.rst`: "Each example below starts from that state" is false for the
   third example**, which is published in its post-`--repair` state. **Introduced by the
   correction pass.** Round 3 found the same thing by running it.
5. **`re_validate`'s batch-mode exit status.** Three command-line conditions exit 1 before
   any validation runs — no path, a path that does not exist, and a path whose resolved
   form does not end in `/holdings` — so "0 even when the run logged errors" needed
   narrowing to what the validations found.
6. **Three of `re_validate`'s option placeholders are wrong.** The parser's metavars are
   `MINUTES`, `ADDR` and `ADDR`; the chapter wrote `N`, `ADDRESS` and `ADDRESS`.
   `doc_user_guide` section 3 asks for the exact placeholder. `--log LOG` was right.
7. **`user_guide_installation.rst`: "each program rejects it" is false twice over.**
   `crlf` and `shelf_consistency_check` never look at a holdings tree at all, and for most
   of the rest what happens is an uncaught traceback rather than a rejection.
8. **`user_guide_shell_scripts.rst` says the scripts fall into three groups**, has four
   section headings, and presents the table as one ungrouped list.
9. **`user_guide_pdsdependency.rst`: "the last six are not runnable".** Only the three
   `<LABEL>` lines are. Round 3 found the same thing by running a `cat` line.
10. **Four bare code objects need cross-reference roles**: `KeyError` in `installation`,
    `TypeError` in `re_validate`, and `KeyError` and `argparse` in `show_opus_products`.
    Sibling pages already use `:exc:` and `:mod:`.
11. **`re_validate` names four logger names for five sections.** The dependency section
    logs under `pds.validation.dependencies`.
12. **`user_guide_shell_scripts.rst` gives the checkout path as the place the scripts
    live.** An installed copy has them at
    `<site-packages>/pdsfile/holdings_maintenance/pds3/`. Load-bearing, because the
    chapter tells `pip` users to run them from the directory they live in.

## Observations worth acting on

* `--all`'s table cell repeats the `--help` text, but `--all` selects the five trees and
  nothing more; "plus their checksums and archives" describes what is then checked.
* The appendix's `_volinfo` and info shelf excerpts are re-padded and truncated without
  the `...` marker `installation` promises.
* The concepts chapter says everything but the bare volume types is derived, and then says
  `_volinfo` is not.

## Checked and confirmed — do not re-check

25 categories; 36 directories created by `setup_new_holdings.sh`; 11 console scripts;
`requires-python >= 3.10`; `tabulate` as a dev-only dependency; the four version suffixes;
the `checksums_`/`superseded`/`_support` rule; `TESTS` at 49 rows naming 41 suites;
`general` at 28 rules; `--archives` on exactly four tools; `_v001` versioning; 9 files and
16 members in the PDS3 archive; root ownership of the log tree; `.DS_Store` and `._*`
dropped while other invisibles are archived; `_volinfo`'s dash semantics; `ERRORS.log` and
`WARNINGS.log` as appending thresholds; the batch `TypeError` with no log root; the three
`pdsdependency` `ERRORS.log` files; the `volumes/` component that is never created; and
zero `os.environ` holdings reads in `pdsdependency`, `re_validate` and `pdslinkshelf`.

## Disposition

All twelve defects and all three observations were applied by the finishing pass.
Defects 1 and 2 were applied first, as the brief required, and each was re-derived from
the code before the page was touched: the path shapes against both holdings trees, and
`general`'s 28 rules by introspecting `PdsDependency.DEPENDENCY_SUITES`.
