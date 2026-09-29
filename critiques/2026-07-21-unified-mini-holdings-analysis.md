# Can OPUS and PdsFile share ONE mini-holdings test-data repo?

> **Status note (2026-07-25):** the mini-holdings concept was subsequently
> **removed from the PdsFile modernization effort entirely** (owner decision);
> the active plan is `plans/2026-07-25-modernization-plan.md` and the
> mini-holdings design record is `plans/2026-07-25-mini-holdings-plan.md`
> (deferred, for future discussion). References below to "PdsFile PR-10/PR-11"
> mean the *archived* v1 plan (`plans/archive/2026-07-17-modernization-plan.md`);
> those PRs were withdrawn, not executed. The analysis itself — the sharing
> argument and the measured size audit — remains valid input to any future
> revival.

**Date:** 2026-07-21, revised 2026-07-25
**Question:** The PdsFile modernization plan creates `rms-pdsfile-test-data` — a
small, manufactured holdings tree so PdsFile tests run without the real archive.
OPUS has the same problem. Could **one common mini-holdings repo** serve both?
**New constraint (owner, 2026-07-25):** the mini-holdings must not exceed
**10 MB**.

**Short answer:** **Yes — unify — but the 2026-07-25 size audit reverses the
key reconciliation this file previously recommended.** The PdsFile plan's PR-10
stub policy ("zero-filled stubs of the **original byte size**") produces a
**~1 GB working tree** from the golden-referenced product set alone; it is
incompatible with the 10 MB cap and must flip to **OPUS's tiny-stub policy**
(1-byte stand-ins, original sizes recorded in the manifest only). With that
flip plus four smaller PR-10 policy changes (§4b), the shared tree fits in
**~8–10 MB of working tree** — measured, not guessed (§3). Everything else in
the earlier unification argument survives and is strengthened: the stub-policy
reconciliation that previously asked OPUS to accept PdsFile's policy now goes
the other way, so OPUS's PR-19 fixture recipe needs *no* change at all to
consume the shared repo.

> **Revision history.** The first draft assumed OPUS's holdings-free tests
> would need shelves, full index tables, and the full ~30 import volumes; the
> 2026-07-21 revision corrected all three against the actual OPUS plan (PR-19
> subsets one bundle per format, truncated, shelf-free, frozen counts). The
> **2026-07-25 revision** adds a measured size audit against the owner's new
> 10 MB cap, reverses the stub-policy reconciliation (original-size zero-fill →
> 1-byte stubs), and records verification results for the factual claims both
> plans and this file make (§7).

*Analysis only — nothing is changed in either plan. §5 lists the plan edits
this analysis implies.*

---

## 1. What each side actually reads / builds (verified against code + both plans)

### 1a. OPUS import at runtime (production + self-hosted integration)

