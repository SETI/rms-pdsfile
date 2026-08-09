# PR-31 validation — the Sphinx tree, the API reference, and a documentation gate that fails

Base: `8f8d825`. Branch: `pr-31-sphinx-scaffolding`. Base branch: `rewrite`. PR #135.

Every command below was run with the tree's interpreter,
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3, Sphinx 9.1.0), from the tree being
measured. Where holdings are needed the environment carried `PDS3_HOLDINGS_DIR`,
`PDS4_HOLDINGS_DIR` and `PDSFILE_TEST_HOLDINGS=full`. The base tree is a second worktree
at `8f8d825`, so "base" numbers were measured rather than recalled.

**Every gate was run with its output to a file, its exit status read, and its totals
grepped out of that file.** The deliverable here is not prose but build behavior, so the
defect this PR could most easily have shipped is a gate that runs and cannot fail.
Sections 4 and 10 are the evidence about that, and the review found that the first
version of the gate could indeed report success over a `docs/_build` that did not exist.

## 1. Scope, which is wider than the brief's list

| file | what happened |
|---|---|
| `docs/conf.py` | new |
| `docs/index.rst` | new |
| `docs/api/index.rst`, `core.rst`, `holdings_maintenance.rst`, `pds3file.rst`, `pds4file.rst`, `tools.rst` | new |
| `docs/Makefile` | new |
| `README.md` | one line: the `<!-- start-after-point -->` marker |
| `scripts/run-all-checks.sh` | `ENABLE_SPHINX` true; `run_sphinx_build()` rewritten; two helper functions added; `RUFF_TARGETS` gains `docs`; three header comments brought to current state |
| `scripts/gen_ruff_ratchet.py` | **not on the brief's list.** `TARGETS` gains `docs`, because its own comment requires it to stay in step with the ruff targets in `run-all-checks.sh` |
| `.cursor/skills/run-all-checks/SKILL.md` | **not on the brief's list.** It described a one-build docs gate, which was inert while `ENABLE_SPHINX` was false and became wrong the moment it was true (section 10, round 2 finding 4) |

Three items on the brief's list turned out to need nothing, and two files it did not name
turned out to matter:

* **`.gitignore` needs no entry.** Line 75 is already `docs/_build/`, which covers both
  build trees this gate writes, `docs/_build/html` and `docs/_build/nitpicky`. Verified
  after a build with `git check-ignore -v docs/_build/html/index.html
  docs/_build/nitpicky/html/index.html` (both matched `.gitignore:75`) and with
  `git status --porcelain -uall`, which listed the new source files and nothing under
  `_build`.
* **`.readthedocs.yaml` needs no edit.** It already names `docs/conf.py` and already
  installs the project with the `docs` extra, which is the arrangement this tree wants.
  It is unedited. What it does **not** set is `sphinx: fail_on_warning`, so the published
  site is a second, ungated build path -- section 6.2 and deferred 334 are about what
  that lets through.
* **The workflow file needs no edit.** Section 5 proves that from the job log rather than
  from the workflow text.
* **`make.bat` was not added.** Windows is not a supported platform here: the matrix in
  `.github/workflows/run-tests.yml` says "Windows is no longer supported and has been
  removed from the matrix". A build file for a platform nothing tests is a file that
  rots.
* **`scripts/read-docs.sh` was not on the brief's list and this PR is what makes it
  live.** It builds with `-W` and no `-n`, and without `make clean`, so it is half of
  this gate and incremental besides. It is a preview tool rather than a gate; it was left
  alone rather than quietly broadened, and deferred 331 records it.

## 2. The page set

Five pages grouped by subpackage plus a landing page, covering every module under
`src/pdsfile` except the gitignored `_version.py`, which does not exist in a source
checkout:

| page | modules |
|---|---:|
| `api/core.rst` | 15 |
| `api/holdings_maintenance.rst` | 23 |
| `api/pds3file.rst` | 27 |
| `api/pds4file.rst` | 11 |
| `api/tools.rst` | 2 |
| | **78** |

Counted from the tree, not from the brief: `find src/pdsfile -name '*.py' | wc -l` is 78,
and the grouping is by the second component of the dotted name. The brief's module table
was right this time, to the module. Each entry carries `:members:`, `:undoc-members:` and
`:show-inheritance:`, which `doc_dev_guide.mdc` section 6 requires on every `automodule`,
plus `:special-members: __init__`, which section 8 explains.

## 3. The two warning families, reproduced and fixed

### 3.1 The brief's table reproduced exactly

A throwaway tree with the inherited configuration (`critiques/pr-29/sphinx-conf.py`'s
extension set unchanged) and the dev-guide directives, over all 78 modules on five pages,
built four ways with `sphinx-build -b html -E -q -w <warnfile>`:

| config | `-W` exit | `-W` problems | `-n` exit | `-n` problems |
|---|---:|---:|---:|---:|
| inherited conf, dev-guide directives | 1 | 27 | **0** | 36 |
| `+ napoleon_use_ivar = True` | 0 | 0 | 0 | 9 |
| `+ :private-members:` instead | 1 | 27 | 0 | 27 |
| both | **0** | **0** | **0** | **0** |

