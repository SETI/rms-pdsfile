##########################################################################################
# tests/holdings_maintenance/conftest.py
#
# Fixtures shared by the maintenance-tool tests.
#
# Each holdings-dependent test module declares, at module level:
#
#   SOURCE_FLAVOR       'pds3' or 'pds4'
#   SOURCE_FINGERPRINTS a sequence of (holdings-relative path, size, md5)
#   SOURCE_PATHS        the holdings-relative paths to copy
#   SOURCE_MTIMES       {holdings-relative path: pinned POSIX mtime}
#
# The module-scoped `tool_tree` fixture verifies every declared path against the
# resolved holdings root and skips the whole module if any of them is missing or
# differs, then copies the subset into a temporary tree with the declared mtimes.
##########################################################################################

import os

import pytest

from tests.holdings_maintenance import readonly_roots, support


@pytest.fixture(scope='session')
def source_stage(tmp_path_factory):
    """Return the per-flavor local staging copies of the declared source files.

    Reading and hashing the sources straight from the holdings root once per module
    is expensive when the root is a network mount, so each declared file is
    verified and copied locally the first time any module asks for it.
    """

    root = tmp_path_factory.mktemp('holdings_maintenance_sources')

    return {flavor: support.SourceStage(root / flavor)
            for flavor in support.HOLDINGS_DIRNAME}


@pytest.fixture(scope='module')
def tool_tree(request, tmp_path_factory, source_stage):
    """Return a temporary holdings tree holding this module's declared subset.

    Skips the module when no holdings are available, or when any declared source
    file is missing or does not match its declared size and md5. A content
    mismatch is as disqualifying as an absent file: the module's goldens were
    generated from specific bytes, and the two real holdings roots do not hold
    identical content for every path.
    """

    module = request.module
    flavor = module.SOURCE_FLAVOR

    holdings = request.config._pdsfile_holdings
    if not holdings.available:                                  # pragma: no cover
        pytest.skip('no holdings available')

    root = holdings.pds3_root if flavor == 'pds3' else holdings.pds4_root

    stage = source_stage[flavor]
    reasons = stage.ensure(root, module.SOURCE_FINGERPRINTS)
    if reasons:
        pytest.skip('declared source subset unusable under this holdings root: '
                    + '; '.join(reasons))

    tmp_dir = tmp_path_factory.mktemp(module.__name__.rpartition('.')[2])

    return support.build_tree(tmp_dir, stage.directory, flavor,
                              module.SOURCE_PATHS, module.SOURCE_MTIMES)


@pytest.fixture
def fresh_tree(tool_tree):
    """Return the module's tree rebuilt to its just-copied state.

    The tree itself is module-scoped, but rebuilding it is cheap (the sources are
    staged locally), so every test can start from the same known state instead of
    depending on the test before it.
    """

    tool_tree.reset()

    return tool_tree


@pytest.fixture(scope='module')
def golden_update(request):
    """Return True when the session was started with --update to rewrite goldens."""

    return bool(request.config.getoption('--update'))


@pytest.fixture(scope='session', autouse=True)
def _holdings_are_read_only():
    """Refuse any write into a real holdings root, in this process and in tool subprocesses.

    These tests drive tools that write -- archives, checksum files, shelves, logs -- and
    are meant to write only into the temporary tree the fixtures build. Nothing enforced
    that. A test that resolves a path through `Pds3File` or `Pds4File` gets whichever
    root the class was preloaded with, and a second `preload()` does not re-root an
    already-preloaded class, so a test that builds its own tree and preloads it still
    resolves into the real holdings and writes there. Observation 3999 has the
    measurements.

    That is not hypothetical: it put an 80 MB archive into the shared PDS4 tree, passed
    locally because that tree is writable, and failed four CI jobs with PermissionError
    against the read-only one. The failure was the lucky case. Where the holdings are
    writable, the damage is silent.

    **The check is an interception rather than a scan.** Walking both roots before and
    after each test cost about 53 seconds across this suite, and per module about 3, for
    the same detection -- but either way the cost grows with the size of the holdings,
    and these trees are a limited copy of something much larger. Wrapping the write
    entry points costs one string comparison per write and does not grow at all.

    A tool subprocess installs the same guard from `_subprocess_guard/sitecustomize.py`,
    which Python imports at startup because `ToolTree.env` puts that directory on
    PYTHONPATH.
    """

    os.environ[readonly_roots.ENV_VAR] = os.pathsep.join(
        support.readonly_holdings_roots())
    readonly_roots.install()
