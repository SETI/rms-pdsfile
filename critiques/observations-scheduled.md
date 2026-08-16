# Observations scheduled for the remaining phases

Open observations that a remaining PR of the modernization plan already owns. Each will be closed by the PR it is listed under; none needs a separate decision. Numbers are stable identifiers, grouped by owning PR with room left between groups.

## Docstring cross-references and wording — PR-31a is permanently deferred to issue #149

### 1000. `log_path_for_index`'s docstring first line describes a bundle

**`log_path_for_index`'s docstring first line describes a bundle.**
`src/pdsfile/_derived_paths.py` opens it with "Return a complete log file path
for this bundle."; it returns an *index* log path, as its own second line and
its `is_index` guard both say. The sibling `log_path_for_bundleset` says
"for this bundle set", so the line is a copy that was never updated. PR-18
moved the definition byte-for-byte and deliberately did not touch it: a commit
that edited the text would break the byte-for-byte claim that makes the move
checkable, and the wording is not a behavior. **Owner: Phase 7** (PR-29–PR-34),
where `doc_python.mdc` comes into force and the docstrings are revised anyway.

The PR-18 round-4 review found a second docstring in the same module with the
same defect, and it belongs to this entry rather than to a new one:
`dirpath_and_prefix_for_archive` says "Return the absolute path to the
directory associated with this archive path." and returns the 2-tuple
`(dirpath, parent)`. Its sibling `dirpath_and_prefix_for_checksum` gets this
right — "Return tuple (…)". Also moved verbatim, also correctly untouched
here. The Phase-7 docstring pass should treat `_derived_paths.py` as a file
with more than one of these, not as a single fix.

### 1001. `napoleon_use_ivar = True` costs five cross-reference targets, all of them `LinkInfo`'s

**`napoleon_use_ivar = True` costs five cross-reference targets, all of them
`LinkInfo`'s.** The setting resolves a since-resolved observation's 27 duplicate-object warnings by
rendering an `Attributes:` section as a field list rather than as a run of attribute
directives, and a field list creates no target. Measured over the whole package by
diffing `objects.inv` at the two settings: 862 objects with the setting off, 857
with it on, and the five that go are
`pdsfile.holdings_maintenance._linkshelf_common.LinkInfo.recno`, `.linktext`,
`.linkname`, `.is_target` and `.target`. The three dataclasses lose nothing, because
autodoc emits their fields from the annotations regardless -- which is what the
duplicate was. `LinkInfo` is a plain class whose attributes are assigned in
`__init__`, so Napoleon's rendering was their only target. Nothing references them
today and the build is clean either way, but a later PR that writes `:attr:` roles
for them will find they do not resolve. **Owner: issue #149, which is where the sweep
that would write those roles now lives.**

### 1002. `src/pdsfile/pds3file/__init__.py`'s alias comment now introduces one method instead of eight

**`src/pdsfile/pds3file/__init__.py`'s alias comment now introduces one
method instead of eight.** After the `F811` de-duplication removed the seven
shadowed definitions, `# Alias, compatible with old function/property names`
at `:123` sits above `log_path_for_volset` alone, while its twin
`log_path_for_volume` and the six alias properties live about fifty lines
below under `# Override functions`. Nothing is wrong — the comment is still
true of the method it introduces — but the two alias groups would read better
merged under one heading. Moving code is not a `ruff check` fix, so it
correctly stayed out of PR-24.
**Owner: Phase 7 (PR-29–PR-34), which owns docstrings and module structure.**

**AMENDED by PR-30a (2026-08-08). The merge is still open and the split is now
navigable without it.** PR-30a documented both groups where they stand rather
than moving anything, since it changes no executable statement. Every one of the
nineteen aliases — thirteen properties and six methods, not the "seven shadowed
definitions plus one" this entry's framing implies — now opens with the same
sentence shape, "The PDS3 name for `bundle...`, whose value it returns", so the
group a member belongs to is legible from the member rather than from the comment
above it, and the class docstring counts them in one place. The `Raises:` and
`Returns:` of each also record where its base member's answer differs from what
the name suggests, which is the thing a merge would not have supplied.

The line numbers have moved: `# Alias, compatible with old function/property
names` is at `:243` above `log_path_for_volset`, `# Override functions` at `:268`,
and the second group now runs from `:268` to `:524` rather than fifty lines. The
two are further apart than when this entry was written, which is an argument for
the merge rather than against it. **Owner: unchanged — a later PR that may move
code.**

### 1003. Docstrings written here use inline literals for API symbols, not Sphinx cross-reference roles…

