# Phase 5 validation record

Required by §5's Phase-5 preamble and §6.2 of
`plans/2026-07-25-modernization-plan.md`: every Phase-5 PR runs the full-data
suite in both modes against the goldens' reference root, **diffs the per-test
pass/fail set against the recorded baseline**, and appends its result here. One
section per PR, in merge order.

## How to read a section

- **Baseline** — which recorded set this PR compared against. Phase 5's first
  three PRs are stacked (`plans/2026-07-26-addendum-phase5-stacked-prs.md`), so
  each compares against its *parent's* recorded set, not against `rewrite`.
- **The comparison is a set diff, not a count check.** Both modes are run with
  `--junitxml`, every `testcase` element is reduced to one
  `outcome<TAB>classname::name` line, the lines are sorted, and the two files
  are diffed. Counts are reported as a convenience; the diff is the evidence.
- **Green means the diff is empty.** A test that newly *passes* is as much a
  flag as one that newly fails. A PR that adds tests states the added ids
  explicitly and shows that nothing else moved.
- Holdings roots are named only by their environment variables (§3.4). The
  limited testing copy the goldens are tuned to is machine-local and appears in
  no checked-in file.

---

## PR-15 — `fix: repair latent bugs in rarely/never-exercised core paths`

**Branch:** `pr-15-latent-bug-fixes`, based on `rewrite` @ `807956a`
("ci: hosted lint/no-holdings job; keep self-hosted full-data gate (#107)")
**Baseline:** `rewrite` @ `807956a`, re-measured locally in a clean
`git worktree` with the identical command lines rather than copied from
`critiques/pr-14/validation.md`. The re-measurement reproduced PR-14's recorded
numbers exactly: `--mode ns` 790 passed / 34 skipped, `--mode s` 555 passed /
3 skipped.
**Date:** 2026-07-26
**Last change under `src/pdsfile/`:** commit `4fdadb0` (the round-2 fix).
Every run recorded below was regenerated after it, per §6.6 step 5.

### 0. Why this section is longer than the ones that follow

PR-15 is the first PR of the whole effort permitted to change observable
behavior, and §5 predicts that one of its seven fixes — `html_path`'s missing
`self._recache()` — "may legitimately shift the pass/fail set of the
cached-behavior full-data tests". So this section does three things a mechanical
refactor's section will not need to: it records a **prediction written before the
runs**, it compares the actual diff against that prediction, and it proves the
returned-values-unchanged claim by measurement instead of asserting it.

### 1. Environment

| Item | Value |
|---|---|
| Interpreter | CPython 3.12.3, repo venv, `pip install -e ".[dev]"` |
| Holdings | `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` + `PDSFILE_TEST_HOLDINGS=full`, pointed at the limited testing copy the goldens are tuned to |
| Baseline tree | `git worktree` detached at `807956a`, same interpreter, same holdings |
| Command lines | exactly those in `scripts/automated_tests/pdsfile_main_test.sh`, serial, plus `-rA --junitxml` |

### 2. Active §2 gates

| Gate | Result |
|---|---|
| API-freeze manifest test | **passed** — and see §5, the dumped surface is byte-identical to the base tree's |
| Full-data suite, both modes | **passed** — set diff empty for every pre-existing id; see §3 |
| `ruff check src/pdsfile tests scripts` | **passed**; the ratchet **shrank** by three codes (§6) |
| Clean-install import check | **passed** (throwaway venv, `pip install .`, full module surface imports) |
| Hosted lint/no-holdings job (`scripts/run-all-checks.sh`) | **passed** with holdings (825/34) and without (59/800); see §4 |
| Adversarial review loop | `critiques/pr-15/round-<k>.md` |

### 3. Full-data suite

The suite driver's `--mode ns` invocation gains `tests/core/`, this PR's new
test directory, so two comparisons are reported. The first isolates the effect
of the source changes by running the **baseline's exact invocation** on both
trees; the second records the new driver's full set, which is PR-16's baseline.

#### 3a. Baseline invocation on both trees — the movers check

`tests/api/ tests/holdings_maintenance/ tests/pds3file/ tests/rules/pds3/
tests/pds4file/ tests/rules/pds4/`, i.e. `tests/core/` excluded, so the two
sides collect exactly the same ids.

| Run | `rewrite` @ `807956a` | `pr-15-latent-bug-fixes` | set diff |
|---|---|---|---|
| `--mode ns` | 790 passed / 34 skipped (824 ids) | 790 passed / 34 skipped (824 ids) | **empty** |
| `--mode s` | 555 passed / 3 skipped (558 ids) | 555 passed / 3 skipped (558 ids) | **empty** |

