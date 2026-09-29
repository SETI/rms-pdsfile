##########################################################################################
# tests/docs/conftest.py
#
# Everything under tests/docs/ checks the documentation sources themselves -- the
# reStructuredText under docs/ and the docstrings under src/ -- by reading files.
# Nothing here touches a holdings tree, so every test collected from this directory
# is holdings-free and must run on a machine with no data, including the hosted
# no-holdings CI job.
#
# tests/conftest.py skips every collected item that does not carry the holdings_free
# marker when no holdings are available. The marker is applied here to everything
# collected from this directory, which also covers future additions.
#
# That makes "no test in this directory needs holdings" a rule of the directory
# rather than an observation about the files currently in it. A test added here that
# does need holdings will fail on a runner without them instead of skipping, which is
# the intended signal: such a test belongs somewhere else in the tree.
##########################################################################################

from pathlib import Path

import pytest

# Resolved, because the collected item paths are resolved too: if the checkout is
# reached through a symlink, an unresolved comparison quietly stops matching and the
# marker stops being applied.
_DOCS_TESTS_DIR = Path(__file__).resolve().parent


# tryfirst: tests/conftest.py's pytest_collection_modifyitems adds the no-holdings skip
# to every item not already marked holdings_free, so this marker has to be in place
# before that hook runs. Conftest hook order is otherwise unspecified.
@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
    """Mark every test collected from this directory holdings-free.

    Parameters:
        items (list): the collected pytest items, modified in place.
    """
    holdings_free = pytest.mark.holdings_free
    for item in items:
        if item.path is not None and item.path.resolve().is_relative_to(_DOCS_TESTS_DIR):
            item.add_marker(holdings_free)
