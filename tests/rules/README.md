# Rule-module tests (`tests/rules/`)

These are the per-dataset unit tests for the PDS3 and PDS4 **rule modules**
(`src/pdsfile/pds{3,4}file/rules/*.py`). They live here as standalone test
modules rather than inline in the rule modules, so that importing `pdsfile` does
not need `pytest` at runtime.

## Layout

```
tests/rules/
├── support.py        # shared helpers (was the two rules/pytest_support.py, merged)
├── pds3/test_<dataset>.py
└── pds4/test_<dataset>.py
```

- `tests/rules/support.py` — `PDS3_TEST_RESULTS_DIR`, `PDS4_TEST_RESULTS_DIR`
  (golden roots under `tests/golden/full/pds{3,4}/`), the translator helpers
  `translate_all` / `unmatched_patterns`, and `versions_test`; it re-exports the
  cross-PDS helpers (`opus_products_test`, `associated_abspaths_test`,
  `instantiate_target_pdsfile`) from `tests/support/pdsfile_test_helper.py`.
- Each `test_<dataset>.py` carries an explicit import header (no star imports);
  where a test references a rule module's production translator table (e.g.
  `associations_to_volumes`), it imports that name from the rule module.

Run them like the rest of the suite (holdings env vars required):

```
python -m pytest tests/rules/pds3 tests/rules/pds4 --mode ns
```

## Core tests (every dataset)

Every `test_<dataset>.py` has the three core tests, unchanged from the inline
originals:

- `test_opus_products` — OPUS product enumeration vs the golden copy.
- `test_associated_abspaths` — associated-file enumeration vs the golden copy.
- `test_opus_id_to_primary_logical_path` — OPUS-ID round-trip.

## Extra tests present today

| Dataset (PDS3) | Extra tests beyond the core three |
|---|---|
| `COCIRS_xxxx` | `test_associations_to_volumes`, `test_associations_to_diagrams` |
| `CORSS_8xxx` | `test_default_viewables`, `test_associations` |
| `COUVIS_8xxx` | `test_versions` |
| `GO_0xxx` | `test_duplicated_products` |

All other PDS3 datasets and all three PDS4 datasets
(`cassini_iss_fring_mosaics_rsfrench2025`,
`cassini_uvis_solarocc_beckerjarmak2023`, `uranus_occs_earthbased`) carry only
the core three. (`cassini_iss` and `cassini_vims` have **no** rule tests — their
only test-shaped content was a commented-out block, removed with the dead
`pytest` imports; there is no `test_cassini_iss.py` / `test_cassini_vims.py`.)

## Additive-coverage applicability (deferred)

The modernization plan's *additive-coverage* step — adding the missing
`test_versions` / `test_associations` / `test_duplicated_products` and generating
their goldens with `--update` — is **deferred to a follow-up PR**, pending an
investigation into why some full-holdings goldens do not reproduce on the local
`/data/pdsdata` copy while passing on the limited testing copy. No goldens are
modified here.

This table records, for each dataset, whether each additive test is already
present (**✓**), is **deferred** (the underlying rule table exists and is
non-trivial, so a test would be meaningful and should be added later), or is
**N/A** (the rule table is null/absent, so the test would be vacuous).

Legend: **✓** present · **deferred** worth adding · **N/A** no applicable rule table

| Dataset | `test_versions` (VERSIONS) | `test_associations` (ASSOCIATIONS) | `test_duplicated_products` (OPUS_PRODUCTS) |
|---|---|---|---|
| `COCIRS_xxxx` | deferred | ✓ [^assoc] | deferred |
| `COISS_xxxx` | N/A | deferred | deferred |
| `CORSS_8xxx` | deferred | ✓ | deferred |
| `COUVIS_0xxx` | N/A | deferred | deferred |
| `COUVIS_8xxx` | ✓ | deferred | deferred |
| `COVIMS_0xxx` | N/A | deferred | deferred |
| `COVIMS_8xxx` | deferred | deferred | deferred |
| `EBROCC_xxxx` | N/A | deferred | deferred |
| `GO_0xxx` | deferred | deferred | ✓ |
| `HSTxx_xxxx` | N/A | deferred | deferred |
| `NHxxxx_xxxx` | deferred | deferred | deferred |
| `VGISS_xxxx` | N/A | deferred | deferred |
| `VG_28xx` | deferred | deferred | deferred |
| `cassini_iss_fring_mosaics_rsfrench2025` | N/A | deferred | deferred |
| `cassini_uvis_solarocc_beckerjarmak2023` | N/A | deferred | deferred |
| `uranus_occs_earthbased` | N/A | deferred | deferred |

- **`test_versions`** column: **✓**/**deferred** where the rule module defines a
  non-trivial `VERSIONS` translator (`all_versions()` can return more than the
  file itself); **N/A** where it does not.
- **`test_associations`** / **`test_duplicated_products`**: every dataset defines
  `ASSOCIATIONS_TO_*` translators and an `OPUS_PRODUCTS` table, so these are
  never N/A — the ones without a test are deferred, not inapplicable.

[^assoc]: `COCIRS_xxxx` covers associations through the translator-level
    `test_associations_to_volumes` / `test_associations_to_diagrams` rather than
    the `test_associations` shape used by `CORSS_8xxx`; both count as association
    coverage.
