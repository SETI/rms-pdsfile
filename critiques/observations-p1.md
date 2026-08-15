# Observations — blocking (P1)

Open observations that block the merge to `main`. These are not the most severe defects on the list; they are the ones where leaving them undone makes a claim this branch makes about itself untrue — a gate that cannot fail, a limit the plan set and did not honour, or published prose that is silently wrong.

## Structure and duplication

### 2000. Two module-length limits the plan set and then declined to waive

**Three maintenance-tool modules are over 1000 lines and are deliberately
not waived.** Measuring the explicit waiver list for a since-resolved observation turned up files
the decision was not asked about:
`src/pdsfile/holdings_maintenance/pds3/pdslinkshelf.py` (**1,779**),
`src/pdsfile/holdings_maintenance/pds4/pds4linkshelf.py` (**1,274**) and
`src/pdsfile/holdings_maintenance/pds3/pdsdependency.py` (**1,166**).
(`src/pdsfile/pds3file/rules/VG_28xx.py` at 1,017 is already covered by the
rule-module entry.)

They were left off the waiver on purpose rather than by oversight. **Phase 6
(PR-25 onward) consolidates the duplicated pds3/pds4 tool logic into
`_common.py`**, so these sizes are expected to change; waiving them now would
pre-empt that work with a statement about to stop being true. Nothing is
broken in the meantime — no gate enforces module length (`ruff`'s select set
has no such check), so this is a documentation question, not a failing check.

Whether they end up waived, split, or shrunk by the consolidation is a
Phase-6 question, answerable once PR-25 has established how much of each file
is duplication.

**Two of the three are answered by PR-27: shrunk, not waived.**
`pdslinkshelf.py` is **471** lines and `pds4linkshelf.py` is **524**, from 1,730
and 1,224 at PR-27's base — the shared code went into `_linkshelf_common.py`
(729) and the 536-line `REPAIRS` table into `pds3/linkshelf_repairs.py` (555).
Both are now comfortably under the limit and neither needs a waiver.
`pdsdependency.py` is untouched at **1,165** and is the only module left in
`holdings_maintenance/` over the limit; it has no pds3/pds4 twin, so the
consolidation this entry was waiting on will never reach it.

**The third is answered by PR-28 only in the sense that the wait is over.**
PR-28 closes Phase 6 without touching `pdsdependency.py`, which is still 1,165
lines: its subject is three scripts that had no `main()`, and splitting a
1,165-line tool is neither in that subject nor a thing to do on the way past.
What PR-28 does settle is that the deferral has expired — this entry parked the
question until the consolidation had shown how much of each file was
duplication, and for this file the answer is none, because there is nothing to
consolidate it against. So it is a live question rather than a waiting one:
waive it, or split it in a later phase. `pdsfile_overrides.mdc` deviation (3)
now says the same rather than pointing at a phase that has ended.

**PR-30c documents the file and does not move the number.** Measured with
`critiques/pr-29a/measure_module_lines.py` at both ends of that PR:
**1,135 code lines at base and 1,135 at head**, against a limit of 1,000, while
the total goes from 1,165 to 1,520 against a limit of 2,000. That is the two
limits behaving as they are meant to — a docstring line is not a code line —
and it is recorded because a reader who sees this file grow by 355 lines in a
docstring PR would otherwise assume the breach got worse. It did not, and the
file is still 480 lines under the total limit. The question this entry holds is
unchanged and unaddressed: the 1,135 code lines are the tool's own, and no PR of
Phase 7 was going to reduce them.
**Owner: open — `pdsdependency.py` needs a waiver-or-split decision, and no
phase currently owns it.**

**`pdsfile.py` is over both module-length limits and the overage is code, not
prose.** Measured with `critiques/pr-29a/measure_module_lines.py`: 2,435 total
lines, 781 of them docstring, **1,654 code** — over the 1,000-line code budget by
654 and over the 2,000-line ingestion budget by 435. It is the only file under
`src/` over both. The owner deferred the split on 2026-08-07 and its waiver stands;
this entry records what a future split has to work with rather than reopening the
decision.

**There is no documentation lever.** The file is one class occupying 2,247 of its
2,435 lines, starting at `pdsfile.py:185` and running to the end of the class body,
holding 37 methods that account for 1,920 lines between them, against a module
docstring of 87 lines. Deleting the module
docstring outright would leave 1,567 code lines, still 567 over. Trimming
docstrings cannot fix either number, and under the two-limit rule it would not even
move the code figure.

The available lever is structural: a tenth mixin, on the pattern Phase 5
established. Whether one exists — whether any coherent group of those 37 methods
can leave without dragging the rest — is open and nothing here answers it.
**Owner: whoever takes the `pdsfile.py` split.**

## Test coverage

### 2100. A stubbed collaborator hid a real break, for the second time in this subsystem

