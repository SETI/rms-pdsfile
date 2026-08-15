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


def test_the_guard_does_not_bind_as_a_method(protected):
    """A replacement stored on a class must not become a method.

    Python 3.10's pathlib holds `os.mkdir` on a class and calls
    `self._accessor.mkdir(self, mode)`. A builtin does not bind, but a plain Python
    function does, which inserts the instance as a first argument and changes the
    arity. Replacing the builtin with a function therefore broke every subprocess that
    reached `Path.mkdir` on that interpreter, and passed on 3.11 and later, where the
    accessor no longer exists. This fails if the guard goes back to being a function.
    """

    class Accessor:
        mkdir = os.mkdir

    target = protected.parent / 'work_via_accessor'
    Accessor().mkdir(target, 0o777)
    assert target.is_dir()


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
