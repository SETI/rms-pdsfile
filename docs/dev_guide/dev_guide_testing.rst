Test-Suite Guide
================

The suite under ``tests/`` is holdings-aware: nearly everything in it runs against a
real PDS holdings tree, and every data-dependent test skips cleanly on a machine that
has none. This chapter explains how the tree is selected, what the session options
and markers mean, and how the two golden mechanisms and the tool-test sandbox work.

Setup and the basic invocation
------------------------------

A development checkout runs the suite from an editable install with the dev extras::

    python -m venv venv
    source venv/bin/activate
    pip install -e ".[dev]"

    export PDS3_HOLDINGS_DIR=/path/to/pdsdata/holdings
    export PDS4_HOLDINGS_DIR=/path/to/pdsdata/pds4-holdings
    export PDSFILE_TEST_HOLDINGS=full

    pytest tests --mode ns

``scripts/run-all-checks.sh`` wraps this invocation (serial by default; ``-w auto``
parallelizes with ``pytest-xdist``) together with every other gate the repository
runs -- see :doc:`dev_guide_ci`. It also fills in the selector for you: with either
holdings variable exported and ``PDSFILE_TEST_HOLDINGS`` unset, it selects ``full``
rather than silently running the holdings-free subset, and with only one of the two
roots exported the session fails naming the missing variable.

Holdings resolution: full, mini, or skip
----------------------------------------

``tests/support/holdings.py`` resolves, once per session and before collection, which
tree the run is against; ``tests/conftest.py`` turns the answer into a session-scoped
preload of both classes. ``PDSFILE_TEST_HOLDINGS`` drives it:

``full``
    Roots come from ``PDS3_HOLDINGS_DIR`` and ``PDS4_HOLDINGS_DIR``. Both must be set
    and both must be directories; anything else fails the session with a usage error
    rather than running a quietly different suite. This is the normal data run,
    against either the complete holdings or a limited real copy.

``mini``
    Roots are ``$PDSFILE_TEST_DATA_DIR/holdings`` and
    ``$PDSFILE_TEST_DATA_DIR/pds4-holdings``. **The mini flavor is dormant,
    reserved machinery**: it belongs to a deferred plan for a manufactured fixture
    tree, no ``PDSFILE_TEST_DATA_DIR`` is set anywhere today, and nothing in the
    repository depends on it. It stays in place so a future revival plugs into the
    resolver without churn; do not remove it and do not build on it.

unset
    Mini if ``PDSFILE_TEST_DATA_DIR`` resolves to real trees (it does not, today);
    otherwise **no holdings**: collection still succeeds, and every test not marked
    ``holdings_free`` is skipped with one clear reason. This is what a contributor
    without data and the hosted CI runners see -- a green, mostly-skipped run, never
    a collection error.

Session options and markers
---------------------------

``--mode s|ns``
    Defined in ``tests/conftest.py``, default ``ns``. The one thing it controls is
    :meth:`~pdsfile.pdsfile.PdsFile.use_shelves_only`, set the same way on both
    classes before the session preload: ``s`` answers the filesystem questions from
    the info shelves, ``ns`` from the filesystem (see ``SHELVES_ONLY`` in
    :doc:`dev_guide_subsystems`). Because the setting is class-level state, the mode
    is a property of the whole session, not of a test. ``ns`` is the broader pass --
    the entire ``tests/`` tree runs under it -- and a shelves-specific failure is
    visible only under ``s``, so a data change is checked with both::

        pytest tests --mode ns
        pytest tests/pds3file tests/rules/pds3 --mode s
        pytest tests/pds4file tests/rules/pds4 --mode s

    The tool tests and ``tests/core/`` are deliberately absent from the ``s`` passes:
    the tools run in their own subprocesses, and ``tests/core/`` builds its own
    inputs, so the mode changes neither.

``--update``
    Rewrites golden files instead of comparing against them; the next section says
    when that is legitimate.

``full_holdings`` marker
    The test is only meaningful against the complete real tree (total sizes, volume
    counts). Under the mini flavor these would be skipped; against a limited real
    copy they simply fail or pass on their own terms. The holdings-dependent
    tool-test modules carry this marker *and* fingerprint verification (below) --
    the marker guards the dormant mini flavor, the fingerprints guard a real copy
    that lacks or diverges from their declared sources.

``holdings_free`` marker
    The test builds every input it needs and must run even with no holdings at all.
    ``tests/api/`` and ``tests/docs/`` apply it to everything they collect through
    their ``conftest.py``, and the ``tests/core/`` modules carry it as a module-level
    ``pytestmark``; this subset is what the hosted CI job actually exercises.

The rule-test goldens
---------------------

The per-dataset tests under ``tests/rules/`` compare structured output --
:meth:`~pdsfile._opus._OpusMixin.opus_products` dictionaries,
:meth:`~pdsfile._associations._AssociationsMixin.associated_abspaths` lists --
against golden copies under ``tests/golden/full/pds3/`` and ``.../pds4/``, through
the helpers in ``tests/support/pdsfile_test_helper.py``. Two behaviors to know:
the stored values are logical paths, which carry no machine-specific root, so the
goldens are portable across machines hosting the same data; and a *missing* golden is
written from the
current output rather than failed, so the first run of a new test creates its golden
and only later runs compare. A wrong rule change therefore cannot be caught by a
golden that was created after it; :doc:`dev_guide_goldens` covers regeneration
discipline.

The tool-test sandbox
---------------------

The maintenance-tool tests under ``tests/holdings_maintenance/`` never touch the real
holdings tree with a tool. Each holdings-dependent test module declares, at module
level, exactly what it needs::

    SOURCE_FLAVOR       'pds3' or 'pds4'
    SOURCE_FINGERPRINTS ((holdings-relative path, size, md5), ...)
    SOURCE_PATHS        the holdings-relative paths to copy
    SOURCE_MTIMES       {holdings-relative path: pinned POSIX mtime}

A module-scoped fixture verifies every declared path against the resolved holdings
root -- any file missing, or differing in size or md5, skips the whole module,
because the committed goldens were generated from specific bytes -- then copies the
subset into a temporary tree under ``tmp_path`` with the declared mtimes applied.
The tools then run against that disposable copy as subprocesses (``python -m
pdsfile.holdings_maintenance...``), which enters each through the same ``main()``
its console script uses; corruption scenarios are fixed edits declared in the test
module, never randomized. Generated artifacts are compared through normalizers
(sorted ``.py`` sidecar text, archive member tuples) rather than as raw bytes,
because md5-file ordering and tar member order are not portable.

Two guards keep the sandbox honest: the real holdings roots are installed as
read-only paths in both the test process and every tool subprocess, so a tool that
escapes its temporary tree fails loudly; and only the two tools that read no
holdings root at all (``crlf``, ``shelf_consistency_check``) may be driven
in-process, since every other tool resolves paths against a class-level cache the
session has preloaded with the *real* tree.

Where the suites run
--------------------

``tests/api/`` pins the public-API freeze and the mixin mechanics; ``tests/docs/``
gates docstring/signature agreement and the two silent markup faults; both run
everywhere, holdings or not. The data suites run on every pull request on
self-hosted runners and nightly against the complete holdings, forever -- that is a
standing rule of the project, not a temporary arrangement -- and :doc:`dev_guide_ci`
maps which job runs what.
