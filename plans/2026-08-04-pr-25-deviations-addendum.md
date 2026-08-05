# Addendum — PR-25's deviations from the plan's spec'd design

**Status: needs owner acknowledgement before PR-25 merges** (§6.4: "Deviations
from this plan require an addendum file in `plans/` acknowledged by the owner
before the deviating PR merges").

The plan's PR-25 entry (`plans/2026-07-25-modernization-plan.md` lines 717–760)
specifies a concrete target interface so the design is not re-invented per
implementer. Four things in the delivered PR-25 depart from it. None changes any
observable behavior; each is a design call the spec did not anticipate, written
up rather than silently absorbed. The measurements behind them are in
`critiques/phase6-validation.md`.

## 1. `write_archive` is not a spec hook

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

**If the owner prefers the literal reading**, the hook can be added in PR-26,
when the other four pairs show whether a `write_*` callback earns its keep
across five families rather than one.

## 2. `ToolSpec` is a plain class, not a `@dataclass`

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
that authorizes its own departure from the plan. If the owner acknowledges this
addendum, adding that sentence to deviation (1) is a reasonable follow-up so
PR-26 and PR-27 do not re-litigate it.

## 3. `hashfile()` and `move_old_<kind>()` did not move into `_common.py`

**The plan says:** the target interface lists "`BACKUP_FILENAME` regex, the
`*_LIMITS` defaults, `hashfile()`, and `move_old_<kind>()` version-numbering —
moved verbatim, one copy".

**What was done:** `BACKUP_FILENAME` and the archives `*_LIMITS` moved.
`hashfile()` and the three `move_old_<kind>()` functions did not.

**Why:** they belong to the checksums, infoshelf and linkshelf tools, which
PR-26 and PR-27 migrate. Moving them now would put code in `_common.py` that no
migrated tool calls, and would touch three modules this PR is otherwise
scoped out of. They are still owed by the phase, just not by this PR.

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

## 5. One consequence worth the owner's eye, which is not a design choice

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
Measured: of 27 captured stdout streams and 23 log files per tree, 25 and 19 are
identical after normalizing the clock, and the six that differ differ in exactly
these traceback frames and nothing else.
