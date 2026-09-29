# PR-35 round 3 — full diff

Reviewer: a new fresh, no-context subagent (same materials as the prior rounds,
plus both committed round records with instructions to verify every claimed
resolution against the code and then sample independently, trusting no prior
round's coverage claims). It made no edits.

The reviewer independently reproduced the gates (stubtest 79 modules exit 0; a
fresh wheel **and sdist** each carrying 43 `.pyi` + `py.typed`; the four freeze
files diff-free with `test_api_freeze.py` passing live; both ruff invocations
passing with the per-file-ignores table untouched; `ENABLE_STUBTEST` wired
end-to-end and live in the hosted CI path; both allowlist entries true against
the code). It confirmed the whole PR diff touches zero `.py` files and that both
fix commits (`f5626d9..fa1f952`, `fa1f952..0a0d862`) touched no `src/**/*.py`,
so the carry-forward claims hold and the recorded suite numbers cannot be stale.
For type truth it read the implementation behind every module-level function,
all six constructors, the instance block, `_sorting` in full, every concretely
typed `_properties` member, the shelf/index/derived-path/local-fs/preload/opus
groups, both cache classes, all of `pdsviewable`, both subclass stubs and seven
rule stubs; ran a mechanical own-body-surface comparison of all 36 rule stubs
against runtime; and checked consumer call sites in rms-opus and rms-viewmaster
against the declared signatures. **Every round-1 and round-2 resolution was
verified real.**

Verdict: **goal met** — zero Major; two new Minor findings, both resolved below,
which per §6.6 sends the loop to the scoped round 4.

## Minor findings, and their resolutions

**m-i. `sort_logical_paths(logical_paths: Iterable[str])` — round-2 m-C's defect
shape, unswept from its one sibling.** The parameter is iterated twice
(`_sorting.py:485`, then `set(logical_paths)` at `:532`), so a one-shot
generator's second pass is empty and the call silently returns `[]` — a worse
failure mode than the raised `ValueError` that round 2 fixed in
`construct_category_list`. The reviewer checked every other `Iterable` parameter
in the stubs and confirmed each is iterated exactly once, so this was the only
remaining sibling. **Fixed:** `Collection[str]`; the derivation row corrected —
it had recorded the double iteration and kept `Iterable` anyway.

**m-ii. The corrected evidence file disagreed with itself.** `derivation-core.md`'s
"Imports needed" note still attributed the `Iterable` import to
`construct_category_list`, which the same file's corrected row records as
`Collection[str]` since round 2. **Fixed:** the note now names both imports and
their owners.

## Gates after the round's fixes

The fixes touch one `.pyi` file and two record files — nothing under
`src/pdsfile/**/*.py` — so the full-data record again carries forward. Re-run
after the fixes: stubtest (`Success: no issues found in 79 modules`, exit 0),
`ruff check src/pdsfile tests scripts docs` (passes), API-freeze (passes).
