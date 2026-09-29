# PR-30b round 2 — the archive, link shelf and index shelf pairs, and the repair table

Reviewer: a fresh subagent with no context from this session or from any other round.
Tree frozen at `5acbf85`; nothing under `src/` moved while it ran.

Surface: seven files, 28 functions, 59 documented parameters, plus a 141-entry data table
whose module docstring makes eight counted claims.

**All eight of the counted claims about `linkshelf_repairs` held**, measured by importing
the table rather than by reading it: 141 entries, 77 dictionary translators holding 267
entries between them of which 24 map to the empty string, 64 regular-expression
translators holding 90, two entries carrying `re.I`, and a comprehension over
`range(0, 50)`. So did every one of the 27 `Raises:` entries in the slice. What failed was
prose about ordering, about what a lookup reaches, and about which of two twins does what.

## What it disproved: 11 claims

1. **"``holdings_sentinel``, which only the other two families read"**, in both archive
   module docstrings. Its two readers serve **three** families: the checksum and info shelf
   tools through `_shelf_common.resolve_holdings_paths()`, and the link shelf tools through
   `_linkshelf_common.locate_nonlocal_link()`. `_common.py`'s own `ToolSpec` docstring,
   which PR-30a wrote and this PR does not touch, states it correctly, so this was a claim
   contradicted by the module it was about.
2. **"That is the whole of the difference between this tool and the PDS3 one"**, in
   `pds4archives`'s module docstring, contradicted 65 lines below by this PR's own sentence
   about the missing-archive check, and by seven other differences the reviewer tabulated,
   including that the PDS4 task functions take no `limits` at all.
3. **"``validate()``, ``repair()`` and ``update()`` iterate over an empty list and report
   nothing"**, in the same docstring. Both `validate()` and `repair()` call
   `load_directory_info()` **before** the loop, so a target with no archives still costs a
   full recursive walk and a log line per file. Demonstrated on a real no-archive target.
4. **"this module is the shortest of the ten"**, in `pds4indexshelf`. Its PDS3 twin is
   shorter under every measure. The identical sentence in the PDS3 module was true, which
   is what let it survive being written twice.
5. **"the same field decides how a path is split for four of the other five PDS4 tools"**,
   in `pds4indexshelf`. There are four others, not five; of those, two split on it, one
   stops an upward search at it, and one does not read it.
6. **"A name that matches nothing local is put through the repair table first"**, in
   `pdslinkshelf.generate_links`. The repair loop runs over every link immediately after
   the file is read and **before** any local lookup, so a repair overrides a name that does
   match a local file. Demonstrated on a synthetic volume: a `GEO.FMT` sitting beside its
   label resolved to `NAV_DATA/GEO.FMT`. The PDS4 twin stated the order correctly, so this
   is the cross-version defect inverted.
7. **"the label's own name matches the file's up to the extension"** as a ground on its
   own, in both link shelf scans. Both crediting paths additionally require the label to
   **name** the file. Demonstrated: a `FOO.LBL` beside a `FOO.IMG` it does not mention
   produces "Label FOO.LBL does not point to file" and "Label is missing", not a credit.
8. **"before any name-matching guess is tried"**, about the `<file_name>` credit in
   `pds4linkshelf`. The name-matching credit is settled in the earlier pass and the later
   pass skips any file already credited. Demonstrated with two labels both naming the same
   file, only one matching by name: the name match won.
9. **"a link that carried a directory and matched no entry at all is shelved under its
   basename"**, in `linkshelf_repairs`. `LinkInfo.remove_path()` is reachable only from
   inside the per-repair loop, which does not run when the **file** matched no entry.
   Demonstrated with two files in one volume, one matching a pattern and one not.
10. **"the two entries that match a lower-case basename"**, in `linkshelf_repairs`. The
    count of two is right; one of the two spells its basename in upper case. What
    distinguishes them is that they must match **either** case.
11. **"every link found is looked up in it"**, about the empty PDS4 repair table, in
    `pds4linkshelf` and again in `linkshelf_repairs`. `REPAIRS.all()` returns an empty list
    for an empty translator, so the per-link loop never runs and no link is looked up at
    all. One lookup happens, per file.

## What it classed as misleading: 7

The two with the widest consequences:

* **`pds4archives.archive_lskip`'s "The two agree wherever an archive packages a bundle
  directory sitting directly under the bundle set"**. Literally true, and it steps around a
  live failure: of the three archive shapes the installed rule modules define, only **one**
  satisfies the condition. For the other two the reviewer wrote an archive with
  `initialize()` and validated it immediately, and got 8 and 11 errors on trees of two and
  a handful of files. "Wherever" reads as "normally"; it is one case in three.
* **`pdsarchives`'s "the ``{'info': 100}`` entries in the shared default limits cap this
  tool's per-file lines"**. Three of the four shared limit dictionaries are `{'info': 100}`
  and the fourth, the one governing the archive write, is `{'info': -1}`, which pdslogger
  documents as no limit. The largest volume of per-file lines is the one explicitly
  uncapped.

Also: `re_validate` calls `pdsarchives.validate()` without assigning the result, so the
bool no caller reads is dead rather than merely ignored; `Pds3File.log_path_for_volume` is
a separate method forwarding to `log_path_for_bundle` rather than the same method; the
JNOJIR group is 50 generated entries plus three written out; and neither link shelf module
docstring mentioned that their `handler_factories` differ, where the archive and index
shelf pairs both call the analogous difference out.

## What it could not verify: 7

Two are unfalsifiable from the tree and are now written as description rather than as
claim: that a maintainer adds a repair entry when a run reports an unresolvable link, and
that a difference is "structural rather than historical". Three needed a fixture the
reviewer would not build against shared holdings -- an unwritable archives tree, an
unreadable directory, and a `--help` rendered in a subprocess. One is about the ordering
rule of the repair table's groups, which is not written down anywhere; the docstring now
says "roughly the alphabetical order" rather than asserting a rule.

## Code defects, not documentation defects: 7

Recorded in `critiques/deferred-observations.md`, entries 302 to 305 and 309; entries 2 and
93/129 already carried two of them. The one the reviewer ranked highest is new and is the
largest thing either round found in the code:

* **`pds4archives` writes archives its own `validate()` cannot match, for two of the three
  archive shapes installed in this repository.** `write_archive()` names a member by the
  basename of its packaged directory and the path below it, while `read_archive_info()`
  rebuilds an absolute path with the bundle set's prefix. The two agree only where the
  packaged directory is a bundle directory directly under the bundle set. Measured on all
  three: `cassini_vims` cruise round-trips; the `cassini_uvis_solarocc_beckerjarmak2023`
  set, whose table packages the bundle set itself, gives 8 errors on a two-file tree; and
  `cassini_vims` saturn, whose table packages collections two levels down, gives 11.

## What the reviewer measured

About 45 relationship claims, 20 cross-version claims, 27 `Raises:` entries of which six
were constructed and run, and 22 counts and boundaries including all eight of the repair
table's. All 28 function docstrings, all 59 documented parameters and all seven module
docstrings were read. 11 disproved, 7 misleading, 7 unverified.
