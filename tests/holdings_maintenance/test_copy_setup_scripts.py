##########################################################################################
# tests/holdings_maintenance/test_copy_setup_scripts.py
#
# The five copy/setup scripts stop an invalid invocation with status 1.
#
# Each script guards its command line -- an argument-count check, then directory
# checks on the arguments -- before it creates or copies anything. Those guards
# exited -1, which is not a status a process can return: bash reduces it to 255
# (ShellCheck SC2242). The six pdsdata-sync-* siblings and
# update_holdings_for_new_metadata.sh exit 1 on the same kind of error, and the
# owner's 2026-08-16 ruling (plans/2026-08-16-addendum-owner-four-items.md)
# extended that status to these five, every guard of which is reachable only by
# an invalid invocation. The scripts are otherwise still document-only.
#
# Only the argument-count guard is run here: it is the first line of every
# script, it needs no scratch tree, and its status is the one a caller's `if`
# or `set -e` actually sees. The directory guards exit through the same
# converted statement, which test_no_exit_minus_one_remains pins textually for
# all twelve sites at once.
##########################################################################################

import subprocess
from pathlib import Path

import pytest

from pdsfile.holdings_maintenance import pds3

pytestmark = pytest.mark.holdings_free

SCRIPTS_DIR = Path(pds3.__file__).parent

COPY_SETUP_SCRIPTS = (
    'setup_new_holdings.sh',
    'copy_documents.sh',
    'copy_shelves.sh',
    'copy_all_except_metadata.sh',
    'create_fake_volumes_for_metadata.sh',
)


@pytest.mark.parametrize('script', COPY_SETUP_SCRIPTS)
def test_usage_error_exits_1(script):
    """No arguments is a usage error, and the status for it is 1, not 255."""

    run = subprocess.run(['bash', str(SCRIPTS_DIR / script)],
                         capture_output=True, text=True)
    assert run.returncode == 1, (
        f'{script} exited {run.returncode}, not 1\n'
        f'stdout: {run.stdout}stderr: {run.stderr}')
    assert 'Usage:' in run.stdout, f'{script} printed: {run.stdout}'


def test_no_exit_minus_one_remains():
    """Every guard in the five scripts exits 1; none says `exit -1` (SC2242)."""

    for script in COPY_SETUP_SCRIPTS:
        text = (SCRIPTS_DIR / script).read_text()
        assert 'exit -1' not in text, f'{script} still carries an exit -1'
        assert 'exit 1' in text, f'{script} has no exit 1 guard at all'
