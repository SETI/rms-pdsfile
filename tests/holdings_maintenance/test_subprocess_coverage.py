##########################################################################################
# tests/holdings_maintenance/test_subprocess_coverage.py
#
# The opt-in path that lets coverage see the maintenance tools. The tools run as
# subprocesses (see this package's __init__ for why that is not negotiable), and
# `coverage run` does not follow a child, so without this path twelve of the fourteen
# programs are reported at a fraction of what the tests actually drive.
#
# Two things have to hold, and each is checked here rather than assumed:
#
#   * the coverage variables reach a tool subprocess, absolute, so a child whose working
#     directory is the disposable tree still finds the config and still writes its data
#     where the run can combine it;
#   * the hook in `_subprocess_guard/sitecustomize.py` really starts the measurement, and
#     kills the interpreter when it cannot.
#
# The subprocess tests below pass `-S`. Coverage 7.10 and later install their own
# `a1_coverage.pth`, which calls the same `coverage.process_startup()` from site
# processing and would start the measurement whether or not this repository's hook works;
# `-S` skips site processing, so what those tests observe can only have come from the
# hook. That also means `sitecustomize` has to be imported explicitly there and
# site-packages named on PYTHONPATH, neither of which a real tool subprocess needs.
##########################################################################################

import glob
import os
import subprocess
import sys
from pathlib import Path

import coverage
import pytest

from tests.holdings_maintenance import support

pytestmark = pytest.mark.holdings_free

PYPROJECT = support.REPO_ROOT / 'pyproject.toml'

# Where coverage is installed, for the `-S` children: without site processing they have
# no site-packages on the path at all, and the hook's first act is to import coverage.
SITE_PACKAGES = str(Path(coverage.__file__).resolve().parent.parent)


@pytest.fixture
def unmeasured(monkeypatch):
    """Present the environment of a run that is not measuring subprocesses.

    The suite itself may be running under `--coverage-subprocess`, which sets all four
    variables; a test of what happens when they are absent has to remove them.
    """

    for name in ('COVERAGE_PROCESS_START', 'COVERAGE_FILE',
                 'PDSFILE_COVERAGE_BRANCH', 'PDSFILE_COVERAGE_PARALLEL'):
        monkeypatch.delenv(name, raising=False)


def _child_env(tmp_path, *, pythonpath):
    """Return the environment for one `-S` child that should measure itself."""

    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(pythonpath)
    env['COVERAGE_PROCESS_START'] = str(PYPROJECT)
    env['COVERAGE_FILE'] = str(tmp_path / '.coverage')
    env['PDSFILE_COVERAGE_PARALLEL'] = 'true'
    env['PDSFILE_COVERAGE_BRANCH'] = 'false'
    # The read-only guard is the other half of sitecustomize and is not under test here;
    # leaving it wanted would make a failure of either look like a failure of both.
    env.pop('PDSFILE_READONLY_ROOTS', None)

    return env


def test_no_coverage_variables_when_the_run_is_not_measuring(unmeasured):
    """Coverage of the tools is opt-in: nothing is added to a subprocess by default."""

    assert support.subprocess_coverage_env() == {}


def test_the_variables_are_made_absolute(unmeasured, monkeypatch, tmp_path):
    """A tool subprocess runs inside the disposable tree, where a relative path lies.

    Its config would be looked for in a directory that has no pyproject.toml, and its
    data would be written into a tree the fixture deletes -- and coverage reports
    whatever it has, so both mistakes subtract from the total in silence.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('COVERAGE_PROCESS_START', 'pyproject.toml')
    monkeypatch.setenv('COVERAGE_FILE', 'build/.coverage')

    assert support.subprocess_coverage_env() == {
        'COVERAGE_PROCESS_START': str(tmp_path / 'pyproject.toml'),
        'COVERAGE_FILE': str(tmp_path / 'build' / '.coverage'),
    }


def test_the_data_file_defaults_to_coverages_own_name(unmeasured, monkeypatch, tmp_path):
    """With COVERAGE_FILE unset the default is resolved here, not in the child.

    Coverage's default is the relative name `.coverage`, and a child that resolved it
    itself would resolve it against the disposable tree.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('COVERAGE_PROCESS_START', str(PYPROJECT))

    assert support.subprocess_coverage_env()['COVERAGE_FILE'] == str(tmp_path / '.coverage')