**Docstrings written here use inline literals for API symbols, not Sphinx
cross-reference roles, and PR-31 will have to revisit that.** `doc_python.mdc`
section 5 wants every mention of a code object to carry a role; section 6 wants the
tree to build clean under `-n`, which fails any role that does not resolve. Only
five modules have autodoc pages today, so a role naming anything else -- `Pds3File`,
`PdsLogger`, `preload`, every mixin -- would resolve to nothing and fail the gate.
Double backticks satisfy the build; what they cost is the links, which is the whole
point of section 5's rule, so this is a deliberate trade of cross-references for a
build that passes. When PR-31 publishes the full API reference the roles become
resolvable and every one of these literals should be swept into a role.

**AMENDED by PR-31, which built the reference and measured the sweep instead of
doing it.** The premise holds: the roles resolve now. The scope does not fit in the
PR that creates the tree. Measured over all 78 modules with an AST walk of every
module, class and function docstring: **3,651 inline-literal occurrences, 1,260
distinct**, of which **2,384 occurrences (652 distinct) name something the package
defines** by a classifier that accepts a module, class, function, method or
assigned module-level name and strips a trailing `()`. The remaining 1,267 are what
section 5 says must stay literals -- `.DS_Store`, `.py`, `--help`, `volumes/`,
`sys.exit()`, `open()`. `_properties.py` alone holds 380 of the 3,651, `pdsfile.py`
299, `pdsviewable.py` 141 and `re_validate.py` 138. Every one of the 2,384 is a
judgment -- is this a code object we own, does the role resolve, is `:meth:` or
`:attr:` right -- and every one edits docstring text in a file that has just been
through a two-reads review. Two of them are already known not to resolve: observation 1001
records the five `LinkInfo` attributes that `napoleon_use_ivar` leaves without a
target, and observation 6403 records the 43 docstrings that are not published at all, whose
roles nothing would check.
**Owner: issue #149, which carries this measurement so it is not re-derived.**

## PR-34 — README rewrite, and the PyMarkdown gate

### 1200. Where the README include marker sits decides what the documentation front page says, and…

**Where the README include marker sits decides what the documentation front page
says, and neither position warns.** Moving `<!-- start-after-point -->` past
`Supported versions: Python >= 3.10` removes the front page's only substantive line;
`:start-after:` swallowing content is not a warning. Placing it before the
`# rms-pdsfile` H1 instead renders the project title twice, `<h1>` then `<h2>`, also
without a warning. It sits after the H1 for that reason. The cost of that choice is
that the README's last line is a second H1 (`# PDS Ring-Moon Systems Node, SETI
Institute`), so the rendered landing page ends with a heading and nothing under it.
**Owner: PR-34, which rewrites the README and inherits the marker.**

### 1201. `CONTRIBUTING.md` documents `pytest` without holdings or `--mode`

**`CONTRIBUTING.md` documents `pytest` without holdings or `--mode`.** Its
testing section shows bare `pytest` / `pytest tests/<file>` with no mention
of `PDS3_HOLDINGS_DIR`/`PDS4_HOLDINGS_DIR`, `PDSFILE_TEST_HOLDINGS`, or
`--mode`. Now that the pytest gate is enabled, a contributor following it
gets an 800-skip run with no explanation of why. **Owner: Phase 7**
(PR-33 ch. 5 "Test-suite guide", or PR-34 with the README rewrite).

## PR-35 — Public-API type stubs and `py.typed`

### 1300. `DictionaryCache.preload_eligible` has no reader

**`DictionaryCache.preload_eligible` has no reader.** It is set True at
`pdscache.py:190` and appears nowhere else in `src/` or `tests/`. `MemcachedCache`
has no such attribute, so it is not part of the shared interface either. It is a
public attribute name, so removing it is not free. Same shape as observation 1301.
**Owner: a future cleanup PR, or PR-35 when it decides what the stubs declare.**

### 1301. Two exported names are read by nothing

**Two exported names are read by nothing.** `_preload.DICTIONARY_CACHE_LIMIT`
(`_preload.py:101`) is re-exported by `preload_and_cache` and by `pdsfile.pdsfile`,
but every cache in the package is built with `cls.DICTIONARY_CACHE_LIMIT`, a class
attribute defined separately and identically in `pdsfile.py:331`,
`pds3file/__init__.py:169` and `pds4file/__init__.py:143`. Rebinding the module
constant changes nothing. `pdscache.MEMCACHED_LOADED` (`pdscache.py:77`) is read
nowhere; the flag the code actually consults is `_preload.HAS_PYLIBMC`, set by a
second `try: import pylibmc` in a second module. Both names are in the frozen API,
so neither can simply go. **Owner: a future cleanup PR, or PR-35 when it decides
what the stubs declare.**

## PR-36 — Run the template critique skills and address the findings

### 1400. Five exception tests pass vacuously when the call under test returns normally

**Five exception tests pass vacuously when the call under test returns
normally.** `tests/pds3file/test_pds3file_whitebox.py` wraps the call in a
bare `try` and asserts only inside the `except` handler, with no `else` and
no unconditional failure:

```python
def test_data_set_id_exception(self, input_path, expected):
    target_pdsfile = instantiate_target_pdsfile(input_path)
    try:
        _ = target_pdsfile.data_set_id
    except ValueError as e:
        assert expected in str(e)
