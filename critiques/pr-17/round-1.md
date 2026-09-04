# PR-17 — adversarial review round 1

**Date:** 2026-07-27
**Reviewer:** a fresh opus-class subagent with no development context, per §6.6
step 2. It received the PR-17 section of the plan, the Phase-5 preamble including
the mixin mechanics, §2, §3.2/§3.4, §6.1, §6.2, §6.4 and §6.6 including the
progressive `.cursor/rules` compliance schedule; the exact diff
`git diff origin/pr-16-path-utils...HEAD`; and read access to the repo at HEAD,
to the real holdings, and to both consumer repos.
**Diff reviewed:** `origin/pr-16-path-utils...9fc58cc` → `1ecd6bd`
(8 files, +1,757 / −719).
**Verdict:** **goal met** — 0 Major, 3 Minor, 2 Deferred.

## What the reviewer verified independently

Worth recording, because §6.6's value is the checks the author did not think to
run. The reviewer re-derived, from its own commands rather than from the record:
the byte-for-byte comparison of all fourteen definitions (and found the one
authorized exception itself); the empty manifest diff, by exporting the parent
tree with `git archive` and running the dumper against both; every one of the 23
per-code ratchet counts; the full-data arithmetic from the raw `--junitxml` and
`.set` artifacts, including the coverage provenance; the holdings-free count; the
monkeypatch audit, including installing a wrong-answering stub itself; the 6,753
sidecar scan; and the §3.4 path scan over every added line.

Two checks it ran that this executor had not:

- **Pickle round-trip across the move.** A `Pds3File` pickled against the parent
  tree unpickles against HEAD, keeps `pdsfile.pds3file.Pds3File`, stays
  weak-referenceable and re-pickles. That is the memcached concern the preamble
  raises, tested rather than reasoned about.
- **The `__bases__[0]` sniff.** `PdsFile.__bases__[0]` changes from `object` to
  `_LocalFsMixin`, and the reviewer confirmed the
  `cls.__bases__[0].__name__ == 'Pds4File'` test in `pdsfile.py` is a rule
  subclass's base, not `PdsFile`'s, so it is unaffected.

## Findings and resolutions

### Minor

**M1 — `_ShelfMixin`'s docstring under-states the attributes it depends on.**
An AST scan of every `cls.<UPPER>` / `self.<UPPER>` reference in `_shelves.py`
returns nine names; the docstring listed seven, omitting `LOGGER` and
`PDS_HOLDINGS`. The same scan over `_local_fs.py` returns exactly the six names
its docstring lists.

**Accepted and fixed** (`114a5c1`). Reproduced with the same scan before acting.
The docstring is the mixin's stated interface with the core class, so an
incomplete list is a defect in the deliverable, not a nit.

**M2 — the `_eval_null_key_record` docstring pinned two measurements of a growing
data set.** It asserted "every one of the 6,753 info sidecars…" and "no sidecar
in the holdings set contains a name". Both are true today and the reviewer
reproduced both, but the count changes whenever a bundle is added, nothing
re-checks it, and §6.2 evidence belongs in the validation record — where it
already was.

**Accepted and fixed** (`114a5c1`). The docstring now states the property being
relied on ("a record the maintenance tools wrote is a tuple of literals and
contains no name, so which module's globals are in scope is not observable"); the
count and the scan stay in `critiques/phase5-validation.md` §8, with their
provenance.

**M3 — a test name overstated its scope.**
`test_every_public_mixin_name_is_reachable_through_pdsfile` iterates
`_defined_names(mixin)`, which includes `_get_shelf`, `_close_shelf` and
`_non_checksum_abspath`. The check is stronger than its name; the name would
mislead the next reader into thinking private members are unguarded.

**Accepted and fixed** (`114a5c1`) — renamed to
`test_every_mixin_name_is_reachable_through_pdsfile`. This renames a test id, so
it changes the §6.2 set; the record's enumerated id list and counts were
regenerated with the run, not edited.

### Deferred

**D1 — the plan's own preamble illustrates a base order the new convention
rejects.** The preamble writes `class PdsFile(_ShelfMixin, _OpusMixin, …)`;
`_OpusMixin` sorts first, so the illustration is the reverse of the alphabetical
rule PR-17 fixed and the new test asserts. Nothing is wrong today — the
illustration is plainly illustrative — but a PR-18–22 executor reading only the
plan would write a class statement the test rejects.

**Appended to `critiques/deferred-observations.md` as entry 35.** Not actionable
here: the fix is one line in the parent plan, which is the owner's to edit.

**D2 — one Phase-5 mechanic had no repeatable check.** The preamble pins "no
module-level `from pdsfile.pdsfile import PdsFile` in a mixin module", and this
PR verified it only as a one-off AST check in the record. Later PRs inherit every
other check in the new test file automatically; they would not have inherited
this one.

**Taken up rather than deferred** (`114a5c1`), because the reviewer's own
reasoning for deferring it turned out to be half right, and measuring showed why:

| injected into `_shelves.py` | outcome |
|---|---|
| `from pdsfile.pdsfile import PdsFile` | the whole suite fails to collect — `ImportError: cannot import name 'PdsFile' from partially initialized module` |
| `import pdsfile.pdsfile` | **raises nothing**; the suite collects and passes |

So the import machinery guards one form of the rule and nothing guarded the
other. `test_no_mixin_module_imports_pdsfile_at_module_level` parses each mixin
module's source and closes it, for every mixin the phase adds.

## Regeneration

The round's fixes touched `src/pdsfile/` (`_shelves.py`'s two docstrings), so
under §6.6 step 5 the full-data record was regenerated before round 2: the head
runs at 03:25:15 and 03:28:04 postdate the last source change (`114a5c1`,
03:25:04). The baseline runs stand — the baseline worktree is detached at
`2ff83a4` and no round has touched it. The set diff is now 14 additions and
nothing else, the `--mode s` diff is still empty, and the manifest diff is still
byte-empty.
