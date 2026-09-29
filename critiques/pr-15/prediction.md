# PR-15 — the pass/fail-set prediction, written before the fixes

**Provenance.** This text was written at commit `b646aee` — the tests-only
commit, before a single change under `src/pdsfile/` — and is reproduced here
verbatim from that point. It is committed as part of PR-15's records commit,
which necessarily comes later than the thing it records; `b646aee` itself
contains only `tests/core/` and the suite-driver edit. Read it as "written
before the runs", not "committed before the runs". `critiques/phase5-validation.md`
§3c cites this file.

---

Written at commit b646aee (tests only, no `src/` change yet).

## The prediction

1. **`--mode s`** (`tests/pds3file/ tests/rules/pds3/`): the per-test set is
   **byte-identical to the baseline** — 555 passed / 3 skipped, 558 ids.
   `tests/core/` is not in that invocation.
2. **`--mode ns`**: the set is the baseline's 824 ids with **exactly the 33 new
   `tests/core/...` ids added, all passing** — 823 passed / 34 skipped, 857 ids.
   **No pre-existing test id changes outcome, in either direction.**
3. **No-holdings run** (whole `tests/` tree, no holdings env vars): 24 + 33 = 57
   passed / 800 skipped, 857 collected. All of `tests/core/` is marked
   `holdings_free`.

## Why bug 1 is predicted not to move anything

`html_path`'s `self._recache` → `self._recache()` restores this:

```python
logical_lc = self.logical_path.lower()
if logical_lc in cls.CACHE and (self.is_merged == cls.CACHE[logical_lc].is_merged):
    cls.CACHE.set(logical_lc, self)
```

- **The suite's cache is a `DictionaryCache`** (`MEMCACHE_PORT = 0`, no memcached
  and no pylibmc installed). A `DictionaryCache` stores the object itself, and
  `_complete()` hands back the cached object, so `self` normally *is* the value
  already stored under `logical_lc`. Re-setting it cannot change what any later
  reader gets.
- What the write-back does change is the entry's **expiration** (recomputed by
  `cache_lifetime_for_class`) and its membership in `DictionaryCache.keys`, the
  trimmable set. Neither is a returned value.
- **Trimming cannot fire**: `_trim()` needs `len(keys) > limit + slop` =
  200,000 + 20,000. The suite's cache is orders of magnitude smaller.
- The same `_recache()` call already runs on ~40 other lazy properties
  (`split`, `anchor`, `is_viewable`, `infoshelf_path_and_key`, …), so this is
  the established behavior of the property pattern, not a new mechanism.
- Only three pre-existing test ids read `PdsFile.html_path` at all
  (`test_pds3file_blackbox.py::TestPdsFileBlackBox::test_html_path`, 2 params,
  and `test_pds3file_whitebox.py::TestPdsFileWhiteBox::test_html_path`, 1
  param). Each asserts the returned string; none inspects cache state. The four
  `.url` reads in `test_pdsviewable_blackbox.py` are `PdsViewable.url`, a
  different class.

## Why the other six cannot move anything

- **2, 4, 5, 6** (`get_permanent_values`, both `set_multi`s, `iconset_for`) have
  **no caller anywhere in `src/` or `tests/`** — measured by grep, not assumed.
  `get_permanent_values` is called only from `preload` on the memcached branch
  (`cls.MEMCACHE_PORT` non-zero), which the suite never takes.
- **3** changes only *which environment-variable name* is read, and only on the
  `abspath_for_logical_path` branch reached when nothing is preloaded and no
  holdings list is cached. The suite always preloads, so `cls.LOCAL_PRELOADED`
  is non-empty and that branch is unreachable during a data run. For `PdsFile`
  and `Pds3File` the name is unchanged regardless.
- **7** changes only which exception classes escape `infoshelf_path_and_key`.
  `shelf_path_and_key_for_abspath` raises `ValueError` (3 sites), `KeyError`
  (`SHELF_PATH_INFO[shelf_type]`) and `AttributeError` (`abspath is None`) —
  all `Exception` subclasses, all still caught. Only `BaseException`s
  (`KeyboardInterrupt`, `SystemExit`, `GeneratorExit`) newly escape, and the
  suite raises none of them there.

## What counts as a violated prediction

Any pre-existing test id whose outcome differs from the baseline, in either
direction. That is a hard stop, reported rather than explained after the fact.
