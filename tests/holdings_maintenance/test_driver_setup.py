##########################################################################################
# tests/holdings_maintenance/test_driver_setup.py
#
# Pins the root log handlers _common.setup_run attaches for a tool.
#
# setup_run is the preamble all three drivers begin with: it parses the command
# line, resolves the log root, and builds the logger. Everything else it does is
# pinned elsewhere -- the missing-task exit by test_task_flags.py, the log-root
# fallback by test_re_validate.py's resolve_log_root cases -- but no other test
# drives a maintenance tool with --log, so the handlers a spec's
# handler_factories create at the log root are reached only here.
#
# pds4checksums declares two factories, a warning handler and an error handler, so
# a preamble that attached only the first would fail this. It also carries the pds3
# tool's progname, which is the subdirectory the handlers are created in.
##########################################################################################

import pytest

from tests.holdings_maintenance import subsets, support

pytestmark = pytest.mark.full_holdings

SOURCE_FLAVOR = 'pds4'
SOURCE_FINGERPRINTS = subsets.PDS4_BUNDLE_SOURCES
SOURCE_PATHS = subsets.paths_of(subsets.PDS4_BUNDLE_SOURCES)
SOURCE_MTIMES = subsets.PDS4_BUNDLE_MTIMES

BUNDLE_DIR = f'bundles/{subsets.PDS4_BUNDLESET}/{subsets.PDS4_BUNDLE}'
PROGNAME = 'pdschecksums'


def test_a_log_root_gets_every_handler_the_spec_declares(fresh_tree, tmp_path):
    """--log wires each of the tool's handler factories into the tool's own directory.

    The files exist whether or not the run has anything to write to them: each
    handler opens its file when it is created.
    """

    log_root = tmp_path / 'logroot'

    run = support.run_tool(fresh_tree, 'pds4checksums', '--initialize',
                           '--log', log_root, fresh_tree.path(BUNDLE_DIR))

    assert run.returncode == 0, run.describe()
    assert (log_root / PROGNAME / 'WARNINGS.log').is_file(), run.describe()
    assert (log_root / PROGNAME / 'ERRORS.log').is_file(), run.describe()
