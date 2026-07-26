# PR-13 (#105) — CI failure and CodeRabbit review

Recorded after the PR was opened, against head `e89ba3a`.

## 1. The CI failure

**Symptom.** Self-hosted matrix run 30196079913: Python 3.11 failed
`tests/holdings_maintenance/test_pds3_dependency.py::test_missing_derived_products_are_reported`
with `AssertionError: golden mismatch`, and fail-fast cancelled the other three
interpreters — one failure, not four. Everything else was green (783 passed / 34
skipped). It could not be reproduced on the development machine, which passed
against **both** holdings roots.

### Root cause — verified, not assumed

`pdsdependency` builds each rule's file list with an **unsorted**
`glob.glob(pattern)` and then iterates it, so the steps one rule contributes come
out in directory-enumeration order. `glob` does not sort, and ext4 returns
directory entries in a hash order seeded per filesystem, so the same tree
enumerates differently on a different machine. The tests build their tree fresh
under `tmp_path`, so the CI runner's temporary filesystem is a third environment
distinct from either holdings root.

I verified this by driving the tool **unmodified** through a wrapper that forces
`glob.glob` to return its results sorted, then reverse-sorted, and diffing the
emitted plan:

- the two orders produce **exactly the same set of steps** (`diff` of the sorted
  lists is empty);
- they differ only in position, and the lines that move are precisely the
  `_hstfiles` / `_index` pairs the truncated CI log showed swapping.

I then closed the loop on the test itself, by putting a `sitecustomize` on the
subprocess `PYTHONPATH` that reverses the tool's enumeration:

| | ordered comparison (as shipped to CI) | sorted comparison (the fix) |
|---|---|---|
| normal enumeration | passes | passes |
| reversed enumeration | **fails**, reproducing the CI symptom exactly | passes |

So the CI failure is reproduced on demand, and the fix is shown to remove it.

### The fix

**In the test, not the tool.** The unsorted glob is pre-existing behaviour and
PR-13 is behaviour-preserving; adding a sort to `pdsdependency` would be a
behaviour change outside this PR's remit. It is recorded instead as entry 14 of
"From PR-13" in `critiques/deferred-observations.md`, owned by Phase 6.

`support.check_golden` gains an opt-in `unordered=True`, used by this one test.
The golden file is still written and committed in the tool's own order, so it
stays readable as a work plan; only the comparison sorts both sides. It therefore
still fails if a step appears, disappears, or changes text — verified directly:

- deleting one step from the produced text → caught;
- altering one step's text → caught;
- reversing the whole list → accepted, which is the intent.

The ordering the tool genuinely does specify is asserted separately, so it stays
pinned. A dependency rule emits its messages in source order, once per path its
glob matched; only rules that matched *several* paths are exposed to enumeration
order. For this subset that is exactly the six steps naming an individual metadata
table — measured by running the tool with its enumeration forced both ways, which
left the other twelve byte-identical in position. Those twelve are compared
against the golden **in exact order**, so a rule reordering its message list, or
the rules being reordered relative to each other, still fails the test.

`unordered` is deliberately opt-in and used exactly once. Every other golden —
shelf sidecars, archive member tuples, the sorted md5 mapping — has a
deterministic order that is worth pinning, and still is.

### The diagnostic

`check_golden`'s custom assertion message suppressed pytest's own diff, so CI
reported "golden mismatch" and nothing else; that cost a full debugging round.
Golden failures now carry a `difflib.unified_diff` of expected vs. produced, with
the path and whether the comparison was ordered.

### Cross-module audit

The coordinator asked whether other modules share the pattern. I audited every
assertion whose expected value derives from a `glob.glob`, `os.listdir` or
`os.walk` enumeration inside a tool, by running each tool twice — once with those
three enumerations forced ascending, once descending — and diffing the artefacts.

| Artefact | Raw order stable under reversed enumeration? | How the test compares it | Verdict |
|---|---|---|---|
| `pdsdependency` step list | **No** | was raw text | **the defect — fixed** |
| pds3 / pds4 md5 files | **No** | sorted `{path: md5}` mapping | already safe by design |
| pds3 / pds4 `.tar.gz` members | Yes (`tarfile.add` sorts internally) | sorted member tuples | safe twice over |
| pds3 / pds4 info sidecars | Yes (the tool sorts) | text | safe |
| pds3 / pds4 link sidecars | Yes | text | safe |
| pds3 index sidecar | Yes (table-row order) | text | safe |
| `show_opus_products --pprint` | Yes | text | safe |

Everything else asserts on log lines with `any()` / `all()`, or on counts, neither
of which depends on order. **`pdsdependency` was the only affected module** — the
md5 files are the only other order-unstable artefact, and the suite already
compared those as a mapping rather than as text.

## 2. CodeRabbit findings (reviewed commit `c00430d`)

| # | Finding | Disposition |
|---|---|---|
| 1 | markdownlint **MD029** on the numbered registry in `critiques/deferred-observations.md` | **Rebutted.** The pymarkdown gate is not in force until PR-34 (§6.6 progressive-compliance schedule), so a markdownlint violation is not a valid finding against PR-13. More concretely, the only fix that satisfies MD029 is renumbering, and these numbers are load-bearing: entries are cited by number from test docstrings, from the deviation addendum, and from the future work assigned to PR-25/26/27/28. Renumbering to satisfy a gate that is not yet enabled would silently break every one of those references. Recorded, not applied. |
| 2 | The addendum still said "awaiting owner acknowledgement" | **Already fixed** in `e89ba3a`, which records the owner's acceptance of all four deviations on 2026-07-26. Confirmed after pulling; no new work. |
| 3 | `test_crlf` argument-validation cases should pass a nonexistent path rather than writing a fixture file | **Applied.** Verified the premise first: `crlf.test_crlf` checks `task` and `threshold` before opening the file. Passing a path that does not exist makes that ordering part of what the test asserts — if validation ever moved after the read, the cases would raise `FileNotFoundError` and fail. The `ValueError` message assertions are kept. |
| 4 | `test_task_flags.py` should use `pytest.fail` rather than a dynamically formatted `AssertionError` | **Applied**, preserving the `run.describe()` diagnostic. |
| 5 | `test_short_and_long_aliases_select_the_same_task` should also exercise the long forms | **Applied**, and widened: the test is now parametrized over **all five task flags plus both short aliases** (7 cases), so every flag is independently pinned rather than only the two aliases. This is the module whose whole job is pinning flag resolution for the Phase 6 consolidation, so the gap was worth closing properly. |
