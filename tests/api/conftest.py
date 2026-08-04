##########################################################################################
# tests/api/conftest.py
#
# Everything under tests/api/ checks the public API surface itself, never the
# holdings data: the freeze test regenerates the manifest in a clean child
# interpreter and compares it against the committed one. So every test collected
# from this directory is holdings-free and must run on a machine with no holdings
# tree -- including the hosted no-holdings CI job.
#
# tests/conftest.py skips every collected item that does not carry the
# holdings_free marker when no holdings are available. Rather than marking each
# module (tests/api/test_api_freeze.py must not be edited), the marker is applied
# here to everything collected from this directory, which also covers future
# additions.
#
# That makes "no test in this directory needs holdings" a rule of the directory,
# not an observation about the files currently in it. A test added here that does
# need a holdings tree will fail on a runner without one instead of skipping --
# loudly, on the first run, which is the intended signal. Such a test belongs
# somewhere else in the tree.
#
# This file is deliberately dependency-free apart from pytest: the API-freeze check
# in scripts/run-all-checks.sh runs with --confcutdir=tests/api, which loads this
# conftest but not tests/conftest.py, and that invocation must stay hermetic. It
# also declares no options, so the session's --mode/--update options keep coming
# from tests/conftest.py alone.
##########################################################################################

from pathlib import Path

import pytest

# Resolved, because the collected item paths are resolved too: if the checkout is
# reached through a symlink, an unresolved comparison quietly stops matching and
# the marker stops being applied.
_API_TESTS_DIR = Path(__file__).resolve().parent


# tryfirst: tests/conftest.py's pytest_collection_modifyitems adds the no-holdings
# skip to every item that is not already marked holdings_free, so this marker has to
# be in place before that hook runs. Conftest hook order is otherwise unspecified.
@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
    holdings_free = pytest.mark.holdings_free
    for item in items:
        if item.path is not None and item.path.resolve().is_relative_to(_API_TESTS_DIR):
            item.add_marker(holdings_free)
