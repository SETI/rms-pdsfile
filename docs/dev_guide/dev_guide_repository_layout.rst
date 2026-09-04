Repository Layout
=================

The importable package is everything under ``src/pdsfile/``; it is what
``pip install rms-pdsfile`` ships, and its public surface is frozen (see
:doc:`dev_guide_subsystems`). Everything else in the repository supports that package:
tests, documentation, CI scripts, development rules, and the planning and review records
of the modernization effort that produced this layout.

::

    rms-pdsfile/
    ├── src/pdsfile/                 # THE PACKAGE: everything importable, all shipped code
    │   ├── __init__.py              # binds __version__, PdsFile, and the pds3file/pds4file names
    │   ├── pdsfile.py               # the PdsFile class statement, class attributes, constructors
    │   ├── _associations.py         # mixin: files that go with this one in other categories
    │   ├── _derived_paths.py        # mixin: checksum, archive and log path arithmetic
    │   ├── _index_rows.py           # mixin: PdsFile objects standing for index-table rows
    │   ├── _local_fs.py             # mixin: the four filesystem questions, shelf-backed under SHELVES_ONLY
    │   ├── _opus.py                 # mixin: OPUS ID resolution and the opus_products() dictionary
    │   ├── _path_utils.py           # module functions: path arithmetic shared by all of the above
    │   ├── _preload.py              # mixin: preload() and the cache bookkeeping it maintains
    │   ├── _properties.py           # mixin: the 64 derived properties, most of them lazy
    │   ├── _shelves.py              # mixin: opening, caching and reading shelf files
    │   ├── _sorting.py              # mixin: sort rules and bulk path/object conversions
    │   ├── pdscache.py              # DictionaryCache and MemcachedCache
    │   ├── pdsviewable.py           # PdsViewable/PdsViewSet, and the icon registry
    │   ├── preload_and_cache.py     # public re-export face of the preload subsystem
    │   ├── pds3file/                # Pds3File and its per-volume-set rule modules
    │   │   ├── __init__.py          # the Pds3File class; imports rules/ at the tail
    │   │   └── rules/               # 25 rule modules + __init__.py of shared default tables
    │   ├── pds4file/                # Pds4File and its per-bundle-set rule modules
    │   │   ├── __init__.py          # the Pds4File class; imports rules/ at the tail
    │   │   └── rules/               # 9 rule modules + __init__.py of shared default tables
    │   ├── holdings_maintenance/    # the maintenance tools (installed as console scripts)
    │   │   ├── _common.py           # ToolSpec, the shared parser and the shared driver
    │   │   ├── _archives_common.py  # shared halves of each tool family, one module per family
    │   │   ├── _shelf_common.py     #   (checksums and info shelves share _shelf_common)
    │   │   ├── _indexshelf_common.py
    │   │   ├── _linkshelf_common.py
    │   │   ├── pds3/                # the PDS3 tools, incl. crlf, re_validate,
    │   │   │                        #   linkshelf_repairs, and the document-only
    │   │   │                        #   sync shell scripts
    │   │   └── pds4/                # the PDS4 halves of the five tool pairs
    │   └── tools/                   # show_opus_products, a python -m diagnostic tool
    ├── tests/                       # the pytest tree (not shipped)
    │   ├── conftest.py              # session setup: holdings resolution, --mode, --update, preload
    │   ├── support/                 # holdings resolver and golden-test helpers
    │   ├── api/                     # public-API freeze, mixin collision and isolation tests
    │   ├── core/                    # holdings-free tests of cache, path and shelf internals
    │   ├── docs/                    # documentation gates: docstring checker, silent-markup check
    │   ├── pds3file/  pds4file/     # blackbox/whitebox tests against real holdings
    │   ├── rules/pds3/  rules/pds4/ # the standardized per-dataset rule tests
    │   ├── holdings_maintenance/    # maintenance-tool tests (tmp_path copies of declared subsets)
    │   └── golden/full/             # golden files: pds3/, pds4/, holdings_maintenance/
    ├── docs/                        # this Sphinx tree: conf.py, index.rst,
    │   │                            #   user_guide/, dev_guide/, api/
    │   └── Makefile                 # make html; the gate passes SPHINXOPTS and BUILDDIR
    ├── scripts/
    │   ├── run-all-checks.sh        # THE gate runner: single source of truth for enabled checks
    │   ├── clean_install_check.sh   # no-extras install + full public import (dependency-leak gate)
    │   ├── check_runtime_imports.py # walks the frozen module list for the gate above
    │   ├── dump_public_api.py       # regenerates the API manifest (never edited by hand)
    │   ├── gen_ruff_ratchet.py      # seeded the ruff per-file-ignores ratchet
    │   ├── read-docs.sh             # convenience wrapper to open the built documentation
    │   └── automated_tests/         # pdsfile_main_test.sh, the self-hosted CI driver
    ├── .github/workflows/           # run-tests.yml, run-tests-and-opus.yml, publish_to_*.yml
    ├── .cursor/                     # rules/ (coding standards + pdsfile_overrides.mdc) and skills/
    ├── plans/                       # the modernization plan and per-PR sub-plans
    ├── critiques/                   # review rounds, validation records, observation registers
    ├── pyproject.toml               # ALL tool and packaging configuration, single source
    ├── requirements.txt             # exactly "-e ." (extras live in pyproject.toml)
    ├── run_tests_coverage.sh        # names test paths that no longer exist; do not use
    │                                #   (scripts/automated_tests/ is the working driver)
    ├── .readthedocs.yaml            # ReadTheDocs build: pip install .[docs], docs/conf.py
    ├── codecov.yml                  # coverage reporting configuration
    └── README.md, CONTRIBUTING.md, LICENSE, CODE_OF_CONDUCT.md

Four boundaries are worth knowing before editing anything:

* **Shipped versus not.** Only ``src/pdsfile/`` is installed. The eleven maintenance
  programs are console scripts into ``holdings_maintenance``, so those modules are
  runtime code with a frozen command-line surface; ``crlf``, ``re_validate`` and
  ``show_opus_products`` ship in the package too but are run as ``python -m`` modules
  rather than installed as scripts.
* **Public versus private.** Modules whose names begin with an underscore are
  implementation: importable, documented in the :doc:`/api/index`, but not part of the
  frozen public surface. The freeze covers what ``tests/api/api_manifest.json``
  records; ``tests/api/test_api_freeze.py`` enforces it, and neither file may be edited
  to make a difference disappear.
* **Configuration lives in one file.** ``pyproject.toml`` carries the packaging
  metadata, the dependencies and extras, every tool's configuration, and the ruff
  per-file-ignores ratchet. There is no ``setup.py``, no ``setup.cfg``, and no
  per-tool dotfile.
* **Records are part of the repository.** ``plans/`` and ``critiques/`` hold the
  plans, review rounds and validation records of the work that produced the current
  tree. They are provenance, not documentation of the code; nothing in the package
  reads them.