```

If `data_set_id` ever stops raising, the handler never runs and the test
passes green while checking nothing. Measured by walking the module's AST for
`try` statements with no `else` and no unconditional failure in the body,
there are five: `:324` (`data_set_id`), `:427` (`from_path`), `:455`
(`from_opus_id` with a wrong id), `:521` (`find_selected_row_key`) and `:554`
(`data_abspath_associated_with_index_row`). It is the reason this file carries
a `PT017` ratchet entry: `pytest.raises` is exactly the construct that makes
the exception mandatory.

Pre-existing — the shape is identical at `8cab66a`, and PR-24 changed only
the `parametrize` argument form and, at `:324`, one `res1 =` to `_ =`. Fixing it means
either adding an `else: raise AssertionError(...)` to each site or converting
to `pytest.raises` and dropping the `PT017` entry, both of which change what
the suite asserts — outside a `ruff check` PR whose gate is an identical
pass/fail set. Note the sibling tests in `test_pds3file_blackbox.py` already
use the stronger form (`assert False  # pragma: no cover` after the call), so
the repair pattern is already in the tree.
**Owner: PR-36 (the test-suite critique pass), or any PR that revisits these
modules' assertions.**

### 1401. Two negative `from_lid` tests are parametrized with an `expected` value they never use

**Two negative `from_lid` tests are parametrized with an `expected` value
they never use.** `tests/pds3file/test_pds3file_blackbox.py`
`test_from_lid_mismatched_lid` (:947) and `test_from_lid_invalid_lid` (:962)
both take `(input_lid, expected)` and assert only on a fixed substring of the
error message, so `expected` — in the first case the data-set ID the
resolution is supposed to disagree with — is dead. The mismatch test would
pass on a `ValueError` naming any other data-set ID.

The stronger version asserts `expected` appears in the message; the invalid
test has no data-set ID in its error contract at all and should simply drop
the parameter. Both are pre-existing at `8cab66a`; PR-24 touched only the
`parametrize` argument form. The unused parameter is invisible to the gate
because `ARG002` is not in the select set.
**Owner: PR-36, with observation 1400 — the two are the same weakness at different
strengths.**

## PR-37 — Finalization: strip the rewrite scaffolding, re-verify every gate

### 1500. `shelf_lookup`'s sidecar shortcut is dark in the reference holdings root

**`shelf_lookup`'s sidecar shortcut is dark in the reference holdings root.**
An info shelf is a `<bundlename>_info.pickle` plus a readable
`<bundlename>_info.py` sidecar, and `shelf_lookup` reads the sidecar's second
line for a bundle rather than unpickling the shelf. The limited testing copy
the goldens are tuned to carries the `.pickle` half only, so that branch is
never executed by either local pass and only the complete-set nightly reaches
it. PR-17 compensates for the parse itself with
`tests/core/test_shelf_sidecar_record.py` (holdings-free) plus a direct run
against the complete set, but the branch in `shelf_lookup` that *chooses* the
shortcut remains uncovered locally. Fixing it means either a test that builds
a whole shelf pair under `tmp_path` or a change to which root CI uses.
**Owner:** PR-37 (Phase 8), where CI root selection and coverage targets are
settled.

### 1501. The hosted no-holdings job has no floor on how many tests actually ran

**The hosted no-holdings job has no floor on how many tests actually ran.**
The plan calls that run "itself the regression test for PR-09's graceful
skip", and it does catch the primary regression: a collection error exits
non-zero. But a regression that skipped *everything* — say the
`tests/api/conftest.py` path predicate quietly stopping matching — exits 0 and
the job stays green, because "0 passed, N skipped" is a passing pytest run
(N was 824 when this was written and is 859 after PR-15).
PR-14 hardened the one known way that could happen (both sides of the path
comparison are resolved), and each PR's §6.2 record pins the expected
no-holdings counts, so a drop is visible in review — but nothing fails
automatically. A cheap tripwire (assert a floor on the passed count, or
require specific node ids to have run) belongs with whatever PR next touches
the hosted job. **Owner:** PR-37's finalization sweep, or any earlier PR that
edits the lint job.

### 1502. The self-hosted `test` job still runs on default workflow permissions

