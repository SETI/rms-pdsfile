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

### 3007. Three defects in `crlf`

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

### 3008. Two defects in the checksum generate-and-validate path

**`pdschecksums.generate_checksums()` returns an empty dict where its own contract is
a list.** The two paths where a selection matched no file, or more than one, return
`({}, latest_mtime)`; every other return is a list of pairs, and `pds4checksums`
returns `([], latest_mtime)` on the same two paths. Every caller tests the value for
truth alone, so nothing breaks today; a caller that iterated it would get keys rather
than pairs.
**Owner: a later maintenance-tool PR.**

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

### 3303. A checker whose totals line is not the last line of its output will be read through `tail` and…

**A checker whose totals line is not the last line of its output will be read
through `tail` and reported as passing.** `critiques/pr-30/check_rule_tables.py`
prints its findings, a blank, the totals, the per-code counts, a blank, and the
`ALLOWED` list. Every re-run during PR-30's correction batches was read through
`| tail -2`, which shows the last blank and `ALLOWED`, so a run reporting 24
findings was recorded as reporting none, and stayed that way through a green CI run.
`tests/docs/check_docstrings.py` escapes this only because its totals line
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

