# PR-13 — validation record

`test: maintenance-tool test suite` (closes issue #82).
Base: `rewrite` @ 8d5cf16. Tests only — **no file under `src/pdsfile/` is touched**.

Holdings roots are referred to by role only, never by path (§3.4.1):

- **the goldens' reference root** — the limited testing copy the golden files are
  tuned to, resolved from `$PDS3_HOLDINGS_DIR` / `$PDS4_HOLDINGS_DIR`.
- **the complete set** — the full real holdings, same two variables.

## Active gates (§2 table)

| Gate | Result |
|---|---|
| `ruff check` (ratcheted) | **Pass.** Clean with **no new `per-file-ignores` entry**; the ratchet block in `pyproject.toml` is untouched. |
| API-freeze manifest test | **Pass** (1 passed). PR-13 changes nothing under `src/`, so the manifest cannot move; the run confirms it. |
| Clean-install import check | **Pass** — "all runtime modules import with no dev extras". |
| Full-data suite, both modes | **Pass**, per-test set diffed below. |
| Adversarial review loop | Six rounds. 1-4 before the PR was opened: all `goal met`, zero Major. Round 5, after the CI failure: **`goal not met`**, 2 Major, both fixed. Round 6, scoped confirmation: `goal met`, zero new Major. See `round-1.md` … `round-6.md`. |

`ENABLE_PYTEST` in `scripts/run-all-checks.sh` stays `false`; PR-14 flips it.

## Full-data suite vs. the recorded baseline (§6.2)

Baseline: the PR-09 record (`critiques/pr-09/round-1.md`) — `--mode ns`
679 passed / 34 skipped, `--mode s` 555 passed / 3 skipped — **re-confirmed on
this machine before any edit** and captured as a per-test set, not just counts.

Against the goldens' reference root:

| Mode | Baseline | After PR-13 | Set diff |
|---|---|---|---|
| `ns` | 713 tests: 679 passed / 34 skipped | 824 tests: 790 passed / 34 skipped | **0 removed, 0 outcome changes**, 111 added — all in `tests.holdings_maintenance` |
| `s` | 558 tests: 555 passed / 3 skipped | 558 tests: 555 passed / 3 skipped | **identical set** |

No pre-existing test changed outcome in either mode. The only delta is the 111
new tests, which is the PR's deliverable.

`--mode s` is unchanged by design: the tool tests drive each tool in its own
subprocess, so `use_shelves_only` (which `--mode` flips inside the pytest process
only) cannot affect them. Running them a second time would add cost and no
signal; the reason is recorded in a comment in
`scripts/automated_tests/pdsfile_main_test.sh`.

## What this record claimed before, and what CI showed

The first version of this record said the suite was green, and it was — on two
holdings roots, on one machine. **CI then failed**, on one test, for a reason
neither root could expose: `pdsdependency` emits its "Steps required" plan in
directory-enumeration order, which is a property of the *filesystem the temporary
tree is built on*, not of the holdings root being read. The development machine
and the CI runner enumerate the same tree differently, so the committed golden
matched here and not there.

A second CI failure then made the same point again from a different angle: an
unrelated dependency emits a deprecation warning on Python 3.10 and not on 3.12,
and `run_tool` was merging stderr into what the golden compared, so the
`show_opus_products` golden could only ever match on some interpreters.

That is a gap in what "green on both roots" proves, and it is worth stating
plainly: passing against two holdings roots establishes that the *input data* is
equivalent, not that the *test* is environment-independent. Three axes had to be
pinned before that became true — the filesystem's enumeration order, the tool
subprocess's output streams, and (from the outset) the timezone and file mtimes. The fix removed the
dependency on an order the tool never specified, and the cross-module audit below
confirms no other artefact had the same exposure. Full analysis, including the
reproduction and the audit method, is in `ci-and-coderabbit.md` in this directory.

Two things changed as a result, both in the tests:

- The `pdsdependency` step-list golden is compared as a sorted multiset. It still
  fails if any step appears, disappears, or changes text; only the order is
  unpinned, and the ordering the tool *does* specify is asserted separately. The
  opt-in is used exactly once — every other golden's order is deterministic and
  stays pinned.
- Golden mismatches now print a unified diff. The CI log had said only "golden
  mismatch" with no indication of what differed, because a custom assertion
  message suppresses pytest's own diff. This paid for itself within one run: it
  identified the second failure's cause from the log alone.
- The tool subprocess's stdout and stderr are captured separately, and anything
  compared against a golden or parsed for structure reads **stdout only**. stderr
  carries whatever the interpreter and the installed libraries choose to emit,
  which is no part of a tool's output.

## Tool tests against **both** holdings roots

| Root | Result |
|---|---|
| the goldens' reference root | **111 passed**, 0 skipped |
| the complete set | **111 passed**, 0 skipped |

No module skipped against either root, and the committed goldens matched
byte-for-byte against both. That is the point of the design: every declared source
file was verified to be byte-identical in the two roots, and the module fixture
re-verifies size and md5 at run time, so a root that ever diverges produces a
clean module skip rather than a golden mismatch (see the sub-plan, §2.1 — the two
roots are *not* identical in general; the reference root stores most large binary
products as zero-byte placeholders).

### Cost

Against the reference root the tool tests add ~119 s serially, or ~38 s under
`pytest -n 4` (they are independent, so xdist works). Against the complete set an
isolated run is several minutes longer, but most of that is the **pre-existing
session preload** of the complete tree: running only the holdings-free
`test_crlf.py` against it takes 263 s on its own. That preload is paid once per
pytest session and is already paid by today's suite, so the marginal cost of
adding `tests/holdings_maintenance/` to the existing not-shelves-only invocation
is roughly the reference-root figure plus source staging.

Most of the remaining time is process startup: every tool runs as a subprocess and
each one imports `pdsfile`. Session-level staging of the declared sources cut the
first complete-set measurement from 624 s to 451 s by reading and hashing each
source file once per session instead of once per module.

## Holdings-free behaviour (feeds PR-14)

With `PDSFILE_TEST_HOLDINGS`, `PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and
`PDSFILE_TEST_DATA_DIR` all unset:

| | Result |
|---|---|
| before PR-13 | 713 skipped, **0 passed** |
| after PR-13 | 801 skipped, **23 passed** |

The 23 are the 17 `crlf` classifier tests and the 6 `shelf_consistency_check`
tests that build their own legacy-layout tree. The PR-13 spec requires the crlf
tests to "run everywhere, including the PR-14 hosted job", which the merged
collect-and-skip rule prevented: it skipped *every* item when no holdings were
available. The rule now exempts items marked `holdings_free` (a new marker,
registered in `pyproject.toml`). This is a three-line, additive change to
`tests/conftest.py`; the PR-09 **holdings-flavor machinery** (`resolve_holdings`,
the `full`/`mini`/skip resolver, the env vars, `full_holdings`,
`tests/golden/full/`) is untouched, exactly as §5 requires.

## Goldens

`tests/golden/full/holdings_maintenance/` — 11 text artifacts, **~12 KB of
content** (52 KB of disk blocks), far under the 1 MB budget. None contains an
absolute path: the tools emit logical paths, and where a temporary root could
appear (the `pdsdependency` step list) it is replaced by `$DISK`. Nothing is
compared as raw bytes — md5 files are compared as a sorted `{path: md5}` mapping
(the tools emit them in `os.walk` order), archives as sorted
`(name, kind, size, mtime)` member tuples, and shelf `.py` sidecars as normalized
text.

`show_opus_products`' table output has **no** golden: it is rendered by
`tabulate`, whose formatting is not ours to pin, so that test asserts structure
(the file, each opus type, each product's logical path) and the byte-exact golden
covers the `--pprint` output instead.

## Confidentiality (§3.4.1)

Every file this PR adds or changes was grepped for the absolute prefixes of both
real holdings roots and for the shared parent directory name they sit under: no
match. Everything resolves from `$PDS3_HOLDINGS_DIR` / `$PDS4_HOLDINGS_DIR`, and
this record names roots by role only.

## Deviations from the active plan

Four, all written up for owner acknowledgement in
`plans/2026-07-25-addendum-holdings-free-marker.md`: the `holdings_free` exemption
in PR-09's collect-and-skip rule; adding the tool tests to one suite invocation
rather than both; the source tables living in `subsets.py` and aliased one line per
module rather than copied into each; and invoking every tool as
`python -m <module>` rather than `python <path>.py`.

## Behaviour preservation

PR-13 adds tests and touches no tool. Seven pre-existing defects were found while
writing the tests and during the review rounds; per §6.4 none is fixed here. Each is pinned by a test that
asserts today's behaviour and points at the numbered entry under "From PR-13" in
`critiques/deferred-observations.md`, where the defect, its location and the
owning PR are written up. Whichever PR changes the behaviour will see the pin
fail.

## Test independence

Every test rebuilds its module's tree from the local source stage before it runs,
so none depends on another. Verified two ways: individual test ids pass in
isolation, and the whole tool-test suite passes under `pytest -n 4`.
