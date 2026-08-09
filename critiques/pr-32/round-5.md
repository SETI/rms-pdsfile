# PR-32 round 5 — the second read of the correction pass

Plan section 6.6 caps a PR at four rounds. This round exceeds that cap deliberately, and
the justification is a measurement rather than a preference.

## Why a fifth round

Rounds 1–4 reported 47 findings, 36 of them distinct. Applying them meant rewriting a
large fraction of the guide's factual sentences: commit `4108fd4` is 18 files, 303 lines
added and 123 removed, of which 17 files, 298 and 121 are the guide itself. That is a new
surface, written in one pass, that no reviewer had read.

The rate at which such a pass introduces defects is not a guess here. **Round 4 attributed
12 of its 19 findings to the correction pass it was reading**, and round 1, working
independently on different chapters, confirmed four of those twelve. Across the eight
prior PRs of this phase the second-read ratio has been 11/23, 10/21, 34/57, 15/22, 10/13,
15/24, 9/10 and now 12/19. Opening the PR on an unread 34-correction pass would have
shipped the one defect this PR has already measured twice.

## Method

The tree was frozen at `4108fd4`, the correction commit, and a fresh no-context reviewer
was given that commit as its entire scope, with **each of its 45 changed passages named by
hand** and told to check every one rather than sample. It had the holdings environment, a
writable sandbox, and instructions to run rather than reason wherever running was
possible.

## Result

| | |
|---|---:|
| passages named | 45 |
| passages checked | 45 |
| defects | 16 |
| lower-confidence or minor findings | 4 |
| **share of findings inside the corrections** | **16 of 16** |

Every finding was in the corrections, which is what naming the scope by hand was for. The
reviewer raised four items outside the diff and kept them separate, as asked.

## The two that matter most

Both are the same failure: **a claim generalized from a single measurement.**

