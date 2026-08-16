# PR-35 validation record — public API type stubs

Branch `feat/api-stubs`, stacked on PR-34's `docs/readme-rewrite` (PR #153), which stacks
on PR-33's `docs/dev-guide` (PR #152). Everything here is measured on this tree; nothing
is projected.

## Plan of record

**Deliverable (plan §5, PR-35).** Hand-written `.pyi` stubs for the public surface, plus
`src/pdsfile/py.typed`, validated with `mypy.stubtest`; mypy added to the `dev` extra for
stubtest only; a stubtest gate wired into `scripts/run-all-checks.sh` and the CI lint job
the way the existing gates are wired (`ENABLE_STUBTEST`, following the
`ENABLE_PYMARKDOWN` pattern PR-34 set). `ENABLE_MYPY` stays false: ground rule 5 waives
inline typing and the type-check gate permanently, and the stubs change no runtime
behavior — a `.pyi` file is never executed.

**Files.** One stub per public module of the frozen manifest
(`tests/api/api_manifest.json`, read-only), in this order:

1. `src/pdsfile/pdscache.pyi` — first, to establish stubtest mechanics on a
   self-contained module.
2. `src/pdsfile/pdsviewable.pyi`
3. `src/pdsfile/pdsfile.pyi` — the `PdsFile` class flattened: the class at runtime
   assembles its members from nine private mixin modules, and the manifest (which is
   blind to mixin structure by construction) records 217 public members on the class;
   the stub declares all of them in one body, so the private mixins need no stubs and
   the stub is stable against any future re-mixing.
4. `src/pdsfile/pds3file/__init__.pyi` — `class Pds3File(PdsFile)` plus its own-body
   members only (measured: 73 public names in `vars(Pds3File)`).
5. `src/pdsfile/pds4file/__init__.pyi` — same shape (47 own-body names).
6. `src/pdsfile/preload_and_cache.pyi` — the nine re-exported preload names, typed at
   their `_preload` definitions.
7. `src/pdsfile/pds3file/rules/__init__.pyi`, `src/pdsfile/pds4file/rules/__init__.pyi`,
   and one `.pyi` per rule module (25 pds3 + 9 pds4). Each rule class subclasses
   `Pds3File`/`Pds4File` and declares only its own-body members — stubtest resolves
   inherited names through the stub's MRO, which is what makes the manifest's 8,645
   class entries reduce to the measured own-body surface (537 public own-body members
   across the 39 manifest classes, plus the mixin-provided members flattened into
   `PdsFile`).
8. `src/pdsfile/__init__.pyi` — `__version__`, the `PdsFile` re-export, and the
   star-import surface of the two subpackages.
9. `src/pdsfile/py.typed` (empty marker, PEP 561).

The private modules (`_associations.py`, `_derived_paths.py`, `_index_rows.py`,
`_local_fs.py`, `_opus.py`, `_path_utils.py`, `_preload.py`, `_properties.py`,
`_shelves.py`, `_sorting.py`, `_version.py`) and the tool/maintenance subpackages get no
stubs: they are not in the manifest, and with `py.typed` present a type checker falls
back to their (unannotated) sources without error.