**The self-hosted `test` job still runs on default workflow permissions.**
`zizmor` flags `excessive-permissions` on `.github/workflows/run-tests.yml`:
neither the workflow nor the `test` job declares a `permissions:` block, so
both `pull_request` jobs got the repository's default token scope. PR-14
fixed the half it owns — the new `lint` job declares
`permissions: contents: read` and its checkout sets
`persist-credentials: false` — but the PR-14 bullet says to keep the
self-hosted matrix exactly as it is, so the `test` job was left alone. It
checks out PR-head code and then runs it, and it additionally needs whatever
scope `codecov/codecov-action` uses, so the right block is not simply a copy
of the lint job's. The same applies to `run-tests-and-opus.yml`, which is
likewise untouched here. **Owner:** a CI-hardening pass, or PR-37's
finalization sweep.

### 1503. The permanent-ruff-set table in the overrides rule file has drifted

**Deviation (4)'s core table enumerates 40 permanent findings where ruff
reports 39.** Re-derived at `ab1fa3b` the way the deviation says
(`ruff check` with the project config and `lint.per-file-ignores = {}`), the
fifteen modules directly under `src/pdsfile/` report **39**, not the 40 the
table's rows add up to. The row that is off is `__init__.py`, recorded as
`F403 ×3` at `:10,:12,:13`; ruff reports `F403 ×2`, at `:14,:15`. The line
numbers moved because the file changed after the table was written, and the
third star import presumably went with them.

Nothing is broken: `F403` is still in `__init__.py`'s `per-file-ignores` entry
and the configured gate passes. It is recorded because the table is what a
later shrink is measured against, and 2,316 total findings at `ab1fa3b` split
39 + 2,277, not 40 + 2,277.
**Owner: whichever PR next shrinks the core group's entries.**

**The per-code table in `pdsfile_overrides.mdc` deviation (4) has drifted from
the tree.** Spot-measured at PR-28's head with
`ruff check --config 'lint.per-file-ignores = {}' --select <code> src/pdsfile
tests scripts`: `UP031` 97 against the table's 124, `B006` 12 against 9,
`B012` 2 against 3, `RUF015` 3 against 2. The drift is from the Phase-6
migrations moving code between files rather than from any entry being wrong —
the ratchet itself, which is the enforced copy, is exact. PR-28 removed the
two rows that had become false statements (`F821`, and the `RUF059` row whose
cited defect no longer exists) and did not re-derive the counts, because a
table PR-24 owns is not a thing to half-refresh from inside another PR.
**Owner: open — one re-derivation of the whole table, by whoever next edits
it.**

**The permanent-ruff-set table in `pdsfile_overrides.mdc` deviation (4) cites line
numbers that have drifted, and one of its counts is wrong.** The table's caption
says the line numbers are "at the merge commit", meaning PR-23's and PR-24's, and
eight PRs have moved code since. Measured at `9466dbc`, before this PR, by running
`ruff check --config 'lint.per-file-ignores = {}'` over the fifteen core modules and
comparing the reported sites against the table:

| row | table says | actual line at `9466dbc` |
|---|---|---|
| `__init__.py` `F403` | 10, 12, 13 — **three of them** | 38 and 39 — **two** |
| `_derived_paths.py` `A002` | 264, 281, 297 | 299, 316, 332 |
| `pdscache.py` `RUF015` / `UP031` | 622 / 324 | 1201 / 775 |
| `pdsfile.py` `B904` / `I001` | 1418, 1824, 1874 / 84 | 1825, 2305, 2355 / 94 |
| `pdsviewable.py` `B006` | 52, 114, 205 | 133, 248, 390 |

The other six rows — for `_index_rows.py`, `_opus.py`, `_preload.py`,
`_properties.py`, `_shelves.py` and `_sorting.py` — were exact at `9466dbc`. This
PR's docstrings move five of the six: the `RUF005` sites go to lines 228, 344 and
449 in the first three, the `B904` site to line 299 in `_shelves.py`, and
`_sorting.py`'s four to lines 283, 291, 295 and 300. `_properties.py` is not
documented here, so its row alone still points at the right line.

**The `F403` count is the part that is not a drift.** `__init__.py` has two star
imports, not three; the third import the row's prose describes,
`from pdsfile.pdsfile import PdsFile as PdsFile`, is an explicit aliased re-export
and raises no `F403` at all. So "the three star imports are what bind `Pds3File`,
`Pds4File` and the rule modules" is wrong about the mechanism as well as the count:
two star imports bind the subpackages, and `PdsFile` arrives by name.

Nothing is broken by this — the enforced copy is the `per-file-ignores` block in
`pyproject.toml`, which lists codes and not lines, and it is correct. The table is
documentation. This PR does not renumber it, because re-deriving rows that PR-23,
PR-24 and PR-29 wrote is not a docstring PR's work and a half-renumbered table is
worse than a consistently historical one. **Owner: whichever PR next revises
deviation (4)** — either re-derive every row, or say in the caption that the
numbers are the sites as of the PR that derived each row and will drift.