Every cell reproduces the figure the brief carried. The `-n` column's zeros in the
exit-status field are the finding section 4.1 is about.

### 3.2 The 27: `napoleon_use_ivar`, and what it costs

The 27 are deferred entry 276 exactly as recorded: 21 for `ToolSpec`, three for
`VersionedFile`, three for `RunResult`, each a duplicate object description of a dataclass
field. Entry 276 measured two fixes and left the choice open. **`napoleon_use_ivar = True`
is the one taken, and the choice is not a coin flip:** the other is dropping
`:undoc-members:`, and `doc_dev_guide.mdc` section 6 says "On each page use `automodule`
directives with `:members:`, `:undoc-members:`, and `:show-inheritance:` so the full
public surface (including as-yet-undocumented members) is visible." One fix satisfies the
rule and the other breaks it. Round 1 flipped the setting off in the finished tree and got
exactly those 27 back, so the fix is load-bearing rather than incidental.

**It costs five cross-reference targets, measured rather than assumed.** Diffing
`objects.inv` at the two settings over the whole package: 862 objects with the setting
off, 857 with it on. The five that go are `LinkInfo.recno`, `.linktext`, `.linkname`,
`.is_target` and `.target` in `holdings_maintenance/_linkshelf_common.py`. `LinkInfo` is a
plain class whose attributes are assigned in `__init__`, so Napoleon's rendering was their
only target; the three dataclasses lose nothing, because autodoc emits their fields from
the annotations regardless, which is what the duplicate was. Nothing references those five
today. Deferred entry 328 records it for the PR that will try to.

### 3.3 The 9: the narrow `:private-members:`, and what the blunt one would have published

The nine are `:show-inheritance:` rendering `PdsFile`'s base list, in which every one of
the nine mixins fails to resolve, because a name starting with an underscore is not
emitted without `:private-members:`. **The warning says the nine classes that carry most
of `PdsFile`'s behavior are absent from the published reference**, so publishing them is
the fix; `doc_python.mdc` section 3 forbids silencing a nitpick warning for a symbol this
package owns, so `nitpick_ignore` was never available.

`:private-members:` takes an optional list of names. The pages use the narrow form -- one
name on each of the nine modules that defines a mixin, `:private-members: _ShelfMixin`
and its eight siblings -- rather than the bare option. Both reach zero. The difference is
what else gets published, measured from `objects.inv`:

| page option | objects in the inventory | HTML bytes |
|---|---:|---:|
| none | 857 | 1,946,297 |
| narrow, nine names | 992 | 2,372,365 |
| bare `:private-members:` | 1,022 | 2,449,581 |

The narrow form adds the nine mixin classes and their public methods, which are
`PdsFile`'s own inherited surface. The bare form adds **30 further private members** that
are not API and that nobody proposed publishing: `_path_utils._clean_abspath`,
`_clean_glob`, `_clean_join`, `_needs_glob`; `PdsFile._complete`, `._recache`,
`._from_absolute_or_logical_path`, `._update_ranks_and_vols`, `._HOLDINGS_ENV`,
`._LOG_TIMETAG`; `Pds3File._HOLDINGS_ENV` and `Pds4File._HOLDINGS_ENV`;
`DictionaryCache._trim`, `._trim_if_necessary`; three `MemcachedCache` internals; four
`_PropertiesMixin` internals; `_ShelfMixin._get_shelf` and `._close_shelf`;
`_shelves._eval_null_key_record`; `_DerivedPathsMixin._log_path_for`, `._log_timetag`,
`._pinned_log_timetag`; `_LocalFsMixin._non_checksum_abspath`;
`pdsviewable._priority_of_icon_type`; and a module-level `_` in
`pds4file/rules/uranus_occs_earthbased.py`.

## 4. The gate, and the proof that it can fail

### 4.1 `sphinx-build -n` exits 0 while reporting the defect it found

`doc_python.mdc` section 6 prescribes two builds, `sphinx-build -W` and `sphinx-build -n`,
and says "BOTH must succeed with ZERO warnings". **Succeeding is not the same condition as
zero warnings.** Measured on this tree with one broken cross-reference in
`docs/api/pds3file.rst` (`:class:`~pdsfile.pds3file.Pds3Filo``):

| flags | exit | problems reported |
|---|---:|---:|
| `-W` | 0 | 0 |
| `-n` | **0** | **1** |
| `-n -W` | 1 | 1 |

So a gate that runs `-n` and reads its exit status is vacuous, and a gate that runs only
`-W` does not check cross-references at all. The gate runs both `-W` and `-n -W` and reads
both statuses. Deferred entry 326 records this against the rule file, because the next
person to build a gate from section 6 as written will build the same vacuous one.

**What the two builds are not.** The first version of the gate carried a comment saying
the two flags catch different defects and neither implies the other. Round 3 disproved it:
`-n` only adds the unresolved-reference warnings, and in every defect the gate caught, the
nitpicky build caught it too. As a detector the second build subsumes the first. The first
build is what produces `docs/_build/html`, the tree a reader opens, and what separates a
cross-reference failure from any other kind; the rule asks for both, and both statuses are
read so the log says which failed. The comment now says that.

