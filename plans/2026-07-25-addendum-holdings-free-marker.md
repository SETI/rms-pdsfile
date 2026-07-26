# Addendum to the active plan — the `holdings_free` marker (PR-13)

**Date:** 2026-07-25
**Active plan:** `2026-07-25-modernization-plan.md`
**Raised by:** PR-13 (`test: maintenance-tool test suite`, issue #82)
**Status:** awaiting owner acknowledgement (§6.4: deviations are recorded as dated
addendum files here and acknowledged before the deviating change merges)

PR-13 makes two departures from the letter of the active plan. Both are small,
both are forced by PR-13's own stated deliverables, and both are described here so
the owner can accept or reject them explicitly.

## 1. PR-13 modifies PR-09's collect-and-skip rule

**What the plan says.** §5 of the active plan: "The merged holdings-flavor
machinery (PR-09) is intentionally left exactly as it is — no PR here touches it."

**What PR-13 also has to satisfy.** The PR-13 section requires the `crlf.py`
classifier tests to be "**holdings-free**; these run everywhere, including the
PR-14 hosted job." PR-09's rule makes that impossible: when no holdings are
available it adds a skip marker to *every* collected item, without exception, so a
test that needs no holdings at all is skipped anyway.

**The change.** Three lines in `tests/conftest.py`: items carrying a new
`holdings_free` marker are exempted from the blanket skip. The marker is
registered in `pyproject.toml` alongside `full_holdings`.

**What is deliberately not touched**, i.e. everything ground rule 3 enumerates as
the retained mini-ready plumbing:

- the `full` / `mini` / skip resolver in `tests/support/holdings.py`
- the `PDSFILE_TEST_HOLDINGS` and `PDSFILE_TEST_DATA_DIR` env vars
- the `full_holdings` marker and its mini-flavor skip branch
- the `tests/golden/full/` layout

The mini flavor stays dormant: nothing sets `PDSFILE_TEST_DATA_DIR`, so it is
never selected.

**Effect.** With no holdings env vars set, the suite goes from 713 skipped /
**0 passed** to 794 skipped / **23 passed** — the 17 `crlf` classifier tests and
the 6 `shelf_consistency_check` tests that build their own tiny tree. Collection
stays clean. PR-14 inherits a working mechanism for its hosted lint/no-holdings
job, and should extend the marker to the other genuinely holdings-free tests its
spec names (the API-freeze test in particular — recorded as entry 9 in
`critiques/deferred-observations.md`).

**If rejected:** the `crlf` tests still exist and still pass wherever holdings are
present; they would simply be skipped on a runner without holdings, and PR-14
would have to make this same change itself.

## 2. `tests/holdings_maintenance/` is added to one suite invocation, not both

**What the plan says.** The PR-13 section: "Update
`scripts/automated_tests/pdsfile_main_test.sh` to include
`tests/holdings_maintenance/` in the suite paths."

**What PR-13 did.** Added it to the not-shelves-only (`--mode ns`) invocation
only, not to the shelves-only (`--mode s`) one.

**Why.** `--mode` flips `use_shelves_only` inside the pytest process. The tool
tests drive every tool in its own subprocess, which inherits none of that, so the
two modes would execute byte-identical work. Adding them to the second invocation
would roughly double their contribution to suite time and produce no additional
signal. The reason is also recorded in a comment in the script itself.

**If rejected:** adding `tests/holdings_maintenance/` to the `--mode s` invocation
is a one-line change.
