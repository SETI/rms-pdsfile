# PR-21 — adversarial review round 4 (scoped re-review)

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent (§6.6), given the §6.6
anti-thrash mandate for a fourth round verbatim — "confirm the prior round's
findings are resolved; raise only **new Major** findings" — plus rounds 1–3's
records to read the findings from, and the instruction to verify each claimed
resolution by re-measuring rather than by reading.
**Diff reviewed:** HEAD `7636cec` ("docs: record round 3 and point the record at
the regenerated full-data run"), 11 files, +2,735 / −525.
**Verdict:** **goal met** — **0 new Major**, all 11 prior findings confirmed
resolved by independent measurement, 5 Deferred.

**This is the §6.6 four-round cap, and the loop terminates here** on the
termination rule: a fresh reviewer returned zero Major and no new un-rebutted
Minor.

## Major

**None.** The reviewer states it could not construct the "goal not met" case, and
that the three things which could have made this Major — a stale full-data record,
a lost name, a widened ratchet — are all clean and each was measured.

## The full-data gate, re-verified as the round's first mandate

Round 3's fixes touched `src/pdsfile/`, so a regeneration was required. The
reviewer checked that it happened rather than that it was claimed:

| Question | Result |
|---|---|
| Last change under `src/pdsfile/` | `dd75796`, **23:34:23** — `7636cec` is docs-only |
| Does the recorded run postdate it? | `ns.xml` **23:37:21**, `s.xml` **23:39:10** — yes |
| Does the record point at the *new* run? | yes; pair 1 is kept, explicitly marked superseded, with the commit its tree was at |
| Is the set diff identical? | it **re-reduced all six junit files itself** and diffed: base↔head2 **0 diff lines in both modes**, head1↔head2 **0** too; ns 882 ids (848 p / 34 s), s 558 ids (555 p / 3 s). Its reductions are **byte-identical to the committed `.set` files** |
| Provenance | head2 71 files, 0 outside the main tree, 14 under `src/pdsfile/`, `_preload` in exactly 1 path; base 70 / 0 / 13 / **0** |

## Resolution check — all 11 prior findings confirmed

Round 1's five (the two-name `pylibmc` measurement, the coverage convention, §8's
"sixteen", the empty "as executed" section, 83-for-82), round 2's three (entry
60's `:495`, entry 60's mixed-tree widths, §15's "30 others") and round 3's three
(the stranded-names heading, the docstring's receiver list, the docstring's
memcached condition) were each re-derived from the code and the data.

Two of those checks went further than the fix required, and are the reason this
round is worth more than a formality:

- **The docstring's receiver enumeration was executed, not read.** The reviewer
  re-derived the 31 receivers, confirmed `set` is absent from the list and is not
  a receiver, and confirmed **all eleven named families do occur**, naming an
  instance of each. It re-derived the contract independently: 25 names listed, 25
  measured, **residue empty in both directions**. It then checked the *write*
  classification the record had only asserted: measured `Store` on `cls` is
  exactly `{CACHE, DEFAULT_CACHING, FS_IS_CASE_INSENSITIVE, LOCAL_PRELOADED,
  MEMCACHE_PORT}`, measured `Store` on the instance receivers is exactly
  `{permanent}`, and `_childnames_filled` is **never** a `Store`, which is what
  the docstring's "mutated in place" claims. All four instance attributes are
  initialised in `PdsFile.__init__` rather than in a subclass, which is what
  "defined on PdsFile itself" claims.
- **The memcached condition was executed across its whole truth table.** It
  patched `pdscache.DictionaryCache` and `MemcachedCache` with raising sentinels,
  stubbed `pylibmc`, and called `preload` on a throwaway `PdsFile` subclass for
  all **8** combinations of `(port, MEMCACHE_PORT, HAS_PYLIBMC)`. All 8 match the
  corrected docstring, **including the case the fix was about**: `port=0,
  MEMCACHE_PORT=11211, HAS_PYLIBMC=True → memcached`.

It additionally re-derived, beyond what any earlier round did: the *entire* moved
spans as single blobs (`2df25ab:pdsfile.py:501–919` ≡ `_preload.py:160–578`,
**18,197 bytes**; `2df25ab:preload_and_cache.py:6–82` ≡ `_preload.py:21–97`,
**2,821 bytes**), including the `pylibmc` try/except with both `# pragma: no
cover` markers; `inspect.getattr_static` over `dir()` of all three classes (257,
299 and 272 names) with **zero lost, zero gained and zero kind changes**; **11**
first-import orders rather than nine, each with 16 identity assertions and the
25/25 import-time category caching; the ratchet's converse check with
per-file-ignores off, locating all 8 of `_preload.py`'s suppressed violations
**inside moved bodies**; and 18 `file:line` citations outside `_preload.py`.

## Deferred — five record-accuracy items, all five fixed in place

The reviewer deliberately filed these as Deferred rather than Minor, per the
scoped-round mandate, and noted they share one cause: round 3's docstring fix
added **4 lines** to `_preload.py`, and figures and line citations below it were
carried forward instead of re-derived. Each was re-measured by the executor and
each reproduced; all five are corrections to text this PR itself wrote, so they
are **fixed here rather than carried forward**, exactly as PR-20's round 4 did
with its own.

1. **`_preload.py`'s line count was 574; it is 578.** 574 was correct at
   `a8f4cb3`. The reviewer's sharpest observation in the round: **PR-19 §5 and
   PR-20 §5 both adopted the wording "counted at HEAD, and re-counted at each
   round rather than carried forward" after PR-20's round 2 hit this exact defect
   (`_sorting.py` 522-for-523), and PR-21 §5 dropped the convention and reproduced
   it.** Fixed to 578, and the convention is restored verbatim, with the 574 → 578
   growth attributed to the docstring and the "no executable line changed" claim
   tied to §3's two identical head pairs.
2. **§8 placed UP015's occurrence at `_preload.py:261`.** `ruff check --select
   UP015` reports it at **`:265`**; `:261` is a `continue`. Fixed.
3. **§12 cited the `DictionaryCache` re-creation at `:361`.** That line is blank;
   the construction is at **`:365`**. Fixed.
4. **`round-3.md` cited the four receiver lines at their pre-fix numbers.** At
   HEAD they are `:255`, `:266`, `:382`, `:387`. Fixed, with a note that the
   pre-fix numbers were four lower and why.
5. **§16 still said entry 57 "is unchanged and still with the owner".** Round 2
   withdrew it on the owner's ruling. Fixed to say so and to point at
   `critiques/pr-21/round-2.md`.

The reviewer also re-checked entries 29, 42, 54, 58, 59 and 60 against the code
and left each where it is, reproducing both halves of entry 58's stub measurement
and endorsing the declined code annotation.

## What the round did not cover, stated so the boundary is visible

The reviewer records that it did **not** re-measure the consumer smoke checks
(§13) or §10's 19 negative-control mutations, as outside a scoped fourth round's
brief. Both were run by the executor at `a8f4cb3` and neither is affected by the
only `src/` change since — round 3's docstring edit, which §3's two identical head
pairs measure as behaviourally inert.

## Regeneration

**No round-4 fix touched anything under `src/pdsfile/`.** All five are in
`critiques/phase5-validation.md` and `critiques/pr-21/round-3.md`. By §6.6 step 5
the full-data record therefore carries forward: the runs at 23:37:21 and 23:39:10
still postdate `dd75796`, which is still the last commit to touch `src/pdsfile/`.