def test_a_tool_tree_environment_absolutizes_them(unmeasured, monkeypatch, tmp_path):
    """The variables have to arrive through ToolTree.env, which is what runs a tool.

    Asserting the values back would prove nothing -- `ToolTree.env` starts from a copy
    of `os.environ`, so anything already set there arrives whether or not this code
    runs. What only this code supplies is the absolute form, so that is what is
    asserted: relative in, absolute out.
    """

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('COVERAGE_PROCESS_START', 'pyproject.toml')
    monkeypatch.setenv('COVERAGE_FILE', 'build/.coverage')

    env = support.ToolTree(tmp_path / 'tree', 'pds3').env

    assert env['COVERAGE_PROCESS_START'] == str(tmp_path / 'pyproject.toml')
    assert env['COVERAGE_FILE'] == str(tmp_path / 'build' / '.coverage')
    # The rest of the environment is unchanged by the coverage variables.
    assert env['PDS3_HOLDINGS_DIR'] == str(tmp_path / 'tree' / 'holdings')
    assert str(support.SUBPROCESS_GUARD_DIR) in env['PYTHONPATH']


def test_a_tool_tree_environment_invents_nothing_when_not_measuring(unmeasured, tmp_path):
    """An unmeasured run must not conjure a data file out of coverage's default name.

    `subprocess_coverage_env` spells `.coverage` itself, so the failure this guards
    against is that spelling escaping into a run nobody asked to measure -- which
    would leave stray data files, and would leave `COVERAGE_FILE` set for anything
    else the tool starts.
    """

    env = support.ToolTree(tmp_path, 'pds3').env

    assert 'COVERAGE_PROCESS_START' not in env
    assert 'COVERAGE_FILE' not in env


def test_the_hook_starts_coverage_in_a_child(tmp_path):
    """The hook measures a `pdsfile` module imported by a child it did not compile.

    `-S` is what makes this attributable: coverage's own `a1_coverage.pth` is skipped,
    so the data file below exists only because sitecustomize started the measurement.
    """

    env = _child_env(tmp_path, pythonpath=[str(support.SUBPROCESS_GUARD_DIR),
                                           SITE_PACKAGES,
                                           str(support.REPO_ROOT / 'src')])
    proc = subprocess.run([sys.executable, '-S', '-c',
                           'import sitecustomize; import pdsfile.pdscache'],
                          env=env, capture_output=True, check=False,
                          timeout=support.TOOL_TIMEOUT)

    assert proc.returncode == 0, proc.stderr.decode('utf-8', errors='replace')

    # One suffixed file, because the run asked pyproject.toml for parallel data files;
    # unsuffixed, every child would overwrite the parent's.
    written = glob.glob(str(tmp_path / '.coverage.*'))
    assert len(written) == 1, written

    data = coverage.CoverageData(written[0])
    data.read()
    measured = [name for name in data.measured_files() if name.endswith('pdscache.py')]
    assert measured, sorted(data.measured_files())
    assert data.lines(measured[0]), 'the module was named but no line was recorded'


