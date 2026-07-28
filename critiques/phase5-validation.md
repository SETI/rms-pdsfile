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

| Run | pdsfile modules measured |
|---|---|
| baseline | `<worktree>/src/pdsfile/{pdsfile,_path_utils,_shelves,_local_fs,_derived_paths}.py` — and **no** `_index_rows.py` or `_opus.py`, because neither exists at `80cd9ff` |
| this branch | `<main tree>/src/pdsfile/{pdsfile,_path_utils,_shelves,_local_fs,_derived_paths,_index_rows,_opus}.py` |

The absence of the two new modules on the baseline side is the decisive bit: had
the worktree run leaked into the main tree's install, they would have been
measured there too. The lists are otherwise identical, module for module. The
one baseline-side path that matches the text `_opus` is
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
`174fe7a` ("refactor: extract OPUS support into a mixin"), at **17:00:33**. The
head runs recorded above postdate it: their `--junitxml` timestamps are
**17:04:18 and 17:06:10**. The baseline runs (16:52:39 and 16:54:29) were taken
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

`pdsfile.py`: 5,125 → 4,593 lines; `_index_rows.py` 308, `_opus.py` 284. All
counted at HEAD.

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
not be: without the import, `ruff check` reports `F821 Undefined name PdsFile` on
`_opus.py:162` under the project's own configuration, so a pure-move commit
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
`_opus.py` has **exactly one**, at line 166, inside `opus_products`, bound by the
deferred import at line 164. `_index_rows.py` has **none**. So the preamble's
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

The distinct (file, code) pairs move 18 → 18 + 2 + 2, and the number of
suppressed violations is unchanged at 21 across the three files. Neither new
module needs `I001`: both import blocks are already isort-clean, which is why
that row conserves rather than growing.

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

| Method | Contexts | Where |
|---|---|---|
| `get_indexshelf` | 9 | `test_pds3file_blackbox.py`, `test_pds3file_blackbox_cached.py`, `test_pds3file_whitebox.py` |
| `find_selected_row_key` | 12 | same three |
| `child_of_index` | 9 | same three |
| `data_abspath_associated_with_index_row` | 4 | `test_pds3file_blackbox.py`, `test_pds3file_whitebox.py` |
| `data_pdsfile_for_index_row` | **0** | — |
| `from_filespec` | 2 | `test_pds3file_blackbox.py`, `test_pds4file_blackbox.py` |
| `from_opus_id` | 19 | the two blackboxes, `test_pds3file_whitebox.py`, and every `tests/rules/pds3/` and `tests/rules/pds4/` module |
| `opus_products` | 28 | every `tests/rules/pds3/` and `tests/rules/pds4/` module |

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

**One near-miss worth recording.** Every rule module defines a module-level
`opus_products = translator.TranslatorByRegex([...])` table, which the rule class
consumes as `OPUS_PRODUCTS = opus_products + …`. It is a *module* global, not a
class attribute, so it never shadows `_OpusMixin.opus_products` — verified: no
rule module has an indented `opus_products =`, and the hierarchy intersection
above is empty. The name is one namespace away from the method the mixin now
owns, and this is recorded as deferred observation 52.

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

| Name | rms-opus | rms-viewmaster |
|---|---|---|
| `from_filespec` | 11 references, e.g. `obs_base_pds3.py:90`, `do_import.py:1480` | — |
| `from_opus_id` | 3, `do_import.py:687,690` | — |
| `opus_products` | 3, `do_import.py:1487` | — |
| `find_selected_row_key` | 2, `do_import.py:1553` | — |
| `data_pdsfile_for_index_row` | — | 3, `viewmaster.py:873,1449,1580` |

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

Four entries are **added**: 49 (the `__bases__` string sniff, which the plan's
PR-19 section explicitly asks be recorded as a phase-"b" item rather than fixed),
50 (`data_pdsfile_for_index_row` has zero in-process test coverage while
rms-viewmaster calls it at three sites), 51 (the four measured coverage gaps
§10's green controls found), and 52 (the rule modules' module-level
`opus_products` table, one namespace away from the mixin method).

### 16. Review loop

| Round | Verdict | Findings | Record |
|---|---|---|---|

*(Rows are written only after the round they describe has run and its record file
exists on disk — the rule PR-18's round-3 Major established.)*
