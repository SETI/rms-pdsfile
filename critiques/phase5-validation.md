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

The final numbers in §3b and §4 are two higher (825/34, 859 ids; 59/800) for a
reason that has nothing to do with the prediction: **the review loop added two
tests.** Round 1 added one for the `_priority_of_icon_type` fix it prompted and
round 2 renamed and broadened it; round 3 added
`test_a_class_does_not_borrow_another_class_holdings_root`, which pins bug 3's
own behavior change. Diffing each regenerated ns set against the previous one
shows exactly those ids appearing, one being renamed, and nothing else. The
claim the prediction actually makes — **no pre-existing test moves** — was
re-measured after each round and still holds with an empty diff in both modes
(§3a).

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
| 4 | goal met | **0 new Major**; 4 non-blocking items, all fixed | `critiques/pr-15/round-4.md` |

Round 3 was the scoped re-review §6.6 prescribes: confirm the prior rounds'
findings are resolved, raise only new Major findings. It confirmed all eight
earlier findings resolved against the tree and found no Major.

**No round found a Major and no finding was rebutted** — all sixteen Minor and
non-blocking findings were accepted and fixed. §6.6's termination condition is
met within the four-round cap.

Rounds 1 and 2 each produced a `src/pdsfile/` fix, so every run recorded above
was regenerated at or after commit `4fdadb0` before the next reviewer was
spawned (§6.6 step 5). Rounds 3 and 4 touched only `tests/` and `critiques/`,
which under that same rule does not stale the record; the counts were
regenerated after round 3 anyway, because it added a test and therefore changed
the set.

---

## PR-16 — `refactor: extract module-level path helpers → _path_utils.py`

**Branch:** `pr-16-path-utils`, based on `pr-15-latent-bug-fixes` @ `1a5d85c`
("docs: reflow two record paragraphs"), opened against that branch, not `rewrite`
(`plans/2026-07-26-addendum-phase5-stacked-prs.md`).
**Baseline:** **PR-15's recorded post-fix set** — §3b above, `--mode ns` 825
passed / 34 skipped (859 ids) and `--mode s` 555 passed / 3 skipped (558 ids) —
**re-measured locally on the parent tip** with this PR's own command lines rather
than copied from the table, exactly as PR-15 re-measured `rewrite`'s. The
re-measurement reproduced §3b exactly.
**Date:** 2026-07-27
**Sub-plan:** [`plans/2026-07-27-pr-16-subplan.md`](../plans/2026-07-27-pr-16-subplan.md)
**Last change under `src/pdsfile/`:** commit `b86adba` (the round-3 fix — a
comment line in `_path_utils.py`), at 02:02:17. The **head** runs recorded below
were regenerated after it, per §6.6 step 5: their `--junitxml` timestamps are
02:02:25 and 02:05:15. The **baseline** runs (01:19:13 and 01:22:05) stand: they
were taken in a detached worktree at `1a5d85c` that no round has touched, so
re-running them would measure the same unchanged tree.

This PR is a pure extraction. Unlike PR-15 it has **no licence to move the
pass/fail set in either direction**, so the gate here is simply "the two set
diffs are empty", and the section is correspondingly short.

### 1. Environment

| Item | Value |
|---|---|
| Interpreter | CPython 3.12.3, repo venv, `pip install -e ".[dev]"` |
| Holdings | `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` + `PDSFILE_TEST_HOLDINGS=full`, pointed at the limited testing copy the goldens are tuned to |
| Baseline tree | a `git worktree` detached at the parent tip `1a5d85c`, same interpreter, same holdings; `pytest` reports that directory as `rootdir` |
| Command lines | exactly those in `scripts/automated_tests/pdsfile_main_test.sh` (serial, under `coverage`), plus `-rA --junitxml` |

**Which source each run actually imported, proved rather than assumed.** The
interpreter is the main tree's venv, whose editable install puts
`<main tree>/src` on `sys.path`, so a worktree run could silently measure the
wrong tree and make the whole comparison vacuous. After each pair of passes,
`coverage.CoverageData.measured_files()` was read for its **absolute** paths:

| Run | pdsfile modules measured |
|---|---|
| baseline | `<worktree>/src/pdsfile/pdsfile.py` — and no `_path_utils.py`, because that file does not exist at `1a5d85c` |
| this branch | `<main tree>/src/pdsfile/pdsfile.py` **and** `<main tree>/src/pdsfile/_path_utils.py` |

The absence of `_path_utils.py` on the baseline side is the decisive bit: had the
worktree run leaked into the main tree's install, the extracted module would have
been measured there too.

### 2. Active §2 gates

| Gate | Result |
|---|---|
| API-freeze manifest test | **passed**; and the dumped surface is byte-identical to the parent's — §4 |
| Full-data suite, both modes | **passed** — both set diffs empty; §3 |
| `ruff check src/pdsfile tests scripts` | **passed**; the ratchet gained no code — §7 |
| Clean-install import check | **passed** (throwaway venv, `pip install .`, full module surface imports) |
| Hosted lint/no-holdings job (`scripts/run-all-checks.sh`, no holdings env vars) | **passed**, 59 passed / 800 skipped — identical to PR-15's §4 |
| Adversarial review loop | `critiques/pr-16/round-<k>.md` |

### 3. Full-data suite — both set diffs empty

Both passes were run on the parent tip and on this branch's head with the same
interpreter and the same holdings. Every `testcase` element of each `--junitxml`
was reduced to one `outcome<TAB>classname::name` line, sorted, and the two files
were diffed with `diff -u`.

| Run | parent `1a5d85c` | `pr-16-path-utils` | set diff |
|---|---|---|---|
| `--mode ns` | 825 passed / 34 skipped (859 ids) | 825 passed / 34 skipped (859 ids) | **empty** |
| `--mode s` | 555 passed / 3 skipped (558 ids) | 555 passed / 3 skipped (558 ids) | **empty** |

No test id was added, removed, or changed outcome, in either mode. The parent
numbers reproduce §3b's recorded set, which is what makes this a comparison
against PR-15's baseline rather than against a fresh unrelated measurement.

### 4. API freeze — empty diff, as a pure extraction requires

1. `pytest tests/api/` passes — 15 ids, of which `test_api_freeze.py` contributes
   one. `tests/api/api_manifest.json`,
   `tests/api/manifest_allowlist.json`, `scripts/dump_public_api.py` and
   `tests/api/test_api_freeze.py` are untouched by this PR (§6.4); no allowlist
   entry was added.
2. `scripts/dump_public_api.py` was run against a worktree at the parent tip and
   against this branch's head. The two dumps are **byte-identical** (733,876
   bytes each, `diff` empty).

The manifest records `pdsfile.pdsfile`'s module-level names including imported
modules, so this gate is stricter here than it looks: dropping the now-unreferenced
`import glob` / `import math` would have been a manifest break. See §6.

`pdsfile._path_utils` is underscore-prefixed, so the dumper skips it where the
submodule import binds it onto the `pdsfile` package — which is exactly the
freeze-invisibility the Phase-5 preamble requires of a new internal name.

### 5. What moved, and the sweep that decided it

Ten module-level symbols, located by name (the plan's ":47–247" window had
drifted — PR-15 edited this file): `construct_category_list`,
`logical_path_from_abspath`, `_clean_join`, `_clean_abspath`, `_clean_glob`,
`_needs_glob`, `repair_case`, `formatted_file_size`, `abspath_for_logical_path`,
`selected_path_from_path`. `abspath_for_logical_path` moved in its **PR-15 form**
— it reads `cls._HOLDINGS_ENV`; the pre-PR-15 hard-coded `'PDS3_HOLDINGS_DIR'`
literal was not resurrected, and `tests/core/test_pdsfile_path_resolution.py`
(five ids, all still passing) is what says so.

**The sweep was computed, not read.** CPython's `symtable` yields the
module-global names each moved function's body references; a second AST pass
covers each definition's decorator expressions and argument defaults, which are
evaluated in module scope and which `symtable` does not attribute to the
function. Result:

| Category | Found |
|---|---|
| module-level **constants** referenced | `FILE_BYTE_UNITS`, **`_GLOB_CACHE_SIZE`** |
| module-level **classes** referenced (import-cycle risk) | **none** |
| module-level **functions** that would stay behind | **none** |
| unclassified names | **none** |
| stdlib imports the moved set needs | `fnmatch`, `functools`, `glob`, `math`, `os` |

The second pass is load-bearing, and this is the "record the method so a reviewer
can check it" case the plan's sweep requirement exists for: `_GLOB_CACHE_SIZE`
appears **only** in `@functools.lru_cache(maxsize=_GLOB_CACHE_SIZE)`, so a
body-only sweep reports it as unreferenced and the extracted module raises
`NameError` at import. The plan's brief names `FILE_BYTE_UNITS` alone; the sweep
found the second one. Both are re-exported: `FILE_BYTE_UNITS` because it is
public and frozen, `_GLOB_CACHE_SIZE` because the Phase-5 preamble's rule is
"`pdsfile.py` keeps re-exporting every name it exports today" without a
public/private qualifier, and carrying it costs one line and keeps the invariant
below exact.

**Zero names lost, measured.** `sorted(vars(pdsfile.pdsfile))` was compared
between the parent worktree and this branch: **45 names on each side, none lost
and none gained.** That is a stronger statement than the manifest makes (the
manifest skips underscore names) and it is the simplest form of the preamble's
"`pdsfile.pdsfile.X` access is unchanged".

`PATH_EXISTS_CACHE_SIZE` was left alone — its consumer is the `lru_cache` on
`os_path_exists`, which moves with `_local_fs.py` in PR-17.

**The sweep's second direction: who *patches* these globals.** The free-variable
sweep answers "what must move with the code"; it does not answer "does anything
outside `src/` rebind one of these names on the old module". That second grep
(`monkeypatch.setattr` / `setattr(<module>` over `tests/` and `scripts/`) finds
three sites repo-wide, of which exactly one was affected:
`tests/core/test_pdsfile_path_resolution.py` replaced `glob` on
`pdsfile.pdsfile`, which `abspath_for_logical_path` no longer resolves through.
The test still *passed* after the move — an outcome-set diff is structurally
blind to a test that has stopped testing — but only because this machine has no
`/Library/WebServer/Documents/holdings*`. It now patches
`abspath_for_logical_path.__globals__` instead, which follows the function
wherever later PRs move it. Proved by making the real `glob.glob` return a hit,
i.e. simulating the MacOS install the branch exists for:

| stub site | result with `glob.glob` returning a hit |
|---|---|
| none | resolves to the stub root — the test would fail |
| `pdsfile.pdsfile.glob` (the old site) | resolves to the stub root — the test would fail |
| `abspath_for_logical_path.__globals__` (the new site) | `ValueError: No holdings directory` — the test passes for the right reason |

The other two patch sites are unaffected: one rebinds `PdsFile` class attributes,
the other rebinds a name on `pdsviewable`, which this PR does not touch. This
reverse direction is worth adding to PR-17's sweep, where `os` is the analogous
name (deferred entry 29).

**No import cycle:** `_path_utils.py`'s module-level imports are `fnmatch`,
`functools`, `glob`, `math`, `os` and nothing else — verified by parsing the
module, not by reading it. No moved function needs a `PdsFile` class object, so
no function-local deferred import was needed.

**Byte-for-byte equivalence, measured.** For each moved definition the exact
source segment (decorators included) was extracted from the parent commit's
`pdsfile.py` and from `_path_utils.py` and compared byte by byte: all ten
functions and both constants identical. The contiguous run from the first moved
`def` to the last also compares identical as a single 6,562-byte blob, which
additionally rules out a reordering or a dropped blank line. No moved body was
restyled to dodge an inherited lint violation — that is PR-23's job.

`pdsfile.pdsfile.X is pdsfile._path_utils.X` for all twelve re-exported names, so
callers get the same objects, not copies.

`pdsfile.py`: 6,308 → 6,125 lines; `_path_utils.py`: 219 lines.

### 6. Keeping `pdsfile.pdsfile.X` resolving without touching the ratchet

Five names in `pdsfile.py` are now referenced nowhere in it but must stay bound:
`glob`, `math`, `FILE_BYTE_UNITS` and `selected_path_from_path` are frozen
members of its public surface, and `_GLOB_CACHE_SIZE` is carried for the
zero-names-lost invariant in §5. Measured rather than assumed — rewriting the
five statements in plain form and re-running `ruff` produces exactly five F401s
and no others:

```
F401 `glob` imported but unused
F401 `math` imported but unused
F401 `._path_utils.FILE_BYTE_UNITS` imported but unused
F401 `._path_utils._GLOB_CACHE_SIZE` imported but unused
F401 `._path_utils.selected_path_from_path` imported but unused
```

`pdsfile.py`'s ratchet entry does not contain F401, and the ratchet header in
`pyproject.toml` forbids both growing it and adding an inline `noqa`. All five
therefore use the PEP-484 redundant-alias form (`import glob as glob`,
`FILE_BYTE_UNITS as FILE_BYTE_UNITS`), which ruff recognises as an explicit
re-export. `pdsfile.py` now reports **0** F401 with no suppression of any kind.

### 7. Ruff ratchet — no code gained

Procedure: for every code in `pdsfile.py`'s entry, the following was run against
both files after the move —

```
ruff check --no-cache --isolated --select <code> \
           --line-length 100 --target-version py310 <file>
```

`--isolated` drops `pyproject.toml`'s `line-length = 100` and would otherwise
report an E501 at 88 columns that the project config does not, so the two
settings are restored explicitly. Reproducing the counts below requires that
exact command.

| File | Entry | Note |
|---|---|---|
| `src/pdsfile/pdsfile.py` | unchanged | every one of its 23 codes is still triggered by lines that stayed, so none could be dropped |
| `src/pdsfile/_path_utils.py` | `["E701", "F841"]` | the only two codes the moved lines trigger |

Both new-entry codes are already in `pdsfile.py`'s entry, so this is a **split of
an existing entry, not a new suppression**: E701 was 16 instances in the parent's
`pdsfile.py` and is now 14 + 2, F841 was 7 and is now 6 + 1. The count of
distinct (file, code) suppressions rises by two while the number of suppressed
violations is unchanged; no code that was not already forgiven for these lines is
forgiven now. Had `_path_utils.py` needed a code absent from `pdsfile.py`'s
entry, that would have been a §6.4 hard stop.

### 8. Consumer smoke — outcome unchanged

`critiques/baselines/consumer-smoke-baseline.md` calls out this PR by name: it
records rms-viewmaster reaching `pdsfile.pdsfile.repair_case` at
`pdsiterator.py:104` and says "Phase 5 moves module-level functions into private
modules while `pdsfile/pdsfile.py` keeps re-exporting every name it exports today
— `repair_case` is one of the names that re-export must preserve, and this
baseline is where a regression would show up." Both checks were re-run. The gate
is **same outcome as baseline**, not "passes".

| Check | Baseline | This branch |
|---|---|---|
| A — rms-opus import paths | 4/4 resolve, 0 failures | **4/4 resolve, 0 failures** |
| B — rms-viewmaster startup | 5 ok, 3 pre-existing failures | **5 ok, 3 failures — the same three** |

The three Check-B failures are still `pdsfile.cache_lifetime` (raises),
`pdsfile.DEFAULT_CACHING` (absent, so viewmaster's assignment stays a silent
no-op) and the same `cache_lifetime` read inside `get_page_cache()`. None became
a pass. **`pdsfile.pdsfile.repair_case` still resolves.**

Environment note carried from the baseline: the check ran under the pdsfile
venv's interpreter with rms-viewmaster's `site-packages` appended to
`PYTHONPATH`, because that venv lacks pdsfile's declared `range_ex` dependency.
rms-viewmaster is at `a0d05e2` with the same three untracked entries the baseline
records.

### 9. Clean install

`scripts/clean_install_check.sh` passes. The new module is picked up by the
existing `include = ["pdsfile*"]` package glob with no packaging change: the
built wheel contains `pdsfile/_path_utils.py`, and the gate imports the whole
manifest module surface — `pdsfile.pdsfile` among them — which cannot succeed if
`_path_utils.py` is missing from the distribution.

### 10. Deferred observations

Six new entries in `critiques/deferred-observations.md`, all raised by the
review loop and all out of scope for a pure move:

| # | Observation | Raised in | Owner |
|---|---|---|---|
| 29 | An extraction sweep must also ask which module namespaces the tests *patch* — and which module-level *data* they rebind — not only which globals the code *reads*. The first half is the direction that produced this PR's one Major | round 1 (+ round 3) | PR-17 onward |
| 30 | `repair_case` raises `UnboundLocalError` on a single-component path | round 1 | PR-23 |
| 31 | `src/pdsfile/__init__.py`'s `from pdsfile import *` is a self-import that binds nothing, and is not simply fixable | round 2 | PR-24 |
| 32 | A commented-out line rode along in the byte-for-byte move, so PR-22's dead-code line list must be rebuilt against the post-Phase-5 module set | round 2 | PR-22 |
| 33 | `scripts/gen_ruff_ratchet.py` emits an empty block against the current tree, so the ratchet-regeneration workflow PR-23/PR-24 depend on cannot be exercised as documented | round 4 | PR-23 |
| 34 | Six pre-existing tracked files carry multi-component fragments of the real holdings roots (no complete root); one is a test module | round 4 | owner, then PR-24 / PR-36 |

No entry in the existing 1–28 is resolved or invalidated by this PR, and none of
them owns a symbol it touches.

### 11. Review loop

| Round | Verdict | Findings | Record |
|---|---|---|---|
| 1 | goal **not** met | **1 Major**, 4 Minor, 2 Deferred — the Major and all four Minor accepted and fixed, none rebutted | `critiques/pr-16/round-1.md` |
| 2 | goal met | 0 Major, 5 Minor (4 accepted and fixed, 1 rebutted), 3 Deferred (2 new entries) | `critiques/pr-16/round-2.md` |
| 3 | goal met | 0 Major, 6 Minor (all accepted and fixed, none rebutted), 2 Deferred (one folded into entry 29) | `critiques/pr-16/round-3.md` |
| 4 | goal met | **0 new Major**; the scoped re-review confirmed 15 of 16 prior findings resolved and the one rebuttal sound, and raised 1 incompletely-resolved Minor plus 2 non-blocking notes, all fixed | `critiques/pr-16/round-4.md` |

Round 1's Major is the one worth carrying forward: the moved code was
byte-perfect and every *call site* resolved, but a test **patched** the namespace
the moved function used to resolve through, so it silently stopped exercising the
code it was written for while still passing. The §6.2 set diff cannot see that
class of defect, which is what the adversarial round is for. Deferred entry 29
turns it into a step for PR-17 onward.

Two rounds touched `src/pdsfile/`, and under §6.6 step 5 each forced a
regeneration before the next reviewer. Round 1's fix (`37d4246`) regenerated both
trees, both modes. Round 3's fix (`b86adba` — a comment line in `_path_utils.py`)
regenerated the **head** side only, the baseline worktree being a detached tree at
`1a5d85c` that no round has touched; §3 records the runs from that second
regeneration. Round 2 changed only `plans/` and `critiques/`, which under the same
rule does not stale the record.

The one rebuttal is round 2's "the PR does not exist yet": §6.6 runs the loop
**before** the PR is opened ("Termination — … Then open the PR"), so a reviewer
cannot see the PR description at review time by construction. It is recorded in
`critiques/pr-16/round-2.md` rather than actioned.

##########################################################################################

## PR-17 — `refactor: extract shelf and local-filesystem subsystems`

**Branch:** `pr-17-shelves-local-fs`, based on `pr-16-path-utils` @ `2ff83a4`
("docs: record round 4 and close the review loop"), opened against that branch,
not `rewrite` (`plans/2026-07-26-addendum-phase5-stacked-prs.md`).
**Baseline:** **PR-16's recorded post-move set** — its §3 above, `--mode ns` 825
passed / 34 skipped (859 ids) and `--mode s` 555 passed / 3 skipped (558 ids) —
**re-measured locally on the parent tip** with this PR's own command lines rather
than copied from the table. The re-measurement reproduced it exactly.
**Date:** 2026-07-27
**Sub-plan:** [`plans/2026-07-27-pr-17-subplan.md`](../plans/2026-07-27-pr-17-subplan.md)
**Last change under `src/pdsfile/`:** commit `5320d83` (the round-2 docstring
clause), at 04:02:58. The **head** runs recorded below postdate it, per §6.6 step
5: their `--junitxml` timestamps are **09:07:05 and 09:09:56**. They were
regenerated after the owner-directed removal of the back-import guard, which
touched `tests/` only — that does not stale the record under step 5, but it drops
a test id, and the enumeration in §3 is meant to reproduce against the artifacts
rather than be approximately right. The **baseline** runs (02:49:30 and 02:52:19)
stand: they were taken in a detached worktree at `2ff83a4` that no round has
touched, so re-running them would measure the same unchanged tree.

This PR is the first that creates **mixin classes**, so §5's mixin mechanics are
exercised for real here rather than described. It is also the PR the parent plan
warns about most: `_local_fs` is the filesystem seam, and §11 below is the
monkeypatch audit that a pass/fail set diff structurally cannot perform.

### 1. Environment

| Item | Value |
|---|---|
| Interpreter | CPython 3.12.3, repo venv, `pip install -e ".[dev]"` |
| Holdings | `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` + `PDSFILE_TEST_HOLDINGS=full`, pointed at the limited testing copy the goldens are tuned to |
| Baseline tree | a `git worktree` detached at the parent tip `2ff83a4`, same interpreter, same holdings; `pytest` reports that directory as `rootdir` |
| Command lines | exactly those in `scripts/automated_tests/pdsfile_main_test.sh` (serial, under `coverage`), plus `-rA --junitxml` |

**Which source each run actually imported, proved rather than assumed.** The
interpreter is the main tree's venv, whose editable install puts `<main tree>/src`
on `sys.path`, and there are now three stacked branches sharing it, so a worktree
run could silently measure the wrong tree and make the comparison vacuous. After
each pair of passes, `coverage.CoverageData.measured_files()` was read for its
**absolute** paths (each run wrote its own `COVERAGE_FILE`):

| Run | pdsfile modules measured |
|---|---|
| baseline | `<worktree>/src/pdsfile/{pdsfile,_path_utils}.py` — and **no** `_shelves.py`, **no** `_local_fs.py`, because neither exists at `2ff83a4` |
| this branch | `<main tree>/src/pdsfile/{pdsfile,_path_utils,_shelves,_local_fs}.py` |

The absence of the two new modules on the baseline side is the decisive bit: had
the worktree run leaked into the main tree's install, they would have been
measured there too.

### 2. Active §2 gates

| Gate | Result |
|---|---|
| API-freeze manifest test | **passed** — the freeze test itself is one id, and `pytest tests/api/` is 15 (that one plus the 14 this PR adds there); and the dumped surface is byte-identical to the parent's — §4 |
| Full-data suite, both modes | **passed** — the only set movement is the 21 ids the two new test files add; §3 |
| `ruff check src/pdsfile tests scripts` | **passed**; the ratchet gained no code and lost four — §7 |
| Clean-install import check | **passed** (throwaway venv, `pip install .`, full module surface imports) |
| Hosted lint/no-holdings job (`scripts/run-all-checks.sh`, no holdings env vars) | **passed**, 80 passed / 800 skipped — the parent's 59/800 plus the same 21 new ids, re-measured on the parent worktree rather than quoted |
| Adversarial review loop | `critiques/pr-17/round-<k>.md` |

### 3. Full-data suite — the only movement is the two new test files

Both passes were run on the parent tip and on this branch's head with the same
interpreter and the same holdings. Every `testcase` element of each `--junitxml`
was reduced to one `outcome<TAB>classname::name` line, sorted, and the two files
were diffed with `diff -u`.

| Run | parent `2ff83a4` | `pr-17-shelves-local-fs` | set diff |
|---|---|---|---|
| `--mode ns` | 825 passed / 34 skipped (859 ids) | 846 passed / 34 skipped (880 ids) | **21 additions, nothing else** |
| `--mode s` | 555 passed / 3 skipped (558 ids) | 555 passed / 3 skipped (558 ids) | **empty** |

The parent numbers reproduce PR-16's recorded set, which is what makes this a
comparison against PR-16's baseline rather than against a fresh unrelated
measurement.

The 21 additions are the whole of the two test files this PR adds — 13 from
`tests/api/test_mixin_collisions.py` and 8 from
`tests/core/test_shelf_sidecar_record.py` — every one an `added, passed` line and
none of them a change to an existing id:

```
+passed  tests.api.test_mixin_collisions::test_a_mixin_defines_no_construction_or_attribute_hook[__getattr__]
+passed  tests.api.test_mixin_collisions::test_a_mixin_defines_no_construction_or_attribute_hook[__init__]
+passed  tests.api.test_mixin_collisions::test_a_mixin_defines_no_construction_or_attribute_hook[__init_subclass__]
+passed  tests.api.test_mixin_collisions::test_a_mixin_defines_no_construction_or_attribute_hook[__new__]
+passed  tests.api.test_mixin_collisions::test_a_mixin_defines_no_construction_or_attribute_hook[__setattr__]
+passed  tests.api.test_mixin_collisions::test_a_mixin_defines_no_construction_or_attribute_hook[__slots__]
+passed  tests.api.test_mixin_collisions::test_a_mixin_defines_only_callables_and_properties
+passed  tests.api.test_mixin_collisions::test_every_mixin_name_is_reachable_through_pdsfile
+passed  tests.api.test_mixin_collisions::test_no_mixin_is_shadowed_by_pdsfile_itself
+passed  tests.api.test_mixin_collisions::test_no_two_mixins_define_the_same_name
+passed  tests.api.test_mixin_collisions::test_the_class_statement_stays_in_pdsfile_pdsfile
+passed  tests.api.test_mixin_collisions::test_the_mixin_bases_are_listed_alphabetically
+passed  tests.api.test_mixin_collisions::test_the_mixins_are_found_and_come_from_private_modules
+passed  tests.core.test_shelf_sidecar_record.TestAMalformedRecord::test_an_unknown_name_is_a_name_error
+passed  tests.core.test_shelf_sidecar_record.TestAMalformedRecord::test_an_unparseable_line_raises_syntax_error[an unclosed tuple-"": ( 1,   2,\n]
+passed  tests.core.test_shelf_sidecar_record.TestAMalformedRecord::test_an_unparseable_line_raises_syntax_error[no colon at all-nothing to partition here\n]
+passed  tests.core.test_shelf_sidecar_record.TestAMalformedRecord::test_an_unparseable_line_raises_syntax_error[nothing after the colon-"":\n]
+passed  tests.core.test_shelf_sidecar_record.TestAMalformedRecord::test_the_last_character_is_dropped_whether_or_not_it_is_the_comma
+passed  tests.core.test_shelf_sidecar_record.TestAWellFormedRecord::test_a_line_read_back_off_a_written_sidecar_parses
+passed  tests.core.test_shelf_sidecar_record.TestAWellFormedRecord::test_the_five_values_come_back_as_python_objects
+passed  tests.core.test_shelf_sidecar_record.TestAWellFormedRecord::test_the_split_is_the_first_colon_and_not_one_of_the_timestamps
```

Nothing was removed and no existing id changed outcome, in either mode. They
appear in `--mode ns` only because `tests/api/` and `tests/core/` are in that pass
alone (the `--mode s` pass runs `tests/pds3file/` and `tests/rules/pds3/`).

All 21 are holdings-free, which is why the no-holdings count in §2 rises by the
same 21.

### 4. API freeze — empty diff, as a mixin move requires

1. `pytest tests/api/` passes. `tests/api/api_manifest.json`,
   `tests/api/manifest_allowlist.json`, `scripts/dump_public_api.py` and
   `tests/api/test_api_freeze.py` are untouched by this PR (§6.4) — verified with
   `git diff --stat 2ff83a4..HEAD` over those four paths, which is empty. No
   allowlist entry was added.
2. `scripts/dump_public_api.py` was run against a worktree at the parent tip and
   against this branch's head. The two dumps are **byte-identical** (733,876
   bytes each, `diff` empty).

That is the expected result and the plan says so: the dumper expands a class's
members with `dir(cls)`, which is MRO-wide, and records names, kinds and
signatures — never the defining class. So moving `PdsFile.glob_glob` into
`_LocalFsMixin` cannot show up here, and any diff would have meant a mistake.

`pdsfile._shelves` and `pdsfile._local_fs` are underscore-prefixed, so the dumper
skips them where the submodule import binds them onto the `pdsfile` package —
the freeze-invisibility the Phase-5 preamble requires of new internal names. The
same applies to `_ShelfMixin` and `_LocalFsMixin` inside `pdsfile.pdsfile`.

### 5. What moved, and the sweep that decided it

Fourteen methods, located by name (the plan's ":1259–1661" and ":5061–5359"
windows had drifted — PR-15 and PR-16 both edited this file).

| New module | Mixin class | Methods |
|---|---|---|
| `src/pdsfile/_shelves.py` | `_ShelfMixin` | `shelf_path_and_lskip`, `shelf_path_and_key`, `_get_shelf`, `_close_shelf`, `close_all_shelves`, `shelf_lookup`, `shelf_path_and_key_for_abspath`, `info_shelf_expected` (property), `shelf_exists_if_expected` |
| `src/pdsfile/_local_fs.py` | `_LocalFsMixin` | `_non_checksum_abspath`, `os_path_exists`, `os_path_isdir`, `os_listdir`, `glob_glob` — plus the module constant `PATH_EXISTS_CACHE_SIZE` |

All six shelf-cache class attributes stay defined on `PdsFile`: `SHELF_CACHE`,
`SHELF_ACCESS`, `SHELF_CACHE_SIZE`, `SHELF_CACHE_SLOP`, `SHELF_ACCESS_COUNT`,
`SHELF_NULL_KEY_VALUES`. The plan names three of the six; all six are class
attributes and the preamble keeps class attributes on `PdsFile`, so all six stay.
`SHELF_PATH_INFO` is defined on the `Pds3File` / `Pds4File` subclasses and is not
touched.

**The sweep was computed, not read.** CPython's `symtable` yields the
module-global names each moved method's body references; a second AST pass covers
each definition's decorator expressions and argument defaults, which are
evaluated in module scope and which `symtable` does not attribute to the method.
Result:

| Category | `_ShelfMixin` | `_LocalFsMixin` |
|---|---|---|
| module-level **constants** referenced | none | **`PATH_EXISTS_CACHE_SIZE`** |
| …of those, seen **only in a decorator** | — | **`PATH_EXISTS_CACHE_SIZE`** |
| module-level **classes** referenced (import-cycle risk) | **none** | **none** |
| module-level **functions** that would stay behind | **none** | **none** |
| unclassified names | **none** | **none** |
| imports the moved set needs | `os`, `pickle` | `bisect`, `fnmatch`, `functools`, `os`, and `_clean_glob` / `_needs_glob` from `._path_utils` |

The second pass is load-bearing, exactly as it was for PR-16's `_GLOB_CACHE_SIZE`:
`PATH_EXISTS_CACHE_SIZE` appears **only** inside
`@functools.lru_cache(maxsize=PATH_EXISTS_CACHE_SIZE)`, so a body-only sweep
reports it unreferenced and `_local_fs.py` raises `NameError` at import. It is
public and frozen, so `pdsfile.py` re-exports it.

**No import cycle, and no deferred import needed.** Parsing the two modules
reports their module-level imports as `os`, `pickle` for `_shelves` and `bisect`,
`fnmatch`, `functools`, `os`, `from ._path_utils import _clean_glob, _needs_glob`
for `_local_fs` — all at column 0, none of them `from pdsfile.pdsfile import`.
The sweep's "module-level CLASSES referenced: none" line is why no method needed
a function-local deferred import of `PdsFile`.

**How `_local_fs` reaches `_shelves`.** Only through `cls.` —
`cls.shelf_path_and_key_for_abspath(...)` and `cls._get_shelf(...)` — a runtime
MRO lookup, not an import. That is the coupling the plan means by "it calls into
`_shelves.py`, which is why it moves in the same PR": neither module imports the
other, but four of `_local_fs`'s five methods are broken unless both mixins are
bases of the same class, so splitting them across two PRs would leave the first
one red.

**Zero names lost, measured.** `sorted(vars(pdsfile.pdsfile))` was compared
between the parent worktree and this branch: **45 names before, 47 after, none
lost.** The two gained are `_LocalFsMixin` and `_ShelfMixin`, which the `class
PdsFile` statement needs; both are underscore names, so the manifest does not see
them.

**Byte-for-byte equivalence, measured.** At the extraction commit (`7b581a1`, a
pure move) each moved definition's exact source segment (decorators included) was
extracted from the parent commit's `PdsFile` body and from the new mixin's body
and compared byte by byte: **all fourteen methods and `PATH_EXISTS_CACHE_SIZE`
identical**. The contiguous run from the first moved definition to the last also
compares identical as a single blob on each side — 11,388 bytes for the shelf
block, 17,520 for the local-filesystem block — which additionally rules out a
reordering or a dropped blank line. Nothing moved is still defined in
`pdsfile.py`, and neither new module carries a name that was not on the move
list. No moved body was restyled to dodge an inherited lint violation; that is
PR-23's job.

At HEAD the same check reports thirteen of the fourteen still identical, the
exception being `shelf_lookup` and the shelf block that contains it. That is
§8's `eval()` isolation, which the parent plan requires and which is a
**separate commit** (`1b0011d`) precisely so that the byte-for-byte claim above
is exactly checkable at `7b581a1`, and so that no commit mixes a move with a
content edit (§2 commit granularity). `_LocalFsMixin` is byte-identical at HEAD
as well as at the extraction commit.

`pdsfile.py`: 6,125 → 5,436 lines; `_shelves.py` 356; `_local_fs.py` 437.

### 6. The base order, and why it is alphabetical

```python
class PdsFile(_LocalFsMixin, _ShelfMixin, object):
```

This is the first Phase-5 mixin PR, so this list is the pattern PR-18 through
PR-22 extend. The rule chosen, and asserted by
`tests/api/test_mixin_collisions.py`, is **alphabetical by mixin class name, with
`object` last**:

1. **MRO order is behaviorally inert here, and is kept that way on purpose.** The
   mixins share no attribute name and neither shadows a name `PdsFile` defines
   itself — which is what the new test asserts. So the ordering rule cannot be
   chosen for semantics; it should be chosen for reviewability.
2. **Append-on-arrival would encode PR chronology** into the class statement. A
   reader cannot derive it, a reviewer cannot check it, and by PR-22 the list is
   eight entries whose order means "the sequence six executors happened to run
   in".
3. **Alphabetical gives every future mixin exactly one legal position**, derivable
   without knowing anything about PR order, and it is machine-checkable — so the
   convention is enforced by a test rather than by each executor having read this
   section.
4. **Dependency order would be a lie.** `_LocalFsMixin` calls into `_ShelfMixin`,
   but through `cls.`, so no ordering of bases expresses or affects it.
5. `object` stays last, where it is today, so `PdsFile.__bases__[-1] is object` is
   unchanged and the `UP004` count in the ratchet is unchanged with it.

`object` is **not a mixin** and is **not required** — Python 3 derives every class
from it whether or not it is written down, so `class PdsFile(_LocalFsMixin,
_ShelfMixin)` would give the identical MRO. It is in the list only because it was
already in the class statement before this PR, and a move PR changes nothing it
does not have to. Removing it is an unrelated cleanup for a later PR, most
naturally PR-23, which owns the core modules' ruff cleanup and already carries
`UP004` for this exact line; whoever does it should also drop the
`PdsFile.__bases__[-1] is object` assertion, which stops being meaningful with it.
`tests/api/test_mixin_collisions.py` discovers mixins by filtering `object` out of
`__bases__`, so neither the ordering rule nor the collision checks depend on it.

`tests/api/test_mixin_collisions.py` **discovers** the mixins from
`PdsFile.__bases__` rather than listing them, so PR-18–22 get all of its checks
the moment they add a base. Beyond the set-intersection check the preamble asks
for, it asserts that the discovery found something at all (so the module cannot
pass vacuously), that the `class PdsFile` statement is still in `pdsfile.pdsfile`
(pickles depend on it), that every mixin name resolves through `PdsFile` to the
same object, that no mixin defines `__init__`/`__new__`/`__slots__`/an attribute
hook or holds class-level data, and the base order.

**It is not tautological — measured.** Each invariant was broken in turn in a
worktree and the module re-run:

| Mutation | Went red |
|---|---|
| bases listed out of alphabetical order | `test_the_mixin_bases_are_listed_alphabetically` |
| the same method name defined by both mixins | `test_no_two_mixins_define_the_same_name`, `test_every_mixin_name_is_reachable_through_pdsfile` |
| a mixin carries class-level state (`SHELF_CACHE = {}`) | `test_a_mixin_defines_only_callables_and_properties` + 2 |
| a mixin defines `__init__` | `test_a_mixin_defines_no_construction_or_attribute_hook[__init__]` + 2 |
| `PdsFile` redefines a name a mixin supplies | `test_no_mixin_is_shadowed_by_pdsfile_itself`, `test_every_mixin_name_is_reachable_through_pdsfile` |
| no mixin bases at all | `test_the_mixins_are_found_and_come_from_private_modules` |
| a mixin claims a public `__module__` | `test_the_mixins_are_found_and_come_from_private_modules` |
| the class statement moved out of `pdsfile.pdsfile` | `test_the_class_statement_stays_in_pdsfile_pdsfile` |

Every check in the module is killed by at least one mutation.

**What is *not* in this file, and why.** An earlier draft also asserted the
preamble's other pinned mechanic — that a mixin module must not import
`pdsfile.pdsfile` at import time. It was a voluntary addition (the plan asks this
file for the collision check and nothing more), it produced the **only two Major
findings of the five review rounds**, and the owner's decision was to strip it and
defer it rather than patch it a third time. Both Majors share a root cause worth
carrying forward: an AST walk is a syntactic approximation of a runtime fact, so
its case matrix only grows — relative vs absolute spellings, aliased forms,
nesting in module-level `try`/`if`/`with`, class bodies (which **do** execute at
import time), the `else` of `if TYPE_CHECKING:`, `match`/`case`, and `__import__`
and star-imports still ahead of it. The robust form is behavioral: import each
mixin module in a fresh interpreter before `pdsfile.pdsfile` and assert it never
lands in `sys.modules`. `critiques/deferred-observations.md` entry 42 carries the
full history and assigns it to **PR-22**, the last Phase-5 PR, where the check
would run over the complete mixin set.

Meanwhile the two spellings that import `PdsFile` itself raise
`ImportError … circular import` and fail the whole suite at collection, so the
obvious wrong thing still self-reports; only an import of some other already-bound
name out of the core module would be silent. Both of this PR's mixin modules were
verified clean by parsing them — §5's "no import cycle" paragraph.

### 7. Ruff ratchet — four codes dropped, none gained

Procedure: for every code in `pdsfile.py`'s entry, the following was run against
all three files after the move —

```
ruff check --no-cache --isolated --output-format concise --select <code> \
           --line-length 100 --target-version py310 <file>
```

`--isolated` drops `pyproject.toml`'s `line-length = 100` and would otherwise
report an E501 at 88 columns that the project config does not, so the two
settings are restored explicitly (PR-16 §7 records the same trap). Reproducing
the counts below requires that exact command, including
`--output-format concise`: ruff 0.15's default output no longer starts a line
with the file path.

**Every one of the 23 codes conserves exactly** — parent count = the three
post-move counts summed — which is the mechanical statement of "this is a split
of an existing entry, not a new suppression":

| Code | parent `pdsfile.py` | → `pdsfile.py` | `_local_fs.py` | `_shelves.py` |
|---|---|---|---|---|
| A002 | 3 | 3 | 0 | 0 |
| B007 | 1 | **0** | 1 | 0 |
| B904 | 4 | 3 | 0 | 1 |
| B905 | 2 | **0** | 1 | 1 |
| C405 | 3 | 3 | 0 | 0 |
| E501 | 5 | 5 | 0 | 0 |
| E701 | 14 | 11 | 3 | 0 |
| E713 | 1 | 1 | 0 | 0 |
| E721 | 1 | 1 | 0 | 0 |
| F841 | 6 | 5 | 0 | 1 |
| I001 | 2 | 2 | 0 | 0 |
| N806 | 2 | 2 | 0 | 0 |
| RUF005 | 8 | 8 | 0 | 0 |
| RUF012 | 16 | 16 | 0 | 0 |
| RUF059 | 1 | **0** | 0 | 1 |
| SIM102 | 1 | 1 | 0 | 0 |
| SIM103 | 3 | **0** | 2 | 1 |
| SIM114 | 2 | 2 | 0 | 0 |
| SIM118 | 2 | 1 | 1 | 0 |
| UP004 | 1 | 1 | 0 | 0 |
| UP015 | 1 | 1 | 0 | 0 |
| UP024 | 18 | 13 | 3 | 2 |
| UP031 | 12 | 9 | 0 | 3 |

Resulting entries:

| File | Entry | Note |
|---|---|---|
| `src/pdsfile/pdsfile.py` | 23 codes → **19** | B007, B905, RUF059 and SIM103 no longer occur in it, so they are **removed** |
| `src/pdsfile/_local_fs.py` | `["B007", "B905", "E701", "SIM103", "SIM118", "UP024"]` | exactly the codes its moved lines trigger |
| `src/pdsfile/_shelves.py` | `["B904", "B905", "F841", "RUF059", "SIM103", "UP024", "UP031"]` | same |

Every code in the two new entries was already in `pdsfile.py`'s parent entry, so
no code that was not already forgiven for these same lines is forgiven now; had a
new module needed a code absent from that entry, the sub-plan makes it a §6.4
hard stop. The number of suppressed violations is unchanged and the ratchet's
distinct (file, code) pairs move 23 → 19 + 6 + 7. The two new modules' own import
blocks were written sorted so that neither needs `I001`, which is why that row
conserves rather than growing by one per file.

### 8. The `eval()`, isolated with a documented contract

The parent plan requires the `.py`-sidecar `eval()` to be **kept** (it is
behavior; ground rule 9) but **isolated in one named function with a documented
contract**. It is now `_eval_null_key_record(rec)`, a module-level private
function in `_shelves.py`, called from `shelf_lookup` in place of the three lines
that used to do the parse inline. The `eval()` expression itself is unchanged
character for character; nothing was replaced with `ast.literal_eval`, which
would reject records `eval` accepts and so would be a behavior change.

The docstring states what the input is (the *second* line of an info-shelf
`*_info.py` sidecar, as returned by `readline()`, newline included), the shape
expected, what the parse does step by step, and how it behaves on malformed input
**today** — no colon → `eval('')` → `SyntaxError`; an incomplete expression →
`SyntaxError`; a line not ending in the trailing comma still loses its last
character, which can silently turn one valid expression into a different one; a
bare name → resolved against the module globals then builtins, else `NameError`.
It also states plainly that the sidecar is executable input and the trust
boundary is the holdings tree, whose sidecars this package's own maintenance
tools write. No validation was added.

**Exercised by tests, not only by a one-off run.** `tests/core/test_shelf_sidecar_record.py`
builds its own two-line sidecar in `tmp_path` and pins the contract the docstring
states: the five values and their types, that the split is the *first* colon and
not one of the timestamp's, that a line read back off a written file parses, and
what each malformed shape does today — `SyntaxError` for a line with no colon, an
unclosed tuple or nothing after the colon; `NameError` for a bare name; and the
silent one, that the final character is dropped by position rather than by
matching the comma, so `"": 123` yields `12`. Eight ids, holdings-free.

**The one consequence worth measuring: the `eval` now runs in
`pdsfile._shelves`'s module namespace rather than `pdsfile.pdsfile`'s** (and its
locals shrink from `shelf_lookup`'s frame to just `rec` and `parts`). That is
observable only by a record whose expression references a *name*. Measured
directly rather than argued: the second line of **every one of the 6,753**
`*_info.py` sidecars under the complete holdings set was parsed with `ast`, and

- **0** contain a `Name` node — so no real record can observe which module's
  globals were in scope;
- **6,753 of 6,753** evaluate to the same shape, `(int, int, str, str, tuple)`;
- 0 fail to parse.

Note for anyone re-running this: the **limited testing copy carries no
`*_info.py` sidecars at all** (only the `.pickle` files), so this branch of
`shelf_lookup` is never reached by the local full-data suite — its set diff is
silent about it either way. It was therefore exercised directly against the
complete set, with the isolated function instrumented to confirm the call
arrives: `shelf_lookup('info')` on a bundle-level `PdsFile` returns
`(4594843481, 9, '2014-07-08 17:47:46.000000', '', (0, 0))` and
`_eval_null_key_record` is recorded as having been called with the sidecar line.

### 9. Consumer smoke — outcome unchanged

The gate is **same outcome as baseline**, not "passes"
(`critiques/baselines/consumer-smoke-baseline.md`).

| Check | Baseline | This branch |
|---|---|---|
| A — rms-opus import paths | 4/4 resolve, 0 failures | **4/4 resolve, 0 failures** |
| B — rms-viewmaster startup | 5 ok, 3 pre-existing failures | **5 ok, 3 failures — the same three** |

The three Check-B failures are still `pdsfile.cache_lifetime` (raises),
`pdsfile.DEFAULT_CACHING` (absent) and the same `cache_lifetime` read inside
`get_page_cache()`. None became a pass.

This PR is one of the few that could plausibly break a consumer, because both
consumers call a name it moves — rms-opus at
`opus/import/do_import.py:1577` (`file.shelf_exists_if_expected()`) and
rms-viewmaster at `viewmaster/pdsiterator.py:102`
(`pdsf_cls.glob_glob(...)`). Both reach them through an instance or a class, so
the mixin move is invisible to them; both were checked directly, along with their
signatures, and `pdsfile.pdsfile.repair_case` (the name PR-16's baseline note
flags) still resolves.

Environment note carried from the baseline: the check ran under the pdsfile
venv's interpreter with rms-viewmaster's `site-packages` appended to
`PYTHONPATH`, because that venv lacks pdsfile's declared `range_ex` dependency.
rms-viewmaster is at `a0d05e2` with the same three untracked entries the baseline
records.

### 10. Clean install

`scripts/clean_install_check.sh` passes inside `run-all-checks.sh`. The two new
modules are picked up by the existing `include = ["pdsfile*"]` package glob with
no packaging change: a `pip wheel --no-deps` build contains
`pdsfile/_shelves.py` and `pdsfile/_local_fs.py`, and the gate imports the whole
manifest module surface — `pdsfile.pdsfile` among them — which cannot succeed if
either is missing from the distribution.

### 11. The monkeypatch audit — the check the set diff cannot perform

Deferred entry 29 (opened by PR-16's round-1 Major, owned by "PR-17 onward") says
an extraction sweep must also ask **which namespaces the tests patch**, not only
which globals the code reads. A test whose patch lands on a module the moved code
no longer resolves through keeps passing while exercising nothing, and §6.2's
outcome-set diff compares pass/fail — so it is *structurally blind* to this
class of defect. `_local_fs` is the worst case in the phase, being the
`os.path.exists` / `os.listdir` / `glob.glob` seam.

**Enumeration.** Every `monkeypatch.setattr` / `setitem` / `delattr` / `setenv` /
`delenv`, `mock.patch`, `patch(`, `patch.object` and bare `setattr(` in `tests/`
and `scripts/` — 20 sites, all `monkeypatch`; the tree uses no `unittest.mock`
at all:

| Target | Sites | Touched by this PR? |
|---|---|---|
| `Pds3File.shelf_path_and_key_for_abspath` (`tests/core/test_pdsfile_path_resolution.py:120,129,137,155`) | 4 | **yes — a symbol this PR moves** |
| `abspath_for_logical_path.__globals__['glob']` (`:92`) | 1 | no — PR-16's fix site, on `_path_utils`'s globals |
| `Pds3File`/`Pds4File.CACHE`, `.LOCAL_PRELOADED`, `.LOCAL_HOLDINGS_DIRS` | 8 | no — class attributes that stay on the classes |
| `pdsviewable.ICON_SET_BY_TYPE` | 1 | no — different module |
| `monkeypatch.setenv` / `delenv` | 6 | no — environment, not a namespace |

One further site is not a `monkeypatch` at all and is easy to miss for that
reason: `tests/pds4file/test_pds4file_blackbox.py:448` assigns
`dummy.glob_glob = lambda …` directly. A regex over `tests/`, `scripts/` and
`src/` for direct assignment to any of the fourteen moved names or
`PATH_EXISTS_CACHE_SIZE` returns exactly that one. It is unaffected: the target is
an **instance** attribute on a `Pds4File.__new__`-built dummy, and an instance
attribute wins over the MRO both before and after the move. The test's assertion
compares against `fake_glob_results`, so it would go red if the stub were
bypassed.

The four affected sites patch the **class** (`Pds3File`), not a module namespace,
and the caller — the `infoshelf_path_and_key` property — invokes
`cls.shelf_path_and_key_for_abspath(...)`. Both sides of that are MRO lookups, so
the patch keeps reaching the method after it moves to `_ShelfMixin`. `monkeypatch`
finds no entry in `Pds3File.__dict__` before or after, so its undo still deletes
the attribute and restores inheritance.

**Proved, not argued — two negative controls per site.** Each control must turn
the test red:

| Control | Result |
|---|---|
| **B — the stub is reached but answers wrongly** (`_raise` returns `('/wrong/shelf.pickle', 'WRONG/KEY')` instead of raising; the success stub returns a different pair) | **all 5 ids red** — which can only happen if the property is calling the stub |
| **A — the stub is misdirected** onto a namespace nothing resolves through (patched onto an unrelated class, the exact PR-16 shape) | 3 of 5 red |
| **B on the PR-16 fix site** (`glob.glob` stub returns a hit instead of `[]`) | `test_a_class_does_not_borrow_another_class_holdings_root` red |

Control A leaves two ids green, and that is correct rather than a gap: with the
patch misdirected, the *real* `shelf_path_and_key_for_abspath` runs on
`volumes/NOSUCH_0xxx/NOSUCH_0001` and legitimately raises, so the property still
answers `('', '')`. Control B is the discriminating one, and it turns all five
red. No surviving patch site is a test that passes both ways.

**Entry 29's second half — rebinding re-exported *data*.** The same asymmetry one
level down, measured on both sides:

| | parent `2ff83a4` | this branch |
|---|---|---|
| namespace `os_path_exists` / `glob_glob` resolve through | `pdsfile.pdsfile` | `pdsfile._local_fs` |
| namespace `_get_shelf` / `shelf_lookup` resolve through | `pdsfile.pdsfile` | `pdsfile._shelves` |
| rebinding `pdsfile.pdsfile.os` / `.pickle` / `.bisect` / `.fnmatch` / `.functools` / `.glob` reaches the consumer | **yes** | **no** |
| `PdsFile.os_path_exists` `lru_cache` maxsize | 200 | 200 |

`PATH_EXISTS_CACHE_SIZE` is the case the plan singles out, and it is inert in
both directions: the decorator reads it once, when the class body executes, so
rebinding it after import never had any effect and still does not. Nothing in
`src/`, `tests/`, `scripts/`, rms-opus or rms-viewmaster rebinds any of these
names — greped, zero hits — so nothing is broken today. The general observation
stands for PR-18 onward and stays in `critiques/deferred-observations.md` as
entry 29.

**The set diff cannot see any of this.** That is the point of the section: every
one of these tests passed before the move and passes after it, and a
pass/fail-set comparison would have reported "identical" in every case, including
the broken one PR-16 found.

### 12. Deferred observations

Entry 29 is the one this PR was told to act on, and §11 is the action. It is
**not** resolved — it is a per-PR step, owned by "PR-17 onward" — so it stays
open for PR-18 through PR-22 with this PR's method as the worked example.
Entry 30 (`repair_case`'s `UnboundLocalError`) sits in `_path_utils.py`, which
this PR does not touch. No entry in 1–34 is resolved or invalidated here.

Eight entries are **added** by this PR's review loop: 35 (the plan's illustrated
base order, now answered by the owner and by PR #110), 36–38 from round 2, 39–41
from round 3, and **42**, which owns the removed back-import guard — its history,
the design note that the robust implementation is behavioral rather than
syntactic, and its owner, **PR-22**.

### 13. Review loop

| Round | Verdict | Findings | Record |
|---|---|---|---|
| 1 | goal met | 0 Major, 3 Minor (all accepted and fixed), 2 Deferred — one of which was taken up rather than deferred | `critiques/pr-17/round-1.md` |
| 2 | goal met | 0 Major, 6 Minor (5 accepted and fixed, 1 partly rebutted), 3 Deferred (entries 36–38) | `critiques/pr-17/round-2.md` |
| 3 | goal met | 0 Major, 3 Minor (all accepted and fixed), 3 Deferred (entries 39–41) | `critiques/pr-17/round-3.md` |
| 4 (scoped) | **goal not met** | **1 new Major** (fixed), 0 new Minor, 3 non-blocking notes; 11 of 12 prior findings confirmed resolved | `critiques/pr-17/round-4.md` |
| 5 (scoped, owner-authorized) | **goal not met** | round 4's Major **fully resolved**; **1 new Major, verified and deliberately NOT fixed** | `critiques/pr-17/round-5.md` |

**Both Majors are resolved by removal, and there is no sixth round.** The owner
decided (2026-07-27) to **strip the back-import guard and defer it** — option 1 of
the three round 5 laid out, and what round 1 originally proposed when it raised
the item in the *Deferred* bucket. No sixth round is needed because the reviewed
surface **shrinks rather than changes**: what remains in
`tests/api/test_mixin_collisions.py` is the plan's actual deliverable, the
set-intersection collision check, plus the base-order and mixin-mechanics
assertions — 13 ids, every one of them already reviewed and mutation-proved in
rounds 1–5. Nothing under `src/pdsfile/` was touched by the removal, and the
gates were re-run after it: §3's set diff, §4's manifest diff, the ratchet, the
no-holdings count and the clean-install gate all above reflect the post-removal
tree.

**The 4-round cap was reached with a new Major, which §6.6 makes an owner
matter.** That Major was fixed — step 4 requires every Major to be resolved — and
the executor stopped. **The owner then authorized a fifth round** on the grounds
that rounds 1–3 each returned zero Majors, so the loop was converging rather than
thrashing, and that the round-4 Major sat in a **voluntary addition** rather than
a plan deliverable: the plan asks this file for a set-intersection check, and the
back-import guard is an extra taken up from round 1's *Deferred* bucket.

**Round 5 confirmed round 4's Major fully resolved and found a new one in the same
guard** — an import in a `class` body is a real import-time cycle that the guard
missed in silence, along with the `else` branch of `if TYPE_CHECKING:` and
`match`/`case`. It is reproduced in `critiques/pr-17/round-5.md`. It was **not**
fixed: a second breach of the cap is the mis-scope signal the rule exists to
raise, so the decision went to the owner, who **stripped the guard and deferred
it** (entry 42, owner PR-22). That is what makes the cap actionable rather than
decorative — the mis-scope it surfaced was a check the plan never asked for
consuming two of five rounds.

Three rounds touched `src/pdsfile/` or its test surface. Under §6.6 step 5, round
1's and round 2's fixes each forced a regeneration before the next reviewer; §3's
recorded runs are round 2's. Rounds 3 and 4 changed only `tests/`, `plans/` and
`critiques/`, which under the same rule does not stale the record — and round 4's
fix changes no test id, so the recorded 22-addition set diff still describes the
tree.

Two rebuttals are recorded rather than actioned, both about the base order
(round 2's Minor 5 and, in part, round 3's M3): a class statement cannot be
written without choosing an order, so "surface it, do not choose" cannot be
satisfied literally by the PR whose deliverable is that statement. What was
accepted is that the surfacing had to be blocking, which is why
`plans/2026-07-27-addendum-phase5-mixin-base-order.md` exists and why PR-17
cannot merge without the owner acknowledging it.

---

## PR-18 — `refactor: extract checksum/archive/log path builders → _derived_paths.py`

**Branch:** `pr-18-derived-paths`, based on `pr-17-shelves-local-fs` @ `ca7a43d`
("docs: refresh the PR-17 figures after the guard removal and repair the
record"), opened against that branch, not `rewrite`
(`plans/2026-07-27-addendum-phase5-stack-extension.md`, which this PR writes).
**Baseline:** **PR-17's recorded post-move set** — its §3 above, `--mode ns` 846
passed / 34 skipped (880 ids) and `--mode s` 555 passed / 3 skipped (558 ids) —
**re-measured locally on the parent tip** with this PR's own command lines rather
than copied from the table. The re-measurement reproduced it exactly.
**Date:** 2026-07-27
**Sub-plan:** [`plans/2026-07-27-pr-18-subplan.md`](../plans/2026-07-27-pr-18-subplan.md)
**Last change under `src/pdsfile/`:** commit `5115c38` (round 3's
keyword-argument and docstring-heading fixes), at **16:03:09**. The **head** runs
recorded below postdate it, per §6.6 step 5: their `--junitxml` timestamps are
**16:03:13 and 16:06:07**. They are the third regeneration step 5 required —
round 1's fixes, round 2's comment fix and round 3's keyword fix each touched
`src/pdsfile/`. The three superseded head pairs (14:29:04 / 14:31:56, 15:15:58 /
15:18:50 and 15:41:26 / 15:44:19) each produced the same two empty diffs. The
**baseline** runs (14:19:27 and 14:22:21) stand throughout: they were taken in a
detached `git worktree` at `ca7a43d` that nothing has touched since.

This PR is the first Phase-5 extraction whose set diff is **empty in both
modes** — it adds no test file and no test id, so unlike PR-15, PR-16 and PR-17
there is no legitimate movement to enumerate and any movement at all would be a
hard stop.

### 1. Environment

| Item | Value |
|---|---|
| Interpreter | CPython 3.12.3, repo venv, `pip install -e ".[dev]"` |
| Holdings | `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` + `PDSFILE_TEST_HOLDINGS=full`, pointed at the limited testing copy the goldens are tuned to |
| Baseline tree | a `git worktree` detached at the parent tip `ca7a43d`, same interpreter, same holdings; `pytest` reports that directory as `rootdir` |
| Command lines | exactly those in `scripts/automated_tests/pdsfile_main_test.sh` (serial, under `coverage`), plus `-rA --junitxml` |

**Which source each run actually imported, proved rather than assumed.** The
interpreter is the main tree's venv, whose editable install appends
`<main tree>/src` to `sys.path`, and there are now four stacked branches sharing
it, so a worktree run could silently measure the wrong tree and make the whole
comparison vacuous. Each run wrote its own `COVERAGE_FILE`, and
`coverage.CoverageData.measured_files()` was read afterwards for its **absolute**
paths:

| Run | pdsfile modules measured |
|---|---|
| baseline | `<worktree>/src/pdsfile/{pdsfile,_path_utils,_shelves,_local_fs}.py` — and **no** `_derived_paths.py`, because it does not exist at `ca7a43d` |
| this branch | `<main tree>/src/pdsfile/{pdsfile,_path_utils,_shelves,_local_fs,_derived_paths}.py` |

The absence of `_derived_paths.py` on the baseline side is the decisive bit: had
the worktree run leaked into the main tree's install, it would have been measured
there too. The two lists are otherwise identical, module for module.

### 2. Active §2 gates

| Gate | Result |
|---|---|
| API-freeze manifest test | **passed** — and the dumped surface is byte-identical to the parent's, 733,876 bytes each; §4 |
| Full-data suite, both modes | **passed** — **the set diff is empty in both modes**; §3 |
| `ruff check src/pdsfile tests scripts` | **passed**; the ratchet gained no code and `pdsfile.py`'s entry lost one — §7 |
| Clean-install import check | **passed** (throwaway venv, `pip install .`, full module surface imports) |
| Hosted lint/no-holdings job (`scripts/run-all-checks.sh`, no holdings env vars) | **passed**, **80 passed / 800 skipped** — the parent's figure, unchanged, because this PR adds no test |
| Adversarial review loop | `critiques/pr-18/round-<k>.md` |

### 3. Full-data suite — an empty set diff in both modes

Both passes were run on the parent tip and on this branch's head with the same
interpreter and the same holdings. Every `testcase` element of each `--junitxml`
was reduced to one `outcome<TAB>classname::name` line, sorted, and the two files
were diffed with `diff -u`.

| Run | parent `ca7a43d` | `pr-18-derived-paths` | set diff |
|---|---|---|---|
| `--mode ns` | 846 passed / 34 skipped (880 ids) | 846 passed / 34 skipped (880 ids) | **empty** |
| `--mode s` | 555 passed / 3 skipped (558 ids) | 555 passed / 3 skipped (558 ids) | **empty** |

`diff -u` produced **zero output lines** for each mode. The parent numbers
reproduce PR-17's recorded set, which is what makes this a comparison against
PR-17's baseline rather than against a fresh unrelated measurement.

Both modes matter and both were run: `--mode s` is the only thing that exercises
the `SHELVES_ONLY` branch, and `checksum_path_if_exact` and
`archive_path_if_exact` both call `cls.os_path_exists`, which is where that
branch lives.

### 4. API freeze — empty diff, as a mixin move requires

1. `pytest tests/api/` passes — 14 ids, the freeze test plus the 13 the parent's
   `tests/api/test_mixin_collisions.py` contributes. `tests/api/api_manifest.json`,
   `tests/api/manifest_allowlist.json`, `scripts/dump_public_api.py` and
   `tests/api/test_api_freeze.py` are untouched by this PR (§6.4) — verified with
   `git diff --stat ca7a43d..HEAD` over those four paths, which is empty. No
   allowlist entry was added.
2. `scripts/dump_public_api.py` was run against a worktree at the parent tip and
   against this branch's head. The two dumps are **byte-identical** (733,876
   bytes each, `diff` empty).

That is the expected result and the plan says so: the dumper expands a class's
members with `dir(cls)`, which is MRO-wide, and records names, kinds and
signatures — never the defining class. So moving `PdsFile.log_path_for_index`
into `_DerivedPathsMixin` cannot show up here, and any diff would have meant a
mistake.

`pdsfile._derived_paths` is underscore-prefixed, so the dumper skips it where the
submodule import binds it onto the `pdsfile` package; the same applies to
`_DerivedPathsMixin` inside `pdsfile.pdsfile` and to the new `_log_path_for`
helper on the mixin. That is the freeze-invisibility the Phase-5 preamble
requires of new internal names.

**One thing the manifest does not record, and that does change: member
`__qualname__`.** `PdsFile.archive_logpath.__qualname__` is now
`_DerivedPathsMixin.archive_logpath`, so a wrong-arity call reports
`_DerivedPathsMixin.archive_logpath() missing 1 required positional argument`
where it used to name `PdsFile`. This is a **phase-wide** consequence of the
mandated mixin technique rather than anything PR-18 chose — it is already true of
`_ShelfMixin` and `_LocalFsMixin` on the parent branch — and the dumper records
`kind` and `signature`, never a qualname, which is why the dump is byte-identical
regardless. Measured: nothing in `src/`, `tests/`, `scripts/`, rms-opus or
rms-viewmaster matches on that text, so no caller, test or golden depends on it.
Raised by round 1 as Minor 2.

The three public signatures the deduplication passes through are frozen and
unchanged, which the byte-identical dump also asserts:
`log_path_for_bundle(self, suffix='', task='', dir='', place='default')`,
`log_path_for_bundleset(self, suffix='', task='', dir='', place='default')` and
`log_path_for_index(self, task='', dir='index', place='default')`.

### 5. What moved, and the sweep that decided it

Eleven definitions, located by name. The plan's ":4898–5059" and ":5361–5516"
windows are against the 6,304-line original; PR-15, PR-16 and PR-17 have all
edited this file, which is 5,436 lines at the parent tip.

| New module | Mixin class | Definitions |
|---|---|---|
| `src/pdsfile/_derived_paths.py` | `_DerivedPathsMixin` | `checksum_path_and_lskip`, `checksum_path_if_exact`, `dirpath_and_prefix_for_checksum`; `archive_path_and_lskip`, `archive_path_if_exact`, `dirpath_and_prefix_for_archive`, `archive_logpath`; `set_log_root` (classmethod), `log_path_for_bundle`, `log_path_for_bundleset`, `log_path_for_index` |

**The move steps around a block it must not touch.** The two source windows are
not adjacent: between them sits the `# Shelf support` banner holding the six
class attributes PR-17 deliberately left on `PdsFile` — `SHELF_CACHE`,
`SHELF_ACCESS`, `SHELF_CACHE_SIZE`, `SHELF_CACHE_SLOP`, `SHELF_ACCESS_COUNT`,
`SHELF_NULL_KEY_VALUES`. Neither the attributes nor the banner is touched, so the
extraction is two deletions from `pdsfile.py`, not one.

**`LOG_ROOT_` does not move**, and neither does `LOGFILE_TIME_FMT`. Both are class
attributes, which the preamble keeps on `PdsFile`, and both are **frozen manifest
members** (`"kind": "data"`), so the answer is not merely conventional — moving
either off the class would be a manifest break. `LOG_ROOT_` keeps its
`# Log path associations` banner in `pdsfile.py`, exactly the shape PR-17 left
the shelf block in. Both halves of its traffic still work from a mixin because
both go through the class at call time: `set_log_root` is a classmethod that
assigns `cls.LOG_ROOT_`, and the three `log_path_for_*` methods read
`cls.LOG_ROOT_` and `cls.LOGFILE_TIME_FMT` after `cls = type(self)`. Measured:
`LOG_ROOT_`, `LOGFILE_TIME_FMT` and `SHELF_CACHE` are all still in
`PdsFile.__dict__` on this branch, exactly as on the parent.

**The sweep was computed, not read.** CPython's `symtable` yields the
module-global names each moved definition's body references; a second AST pass
covers each definition's decorator expressions and argument defaults, which are
evaluated in module scope and which `symtable` does not attribute to the method.
Result:

| Category | `_DerivedPathsMixin` |
|---|---|
| module-level **imports** referenced | **`datetime`** (by the three `log_path_for_*` bodies only) |
| module-level **constants** referenced | **none** |
| module-level **functions** referenced | **none** |
| module-level **classes** referenced (import-cycle risk) | **none** |
| unclassified names | **none** |
| seen **only** in a decorator or an argument default | **none** |

The second pass found nothing this time, which is itself the result worth
recording: PR-16's `_GLOB_CACHE_SIZE` and PR-17's `PATH_EXISTS_CACHE_SIZE` were
both invisible to a body-only sweep, so the pass is run whether or not it is
expected to fire, and its "none" is measured rather than assumed.

**No module-level name leaves `pdsfile.py` in this PR** — the difference from
PR-16 and PR-17, and the reason no redundant-alias re-export was needed.
`pdsfile.py` still uses `datetime` in seven places in its properties block, so
`import datetime` stays a plain import there and `pdsfile.pdsfile.datetime` still
resolves (measured on both sides).

**No import cycle, and no deferred import needed.** Parsing the new module
reports exactly one module-level import, `import datetime` at column 0, and no
`from pdsfile.pdsfile import` of any spelling. The sweep's "module-level CLASSES
referenced: none" line is why no method needed a function-local deferred import
of `PdsFile`.

**How `_derived_paths` reaches the other mixins.** Only through `cls.` —
`checksum_path_if_exact` and `archive_path_if_exact` both call
`cls.os_path_exists(...)`, which `_LocalFsMixin` supplies — a runtime MRO lookup,
not an import. `archive_logpath` reaches `log_path_for_bundle` through `this.`,
an instance of the same class. Neither module imports the other.

**Zero names lost, measured.** `sorted(vars(pdsfile.pdsfile))` was compared
between the parent worktree and this branch: **47 names before, 48 after, none
lost.** The one gained is `_DerivedPathsMixin`, which the `class PdsFile`
statement needs; it is an underscore name, so the manifest does not see it.

**Byte-for-byte equivalence, measured.** At the extraction commit (`26afe09`, a
pure move) each moved definition's exact source segment (decorators included) was
extracted from the parent commit's `PdsFile` body and from the new mixin's body
and compared byte by byte: **all eleven identical**. Each of the two contiguous
runs — first moved definition to last — also compares identical as a single blob
on each side — 5,867 bytes for the checksum-and-archive block and 4,909 for the
log-path block, measured from the first character of the first definition (its
decorator, where it has one) to the last character of the last definition's last
line, exclusive of the trailing newline — which additionally rules out a
reordering or a dropped blank line. Nothing moved is still defined in
`pdsfile.py`, and the new module carries no definition that was not on the move
list. No moved body was restyled to dodge an inherited lint violation; that is
PR-23's job.

At HEAD, **eight** of the eleven are still byte-identical: the seven checksum and
archive definitions and `set_log_root`. The three that are not are
`log_path_for_bundle`, `log_path_for_bundleset` and `log_path_for_index` — §6's
deduplication, which the parent plan requires and which is a **separate commit**
(`316d9c7`, refined by `10fa308`) precisely so that the byte-for-byte claim above
is exactly checkable at `26afe09`, and so that no commit mixes a move with a
content edit (§2 commit granularity). The mixin also carries one definition that
is not on the move list, `_log_path_for` itself; it is the deduplication's helper,
it is underscore-prefixed, and §6 is its account.

`pdsfile.py`: 5,436 → 5,125 lines; `_derived_paths.py` 314. Both counted at HEAD.

### 6. The deduplication, and the divergences it had to reproduce

The parent plan: "Deduplicate the three near-identical `log_path_for_*` bodies
into one private `_log_path_for(...)` helper the three methods delegate to
(behavior-identical…)." They are *near*-identical, so **the divergences are the
whole risk**. A three-way diff of the three bodies finds exactly five, and each
is reproduced by a parameter rather than collapsed:

| # | Divergence | How the helper reproduces it |
|---|---|---|
| 1 | the default `dir` is `''`, `''` and `'index'` | the public signatures are frozen and untouched; each default is applied before the delegation |
| 2 | `log_path_for_index` has **no `suffix` parameter** and no suffix step | it passes `suffix=''`, and `if suffix:` is then false — the same instructions execute |
| 3 | `log_path_for_index` first raises `ValueError('Not an index file: …')` when `not self.is_index` | the check **stays in the public method, ahead of the delegation**, so it still precedes the `place` validation |
| 4 | the parts naming the target: `[category_, bundleset_, bundlename]` / `[category_, bundleset, suffix]` / `[logical_path.rpartition('.')[0]]` | a **callable**, the helper's first argument, invoked at the point the parts are appended |
| 5 | everything else — the `place` branch, the log-root branch, the `dir` branch, the time tag, the task tag, `'.log'`, the `''.join` | identical in all three today, and is the helper's body, character for character |

Divergence 3 is the subtle one, because it is an **ordering** fact rather than a
value: on a non-index file called with an unrecognized `place`, today's code
reports the index error, not the place error. Keeping the check in the public
method preserves that, and the probe below pins it.

**The helper is a method on the mixin, not a module-level function.** It needs
`self` for six attribute reads and `type(self)` for `LOG_ROOT_` and
`LOGFILE_TIME_FMT`; as a module-level function every one of those becomes an
explicit argument, which is more code and reads worse, and the class-attribute
lookups would no longer be written the way the rest of the class writes them. It
is underscore-prefixed, so it is freeze-invisible, and it introduces no state.
Its `subdir` parameter is the public `dir` under a name that does not shadow the
builtin, so the helper contributes no `A002` of its own.

**Evaluation order, preserved exactly — and this is why divergence 4 is a
callable.** Passing the target parts as an already-built list would read
`category_`, `bundleset_`, `bundlename`, `bundleset`, `suffix` and `logical_path`
in the *caller*, i.e. **before** the `place` option is validated rather than
after. That is unobservable on any object the package's constructors can build —
`PdsFile.__init__` assigns all six and `copy()` carries the whole `__dict__` — and
a walk over the **34 classes** in the `PdsFile` hierarchy finds **no class-level
definition of any of the six in any MRO**, so no read has a side effect. But "no
side effect" is not "cannot raise": on a `PdsFile.__new__` instance, which has
none of them, the reordered code answers `AttributeError` where today's answers
`ValueError('unrecognized place option: …')`, and §2 says a PR that changes
observable behavior is wrong without a reachability qualifier. So the parameter is
a **zero-argument callable the helper invokes where the original built the list**,
which puts every read back in its place at the cost of three `lambda:` prefixes
and no duplicated code. This was raised by round 1 as Minor 1, with a prose
correction as its suggested fix; the code fix is strictly stronger and is what
shipped (`10fa308`).

The same walk finds exactly one descriptor among the names these methods touch —
`is_index`, a property that can call `self._recache()` — and that is divergence 3,
deliberately left in the public method.

**Behavior identity, measured rather than asserted — and measured across trees,
not across commits.** A **666-case** probe is run twice, once against a
`PYTHONPATH` pointing at the parent worktree and once against this tree, so what
is compared is the parent branch's behavior and this branch's, not two states of
one file. It calls the three log-path methods, `archive_logpath` and the six
checksum and archive builders over: three `place` spellings including an invalid
one; four `dir` shapes (empty, plain, trailing-slash, and `'index'`); three
`suffix` shapes (empty, plain, and one with a leading underscore, which exercises
the `lstrip('_')`); two `task` shapes; three log roots (`None`, `'/florida'`,
`'/florida/'`); the default-argument and keyword spellings; both `Pds3File` alias
methods; `archive_logpath` with and without a task; and the error paths —
`log_path_for_index` on a **non-index** file with an invalid `place`, which pins
divergence 3, and **48 cases against a `PdsFile.__new__` instance that has none of
the six target attributes**, which pin the evaluation-order question above. Each
answer is recorded with the embedded time tag normalized.

**The two dumps are byte-identical:** 666 lines each, `diff` empty, 40 of them
`AttributeError` lines and 240 `ValueError` lines carrying the same messages on
both sides.

**`archive_logpath` is a free correctness check** on the result, because it calls
`log_path_for_bundle` on a copy of itself; it is in the probe and in the golden
tests, and it is unchanged.

### 7. Ruff ratchet — one code moves, none is gained

Procedure: for every code in `pdsfile.py`'s entry, the following was run against
the parent's `pdsfile.py`, this branch's `pdsfile.py` and `_derived_paths.py`
after the move —

```
ruff check --no-cache --isolated --output-format concise --select <code> \
           --line-length 100 --target-version py310 <file>
```

`--isolated` drops `pyproject.toml`'s `line-length = 100` and would otherwise
report an E501 at 88 columns that the project config does not, so the two
settings are restored explicitly (PR-16 §7 and PR-17 §7 record the same trap), and
`--output-format concise` is required because ruff 0.15's default output no
longer starts a line with the file path.

**Every one of the 19 codes conserves exactly** — parent count = the two
post-move counts summed — which is the mechanical statement of "this is a split
of an existing entry, not a new suppression":

| Code | parent `pdsfile.py` | → `pdsfile.py` | `_derived_paths.py` |
|---|---|---|---|
| A002 | 3 | **0** | 3 |
| B904 | 3 | 3 | 0 |
| C405 | 3 | 3 | 0 |
| E501 | 5 | 5 | 0 |
| E701 | 11 | 11 | 0 |
| E713 | 1 | 1 | 0 |
| E721 | 1 | 1 | 0 |
| F841 | 5 | 5 | 0 |
| I001 | 2 | 2 | 0 |
| N806 | 2 | 2 | 0 |
| RUF005 | 8 | 8 | 0 |
| RUF012 | 16 | 16 | 0 |
| SIM102 | 1 | 1 | 0 |
| SIM114 | 2 | 2 | 0 |
| SIM118 | 1 | 1 | 0 |
| UP004 | 1 | 1 | 0 |
| UP015 | 1 | 1 | 0 |
| UP024 | 13 | 13 | 0 |
| UP031 | 9 | 9 | 0 |

The **converse** check matters as much and is easy to skip: running the project's
whole select set (`E,F,W,I,UP,B,SIM,C4,A,N,PT,RUF` minus the three project-wide
ignores) against `_derived_paths.py` with **no** per-file entry reports exactly
three violations, all `A002`. So the new module needs no code that was not
already forgiven for these same lines; had it needed one, the sub-plan makes that
a §6.4 hard stop.

Resulting entries:

| File | Entry | Note |
|---|---|---|
| `src/pdsfile/pdsfile.py` | 19 codes → **18** | A002 no longer occurs in it, so it is **removed** |
| `src/pdsfile/_derived_paths.py` | `["A002"]` | exactly the code its moved lines trigger |

`A002` is the frozen `dir=` parameter of the three `log_path_for_*` methods,
which the tools call by keyword; the plan's PR-23 section lists it as a permanent
freeze-locked ignore. It is therefore not fixable and simply changes file: **the
PR-23 note that `A002` lives in `pdsfile.py` now reads `_derived_paths.py`.** The
distinct (file, code) pairs move 19 → 18 + 1, and the number of suppressed
violations is unchanged.

**The deduplication commit does not move the ratchet.** It was measured
separately: the three public parameters are still named `dir`, so `A002` is still
3, and the helper's `subdir` adds nothing. The plan allows the dedup to *shrink*
the ratchet; here it neither shrank nor grew it.

The new module's import block is a single `import datetime`, so it needs no
`I001`, which is why that row conserves rather than growing by one.

### 8. The tests that actually pin this code — measured, and not what the plan says

The parent plan describes the deduplication as "golden-tested via the tool tests
from PR-13". **That is half right, and the half that is wrong matters**, so it was
measured three ways rather than taken on trust.

**(a) Which tests execute the moved code.** A coverage run of
`tests/holdings_maintenance/`, `tests/pds3file/`, `tests/pds4file/` and
`tests/core/` with `dynamic_context = test_function` attributes every line of
`_derived_paths.py` to a test:

| Method | Tests whose context covers it |
|---|---|
| `checksum_path_and_lskip` | `test_checksum_path_and_lskip`, `test_checksum_path_if_exact`, `test_exact_checksum_url` |
| `checksum_path_if_exact` | `test_checksum_path_if_exact`, `test_exact_checksum_url` |
| `dirpath_and_prefix_for_checksum` | `test_dirpath_and_prefix_for_checksum` |
| `archive_path_and_lskip` | `test_archive_path_and_lskip`, `test_archive_path_if_exact`, `test_exact_archive_url1` |
| `archive_path_if_exact` | `test_archive_path_if_exact`, `test_exact_archive_url`, `test_exact_archive_url1` |
| `dirpath_and_prefix_for_archive` | `test_dirpath_and_prefix_for_archive` |
| `archive_logpath` | `test_archive_logpath` |
| `set_log_root` | `test_log_path_for_volume`, `test_log_path_for_volset`, `test_log_path_for_index` |
| `_log_path_for` | those three plus `test_archive_logpath` |
| `log_path_for_bundle` | `test_log_path_for_volume`, `test_archive_logpath` |
| `log_path_for_bundleset` | `test_log_path_for_volset` |
| `log_path_for_index` | `test_log_path_for_index` |

All of them are in `tests/pds3file/test_pds3file_blackbox.py` (one is in
`test_pds3file_whitebox.py`). **Not one `tests/holdings_maintenance/` context
appears.** That is not because the tools do not call these methods —
`pdsinfoshelf.py:859` and the equivalent call in eleven other tool modules
invoke `log_path_for_volume` / `log_path_for_volset` / `log_path_for_index`
unconditionally inside `main()`'s loop —
but because PR-13's harness runs each tool as a **subprocess**
(`tests/holdings_maintenance/support.py:297`, `subprocess.run([sys.executable,
'-m', …])`), which in-process coverage does not follow. The measurement is
therefore *structurally blind* here, in the same way §6.2's set diff is blind to a
misdirected patch, and it was not left at that.

**(b) The tool tests do execute it — proved by the artifact.** Running one tool
test module with `--basetemp` and inspecting the trees afterwards finds log files
whose names are exactly `log_path_for_volume`'s output shape, e.g.
`<tree>/logs/pdsinfoshelf/volumes/HSTNx_xxxx/HSTN0_7176_info_<timetag>_initialize.log`
— nine files from eight tests: seven whose basenames are `log_path_for_volume`'s
return value, and two `ERRORS.log` written into the directories those names
imply. Only the moved code can have produced those paths.

**(c) But the tool tests do not *pin* the value.** No test in
`tests/holdings_maintenance/` asserts anything about a log **filename**; they
assert on the tool's exit code, its stdout and its shelf output. Measured: with
`_log_path_for` deliberately emitting `.LOGWRONG` instead of `.log` **and**
`'WRONG'` instead of the parts naming the target, the pds3 infoshelf, indexshelf
and checksums and the pds4 infoshelf modules still report **31 passed**, exactly
as unmutated.

**So the regression net for this PR is `tests/pds3file/test_pds3file_blackbox.py`,
not the tool tests** — 41 log-path ids (16 `log_path_for_volume`, 16
`log_path_for_volset`, 8 `log_path_for_index`, 1 `archive_logpath`) plus 20
checksum/archive ids, and it is a real net rather than a hoped-for one, which §9
shows. The tool tests are a **liveness** net: they run the code in a subprocess and
would notice a path that could not be created. That is information for the plan,
not a licence to add scope — no test was added here, and the gate remains an
identical pass/fail set. It is recorded as a deferred observation for the phase
that owns the tool tests.

### 9. Negative controls — the golden net is live, not decorative

Every check below is a mutation of the **moved or deduplicated** code, run
against `tests/pds3file/` with the 61-id selection above (61 passed, unmutated).
Each must turn tests red; a mutation that changed nothing would mean the tests
reach some other copy of the code, or nothing at all. **All figures below were
re-measured at HEAD** after the last change under `src/pdsfile/`, so no row
describes an earlier state of the file.

**The harness has a trap in it, and the first attempt fell into it.**
`pyproject.toml` sets `pythonpath = [".", "src"]`, which pytest resolves against
**rootdir** and inserts at the front of `sys.path` — **ahead of `PYTHONPATH`**.
Measured under pytest from the repo root: `sys.path` is `tests/api`, `tests`,
`<rootdir>`, `<rootdir>/src`, `<rootdir>`, then the `PYTHONPATH` entry. So
mutating a copy of `src/` and pointing `PYTHONPATH` at it from the repo root
imports the *unmutated* tree, and all seven controls report green, which reads
exactly like "the tests do not reach this code" and is in fact "the harness does
not reach the mutation". Each mutation is therefore written into a **full copy of
the working tree** and pytest is run from inside it, and a `conftest.py` in that
copy prints `_derived_paths.__file__` so the run asserts it imported the mutated
module. The same trap is why §3's runs `cd` into the tree they measure — see
§1, whose `measured_files()` table is the independent statement that they did.

| Mutation | Result |
|---|---|
| `_log_path_for` emits `.LOGWRONG` instead of `.log` | **41 failed** — every log-path id |
| `_log_path_for` ignores the target parts | **41 failed** |
| `_log_path_for` drops the `subdir` segment | **21 failed** — exactly the cases that pass a `dir` |
| `_log_path_for` ignores `cls.LOG_ROOT_` (always takes the parallel root) | **5 failed** — exactly the cases with an explicit log root *and* `place='default'`; the other 11 log-root cases are `place='parallel'`, which never reads it |
| `checksum_path_and_lskip` returns `lskip + 1` | **3 failed** |
| `archive_path_and_lskip` writes `archivesWRONG-` into the abspath | **4 failed** |
| `dirpath_and_prefix_for_archive` drops `bundleset_` from the parent | **1 failed** |

The `LOG_ROOT_` control is the discriminating one for the class-attribute
question: it is the measurement that the log root is still read **off the class**
after `set_log_root` writes it there, from a method that now lives in another
module.

The inherited mixin checks were mutation-tested too, because
`tests/api/test_mixin_collisions.py` discovers its subjects and a new mixin could
in principle be discovered and then checked vacuously. Unmutated the module is 13
passed; each mutation names the tests it turned red, so the row is reproducible
rather than a count:

| Mutation | Went red |
|---|---|
| `_DerivedPathsMixin` and `_LocalFsMixin` swapped in the class statement | `test_the_mixin_bases_are_listed_alphabetically` |
| `_DerivedPathsMixin` carries class-level state (`LOG_ROOT_ = None`) | `test_a_mixin_defines_only_callables_and_properties`, `test_no_mixin_is_shadowed_by_pdsfile_itself`, `test_the_mixin_bases_are_listed_alphabetically` |
| `_DerivedPathsMixin` also defines `shelf_path_and_key_for_abspath`, which `_ShelfMixin` defines | `test_no_two_mixins_define_the_same_name`, `test_every_mixin_name_is_reachable_through_pdsfile` |
| `PdsFile` itself redefines `archive_logpath` | `test_no_mixin_is_shadowed_by_pdsfile_itself`, `test_every_mixin_name_is_reachable_through_pdsfile` |

### 10. The base order

```python
class PdsFile(_DerivedPathsMixin, _LocalFsMixin, _ShelfMixin, object):
```

`_DerivedPathsMixin` sorts before `_LocalFsMixin`, so it takes the first slot. The
rule — **alphabetical by mixin class name, with `object` last** — was set by PR-17
and is owner-acknowledged in
`plans/2026-07-27-addendum-phase5-mixin-base-order.md`; it is asserted by
`tests/api/test_mixin_collisions.py::test_the_mixin_bases_are_listed_alphabetically`.

**The plan text on this branch does not say this.** Its Phase-5 preamble
illustrates `class PdsFile(_ShelfMixin, _OpusMixin, …)`, the opposite order; the
correction merged to `rewrite` in PR #110 **after** this stack branched, and
merging `rewrite` forward to obtain it would drag #110's diff into this PR. The
addendum is the authority here, and
`plans/2026-07-27-addendum-phase5-stack-extension.md` §"What is new" says so for
PR-19 through PR-22 as well.

`tests/api/test_mixin_collisions.py` **discovers** the mixins from
`PdsFile.__bases__`, so this PR's mixin inherited all of its checks — collision,
shadowing, reachability, no-`__init__`, callables-and-properties-only, base order
— without a new test id, which is why the no-holdings count is unchanged at
80/800. §9's mutation table is the evidence that the inheritance is real.

### 11. Consumer smoke — outcome unchanged

The gate is **same outcome as baseline**, not "passes"
(`critiques/baselines/consumer-smoke-baseline.md`).

| Check | Baseline | This branch |
|---|---|---|
| A — rms-opus import paths | 4/4 resolve, 0 failures | **4/4 resolve, 0 failures** |
| B — rms-viewmaster startup | 5 ok, 3 pre-existing failures | **5 ok, 3 failures — the same three** |

The three Check-B failures are still `pdsfile.cache_lifetime` (raises),
`pdsfile.DEFAULT_CACHING` (absent) and the same `cache_lifetime` read inside
`get_page_cache()`. None became a pass. `pdsfile.pdsfile.repair_case` still
resolves.

Unlike PR-17, **neither consumer calls any name this PR moves** — a grep of
rms-opus and rms-viewmaster for the eleven method names, `LOG_ROOT_` and
`LOGFILE_TIME_FMT` returns nothing but rms-viewmaster's own unrelated
`LOG_ROOT_PREFIX_` config constant. The log-path builders are used only by this
package's maintenance tools, which is the premise of issue #47 and is confirmed
here rather than assumed.

Environment note carried from the baseline: the check ran under the pdsfile
venv's interpreter with rms-viewmaster's `site-packages` appended to
`PYTHONPATH`, because that venv lacks pdsfile's declared `range_ex` dependency.
rms-viewmaster is at `a0d05e2` with the same three untracked entries the baseline
records; rms-opus is at `73cb6de7`.

### 12. Clean install

`scripts/clean_install_check.sh` passes inside `run-all-checks.sh`. The new module
is picked up by the existing `include = ["pdsfile*"]` package glob with no
packaging change, and the gate imports the whole manifest module surface —
`pdsfile.pdsfile` among them — which cannot succeed if `_derived_paths.py` is
missing from the distribution.

### 13. The monkeypatch audit — the check the set diff cannot perform

Deferred entry 29 (opened by PR-16's round-1 Major, owned by "PR-17 onward") says
an extraction sweep must also ask **which namespaces the tests patch**, not only
which globals the code reads. A test whose patch lands on a module the moved code
no longer resolves through keeps passing while exercising nothing, and §6.2's
outcome-set diff compares pass/fail — so it is *structurally blind* to this class
of defect.

**Enumeration.** Every `monkeypatch.setattr` / `setitem` / `delattr` / `setenv` /
`delenv`, `mock.patch`, `patch(`, `patch.object` and bare `setattr(` in `tests/`
and `scripts/` — 20 sites, all `monkeypatch`; the tree still uses no
`unittest.mock` at all:

| Target | Sites | Names a symbol **this PR** moves? |
|---|---|---|
| `Pds3File.CACHE` (`tests/core/conftest.py:28`, `test_pdsfile_caching.py:112,126`) | 3 | no — a class attribute that stays on the class |
| `Pds3File.preload` (`test_pdsfile_caching.py:127`) | 1 | no — PR-21's symbol; patched on the class, so an MRO lookup either way |
| `Pds3File`/`Pds4File.LOCAL_PRELOADED`, `.LOCAL_HOLDINGS_DIRS` (`test_pdsfile_path_resolution.py:58,59,71,72,85,86`) | 6 | no — class attributes that stay on the classes |
| `Pds3File.shelf_path_and_key_for_abspath` (`test_pdsfile_path_resolution.py:120,129,137,155`) | 4 | no — PR-17's symbol, audited there |
| `abspath_for_logical_path.__globals__['glob']` (`test_pdsfile_path_resolution.py:92`) | 1 | no — PR-16's fix site, on `_path_utils`'s globals |
| `pdsviewable.ICON_SET_BY_TYPE` (`test_pdsviewable_iconset_for.py:47`) | 1 | no — different module |
| `monkeypatch.setenv` / `delenv` (`test_pdsfile_path_resolution.py:54,70,83,84`) | 4 | no — environment, not a namespace |

**No patch site names any of the eleven methods, `LOG_ROOT_` or
`LOGFILE_TIME_FMT`.** A regex over `tests/`, `scripts/` and `src/` for *direct
assignment* to any of those thirteen names — the form that is not a `monkeypatch`
and is easy to miss, which is how PR-17 nearly under-reported its own audit —
returns exactly two hits, both inside `set_log_root` itself
(`cls.LOG_ROOT_ = …`), which is the method's entire job.

**The one thing that does mutate this PR's state, and its negative control.**
`tests/pds3file/test_pds3file_blackbox.py` brackets each log-path case with
`pds3file.Pds3File.set_log_root(logroot)` … `set_log_root()`. That is not a
`monkeypatch`, but it is functionally a patch of `Pds3File.LOG_ROOT_`, and it is
the only test-side mutation this PR's code observes. §9's fourth control is its
proof: with `_log_path_for` ignoring `cls.LOG_ROOT_`, exactly the five ids that
set a log root **and** ask for `place='default'` go red. So the write still lands
where the moved reader looks, and the test would notice if it did not.

**The clock.** The `log_path_for_*` methods embed
`datetime.datetime.now().strftime(cls.LOGFILE_TIME_FMT)`. **Nothing in `tests/`
pins the clock** — no `freezegun`, no `monkeypatch` of `datetime`, no patch of
`time`. The golden tests match the time tag with the regex
`20..-..-..T..-..-..`, so they assert the *format* and the *position* and not the
value; §9's first control shows they are sensitive to everything around it. This
means the moved code has no hidden dependence on a test-controlled clock that
could stop reaching it after the move — the failure mode the brief warns about
does not exist here because the pin does not exist. It also means the tests will
need attention in the year 2100, which is noted as a deferred observation rather
than fixed here.

**Entry 29's second half — rebinding re-exported *data*.** The same asymmetry one
level down, measured on both sides:

| | parent `ca7a43d` | this branch |
|---|---|---|
| namespace the eleven methods resolve through | `pdsfile.pdsfile` | `pdsfile._derived_paths` |
| namespace `datetime` resolves in, for a log path | `pdsfile.pdsfile` | `pdsfile._derived_paths` |
| rebinding `pdsfile.pdsfile.datetime` reaches the log-path builders | **yes** | **no** |
| `PdsFile.LOG_ROOT_` / `.LOGFILE_TIME_FMT` still on the class | yes | yes |
| `pdsfile.pdsfile.datetime` still bound | yes | yes |

Nothing in `src/`, `tests/`, `scripts/`, rms-opus or rms-viewmaster rebinds
`pdsfile.pdsfile.datetime` or any other module attribute — greped, zero hits — so
nothing is broken today. The general observation stands for PR-19 onward and stays
in `critiques/deferred-observations.md` as entry 29.

**The set diff cannot see any of this.** That is the point of the section: every
one of these tests passed before the move and passes after it, and a
pass/fail-set comparison would have reported "identical" in every case, including
the broken one PR-16 found.

### 14. Which half of issue #47 this is

The plan is explicit and so is this record:

- **This PR does the file-location half.** `set_log_root` and the three
  `log_path_for_*` methods — used only by the maintenance tools, which §11
  confirms by measurement against both consumers — move physically out of
  `pdsfile.py`.
- **Because of the API freeze they stay reachable as `PdsFile.set_log_root` and
  `PdsFile.log_path_for_*`**, and the tools keep calling them exactly as today.
  The move is invisible to callers, which the byte-identical API dump in §4 is the
  formal statement of.
- **Removing them from the public class surface — what #47 ultimately wants — is
  an API break deferred to phase "b".** It is not done here and not half-done
  here. **Issue #47 stays open.**

### 15. Deferred observations

Entry 29 is the one this PR was told to act on, and §13 is the action. It is
**not** resolved — it is a per-PR step, owned by "PR-17 onward" — so it stays open
for PR-19 through PR-22. Entry 42 (the back-import guard, owner PR-22) is
untouched: this PR adds a mixin module and §5 shows it is clean by the same
parsing check, but it builds no guard. No entry in 1–42 is resolved or
invalidated here.

Five entries are **added**: 43 (the tool tests run the log-path builders but
assert nothing about their output, and in-process coverage cannot see them at all
— owner Phase 6), 44 (the golden tests' `20..` year prefix — owner PR-24), 45
(`A002`'s freeze-locked home moves to `_derived_paths.py`, which PR-23's
enumerated list must follow), 46, from the round-1 review (the deduplicated code
has no holdings-free coverage — owner Phase 6, alongside 43), and 47, from the
round-3 review (`log_path_for_index`'s docstring first line describes a bundle;
it moved verbatim, so editing it here would break the byte-for-byte claim —
owner Phase 7). A sixth, 48, comes from the round-4 review:
`tests/api/test_mixin_collisions.py`'s shadowing check looks at `PdsFile` only
and not at `Pds3File` / `Pds4File`, which is where the method surface is actually
extended — measured empty today, owner PR-19. Round 4 also found a second wrong
docstring in `_derived_paths.py` (`dirpath_and_prefix_for_archive` says it
returns a path and returns a tuple); it is **folded into entry 47** rather than
given a number of its own, so the Phase-7 pass sees one entry naming both.

### 16. Review loop

| Round | Verdict | Findings | Record |
|---|---|---|---|
| 1 | goal met | 0 Major, 4 Minor (all accepted; two fixed in code, two in the records), 2 Deferred (entry 46 added) | `critiques/pr-18/round-1.md` |
| 2 | goal met | 0 Major, 5 Minor (all accepted and fixed; all five are record or comment accuracy), 3 Deferred (all already recorded) | `critiques/pr-18/round-2.md` |
| 3 | goal met | **1 Major** (a fabricated row in this table — fixed), 3 Minor (all accepted and fixed), 4 Deferred | `critiques/pr-18/round-3.md` |
| 4 | goal met | 0 Major, 1 Minor (accepted and fixed), 3 Deferred (entry 48 added; one folded into 47) | `critiques/pr-18/round-4.md` |

**The loop terminates at round 4**, one round inside §6.6's four-round cap: a
fresh reviewer returned zero Major and no new un-rebutted Minor. Its Minor was
that `critiques/pr-18/round-3.md` still described this table as carrying a
forward-reference row for round 4 after that row had been removed — the same
record-accuracy defect as round 3's Major, one notch weaker, in the file that
documents it. Fixed in the round-3 record, additively.

**Round 3's Major was in this table.** While fixing round 2's Minor 4 — "the
review-loop table is empty" — the table was filled in for **three** rounds when
two had been held: it asserted `goal met`, "0 Major, 0 new Minor" and a
`critiques/pr-18/round-3.md` that did not exist, and the paragraph beneath it
still said "both rounds". That is a manufactured process-compliance claim in the
one document the §6.2 gate rests on, and it was wrong on the facts as well as in
principle — round 3 returned a Major. It is deleted, this paragraph replaces the
one that carried it, and every row above is written only after the round it
describes has run and its record file exists. Round 3's fix left a fourth row as
an explicit forward reference to `critiques/pr-18/round-4.md` with no verdict
claimed; that row has since been removed too, because the rule is that a row
appears when its record does, and a pointer to a file that does not exist is the
same defect in a weaker form.

Each reviewer re-derived the move fidelity, the API dump, the set diff, the
ratchet conservation and the runtime class shape with its own scripts rather than
reading them here, and each brought its own differential probe: round 1
**48,649** cases, round 2 **909,837** comparisons over 167 instances, round 3
**939,047** outcomes per tree over 30 instances including 14 progressively
populated `PdsFile.__new__` objects. All three found the same single behavioral
difference — the `__qualname__` consequence of the mandated mixin technique,
recorded in §4 — and all three agreed it is inherent to the technique rather than
a choice this PR made.

§6.6 step 5's regeneration rule was applied mechanically at every boundary: round
1's fixes, round 2's two-word comment correction and round 3's keyword-argument
fix each touched `src/pdsfile/`, so the full-data record was regenerated three
times. §3's figures are the last of them. **Round 4's fix touches `critiques/`
only, so the record carries forward unchanged** — which is the other half of the
same rule, and is why the last change under `src/pdsfile/` is still `5115c38`.

## PR-19 — `refactor: extract OPUS and index-row support → _opus.py, _index_rows.py`

**Branch:** `pr-19-opus-index-rows`, based on `pr-18-derived-paths` @ `80cd9ff`
("docs: record round 4 and close the review loop"), opened against that branch,
not `rewrite` (`plans/2026-07-27-addendum-phase5-stack-extension.md`).
**Baseline:** **PR-18's recorded post-move set** — its §3 above, `--mode ns` 846
passed / 34 skipped (880 ids) and `--mode s` 555 passed / 3 skipped (558 ids) —
**re-measured locally on the parent tip** with this PR's own command lines rather
than copied from the table. The re-measurement reproduced it exactly.
**Date:** 2026-07-27
**Sub-plan:** [`plans/2026-07-27-pr-19-subplan.md`](../plans/2026-07-27-pr-19-subplan.md)

This is the first Phase-5 extraction since PR-17 whose set diff is **not** empty,
and the movement is **two test ids and nothing else**: the widened mixin
shadowing check that deferred entry 48 assigns to this PR. Both are enumerated in
§3 and shown to be the whole difference.

### 1. Environment

| Item | Value |
|---|---|
| Interpreter | CPython 3.12.3, repo venv, `pip install -e ".[dev]"` |
| Holdings | `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` + `PDSFILE_TEST_HOLDINGS=full`, pointed at the limited testing copy the goldens are tuned to |
| Baseline tree | a `git worktree` detached at the parent tip `80cd9ff`, same interpreter, same holdings; `pytest` reports that directory as `rootdir` |
| Command lines | exactly those in `scripts/automated_tests/pdsfile_main_test.sh` (serial, under `coverage`), plus `-rA --junitxml` |

**Which source each run actually imported, proved rather than assumed.** The
interpreter is the main tree's venv, whose editable install appends
`<main tree>/src` to `sys.path`, and there are now five stacked branches sharing
it, so a worktree run could silently measure the wrong tree and make the whole
comparison vacuous. Each run wrote its own `COVERAGE_FILE`, and
`coverage.CoverageData.measured_files()` was read afterwards for its **absolute**
paths:

| Run | top-level `pdsfile` modules measured | count |
|---|---|---|
| baseline | `<worktree>/src/pdsfile/` — `__init__`, `_derived_paths`, `_local_fs`, `_path_utils`, `_shelves`, `pdscache`, `pdsfile`, `pdsviewable`, `preload_and_cache` | **9** |
| this branch | `<main tree>/src/pdsfile/` — the same nine, plus **`_index_rows`** and **`_opus`** | **11** |

Those are the modules directly under `src/pdsfile/`; both runs additionally
measure the same `holdings_maintenance/`, `pds3file/`, `pds4file/` and `tools/`
subpackages, each under its own tree's prefix. Round 3 raised the earlier
five-name set notation as Minor 4; the enumeration above is the full one.

The presence of exactly two extra modules on this branch and **zero** of them on
the baseline side is the decisive bit: had the worktree run leaked into the main
tree's install, they would have been measured there too. Every path in the
baseline list begins with the worktree prefix and every path in the head list
with the main tree's; no path appears under the other tree's prefix in either
run. The one baseline-side path that matches the text `_opus` is
`src/pdsfile/tools/show_opus_products.py`, a pre-existing tool module that both
runs measure.

### 2. Active §2 gates

| Gate | Result |
|---|---|
| API-freeze manifest test | **passed** — and the dumped surface is byte-identical to the parent's, 733,876 bytes each; §4 |
| Full-data suite, both modes | **passed** — `--mode ns` moves by exactly the two ids §5 adds, `--mode s` diff is empty; §3 |
| `ruff check src/pdsfile tests scripts` | **passed**; the ratchet gained no code — §8 |
| Clean-install import check | **passed** (throwaway venv, `pip install .`, full module surface imports) |
| Hosted lint/no-holdings job (`scripts/run-all-checks.sh`, no holdings env vars) | **passed**, **82 passed / 800 skipped** — the parent's 80 plus this PR's two ids |
| Adversarial review loop | `critiques/pr-19/round-<k>.md` |

### 3. Full-data suite — two added ids in `--mode ns`, an empty diff in `--mode s`

Both passes were run on the parent tip and on this branch's head with the same
interpreter and the same holdings. Every `testcase` element of each `--junitxml`
was reduced to one `outcome<TAB>classname::name` line, sorted, and the two files
were diffed with `diff -u`.

| Run | parent `80cd9ff` | `pr-19-opus-index-rows` | set diff |
|---|---|---|---|
| `--mode ns` | 846 passed / 34 skipped (880 ids) | 848 passed / 34 skipped (882 ids) | **+2, both new** |
| `--mode s` | 555 passed / 3 skipped (558 ids) | 555 passed / 3 skipped (558 ids) | **empty** |

The whole `--mode ns` diff, verbatim — two added lines, no removals and no
outcome changes:

```
+passed	tests.api.test_mixin_collisions::test_no_mixin_is_shadowed_by_a_pdsfile_subclass[Pds3File]
+passed	tests.api.test_mixin_collisions::test_no_mixin_is_shadowed_by_a_pdsfile_subclass[Pds4File]
```

`diff -u` produced **zero output lines** for `--mode s`. The parent numbers
reproduce PR-18's recorded set, which is what makes this a comparison against
PR-18's baseline rather than against a fresh unrelated measurement.

Both modes matter and both were run: `--mode s` is the only thing that exercises
the `SHELVES_ONLY` branch, and `get_indexshelf` goes through `_get_shelf` while
`from_opus_id` and `opus_products` go through `glob_glob` and `os_path_exists`,
all of which branch on it.

**Freshness (§6.6 step 5).** The last change under `src/pdsfile/` is commit
`b6bda4a` (round 3's Minor-1 and Minor-5 fixes in `_index_rows.py`, `_opus.py`
and `tests/api/test_mixin_collisions.py`), at **18:33:45**. The head runs
recorded above postdate it: their `--junitxml` timestamps are **18:36:54 and
18:38:43**. They are the third regeneration §6.6 step 5 requires — rounds 1, 2
and 3 each produced a fix under `src/pdsfile/`.

The three **superseded** head pairs are recorded rather than dropped, each with
the commit its tree was actually at:

| Head pair | `--junitxml` written | Tree at | Reduced sets |
|---|---|---|---|
| 1 | 17:04:18 / 17:06:10 | `b554c77` | identical to pairs 2, 3 and 4 |
| 2 | 17:42:28 / 17:44:16 | `cf35a0f` | identical to pairs 1, 3 and 4 |
| 3 | 18:07:33 / 18:09:29 | `3ab1738` | identical to pairs 1, 2 and 4 |
| **4 (current)** | **18:36:54 / 18:38:43** | **`b6bda4a`** | **the figures above** |

`b554c77` is the last commit before pair 1 started; the two commits between it
and pair 2 (`8916229`, `bc5147e`) are records that touch nothing under
`src/pdsfile/`, so pair 1 measured the same `src/` tree they carry. An earlier
draft labelled pair 1 "taken at `bc5147e`", 16 minutes after its XMLs were
written; round 2 raised that as Minor 5. All four pairs produced **identical
reduced sets** — `diff` between any two of them is empty in both modes — which is
what docstring- and comment-only changes should do, and is measured rather than
assumed. Every fix in all three rounds was a docstring, a comment or a record;
none touched an executable line, and the four identical pairs are the evidence
for that rather than the claim of it.

The **baseline** runs (16:52:39 and 16:54:29) stand throughout: they were taken
in a detached `git worktree` at `80cd9ff` that nothing has touched since.

### 4. API freeze — empty diff, as a mixin move requires

1. `pytest tests/api/` passes — 16 ids, the freeze test plus the 15 that
   `tests/api/test_mixin_collisions.py` now contributes (13 on the parent, plus
   this PR's two). `tests/api/api_manifest.json`,
   `tests/api/manifest_allowlist.json`, `scripts/dump_public_api.py` and
   `tests/api/test_api_freeze.py` are untouched by this PR (§6.4) — verified with
   `git diff --stat 80cd9ff..HEAD` over those four paths, which is empty. No
   allowlist entry was added.
2. `scripts/dump_public_api.py` was run against a worktree at the parent tip and
   against this branch's head. The two dumps are **byte-identical** (733,876
   bytes each, `diff` empty, both stderr streams empty).

That is the expected result and the plan says so: the dumper expands a class's
members with `dir(cls)`, which is MRO-wide, and records names, kinds and
signatures — never the defining class. So moving `PdsFile.opus_products` into
`_OpusMixin` cannot show up here, and any diff would have meant a mistake.

`pdsfile._index_rows` and `pdsfile._opus` are underscore-prefixed, so the dumper
skips them where the submodule import binds them onto the `pdsfile` package; the
same applies to `_IndexRowsMixin` and `_OpusMixin` inside `pdsfile.pdsfile`. That
is the freeze-invisibility the Phase-5 preamble requires of new internal names.
This PR introduces **no** new non-underscore name anywhere.

**The three signatures the consumers depend on are frozen and unchanged**, which
the byte-identical dump also asserts: `from_filespec(cls, filespec,
fix_case=False)`, `from_opus_id(cls, opus_id)` and `opus_products(self)`.

The `__qualname__` consequence PR-18 §4 records applies here too and for the same
reason — `PdsFile.opus_products.__qualname__` is now `_OpusMixin.opus_products`.
It is a phase-wide consequence of the mandated mixin technique, already true of
the three mixins on the parent branch, and the dumper records `kind` and
`signature`, never a qualname. Measured again for this PR's eight names: nothing
in `src/`, `tests/`, `scripts/`, rms-opus or rms-viewmaster matches on that text.

### 5. What moved, and the sweep that decided it

Eight definitions, located by name. The plan's ":4642–4896" and ":4358–4640"
windows are against the 6,304-line original; PR-15 through PR-18 have all edited
this file, which is 5,125 lines at the parent tip. On that tip the targets are
exactly two consecutive banner blocks, `pdsfile.py:3779–4318`.

| New module | Mixin class | Definitions |
|---|---|---|
| `src/pdsfile/_index_rows.py` | `_IndexRowsMixin` | `get_indexshelf`, `find_selected_row_key`, `child_of_index`, `data_abspath_associated_with_index_row`, `data_pdsfile_for_index_row` |
| `src/pdsfile/_opus.py` | `_OpusMixin` | `from_filespec` (classmethod), `from_opus_id` (classmethod), `opus_products` |

**`from_filespec` is an alternative constructor and is in `_opus.py` anyway**,
which a reviewer will ask about. Two independent authorities put it there: the
parent plan's PR-19 window contains it, and the file's own `# OPUS support
methods` banner contains it. The banner boundary is the boundary, in both
directions — which is also why the index-related *properties*
(`indexshelf_abspath`, `is_index`, `index_pdslabel`, `filename_keylen`) do **not**
move: they are in the `# Properties` block and belong to PR-22.

**Neither block contains a class-level assignment.** An AST pass over both
windows finds eight `FunctionDef`s and **zero** `Assign` nodes, so the "class
attributes stay on `PdsFile`" rule has nothing to catch here. That is different
from PR-17 (six shelf attributes) and PR-18 (`LOG_ROOT_`), and it is recorded as
a measurement rather than an absence noticed by eye.

**The sweep was computed, not read.** CPython's `symtable` yields the
module-global names each moved definition's body references; a second AST pass
covers each definition's decorator expressions and argument defaults, which are
evaluated in module scope and which `symtable` does not attribute to the method.
Result:

| Category | `_IndexRowsMixin` | `_OpusMixin` |
|---|---|---|
| module-level **imports** referenced | `numbers`, `pdstable` | `defaultdict` |
| module-level **functions** referenced (from `_path_utils`) | `_clean_join` | `_needs_glob`, `abspath_for_logical_path` |
| module-level **constants** referenced | **none** | **none** |
| module-level **classes** referenced (import-cycle risk) | **none** | **`PdsFile`** |
| unclassified names | **none** | **none** |
| seen **only** in a decorator or an argument default | **none** | **none** |

The second pass found nothing this time, which is itself the result worth
recording: PR-16's `_GLOB_CACHE_SIZE` and PR-17's `PATH_EXISTS_CACHE_SIZE` were
both invisible to a body-only sweep, so the pass is run whether or not it is
expected to fire, and its "none" is measured rather than assumed.

Per-definition, so the aggregate can be checked rather than trusted:
`get_indexshelf`, `find_selected_row_key` and `data_pdsfile_for_index_row`
reference **no** module global at all; `child_of_index` references
`_clean_join`, `numbers` and `pdstable`; `data_abspath_associated_with_index_row`
references `pdstable`; `from_filespec` references none; `from_opus_id`
references `_needs_glob` and `abspath_for_logical_path`; `opus_products`
references `defaultdict` and `PdsFile`.

**Three module-level names are stranded in `pdsfile.py`, and all three stay.**
This is the difference from PR-18, which stranded none. After the move `numbers`,
`pdstable` and `defaultdict` have **zero** remaining references in `pdsfile.py`
— counted over the AST, not eyeballed — and all three are **frozen manifest
members** of `pdsfile.pdsfile` (`numbers` and `pdstable` `"kind": "module"`,
`defaultdict` `"kind": "class"`). Deleting them would be a manifest break, an
inline `noqa` and a ratchet grow are both forbidden, so they move into the
PEP-484 redundant-alias re-export form the header already used for six modules:

```python
import numbers as numbers
import pdstable as pdstable
from collections import defaultdict as defaultdict
```

`_clean_join` (10 remaining references), `abspath_for_logical_path` (4) and
`_needs_glob` (1) keep live callers in `pdsfile.py` and so keep their plain
import form. Every one of those counts is measured.

**No import cycle.** Parsing both new modules reports their module-level imports
as `numbers`, `pdstable`, `from ._path_utils import _clean_join` and
`from collections import defaultdict`,
`from ._path_utils import _needs_glob, abspath_for_logical_path` — all at column
0, none of them a `from pdsfile.pdsfile import` of any spelling. §6 is the
account of the one import that is not at module level.

**How the two new modules reach the other mixins.** Only through `cls.` /
`self.` — `get_indexshelf` calls `cls._get_shelf` (`_ShelfMixin`),
`data_abspath_associated_with_index_row` calls `cls.os_path_exists`
(`_LocalFsMixin`), and `from_opus_id` and `opus_products` call `cls.glob_glob`,
`cls.os_path_exists` and `pdsf.shelf_lookup`. Those are runtime MRO lookups, not
imports. None of the five mixin modules imports another. The two blocks are also
independent of **each other**: an attribute-name scan over both windows finds no
call from an index-row method to an OPUS method or the reverse, which is why
they could be moved in two separate commits with the tree green in between.

**Zero names lost, measured.** `sorted(vars(pdsfile.pdsfile))` was compared
between the parent worktree and this branch: **48 names before, 50 after, none
lost.** The two gained are `_IndexRowsMixin` and `_OpusMixin`, which the
`class PdsFile` statement needs; both are underscore names, so the manifest does
not see them.

**Byte-for-byte equivalence, measured.** At each extraction commit each moved
definition's exact source segment (decorators included) was extracted from the
parent commit's `PdsFile` body and from the new mixin's body and compared byte by
byte:

| Definition | Bytes | At its extraction commit | At HEAD |
|---|---|---|---|
| `get_indexshelf` | 657 | identical | identical |
| `find_selected_row_key` | 3,842 | identical | identical |
| `child_of_index` | 2,231 | identical | identical |
| `data_abspath_associated_with_index_row` | 3,111 | identical | identical |
| `data_pdsfile_for_index_row` | 386 | identical | identical |
| `from_filespec` | 774 | identical | identical |
| `from_opus_id` | 2,015 | identical | identical |
| `opus_products` | 8,199 → 8,385 | **+4 lines** — §6 | same |

The five index-row definitions also compare identical as a **single 10,251-byte
blob** on each side, first definition to last, which additionally rules out a
reordering or a dropped blank line; `from_filespec` and `from_opus_id` do the
same as a 2,795-byte blob. Nothing moved is still defined in `pdsfile.py`, and
neither new module carries a definition that was not on the move list. No moved
body was restyled to dodge an inherited lint violation; that is PR-23's job.

`pdsfile.py`: 5,125 → 4,593 lines; `_index_rows.py` 328, `_opus.py` 304. All
counted at HEAD, and re-counted at each round rather than carried forward: the
two new modules grew after the extraction commits, by 20 and 20 lines
respectively, **entirely in their class docstrings**, which rounds 1, 2 and 3
each corrected. The `pdsfile.py` figures are unchanged since the extraction, and
no executable line in either new module has changed since its extraction commit.

### 6. The one line that is not a pure move, and why it is in the move commit

`opus_products` reads the **class object** `PdsFile`, to enumerate its direct
subclasses. The Phase-5 preamble names this as the only bare class-object
reference in the whole phase and pins the pattern: a function-local deferred
import, never a module-level one, because `pdsfile.py` imports `_opus` to build
the class. The whole difference between the moved body and the original is
therefore these four lines:

```python
+        # Deferred: pdsfile.py imports this module to build PdsFile, so importing
+        # the class at module level here would be a cycle.
+        from pdsfile.pdsfile import PdsFile
+
         direct_pds_subclasses = PdsFile.__subclasses__()
```

**Why it is not a separate commit.** §2's commit-granularity rule sends keep-green
edits — "CI paths, **imports**, packaging, ignore globs" — to their own
content-edit commit, and the sub-plan said that is what would happen. It could
not be: without the import, `ruff check` reports `F821 Undefined name PdsFile`
against `_opus.py`, inside `opus_products`, under the project's own
configuration, so a pure-move commit
would be **red on an active gate**, and making it green would mean putting `F821`
into the ratchet entry — a widen, which §6.4 forbids absolutely. §2's PR-discipline
paragraph resolves it the other way for exactly this case: a move commit may
carry "the minimal edits required to keep the package importable **and every
active gate green** … each itemized explicitly in the PR description". This is
that edit, it is the only one, and it is itemized here, in the commit message and
in the PR. The other seven definitions are byte-identical, so the claim the
separation exists to protect is still exactly checkable.

**The deferred import is load-bearing, measured.** Deleting those lines from a
full copy of the tree and running `tests/pds3file/ tests/pds4file/
tests/rules/pds3/ tests/rules/pds4/ tests/core/` gives **39 failed** — every
`opus_products` and cross-PDS id — where the unmutated copy gives 721 passed.

**The bare-class-reference sweep, and its "nothing else" line.** Both new modules
were parsed for every `Name` node spelling `PdsFile`, `Pds3File` or `Pds4File`.
`_opus.py` has **exactly one**, inside `opus_products`, on the line immediately
below the deferred import that binds it. `_index_rows.py` has **none**. So the
preamble's
2026-07-17 claim that this is the only bare class-object reference in any
extraction seam holds for these two modules as well.

### 7. The `__bases__` sniff — moved byte-for-byte, and its premise verified

`data_abspath_associated_with_index_row`'s nested `get_keys` contains

```python
            if cls.__bases__[0].__name__ == 'Pds4File':
```

The plan is explicit that this stays behaviorally unchanged and that replacing it
with `issubclass`, an inherited class flag or anything else would **not** be
behavior-identical. It moved byte-for-byte inside its 3,111-byte definition. It
is the one place in either new module where a class is named, and the name is a
**string literal** resolved by `__name__` — the parse in §6 reports it as the
only such literal — so nothing had to be imported across a module boundary for
it.

**The plan's premise is verified rather than repeated.** For all **34** classes
in the `PdsFile` hierarchy, `__bases__[0].__name__`, the full `__bases__` tuple,
the full MRO and the sniff's own verdict were dumped on the parent tip and at
HEAD:

| Property | Classes where parent and HEAD differ |
|---|---|
| `__bases__[0].__name__` | **none** — all 34 identical |
| the sniff's verdict (`… == 'Pds4File'`) | **none** — `True` for exactly the same six pds4 rule classes on both sides |
| `__bases__` tuple | **one**: `PdsFile` itself, which gains the two mixins |
| MRO | all 34, and only by the insertion of `_IndexRowsMixin` and `_OpusMixin` |

That is the claim precisely: the sniff reads a rule subclass's *direct base*, and
adding mixin bases to `PdsFile` moves the MRO without moving any subclass's
`__bases__[0]`. The MRO row is the reason the check had to be run rather than
argued — every MRO does change, and only the property the sniff actually reads
does not.

**Both directions of the sniff were mutation-tested**, and they do not answer the
same way:

| Mutation | Result |
|---|---|
| sniff forced **on** (always take the PDS4 branch) | **1 failed** — `TestPds3FileBlackBox::test_data_abspath_associated_with_index_row` |
| sniff forced **off** (never take the PDS4 branch) | **721 passed** — nothing notices |

So the PDS3 side of the branch is pinned by the golden tests and the PDS4 side is
not, on the limited testing copy. That is a property of the tests, not of this
PR, and it is recorded as a deferred observation rather than acted on: this PR's
gate is the set diff, and adding a test id is movement.

The string-sniff fragility itself is now recorded as a phase-"b" item in
`critiques/deferred-observations.md` (entry 49), which the plan's PR-19 section
asks for in place of a fix. It was checked against entries 1–48 first: it was not
there.

### 8. Ruff ratchet — two codes split three ways, none gained

Procedure: for every code in `pdsfile.py`'s entry, the following was run against
the parent's `pdsfile.py`, this branch's `pdsfile.py`, `_index_rows.py` and
`_opus.py` —

```
ruff check --no-cache --isolated --output-format concise --select <code> \
           --line-length 100 --target-version py310 <file>
```

`--isolated` drops `pyproject.toml`'s `line-length = 100` and would otherwise
report an E501 at 88 columns that the project config does not, so the two
settings are restored explicitly (PR-16 §7, PR-17 §7 and PR-18 §7 record the same
trap), and `--output-format concise` is required because ruff 0.15's default
output no longer starts a line with the file path.

**Every one of the 18 codes conserves exactly** — parent count = the three
post-move counts summed — which is the mechanical statement of "this is a split
of an existing entry, not a new suppression". Only the two rows that move are
non-trivial:

| Code | parent `pdsfile.py` | → `pdsfile.py` | `_index_rows.py` | `_opus.py` |
|---|---|---|---|---|
| RUF005 | 8 | **6** | 1 | 1 |
| UP024 | 13 | **10** | 2 | 1 |
| B904, C405, E501, E701, E713, E721, F841, I001, N806, RUF012, SIM102, SIM114, SIM118, UP004, UP015, UP031 | 3, 3, 5, 11, 1, 1, 5, 2, 2, 16, 1, 2, 1, 1, 1, 9 | unchanged | 0 | 0 |

The **converse** check matters as much and is easy to skip: running the project's
whole select set (`E,F,W,I,UP,B,SIM,C4,A,N,PT,RUF` minus the three project-wide
ignores) against each new module with **no** per-file entry reports exactly the
codes its entry lists, and nothing else — `RUF005` + `UP024` for `_index_rows.py`,
and `RUF005` + `UP024` for `_opus.py` once the deferred import is in place. So
neither module needs a code that was not already forgiven for these same lines;
had either needed one, the sub-plan makes that a §6.4 hard stop.

Resulting entries:

| File | Entry | Note |
|---|---|---|
| `src/pdsfile/pdsfile.py` | 18 codes | unchanged — it still triggers every one of them |
| `src/pdsfile/_index_rows.py` | `["RUF005", "UP024"]` | exactly the codes its moved lines trigger |
| `src/pdsfile/_opus.py` | `["RUF005", "UP024"]` | exactly the codes its moved lines trigger |

The distinct (file, code) pairs move 18 → 18 + 2 + 2, and the **total number of
suppressed violations is unchanged at 85**: 85 on the parent's `pdsfile.py`, and
85 summed over this branch's `pdsfile.py`, `_index_rows.py` and `_opus.py`. (The
two codes that actually move account for 21 of those 85 — 8 `RUF005` plus 13
`UP024` — which an earlier draft of this paragraph reported as the whole; round 2
raised it as Minor 3. Both figures come from the same per-code counting loop as
the table above.) Neither new module needs `I001`: both import blocks are already
isort-clean, which is why that row conserves rather than growing.

Unlike PR-18, `pdsfile.py`'s entry does not shrink here — every one of its 18
codes still occurs in what remains — so there is no PR-23 note to add.

### 9. The tests that pin this code — measured, not assumed

A coverage run of `tests/pds3file/`, `tests/pds4file/`, `tests/rules/`,
`tests/core/` and `tests/holdings_maintenance/` with
`dynamic_context = test_function` attributes **50 distinct test contexts** to the
two new modules, from `tests/pds3file/`, `tests/pds4file/` and `tests/rules/`
only. **No `tests/holdings_maintenance/` context appears**, for the reason PR-18
established: PR-13's harness runs each tool as a subprocess that in-process
coverage does not follow. **No `tests/core/` context appears either.**

| Method | Contexts | Which test modules |
|---|---|---|
| `get_indexshelf` | 9 | `test_pds3file_blackbox.py`, `test_pds3file_blackbox_cached.py`, `test_pds3file_whitebox.py`, `rules/pds3/test_corss_8xxx.py` |
| `find_selected_row_key` | 12 | the same four |
| `child_of_index` | 9 | the same four |
| `data_abspath_associated_with_index_row` | 4 | `test_pds3file_blackbox.py`, `test_pds3file_whitebox.py` |
| `data_pdsfile_for_index_row` | **0** | — |
| `from_filespec` | 2 | `test_pds3file_blackbox.py`, `test_pds4file_blackbox.py` |
| `from_opus_id` | 19 | `test_pds3file_blackbox.py`, `test_pds3file_whitebox.py`, and 15 `tests/rules/` modules |
| `opus_products` | 28 | the same 15 `tests/rules/` modules |

Three details the round-3 review corrected in this table, all in the "which
modules" column and none in the counts, which it re-derived and reproduced
exactly. **(a)** The three index-row methods also get a context from
`tests/rules/pds3/test_corss_8xxx.py::test_associations`, which reaches them
through an association that crosses an index. **(b)** `from_opus_id`'s modules
are the *pds3* blackbox and whitebox — the pds4 blackbox contributes only to
`from_filespec`. **(c)** The 15 `tests/rules/` modules are 13 of the 13 under
`pds3/` and 2 of the 3 under `pds4/`:
`tests/rules/pds4/test_cassini_iss_fring_mosaics_rsfrench2025.py` is
module-skipped on this holdings copy and contributes no context at all. Round 1
raised an earlier "every … module" here as its Minor 3 and this table's first
correction was itself incomplete; the names above are read out of the coverage
data rather than described.

`data_pdsfile_for_index_row`'s **zero** is the one that matters, and it is not an
artifact of the subprocess blindness above: no in-process test calls it at all.
rms-viewmaster calls it at three sites. It is recorded as a deferred observation
(entry 50), not fixed here.

### 10. Negative controls — which parts of the moved code the net actually pins

Every check below is a mutation of the **moved** code, run against
`tests/pds3file/ tests/pds4file/ tests/rules/pds3/ tests/rules/pds4/
tests/core/` in `--mode ns`, which is **721 passed / 34 skipped** unmutated.

**The harness has a trap in it, and it is avoided by construction.**
`pyproject.toml` sets `pythonpath = [".", "src"]`, which pytest resolves against
**rootdir** and inserts at the front of `sys.path` — **ahead of `PYTHONPATH`**.
So mutating a copy of `src/` and pointing `PYTHONPATH` at it from the repo root
imports the *unmutated* tree, and every control reports green, which reads
exactly like "the tests do not reach this code" and is in fact "the harness does
not reach the mutation". PR-18 fell into this and re-ran all seven of its
controls. Each mutation here is therefore written into a **full copy of the
working tree**, pytest is run **from inside that copy**, and an extra
`conftest.py` there prints `pdsfile.pdsfile.__file__`,
`pdsfile._index_rows.__file__` and `pdsfile._opus.__file__`, which the harness
asserts all point into the mutated copy. **Every row below carries that
assertion, and every row passed it.**

| Mutation | Result |
|---|---|
| `get_indexshelf` returns a stub dict instead of the shelf | **21 failed**, 11 test functions |
| `find_selected_row_key` corrupts the exact-match answer | **14 failed**, 4 test functions |
| `child_of_index` builds its row PdsFile with empty `row_dicts` | **5 failed**, 4 test functions |
| `data_abspath_associated_with_index_row` corrupts the filespec segment | **1 failed** |
| `from_filespec` corrupts the bundleset segment | **5 failed**, both the pds3 and pds4 ids |
| `from_opus_id` corrupts the single-match return | **32 failed**, 3 test functions |
| `opus_products` truncates each glob to one path | **32 failed**, 3 test functions |
| `opus_products` loses its deferred import | **39 failed**, 3 test functions |
| the `__bases__` sniff forced **on** | **1 failed** |

**Four mutations changed nothing, and they are reported rather than dropped.**
A control that comes back green is a measurement too:

| Mutation | Result | What it means |
|---|---|---|
| `child_of_index` corrupts the CACHE lookup key | 721 passed | the corrupted key simply misses the cache and the object is rebuilt; the mutation is close to a no-op, so this row measures the mutation and not the tests |
| `data_pdsfile_for_index_row` always returns `None` | 721 passed | matches §9's zero contexts — nothing calls it |
| the `__bases__` sniff forced **off** | 721 passed | the PDS4 side of the branch is not exercised on the limited testing copy |
| `opus_products` sorts versions ascending instead of descending | 721 passed | no golden case has two versions of one product |
| `opus_products` sees no sibling subclass (`__subclasses__()` → `[]`) | 721 passed | the cross-PDS product path is not pinned on this holdings copy — but the *import* that feeds it is, as the 39-failure row above shows |

These are properties of the test suite, not of this PR, and this PR may not fix
them: its gate is the pass/fail set and a new test id is movement. They are
recorded as deferred observation 51.

The inherited and new mixin checks were mutation-tested too, because
`tests/api/test_mixin_collisions.py` discovers its subjects and a new mixin could
in principle be discovered and then checked vacuously. Unmutated the module is 15
passed; each mutation names the tests it turned red:

| Mutation | Went red |
|---|---|
| `_OpusMixin` moved to the front of the class statement | `test_the_mixin_bases_are_listed_alphabetically` |
| `_OpusMixin` also defines `get_indexshelf`, which `_IndexRowsMixin` defines | `test_no_two_mixins_define_the_same_name`, `test_every_mixin_name_is_reachable_through_pdsfile` |
| `Pds3File` itself defines `opus_products` | **`test_no_mixin_is_shadowed_by_a_pdsfile_subclass[Pds3File]`** — the check this PR adds, and nothing else |

The last row is the point of §11: on the parent branch that mutation turns
**nothing** red.

### 11. Deferred entry 48 — the shadowing check now covers the subclasses

Entry 48, raised by PR-18's round 4 and owned by PR-19:
`test_no_mixin_is_shadowed_by_pdsfile_itself` intersects each mixin's names with
`PdsFile`'s own and stops there, but the subclasses are where `PdsFile`'s method
surface is actually extended and are what the tools, OPUS and the rule modules
instantiate. A name a subclass defines wins over every base, so a collision with
a mixin would make the mixin's copy unreachable on the class callers actually
use.

It is taken up here rather than deferred again because **this PR is the case the
entry is about**: `_OpusMixin` carries `opus_products` and `from_opus_id`, and
OPUS support is where the rule subclasses override most. That puts it inside this
PR's deliverables rather than in the volunteered-Deferred category the common
brief warns about.

`test_no_mixin_is_shadowed_by_a_pdsfile_subclass` is a **new** test parametrized
over `Pds3File` and `Pds4File`, not a re-parametrization of the existing one, so
no existing id changes and §3's diff is additions only. It asserts first that
each subject really is in `PdsFile.__subclasses__()`, so it cannot pass by
looking at the wrong classes.

**The intersection was re-measured with the two new mixins included before the
test was written**, because a non-empty result is a hard stop rather than
something to resolve in the PR:

| | `_DerivedPathsMixin` | `_IndexRowsMixin` | `_LocalFsMixin` | `_OpusMixin` | `_ShelfMixin` |
|---|---|---|---|---|---|
| `Pds3File` (76 own names) | empty | empty | empty | empty | empty |
| `Pds4File` (50 own names) | empty | empty | empty | empty | empty |

The same intersection over the **whole 33-class subclass hierarchy**, rule
modules included, is also empty — that is measured but deliberately **not**
turned into a test: entry 48 asks for the direct subclasses, and building more
than the entry asks for is the failure mode PR-17 paid two rounds for.

**One near-miss worth recording.** **18 of the 34** rule modules define a
module-level `opus_products = translator.TranslatorByRegex([...])` table, which
the rule class consumes as `OPUS_PRODUCTS = opus_products + …`. It is a *module*
global, not a class attribute, so it never shadows `_OpusMixin.opus_products` —
verified: **zero** rule modules have an indented `opus_products =`, and the
hierarchy intersection above is empty. The name is one namespace away from the
method the mixin now owns, and this is recorded as deferred observation 52. (The
counts are measured: `grep -l '^opus_products\s*=' src/pdsfile/pds{3,4}file/rules/*.py`
gives 18, `grep -rn '^\s\+opus_products\s*='` over the same tree gives 0, and the
tree holds 34 rule modules excluding the two `__init__.py` files. Round 1 raised
an earlier "every rule module" as Minor 2.)

Entry 48 is **resolved** by this PR.

### 12. Consumer smoke — outcome unchanged, and it matters more here than for PR-18

The gate is **same outcome as baseline**, not "passes"
(`critiques/baselines/consumer-smoke-baseline.md`).

| Check | Baseline | This branch |
|---|---|---|
| A — rms-opus import paths | 4/4 resolve, 0 failures | **4/4 resolve, 0 failures** |
| B — rms-viewmaster startup | 5 ok, 3 pre-existing failures | **5 ok, 3 failures — the same three** |

The three Check-B failures are still `pdsfile.cache_lifetime` (raises),
`pdsfile.DEFAULT_CACHING` (absent) and the same `cache_lifetime` read inside
`get_page_cache()`. None became a pass. `pdsfile.pdsfile.repair_case` still
resolves.

**Unlike PR-18, both consumers call methods this PR moves**, which is why the
smoke is a real check here rather than a formality:

| Name | rms-opus — **call sites** | rms-viewmaster — **call sites** |
|---|---|---|
| `from_filespec` | 4: `obs_base_pds3.py:90`, `obs_base_pds4.py:33`, `do_import.py:1480`, `do_import.py:1482` | — |
| `from_opus_id` | 2: `do_import.py:687,690` | — |
| `opus_products` | 1: `do_import.py:1487` | — |
| `find_selected_row_key` | 1: `do_import.py:1553` | — |
| `data_pdsfile_for_index_row` | — | 3: `viewmaster.py:873,1449,1580` |

These are **call sites**, counted after excluding comments and the unrelated
local helpers whose names contain the same substring — rms-opus's own
`_pdsfile_from_filespec` and `get_opus_products_rows_for_filespec` — which an
earlier draft of this table counted as references. Round 1 raised that as
Deferred 2; it is corrected here rather than deferred, because a wrong figure in
this record is the defect class PR-18's round-3 Major was about. The
rms-viewmaster figure was already call sites (its three `.py` hits; the other
three matches are in `docs/_build/html/`, generated output).

Every one of them is an attribute access on the class or on an instance
(`Pds3File.from_filespec(...)`, `pdsf.opus_products()`,
`query_pdsfile.data_pdsfile_for_index_row()`), so each resolves through the MRO
and the mixin move is invisible to it — which is what the byte-identical API dump
in §4 is the formal statement of, and what Check A and Check B confirm at run
time.

Environment note carried from the baseline: the check ran under the pdsfile
venv's interpreter with rms-viewmaster's `site-packages` appended to
`PYTHONPATH`, because that venv lacks pdsfile's declared `range_ex` dependency.
rms-viewmaster is at `a0d05e2`; rms-opus is at `73cb6de7`.

### 13. Clean install

`scripts/clean_install_check.sh` passes inside `run-all-checks.sh`. Both new
modules are picked up by the existing `include = ["pdsfile*"]` package glob with
no packaging change, and the gate imports the whole manifest module surface —
`pdsfile.pdsfile` among them — which cannot succeed if either is missing from the
distribution.

### 14. The monkeypatch audit — the check the set diff cannot perform

Deferred entry 29 (opened by PR-16's round-1 Major, owned by "PR-17 onward") says
an extraction sweep must also ask **which namespaces the tests patch**, not only
which globals the code reads. A test whose patch lands on a module the moved code
no longer resolves through keeps passing while exercising nothing, and §6.2's
outcome-set diff compares pass/fail — so it is *structurally blind* to this class
of defect. **This PR's set diff would have reported "two ids added and nothing
else" in every one of the cases below, including a broken one.**

**Enumeration.** Every `monkeypatch.setattr` / `setitem` / `delattr` / `setenv` /
`delenv`, `mock.patch`, `patch(`, `patch.object` and bare `setattr(` in `tests/`
and `scripts/` — 20 sites, all `monkeypatch`; the tree still uses no
`unittest.mock` at all:

| Target | Sites | Names a symbol **this PR** moves? | Does this PR's moved code read it? |
|---|---|---|---|
| `Pds3File.CACHE` (`tests/core/conftest.py:28`, `test_pdsfile_caching.py:112,126`) | 3 | no — a class attribute that stays on the class | **yes** — `child_of_index` reads `cls.CACHE` |
| `Pds3File.preload` (`test_pdsfile_caching.py:127`) | 1 | no — PR-21's symbol | no |
| `Pds3File`/`Pds4File.LOCAL_PRELOADED`, `.LOCAL_HOLDINGS_DIRS` (`test_pdsfile_path_resolution.py:58,59,71,72,85,86`) | 6 | no — class attributes that stay on the classes | **yes** — `opus_products` reads `sub_cls.LOCAL_PRELOADED` |
| `Pds3File.shelf_path_and_key_for_abspath` (`test_pdsfile_path_resolution.py:120,129,137,155`) | 4 | no — PR-17's symbol, audited there | no |
| `abspath_for_logical_path.__globals__['glob']` (`test_pdsfile_path_resolution.py:92`) | 1 | no — PR-16's fix site, on `_path_utils`'s globals | **indirectly** — `from_opus_id` calls that same function object |
| `pdsviewable.ICON_SET_BY_TYPE` (`test_pdsviewable_iconset_for.py:47`) | 1 | no — different module | no |
| `monkeypatch.setenv` / `delenv` (`test_pdsfile_path_resolution.py:54,70,83,84`) | 4 | no — environment, not a namespace | no |

**No patch site names any of the eight methods.** A regex over `tests/`,
`scripts/` and `src/` for *direct assignment* to any of the eight — the form that
is not a `monkeypatch` and is easy to miss — returns hits only in the rule
modules' module-level `opus_products` translator tables (§11), and none at all
for the other seven names. No test assigns to any attribute of
`pdsfile.pdsfile`.

**Three targets survive the move because they are read through the class, and
that is proved, not argued.** The first two rows above are the ones this PR's
code actually reads; the fifth is a function it calls. Each was forced to answer
wrongly in a full-tree copy, and each turned its own test red:

| Forced-wrong control | Went red |
|---|---|
| the `Pds3File.CACHE` patch removed | `TestGetPermanentValues::test_caching_is_resumed_after_the_values_are_read` |
| the `Pds3File.preload` patch removed | `TestGetPermanentValues::test_caching_is_resumed_after_a_missing_value_triggers_a_reload` |
| `LOCAL_PRELOADED` stubbed to a non-empty list | `TestHoldingsEnvironmentVariable::test_a_class_does_not_borrow_another_class_holdings_root` |
| the `glob` stub in `abspath_for_logical_path.__globals__` answers non-empty | the same id |
| `shelf_path_and_key_for_abspath` returns instead of raising | 4 ids across `TestInfoshelfPathAndKey` |
| the `pdsviewable.ICON_SET_BY_TYPE` patch removed | 9 ids across `TestIconsetFor` |

Six controls cover all 20 sites, because sites sharing a target share a
mechanism. Every one asserted the file it imported, as §10 describes.

**PR-16's fix shape is confirmed move-proof by this PR.**
`test_pdsfile_path_resolution.py:92` patches `abspath_for_logical_path.__globals__`
— the function's *own* namespace, whichever module that is — rather than
`pdsfile.pdsfile.glob`. `from_opus_id` now lives in `_opus.py` and still calls
the same function object, so the patch reaches exactly what it reached before.
Had the test patched `pdsfile.pdsfile.glob`, PR-16's move would already have
silenced it. This is the concrete second data point for entry 29's preferred fix.

**Entry 29's second half — rebinding re-exported *data*.** The same asymmetry one
level down, measured on both sides:

| | parent `80cd9ff` | this branch |
|---|---|---|
| namespace the eight methods resolve through | `pdsfile.pdsfile` | `pdsfile._index_rows` / `pdsfile._opus` |
| namespace `pdstable`, `numbers`, `defaultdict` resolve in, for the moved code | `pdsfile.pdsfile` | the new modules |
| rebinding `pdsfile.pdsfile.pdstable` reaches `child_of_index` | **yes** | **no** |
| `pdsfile.pdsfile.pdstable` / `.numbers` / `.defaultdict` still bound | yes | yes |

Nothing in `src/`, `tests/`, `scripts/`, rms-opus or rms-viewmaster rebinds any
of those three module attributes — greped, zero hits — so nothing is broken
today. The general observation stands for PR-20 onward and stays in
`critiques/deferred-observations.md` as entry 29.

### 15. Deferred observations

Entry 29 is the one this PR was told to act on every time, and §14 is the action.
It is **not** resolved — it is a per-PR step, owned by "PR-17 onward" — so it
stays open for PR-20 through PR-22. **Entry 48 is resolved** by §11. Entry 42
(the back-import guard, owner PR-22) is untouched: this PR adds two mixin modules
and §5 shows both are clean by the same parsing check, but it builds no guard.
No other entry in 1–48 is resolved or invalidated here.

Four entries are **added** by the executor's own measurements: 49 (the
`__bases__` string sniff, which the plan's PR-19 section explicitly asks be
recorded as a phase-"b" item rather than fixed), 50 (`data_pdsfile_for_index_row`
has zero in-process test coverage while rms-viewmaster calls it at three sites),
51 (the four measured coverage gaps §10's green controls found), and 52 (the rule
modules' module-level `opus_products` table, one namespace away from the mixin
method). A fifth, 53, comes from the round-1 review: the new subclass check names
its two subjects rather than discovering them, so a third direct subclass would
go unchecked — owner PR-20. A sixth, 54, comes from the round-2 review: the
mixins' hand-written "state contract" docstrings drift and are mechanically
derivable, and a read-side AST check would catch both that and a genuinely
stranded attribute — owner PR-22. Round 2's second Deferred item is folded into
entry 51 rather than given a number, because it is a method for closing 51(a)
cheaply; its third was informational and is noted at the end of 54. Round 1's
other Deferred item was a wrong figure in §12 of this record; it is **corrected
there** rather than deferred, because a wrong figure in this document is the
defect class PR-18's round-3 Major was about.

### 16. Review loop

| Round | Verdict | Findings | Record |
|---|---|---|---|
| 1 | goal met | 0 Major, 3 Minor (all accepted; one fixed in `src/`, two in this record), 2 Deferred (entry 53 added; the other corrected in §12 instead) | `critiques/pr-19/round-1.md` |
| 2 | goal met | 0 Major, 5 Minor (all accepted and fixed; one in `src/`, four in this record), 3 Deferred (entry 54 added; one folded into 51, one informational) | `critiques/pr-19/round-2.md` |
| 3 | goal met | 0 Major, 5 Minor (all accepted and fixed; two in `src/` and `tests/`, three in this record), 2 Deferred (both fold into entries 53 and 54) | `critiques/pr-19/round-3.md` |
| 4 | goal met | 0 Major, 0 new Minor; all 13 prior findings confirmed resolved; 2 Deferred (one folds into 54, one fixed in place here) | `critiques/pr-19/round-4.md` |

**The loop terminates at round 4**, at §6.6's four-round cap: a fresh reviewer
returned zero Major and no new un-rebutted Minor. Round 4 is the *scoped*
re-review the anti-thrash rule prescribes — confirm the prior rounds' findings
are resolved, raise only new Major — and it confirmed all thirteen by
re-measuring each rather than reading this record: it re-ran the AST attribute
walk over both mixin modules and found both docstrings exact in both directions,
re-ran its own `dynamic_context` coverage pass and reproduced every count *and*
every corrected attribution in §9, re-derived the byte equivalence, the ratchet
conservation, the API dump, the four junit reductions and the 34-class shape
dump, and re-ran the no-holdings job. Its two Deferred items are the last piece
entry 54's automated check will need — an exclusion for the names a mixin defines
itself, without which `_IndexRowsMixin`'s four intra-mixin calls read as external
dependencies — and one wording point in this section, fixed in place above rather
than deferred.

**Nothing was rebutted in any round.** Every finding in all four rounds was
accepted and fixed, which is itself worth stating: there was no scope-creep
finding to push back on, and no disagreement to escalate.

*(Rows are written only after the round they describe has run and its record file
exists on disk — the rule PR-18's round-3 Major established. No row is written
for a round that has not run.)*

Round 1's three Minors were all record- or docstring-accuracy defects, and all
three were **counts asserted rather than measured** — the same failure shape,
three times. Minor 1: `_IndexRowsMixin`'s class docstring called all nine names
it lists "lazy properties", when `is_index_row`, `row_dicts` and `column_names`
are plain instance attributes assigned in `PdsFile.__init__` (`pdsfile.py:333`,
`:335`, `:337`), and its "read" framing hid that `child_of_index` also *writes*
`column_names`. Minor 2: "every rule module defines a module-level
`opus_products` table" — measured, 18 of 34. Minor 3: "every
`tests/rules/pds{3,4}/` module" contributes a context — measured, 15 of 16;
`test_cassini_iss_fring_mosaics_rsfrench2025.py` is module-skipped on this
holdings copy. Each is fixed with the measurement in place of the assertion.

The round-1 reviewer re-derived, with its own scripts rather than reading them
here: the byte-for-byte segment comparison of all eight definitions, the API
dumps, the four junit reductions and both set diffs, the `measured_files`
non-vacuity argument, the ratchet conservation, the `__bases__[0].__name__` and
`dir()` surface of all 34 classes, the `F821` proof that the deferred import is
gate-load-bearing, the greenness of the intermediate commit `2d2de4a`, and its
own `dynamic_context` coverage run, which reproduced §9's table exactly.

Round 2 found five more of the same shape and no Major, which is the useful
signal: **every finding in both rounds so far has been a number in this document
that was stated rather than measured**, and none has been in the extracted code.
Round 2's were the `_index_rows.py` line count (308 → 326, stale after round 1's
own fix), the `from_filespec` consumer count (given as 3 above a row listing 4 —
the very table round 1 had corrected, corrected one short), the ratchet's
"suppressed violations unchanged at 21" (the subtotal of the two moving codes;
the total is **85**), the `_IndexRowsMixin` docstring again (round 1 fixed what
it said, round 2 found what it omitted), and a superseded run labelled with a
commit that postdates it by 16 minutes. All five are fixed above with the
measurement in place of the assertion, and round 2's fix rewrote both docstrings
from an AST walk of their own modules rather than by hand. **That walk was itself
incomplete** — it followed `self.X` and `cls.X` but not an attribute on a
subscript, so it missed `_opus.py`'s `version_rank`, which round 3 caught. The
walk was widened to every `Attribute` node and both docstrings now verify
complete in **both** directions against it; deferred entry 54 asks that the
widened form move into a test.

The round-2 reviewer independently proved that a module-level back-import in
`_opus.py` raises a real `ImportError`, mutation-tested the new subclass check
(it catches the collision and nothing else fires), and ran three real-holdings
behavior probes — normal mode, `SHELVES_ONLY` mode, and a synthetic object that
forces the sniff's PDS4 branch — all byte-identical between the parent tip and
this branch. That third probe is also the method entry 51(a) now records.

**Round 3 found the same shape a third time and still no Major**, which is the
most useful thing this loop has produced. Its five: `_OpusMixin`'s "and nothing
else" contract omitted `version_rank`, read as `li[0].version_rank` — a shape the
AST walk that generated the list did not follow, so round 2's "derived from an
AST walk" was itself the assertion that failed; §9's *which modules* column was
wrong in three ways while every count in it was right; three `_opus.py` line
numbers in §6 were stale by exactly the 17 lines §5 itself records the docstrings
adding; §1's non-vacuity table used set notation naming five modules where nine
and eleven were measured; and the new subclass check's comment claimed to catch a
failure the move introduces, which it does not.

That last one is the only round-3 finding that is not a number. It is right: a
name a subclass and a mixin both define was already shadowed before the
extraction, when the copy lived on `PdsFile`. The comment now states the
invariant the check really pins and carries the measurement that makes its
strictness safe for the rest of the phase — every name `Pds3File` and `Pds4File`
override is a class attribute, which stays on `PdsFile`, or is on PR-22's
stay-list. The generalization is deferred entry 53.

The §6 line numbers are not re-stated with corrected values: the project's own
rule is to locate by symbol, and a line number in a record that the next round's
docstring fix will move is a defect generator. They now name `opus_products`.

**§6.6 step 5 was applied at every boundary.** Rounds 1, 2 and 3 each produced a
fix under `src/pdsfile/`, so the full-data record was regenerated after each.
§3's figures are the third regeneration, and its superseded-pair table records
that all four head runs produced the same two reduced sets — which is also the
evidence that every fix in this loop was a docstring, a comment or a record, and
that no executable line changed after the extraction commits. **Round 4's fixes
touch `critiques/` only, so the record carries forward unchanged** — the other
half of the same rule, and the reason the last change under `src/pdsfile/` is
still `b6bda4a`.

## PR-20 — `refactor: extract associations, split/sort, transformations → _associations.py, _sorting.py`

**Branch:** `pr-20-associations-sorting`, based on `pr-19-opus-index-rows` @ `bf42ae7`
("docs: note that round 4's fixes leave the full-data record valid"), opened
against that branch, not `rewrite`
(`plans/2026-07-27-addendum-phase5-stack-extension.md`).
**Baseline:** **PR-19's recorded post-move set** — its §3 above, `--mode ns` 848
passed / 34 skipped (882 ids) and `--mode s` 555 passed / 3 skipped (558 ids) —
**re-measured locally on the parent tip** with this PR's own command lines rather
than copied from the table. The re-measurement reproduced it exactly.
**Date:** 2026-07-27
**Sub-plan:** [`plans/2026-07-27-pr-20-subplan.md`](../plans/2026-07-27-pr-20-subplan.md)

This is the largest extraction in the phase — **27 definitions, 761 source lines
across three banner blocks, into two modules** — and its set diff is **empty in
both modes**. It touches no test file, so unlike PR-19 it adds no test id.

### 1. Environment

| Item | Value |
|---|---|
| Interpreter | CPython 3.12.3, repo venv, `pip install -e ".[dev]"` |
| Holdings | `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` + `PDSFILE_TEST_HOLDINGS=full`, pointed at the limited testing copy the goldens are tuned to |
| Baseline tree | a `git worktree` detached at the parent tip `bf42ae7`, same interpreter, same holdings; `pytest` reports that directory as `rootdir` |
| Command lines | exactly those in `scripts/automated_tests/pdsfile_main_test.sh` (serial, under `coverage`), plus `-rA --junitxml` |

**Which source each run actually imported, proved rather than assumed.** The
interpreter is the main tree's venv, whose editable install appends
`<main tree>/src` to `sys.path`, and there are now **six** stacked branches
sharing it, so a worktree run could silently measure the wrong tree and make the
whole comparison vacuous. Each run wrote its own `COVERAGE_FILE`, and
`coverage.CoverageData.measured_files()` was read afterwards for its **absolute**
paths:

| Run | top-level `pdsfile` modules measured | count |
|---|---|---|
| baseline | `<worktree>/src/pdsfile/` — `__init__`, `_derived_paths`, `_index_rows`, `_local_fs`, `_opus`, `_path_utils`, `_shelves`, `pdscache`, `pdsfile`, `pdsviewable`, `preload_and_cache` | **11** |
| this branch | `<main tree>/src/pdsfile/` — the same eleven, plus **`_associations`** and **`_sorting`** | **13** |

Those are the modules directly under `src/pdsfile/`; both runs additionally
measure the same `holdings_maintenance/`, `pds3file/`, `pds4file/` and `tools/`
subpackages, each under its own tree's prefix — 68 measured files on the baseline
side and 70 on this branch, the difference being exactly the two new modules.

The presence of exactly two extra modules on this branch and **zero** of them on
the baseline side is the decisive bit: had the worktree run leaked into the main
tree's install, they would have been measured there too. Counted mechanically:
**0** baseline paths fall outside the worktree prefix, **0** head paths fall
outside the main tree's, and the text `_sorting` or `_associations` appears in
**0** baseline paths and **2** head paths.

### 2. Active §2 gates

| Gate | Result |
|---|---|
| API-freeze manifest test | **passed** — and the dumped surface is byte-identical to the parent's, 733,876 bytes each, same MD5; §4 |
| Full-data suite, both modes | **passed** — **empty set diff in both modes**; §3 |
| `ruff check src/pdsfile tests scripts` | **passed**; the ratchet gained no code — §8 |
| Clean-install import check | **passed** (throwaway venv, `pip install .`, full module surface imports) |
| Hosted lint/no-holdings job (`scripts/run-all-checks.sh`, no holdings env vars) | **passed**, **82 passed / 800 skipped** — the parent's figure, unchanged, and re-measured on the parent tip in the same session to confirm it |
| Adversarial review loop | `critiques/pr-20/round-<k>.md` |

### 3. Full-data suite — an empty diff in both modes

Both passes were run on the parent tip and on this branch's head with the same
interpreter and the same holdings. Every `testcase` element of each `--junitxml`
was reduced to one `outcome<TAB>classname::name` line, sorted, and the two files
were diffed with `diff -u`.

| Run | parent `bf42ae7` | `pr-20-associations-sorting` | set diff |
|---|---|---|---|
| `--mode ns` | 848 passed / 34 skipped (882 ids) | 848 passed / 34 skipped (882 ids) | **empty** |
| `--mode s` | 555 passed / 3 skipped (558 ids) | 555 passed / 3 skipped (558 ids) | **empty** |

`diff -u` produced **zero output lines** for both modes. The parent numbers
reproduce PR-19's recorded set, which is what makes this a comparison against
PR-19's baseline rather than against a fresh unrelated measurement.

Both modes matter and both were run: `--mode s` is the only thing that exercises
the `SHELVES_ONLY` branch, and `associated_abspaths` reaches it through
`cls.glob_glob` and `cls.os_path_exists` while `sort_basenames` reaches it
through `cls.os_path_isdir`.

**Freshness (§6.6 step 5).** The last change under `src/pdsfile/` is commit
`9684c33` (round 4's deferred fix (b), one line of `_associations.py`'s class
docstring), at **21:33:16**. The head runs recorded above postdate it: their
`--junitxml` timestamps are **21:36:12 and 21:38:03**. They are the fourth
regeneration §6.6 step 5 requires — every one of the four rounds produced a fix
under `src/pdsfile/`, and the last one did so after the loop had already
terminated, which the rule covers just the same: a record predating the last
`src/` change is stale whether or not another reviewer follows.

The **superseded** head pairs are recorded rather than dropped, each with the
commit its tree was actually at:

| Head pair | `--junitxml` written | Tree at | Reduced sets |
|---|---|---|---|
| 1 | 19:23:02 / 19:24:53 | `48b0605` | identical to pairs 2, 3, 4 and 5 |
| 2 | 20:14:26 / 20:16:15 | `6350859` | identical to pairs 1, 3, 4 and 5 |
| 3 | 20:46:47 / 20:48:37 | `752bd12` | identical to pairs 1, 2, 4 and 5 |
| 4 | 21:12:38 / 21:14:29 | `a529d26` | identical to pairs 1, 2, 3 and 5 |
| **5 (current)** | **21:36:12 / 21:38:03** | **`9684c33`** | **the figures above** |

`diff` between any two of the five pairs is empty in both modes, which is what
docstring-only changes should do and is measured rather than assumed — and is
also the evidence that every fix in this loop has been a docstring, a comment or a
record, rather than the claim of it. The provenance check was re-run on each pair:
70 measured files, **0** of them outside the main tree's prefix, 13 directly under
`src/pdsfile/`.

The **baseline** runs (19:08:48 and 19:10:39) stand throughout: they were taken
in a detached `git worktree` at `bf42ae7` that nothing has touched since.

### 4. API freeze — empty diff, as a mixin move requires

1. `pytest tests/api/` passes — 16 ids, unchanged from the parent: the freeze
   test plus the 15 that `tests/api/test_mixin_collisions.py` contributes. This
   PR adds no id there and edits no test file.
   `tests/api/api_manifest.json`, `tests/api/manifest_allowlist.json`,
   `scripts/dump_public_api.py` and `tests/api/test_api_freeze.py` are untouched
   (§6.4) — verified with `git diff --stat bf42ae7..HEAD` over those four paths,
   which is empty. No allowlist entry was added.
2. `scripts/dump_public_api.py` was run against a worktree at the parent tip and
   against this branch's head. The two dumps are **byte-identical** (733,876
   bytes each, identical MD5 `442428da…`, `diff` empty, both stderr streams
   empty).

That is the expected result and the plan says so: the dumper expands a class's
members with `dir(cls)`, which is MRO-wide, and records names, kinds and
signatures — never the defining class. So moving `PdsFile.associated_parallel`
into `_AssociationsMixin` cannot show up here, and any diff would have meant a
mistake.

`pdsfile._associations` and `pdsfile._sorting` are underscore-prefixed, so the
dumper skips them where the submodule import binds them onto the `pdsfile`
package; the same applies to `_AssociationsMixin` and `_SortingMixin` inside
`pdsfile.pdsfile`. That is the freeze-invisibility the Phase-5 preamble requires
of new internal names. **This PR introduces no new non-underscore name
anywhere.**

The `__qualname__` consequence PR-18 §4 records applies here too and for the same
reason — `PdsFile.sort_basenames.__qualname__` is now
`_SortingMixin.sort_basenames`. It is a phase-wide consequence of the mandated
mixin technique, already true of the five mixins on the parent branch, and the
dumper records `kind` and `signature`, never a qualname. Measured again for this
PR's 27 names: nothing in `src/`, `tests/`, `scripts/`, rms-opus or
rms-viewmaster matches on that text.

### 5. What moved, and the 3-blocks-into-2-modules mapping

27 definitions, located by name. The plan's `:5979–6289`, `:5518–5871` and
`:5873–5977` windows are against the 6,304-line original; PR-15 through PR-19
have all edited this file, which is **4,593 lines at the parent tip**. On that
tip the targets are the last three banner blocks of the class body, and they are
consecutive: `pdsfile.py:3807–4567`.

| Banner | Lines at `bf42ae7` | New module | Definitions |
|---|---|---|---|
| `# How to split and sort filenames` | 3807–4160 | `src/pdsfile/_sorting.py` (`_SortingMixin`) | `split_basename`, `basename_is_label`, `basename_is_viewable`, `sort_basenames`, `sort_sibnames`, `sort_siblings`, `sort_logical_paths`, `sort_childnames`, `viewable_childnames`, `childnames_by_anchor`, `viewable_childnames_by_anchor` — **11** |
| `# Transformations` | 4162–4266 | the same module | `abspaths_for_pdsfiles`, `logicals_for_pdsfiles`, `basenames_for_pdsfiles`, `pdsfiles_for_abspaths`, `logicals_for_abspaths`, `basenames_for_abspaths`, `pdsfiles_for_logicals`, `abspaths_for_logicals`, `basenames_for_logicals`, `pdsfiles_for_basenames`, `abspaths_for_basenames`, `logicals_for_basenames` — **12** |
| `# Associations` | 4268–**4567** | `src/pdsfile/_associations.py` (`_AssociationsMixin`) | `associated_logical_paths`, `associated_pdsfiles`, `associated_abspaths`, `associated_parallel` — **4** |

**Why two modules and not three.** The parent plan names exactly two module files
for this PR, so a `_transformations.py` would deviate from the stated deliverable
and would need an owner-acknowledged addendum. The pairing chosen is also the one
the code supports: split/sort and the transformations are one domain — bulk
operations over lists of basenames, logical paths, abspaths and `PdsFile`
objects, none of which reads the filesystem itself (the four that need to probe
it delegate to `_LocalFsMixin`) — whereas associations are the category-crossing
lookup layer that walks the holdings tree. The measured call
graph agrees, and one way: **the associations call the transformations at three
sites and the transformations never call back** (§6). Because the filename
`_sorting.py` undersells a module that also holds twelve conversion helpers, its
module header and class docstring say what it actually holds.

**The associations window ends at `associated_parallel`, not at the end of its
banner block.** `is_logical_path` (`:4569–4578` on the parent tip) falls inside
the plan's association line window but is a generic path predicate, and it is a
frozen public `PdsFile` classmethod, so the plan says leave it in core and
PR-22's stay-list names it again. It and the module-level tail below the class
(`PdsFile.SUBCLASSES['default'] = PdsFile`, `PdsFile.cache_category_merged_dirs()`)
stay put. This is the one window boundary in the PR that does not follow a
banner, which is exactly what a mechanical block-move gets wrong, so it is
checked rather than asserted: at HEAD `is_logical_path` is still in
`vars(PdsFile)`, `inspect.getattr_static(PdsFile, 'is_logical_path')` still
resolves to `PdsFile`'s own function object, and its source segment is
byte-identical to the parent's.

Taking the `# Associations` banner with its block left `is_logical_path` sitting
directly under the `# Log path associations` banner, which then described a
section it is not part of. A **separate four-line commit** (`48b0605` — three comment
lines and the blank that separates them from the method) gives it its own
banner; it is kept out of the move commit so that commit stays a pure move.

**No block contains a class-level assignment.** An AST pass over the `PdsFile`
body reports the three windows as 27 `FunctionDef`s and **zero** `Assign` nodes,
so the "class attributes stay on `PdsFile`" rule has nothing to catch here. That
is the same result PR-19 measured and different from PR-17 (six shelf attributes)
and PR-18 (`LOG_ROOT_`), and it is recorded as a measurement rather than an
absence noticed by eye. In particular the sort configuration — `SORT_ORDER`
(`:244`), `SORT_KEY` (`:212`) and the four setters `sort_labels_after` /
`sort_dirs_first` / `sort_dirs_last` / `sort_info_first` (`:253–299`), all under
the `# DEFAULT FILE SORT ORDER` banner — and the association registries
`ASSOCIATIONS`, `NEIGHBORS`, `SIBLINGS`, `VERSIONS` (`:207–211`) stay on
`PdsFile`, where the moved methods read them off the class and where PR-22's
stay-list expects them.

**The sweep was computed, not read.** CPython's `symtable` yields the
module-global names each moved definition's body references — a name bound in an
enclosing *function* scope is FREE, not GLOBAL, so `is_global()` is exactly the
module-global question — and a second AST pass covers each definition's decorator
expressions and argument defaults, which are evaluated in module scope and which
`symtable` does not attribute to the method. Result:

| Category | `_SortingMixin` | `_AssociationsMixin` |
|---|---|---|
| module-level **imports** referenced | `os` | `os` |
| module-level **functions** referenced (from `_path_utils`) | `_clean_join`, `abspath_for_logical_path`, `logical_path_from_abspath` | `_clean_join`, `_needs_glob` |
| module-level **constants** referenced | **none** | **none** |
| module-level **classes** referenced (import-cycle risk) | **none** | **none** |
| unclassified names | **none** | **none** |
| seen **only** in a decorator or an argument default | **none** | **none** |

The second pass found nothing again, which is itself the result worth recording:
PR-16's `_GLOB_CACHE_SIZE` and PR-17's `PATH_EXISTS_CACHE_SIZE` were both
invisible to a body-only sweep, so the pass is run whether or not it is expected
to fire, and its "none" is measured rather than assumed.

**No class object is referenced by either module, so neither needs a
function-local deferred import.** That is the difference from PR-19, whose
`_opus.py` needed one for `PdsFile.__subclasses__()`; both PR-20 move commits are
therefore pure moves plus their header imports. Confirmed by parsing both modules
for every `Name` node spelling `PdsFile`, `Pds3File` or `Pds4File`: **zero in
each**. **No string literal is used to resolve a class by name either** — the parse finds
four string constants containing one of those three words, **one in `_sorting.py`
and three in `_associations.py`, and all four are docstrings**, which the parse
classifies as such rather than the eye. (Contrast `_index_rows.py`, where
PR-19's `__bases__[0].__name__ == 'Pds4File'` sniff really does resolve a class
by a string literal in executable code.)

Per-definition, so the aggregate can be checked rather than trusted: of the 23
`_SortingMixin` definitions, 16 reference **no** module global at all;
`sort_basenames`, `abspaths_for_basenames` and `logicals_for_basenames`
reference `_clean_join`; `basenames_for_abspaths` and `basenames_for_logicals`
reference `os`; `abspaths_for_logicals` references `abspath_for_logical_path`;
`logicals_for_abspaths` references `logical_path_from_abspath`. Of the four
`_AssociationsMixin` definitions, three reference nothing and
`associated_abspaths` references `_clean_join`, `_needs_glob` and `os`.

**One module-level name is stranded in `pdsfile.py`, and it stays.** Counted over
the AST, not eyeballed:

| Name | total refs before | inside moved bodies | left in `pdsfile.py` |
|---|---|---|---|
| `os` | 18 | 3 | 15 |
| `_clean_join` | 10 | 4 | 6 |
| `abspath_for_logical_path` | 4 | 1 | 3 |
| `logical_path_from_abspath` | 2 | 1 | 1 |
| **`_needs_glob`** | **1** | **1** | **0 — stranded** |

`_needs_glob` is private, so it is not a frozen manifest member — but it is
reachable today as `pdsfile.pdsfile._needs_glob`, and the header's re-export block
exists for exactly that reason ("carried so that no name reachable as
`pdsfile.pdsfile.<name>` is lost"), where `_GLOB_CACHE_SIZE` and `_clean_glob`
already sit. Deleting it would break the no-name-lost invariant every Phase-5 PR
has measured; an inline `noqa` and a ratchet grow are both forbidden. So its
import moved into that block in the PEP-484 redundant-alias form:

```python
from ._path_utils import (FILE_BYTE_UNITS as FILE_BYTE_UNITS,
                          _GLOB_CACHE_SIZE as _GLOB_CACHE_SIZE,
                          _clean_glob as _clean_glob,
                          _needs_glob as _needs_glob,
                          selected_path_from_path as selected_path_from_path)
```

**No import cycle.** Parsing both new modules reports their module-level imports
as `import os` and `from ._path_utils import …`, both at column 0, and **no
import statement anywhere in either file mentions `pdsfile`** in any spelling.
`_path_utils` imports only `fnmatch`, `functools`, `glob`, `math` and `os`, so
neither import can close a cycle back to `pdsfile.pdsfile`; that is read out of
the file rather than assumed.

**Zero names lost, measured.** `sorted(vars(pdsfile.pdsfile))` was compared
between the parent worktree and this branch, each run printing the `__file__` it
had imported: **50 names before, 52 after, none lost.** The two gained are
`_AssociationsMixin` and `_SortingMixin`, which the `class PdsFile` statement
needs; both are underscore names, so the manifest does not see them.

**Byte-for-byte equivalence, measured.** At each extraction commit each moved
definition's exact source segment (decorators included) was extracted from the
parent commit's `PdsFile` body and from the new mixin's body and compared byte by
byte. **All 27 are identical, with no exception** — this PR has no counterpart to
PR-19's four-line deferred import:

| Module | Definitions | Total bytes | Result |
|---|---|---|---|
| `_sorting.py` | 23 | 17,886 | all identical |
| `_associations.py` | 4 | 11,900 | all identical |

Every byte figure in this section is the source segment **without** its trailing
newline — the definition's first line through its last, joined by `\n` — because
that is what `ast`'s line span gives. A reader who joins with `keepends=True`
gets one byte more per definition and one more per blob, which is the same
comparison; the convention is stated so the numbers can be reproduced rather than
approached.

Each contiguous run also compares identical as a single blob, which additionally
rules out a reordering or a dropped blank line: the split/sort run
(`split_basename` … `viewable_childnames_by_anchor`) as **14,586 bytes**, the
transformations run (`abspaths_for_pdsfiles` … `logicals_for_basenames`) as
**3,424 bytes**, and the associations run (`associated_logical_paths` …
`associated_parallel`) as **11,906 bytes**. The three in-class banner comments moved
with their blocks rather than being retyped: `# How to split and sort filenames`
and `# Transformations` head the two halves of `_sorting.py`'s class body, and
`# Associations` heads `_associations.py`'s. (No line number is given for them:
the project's own rule is to locate by symbol, and a docstring fix in the next
review round moves every line number in these files.) Nothing moved is still defined in
`pdsfile.py`, and neither new module carries a definition that was not on the
move list. No moved body was restyled to shed an inherited lint violation; that
is PR-23's job.

`pdsfile.py`: 4,593 → 3,837 lines; `_sorting.py` 525, `_associations.py` 373. All
counted at HEAD, and re-counted at each round rather than carried forward: the two
new modules were 522 and 370 at their extraction commits and grew by 3 lines each,
**entirely in their class docstrings**, which all four rounds corrected.
The `pdsfile.py` figure is unchanged since the extraction, and no executable line
in either new module has changed since its extraction commit — which the five
identical head pairs in §3 measure rather than assert.

### 6. Cross-block calls — enumerated, and every one an attribute lookup

A call that went through a **module-level name** rather than through
`self.`/`cls.` would break at the split, and it is the one way this move fails
silently. Measured over the AST:

**Associations → sorting, 3 sites, all `cls.`:** `associated_logical_paths` →
`cls.logicals_for_abspaths`; `associated_pdsfiles` → `cls.pdsfiles_for_abspaths`;
`associated_abspaths` → `cls.abspaths_for_logicals`.
**Sorting → associations: none.** The dependency runs one way.

**Within `_sorting.py`, 14 sites** — every `Attribute` node in the module whose
name is one of its own 23, counted individually — all `self.`/`cls.` (12) or an
attribute on a `PdsFile`-valued expression (the other two: `parent.sort_basenames`
in `sort_sibnames`, `pdsf_dict[path].sort_basenames` in `sort_logical_paths`).
**Within `_associations.py`, 5 sites**, all `self.`: `associated_abspaths` is
called by `associated_logical_paths`, by `associated_pdsfiles` and twice by
itself, and `associated_parallel` once by `associated_abspaths`.

(No line numbers are given for any of these, for the reason §5 gives: a docstring
fix in a later review round moves every line number in these two files, and one
did.)

**Core → moved, 11 sites**, all `self.`/`cls.`/`parent.`: `_info`
(`basename_is_viewable`), `all_versions` (`pdsfiles_for_abspaths`), `childnames`
(`sort_basenames`, twice), `is_viewable`, `islabel`, `local_viewset`, `split`,
and `viewset_lookup` three times — including
`parent.viewable_childnames_by_anchor` and `parent.pdsfiles_for_basenames`,
the two the brief flags.

**Sibling mixins → moved, 3 sites**: `_index_rows.py:163` `self.sort_basenames`;
`_opus.py:105` `cls.pdsfiles_for_abspaths` and `:244`
`pds_class.pdsfiles_for_abspaths`. **Maintenance tools → moved, 2 sites**:
`pdsindexshelf.py:466` and `pds4indexshelf.py:452`, both
`pdsfile.Pds3File`/`Pds4File.pdsfiles_for_abspaths` — attribute access on a class
object.

**Bare module-level references to a moved name: zero**, inside the moved bodies
and in module-level code outside the class alike. Every reference to any of the
27 names, anywhere in `src/`, is an attribute access, so all of them are runtime
MRO lookups and the split is transparent to them. None of the seven mixin modules
imports another.

### 7. Base order and the mixin harness

```python
class PdsFile(_AssociationsMixin, _DerivedPathsMixin, _IndexRowsMixin, _LocalFsMixin,
              _OpusMixin, _ShelfMixin, _SortingMixin, object):
```

Alphabetical by mixin class name with `object` last, per
`plans/2026-07-27-addendum-phase5-mixin-base-order.md` (owner, 2026-07-27) and
enforced by
`tests/api/test_mixin_collisions.py::test_the_mixin_bases_are_listed_alphabetically`,
which was run first, before anything else, and at every commit. The Phase-5
preamble's illustration on this branch shows a different order; it was corrected
by PR #110, which merged to `rewrite` **after** this stack branched, so merging
`rewrite` forward to obtain it would drag #110's diff into this PR. The addendum
is the authority here.

`_AssociationsMixin` sorts before every existing mixin and `_SortingMixin` after
every existing one, so the first move commit appended its base at the end of the
list and the second inserted its base at the front; neither commit disturbed what
the other wrote.

**This PR changes `PdsFile.__bases__[0]`, which is the one thing in the class
shape that any code actually reads**, so it is measured rather than argued.
`_index_rows.py:254` sniffs `cls.__bases__[0].__name__ == 'Pds4File'` (deferred
entry 49), and `tests/api/test_mixin_collisions.py:72` pins only `__bases__[-1]`.
Dumping `__bases__[0].__name__`, the full `__bases__` tuple, the full MRO and the
sniff's own verdict for all **34** classes in the hierarchy, on the parent tip
and at HEAD:

| Property | Classes where parent and HEAD differ |
|---|---|
| `__bases__[0].__name__` | **one**: `PdsFile` itself, `_DerivedPathsMixin` → `_AssociationsMixin` |
| the sniff's verdict (`… == 'Pds4File'`) | **none** — `True` for exactly the same six pds4 rule classes on both sides |
| `__bases__` tuple | **one**: `PdsFile` itself, which gains the two mixins |
| MRO | all 34, and only by the insertion of `_AssociationsMixin` and `_SortingMixin` |

`cls` in that sniff is `type(self)`, a *rule* subclass, and no rule subclass's
first base moves — only `PdsFile`'s does, and `PdsFile` is not one of the six the
sniff answers `True` for, on either side. The MRO row is why the check had to be
run rather than reasoned: every MRO changes, and only the property the sniff
actually reads does not.

The harness **discovers** its subjects from `PdsFile.__bases__`, so it picked up
both new mixins for free and this PR edits no test file. At HEAD it reports seven
mixins defining 4, 12, 5, 5, 3, 9 and 23 names respectively.

**The mixin/subclass intersection was re-measured before a line was written,
because a non-empty result is a hard stop rather than something to resolve in the
PR** (§4.1 of the brief; deferred entry 48's check is strict). Using the test's
own `_defined_names` helper, which drops the eight structural names:

| | 27 moved names |
|---|---|
| `Pds3File` (76 own names) | **empty** |
| `Pds4File` (50 own names) | **empty** |
| all 33 classes in the subclass hierarchy, rule modules included | **empty** |
| `PdsFile`'s own body | **empty** |

Re-measured at HEAD after the move: still empty on every row.

### 8. Ruff ratchet — 18 codes, every one conserving, none gained

Procedure: for every code in `pdsfile.py`'s entry, the following was run against
the parent's `pdsfile.py`, this branch's `pdsfile.py`, `_sorting.py` and
`_associations.py` —

```
ruff check --no-cache --isolated --output-format concise --select <code> \
           --line-length 100 --target-version py310 <file>
```

`--isolated` drops `pyproject.toml`'s `line-length = 100` and would otherwise
report an E501 at 88 columns that the project config does not, so the two
settings are restored explicitly (PR-16 §7 through PR-19 §8 record the same
trap), and `--output-format concise` is required because ruff 0.15's default
output no longer starts a line with the file path.

**Every one of the 18 codes conserves exactly** — parent count = the three
post-move counts summed. Only the two rows that move are non-trivial:

| Code | parent `pdsfile.py` | → `pdsfile.py` | `_sorting.py` | `_associations.py` |
|---|---|---|---|---|
| E701 | 11 | **10** | 1 | 0 |
| RUF005 | 6 | **2** | 4 | 0 |
| UP024 | 10 | **9** | 0 | 1 |
| B904, C405, E501, E713, E721, F841, I001, N806, RUF012, SIM102, SIM114, SIM118, UP004, UP015, UP031 | 3, 3, 5, 1, 1, 5, 2, 2, 16, 1, 2, 1, 1, 1, 9 | unchanged | 0 | 0 |

The **total number of suppressed violations is unchanged at 80**: 80 on the
parent's `pdsfile.py`, and 80 summed over this branch's `pdsfile.py`,
`_sorting.py` and `_associations.py`. The distinct (file, code) pairs move
18 → 18 + 2 + 1.

The **converse** check matters as much and is easy to skip: running the project's
whole select set (`E,F,W,I,UP,B,SIM,C4,A,N,PT,RUF` minus the three project-wide
ignores) against each new module with **no** per-file entry reports exactly the
codes its entry lists and nothing else — `E701` + `RUF005` for `_sorting.py`,
`UP024` for `_associations.py`. So neither module needs a code that was not
already forgiven for these same lines; had either needed one, the sub-plan makes
that a §6.4 hard stop.

Resulting entries:

| File | Entry | Note |
|---|---|---|
| `src/pdsfile/pdsfile.py` | 18 codes | unchanged — it still triggers every one of them |
| `src/pdsfile/_sorting.py` | `["E701", "RUF005"]` | exactly the codes its moved lines trigger |
| `src/pdsfile/_associations.py` | `["UP024"]` | exactly the code its moved lines trigger |

**`pdsfile.py`'s entry does not shrink, and that is a measurement, not an
oversight.** This is the largest block the phase moves, so the sub-plan expected
some code to leave; none did. All 18 still occur among the 3,837 lines that
remain — the closest calls are `RUF005`, down from 6 to 2, and `E713`, `E721`,
`SIM102`, `SIM118`, `UP004` and `UP015`, which sat at 1 before the move and still
sit at 1. So there is no PR-23 note to add.

**Neither new module needs `I001`.** `_sorting.py`'s three-name `from
._path_utils import …` was first written in the parenthesized multi-line form the
old header used, which ruff's isort reports as unformatted; it was written on the
single line ruff wants instead — a choice about *new* code in the module header,
not a restyle of a moved body — so the entry is one code smaller than it would
otherwise have been.

### 9. The tests that pin this code — measured, not assumed

A coverage run of `tests/pds3file/`, `tests/pds4file/`, `tests/rules/`,
`tests/core/` and `tests/holdings_maintenance/` with
`dynamic_context = test_function` attributes **224 distinct test functions** to
the two new modules, from **20 test modules**: 4 under `tests/pds3file/`, 1 under
`tests/pds4file/`, 15 under `tests/rules/`. **No `tests/holdings_maintenance/`
context appears**, for the reason PR-18 established: PR-13's harness runs each
tool as a subprocess that in-process coverage does not follow, which is also why
`pdsindexshelf.py`'s and `pds4indexshelf.py`'s calls to `pdsfiles_for_abspaths`
are invisible here. **No `tests/core/` context appears either.**

| Method | Contexts | Test modules |
|---|---|---|
| `split_basename` | 208 | 20 — every module that reaches either mixin |
| `basename_is_label` | 62 | 18 |
| `basename_is_viewable` | 20 | 15 |
| `sort_basenames` | 22 | 5 |
| `sort_sibnames` | **0** | — |
| `sort_siblings` | **0** | — |
| `sort_logical_paths` | 1 | `pds3file.test_pds3file_blackbox` |
| `sort_childnames` | 1 | the same |
| `viewable_childnames` | 1 | the same |
| `childnames_by_anchor` | 4 | 3 |
| `viewable_childnames_by_anchor` | 4 | 3 |
| `abspaths_for_pdsfiles` | 2 | 2 |
| `logicals_for_pdsfiles` | 17 | 17 |
| `basenames_for_pdsfiles` | 3 | 2 |
| `pdsfiles_for_abspaths` | 36 | 16 |
| `logicals_for_abspaths` | 16 | 16 |
| `basenames_for_abspaths` | 2 | 2 |
| `pdsfiles_for_logicals` | 3 | 2 |
| `abspaths_for_logicals` | 31 | 16 |
| `basenames_for_logicals` | 2 | 2 |
| `pdsfiles_for_basenames` | 6 | 3 |
| `abspaths_for_basenames` | 2 | 2 |
| `logicals_for_basenames` | 2 | 2 |
| `associated_logical_paths` | **0** | — |
| `associated_pdsfiles` | **0** | — |
| `associated_abspaths` | 26 | 15 |
| `associated_parallel` | 14 | 10 |

**Four methods have zero in-process coverage**, and none of the four is an
artifact of the subprocess blindness above — nothing in the suite calls them at
all, which a grep of `tests/` for each name independently confirms (zero call
sites for all four). All four are live consumer API: rms-viewmaster calls
`associated_pdsfiles` at 7 sites and `sort_siblings` at 1, and `sort_siblings`
is the only caller of `sort_sibnames`. Recorded as deferred observation 55, not
fixed here: this PR's gate is the pass/fail set and a new test id is movement.

### 10. Negative controls — which parts of the moved code the net actually pins

Every check below is a mutation of the **moved** code, run against
`tests/pds3file/ tests/pds4file/ tests/rules/pds3/ tests/rules/pds4/
tests/core/` in `--mode ns`, which is **721 passed / 34 skipped** unmutated.

**The harness has a trap in it, and it is avoided by construction.**
`pyproject.toml` sets `pythonpath = [".", "src"]`, which pytest resolves against
**rootdir** and inserts at the front of `sys.path` — **ahead of `PYTHONPATH`**.
So mutating a copy of `src/` and pointing `PYTHONPATH` at it from the repo root
imports the *unmutated* tree, and every control reports green, which reads
exactly like "the tests do not reach this code" and is in fact "the harness does
not reach the mutation". PR-18 fell into this and re-ran all seven of its
controls. Each mutation here is therefore written into a **full copy of the
working tree**, pytest is run **from inside that copy**, and an extra
`conftest.py` there prints `pdsfile.pdsfile.__file__`,
`pdsfile._sorting.__file__` and `pdsfile._associations.__file__`, which the
harness asserts all point into the mutated copy. **All 41 controls -- the 35 in this section and the six in §11 -- carry that
assertion, and every one of them passed it.**

**Of the 35 controls in this section, 23 turned tests red** -- 19 mutations of
moved code and four of the mixin harness:

| Mutation | Result |
|---|---|
| `basename_is_label` always returns False | **16 failed**, 15 test functions |
| `basename_is_viewable` always returns False | **12 failed**, 7 test functions |
| `sort_basenames` sorts in reverse | **8 failed**, 8 test functions |
| `sort_logical_paths` sorts each directory plainly instead of by `sort_basenames` | **1 failed** |
| `sort_childnames` reverses its answer | **1 failed** |
| `viewable_childnames` returns `[]` | **1 failed** |
| `childnames_by_anchor` matches a corrupted anchor | **5 failed**, 4 test functions |
| `logicals_for_pdsfiles` corrupts each path | **27 failed**, 16 test functions |
| `basenames_for_pdsfiles` corrupts each basename | **2 failed** |
| `pdsfiles_for_abspaths` truncates to one | **9 failed**, 5 test functions |
| `logicals_for_abspaths` corrupts each path | **30 failed**, 16 test functions |
| `basenames_for_abspaths` corrupts each basename | **2 failed** |
| `abspaths_for_logicals` corrupts each path | **26 failed**, 17 test functions |
| `basenames_for_logicals` corrupts each basename | **1 failed** |
| `abspaths_for_basenames` corrupts each path | **1 failed** |
| `logicals_for_basenames` corrupts each path | **1 failed** |
| `associated_abspaths` truncates the de-duplicated answer to one | **25 failed**, 13 test functions |
| `associated_abspaths` truncates its `glob_glob` result to one | **8 failed**, 5 test functions |
| `associated_parallel` never takes its `rank is None` branch | **5 failed**, 3 test functions |
| the base order is no longer alphabetical | **1 failed** — `test_the_mixin_bases_are_listed_alphabetically`, and nothing else |
| `_AssociationsMixin` also defines `viewable_childnames_by_anchor` | **2 failed** — `test_no_two_mixins_define_the_same_name` and `test_every_mixin_name_is_reachable_through_pdsfile` |
| `Pds3File` itself defines `associated_parallel` | **1 failed** — `test_no_mixin_is_shadowed_by_a_pdsfile_subclass[Pds3File]`, and nothing else |
| `PdsFile`'s own body redefines `sort_basenames` | **2 failed** — `test_no_mixin_is_shadowed_by_pdsfile_itself` and `test_every_mixin_name_is_reachable_through_pdsfile` |

A twenty-fourth harness mutation is worth its own line because it does not
produce failures: making `_AssociationsMixin` define `sort_basenames` — a name
`PdsFile.childnames` calls during fixture setup — turns the whole module into
**15 errors** with `TypeError: _AssociationsMixin.sort_basenames() got an
unexpected keyword argument 'labels_after'` at `pdsfile.py:1367`. That is the
collision being caught by the interpreter before the check can report it, so the
quieter variant above is the one that demonstrates the check itself.

**Eleven mutations changed nothing, and they are reported rather than dropped.**
A control that comes back green is a measurement too, and they fall into two
distinct classes:

*(a) nothing calls the method — matches §9's zero-context rows exactly:*

| Mutation | Result |
|---|---|
| `sort_sibnames` reverses the list it hands to `parent.sort_basenames` | 721 passed |
| `sort_siblings` truncates the basenames it sorts | 721 passed |
| `associated_logical_paths` truncates its answer to one | 721 passed |
| `associated_pdsfiles` truncates its answer to one | 721 passed |

*(b) the method is covered, but no assertion catches the change:*

| Mutation | Result | Why |
|---|---|---|
| `split_basename` corrupts the three-group `BUNDLENAME_PLUS_REGEX` return | 721 passed | that branch needs a bundle name whose split rule leaves it unchanged; 208 contexts reach the method and none reaches this return |
| `sort_basenames` inverts the `labels_after` sort key | 721 passed | the `labels_after=True` branch is not reached by any golden case |
| `viewable_childnames_by_anchor` truncates to one | 721 passed | its 4 contexts all come through `viewset_lookup`, which never checks the length |
| `abspaths_for_pdsfiles` truncates its `must_exist=False` branch | 721 passed | the two tests assert `for path in res: assert path in expected` — a subset, never a length |
| `pdsfiles_for_logicals` truncates to one | 721 passed | same subset-assertion shape, in both of its tests |
| `pdsfiles_for_basenames` truncates to one | 721 passed | its 6 contexts all arrive through `viewset_lookup` |
| `associated_parallel` returns a path from its `# This should never happen` line | 721 passed | that line is, as its comment says, not reached |

Class (b) is one finding stated seven ways: **several of these tests assert that
every value returned is expected, and never that everything expected was
returned**, so a truncation is invisible to them. That is a property of the test
suite, not of this PR, and this PR may not fix it — its gate is the pass/fail set
and strengthening an assertion is out of scope (common brief §5.1). Recorded as
deferred observation 56.

### 11. The monkeypatch audit — the check the set diff cannot perform

Deferred entry 29 (opened by PR-16's round-1 Major, owned by "PR-17 onward") says
an extraction sweep must also ask **which namespaces the tests patch**, not only
which globals the code reads. A test whose patch lands on a module the moved code
no longer resolves through keeps passing while exercising nothing, and §6.2's
outcome-set diff compares pass/fail — so it is *structurally blind* to this class
of defect. **This PR's set diff is empty, and it would have been empty in every
one of the cases below, including a broken one.**

**Enumeration.** Every `monkeypatch.setattr` / `setitem` / `delattr` / `setenv` /
`delenv`, `mock.patch`, `patch(`, `patch.object` and bare `setattr(` in `tests/`
and `scripts/` — 20 sites, all `monkeypatch`; the tree still uses no
`unittest.mock` at all:

| Target | Sites | Names a symbol **this PR** moves? | Does this PR's moved code reach it? |
|---|---|---|---|
| `Pds3File.CACHE` (`tests/core/conftest.py:28`, `test_pdsfile_caching.py:112,126`) | 3 | no — a class attribute that stays on the class | not directly; `associated_parallel` reaches the cache through `self._recache()`, which stays in core |
| `Pds3File.preload` (`test_pdsfile_caching.py:127`) | 1 | no — PR-21's symbol | no |
| `Pds3File`/`Pds4File.LOCAL_PRELOADED`, `.LOCAL_HOLDINGS_DIRS` (`test_pdsfile_path_resolution.py:58,59,71,72,85,86`) | 6 | no — class attributes that stay on the classes | **indirectly** — `abspaths_for_logicals` calls `abspath_for_logical_path`, which reads them |
| `Pds3File.shelf_path_and_key_for_abspath` (`test_pdsfile_path_resolution.py:120,129,137,155`) | 4 | no — PR-17's symbol, audited there | no |
| `abspath_for_logical_path.__globals__['glob']` (`test_pdsfile_path_resolution.py:92`) | 1 | no — PR-16's fix site, on `_path_utils`'s globals | **yes** — `abspaths_for_logicals` calls that same function object |
| `pdsviewable.ICON_SET_BY_TYPE` (`test_pdsviewable_iconset_for.py:47`) | 1 | no — different module | no |
| `monkeypatch.setenv` / `delenv` (`test_pdsfile_path_resolution.py:54,70,83,84`) | 4 | no — environment, not a namespace | no |

**No patch site names any of the 27 methods.** A regex over `tests/`, `scripts/`
and `src/` for *direct assignment* to any of the 27 — the form that is not a
`monkeypatch` and is easy to miss — returns **zero** hits for all 27 names, and
no test assigns to any attribute of `pdsfile.pdsfile`.

**Every one of the six patch mechanisms was forced to answer wrongly in a
full-tree copy, and each turned its own test red:**

| Forced-wrong control | Went red |
|---|---|
| the `glob` stub in `abspath_for_logical_path.__globals__` answers non-empty | `TestHoldingsEnvironmentVariable::test_a_class_does_not_borrow_another_class_holdings_root` |
| `LOCAL_PRELOADED` stubbed to a non-empty list | the same id |
| `shelf_path_and_key_for_abspath` returns instead of raising | **4 failed**, 3 ids across `TestInfoshelfPathAndKey` |
| the `Pds3File.CACHE` patch removed | `TestGetPermanentValues::test_caching_is_resumed_after_the_values_are_read` |
| the `Pds3File.preload` patch removed | `TestGetPermanentValues::test_caching_is_resumed_after_a_missing_value_triggers_a_reload` |
| the `pdsviewable.ICON_SET_BY_TYPE` patch removed | **9 failed**, 6 ids across `TestIconsetFor` |

Six controls cover all 20 sites, because sites sharing a target share a
mechanism. Every one asserted the file it imported, as §10 describes.

**PR-16's fix shape is confirmed move-proof a second time.**
`test_pdsfile_path_resolution.py:92` patches `abspath_for_logical_path.__globals__`
— the function's *own* namespace, whichever module that is — rather than
`pdsfile.pdsfile.glob`. `abspaths_for_logicals` now lives in `_sorting.py` and
still calls the same function object, so the patch reaches exactly what it
reached before. Had the test patched `pdsfile.pdsfile.glob`, PR-16's move would
already have silenced it.

**Entry 29's second half — rebinding re-exported *data*.** The same asymmetry one
level down, measured on both sides:

| | parent `bf42ae7` | this branch |
|---|---|---|
| namespace the 27 methods resolve through | `pdsfile.pdsfile` | `pdsfile._sorting` / `pdsfile._associations` |
| namespace `os`, `_clean_join`, `_needs_glob`, `abspath_for_logical_path`, `logical_path_from_abspath` resolve in, for the moved code | `pdsfile.pdsfile` | the new modules |
| rebinding `pdsfile.pdsfile.os` reaches `basenames_for_abspaths` | **yes** | **no** |
| `pdsfile.pdsfile.os` / `._clean_join` / `._needs_glob` / … still bound | yes | yes |

Nothing in `src/`, `tests/`, `scripts/`, rms-opus or rms-viewmaster rebinds any of
those five module attributes — greped, zero hits — so nothing is broken today.
The general observation stands for PR-21 and PR-22 and stays in
`critiques/deferred-observations.md` as entry 29.

### 12. Consumer smoke — outcome unchanged, and this is the PR where it matters most

The gate is **same outcome as baseline**, not "passes"
(`critiques/baselines/consumer-smoke-baseline.md`).

| Check | Baseline | This branch |
|---|---|---|
| A — rms-opus import paths | 4/4 resolve, 0 failures | **4/4 resolve, 0 failures** |
| B — rms-viewmaster startup | 5 ok, 3 pre-existing failures | **5 ok, 3 failures — the same three** |

The three Check-B failures are still `pdsfile.cache_lifetime` (raises),
`pdsfile.DEFAULT_CACHING` (absent) and the same `cache_lifetime` read inside
`get_page_cache()`. None became a pass. `pdsfile.pdsfile.repair_case` still
resolves.

**rms-viewmaster uses this PR's surface more heavily than any other Phase-5
PR's** — 37 call sites across twelve of the 27 moved names, counted after
excluding comments and generated `docs/_build/` output:

| Name | rms-viewmaster — call sites | rms-opus — call sites |
|---|---|---|
| `sort_basenames` | 9: `pdsgroup.py:314,368,586,591`, `pdsgrouptable.py:362`, `pdsiterator.py:277,284,415,474` | — |
| `associated_pdsfiles` | 7: `viewmaster.py:844,1039,1047,1258,1433,1444,1547` | — |
| `associated_parallel` | 3: `viewmaster.py:841,849,861` | — |
| `logicals_for_pdsfiles` | 3: `viewmaster.py:1043,1251,1436` | — |
| `pdsfiles_for_basenames` | 3: `pdsgroup.py:597`, `viewmaster.py:1334,1454` | — |
| `logicals_for_basenames` | 3: `pdsiterator.py:286,417`, `viewmaster.py:1029` | — |
| `basename_is_label` | 2: `pdsgroup.py:324,378` | — |
| `sort_logical_paths` | 2: `pdsiterator.py:117,130` | — |
| `childnames_by_anchor` | 2: `viewmaster.py:1320,1453` | — |
| `split_basename` | 1: `pdsgroup.py:577` | — |
| `sort_siblings` | 1: `viewmaster.py:1407` | — |
| `logicals_for_abspaths` | 1: `pdsiterator.py:107` | — |
| `associated_abspaths` | — | 1: `do_import.py:596` |

Every one of them is an attribute access on the class or on an instance
(`pdsf.sort_basenames(...)`, `query_pdsfile.associated_pdsfiles(...)`,
`Pds3File.logicals_for_pdsfiles(...)`), so each resolves through the MRO and the
mixin move is invisible to it — which is what the byte-identical API dump in §4
is the formal statement of, and what Check A and Check B confirm at run time.
Two of these names — `associated_pdsfiles` and `sort_siblings` — are among §9's
zero-coverage four, so for them the consumer smoke is the only thing that
exercised them at all in this PR.

Environment note carried from the baseline: the check ran under the pdsfile
venv's interpreter with rms-viewmaster's `site-packages` appended to
`PYTHONPATH`, because that venv lacks pdsfile's declared `range_ex` dependency,
and with the holdings environment variables set — without them `create_app()`
exits and the run reports 3 ok / 5 failures, which is a harness artifact and not
a result. rms-viewmaster is at `a0d05e2`; rms-opus is at `73cb6de7`.

### 13. Clean install

`scripts/clean_install_check.sh` passes inside `run-all-checks.sh`. Both new
modules are picked up by the existing `include = ["pdsfile*"]` package glob with
no packaging change, and the gate imports the whole manifest module surface —
`pdsfile.pdsfile` among them — which cannot succeed if either is missing from the
distribution.

### 14. The two class docstrings are derived, and verified in both directions

Deferred entry 54 records that the mixins' "state contract" docstrings are
hand-written, drift, and are mechanically derivable; PR-19's rounds 1, 2 and 3
each found one wrong. The entry asks for the derivation to become a *test* and
assigns that to PR-22. This PR does not build the test — it is not in its
deliverables — but it applies the method by hand, in the widened form PR-19's
rounds 3 and 4 settled: walk **every** `ast.Attribute` node rather than only
`self.X`/`cls.X`, scope the claim to the receivers that hold a `PdsFile` object
or the `PdsFile` class, and **exclude the names the mixin itself defines**.

The receiver list is printed in full so the scoping is checkable rather than
asserted: `_SortingMixin`'s PdsFile-side receivers are `self`, `cls`, `parent`,
`p`, `pdsf` and `pdsf_dict[path]`, against 26 others that are strings, lists,
dicts, regex match objects, translators, the logger or `os.path`;
`_AssociationsMixin`'s are `self`, `cls`, `parent`, `pdsf`, `new_root` and
`old_root`, against 12 others.

**Direction 1 — every PdsFile-side name the code reaches appears in the
docstring: 22 of 22 for `_SortingMixin`, 34 of 34 for `_AssociationsMixin`,
nothing missing on either side.** Direction 2's residue is prose only, and it is
re-derived at every round rather than described once: at HEAD it is the five
sibling-mixin class names, the four sort-config setters the docstring says
explicitly do *not* move, the `<plural>_for_<plural>` naming pattern, the two
exception names `AttributeError` and `TypeError`, the label `WRITTEN`, and the
words `None`, `So` and `Either`.

One claim in `_SortingMixin`'s first draft was written rather than measured and
was wrong before it was committed: it said `sort_basenames` *and* `sort_sibnames`
reach `os_path_isdir` and that `pdsfiles_for_basenames` reaches `os_path_exists`.
Measured, `sort_basenames` alone reaches `os_path_isdir`, and
`logicals_for_abspaths`, `basenames_for_abspaths` and `abspaths_for_logicals`
reach `os_path_exists`. The docstring says the measured thing.

Both docstrings also record something the derivation surfaced and the phase had
not previously written down: **four class attributes `_SortingMixin` reads
(`BUNDLENAME_PLUS_REGEX`, `BUNDLESET_PLUS_REGEX`, `BUNDLESET_PLUS_REGEX_I`,
`LBL_EXT`) and one `_AssociationsMixin` reads (`IDX_EXT`) are defined only on
`Pds3File` and `Pds4File`, not on `PdsFile`.** So those methods work on a
subclass instance and not on a bare `PdsFile`. That is pre-existing behavior —
the same lookup failed the same way before the move — and it is recorded rather
than changed.

### 15. Deferred observations

Entry 29 is the one this PR was told to act on, and §11 is the action. It is
**not** resolved — it is a per-PR step, owned by "PR-17 onward" — so it stays open
for PR-21 and PR-22. **Entries 53 and 54 are deliberately not taken up**, even
though 53's text names PR-20 as its owner: the coordinator directed that both stay
open and that this PR build no new check, which is the common brief §5.1 rule
written after PR-17 spent two rounds on a voluntarily adopted Deferred item. This
PR touches no test file at all, which is also what makes its set diff empty.
Entry 53 is annotated with that direction so the next reader does not think it was
overlooked. Entry 42 (the back-import guard, owner PR-22) is untouched: this PR
adds two mixin modules and §5 shows both are clean by the same parsing check, but
it builds no guard. No other entry in 1–54 is resolved or invalidated here.

Two entries are **added** by the executor's own measurements: **55** (four moved
methods — `sort_sibnames`, `sort_siblings`, `associated_logical_paths`,
`associated_pdsfiles` — have zero in-process test coverage while rms-viewmaster
calls two of them at eight sites) and **56** (the subset-shaped assertions in the
`tests/pds3file/` transformation tests, which cannot see a truncated answer, and
the six other measured coverage gaps §10's green controls found).

### 16. Review loop

| Round | Verdict | Findings | Record |
|---|---|---|---|
| 1 | goal met | 0 Major, 8 Minor (all accepted; one fixed in `src/`, seven in this record and the sub-plan), 0 new Deferred | `critiques/pr-20/round-1.md` |
| 2 | goal met | 0 Major, 7 Minor (all accepted; two fixed in `src/`, five in this record and the sub-plan), 1 Deferred (entry 57 added) | `critiques/pr-20/round-2.md` |
| 3 | goal met | 0 Major, 4 Minor (all accepted; one fixed in `src/`, three in this record and the deferred-observations file), 3 Deferred (two are confirmations; the third folds into entry 57) | `critiques/pr-20/round-3.md` |
| 4 | goal met | **0 Major, 0 new Minor**; all 20 prior findings confirmed resolved by re-measurement; 4 Deferred (three fixed in place here, one declined) | `critiques/pr-20/round-4.md` |

*(Rows are written only after the round they describe has run and its record file
exists on disk — the rule PR-18's round-3 Major established. No row is written
for a round that has not run.)*

**Round 1 found no Major and eight Minor, and six of the eight were counts stated
rather than measured** — the same failure shape PR-19's four rounds produced
thirteen times. They were: core call sites given as 12 (measured 11); the two
within-module counts computed under two different rules in one sentence (measured
14 and 5); sibling-mixin sites given as 2 in the sub-plan while the record already
said 3; "the two in-class banner comments" when three moved; "a three-line commit"
for a four-line one; and deferred entry 56's "other four" green controls when the
clause itself named five. Each was re-measured by the executor before being fixed,
and each measurement reproduced the finding.

The seventh added the measurement §7 was missing, and it is the one that mattered:
**this PR changes `PdsFile.__bases__[0]`**, which `_index_rows.py`'s `Pds4File`
sniff reads and which `tests/api/test_mixin_collisions.py` does not pin (it
asserts `__bases__[-1]`). The 34-class shape dump now stands in §7. The eighth was
the only fix under `src/`: `_SortingMixin`'s docstring called the module's methods
free of I/O twenty-seven lines above a paragraph naming the four that reach
`_LocalFsMixin`.

The round-1 reviewer re-derived, with its own scripts rather than reading them
here: the byte-for-byte segment comparison of all 27 definitions **and of all 110
definitions that stayed**, the API dumps, the four junit reductions and both set
diffs, the `measured_files` non-vacuity argument, the ratchet conservation and its
converse check, the whole of §9's per-test-context table, the consumer call-site
counts, both docstring contracts in both directions, and the mixin/subclass
intersections.

**Round 2 found seven more and still no Major**, and the useful signal is that
**the two that were in `src/` were both prose about runtime behavior that had been
written rather than executed**. `_SortingMixin`'s closing paragraph said
`split_basename` and `basename_is_label` are the methods that need a subclass
instance. Measured by AST the readers are `split_basename`
(`BUNDLENAME_PLUS_REGEX`, `BUNDLESET_PLUS_REGEX`), `basename_is_label` (`LBL_EXT`)
and **`sort_basenames`** (`BUNDLESET_PLUS_REGEX_I`); executed on a bare `PdsFile`,
the two that raise are `basename_is_label` and `sort_basenames`, and
`split_basename` returns cleanly because `SPLIT_RULES` is `None` there and it
returns before either regex. So the sentence named a method that does not fail and
omitted the one that does. The second was the contract's exhaustive out-of-scope
list, which omitted `set` and `os.path` — the only two receiver categories a
receiver-type sweep finds that the prose did not name.

Round 2's other five were record accuracy: a line count stale by one after round
1's own fix; §16 empty while `round-1.md` was already committed; the sub-plan's
promised "as executed" delta missing; "zero string literals naming any of the
three" falsified by four docstrings; and three banner citations under two
conventions. That last one was fixed by **removing** the line numbers rather than
correcting them, on the rule PR-19's round 3 established.

Its one Deferred is entry 57, and it is the only finding in this loop that reaches
outside the PR: an archived plan carries a home-rooted holdings path.

**Round 3 found four more, no Major, and one of them is the most consequential
finding of the loop** — and it is not in the extracted code either. Entry 57's
bounding measurement said "neither token is the current limited testing copy's
root … stale history rather than a live leak". That holds only under literal
string equality. Measured properly: `os.path.dirname()` of **both**
`PDS3_HOLDINGS_DIR` and `PDS4_HOLDINGS_DIR` **equals** the committed token, and
each root is that token plus exactly **one** further component. So the archived
plan does disclose the location §3.4 calls confidential, and the entry as first
written would have steered the owner wrong. It is corrected, its owner is now the
repo owner rather than "unassigned", and it is surfaced as an item needing a
decision. It is still not fixed here: it is pre-existing, identical on `rewrite`,
and outside this PR's diff.

Round 3's other three: seven stale line numbers in §6 — the same defect round 2's
own Minor 7 had just stripped out of §5, one section up, so §6 now names its
callers and gives no line numbers either; §16 missing the round-2 row while
`round-2.md` was already committed, the second time that section lagged its own
rule; and `_AssociationsMixin`'s round-2-corrected paragraph still saying "the line
above" for a read thirteen lines away and "neither method … they" with one method
named. The third is the only round-3 fix under `src/`.

**Every finding in all three rounds has been a statement in a record, a sub-plan
or a docstring, and not one has been in the extracted code** — which is the same
result PR-19's four rounds produced, and is the strongest evidence available that
the extraction itself is clean.

**The loop terminates at round 4**, at §6.6's four-round cap: a fresh reviewer
returned zero Major and no new un-rebutted Minor. Round 4 is the *scoped*
re-review the anti-thrash rule prescribes — confirm the prior rounds' findings are
resolved, raise only new Major — and it confirmed all twenty by re-measuring each
rather than reading this record: it re-ran the 34-class shape dump, **executed**
the docstrings' runtime claims on a bare `PdsFile` in both modules, re-derived the
byte equivalence for the 27 moved **and the 110 that stayed**, the API dump, the
ratchet conservation, **all ten junit reductions** (matching the committed `.set`
files in every case), the provenance counts, the `symtable` sweep, both docstring
contracts, the consumer call-site table, and the no-holdings job — and it swept
for line numbers into the two new modules to confirm none had gone stale a second
time.

**It also checked four mixin-move hazards nothing else in this PR had checked**,
and all four are clean: no `super()`, no `__class__`, no `__`-name-mangled
attribute and no `getattr`/`hasattr`-by-string reference to any of the 27 anywhere
in `src/`. Those are the four ways moving a body into a different defining class
can change its meaning; their absence is a stronger statement than byte
equivalence alone, and it is recorded here because it is the check this PR would
otherwise have shipped without.

Its four Deferred items are all corrections to text this PR itself wrote, and
three are fixed in place rather than carried forward: §14's residue list named a
phrase round 1 had already deleted and omitted two rounds 2 and 3 had added;
`_AssociationsMixin`'s out-of-scope receiver list omitted `os.path`, the same
defect round 2 fixed in `_SortingMixin`'s twin sentence and did not carry across;
and §5's byte convention (segment without its trailing newline) was uniform but
unstated. The fourth — that §5 cites parent-tip line numbers and §10 a HEAD one —
is left as it is: §5 documents the parent-tip windows and renumbering half of it
would make it disagree with what it exists to record.

**Nothing was rebutted in any round.** All 19 Minor findings across rounds 1–3
were accepted and fixed, which is worth stating: there was no scope-creep finding
to push back on and no disagreement to escalate.

## PR-21 — `refactor: extract preload machinery → _preload.py`

**Branch:** `pr-21-preload`, based on `pr-20-associations-sorting` @ `2df25ab`
("docs: note that round 4's fix leaves the full-data record fresh"), opened
against that branch, not `rewrite`
(`plans/2026-07-27-addendum-phase5-stack-extension.md`).
**Baseline:** **PR-20's recorded post-move set** — its §3 above, `--mode ns` 848
passed / 34 skipped (882 ids) and `--mode s` 555 passed / 3 skipped (558 ids),
no-holdings 82 passed / 800 skipped — **re-measured locally on the parent tip**
with this PR's own command lines rather than copied from the table. The
re-measurement reproduced it exactly.
**Date:** 2026-07-27
**Sub-plan:** [`plans/2026-07-27-pr-21-subplan.md`](../plans/2026-07-27-pr-21-subplan.md)

This PR has two coupled deliverables, and only the first is the mixin extraction
the four PRs before it did. The second turns an existing **public** module,
`preload_and_cache.py`, into a re-export shim. Its set diff is **empty in both
modes**; it touches no test file and adds no test id.

### 1. Environment

| Item | Value |
|---|---|
| Interpreter | CPython 3.12.3, repo venv, `pip install -e ".[dev]"` |
| Holdings | `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` + `PDSFILE_TEST_HOLDINGS=full`, pointed at the limited testing copy the goldens are tuned to |
| Baseline tree | a `git worktree` detached at the parent tip `2df25ab`, same interpreter, same holdings; `pytest` reports that directory as `rootdir` |
| Command lines | exactly those in `scripts/automated_tests/pdsfile_main_test.sh` (serial, under `coverage`), plus `-rA --junitxml`; the holdings variables come from the same `source ~/pdsfile_runner_secrets` that script uses, so no root is written anywhere |

**Which source each run actually imported, proved rather than assumed.** The
interpreter is the main tree's venv, whose editable install appends
`<main tree>/src` to `sys.path`, and there are now **seven** stacked branches
sharing it, so a worktree run could silently measure the wrong tree and make the
whole comparison vacuous. Each run wrote its own `COVERAGE_FILE`, and
`coverage.CoverageData.measured_files()` was read afterwards for its **absolute**
paths:

| Run | top-level `pdsfile` modules measured | count |
|---|---|---|
| baseline | `<worktree>/src/pdsfile/` — `__init__`, `_associations`, `_derived_paths`, `_index_rows`, `_local_fs`, `_opus`, `_path_utils`, `_shelves`, `_sorting`, `pdscache`, `pdsfile`, `pdsviewable`, `preload_and_cache` | **13** |
| this branch | `<main tree>/src/pdsfile/` — the same thirteen, plus **`_preload`** | **14** |

Those are the modules directly under `src/pdsfile/`; both runs additionally
measure the same `holdings_maintenance/`, `pds3file/`, `pds4file/` and `tools/`
subpackages, each under its own tree's prefix — **70** measured files on the
baseline side and **71** on this branch, the difference being exactly the one new
module.

Counted mechanically: **0** baseline paths fall outside the worktree prefix, **0**
head paths fall outside the main tree's, and the text `_preload` appears in **0**
baseline paths and **1** head path. Had the worktree run leaked into the main
tree's editable install, `_preload.py` would have been measured there too.

### 2. Active §2 gates

| Gate | Result |
|---|---|
| API-freeze manifest test | **passed** — and the dumped surface is byte-identical to the parent's, 733,876 bytes each, same MD5 `442428da…`; §4 |
| Full-data suite, both modes | **passed** — **empty set diff in both modes**; §3 |
| `ruff check src/pdsfile tests scripts` | **passed**; the ratchet **shrank** by one code and gained none — §8 |
| Clean-install import check | **passed** (throwaway venv, `pip install .`, full module surface imports, `pdsfile.preload_and_cache` among them) |
| Hosted lint/no-holdings job (`scripts/run-all-checks.sh`, no holdings env vars) | **passed**, **82 passed / 800 skipped** — the parent's figure, unchanged, and re-measured on the parent tip in the same session to confirm it |
| Adversarial review loop | `critiques/pr-21/round-<k>.md` |

### 3. Full-data suite — an empty diff in both modes

Both passes were run on the parent tip and on this branch's head with the same
interpreter and the same holdings. Every `testcase` element of each `--junitxml`
was reduced to one `outcome<TAB>classname::name` line, sorted, and the two files
were diffed with `diff -u`.

| Run | parent `2df25ab` | `pr-21-preload` | set diff |
|---|---|---|---|
| `--mode ns` | 848 passed / 34 skipped (882 ids) | 848 passed / 34 skipped (882 ids) | **empty** |
| `--mode s` | 555 passed / 3 skipped (558 ids) | 555 passed / 3 skipped (558 ids) | **empty** |

`diff -u` produced **zero output lines** for both modes. The parent numbers
reproduce PR-20's recorded set, which is what makes this a comparison against
PR-20's baseline rather than against a fresh unrelated measurement.

Both modes matter and both were run: `--mode s` is the only thing that exercises
the `SHELVES_ONLY` branch, and `preload` reaches it through `cls.os_path_exists`
and `cls.os_path_isdir` on every category directory of every holdings root.

**Freshness (§6.6 step 5).** The last change under `src/pdsfile/` is commit
`dd75796` ("docs: correct the mixin docstring's out-of-scope list and memcached
condition"), round 3's two-paragraph fix to `_PreloadMixin`'s docstring, at
**23:34:23**. The head runs recorded above postdate it: their `--junitxml`
timestamps are **23:37:21 and 23:39:10**. They are the regeneration §6.6 step 5
requires, and the only one this loop has needed — rounds 1 and 2 changed nothing
under `src/pdsfile/`, so their records carried forward.

The **superseded** head pair is recorded rather than dropped, with the commit its
tree was actually at:

| Head pair | `--junitxml` written | Tree at | Reduced sets |
|---|---|---|---|
| 1 | 22:08:52 / 22:10:41 | `a8f4cb3` | identical to pair 2 |
| **2 (current)** | **23:37:21 / 23:39:10** | **`dd75796`** | **the figures above** |

`diff` between the two pairs is empty in both modes, which is what a
docstring-only change should do and is measured rather than assumed. The
provenance check was re-run on the second pair: **71** measured files, **0** of
them outside the main tree's prefix, **14** directly under `src/pdsfile/`. So were
§9's and §12's statement figures: 226 statements / 43 missing / 5 excluded for the
file, and `preload` still 113 / 83 / 30 — the docstring is not a statement, and
that is checked rather than assumed.

The baseline runs (21:52:34 and 21:54:25) stand throughout: they were taken in a
detached `git worktree` at `2df25ab` that nothing has touched since.

### 4. API freeze — empty diff, as a mixin move plus a shim requires

1. `pytest tests/api/` passes — 16 ids, unchanged from the parent: the freeze test
   plus the 15 that `tests/api/test_mixin_collisions.py` contributes. This PR adds
   no id there and edits no test file.
   `tests/api/api_manifest.json`, `tests/api/manifest_allowlist.json`,
   `scripts/dump_public_api.py` and `tests/api/test_api_freeze.py` are untouched
   (§6.4) — verified with `git diff --stat 2df25ab..HEAD` over those four paths,
   which is empty. No allowlist entry was added.
2. `scripts/dump_public_api.py` was run against a worktree at the parent tip and
   against this branch's head. The two dumps are **byte-identical** (733,876 bytes
   each, identical MD5 `442428da…`, `diff` empty, both stderr streams empty).

That is the expected result for the mixin half and the plan says so: the dumper
expands a class's members with `dir(cls)`, which is MRO-wide, and records names,
kinds and signatures — never the defining class. It is **not** automatic for the
shim half: `preload_and_cache` is one of the seven fixed modules in the dumper's
`_TOP_MODULES`, and its record is built from `vars(module)`, so a name that
stopped being bound there would show up immediately. §6 measures that directly
rather than inferring it from the dump.

`pdsfile._preload` is underscore-prefixed, so the dumper skips it where the
submodule import binds it onto the `pdsfile` package; the same applies to
`_PreloadMixin` inside `pdsfile.pdsfile`. That is the freeze-invisibility the
Phase-5 preamble requires of new internal names. **This PR introduces no new
non-underscore name anywhere.**

The `__qualname__` consequence PR-18 §4 records applies here too and for the same
reason — `PdsFile.preload.__qualname__` is now `_PreloadMixin.preload`. It is a
phase-wide consequence of the mandated mixin technique, already true of the seven
mixins on the parent branch, and the dumper records `kind` and `signature`, never
a qualname.

### 5. What moved

Two source files feed one new module. Located by symbol; the plan's `:662–1079`
window is against the 6,304-line original, and `pdsfile.py` is **3,837 lines** at
the parent tip.

| From | Lines at `2df25ab` | Content |
|---|---|---|
| `pdsfile.py` | 501–503 | the `# Preload management` in-class banner |
| `pdsfile.py` | 504–919 | `get_permanent_values`, `load_volume_info`, `cache_category_merged_dirs`, `preload`, `cache_lifetime` — **5** classmethods, 419 lines with the banner |
| `preload_and_cache.py` | 6–8 | the `# Memcached and other cache support` banner |
| `preload_and_cache.py` | 10–39 | the `CACHE[...]` key-scheme documentation |
| `preload_and_cache.py` | 41–45 | `DEFAULT_FILE_CACHE_LIFETIME`, `LONG_FILE_CACHE_LIFETIME`, `SHORT_FILE_CACHE_LIFETIME`, `FOEVER_FILE_CACHE_LIFETIME`, `DICTIONARY_CACHE_LIMIT` — **5** constants |
| `preload_and_cache.py` | 47–82 | `cache_lifetime_for_class`, `is_preloading`, `pause_caching`, `resume_caching` — **4** functions |

`pdsfile.py`: 3,837 → 3,415 lines. `preload_and_cache.py`: 82 → 16.
`_preload.py`: **578**. All counted at HEAD, and **re-counted at each round rather
than carried forward** — the convention PR-19 §5 and PR-20 §5 adopted after PR-20's
round 2 found a stale one. `_preload.py` was 574 at its extraction commit and grew
by 4 lines, entirely in the class docstring, which round 3 corrected. No executable
line in it has changed since the extraction, which the two identical head pairs in
§3 measure rather than assert.

**`_preload_dir` is a nested local function inside `preload`**, not a class
method, and it moved inside `preload`'s body — it is not a separate definition in
`_PreloadMixin`, which holds exactly five.

**The block ends at `cache_lifetime`, not at the end of its banner region.**
`new_merged_dir`, `new_index_row_pdsfile`, `copy` and `__repr__` sit under the
same `# Preload management` banner and are on PR-22's explicit stay-list, so the
extraction boundary here is a *symbol* boundary. This is exactly what a mechanical
block-move gets wrong, so it is checked rather than asserted: at HEAD all four are
still members of `PdsFile`'s own body and their source segments are byte-identical
to the parent's (§5.1). So are `use_shelves_only`, `require_shelves`, `set_logger`,
`set_easylogger` and `is_logical_path`, the other stay-list names near the seam.

**The module tail stays where it is and still runs.** `pdsfile.py` still ends with
`PdsFile.SUBCLASSES['default'] = PdsFile` and `PdsFile.cache_category_merged_dirs()`,
and `pds3file/__init__.py:300` and `pds4file/__init__.py:237` make the same call
for their own classes. That call is an import-time side effect whose position
matters. Measured at HEAD rather than assumed: immediately after `import pdsfile`,
**25 of 25** categories are in `PdsFile.CACHE`, `Pds3File.CACHE` and
`Pds4File.CACHE` alike, and `inspect.getattr_static(PdsFile, 'cache_category_merged_dirs')`
now resolves to `_PreloadMixin.cache_category_merged_dirs` in `pdsfile._preload`
while `'cache_category_merged_dirs' in vars(PdsFile)` is `False`. The side effect
runs at the same point, through the mixin.

**No class-level assignment moves.** An AST pass over the `PdsFile` body reports
the window `504–919` as **5 `FunctionDef`s and 0 `Assign` nodes**. `CACHE`,
`MEMCACHE_PORT`, `DEFAULT_CACHING`, `LOCAL_PRELOADED`, `PRELOAD_TRIES`,
`DICTIONARY_CACHE_LIMIT`, `CATEGORY_LIST`, `VOLTYPES`, `EXTRA_README_BASENAMES`,
`FS_IS_CASE_INSENSITIVE` and `LOGGER` all stay on `PdsFile` (and, for `CACHE`,
`LOCAL_PRELOADED` and `DICTIONARY_CACHE_LIMIT`, on `Pds3File`/`Pds4File` where
those classes define their own). Every one of them is reached through `cls.` —
§5.2's contract lists all eleven and the AST walk that produced it found no
module-level name among them.

**Byte-for-byte equivalence, measured.** Each moved definition's exact source
segment (decorators included) was extracted from the parent commit and from
`_preload.py` at HEAD and compared byte by byte:

| Group | Definitions | Total bytes | Result |
|---|---|---|---|
| the five classmethods | 5 | 17,982 | all identical |
| the four module functions | 4 | 1,148 | all identical |

Each contiguous run also compares identical as a single blob, which additionally
rules out a reordering or a dropped blank line: the classmethods as **17,990
bytes** and the functions as **1,154 bytes**. The in-class `# Preload management`
banner compares identical as **206 bytes**, so it moved rather than being retyped.
Every byte figure is the source segment **without** its trailing newline — the
definition's first line through its last, joined by `\n` — because that is what
`ast`'s line span gives.

Nothing moved is still defined in `pdsfile.py` (`0` of the five names remain in
`vars(PdsFile)`), and `_PreloadMixin` carries **no** definition that was not on
the move list.

#### 5.1 The stay-list, byte-checked

| Definition | bytes | result |
|---|---|---|
| `new_merged_dir` | 3,087 | identical |
| `new_index_row_pdsfile` | 3,016 | identical |
| `copy` | 188 | identical |
| `__repr__` | 328 | identical |
| `is_logical_path` | 281 | identical |
| `use_shelves_only` | 412 | identical |
| `require_shelves` | 423 | identical |
| `set_logger` | 462 | identical |
| `set_easylogger` | 332 | identical |

#### 5.2 The sweep was computed, not read

CPython's `symtable` yields the module-global names each moved definition's body
references — a name bound in an enclosing *function* scope is FREE, not GLOBAL, so
`is_global()` is exactly the module-global question — and a second AST pass covers
each definition's decorator expressions and argument defaults, which are evaluated
in module scope and which `symtable` does not attribute to the method.

| Definition | module-globals its body references (builtins removed) |
|---|---|
| `get_permanent_values` | `pause_caching`, `resume_caching` |
| `load_volume_info` | `_clean_join`, `os` |
| `cache_category_merged_dirs` | **none** |
| `preload` | `HAS_PYLIBMC`, `_clean_abspath`, `_clean_join`, `os`, `pdscache`, `pdsviewable`, `pylibmc`, `time` |
| `cache_lifetime` | `cache_lifetime_for_class` |
| `cache_lifetime_for_class` | the four lifetime constants |
| `is_preloading`, `pause_caching`, `resume_caching` | **none** |

Every one of the five classmethods carries the single decorator `classmethod` and
no non-literal argument default, so pass 2 reports **names seen only in a
decorator or a default: none**. The pass is run whether or not it is expected to
fire, and its "none" is recorded as a measurement — it is what caught PR-16's
`_GLOB_CACHE_SIZE` and PR-17's `PATH_EXISTS_CACHE_SIZE`.

Re-run against the **delivered** `_preload.py`, the same sweep reports
**referenced but not bound here: none**, and **bound but not referenced by any
body: `DICTIONARY_CACHE_LIMIT` and `is_preloading`** — the two names the module
carries purely as public surface, which is what ground rule 9 requires of them.

**No class object is referenced, so `_preload.py` needs no function-local deferred
import.** Parsing the module for every `Name` node spelling `PdsFile`, `Pds3File`
or `Pds4File` finds **zero**. Its module-level imports are `import os`, `import
time`, `from pdsfile import pdscache, pdsviewable` and `from ._path_utils import
_clean_abspath, _clean_join`, plus the nested `import pylibmc` inside the
try/except; **no import statement in the file mentions `pdsfile.pdsfile`** in any
spelling. `_path_utils` imports only `fnmatch`, `functools`, `glob`, `math` and
`os`, so that edge cannot close a cycle either.

**One string literal does resolve a class by name, and it is meant to.**
`preload` reads `if cls.__name__ != 'Pds4File':` before looking for `_volinfo`.
Parsing for string constants containing a class name finds five: this one, three
log-message templates ('Connecting to PdsFile Memcache…', two 'Failed to connect
PdsFile Memcache…') and one log line ('PdsFile preloading completed'), plus the
class docstring's opening sentence. Only the first is executable class resolution,
and resolving by `__name__` rather than by importing the class is exactly what the
Phase-5 preamble prescribes — the same shape as `_index_rows.py`'s
`__bases__[0].__name__` sniff.

#### 5.3 Six names are stranded in `pdsfile.py`; five stay bound and the sixth is §5.4

Counted over the AST at the parent tip: total `Name` loads of each module-global,
how many fall inside the five moved bodies, how many are left.

| Name | total | inside moved bodies | left | what was done |
|---|---|---|---|---|
| `os` | 15 | 3 | 12 | plain import, unchanged |
| `_clean_join` | 6 | 3 | 3 | plain import, unchanged |
| `pdscache` | 6 | 5 | 1 | plain import, unchanged |
| `pdsviewable` | 7 | 1 | 6 | plain import, unchanged |
| `cache_lifetime_for_class` | 2 | 1 | 1 | plain import, retargeted to `._preload` |
| **`time`** | 1 | 1 | **0** | frozen member → `import time as time` |
| **`HAS_PYLIBMC`** | 1 | 1 | **0** | frozen member → `from ._preload import HAS_PYLIBMC as HAS_PYLIBMC` |
| **`pause_caching`** | 1 | 1 | **0** | frozen member → redundant-alias re-export |
| **`resume_caching`** | 1 | 1 | **0** | frozen member → redundant-alias re-export |
| **`_clean_abspath`** | 1 | 1 | **0** | private but reachable as `pdsfile.pdsfile._clean_abspath` → redundant-alias re-export |
| **`pylibmc`** | 1 | 1 | **0** | see §5.4 |

`time`, `HAS_PYLIBMC`, `pause_caching` and `resume_caching` are frozen members of
`pdsfile.pdsfile` in `tests/api/api_manifest.json`; deleting any of them is a
manifest break. `_clean_abspath` is PR-20's `_needs_glob` case: private, so not
frozen, but reachable today and covered by the no-name-lost invariant every
Phase-5 PR has measured. An inline `noqa` and a ratchet grow are both forbidden,
so all five use the PEP-484 redundant-alias form. `import time as time` joins the
stdlib re-export block, whose comment now says "these eight" rather than "these
seven"; the block below it, which called that block "the seven above", says
"the eight above".

#### 5.4 `pylibmc` — the one name this PR does not carry back, and the measurement that settles it

`preload`'s `except pylibmc.Error` and the `HAS_PYLIBMC` flag come from one
try/except block whose only purpose is `preload`, so it moved with its consumer —
the rule the Phase-5 preamble states and PR-16 (`FILE_BYTE_UNITS`) and PR-17
(`PATH_EXISTS_CACHE_SIZE`) already applied. `HAS_PYLIBMC` is re-exported.
`pylibmc` itself is a *conditionally bound module import*: re-exporting it would
need a new `if HAS_PYLIBMC:` statement in `pdsfile.py`, which is new logic rather
than a move.

Measured rather than argued:

- `pylibmc` **is not installed in this environment**, so
  `pdsfile.pdsfile.pylibmc` does not exist here on either side and §6's name
  comparison cannot see it either way.
- With a stub `pylibmc.py` on `PYTHONPATH`, `HAS_PYLIBMC` becomes `True`,
  `'pylibmc' in vars(pdsfile.pdsfile)` becomes `True`, and
  `scripts/dump_public_api.py` records `"pylibmc": "module"` under
  `pdsfile.pdsfile`. Diffing that dump against the committed manifest reports
  **two extra names, both spelled `pylibmc`: one under `pdsfile.pdsfile` and one
  under `pdsfile.pdscache`.**
- **Only the first is this PR's.** `pdscache.py:7` has its own optional
  `import pylibmc` behind a `try`, `pdsfile.pdscache` is also one of the dumper's
  seven fixed modules, and Phase 5 does not touch it. Re-running the same stub
  against **HEAD** confirms it: the diff is down to **one** extra name, under
  `pdsfile.pdscache`.

So on any machine where the name exists at all, the API-freeze gate is **already
red today**, and it stays red at HEAD for the `pdscache` half, which no Phase-5 PR
removes. `pylibmc` is not part of the frozen contract on either side. After this
PR the `pdsfile.pdsfile` occurrence resolves as `pdsfile._preload.pylibmc` instead.
Nothing in `src/`, `tests/`, `scripts/`, rms-opus or rms-viewmaster refers to
`pdsfile.pdsfile.pylibmc`. Recorded as deferred observation 58, not changed here.

### 6. `preload_and_cache.py` is a shim, and its surface is measured on both sides

The public surface was dumped before the change and after it and diffed, rather
than reasoned about. `vars(pdsfile.preload_and_cache)` holds **17 names, 9 of them
public**, on both sides:

```
DEFAULT_FILE_CACHE_LIFETIME  DICTIONARY_CACHE_LIMIT  FOEVER_FILE_CACHE_LIFETIME
LONG_FILE_CACHE_LIFETIME     SHORT_FILE_CACHE_LIFETIME
cache_lifetime_for_class     is_preloading   pause_caching   resume_caching
```

which is exactly the manifest's record for that module. The dump printed each
name with its kind and, for data, its value; **the before and after files are
identical, `diff` empty**, including `__file__` (still `preload_and_cache.py`),
the five integer values, and the four functions' kinds.

**No name is lost anywhere in the package**, measured module by module on the
parent tip and at HEAD, each run printing the `__file__` it imported:

| module | parent | head | lost | gained |
|---|---|---|---|---|
| `pdsfile` | 63 | 64 | **none** | `_preload` |
| `pdsfile.pdsfile` | 52 | 53 | **none** | `_PreloadMixin` |
| `pdsfile.preload_and_cache` | 17 | 17 | **none** | none |
| `pdsfile.pdscache` | 17 | 17 | **none** | none |
| `pdsfile.pdsviewable` | 19 | 19 | **none** | none |
| `pdsfile.pds3file` | 41 | 41 | **none** | none |
| `pdsfile.pds4file` | 22 | 22 | **none** | none |

Both gained names are underscore names, so the manifest does not see them.

**Which import path `pdsfile.py` uses, and why.** `_preload` is canonical, so
`pdsfile.py` imports `cache_lifetime_for_class` (still used at class level, for
`CACHE = pdscache.DictionaryCache(lifetime=cache_lifetime_for_class, …)`) and
re-exports `HAS_PYLIBMC`, `pause_caching` and `resume_caching` from `._preload`,
not from the shim. Three reasons: the shim is compatibility surface for external
callers, and pointing internal code at it would make it load-bearing rather than
compatibility; a direct import keeps the import graph acyclic by construction; and
it keeps `pdsfile.py`'s header honest about where the code lives.
`pds3file/__init__.py:12` and `pds4file/__init__.py:12` are **left alone** — their
`from pdsfile.preload_and_cache import cache_lifetime_for_class` keeps working
through the shim and keeps the shim exercised at package-import time in-tree,
which is a stronger check than any external caller would give it.

**The shim needs no ratchet entry, and that shaped its form.** ruff's isort runs
with `combine-as-imports = false` (the default), so the nine re-exports as one
parenthesized tuple report `I001`; one `from ._preload import X as X` line per
name is clean. Measured both ways; `preload_and_cache.py` had no per-file-ignores
entry before and has none now.

**The import graph, and both import orders executed.** The graph is:

```
   stdlib:  os   time   (pylibmc, optional)
                 │
                 ▼
        pdsfile/_path_utils.py
                 │
                 ▼
        pdsfile/_preload.py  ◄────  from pdsfile import pdscache, pdsviewable
             ▲        ▲
             │        └────────  pdsfile/preload_and_cache.py   (9 re-export lines)
             │                            ▲            ▲
        pdsfile/pdsfile.py            pds3file/    pds4file/
             ▲                        __init__.py  __init__.py
             └────────────────────────────┴────────────┘
```

`_preload.py`'s `from pdsfile import pdscache, pdsviewable` imports the package
from inside the package while the package's own `__init__.py` is mid-execution.
That is the same form `pdsfile.py` and `pds3file/__init__.py` already use, but
reasoning is not evidence, so **four fresh interpreters** each imported one module
of the graph first — `pdsfile.pdsfile`, `pdsfile.preload_and_cache`, `pdsfile`,
`pdsfile._preload` — and then checked eleven identities. All four orders: no
exception, all six modules resolved to this tree, and in every order
`preload_and_cache.pause_caching`, `.resume_caching`, `.is_preloading` and
`.cache_lifetime_for_class` **are** the `_preload` objects,
`pdsfile.pdsfile.cache_lifetime_for_class`, `.pause_caching` and `.HAS_PYLIBMC`
**are** the `_preload` objects, `pds3file`/`pds4file`'s
`cache_lifetime_for_class` **is** the same object, `PdsFile.preload` resolves to
`_PreloadMixin.preload` with nothing in `vars(PdsFile)` shadowing it, and the five
constants compare equal through both modules. **0 failures in each of the four
orders.**

### 7. Base order, the class shape, and the mixin harness

```python
class PdsFile(_AssociationsMixin, _DerivedPathsMixin, _IndexRowsMixin, _LocalFsMixin,
              _OpusMixin, _PreloadMixin, _ShelfMixin, _SortingMixin, object):
```

Alphabetical by mixin class name with `object` last, per
`plans/2026-07-27-addendum-phase5-mixin-base-order.md` (owner, 2026-07-27) and
enforced by
`tests/api/test_mixin_collisions.py::test_the_mixin_bases_are_listed_alphabetically`,
which was run first, before anything else, and at every commit. The Phase-5
preamble's illustration on this branch shows a different order; it was corrected
by PR #110, which merged to `rewrite` **after** this stack branched, so merging
`rewrite` forward to obtain it would drag #110's diff into this PR. The addendum
is the authority here.

`_PreloadMixin` sorts between `_OpusMixin` and `_ShelfMixin`, so unlike PR-20 this
PR does **not** move `PdsFile.__bases__[0]`. That is measured rather than argued
from the alphabet, because `_index_rows.py:254` sniffs
`cls.__bases__[0].__name__ == 'Pds4File'` (deferred entry 49) and
`tests/api/test_mixin_collisions.py:72` pins only `__bases__[-1]`. Dumping
`__bases__[0].__name__`, the full `__bases__` tuple, the full MRO and the sniff's
verdict for all **34** classes in the hierarchy, on the parent tip and at HEAD:

| Property | Classes where parent and HEAD differ |
|---|---|
| `__bases__[0].__name__` | **none** |
| the sniff's verdict (`… == 'Pds4File'`) | **none** — `True` for exactly the same six pds4 rule classes on both sides |
| `__bases__` tuple | **one**: `PdsFile` itself, which gains `_PreloadMixin` |
| MRO | all 34 — and every one of them **only** by the insertion of `_PreloadMixin`, each gaining exactly one entry, checked by deleting `_PreloadMixin` from the head MRO and comparing to the parent's |

The harness **discovers** its subjects from `PdsFile.__bases__`, so it picked up
`_PreloadMixin` for free and this PR edits no test file. At HEAD it reports eight
mixins defining 4, 12, 5, 5, 3, 5, 9 and 23 names respectively.

**The mixin/subclass intersection was re-measured before a line was written,
because a non-empty result is a hard stop rather than something to resolve in the
PR.** Using the test's own `_defined_names` helper, which drops the eight
structural names:

| | the 5 moved names |
|---|---|
| `Pds3File` (76 own names) | **empty** |
| `Pds4File` (50 own names) | **empty** |
| all 33 classes in the subclass hierarchy, rule modules included | **empty** |
| each of the 7 pre-existing mixins | **empty** |
| `PdsFile`'s own body at HEAD | **empty** |

### 8. Ruff ratchet — 17 codes conserve exactly, one shrinks, none is gained

Procedure: for every code in `pdsfile.py`'s entry, the following was run against
the parent's `pdsfile.py`, this branch's `pdsfile.py` and `_preload.py` —

```
ruff check --no-cache --isolated --output-format concise --select <code> \
           --line-length 100 --target-version py310 <file>
```

`--isolated` drops `pyproject.toml`'s `line-length = 100` and would otherwise
report an E501 at 88 columns that the project config does not, so the two settings
are restored explicitly (PR-16 §7 through PR-20 §8 record the same trap), and
`--output-format concise` is required because ruff 0.15's default output no longer
starts a line with the file path.

| Code | parent `pdsfile.py` | → `pdsfile.py` | `_preload.py` | sum |
|---|---|---|---|---|
| E501 | 5 | 4 | 1 | 5 |
| E701 | 10 | 8 | 2 | 10 |
| F841 | 5 | 4 | 1 | 5 |
| RUF005 | 2 | 1 | 1 | 2 |
| **UP015** | **1** | **0** | **1** | **1** |
| UP031 | 9 | 7 | 2 | 9 |
| **I001** | **2** | **1** | **0** | **1** |
| B904, C405, E713, E721, N806, RUF012, SIM102, SIM114, SIM118, UP004, UP024 | 3, 3, 1, 1, 2, 16, 1, 2, 1, 1, 9 | unchanged | 0 | = parent |

Seventeen codes conserve exactly; one of those seventeen — **UP015** — conserves
by leaving `pdsfile.py` entirely, so **`pdsfile.py`'s entry drops it**. Its single
occurrence was
`open(table_path, 'r', encoding='utf-8')` inside `load_volume_info`, now
`_preload.py:265`.

**I001 goes 2 → 1, and that is a genuine shrink rather than a leak.** The parent's
`pdsfile.py` had two unsorted import blocks, at `:6` and at `:44`; removing the
`pylibmc` try/except from between them merged the two into one, which ruff reports
once. `_preload.py` reports **zero** I001, because its own header was written in
the single-line `from X import a, b` form ruff's isort wants rather than the
parenthesized form the old header used — a choice about *new* code in a module
header, not a restyle of a moved body. So the total suppressed-violation count
goes **74 → 73**, one lower, never higher.

The **converse** check, which is easy to skip: running the project's whole select
set (`E,F,W,I,UP,B,SIM,C4,A,N,PT,RUF` minus the three project-wide ignores)
against `_preload.py` with **no** per-file entry reports exactly the codes its
entry lists and nothing else — `E501` 1, `E701` 2, `F841` 1, `RUF005` 1, `UP015`
1, `UP031` 2. Against `preload_and_cache.py` it reports **nothing**, on the parent
tip and at HEAD alike, which is why the shim needs no entry.

Resulting entries:

| File | Entry | Note |
|---|---|---|
| `src/pdsfile/pdsfile.py` | 17 codes | **UP015 removed**; it still triggers the other seventeen |
| `src/pdsfile/_preload.py` | `["E501", "E701", "F841", "RUF005", "UP015", "UP031"]` | exactly the codes its moved lines trigger, every one already in `pdsfile.py`'s entry |
| `src/pdsfile/preload_and_cache.py` | *(no entry, before or after)* | the shim triggers nothing |

### 9. The tests that pin this code — measured, and the measurement needs reading carefully

A coverage run of `tests/api/`, `tests/pds3file/`, `tests/pds4file/`,
`tests/rules/`, `tests/core/` and `tests/holdings_maintenance/` with
`dynamic_context = test_function` attributes **118 distinct test functions** to
`_preload.py`, from **19 test modules**.

| Definition | Contexts | Test modules |
|---|---|---|
| `cache_lifetime_for_class` | 116 | 18 |
| `get_permanent_values` | 2 | 1 — `tests/core/test_pdsfile_caching.py` |
| `pause_caching` | 2 | the same |
| `resume_caching` | 2 | the same |
| `preload` | **0** | — |
| `load_volume_info` | **0** | — |
| `cache_category_merged_dirs` | **0** | — |
| `cache_lifetime` | **0** | — |
| `is_preloading` | **0** | — |

**Four of those five zeros do not mean what the same figure meant in PR-20.**
`dynamic_context = test_function` attributes a line to the test function that was
running when it executed, and `preload`, `load_volume_info` and
`cache_category_merged_dirs` run at **session-fixture and module-import time**,
before any test function starts — so they get zero contexts while being heavily
exercised. Statement coverage from the same full-data run says so: `preload` runs
**83 of its 113 statements**, `load_volume_info` **52 of 53**, and
`cache_category_merged_dirs` **4 of 4**. The negative controls in §10 are the
independent confirmation: mutating `preload` turns up to 57 tests red.

**The convention behind every statement figure in this section and in §12**, so
they can be reproduced rather than approached: the statement set is **coverage's
own**, from `coverage.Coverage(data_file=…).analysis2(path)` against the head
full-data run's `.coverage`, not an AST statement count — an AST walk counts
`try:` and a few other headers that CPython emits no line event for, which is how
this record's first draft reached 109 for `preload` and 20 for
`get_permanent_values`. A definition's statements are those of coverage's set
falling inside its AST span, **`def` line included, decorators excluded**; the
`def` line is executed at import, so a definition whose body never runs still
shows one hit. `preload`'s 113 include the 14 of its nested `_preload_dir`, all
14 of them hit. The file as a whole is 226 statements, 43 missing, and 5 excluded
— the `pragma: no cover` lines of the `pylibmc` try/except.

The two genuine zeros are `cache_lifetime` (**1 of 2** statements — only its `def`
line) and `is_preloading` (**1 of 2**, likewise). Neither body is executed by
anything in the suite. `is_preloading` has no caller anywhere in `src/`, `tests/`,
`scripts/`, rms-opus or rms-viewmaster; `cache_lifetime` is passed as
`lifetime=cls.cache_lifetime` only by the three `pdscache` constructions **inside**
`preload`, and every one of those is on a branch the suite does not take (§11), so
the lifetime function actually in use is the module-level `cache_lifetime_for_class`
that `pdsfile.py:180`, `pds3file/__init__.py:60` and `pds4file/__init__.py:49`
hand to their class-level `DictionaryCache`. Both are live API — ground rule 9
keeps them — and both are recorded as deferred observation 59 rather than fixed:
this PR's gate is the pass/fail set and a new test id is movement.

### 10. Negative controls — 19 mutations, 13 red, 6 green, every one guard-checked

Every control below is a mutation of the **moved** code (or of the harness, or of
a patch site), run against `tests/api/ tests/core/ tests/pds3file/ tests/pds4file/
tests/rules/pds3/ tests/rules/pds4/` in `--mode ns`, which is **737 passed / 34
skipped** unmutated.

**The harness has a trap in it, and it is avoided by construction.**
`pyproject.toml` sets `pythonpath = [".", "src"]`, which pytest resolves against
**rootdir** and inserts at the front of `sys.path` — **ahead of `PYTHONPATH`**. So
mutating a copy of `src/` and pointing `PYTHONPATH` at it from the repo root
imports the *unmutated* tree, and every control reports green, which reads exactly
like "the tests do not reach this code" and is in fact "the harness does not reach
the mutation". PR-18 fell into this and re-ran all seven of its controls. Each
mutation here is therefore written into a **full copy of the working tree**,
pytest is run **from inside that copy**, and an appended block in that copy's
`tests/conftest.py` asserts that `pdsfile.pdsfile`, `pdsfile._preload` and
`pdsfile.preload_and_cache` all resolve inside the copy and writes their
`__file__`s to a marker file the harness then reads. **All 19 controls carried
that assertion and every one of them passed it.**

(The guard runs at conftest *import* time rather than in a `pytest_configure`
hook. A second `def pytest_configure` in the same module shadows the repo's own,
which sets `config._pdsfile_holdings`, and every run dies in an `INTERNALERROR`
before collecting anything — which the first attempt at this harness did, 19 times
in a row, with the guard reporting success each time. Worth writing down: a guard
that passes while the run it guards never happens is the same failure class as a
vacuous gate.)

**Thirteen mutations turned tests red:**

| Mutation | Result |
|---|---|
| `preload` does not recurse into a directory's children | **6 failed**, 2 test functions |
| `preload` skips `load_volume_info` | **57 failed**, 14 test functions |
| `preload` never appends to `LOCAL_PRELOADED` | **57 failed**, 17 test functions |
| `load_volume_info` corrupts every description | **7 failed**, 3 test functions |
| `get_permanent_values` never calls `resume_caching` (PR-15's bug 2, reintroduced) | **2 failed** — both `TestGetPermanentValues` ids |
| `get_permanent_values` never re-preloads on a missing key | **1 failed** — `test_caching_is_resumed_after_a_missing_value_triggers_a_reload` |
| `pause_caching` is a no-op | **2 failed** — both `TestGetPermanentValues` ids |
| `resume_caching` is a no-op | **2 failed** — both `TestGetPermanentValues` ids |
| the base order is no longer alphabetical | **1 failed** — `test_the_mixin_bases_are_listed_alphabetically`, and nothing else |
| `_PreloadMixin` also defines `os_path_isdir` | **2 failed** — `test_no_two_mixins_define_the_same_name` and `test_every_mixin_name_is_reachable_through_pdsfile` |
| `Pds3File` itself defines `preload` | **88 failed**, 24 test functions — including `test_no_mixin_is_shadowed_by_a_pdsfile_subclass` |
| the `Pds3File.CACHE` patch removed from `test_pdsfile_caching.py` | **34 failed**, 6 test functions |
| the `Pds3File.preload` patch removed from `test_pdsfile_caching.py` | **56 failed**, 33 test functions |

The last two are §11's forced-wrong controls; they are listed here because they
share the harness. The `Pds3File`-shadows-`preload` control is loud for the same
reason PR-20's `sort_basenames` collision was: the shadowing method breaks the
session preload before the harness check can report, so the check's own id fails
alongside 23 others rather than alone.

**Six mutations changed nothing, and they are reported rather than dropped.** A
control that comes back green is a measurement too:

| Mutation | Result | Why |
|---|---|---|
| `cache_lifetime` always returns 0 | 737 passed | its body is never executed (§9); nothing takes the branch that would pass it to a cache |
| `is_preloading` always returns True | 737 passed | no caller anywhere |
| `cache_category_merged_dirs` iterates nothing | 737 passed | `preload` caches the same merged directories itself, and the session fixture always preloads, so the import-time seeding is redundant whenever a preload follows |
| `cache_lifetime_for_class` returns "forever" for everything | 737 passed | it is called 116 times (§9), but the value only sets a `DictionaryCache` eviction deadline and no test asserts one |
| `DEFAULT_FILE_CACHE_LIFETIME` changed from 12 h to 13 h | 737 passed | same reason, one level down |
| `preload` leaves `FS_IS_CASE_INSENSITIVE` at its class default instead of computing it | 737 passed | the class default is `True` and `preload` normally computes `False` here; the flag only gates `force_case_sensitive` handling in `_path_utils`/`_local_fs`, which no golden case reaches |

The last of those is the one worth a second look: it is not "nothing calls this"
but "the suite never distinguishes a case-sensitive filesystem from a
case-insensitive one". Recorded with the other coverage gaps as deferred
observation 59.

### 11. The monkeypatch audit — the check the set diff cannot perform

Deferred entry 29 (opened by PR-16's round-1 Major, owned by "PR-17 onward") says
an extraction sweep must also ask **which namespaces the tests patch**, not only
which globals the code reads. A test whose patch lands on a module the moved code
no longer resolves through keeps passing while exercising nothing, and §6.2's
outcome-set diff compares pass/fail — so it is *structurally blind* to this class
of defect. **This PR's set diff is empty, and it would have been empty in every
one of the cases below, including a broken one.**

**Enumeration.** Every `monkeypatch.setattr` / `setitem` / `delattr` / `setenv` /
`delenv`, `mock.patch`, `patch(`, `patch.object` and bare `setattr(` in `tests/`
and `scripts/` — 20 sites, all `monkeypatch`; the tree still uses no
`unittest.mock` at all:

| Target | Sites | Names a symbol **this PR** moves? | Does this PR's moved code reach it? |
|---|---|---|---|
| **`Pds3File.preload`** (`test_pdsfile_caching.py:127`) | 1 | **yes — `preload` is one of the five** | **yes** — `get_permanent_values` calls `cls.preload(...)` on its `KeyError` path |
| **`Pds3File.CACHE`** (`tests/core/conftest.py:28`, `test_pdsfile_caching.py:112,126`) | 3 | no — a class attribute that stays on the class | **yes** — `get_permanent_values`, `pause_caching` and `resume_caching` all read `cls.CACHE` |
| `Pds3File`/`Pds4File.LOCAL_PRELOADED`, `.LOCAL_HOLDINGS_DIRS` (`test_pdsfile_path_resolution.py:58,59,71,72,85,86`) | 6 | no — class attributes that stay on the classes | not in these tests; `preload` writes `LOCAL_PRELOADED` elsewhere |
| `Pds3File.shelf_path_and_key_for_abspath` (`test_pdsfile_path_resolution.py:120,129,137,155`) | 4 | no — PR-17's symbol, audited there | no |
| `abspath_for_logical_path.__globals__['glob']` (`test_pdsfile_path_resolution.py:92`) | 1 | no — PR-16's fix site, on `_path_utils`'s globals | no |
| `pdsviewable.ICON_SET_BY_TYPE` (`test_pdsviewable_iconset_for.py:47`) | 1 | no — different module | no |
| `monkeypatch.setenv` / `delenv` (`test_pdsfile_path_resolution.py:54,70,83,84`) | 4 | no — environment, not a namespace | no |

**`Pds3File.preload` is the first patch site in this phase that names a symbol the
PR is moving**, so it gets the closest look. `monkeypatch.setattr(Pds3File,
'preload', …)` resolves the *old* value with `getattr` and, because `'preload'` is
not in `vars(Pds3File)`, records `notset` so undo does `delattr` — which is true
before this PR (`preload` was inherited from `PdsFile`) and equally true after it
(inherited from `_PreloadMixin` through `PdsFile`). The patch writes onto
`Pds3File` either way, and `get_permanent_values` reaches it through `cls.preload`
where `cls is Pds3File`, so the site reaches exactly what it reached before. Both
halves are measured, not reasoned: `'preload' in vars(Pds3File)` is `False` at
HEAD, and forcing the patch away turns the test red (below).

**No patch site names any of the other thirteen moved names**, and a regex over
`tests/`, `scripts/` and `src/` for *direct assignment* to any of the fourteen —
the form that is not a `monkeypatch` and is easy to miss — returns **zero** hits
for all fourteen, and no test assigns to any attribute of `pdsfile.pdsfile` or of
`pdsfile.preload_and_cache`.

**Every patch mechanism that this PR's code reaches was forced to answer wrongly,
and each turned its own test red:**

| Forced-wrong control | Went red |
|---|---|
| the `Pds3File.preload` patch removed | `TestGetPermanentValues::test_caching_is_resumed_after_a_missing_value_triggers_a_reload` (plus 55 collateral ids — with `preload` unpatched, the stub cache's `KeyError` sends the real `preload` through the session's cache) |
| the `Pds3File.CACHE` patch removed | `TestGetPermanentValues::test_caching_is_resumed_after_the_values_are_read` (plus 33 collateral) |

The four mechanisms this PR's code does **not** reach — the `glob` stub in
`abspath_for_logical_path.__globals__`, the `LOCAL_PRELOADED` stub, the
`shelf_path_and_key_for_abspath` stub and the `pdsviewable.ICON_SET_BY_TYPE`
stub — were each forced wrong by PR-17 and PR-20 and each went red there; nothing
in this PR changes what they resolve through, and the enumeration above says why
for each.

**Entry 29's second half — rebinding re-exported *data*.** The same asymmetry one
level down, measured on both sides:

| | parent `2df25ab` | this branch |
|---|---|---|
| namespace the 5 methods resolve through | `pdsfile.pdsfile` | `pdsfile._preload` |
| namespace `os`, `time`, `pdscache`, `pdsviewable`, `_clean_join`, `_clean_abspath`, `HAS_PYLIBMC`, `pause_caching`, `resume_caching`, `cache_lifetime_for_class` resolve in, **for the moved code** | `pdsfile.pdsfile` (and, for the last four, `pdsfile.preload_and_cache`) | `pdsfile._preload` |
| rebinding `pdsfile.pdsfile.time` reaches `preload`'s retry sleep | **yes** | **no** |
| rebinding `pdsfile.preload_and_cache.pause_caching` reaches `get_permanent_values` | **yes** | **no** |
| all ten still bound on `pdsfile.pdsfile` / `preload_and_cache` | yes | yes |

Nothing in `src/`, `tests/`, `scripts/`, rms-opus or rms-viewmaster rebinds any of
those module attributes — greped, zero hits — so nothing is broken today. The
general observation stands for PR-22 and stays in
`critiques/deferred-observations.md` as entry 29. The shim makes it slightly
sharper than before: a caller who rebinds `pdsfile.preload_and_cache.X` now
rebinds only the shim's own name and not the definition, which is inherent to what
a re-export shim is.

### 12. What the green set does **not** prove

`preload` is the single most consequential method in the package, and its most
important branch is dark here. Measured from the head full-data run's statement
coverage of the delivered `_preload.py` — coverage's own statement set, §9's
convention — **30 of `preload`'s 113 statements are never executed**, and they are
not a random 30:

- **the whole memcached path** — `MemcachedCache` construction, the
  `PRELOAD_TRIES` retry loop, `time.sleep(2.**k)`, `pylibmc.Error`, the
  give-up-and-fall-back-to-`DictionaryCache` branch, and
  `cls.DEFAULT_CACHING = 'all'`. It needs `HAS_PYLIBMC` true *and* a non-zero
  port; `pylibmc` is not installed here and no test passes `port=`;
- **`clear=True` and `force_reload=True`** — `CACHE.clear(block=True)`,
  `wait_and_block()`, `unblock()`, and both `LOCAL_PRELOADED = []` resets;
- **the already-preloaded early return**, including the
  `if cls.MEMCACHE_PORT: cls.get_permanent_values(...)` call — the recursion PR-15's
  bug 2 lived in;
- the `DictionaryCache` re-creation at `:365`, because the class-level `CACHE` is
  already a `DictionaryCache` when the session fixture preloads;
- two logging branches (`Pre-load not needed for …`, `Not a directory, ignored: …`).

`get_permanent_values` is the same story: **8 of its 21 statements** never run,
namely the entire bundleset/bundle descent, because the only tests that reach it
hand it a stub whose categories have no children. And `cache_lifetime_for_class`
never returns `DEFAULT_FILE_CACHE_LIFETIME` from its `isinstance(arg, str)` branch
or `FOEVER_FILE_CACHE_LIFETIME` from its `not isinstance(arg, cls)` branch.

rms-viewmaster passes `port=` in deployment (ground rule 9 names it), so this code
is live. **That is precisely why the only defensible approach here is a
byte-for-byte move with no cleanup of any kind**, and why §5's byte comparison,
not the suite, is the load-bearing check of this PR. §13's Check B is the only
thing in this record that runs the moved `preload` against a *different* holdings
tree, and it runs the `DictionaryCache` path there too.

### 13. Consumer smoke — outcome unchanged

The gate is **same outcome as baseline**, not "passes"
(`critiques/baselines/consumer-smoke-baseline.md`).

| Check | Baseline | This branch |
|---|---|---|
| A — rms-opus import paths | 4/4 resolve, 0 failures | **4/4 resolve, 0 failures** |
| B — rms-viewmaster startup | 5 ok, 3 pre-existing failures | **5 ok, 3 failures — the same three** |

The three Check-B failures are still `pdsfile.cache_lifetime` (raises),
`pdsfile.DEFAULT_CACHING` (absent) and the same `cache_lifetime` read inside
`get_page_cache()`. None became a pass. `pdsfile.pdsfile.repair_case` still
resolves.

**Check B is load-bearing for this PR in a way it was not for the others.**
`create_app()` → `init_once()` calls `Pds3File.preload(...)` and `Pds4File.preload(...)`
on rms-viewmaster's own holdings configuration, so the stage that reports `ok`
is the moved `preload` running end to end outside this repo's test harness: the
run's log shows `Pre-loading:` lines for the category directories, the
`Missing category dir:` warnings for the ones absent there, and
`PdsFile preloading completed`. rms-viewmaster also reads `DEFAULT_CACHING` and
`cache_lifetime` at package level, and both are ground-rule-1 failures that must
stay failures — they did.

Environment note carried from the baseline: the check ran under the pdsfile venv's
interpreter with rms-viewmaster's `site-packages` appended to `PYTHONPATH`,
because that venv lacks pdsfile's declared `range_ex` dependency, and with the
holdings environment variables set. rms-viewmaster is at `a0d05e2`; rms-opus is at
`73cb6de7`.

### 14. Clean install

`scripts/clean_install_check.sh` passes inside `run-all-checks.sh`. `_preload.py`
is picked up by the existing `include = ["pdsfile*"]` package glob with no
packaging change, and the gate imports the whole manifest module surface —
`pdsfile.preload_and_cache` is in `scripts/check_runtime_imports.py`'s list and
`pdsfile.pdsfile` is too, neither of which can import if `_preload.py` is missing
from the distribution.

### 15. The class docstring is derived, and verified in both directions

Deferred entry 54 records that the mixins' "state contract" docstrings are
hand-written, drift, and are mechanically derivable; PR-19's rounds 1, 2 and 3 and
PR-20's rounds 2 and 3 each found one wrong. The entry asks for the derivation to
become a *test* and assigns that to PR-22. This PR does not build the test — it is
not in its deliverables — but it applies the method by hand, in the widened form
PR-19's rounds 3 and 4 settled: walk **every** `ast.Attribute` node rather than
only `self.X`/`cls.X`, scope the claim to the receivers that hold a `PdsFile`
object or the `PdsFile` class, and **exclude the names the mixin itself defines**.

The receiver list is printed in full so the scoping is checkable rather than
asserted. Scoped to the mixin's five methods, which is what the contract covers:
`_PreloadMixin`'s PdsFile-side receivers are `cls`, `pdsdir`, `pdsf0` and
`pdsf1` — **4 of its 31 distinct receiver expressions** — against **27** others
that are strings, lists, dicts, files, `os`, `os.path`, `pdscache`,
`pdsviewable`, `pylibmc`, `time`, the logger, and `cls.CACHE` / `cls.LOGGER` /
`cls.LOCAL_PRELOADED`, whose own methods are cache, logger and list methods
rather than PdsFile surface. (A walk over the *whole module* rather than the
mixin finds 34 receivers, the three extra being `arg`, `arg.interior` and
`arg.interior.lower()` inside the module-level `cache_lifetime_for_class` —
where `arg` **is** a PdsFile object. It is out of the contract because the
contract is the mixin's, not the module's, and the figure is given so the two
scopings cannot be confused.)

**Direction 1 — every PdsFile-side name the code reaches appears in the docstring:
25 of 25, nothing missing.** Direction 2's residue is prose only: `DictionaryCache`,
`MemcachedCache` and `Error` (the three `pdscache`/`pylibmc` names the text
mentions), `_LocalFsMixin` and `_index_rows` and `__bases__` (the sibling
references), `_volinfo` (a directory name), `cache_lifetime_for_class` (reached as
a module global rather than as an attribute, so the attribute walk does not see
it), the label `WRITTEN`, and the words `Filling`, `Neither` and `Viewmaster`.

Unlike `_SortingMixin` and `_AssociationsMixin`, **every** class attribute this
mixin reads is defined on `PdsFile` itself and not only on `Pds3File`/`Pds4File`
— which is what makes `PdsFile.cache_category_merged_dirs()` at the bottom of
`pdsfile.py` work on the bare class at import time, and that is executed at every
import rather than asserted here.

### 16. Deferred observations

Entry 29 is the one this PR was told to act on, and §11 is the action. It is
**not** resolved — it is a per-PR step, owned by "PR-17 onward" — so it stays open
for PR-22. Entries 53 and 54 are deliberately not taken up, per the coordinator's
standing direction that neither is this PR's to build (common brief §5.1). Entry
42 (the back-import guard, owner PR-22) is untouched: §5.2 shows `_preload.py` is
clean by the same parsing check, but this PR builds no guard. **Entry 57 (the
home-rooted holdings path in an archived plan) was withdrawn during this loop**, on
the owner's ruling of 2026-07-27 that absolute holdings paths in `plans/` and
`critiques/` are not confidential; round 2 applied it and
`critiques/pr-21/round-2.md` records it. The entry is kept and marked closed rather
than deleted, because its measurement is still an accurate record of what was
found. No other entry in 1–57 is resolved or invalidated here.

Two entries are **added** by the executor's own measurements: **58** (`pylibmc`
resolves as `pdsfile._preload.pylibmc` rather than `pdsfile.pdsfile.pylibmc` where
it is installed at all, and where it is installed the freeze gate is already red)
and **59** (the five measured coverage gaps: `cache_lifetime` and `is_preloading`
have no executed body at all, `cache_category_merged_dirs` is redundant whenever a
preload follows, the lifetime values are never asserted, and no test distinguishes
a case-sensitive filesystem from a case-insensitive one).

### 17. Review loop

| Round | Verdict | Findings | Record |
|---|---|---|---|
| 1 | goal met | 0 Major, 5 Minor (all accepted and fixed; **none in `src/`** — all five in this record, the sub-plan or the deferred-observations file), 2 Deferred (one folded into entry 58, one added as entry 60) | `critiques/pr-21/round-1.md` |
| 2 | goal met | 0 Major, 3 Minor (all accepted and fixed; **none in `src/`** — all three in this record or the deferred-observations file), **0 new Deferred** | `critiques/pr-21/round-2.md` |
| 3 | goal met | 0 Major, 3 Minor (all accepted and fixed; **two in `src/`** — the mixin docstring — and one a heading in this record and the sub-plan), **0 new Deferred** | `critiques/pr-21/round-3.md` |
| 4 | goal met | **0 Major, 0 new Minor**; all 11 prior findings confirmed resolved by re-measurement; 5 Deferred (all five fixed in place here) | `critiques/pr-21/round-4.md` |

*(Rows are written only after the round they describe has run and its record file
exists on disk — the rule PR-18's round-3 Major established. No row is written for
a round that has not run.)*

**Round 1 found no Major and five Minor, and the one that mattered was not
arithmetic.** §5.4 and deferred entry 58 said a stub `pylibmc` makes the manifest
dump gain "exactly one extra name". Re-measured: it gains **two**, because
`pdscache.py:7` has its own optional import of the same module and
`pdsfile.pdscache` is also one of the dumper's seven fixed modules. The half this
PR moves is the smaller one, so **the freeze gate stays red on a memcached-capable
host after this PR**, which the entry as first written would have hidden from the
owner. The correction is in §5.4, in the sub-plan and in entry 58, which now says
any fix has to cover `pdscache` too.

The second was §9's and §12's statement-coverage totals, derived from an AST
statement count rather than from coverage's own statement set — an AST walk counts
`try:` and other headers CPython emits no line event for. `preload` is **113
statements, 83 hit, 30 missing**, not 109/80/29, and `get_permanent_values` is 21,
not 20. The convention is now stated in §9 so the figures can be reproduced, and
§12's conclusion is unchanged: the same 30 lines, enumerated the same way.

The other three were record and sub-plan accuracy: §8's body saying "sixteen"
where its own heading and the commit message say seventeen; the sub-plan's
"as executed" section left empty although four things had diverged, one of them
the ratchet criterion §7 states ("each code must conserve") that I001 does not
meet; and an 83-for-82 line count.

**No round-1 fix touched `src/pdsfile/`**, so by §6.6 step 5 the full-data record
carries forward unregenerated.

**Round 2 found no Major and three more Minor, and all three are record wording
again.** Entry 60 cited the blank line before the banner PR-21 adds rather than
the banner (`:495` for `:496–498`); entry 60's banner-width figures were HEAD's
while the clause identifying them described the parent's, and each banner
contributes *two* rule lines, so a two-banner list could not describe two rule
lines — the entry now carries a three-tree table and names the 84-column interior
pair `_preload.py` also inherited; and §15's "30 others" was a whole-module
receiver count inside a sentence scoped to the mixin, where the figure is **27**,
the three extra being `cache_lifetime_for_class`'s `arg`, which is itself a
PdsFile object rather than one of the "strings, lists, dicts, files" the sentence
characterised them as.

The round-2 reviewer re-derived, with its own scripts: both moved blocks
byte-for-byte, all five byte totals, all nine stay-list counts, the `vars()` and
`dir()` and MRO comparisons, the API dump, the whole §8 ratchet table cell by
cell, the `symtable` sweep, §7's 34-class figures, §11's 20 patch sites, §15's
contract in both directions (25 of 25, zero residue), and every `file:line`
citation. It **ran** the clean-install gate and the no-holdings job (82 / 800 on
both sides), imported eight modules first-in-a-fresh-interpreter, and checked all
three code commits for importability, ruff cleanliness and a green `tests/api`.
Two of its checks this record had not made: it recomputed the **minimal** ruff
code set per file with per-file-ignores disabled, confirming `_preload.py` needs
exactly its six and `pdsfile.py` exactly its seventeen; and it located each of
`_preload.py`'s eight suppressed violations by line and confirmed **all eight are
on moved lines**, none in the new header or docstring.

**Deferred entry 57 is withdrawn in this round**, not as a review finding but on
an owner ruling of 2026-07-27 delivered while the round was running: absolute
holdings paths in `plans/` and `critiques/` are not confidential. The entry is
kept and marked closed, with the measurement it recorded left intact and a note
that code, tests and CI still resolve holdings roots through the environment
variables on portability grounds. Both rounds' reviewers checked §3.4 and neither
found anything to report, so no finding in this loop changes.

**No round-2 fix touched `src/pdsfile/`** either, so the full-data record carries
forward unregenerated a second time.

**Round 3 found no Major and three more Minor, and two of them are the first
findings in this loop that land in `src/`** — both in `_PreloadMixin`'s docstring,
both prose about runtime behavior that had been written rather than executed. Its
"and nothing else" enumeration named `set`, which is never a receiver in these
five methods (`set(parts[2])` is a constructor call), and omitted four families
that are: `os` itself, file objects, `pylibmc` and `time`. And it said the
memcached half runs "only when a non-zero port is supplied", which excludes the
path deployment takes: the condition is
`(port == 0 and cls.MEMCACHE_PORT == 0) or not HAS_PYLIBMC`, and `preload` writes
the port it was given back onto the class, so a later argumentless call still
takes it — the docstring's own contract table lists `MEMCACHE_PORT` as written two
paragraphs above. Both now say the measured thing, and the name list below the
colon is unchanged: 25 of 25 in both directions, re-run after the edit.

The third was a heading in this record's §5.3 and the sub-plan's §5.2 — "six names
are stranded **and every one of them stays bound**" — sitting directly above a
table whose sixth row is `pylibmc`, which does not, and directly above a §5.4
headed "the one name this PR does **not** carry back". Measured: `'pylibmc' in
vars(pdsfile.pdsfile)` is `True` at the parent with a stub on `PYTHONPATH` and
`False` at HEAD. Both headings now say five.

**Round 3's fixes did touch `src/pdsfile/`, so the full-data record was
regenerated** before the round was recorded — the pair at 23:37:21 / 23:39:10 in
§3, empty against the baseline and against the superseded pair in both modes.

The round-3 reviewer also measured the §8 ratchet table **with per-file-ignores
disabled**, so it checked the *minimal* code set for each file rather than the
configured one, and it set out to raise the `pylibmc` name loss as a Major and
recorded that it could not sustain it. Its one suggestion outside the findings —
annotate the `pylibmc` exception inside `pdsfile.py`'s re-export comment — was
**declined**, with the reasoning recorded in deferred entry 58: that comment's
clause is a purpose statement scoped to the four private names it introduces, none
of which is `pylibmc`, and it is inherited wording that PR-16 wrote and PR-17,
PR-20 and PR-21 have only added names to.

**The loop terminates at round 4**, at §6.6's four-round cap: a fresh reviewer
returned zero Major and no new un-rebutted Minor. Round 4 is the *scoped*
re-review the anti-thrash rule prescribes — confirm the prior rounds' findings are
resolved, raise only new Major — and it confirmed all eleven by re-measuring each
rather than reading this record. Two of those re-measurements went further than
the fix required, and they are why the round was worth running:

- it **executed** the docstring's receiver enumeration rather than reading it,
  confirming `set` is gone and that all eleven named families do occur with an
  instance of each; re-derived the contract to 25 of 25 with empty residue both
  ways; and then checked the *write* classification this record had only asserted
  — measured `Store` on `cls` is exactly the five the docstring marks WRITTEN,
  measured `Store` on the instance receivers is exactly `permanent`, and
  `_childnames_filled` is never a `Store`, which is what "mutated in place" means;
- it **executed** the corrected memcached condition across the full truth table of
  `(port, MEMCACHE_PORT, HAS_PYLIBMC)` with `pdscache`'s two cache classes patched
  to raising sentinels — **8 of 8 match**, including `port=0,
  MEMCACHE_PORT=11211, HAS_PYLIBMC=True → memcached`, the case round 3's fix was
  about.

It also re-derived the two moved spans as single blobs (18,197 and 2,821 bytes,
`# pragma: no cover` markers included), `getattr_static` over `dir()` of all three
classes (257 / 299 / 272 names, zero lost, zero gained, **zero kind changes**),
eleven first-import orders, and the ratchet's converse check with per-file-ignores
off — which located all eight of `_preload.py`'s suppressed violations **inside
moved bodies**, none in the new header or docstring.

Its five Deferred items are all corrections to text this PR itself wrote, and all
five are **fixed in place** here rather than carried forward. Four are line
citations and a count that round 3's four-line docstring fix moved. The fifth is
the one worth naming: `_preload.py`'s line count was carried forward from its
extraction commit rather than re-counted, which is **the same defect PR-20's round
2 found in `_sorting.py`** — and the "counted at HEAD, and re-counted at each round
rather than carried forward" sentence PR-19 §5 and PR-20 §5 adopted in response is
the sentence §5 of this section had dropped. It is restored.

**Nothing was rebutted in any round.** All eleven Minor findings across rounds 1–3
were accepted and fixed, and the one out-of-band suggestion that was declined
(round 3's, to annotate the `pylibmc` exception in `pdsfile.py`'s comment) was
recorded in deferred entry 58 with its reasoning rather than argued. Of the
sixteen findings this loop produced across four rounds, **fourteen were figures or
phrases in records and sub-plans and two were prose in the mixin docstring; not
one was in the extracted code** — the same result PR-19 and PR-20 each produced,
and the strongest evidence available that the extraction itself is clean.

## PR-22 — `refactor: finalize pdsfile.py core`

**Branch:** `pr-22-core-finalize`, based on `pr-21-preload` @ `f286dda`
("docs: record round 4 and close the review loop"), opened against that branch,
not `rewrite` (`plans/2026-07-27-addendum-phase5-stack-extension.md`).
**Baseline:** **PR-21's recorded post-move set** — its §3 above, `--mode ns` 848
passed / 34 skipped (882 ids), `--mode s` 555 passed / 3 skipped (558 ids),
no-holdings 82 passed / 800 skipped — **re-measured locally on the parent tip**
in a detached worktree with this PR's own command lines rather than copied from
the table. The re-measurement reproduced it exactly.
**Date:** 2026-07-28
**Sub-plan:** [`plans/2026-07-27-pr-22-subplan.md`](../plans/2026-07-27-pr-22-subplan.md)

This is the last PR of Phase 5 and it has four deliverables: the `_properties.py`
extraction, the finalization of core against the plan's explicit stay-list, the
removal of the commented-out dead code, and the module docstring plus the
behavioral check that makes the decomposition self-verifying (deferred
observation 42). **§18 below is the phase-closing table** the brief asks the last
PR for.

Unlike every other PR in this group, this one **adds test ids** — 10 of them, the
back-import check — which is the one movement §6.2's strict gate licenses here.
Every added id is enumerated in §3, in both the full-data `ns` set and the
no-holdings set, and nothing else moved in either.

### 1. Environment

| Item | Value |
|---|---|
| Interpreter | CPython 3.12.3, repo venv, `pip install -e ".[dev]"` |
| Holdings | `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` + `PDSFILE_TEST_HOLDINGS=full`, pointed at the limited testing copy the goldens are tuned to |
| Baseline tree | a `git worktree` detached at the parent tip `f286dda`, same interpreter, same holdings; `pytest` reports that directory as `rootdir` |
| Command lines | exactly those in `scripts/automated_tests/pdsfile_main_test.sh` (serial, under `coverage`), plus `-rA --junitxml`; the holdings variables come from the same `source ~/pdsfile_runner_secrets` that script uses, so no root is written anywhere |

**Which source each run actually imported, proved rather than assumed.** The
interpreter is the main tree's venv, whose editable install appends
`<main tree>/src` to `sys.path`, and there are now **eight** stacked branches
sharing it, so a worktree run could silently measure the wrong tree and make the
whole comparison vacuous. Each run wrote its own `COVERAGE_FILE`, and
`coverage.CoverageData.measured_files()` was read afterwards for its **absolute**
paths:

| Run | top-level `pdsfile` modules measured | count |
|---|---|---|
| baseline | `<worktree>/src/pdsfile/` — `__init__`, `_associations`, `_derived_paths`, `_index_rows`, `_local_fs`, `_opus`, `_path_utils`, `_preload`, `_shelves`, `_sorting`, `pdscache`, `pdsfile`, `pdsviewable`, `preload_and_cache` | **14** |
| this branch | `<main tree>/src/pdsfile/` — the same fourteen, plus **`_properties`** | **15** |

Counting every measured file, not only the top-level ones: **71** on the baseline
side and **72** on this branch, the difference being exactly the one new module.
**0** baseline paths fall outside the worktree prefix, **0** head paths fall
outside the main tree's, and the text `_properties` appears in **0** baseline
paths and **1** head path. Had the worktree run leaked into the main tree's
editable install, `_properties.py` would have been measured there too.

The same provenance question applies to the API dump, which is not run under
coverage. It was answered directly: with the same cwd and `PYTHONPATH` used for
the baseline dump, `pdsfile.pdsfile.__file__` is
`<worktree>/src/pdsfile/pdsfile.py` and `sys.path[1]` is `<worktree>/src`.

### 2. Active §2 gates

| Gate | Result |
|---|---|
| API-freeze manifest test | **passed** — and the dumped surface is byte-identical to the parent's, 733,876 bytes each, same MD5 `442428da…`; §4 |
| Full-data suite, both modes | **passed** — `--mode ns` gains exactly this PR's 10 new ids and nothing else; `--mode s` diff **empty**; §3 |
| `ruff check src/pdsfile tests scripts` | **passed**; the ratchet **shrank** by one code and gained none — §9 |
| Clean-install import check | **passed** (throwaway venv, `pip install .`, full module surface imports) |
| Hosted lint/no-holdings job (`scripts/run-all-checks.sh`, no holdings env vars) | **passed**, **92 passed / 800 skipped** — the parent's 82 plus this PR's same 10 ids, re-measured on the parent tip in the same session to confirm the 82 |
| Adversarial review loop | `critiques/pr-22/round-<k>.md` |

### 3. Full-data suite — ten added ids in `--mode ns`, an empty diff in `--mode s`

Both passes were run on the parent tip and on this branch's head with the same
interpreter and the same holdings. Every `testcase` element of each `--junitxml`
was reduced to one `outcome<TAB>classname::name` line, sorted, and the two files
were diffed with `diff -u`.

| Run | parent `f286dda` | `pr-22-core-finalize` | set diff |
|---|---|---|---|
| `--mode ns` | 848 passed / 34 skipped (882 ids) | 858 passed / 34 skipped (892 ids) | **+10, all new, all passing; 0 removed, 0 changed** |
| `--mode s` | 555 passed / 3 skipped (558 ids) | 555 passed / 3 skipped (558 ids) | **empty** |
| no-holdings | 82 passed / 800 skipped (882 ids) | 92 passed / 800 skipped (892 ids) | **the same +10, nothing else** |

`diff -u` produced **zero output lines** for `--mode s`. For `--mode ns` and for
the no-holdings run it produced exactly ten `+` lines and no `-` line — the same
ten in both:

```
tests.api.test_mixin_import_isolation::test_the_mixin_modules_are_found
tests.api.test_mixin_import_isolation::test_a_mixin_module_does_not_import_pdsfile_pdsfile[_associations]
tests.api.test_mixin_import_isolation::test_a_mixin_module_does_not_import_pdsfile_pdsfile[_derived_paths]
tests.api.test_mixin_import_isolation::test_a_mixin_module_does_not_import_pdsfile_pdsfile[_index_rows]
tests.api.test_mixin_import_isolation::test_a_mixin_module_does_not_import_pdsfile_pdsfile[_local_fs]
tests.api.test_mixin_import_isolation::test_a_mixin_module_does_not_import_pdsfile_pdsfile[_opus]
tests.api.test_mixin_import_isolation::test_a_mixin_module_does_not_import_pdsfile_pdsfile[_preload]
tests.api.test_mixin_import_isolation::test_a_mixin_module_does_not_import_pdsfile_pdsfile[_properties]
tests.api.test_mixin_import_isolation::test_a_mixin_module_does_not_import_pdsfile_pdsfile[_shelves]
tests.api.test_mixin_import_isolation::test_a_mixin_module_does_not_import_pdsfile_pdsfile[_sorting]
```

They are absent from `--mode s` because that invocation is
`tests/pds3file/ tests/rules/pds3/` only, which does not collect `tests/api/`.

**That the ten appear in the no-holdings set is the evidence that the new module
really runs in the hosted job**, rather than the assumption that
`tests/api/conftest.py`'s directory-wide `holdings_free` marker covers it. The
no-holdings run was made with every holdings variable unset (`env -u`), and its
collected total went 882 → 892 with the skip count unchanged at 800 — so the ten
ran, they did not skip.

The parent numbers reproduce PR-21's recorded set, which is what makes this a
comparison against PR-21's baseline rather than against a fresh unrelated
measurement.

Both modes matter and both were run: `--mode s` is the only thing that exercises
the `SHELVES_ONLY` branch, and the moved properties reach it — `exists`, `isdir`,
`childnames` and `label_basename` all call `cls.os_path_exists` /
`cls.os_path_isdir` / `cls.os_listdir` / `cls.glob_glob`, which is where that
branch lives.

**Freshness (§6.6 step 5).** The last change under `src/pdsfile/` is commit
`11ddf91` ("docs: correct three docstring statements the round-3 review measured
wrong") at **02:12:25**. The head runs recorded above postdate it: their
`--junitxml` files were written at **02:15:26** (`ns`) and **02:17:15** (`s`), and
the no-holdings `--junitxml` at **02:17:53**. They are the third of the three
regenerations §6.6 step 5 has required in this loop, one per round; all three
rounds' fixes touched `src/pdsfile/`, every one of them a docstring.

The **superseded** head triples are recorded rather than dropped, each with the
commit its tree was actually at:

| Head triple | `--junitxml` written (ns / s / no-holdings) | Tree at | Reduced sets |
|---|---|---|---|
| 1 | 00:32:43 / 00:34:32 / 00:35:30 | `57134ac` | identical to triple 4 |
| 2 | 01:15:19 / 01:17:08 / 01:17:44 | `0a2925c` (round 1's fixes) | identical to triple 4 |
| 3 | 01:40:56 / 01:42:44 / 01:43:09 | `1490fdb` (round 2's fixes) | identical to triple 4 |
| **4 (current)** | **02:15:26 / 02:17:15 / 02:17:53** | **`11ddf91`** (round 3's fixes) | **the figures above** |

`diff` between consecutive triples is **empty in all three runs** — 0 lines for
`ns`, 0 for `s`, 0 for no-holdings, three times over — which is what a
docstring-only change should do and is measured rather than assumed. The
provenance check was re-run on each: **72** measured files, **0** of them outside
the main tree's prefix, **15** directly under `src/pdsfile/`, `_properties` in
exactly **1** path. So were §10's coverage figures: `_properties.py` still 844
statements / 71 missing / 89% on all four, which is what a docstring change should
leave alone and is checked rather than assumed.

The baseline runs (00:08:41, 00:10:32 and the no-holdings pass) were taken in a
detached `git worktree` at `f286dda` that nothing has touched since.

### 4. API freeze — an empty diff, as a mixin move requires

1. `pytest tests/api/` passes — **26 ids**, the parent's 16 plus this PR's 10.
   `tests/api/api_manifest.json`, `tests/api/manifest_allowlist.json`,
   `scripts/dump_public_api.py` and `tests/api/test_api_freeze.py` are untouched
   (§6.4) — verified with `git diff --stat pr-21-preload..HEAD` over those four
   paths, which is empty. No allowlist entry was added.
2. `scripts/dump_public_api.py` was run against a worktree at the parent tip and
   against this branch's head. The two dumps are **byte-identical** (733,876
   bytes each, identical MD5 `442428da…`, `diff` empty, both stderr streams
   empty).

That is the expected result and the plan says so: the dumper expands a class's
members with `dir(cls)`, which is MRO-wide, and records names, kinds and
signatures — never the defining class. Three things in this PR could in principle
have disturbed it, and none did:

- **`_PropertiesMixin` and `pdsfile._properties`** are underscore-prefixed, so
  the dumper skips them where the submodule import binds them onto the `pdsfile`
  package and where the class name lands in `vars(pdsfile.pdsfile)`. **This PR
  introduces no new non-underscore name anywhere.**
- **The five names that lost their last local reader in `pdsfile.py`** —
  `datetime`, `PIL`, `pdsparser`, `pdsviewable`, `formatted_file_size` — are all
  frozen members of `pdsfile.pdsfile` (`"module"`, `"module"`, `"module"`,
  `"module"`, `"function"`). They are re-exported in the redundant-alias form
  rather than deleted, which is what keeps the dump identical. Measured at HEAD:
  each resolves on both `pdsfile.pdsfile` and `pdsfile._properties` and is the
  **same object** in both.
- **The new module docstring.** `__doc__` starts with an underscore, so
  `build_manifest`'s `if name.startswith('_'): continue` skips it. The dump was
  taken before and after the docstring commit; both are the same 733,876 bytes.

### 5. What moved

Located by symbol. The plan's `:1083–2641` window is against a tip the stack has
moved past; `pdsfile.py` is **3,415 lines** at the parent tip and the block is
the `# Properties` banner region, **672–2230**, 1,559 lines.

| From | Lines at `f286dda` | Content |
|---|---|---|
| `pdsfile.py` | 672–674 | the `# Properties` in-class banner |
| `pdsfile.py` | 675–2034 | **63** properties from `exists` to `infoshelf_path_and_key`, plus `_repair_width_height` — 64 statements |
| `pdsfile.py` | **2036** | **`LATEST_VERSION_RANKS` — does NOT move** |
| `pdsfile.py` | 2037–2230 | `version_info` (staticmethod), `all_versions`, the 64th property `all_version_abspaths`, `viewset_lookup` — 4 statements |

**68 of the block's 69 top-level statements move**: 64 `@property`, one
`@staticmethod` (`version_info`) and three plain methods (`_repair_width_height`,
`all_versions`, `viewset_lookup`). The brief warns that "the lazy-property block"
is a description rather than a predicate and that a reviewer will check the
edges, so the four non-properties are called out here rather than left implicit:
none of them is on the plan's stay-list, all four are inside the banner block, so
all four move.

**The 69th statement is a class attribute and stays.** `LATEST_VERSION_RANKS` is
a class-level `Assign` inside the block, a frozen manifest member
(`{"kind": "data"}`), and the Phase-5 preamble says class attributes stay defined
on `PdsFile`. Its only readers are at `pdsfile.py:3274–3330` in the alternative
constructors, which are on the stay-list; the moved block never reads it (the
attribute sweep in §6 finds no reference). It is left exactly where it was and
given a `# Version ranks` banner, the convention PR-17 established for
`SHELF_CACHE` and PR-18 for `LOG_ROOT_`.

`pdsfile.py`: 3,415 → **1,939** lines. `_properties.py`: **1,686**.
`_path_utils.py`: 220 → 219 (one dead comment line, §7). All counted at HEAD and
**re-counted at each round rather than carried forward** — the convention PR-19
adopted after PR-20's round 2 found a stale count.

#### 5.1 Byte-for-byte equivalence, measured three ways

**(a) The moved text is the exact concatenation of two line ranges of the
parent's file.** `672–2034` and `2037–2230` — 1,363 + 194 = **1,557 lines** —
compare byte-identical to `_properties.py`'s lines **130–1686**, MD5
`a49cd66334d4952bd82c6b9b518ce246` on both sides — the offset re-measured at
HEAD, after rounds 1, 2 and 3 each rewrote part of the class docstring above it,
rather than carried forward from the extraction commit. Round 4 found this offset
stale for a third time, so it is now measured by searching every line range for
the digest rather than by adding up the docstring's growth. Line 2035 is the blank before
`LATEST_VERSION_RANKS`; dropping it rather than 2037 is what leaves exactly one
blank line at the join. This whole-blob comparison rules out reordering and a
dropped blank line, which a per-definition comparison alone would not.

**(b) Per definition, independently.** Each moved definition's source segment
(decorators included, `ast` line span) was extracted from the parent commit and
from `_properties.py` at HEAD: **68 of 68 identical**, **53,113 bytes** in total.
No moved name is still defined in `pdsfile.py` (`0` of 68 remain in the class
body), and `_PropertiesMixin` carries **no** definition that was not on the move
list.

**(c) The remainder of core.** Everything in `pdsfile.py` after the `class
PdsFile(...)` statement — 1,774 lines — is byte-identical to the parent's with
those two ranges deleted and `LATEST_VERSION_RANKS` plus one blank line spliced
in, MD5 `e2be29a1d491692e7281339c7e1db27c` on both sides, **as of the move
commit**. Every edit `pdsfile.py` receives from the move is therefore in its
header (imports) and in the class statement itself.

Two later commits change the class body deliberately, and the difference is
enumerated rather than waved at: of the **37** definitions left in `PdsFile`'s
own body, **34 are byte-identical** to the parent's, and the three that are not —
`_complete`, `from_abspath`, `from_path` — differ **only** by five of the seven
commented-out lines §7 removes from this file. The `diff` is five `-` lines and
zero `+` lines across the three. The other two of the seven trail the `return`
statement in `is_bundle_dir` and `is_bundle_file`, so they fall outside every
definition's AST span and a definition-level comparison cannot see them; they are
covered by the whole-file `diff` in §7 instead.

#### 5.2 No class-level assignment moves, and no new state is created

An AST pass over `PdsFile`'s body counts **61** class-level `Assign` targets at
the parent tip and **61** at HEAD; `_PropertiesMixin` has **0**. Nothing was
lost. `tests/api/test_mixin_collisions.py::test_a_mixin_defines_only_callables_and_properties`
asserts the same thing from the live class objects.

Every attribute the moved bodies write through `self.` or through another PdsFile
object is one of the **41** slots `PdsFile.__init__` already creates. There are
no writes to anything else — measured, not asserted, by walking every
`ast.Attribute` node in Store context. Forty are written on `self`; the
forty-first, `_all_version_abspaths`, is written by `all_versions` onto each
sibling PdsFile it constructs, alongside that sibling's `_recache()`. That is one
of the reasons the contract in §15 is derived by walking every attribute node
rather than only `self.X` and `cls.X`.

`_recache` and `_complete` stay in core. `_recache` is read at **47** sites in
the moved block — 46 through `self.` and one through a sibling PdsFile object
(`pdsf._recache()` in `all_versions`) — never through a module-level name, which
is what makes the split transparent.

#### 5.3 The free-variable sweep was computed, and its "nothing else" is measured

Every `ast.Name` in Load context inside the 69 statements, minus each function's
own bindings, minus builtins, **including decorator arguments** (PR-16's
`_GLOB_CACHE_SIZE` lesson — a body-only sweep misses a name used only in
`@functools.lru_cache(maxsize=…)`). The result is **seven** module-level names
and nothing else:

| Name | sites in the block | where it comes from in `_properties.py` |
|---|---|---|
| `datetime` | 6 | `import datetime` |
| `os` | 9 | `import os` |
| `PIL` | 1 | `import PIL` |
| `pdsparser` | 1 | `import pdsparser` |
| `pdsviewable` | 6 | `from pdsfile import pdsviewable` |
| `abspath_for_logical_path` | 2 | `from ._path_utils import …` |
| `formatted_file_size` | 1 | `from ._path_utils import …` |

Cross-checked a second way, because "nothing else" is the part that is easy to
get wrong: a plain word-boundary grep of the block's text against **all 45**
module-level names of the parent's `pdsfile.py` returns those seven plus
`PdsFile`, `pickle` and `time` — and all three of those are docstring, comment or
string-literal matches with no code site (`PdsFile` in four docstrings, `pickle`
in two `.replace('...', '.pickle')` string literals, `time` in two comments and
one docstring).
So the block references **no** module-level name the seven imports do not supply,
and — separately — **no reference to the `PdsFile` class object at all**, which
is why this mixin needs no function-local deferred import.

`re`, `pdstable`, `pdslogger` and `translator` are *not* used by the moved code,
despite being plausible; they stay in `pdsfile.py` untouched.

#### 5.4 Which imports `pdsfile.py` keeps, and why

Five names lose their last local reader in `pdsfile.py`. All five are frozen
members of `pdsfile.pdsfile`, so deleting them would be a manifest break outside
both forgiveness categories:

| Name | uses in the block | uses left in core | manifest kind |
|---|---|---|---|
| `datetime` | 6 | 0 | `module` |
| `PIL` | 1 | 0 | `module` |
| `pdsparser` | 1 | 0 | `module` |
| `pdsviewable` | 6 | 0 | `module` |
| `formatted_file_size` | 1 | 0 | `function` |
| `os` | 9 | **3** | `module` |
| `abspath_for_logical_path` | 2 | **1** | `function` |

The five move into the header's existing redundant-alias block (`import PIL as
PIL`, `from pdsfile import pdsviewable as pdsviewable`, and so on) — the PEP-484
explicit re-export form the header already uses for eight stdlib modules,
`pdstable` and `defaultdict`. An inline `noqa` and a ratchet grow are both
forbidden, and neither was used. `os` and `abspath_for_logical_path` still have
readers in core and stay plain imports.

### 6. The stay-list, conformed to rather than approximated

The plan's instruction for this PR is as much a prohibition as a task: "nothing
else is extracted in phase 'a' — do not over-extract". What `pdsfile.py` contains
at HEAD, by banner block, against the plan's list:

| Plan's stay-list item | At HEAD |
|---|---|
| class config / registries | 52 class attributes before the first banner (`VOLTYPES` … `_HOLDINGS_ENV`), plus `SORT_ORDER` |
| the sort-config setters | `# DEFAULT FILE SORT ORDER`: `sort_labels_after`, `sort_dirs_first`, `sort_dirs_last`, `sort_info_first` |
| `use_shelves_only` / `require_shelves` / `set_logger` / `set_easylogger` | `# Set parameters for both Pds3File and Pds4File`: all four |
| the constructor and the `_X_filled` slots | `# Constructor`: `__init__`, `new_pdsfile` |
| `new_merged_dir`, `new_index_row_pdsfile`, `copy`, `__repr__` | `# Merged directories, index rows, and object utilities`: all four |
| the bundle/bundleset utilities | `# Utilities`: 11 members, `bundle_pdsfile` … `bundleset_abspath` |
| `_complete`, `_update_ranks_and_vols`, `_recache` | `# Support for alternative constructors`: all three |
| the `child` / `parent` / `from_*` constructors | `# Alternative constructors`: 8 members |
| `is_logical_path` | `# Logical path test` |
| (implicit) the shelf and log class attributes PR-17/PR-18 left | `# Shelf support` (6), `# Log path associations` (`LOG_ROOT_`) |
| (implicit) the module tail | `PdsFile.SUBCLASSES['default'] = PdsFile` and `PdsFile.cache_category_merged_dirs()` |
| (implicit) the class statement | `class PdsFile(...)`, nine mixin bases and `object` |

Plus the one item the plan's list does not name because it is inside the block
being extracted: `LATEST_VERSION_RANKS`, §5.

**`PdsFile`'s own body defines 98 names at HEAD.** Nothing outside the stay-list
is left in it, and nothing on the stay-list left.

### 7. Dead code — the real inventory, and why it is eight lines rather than ~89

The plan says "remove commented-out dead code (~89 lines) — listed line-by-line
in the PR", with "~89" being its 2026-07-17 estimate against the 6,304-line
original. Deferred observation 32 (opened by PR-16's review) already records that
the list has to be rebuilt against the post-Phase-5 module set, because at least
one such line moved out of `pdsfile.py` with its function.

**Scope searched:** `src/pdsfile/pdsfile.py` **and all ten modules this phase
created** (`_associations`, `_derived_paths`, `_index_rows`, `_local_fs`, `_opus`,
`_path_utils`, `_preload`, `_properties`, `_shelves`, `_sorting`) plus
`preload_and_cache.py`.

**Method, two independent passes.** (a) An AST detector over every maximal run of
whole-line comments: strip the `#`, dedent, and keep the run if it parses as
Python *and* contains a statement or a call/subscript expression, so English prose
that happens to parse is rejected. (b) A wider regex sweep for comment lines
containing `return`/`if `/`for `/`def `/`import `/`self.X =`/`this.`/`name = value`
shapes, whose 18 hits were then read one by one in context. The two passes agree
on the same eight lines; the regex pass's other ten hits are prose (`# for
always.`, `# for directories containing only empty directories`, `# returns a
bundleset or bundlename PdsFile.`, `# if there is .targz, treat it as .tar.gz`,
and six similar).

**The eight lines, with location and what each was:**

| File / enclosing definition | Line at the parent tip | Line at HEAD-before-removal | What it was |
|---|---|---|---|
| `pdsfile.py` `is_bundle_dir` | 2293 | 746 | `#return (self.bundlename_ and not self.interior or False)` — an older form of the live `bool(...)` return above it, annotated `# MJTM: 'or False' account for bundle sets` |
| `pdsfile.py` `is_bundle_file` | 2299 | 752 | `#return (self.bundlename and not self.bundlename_ or False)` — the same, for the file predicate |
| `pdsfile.py` `_complete` | 2450 | 903 | `# if not self.exists and not self.category_.startswith('checksums-archives-'): return self` — a widened form of the live `if not self.exists: return self` guard directly above it |
| `pdsfile.py` `from_abspath` | 2894 | 1347 | `# this = PdsFile()` — superseded by the live `this = cls()` |
| `pdsfile.py` `from_path` | 3040 | 1493 | `# this = PdsFile()` — the same |
| `pdsfile.py` `from_path` | 3174 | 1627 | `# if matchobj.group(2) and matchobj.group(3):` — superseded by the live `if len(matchobj.groups()) > 2 and matchobj.group(3):` |
| `pdsfile.py` `from_path` | 3213 | 1666 | `# this.bundletype_ = 'volumes/'` — superseded by `this.bundletype_ = cls.BUNDLE_DIR_NAME + '/'`, which is `'bundles/'` for PDS4 |
| `_path_utils.py` `_clean_join` | (n/a) | 48 | `#     joined = _clean_join(a,b).replace('\\', '/')` — a Windows-path variant, never called; deferred observation 32's line |

**Why two passes were needed.** The AST detector alone finds only five of the
eight, because it groups *maximal runs* of consecutive comment lines and three of
the eight sit directly beneath a line of prose: `# Fill in this.disk_, …` above
one `# this = PdsFile()`, `# Interpret leading parts` above the other, and
`# If there is a matched extension` above the `# if matchobj.group(2) …`. Parsing
prose-plus-code as one dedented block raises `SyntaxError` and the whole run is
rejected. The regex pass has no such grouping and finds all eight. A single-pass
inventory would have been quietly short by three, which is worth recording since
the deliverable is the list itself.

**The divergence from ~89 is reported, not chased.** Running both passes against
`rewrite`'s 6,304-line `src/pdsfile/pdsfile.py` finds **exactly the same eight
lines** — at `:75`, `:3284`, `:3290`, `:3441`, `:3885`, `:4031`, `:4165` and
`:4204` — of 64 regex candidates, the other 56 being prose. So the inventory was
eight before Phase 5 started and is eight now: PR-15 through PR-21 neither added
nor removed a line of commented-out code, and the ~89 estimate does not correspond
to anything that was ever in the file. Nothing was removed to make a number, and
ground rule 9 was not stretched.

**What was deliberately kept**, because it documents behavior rather than being
disabled code: the `CACHE[...]` key-scheme block in `_preload.py` (30 lines of
prose describing a data structure), the `#   (recno, basename, internal_path)`
tuple-shape notes in `_properties.py`, `_sorting.py`'s `#   info_first = 0 or
False: never put info files first` table, the `# Version ranks: / #   _v2 ->
20000` mapping inside `version_info`, and the `### Warning to Dave: I changed all
these to properties because I kept typing them wrong.` note above the bundle
predicates. Ground rule 9's licence here covers only text the interpreter never
sees.

### 8. Base order, the class shape, and the mixin harness

```python
class PdsFile(_AssociationsMixin, _DerivedPathsMixin, _IndexRowsMixin, _LocalFsMixin,
              _OpusMixin, _PreloadMixin, _PropertiesMixin, _ShelfMixin, _SortingMixin,
              object):
```

Alphabetical by mixin class name with `object` last, per
`plans/2026-07-27-addendum-phase5-mixin-base-order.md` (owner, 2026-07-27) and
enforced by
`tests/api/test_mixin_collisions.py::test_the_mixin_bases_are_listed_alphabetically`,
which was run first, before anything else, and at every commit. The Phase-5
preamble's illustration on this branch shows a different order; it was corrected
by PR #110, which merged to `rewrite` **after** this stack branched, so merging
`rewrite` forward to obtain it would drag #110's diff into this PR. The addendum
is the authority here.

`_PropertiesMixin` sorts between `_PreloadMixin` and `_ShelfMixin`, so this PR
does **not** move `PdsFile.__bases__[0]`. That is measured rather than argued from
the alphabet, because `_index_rows.py:254` sniffs
`cls.__bases__[0].__name__ == 'Pds4File'` (deferred observation 49) and
`tests/api/test_mixin_collisions.py:72` pins only `__bases__[-1]`. Dumping
`__bases__[0].__name__`, the full `__bases__` tuple, the full MRO and the sniff's
verdict for all **34** classes in the hierarchy, on the parent tip and at HEAD:

| Property | Classes where parent and HEAD differ |
|---|---|
| `__bases__[0].__name__` | **none** |
| the sniff's verdict (`… == 'Pds4File'`) | **none** — `True` for exactly the same six pds4 rule classes on both sides |
| `__bases__` tuple | **one**: `PdsFile` itself, which gains `_PropertiesMixin` |
| MRO | all 34 — and every one of them **only** by the insertion of `_PropertiesMixin`, checked by deleting `_PropertiesMixin` from each head MRO and comparing to the parent's |

The harness **discovers** its subjects from `PdsFile.__bases__`, so it picked up
`_PropertiesMixin` for free and this PR edits no existing test file. At HEAD it
reports nine mixins defining 4, 12, 5, 5, 3, 5, **68**, 9 and 23 names
respectively — **134** mixin names against `PdsFile`'s own 98.

**The mixin/subclass intersection was re-measured before a line was written,
because a non-empty result is a hard stop rather than something to resolve in the
PR.** With nine mixins the collision and shadowing checks finally have a large
surface to work on:

| | the 68 moved names | all 134 mixin names |
|---|---|---|
| each of the 8 pre-existing mixins, pairwise | **empty** | **empty** |
| `Pds3File` | **empty** | **empty** |
| `Pds4File` | **empty** | **empty** |
| all 33 classes in the subclass hierarchy, rule modules included | **empty** | **empty** |
| `PdsFile`'s own body at HEAD | **empty** | **empty** |

Deferred observation 53's second half predicted this: the names `Pds3File` and
`Pds4File` override are class attributes and translator tables plus `__init__`,
`__repr__` and the four class-configuration classmethods, every one of which is on
this PR's stay-list. The prediction is now measured against the largest mixin in
the phase and holds. `inspect.getattr_static` also confirms all 134 mixin names
resolve through `PdsFile` to the same object the mixin defines.

### 9. Ruff ratchet — 17 codes conserve exactly, one leaves, none is gained

Procedure: for every code in `pdsfile.py`'s entry, the following was run against
the parent's `pdsfile.py`, this branch's `pdsfile.py` and `_properties.py` —

```
ruff check --no-cache --isolated --output-format concise --select <code> \
           --line-length 100 --target-version py310 <file>
```

`--isolated` drops `pyproject.toml`'s `line-length = 100` and would otherwise
report an E501 at 88 columns that the project config does not, so the two settings
are restored explicitly (PR-16 §7 through PR-21 §8 record the same trap), and
`--output-format concise` is required because ruff 0.15's default output no longer
starts a line with the file path.

**Measured at the move commit `a9a6053`**, which is where the split happens and
therefore where conservation is the question:

| Code | parent `pdsfile.py` | → `pdsfile.py` | `_properties.py` | sum |
|---|---|---|---|---|
| E701 | 8 | 4 | 4 | 8 |
| F841 | 4 | 2 | 2 | 4 |
| **RUF005** | **1** | **0** | **1** | **1** |
| SIM114 | 2 | 1 | 1 | 2 |
| UP024 | 9 | 5 | 4 | 9 |
| UP031 | 7 | 6 | 1 | 7 |
| B904, C405, E501, E713, E721, I001, N806, RUF012, SIM102, SIM118, UP004 | 3, 3, 4, 1, 1, 1, 2, 16, 1, 1, 1 | unchanged | 0 | = parent |

**All seventeen conserve exactly.** One of them — **RUF005** — conserves by
leaving `pdsfile.py` entirely, so **`pdsfile.py`'s entry drops it**, 17 codes to
16. Its single occurrence is `self._info[:4] + (shape,)` inside
`_repair_width_height`, now `_properties.py:606`.

**Two more violations disappear at the dead-code commit `59a6405`, and they are a
shrink rather than a leak.** `pdsfile.py`'s E501 count goes **4 → 2** there,
because two of the seven removed lines are 108 and 110 columns long
(`#return (self.bundlename_ …) # MJTM: …` and its twin). The code still triggers
twice, so `pdsfile.py` keeps E501. Total suppressed violations across the two
files: **65 → 63**, never higher.

The **converse** check, which is easy to skip: running the project's whole select
set (`E,F,W,I,UP,B,SIM,C4,A,N,PT,RUF` minus the three project-wide ignores) with
**no** per-file entry reports exactly what each entry lists and nothing else —

| File | reported without its entry | entry |
|---|---|---|
| `_properties.py` | E701 4, F841 2, RUF005 1, SIM114 1, UP024 4, UP031 1 | `["E701", "F841", "RUF005", "SIM114", "UP024", "UP031"]` |
| `pdsfile.py` | the 16 codes below, nothing else | `["B904", "C405", "E501", "E701", "E713", "E721", "F841", "I001", "N806", "RUF012", "SIM102", "SIM114", "SIM118", "UP004", "UP024", "UP031"]` |
| `_path_utils.py` | E701 2, F841 1 | `["E701", "F841"]` — unchanged; the removed line was a comment |

Every code in `_properties.py`'s entry already appears in `pdsfile.py`'s parent
entry, which is what "a split, never an addition" means. `_properties.py`'s import
block was written in the single-line `from X import a, b` form ruff's isort wants,
so it reports **zero** I001 and needs no I001 entry.

**Conservation across the whole phase, the last chance to catch a code that crept
in during PR-16–22.** Phase 5 has created **ten** entries under `src/pdsfile/`,
not nine — `_path_utils.py` has one although it is not a mixin. Their union is
**15** codes:

```
A002 B007 B904 B905 E501 E701 F841 RUF005 RUF059 SIM103 SIM114 SIM118
UP015 UP024 UP031
```

`rewrite`'s `src/pdsfile/pdsfile.py` entry, before Phase 5 touched anything, was
**25** codes:

```
A002 B007 B018 B904 B905 C405 E501 E701 E713 E721 E722 F841 I001 N806
RUF005 RUF012 RUF059 SIM102 SIM103 SIM114 SIM118 UP004 UP015 UP024 UP031
```

**The union is a subset: 15 of 15 appear there, and the set difference in the
other direction is 10 codes** (B018, C405, E713, E721, E722, I001, N806, RUF012,
SIM102, UP004) — codes that stayed with the lines that carry them, or that PR-15
removed outright (E722, the bare `except:` of bug 7). So across the whole phase
**no private module's entry contains a code ruff did not already suppress for
`pdsfile.py` on `rewrite`**, which is what "a split, never an addition" has to
mean at the end of the phase, and nothing crept in during PR-18–22.

### 10. The tests that pin this code

The moved block is the most heavily exercised part of the package.
`tests/pds3file/test_pds3file_blackbox.py`, `…_blackbox_cached.py` and
`…_whitebox.py` are almost entirely property assertions, and
`test_pds3file_blackbox_cached.py`'s pattern — read the property twice, assert
both reads agree — exists precisely to exercise the fill-then-`_recache` shape
this mixin now owns.

Coverage of the delivered module, from the head full-data run (coverage's own
statement set):

| File | statements | missing | coverage (statement + branch) |
|---|---|---|---|
| `_properties.py` | 844 | 71 | **89%** |
| `pdsfile.py` (after the move) | 906 | 90 | 87% |
| `_path_utils.py` | 104 | 12 | 84% |

### 11. Negative controls — the moved code is reached, and reached through the new module

An outcome-set diff proves nothing about a body no test executes. Six mutations
were applied to the delivered `_properties.py` and `_path_utils.py`, each run
against `tests/pds3file/ tests/core/ tests/pds4file/ --mode ns` (**641 passed / 24
skipped** unmutated), then reverted:

| Mutation | Result |
|---|---|
| `exists` returns `True` unconditionally | **7 failed** — across pds3 blackbox, pds3 whitebox, pds3 cached and pds4 blackbox |
| `html_path` loses the `()` on `self._recache()` — **PR-15's bug-1 fix, reverted** | **1 failed**: `tests/core/test_pdsfile_caching.py::TestHtmlPathCaching::test_the_filled_value_is_written_back_to_the_cache` |
| `mime_type` returns `'application/octet-stream'` | **5 failed** |
| `version_info` returns rank 111111 for the current version | **3 failed**, all `test_version_ranks` |
| `formatted_size` returns `'WRONG'` | **2 failed** |
| `abspath_for_logical_path` raises (does the moved code still reach `_path_utils`?) | **28 failed** |

**The `html_path` control is the one the brief asks for by name.** PR-15's bug 1
was `self._recache` missing its parentheses in this property; PR-15 fixed it and
pinned the fix with a regression test. This PR moves the fixed version into a new
module, and re-introducing the bug in the moved copy turns exactly PR-15's
regression test red — so that test still reaches the code it was written for.

### 12. The monkeypatch audit — the check the set diff cannot perform

Deferred observation 29 (opened by PR-16's round-1 Major, owned by "PR-17 onward")
says an extraction sweep must also ask **which namespaces the tests patch**, not
only which globals the code reads. A test whose patch lands on a module the moved
code no longer resolves through keeps passing while exercising nothing, and
§6.2's outcome-set diff compares pass/fail — so it is *structurally blind* to this
class of defect. **This PR's set diff would have looked the same in every case
below, including a broken one.**

**Enumeration.** Every `monkeypatch.setattr` / `setitem` / `delattr` / `setenv` /
`delenv`, `mock.patch`, `patch(`, `patch.object` and bare `setattr(` in `tests/`,
`scripts/` and `src/` — **20 sites, all `monkeypatch`**; the tree still uses no
`unittest.mock` at all:

| Target | Sites | Names one of the 68 moved symbols? | Does this PR's moved code reach it? |
|---|---|---|---|
| `Pds3File.CACHE` (`tests/core/conftest.py:28`, `test_pdsfile_caching.py:112,126`) | 3 | no — a class attribute that stays on the class | **yes** — `_volume_info`, `description` and `version_ranks` read `cls.CACHE`, and `_recache` writes it |
| `Pds3File.preload` (`test_pdsfile_caching.py:127`) | 1 | no — PR-21's symbol, audited there | no |
| `Pds3File.shelf_path_and_key_for_abspath` (`test_pdsfile_path_resolution.py:120,129,137,155`) | 4 | no — PR-17's symbol | **yes** — `infoshelf_path_and_key` calls it through `cls.` |
| `abspath_for_logical_path.__globals__['glob']` (`test_pdsfile_path_resolution.py:92`) | 1 | no — PR-16's fix site | **yes, indirectly** — `internal_link_info` calls `abspath_for_logical_path` |
| `pdsviewable.ICON_SET_BY_TYPE` (`test_pdsviewable_iconset_for.py:47`) | 1 | no — an attribute of a shared module object | **yes** — `_iconset` reads it |
| `Pds3File`/`Pds4File.LOCAL_PRELOADED`, `.LOCAL_HOLDINGS_DIRS` (`test_pdsfile_path_resolution.py:58,59,71,72,85,86`) | 6 | no — class attributes | no |
| `monkeypatch.setenv` / `delenv` (`test_pdsfile_path_resolution.py:54,70,83,84`) | 4 | no — environment, not a namespace | no |

**No patch site names any of the 68 moved names** — the intersection is empty,
computed rather than eyeballed. A regex over `tests/`, `scripts/` and `src/` for
*direct assignment* to any of the 68 — the form that is not a `monkeypatch` and is
easy to miss — returns 11 hits, **all** of them `self.X = …` on unrelated objects
(`PdsViewable.url/width/height/alt` inside `pdsviewable.py`, and two test stub
classes defining their own `childnames` and `icon_type`). None assigns onto a
`PdsFile` class or onto a module namespace. Nothing anywhere rebinds
`pdsfile.pdsfile.<name>`, and nothing outside `src/pdsfile/` mentions
`pdsfile._properties`.

**Why the four reachable mechanisms survive the move**, and why none needed
changing:

- `Pds3File.CACHE` and `Pds3File.shelf_path_and_key_for_abspath` are reached by
  the moved code through `cls.`, an attribute lookup on the class at run time. A
  patch onto `Pds3File` wins over any base, so it lands in front of the moved code
  exactly as it did before.
- `abspath_for_logical_path.__globals__['glob']` is the move-proof form PR-16's
  round-1 Major produced: it patches the function's *own* globals, which are
  `_path_utils`'s module dict, whichever module the caller resolves the name
  through. Measured at HEAD: `pdsfile.pdsfile.abspath_for_logical_path` and
  `pdsfile._properties.abspath_for_logical_path` are the **same object**.
- `pdsviewable.ICON_SET_BY_TYPE` patches an attribute *inside* the shared
  `pdsfile.pdsviewable` module object. Measured at HEAD:
  `pdsfile.pdsfile.pdsviewable is pdsfile._properties.pdsviewable` is `True`, so
  both namespaces reach the same dictionary.

**Every patch mechanism the moved code reaches was forced to answer wrongly, and
each turned its own test red:**

| Forced-wrong control | Went red |
|---|---|
| the `Pds3File.CACHE` patch removed from `tests/core/conftest.py` | `TestHtmlPathCaching::test_the_filled_value_is_written_back_to_the_cache` |
| the four `shelf_path_and_key_for_abspath` patches removed | 3 ids in `TestInfoshelfPathAndKey` |
| the `glob` stub made to answer with a non-empty list instead of `[]` | `TestHoldingsEnvironmentVariable::test_a_class_does_not_borrow_another_class_holdings_root` |
| the `pdsviewable.ICON_SET_BY_TYPE` patch removed | 9 ids in `TestIconsetFor` |

One of these needed a second attempt, and the first attempt is recorded because
it is a real measurement about the suite: **removing** the `glob` stub outright
leaves every test green on this machine (531 passed), because the stubbed call is
`glob.glob('/Library/WebServer/Documents/holdings*')` and on Linux the real call
returns `[]` anyway. The stub is a portability guard, not a load-bearing patch
here. Forcing it to answer *wrongly* — a non-empty list — is the control the
brief actually asks for, and that does turn the test red. Recorded as deferred
observation 61.

### 13. Consumer smoke — outcome unchanged

The gate is **same outcome as baseline**, not "passes"
(`critiques/baselines/consumer-smoke-baseline.md`).

| Check | Baseline | This branch |
|---|---|---|
| A — rms-opus import paths | 4/4 resolve, 0 failures | **4/4 resolve, 0 failures** |
| B — rms-viewmaster startup | 5 ok, 3 pre-existing failures | **5 ok, 3 failures — the same three** |

The three Check-B failures are still `pdsfile.cache_lifetime` (raises),
`pdsfile.DEFAULT_CACHING` (absent) and the same `cache_lifetime` read inside
`get_page_cache()`. None became a pass. `pdsfile.pdsfile.repair_case` still
resolves.

Check B is load-bearing here in a specific way: `create_app()` → `init_once()`
preloads rms-viewmaster's own holdings configuration, which walks category
directories and constructs PdsFile objects — so the moved `exists`, `isdir` and
`childnames` properties run end to end against a **different holdings tree** than
this repo's tests use, outside this repo's harness. The run's log shows the
`Pre-loading:` lines, the `Missing category dir:` warnings for the categories
absent there, and `PdsFile preloading completed`.

Environment note carried from the baseline: the check ran under the pdsfile venv's
interpreter with rms-viewmaster's `site-packages` appended to `PYTHONPATH`,
because that venv lacks pdsfile's declared `range_ex` dependency, and with the
holdings environment variables set. rms-viewmaster is at `a0d05e2`; rms-opus is at
`73cb6de7`.

### 14. Clean install

`scripts/clean_install_check.sh` passes inside `run-all-checks.sh`.
`_properties.py` is picked up by the existing `include = ["pdsfile*"]` package
glob with no packaging change, and the gate imports the whole manifest module
surface — `pdsfile.pdsfile` is in `scripts/check_runtime_imports.py`'s list and
cannot import if `_properties.py` is missing from the distribution.

### 15. The class docstring is derived, and verified in both directions

Deferred observation 54 records that the mixins' "state contract" docstrings are
hand-written, drift, and are mechanically derivable; PR-19's rounds 1, 2 and 3 and
PR-20's rounds 2 and 3 each found one wrong. The entry names PR-22 as the owner of
turning the derivation into a *test*. **This PR does not build that test** — the
coordinator's standing direction (common brief §5.1) is that entries 53 and 54
stay open and that no check beyond entry 42 is built here, and PR-17 paid two
review rounds for taking up an unasked-for check. What this PR does is apply the
method by hand, in the widened form PR-19's rounds 3 and 4 settled, and record it
so the next reader can check the method rather than trust the result.

The derivation walks **every** `ast.Attribute` node in the class body, resolves
the root of its value expression, keeps the attribute if its name is part of the
`PdsFile` surface (core body, any mixin, an `__init__` slot, or a name defined
only on `Pds3File`/`Pds4File`), and **excludes the names the mixin itself
defines**.

The receiver list is printed in full so the scoping is checkable. The module has
**71** distinct receiver expressions; **8** of them carry at least one
PdsFile-surface attribute: `self`, `cls`, `child`, `parent`, `pdsf`,
`self.parent()`, `version_dict[key]` — and `os.path`, which is a **false
positive**, matched only because `os.path.basename` shares a name with the
instance attribute `basename`. It is named rather than filtered out, because a
derivation that silently drops what it cannot classify is exactly the failure
entry 54 is about. The **five** genuine non-`self`/`cls` receivers — `child`,
`parent`, `pdsf`, `self.parent()` and `version_dict[key]` — are the reason the
walk cannot be restricted to `self.X` and `cls.X`: `viewset_lookup` reaches
`pdsfiles_for_basenames` and `viewable_childnames_by_anchor` through `parent`,
which a `self.`-only walk would have missed outright, and `all_versions` writes
`pdsf._all_version_abspaths`, a name such a walk *would* have found — it is read
through `self` in `all_version_abspaths` — but would have classified as read-only.
So: two names missed and one write mis-classified.

**Direction 1 — every derived name appears in the docstring: 114 of 114, nothing
missing.** Direction 2's residue is prose only: `A`, `PIL`, `WRITTEN`, `X`,
`_X_filled`, `__init__`, the five sibling-mixin class names, and the three module
names `_associations`, `_local_fs`, `_sorting`.

Two claims in the docstring are measured rather than reasoned. `IDX_EXT` and
`LBL_EXT` are read off `cls` but defined only on `Pds3File` and `Pds4File`:
`getattr(PdsFile, 'IDX_EXT')` raises `AttributeError` at HEAD, as it did before
the move, so those three properties behave on a bare `PdsFile` exactly as they
always have. And the 41 instance slots the mixin writes are exactly the 41
underscore-prefixed instance attributes it reads — set equality, not
approximation; `_recache` is the only underscore name read but not written, and it
is a method.

### 16. Entry 42 — the back-import check, and the two ways it was seen red

`tests/api/test_mixin_import_isolation.py`, 10 ids, holdings-free.

Entry 42's design note is binding and was followed: **no third AST walk.** PR-17's
syntactic guard produced the only two Majors of five review rounds, both inside
the guard, because an AST approximation of a runtime fact has a case matrix that
only grows. The check here loads each mixin module in a fresh interpreter and asks
`sys.modules`.

**The obstacle the design note does not mention, found by measurement rather than
by reading.** `src/pdsfile/__init__.py` does `from .pds3file import *`, so
importing *any* `pdsfile.*` submodule executes the package `__init__` and pulls
`pdsfile.pdsfile` into `sys.modules`. The naive probe — `import pdsfile._preload;
assert 'pdsfile.pdsfile' not in sys.modules` — reports `True` for **all ten**
private modules, i.e. it would be red for every module always. A check that can
never pass is as useless as one that can never fail, and this is the shape of
mistake entry 42 exists to prevent.

The fix keeps the check behavioral. The probe installs a **stub `pdsfile` package
module** in `sys.modules` — a real `importlib.machinery.ModuleSpec` with
`submodule_search_locations` pointing at the package directory, with no
`__init__.py` executed — and then imports the module under test by name. Relative
imports (`from ._path_utils import …`) and in-package absolute imports
(`from pdsfile import pdscache`) both resolve normally through those search
locations; only the package `__init__`'s star-imports are excluded. What is left
is exactly the property the preamble cares about: *loading this mixin module must
not require `pdsfile.pdsfile`.*

**Shape: one subprocess per module**, ten in all, ~1.0 s for the file. A single
interpreter importing all ten in sequence could mask a violation two ways — the
first module's back-import would put `pdsfile.pdsfile` in `sys.modules` for every
later module, and a module that imports a sibling would load that sibling before
its own probe ran. A process that has loaded exactly one of them can do neither.
The subjects are discovered from `PdsFile.__bases__` in the parent process (which
may import `pdsfile.pdsfile` freely), so a future mixin is covered on arrival, and
`test_the_mixin_modules_are_found` asserts the discovery found at least nine so
the parametrization cannot shrink to nothing and pass by not existing. The probe
also prints the `__file__` it actually loaded and the test asserts it equals the
one the parent measured, so a stale copy elsewhere on `sys.path` cannot answer for
it — the `pythonpath` trap PR-18 §9 documents, applied to a construction that is
itself a subprocess-and-import.

**Proof it can fail.** Entry 42 says the case worth testing is not `PdsFile`
itself — that raises a circular-import error and fails collection loudly — but
some *other* name already bound in the core module. Both demonstrations use
`repair_case`, which `pdsfile.py` binds at its line 40, and both were made on the
real tree and reverted:

| Demonstration | Silent in normal import order? | Check's verdict | Which assertion caught it |
|---|---|---|---|
| `from pdsfile.pdsfile import repair_case` at the **head** of `_associations.py` | **yes** — `import pdsfile.pdsfile` succeeds, `_associations.repair_case is pdsfile.pdsfile.repair_case` is `True`, and the rest of `tests/api/` stays green (25 passed) | **red** — `[_associations]` fails | the subprocess `returncode`: the probe order re-enters the partially initialized module and raises `ImportError: cannot import name '_AssociationsMixin' … (most likely due to a circular import)` |
| the same import at the **tail** of `_properties.py`, after the class | **yes**, and more completely: no exception anywhere, in any import order, and the probe subprocess **exits 0** | **red** — `[_properties]` fails | the `sys.modules` assertion: `CORE_PRESENT` is `'True'`, `assert 'True' == 'False'` |

The second is the one that matters: it is caught **only** by the `sys.modules`
assertion, which is what proves that half of the check is load-bearing rather than
decoration on an exit-code test. Both mutations were reverted and `tests/api/`
returns to 26 passed; `git status` is clean over `src/` and `tests/`.

### 17. Deferred observations

Entry 29 is the one this PR was told to act on, and §12 is the action. It is
**not** resolved — it is a per-PR step, owned by "PR-17 onward" — so it stays open
for whatever PR next extracts. **Entry 42 is resolved by this PR** (§16) and
marked so. Entries 53 and 54 are deliberately **not** taken up, per the
coordinator's standing direction; §8 and §15 re-measure what each is about,
with nine mixins and the largest one in the phase in scope, and both entries stay
open with their owners unchanged. Entry 32 (the commented-out line in
`_path_utils.py`) is **resolved** — §7 removes the line and rebuilds the list
against the post-Phase-5 module set, which is what the entry asked for. Entry 45
(`A002`'s home) and entry 49 (the `__bases__[0]` sniff) are re-measured here and
unchanged. No other entry in 1–60 is resolved or invalidated.

Four entries are **added**: **61** by the executor's own measurements (the `glob`
stub in `test_pdsfile_path_resolution.py` is a portability guard whose removal is
invisible on Linux, so "delete the patch and watch it go red" is not a valid
control for it), and **62**, **63** and **64** by the round-1 review
(`filename_keylen` fills its slot without calling `_recache()`; the back-import
guard covers the nine mixin modules and not `_path_utils.py`; six lines of
commented-out `MemcachedCache.get_multi` code remain in `pdscache.py`, outside
this PR's dead-code scope). None of the three was taken up here.

### 18. Phase closing — Phase 5 in one table

`src/pdsfile/pdsfile.py` at each PR boundary, and what left it:

| Boundary | `pdsfile.py` | Δ | Modules created |
|---|---|---|---|
| `rewrite` @ `807956a` | **6,304** | — | — |
| PR-15 `pr-15-latent-bug-fixes` | 6,308 | +4 | — (bug fixes, `_HOLDINGS_ENV`) |
| PR-16 `pr-16-path-utils` | 6,125 | −183 | `_path_utils.py` |
| PR-17 `pr-17-shelves-local-fs` | 5,436 | −689 | `_shelves.py`, `_local_fs.py` |
| PR-18 `pr-18-derived-paths` | 5,125 | −311 | `_derived_paths.py` |
| PR-19 `pr-19-opus-index-rows` | 4,593 | −532 | `_opus.py`, `_index_rows.py` |
| PR-20 `pr-20-associations-sorting` | 3,837 | −756 | `_associations.py`, `_sorting.py` |
| PR-21 `pr-21-preload` | 3,415 | −422 | `_preload.py` (+ `preload_and_cache.py` → shim) |
| **PR-22 `pr-22-core-finalize`** | **1,939** | **−1,476** | **`_properties.py`** |

Ten private modules, 5,120 lines of them (`_associations` 373, `_derived_paths`
314, `_index_rows` 328, `_local_fs` 437, `_opus` 304, `_path_utils` 219,
`_preload` 578, `_properties` 1,686, `_shelves` 356, `_sorting` 525), plus a
16-line `preload_and_cache.py` shim.

**The pass/fail set across the whole phase**, against the `rewrite` @ `807956a`
baseline, with every id that moved accounted for:

| Boundary | `--mode ns` | ids | Δ ids | `--mode s` | no-holdings |
|---|---|---|---|---|---|
| `rewrite` @ `807956a` | 790 p / 34 s | 824 | — | 555 p / 3 s (558) | 24 p / 800 s |
| PR-15 | 825 p / 34 s | 859 | **+35** — all under `tests.core.*`, the regression tests for the seven bug fixes | 555 p / 3 s (558) | 59 p / 800 s |
| PR-16 | 825 p / 34 s | 859 | 0 | 555 p / 3 s (558) | 59 p / 800 s |
| PR-17 | 846 p / 34 s | 880 | **+21** — `tests/api/test_mixin_collisions.py` (13) + `tests/core/test_shelf_sidecar_record.py` (8) | 555 p / 3 s (558) | 80 p / 800 s |
| PR-18 | 846 p / 34 s | 880 | 0 | 555 p / 3 s (558) | 80 p / 800 s |
| PR-19 | 848 p / 34 s | 882 | **+2** — the two ids deferred observation 48 required | 555 p / 3 s (558) | 82 p / 800 s |
| PR-20 | 848 p / 34 s | 882 | 0 | 555 p / 3 s (558) | 82 p / 800 s |
| PR-21 | 848 p / 34 s | 882 | 0 | 555 p / 3 s (558) | 82 p / 800 s |
| **PR-22** | **858 p / 34 s** | **892** | **+10** — `tests/api/test_mixin_import_isolation.py`, §16 | 555 p / 3 s (558) | **92 p / 800 s** |

824 + 35 + 21 + 2 + 10 = **892**. **Every id added across Phase 5 is a new test
id, in a PR that recorded it; no id was ever removed, and no id ever changed
outcome.** `--mode s` is 558 ids and 555 passed / 3 skipped at every one of the
nine boundaries — it collects `tests/pds3file/` and `tests/rules/pds3/` only, so
none of the added ids reaches it. The no-holdings column moves in lock-step with
the `ns` column because every id added in the phase is holdings-free.

### 19. The ~1,750-line target, and why HEAD is 1,939

The plan's arithmetic is 6,304 − ~2,930 (PR-16–21) − ~1,550 (the property block) −
~89 (dead code) = ~1,735, stated as "~1,750". HEAD is **1,939**, +189 against the
stated target and +204 against the arithmetic. Decomposed, every term measured and
reconciled against §18's per-PR deltas:

| Term | Plan | Actual | Δ |
|---|---|---|---|
| PR-15's regression-test support (`_HOLDINGS_ENV` and the bug fixes) | not in the model | +4 | **+4** |
| leaves in PR-16–21, summing §18's six deltas (each net of the header lines that PR added) | ~2,930 | 2,893 | **+37** |
| the property block, net of this PR's header rework | ~1,550 | 1,553 | −3 |
| commented-out dead code in `pdsfile.py` | ~89 | 7 | **+82** |
| the module docstring the plan also asks for, plus two rounds of corrections to it | not budgeted | 74 + 3 + 1 | **+78** |
| the `# Version ranks` banner for the class attribute left behind | not budgeted | 6 | **+6** |
| | | | **= +204** |

Read forwards: 6,304 + 4 − 2,893 − 1,553 + 6 − 7 + 78 = **1,939**. The earlier
"2,889 lines leave in PR-16–21" was the net change from `rewrite` to PR-21's tip,
which silently absorbs PR-15's +4; splitting the two makes the decomposition
reconcile against §18 line by line.

Per commit: 3,415 → 1,862 (the move) → 1,868 (the banner) → 1,861 (dead code) →
1,935 (the docstring) → 1,938 (round 1's docstring corrections) → 1,939
(round 2's).

**The delta is explained rather than chased**, per the brief: the target is a
check on over- and under-extraction, and on that question it is satisfied — §6
shows every stay-list item present and nothing beyond it, and nothing was
extracted to reach a number. The two largest terms are a docstring the same plan
section asks for in its next sentence, and an estimate of commented-out code that
does not correspond to anything that was ever in the file (§7 measures eight such
lines on `rewrite`, not 89).

### 20. Review loop

| Round | Verdict | Findings | Record |
|---|---|---|---|
| 1 | goal met | 0 Major, 8 Minor (all accepted and fixed; **four in `src/pdsfile/` docstrings, three in this record, one a missing subprocess timeout in the new test** — none in the extracted code), 3 Deferred (added as entries 62, 63 and 64) | `critiques/pr-22/round-1.md` |
| 2 | goal met | 0 Major, 8 Minor (all accepted and fixed; **three in `src/pdsfile/` docstrings, five in this record and the sub-plan** — none in the extracted code), 1 Deferred (added as entry 65) | `critiques/pr-22/round-2.md` |
| 3 | goal met | 0 Major, 7 Minor (all accepted and fixed; **three in `_properties.py`'s docstring, four in this record and the sub-plan** — none in the extracted code), **0 new Deferred** | `critiques/pr-22/round-3.md` |
| 4 (scoped) | goal met | **0 Major, 3 Minor** (all accepted and fixed; **all three in this record, the sub-plan and the deferred-observations file — none under `src/`**), **0 new Deferred**; 21 of the 23 prior findings confirmed resolved by re-measurement, the other 2 regressed by two lines and re-fixed | `critiques/pr-22/round-4.md` |

*(Rows are written only after the round they describe has run and its record file
exists on disk — the rule PR-18's round-3 Major established. No row is written for
a round that has not run.)*

**Round 1 found no Major, and the one Minor that mattered was a claim about
control flow that the name-coverage derivation in §15 structurally could not
check.** Both docstrings said the 64 properties share one shape — fill an
`_X_filled` slot, then `_recache()`. Measured: **40** fill a slot, **39** of those
`_recache()`, and **24** hold no slot at all and recompute on every access. §15's
derivation verifies that every *name* the code reaches appears in the docstring,
in both directions; it says nothing about a sentence describing what the bodies
*do*. Both docstrings now give the measured split and name all 24. A first attempt
at the fix added a second unmeasured claim ("most of which are one-line
compositions"), which was measured before committing and is false — 8 of the 24
are a single `return` — and the committed text says so.

Three more were figures in this record: the moved blob's destination range
(measured on an earlier draft and not re-measured after the class docstring was
rewritten), an off-by-one that made §5's two table rows sum to 69 statements
rather than 68, and `_recache`'s site count, which counted `self._recache` and
omitted the one call through a sibling object that the same subsection discusses
two paragraphs earlier. Two were inventory slips in the module docstring's module
map (`from_filespec` is not an OPUS-id constructor; two `_path_utils` names and
two `_preload` constants were missing), one was a stale word ("eleven" for a block
of ten imports), and one was a genuine robustness gap in the new test — the probe
subprocess had no timeout, so a module that blocked at import time would have hung
the gate rather than failed it.

**Round 1's fixes touched `src/pdsfile/`, so §6.6 step 5's regeneration rule
applies and the full-data record above is a regenerated one.** The superseded
triples and the empty diffs between them are in §3.

**Round 2 found no Major and eight more Minor, three of them in `src/pdsfile/`
docstrings and five in this record and the sub-plan — and the first is round 1's
Minor 1 one level down.** Round 1's fix enumerated the 24 no-slot properties and
added a sentence about what the sixteen multi-statement ones read; that sentence
is wrong for four of the sixteen. A second attempt at it ("eight are a single
`return`; the other sixteen are two to seven statements") was measured before
committing and is wrong too — three of the eleven single-statement ones are not a
bare `return`. The sentence is now gone; the enumerated list is the claim.
Round 2's other two `src/` findings are round 1's own fixes not applied
consistently: the 39-of-40 `_recache` exception reached `_properties.py`'s
docstring and not `pdsfile.py`'s map, and the map became a complete inventory when
round 1 added two `_path_utils` names to it, which made two other lists in it
short by one name each.

The five record findings are: §19's heading against its own body (1,935 vs
1,938); §11 saying seven mutations above a table of six; "PR-16–21 removed 2,889
lines net", which is the net change from `rewrite` and silently absorbs PR-15's
+4, so §19's table now carries the two separately and reconciles against §18 row
by row; the sub-plan's §2.4 still carrying the 46 that round 1 corrected to 47 in
§5.2; and the figures that move with each docstring edit, which are re-measured at
the final HEAD rather than carried forward.

**Round 2's fixes also touched `src/pdsfile/`, so the record was regenerated a
second time.** All three of §3's runs are identical across all four head triples.
Two entries in the executor's own sub-plan were corrected in the same pass without
a reviewer raising them: §2.4's "15 sibling-mixin methods" (17 under the widened
walk) and §2.6's "all nine modules this phase created" (ten — `_path_utils.py` is
private and has its own ratchet entry, but is not a mixin).

**Round 3 found no Major and seven more Minor, every one of them a consequence of
rounds 1 and 2's own fixes rather than of the move.** Three were in
`_properties.py`'s docstring: the contract row headed "core lazy properties read"
lists four core properties that hold no slot and so are not lazy under the
definition the same docstring gives four paragraphs earlier; "viewset_lookup reads
through child" named the wrong method (`child` is `all_viewsets`' receiver, and it
contributes nothing the widened walk needs); and the file's two-line banner still
carried the pre-round-1 claim that the lazy properties fill a slot *and* write
back to the cache. Four were figures here and in the sub-plan: §5.1(c)'s 1,775
lines is 1,774 — the figure counted a `split('\n')` list whose last element is the
empty string a trailing newline produces, and the MD5 quoted beside it is the
digest of exactly that 1,774-line region, so the digest was right and the count was
not; §15's "six genuine non-`self`/`cls` receivers" is five, the sixth being the
`os.path` false positive the same sentence names; §15's "three names a `self.`-only
walk would have missed" is two names missed outright plus one *write*
mis-classified as a read; and the sub-plan's +82 dead-code term subtracts
`pdsfile.py`'s seven from ~89, not the eight-line whole-module-set count.

Round 3 raised **no new Deferred item** — it confirmed entries 61–65 already cover
everything it found that is out of scope, and verified entry 63's parenthetical by
running the probe against `_path_utils.py` itself.

It also went one step further than rounds 1 and 2 on the entry-42 check, and the
extra step is worth recording: besides the head-placed and tail-placed imports it
broke the check with a module-level
`importlib.import_module('pdsfile.pdsfile')` — **a spelling no AST walk over
import statements can see at all**, and exactly the case entry 42's design note
gives as the reason not to write a third AST walk. It also confirmed the two
controls the design needs: a *function-local* deferred import leaves the check
green, and the naive probe without the stub package is red for all ten private
modules, so the stub construction is necessary rather than decorative.

**Round 3's fixes touched `src/pdsfile/` too, so the record was regenerated a third
time.** One finding was not fixed in place: the move commit `a9a6053`'s message
says "64 lazy properties" where 40 are lazy and 24 recompute. Amending it means
rewriting eight commits, and this record, three round records and five commit
messages cite the current hashes — a rebase would invalidate every one of those
citations to fix one adjective. The reviewer's own suggestion, to state it
correctly in the PR description, is what was done; `critiques/pr-22/round-3.md`
records the decision.

**Round 4 is §6.6's scoped fourth round** — "confirm the prior round's findings
are resolved; raise only new Major findings" — and it returned **zero Major**. It
re-measured all 23 prior Minor fixes and found 21 correct in the tree and **2
regressed by two lines**: round 1's Minor 3 and round 2's Minor 8 are the same
figure, `_properties.py`'s size and the moved blob's offset inside it, and round
3's own docstring fix moved them again after the round-3 recording commit had set
them. The byte-equivalence conclusion was never in doubt; only the coordinates
were. The fix is not only the number — §5.1(a) now obtains the offset by searching
every line range for the digest instead of by adding up the docstring's growth,
which is the method that cannot go stale. The other two findings were the
sub-plan's round summary, which still described two rounds, and one clause here
that called `time`'s three textual matches three comments when one of them is a
docstring.

**None of round 4's three findings touches `src/pdsfile/`**, so §6.6 step 5's
regeneration rule does not apply and the full-data record in §3 carries forward.
§6.6's hard cap is four rounds and this was the fourth, so **no fifth reviewer was
run**; the three Minors were fixed in place after it, which is what the cap allows
and what this executor's brief directs.

**The loop's arithmetic across four rounds: 26 findings, 0 Major.** Ten were
statements in docstrings under `src/pdsfile/`, fifteen were figures or labels in
this record and the sub-plan, and one was a missing subprocess timeout in the new
test. **Not one was in the extracted code** — the same result PR-19, PR-20 and
PR-21 each produced, here on the largest single move of the phase.

---

## PR-23 — `style: ruff-clean core modules`

**Branch:** `pr-23-ruff-core`, based on and opened against `rewrite` @ `96e5960`.
PR-23 is **not stacked** (owner, 2026-08-03,
`plans/2026-08-03-addendum-pr23-24-owner-decisions.md` decision 4), so its
baseline is `rewrite` itself and its reviewer diff is `git diff origin/rewrite...HEAD`.

**Sub-plan:** `plans/2026-08-03-pr-23-subplan.md`.
**Deliverable:** `ruff check` only. No `ruff format`, no `ruff format --check`
gate, no `# fmt: off` guards — the churn checkpoint ran on 2026-08-03 and the
owner dropped the reformat entirely. No test is added and no golden is touched,
so the §6.2 gate is an **identical** per-test set in both modes.

### 1. Environment

| Item | Value |
|---|---|
| Python | 3.12.3 |
| ruff | 0.15.22 |
| Suite driver | the command lines of `scripts/automated_tests/pdsfile_main_test.sh` — serial, under `coverage run`, plus `-rA --junitxml` |
| Holdings | `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` at the limited testing copy the goldens are tuned to |
| Baseline tree | a detached worktree at `96e5960`, measured today rather than copied from a record |

### 2. Full-data suite — an identical set in both modes

Both runs were regenerated after the last change under `src/pdsfile/`.

| Mode | Baseline @ `96e5960` | PR-23 head | ids | Diff |
|---|---|---|---|---|
| `--mode ns` | 858 passed / 34 skipped | **858 passed / 34 skipped** | 892 both | **empty** |
| `--mode s` | 555 passed / 3 skipped | **555 passed / 3 skipped** | 558 both | **empty** |

The comparison is id-by-id from the two `junitxml` files, not a count check:
every `testcase` is reduced to `classname::name -> outcome` and the two maps are
compared three ways — ids only in the baseline, ids only in the head, and ids
whose outcome changed.

```
ns: 892 vs 892 ids; only-in-baseline 0, only-in-head 0, outcome changed 0
 s: 558 vs 558 ids; only-in-baseline 0, only-in-head 0, outcome changed 0
```

**Non-vacuity, at file level.** `coverage.CoverageData.measured_files()` for the
head run lists **15 of the 15** modules directly under `src/pdsfile/` —
`__init__.py`, `_associations.py`, `_derived_paths.py`, `_index_rows.py`,
`_local_fs.py`, `_opus.py`, `_path_utils.py`, `_preload.py`, `_properties.py`,
`_shelves.py`, `_sorting.py`, `pdscache.py`, `pdsfile.py`, `pdsviewable.py` and
`preload_and_cache.py`.

**Non-vacuity, at line level — the number that actually bounds the risk.** Of the
**143 executable lines this PR changed** (`git diff -U0 origin/rewrite...HEAD`
intersected with `coverage`'s own statement set), the run executed **81** and did
not reach **62**:

| File | changed executable | executed |
|---|---|---|
| `pdscache.py` | 24 | 5 |
| `pdsfile.py` | 41 | 25 |
| `pdsviewable.py` | 16 | 7 |
| `_properties.py` | 15 | 11 |
| `_local_fs.py` | 13 | 12 |
| `_preload.py` | 9 | 7 |
| `_shelves.py` | 7 | 5 |
| `_sorting.py` | 6 | 5 |
| `_path_utils.py` | 5 | 1 |
| `_index_rows.py` | 3 | 2 |
| `_opus.py`, `_associations.py`, `__init__.py` | 4 | 1 |
| **total** | **143** | **81** |

The unreached lines are the ones a reader should know about: 19 of the 24 in
`pdscache.py`, almost all inside `MemcachedCache` (`unblock`'s two collapsed
conditionals, `__contains__`, `get_multi`'s `tuple`→`pair` rename, `get_now`'s
`RUF059` rename, three `F541` fragments and the `type(port) is str` comparison);
`PdsFile.__repr__`'s `type(self) is PdsFile`; all three `next(iter(...))` sites
and `PdsViewSet.append`'s `B020` rename; `_get_shelf`'s failure path;
`repair_case`'s not-found path; and the `N806` rename in `from_abspath`'s
multi-holdings branch. An identical pass/fail set does not speak for any of them.

One `MemcachedCache` region **is** covered by the suite, and it is worth naming
because it is the only one: `set_multi`'s `tuple`→`pair` rename runs under
`tests/core/test_pdscache_set_multi.py`, which builds a `MemcachedCache` with
`__new__` and a stub client because `pylibmc` is not installed.

**So the rest were exercised directly instead.** A differential probe — **55
labelled values, no holdings tree, no committed test id** — was run under the
**baseline** tree and under the **head** tree and the two outputs diffed. It
borrows `test_pdscache_set_multi.py`'s `__new__`-plus-stub-client technique to
drive the `MemcachedCache` methods the suite cannot reach. Measured under
`coverage`, the probe reaches **36** of the 143 changed executable lines, **24 of
which the suite does not**, so the union is **105 of 143** and **38** remain
unreached by anything.

| Reached by | changed executable lines |
|---|---|
| the full-data suite | 81 |
| the differential probe | 36 |
| **either** | **105** |
| neither | 38 |

Per file, "reached by neither": `pdsfile.py` 15, `_path_utils.py` 4,
`_properties.py` 4, `pdscache.py` 3, `_shelves.py` 2, `_preload.py` 2,
`pdsviewable.py` 2, and one each in `__init__.py`, `_associations.py`,
`_index_rows.py`, `_local_fs.py`, `_opus.py`, `_sorting.py`. **35 of the 38** are
one of: a `UP024` alias substitution (`IOError` **is** `OSError`), an f-string
whose text was compared byte for byte by hand, an `E701` split that cannot change
semantics, a local rename `ruff`/`pyflakes` proves complete, or an `F841` binding
removal whose right-hand side is preserved or absent (`_path_utils.py:136`,
`_preload.py:201`, `_shelves.py:171`, `__init__.py:7`). **The other three are named rather than
folded in**: `pdscache.py:321`'s `E721` and the `F541` fragments at `:599` and
`:1042`, all of which need `pylibmc` to reach (deferred observation 72). No
`SIM`, `RUF005`, `RUF015`, `B020`, `SIM118`, `C405`, `E713` or `F401` fix is among
the 38; every one of those is covered by the suite, the probe, or both. The one
unreached `E721` is discharged by the metaclass argument in §4 and by the probe's
direct evaluation of `type(x) is str` on a `str`, a `str` subclass, an `int` and a
`bool`.

What the probe covers, by code: **`E721`** — two of the three sites called for
real (`PdsFile.__repr__` on `PdsFile`, `Pds3File`, `Pds4File` and an anonymous
subclass; `iconset_for` on a bare object, a plain `list` and a `list` **subclass**
— exactly the inputs `isinstance` would have mis-dispatched); the third,
`MemcachedCache.__init__`, cannot be constructed without `pylibmc`, so the probe
evaluates the predicate on a `str`, a `str` **subclass**, an `int` and a `bool`
instead. **`RUF015`** — all three sites plus their empty-guard paths.
**`B020`** — `append` with a nested viewset, and with an empty one.
**`SIM102`** — `unblock` on all five logger/pid combinations.
**`F541`** — `DictionaryCache._trim`'s message and `unblock`'s two.
**`A001`** — `get_multi`'s renamed loop. **`RUF059`** — `get_now`.
**`F401`** — both re-exports. **`UP004`** — the three MROs.

**All 55 values identical, over three independent base/head run pairs.** Sample:

```
repr(PdsFile abspath)                    = 'PdsFile("/a/b")'
repr(Pds3File abspath)                   = 'Pds3File("/a/b")'
repr(anon subclass abspath)              = 'PdsFile._PdsFileSubclass("/a/b")'
iconset_for(list SUBCLASS)               !! AttributeError: '_ListSubclass' object has no attribute 'icon_type'
for_width on empty                       !! OSError: No viewables have been defined
MemcachedCache.__contains__('perm')      = True
MemcachedCache.get_multi                 = [('a', 'A'), ('b', 'B')]
MemcachedCache.unblock otherpid/logger   = (None, [], [('error', 'Process 4242 is unable to unblock MemcachedCache [11211]; Cache is blocked by process 99')])
DictionaryCache._trim log                = [('debug', '21 items trimmed from DictionaryCache'), ...]
```

The `repr` lines are the point of `E721`: had `isinstance` been used, the
`Pds3File` line would read `PdsFile("/a/b")` and the subclass line would lose its
class name. The `iconset_for(list SUBCLASS)` line is the other one: `isinstance`
would have stopped wrapping the subclass, so the error would have come from a
different place. The `unblock` lines are `SIM102`, and they also show the
collapse preserving the fall-through when `self.logger` is falsy — the two
`no-logger` cases still reach `self.mc.set('$OK_PID', 0, time=0)`, which is the
behavior the nested form had.

The three lines nothing reaches in `pdscache.py` are `type(port) is str` in
`MemcachedCache.__init__` and the two `F541` fragments inside
`except pylibmc.TooBig` handlers; all three need `pylibmc`, which is not a
declared dependency. Recorded as deferred observation 72.

The probe also **caught something**, which is why it is worth reporting rather
than merely claiming: one value differed on the first pair, and it turned out to
differ between two runs of the **same** tree. `PdsViewSet.append`'s recursive
branch keeps an arbitrary member of the nested set and `PdsViewable` is hashed by
identity, so which one survives is not a function of the input. Recorded as
deferred observation 73, with five-run evidence on unmodified `rewrite`; the
probe now asserts the invariant rather than the member.

### 3. The violation set was derived, not assumed

The plan says not to trust its own PR-23 list, and the list is provably stale: it
places `A002` in `pdsfile.py`, but PR-18 moved those three methods into
`_derived_paths.py` (deferred entry 45).

`ruff check` was run with the template select set and **no `per-file-ignores` at
all**, so nothing the committed ratchet suppresses could hide. Over the fifteen
modules: **154 violations in 14 files**; `preload_and_cache.py` is the one clean
file, and `_version.py` is `.gitignore`d and absent from a checkout. The
coordinator's scoping run reported 155; the one-violation difference is not
reconciled and is not load-bearing — every disposition below is keyed to a
`file:line`, not to a total.

**154 → 33. 121 fixed, 33 permanent.** By code. **Superseded by the "PR-23 revision" section at the end of this file: the owner's `RUF005` ruling on 2026-08-03 reverted seven fixes, so the measured figures are now 154 → 40, 114 fixed, 40 permanent, with `RUF005` 0 fixed / 8 permanent.**

| Code | n | Fixed | Frozen |
|---|---|---|---|
| `E701` | 20 | 20 | — |
| `UP024` | 20 | 20 | — |
| `RUF012` | 16 | — | 16 |
| `UP031` | 14 | 13 | 1 |
| `F841` | 9 | 9 | — |
| `RUF005` | 8 | 7 | 1 |
| `F541` | 7 | 7 | — |
| `B904` | 4 | — | 4 |
| `C405` | 4 | 4 | — |
| `I001` | 4 | 3 | 1 |
| `RUF015` | 4 | 3 | 1 |
| `UP004` | 4 | 4 | — |
| `A002` | 3 | — | 3 |
| `B006` | 3 | — | 3 |
| `E501` | 3 | 3 | — |
| `E721` | 3 | 3 | — |
| `F403` | 3 | — | 3 |
| `SIM102` | 3 | 3 | — |
| `SIM103` | 3 | 3 | — |
| `A001`, `B007`, `B905`, `F401`, `N806`, `RUF059`, `SIM114`, `SIM118` | 2 each | 16 | — |
| `B020`, `E713`, `UP015` | 1 each | 3 | — |
| **Total** | **154** | **121** *(now 114)* | **33** *(now 40)* |

### 4. The behavior-equivalence proofs, per risky code

§2 permits exactly three PRs to change observable behavior and this is not one of
them. "Mechanical" describes the diff, not the risk.

**`E721` — `is`/`is not`, never `isinstance`.** All three sites sit in a package
whose design is a subclass hierarchy, and `isinstance` would change dispatch at
two of them:

| Site | Before | After | What `isinstance` would have done |
|---|---|---|---|
| `pdsfile.py` `__repr__` | `type(self) == PdsFile` | `type(self) is PdsFile` | made the branch true for every `Pds3File`/`Pds4File`, changing their repr |
| `pdsviewable.py` `iconset_for` | `type(pdsfiles) != list` | `type(pdsfiles) is not list` | stopped wrapping a `list` **subclass** in a one-element list |
| `pdscache.py` `MemcachedCache.__init__` | `type(port) == str` | `type(port) is str` | sent a `str` subclass down the `'127.0.0.1:%d'` branch |

`type(x) is C` and `type(x) == C` can differ only if the metaclass of `type(x)`
overrides `__eq__`; every class reachable here has metaclass `type`.

**`F841` — two of the nine right-hand sides have effects, and both are kept.**
`_preload.py`'s `pdsf2 = cls.CACHE[key]` and `pdsfile.py`'s
`pdsf = cls.CACHE[child_logical_path.lower()]` both become `_ = cls.CACHE[…]` —
the spelling `_preload.get_permanent_values` already used for the same idiom two
lines earlier: the lookup still happens, still updates cache bookkeeping, and
still raises the `KeyError` the enclosing handler is there to catch. Only the
named binding goes. The other seven are `except … as e` bindings never read, a
`with open(...) as f: pass` whose `open()` is the entire point (`as f` dropped,
`open()` kept), and two dead assignments whose right-hand sides are a constant and
a plain list index. Both dead assignments turned out to mark latent defects, which
are recorded as deferred observations 67 and 68 rather than repaired.

**`B904` — all four frozen.** There is no behavior-preserving variant.
`raise X from err` sets `__cause__` **and** `__suppress_context__`, turning the
traceback's "During handling of the above exception, another exception occurred"
into "The above exception was the direct cause of"; `raise X from None` sets
`__suppress_context__` and hides the original traceback entirely. §2 names error
messages as observable, so both are out of scope here.

**`RUF005` — seven local proofs, one refusal.** `_sorting.py`'s four sites operate
on `parts`, a list literal built in the same function; `_opus.py`'s two operands
are assigned seven lines above and are both lists; `_preload.py`'s
`volinfo_dict[key]` has exactly one assignment in the same function and it is a
tuple literal; `_index_rows.py`'s `self.childnames` is a list on **every** one of
its six assignments in the package (`pdsfile.py:428` — to `None`, before the
property's own `[]` — and `:632`/`:688`,
`_properties.py:398/403/413`, where `sort_basenames` ends
`basenames = list(basenames); basenames.sort(...); return basenames`).

`_properties.py`'s `self._info[:4] + (shape,)` is **frozen**: `_info_filled` is a
**list** at `pdsfile.py:634` and `:690` (`new_merged_dir` and
`new_index_row_pdsfile`). On those objects `list + tuple` raises `TypeError`
today, while `(*self._info[:4], shape)` would silently succeed. The site is
unreachable with a list only via a whole-program argument about
`len(self._info[4]) > 2`, and a mechanical style PR should not rest on that.

**`SIM102`/`SIM114` — same short-circuit, proven structurally.** ruff raises
SIM102 only when the outer `if`'s body is *exactly* the nested `if`, so
`if A: if B: S` ≡ `if A and B: S` evaluates `A`, then `B` only if `A` is truthy —
the same order and the same subset. SIM114 merges two branches with identical
bodies into `if A or B`, which likewise evaluates `B` only when `A` is falsy,
exactly as the `elif` did.

**`SIM103` — all three fixed, as `return bool(...)`.** The *bare* collapse would
change the returned object from the `True`/`False` singleton to the condition's
raw value, and `_local_fs.py`'s condition is a call
(`cls.os_path_exists(shelf_abspath)`) that is not proven `bool`-returning — it has
a `return (pdsf.exists and pdsf.child_of_index(...).exists)` path. Wrapping in
`bool(...)`, which is the form ruff's own message names, removes the question
entirely: `bool(x)` invokes exactly the `__bool__`/`__len__` that `if x:` invoked
and returns exactly the singleton the branch returned, so the callee's return type
never reaches the caller. `_shelves.py:338`'s `bool(self.bundlename)` is the same
argument on a `str`. **This is a round-1 correction**: the two `_local_fs.py`
sites were first classified freeze-locked on the strength of the bare rewrite
alone, and the reviewer showed that the `bool(...)` form — which this PR was
already using at `_shelves.py:338` — makes them provable locally. See
`critiques/pr-23/round-1.md` M1.

**`UP031` — thirteen fixes, one refusal.** For every fixed site the argument is a
`str`, an explicit tuple literal matching the placeholder count, or `len(...)`;
`'%s' % x` is `str(x)` and `f'{x}'` is `format(x, '')`, which is `str(x)` for
every type here, and the only general divergence — a tuple right-hand operand
raising `TypeError` under `%` — cannot arise. `pdscache.py`'s
`'127.0.0.1:%d' % port` is **frozen**: `%d` truncates a non-int, `{port:d}` raises
on one, and `{port}` prints it, so no f-string spelling reproduces the current
behavior across the whole input domain. It is also inside `MemcachedCache`, which
ground rule 9 protects and no test here can reach.

**`UP024` — genuinely safe, and for a stronger reason than "renamed".** In Python
3 `IOError` and `EnvironmentError` **are** `OSError` — the same class object — so
`except IOError` and `except OSError` compile to the same catch, `raise IOError(x)`
constructs the same object, and a traceback already prints `OSError` either way.
Three sites additionally simplified `except (ValueError, IndexError, IOError,
OSError)` to a tuple without the duplicate.

**`UP004` — the class statement, measured rather than assumed.**
`plans/2026-07-27-addendum-phase5-mixin-base-order.md` already ruled that trailing
`object` is not a mixin, is not required, gives an identical MRO, and is left for
PR-23. Verified in both trees:

| | Baseline `96e5960` | PR-23 head |
|---|---|---|
| `PdsFile.__mro__` | 11 entries, `PdsFile` → 9 mixins → `object` | **identical, entry for entry** |
| `Pds3File.__mro__` | 12 entries | **identical** |
| `Pds4File.__mro__` | 12 entries | **identical** |
| `PdsFile.__bases__` | 9 mixins + `object` | 9 mixins |

The one line that depended on it is `test_the_class_statement_stays_in_pdsfile_pdsfile`'s
`assert PdsFile.__bases__[-1] is object`, which the addendum names explicitly
("stops being meaningful once `object` is gone"). It is replaced by two
assertions that have teeth — `object not in PdsFile.__bases__`, and a check that
every base's `__module__` starts with `pdsfile._`, which fails both if `object`
returns to the base list and if any non-mixin base is added. (An earlier draft
used `PdsFile.__mro__[-1] is object`; round 2 removed it as a tautology — it
cannot fail for any Python 3 class.) **The test id set is unchanged**; the module's
mixin discovery (`[base for base in PdsFile.__bases__ if base is not object]`)
reads the same either way, and `tests/api/` is 26 passed before and after.

**`N806`, `A001`, `B007`, `B020`, `RUF059` — local renames only.** Every renamed
name is a function-local or a loop variable; none appears in a signature, in the
manifest, or after the construct that binds it. `pdscache.py`'s two `tuple`
shadows are safe to rename because the builtin `tuple` is never called anywhere in
that module (`grep -n 'tuple('` → no matches).

**`F401` — fixed by re-export, not by deletion.** `pdsfile.pdscache.sys` and
`pdsfile.pdsviewable.pdslogger` are **frozen manifest members**, so deleting
either import is a manifest break. Both become `import X as X` with a comment,
which is the form `pdsfile.py` already uses for ten unused stdlib modules and
which ruff honours (that file reports no `F401`). The names stay bound; the
manifest is unchanged.

### 5. The ratchet — 14 entries and 78 code slots become 7 and 10

| File | Before | After |
|---|---|---|
| `__init__.py` | `F403, F841, I001` | `F403` |
| `_associations.py` | `UP024` | **removed** |
| `_derived_paths.py` | `A002` | `A002` |
| `_index_rows.py` | `RUF005, UP024` | **removed** |
| `_local_fs.py` | `B007, B905, E701, SIM103, SIM118, UP024` | **removed** |
| `_opus.py` | `RUF005, UP024` | **removed** |
| `_path_utils.py` | `E701, F841` | **removed** |
| `_preload.py` | `E501, E701, F841, RUF005, UP015, UP031` | **removed** |
| `_properties.py` | `E701, F841, RUF005, SIM114, UP024, UP031` | `RUF005` |
| `_shelves.py` | `B904, B905, F841, RUF059, SIM103, UP024, UP031` | `B904` |
| `_sorting.py` | `E701, RUF005` | **removed** |
| `pdscache.py` | `A001, E701, E721, F401, F541, F841, I001, RUF015, RUF059, SIM102, UP004, UP031` | `RUF015, UP031` |
| `pdsfile.py` | `B904, C405, E501, E701, E713, E721, F841, I001, N806, RUF012, SIM102, SIM114, SIM118, UP004, UP024, UP031` | `B904, I001, RUF012` |
| `pdsviewable.py` | `B006, B007, B020, C405, E701, E721, F401, I001, RUF015, RUF059, UP004, UP024` | `B006` |

Each of the 10 surviving codes is a real, present violation: the no-ignores run
over the same fifteen files after the fixes reports **exactly 33**, and they map
one-for-one onto the 10 slots. (Point ruff at `src/pdsfile/*.py` in a tree where
an install has regenerated the gitignored `_version.py` and the answer is 34, the
extra one being that file's `RUF022` — deferred observation 71.) `pdsviewable.py`'s `RUF059` was **already dead** in
the committed table — the derived set has no `RUF059` in that file — so it leaves
as a stale-entry removal rather than as a fix, and that is stated rather than
counted as work.

**Nothing was added.** No entry gained a code, no entry gained a file, and no
inline `noqa` exists in any source file: `grep -rn noqa src/pdsfile/*.py` → no
matches, at head. (A naive `git diff … | grep -c '^+.*noqa'` returns 6, all of
them prose — this paragraph, two sub-plan lines, the `pyproject.toml` and
`pdsfile_overrides.mdc` sentences that say `noqa` is never added. The grep worth
recording is the one that answers the question.)

`.cursor/rules/pdsfile_overrides.mdc` deviation (4) records the same set as a
per-file table with the same reasons, as the plan requires. Its non-core lines
(rule modules, the `pds{3,4}file/__init__.py` pair, `re_validate.py`,
`tests/rules/**`) are unchanged and stay PR-24's to re-derive.

**`scripts/gen_ruff_ratchet.py` was not used**, and the ratchet header now says
why: deferred entry 33 records that the script runs `ruff` with the project config
and therefore emits an empty block against a tree whose committed ignores already
suppress everything — which is exactly this tree.

### 6. Deferred entry 60 — banner widths, proven comment-only

Measured over every indented `#`-only line in the fifteen modules (each banner
contributes two, one above its text and one below): the in-class convention is
**80 columns**, with six outliers forming three banners — `# Preload management`
and `# Set parameters for both Pds3File and Pds4File` at 90, and
`# Interior function to recursively preload one physical directory`, indented
eight spaces inside `preload()`, at 84. All six now end at column 80; the tally
across all fifteen files is 40 lines at 80 and nothing else, except the two
8-space bare `#` lines at `pdsfile.py:989`/`:994`, which are blank lines inside a
comment paragraph rather than banner rules.

Proven rather than asserted: each of the fifteen modules was tokenized before and
after with `tokenize.generate_tokens`, `COMMENT` and `NL` tokens dropped, and the
remaining `(type, string)` streams compared. **15 files compared, 0 differing.**

### 7. API freeze — an empty diff, byte for byte

`scripts/dump_public_api.py` was run in the baseline worktree and in the head
worktree:

| | Bytes | md5 |
|---|---|---|
| `96e5960` | 733,876 | `442428dafbdf30f291987a196b22a2ce` |
| PR-23 head | 733,876 | `442428dafbdf30f291987a196b22a2ce` |

`diff` is empty. `tests/api/test_api_freeze.py` passes inside `run-all-checks.sh`.
Neither the manifest, the allowlist, the dumper nor the checker was edited.

This is the gate that catches the two riskiest fixes in the PR — dropping
`object` from `PdsFile`'s bases, and rewriting two frozen module-level imports as
`import X as X`. Both leave the dump byte-identical.

### 8. Holdings-free gate

`scripts/run-all-checks.sh` with `PDS3_HOLDINGS_DIR`, `PDS4_HOLDINGS_DIR`,
`PDSFILE_TEST_HOLDINGS` and `PDSFILE_TEST_DATA_DIR` all unset:

| Check | Result |
|---|---|
| `ruff check src/pdsfile tests scripts` | passed |
| pytest | **92 passed, 800 skipped** — the same split as the baseline |
| pyroma | passed |
| API freeze | passed |
| clean install | passed — all runtime modules import with no dev extras |

### 9. Consumer smoke — outcome unchanged

The gate is **same outcome as baseline**, not "passes"
(`critiques/baselines/consumer-smoke-baseline.md`).

| Check | Baseline | This branch |
|---|---|---|
| A — rms-opus import paths | 4/4 resolve, 0 failures | **4/4 resolve, 0 failures** |
| B — rms-viewmaster startup | 5 ok, 3 pre-existing failures | **5 ok, 3 failures — the same three** |

The three Check-B failures are still `pdsfile.cache_lifetime` (raises),
`pdsfile.DEFAULT_CACHING` (absent) and the same `cache_lifetime` read inside
`get_page_cache()` with `PAGE_CACHING=True`. None became a pass, which matters
here: a `F401` "fix" that deleted `sys` or `pdslogger`, or an `__init__.py`
"cleanup" of the star imports, is exactly the class of change that would move this
table. `pdsfile.pdsfile.repair_case` still resolves.

Check B is load-bearing in a second way: `create_app()` → `init_once()` preloads
rms-viewmaster's own holdings configuration against a **different holdings tree**
than this repo's tests use, so the edited `child()`, `os_path_exists`,
`glob_glob`, `sort_basenames` and `_get_shelf` all run outside this repo's
harness. The run's log shows the `Pre-loading:` lines, the
`Missing category dir:` warnings for categories absent there, and
`PdsFile preloading completed`.

Environment note carried from the baseline: the check ran under the pdsfile venv's
interpreter with rms-viewmaster's `site-packages` appended to `PYTHONPATH`,
because that venv lacks pdsfile's declared `range_ex` dependency.
rms-viewmaster is at `a0d05e2`; rms-opus is at `73cb6de7`.

### 10. Deferred observations

Entries **45** and **60** are resolved by this PR. Entry **33** is resolved as
documented rather than fixed — the ratchet header now records the workaround —
and stays open as a tooling gap. Entry **37** is half resolved: its `F841` is
fixed, its `B904` is now a justified permanent ignore. Entry **31** is untouched
and still needs the owner decision it asks for. Entry **64** is untouched **on
purpose**: it asks for an owner decision that has not been given, and PR-23 did
not remove the six commented-out `MemcachedCache.get_multi` lines.

Seven new entries are recorded in `critiques/deferred-observations.md`:
**67** (`child()` discards the cache entry it looks up), **68** (`version_ranks`
returns `None` for a nonexistent file), **69** (`_local_fs.py`'s now-visibly-dead
`values`/`zip` pair), **70** (`tools/show_opus_products.py`'s orphan `I001`
ratchet entry), **71** (the gitignored `_version.py` carries a real `RUF022` no
gate can see), **72** (only one `MemcachedCache` method is reachable by any test
here: 28 of the 37 lines this PR changed in `pdscache.py` are inside that class,
and `set_multi` is the only one the suite executes) and **73** (`PdsViewSet.append` keeps a nondeterministic member of a
nested viewset). 67, 68, 69 and 73 are latent defects this PR uncovered — the
first three while removing the unused bindings that concealed them, the last by
diffing the differential probe — and repairing any of them is a behavior change
§2 forbids here.

Later rounds and reviews added seven more, so this PR carries **fourteen** in
all: **74** (`MemcachedCache.flush` calls `.sort()` on a `dict_keys`) and **75**
(`_opus.py` spelled one concatenation two ways — closed by the `RUF005` revert)
from round 2; **76** (`pdscache.py`'s off-grid indentation, invisible because
ruff's `E1xx` rules are preview-gated) and **77** (whether prose may follow a
mechanical fix) from round 3; **78** (`MemcachedCache.unblock` releases a lock it
does not own when no logger is configured) from the CodeRabbit review of this PR;
**79** (130 logging calls across the package build their message eagerly) from
the owner's lazy-logging correction; and **80** (the module headers narrate the
port instead of describing the code) from the owner directly.

The count is stated here rather than left implicit because it is the one figure
in this record that a later reader can check in a second, against
`critiques/deferred-observations.md`.

### 11. Review loop

Every round's record exists on disk before its row is written here.

| Round | Major | Minor | Deferred | Verdict | Full-data record |
|---|---|---|---|---|---|
| [1](pr-23/round-1.md) | **1** | 9 | 2 | `goal not met` | regenerated after the fixes (`runs/pr23-r2`) |
| [2](pr-23/round-2.md) | 0 | 6 | 2 | `goal met`, but new Minors → loop continues | regenerated after the fixes (`runs/pr23-r3`) |
| [3](pr-23/round-3.md) | 0 | 6 | 2 | `goal met`, but new Minors → loop continues | regenerated after the fixes (`runs/pr23-r4`) |
| [4](pr-23/round-4.md), **scoped** | **0** | — | — | **`goal met`** — loop terminates | `runs/pr23-r4` carries forward: the round's four record fixes touch no source |

**Round 1's Major is the one finding that changed the deliverable.** `SIM103` ×2
in `_local_fs.py` had been classified freeze-locked on the strength of ruff's
*bare* rewrite; the reviewer showed that `return bool(<condition>)` — the form
ruff's own message names, and the form this PR was already using at
`_shelves.py:338` — is provable locally, so the classification was internally
inconsistent and `pdsfile_overrides.mdc` was about to record a false claim
permanently. Fixed; 35 → 33 permanent, ratchet 8/11 → 7/10.

**Round 2 found no Major and confirmed every gate by independent measurement**,
including the one that is hardest to check from a diff: `ruff format --check`
reports the *same* 13 unformatted files at base and at head, which is direct
evidence that owner decision 3 was honoured.

**Round 2's m1 is the most useful Minor of the two rounds.** The record claimed
the differential probe covered `pdscache.py`; it covered none of it — the
`DictionaryCache` round trip went through `DictionaryCache`'s own methods, which
this PR never touched. That claim is now replaced by a measurement, and the probe
was extended to drive `MemcachedCache` through the `__new__`-plus-stub-client
technique `tests/core/test_pdscache_set_multi.py` already uses. It is why §2's
numbers are 55 values and 105 of 143 lines rather than 39 and 81.

**Round 3 invented the two strongest checks in this record**, neither of which
the executor had run: an **AST control-flow skeleton diff** of all thirteen
changed source files base-vs-head, whose only differences are the two `SIM102`,
three `SIM103` and two `SIM114` collapses, the `version_ranks` inversion, and
index shifts — direct mechanical evidence that none of the 20 `E701` splits
moved a statement into or out of a block; and **mutation-testing the
differential probe** in a scratch copy, which showed that reverting each of the
`E721`, `SIM102` and `B020` fixes changes a probe value, i.e. the probe is not
passing vacuously.

**Round 4 is §6.6's scoped fourth round** — "confirm the prior round's findings
are resolved; raise only new Major findings" — and the hard cap. It confirmed
all six of round 3's Minors and both Deferred items resolved, and returned
**zero Major**, so the loop terminates. It also ran one check no earlier round
did: it cross-validated `setdiff.py` against the raw junit XML
(`failures="0" errors="0"` in all four files) so that no failure could be masked
by the script's last-child-wins outcome rule. Its four would-be-Minors — which a
scoped round may not raise — were all one-line record corrections, and were made
rather than carried; since they touch no source, `runs/pr23-r4` carries forward.

**Findings by kind, across the four rounds: 1 Major and 21 Minor.** **Four
Minors were in the code** — a tautological assertion, two one-character idiom
mismatches, and one comment placed above the wrong import. The other seventeen
and the Major were figures, claims or classifications in this record, the
sub-plan, `pdsfile_overrides.mdc` and one plan addendum. That is the same
distribution PR-19 through PR-22 reported: the defects are in what the executor
*says*, not in what it changed. **No round found a defect in the behavior of the
code this PR changed.**

---

### PR-23 revision — four owner corrections, 2026-08-03

Appended, not merged into the sections above, so that the record shows the state
before and after the corrections. The corrections were given after the §6.6 loop
had closed clean at `0a7dc60`; `f59ec05` is the coordinator commit that recorded deferred 78 on top of it, and is the base of the corrections diff. Everything below was measured after them.

#### What changed and why

| # | Correction | What it touched |
|---|---|---|
| 1 | `RUF005`'s `[*a, b]` rewrite is not wanted; the exclusion is permanent | 7 source lines reverted; 4 ratchet entries recreated; `pdsfile_overrides.mdc` (4); deferred 75 closed |
| 2 | Logging passes lazy `%` arguments, never f-strings | 4 logging calls; deferred 79 added |
| 3 | Code comments may not name plans, critiques, PR numbers, the frozen surface or the manifest | 11 comment/docstring sites in 6 files |
| 4 | `pyproject.toml`'s plan commentary is allowed only until the rewrite finishes | plan §Phase 8, as a PR-37 deliverable |

Corrections 2 and 3 are restatements of standing rules that this PR had violated,
not new preferences. Correction 1 reverses a fix the PR made; correction 4 adds a
future obligation and changes nothing now.

#### 1. The seven reverts are byte-identical, not merely equivalent

Each restored line was extracted from `git show origin/rewrite:<file>` and
required to appear byte-for-byte in the working tree. Both operands and the exact
whitespace match, including `_preload.py`'s idiosyncratic continuation indent:

| Site (HEAD line) | Restored text |
|---|---|
| `_index_rows.py:164` | `childnames = self.childnames + [selection]` |
| `_opus.py:246` | `label_pdsfiles[abspath] = [pdsf] + fmt_pdsfiles` |
| `_sorting.py:188` | `parts[3:] = [self.basename_is_label(basename)] + parts[3:]` |
| `_sorting.py:196` | `parts = [not isdir] + parts` |
| `_sorting.py:200` | `parts = [isdir] + parts` |
| `_sorting.py:205` | `parts = [self.info_basename != basename] + parts` |
| `_preload.py:325–327` | `volinfo_dict[key] = (volinfo_dict[key][:4] +` / `(dsids_vs_key[alt_key],` / `volinfo_dict[key][5]))` |

`git diff origin/rewrite -- <those four files>` no longer contains any of them.
`_opus.py:268` and `_sorting.py:269` also carry `+` concatenations; neither was
ever converted and neither changed, so all of `_opus.py`'s concatenations read
alike again — which is what closes deferred entry **75**.

#### 2. This is a shrink, not a widen

The claim a reviewer must be able to check is **per file**: no file's remaining
code set contains a code its `origin/rewrite` set did not. Measured against
`96e5960`:

| File | at `96e5960` | now | added? |
|---|---|---|---|
| `__init__.py` | `F403, F841, I001` | `F403` | no |
| `_associations.py` | `UP024` | *(entry removed)* | no |
| `_derived_paths.py` | `A002` | `A002` | no |
| `_index_rows.py` | `RUF005, UP024` | `RUF005` | no |
| `_local_fs.py` | `B007, B905, E701, SIM103, SIM118, UP024` | *(entry removed)* | no |
| `_opus.py` | `RUF005, UP024` | `RUF005` | no |
| `_path_utils.py` | `E701, F841` | *(entry removed)* | no |
| `_preload.py` | `E501, E701, F841, RUF005, UP015, UP031` | `RUF005` | no |
| `_properties.py` | `E701, F841, RUF005, SIM114, UP024, UP031` | `RUF005` | no |
| `_shelves.py` | `B904, B905, F841, RUF059, SIM103, UP024, UP031` | `B904` | no |
| `_sorting.py` | `E701, RUF005` | `RUF005` | no |
| `pdscache.py` | 12 codes | `RUF015, UP031` | no |
| `pdsfile.py` | 16 codes | `B904, I001, RUF012` | no |
| `pdsviewable.py` | 12 codes | `B006` | no |

**14 entries / 78 code slots → 11 entries / 14 slots.** Every `RUF005` entry is a
restoration of a code that file already carried; none is new. Four entries the
first pass deleted are recreated (`_index_rows.py`, `_opus.py`, `_preload.py`,
`_sorting.py`), which is why the entry count went 7 → 11.

Re-derived violation counts, `ruff 0.15.22`, template select set, **no**
`per-file-ignores`, over the fifteen in-scope modules — the generated
`_version.py` excluded, per deferred entry 71:

| Tree | Violations |
|---|---|
| `origin/rewrite` @ `96e5960` | **154** |
| this branch | **40** |

So **114 fixed**, not the 121 this record claimed before the revert. The 40 are
`RUF012` 16, `RUF005` 8, `B904` 4, `A002` 3, `B006` 3, `F403` 3, `I001` 1,
`RUF015` 1, `UP031` 1. `ruff check src/pdsfile tests scripts` with the project
config is clean.

#### 3. The four logging conversions emit the same text

`pdslogger.PdsLogger.log()` reinterprets a lone argument as a `filepath` when the
message carries no substitution pattern, so "it has a `%s`" is a fact that has to
be checked, not assumed. `_message_uses_args` tests `re.compile(r'%[^\(]')`
against the message with `%%` removed; all four messages match.

| File:line | Now |
|---|---|
| `_preload.py:204` | `cls.LOGGER.warn('Permanent value %s missing from Memcache; ' 'preloading again', str(e))` |
| `_preload.py:382` | `cls.LOGGER.info('Connecting to PdsFile Memcache [%s]', cls.MEMCACHE_PORT)` |
| `_shelves.py:258` | `cls.LOGGER.debug('Retrieving key "%s"', py_path)` |
| `pdscache.py:73` | `self.logger.debug('%d items trimmed from DictionaryCache', len(pairs))` |

The first is wrapped as two implicitly concatenated literals; the format string
the interpreter sees is the single-line one.

A probe exercised each site in three spellings — A = `origin/rewrite`'s eager
`'fmt' % v`, B = this PR's f-string, C = the lazy form — over 18 value cases
(realistic values, empty strings, ints, `str`/`int` ports, and values containing
a literal `%`), through both of `pdslogger`'s output paths. It asserts that a
handler is attached and that output is non-empty, so it cannot pass vacuously.

| Path | Cases | A ≡ B ≡ C |
|---|---|---|
| `PdsLogger` with a handler (production; `self._logger.log(level, text, *args)`) | 18 | **18** |
| `EasyLogger` / no handler (`print(self._format_message(...))`) | 18 | 14 |

The four `EasyLogger` divergences are exactly the cases whose value contains a
literal `%`. There, **both** eager spellings raise
`TypeError: not enough arguments for format string` out of the log call and emit
nothing, while the lazy form logs correctly. No text that an existing spelling
emits changes; the lazy form only produces output where `rewrite` throws. None of
the four values can contain `%` in practice — a `KeyError` on a holdings logical
path, a port, a shelf `.py` path, and `len(pairs)`.

The exception messages are untouched: `raise ValueError(f'…')` / `raise
OSError(f'…')` in `_properties.py`, `_shelves.py` and `pdsfile.py` stay as
f-strings, which is what the owner asked for.

**Pre-existing inventory, swept and recorded, not converted.** An AST sweep of
`src/pdsfile/**/*.py` (excluding the generated `_version.py`). The predicate,
stated exactly so the count is reproducible: an `ast.Call` whose `func` is an
`ast.Attribute` with `attr` in `{debug, info, warn, warning, error, critical,
exception, log, fatal, open, close}` and whose receiver, as `ast.unparse`d text,
contains `logger` (case-insensitive), counted once if its **first** argument is
an `ast.JoinedStr`, an `ast.BinOp` with `Add` or `Mod`, or a `.format()` call:

| Area | Sites | `+` | f-string | eager `%` |
|---|---|---|---|---|
| core, `src/pdsfile/*.py` | 34 | 30 | 2 | 2 |
| subpackages | 96 | 33 | 7 | 56 |
| total | **130** | 63 | 9 | 58 |

Core by file: `pdscache.py` 20, `_preload.py` 8, `_sorting.py` 2, `_opus.py` 1,
`_properties.py` 1, `pdsfile.py` 1, `pdsviewable.py` 1. Recorded as deferred
observation **79**, which also notes the two traps a future conversion faces: the
message must keep its `%` pattern, and many of these calls already pass a real
second argument that *is* a filepath.

#### 4. Disposition of all eleven comment sites

Each was re-read and decided on its own; no blanket transformation.

| Site | Was | Now |
|---|---|---|
| `_index_rows.py:55` | "Its fragility is deferred observation 49." | the fragility itself, in code terms: a subclass one level deeper, or one whose first base is not the PDS3/PDS4 class, silently gets the PDS3 table |
| `_properties.py:1340` | "…; see critiques/deferred-observations.md." | "…, so the property returns None in that case" |
| `pdsfile.py:1112` | "The looked-up object is discarded; see critiques/deferred-observations.md." | "…discarded, not returned, so the child is rebuilt below either way" |
| `pdscache.py:4–5` | "…a frozen member of this module's public surface (tests/api/api_manifest.json)…" | "`sys` is not referenced below; it is re-exported for callers that reach it as `pdsfile.pdscache.sys`" |
| `pdsviewable.py:7–9` | same shape, for `pdslogger` | same rewrite, for `pdsfile.pdsviewable.pdslogger` |
| `pdsfile.py:79–81` | "…and tests/api/api_manifest.json — which records names and kinds, never the defining class — is unchanged." | "…nothing a caller imports or calls has moved or been renamed. It does show in `__module__`, `__qualname__` and `__mro__`." |
| `pdsfile.py:87–89` | "…all of them are frozen members of this module's public surface…" | "…re-exported for callers that reach them as `pdsfile.pdsfile.<name>`" |
| `pdsfile.py:106–107` | "…all three names are frozen members of this module's surface…" | "…all three are also reachable as `pdsfile.pdsfile.<name>`…" |
| `pdsfile.py:117` | "…resolving for callers and for the API freeze." | "…resolving for callers." |
| `pdsfile.py:141–145` | "…are frozen members of this module's public surface; … are private…" | "…are public; … are private. All are carried so that no name reachable as `pdsfile.pdsfile.<name>` is lost." |
| `_derived_paths.py:225` | "…; theirs is frozen by the public API" | "…; theirs stays `dir` because callers pass it by that keyword" |

Five of the eleven exist to stop a future reader deleting an import that looks
unused. That is a real, current property of the code, so it is kept — restated
without naming the freeze. The rest carried nothing beyond a pointer and lost it.

Measured as prose-only: tokenizing all fifteen core modules at the commit before
and after, with `COMMENT`/`NL` dropped — **12 of 15 byte-identical token
streams**; the other three (`_derived_paths.py`, `_index_rows.py`, `pdsfile.py`)
differ in **exactly one `STRING` token each, at identical token counts**, because
those three sites are docstrings rather than `#` comments. The API dump records
names and kinds, never docstrings.

#### 5. Re-validation

The whole suite of gates was re-run after the corrections, because they touch
`src/pdsfile/`; the pre-correction run is superseded and not carried forward.

| Gate | Baseline (`rewrite` @ `96e5960`) | This branch | Verdict |
|---|---|---|---|
| §6.2 `--mode ns` | 892 ids, 858 passed / 34 skipped | 892 ids, 858 passed / 34 skipped | **identical set** — 0 ids only in baseline, 0 only in head, 0 outcomes changed |
| §6.2 `--mode s` | 558 ids, 555 passed / 3 skipped | 558 ids, 555 passed / 3 skipped | **identical set** — 0/0/0 |
| non-vacuity | — | all fifteen in-scope modules in `measured_files()` | pass |
| no holdings | 92 passed / 800 skipped | **92 passed / 800 skipped**, `run-all-checks.sh` green throughout | pass |
| API freeze | dump 733,876 bytes | dump 733,876 bytes | **`diff` empty** |
| `PdsFile.__mro__` | — | identical at base and head for `PdsFile`, `Pds3File`, `Pds4File` | pass |
| `ruff check src/pdsfile tests scripts` | clean | clean | pass |
| clean install | passes | passes | pass |
| consumer smoke A (rms-opus) | 4/4 resolve, 0 failures | **4/4, 0 failures** | same outcome |
| consumer smoke B (rms-viewmaster) | 5 ok, 3 pre-existing failures | **5 ok, 3 failures — the same three** | same outcome |

Check B still exercises the edited code against a different holdings tree than
this repo's tests use: the run log shows the `Pre-loading:` lines, the
`Missing category dir:` warnings, and `PdsFile preloading completed`. The three
failures are still `pdsfile.cache_lifetime` (raises), `pdsfile.DEFAULT_CACHING`
(absent) and the same `cache_lifetime` read inside `get_page_cache()` with
`PAGE_CACHING=True`; `pdsfile.pdsfile.repair_case` still resolves. That last one
matters more after correction 3 than before, because correction 3 rewrote the
comments that explain why the re-export imports exist.

#### 6. Deferred observations after the revision

**75** is closed by the revert. **79** is new — the 130-site eager-logging
inventory. **31**, **33**, **37** and **64** are unchanged and still open;
**64** still needs the owner decision it has always needed.

#### 7. Review round 5, and the regenerated evidence

The four corrections were given after the §6.6 loop had already closed clean at
round 4. **One** fresh, no-context, opus-class round was run over the corrected
branch, told what the four corrections were. Record:
`critiques/pr-23/round-5.md`. It is not a fifth round of the original loop — that
loop terminated — and does not breach the hard cap of four.

**Verdict returned: `goal not met` — 2 Major, 6 Minor, 3 Deferred.** Both Majors
were in text that **correction 3 itself introduced**, which is the correction
whose subject is comment text:

- **M1, `pdsfile.py:79–81`** — the rewrite that removed the `api_manifest.json`
  reference generalised it into a false claim ("a caller cannot tell which module
  defines any of them"). `PdsFile.opus_products.__module__` is `pdsfile._opus`,
  and the paragraph nine lines above tells the reader that two tests inspect
  exactly that. Fixed to what is true, in the same three lines so no line number
  in `pdsfile.py` moves.
- **M2, `tests/api/test_mixin_collisions.py:74`** — this PR had itself added a
  code comment citing `plans/2026-07-27-addendum-phase5-mixin-base-order.md`.
  Correction 3's sweep covered `src/` only; the rule is about code comments, so
  it reaches `tests/` too. Parenthetical dropped. The 36 other `plans/`/
  `critiques/` lines under `tests/` are pre-existing and out of scope.

The six Minors were all figures: six stale `file:line` sites in three records
(correction 3 shifted `pdscache.py` −1, `_derived_paths.py` +1, `_index_rows.py`
+2), two missing supersession pointers, a banner count of 32 that is 34, two
off-by-one citations, a non-reproducible subpackage logging count, and one
request to state rather than assume that `pyproject.toml`'s freeze wording is
covered by correction 4. All fixed in `374dcdd`; details in the round record.

**M1 is the lesson worth keeping.** Correction 3 says to restate a comment "in
terms of the code" rather than delete it. That is only safe when the restatement
is itself checked against the code. A weaker, more general sentence is not
automatically a safer one — here it was the only *false* sentence the PR
produced, and it was produced by the rule meant to make comments truer.

M1 touched `src/pdsfile/`, so §6.6's regeneration rule applies and every figure
in §5 above was re-measured at `374dcdd` rather than carried forward. **All ten
gates returned the same results**, listed again in the round record: ns
892/892 ids with 0/0/0 movement, s 558/558 with 0/0/0, all fifteen modules
measured, 92 passed / 800 skipped with no holdings, an empty manifest diff at
733,876 bytes each side, identical MROs, `ruff check` clean with the no-ignores
derivation still at 40, and the consumer smoke unchanged.

## PR-24 — `style: ruff-clean rules and remaining files`

**Branch:** `pr-24-ruff-rest`, based on and opened against `rewrite` @ `8cab66a`
(the merge of PR-23, #118). PR-24 is **not stacked** (owner, 2026-08-03,
`plans/2026-08-03-addendum-pr23-24-owner-decisions.md` decision 4), so its
baseline is `rewrite` itself and its reviewer diff is `git diff origin/rewrite...HEAD`.

**Sub-plan:** `plans/2026-08-04-pr-24-subplan.md`.
**Deliverable:** `ruff check` only over everything PR-23 did not take — the rule
modules, the `pds3file`/`pds4file` initializers, the holdings-maintenance tools,
the tools/scripts entry points and the test tree. No `ruff format`, no
`ruff format --check` gate, no `# fmt: off` guards. No test is added and no golden
is touched, so the §6.2 gate is an **identical** per-test set in both modes.

**Why this PR's gate is sharper than PR-23's:** PR-24 edits the files that
*generate* the test ids. A `PT006` or `N806` rewrite inside a parametrized test
changes the source pytest builds ids from, so the gate is the **id set**, not the
counts — one id removed and one added would net to zero in a count check.

### 1. Environment

| Item | Value |
|---|---|
| Python | 3.12.3 |
| ruff | 0.15.22 |
| Suite driver | the command lines of `scripts/automated_tests/pdsfile_main_test.sh` — serial, under `coverage run`, plus `-rA --junitxml` |
| Holdings | `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` at the limited testing copy the goldens are tuned to |
| Baseline tree | a detached worktree at `8cab66a`, measured here rather than copied from a record |

### 2. Full-data suite — an identical set in both modes

Regenerated after the last change under `src/` and `tests/`.

| Mode | Baseline @ `8cab66a` | PR-24 head | ids | Diff |
|---|---|---|---|---|
| `--mode ns` | 858 passed / 34 skipped | **858 passed / 34 skipped** | 892 both | **empty** |
| `--mode s` | 555 passed / 3 skipped | **555 passed / 3 skipped** | 558 both | **empty** |

The comparison is id-by-id from the two `junitxml` files: every `testcase` is
reduced to `classname::name -> outcome` and the two maps are compared three ways.

```
ns: 892 vs 892 ids; only-in-baseline 0, only-in-head 0, outcome changed 0
 s: 558 vs 558 ids; only-in-baseline 0, only-in-head 0, outcome changed 0
```

The independently-measured baseline was also checked against the coordinator's
`8cab66a` capture: 892/558 ids, 0/0/0 on both modes, so the two agree and the
baseline is not being taken on trust.

**The id set was additionally measured after the `PT006` rewrite alone**, before
the rest of the test-tree work, by `pytest --collect-only -q` — 892 and 558 ids,
identical id-for-id. `PT006`'s fix is one ruff marks **unsafe**, and this
measurement is what discharges that, rather than an argument about how pytest
builds ids.

**Non-vacuity, at file level.** `coverage.CoverageData.measured_files()` for the
head run lists **72** files under `src/pdsfile/`, including **all 36** rule
modules.

**Non-vacuity, at line level.** Of the **363 executable lines this PR changed**
(`git diff -U0 origin/rewrite...HEAD` intersected with `coverage`'s own statement
set):

| Area | changed executable | executed | how measured |
|---|---:|---:|---|
| rule modules, the two initializers, `show_opus_products.py` | 77 | **73** | the in-process full-data run |
| holdings-maintenance tools | 161 | **108** | a **second** coverage run, see below |
| `tests/**` | 124 | — | `[tool.coverage.run] omit = tests/*`, so coverage cannot report them; the 892 collected ids and 858 passes are what prove these modules import and run |
| `scripts/check_runtime_imports.py` | 1 | — | exercised by the clean-install gate as a subprocess |
| **total** | **363** | **181** | |

**The maintenance tools needed their own measurement, and this is the one thing
the sub-plan did not anticipate.** `tests/holdings_maintenance/` drives the tools
through `subprocess`, so the in-process run records all 17 modules in
`measured_files()` with **zero executed statements** — a coverage number that
looks like total absence of testing and is in fact an artifact of the harness. A
second run of `tests/holdings_maintenance/` with `COVERAGE_PROCESS_START` and a
`sitecustomize.py` that calls `coverage.process_startup()` collects the child
processes: **111 passed**, and 108 of the 161 changed executable lines execute.

The 53 that do not are: **`re_validate.py` entirely (23)** — deviation (6)
freezes it and no test imports it; the four `except (OSError, ValueError)`
fallback branches in the checksum/info tools (17 lines, the `A001` `dir` →
`dirname` renames); three `E701` `return` splits; two `raise OSError` lines; the
`SIM102` collapse in `pds4linkshelf.py`; and two `log_path_for_*` set literals.

### 3. The unreached rewrites — a differential probe

Because 53 tool lines and all of `re_validate.py` are unreached, the
behavior-sensitive rewrites among them were proved directly rather than by
assertion. The probe evaluates the `rewrite` spelling and the PR-24 spelling over
the same inputs and compares:

| Check | Inputs | Result |
|---|---|---|
| `SIM102` nested-`if` collapse — branch taken **and** operand evaluation order | 8 of 8 boolean combinations, with a trace of which operands were evaluated | agree |
| `E721` `type(x) == C` → `type(x) is C` | 7 values including `str` and `list` subclasses | agree |
| `E721` — that `isinstance()` would **not** be equivalent | the same subclasses | confirmed different, which is why the fix is `is` |
| `RUF051` `if k in d: del d[k]` → `d.pop(k, None)` | present and absent key | agree |
| `UP034` parentheses around an `or`-chain in `&=` | 16 of 16 combinations | agree |
| `UP024` `IOError is OSError`, and the two `except` tuples | 3 exception instances | agree |
| `E701` one-line-`if` split | 6 representative sites, `ast.dump` compared | identical AST |
| `C405` `set([…])` → `{…}` | the real literals, incl. one with a duplicate element | agree |
| `UP015` `open(p, 'r')` → `open(p)` | round-trip read | agree |
| `F541` f-string with no placeholder | the `pdslinkshelf.py` message | identical string |
| `UP031` `%s`/`%d` → f-string | str, empty, `%`-containing, custom `__str__`, four ints | agree |
| `E711` / `E712` | str/None values; `False`/`True`/object | agree |
| `E712` — that ruff's suggested `if res:` would **not** be equivalent | an empty falsy value | confirmed different, which is why the fix is `is not False` |

**15 checks, 15 agree, 0 disagree.** The probe is scratch evidence, not a
committed test: PR-24's gate is an identical test-id set, and a new test id is
movement.

**A mechanical check that no rename left a dangling name.** The `A001` and `N806`
work renamed 34 identifiers in the tools and 51 in the test tree, all by AST
position within one function scope. A missed use — or a renamed use whose binding
was missed — is an undefined name, and `F821` reports exactly **1** violation
both at `8cab66a` and at HEAD: the pre-existing `error`/`errors` typo at
`shelf_consistency_check.py`, which deferred entry 6 assigns to a later PR.

### 4. API freeze

`scripts/dump_public_api.py` run against a worktree at `8cab66a` and against
HEAD: **733,876 bytes each, `diff` empty**. `tests/api/test_api_freeze.py` passes,
and all 26 tests under `tests/api/` pass.

The freeze is what stopped three otherwise-obvious fixes: the 31 `F401`s in the
two initializers (every name is a manifest member), `B007` in
`uranus_occs_earthbased.py` (a module-scope loop variable that is a manifest
member), and `N805`/`N802` on the frozen uppercase methods.

### 5. Other gates

| Gate | Result |
|---|---|
| no holdings — `scripts/run-all-checks.sh`, all holdings vars unset | **92 passed / 800 skipped**; ruff, pytest, pyroma, API-freeze and clean-install all green |
| `ruff check src/pdsfile tests scripts` with the project config | clean, over **139 files** (26 pds3 rule modules, 10 pds4, 17 maintenance modules, 2 tools, 2 subpackage initializers, 64 test modules, 3 scripts, 15 PR-23 core) |
| no-ignores re-derivation over the in-scope files | reports exactly the 2,259 permanent violations and nothing else |
| clean install | `scripts/clean_install_check.sh`, via `run-all-checks.sh` — passed |
| `__mro__` for the three `UP004` classes | identical at base and HEAD |
| inline `noqa` | **none added**; the only `noqa` strings in the diff are prose in the sub-plan and this file |
| consumer smoke | see §6 |

### 6. Consumer smoke — same outcome as the baseline

Against `critiques/baselines/consumer-smoke-baseline.md`. The gate is **same
outcome**, so fewer failures would be as much a flag as more.

| Check | Baseline | PR-24 head |
|---|---|---|
| A — rms-opus import paths | 4/4 ok, 0 failures | **4/4 ok, 0 failures** |
| B — rms-viewmaster startup | 5 ok / 3 fail | **5 ok / 3 fail** |

The three check-B failures are the same three: `pdsfile.cache_lifetime` (twice,
once directly and once through `get_page_cache()` with `PAGE_CACHING=True`) and
`pdsfile.DEFAULT_CACHING`. `pdsfile.pdsfile.repair_case` still resolves.

### 7. The ratchet

`per-file-ignores` in scope: **78 entries / 369 code slots → 59 entries / 175
slots**. Nineteen files come off entirely. Whole-file totals including PR-23's
eleven core entries: 89 → 70 entries, 383 → 189 slots.

The shrink property was checked mechanically against `git show
origin/rewrite:pyproject.toml`, not against any intermediate state of this branch:

```
WIDENED (a code present after but not before): NONE
NEW FILES with no committed entry:             NONE
```

Two of the nineteen removals are **stale** entries rather than fixes:
`tests/pds3file/helper.py` and `tests/pds4file/helper.py` both carried `B904`,
and the no-ignores derivation at `8cab66a` reports no `B904` in either file — the
same class of dead entry PR-23 found in `pdsviewable.py`'s `RUF059`.

`scripts/gen_ruff_ratchet.py` was **not** used: deferred entry 33 records that it
emits an empty block against a tree whose committed ignores already suppress
everything, which is exactly this tree. The block is hand-derived from the
no-ignores run and then verified by running the project config.

### 8. Violation arithmetic

Derived with the template select set, `target-version = "py310"`, `line-length =
100`, `extend-ignore = ["PT011", "SIM105", "SIM108"]` and **no**
`per-file-ignores`:

| | |
|---|---:|
| at `8cab66a`, in scope | **2,760** |
| fixed | **501** |
| permanent | **2,259** |

The sub-plan predicted 505/2,255; §11 of it reconciles the four-violation
difference line by line (`I001` −4, `B007` −1, `N806` −3, `A002` +1, `E501` +3),
each of which is a case where the plan's classification was wrong and the
measurement corrected it.

### 9. What this PR deliberately did not do

- **No logging call was converted.** 46 of the 139 permanent `UP031`s are logging
  calls. `pdslogger.PdsLogger.log` treats a lone positional argument as the
  keyword-only `filepath` once the message has no `%` pattern, so the naive lazy
  rewrite is a `TypeError` at every site that already passes a filepath — 69 of
  them, measured. Deferred entry 79 owns the conversion and says in terms that it
  is too large for PR-24. Entry 82 corrects its figures from 130/67 to 132/69.
- **No prose was rewritten** except where a fix in this PR made it wrong — the
  rule stated in sub-plan §4.2, which closes deferred entry 77.
- **Deferred entries 31, 44, 52 and 76 were not acted on**; 31 and 76 need owner
  decisions that have not been given.
