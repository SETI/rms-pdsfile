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
| Adversarial pre-PR review loop | See `round-*.md` in this directory. |

`ENABLE_PYTEST` in `scripts/run-all-checks.sh` stays `false`; PR-14 flips it.

## Full-data suite vs. the recorded baseline (§6.2)

Baseline: the PR-09 record (`critiques/pr-09/round-1.md`) — `--mode ns`
679 passed / 34 skipped, `--mode s` 555 passed / 3 skipped — **re-confirmed on
this machine before any edit** and captured as a per-test set, not just counts.

Against the goldens' reference root:

| Mode | Baseline | After PR-13 | Set diff |
|---|---|---|---|
| `ns` | 713 tests: 679 passed / 34 skipped | 814 tests: 780 passed / 34 skipped | **0 removed, 0 outcome changes**, 101 added — all in `tests.holdings_maintenance` |
| `s` | 558 tests: 555 passed / 3 skipped | 558 tests: 555 passed / 3 skipped | **identical set** |

No pre-existing test changed outcome in either mode. The only delta is the 101
new tests, which is the PR's deliverable.

`--mode s` is unchanged by design: the tool tests drive each tool in its own
subprocess, so `use_shelves_only` (which `--mode` flips inside the pytest process
only) cannot affect them. Running them a second time would add cost and no
signal; the reason is recorded in a comment in
`scripts/automated_tests/pdsfile_main_test.sh`.

## Tool tests against **both** holdings roots

| Root | Result |
|---|---|
| the goldens' reference root | **101 passed**, 0 skipped, 92 s |
| the complete set | **101 passed**, 0 skipped, 451 s |

No module skipped against either root, and the committed goldens matched
byte-for-byte against both. That is the point of the design: every declared source
file was verified to be byte-identical in the two roots, and the module fixture
re-verifies size and md5 at run time, so a root that ever diverges produces a
clean module skip rather than a golden mismatch (see the sub-plan, §2.1 — the two
roots are *not* identical in general; the reference root stores most large binary
products as zero-byte placeholders).

### Cost

Against the reference root the 101 tool tests add ~92 s. Against the complete set
the isolated run is 451 s, but **263 s of that is the pre-existing session
preload** of the complete tree (measured by running only the holdings-free
`test_crlf.py` against it: 16 passed in 263 s). That preload is paid once per
pytest session and is already paid by today's suite, so the marginal cost of
adding `tests/holdings_maintenance/` to the existing not-shelves-only invocation
is ~190 s, not 451 s.

Most of the remaining time is process startup: every tool runs as a subprocess and
each one imports `pdsfile`. Session-level staging of the declared sources (added
after a first measurement) cut the complete-set run from 624 s to 451 s by reading
and hashing each source file once per session instead of once per module.

## Holdings-free behaviour (feeds PR-14)

With `PDSFILE_TEST_HOLDINGS`, `PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR` and
`PDSFILE_TEST_DATA_DIR` all unset:

| | Result |
|---|---|
| before PR-13 | 713 skipped, **0 passed** |
| after PR-13 | 792 skipped, **22 passed** |

The 22 are the 16 `crlf` classifier tests and the 6 `shelf_consistency_check`
tests that build their own legacy-layout tree. The PR-13 spec requires the crlf
tests to "run everywhere, including the PR-14 hosted job", which the merged
collect-and-skip rule prevented: it skipped *every* item when no holdings were
available. The rule now exempts items marked `holdings_free` (a new marker,
registered in `pyproject.toml`). This is a three-line, additive change to
`tests/conftest.py`; the PR-09 **holdings-flavor machinery** (`resolve_holdings`,
the `full`/`mini`/skip resolver, the env vars, `full_holdings`,
`tests/golden/full/`) is untouched, exactly as §5 requires.

## Goldens

`tests/golden/full/holdings_maintenance/` — 12 text artifacts, **52 KB total**,
well under the 1 MB budget. None contains an absolute path: the two
`show_opus_products` goldens and the `pdsdependency` step list have the temporary
root replaced by `$DISK`. Nothing is compared as raw bytes — md5 files are
compared as a sorted `{path: md5}` mapping (the tools emit them in `os.walk`
order), archives as sorted `(name, kind, size, mtime)` member tuples, and shelf
`.py` sidecars as normalized text.

## Confidentiality (§3.4.1)

`grep -rniE "/seti/opus|/data/pdsdata|pdsdata"` over every file this PR adds or
changes returns nothing. Everything resolves from `$PDS3_HOLDINGS_DIR` /
`$PDS4_HOLDINGS_DIR`, and this record names roots by role only.

## Behaviour preservation

PR-13 adds tests and touches no tool. Five pre-existing defects were found while
writing the tests; per §6.4 none is fixed here. Each is pinned by a test whose
docstring names the defect, the source line, and the PR that owns the fix, so
that PR sees a failing pin the moment it changes the behaviour. They are listed
in `critiques/deferred-observations.md` under "From PR-13".