**No pre-existing test changed outcome in either direction, in either mode.**

#### 3b. The driver's invocation on this branch — PR-16's baseline

`tests/api/ tests/core/ tests/holdings_maintenance/ tests/pds3file/
tests/rules/pds3/ tests/pds4file/ tests/rules/pds4/`.

| Run | Result | Diff vs the `807956a` baseline set |
|---|---|---|
| `--mode ns` | **825 passed / 34 skipped** (859 ids) | 35 ids added, 0 removed, 0 changed |
| `--mode s` | **555 passed / 3 skipped** (558 ids) | **empty** — `tests/core/` is not in this invocation |

All 35 added ids are `tests.core.*` and all 35 pass; the count of added ids that
are **not** under `tests.core` is **0**, computed mechanically rather than read
off the list. `--mode s` is untouched because the shelves-only pass runs
`tests/pds3file/ tests/rules/pds3/` only.

**PR-16 and PR-17 compare against the two sets in this sub-section: ns 825
passed / 34 skipped (859 ids), s 555 passed / 3 skipped (558 ids).**

#### 3c. The prediction, written before any of these runs

Written at commit `b646aee` — the tests-only commit, before a single change
under `src/pdsfile/` — and committed verbatim as
[`critiques/pr-15/prediction.md`](pr-15/prediction.md), whose header explains
why a record commit necessarily post-dates what it records. Its three claims:

> 1. `--mode s`: byte-identical to the baseline, 555 passed / 3 skipped.
> 2. `--mode ns`: the baseline's 824 ids with exactly the 33 new `tests/core/…`
>    ids added, all passing — 823 passed / 34 skipped. **No pre-existing test id
>    changes outcome, in either direction.**
> 3. No-holdings run: 24 + 33 = 57 passed / 800 skipped, 857 collected.

The reasoning behind it, also written first:

- The suite's cache is a `DictionaryCache` (`MEMCACHE_PORT = 0`; pylibmc is not
  even installed). A `DictionaryCache` stores the object itself and `_complete()`
  hands back the cached object, so `self` normally *is* the value already stored
  under `logical_lc`. Re-setting it cannot change what a later reader gets.
- What the write-back does change is the entry's expiration and its membership
  in `DictionaryCache.keys`, the trimmable set — neither is a returned value.
- Trimming cannot fire: `_trim()` needs `len(keys) > limit + slop` =
  200,000 + 20,000, and the suite's cache is orders of magnitude smaller.
- Bugs 2, 4, 5 and 6 have no caller anywhere in `src/` or `tests/` (measured by
  grep). `get_permanent_values` is reached only from `preload`'s memcached
  branch, which the suite never takes.
- Bug 3 changes only *which* environment-variable name is read, and only on the
  `abspath_for_logical_path` branch taken when nothing is preloaded and no
  holdings list is cached. The suite always preloads. For `PdsFile` and
  `Pds3File` the name is unchanged regardless.
- Bug 7 changes only which exception classes escape `infoshelf_path_and_key`.
  `shelf_path_and_key_for_abspath` raises `ValueError`, `KeyError` and
  `AttributeError`, all still caught by `except Exception`.

**One clause of that reasoning is wrong, and is corrected rather than edited
away.** "Bugs 2, 4, 5 and 6 have no caller anywhere in `src/` or `tests/`" is
true of bugs 4, 5 and 6 but **not** of bug 2: `get_permanent_values` is called
from `preload` (`pdsfile.py:945`), unguarded, on the branch taken when
`cls.MEMCACHE_PORT` is non-zero and every holdings root is already cached. So
bug 2 is not dead code in production — on a memcached deployment, `preload()`
raised `TypeError` out of its own `finally` every time it found the cache warm.
What the next clause said, and what the gate actually rests on, is unaffected:
the suite never sets `MEMCACHE_PORT`, so it never reaches that branch, which is
why the prediction of "no movers" held anyway. The plan's framing of bugs 2–7 as
the "genuinely dead" ones does not hold for bug 2, and the PR description says
so.

**Outcome: the prediction held.** On the run it was written for — the branch as
it stood at `a6496f8`, before the review loop — it was exact: predicted 823/34
and 555/3 with zero movers, measured 823/34 and 555/3 with zero movers;
predicted 57/800 with no holdings, measured 57/800.

