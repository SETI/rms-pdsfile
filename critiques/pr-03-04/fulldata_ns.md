# PR-03+04 full-data suite record (`--mode ns`)

Invocation (holdings roots resolved from `PDS3_HOLDINGS_DIR` /
`PDS4_HOLDINGS_DIR`; the **limited testing holdings copy** is used — the set the
test goldens are tuned to — not the complete `/data/pdsdata` set):

```
pytest tests/api/ pdsfile/pds3file/tests/ pdsfile/pds3file/rules/*.py \
       pdsfile/pds4file/tests/ pdsfile/pds4file/rules/*.py --mode ns
```

Result: **679 passed, 34 skipped, 0 failed** (28.32s).

The 34 skips are legitimate — PDS4 bundles (`cassini_iss_fring_mosaics_...`,
`cassini_iss_spokes_...`) not present in the reference holdings set; the tests
skip with a reason rather than failing.

## Behavior preservation

This PR (PR-03 + PR-04) is config-only: `git diff --stat rewrite..HEAD --
pdsfile/` is empty, so no test logic changed. The full-data pass/fail set is
determined entirely by the (unchanged) `pdsfile/` source and the holdings, so it
is unchanged by this PR.

## Root-dependent goldens on the complete `/data/pdsdata` set (not a rewrite regression)

Run against the *complete* `/data/pdsdata` set, the same suite reported 6 failures:

```
FAILED pds3file/tests/test_pds3file_blackbox.py::...::test_label_basename[...COUVIS_0001...HDAC1999_007_16_31...]
FAILED pds3file/rules/COCIRS_xxxx.py::test_opus_products[...COCIRS_0406...]
FAILED pds3file/rules/CORSS_8xxx.py::test_opus_products[...CORSS_8001...]
FAILED pds3file/rules/CORSS_8xxx.py::test_opus_id_to_primary_logical_path
FAILED pds3file/rules/COVIMS_8xxx.py::test_opus_id_to_primary_logical_path
FAILED pds3file/rules/NHxxxx_xxxx.py::test_opus_id_to_primary_logical_path
```

All six are data/golden assertions (e.g. `assert abspath in opus_id_abspaths`)
whose expected values are tuned to the limited testing copy, and all six **pass**
against it. They legitimately differ against the complete `/data/pdsdata` set —
expected root-dependent behavior, not a change in this PR. Local test runs use
the limited testing copy from now until a later phase (owner, 2026-07-23).
Recorded here so the difference is neither blamed on the rewrite nor silently
absorbed.
