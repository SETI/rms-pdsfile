# PR-19 — adversarial pre-PR review, round 4 (scoped)

**Reviewer:** fresh, no development context.
**Scope:** §6.6's 4th-round rule — confirm rounds 1–3's findings are resolved at
HEAD; raise only **new Major** findings.
**Diff reviewed:** `git diff origin/pr-18-derived-paths...HEAD` (base `80cd9ff`,
head `73114c0`). I regenerated the diff and confirmed it is byte-identical to the
copy I was handed; `git merge-base` is `80cd9ff`, so `...` and `..` agree.
**Date:** 2026-07-27

## How I checked, before the table

I re-derived every claim rather than reading it. **Byte equivalence:** an `ast`
pass extracted all eight moved definitions from the parent worktree's `PdsFile`
body and from the two mixin bodies and compared them byte for byte — seven
identical, `opus_products` differing by exactly the four deferred-import lines,
shown as a unified diff by my own tool. The set removed from `PdsFile` equals the
set added to the mixins; **no method remaining in `PdsFile` changed one
character**; no class-level `Assign` name was lost or gained; both mixin class
bodies hold **zero** assignments. §5's byte figures all reproduce under the
record's own convention (decorators included, leading indent and trailing newline
stripped): 657 / 3,842 / 2,231 / 3,111 / 386 / 774 / 2,015 / 8,199 → 8,385 (delta
**186**), and both blobs at 10,251 and 2,795. **Free variables:** `symtable` plus
an AST pass over decorators and argument defaults reports **zero** dangling names
in either module and **no** module-level `pdsfile.pdsfile` import of any
spelling; each of `pdsfile._opus`, `pdsfile._index_rows`, `pdsfile.pdsfile`,
`pdsfile`, `pdsfile.pds3file`, `pdsfile.pds4file` imports cleanly as the *first*
import in a fresh interpreter. **Gates:** `ruff check src/pdsfile tests scripts`
→ all passed; `pytest tests/api/` → 16 passed; `scripts/run-all-checks.sh` with
every holdings variable unset → all six sub-checks green, **82 passed / 800
skipped**, clean-install gate included; `scripts/dump_public_api.py` run against
a worktree at the parent tip and against HEAD gives **byte-identical** dumps
(733,876 bytes each, both stderr empty). **Ratchet:** the per-code loop over all
18 codes gives parent `pdsfile.py` **85** and HEAD 80 + 3 + 2 = **85**, every code
conserving exactly, `RUF005` 8 → 6+1+1 and `UP024` 13 → 10+2+1; the converse
whole-select-set run against each new module reports exactly `RUF005` and
`UP024` and nothing else, so neither entry is vacuous and neither widens.
**§6.2:** I reduced all ten junit XMLs in `runs/p19-{base,head1..head4}/` with my
own `xml.etree` reducer — `--mode ns` **880 → 882**, the whole diff being the two
`test_no_mixin_is_shadowed_by_a_pdsfile_subclass[Pds3File|Pds4File]` lines, no
removals and no outcome changes; `--mode s` **558 → 558**, zero-line diff; all
four head pairs reduce identically; my reductions are byte-identical to
`p19_{base,head4}_{ns,s}.txt` on disk; counts 846/34 → 848/34 and 555/3 → 555/3
reproduce, and PR-18's §3 records exactly that baseline. The `--mode s` set
contains **no** `tests.api` id (so its empty diff is the right answer) but **69**
OPUS and **24** index-row ids, so it is not vacuous. Non-vacuity:
`CoverageData.measured_files()` gives **9** top-level modules under one tree's
prefix for the baseline and **11** under the other's for HEAD, with zero
cross-tree leakage. Freshness: the last `src/pdsfile/` change is `b6bda4a` at
**18:33:45**; head4's runs *start* at 18:33:59 and 18:37:00 and are written
18:36:54 and 18:38:43; the only later commit, `73114c0`, touches `critiques/`
only. **Behaviour:** a probe over two real index tables exercising
`get_indexshelf`, `child_of_index`, `find_selected_row_key(<,>)`, `column_names`,
`data_abspath_associated_with_index_row`, **`data_pdsfile_for_index_row`** (the
zero-coverage method) on present *and* missing rows, plus `from_filespec`,
`from_opus_id` and a full `opus_products` dictionary, is **identical** between
the parent worktree and HEAD. A 34-class dump of `__bases__[0].__name__`, the
sniff's verdict, `__base__` and `dir()` differs **nowhere**; the sniff is `True`
for exactly the same six pds4 rule classes. The mixin-name intersection over the
whole 34-class hierarchy is empty, and `PdsFile.__subclasses__()` is exactly
`[Pds3File, Pds4File]`. **§6.4:** `api_manifest.json`, `manifest_allowlist.json`,
`scripts/dump_public_api.py` and `tests/api/test_api_freeze.py` are untouched; no
golden or baseline file is touched; `critiques/deferred-observations.md` is
additions only; no `noqa`, `skip`, `xfail` or `type: ignore` is added; no CRLF,
no trailing whitespace, no annotations.