The final numbers in §3b and §4 are one higher (824/34, 858 ids; 58/800) for a
reason that has nothing to do with the prediction: **round 1 of the adversarial
review added one test** for the `_priority_of_icon_type` fix it prompted, and
round 2 renamed and broadened that same test (see `critiques/pr-15/round-1.md`
and `round-2.md`). Diffing each regenerated ns set against the previous one
shows exactly that one id appearing, then being renamed, and nothing else. The
claim the prediction actually makes — **no pre-existing test moves** — was
re-measured after each round's source fix and still holds with an empty diff in
both modes (§3a).

Nothing moved that was not predicted, so there is nothing to escalate under the
"any unpredicted mover is a hard stop" rule.

### 4. No-holdings run

Whole `tests/` tree with `PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR`,
`PDSFILE_TEST_HOLDINGS` and `PDSFILE_TEST_DATA_DIR` all unset.

| | `rewrite` @ `807956a` (PR-14's record) | this branch |
|---|---|---|
| passed | 24 | **59** |
| skipped | 800 | **800** |
| collected | 824 | **859** |

`passed + skipped == collected` on both sides. The 35 additions are exactly the
`tests/core/` ids: every module there is marked `holdings_free` because every
test builds its own inputs. Nothing stopped passing and the skip count is
unchanged, so no pre-existing test lost its ability to run.

This is a real improvement to the hosted job rather than a bookkeeping one: the
hosted leg went from 24 of 824 tests actually running (deferred entry 20's
concern) to 59 of 859.

### 5. API freeze

Two independent checks, both green:

1. `pytest tests/api/test_api_freeze.py` passes — no diff outside the two
   pre-approved forgiveness categories (§6.1). No allowlist entry was added;
   `tests/api/manifest_allowlist.json`, `api_manifest.json`,
   `scripts/dump_public_api.py` and `tests/api/test_api_freeze.py` are
   untouched (§6.4).
2. `scripts/dump_public_api.py` was run against the base worktree at `807956a`
   and against this branch's head. The two dumps are **byte-identical**
   (733,876 bytes each, `diff` empty). The new names `_HOLDINGS_ENV` and
   `_priority_of_icon_type` appear nowhere in either dump — they are
   underscore-prefixed and therefore freeze-invisible, which is what the Phase-5
   preamble requires of any new internal name.

### 6. Ruff ratchet — it shrank

`per-file-ignores` may only shrink (§2). Three codes were removed, one per
defect, each verified to have been that file's **only** instance before the fix
and to produce no violation after it (`ruff check --isolated --select …`):

| File | Code removed | Was |
|---|---|---|
| `src/pdsfile/pdsfile.py` | `B018` | the useless-expression `self._recache` at the html_path defect |
| `src/pdsfile/pdsfile.py` | `E722` | the bare `except:` in `infoshelf_path_and_key` |
| `src/pdsfile/pdsviewable.py` | `F821` | the two `ICON_FILENAME_VS_TYPE` references |

`src/pdsfile/pdscache.py` keeps its `A001` entry: the builtin-shadowing `tuple`
on the line fixed for bug 5 was left alone as out of scope for a bug fix, and a
second instance exists at `:706` regardless.

### 7. Bug 1 in detail — returned values unchanged, cache state changed

The plan's claim is "returned *values* are unchanged; only cache state is". That
is proved here, not asserted.

**Method.** A probe script preloads both classes against the same holdings roots
the suite uses, walks breadth-first from every category (4 levels, 12 children
per node), reads `html_path` and `url` on every object reached, and then dumps
(a) every returned value keyed by class and logical path and (b) the resulting
cache contents. **36 of the 1,910 probed objects produce no value:** they are
category directories that the preload knows about but that are empty in this
reference root, so `html_path`'s merged-directory branch indexes an empty
`childnames` and raises `IndexError` (recorded below as deferred entry 27). They
raise identically on both trees, so the comparison is over the 1,874 objects
that do return a value, plus 36 that raise the same way on both sides. The dump
records, for each cache key, the stored value's type, `logical_path`, `abspath`,
and whether it carries an expiration. The same script ran against the base
worktree and against this branch.

**Result over 1,910 objects spanning both classes and all categories:**

| Measurement | Base `807956a` | This branch |
|---|---|---|
| objects probed | 1,910 | 1,910 |
| probed key sets identical | — | **yes** |
| `html_path`/`url` results that differ (values, and which 36 raise) | — | **0** |
| Pds3File cache entries | 11,242 | 11,242 |
| Pds4File cache entries | 474 | 474 |
| cache key sets identical | — | **yes**, both classes |
| entries whose (type, logical_path, abspath) differ | — | **0**, both classes |
| entries whose has-expiration flag differs | — | **14** (10 Pds3File, 4 Pds4File) |

So: **not one returned value changed**, the cache holds **the same keys mapped
to the same objects**, and the entire difference is that 14 entries which had no
expiration now have one. The 14 are all top-level category entries
(`volumes`, `metadata`, `diagrams`, `bundles`, `checksums-volumes`, …) — the
merged directories whose `html_path` takes the `abspath is None` branch. `preload`
stores them with `lifetime=0` (never expire); `_recache()` re-stores them with
the default lifetime, which `cache_lifetime_for_class` computes as
`LONG_FILE_CACHE_LIFETIME` (7 days) for an object with no interior.

**That transition is not new, and that was measured too.** On the **unfixed base
tree**, resetting the `volumes` entry to permanent and then reading each lazy
property in turn shows that `description` and `iconset_closed` *already* flip it
to expiring, via their own correct `_recache()` calls. The fix makes `html_path`
behave like the ~40 other lazy properties that have always done this; it does
not introduce a new mechanism. (Most properties do not flip it only because they
are already filled on a category object by the time it is cached — `split`,
`anchor`, `is_viewable` and the rest return early. `html_path` is not
pre-filled, which is why the difference shows up on exactly these entries.)

**Why no test observes it.** Not because the property is rarely read — it is
read widely. Three pre-existing test ids read `PdsFile.html_path` directly, but
`PdsFile.url` is an alias for it (`pdsfile.py:1797`) and is consumed by
`pdsviewable.PdsViewable.from_pdsfile` and by `exact_archive_url` /
`exact_checksum_url`, so the restored write-back fires across much of the suite.
The invariant that actually makes it unobservable is narrower and stronger:
**nothing in the suite reads `DictionaryCache.dict` expirations or
`DictionaryCache.keys`**, and trimming — the only behavior an expiration feeds
into — needs 220,000 tracked keys against the 11,242 the largest run produces.
Every test that touches `html_path` or `url` asserts the returned string, and
§7's table shows no returned string moved.

### 8. Regression tests came first, and are shown to have failed

§2 requires each enumerated behavior change to "first add a regression test
pinning the intended behavior". The history makes that checkable rather than
claimed:

- **`b646aee`** adds `tests/core/` and nothing else. At that commit
  `pytest tests/core` reports **20 failed, 13 passed** of 33. Reproduced here in
  a clean `git worktree` at `b646aee` (from a worktree, `PYTHONPATH=<tree>/src`
  is needed so the editable install of the main tree does not shadow it).
- **`a6496f8`** applies the seven fixes. At that commit the same command reports
  **33 passed**.
- **`21ac769`** and **`4fdadb0`** are the review-loop fixes to
  `_priority_of_icon_type` (rounds 1 and 2). Between them they add the 34th test,
  which was confirmed to fail against each preceding version of that helper
  before the version that satisfies it landed. `pytest tests/core` reports
  **34 passed**. Round 3 added the 35th test, likewise confirmed to fail against
  the base tree's hard-coded environment lookup.

Failures at `b646aee`, grouped by the defect each pins:

| Defect | Failing ids at `b646aee` |
|---|---|
| 1 `html_path` write-back | 1 |
| 2 `get_permanent_values` | 2 |
| 3 `_HOLDINGS_ENV` | 2 |
| 4 `DictionaryCache.set_multi` | 4 |
| 5 `MemcachedCache.set_multi` | 1 |
| 6 `iconset_for` | 8 |
| 7 bare `except:` | 2 |

The 13 that already passed are deliberate guards on behavior that must **not**
move: that PDS3 resolution is unchanged, that a preloaded root still beats the
environment, that a `ValueError` from the shelf-path lookup is still absorbed,
that `html_path` still equals `html_root_ + logical_path`, that an object absent
from the cache is still not added to it.

The `tests/core/` modules run identically under `--mode ns` and `--mode s` — all
35 ids, diffed, zero differing lines — which is why the suite driver runs the
directory in the `ns` pass only, as it already does for
`tests/holdings_maintenance/`. Nothing there consults a shelf, so
`use_shelves_only` cannot reach it.

### 9. Bug 7's behavior audit

§5 marks the bare-`except:` fix "behavior-audited": the change is safe only if
nothing being caught there is a `BaseException` that the current code swallows
and the fix would let through.

`infoshelf_path_and_key`'s `try` block contains exactly one call,
`cls.shelf_path_and_key_for_abspath(self.abspath, 'info')`. Reading that method
end to end, it can raise:

| Raised | Class | Still caught? |
|---|---|---|
| `ValueError('No shelf files for checksums: …')` | `Exception` | yes |
| `ValueError('Archive shelves require bundle sets: …')` | `Exception` | yes |
| `ValueError('Non-archive shelves require bundle names: …')` | `Exception` | yes |
| `KeyError` from `cls.SHELF_PATH_INFO[shelf_type]` | `Exception` | yes |
| `AttributeError` from `abspath.partition(...)` when `abspath` is `None` | `Exception` | yes |

It contains no `raise SystemExit`, no `sys.exit`, no generator, and no code that
can produce a `BaseException` of its own. The only `BaseException`s that can
reach the handler are asynchronous — `KeyboardInterrupt` from a Ctrl-C, or a
`SystemExit` propagating out of an interpreter shutdown — and turning either of
those into `('', '')` is the defect, not a behavior anyone can depend on. **The
audit says the change is safe.** Both directions are pinned by tests: an
`AttributeError` is still absorbed, a `KeyboardInterrupt` and a `SystemExit` are
not.

### 10. Consumer smoke — outcome unchanged

Bugs 4 and 5 are in `pdscache`, which
`critiques/baselines/consumer-smoke-baseline.md` records rms-viewmaster using
directly. Both checks in that file were re-run against this branch. The gate is
**same outcome as baseline**, not "passes".

| Check | Baseline | This branch |
|---|---|---|
| A — rms-opus import paths | 4/4 resolve, 0 failures | **4/4 resolve, 0 failures** |
| B — rms-viewmaster startup | 5 ok, 3 pre-existing failures | **5 ok, 3 failures — the same three** |

The three Check-B failures are still `pdsfile.cache_lifetime` (raises),
`pdsfile.DEFAULT_CACHING` (absent, so viewmaster's assignment stays a silent
no-op) and the same `cache_lifetime` read inside `get_page_cache()`. None became
a pass, which the baseline is explicit about mattering: fewer failures would
mean pdsfile had grown a package-level name ground rule 1 forbids.
`pdsfile.pdsfile.repair_case` still resolves.

### 11. Deferred observations raised by this PR

Six new entries in `critiques/deferred-observations.md`, all under Phase 5. Four
were found while fixing the seven the plan enumerates:

| # | Observation |
|---|---|
| 23 | `DictionaryCache(lifetime=0)` cannot serve `set()` without an explicit lifetime |
| 24 | `DictionaryCache.set_multi`'s `pause` parameter no longer suppresses the per-key trim |
| 25 | `MemcachedCache.set_multi` applies one key's lifetime to the whole batch |
| 26 | `_recache()` downgrades a permanent cache entry to an expiring one |

Two more came out of the review loop (round 2):

| # | Observation |
|---|---|
| 27 | `html_path` raises `IndexError` on an empty merged category — measured at 36 of the 1,910 probed objects, identically before and after this PR |
| 28 | `iconset_for`'s terminal lookup assumes an `UNKNOWN` icon set exists |

Each is outside the enumerated list, so each is recorded rather than fixed.

No entry in the existing 1–22 is resolved or invalidated by these fixes; entries
10 and 11 are maintenance-tool defects owned by PR-26/PR-28 and were not
touched. Two entries cite suite counts that this PR moves — entry 15's "24 the
hosted job runs" and entry 20's "824 skipped" — and both are annotated in place;
the observations themselves stand.

### 12. Review loop

| Round | Verdict | Findings | Record |
|---|---|---|---|
| 1 | goal met | 0 Major, 3 Minor (all accepted and fixed), 3 Deferred (all already recorded) | `critiques/pr-15/round-1.md` |
| 2 | goal met | 0 Major, 5 Minor (all accepted and fixed), 2 Deferred (new entries 27–28) | `critiques/pr-15/round-2.md` |
| 3 | goal met | 0 new Major, 4 Minor (all accepted and fixed), 1 Deferred (accepted and pinned by a test instead) | `critiques/pr-15/round-3.md` |
| 4 | see the record | — | `critiques/pr-15/round-4.md` |

Round 3 was the scoped re-review §6.6 prescribes: confirm the prior rounds'
findings are resolved, raise only new Major findings. It confirmed all eight
earlier findings resolved against the tree and found no Major.

**No round found a Major and no finding was rebutted** — all twelve Minors were
accepted and fixed. Rounds 1 and 2 each produced a `src/pdsfile/` fix, so every
run recorded above was regenerated at or after commit `4fdadb0` before the next
reviewer was spawned (§6.6 step 5). Round 3's fixes touched only `tests/` and
`critiques/`, which under that same rule does not stale the record; the counts
were regenerated anyway because the round added a test and therefore changed the
set.
