# Can OPUS and PdsFile share ONE mini-holdings test-data repo?

**Date:** 2026-07-21
**Question:** The PdsFile modernization plan creates `rms-pdsfile-test-data` — a
small, manufactured holdings tree so PdsFile tests run without the real archive.
OPUS has the same problem. Could **one common mini-holdings repo** serve both?

**Short answer:** **Yes, and the two modernization plans have independently
designed the same thing — but via two *different* fixture recipes, in two
different locations, neither aware of the other.** Left as written, the PdsFile
plan (PR-10) and the OPUS plan (PR-19) will each build a miniature holdings
stand-in from scratch. The single strongest argument for unifying is that
**PdsFile's PR-10 fixture generator directly solves what the OPUS plan calls its
"largest unknown" (PR-19).** Unification is very feasible; it requires three
concrete reconciliations (below), all cheap if done before either plan executes
its fixture PR and expensive to retrofit after.

> **This revises an earlier draft of this file.** The first draft assumed OPUS's
> holdings-free tests would need shelves, full index tables, and the full ~30
> import volumes. Reading the actual OPUS plan (`rms-opus/plans/
> opus_modernization_plan.md`, PR-19) corrected all three: OPUS's holdings-free
> CI deliberately runs **without shelves**, on **truncated** indexes with
> **frozen** counts, over **one bundle per format** (COISS_2002 + a PDS4
> bundle). The full 30-volume import stays on the self-hosted integration runner
> against real holdings. The correction makes unification *easier*, not harder.

*Analysis only — nothing is changed in either plan.*

---

## 1. What each side actually reads / builds (verified against code + both plans)

### 1a. OPUS import at runtime (production + self-hosted integration)

OPUS import runs **PdsFile in shelves-only + require-shelves mode by default**
(`main_opus_import.py:419-432`). It opens the real metadata/index tables
(`pdstable.PdsTable`, `import_util.py:296-301`; primary index per
`config_bundle_info.py`; geometry/inventory/supplemental tables scanned at
`do_import.py:750-772`), and pulls every product's `size/checksum/width/height`
from the **info shelf** (`pdsfile.py:1988-2003, 2098-2123`;
`do_import.py:1583-1611`). It **never opens raw data-product bytes.** This is the
path the self-hosted integration suite exercises against real holdings.

### 1b. OPUS holdings-free CI, as the OPUS plan specifies it (PR-19)

The OPUS plan does **not** reuse the production shelves-only path for its
holdings-free CI. Its PR-19 "subset, don't synthesize" fixture:

- **Subsets one bundle per format** — real `holdings/metadata/COISS_2xxx/
  COISS_2002/` index + supplemental + ring/moon summary + inventory tables,
  **truncated to the first N rows** ("one coherent observation set"), editing
  only `ROWS`/`FILE_RECORDS` in the `.lbl`; PDS4 `uranus_occ_u0_kao_91cm` the
  same way. *Not* the full ~30-volume `import_for_tests.sh` list.
- **1-byte data stand-ins** at each surviving path — "never 0 bytes
  (`do_import.py:1624-1626` errors on zero size)"; data files are only stat'd.
- **No shelves.** PR-02 moves `require_shelves(True)` inside the
  `--dont-use-shelves-only` guard, and PR-19 imports with
  `--dont-use-shelves-only` so pdsfile falls back to `os.stat`.
- **Frozen expectations:** "the asserted table contents come from the first
  successful run, reviewed once, then frozen" — i.e. OPUS *re-baselines* against
  the truncated tree; mini counts are not real-archive counts.
- **Location:** committed **inside rms-opus** at
  `tests/opus_import/fixtures/mini_holdings/` — not a separate repo.
- **Fallback:** a `FakePds3File` mock at the pdsfile boundary if pdsfile's
  directory-acceptance logic fails a ≤2-day spike.
- The OPUS plan's §8 self-critique calls this "**the plan's largest unknown.**"

### 1c. OPUS application tests

Read **only** the MySQL DB — never holdings/shelves/PdsFile on disk (the lone
`pdsfile` call, `file_utils.py:220`, rebuilds a `PdsViewSet` from a DB JSON
blob). Golden mechanism: `integration/test_api/` (411 fixtures) + `UPDATE_FILES`.
No holdings requirement of their own; they need the DB the import step builds.

### 1d. PdsFile mini (PdsFile plan PR-10)