### 4.2 Two builds that share a `BUILDDIR` are one build

With the same broken cross-reference still in the tree:

    cd docs && make clean && make html SPHINXOPTS="-W"          # exit 0
    cd docs && make html SPHINXOPTS="-n -W"                     # exit 0, and:
    updating environment: 0 added, 0 changed, 0 removed
    reading sources...
    no targets are out of date.
    build succeeded.

Nitpick warnings are emitted while a document is resolved and written. A build that
re-reads and re-writes nothing emits none, and `nitpicky` is a configuration value with no
rebuild flag, so changing it between two builds does not invalidate the environment. **The
second build therefore gets its own `BUILDDIR`**, `_build/nitpicky`, and `docs/Makefile`
says why. Round 2 reproduced this independently and rated it "a real trap the code
avoids". Deferred entry 327.

### 4.3 The mutation tests

Each mutation was made in a copy of the tree, the shipped gate was run
(`VENV=... bash scripts/run-all-checks.sh --sphinx -s`), the exit status was read, and the
mutation was reverted and the revert verified with `diff -r` against a pristine copy.
Every row below was re-run against the **final** gate, after the review's fixes.

| # | mutation | `-W` build | `-n -W` build | gate exit |
|---|---|---|---|---:|
| 1 | `:class:`~pdsfile.pds3file.Pds3File`` becomes `Pds3Filo` in `docs/api/pds3file.rst` | passes, exit 0, 0 problem lines | **fails**, exit 2, `py:class reference target not found` | **1** |
| 2 | the `automodule` for `pdsfile.tools.show_opus_products` is deleted from `docs/api/tools.rst` | **fails**, exit 2 | **fails**, exit 2 | **1** |
| 3 | a new module `src/pdsfile/_probe_new_module.py` with no page entry | **fails**, exit 2 | **fails**, exit 2 | **1** |
| 4 | `docs/api/index.rst` gains a `toctree` entry naming a page that does not exist | **fails**, exit 2, `toctree contains reference to nonexisting document` | **fails**, exit 2 | **1** |
| 5 | `MAKEFLAGS=-n`, so `make` prints its recipes and builds nothing at all | **fails**: `exited 0 but reported no API-reference coverage` | same | **1** |
| 6 | `docs/api` moved aside, in **parallel** mode | **fails**, exit 2, 79 problem lines | **fails**, exit 2, 79 problem lines | **1** |
| 7 | a new module, through a bare incremental `make html` with a warm `_build` | **fails**, exit 2, after printing `no targets are out of date` | -- | -- |

Mutation 1 is why both builds are run: the warnings-as-errors build passes a broken
cross-reference. Mutations 2 and 3 are the same check in its two directions, and the
messages name the module:

    WARNING: pdsfile.tools.show_opus_products is documented by no page in this tree, so
    it is absent from the API reference
    API reference: 77 of 78 modules under <source root> documented

Sphinx has no opinion about a module nobody wrote an `automodule` for, so without that
check a page set that had fallen behind the package would build clean. `doc_python.mdc`
section 7 requires that a new public module get an API-reference entry in the same change;
mutation 3 is that rule made mechanical.

**Mutations 5, 6 and 7 are the review's, and each of them passed the first version of the
gate.** 5 is round 2's demonstration that the pass line was an assertion rather than a
measurement -- it printed `0 warnings ... 78 automodule entries in 6 files` over a
`docs/_build` that did not exist. 6 is round 2's demonstration that in parallel mode, the
default, the gate could abort before either build ran. 7 is round 1's: the coverage check
ran from an event Sphinx fires only when a document was re-read, so a developer's
incremental `make html` after adding a module printed `no targets are out of date` and
exited 0. All three are fixed and all three are re-measured above.

### 4.4 What the gate states when it passes

    ✓ Sphinx warnings-as-errors build passed (exit 0, problem lines: 0, API reference:
      78 of 78 modules under <source root> documented)
    ✓ Sphinx nitpicky build passed (exit 0, problem lines: 0, API reference: 78 of 78
      modules under <source root> documented)
    ✓ Sphinx build passed: 0 problem lines under -W and 0 under -n -W, and both builds
      report API reference: 78 of 78 modules under <source root> documented

Every number there is read out of the builds' own output. A build is accepted only if it
exited 0, **wrote its HTML**, and **printed that coverage line** -- so a `make` that
resolves to nothing, or a `conf.py` whose check has been removed, fails rather than
passing quietly -- and the two builds' coverage lines must agree, because they document
one tree. Two of the three numbers cannot vary: under `-W` any problem line fails the
build, so the success path can only print two zeros. Deferred entry 345 says so rather
than letting a reader take them for evidence.

## 5. The gate runs in CI, quoted from the job log