**A stubbed collaborator hid a real break, for the second time in this
subsystem.** The migration left the four thin tool modules with a task *table*
and no task *names*, and `re_validate.validate_one_volume()` reaches
`pdslinkshelf.validate()` by attribute. The full `--mode ns` data suite ran
green in that state — 1,047 passed, 34 skipped — and so did
`run-all-checks -c -s`. Nothing could have caught it: every test that drives
`validate_one_volume` replaces all five sibling tools with `SimpleNamespace`
stubs, which is what lets those tests run without holdings and is also what
makes them silent about whether the real functions exist.

Fixed here — each module binds its five tasks under the names it carries them
as a library, and `test_re_validate.py` gains
`test_the_sibling_tools_really_accept_what_this_module_calls_them_with`, which
binds each of the seven calls against the real modules. The general shape is
what is left open: `re_validate` is not the only module in this tree that
stubs a collaborator wholesale, and a stub that outlives its subject is
invisible to every gate. observation 6607 is the same failure mode one level down —
a subprocess importing a different tree — and the fix is the same in kind: one
test that exercises the real thing, however narrowly.
**Owner: open.**

## Gates, tooling and CI

### 2200. `pylibmc` is reachable as `pdsfile.pdsfile.pylibmc` today and as `pdsfile._preload.pylibmc`…

**`pylibmc` is reachable as `pdsfile.pdsfile.pylibmc` today and as
`pdsfile._preload.pylibmc` after PR-21 — and on any machine where it is
reachable at all, the API-freeze gate is already red.** PR-21 moved the
`try: import pylibmc / HAS_PYLIBMC = True / except ImportError` block out of
`pdsfile.py` and into `_preload.py`, because `preload` is its only consumer.
`HAS_PYLIBMC` is a frozen member of `pdsfile.pdsfile`, so it is re-exported in
the redundant-alias form; `pylibmc` is a *conditionally bound module import*,
and re-exporting it would need a new `if HAS_PYLIBMC:` statement in
`pdsfile.py` — new logic rather than a move.

Measured rather than argued:

- `pylibmc` is not installed in this environment, so `pdsfile.pdsfile.pylibmc`
  does not exist here on either side of the change.
- With a stub `pylibmc.py` on `PYTHONPATH`, `HAS_PYLIBMC` becomes `True`,
  `'pylibmc' in vars(pdsfile.pdsfile)` becomes `True`, and
  `scripts/dump_public_api.py` records `"pylibmc": "module"` under
  `pdsfile.pdsfile`. Diffing that dump against the committed
  `tests/api/api_manifest.json` reports **two extra names, both spelled
  `pylibmc`: one under `pdsfile.pdsfile` and one under `pdsfile.pdscache`.**
- **Only the first is PR-21's, and it is the smaller half.**
  `src/pdsfile/pdscache.py:7` has its own optional `import pylibmc` behind a
  `try`, and `pdsfile.pdscache` is also one of the dumper's seven fixed
  modules (`scripts/dump_public_api.py:37`). Phase 5 does not touch it, and
  re-running the same stub against PR-21's HEAD leaves the diff at **one**
  extra name, under `pdsfile.pdscache`.

So `pylibmc` is not part of the frozen contract; a machine that has it already
fails the freeze gate before Phase 5 touches anything, and **still fails it
after PR-21**, via `pdscache`. Nothing in `src/`, `tests/`, `scripts/`,
rms-opus or rms-viewmaster refers to `pdsfile.pdsfile.pylibmc`. What the owner
may want to decide separately: the manifest is environment-dependent for
optional dependencies — a property of the dumper's `vars(module)` walk rather
than of any PR — and it means the freeze gate cannot be run on a
memcached-capable deployment host, whatever Phase 5 does. Any fix has to cover
`pdscache` as well as `pdsfile.pdsfile`, and editing the dumper or the
manifest is a §6.4 prohibition for the executor, so this is an owner decision.

**A third reviewer suggested annotating the exception in the code**, at
`src/pdsfile/pdsfile.py`'s re-export block, whose comment says the private
names there "are carried so that no name reachable as `pdsfile.pdsfile.<name>`
is lost". PR-21 declined, for two reasons worth recording so the next reader
does not re-derive them. The clause is a *purpose* statement scoped to the
four private names the sentence introduces (`_GLOB_CACHE_SIZE`,
`_clean_abspath`, `_clean_glob`, `_needs_glob`), not a global invariant over
the module — none of the four is `pylibmc`. And the sentence is inherited
wording, written by PR-16 and extended by PR-17, PR-20 and PR-21 only by
adding names to its lists, so rewording its claim is a change to another PR's
prose. If the owner wants the exception visible in the source rather than
here, that is a one-line edit for whichever PR next touches that block.
**Owner: unassigned (a freeze/manifest question, not Phase 5).**