OPUS import runs **PdsFile in shelves-only + require-shelves mode by default**
(verified 2026-07-25: `main_opus_import.py:419-424` — `use_shelves_only()`
under the `dont_use_shelves_only` guard, `require_shelves(True)` unconditional
at :423, PDS4 equivalents commented out). It opens the real metadata/index
tables (`pdstable.PdsTable`, `import_util.py:296-301`; primary index per
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
  (Correction: COISS_2xxx has **no supplemental index** in
  `metadata/COISS_2xxx/COISS_2002/` — the five tables there are index,
  inventory, and the moon/ring/saturn summaries; supplemental indexes exist
  for other volsets, e.g. COUVIS_0xxx. The OPUS plan's list should read
  "supplemental index where present." Harmless, but an executor grepping for
  the file would stall.)
- **1-byte data stand-ins** at each surviving path. (Correction to the OPUS
  plan's stated rationale: `do_import.py:1624-1626` emits a
  `log_nonrepeating_warning` on zero size, **not an error** — verified
  2026-07-25. Zero-byte stand-ins would import with warnings; 1-byte remains
  the right choice because it costs nothing and keeps the warning stream
  clean, but it is a preference, not a hard requirement.)
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
**zero-filled stubs at original byte size** (reversed by this analysis — §4);
**dogfooded info/link/index shelves** self-consistent with the stub bytes. A
**separate public repo** (`rms-pdsfile-test-data`), resolved via
`PDSFILE_TEST_DATA_DIR`.

---

## 2. The two fixtures are close cousins — here is exactly where they differ

Both subset real metadata tables, truncate them, stub the data products, and
never read raw bytes. They differ in four concrete, reconcilable ways:

| Dimension | PdsFile PR-10 | OPUS PR-19 | Reconciled (shared repo) |
|---|---|---|---|
| **Data-product stubs** | zero-filled at **original byte size** | **1-byte** | **1-byte stubs, original size + mtime recorded in the manifest** — the reverse of this file's earlier recommendation. Original-size zero-fill is a ~1 GB working tree (§3) and blows the 10 MB cap; the git *repo* compresses zeros away but every checkout writes them back out. PdsFile's mini goldens are re-baselined against the tree anyway (PR-11's override model), so stub-consistent `size=1` values land in `mini/` overrides exactly like any other tree-shape fact. |
| **Shelves** | dogfooded + committed | **none** (`--dont-use-shelves-only` + `os.stat`) | **Present** (PdsFile builds them anyway; over 1-byte stubs they record `size=1`, self-consistent with the tree). OPUS then *chooses*: keep `--dont-use-shelves-only` (identical results — both paths see 1-byte files), or test the **production shelves-only path for free** (§4). |
| **Truncation + expected values** | truncate, mini-flavor goldens (stub-consistent) | truncate, freeze counts from first run | **Same philosophy** (both re-baseline against the truncated tree). Requires **one shared truncation** of any co-used volume so shelves + both projects' goldens agree (§4). |
| **Location** | separate public repo | inside rms-opus `tests/…/fixtures/` | Separate public repo; **OPUS points at it** via env var instead of committing its own copy. |

With the stub policy flipped to 1-byte, **OPUS's PR-19 recipe is now a strict
subset of the shared repo's recipe** — the shared tree is byte-for-byte what
PR-19 would have built for COISS_2002 + the PDS4 bundle, plus more volumes and
the shelves OPUS may ignore. The remaining headline stands: OPUS avoids shelves
in PR-19 largely because generating them is work OPUS did not want to own;
PdsFile's PR-10 dogfooding owns exactly that work, so unification lets OPUS
optionally test the production shelves-only path instead of the
`--dont-use-shelves-only` bypass — a test-quality upgrade OPUS gets for free.

---

## 3. Size audit against the 10 MB cap (measured 2026-07-25)

Measured on `/data/pdsdata/holdings` + `pds4-holdings`, driven by the actual
consumer footprint: the union of every product path resolved by the current
`opus_products` goldens (`tests/golden/full/`, all 16 datasets — 13 PDS3
volsets + 3 PDS4 bundles) — **1,547 unique paths across 183 volume
directories** (including `_v1`/`_v2` versioned variants). This is a lower
bound on the final access-log-seeded manifest (childnames/associations/index
tests add paths), but it captures the dominant classes.

What those 1,547 paths weigh **at real size**, by PR-10 copy class:

| Class (PR-10 policy) | Files | Real bytes | In the mini tree |
|---|---|---|---|
| Link-source text, copied real (`.lbl` 490, `.txt` 28, `.xml` 28, `.fmt` 16, `.cat`, …) | ~562 | **7.1 MB** | ~5.5–7 MB (only 2 files >100 KB; trimmable — §4b) |
| Tables (`.tab` 294, `.csv` 9) | 303 | **683 MB** | ~0.5–1.5 MB truncated (row-context knob — §4b) |
| Everything else → stubs (`.pdf` 626 MB, `.img` 131 MB, `.fit` 101 MB, `.tif` 69 MB, `.docx` 39 MB, `.dat` 19 MB, …) | ~570 | **~1,004 MB** | **~0 as 1-byte stubs; ~1 GB as original-size zero-fill** |
| Previews/diagrams, regenerated tiny (`.jpg` 145 + `.png` 83 + misc) | ~230 | 27 MB | ~0.5 MB (tiny PNG/JPG at original pixel dims) |

Plus the classes outside the product set:

- **`_icons` tree, "copied real" per PR-10:** **5.2 MB / 392 files** measured —
  more than half the entire budget, almost all in `blue/` (`png-500` icons are
  ~50 KB each). Must become access-log-subset like everything else (§4b);
  the accessed slice is plausibly ~0.2–0.5 MB.
- **Dogfooded derived trees** (info/link/index shelves + `.py` sidecars,
  checksum `.md5` files, `archives-*` tarballs of 1-byte-stub volumes):
  proportional to mini file count, est. **~0.5–1 MB**.
- **Manifest** (path, size, mtime, copy-class for every entry): est.
  **~0.5 MB**.
- **`.git`:** roughly the compressed content, est. **~2–4 MB** on a fresh
  clone.

**Bottom line:** with the §4b policy set, the working tree lands at
**~8–10 MB** — inside the cap, with little slack. If the 10 MB cap is meant to
include `.git` (i.e. total clone size), the knobs to turn are truncation
context (+10 rows instead of +100 saves ~2–4 MB) and role-based trimming of
the copied-real text class (§4b); ~7 MB tree + ~2.5 MB `.git` is achievable.
Under the **original PR-10 policy** the same footprint is **~1 GB of working
tree** — the zero-fill claim in this file's earlier draft ("compresses to
~nothing in git") was true of the repository object store and irrelevant to
every checkout, CI runner, and the cap.

Two structural observations from the same audit:

- **The `.tab` extension is not a metadata marker.** 683 MB of the
  golden-referenced `.tab` bytes are mostly *science data products*
  (occultation profiles, cumulative volume indexes) that PR-10's
  extension-based rule ("metadata index tables (.tab/.csv) + labels: copied
  real; truncated >2,000 rows") would copy real or truncate via a
  `PdsTable` round-trip they don't need. Classification must be by **observed
  access mode** (§4b), not extension.
- **112 of the 1,547 golden paths (~7%) don't exist on either holdings root**
  (`/data/pdsdata` or `/seti/opus/pdsdata`) — nearly all
  `cassini_iss_fring_mosaics_rsfrench2025` `browse_mosaic` products. This is
  pre-existing goldens-vs-holdings drift, not a mini-tree problem (the
  generator seeds from the *access log* of a real test run, not from golden
  contents), but PR-10's executor should expect it and not chase the missing
  paths.

---

## 4. Reconciliations to make one repo serve both

1. **Stub policy = 1-byte stand-ins** (reversed from this file's earlier
   original-size-zero-fill recommendation, forced by the 10 MB cap — §3).
   Original sizes and mtimes live in the manifest, not on disk. Consequences,
   all benign: the dogfooded info shelves record `size=1` (self-consistent
   with the tree — `shelf-consistency-check` passes); PdsFile tests asserting
   sizes get `mini/` overrides exactly as PR-11 already prescribes for
   stub-dependent values; OPUS's zero-size *warning* (not error — §1b) never
   fires; preview width/height stay real because previews are regenerated at
   original pixel dimensions, so shelf `width/height` are unaffected.
2. **One shared, pinned truncation of every co-used volume** (COISS_2002
   today). The dogfooded shelves, PdsFile's mini goldens, and OPUS's frozen
   import expectations must all be generated against the **same** surviving
   row set, or they contradict each other. The generator's manifest is the
   natural home for "COISS_2002 → keep these rows." The truncation must keep
   **PdsFile's referenced rows ∪ one contiguous leading block** (OPUS's "one
   coherent observation set" is "first N rows" — a scattered
   referenced-rows-only cut would break it). The stub tree must contain every
   product that `opus_products()` resolves for those rows (both projects
   enumerate products through the same PdsFile call, so one product set
   satisfies both).
3. **Ship shelves; let OPUS choose its mode.** With dogfooded shelves present,
   OPUS's PR-19 can either keep `--dont-use-shelves-only` (unchanged — with
   1-byte stubs both modes see identical sizes) or switch its holdings-free
   import to the **production shelves-only path**. The latter is strictly
   better testing and removes the PR-02 `require_shelves` special-casing
   rationale — but it is OPUS's call, not a precondition for sharing.

PDS4 note: OPUS import currently disables shelves-only for PDS4 (#1077/#1440), so
OPUS's PDS4 bundle would run via `--dont-use-shelves-only` + `os.stat` regardless
until #1077 lands. PdsFile already dogfoods PDS4 shelves (#57), so the artifacts
exist for when OPUS is ready.

### 4b. PR-10 policy changes required by the 10 MB cap

These are the concrete edits to the PdsFile plan's PR-10 (and one to PR-11)
that the audit shows are necessary; without them the cap is unreachable or
survives only by luck:

1. **Stubs: 1-byte, not original-size zero-fill** (≈1 GB → ≈0; §4 item 1).
2. **Classify by observed access mode, not extension.** The audit-hook seed
   already records *how* each path was touched. Copy-real only what was
   **opened for reading** (labels/text parsed by `pdslinkshelf`, tables read
   via `PdsTable`, documents a test actually reads); everything merely
   stat'd/listed — including `.tab` science products and `documents/` files
   that are only enumerated — becomes a 1-byte stub. This both prevents the
   683 MB `.tab` trap (§3) and trims the copied-real text class below its
   7.1 MB worst case.
3. **`_icons`: drop the "copied real" special case** (5.2 MB — half the
   budget). Subset it by access log like every other tree; the accessed slice
   is a few hundred KB.
4. **Truncation context is a manifest knob, default small.** COISS_2002's
   index runs ~3.1 KB/row, so "+100 rows for context" costs ~300 KB *per
   table* on the widest tables; across 16 datasets that is ~2–4 MB of pure
   padding. Default to ~+10 and record the exact surviving row set per volume
   (needed anyway for reconciliation 2).
5. **Make the cap a gate, not an aim.** Replace PR-10's "aim well under
   100 MB checked out; report actual size" with the owner's hard cap: the
   generator fails (and CI checks) if the working tree exceeds 10 MB.
   Correspondingly, PR-11's fixture-expansion rule (c) — "expand iff the
   additional payload is < 5 MB compressed and < 500 files" — is far too loose
   for a 10 MB total; ~0.5–1 MB per expansion is the compatible threshold.
6. **Empty directories need manifest handling.** Git cannot store empty
   directories, and the skeleton's directory *names* are load-bearing
   (regexes, `childnames`). Do **not** solve this with `.keep`/`.gitkeep`
   files — a stray file inside a holdings directory changes `os_listdir`/
   `childnames` results and would poison goldens. The manifest records empty
   dirs and the checkout step (the same conftest fixture that re-applies
   mtimes) recreates them.

---

## 5. What each plan would change to adopt this

**PdsFile plan (do now — PR-10 has not executed yet; §4b is cheap before the
tree exists and expensive after):**
- PR-10: apply all six §4b changes (1-byte stubs, access-mode classification,
  icons subset, truncation knob + recorded row set, 10 MB hard gate, empty-dir
  manifest handling).
- PR-10: add the PDS4 bundle `uranus_occ_u0_kao_91cm` to the fixture set
  (OPUS's PDS4 spike volume); the three PDS4 bundles PdsFile already tests
  don't include it.
- PR-11: tighten expansion rule (c)'s threshold to ~0.5–1 MB (§4b item 5).
- §8.1 / §4 / §7: note the dual-consumer purpose and a "two consumers, one
  tree" coordination risk.
- Nothing about the PdsFile API freeze, decomposition, or hermetic CI changes.

**OPUS plan (its PR-19 shrinks — this is a scope *reduction*):**
- PR-19 stops building `tests/opus_import/fixtures/mini_holdings/` from scratch
  and instead **consumes the shared repo** via `PDSFILE_TEST_DATA_DIR` (the CI
  checks out the data repo at a pinned SHA, as PdsFile's PR-14 already does).
- The "subset + truncate + 1-byte stub" machinery and the ≤2-day
  `FakePds3File` fallback spike — the plan's **largest unknown** — are replaced
  by "point at the generated tree." With the stub policy now 1-byte on both
  sides, OPUS's fixture *content* assumptions need no change at all.
- OPUS optionally drops `--dont-use-shelves-only` for the shared-repo import and
  tests the production shelves-only path (and can then revisit the PR-02
  `require_shelves` change).
- OPUS keeps its own frozen import expectations and its `integration/test_api`
  goldens — regenerated against the shared tree.
- Textual fix: "supplemental index" → "supplemental index where present"
  (COISS_2002 has none — §1b).

---

## 6. Recommendation

**Unify, and stage it so neither plan is blocked on the other.** Unchanged
from the 2026-07-21 revision, with the stub policy reversed:

1. **Now, in the PdsFile plan:** adopt the §4b policy set and add the one PDS4
   bundle. This yields a `rms-pdsfile-test-data` that fits the 10 MB cap *and*
   is already a valid OPUS fixture.
2. **Later, in the OPUS plan:** point PR-19 at the shared repo instead of
   hand-building a fixture — now literally the same recipe, so this *removes*
   OPUS's single largest fixture unknown rather than adding scope.
3. **Later still:** when OPUS PDS4 shelves-only lands (#1077), the PDS4 half
   shares the production path too.

Why bother at all: both plans independently specify a miniature archive
stand-in, hermetic cloud CI, and a retained real-holdings integration suite —
the same design, twice, in different locations with (before this revision)
different stub recipes. One repo, one generator, per-project goldens is
strictly less to build (it deletes OPUS's riskiest fixture PR) and less to
maintain.

The one genuine cost of unifying is **coupling**: OPUS's holdings-free CI would
depend on a PdsFile-owned data repo and its pinned SHA. That is the same
cross-repo pin PdsFile's own CI already carries (PR-14), and it is a smaller
liability than two trees silently drifting — but it is a real coordination
surface (a shared truncation change touches both projects' goldens) and should
be owned explicitly, e.g. the data repo versioned and both consumers pinning a
SHA.

---

## 7. Verification record (2026-07-25 audit)

Claims checked against code and holdings during this revision:

**Confirmed:**
- OPUS shelves-only + require-shelves default: `main_opus_import.py:419-424`.
- COISS_2002 volume = 5.4 GB; its metadata = 18 MB (10.1 MB index at
  ~3.1 KB/row × 3,296 rows + 7.5 MB summaries/inventory).
- COISS_2002 is in the PdsFile test set (21 references across
  `tests/pds3file/` + `tests/rules/pds3/`).
- Golden coverage = 13 PDS3 volsets + 3 PDS4 bundles; their `opus_products`
  goldens resolve 1,547 unique product paths across 183 volume directories.
- `_icons` = 5.2 MB / 392 files (the `blue/` set is 5.1 MB of it).
- OPUS plan PR-19's location, no-shelves design, frozen-expectation model, and
  `FakePds3File` fallback, as described in §1b.

**Corrected:**
- `do_import.py:1624-1626` **warns** on zero size
  (`log_nonrepeating_warning`); it does not error. (OPUS plan overstates;
  1-byte stubs remain the sensible policy.)
- `metadata/COISS_2xxx/COISS_2002/` has **no supplemental index** (OPUS plan
  PR-19 step 1 names one).
- This file's earlier §4 reconciliation 1 (original-size zero-fill) is
  **withdrawn**: it implied a ~1 GB working tree; "compresses to ~nothing in
  git" ignored checkout size, which is what the 10 MB cap governs.

**Observed (informational):**
- 112 golden-referenced paths (~7%), nearly all
  `cassini_iss_fring_mosaics_rsfrench2025` browse products, exist on neither
  holdings root — pre-existing goldens/holdings drift the PR-10/PR-11
  executors should expect; the access-log seed sidesteps it.
