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

import pytest

from tests.holdings_maintenance import support


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


@pytest.fixture(scope='session')
def _holdings_baseline(request):
    """Return the mutable record of what each real holdings root holds.

    Snapshotting is the expensive half of the read-only guard, so the state left by
    one test becomes the baseline for the next instead of being taken twice per test.
    """

    holdings = request.config._pdsfile_holdings
    if not holdings.available:                                  # pragma: no cover
        return None

    roots = [str(r) for r in (holdings.pds3_root, holdings.pds4_root) if r]

    return {root: support.snapshot_tree(root) for root in roots}


@pytest.fixture(autouse=True)
def _holdings_stay_read_only(request, _holdings_baseline):
    """Fail any test that leaves a new file inside a real holdings root.

    These tests drive tools that write -- archives, checksum files, shelves -- and
    they are meant to write only into the temporary tree `tool_tree` builds. Nothing
    enforced that. A test that resolves a path through `Pds3File` or `Pds4File` gets
    whichever root the class was preloaded with, and a second `preload()` call does
    not re-root an already-preloaded class, so a test that builds its own tree and
    preloads it still resolves into the real holdings and writes there.

    That is not hypothetical: it put an 80 MB archive into the shared PDS4 tree,
    passed locally because that tree is writable, and failed four CI jobs with
    PermissionError against the read-only one. The failure is the lucky case. On a
    machine where the holdings are writable, the damage is silent.

    Each root is walked once per test and the result carried forward as the next
    test's baseline, so a violation is attributed to the test that caused it and the
    baseline moves on rather than reporting the same paths for every test after it.
    """

    yield

    if _holdings_baseline is None:                              # pragma: no cover
        return

    appeared = []
    for root, before in _holdings_baseline.items():
        after = support.snapshot_tree(root)
        appeared += sorted(after - before)
        _holdings_baseline[root] = after

    assert not appeared, (
        f'{request.node.nodeid} wrote into a real holdings root. Tools under test '
        f'must write only into the temporary tree. New paths:\n  '
        + '\n  '.join(appeared[:20])
        + (f'\n  ... and {len(appeared) - 20} more' if len(appeared) > 20 else ''))
