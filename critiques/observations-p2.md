# Observations — before the merge (P2)

Open observations to settle before the merge to `main`: cheap fixes, decisions that get harder once the branch lands, and risks the merge would otherwise lock in.

## Correctness

### 3000. `filename_keylen` is the only slot-filling lazy property that never writes its filled object…

**`filename_keylen` is the only slot-filling lazy property that never writes
its filled object back to the cache.** `src/pdsfile/_properties.py` — 40 of
the mixin's 64 properties fill an `_X_filled` slot, and 39 of those then call
`self._recache()` so the shared cache keeps the filled object.
`filename_keylen` assigns `self._filename_keylen_filled` and returns. The
consequence is the same one PR-15's bug 1 had for `html_path`: every object
re-fetched from the cache recomputes the value, because the fill never
reaches the cached copy.

It is **not** the same defect — `html_path`'s was `self._recache` written
without its parentheses, a call that silently did nothing, whereas here there
is no call at all, which may well be deliberate for a value this cheap
(`FILENAME_KEYLEN.first(self.basename)`, a translator lookup). Deciding that
needs the same treatment PR-15's bugs got: a regression test pinning the
intended behavior first, then the change. PR-22 may not act on it — the code
is byte-identical through the move, its gate is the pass/fail set, and adding
a test id is movement beyond the ten the a since-resolved observation check required.
**Owner: unassigned (a future bug-fix PR, with a regression test).**

### 3001. `pds4archives` writes archives it cannot read back

**`pds4archives` cannot round-trip.** `write_archive()` adds members under
`arcname=<bundle-set basename>` (`pds4archives.py:238-241`) while
`read_archive_info()` rebuilds each member path with the prefix that already
ends at the bundle set (`pds4archives.py:126-135`, via
`dirpath_and_prefix_for_archive`). Every member comes back doubled
(`bundles/<bs>/<bs>/…`), so `--validate` fails immediately after a successful
`--initialize`. The complete holdings set's `archives-bundles/<bs>/` directory
is empty, i.e. this has never round-tripped in production either.
Pinned by `test_pds4_archives.test_validate_cannot_round_trip`. **Owner: PR-25.**

**`pds4archives` writes archives its own `validate()` cannot match, for two of the
three archive shapes installed in this repository.** `write_archive()` gives each
member the basename of its packaged directory and the path below it, while
`read_archive_info()` rebuilds an absolute path by putting the **bundle set's** prefix
in front of that member name. The two agree only where the packaged directory is a
bundle directory sitting directly under the bundle set. Measured by writing an archive
with `initialize()` and validating it immediately, on all three shapes the rule modules
define: `cassini_vims` cruise, whose `ARCHIVE_DIRS` packages a bundle directory, round
trips; `cassini_uvis_solarocc_beckerjarmak2023`, whose table packages the bundle set
itself, gives 8 errors on a two-file tree; and `cassini_vims` saturn, whose table
packages collections two levels down, gives 11, the bundle name being dropped from
every rebuilt path. Round 4 enumerated the installed tables rather than sampling them:
of the **seven**, one round trips. `cassini_vims`'s cruise rule packages a bundle
directory; `uranus_occs_earthbased` and `cassini_uvis_solarocc_beckerjarmak2023`
package the bundle set itself; and `cassini_iss`, `cassini_vims` (saturn),
`cassini_iss_spokes_hedman_hamilton_2024` and
`cassini_iss_fring_mosaics_rsfrench2025` package collections two levels down. Round 4
also reproduced it end to end on a six-file copy of the uvis set: 18 errors, 9 from
each side. a since-resolved observation already records that the pds4 archive round trip has
never worked in production; this is the mechanism, measured, and it is a property of
the pair of rules rather than of either function alone.
**Owner: a later maintenance-tool PR, together with a since-resolved observation.**

### 3002. `pdsinfoshelf --initialize` crashes on a file selection instead of refusing

**`pdsinfoshelf --initialize` on a file inside a volume ends in `AttributeError`.**
`initialize()` resolves its logger only inside the branch that finds an existing
shelf, so on the path that reaches the selection check the logger is still whatever
the caller passed, and `_shelf_common.run_selection_main()` calls a task as
`tasks[task](pdsdir, selection)` and passes none. The
`logger.error('File selection is disallowed for task "initialize"', selection)` call
is then made on None. Demonstrated against a stub: the pds3 tool raises
`AttributeError: 'NoneType' object has no attribute 'error'` and `pds4infoshelf` logs
the error and returns, because it resolves its logger before either test. The driver
reaches this for the `initialize` task alone, since it demotes `reinitialize` on a
selection to `update`. The fix is one line, hoisting the `logger = logger or …` above
the first test as the pds4 half already does; it is a behavior change on a frozen
surface and this PR documents it rather than making it.
**Owner: a later maintenance-tool PR.**

**`pdsinfoshelf --initialize` with a file selection crashes instead of refusing, and
its PDS4 twin does not.** `initialize()` in `holdings_maintenance/pds3/pdsinfoshelf.py`
binds its logger inside the `if os.path.exists(info_path)` branch, so a run that
reaches the `if selection:` refusal below it with no existing shelf still has
`logger` set to `None`. The driver calls the task functions without passing a
logger, so that is the ordinary case. Measured in a sandbox, with the shelf removed
and one top-level file named:
`AttributeError: 'NoneType' object has no attribute 'error'`, raised at the
`if selection:` refusal inside that module's `initialize()`, exit 1, with the
intended message `File selection is disallowed for task "initialize"` never printed.
`pds4infoshelf.py` binds the same logger unconditionally at the top of its own
`initialize()` and logs the message properly, exiting 1; both checksum programs
raise `ValueError` carrying the text. So one of the four is wrong and the fix is one
line, moving the binding above the first check. The guide documents the crash.
**Owner: whoever next touches `pdsinfoshelf`.**

### 3003. `prefix_mapping` is a `set`, so four derived structures are built in an order that depends on…

**`prefix_mapping` is a `set`, so four derived structures are built in an order that
depends on `PYTHONHASHSEED`.** `opus_id_list`, `opus_id_to_primary_filespec_list`,
`opus_id_to_subclass_set` and the class's `volset_list` all iterate it. Round 4 could
not make it change an answer -- resolving all 399 synthetic reverse OPUS IDs under two
seeds gives byte-identical output, because the emission order within one entry is fixed
and the only duplicate prefixes are inside a single entry -- so this is recorded as a
hazard rather than a defect. A `TranslatorByRegex` returns its first match, so an order
that varies is an order that could one day matter. Owner: whoever next touches
`uranus_occs_earthbased.py`.

### 3004. `shelf_consistency_check` targets a legacy holdings layout

