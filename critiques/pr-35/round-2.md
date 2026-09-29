# PR-35 round 2 — full diff

Reviewer: a new fresh, no-context subagent (same materials as round 1, plus the
committed round-1 record with instructions to verify its resolutions and weight
sampling toward round 1's blind spots). It made no edits.

The reviewer independently reproduced the gates (stubtest 79 modules exit 0, a
fresh wheel with 43 `.pyi` + `py.typed`, freeze files untouched and passing,
ruff clean with the per-file-ignores table untouched, the `ENABLE_*` wiring live
in the hosted CI path) and verified the diff changes **zero `.py` files**, so the
recorded suite numbers cannot be stale and round 1's carry-forward claim is true.
It checked manifest coverage mechanically (the manifest's 43 modules and the 43
stub modules are an exact 1:1 set), wrote its own checker validating all 153
concrete data annotations across the stubs against live runtime values (zero
failures), read the implementation behind the previously unsampled territory
(`preload_and_cache`, the module-level functions, the 25-attribute instance
block, the remaining rule stubs, both `__all__` lists, the pds4 bundle and
`*_primary_filespec` stubs), verified every round-1 resolution against the code,
and checked consumer call sites in rms-opus and rms-viewmaster against the
declared parameter types.

Verdict: **goal met** — zero Major; three new Minor findings, each resolved
below, which per §6.6 sends the loop to a further round.

## Minor findings, and their resolutions

**m-A. `row_dicts: list[dict[str, Any]]` is not derivable under the PR's own
untyped-dependency rule.** The only non-empty writer is `new_index_row_pdsfile`,
whose real argument is untyped `pdstable.PdsTable(...).dicts_by_row()` content
(`_index_rows.py:340-354`) — the same flow for which `column_names`, assigned in
the same block, was broadened to `list[Any]`. The docstring's "column name to
value" is a claim, not a derivation. **Fixed:** `list[dict[Any, Any]]` on both
the attribute and the `new_index_row_pdsfile` parameter; the two derivation rows
corrected.

**m-B. `lifetime: int | None` on the six constructors is narrower than the
provable contract.** The value flows unmodified into `CACHE.set(...,
lifetime=lifetime)`, which this PR's own `pdscache.pyi` types `float | None`;
the implementation docstrings say only "in seconds". The derivation row had
flagged `float | None` as the alternative and the assembled stub took the narrow
reading without recording why. **Fixed:** `float | None` on `child`, `parent`,
`from_abspath`, `from_logical_path`, `from_path`, `from_relative_path`; the
derivation rows now record the reasoning.

**m-C. `construct_category_list(voltypes: Iterable[str])` admits arguments the
code provably rejects.** The input is iterated four times, so a one-shot
generator yields only the first pass and the function then raises — a hazard the
function's own docstring and the derivation row both describe while the stub
still said `Iterable`. **Fixed:** `Collection[str]` — the broadest contract
whose every value survives the four iterations; the `documents` membership
requirement remains a documented `ValueError`, not a type.

## Gates after the round's fixes

The fixes touch one `.pyi` file and two record files — nothing under
`src/pdsfile/**/*.py` — so the full-data record again carries forward. Re-run
after the fixes: stubtest (`Success: no issues found in 79 modules`, exit 0),
`ruff check src/pdsfile tests scripts docs` (passes), API-freeze (passes).