Many volumes; directory skeleton; **real link-source text**; **real metadata
tables, truncated >2,000 rows** to referenced+100; tiny regenerated previews;
**zero-filled stubs at original byte size**; **dogfooded info/link/index
shelves** self-consistent with the stub bytes. A **separate public repo**
(`rms-pdsfile-test-data`), resolved via `PDSFILE_TEST_DATA_DIR`.

---

## 2. The two fixtures are close cousins — here is exactly where they differ

Both subset real metadata tables, truncate them, stub the data products, and
never read raw bytes. They differ in four concrete, reconcilable ways:

| Dimension | PdsFile PR-10 | OPUS PR-19 | Reconciled (shared repo) |
|---|---|---|---|
| **Data-product stubs** | zero-filled at **original byte size** | **1-byte** (only needs non-zero) | **Original-size zero-fill** — a superset: it is non-zero (satisfies OPUS's `do_import.py:1624-1626` check) *and* records the correct size in the info shelf (satisfies PdsFile). Zero-fill compresses to ~nothing in git. |
| **Shelves** | dogfooded + committed | **none** (`--dont-use-shelves-only` + `os.stat`) | **Present** (PdsFile builds them anyway). OPUS then *chooses*: keep `--dont-use-shelves-only`, or — better — test the **production shelves-only path for free** (see §4). |
| **Truncation + expected values** | truncate, mini-flavor goldens (stub-consistent) | truncate, freeze counts from first run | **Same philosophy** (both re-baseline against the truncated tree). Requires **one shared truncation** of any co-used volume so shelves + both projects' goldens agree (§3). |
| **Location** | separate public repo | inside rms-opus `tests/…/fixtures/` | Separate public repo; **OPUS points at it** via env var instead of committing its own copy. |

The headline: **OPUS avoids shelves in PR-19 largely because generating them is
work OPUS did not want to own.** The PdsFile plan *does* own exactly that work
(PR-10 dogfooding). So unification removes OPUS's reason to use the non-production
`--dont-use-shelves-only` test path — OPUS could instead test the same
shelves-only code path production uses, which is a **test-quality upgrade OPUS
gets for free**.

---

## 3. The real footprint is small — and mostly already shared

Because OPUS's *holdings-free* CI is only "prove the pipeline runs end-to-end on
one bundle per format" (broad instrument coverage comes from the obs-field-method
tests against fixture **metadata dicts**, plus the self-hosted integration suite
on real holdings), the shared repo needs, for OPUS:

- **COISS_2002** (PDS3) — **already in the PdsFile test set** (22 references).
- **`uranus_occ_u0_kao_91cm`** (PDS4) — add to the shared repo if not present.

That's it for OPUS's holdings-free needs. The other ~28 volumes in
`import_for_tests.sh` (COISS_2008/2111, COUVIS_0002, the HST/NH/VG/occultation
volumes, etc.) are exercised **only** by the self-hosted integration suite, which
uses **real holdings** and does **not** touch the mini repo at all. So the
"union of ~40 volumes" figure from the first draft was wrong: the *shared* repo
needs the PdsFile volume set **plus one PDS4 bundle**, because OPUS's mini-CT
footprint is essentially a subset of PdsFile's.

**Size** (measured against `/data/pdsdata/holdings`): the huge thing —
data products (COISS_2002 alone = 5.4 GB of pixels) — is stubbed to ~0 for both.
COISS_2002 metadata is 18 MB (10 MB index + 7.5 MB geometry summaries); after
PR-19-style truncation to one observation set it is a few hundred KB. So the
shared repo stays essentially at the PdsFile plan's own size target; OPUS adds
one small PDS4 bundle.

---

## 4. Three reconciliations to make one repo serve both

1. **Stub policy = original-size zero-fill** (not 1-byte). Superset of both
   needs; keeps the info shelf's `size` correct while staying non-zero for
   OPUS's zero-size guard. (If any real product is genuinely 0 bytes — none
   known — it must be forced to ≥1 byte for OPUS.)
2. **One shared, pinned truncation of every co-used volume** (COISS_2002 today).
   The dogfooded shelves, PdsFile's mini goldens, and OPUS's frozen import
   expectations must all be generated against the **same** surviving row set, or
   they contradict each other. The generator's manifest is the natural home for
   "COISS_2002 → keep these rows." The stub tree must contain every product that
   `opus_products()` resolves for those rows (both projects enumerate products
   through the same PdsFile call, so one product set satisfies both).