**`shelf_consistency_check` targets a legacy holdings layout.** It walks for
`shelves/<info|links|index>/…`, but current holdings keep shelves in
`_infoshelf-volumes/`, `_linkshelf-volumes/` and `_indexshelf-metadata/`, none
of which contain the substring `shelves`. Run against a modern tree with real,
valid shelves it reports "Tests performed: 0, Errors found: 0". Its
`error += 1` / `errors` typo (already on PR-15's list, fixed in PR-28) is only
reachable through the legacy layout. Both are pinned in
`test_shelf_consistency_check.py`. This entry named **PR-28**, which gives this
tool a `main()`, as where the layout question had to be answered.

**PR-28 fixed the typo and left the layout question open.** The two are not the
same size: the typo is one identifier with a regression test, and teaching the
walk about `_infoshelf-volumes/` and its siblings is a rewrite of what the tool
looks for, on a tool nothing in this repository or in the sync scripts currently
runs. Making that change inside a PR whose subject is three `main()` functions
would have put the interesting decision — what a modern-layout run should
*report* — under a heading nobody would look for it under.
**Owner: open — the layout question needs a PR of its own, and no phase owns
it.**

### 3005. `show_opus_products` dies with an `IndexError` on real holdings paths

**`show_opus_products` dies with an `IndexError` on real holdings paths.**
`golden_opus_types = [prod_category[2] for prod_category, _ in opus_prod.items()]`
assumes every key of `opus_products()` is a five-element tuple; two more places
assume the same. Four paths in `/seti/opus/pdsdata/holdings` return a dictionary
keyed by the empty string, carrying the volume set's `documents/` products:
`volumes/VG_20xx/VG_2001/JUPITER/CALIB/VG1PREJT.LBL` and three files under
`volumes/VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1/`. Found by round 2,
which scanned 6,674 files across every volume of the test holdings to establish that
it is four and not more, and reproduced here. The tool prints a traceback and
returns nothing. **Two owners: the tool should not subscript an unchecked key, and
separately `opus_products()` producing an empty-string key at all belongs to
`_opus.py` and the `VG_20xx`/`VGIRIS_xxxx` rule modules.**

### 3006. `update` cannot see a deletion, and never refreshes a directory entry

**`update` cannot see a deletion, in all four checksum and info shelf tools.**
`generate_checksums()` rebuilds its result from `old_keys = [p[0] for p in oldpairs]`,
all of them, and `generate_infodict()` starts from `old_infodict.copy()`, so an entry
for a file that is no longer on disk survives every update. Because it survives, the
comparison the task then makes still holds and the run reports "update canceled": a
deletion is not merely un-removed, it is invisible. Measured in both pairs with an
`oldpairs`/`old_infodict` naming a file that does not exist. Only `reinitialize` or
`repair` clears it. The link shelf tools do drop such an entry, because
`generate_links()` assembles its result from the paths the walk found; that asymmetry
between the three families is what made this hard to see. Found by round 1.
**Owner: a later maintenance-tool PR.**

**The info shelf `update` never refreshes a directory entry.** `get_info()` recomputes
a directory's byte count, child count and date from the children the walk found, and
the merge that follows writes a key only `if key not in merged`, so a directory
already in the shelf keeps the entry it was shelved with and the recomputation is
discarded. Measured with a deliberately stale directory entry: the fresh walk computed
one value and the returned dictionary carried the old one. A unit that has gained or
lost a file therefore keeps a wrong child count and byte total for every ancestor
directory until a `reinitialize` or a `repair`, and `validate` reports those as "Child
count mismatch" and "File size mismatch", so the two tasks disagree about the same
shelf. Found by round 1.
**Owner: a later maintenance-tool PR.**

### 3007. Four defects in `crlf`

**`crlf.test_crlf` raises `ZeroDivisionError` on a zero-byte file.** The
non-ASCII fraction divides by the decoded length without guarding an empty
file, so `crlf --repair` over a tree containing one dies instead of reporting
it. Pinned by
`test_crlf.TestArgumentValidation.test_an_empty_file_raises_zerodivisionerror`.
This entry named **PR-28**, which gives `crlf` a `main()`, as where deciding
what an empty file should classify as ('OK'? 'BINARY'?) belonged.

**PR-28 preserved it.** The decision is a behaviour change on a frozen surface
with no obviously right answer — 'OK' says an empty file has no bad
terminators, 'BINARY' says it is not text, and a third reading is that the
tool should report it and move on — and the Phase-6 rule lets output move only
where keeping it would force duplication or a flag, which this does not. The
pin is unchanged and inverting it is still what a fix has to do.
**Owner: open — one of three answers, and no phase owns the choice.**

**`crlf` prints no summary at all when it repairs more than one file.** The
summary block reads `if repairs: if repairs == 1: print(f'{repairs}/{nfiles}
files repaired')`, so a run over three files that fixes two lists both
`REPAIRED` lines and then says nothing, where a run that fixes one says
`1/3 files repaired` and a run that fixes none says `2/3 files invalid`. The
`elif invalid` branch is unreachable whenever anything was repaired, so a run
that repairs one file and finds another invalid does not mention the invalid
one either.

Preserved, not fixed: the Phase-6 rule lets output text move only where keeping
it would force duplication or a flag, and keeping this forces neither. Pinned
as current behaviour by `test_two_repairs_print_no_summary_at_all` and by
transcript record `crlf/repair-two-of-three`, whose docstring says a fix has to
invert it.
**Owner: open.**

**`crlf` exits 0 whether or not it found anything.** Every transcript record
that reaches the end of `main()` exits 0, including the ones that print
`INVALID` for every file given. A caller that wants to know whether a tree is
clean has to parse stdout; `find … -exec crlf {} +` in a shell script cannot
branch on the result. `shelf_consistency_check` does return 1 on errors, and
did before this PR, so the two halves of what is nominally the same job report
differently. Preserved because an exit code is frozen and this one is
load-bearing in the other direction: a tool that started exiting 1 on an
invalid file would fail any pipeline that runs it over a tree expecting to read
the report.
**Owner: open.**

**`crlf` can no longer be given a path that begins with `-`, and `--` only
half-rescues it.** The tool took every argument literally before it had a
parser, so `crlf -dash.txt` checked that file; argparse reads a leading `-` as
an option, so it is now a usage error exiting 2. This is the only invocation
that worked at the base and does not work now — every other changed record is
an error path that changed shape.

The usual answer is the `--` separator, and under `parse_intermixed_args` it
works only when a plain positional comes first: `crlf ok.txt -- -dash.txt`
checks both, and `crlf -- --verbose` turns verbose *on* rather than checking a
file of that name. `parse_intermixed_args` parses the argv before the first
`--` with `parse_known_args` and re-parses the remainder, so a `--` in first
position leaves nothing in front of it and the remainder is read with the
optionals still live. Plain `parse_args` handles `--` correctly and rejects a
flag between two positionals; the two cannot both be had.

**And `--` in first position is not even stable across the versions this
package supports.** `crlf -- -dash.txt` exits 2 on Python 3.10 through 3.12
and exits 0, checking the file, from 3.13 — measured on 3.12.3 and 3.14.5 and
confirmed by CI's 3.13 leg, which is the only place it showed up: every local
run and all four adversarial review rounds used a single interpreter. The
tests assert only the two outcomes that hold everywhere (a bare leading-`-`
argument is a usage error; a path, a `--` and then the dashed file works), so
the suite does not pin one interpreter's answer to the third.

The trade was made toward the flags: `crlf a --verbose b` is a plausible
command line and a file named `-something` is not — `find` over both holdings
roots for `-*` returns nothing. Pinned by
`test_a_path_beginning_with_a_dash_needs_a_path_and_a_separator_before_it`,
which asserts both so a later switch to `parse_args` has to invert
them. `shelf_consistency_check` has the same property, pinned by
`test_a_shelf_root_beginning_with_a_dash_is_a_usage_error` and by transcript
record `shelf/dash-root`, where the base run walked the directory and reported
on it.
**Owner: open.**

### 3008. Four defects in the checksum generate-and-validate path

**A blank line in a checksum manifest ends the read with `IndexError`.**
`read_checksums()` parses by fixed offsets, so a short record yields an empty
`filepath` and an empty `basename`, and `if basename[0] == '.':` then subscripts an
empty string. Reproduced in both flavors with a manifest holding one blank line:
`IndexError: string index out of range`, logged through `exception()` and re-raised.
With a selection given the record is skipped by the basename test above it and the
read completes, so the failure depends on the task. `basename.startswith('.')` is the
one-character fix. Found by round 1.
**Owner: a later maintenance-tool PR.**

**`pdschecksums.generate_checksums()` returns an empty dict where its own contract is
a list.** The two paths where a selection matched no file, or more than one, return
`({}, latest_mtime)`; every other return is a list of pairs, and `pds4checksums`
returns `([], latest_mtime)` on the same two paths. Every caller tests the value for
truth alone, so nothing breaks today; a caller that iterated it would get keys rather
than pairs.
**Owner: a later maintenance-tool PR.**

**`pdschecksums.validate_pairs()` and `pdsinfoshelf.validate_infodict()` return from
their `finally` clause, so nothing raised inside them escapes.** The `except` above
each re-raises and the `return` in the `finally` discards it, including a
`KeyboardInterrupt`. `validate_pairs` then reports the flag as it stood, which for a
failure part way through a comparison that had so far agreed is True. Both are why
`B012` is on `pdschecksums.py`'s and `pdsinfoshelf.py`'s ruff ignore lists, and both
pds4 twins get it right -- `pds4checksums.validate_pairs` returns after the `try` and
`pds4infoshelf.validate_infodict` assigns in the `finally` and returns after it.
**Owner: a later maintenance-tool PR; the two ratchet codes retire with the fix.**

**`validate_pairs()` computes a merged limits dictionary and then passes the unmerged
one**, in both flavors: `merged_limits` is built from `VALIDATE_PAIRS_LIMITS` and the
argument, and `logger.open(…, limits=limits)` is what runs. `VALIDATE_PAIRS_LIMITS` is
empty, so the two are equal today and the defect is latent: an entry added to that
constant would have no effect.
**Owner: a later maintenance-tool PR.**

### 3009. Pre-existing pds4 uranus s-mode blackbox failures (full-holdings golden area, owner-deferred)

**Pre-existing pds4 uranus s-mode blackbox failures (full-holdings golden
area, owner-deferred).** A full `pytest tests --mode s` (i.e. including
`tests/pds4file/`) shows 5 failures in
`tests/pds4file/test_pds4file_blackbox.py` (uranus_occ, a
`KeyError`→`UnboundLocalError` around `pdsfile.py:4254/4265`). Verified
**identical on `origin/rewrite`** — pre-existing, not introduced by PR-08 —
and **not** exercised by the CI s-mode invocation, which is pds3-only
(`tests/pds3file tests/rules/pds3 --mode s`). Sits in the full-holdings
golden/shelf-reproducibility area the owner split out of PR-08. Owner:
the deferred additive-coverage / golden-reproducibility follow-up.

### 3010. The archive validator accepts a wrong member path in silence

**`validate_tuples()` enters its mismatch branch on a `dirpath` difference and
then reports nothing.** `_archives_common.py`: the branch is
`elif (dirpath, nbytes, modtime) != tardict[abspath]:`, and inside it only
`nbytes` and `modtime` are compared. If the archive-relative path is the only
thing that differs, the branch runs, logs no error, leaves `valid` True, and
`del`etes the entry — so an archive whose member path is wrong validates
clean. Moved verbatim in PR-26's split; present at base and head alike.
Not fixed here for the same reason as 116: the archive family is not this PR's
scope, and adding an error changes the archive tools' observable output.
**Owner: open.**

**`_archives_common.validate_tuples()` accepts an interior-path-only mismatch in
silence.** The comparison branches on the whole `(dirpath, nbytes, modtime)` triple
but then checks only the byte count and the modification time, so an entry that
agrees on absolute path, size and time is deleted from the tarfile dictionary and
`valid` stays True however far apart the two interior paths are. Measured: with
`dir_tuples=[('/a/x.txt', 'V/x.txt', 10, 100.0)]` and
`tar_tuples=[('/a/x.txt', 'TOTALLY/DIFFERENT.txt', 10, 100.0)]` the function returns
`True` and logs nothing. It cannot arise from the two archive tools as they stand,
since each list derives its interior path from its own absolute path by a fixed
rule, so this is a latent hole rather than a live bug. PR-30a documents the behavior
rather than the intent. **Owner: a later archive-tool PR.**

### 3011. The archive writers and the directory listing disagree about what to skip

**`archive_filter()` archives the backup files `load_directory_info()` skips.**
In `_archives_common.py`, `load_directory_info()` skips any name matching
`BACKUP_FILENAME` or containing `' copy'`, and `archive_filter()` — the filter
the archive writers add members through — does not. So a volume holding
`FOO_2021-01-01T00-00-00.LBL` or `BAR copy.TXT` has that file written into the
tarball but left out of the directory listing, and `validate_tuples()` then
reports it as `Missing from directory`.

Both functions moved verbatim into `_archives_common.py` in PR-26's split and
are otherwise untouched by it; the divergence is at PR-26's base and at its
head alike. Not fixed here because it changes what the archive tools *write*,
which is neither a PR-26 scope item nor an enumerated behavior change, and
because the right repair is not obvious: excluding them changes existing
archives' contents on the next `--repair`, while including them in the
directory listing changes what `pdschecksums` and `pdsinfoshelf` record.
**Owner: open.**

**`pdsarchives.read_archive_info()`'s "skip" comments do not skip.** The `.DS_Store`
and dot-underscore branches carry `# skip .DS_Store files` and
`# skip dot-underscore files` and neither has a `continue`, so both members are logged
as errors and then inventoried. The walk they are compared against does skip them, so
such a member is reported twice, once there and again as "Missing from directory".
Identical in `pds4archives`. The behavior is defensible and the comments are not.
**Owner: a later maintenance-tool PR.**

### 3012. The chained-run argv rewrite is broken in two ways

**The pds4 `--infoshelf` chain re-runs `pds4checksums`, not `pds4infoshelf`.**
Both checksums tools build the chained command by rewriting their own argv:
`[a.replace('pdschecksums', 'pdsinfoshelf') for a in sys.argv]`. The pds4 tool
carries that line **verbatim from its pds3 twin**, and `'pdschecksums'` is not
a substring of `'pds4checksums'` — `pds4c…` breaks the run of characters. So
no element is rewritten, `--infoshelf`/`-i` is stripped, and the child is the
same `pds4checksums` command over again with the chain flag removed:

```
'/venv/bin/pdschecksums'.replace('pdschecksums', 'pdsinfoshelf')
    -> '/venv/bin/pdsinfoshelf'          # pds3: the other tool
'/venv/bin/pds4checksums'.replace('pdschecksums', 'pdsinfoshelf')
    -> '/venv/bin/pds4checksums'         # pds4: itself
```

`pds4checksums --initialize --infoshelf <bundle>` therefore runs the checksum
task twice and never builds an info shelf; the second run's
"Checksum file already exists" error is what it reports.

Identical at PR-26's base and head. It was **not** fixed here: the plan
enumerates PR-26's behavior changes and this is not among them, and rewriting
the substitution changes what the pds4 chain *does* rather than how faithfully
it reports. The migration deliberately left both tools' substitution strings
alone. Whether the fix is `'pds4checksums'` → `'pds4infoshelf'` or dropping
argv[0] rewriting for an explicit console-script name is worth settling once
for both flavors, since argv[0] rewriting also assumes an installed console
script — `python -m …` puts a module file path there and the chain then
depends on that file's executable bit and shebang.
**Owner: open.**

**`pds4checksums --infoshelf` does not do nothing; it runs `pds4checksums` a second
time.** The chain rebuilds the command line by replacing the string `pdschecksums`
with `pdsinfoshelf` throughout `sys.argv` and dropping `--infoshelf`. No PDS4
command line carries that string -- the console script is `pds4checksums` and the
module path ends `pds4/pds4checksums.py` -- so the substitution changes nothing and
the subprocess is the same program running the same task over the same paths again.
The process exits with the second run's status.

Measured: `pds4checksums --validate --infoshelf <bundle>` printed **796 timestamped
log lines** against the **398** of the same command without the flag, with two
`|| HEADER |` lines, the second naming `pds4checksums --validate <bundle>`. No
`pds.validation.fileinfo` line appears anywhere in it. Under `--initialize` the
second run additionally reports `Checksum file already exists`, an error the first
run did not produce.

The cost is a doubled run rather than a wrong answer. **Owner: whoever fixes the
PDS4 chain**, which is the same substitution `pdschecksums` uses correctly.

**The chained-run substitution rewrites every argument, not just `argv[0]`.**
Both checksums tools build the chained command as
`[a.replace('pdschecksums', 'pdsinfoshelf') for a in sys.argv]`. The intent is
to name the other tool in `argv[0]`, but the comprehension rewrites the
substring wherever it appears — so `--log /var/logs/pdschecksums` becomes
`--log /var/logs/pdsinfoshelf`, and any holdings path containing the tool's
name is silently redirected. A log root named after the tool is the documented
layout: `--help` says logs are created inside the "pdschecksums" subdirectory
of each log root.

Present at PR-26's base and head alike; PR-26 changed how the command is
*executed* (`subprocess.run` on a list, an enumerated fix) but deliberately
left what is *substituted* alone, since narrowing it changes which directory a
chained run reads and writes. This is the same line as a since-resolved observation, so both
should be settled together: restricting the substitution to `argv[0]` fixes
this one, and naming the target tool explicitly per flavor fixes 109.
**Owner: open.**

### 3013. The checksum tools exit 0 after logging errors

**`pdschecksums` and `pds4checksums` never propagate errors into the exit
   code.** Both compute a `proceed` flag from `fatal or errors` and then use it
   only to gate the optional `--infoshelf` chain (`pdschecksums`'s `--infoshelf` chain,
   `pds4checksums`'s `--infoshelf` chain at PR-25's head); neither ends in `sys.exit(status)` the way the
   other nine tools do. A `--validate` that reports checksum mismatches still
   exits 0. Pinned in both checksum test modules (see
   `support.TOOLS_WITHOUT_EXIT_STATUS`). **Owner: PR-25** — its `run_main()` spec
   says "set exit code from fatal/errors", which will change these two tools'
   exit codes; that is an intended, plan-sanctioned behavior change and the pins
   must be updated with it.

Two further observations, not defects in a single tool:

**`pdschecksums` and `pds4checksums` still exit 0 after logging errors.**
`support.TOOLS_WITHOUT_EXIT_STATUS` records this and PR-13's tests assert it:
a `--validate` that reports checksum mismatches exits 0. PR-26 **preserved it
deliberately**. The shared driver returns its status rather than exiting, and
each tool decides: `pdsinfoshelf`/`pds4infoshelf` call `sys.exit(result.status)`,
the two checksums tools do not, exactly as before.

Preserved rather than fixed because it is pinned current behavior that the plan
does not enumerate as a PR-26 change, and because changing it would change the
exit code of every failing checksums run — the most externally visible thing
these tools do, and something a sync script or a cron wrapper may depend on.
The one change PR-26 did make here is adjacent and enumerated: a **chained**
`pdsinfoshelf` run's exit code now reaches the caller intact, where
`os.system`'s wait status previously truncated every failure to 0. So
`pdschecksums --infoshelf` now reports the chained run's failure while still
not reporting its own.

Giving these two tools an exit status is now a two-line change in one place
each, and `expected_error_exit_code()` is the single point the tests would move
through.
**Owner: open.**

**`pds4checksums --initialize` over an existing manifest logs an error and exits 0**,
which makes any `&&` chain onto it vacuous. Measured: the run reports
`Checksum file already exists: ...`, closes with `1 ERROR message`, and exits 0, so
`pds4checksums --initialize "$B" && pds4infoshelf --initialize "$B"` runs the second
command over a bundle whose manifest was not written. This is a since-resolved observation's exit-status
behavior seen from the operator's side; it is recorded separately because the
natural workaround for observation 3012 is exactly that `&&`, and it does not work.
**Owner: PR-25's exit-status change, which fixes both.**

## Structure and duplication

### 3100. `pdsfile.tools.show_opus_products` is importable now, and it imports `tabulate` at module scope…

**`pdsfile.tools.show_opus_products` is importable now, and it imports
`tabulate` at module scope — a `dev`-only extra.** The module has always
imported `tabulate`, so `python -m pdsfile.tools.show_opus_products` has always
needed the dev extra; what changed is that the module can now be *imported*
without running, which is what an autodoc build or a console-script entry point
would do. `scripts/check_runtime_imports.py` walks the frozen public module set
and does not reach `src/pdsfile/tools/`, and CI installs `.[dev]`, so the
clean-install gate is green and stays green. The question this leaves is which
way to settle it: move `tabulate` to the runtime dependencies, or import it
inside the branch that renders a table so the other three output modes work in
a bare install. Both are behaviour decisions about a shipped module rather than
tidying.
**Owner: open.**

### 3101. A shipped module imports a development-only dependency at module level, and the documentation…

**A shipped module imports a development-only dependency at module level, and the
documentation build is the first thing that has to work around it.**
`src/pdsfile/tools/show_opus_products.py` carries `import tabulate` at module level,
and `tabulate` is
in the `dev` extra of `pyproject.toml`, not in the runtime dependencies and not in
the `docs` extra. ReadTheDocs installs the project with the `docs` extra alone, so
`tabulate` is absent there. Measured by building with a `tabulate` that raises
`ImportError`: without a mock the build exits **1** with two warnings -- `autodoc:
failed to import 'show_opus_products' from module 'pdsfile.tools'`, and this
configuration's own coverage check reporting the module absent, since a module that
fails to import is never recorded in the Python domain. With
`autodoc_mock_imports = ['tabulate']` the same build is clean, which is the fix
`doc_dev_guide.mdc` section 7 prescribes. The mock documents the module; it does not
answer whether a shipped module should import a dev-only dependency at module level
at all. No gate in the repository would have caught it -- see observation 4312.
**Owner: a later packaging PR.**

### 3102. Logging calls build their message eagerly instead of passing arguments

**Logging calls across `src/pdsfile/` build their message eagerly instead of
passing lazy `%`-style arguments.** The owner's rule, given on 2026-08-03, is
that a logging call passes a `%`-style format string and the values as
*arguments* — `logger.warn('Message: %s', the_message)` — and that f-strings
belong in exception messages, not in logging calls. PR-23 converted the four
calls it had itself turned into f-strings (`_preload.py` ×2, `_shelves.py`,
`pdscache.py`) and swept the rest of the package. It did **not** convert them:
they are pre-existing and outside a `ruff check` PR's warrant, and `ruff`
has no rule that reports them (`G004`/`flake8-logging-format` is not in the
selected set, and would not catch the `+` form anyway).

Measured with an AST sweep over `src/pdsfile/**/*.py`, excluding the
generated `_version.py`. The predicate, stated exactly so the count is
reproducible: an `ast.Call` whose `func` is an `ast.Attribute` with `attr` in
`{debug, info, warn, warning, error, critical, exception, log, fatal, open,
close}` and whose receiver, as `ast.unparse`d text, contains `logger`
(case-insensitive), counted once if its **first** argument is an
`ast.JoinedStr`, an `ast.BinOp` with `Add` or `Mod`, or a `.format()` call.
The core figure is stable under three variants of the predicate (first
argument only, any argument, and dropping `open`/`close` from the method
set); an independent sweep during review reported **98** rather than 96 for
the subpackages, and the two extra sites were not identified, so treat the
subpackage figure as ±2. Nothing in the decision this entry asks for turns on
it.

| Area | Sites | `+` concat | f-string | eager `%` |
|---|---|---|---|---|
| core, `src/pdsfile/*.py` | **34** | 30 | 2 | 2 |
| subpackages, `src/pdsfile/**/` | **96** | 33 | 7 | 56 |
| **total** | **130** | 63 | 9 | 58 |

Core, by file: `pdscache.py` 20, `_preload.py` 8, `_sorting.py` 2, `_opus.py`
1, `_properties.py` 1, `pdsfile.py` 1, `pdsviewable.py` 1. Most of
`pdscache.py`'s are `+`-joined f-string fragments inside `MemcachedCache`,
which no test here executes (observation 4207). The subpackage total is dominated by
the maintenance tools, which Phase 6 consolidates.

Two things make this more than a style sweep, and are why it needs a decision
rather than a mechanical pass:

- **The messages must keep their `%` pattern.** `pdslogger`'s `log()` reads
  "if there are no substitution patterns (indicated by `%` or `{`) inside the
  message string, a single argument is interpreted as the `filepath`", so a
  conversion that drops the pattern silently turns its value into a path
  suffix instead of raising.
- **Many of these calls already pass a real second argument that *is* a
  filepath** (`_opus.py:114`, `_properties.py:1582`, `pdscache.py:599`/`:610`,
  and most of the maintenance tools' `logger.error(..., abspath)` calls). A
  conversion has to distinguish a filepath argument from a value argument at
  every site. `pdsviewable.py:529` shows the failure mode already present:
  `logger.warn(f'Missing sizes for icon {icon_name} ({key})', str(missing)[1:-1])`
  has no `%` in the message, so the size list is being rendered through the
  filepath path rather than as a value.

**Owner: owner decision on scope, then a dedicated style PR — the count is too
large and too spread out for PR-24, whose warrant is `ruff check` on the
subpackages.**

**a since-resolved observation's eager-logging inventory undercounts: it is 132 sites
and 69 filepath-passing sites, not 130 and 67.** a since-resolved observation states its
predicate exactly, and the `attr` set it uses —
`{debug, info, warn, warning, error, critical, exception, log, fatal, open,
close}` — omits `pdslogger.PdsLogger.normal()`, which is a real level method
alongside `blankline`, `ds_store`, `dot_underscore`, `invisible` and
`hidden`. Re-running the same sweep with the full method set adds
`pds4checksums.py:119` and `:128`
(`logger.normal('Selected MD5=%s' % md5, abspath)` and
`logger.normal('MD5=%s' % md5, abspath)`) — both of which are also
filepath-passing sites, so both counts move by two. Their pds3 counterparts
at `pdschecksums.py:118`/`:127` use `logger.info` and were already counted,
which is what makes the asymmetry easy to miss.

This does not change a since-resolved observation's conclusion or PR-24's disposition; it is
recorded so the figure a later PR works from is the measured one.
**Owner: whoever executes the a since-resolved observation conversion.**

**The a since-resolved observation fix left an eager `%` inside a logging call.** In
`pds4linkshelf.generate_links`, the label-identification loop logs
`logger.info('Label identified (by file_name tag) for %s' % linktext,
label_abspath)` — the message is formatted before the call rather than passed
as a lazy argument, which the standing logging rule is against. It is base
code that PR-27's one-line fix edited in place rather than logging PR-27
wrote, so converting it there would have been gratuitous churn inside an
otherwise verbatim function. It is now a line this PR touched, though, and it
belongs with the `UP031` residue still ratcheted in both `generate_links`
functions — one sweep, not two.

**Wider than one line.** Four more eager-`%` logging calls sit in the two new
shared modules — the two "Index shelf file is out of date" lines in
`_indexshelf_common.index_repair` and the two "Link shelf file is out of date"
lines in `_linkshelf_common.link_repair`. Ruff's `UP031` does not flag any of
them, because the operand is a parenthesized expression rather than a plain
name, so they are outside the ratchet as well: a sweep that follows the ratchet
alone would miss them.
**Owner: open.**

## Test coverage

### 3200. `data_pdsfile_for_index_row` has no in-process test coverage at all, and rms-viewmaster calls…

**`data_pdsfile_for_index_row` has no in-process test coverage at all, and
rms-viewmaster calls it three times.** A per-test-context coverage run over
`tests/pds3file/`, `tests/pds4file/`, `tests/rules/`, `tests/core/` and
`tests/holdings_maintenance/` attributes **50** distinct test contexts to the
two modules PR-19 creates and **zero** of them to
`data_pdsfile_for_index_row` (`critiques/phase5-validation.md`, PR-19 §9).
Independently: mutating it to always return `None` leaves the suite at 721
passed, exactly as unmutated (§10). Unlike PR-18's observation 4214, this is not the
subprocess blindness — nothing calls it in-process either.

It is not dead code. `viewmaster/viewmaster.py:873`, `:1449` and `:1599` call
it on every index-row page. So the one method in this extraction with no test
is also one of the two that a live consumer depends on. The method is four
lines over `data_abspath_associated_with_index_row` (which *is* covered) plus
`from_abspath`, so a test costs almost nothing.

PR-19 may not add it: its gate is an identical pass/fail set apart from the
two ids observation 4210 required, and a further new test id is movement.
**Owner: Phase 6**, alongside observations 4214 and 4214, which are the same shape.

### 3201. Four methods PR-20 moved have zero in-process test coverage, and rms-viewmaster calls two of…

**Four methods PR-20 moved have zero in-process test coverage, and
rms-viewmaster calls two of them.** A `dynamic_context = test_function`
coverage run over `tests/pds3file/`, `tests/pds4file/`, `tests/rules/`,
`tests/core/` and `tests/holdings_maintenance/` attributes 224 distinct test
functions to `src/pdsfile/_sorting.py` and `src/pdsfile/_associations.py`,
and **zero** to `sort_sibnames`, `sort_siblings`, `associated_logical_paths`
and `associated_pdsfiles`. A grep of `tests/` confirms it independently: none
of the four has a single call site there. Mutating each of them — reversing
the list `sort_sibnames` hands to `sort_basenames`, truncating what
`sort_siblings` sorts, truncating either association method's answer — leaves
the suite at 721 passed.

Unlike PR-19's observation 3200, this is not a "nothing calls it anywhere" finding:
rms-viewmaster calls `associated_pdsfiles` at seven sites
(`viewmaster.py:844,1039,1047,1258,1433,1444,1547`) and `sort_siblings` at
one (`viewmaster.py:1407`), and `sort_siblings` is the only caller of
`sort_sibnames`. `associated_logical_paths` has no consumer call site in
either repo but is a frozen public method. So four live pieces of the public
surface are pinned by nothing but the API manifest, which records a signature
and not a behavior.

PR-20 did not fix it: its gate is an identical pass/fail set and any new test
is a new id. The natural owner is whoever next adds tests to
`tests/pds3file/` — the four are cheap to cover, since `sort_siblings` and
`associated_pdsfiles` are thin wrappers over `sort_sibnames` and
`associated_abspaths`, both of which are heavily golden-tested.
**Owner: unassigned (a future test PR, not Phase 5).**

### 3202. Several transformation tests assert a subset, never a length, so a truncated answer is…

**Several transformation tests assert a subset, never a length, so a
truncated answer is invisible to them.** PR-20's negative controls turned up
seven mutations of *covered* code that changed no outcome. The dominant shape
is `test_abspaths_for_pdsfiles`, `test_pdsfiles_for_logicals` and their
whitebox twins, which do

```python
res = pds3file.Pds3File.abspaths_for_pdsfiles(pdsfiles=pdsfiles, must_exist=True)
for path in res:
    assert path in expected
```

— every returned value must be expected, but nothing asserts that everything
expected was returned, so replacing the body's return with `[...][:1]` still
passes. Adding `assert len(res) == len(expected)`, or comparing sorted lists,
would close it and is a one-line change per test.

The other five green controls are branch reachability or a caller that never
looks at a length, rather than assertion strength in the method's own test, and are recorded here so a later round does not re-derive them:
`split_basename`'s three-group `BUNDLENAME_PLUS_REGEX` return needs a bundle
name whose split rule leaves it unchanged and no golden case supplies one;
`sort_basenames`' `labels_after=True` sort key is never exercised;
`viewable_childnames_by_anchor` and `pdsfiles_for_basenames` are reached only
through `viewset_lookup`, which never checks a length; and
`associated_parallel`'s `# This should never happen` return is, as its comment
says, not reached.

PR-20 may not act on any of it — its gate is the pass/fail set — and
strengthening an assertion in a test the PR does not otherwise touch is the
volunteered-scope failure mode the common brief §5.1 forbids.
**Owner: unassigned (a future test PR, not Phase 5).**

### 3203. Three behaviours the migration moved are pinned only by the out-of-repo tool transcript

**Three behaviours the migration moved are pinned only by the out-of-repo tool
transcript.** Probed by mutation against
`pytest tests/holdings_maintenance/ --mode ns`, which sat at 297 passed for
each: inverting `index_repair`'s `if latest_mtime > shelf_mtime`, which chooses
between re-dating an up-to-date shelf and cancelling; and replacing
`run_index_main`'s `rpartition`-based log directory with
`os.path.split(logfile)[0]`, which is precisely the alternative observation 4044
rebuts. Both are moved code and pre-existing gaps rather than PR-27
regressions, and both are covered by the 81-record transcript, which lives
outside the repository. The two mutations PR-27 *did* have to argue for — the
backup skip reporting as an error, and `link_targets` filtering a unit set's
non-directory children — were in the same state and are now pinned by tests.
**Owner: open.**

## Gates, tooling and CI

### 3300. `critiques/pr-29/check_docstrings.py` is not wired into any gate

**`critiques/pr-29/check_docstrings.py` is not wired into any gate.** `grep -rI
check_docstrings` outside `critiques/` and `.git/` returns nothing: it is not in
`scripts/run-all-checks.sh` and not in any workflow. It is the only thing in the
repository that catches docstring-against-signature drift, and the Sphinx gate
catches none of it: with the signature untouched, deleting a `Parameters:` entry,
inventing one, renaming one, and inverting a stated default all pass the
documentation gate with zero warnings, and the published page then shows the real
signature directly above a parameter list that contradicts it. The checker catches
four of those five shapes (P1, P2, R1) and not the wrong default. Wiring it in is a
one-line change to the code checks and a decision about where a `critiques/` tool
should live. **Owner: the owner.**

### 3301. `scripts/check_runtime_imports.py` covers seven core modules and the two rules packages; it…

**`scripts/check_runtime_imports.py` covers seven core modules and the two
rules packages; it never imports a maintenance tool.** `_TOP_MODULES` lists
`pdsfile`, `pdsfile.pdsfile`, `pdsfile.pdscache`, `pdsfile.pdsviewable`,
`pdsfile.preload_and_cache`, `pdsfile.pds3file` and `pdsfile.pds4file`, plus
everything under the two `rules` packages. Nothing under
`holdings_maintenance/` is in the set, so a tool that grows an import outside
the runtime dependencies passes the clean-install gate untouched.

Now that `re_validate.py` imports cleanly — PR-25a — extending the gate to the
tool modules is finally *possible*: before PR-25a, importing that one module
ran a command line and called `sys.exit()`, so the gate could not have
imported it at all. It is still not *free*: the tools import `pdslogger` and
`translator`, and whether every one of those is a runtime dependency rather
than a dev extra is a measurement nobody has made. Extending the gate can
therefore legitimately turn CI red, which makes it its own measured change
rather than a rider on this PR.
**Owner: open.**

### 3302. `scripts/read-docs.sh` builds the documentation with half the gate, and this PR is what makes…

**`scripts/read-docs.sh` builds the documentation with half the gate, and this PR is
what makes it live.** The script has been in the tree since before `docs/` existed
and refuses to run without it, so it has never run. It runs
`make -C docs html SPHINXOPTS="-W"`: no `-n`, so no cross-reference is checked, and
no `make clean`, so a second run over an unchanged tree reports nothing at all
(observation 3304 is the same mechanism, and observation 4309's fix covers only the coverage
check). It is a preview tool rather than a gate -- it builds the HTML and opens it --
and the gate in `run-all-checks.sh` is what the repository's enabled set means. It
was left alone rather than quietly broadened. **Owner: the owner, if the two should
agree.**

### 3303. A checker whose totals line is not the last line of its output will be read through `tail` and…

**A checker whose totals line is not the last line of its output will be read
through `tail` and reported as passing.** `critiques/pr-30/check_rule_tables.py`
prints its findings, a blank, the totals, the per-code counts, a blank, and the
`ALLOWED` list. Every re-run during PR-30's correction batches was read through
`| tail -2`, which shows the last blank and `ALLOWED`, so a run reporting 24
findings was recorded as reporting none, and stayed that way through a green CI run.
`critiques/pr-29/check_docstrings.py` escapes this only because its totals line
happens to fall within the last two.

Two cheap fixes, either of which would have caught it: **print the totals last**, or
have the caller read the exit status rather than the tail. The second is already the
rule for the Sphinx probe, which appends a line of its own on a nonzero exit for
exactly this reason. **Owner: whichever PR next writes or runs a checker of this
shape; the ordering fix belongs in `check_rule_tables.py` itself.**

### 3304. The documentation gate can pass while measuring nothing

**`sphinx-build -n` reports every unresolved cross-reference and exits 0, so a gate
that runs it and reads its exit status proves nothing.** `doc_python.mdc` section 6
prescribes two builds, `sphinx-build -W` and `sphinx-build -n`, and says "BOTH must
succeed with ZERO warnings". Succeeding is not the same condition as zero warnings:
`-n` turns nitpick checking on and does not make warnings fatal. Measured on this
tree with one broken cross-reference in `docs/api/pds3file.rst`
(`:class:`~pdsfile.pds3file.Pds3Filo``): `-W` alone exits **0** with **0** warnings,
because the reference is not checked at all; `-n` alone exits **0** while reporting
the warning; `-n -W` exits **2**. The gate this PR ships runs `-W` and `-n -W` and
reads both statuses. This is a property of the rule file, not of this PR, and the
next person to build a documentation gate from section 6 as written will build a
vacuous one. **Owner: the rule file, if it is ever revised.**

**Two Sphinx builds that share a `BUILDDIR` share its doctree cache, and the second
one reports nothing.** With the same broken cross-reference in place,
`make html SPHINXOPTS="-W"` followed by `make html SPHINXOPTS="-n -W"` into the same
`_build` prints `updating environment: 0 added, 0 changed, 0 removed`, then `no
targets are out of date`, then `build succeeded`, and exits **0**. Nitpick warnings
are emitted while a document is resolved and written; a build that re-reads and
re-writes nothing emits none, and `nitpicky` is a configuration value with no
rebuild flag, so changing it between two builds does not invalidate the environment.
The gate gives the second build its own `BUILDDIR` for this reason and
`docs/Makefile` records it. Anything that reuses one build directory for two flag
settings -- a later gate, a CI cache, a developer running both by hand -- inherits
the same trap.

### 3305. The documentation gate depends on reaching `docs.python.org`, and an unreachable inventory is a…

**The documentation gate depends on reaching `docs.python.org`, and an unreachable
inventory is a build failure.** `intersphinx_mapping` is what makes the
standard-library names in `Parameters:`, `Returns:` and `Raises:` entries resolve.
Measured by pointing it at a host that does not resolve: `-W` alone exits **1** with
one warning (`failed to reach any of the inventories`), and `-n -W` exits **1** with
**37** -- that one plus the 36 references the inventory was resolving
(`collections.abc.Callable` x11, `argparse.Namespace` x8,
`argparse.ArgumentParser` x5, `re.Pattern` x4, `tarfile.ReadError` x2,
`pickle.UnpicklingError` x2, and one each of `smtplib.SMTPException`,
`pickle.PickleError`, `pathlib.Path`, `datetime.datetime`). It was 34 before the
constructor docstrings were published; publishing them added two. So a transient outage at
`docs.python.org` turns the hosted lint job red, and the message names the inventory
rather than anything about this tree. `intersphinx_timeout = 30` bounds the case
where the host accepts the connection and never answers, which would otherwise stall
the build instead of failing it. The remedy if it ever flakes in practice is a second
inventory location in the mapping tuple pointing at a copy of `objects.inv` committed
here; that was not done, because it commits a binary that goes stale and the flake
has not been observed. **Owner: whoever sees it flake.**

## Documentation and records

### 3400. Module-level comments and docstrings still narrate the port instead of describing the code

**Module-level comments and docstrings still narrate the port instead of
describing the code.** The rule is the same one that governs every other
comment: say what the code *is*, not how it got that way. The module headers
were written during the decomposition and read accordingly.

`src/pdsfile/pdsfile.py`'s module docstring is the main one. Its concrete
tells, measured rather than characterised:

- "re-exports every name it **has ever exported**" (:10) — a claim about the
  past. It re-exports the names it exports; that is all a reader needs.
- "`preload_and_cache.py` … is **now** a re-export shim over `_preload.py`"
  (:47) — "now" is only meaningful against a previous state.
- The whole closing paragraph (:80–82): "The split is invisible to a caller's
  code: `pdsfile.pdsfile.<name>` still resolves for every name it resolved
  for **before**, and nothing a caller imports or calls has **moved or been
  renamed**." This is a statement about a migration, not about the module.
- "**What stays here, and why**" (:51) frames the contents as a residue of an
  extraction rather than as the module's subject matter.

Elsewhere: `src/pdsfile/preload_and_cache.py:4` ("every name this module has
**always** exported still resolves here"), and the same "stays"/"still"
framing in the re-export blocks of `pdsfile.py`, `pdscache.py` and
`pdsviewable.py`.

The information in these headers is worth keeping — the module map, the
mixin mechanics, the reason the `class PdsFile` statement cannot move, the
reason an unreferenced import must not be deleted. **Only the framing
changes:** written as description rather than as change history, every one of
these facts still has a natural form. Rewrite them; do not delete them.

Deliberately not done inside PR-23: it is a prose pass over fifteen module
headers, wanted by the owner as its own piece of work rather than folded into
a `ruff check` PR whose warrant is that it changes nothing. It also overlaps
Phase 7, which owns docstrings.
**Owner: owner-directed; Phase 7 (PR-29–PR-34) is the natural home.**

### 3401. Six pre-existing tracked files carry multi-component fragments of the real holdings roots

**Six pre-existing tracked files carry multi-component fragments of the real
holdings roots.** §3.4 requires that no absolute holdings path appear in
committed code, tests, docs, CI or `critiques/` records. Measured by scanning
every tracked file for any run of two or more consecutive components of
either root: `tests/pds3file/test_pds3file_whitebox.py`,
`plans/archive/2026-07-17-modernization-plan.md`,
`critiques/2026-07-21-unified-mini-holdings-analysis.md`,
`critiques/pr-02/validation.md`, `critiques/pr-14/round-1.md` and
`critiques/pr-14/validation.md`. No complete root appears in any of them; the
longest run is 29 characters, in the archived v1 plan. PR-16 does not touch
any of these files and cleaning them is outside a pure move PR's goal, so
they are recorded rather than fixed — but one of them is a **test module**,
which is the one category where a fragment could also become a portability
problem rather than only a disclosure one. The scan is a few lines and would
make a reasonable addition to `run-all-checks.sh` if the owner wants the rule
enforced rather than observed. **Owner:** owner decision, then PR-24 (records
and the archived plan) and PR-36 (the test module, via the critique pass).

## Accepted or frozen

### 3500. `pdsarchives` logs under a `_links` suffix

**`pdsarchives` names its per-volume log file `_links`, not `_archives`.**
`pdsarchives`'s log-path spec fields passes `'_links'` to `log_path_for_volume`, so a run
writes `.../HSTN0_7176_links_<timetag>_<task>.log`. Every other pds3 tool
passes a suffix matching its own kind (`_md5`, `_info`, `_dependency`,
`_re-validate`) and `pds4archives.py` passes `'_archives'`.

`pdslinkshelf`'s `main()` passes the same `'_links'` suffix for the same
volume and the same five task names, which raises the question of a collision.
Measured: there is none. `_log_path_for` (`_derived_paths.py`'s `_log_path_for`) inserts the
`dir=` argument as a directory component, and the two tools pass
`dir='pdsarchives'` and `dir='pdslinkshelf'`, so for one volume and
`task='validate'` the paths are

```
<disk>/logs/pdsarchives/volumes/HSTNx_xxxx/HSTN0_7176_links_<t>_validate.log
<disk>/logs/pdslinkshelf/volumes/HSTNx_xxxx/HSTN0_7176_links_<t>_validate.log
```

Different directories, so neither run can overwrite or interleave with the
other. What remains is a naming inconsistency: the basename of an archive log
says `links`. Log file paths are frozen behavior, so PR-25 moved the suffix
across unchanged.
**Owner: cosmetic, but it is a frozen path -- renaming it to `_archives` needs
a decision.**

**`pdsarchives` logs under a `_links` suffix.** `pds3/pdsarchives.py`'s spec
carries `log_suffix='_links'` where `pds4/pds4archives.py` carries
`'_archives'`, so a pds3 archive run writes
`logs/pdsarchives/<category>/<set>/<unit>_links_<tag>.log`. Not a PR-25 slip:
the tool wrote `pdsdir.log_path_for_volume('_links', …)` before PR-25 as well,
so PR-25 preserved it faithfully and PR-27 does not touch it. Changing it moves
a log file name, which is exactly the kind of thing a sync script or a log
rotation rule can be written against.
**Owner: open.**

### 3501. The PDS4 programs identify themselves as their PDS3 twins

**The pds4 tools identify themselves as their pds3 twins, in help text, in
one error message, and in their log directory.** `pds4checksums --help` begins
`pdschecksums: Create, maintain and validate MD5 checksum files…`, its missing
task error is `pdschecksums error: Missing task`, and both its log root
subdirectory and its per-target log directory are `pdschecksums/`. Same for
`pds4infoshelf` and `pdsinfoshelf`. That is the behavior at base, it is not new,
and PR-25 already carried it forward for the archive pair by giving
`pds4archives` `progname='pdsarchives'`. PR-26 does the same for these four, so
the logs of a PDS3 and a PDS4 run still land under one directory name and can
collide only by holdings root, not by tool.

It is now a **single, visible piece of data** — one `progname` field per spec —
rather than five hand-copied strings per tool, so changing it is a one-line
decision per tool rather than a hunt. Not changed here: the log directory name
is a path that existing installations and the sync scripts already use.
**Owner: open.**

**`pdsindexshelf` and `pds4indexshelf` both call themselves `pdsindexshelf`,
and both link shelf tools call themselves `pdslinkshelf`.** The pds4 flavors'
`--help` description, their "Missing task" error and the subdirectory of each
log root are all the pds3 name, in both pairs. That is preserved rather than
fixed: it is what a run looks like today, and the names of log directories are
what a sync script would have been written against. It is recorded because a
reader of `pds4indexshelf.py` now sees `progname='pdsindexshelf'` in the spec
and could reasonably read it as a copy-paste error. The archives, checksums and
infoshelf pairs do not share this: each of those names itself.
**Owner: open — a rename is a CLI-visible change and needs a decision.**

**All five PDS4 programs identify themselves as their PDS3 twin, and it is now
published.** `ToolSpec.progname` is `'pdsarchives'` on `pds4archives`,
`'pdschecksums'` on `pds4checksums`, and so on for all five. It is read in two
places: `_common.build_arg_parser()`, so `pds4archives --help` describes itself as
`pdsarchives`; and `_common.setup_run()`, which joins it to the log root, so
**`pds4archives` writes its logs into `<log root>/pdsarchives/`**, mixed with the
PDS3 program's and separated only by the category component below (`bundles/` vs
`volumes/`). Measured on a real run: `pds4checksums --initialize` wrote
`logs/pdschecksums/bundles/<bundle set>/<bundle>_md5_<time tag>_initialize.log`.

**It is pre-existing rather than a consolidation regression.** The original
standalone `holdings_maintenance/pds4/pds4archives.py` on `main` already joined the
log root to the literal `'pdsarchives'`, and all five originals did the same.

The guide states the behavior as it is, in the shared chapter and in each of the
five PDS4 chapters. Whether it may be fixed is an owner decision the frozen-CLI rule
does not settle: names, flags and exit codes are frozen and a log *directory* is
none of the three, while log text is explicitly unfrozen -- but operators may have
tooling pointed at those paths, and a fix would move every PDS4 log tree at once.
**Owner: the owner.**