def test_the_hook_measures_a_child_that_processes_site(tmp_path):
    """The path every real tool subprocess takes: site processed, sitecustomize automatic.

    The `-S` tests above isolate the hook, at the cost of never reaching the branch that
    runs when something else started coverage first -- which, from coverage 7.10, is what
    happens in every real run, because `a1_coverage.pth` gets there first and
    `process_startup()` then returns None. Without this id, tightening that branch to
    reject None outright would kill every tool subprocess and leave all the other tests
    green.
    """

    env = _child_env(tmp_path, pythonpath=[str(support.SUBPROCESS_GUARD_DIR),
                                           str(support.REPO_ROOT / 'src')])
    proc = subprocess.run([sys.executable, '-c', 'import pdsfile.pdscache'],
                          env=env, capture_output=True, check=False,
                          timeout=support.TOOL_TIMEOUT)

    assert proc.returncode == 0, proc.stderr.decode('utf-8', errors='replace')

    written = glob.glob(str(tmp_path / '.coverage.*'))
    assert len(written) == 1, written
    data = coverage.CoverageData(written[0])
    data.read()
    assert [name for name in data.measured_files() if name.endswith('pdscache.py')], \
        sorted(data.measured_files())


def test_the_hook_refuses_to_start_when_coverage_is_missing(tmp_path):
    """A child that cannot measure must die rather than run unmeasured.

    Python prints what a sitecustomize hook raises and carries on, and a tool
    subprocess's stderr is captured by the test that ran it and read by nobody, so a
    hook that failed quietly would subtract from the total with nothing to show for it.
    """

    # Only the guard directory: with `-S` there is no site-packages, so coverage cannot
    # be imported at all.
    env = _child_env(tmp_path, pythonpath=[str(support.SUBPROCESS_GUARD_DIR)])
    proc = subprocess.run([sys.executable, '-S', '-c',
                           'import sitecustomize; print("ran unmeasured")'],
                          env=env, capture_output=True, check=False,
                          timeout=support.TOOL_TIMEOUT)

    assert proc.returncode == 70, proc.stdout
    assert b'ran unmeasured' not in proc.stdout, proc.stdout
    assert b'refusing to start without coverage measurement' in proc.stderr, proc.stderr


def test_the_hook_refuses_to_start_without_per_process_data_files(tmp_path):
    """Measuring into a shared data file is worse than not measuring.

    Every measured process writes the name `COVERAGE_FILE` gives, so without the suffix
    `parallel` supplies, each child overwrites the parent's data and every sibling's --
    and the run reports a fraction of what it measured, with nothing to say so. A
    developer who exports COVERAGE_PROCESS_START by hand and not
    PDSFILE_COVERAGE_PARALLEL lands exactly there.
    """

    env = _child_env(tmp_path, pythonpath=[str(support.SUBPROCESS_GUARD_DIR),
                                           str(support.REPO_ROOT / 'src')])
    env.pop('PDSFILE_COVERAGE_PARALLEL')
    proc = subprocess.run([sys.executable, '-c', 'print("ran into a shared data file")'],
                          env=env, capture_output=True, check=False,
                          timeout=support.TOOL_TIMEOUT)

    assert proc.returncode == 70, proc.stdout
    assert b'ran into a shared data file' not in proc.stdout, proc.stdout
    assert b'parallel=false' in proc.stderr, proc.stderr
    assert not glob.glob(str(tmp_path / '.coverage*')), 'it wrote data anyway'


def test_the_configured_default_is_still_branch_coverage_in_one_data_file(unmeasured):
    """What `--coverage` and the data gate get when neither variable is set.

    The two settings are written in pyproject.toml as environment substitutions so that
    `--coverage-subprocess` can flip them without a second config file. This pins the
    fallbacks: a run that sets nothing measures branches into one unsuffixed file,
    which is what scripts/automated_tests/pdsfile_main_test.sh has always produced.
    """

    config = coverage.Coverage(config_file=str(PYPROJECT)).config

    assert config.branch is True
    assert config.parallel is False
    assert config.source == ['pdsfile']


def test_the_subprocess_settings_are_readable_from_the_same_config(monkeypatch):
    """And what `--coverage-subprocess` gets from the same file, with both set."""

    monkeypatch.setenv('PDSFILE_COVERAGE_BRANCH', 'false')
    monkeypatch.setenv('PDSFILE_COVERAGE_PARALLEL', 'true')

    config = coverage.Coverage(config_file=str(PYPROJECT)).config

    assert config.branch is False
    assert config.parallel is True
    assert config.source == ['pdsfile']
