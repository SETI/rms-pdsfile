# Consumer-smoke baseline

**Captured:** 2026-07-26
**pdsfile commit:** `0d588b3` on `rewrite` ("test: maintenance-tool test suite (#105)")
**Required by:** §3.4 item 3 of `plans/2026-07-25-modernization-plan.md`
**Consumed by:** PR-37, whose consumer smoke check diffs its outcomes against
this record.

## Why this exists, and what the gate means

PR-37 runs the rms-opus import-path smoke and the rms-viewmaster startup
against the rewrite branch. **The gate is "same outcome as baseline", not
"passes."** rms-viewmaster has pre-existing failures that already occur against
current pdsfile; ground rule 1 says they are not caused by, and not fixable by,
this rewrite (the owner will patch rms-viewmaster separately), and specifically
that pdsfile must **not** grow package-level `cache_lifetime` / `DEFAULT_CACHING`
to make them go away. Recording them here is what stops a future run from
reading them as a regression.

v1 of the plan specified capturing this in Phase 0 and it was never captured.
It is captured now, before Phase 5 begins: every PR merged to this point
(PR-01–PR-13) is behavior-preserving, so a capture at `0d588b3` is still a valid
stand-in for the Phase-0 state.

## Environment

| Item | Value |
|---|---|
| Python | 3.12.3 |
| pdsfile under test | `0d588b3`, imported from a `rewrite` worktree via `PYTHONPATH` |
| rms-opus | branch `rewrite` @ `73cb6de7`, working tree clean |
| rms-viewmaster | branch `clean_up_viewmaster` @ `a0d05e2`, three untracked entries (`critiques/`, `examples/`, `pyproject.toml`) |
| Holdings | `PDS3_HOLDINGS_DIR` / `PDS4_HOLDINGS_DIR` pointed at the limited testing copy (the root the goldens are tuned to) |

Holdings roots are named only by their environment variables here, per §3.4.

Two environment notes that will bite a re-run:

- **rms-viewmaster's venv does not contain `range_ex`**, which is a declared
  runtime dependency of pdsfile at `rewrite` (`pyproject.toml`), pulled in by the
  pds3 rule modules. Pointing that venv's interpreter at the rewrite source via
  `PYTHONPATH` alone therefore dies at `import pdsfile` with
  `ModuleNotFoundError: No module named 'range_ex'` — an artifact of the harness,
  not a consumer defect. **PR-37 should install the rewrite pdsfile into the
  consumer environment** (`pip install -e <pdsfile>`, as `run-tests-and-opus.yml`
  already does for rms-opus) rather than relying on `PYTHONPATH`. The capture
  below worked around this by running the pdsfile venv's interpreter — so
  pdsfile and all its declared dependencies are coherent — with
  rms-viewmaster's `site-packages` appended to `PYTHONPATH` for Flask/pylibmc.
- rms-viewmaster's untracked `pyproject.toml` is a stray copy of **rms-pdsfile's**
  (`name = "rms-pdsfile"`). It played no part in this capture, but anyone who
  installs rms-viewmaster from that directory will get the wrong metadata.

## Check A — rms-opus import-path smoke

rms-opus touches pdsfile from six modules; the distinct import paths are
`import pdsfile` (`opus/import/{do_import,import_util,obs_base_pds3,obs_base_pds4}.py`),
`from pdsfile import Pds3File, Pds4File` (`opus/import/main_opus_import.py:19`),
and `import pdsfile.pdsviewable` (`opus/application/apps/tools/file_utils.py:16`,
used at `:220` as `pdsfile.pdsviewable.PdsViewSet.from_dict`). Every other
`pdsfile.<name>` in rms-opus is attribute access on a local variable named
`pdsfile`, not on the module.

| Name | Outcome |
|---|---|
| `import pdsfile` | ok |
| `import pdsfile.pdsviewable` | ok |
| `from pdsfile import Pds3File, Pds4File` | ok |
| `pdsfile.pdsviewable.PdsViewSet.from_dict` | ok |

**Result: 4/4 resolve, 0 failures.**

This is a name-resolution smoke. The behavioral integration coverage for rms-opus
is the separate `scripts/automated_tests/opus_main_test.sh` leg of
`.github/workflows/run-tests-and-opus.yml`, which is already in CI and is not
duplicated here.

## Check B — rms-viewmaster startup

Startup is `viewmaster.viewmaster.create_app()` (which calls `init_once()` →
`get_or_create_logger()`, `get_holdings_path()`, `get_page_cache()`) followed by
the two further steps the `__main__` block performs before serving:
`pdsviewable.load_icons()` and `initialize_caches(reset=False)`.
**`app.run()` is deliberately not called** — this baseline never binds a port.