No workflow edit was needed and none was made. The hosted lint job runs
`scripts/run-all-checks.sh --sequential` with no scope selector, which takes the
default-all branch and sets `RUN_SPHINX=true`; `ENABLE_SPHINX` is what had been holding it
back. Sphinx arrives through `pip install -e ".[dev]"`, because the `dev` extra lists
`rms-pdsfile[docs]`; the log shows `Obtaining file:///home/runner/work/rms-pdsfile/rms-pdsfile`
and `Collecting sphinx>=7 (from rms-pdsfile==0.1.dev1)`, so it resolves from the local
tree rather than from PyPI.

From `gh api repos/SETI/rms-pdsfile/actions/jobs/93216654110/logs`, job **Lint and
holdings-free tests (3.13)** of run `31302178436` -- the run of the head commit, all six
jobs green -- verbatim, timestamps trimmed to the second:

    07:54:13 >>> Sphinx Build
    07:54:13 ℹ Emptying docs/_build...
    07:54:13 ℹ Building documentation (warnings as errors)...
    07:54:13 Running Sphinx v9.1.0
    07:54:14 building [html]: targets for 7 source files that are out of date
    07:54:25 API reference: 78 of 78 modules under
             /home/runner/work/rms-pdsfile/rms-pdsfile/src documented
    07:54:26 ✓ Sphinx warnings-as-errors build passed (exit 0, problem lines: 0,
             API reference: 78 of 78 modules under .../src documented)
    07:54:26 ℹ Building documentation (nitpicky, warnings as errors)...
    07:54:26 Running Sphinx v9.1.0
    07:54:26 building [html]: targets for 7 source files that are out of date
    07:54:37 API reference: 78 of 78 modules under .../src documented
    07:54:38 ✓ Sphinx nitpicky build passed (exit 0, problem lines: 0, API reference:
             78 of 78 modules under .../src documented)
    07:54:38 ✓ Sphinx build passed: 0 problem lines under -W and 0 under -n -W, and both
             builds report API reference: 78 of 78 modules under .../src documented
    07:54:38 ✓ SUCCESS - All checks completed successfully
    07:54:38 ℹ Total time: 1m 0s

Round 2 was asked to hunt the vacuity signature in the equivalent log of an earlier run
and reported it absent; it is absent here too. `grep -c "no targets are out of date"` is
**0**, and both builds report `7 source files that are out of date`. The 3.10 leg runs the
same gate on **Sphinx 8.1.3** and `myst-parser 4.0.1`; both legs pass. The pytest gate in
the same job reports **318 passed, 817 skipped**, which is the recorded no-holdings
figure. The two documentation builds cost about 25 s of the job's 60 s.

**Which invocations reach the gate.** `--sequential` and a bare invocation both take the
default-all branch, so both run it. `-c` does not: it selects the code scope, and Sphinx is
in the documentation scope, `-d`. Verified by running `-c -s` with every code gate
disabled: the run prints no Sphinx section at all. The two invocations in the repository --
the CI job (`--sequential`) and `CONTRIBUTING.md` (bare) -- both take the default-all
branch, so the enabled set and the invocations correspond, which is what `environment.mdc`
section 2 requires. The third corner of that rule, `.cursor/skills/run-all-checks/SKILL.md`,
did **not** correspond and is fixed here (section 10).

## 6. The two environment hazards this build has

### 6.1 intersphinx needs the network, and a failure is a build failure

Measured by pointing `intersphinx_mapping` at a host that does not resolve:

| flags | exit | problems |
|---|---:|---:|
| `-W` | 1 | 1 (`failed to reach any of the inventories`) |
| `-n -W` | 1 | 37 (that one, plus the 36 references the inventory was resolving) |

The 36 are all standard-library names: `collections.abc.Callable` eleven times,
`argparse.Namespace` eight, `argparse.ArgumentParser` five, `re.Pattern` four,
`tarfile.ReadError` and `pickle.UnpicklingError` twice each, and one each of
`smtplib.SMTPException`, `pickle.PickleError`, `pathlib.Path` and `datetime.datetime`.
They come from `Parameters:`, `Returns:` and `Raises:` entries -- round 1 established the
section of origin for 13 of them and corrected `conf.py`'s comment, which had named only
`Parameters:`. **It was 34 until the constructor docstrings were published**, and round 4
caught the comment still saying 34 after the same commit had made it 36: measured at 36
with the constructors published and 34 with that one line deleted and nothing else
changed.

So a transient outage at `docs.python.org` turns the hosted lint job red, and the message
names the inventory rather than anything about this tree. **This is left as a known flake
surface rather than engineered around**, because the alternative -- a second inventory
location in the mapping tuple, pointing at a copy of `objects.inv` committed here --
commits a binary that goes stale, and the flake has not been observed. `intersphinx_timeout
= 30` was added: without it, a host that accepts the connection and never answers stalls
the build instead of failing it. Deferred entry 329.

### 6.2 The documentation builder does not have `tabulate`, and the build now survives that

`src/pdsfile/tools/show_opus_products.py:32` is `import tabulate`, and `tabulate` is in the
`dev` extra only. ReadTheDocs installs the project with the `docs` extra, so it is absent
there, while every local and CI build has it through `dev` -- a difference that would have
made the gate green and the published site wrong. Measured by building with a `tabulate`
that raises `ImportError`:

