# PR-27 adversarial review — round 1

Two independent reviews ran against the same head: the §6.6 fresh no-context
adversarial reviewer, and CodeRabbit on PR #125. This file records both, the
resolution of every finding, and the rebuttals.

## CodeRabbit (PR #125, first pass)

Five inline findings plus one outside-diff finding, all filed as Trivial. Every
one was answered on its own thread.

| # | finding | resolution |
|---|---|---|
| 1 | `_indexshelf_common.py:282` — the `index_dict is None` checks are unreachable | **rebutted**, deferred entry 126 |
| 2 | `_indexshelf_common.py:584` — no fallback when the tool subdirectory is absent from the log path | **rebutted**, deferred entry 127 |
| 3 | `_linkshelf_common.py:462` — `validate_links` empties both input dictionaries and does not say so | **fixed** in `8b3c939` |
| 4 | `_linkshelf_common.py:638` — `link_update` drops `limits` when it falls back to `link_initialize` | **fixed** in `8b3c939`, and it was five more sites than reported |
| 5 | `test_re_validate.py:1450` — cover all four migrated task namespaces | **covered elsewhere** in `8b3c939` |
| 6 | `pds4linkshelf.py:336-347` (outside diff) — guard the loop against a non-list value from `old_links` | **rebutted**, deferred entry 128 |

### 1 — unreachable `None` checks. Rebutted.

Correct that they are unreachable: `generate_indexdict()` returns a two-tuple or
raises. Both flavors carried the branch before this PR (`pdsindexshelf.py:224`,
`pds4indexshelf.py:221` at `2265393`), so merging them forced no choice.

This PR *did* remove one dead branch — a `move_old()` in
`pdslinkshelf.initialize` sitting after a guard that returns when the shelf file
exists — and enumerated it. The distinction is the one that decides both cases:
that branch was in only **one** of the two flavors, so the merge had to pick;
this one is in **both**, so the merge picks nothing, and removing it is a cleanup
rather than a consequence of the migration.

### 2 — the log-directory `rpartition`. Rebutted.

The line is the two base tools'
`logfile.rpartition('/pdsindexshelf/')[0] + '/pdsindexshelf'`
(`pdsindexshelf.py:497-498`, `pds4indexshelf.py:483-484` at `2265393`)
generalized over `spec.progname`, not new code. It is deliberately not
`os.path.split(logfile)[0]`, which the other two drivers use: `log_path_for_index`
builds a path carrying the table's whole logical path, so splitting would put a
copy of the tool's error handler in every per-table directory.

The suggested fallback has nothing to fall back from. `log_paths_for` is called
with `dir=spec.progname`, a non-empty constant, and `_derived_paths._log_path_for`
appends `[subdir.rstrip('/'), '/']` after a log root that always ends in `/`, so
the built path always contains `/<progname>/`.

### 3 — `validate_links` mutates its inputs. Fixed.

It deletes from both dictionaries as it goes, which is exactly how the last two
loops know what each side lacks. The docstring now says so, says why, and says a
caller needing either afterwards has to pass a copy.

### 4 — `limits` dropped on the fallback. Fixed, and wider than reported.

Measured at the base rather than taken as read: **three** of the six pds3
fallbacks dropped `limits` (`pdsindexshelf.reinitialize`, `pdsindexshelf.repair`,
`pdslinkshelf.update`) and all four pds4 sites had no `limits` parameter at all.
All six now forward it. Enumerated as change 11 in `pr-27-validation.md`.
Invisible from the command line, where the driver never passes limits; visible to
a library caller that does.

### 5 — cover all four migrated namespaces. Covered, elsewhere.

Extending the `re_validate` test would have blurred what it is for: it pins the
seven calls `validate_one_volume` makes, against the real modules rather than the
`SimpleNamespace` stubs every other test in that module installs. The other three
tools are not among its callees.

The class the finding points at is real, so it is pinned where it belongs.
`tests/holdings_maintenance/test_shelf_common.py` gains two parametrized tests
over all four migrated tools:

- `test_each_migrated_tool_still_carries_its_five_task_names` — each name exists,
  is that tool's own table entry, and binds `(target, logger=, limits=)`.
- `test_each_migrated_tool_binds_its_own_spec_into_its_tasks` — each table entry
  is the family function with that tool's own `SPEC` bound in, and the spec's
  `PdsFile` class matches the flavor.

Negative control: rebinding `pds4indexshelf`'s table to `pdsindexshelf`'s spec
fails the second test for that tool and nothing else (`1 failed, 24 passed`).

### 6 — guard against a non-list `old_links` value. Rebutted.

The finding says itself that it "cannot reach Line 342 today"; the reachability
was then measured rather than assumed. Keys reaching that loop are filtered to
`local_labels_abspath`, the `.xml`/`.lblx` files of the current directory. Every
one of those is put into `linkinfo_dict` with a **list** value by the loop above
(both extensions are in `EXTS_WO_LABELS`), and the merge preserves it: a key in
`linkinfo_dict` keeps its list, and only a key in neither `linkinfo_dict` nor
`label_dict` becomes `''`. A label path with a string value is not a state this
code can produce or read back.

The fix in this PR does not worsen it either: a string value raised
`AttributeError` on `.linktext` before and would raise `IndexError` on `info[1]`
after — the same unreachable branch. Adding an `isinstance` guard means adding a
branch no test can reach on a behaviour-preserving refactor.

## §6.6 adversarial reviewer

<!-- ROUND1 REVIEWER -->