1. **An unusable path was said to split the ten maintenance programs by whether the path
   exists.** It splits them by *where the path is*. The correction had been written from
   one measurement, of a nonexistent path *inside* a holdings tree. Measured across all
   ten and both cases: outside any holdings tree, the checksum and info shelf programs
   print `Not a holdings subdirectory:` and the other six give a `ValueError` traceback;
   inside a holdings tree but nonexistent, the sides swap — the other six print
   `No such file or directory:` and the checksum and info shelf programs give an `OSError`
   traceback. The correction's own worked example, `pdsarchives --validate
   /no/such/volume`, illustrates a case its surrounding prose then described backwards.
2. **`--quiet` was said to leave the run's own opening and closing lines on the
   terminal.** It does, but only with no log root configured. Those lines survive as
   `pdslogger`'s fallback for a record with no handler anywhere in its ancestry; `--log`
   or `PDS_LOG_ROOT` attaches a handler at that same outermost level and the fallback
   stops firing. Measured: 6 lines with no log root, 0 with one, by either route. Deferred
   355 records it.

## The other fourteen

3. "That is every registered level name" omits the two aliases, `WARN` for `WARNING` and
   `FATAL` for `CRITICAL`, which `pdslogger` registers on the same footing.
4. The `SUMMARY` explanation was imprecise: those lines are emitted at `HEADER`'s severity
   of 20, a constant, not at "the severity its `HEADER` was opened with". The consequence
   worth stating is that a summary line counting errors is itself a severity-20 record.
5. `user_guide_installation.rst` said thirteen of the other fourteen programs work in a
   holdings tree. It is twelve: the thirteen counts `show_opus_products`, which is not one
   of the fourteen. An arithmetic error inside a correction whose point was a count.
6. The same paragraph's two behavior groups cover 11 of the 13. `re_validate` and
   `show_opus_products` were unaccounted for. Measured: `re_validate` ends in the
   `ValueError` traceback like the other seven, and **`show_opus_products` neither refuses
   nor crashes** — it prints a `WARNING:` line, carries on, and exits 0. The reviewer put
   both in the traceback group; the finishing pass measured `show_opus_products` and found
   it needs a group of its own.
7. `user_guide_pds4archives.rst`: "four of the five say nothing at all about the absence".
   Three do. The page's own next sentences name the two that speak.
8. The appendix's new declaration about its shelf excerpts is wrong about one of the
   three: the link shelf excerpt is entries 2 and 6 rather than the first two, chosen to
   show one of each value shape, and its second column was un-padded as well as its first.
9. `user_guide_pdschecksums.rst` attributed `12 INFO` to the nine `MD5=` lines. It is
   nine `MD5=` plus three other `INFO` lines visible in the same example. Measured: 12
   when the destination directory has to be created, 11 when it already exists.
10. `user_guide_shell_scripts.rst`: "Either way that directory is where a run of one has
    to start". Two of the twelve depend on the working directory —
    `copy_all_except_metadata.sh` and `update_holdings_for_new_metadata.sh` — and the
    other ten take absolute paths and run from anywhere.
11. `user_guide_crlf.rst` told the reader to re-create the files to run any example on its
    own, which reproduces the first run and not the other two.
12. `user_guide_pdsarchives.rst`: "the gzip layer fails before the tar layer is reached at
    all" is wrong about the order. The traceback shows `tarfile.open()` succeeding and the
    member walk under way when gzip runs out of data. The exception types and texts are
    right.
13. `user_guide_concepts.rst`: "one file per unit, per unit set or per table" is true of
    the archive and checksum trees and false of the three shelf families, which write two
    files, a `.pickle` and a `.py`.
14. The same table's column was headed "Category" while four of its rows name shelf trees,
    which the chapter has just defined out of that word — `Pds3File.CATEGORY_LIST` holds
    25 names and no shelf tree is among them.
15. The same section's closing rule of thumb, "count the directory levels", does not
    discriminate: a `documents` file and a checksum file sit at the same depth, and so do
    a metadata table and its index shelf. The first component is what tells you.
16. `user_guide_installation.rst`: "The three link shelf directories above" sits directly
    under the PDS4 layout block, which lists one.

## Minor

* The library path that reads a holdings root is reached from more than the one operation
  named.
* `re_validate` tests `endswith('/holdings')`, so a directory named `pdsholdings` is
  rejected too — worth saying, since the prose said "does not end in `holdings`".
* The three `cat` lines in `pdsdependency`'s "Steps required" need the cumulative volume's
  directory to exist for the redirect to land.
* `checksums-archives-volumes/COUVIS_0xxx_md5.txt` was offered as an example and no such
  file exists. `COCIRS_0xxx_md5.txt` does, in the shared tree.

## Found sound

The reviewer found 34 of the 45 passages sound, three of them only in part -- passages
27, 32 and 35 each carried one of the defects above alongside claims that held. Most were
confirmed by measurement rather than by reading, among them: `general`'s 28 rules and `obsindex`'s single rule by introspecting
`DEPENDENCY_SUITES`; all four refusal messages and their exit statuses; all four
`--initialize`-with-selection cases with the product present and absent; the ten-program
split on a path outside any holdings tree; `--help` on all fifteen; `re_validate`'s three
metavars, its three batch rejections and its five nested logger names; the backup-skip
path form in both positions; the 192 tar members and the single survivor of the doubling,
identified by name; the three capped phases and their `{'info': 100}` limits;
`MODTIME_TOLERANCE` and `repair()`'s exact-equality comparison; and the coverage checker's
own pass line.

## What it could not verify

* That a complete published `COUVIS_0001` carries an `INDEX.LBL`. Both available trees
  carry the same trimmed `INDEX/`, so the artifact is confirmed and the counterfactual is
  not. Everything else in that note was verified by running `pdslinkshelf --validate` and
  reading `HDAC1999_007_16_33.LBL`, which carries
  `^TIME_SERIES = "HDAC1999_007_16_31.DAT"`.
* Any command in the guide that reaches the environment-reading library path — which is
  what the paragraph in question itself claims.

## Disposition

All 16 defects and all 4 minor findings were applied, at `bf3e9b4`. Finding 6 was applied
in a different form than the reviewer proposed, because measuring `show_opus_products`
directly disagreed with its report: it does not fail on such a path at all. That is the
second finding of this PR corrected on measurement rather than accepted on report; round
3's item 1 is the first.
