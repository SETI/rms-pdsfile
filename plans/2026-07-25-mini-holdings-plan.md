# Mini-holdings / hermetic test data — deferred plan

**Date:** 2026-07-25
**Status:** DEFERRED — for future discussion. Not scheduled; no PR in the
active modernization plan (`plans/2026-07-25-modernization-plan.md`) depends
on anything here. This document exists so the design work already done is not
lost and so a future decision starts from the current state of the analysis,
not from scratch.

**Owner decision (2026-07-25):** the mini-holdings concept is removed from the
modernization effort. Testing continues against real holdings (complete or
limited copies) on self-hosted runners and machines that have them, with
graceful skip elsewhere. If mini-holdings is ever revived, it must fit a
**hard 10 MB size cap** and the open design fork in §4 must be resolved first.

---

## 1. What this would be for

The motivation (unchanged from the original plan's goal G3): a way for the
default test suite to exercise PdsFile's data-dependent behavior **without
access to the real archive** — on stock GitHub-hosted runners, on
contributors' machines, cross-OS. Secondary motivation: rms-opus's
modernization plan (PR-19 there) needs the same artifact for its holdings-free
import CI, and one shared fixture could serve both — see
`critiques/2026-07-21-unified-mini-holdings-analysis.md` (the "unified
analysis"),
which studies that sharing in detail and carries the measured size audit.

What exists today that a revival would build on:

- `SETI/rms-pdsfile-test-data` — public repo, **empty**; stays empty.
- The modernization plan's PR-09 (merged, #103) built a full/mini/skip
  holdings resolver in `tests/support/holdings.py`, with the
  `PDSFILE_TEST_HOLDINGS`/`PDSFILE_TEST_DATA_DIR` env vars, the
  `full_holdings` marker, and the `tests/golden/full/` layout (the base tier
  of the override-golden model). **All of it stays in place, dormant**
  (owner, 2026-07-25) — a revival plugs into it directly; nothing needs
  recovering from git history.
- The archived v1 modernization plan
  (`plans/archive/2026-07-17-modernization-plan.md`) contains the withdrawn
  full specs: PR-10 (fixture-tree generator), PR-11 (override-model goldens +
  hermetic audit), PR-12 (pytest-xdist), and PR-14's hermetic CI matrix +
  test-data SHA pinning. This document summarizes them; the archive holds the
  verbatim text.

## 2. Summary of the withdrawn v1 design (the "mini tree" approach)

One sentence: a generator (`make_test_holdings.py`) runs on a machine with
real holdings, records every path the test suite actually touches (a
`sys.addaudithook` access log), and emits a miniature holdings tree into the
test-data repo — real directory skeleton, real link-source text, truncated
metadata tables, tiny regenerated previews, stubbed data products, and
dogfooded (tool-generated) shelves self-consistent with the stub bytes —
which CI checks out at a pinned SHA and the suite runs against under a `mini`
flavor, with a single base golden set plus sparse `mini/` overrides for the
tests whose expected values are tree-shape facts.

Key elements worth keeping from that design (details in the archive):

- **Access-log seeding** (audit hook over a real-holdings test run) rather
  than static parsing of parametrize tables — this survives any redesign; the
  same inventory also enumerates every raw filesystem call for §4's
  alternative.
- **The override-model goldens** (base `full/` set + sparse `mini/`
  overrides written by `--update` only when the value genuinely differs) —
  kills dual-maintenance drift.
- **The PR-10 → PR-11 convergence loop** (generate → run → add missing paths
  to the manifest → regenerate) and the per-test (a)–(d) classification rule
  (passes unchanged / golden-convert / expand fixture / mark
  `full_holdings`).
- **Dogfooding order** for the derived trees (archives → checksums →
  infoshelf → indexshelf → linkshelf), archive comparison by member tuples
  (never bytes), `.gitattributes * -text`, case-collision checks, and
  manifest-carried mtimes.

## 3. The 10 MB cap and the 2026-07-25 size audit (what's wrong with v1 as written)

The owner capped the mini-holdings at **10 MB**. A measured audit against
real holdings (full numbers and method in the unified analysis, §3/§4b/§7)
showed the v1 recipe cannot meet it without six policy changes:

1. **Stubs must be 1-byte stand-ins, not zero-fill at original byte size.**
   The product paths the current `opus_products` goldens resolve total
   **~1 GB** of real size; zero-fill compresses in git's object store but
   every checkout writes the zeros back out.
2. **Copy-real vs stub must be classified by observed access mode, not
   extension** — 683 MB of golden-referenced `.tab` files are science data
   products, not metadata; the "`.tab`/`.csv` copied real, truncated
   >2,000 rows" rule is a trap.
3. **`_icons` cannot be copied whole** (5.2 MB — half the budget); subset it
   by access log like everything else.
4. **Truncation context must be a small knob** (~+10 rows, not +100 —
   COISS_2002's index runs ~3.1 KB/row).
5. **The cap must be a generator/CI gate, not an aim**, and the fixture
   expansion threshold must shrink to ~0.5–1 MB per expansion.
6. **Empty directories need manifest handling** (git can't store them;
   `.gitkeep` files would poison `childnames` results).

With those changes the tree lands at ~8–10 MB of working tree (+~2–4 MB
`.git`) — inside the cap with little slack. The irreducible core is ~5.5–7 MB
of copied-real label/text files.

## 4. The open design fork (must be resolved before any revival)

Two architectures are on the table; neither is chosen.

**Option A — mini tree (v1 amended per §3).** Real files on disk, 1-byte
stubs, dogfooded shelves consistent with stub bytes. Conventional; everything
(PdsFile, tools, OPUS) runs on a real filesystem; no mock risk. Costs:
~8–10 MB and thousands of stub files in git, mtime re-application after
checkout, manifest-recreated empty dirs, case-collision handling, and a
sizable `mini/` golden-override set (every stat'd size becomes 1).

**Option B — manifest + interception (owner-proposed 2026-07-25).** Replace
the tree with a **manifest** recording every file's path, real size, real
mtime (and checksum/pixel dims), keep on disk **only** files whose contents
are actually read (truncated metadata tables, the few parsed text files), and
intercept the filesystem calls in tests so existence/listing/stat answers
come from the manifest. Assessment (from the 2026-07-25 discussion):

- PdsFile is *already* manifest-driven in shelves-only mode; the natural,
  safe interception seam is PdsFile's own local-filesystem layer
  (`os_path_exists`/`os_path_isdir`/`os_listdir`/`glob_glob`,
  `pdsfile.py:1259–1661`, extracted as `_local_fs.py` in the active plan's
  PR-17) — **never** a global `os`/`os.path`/`glob` monkey-patch (fragile,
  affects pytest and every in-process library).
- Shelves can be **subsetted from the real shelves** (real sizes, checksums,
  dims) instead of dogfooded over stubs — then hermetic assertions return
  full-holdings-true values and the golden-override set nearly vanishes.
  Link shelves subsetted from real ones also remove the need to keep most
  label text on disk (the ~7 MB class), shrinking the repo to ~3–6 MB.
- A **materializer** (manifest → 1-byte files + copied tables in `tmp_path`)
  is needed regardless, for the maintenance-tool tests (they hash/tar real
  bytes via raw `os.walk`) and for OPUS if it keeps
  `--dont-use-shelves-only`. Build it as the second consumer of the same
  manifest.
- "Every file" needs scoping: a full inventory of the tested volumes is too
  big (COISS_2002 alone is 36k files; its real info shelf pair is 5.1 MB).
  The manifest stays access-log-scoped.
- Coherence rule: shelf values and stat values must agree within a run —
  real-value shelves pair with interception; stub-consistent dogfooded
  shelves pair with a materialized tree. Don't mix.
- Honest cost: the interception layer is a mock — a shim bug could pass
  hermetically while real behavior differs. Mitigation is the retained
  nightly full-data suite (the active plan's G4), plus a **time-boxed spike**
  before committing: patch the four seam methods in a throwaway conftest
  against a hand-built one-volume manifest, run the COISS blackbox tests,
  and count failures whose cause isn't a missing manifest entry. If the seam
  leaks (pervasive raw `os` calls), fall back to manifest + materializer
  only.

## 5. Relationship to rms-opus (unification)

The unified analysis' conclusion stands independent of the fork: **one shared
fixture should serve both projects** if either ever builds one. OPUS's plan
(PR-19 there) specifies subset-don't-synthesize with 1-byte stubs over
COISS_2002 + one PDS4 bundle (`uranus_occ_u0_kao_91cm`) — a strict subset of
either option here. Any revival should:
- keep one pinned truncation per co-used volume (PdsFile's referenced rows ∪
  a contiguous leading block for OPUS's "one coherent observation set");
- ship shelves so OPUS can optionally test its production shelves-only path;
- let OPUS consume the shared repo via env var + pinned SHA instead of
  committing its own copy.
Two factual corrections for the OPUS plan recorded in the analysis §7:
`do_import.py:1624` *warns* (not errors) on zero size, and COISS_2002 has no
supplemental index.

## 6. Decision points for the future discussion

1. Is hermetic data CI worth having at all, given the self-hosted PR gate
   works and the hosted lint job (active plan PR-14) covers the
   holdings-free surface? (If no — close this file and the empty data repo.)
2. If yes: Option A (mini tree) vs Option B (manifest + interception) —
   gated by the Option-B spike above.
3. Budget interpretation: does the 10 MB cap cover the working tree only, or
   the full clone including `.git`?
4. Coordination with rms-opus: build for one consumer or two from day one
   (the analysis recommends two — it deletes OPUS's riskiest fixture PR)?
5. Golden model: revive the v1 override model as-is, or (under Option B with
   real-value shelves) accept the much smaller override set it implies?

## 7. References

- `critiques/2026-07-21-unified-mini-holdings-analysis.md` — the OPUS/PdsFile
  sharing analysis + the measured 10 MB size audit (§3/§4b) + verification
  record (§7).
- `plans/archive/2026-07-17-modernization-plan.md` — verbatim v1 specs:
  PR-10 (generator, six-class copy policy, dogfood order), PR-11 (override
  goldens, hermetic audit, convergence loop), PR-12 (xdist), PR-14 (hermetic
  CI matrix, `tests/test_data_version.txt` SHA pinning), §8 decisions 1–2.
- `rms-opus/plans/2026-07-18_opus_modernization_plan.md` — OPUS PR-19
  (holdings-free import suite) and PR-02 (`require_shelves` guard move).
- `SETI/rms-pdsfile-test-data` — the (empty) public data repo.