| Stage | Outcome |
|---|---|
| `import viewmaster.viewmaster` | ok |
| `create_app()` | ok |
| `pdsviewable.load_icons()` | ok |
| `initialize_caches(reset=False)` | ok |
| read `pdsfile.cache_lifetime` | **FAIL** — `AttributeError: module 'pdsfile' has no attribute 'cache_lifetime'` |
| `pdsfile.DEFAULT_CACHING` is consumed | **FAIL** — `AssertionError: pdsfile.pdsfile defines no DEFAULT_CACHING` |
| `pdsfile.pdsfile.repair_case` | ok |
| `get_page_cache()` with `PAGE_CACHING=True` | **FAIL** — `AttributeError: module 'pdsfile' has no attribute 'cache_lifetime'` |

**Result: 5 ok, 3 pre-existing failures.** All three are the ground-rule-1
flat-name usages. None is caused by this rewrite and none may be "fixed" in
pdsfile.

### The two flat names, precisely

- **`pdsfile.cache_lifetime`** is read at `viewmaster/viewmaster.py:411` and
  `:421`, inside `get_page_cache()`. pdsfile exposes no such package-level name,
  so the read raises `AttributeError`.

  **This is why `create_app()` nonetheless succeeds here:** the checked-in
  `viewmaster/viewmaster_config.py` sets `PAGE_CACHING = False` on **both**
  branches (testing and as-deployed), so `get_page_cache()` returns before
  reaching either read. The failure is therefore *latent in this configuration
  and live in any deployment that turns page caching on* — which is why the
  table above forces the branch as its own stage rather than declaring startup
  clean. A future run that reports `create_app()` as passing has **not**
  demonstrated that `cache_lifetime` is fine.

- **`pdsfile.DEFAULT_CACHING`** is *assigned* at `viewmaster/viewmaster.py:58`
  (`pdsfile.DEFAULT_CACHING = 'dir'`). An assignment onto a module object always
  succeeds, so this produces no traceback at all — it is a **silent** no-op:
  pdsfile defines no `DEFAULT_CACHING` at package level or in
  `pdsfile.pdsfile`, and nothing reads the attribute viewmaster sets. The
  intended "cache all directories" configuration is simply not applied. The
  stage above asserts the name's absence explicitly so the silence is recorded
  as a fact rather than mistaken for success.

- **`pdsfile.pdsfile.repair_case`** (`viewmaster/pdsiterator.py:104`) is a third
  flat-ish usage, reaching through to the `pdsfile.pdsfile` submodule. It
  **resolves** today. It is listed here because Phase 5 moves module-level
  functions into private modules while `pdsfile/pdsfile.py` keeps re-exporting
  every name it exports today — `repair_case` is one of the names that
  re-export must preserve, and this baseline is where a regression would show up.

## Reproducing

From the pdsfile repo, with the holdings environment variables exported:

```bash
# Check A — rms-opus import paths
python -c "
import pdsfile, pdsfile.pdsviewable
from pdsfile import Pds3File, Pds4File
assert callable(pdsfile.pdsviewable.PdsViewSet.from_dict)
print('opus import-path smoke: ok')
"

# Check B — rms-viewmaster startup (run from the rms-viewmaster checkout, with
# the rewrite pdsfile installed into that environment; never call app.run())
python -c "
from viewmaster import viewmaster as m
m.create_app()
m.pdsviewable.load_icons(path=m.ICON_ROOT_, url=m.ICON_URL_,
                         color=m.ICON_COLOR, logger=m.LOGGER)
m.initialize_caches(reset=False)
import pdsfile
for probe in ('cache_lifetime', 'DEFAULT_CACHING'):
    print(probe, 'present' if hasattr(pdsfile, probe) else 'ABSENT (expected)')
"
```

The `get_page_cache()` stage is reproduced by setting `m.PAGE_CACHING = True`
and `m.PAGE_CACHE = None` before calling `m.get_page_cache(m.LOGGER)`.

## What PR-37 must conclude

- Check A must still be **4/4 ok**. Any failure is a real regression against
  ground rule 1's protected consumer.
- Check B must produce the **same 5 ok / 3 fail split, with the same three
  failures**. Fewer failures is as much a flag as more: if `cache_lifetime` or
  `DEFAULT_CACHING` starts resolving, pdsfile has grown a package-level name
  that ground rule 1 forbids.
- `pdsfile.pdsfile.repair_case` must still resolve after the Phase 5 extraction.
