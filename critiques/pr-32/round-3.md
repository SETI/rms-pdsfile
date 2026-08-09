# PR-32 round 3 — every published command, run

Fresh no-context reviewer, given the holdings environment and told to execute the guide's
examples and report anything that did not behave as printed. Tree frozen at `5cefb3d`;
`git status --porcelain` empty before and after. The reviewer worked in its own copy of
the sandbox and confirmed it left the shared one untouched.

## Result

| | |
|---|---:|
| command lines published | 56 (42 `console`, 14 `bash`) |
| run | 51 |
| not run | 5 |
| **reproduced their published output** | **51 of 51 runnable** |
| failed to run at all | **0** |
| defects in the pages themselves | 5 |

The five not run are the three `pip`/`pipx` install lines, a duplicate of one of them, and
`pdsdata-sync-volset.sh`, which is out of scope and assumes macOS.

## The state each example assumes

Eleven `--initialize` examples reported "already exists" against the sandbox as handed
over, because that sandbox is the *post-capture* state: the products those examples build
are already there. **After removing the one product each example builds, all eleven
reproduced their published output exactly**, counts included — 12 INFO / 9 DEBUG for
`pdschecksums`, 19 INFO and 16 `File archived:` for `pdsarchives`, 185/2/184 for
`pds4checksums`, 194 NORMAL for `pds4archives` on the bundle set, `Rows tabulated: 2930`
for `pdsindexshelf`, and so on.

Two further examples, `pdsdependency` and `re_validate`, differed by exactly two messages
each. The reviewer found the cause rather than guessing it: the sandbox's
`COUVIS_0001_md5.txt` carries mtime 01:52:34, eight minutes after the documented run at
01:44:24, because a `pdschecksums --reinitialize` was run against it afterwards — the
versioned copy that run left behind is still in the log tree, and the reviewer diffed it
against the shipped manifest and found them **byte-identical**, only the mtime changed.
That makes the info shelf look stale. Rebuilt in the documented order, both examples
reproduced exactly: `10 ERROR / 30 INFO` and 19 steps for `pdsdependency`,
`2 CRITICAL / 63 ERROR / 159 of 174 / 19 of 33` for `re_validate`.

The reinitialize in question was the executor's own, run against the shared sandbox while
an earlier review was in flight. Section 11 of the validation record owns that.

## Ordering, correctly discounted

The reviewer was told the guide claims per-file line order follows filesystem directory
order and is unstable, and was asked not to count that as a defect. It found eight such
differences and counted none of them, which is the check on that claim: the claim holds.

## The placeholder question

**No published example was captured against a zero-byte placeholder.** The reviewer looked
for the signature specifically: no `tarfile.ReadError`, no checksum run over zero files,
no zero-length archive or manifest. `COUVIS_0001.tar.gz` is 55,543 bytes over 16 members;
the PDS4 archive is 80,800,164 bytes over 192, and `tar tzf` lists all 192, which
independently confirms the appendix's member-naming claim. The PDS3 manifest covers 9
files and the PDS4 one 184.

Two zero-byte files in the *published data* do reach published output, and both are
recorded rather than papered over:

* `volumes/COUVIS_0xxx/COUVIS_0001/INDEX/INDEX.TAB` is zero bytes and its directory holds
  no `INDEX.LBL`. It appears once, as `pdslinkshelf --validate`'s third error. The guide
  attributed that to the published volume's own link problems; the shared testing tree
  shows the same shape, so the attribution cannot be supported from either tree and the
  page no longer makes it.
* Four preview PNGs are zero bytes. They appear as products in the `show_opus_products`
  tables and as `Confirmed:` lines in `pdsdependency`. Neither program opens them, so the
  output is what real files would give.

## Defects in the pages

1. **`user_guide_pdsindexshelf.rst`** published a `Backup file skipped:` line carrying a
   logical path. The program logs `pdsf.abspath`, so the line carries an absolute path and
   the guide's own substitution rule makes it `$PDS3_HOLDINGS_DIR/metadata/...`. The line
   was hand-written rather than copied from a run — the only such line left in the guide.
2. **`user_guide_pdsdependency.rst`**: "the last six are not runnable as they stand". The
   reviewer ran one of the three `cat` lines verbatim; it exited 0 and wrote a
   156,701,895-byte table. Only the three `<LABEL>` lines are not runnable. Introduced by
   the correction pass, and contradicted by the page's own next sentence.
3. **`user_guide_crlf.rst`**: "Each example below starts from that state" is false for the
   third example, which is published in its post-`--repair` state. Introduced by the
   correction pass.
4. **The reproducibility sentence** in `user_guide_installation.rst` is true of the runs
   but cannot be reproduced from the sandbox as it stands, for the mtime reason above.
5. Cosmetic: the appendix's shelf snippets use narrower key-column padding than the real
   files. Every value is exact.

## What it could not verify

The three `pip`/`pipx` lines, whose effect it checked another way (`tabulate` imports and
`show_opus_products` runs). The first of `pds4indexshelf`'s two documented failures, whose
bundle set is not in the sandbox — the executor's logs for it survive in the log tree, so
it was run, against a tree the sandbox does not carry. And "a single top-level file of a
volume" as a target, because no volume in the tree has one; it used a volume's archive
file, which the same rule covers, and got the documented
`ValueError: File selection is disallowed for task "initialize"`.