| configuration | exit | warnings |
|---|---:|---|
| no mock | 1 | `autodoc: failed to import 'show_opus_products' from module 'pdsfile.tools'`, and the coverage check reporting the module absent |
| `autodoc_mock_imports = ['tabulate']` | 0 | none |

`doc_dev_guide.mdc` section 7 prescribes exactly this ("mock heavy optional imports in
`conf.py` rather than dropping modules from the reference"). Two things are worth saying
plainly: the coverage check caught the import failure independently, because a module that
fails to import is never recorded in the Python domain; and **no gate in this repository
would have caught the underlying import**. Round 3 proved that by adding `import pytest`
to `pdsarchives.py` and watching the clean-install gate pass at exit 0:
`scripts/check_runtime_imports.py` walks the frozen public set -- seven top modules plus
the rule modules -- and 35 of the 78 documented modules are outside it. Deferred entries
330 and 334.

## 7. The README marker, and where the include goes

The marker is `<!-- start-after-point -->`, placed immediately after the `# rms-pdsfile`
H1, and it is the only change to `README.md`. `index.rst` includes the README from that
point through `myst_parser`.

**The placement was measured, not reasoned about.** Both candidate positions build clean --
the predicted duplicate-title warning does not fire on this README under the full extension
set -- so the decision is what the page renders:

| marker position | build | what the docs landing page shows |
|---|---|---|
| after the H1 (**taken**) | `-n -W` exit 0, 0 warnings | one `<h1>rms-pdsfile</h1>` from the page title |
| before the H1 | `-n -W` exit 0, 0 warnings | `<h1>rms-pdsfile</h1>` and then `<h2>rms-pdsfile</h2>`, the title twice |

The badge block is above the marker either way, so the 22 badge lines stay on GitHub and
out of the documentation. Round 3 measured the third position -- after `Supported
versions: Python >= 3.10` -- and found it removes the front page's only substantive line,
silently, because `:start-after:` swallowing content is not a warning. Deferred entry 338.

**The include cost one structural change to `index.rst`.** The README ends with a second
H1 (`# PDS Ring-Moon Systems Node, SETI Institute`), and an included heading opens a
section that swallows everything after it in the including document: with the `toctree`
written after the include, the rendered page nested the whole API reference inside that
section (`<section id="pds-ring-moon-systems-node-seti-institute">` containing
`<div class="toctree-wrapper">`). The `toctree` is therefore written before the include,
which puts it at the document's top level whatever the README grows into. Neither
arrangement warns. What remains is that the landing page ends with that heading and
nothing under it, which is a property of the README and PR-34's to fix.

## 8. `conf.py`: what it sets, and what differs from the inherited configuration

`critiques/pr-29/sphinx-conf.py` is the configuration PR-29 built its five-module probe
with. What differs, and why:

| setting | inherited | here | why |
|---|---|---|---|
| source root | `os.environ['PDSFILE_SRC']` | `Path(__file__).parent.parent / 'src'` | the tree is in the repository now; `doc_python.mdc` section 3 wants autodoc to import without an install step |
| `project` | `pdsfile` | `rms-pdsfile` | the published site is the distribution's; the importable package is named throughout the reference |
| `version` / `release` | absent | `importlib.metadata.version('rms-pdsfile')` | section 3 requires the version come from installed metadata rather than a literal |
| `myst_parser` | absent | present | section 3 requires it, and `index.rst` includes the Markdown README |
| `source_suffix` | absent | `.rst` and `.md` | section 3 |
| `html_theme` | absent | `sphinx_rtd_theme` | the theme the `docs` extra installs and the one ReadTheDocs serves |
| `html_show_copyright` | absent | `False` | the repository names no copyright holder -- `LICENSE` is the stock Apache-2.0 text with no holder line and there is no `NOTICE` -- and the theme was rendering "(c) Copyright ." on every page |
| `napoleon_use_ivar` | absent | `True` | section 3.2 |
| the `automodule` options | `:members: :undoc-members: :show-inheritance:` | those three plus `:special-members: __init__` | nine `__init__` docstrings, six with a `Parameters:` block, were written and never published; all nine now are, one copy each |
| `autodoc_mock_imports` | absent | `['tabulate']` | section 6.2 |
| `intersphinx_timeout` | absent | `30` | section 6.1 |
| `exclude_patterns` | absent | `['_build']` | the build tree is inside the source directory |
| `setup(app)` | absent | registers the API-reference coverage check on `build-finished` | `doc_python.mdc` section 7 |

**A diagram extension is deliberately absent.** `doc_python.mdc` section 3 asks for one
"when the guides use diagrams"; no guide exists yet and no page in this tree draws a
diagram. Enabling `sphinxcontrib.mermaid` anyway put a `<script type="module">` pointing at
`cdn.jsdelivr.net` into **70 of the 77** built pages, because the extension skips only the
pages whose doctree it can inspect, and every `_modules/*` viewcode page and every
generated index is built with no doctree. After removing it: **0 of 77**. Round 1 also
found that `mermaid_output_format = 'raw'` restated the extension's own default. PR-32 or
PR-33 turns it on with the first diagram.

`nitpick_ignore` is carried over and stays **empty**. Nothing in this tree needs an entry,
and section 3 permits one only for a symbol with no resolvable target, never for a symbol
this package owns.

**The constructor docstrings are published by a page option, not by
`autoclass_content`.** `autoclass_content = 'both'` publishes them and also appends the
base class's `__init__` docstring to every subclass entry that inherits it -- 26 copies of
`Pds3File.__init__`'s on the PDS3 page and 7 of `Pds4File.__init__`'s on the PDS4 page,
because `autodoc_inherit_docstrings` defaults to true and setting it false does not change
that. `:special-members: __init__` on the `automodule` entries documents `__init__` only
for a class that defines one, because `:inherited-members:` is not set. Measured: nine
constructor docstrings published and none missing, twelve `__init__` entries in the
inventory (the nine plus the generated constructors of `ToolSpec`, `RunResult` and
`VersionedFile`), and one copy of each. The option is on all 78 entries rather than on the
seven modules that need it, so every entry carries the same four options.

**The coverage check runs from `build-finished`, not `env-check-consistency`.** Sphinx
guards the consistency event with `if updated_docnames:`; adding a `.py` file changes no
Sphinx source, so an incremental build re-read nothing and the check did not run at all --
the one case it exists for. Measured before and after in section 4.3, mutation 7. Deferred
entry 341.

## 9. Standing gates

### 9.1 Sphinx, base and head

**Base cannot be clean and is not reported as zero.** `docs/` does not exist at `8f8d825`
(`git ls-tree -r 8f8d825 --name-only | grep -c '^docs/'` is 0), so there is nothing to
build and the gate could not have been enabled before this PR. The honest base measurement
is the throwaway probe's, which is section 3.1's first row: 27 problems under `-W`, 36
under `-n`.

At head, over 7 documents, 6 files under `docs/api`, 78 `automodule` entries, 78 modules
and 77 built HTML pages:

| build | exit | problem lines |
|---|---:|---:|
| `sphinx-build -b html -E -W docs <out>` | 0 | 0 |
| `sphinx-build -b html -E -n -W docs <out>` | 0 | 0 |
| the shipped gate, both builds | 0 | 0 |

The published inventory holds **1,005 objects**, and all nine `__init__` docstrings appear
on the pages (verified by matching each one's first line against the built HTML: 9
published, 0 missing).

### 9.2 Test id sets, full data, both modes

Command lines are `scripts/automated_tests/pdsfile_main_test.sh`'s, plus `--junitxml`, run
from each tree in turn, one at a time.

| mode | scope | base | head | ids only in base | ids only in head | outcome changed |
|---|---|---|---|---|---|---|
| `ns` | all seven directories | 1101 passed, 34 skipped (1135 ids) | 1101 passed, 34 skipped (1135 ids) | none | none | **none** |
| `s` | `tests/pds3file/ tests/rules/pds3/` | 555 passed, 3 skipped (558 ids) | 555 passed, 3 skipped (558 ids) | none | none | **none** |

The per-test id sets are diffed, not the counts: the junit files are parsed and compared
id by id with the outcome attached, so a test that changed from passed to skipped would
show even though the totals would not.

**The first `ns` run of the base tree reported two failures, and they were machine load,
not defects.** Both were `subprocess.TimeoutExpired ... timed out after 60 seconds` from
`tests/api/test_mixin_import_isolation.py`, whose nine parametrized cases each spawn an
interpreter to import one mixin module; that run took 38m 43s while this machine carried a
load average between 40 and 80 from unrelated work. The same nine cases pass in **1.64 s**
when `tests/api/` is run on its own in the base tree (26 passed), pass on all four
self-hosted CI legs of this PR's run, and passed when the whole base `ns` pass was re-run
on a quiet machine -- 4m 49s, **1101 passed, 34 skipped**, which is the row above.
Deferred entry 342 records the load sensitivity.

**The self-hosted CI legs are the independent full-data measurement at head**, and they
reproduce the recorded baseline exactly: `1101 passed, 34 skipped` for the `ns` pass and
`555 passed, 3 skipped` for the `s` pass, on each of Python 3.10, 3.11, 3.12 and 3.13.

### 9.3 The code checks with no holdings, and the whole enabled set

    env -u PDS3_HOLDINGS_DIR -u PDS4_HOLDINGS_DIR -u PDSFILE_TEST_HOLDINGS \
        VENV=/seti/all_repos/rms-pdsfile/venv bash scripts/run-all-checks.sh -c -s

Exit 0: ruff, the indentation pass, pytest (**318 passed, 817 skipped**), pyroma, the
API-freeze check and the clean-install gate. The same figure the hosted lint job reports.

    env -u PDS3_HOLDINGS_DIR -u PDS4_HOLDINGS_DIR -u PDSFILE_TEST_HOLDINGS \
        VENV=/seti/all_repos/rms-pdsfile/venv bash scripts/run-all-checks.sh -s

Exit 0, and this is the run that matters for the new gate, because `-c` does not select
it: the same six code gates plus **both Sphinx builds**, each reporting `problem lines: 0`
and `API reference: 78 of 78 modules ... documented`. Run in the default parallel mode as
well as sequentially, since the two modes reach the gate by different paths.

### 9.4 The API freeze

**26 passed**, inside the `ns` runs above and again on their own. The four frozen files are
byte-identical to `8f8d825`, checked with `git diff --quiet 8f8d825 -- <file>` on each of
`tests/api/api_manifest.json`, `tests/api/manifest_allowlist.json`,
`scripts/dump_public_api.py` and `tests/api/test_api_freeze.py`. This PR adds no Python to
`src/` and removes none, so the public surface cannot move; the check is run anyway.

### 9.5 ruff

    ruff check src/pdsfile tests scripts docs                     # All checks passed, exit 0
    ruff check .                                                  # All checks passed, exit 0
    ruff check --preview --select E111,E112,E113 .                # All checks passed, exit 0
    ruff check . --config 'lint.per-file-ignores = {}'            # Found 2249 errors, exit 1

`ruff format` was not run, in any form. `docs/` is a new lint target: `docs/conf.py` is the
one Python file the documentation tree carries, and it passes the configured gate, the
indentation pass **and** the no-ignores run with no new `per-file-ignores` entry.
`scripts/gen_ruff_ratchet.py`'s `TARGETS` is updated in the same change, because its own
comment requires the two to stay in step.

### 9.6 The ratchet

| | base | head |
|---|---:|---:|
| `per-file-ignores` entries | 66 | 66 |
| code slots across those entries | 180 | 180 |
| findings with `per-file-ignores = {}` | 2,249 | 2,249 |
| `[project.scripts]` entries | 11 | 11 |

Nothing moved, and `pyproject.toml` is byte-identical to `8f8d825`
(`git diff --quiet 8f8d825 -- pyproject.toml`).

### 9.7 The docstring and record checkers

`critiques/pr-29/check_docstrings.py` over the 78 modules under `src/pdsfile`: **0 findings
over 78 files**, unchanged. Over `docs/conf.py`, which is a new Python file: **0 findings
over 1 file**. The 78 excludes `src/pdsfile/_version.py`, which is not in a checkout but
which a local full run writes, because the clean-install gate builds the project and
`setuptools_scm` puts it there; with it present the same command reports 79 files and one
M1 finding, and the Sphinx build still reports 78 of 78 modules documented. Deferred entry
346. The checker should cover it -- its rules are the mechanically checkable half
of `doc_python.mdc` section 4, and a `conf.py` with a module docstring and three functions
is exactly what they are for -- so it was run. Nothing automates that: round 3 found the
checker is wired into no gate at all, which is deferred entry 337.

`critiques/pr-28/check_record_numbers.py`: **15 stale at base and 15 at head**.
`critiques/pr-29/check_citations.py`: **6 stale at base and 6 at head**. Both outputs are
byte-identical between the two trees (`diff` reports no difference), and both were re-run
after this record, the round records, the deferred entries and the plan amendment were
written. The 15 are PR-28's own, invalidated by PR-28a's extraction; the 6 are
deferred-observation citations into files outside the citation checker's scope list. This
PR neither caused nor repaired either.

### 9.8 The build output is not committed

`git status --porcelain -uall` after a full gate run lists no path under `docs/_build`.
`git check-ignore -v` attributes both `docs/_build/html/index.html` and
`docs/_build/nitpicky/html/index.html` to `.gitignore:75`.

## 10. Review

Four rounds, each a fresh no-context subagent given the tree, the rule files and a scope,
and nothing about how the change was arrived at. The tree was frozen for rounds 1-3:
`git status --porcelain` was empty when they started and empty when they finished, and
every reviewer was told to copy the tree before changing anything. Round 4 read the
corrections the first three produced.

| round | scope | defects | observations |
|---|---|---:|---:|
| 1 | `conf.py`, the API pages, the `Makefile`, the README marker | 12 | 9 |
| 2 | the gate, the CI wiring, and whether the two correspond | 5 | 7 |
| 3 | one job: prove the gate is vacuous | 12 | -- |
| 4 | a second read of what rounds 1-3 changed | 10 | 9 |

Records at `critiques/pr-31/round-N.md`.

**The three findings that changed what this PR is.** Round 2 ran the gate under
`MAKEFLAGS=-n`, where `make` builds nothing, and got a green `✓ Sphinx build passed: 0
warnings ... over 78 automodule entries in 6 files` over a `docs/_build` that did not
exist -- the pass line was an assertion, not a measurement, and one of its two numbers was
wrong besides. Round 1 found the coverage check did not run at all on an incremental
build, which is the one case it exists for. Round 3 found the comment defending two builds
claimed something false about what each catches. This project has shipped four gates whose
output nobody read; without those three findings this would have been the fifth in a
different way, green over a build that never happened.

**Round 3's list of what the gate does not catch is the most valuable output of this PR**,
because PR-32, PR-33 and PR-34 all lean on this gate. Twelve defects pass it, of which one
was fixed here (the unpublished constructor docstrings), one was a false claim in the
gate's own comment, and the rest are recorded as deferred entries 333-341: docstring-against-signature drift in
every shape; cross-references inside the 43 docstrings that are never published; a
dev-only import in any of the 35 modules no dependency gate imports; `__all__` narrowing a
module to one member; a missing `:members:` taking a module from 46 published objects to 0;
a decorator without `functools.wraps`; `.. note:` with one colon deleting its own block;
a duplicate `automodule` with `:no-index:`; a module exempted by name in `conf.py`; and a
moved README marker emptying the front page.

**Round 4 says how well the first three rounds' corrections held: nine of its ten defects
were in the corrections themselves.** The intersphinx comment's number was made wrong by a
change in the same commit that rewrote it -- 34 became 36. The regex that reads the
coverage line rejected any project path containing a space, turning a clean build into a
gate failure. `autoclass_content = 'both'`, added to publish nine constructor docstrings,
also appended a base class's constructor docstring to 33 subclass entries that never wrote
one; the fix for that is now a page option, `:special-members: __init__`, which documents
`__init__` only for a class that defines one. The rewritten `docs/api/index.rst`
contradicted the `conf.py` docstring rewritten beside it. A comment named `pipefail` where
the option was `errexit`; one claimed an extension set the pages do not rely on; one
over-corrected a page intro into saying the maintenance tools build a holdings tree; the
skill file's new snippet was not runnable as a block; and a docstring said a failed build
is not asked about its coverage, which is false for the way `-W` fails in Sphinx 9. All are
fixed and re-measured, and round 4's record lists the seven corrections it checked and
found sound. Nine in ten is the same ratio six docstring PRs recorded, and it is why a
fourth round exists.

**Ask every reviewer what it could not verify.** All four did, and the recurring answer is
ReadTheDocs: nobody ran a build there, `.readthedocs.yaml` sets no `fail_on_warning`, and
several findings have teeth only in CI. That is stated rather than papered over. Round 4
also could not verify what `src/pdsfile/_version.py` holds in this tree, since it is
gitignored -- and a local full run has since written it, which is deferred entry 346 and
which turns the coverage check's exemption for it from theoretical into load-bearing: with
the file present the build still reports **78 of 78**.

### 10.1 The grep after each correction

Every correction was grepped for across the whole repository before this record was
written, because a fix that reaches the code and not the record is how three of
CodeRabbit's PR-30b findings survived. Four reached more than one place:

* **"6 files under docs/api"** -- the script's pass line and round 3's quoted baseline.
* **"the two flags catch different defects"** -- `run-all-checks.sh`, this record's draft
  and the PR body.
* **the intersphinx count** -- `conf.py`'s comment, deferred entry 329 and section 6.1 of
  this record all said 34 and all now say 36.
* **the docs-gate command** -- `run-all-checks.sh`'s header, `docs/Makefile` and three
  places in `.cursor/skills/run-all-checks/SKILL.md`.

The rest -- the four page intros, the remaining `conf.py` comments, the two shell comments
-- each lived in one file. One correction had to be made twice for a reason worth
recording: the sentence in deferred entry 330 that cites `show_opus_products` was rewritten
to drop its line number because `check_citations.py` reads every entry after PR-29's, and
then entry 343, which explains that, tripped the same check by quoting the citation. It
now describes the pattern instead of showing it.

## 11. What this closes, and what remains of Phase 7

Closed: deferred **276** (`napoleon_use_ivar`, with the numbers, entry 328 carrying its
cost) and deferred **169** (no trailing-underscore reference fires at head; 64 occurrences
are inside double backticks, 29 of the 42 bare ones are in `::` literal blocks and the
other 13 are followed by a character that cannot close a reference). Deferred **168** is
amended with its measured scope and re-owned to **PR-31a**.

Phase 7 has left: **PR-31a** (the cross-reference sweep, 3,651 literals of which 2,384
name something the package defines), **PR-32** (user guide), **PR-33** (developer guide)
and **PR-34** (README rewrite, which inherits the marker and the empty trailing section
of section 7).

## 12. What the owner might decide differently

* **The diagram extension.** It is off, with the CDN measurement as the reason. Turning it
  on is one line whenever a guide draws a diagram. `sphinxcontrib-mermaid` stays in the
  `docs` extra, so it is installed and unused until then (deferred 344).
* **`html_show_copyright = False`.** The alternative is stating a holder and a year, which
  the repository does not state anywhere today.
* **The intersphinx network dependency** (6.1) is kept, with the local-inventory fallback
  named but not taken.
* **`check_docstrings.py` is not a gate** (deferred 337), and it is the only thing that
  catches the drift round 3's first finding demonstrates. Wiring it in is small and is a
  policy decision about where a `critiques/` tool belongs.
* **`scripts/read-docs.sh`** builds with half the gate (deferred 331); it was left alone.
* **The lint job's name**, "Lint and holdings-free tests", now covers two documentation
  builds as well. It is a branch-protection check name, so renaming it is the owner's.
* **`-c -s`**, the habitual local command in six validation records, does not run this
  gate. That is correct scoping, but the habit now skips something CI runs.
