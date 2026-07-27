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
**Last change under `src/pdsfile/`:** commit `37d4246` (the round-1 fix), at
01:18:32. Every run recorded below was regenerated after it, per §6.6 step 5 —
the four `--junitxml` timestamps are 01:19:13, 01:22:05, 01:24:02 and 01:26:51.

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

1. `pytest tests/api/` passes. `tests/api/api_manifest.json`,
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

Four new entries in `critiques/deferred-observations.md`, all raised by the
review loop and all out of scope for a pure move:

| # | Observation | Raised in | Owner |
|---|---|---|---|
| 29 | An extraction sweep must also ask which module namespaces the tests *patch* — and which module-level *data* they rebind — not only which globals the code *reads*. The first half is the direction that produced this PR's one Major | round 1 (+ round 3) | PR-17 onward |
| 30 | `repair_case` raises `UnboundLocalError` on a single-component path | round 1 | PR-23 |
| 31 | `src/pdsfile/__init__.py`'s `from pdsfile import *` is a self-import that binds nothing, and is not simply fixable | round 2 | PR-24 |
| 32 | A commented-out line rode along in the byte-for-byte move, so PR-22's dead-code line list must be rebuilt against the post-Phase-5 module set | round 2 | PR-22 |

No entry in the existing 1–28 is resolved or invalidated by this PR, and none of
them owns a symbol it touches.

### 11. Review loop

| Round | Verdict | Findings | Record |
|---|---|---|---|
| 1 | goal **not** met | **1 Major**, 4 Minor, 2 Deferred — the Major and all four Minor accepted and fixed, none rebutted | `critiques/pr-16/round-1.md` |
| 2 | goal met | 0 Major, 5 Minor (4 accepted and fixed, 1 rebutted), 3 Deferred (2 new entries) | `critiques/pr-16/round-2.md` |
| 3 | goal met | 0 Major, 6 Minor (all accepted and fixed, none rebutted), 2 Deferred (one folded into entry 29) | `critiques/pr-16/round-3.md` |

Round 1's Major is the one worth carrying forward: the moved code was
byte-perfect and every *call site* resolved, but a test **patched** the namespace
the moved function used to resolve through, so it silently stopped exercising the
code it was written for while still passing. The §6.2 set diff cannot see that
class of defect, which is what the adversarial round is for. Deferred entry 29
turns it into a step for PR-17 onward.

Round 1's fixes touched `src/pdsfile/pdsfile.py`, so the full-data record was
regenerated before round 2 (§6.6 step 5) — both trees, both modes, after commit
`37d4246`. Later rounds changed only `plans/` and `critiques/`, which under that
same rule does not stale the record, so the runs recorded in §3 carry forward
unchanged.

The one rebuttal is round 2's "the PR does not exist yet": §6.6 runs the loop
**before** the PR is opened ("Termination — … Then open the PR"), so a reviewer
cannot see the PR description at review time by construction. It is recorded in
`critiques/pr-16/round-2.md` rather than actioned.
