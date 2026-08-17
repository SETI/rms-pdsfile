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
# Every guard is driven for real: the argument-count guard by an empty command
# line, and each directory guard by a scratch tree missing exactly the directory
# that guard checks, so no test touches a holdings root. The subprocess cases
# equal the guard sites one for one -- test_no_exit_minus_one_remains counts
# both and pins the per-script site totals textually.
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

# `exit 1` sites per script: one argument-count guard each, plus a directory
# guard for every directory the script requires to exist.
EXIT_1_SITES = {
    'setup_new_holdings.sh': 2,
    'copy_documents.sh': 3,
    'copy_shelves.sh': 3,
    'copy_all_except_metadata.sh': 1,
    'create_fake_volumes_for_metadata.sh': 3,
}

VOLSET = 'TESTSET_xxxx'


def _run(script, args):
    """Run one script under bash with the given arguments."""

    return subprocess.run(['bash', str(SCRIPTS_DIR / script), *args],
                          capture_output=True, text=True)


def _setup_holdings_missing(tmp_path):
    # setup_new_holdings.sh guard 2: <holdings_dir> does not exist. The parent
    # exists so `realpath` resolves and the guard itself is what fires.
    return [str(tmp_path / 'missing')]


def _documents_src_volset_missing(tmp_path):
    # copy_documents.sh guard 2: <src>/documents/<volset> does not exist.
    (tmp_path / 'src').mkdir()
    (tmp_path / 'dest').mkdir()
    return [str(tmp_path / 'src'), str(tmp_path / 'dest'), VOLSET]


def _documents_dest_documents_missing(tmp_path):
    # copy_documents.sh guard 3: <dest>/documents does not exist.
    (tmp_path / 'src' / 'documents' / VOLSET).mkdir(parents=True)
    (tmp_path / 'dest').mkdir()
    return [str(tmp_path / 'src'), str(tmp_path / 'dest'), VOLSET]


def _shelves_src_type_volset_missing(tmp_path):
    # copy_shelves.sh guard 2: <src>/<shelf_type>/<volset> does not exist.
    (tmp_path / 'src').mkdir()
    (tmp_path / 'dest').mkdir()
    return [str(tmp_path / 'src'), str(tmp_path / 'dest'), VOLSET, 'volumes']


def _shelves_dest_type_missing(tmp_path):
    # copy_shelves.sh guard 3: <dest>/<shelf_type> does not exist.
    (tmp_path / 'src' / 'volumes' / VOLSET).mkdir(parents=True)
    (tmp_path / 'dest').mkdir()
    return [str(tmp_path / 'src'), str(tmp_path / 'dest'), VOLSET, 'volumes']


def _fake_volumes_holdings_missing(tmp_path):
    # create_fake_volumes_for_metadata.sh guard 2: <holdings_dir> does not
    # exist (parent present, as above).
    return [str(tmp_path / 'missing'), VOLSET]


def _fake_volumes_metadata_volset_missing(tmp_path):
    # create_fake_volumes_for_metadata.sh guard 3: <holdings>/metadata/<volset>
    # does not exist.
    (tmp_path / 'holdings').mkdir()
    return [str(tmp_path / 'holdings'), VOLSET]


# One case per directory guard; the argument-count guards are the other test.
DIRECTORY_GUARD_CASES = (
    ('setup_new_holdings.sh', _setup_holdings_missing),
    ('copy_documents.sh', _documents_src_volset_missing),
    ('copy_documents.sh', _documents_dest_documents_missing),
    ('copy_shelves.sh', _shelves_src_type_volset_missing),
    ('copy_shelves.sh', _shelves_dest_type_missing),
    ('create_fake_volumes_for_metadata.sh', _fake_volumes_holdings_missing),
    ('create_fake_volumes_for_metadata.sh', _fake_volumes_metadata_volset_missing),
)


@pytest.mark.parametrize('script', COPY_SETUP_SCRIPTS)
def test_usage_error_exits_1(script):
    """No arguments is a usage error, and the status for it is 1, not 255."""

    run = _run(script, [])
    assert run.returncode == 1, (
        f'{script} exited {run.returncode}, not 1\n'
        f'stdout: {run.stdout}stderr: {run.stderr}')
    assert 'Usage:' in run.stdout, f'{script} printed: {run.stdout}'


@pytest.mark.parametrize(('script', 'build_args'), DIRECTORY_GUARD_CASES,
                         ids=[f'{script}-{build.__name__.lstrip("_")}'
                              for script, build in DIRECTORY_GUARD_CASES])
def test_directory_guard_exits_1(script, build_args, tmp_path):
    """A scratch tree missing one directory drives that guard to status 1."""

    run = _run(script, build_args(tmp_path))
    assert run.returncode == 1, (
        f'{script} exited {run.returncode}, not 1\n'
        f'stdout: {run.stdout}stderr: {run.stderr}')
    assert 'Directory does not exist' in run.stdout, f'{script} printed: {run.stdout}'


def test_no_exit_minus_one_remains():
    """Every guard site says `exit 1` and is driven by a subprocess case above."""

    for script in COPY_SETUP_SCRIPTS:
        text = (SCRIPTS_DIR / script).read_text()
        assert 'exit -1' not in text, f'{script} still carries an exit -1'
        assert text.count('exit 1') == EXIT_1_SITES[script], (
            f'{script} has {text.count("exit 1")} `exit 1` sites, '
            f'not {EXIT_1_SITES[script]}')

    # Twelve sites, twelve subprocess cases: one usage case per script plus the
    # directory-guard cases cover every guard.
    assert sum(EXIT_1_SITES.values()) == 12
    assert len(COPY_SETUP_SCRIPTS) + len(DIRECTORY_GUARD_CASES) == 12
