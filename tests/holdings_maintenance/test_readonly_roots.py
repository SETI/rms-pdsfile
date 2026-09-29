##########################################################################################
# tests/holdings_maintenance/test_readonly_roots.py
#
# The guard that keeps the maintenance-tool tests out of the real holdings. It is
# installed for every test in this directory, so a defect in it is either invisible or
# breaks everything; these exercise it directly.
##########################################################################################

import os
import subprocess
import sys

import pytest

from tests.holdings_maintenance import readonly_roots, support

pytestmark = pytest.mark.holdings_free


@pytest.fixture
def protected(tmp_path, monkeypatch):
    """Install the guard over a temporary directory standing in for a holdings root."""

    root = tmp_path / 'holdings'
    (root / 'volumes').mkdir(parents=True)
    (root / 'volumes' / 'readable.txt').write_text('content', encoding='utf-8')

    monkeypatch.setenv(readonly_roots.ENV_VAR, str(root))
    readonly_roots.install()

    yield root

    # Put the session-wide guard back, over the real roots.
    monkeypatch.undo()
    readonly_roots.install()


def test_a_write_inside_the_root_is_refused(protected):
    with pytest.raises(readonly_roots.ReadOnlyHoldingsError), \
            open(protected / 'volumes' / 'new.txt', 'w'):
        pass                                            # pragma: no cover
    assert not (protected / 'volumes' / 'new.txt').exists()


def test_making_a_directory_inside_the_root_is_refused(protected):
    with pytest.raises(readonly_roots.ReadOnlyHoldingsError):
        os.makedirs(protected / 'archives-volumes' / 'X')
    assert not (protected / 'archives-volumes').exists()


def test_deleting_inside_the_root_is_refused(protected):
    with pytest.raises(readonly_roots.ReadOnlyHoldingsError):
        os.remove(protected / 'volumes' / 'readable.txt')
    assert (protected / 'volumes' / 'readable.txt').exists()


def test_reads_are_untouched(protected):
    assert (protected / 'volumes' / 'readable.txt').read_text(encoding='utf-8') == 'content'
    assert os.listdir(protected / 'volumes') == ['readable.txt']


def test_writes_outside_the_root_are_untouched(protected, tmp_path):
    elsewhere = tmp_path / 'work' / 'out.txt'
    elsewhere.parent.mkdir()
    elsewhere.write_text('fine', encoding='utf-8')
    assert elsewhere.read_text(encoding='utf-8') == 'fine'


def test_a_subprocess_installs_the_same_guard(protected, tmp_path):
    """The guard reaches a tool subprocess through sitecustomize on PYTHONPATH."""

    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join([str(support.SUBPROCESS_GUARD_DIR),
                                         str(support.REPO_ROOT)])
    env[readonly_roots.ENV_VAR] = str(protected)

    target = protected / 'volumes' / 'from_a_child.txt'
    proc = subprocess.run([sys.executable, '-c', f'open({str(target)!r}, "w")'],
                          env=env, capture_output=True, check=False)

    assert proc.returncode != 0, proc.stdout
    assert b'ReadOnlyHoldingsError' in proc.stderr, proc.stderr
    assert not target.exists()


def test_a_symlink_into_the_root_is_refused(protected, tmp_path):
    """A path that reaches the root through a symlink elsewhere is still inside it.

    `abspath()` keeps symlink components, so comparing with it let an aliased path
    pass while the write landed in the protected tree. Both the roots and the targets
    are resolved with `realpath()` now.
    """

    alias = tmp_path / 'alias'
    alias.symlink_to(protected)

    with pytest.raises(readonly_roots.ReadOnlyHoldingsError), \
            open(alias / 'volumes' / 'through_a_link.txt', 'w'):
        pass                                            # pragma: no cover
    assert not (protected / 'volumes' / 'through_a_link.txt').exists()


def test_os_open_is_refused(protected):
    """`os.open()` is the floor every other write stands on, so it is guarded too."""

    with pytest.raises(readonly_roots.ReadOnlyHoldingsError):
        os.open(protected / 'volumes' / 'low_level.txt', os.O_CREAT | os.O_WRONLY)
    assert not (protected / 'volumes' / 'low_level.txt').exists()


def test_os_open_for_reading_still_works(protected):
    """Guarding os.open must not stop the reads these tests depend on."""

    fd = os.open(protected / 'volumes' / 'readable.txt', os.O_RDONLY)
    try:
        assert os.read(fd, 7) == b'content'
    finally:
        os.close(fd)


def test_pathlib_write_text_is_refused(protected):
    """`pathlib` writes through `io.open`, a separate reference to the same builtin.

    Patching `builtins.open` alone left `Path.write_text()` unguarded.
    """

    with pytest.raises(readonly_roots.ReadOnlyHoldingsError):
        (protected / 'volumes' / 'via_pathlib.txt').write_text('x', encoding='utf-8')
    assert not (protected / 'volumes' / 'via_pathlib.txt').exists()


def test_the_subprocess_hook_refuses_to_start_without_the_guard(tmp_path):
    """A subprocess that cannot install the guard must die, not run unprotected.

    Python prints whatever a sitecustomize hook raises and carries on starting up, so
    a guard that failed to install would leave the tool running against the real
    holdings while its test still passed.
    """

    env = dict(os.environ)
    env['PYTHONPATH'] = str(support.SUBPROCESS_GUARD_DIR)   # the guard is NOT importable
    env[readonly_roots.ENV_VAR] = str(tmp_path)

    proc = subprocess.run([sys.executable, '-c', 'print("ran unprotected")'],
                          env=env, capture_output=True, check=False)

    assert proc.returncode != 0, proc.stdout
    assert b'ran unprotected' not in proc.stdout, proc.stdout
    assert b'refusing to start without' in proc.stderr, proc.stderr
