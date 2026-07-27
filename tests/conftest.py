##########################################################################################
# tests/conftest.py
#
# Configuration & setup before running tests on pds3file and pds4file.
#
# The holdings tree is selected once per session by tests.support.holdings (see
# PDSFILE_TEST_HOLDINGS there). When no holdings are available, collection still
# succeeds and every test is skipped rather than erroring at import time.
##########################################################################################

import pdslogger
import pytest

from pdsfile import (Pds3File,
                     Pds4File)
from tests.support.holdings import resolve_holdings, SKIP_REASON

##########################################################################################
# Setup before all tests
##########################################################################################
def pytest_addoption(parser):
    # 'ns' is the default because it is the broader pass: every test directory runs
    # under it, while 's' covers pds3 only. choices makes a mistyped mode a loud
    # usage error rather than a silently different session.
    parser.addoption("--mode", action="store", choices=('s', 'ns'), default='ns')
    parser.addoption("--update", action="store_true")

def pytest_configure(config):
    # Resolve the holdings selection once, before collection. An explicit but
    # broken selection (PDSFILE_TEST_HOLDINGS=full/mini with missing paths) fails
    # the session loudly with a clean usage error.
    try:
        config._pdsfile_holdings = resolve_holdings()
    except RuntimeError as exc:
        raise pytest.UsageError(str(exc)) from None

def pytest_collection_modifyitems(config, items):
    holdings = config._pdsfile_holdings
    if not holdings.available:
        # No holdings: skip every data-dependent test (nearly the whole suite) with
        # a clear reason instead of failing collection. Tests marked holdings_free
        # build their own inputs and must still run on a machine with no holdings.
        skip = pytest.mark.skip(reason=SKIP_REASON)
        for item in items:
            if 'holdings_free' in item.keywords:
                continue
            item.add_marker(skip)
        return
    if holdings.flavor == 'mini':
        # full_holdings-marked tests are only meaningful against the complete real
        # tree; skip them under the mini fixtures.
        skip_full = pytest.mark.skip(reason="full_holdings: skipped under the mini fixtures")
        for item in items:
            if 'full_holdings' in item.keywords:
                item.add_marker(skip_full)

def turn_on_logger(filename):
    LOGGER = pdslogger.PdsLogger(filename)
    Pds3File.set_logger(LOGGER)
    Pds4File.set_logger(LOGGER)

@pytest.fixture(scope='session', autouse=True)
def setup(request):
    holdings = request.config._pdsfile_holdings
    if not holdings.available:
        # Every test is skipped; there is nothing to preload.
        return

    # --mode is restricted to 's'/'ns' and defaults to 'ns', so the two modes are
    # exhaustive: 's' is shelves-only for both classes, 'ns' is neither. The two
    # classes are always set together; a session where they disagree is not a mode
    # the suite exercises.
    shelves_only = request.config.option.mode == 's'
    Pds3File.use_shelves_only(shelves_only)
    Pds4File.use_shelves_only(shelves_only)

    # turn_on_logger("test_log.txt")
    Pds3File.preload(holdings.pds3_root)
    Pds4File.preload(holdings.pds4_root)
