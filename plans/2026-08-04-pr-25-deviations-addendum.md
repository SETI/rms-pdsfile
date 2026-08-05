# Addendum — PR-25's deviations from the plan's spec'd design

**Status: ruled on by the owner, 2026-08-05.** §1, §2, §3 and §5 are settled and
each records the ruling under a **Ruling** heading; §4 and §6 stand as written and
were not objected to. §7 is **new and needs the owner's eye**: it is a public-API
question the rulings opened, and it is written to be read on its own. (§6.4:
"Deviations from this plan require an addendum file in `plans/` acknowledged by
the owner before the deviating PR merges".)

The plan's PR-25 entry (`plans/2026-07-25-modernization-plan.md` lines 717–760)
specifies a concrete target interface so the design is not re-invented per
implementer. Five things in the delivered PR-25 depart from it. None changes any
observable behavior; each is a design call the spec did not anticipate, written
up rather than silently absorbed. The measurements behind them are in
`critiques/phase6-validation.md`.

## 1. `write_archive` is not a spec hook — ACCEPTED

**The plan says:** migrate the archives pair first, "hardest divergence: pds3
single-tar vs pds4 one-bundle-→-many-tarballs — modelled as a `write_archive`
hook on the spec, not an `if pds4:` branch".

**What was done:** both `write_archive` implementations, and all ten task
functions, stay in their own tool modules. `_common.py` holds no `write_archive`
and no spec field naming one.

**Why:** the divergence is larger than the phrasing anticipates. On top of the
structural split, the task functions differ in six further observable ways, each
verified at `ab1fa3b`: pds3 `repair`/`update` pass `force=True` to `logger.info`
and pds4 does not; pds3 `update` calls `write_archive(clobber=True)` where pds4
calls `clobber=False`; pds3 `repair` returns after one decision where pds4 loops
and `continue`s; pds4 `update` accumulates `wrote_any` where pds3 returns
immediately; pds4 `validate`/`repair` filter `dir_tuples` per tarball; pds4
`validate` short-circuits on the first invalid tarball.

A spec field whose value is the whole function is not a hook — it shares
nothing, and it puts a callback indirection in front of code that is easier to
read where it is. The alternative, one shared `write_archive` carrying flags for
the `clobber` default, the `force=`, the per-tarball filtering and the
early-return shape, is exactly the shrug-flag accumulation §2 of the sub-plan
forbids, and each flag would be one more chance to change frozen output.

The plan's actual requirement — no `if pds4:` branch anywhere — is met:
`_common.py` contains no test on which flavor is running.

**Ruling (owner, 2026-08-05): accepted.** `write_archive` is not a spec hook, and
the plan has been amended so PR-26 and PR-27 do not re-derive the argument: the
PR-25 entry of `plans/2026-07-25-modernization-plan.md` now says so, points here,
and keeps the requirement that actually governs — no `if pds4:` branch anywhere.
This section is now a record rather than a request.

## 2. `ToolSpec` is a plain class, not a `@dataclass` — MOOT

**The plan says:** "A `@dataclass ToolSpec` capturing everything that varies
between a pds3 and pds4 tool".

**What was done:** `ToolSpec` is a plain class with a keyword-only `__init__`
and a docstring naming every field.

**Why:** a dataclass declares its fields by annotation and cannot be written
without one. Ground rule 5 and `pdsfile_overrides.mdc` deviation (1) forbid
inline type annotations, and deviation (4) already reads that ban as covering
class-body annotations — it is the stated reason `RUF012` can never be fixed
with `ClassVar`. Twelve annotated dataclass fields would be a larger annotation
footprint than the single `ClassVar` that ban rejects.

**The alternative considered and not taken:** `collections.namedtuple('ToolSpec',
[...])` also declares fields without annotations and is immutable. It was not
chosen because it makes the spec a tuple — iterable, indexable and unpackable —
which invites positional construction of a twelve-field record, and because
per-field documentation has no natural home on it. Both spellings hold the same
data; if the owner prefers the namedtuple, the change is local to `_common.py`
and its two `SPEC = ...` call sites.

**Note:** an earlier revision of this PR extended deviation (1) in
`.cursor/rules/pdsfile_overrides.mdc` to say that the annotation ban rules out
`@dataclass`. That edit was **reverted**: a PR should not extend the rules file
that authorizes its own departure from the plan.

**Ruling (owner, 2026-08-05): moot — the deviation is withdrawn.** The owner
lifted the annotation ban for this case rather than accepting the argument above,
so `ToolSpec` is now the `@dataclass(kw_only=True)` the plan specified, with a
field annotation per field and no other change to what it holds. The whole of the
reasoning in this section is therefore superseded: it was never rejected on its
merits, it simply stopped applying. Deviation (1) now says field annotations on a
`@dataclass` are permitted, so PR-26 and PR-27 do not re-litigate it; the ban on
inline type hints generally, on mypy, and on `ClassVar` for `RUF012` is unchanged.
The `collections.namedtuple` alternative weighed above was not taken and is not
open: the owner chose the dataclass.

## 3. `hashfile()` and `move_old_<kind>()` did not move into `_common.py` — OVERRULED

**The plan says:** the target interface lists "`BACKUP_FILENAME` regex, the
`*_LIMITS` defaults, `hashfile()`, and `move_old_<kind>()` version-numbering —
moved verbatim, one copy".

**What was done:** `BACKUP_FILENAME` and the archives `*_LIMITS` moved.
`hashfile()` and the three `move_old_<kind>()` functions did not.

**Why:** they belong to the checksums, infoshelf and linkshelf tools, which
PR-26 and PR-27 migrate. Moving them now would put code in `_common.py` that no
migrated tool calls, and would touch three modules this PR is otherwise
scoped out of. They are still owed by the phase, just not by this PR.

**Ruling (owner, 2026-08-05): overruled — move them now.** "If a future PR is
going to need a field, might as well add it now" applies to the code as well as to
the spec fields. `hashfile()`, `move_old_checksums()`, `move_old_info()`,
`move_old_links()` and the `LOGDIRS` list they read are now one copy each in
`_common.py`, and the six tool modules call them there. PR-25's file scope is
widened to those six modules **for that move only** — not for migration onto
`run_main`, not for ruff cleanup, not for style edits.

Three divergences had to be resolved to make one copy of each, and each one is a
behavior change on the side that loses:

1. **`move_old_checksums`'s two log lines** (deferred entry 95): pds3 passed
   `force=True` to both, pds4 passed neither. **`force=True` wins** (owner,
   2026-08-05): versioning a file is a filesystem mutation and its report should
   not be droppable by a limits cap, and it is the spelling that was already
   reachable. **This changes pds4 behavior**: a `pds4checksums` run under a scope
   that caps `info` now reports the versioning where before it could be silenced.
   Pinned by `TestReportingUnderAnInfoCap` in
   `tests/holdings_maintenance/test_common_versioning.py`, whose control is the
   same cap applied to a shelf mover that still does not force.
2. **`hashfile`**: pds3 opened the file and never closed it (a `while` loop over
   `read`); pds4 used a `with` block and `iter`. The pds4 spelling is the one
   copy. Same digest for the same bytes either way — the difference is when the
   descriptor is released, and it also removes one `SIM115` from the ratchet.
3. **`move_old_checksums`'s signature**: pds3 `(check_path, *, logger=None)`,
   pds4 `(check_path, logger=None)`. The keyword-only pds3 spelling is the one
   copy; every call site in both trees already passes `logger=`.

**`move_old_info` and `move_old_links` needed no decision**: their pds3 and pds4
twins are byte-identical, so each moved verbatim.

**What was *not* merged, and why — the hard stop this section's own rule
requires.** The three `move_old_<kind>()` functions are **not** one function with
data differences. Two of their differences are data (the noun in the two
messages; which sidecar files are copied alongside). The third is not: the
"moved to" line is `logger.info(noun + ' moved to', dest)` in the checksums and
info movers and `logger.info(noun + ' moved to ' + dest)` in the links mover, and
`pdslogger` renders those differently — measured against 3.2.1, `… moved to:
/path` for the two-argument form against `… moved to /path` for the concatenated
one, and only the two-argument form's path is subject to `replace_root`.
Collapsing the three would need a flag choosing between two call shapes, which is
the shrug-flag §2 of the sub-plan forbids, and either choice rewrites frozen log
text for two tool families. So `_common.py` holds three functions, one per kind,
sharing a section rather than a body. The identical version-numbering block
inside them (about ten lines, three copies) could be lifted into one private
helper without touching any log text; that was left for the PR that has all the
copies in front of it, because "moved verbatim" is what this section was ordered
to do.

## 4. The task-flag help text is spec data, not `build_arg_parser` content

**The plan says:** "`build_arg_parser(spec)` → the argparse parser with the five
task flags with **today's exact semantics**".

**What was done:** `build_arg_parser` owns the *semantics* — five independent
`store_const` actions writing into one `task` destination, in a fixed order,
emphatically not an `add_mutually_exclusive_group` — and takes the *wording*
from the spec as three template strings with `{unit}` / `{units}` fields.

**Why:** the five help strings talk about `.tar.gz` archives, so they are
archives-specific and cannot live in a parser builder that the checksums,
indexshelf, infoshelf and linkshelf pairs will also call. The plan's `vocab`
field is the `{unit}` substitution under a shorter name. The rendered result is
byte-identical to both originals, verified by dumping every `add_argument` call
from both trees.

## 5. Three `ToolSpec` fields differ from the plan's list — PARTLY OVERRULED

**The plan says** the `ToolSpec` captures "`pdsfile_cls` …, `vocab` …,
`holdings_sentinel` (`'/holdings/'` vs `'/pds4-holdings/'`), `index_ext`
(`.tab`/`.csv`), `logname` …, and a `log_extra_handlers` flag (pds4 adds a
`warning_handler`; pds3 does not)".

**What was done:** `holdings_sentinel` and `index_ext` are **not** fields, and
`log_extra_handlers` is not a flag — it is `handler_factories`, an **ordered
tuple** of `pdslogger` handler factories: `(error_handler,)` for pds3 and
`(warning_handler, error_handler)` for pds4.

**Why:** neither archives tool reads a holdings sentinel or an index extension —
`index_ext` belongs to the indexshelf pair, which PR-27 migrates, and nothing in
the two archives modules distinguishes the two holdings roots by string at all.
Adding either now would be a field no caller reads.

**Ruling (owner, 2026-08-05): add the two fields now; `handler_factories`
stands.** "If a future PR is going to need a field, might as well add it now."
`holdings_sentinel` and `index_ext` are now `ToolSpec` fields, and both archives
specs carry their flavor's value even though neither archives tool reads one —
the two are properties of the PDS3/PDS4 flavor, not of a tool. The `ToolSpec`
docstring says so and says they are read nowhere today.

The plan's parenthetical values were checked against the code rather than taken on
trust, and **both are right**. `holdings_sentinel` is `'/holdings/'` at
`pdschecksums.py:697`, `pdsdependency.py:1107` and `pdsinfoshelf.py:734`, and
`'/pds4-holdings/'` at `pds4checksums.py:669,680` and `pds4infoshelf.py:715,726`;
each tool both splits a command-line path on it and rebuilds an archives path
with it, so the value is the literal including both slashes. `index_ext` is
`'.tab'` at `pdsindexshelf.py:459,461,464,473` and `'.csv'` at
`pds4indexshelf.py:445,447,450,459`, used both as a `glob` suffix and in an
`endswith` test, so the value includes the dot. One thing the plan does not say
and the code assumes: the sentinel hard-codes the *name* of the holdings
directory, so a holdings root not called `holdings` or `pds4-holdings` fails the
`if not parts[1]` guard in five tools. That is pre-existing and is not this PR's
to change; it is recorded so the field is not read as a configuration point.

The `handler_factories` change is the more material one and is deliberate. A
boolean "pds4 adds a warning handler" is exactly the shrug-flag the sub-plan's
rule forbids, and it would not carry the thing that is actually observable: the
**order** in which handlers are added, at the log root
(`_common.py:246-249`) and again per target (`_common.py:276-277`). A tuple of
factories carries both which handlers and in what order, as data, and generalizes
to a tool that wants some third handler. The two `--log` / `PDS_LOG_ROOT`
invocations per tool in `critiques/phase6-validation.md` §5 are what put that
ordering under the gate.

## 6. One consequence worth the owner's eye, which is not a design choice

Extracting `main()` into a shared `run_main` changes what a **Python traceback**
inside a tool log looks like: where the pre-PR log showed one frame,
`pds4archives.py, in main / initialize(pdsdir)`, the post-PR log shows
`pds4archives.py, in main / _common.run_main(SPEC, TASKS, sys.argv)` followed by
`_common.py, in run_main / tasks[args.task](pdsdir)`. Nothing else about the log
changes — same message, same level, same counts, same file name — and the
frames below the driver are unchanged.

This is not avoidable by any implementation: a traceback names the frames on the
stack, and the plan's own design puts a shared frame there. It is called out
because §2 freezes log formats and this is the one place where a real-holdings
run of the migrated tools produces text that differs from the pre-PR run.
Measured: of 36 captured stdout streams and 39 log files per tree, 34 and 35 are
identical after normalizing the clock, and the six that differ differ in exactly
these traceback frames and nothing else.

## 7. The log time-tag race, and the public surface it did *not* need

**This section needs the owner's eye and is written to be read on its own.**

**The bug.** A log file's name carries a time tag, `LOGFILE_TIME_FMT =
'%Y-%m-%dT%H-%M-%S'` — **one-second resolution**. `_log_path_for`
(`src/pdsfile/_derived_paths.py`) read the clock on **every** call. Each of the
eleven maintenance tools writes one run's log in up to two places and builds the
two paths with two separate calls, so a run whose two calls straddle a second
boundary wrote its two copies of one log under time tags one second apart, and
they stopped naming one run. Rare — the two calls are microseconds apart — but
real, and it would make any future golden over a two-log run flaky at that rate.

**The fix, and where it went.** `PdsFile` gains a private class attribute
`_LOG_TIMETAG` (default `None`) and the derived-paths mixin gains two private
methods: `_log_timetag()`, which reads the clock, and `_pinned_log_timetag()`, a
context manager that reads it **once** on the way in, holds it for the length of
the block, and restores the previous value on the way out. `_log_path_for` uses
the pinned tag when there is one and reads the clock when there is not.
`_common.log_paths_for(spec, pdsdir, task)` is new, wraps its two calls in the
pin, and `run_main` calls it.

The pin is class state, set on the class it is called on and found through the MRO
by the rule subclass a real target is an instance of. On the way out the class
dictionary is put back exactly as it was found — restored if the class had its own
value, deleted if the value was inherited — because writing it back
unconditionally leaves a shadowing entry, and a class holding its own value stops
seeing one set on a base class. Otherwise it is the same shape as `set_log_root`,
which already writes `LOG_ROOT_` onto the class it is called on, so it introduces
no pattern the module did not have.

**The fix reaches one of the eleven tools, and the owner should decide the rest
rather than inherit it.** Measured at this head, the two-call pair is built at
**15 sites**: `_common.py:200`, which is fixed, and **14 in ten tool modules**,
which are not — the checksums, infoshelf, linkshelf and indexshelf pairs,
`pdsdependency` and `re_validate`. Eight of those ten reach `run_main` in PR-26
and PR-27 and inherit the fix then. **Two do not**: this plan leaves
`pdsdependency` a standalone tool this phase, and ground rule 7 freezes
`re_validate.py`. The two indexshelf tools deserve a specific mention — they
dedupe their pair explicitly with `if logfiles[0] == logfiles[1]: logfiles =
logfiles[:-1]`, and that comparison is defeated by precisely this race, so on a
straddling second they write one run's log **twice into one directory**. PR-25
did not touch any of the fourteen, because its scope over six of those files is
the versioning move only; deferred entry 104 records the scope.

**The owner relaxed the frozen-signature constraint for this fix, and the fix did
not need it.** The owner's ruling on 2026-08-05 was: do not be picky about frozen
signatures when fixing an actual bug, put the fix where it belongs, and add an
`exact` entry to `tests/api/manifest_allowlist.json` if that means changing a
frozen member. Taking that permission, the obvious surface fix is an optional
`timetag=`/`time=` keyword on `log_path_for_bundle`, `log_path_for_bundleset` and
`log_path_for_index`, plus the two pds3 aliases `log_path_for_volume` and
`log_path_for_volset`.

**Measured, that costs 154 allowlist entries.** The manifest records methods per
class, and those five names appear on 34, 34, 34, 26 and 26 classes respectively.
With `exact` entries only and no category predicate — which the ruling requires —
one changed member is one entry, so the five signatures are 154 entries for a
one-second race. A new public method returning the pair costs 34 to 39 for the
same reason.

**So no public name changed and no allowlist entry was added.** `_log_path_for`
was already private and appears **zero** times in `tests/api/api_manifest.json`;
`tests/api/consumer_used_private_names.json` is `[]`, so no underscore name is
dumped at all, and the two new methods and the new class attribute are all
underscore-prefixed. `pytest tests/api/` passes with its 26 ids unchanged and the
allowlist is untouched, which is the proof rather than a hand-diff of the dumper.
The relaxation is recorded here because it was granted and because the next PR
that finds a bug behind a frozen signature should know it exists — not because
this fix spent it.

**Consumer compatibility.** Nothing to check: the three public signatures are
character-for-character what they were, so no consumer call can break. Had the
keyword been added, an *optional* keyword would have been backward compatible for
every existing call, but that is now hypothetical.

**Pinned by** `tests/core/test_log_path_timetag.py`, twelve ids, `holdings_free`.
The clock those tests install advances one second on **every** reading, which
turns the race from rare into certain; each test that asserts the pin holds also
builds the same pair unpinned and asserts those two disagree, so no assertion can
pass by the race failing to fire. Against the unfixed reader — `_log_path_for`
reading the clock unconditionally — **8 of the 12 fail**; the four that still pass
assert only the pin's own bookkeeping — that it is released on exit and on a raise,
and that it leaves the class dictionary as it found it — which the reader does not
touch. They are not idle: the round-5 adversarial reviewer broke the fix **eleven**
different ways and all eleven were caught, with those four catching the mutations
that drop or misplace the `finally`.