**Scope note.** The plan names `__init__.pyi` plus five module stubs and measures their
140 module-level names; it also measures the class surface across all 36 rule
subclasses and gives `class GO_0xxx(Pds3File): ...` as the stub form that satisfies
inheritance — which is only meaningful if the rule modules are stubbed. The manifest
is the coverage contract ("covering exactly the manifest names"), so the rule modules
and `preload_and_cache` (a manifest module the plan's list does not name, 9 names) are
stubbed too. Runtime, not the manifest, is the arbiter where the two disagree: the
manifest still records the rule modules' `test_*`/test-support names that PR-08 removed
(the second pre-approved forgiveness category), and stubtest checks stubs against
runtime, so the stubs carry the runtime surface — manifest names minus the two forgiven
categories, nothing else.

**How each type is derived.** The implementation is unannotated; every annotation is
derived from the implementation code and its docstrings (Phase 7 gave every public
member a Google-style docstring with typed `Returns:`/`Parameters:` sections). The
typing rule is the plan's, applied in this order:

1. The code wins. Where a docstring and the code disagree, the code's type is declared
   and the discrepancy is recorded in this file.
2. Broad over narrow. A union covers every return path (`str | None` for a method with
   a bare-`None` path); a container type is declared at what the code builds (`list`,
   not `Sequence`, when callers may mutate); where the truth is genuinely dynamic, the
   type is `Any` — a wrong narrow type in a stub is worse than a broad one, because
   stubtest cannot catch it and it turns correct consumer code into type errors.
3. Untyped dependencies stay `Any`. `rms-pdslogger`, `rms-translator`, `rms-pdsparser`,
   `rms-pdstable` ship no `py.typed` marker (verified in the dev venv), so their types
   cannot be named in a stub; attributes holding them are declared through commented
   private `Any` aliases (`_PdsLogger`, `_Translator`, ...), which keeps the reason
   visible at every use.

Modern 3.11 stub syntax throughout: `X | None`, builtin generics, no `typing.Optional`,
no `typing.List`.

**Stubtest invocation and allowlist policy.** The gate runs, from the venv:

    MYPYPATH=src python -m mypy.stubtest <the 43 stubbed modules>

and its full output is read and recorded — never tailed. A pass proves the stubs' names,
kinds and signatures match the runtime; it does **not** prove the annotated types are
true, because the runtime carries no annotations to compare against. Type truth is
established by the derivation rule above and checked by the adversarial review rounds,
whose reviewers are instructed to verify stub types against the implementation. The
allowlist starts empty and stays minimal: an entry is added only for a name stubtest
cannot model, with a comment saying why, and an empty allowlist means the file is absent
rather than present-and-empty.

**Known risk (deferred observation 58).** On a host with `pylibmc` installed,
`pdscache.py` binds the name `pylibmc` and sets `MEMCACHED_LOADED = True`, changing the
runtime surface stubtest introspects. This machine does not have `pylibmc`
(`ModuleNotFoundError`, verified), so the stubs are written against the
`MEMCACHED_LOADED = False` surface, matching the committed manifest. If stubtest on any
host reports a `pylibmc`-related diff that would force a manifest or allowlist decision,
that is a hard stop to the owner, not a choice this PR makes.

**Gates.** All active gates (§2 table): `./run-all-checks.sh` exit 0 with every section
read; full suite at baseline both modes against `/seti/opus/pdsdata` holdings (ns
1205/34, s 555 pds3 / 123 pds4); both Sphinx builds clean (stubs must not break
autodoc); clean-install gate green, plus a check that the built wheel and sdist actually
contain `py.typed` and every `.pyi` (packaging config decides; a missing package-data
rule fails silently); API-freeze unchanged (stubs are invisible to it — the dumper
introspects runtime); ruff ratchet untouched. Then the §6.6 loop to convergence.

**Scheduled observations owned by PR-35.** Entries 1300 (`DictionaryCache.
preload_eligible` has no reader) and 1301 (two exported names read by nothing) are
listed as "a future cleanup PR, or PR-35 when it decides what the stubs declare". PR-35
decides: the stubs declare the runtime surface as it is — `preload_eligible: bool`,
`DICTIONARY_CACHE_LIMIT: int`, `MEMCACHED_LOADED: bool` — because removing any of them
is an API-manifest diff, which is a hard stop this PR does not take. The removal
question stays open and moves to the post-merge register (P3) with the decision
recorded.

## Execution log

### Stubtest mechanics (measured before the plan was frozen)

* `MYPYPATH=src python -m mypy.stubtest pdsfile.pdscache` against the finished
  `pdscache.pyi`: `Success: no issues found in 1 module`, exit 0. Established: instance
  attributes declared in a stub class body are accepted; underscore members may be
  omitted; stdlib module attributes (`os`, `sys`, ...) may be re-exported with the
  `import X as X` form; `pylibmc` absent locally, so the optional-import surface
  matches the manifest.
* mypy build note: `DictionaryCache` has attributes named `dict` and `keys`, which
  shadow the builtins inside the class body; the stub qualifies those annotations
  through `import builtins`.
* Package-walk behavior, measured: `stubtest pdsfile` walks the whole inline
  package — in a PEP 561 inline-typed package every `.py` without a `.pyi` beside it
  *is* the stub for its module — so the private mixins, `holdings_maintenance` and
  `tools` join the build (79 modules total). Their unannotated sources must not fail
  the mypy build stubtest runs first, which is what the `[tool.mypy]` section in
  `pyproject.toml` exists for (`ignore_missing_imports` for the untyped
  dependencies; `ignore_errors` scoped to exactly those non-public modules). The
  section is read by nothing but this gate.

### How the stubs were derived and audited

The member surface was measured mechanically (a script over the runtime, using the
manifest dumper's own classifiers) into per-module work lists carrying every public
name, kind, and runtime signature string. Type derivation was then done by reading
every implementation module in full — five parallel derivation passes covering
`_properties.py` (64 members), `pdsfile.py` (91 members + 25 public instance
attributes + the module-level names), `_sorting.py`/`_shelves.py`/`_index_rows.py`
(35), `_derived_paths.py`/`_local_fs.py`/`_preload.py`/`_associations.py`/`_opus.py`
(27), and the two subclass initializers (73 + 47) — each producing, per member, the
declared type and its deriving evidence (file:line), plus a code-vs-docstring
discrepancy list. The 36 rule-module stubs were generated from the measured surface
by a script whose type table fails loudly on any name it has no entry for; the seven
rule-class methods and every non-translator data name were hand-derived. The
executor then audited the assembled stubs: spot-checks against the source
(`childnames`, `exists`, `IDX_EXT`/`LBL_EXT`, the log-path builders), one
wrong-narrow type caught and fixed before any review round — the derivation pass
gave `Pds3File.CACHE: DictionaryCache`, but `_preload.py:583` rebinds `CACHE` to a
`MemcachedCache` when `preload(port=...)` is used (the Viewmaster path), so all
three classes declare `DictionaryCache | MemcachedCache` — and a consumer's-eye
mypy run over a usage snippet confirming the stubs drive `reveal_type` usefully
(`exists -> bool`, `abspath -> str | None`, `CACHE -> DictionaryCache |
MemcachedCache`, `iconset_for -> PdsViewSet`).

Notable stub-shape decisions, each mirroring a runtime truth:

* `PdsFile.SUBCLASSES` is declared once, on the base, as `dict[str,
  type[PdsFile]]`. The subclasses do carry their own dicts at runtime, but `dict`
  is invariant, so redeclaring the narrowed value type is a mypy `[assignment]`
  error; the base declaration is inherited and stubtest resolves it through the
  MRO. Broad-and-true over narrow-and-rejected.
* The two rules packages define `__all__` at runtime; stubtest compares it, so the
  stubs mirror the runtime lists verbatim (24 entries pds3, 4 entries pds4).
* `pdsfile/__init__.pyi` replaces the implementation's two star imports with
  explicit `as`-form re-exports of every manifest name, because the two stars both
  export a name `rules` (a mypy `[no-redef]` build error) and at runtime the later
  import wins — the stub binds `rules` to the pds4file rules package explicitly and
  says why.
* Five class members override an incompatibly-typed base member at runtime
  (`FILENAME_KEYLEN` as a method in three classes over the base's `int`,
  `DATA_SET_ID` as a method in `COUVIS_0xxx` over the base's data attribute,
  `COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH` as a plain function in the class
  body with no `self`). The stubs declare what the runtime does and carry per-line
  `type: ignore[override]`/`[misc]` suppressions naming the pattern.
* Untyped-dependency names are re-exported with `# type: ignore[import-untyped]`
  (the manifest freezes `pdslogger`, `translator`, `pdsparser`, `pdstable` and
  stdlib module names as public module attributes), and values typed by those
  libraries are commented `Any` aliases (`_Translator`, `_PdsLogger`).

### Ruff and the stubs

`ruff check` over the new `.pyi` files reports 141 findings, dominated by the
naming codes the ratchet already records as permanent for the same names' `.py`
homes (`N801`/`N999`/`N802`/`N805`/`A002` — frozen class, module, method and
parameter names) plus stub-layout codes (`E501` in generated tables). The ratchet
may only shrink and inline `noqa` is prohibited, so neither of the two compliant
routes exists for new files carrying frozen names; the stubs are excluded from ruff
via `extend-exclude = ["*.pyi"]` with a comment in `pyproject.toml` saying exactly
this. Stub imports were still sorted to isort order voluntarily (`ruff check
--isolated --select I --fix` over explicit paths, which bypass the exclusion).
`ruff check` over `src/pdsfile tests scripts docs` passes unchanged; the ratchet
table is untouched.

### Stubtest gate result (this tree)

    MYPYPATH=src python -m mypy.stubtest --mypy-config-file pyproject.toml \
        --allowlist scripts/stubtest_allowlist.txt --ignore-unused-allowlist pdsfile

    Success: no issues found in 79 modules

79 modules = the 43 stubbed modules (7 top-level + 36 rules) plus the 36
unstubbed private/maintenance/tool modules the inline-package walk includes.
Allowlist: **2 entries**, both private-module dynamics stubtest cannot model
(`_path_utils._clean_glob`, an `functools.lru_cache` wrapper whose runtime
signature is the wrapped function's; `_preload.pylibmc`, the guarded optional
import — absent at runtime here, present on a pylibmc host, which is why the gate
passes `--ignore-unused-allowlist`; deferred observation 58 context). **What this
pass proves:** every stubbed name exists at runtime with the declared kind,
signature shape and defaults, and no public runtime name is missing from the
stubs. **What it cannot prove:** that any annotated type is true — the runtime is
unannotated, so there is nothing for stubtest to compare a type against. Type
truth rests on the derivation evidence above and the adversarial rounds below.

### Per-member derivation evidence and the code-vs-docstring discrepancies

The full per-member evidence — declared type, deriving file:line, and a clause —
lives in `critiques/pr-35/derivation-*.md`, one file per derivation pass. Their
`## Discrepancies` sections record every place a docstring claims a narrower type
than the code proves; the ones that shaped the stubs:

* `__init__`'s attribute comments present `abspath`, `disk_`, `root_`,
  `html_root_` as strings; `new_merged_dir` sets all four to `None`
  (`pdsfile.py:739-744`), so the stubs say `str | None`. The class docstring
  already admits this; the attribute comments do not.
* `copy`, `new_merged_dir`, `new_index_row_pdsfile` docstrings say "Returns:
  PdsFile"; each provably returns `type(self)`/`cls()` — declared `Self` (narrower
  *and* provable, the one direction the typing rule allows).
* `from_opus_id`'s docstring says "Returns: PdsFile"; when a rule class implements
  `OPUS_ID_TO_PRIMARY_LOGICAL_PATH` as a plain function the method returns that
  untyped call's result verbatim (`_opus.py:156-157`) — declared `Any`.
* `abspaths_for_basenames` says "the absolute paths"; a merged-directory child
  contributes `None` (`_sorting.py:879`) — declared `list[str | None]`.
* `split_basename` documents a 3-tuple; the `SPLIT_RULES is None` branch returns
  the bare `str` and the other branch flows through the untyped translator —
  declared `Any`.
* `volset_pdsfile`/`volume_pdsfile` docstrings say `Pds3File`; the base's rank
  branch flows through `all_versions()[rank]`, provably only `PdsFile` — declared
  `PdsFile | None`.
* `_properties.py` carries the bulk (24 discrepancy entries): most lazy
  properties' docstrings state the intended `str`/`int`/`bool` while the value
  flows from the untyped cache, a translator table, or unpickled shelf content;
  those are declared `Any` (`size_bytes`, `width`, `height`, `date`, `checksum`,
  `opus_id`, `icon_type`, ...), with the provable minority concrete (`exists`,
  `isdir`, `islabel: bool`; `alt`, `url`, `filespec`, `global_anchor`: `str`;
  `viewset: PdsViewSet | bool`).
* The source spells `FOEVER_FILE_CACHE_LIFETIME` (sic); the stub reproduces the
  frozen name.

### Gate results (this tree, holdings `/seti/opus/pdsdata`)

`./scripts/run-all-checks.sh --sequential` with both holdings roots exported:
**exit 0**, every section read individually:

| Gate | Result |
|---|---|
| ruff check (+ indentation pass) | passed, ratchet untouched |
| pytest `--mode ns` (holdings: full) | **1205 passed, 34 skipped** — identical to baseline |
| pyroma | passed |
| API-freeze | passed (stubs are invisible to the dumper, which introspects runtime) |
| clean-install | passed (throwaway venv, runtime deps only, full module surface imports) |
| stubtest | **Success: no issues found in 79 modules** |
| Sphinx `-W` | exit 0, 0 problem lines, API reference 78 of 78 modules |
| Sphinx `-n -W` (own BUILDDIR) | exit 0, 0 problem lines, API reference 78 of 78 modules |
| PyMarkdown | passed (2 files scanned) |

Shelves-only mode, run separately:

| Suite | Result |
|---|---|
| `tests/pds3file tests/rules/pds3 --mode s` | **555 passed, 3 skipped** — identical to baseline |
| `tests/pds4file tests/rules/pds4 --mode s` | **123 passed, 31 skipped** — identical to baseline |

Packaging: `python -m build` produces a wheel and an sdist that each carry all
**43 `.pyi` files and `py.typed`** (counted in the archives, not inferred from
config). The stubs change no runtime behavior — a `.pyi` is never executed and
`py.typed` is an empty marker — so identical suite numbers are the expected
result, and the pass/fail set diff is empty by construction.

### The adversarial loop (§6.6)

Four rounds, each a fresh no-context reviewer; records in
`critiques/pr-35/round-<k>.md`. Round 1 (full diff): 2 Major — both wrong-narrow
types, the defect class the typing rule names as the worst — and 4 Minor; all
fixed, and writing the missing evidence rows surfaced one further instance of
the Major-1 shape, fixed in the same pass. Round 2 (full diff, weighted to round
1's blind spots; the reviewer also machine-checked all 153 concrete data
annotations against live runtime values): 0 Major, 3 new Minor; all fixed.
Round 3 (full diff, independent sampling): 0 Major, 2 new Minor — one of them
the round-2 defect shape in its single remaining sibling; all fixed. Round 4
(scoped per the cap rule): every resolution confirmed in the tree, gates re-run
green, **zero Major — goal met, loop terminated**. No finding was rebutted;
every one was fixed. Every fix round touched only `.pyi` and record files (and
`pyproject.toml`'s ruff exclusion once), never a runtime `.py`, so the full-data
record above carried forward per §6.6 step 5, and each round's reviewer verified
that claim against the actual commit diffs.
