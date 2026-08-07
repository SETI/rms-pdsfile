##########################################################################################
# tests/holdings_maintenance/test_driver_setup.py
#
# Pins the log handlers _common.setup_run attaches at a tool's log root.
#
# setup_run is the preamble all three drivers begin with: it parses the command
# line, resolves the log root, builds the logger, and attaches the handlers the
# tool's spec declares. No other test drives a driver-backed tool with --log, so
# that last step is reached only here -- and reached in both halves, because a
# handler that is created and never attached leaves the same file behind.
#
# pds4checksums declares two factories, a warning handler and an error handler, so
# a preamble that attached only the first fails this. It also carries the pds3
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

    The run validates a bundle that has no checksum file yet, so it logs an error.
    That is what gives the handlers something to write: their files exist either
    way, since each opens its file when it is created, and only what the files hold
    says whether the logger ever reached them.
    """

    log_root = tmp_path / 'logroot'

    run = support.run_tool(fresh_tree, 'pds4checksums', '--validate',
                           '--log', log_root, fresh_tree.path(BUNDLE_DIR))

    assert run.error_lines, run.describe()

    written = log_root / PROGNAME
    assert (sorted(path.name for path in written.glob('*.log'))
            == ['ERRORS.log', 'WARNINGS.log']), run.describe()
    assert written.joinpath('ERRORS.log').read_text(), run.describe()
    assert written.joinpath('WARNINGS.log').read_text(), run.describe()