## Resolution of rounds 1–3

| # | Finding | At HEAD | Evidence |
|---|---|---|---|
| **1-M1** | `_IndexRowsMixin` docstring calls nine names "lazy properties"; three are plain instance attributes and one is *written* | **Resolved** | `src/pdsfile/_index_rows.py:29-50` now splits four categories. My AST walk over the module's methods, classified with `inspect.getattr_static(PdsFile, …)`: the 8 names under "lazy properties read" are all `property` objects on `PdsFile`; the 6 under "instance attributes read" are all non-descriptors; the write clause names `column_names` (`:219`) and `_exists_filled` (`:227`, `:232`), the only two writes in the module |
| **1-M2** | "every rule module" / "24 other" `opus_products` tables | **Resolved** | `phase5-validation.md` §11 and `deferred-observations.md` entry 52 both say **18 of 34** / "17 other". Measured: 34 rule modules, `^opus_products\s*=` in **18**, indented `opus_products =` in **0** |
| **1-M3** | "every `tests/rules/pds{3,4}/` module" contributes a context | **Resolved** | §9 note (c) says 13 of 13 pds3 and 2 of 3 pds4. My own `dynamic_context` run: exactly 13 pds3 + 2 pds4 modules contribute; `tests/rules/pds4/test_cassini_iss_fring_mosaics_rsfrench2025.py:15` carries a module-level `pytest.mark.skip` |
| 1-D1 | subclass check names its subjects | Recorded | entry 53, owner PR-20 |
| 1-D2 | §12 "references" vs call sites | Corrected in §12, not deferred | see 2-m2 |
| **2-m1** | `_index_rows.py` line count stale (308) under "All counted at HEAD" | **Resolved** | §5 says `_index_rows.py` **328**, `_opus.py` **304**; `wc -l` gives 328 and 304 |
| **2-m2** | `from_filespec` consumer count 3 where 4 sites are listed | **Resolved** | §12 row now reads `4:` with all four lines. Re-greped rms-opus @ `73cb6de7`: `obs_base_pds3.py:90`, `obs_base_pds4.py:33`, `do_import.py:1480`, `do_import.py:1482`. The other rows (2/1/1 and viewmaster's 3 at `viewmaster.py:873,1449,1580`) also reproduce exactly |
| **2-m3** | "suppressed violations unchanged at 21" not reproducible from stated scope | **Resolved** | §8 now says "unchanged at **85**", with 21 kept as the explicit subtotal of the two moving codes. My per-code loop: 85 → 85, `RUF005` 8 → 6+1+1, `UP024` 13 → 10+2+1 |
| **2-m4** | `_index_rows.py` state contract omits `exists`, `label_abspath`, `CACHE`, `_exists_filled` | **Resolved** | All four are present at `_index_rows.py:33-41`, and my AST walk finds **no** further omission in either direction |
| **2-m5** | superseded head pair 1 labelled with a commit 16 minutes later | **Resolved** | §3's table attributes pair 1 to `b554c77` (authored 17:01:22, before its 17:04:18 / 17:06:10 XMLs). Pairs 2 and 3 (`cf35a0f` 17:39:31 → 17:42/17:44; `3ab1738` 18:04:34 → 18:07/18:09) are likewise consistent |
| 2-D1/D2/D3 | AST-derive the contracts / PDS4 branch testable / `_version` | Recorded | entry 54; folded into 51; informational |
| **3-m1** | `_OpusMixin`'s "and nothing else" omits `version_rank`; and the record's "derived from an AST walk" is thereby false | **Resolved (code); partially resolved (record)** | `src/pdsfile/_opus.py:32` now reads `abspath, logical_path, root_, version_rank`, and my AST walk over `_opus.py` returns exactly those four — plus the 9 class attributes + `__base__`/`__subclasses__`, the 4 lazy properties, the 4 other methods and the 3 sibling-mixin names, all of which the docstring lists and none of which it omits or invents. **Both docstrings now match an AST walk exactly, in both directions.** The record half: `phase5-validation.md:2845-2846` still asserts "the two docstrings are now **derived** from an AST walk … which is what deferred entry 54 asks be automated"; it is retracted 13 lines later (`:2859-2860`) rather than softened in place. Substantively harmless — the content claim verifies, and §15 keeps entry 54 open — so I record it as Deferred D2, not as a Major |
| **3-m2** | §9's "Where" column wrong in four of eight rows | **Resolved** | My own `dynamic_context = test_function` run over `tests/pds3file/ tests/pds4file/ tests/rules/ tests/core/ tests/holdings_maintenance/` reproduces **50** distinct contexts and 9/12/9/4/**0**/2/19/28, *and* every corrected attribution: the three index-row rows do get a context from `tests/rules/pds3/test_corss_8xxx.py::test_associations`; `from_opus_id`'s 19 are pds3 blackbox ×2, pds3 whitebox ×1 and 16 contexts across 15 rules modules; the pds4 blackbox contributes only to `from_filespec`; `opus_products`' 28 come from the same 15 modules; no `tests/core/` or `tests/holdings_maintenance/` context appears |
| **3-m3** | three stale `_opus.py` line numbers in §6 | **Resolved by removal** | §6 now locates by symbol ("against `_opus.py`, inside `opus_products`"; "on the line immediately below the deferred import"). No line number remains in that section, and §16 states the reasoning |
| **3-m4** | non-vacuity table's five-module set notation reads as exhaustive | **Resolved** | §1's table lists all **nine** baseline and **eleven** head modules with a count column. `CoverageData.measured_files()` on `runs/p19-base/.coverage` and `runs/p19-head4/.coverage` returns exactly those names, one tree prefix each, zero leakage |
| **3-m5** | the new check's comment claims a failure the move introduces, and its strictness is unexplained | **Resolved, and its added measurement reproduces** | `tests/api/test_mixin_collisions.py:112-123` now says the check pins a name-discipline rule, "not a defect a move introduces". Its new claim measures true: `Pds3File` overrides **34** `PdsFile` names, `Pds4File` **35**, and in both cases the callable/property overrides are exactly `__init__`, `__repr__`, `require_shelves`, `set_easylogger`, `set_logger`, `use_shelves_only` — the six named — with everything else a class attribute or translator table |
| 3-D1/D2 | generalize the subclass check / entry 54 is due | Recorded | entries 53 and 54 |

Nothing recorded as fixed was silently dropped, and nothing was fixed in a way
that introduced a new defect.

## Major findings

**None — no new Major.** I could not construct a case where this refactor changes
behaviour, strands a name, loses a reachable member, widens the ratchet, breaks
the freeze, introduces a cycle, moves an id the PR is not entitled to move, or
where a figure in the gate evidence fails to reproduce from an artifact I could
point at. The two added ids are real, non-vacuous and are the ones deferred entry
48 assigns to this PR.

## Deferred (new, non-blocking)

### D1 — the mechanical contract check entry 54 asks for needs a self-call rule, or it will fire on four true negatives

`_IndexRowsMixin`'s docstring opens "Every attribute these methods read or write
on a PdsFile object or on a PdsFile class, **and nothing else**". Read strictly,
four attribute lookups on PdsFile objects are unlisted: `self.get_indexshelf`
(`src/pdsfile/_index_rows.py:206`), `self.find_selected_row_key` (`:195`),
`parent.child_of_index` (`:303`) and
`neighbor.data_abspath_associated_with_index_row` (`:304`) — the mixin's *own*
methods, defined in the same class body, which is why leaving them out is the
right editorial call and why I am not raising it as a finding. But the AST walk
entry 54 asks be automated returns them, so that check needs an explicit
"defined by this mixin" exclusion or it will report four false positives on this
module the day it is written. `_opus.py` has no intra-mixin call and so does not
show the problem. **Owner: PR-22, appended to entry 54.**

### D2 — `phase5-validation.md:2845-2846` retracts a claim rather than correcting it

The round-2 paragraph of §16 still says, in the present tense, that "the two
docstrings are now **derived** from an AST walk of their own modules rather than
written by hand — which is what deferred entry 54 asks be automated"; the round-3
paragraph at `:2859-2860` says that same claim "was itself the assertion that
failed". Both stand. The *content* claim verifies at HEAD — I re-derived both
lists from an AST walk and they match exactly, in both directions — and §15 keeps
entry 54 open for PR-22, so no reader is misled about what remains to be built.
The sentence should lose "derived" (or gain "as of round 2") the next time this
record is edited; there is no code impact and re-editing `critiques/` now would
buy nothing. **Owner: PR-20's validation record, as a convention note.**

## Verdict

**goal met** — every Major and Minor from rounds 1, 2 and 3 is resolved at HEAD
(3-m1's record half only partially, and harmlessly, recorded as D2); **0 new
Major**; 2 Deferred. The extraction is byte-for-byte apart from the four
sanctioned deferred-import lines, the `class PdsFile` statement and every class
attribute stayed in `pdsfile.py`, the mixins hold methods and no state, the bases
are alphabetical with `object` last, the public surface is unchanged to the byte,
the ratchet is a strict split of `pdsfile.py`'s entry, the
`__bases__[0].__name__` sniff moved untouched and its premise verifies
empirically for all 34 classes, and the full-data pass/fail set differs from
PR-18's recorded baseline by exactly the two ids deferred entry 48 entitles this
PR to add.
