# Observations scheduled for the remaining phases

Open observations that a remaining PR of the modernization plan already owns. Each will be closed by the PR it is listed under; none needs a separate decision. Numbers are stable identifiers, grouped by owning PR with room left between groups.

## Docstring cross-references and wording — PR-31a is permanently deferred to issue #149

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

## PR-36 — the skills have run; the fixes half owns these

PR-36's reporting half merged as #160: the three template critique skills ran, and
their reports and triage are in `critiques/2026-08-16-*.md`. Neither entry below
was closed by it. Observation 1401 was not re-found by any skill; 1400 was re-found
as finding TS-05, which adds two blackbox sites to the five recorded here. Both are the fixes half's to take from the register rather than
from the reports.

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

**The `pdscache.py` row's coverage clause is imprecise, and it is the same
re-derivation's work.** The row ends "Both sit inside `MemcachedCache`, which
ground rule 9 protects and no test here exercises". The relative clause attaches
to the class, and of the class it is false: `tests/core/test_pdscache_set_multi.py`
builds an instance with `__new__` and a stub client and exercises `set_multi`,
which is exactly what observation 4207 records. It is true of the two *sites* —
re-measured at head with the project configuration under both the `PATH` ruff
0.15.7 that `pyproject.toml:176` names and the venv's 0.15.22, `UP031` is
`pdscache.py:775`, inside `MemcachedCache.__init__`'s `pylibmc.Client` call, and
`RUF015` is `pdscache.py:1201`, inside `flush`'s debug message; no test reaches
either. Saying so of the sites rather than of the class costs one clause and stops
the row from reading as a claim that the class has no gate at all. Raised by
PR-36's review rounds and left for the owner there, because the overrides file
records owner decisions; it is recorded here so the next revision of deviation (4)
picks it up with the rest. The same re-measurement confirms the first paragraph
still holds at head: `src/pdsfile/__init__.py` reports `F403` twice, at `:38` and
`:39`, against the table's three sites at `:10,:12,:13`.
