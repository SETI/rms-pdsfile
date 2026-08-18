CI and Release Workflow
=======================

One script is the source of truth for what "all checks" means, and every job in the
test workflows either runs it directly or is a driver whose differences from it are
stated below (the publish workflows build and upload -- the PyPI one also validates
the built distribution with ``twine check`` before publishing -- and run none of
the script's gates). When a gate is added,
enabled or retired, ``scripts/run-all-checks.sh`` is where that happens, and CI
follows it by construction.

``run-all-checks.sh``
---------------------

``scripts/run-all-checks.sh`` runs every enabled check, in parallel by default
(``-s`` for sequential, ``-w N`` for pytest workers, individual ``--<check>`` flags
to scope a run, ``--coverage`` and ``--coverage-subprocess`` to measure coverage).
Each check runs only if selected *and* enabled; the ``ENABLE_*``
defaults in the script are the canonical record of which gates this repository runs:

=====================  ========  ==========================================================
check                  enabled   what it measures
=====================  ========  ==========================================================
``ruff check``         yes       the configured lint rules, plus a second preview-gated
                                 pass for indentation only (``E111``, ``E112``, ``E113``)
``ruff format``        never     owner decision: the reformat conflicts with the house
                                 continuation-line style
``mypy``               never     no inline typing, by ground rule; the public API is
                                 stubbed instead
pytest                 yes       one ``--mode ns`` pass over ``tests/``; a full data run
                                 when the holdings variables are set, the holdings-free
                                 subset otherwise (see :doc:`dev_guide_testing`)
pyroma                 yes       packaging metadata quality
API freeze             yes       the public surface against ``tests/api/api_manifest.json``
clean install          yes       a no-extras install into a throwaway venv, then an import
                                 of the whole public module surface -- the one check that
                                 catches a runtime dependency leak
bandit, vulture        never     permanently off, by decision
Sphinx                 yes       two documentation builds, read rather than tailed (below)
PyMarkdown             yes       Markdown lint over the files its selection reaches
=====================  ========  ==========================================================

The Sphinx gate is two builds from one ``docs/conf.py``: ``make html`` with ``-W``
(warnings as errors), then again with ``-n -W`` (nitpicky: every unresolved
cross-reference is a warning, and ``-W`` is what makes that fatal) into a build
directory of its own. Both details are load-bearing: ``-n`` without ``-W`` exits 0
while reporting every broken reference, and two builds sharing a build directory
share its doctree cache, so the second re-reads nothing and re-reports nothing. A
build is accepted only if it exits 0, writes its HTML, and prints the module-coverage
line ``conf.py`` emits -- exit status alone would accept a build that resolved to
nothing.

Coverage
--------

Coverage is off for a day-to-day run and on when asked for. ``--coverage`` runs the
pytest gate under ``coverage run``, prints a report and writes ``htmlcov/``; what is
measured comes from ``[tool.coverage.*]`` in ``pyproject.toml``, so it produces the
branch coverage the data gate produces. Neither flag is a check, so neither has an
``ENABLE_*`` entry above: they change how the pytest gate runs, the way ``-p``,
``-s`` and ``-w`` do, and asking for coverage in a run that does not schedule that
gate exits 1 rather than reporting 0%.

The eleven console-script tools and ``show_opus_products`` are driven as
subprocesses by their tests, and ``coverage run`` does not follow a child, so
``--coverage`` reports them at whatever their imports reach.
``--coverage-subprocess`` measures them too, by setting ``COVERAGE_PROCESS_START``
in the tool subprocess environment, writing one data file per process and combining
them afterwards. Two things act on that variable: coverage's own
``a1_coverage.pth``, which site processing runs first on coverage 7.10 and later,
and the ``coverage.process_startup()`` hook in
``tests/holdings_maintenance/_subprocess_guard/sitecustomize.py``, which is what
works below that version and what kills a child that cannot measure instead of
leaving the report quietly short. Over the whole suite the mode takes the
maintenance-tool tree from 34% to 78% and the package from 56% to 81% -- of which
4 points are branch analysis leaving the denominator and 21 are the subprocesses
arriving, separated by measuring a line-only parent-only control at 60%.

It is opt-in because it constrains the whole run. The cost of measuring a child is
the tracer running inside it -- 10.60s of tool tests become 79.68s under the C
tracer -- and the way out is ``COVERAGE_CORE=sysmon``, which cannot measure branches
below Python 3.14 and silently falls back if asked to. So the mode turns branch
analysis off for the whole run, which brings the same tests to 12.49s, and
``coverage combine`` refuses to mix branch data with statement data, so this is a
whole-run choice rather than a per-process one. The run prints which kind of
coverage it produced, read back out of the data file rather than out of the flags
that were meant to produce it.

Nothing in CI sets ``COVERAGE_PROCESS_START``: the data gate below still measures
the pytest process only, in branch mode, and its numbers are the ones uploaded to
codecov.

The self-hosted data jobs
-------------------------

``.github/workflows/run-tests.yml`` runs on pull requests targeting ``rewrite``, on
pushes to ``main``, nightly on a schedule, and on manual dispatch. Two jobs:

* **Lint and holdings-free tests** (``ubuntu-latest``, Python 3.11 and 3.13): a
  stock hosted runner with no holdings tree. It builds a venv, installs
  ``-e ".[dev]"`` and runs ``scripts/run-all-checks.sh --sequential`` with no
  holdings variables, so its pytest gate collects everything, runs the
  holdings-free subset and skips the rest. Because it runs the script itself, its
  gate set cannot drift from the local one.
* **Test pdsfile** (self-hosted Linux, Python 3.11, 3.12 and 3.13): the full-data
  matrix, the only place the data suite can run in CI. It runs
  ``scripts/automated_tests/pdsfile_main_test.sh``, its own driver: the
  clean-install gate first, then one ``--mode ns`` pass under coverage over
  ``tests/api core holdings_maintenance pds3file rules/pds3 pds4file rules/pds4``
  (every directory except ``tests/docs/``, whose gates run only in the lint job's
  ``run-all-checks.sh`` pass), then a second, PDS3-only pass
  (``tests/pds3file tests/rules/pds3``) with ``--mode s``, then the coverage
  report, uploaded to codecov from the 3.13 runner. The holdings roots come from
  the runner's environment, not from the repository.

Concurrent runs on one pull request cancel the older one; nightly and ``main`` runs
are left to finish. A newly pushed PR run can take up to about half an hour to
appear when the runners are busy -- latency, not failure.

``run-tests-and-opus.yml`` runs on pull requests targeting ``main`` and on dispatch:
the whole workflow above, then a second job that checks out the OPUS repository on a
self-hosted runner, replaces the ``rms-pdsfile`` in OPUS's environment with an
editable install of this checkout, and runs OPUS's own test suite and coverage
check against it. That is the consumer-facing gate: OPUS is the API consumer that
must not break.

Versioning and release
----------------------

The version is not written anywhere in the source. ``setuptools_scm`` derives it
from the git tag at build time and writes ``src/pdsfile/_version.py`` (gitignored)
into the build; an installed package reports it via ``pdsfile.__version__``, and a
source checkout with no build metadata reports ``'Version unspecified'``. Releasing
is therefore tagging:

1. Feature branches (and integration branches such as ``rewrite``) merge to
   ``main`` through pull requests with CI green.
2. A release is a git tag on ``main``; the tag is what fixes the version string.
3. ``publish_to_pypi.yml`` builds the distribution, validates it with
   ``twine check``, and uploads it when a GitHub release is published from that
   tag; ``publish_to_test_pypi.yml`` builds and uploads to Test PyPI on manual
   dispatch. ReadTheDocs builds the documentation from
   ``docs/conf.py`` per ``.readthedocs.yaml``, installing the package with the
   ``docs`` extra.

The contribution workflow around all of this -- conventional commit format,
branching, review expectations -- is in ``CONTRIBUTING.md`` and the rule files under
``.cursor/rules/``, which are the project's coding-convention reference. Two
conventions deserve calling out because the gates enforce them mechanically: the
ruff per-file-ignores table in ``pyproject.toml`` is a ratchet that may only shrink,
and the API-freeze files (the manifest, its allowlist, the dumper and the checker)
are never edited to make a difference disappear -- a deliberate surface change
regenerates the manifest and shows the diff (:doc:`dev_guide_extending_rules`).