3. **Ship shelves; let OPUS choose its mode.** With dogfooded shelves present,
   OPUS's PR-19 can either keep `--dont-use-shelves-only` (unchanged) or switch
   its holdings-free import to the **production shelves-only path**. The latter
   is strictly better testing and removes the PR-02 `require_shelves` special-
   casing rationale — but it is OPUS's call, not a precondition for sharing.

PDS4 note: OPUS import currently disables shelves-only for PDS4 (#1077/#1440), so
OPUS's PDS4 bundle would run via `--dont-use-shelves-only` + `os.stat` regardless
until #1077 lands. PdsFile already dogfoods PDS4 shelves (#57), so the artifacts
exist for when OPUS is ready.

---

## 5. What each plan would change to adopt this

**PdsFile plan (small, forward-compatible — do now even if OPUS decides later):**
- PR-10: make truncation a **per-volume manifest flag** (already needed for the
  override-model goldens) and record the **exact surviving row set** for any
  co-used volume, so the tree is reproducible for both consumers.
- PR-10: add the PDS4 bundle `uranus_occ_u0_kao_91cm` to the fixture set (OPUS's
  PDS4 spike volume) if not already covered.
- §8.1 / §4 / §7: note the dual-consumer purpose and a "two consumers, one tree"
  coordination risk.
- Nothing about the PdsFile API freeze, decomposition, or hermetic CI changes.

**OPUS plan (its PR-19 shrinks — this is a scope *reduction*):**
- PR-19 stops building `tests/opus_import/fixtures/mini_holdings/` from scratch
  and instead **consumes the shared repo** via `PDSFILE_TEST_DATA_DIR` (the CI
  checks out the data repo at a pinned SHA, as PdsFile's PR-14 already does).
- The "subset + truncate + 1-byte stub" machinery and the ≤2-day
  `FakePds3File` fallback spike — the plan's **largest unknown** — are replaced
  by "point at the generated tree," because PR-10's generator already produced a
  self-consistent COISS_2002 subset (with shelves).
- OPUS optionally drops `--dont-use-shelves-only` for the shared-repo import and
  tests the production shelves-only path (and can then revisit the PR-02
  `require_shelves` change).
- OPUS keeps its own frozen import expectations and its `integration/test_api`
  goldens — regenerated against the shared tree.

---

## 6. Recommendation

**Unify, and stage it so neither plan is blocked on the other.**

1. **Now, in the PdsFile plan (which is ready to execute and is the one that
   builds the generator):** adopt the two cheap forward-compatible choices in §5
   — per-volume truncation flag + the recorded row set, and add the one PDS4
   bundle. This yields a `rms-pdsfile-test-data` that is *already* a valid OPUS
   fixture, at essentially no extra cost or size.
2. **Later, in the OPUS plan (whose PR-19 is deep in Phase E, gated behind five
   phases of packaging/framework work):** point PR-19 at the shared repo instead
   of hand-building a fixture. This *removes* OPUS's single largest fixture
   unknown rather than adding scope.
3. **Later still:** when OPUS PDS4 shelves-only lands (#1077), the PDS4 half
   shares the production path too.

The sequencing is favorable by default: PdsFile *builds the generator first*
because it gets there first; OPUS *needs a generator it hasn't built* and arrives
later. The only ask of the PdsFile plan today is two small design choices that
are far cheaper now than after the tree is generated and committed.

Why bother at all: both plans independently specify a miniature archive
stand-in, hermetic cloud CI, and a retained real-holdings integration suite —
the same design, twice. Worse, they specify *different* fixture recipes in
*different* locations, so without coordination the Node maintains two
divergent mini-holdings trees, two generators, two manifests, and two
regeneration runbooks — for what is fundamentally the same artifact consumed by
two clients of the same PdsFile shelf/metadata abstraction. One repo, one
generator, per-project goldens is strictly less to build (it deletes OPUS's
riskiest fixture PR) and less to maintain.

The one genuine cost of unifying is **coupling**: OPUS's holdings-free CI would
depend on a PdsFile-owned data repo and its pinned SHA. That is the same
cross-repo pin PdsFile's own CI already carries (PR-14), and it is a smaller
liability than two trees silently drifting — but it is a real coordination
surface (a shared truncation change touches both projects' goldens) and should be
owned explicitly, e.g. the data repo versioned and both consumers pinning a SHA.
