# PR-32 round 4 — the second read of what the first correction pass changed

Fresh no-context reviewer, given the earlier correction commit by name and asked two
questions of every sentence it touched: is this true, and did the correction make it worse
than what it replaced? Tree frozen at `5cefb3d`.

## Result

| | |
|---|---:|
| defects **introduced** by the correction pass | 12 |
| defects that **survived** it | 7 |
| total | 19 |
| introduced share | **12 of 19** |

This is the ninth PR in this phase to measure the second-read ratio, and it lands where
the previous eight did. The running list is in `critiques/pr-32-validation.md`.

## Mechanical check, first

`-n -W` exits 0 with an empty warning file; **0** `<strong>…``…</strong>` spans in the
built HTML, and **0** en-dashed flags. Deferred 351 records that class of defect and this
is the check for it. The unwrapping of the previous pass is complete and broke nothing the
build can see.

## Introduced by the correction pass

1. `user_guide_installation.rst`: "The other fourteen … splitting the path at its
   `/holdings/`" is false for `crlf` and `shelf_consistency_check`. **The pre-correction
   text carved them out and the correction deleted the carve-out**, which is the sharpest
   single example of the ratio above. It also contradicts two other chapters.
2. `user_guide_maintenance_tools.rst`: "the two driver families" covers 8 of 10. The two
   index shelf programs are a third member of the traceback family. Round 1 found this
   independently.
3. `user_guide_maintenance_tools.rst`: the deep-file message is
   `Invalid file for an infoshelf:` for the two info shelf programs, not
   `Invalid file for checksumming:`. Round 1 found this independently.
4. `user_guide_maintenance_tools.rst`: `--initialize` on a selection. `pdschecksums`
   raises `ValueError`; `pdsinfoshelf` raises
   `AttributeError: 'NoneType' object has no attribute 'error'` at `pdsinfoshelf.py:735`
   — an unintended crash rather than a refusal. Round 1 found this independently.
   The finishing pass measured the two PDS4 halves as well and found this account still
   incomplete; see round 5 and deferred 354.
5. `user_guide_pdsdependency.rst`: the `general` breakdown accounts for 18 of 28. Round 2
   found this independently. The real shape is five rules over each of five types, plus
   three link shelf rules.
6. `user_guide_pdsdependency.rst`: `obsindex` holds neither index shelves nor cumulative
   tables. It has **one** rule, requiring `metadata/\1/\2/\2_obsindex.tab`. Index shelf
   substitutions live in the `metadata` suite and the four `cumindex*`; cumulative rules
   only in `cumindex*`.
7. `user_guide_pdsdependency.rst`: "the five volume types" contradicts
   `user_guide_concepts.rst`, which says seven. It should read "five of the seven".
8. `user_guide_pdsindexshelf.rst`: the `Backup file skipped:` line was said to carry an
   absolute path, because the skip happens before `logger.replace_root()`. Round 3 raised
   the same thing. **Both were rejected on measurement by the finishing pass** — the path
   is absolute only for a run's first target, and the published example's backup is not
   one. See round 3's item 1 and deferred 356.
9. `user_guide_pds4archives.rst`: "each of the five tasks" handles a missing archive
   differently. There are three behaviors, as the page's own next two sentences show.
10. `user_guide_shell_scripts.rst`: "the first group" of six does not exist. Line 9 says
    three groups, the sections split 1/3/2, and the table is one ungrouped list. The
    underlying facts about the scripts are right.
11. Three prose lines now exceed about 90 columns where the first draft had none:
    `pdsindexshelf` at 155, `show_opus_products` at 110, `pds4archives` at 101.
12. `user_guide_maintenance_tools.rst`: the severity table is presented as exhaustive and
    omits `header` (severity 20) and `hidden` (severity 1). Since `HEADER` *is* a
    registered level name, "`HEADER` and `SUMMARY` are not severities at all" overstates;
    only `SUMMARY` is a text tag. Round 5 later found the corrected table still short of
    the two aliases.

## Survived the correction pass

* **A.** `user_guide_appendix_file_formats.rst` still said modification times are
  "compared as a string". Both info shelf pages had been fixed; the appendix — the
  canonical statement of the format — was not. It wraps across two lines, which is why a
  plain grep for the phrase missed it.
* **B.** `user_guide_installation.rst` still said "link shelves: volumes, calibrated,
  metadata only", while `user_guide_pdslinkshelf.rst` now said nothing restricts it.
  Verified against the program: `_linkshelf-previews` builds.
* **C.** "a single file inside a volume/bundle" survived on the two info shelf pages after
  being narrowed on the three others, and neither mentions the `--initialize` refusal.
  Round 1 found this independently.
* **D.** `user_guide_pdsdependency.rst`: "the last six are not runnable". The original
  said "Two"; the correction **tripled the error instead of fixing it**. Rounds 2 and 3
  found the same thing.
* **E.** `user_guide_pdsindexshelf.rst` says `re_validate` re-runs four validations;
  `user_guide_re_validate.rst` says five. Pre-existing. Round 1 found this independently.
* **F.** ***A real bug in `critiques/pr-32/check_cli_coverage.py`.*** At line 308,
  `names = '/'.join(strings)` in the third comparison **shadows the program-name set**
  built at line 260 and read at 276 and 279 on every later iteration. The first time a
  substantive default goes unstated, every later program is checked against a corrupted
  `all_progs`, and `documented_flags()` starts matching single characters as program
  names. Present since the first commit, latent on a clean run. **Fixed in `824c01f`**;
  see the validation record for what it was hiding.
* **G.** `user_guide_show_opus_products.rst` still wrote ``argparse`` where three other
  pages use `:mod:`.

## What it could not verify

* **That all fourteen programs work with both variables unset in every circumstance.**
  `_path_utils.abspath_for_logical_path()` does read `cls._HOLDINGS_ENV`, and
  `_properties.internal_link_info` reaches it for a shelved link whose internal path
  begins `../../`. No cross-volume label link in the sandbox exercises it. The claim was
  softened to what was actually proved.
* `pds4indexshelf`'s "no label at all" failure, whose bundle set is absent from the
  sandbox.
* Exact counts in the `pdsdependency` and `re_validate` examples; the sandbox had drifted,
  which round 3 diagnosed.

## Not a defect, but noted

`repair()` compares info dicts with `==` — exact modification-time string equality — and
not with `modtimes_agree()`. So a sub-second difference `--validate` forgives is still
enough to make `--repair` rewrite. The appendix now states both comparisons.

## Disposition

All 12 introduced and 6 of the 7 survivors were applied by the finishing pass; F was
already fixed at `824c01f`. Item 8 was rejected on measurement, with the evidence above.
