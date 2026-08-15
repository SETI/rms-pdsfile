##########################################################################################
# tests/holdings_maintenance/readonly_roots.py
#
# Refuse, at the moment of the call, any write whose target lies inside a real holdings
# root. The maintenance tools write -- archives, checksum files, shelves, logs -- and are
# meant to write only into the temporary tree the fixtures build. Nothing enforced that,
# and a test that resolved a path through Pds3File or Pds4File got whichever root the
# class was preloaded with: a second preload() does not re-root an already-preloaded
# class, so a test that built its own tree and preloaded it still resolved into the real
# holdings and wrote there. Observation 3999 has the measurements.
#
# This replaces walking the roots before and after. A walk costs time proportional to the
# size of the holdings -- 150 ms against a limited copy, and these trees are expected to
# grow -- while an interception costs one string comparison per write and does not care
# how large the tree is.
#
# The roots to protect arrive in PDSFILE_READONLY_ROOTS, so that a tool subprocess
# installs the same guard from sitecustomize.py without the test having to know how the
# tool is launched.
##########################################################################################

import builtins
import os

ENV_VAR = 'PDSFILE_READONLY_ROOTS'

# open() modes that can create or change a file. 'r' alone is the only one that cannot.
_WRITE_FLAGS = frozenset('wxa+')


class ReadOnlyHoldingsError(PermissionError):
    """Raised when a test, or a tool a test started, writes into a real holdings root."""


def _roots():
    """Return the protected roots, as absolute paths with no trailing separator.

    Returns:
        tuple: the roots named in the environment, empty if none are.
    """

    raw = os.environ.get(ENV_VAR, '')

    return tuple(os.path.abspath(r) for r in raw.split(os.pathsep) if r)


def _check(path, roots, what):
    """Raise if a path lies inside a protected root.

    Args:
        path: The path the caller is about to write to.
        roots: The protected roots.
        what: The operation, named in the error message.

    Raises:
        ReadOnlyHoldingsError: if the path is inside a protected root.
    """

    if not roots or path is None:
        return

    try:
        target = os.path.abspath(os.fspath(path))
    except TypeError:                       # a file descriptor, not a path
        return

    for root in roots:
        if target == root or target.startswith(root + os.sep):
            raise ReadOnlyHoldingsError(
                f'{what} would write into a real holdings root, which the tests treat '
                f'as read-only: {target}. Tools under test must write only into the '
                f'temporary tree the fixtures build. This usually means a path was '
                f'resolved through a PdsFile class that is still preloaded with the '
                f'real root.')


def install():
    """Wrap the write entry points so a protected root cannot be written to.

    Reads are untouched: the tests read the real holdings constantly, to stage their
    source subsets. Only calls that can create or change something are checked, and
    only against the roots named in the environment, so everything outside them --
    the temporary tree, pytest's own caches, coverage data -- is unaffected.

    Calling this more than once is harmless; the second call is ignored.
    """

    roots = _roots()
    if not roots or getattr(builtins.open, '_pdsfile_guarded', False):
        return

    real_open = builtins.open
    real_mkdir = os.mkdir
    real_makedirs = os.makedirs
    real_rename = os.rename
    real_replace = os.replace
    real_remove = os.remove
    real_unlink = os.unlink
    real_rmdir = os.rmdir

    def guarded_open(file, mode='r', *args, **kwargs):
        if _WRITE_FLAGS.intersection(mode):
            _check(file, roots, 'open()')
        return real_open(file, mode, *args, **kwargs)

    guarded_open._pdsfile_guarded = True

    def guarded_mkdir(path, *args, **kwargs):
        _check(path, roots, 'mkdir()')
        return real_mkdir(path, *args, **kwargs)

    def guarded_makedirs(name, *args, **kwargs):
        _check(name, roots, 'makedirs()')
        return real_makedirs(name, *args, **kwargs)

    def guarded_rename(src, dst, *args, **kwargs):
        _check(dst, roots, 'rename()')
        _check(src, roots, 'rename()')
        return real_rename(src, dst, *args, **kwargs)

    def guarded_replace(src, dst, *args, **kwargs):
        _check(dst, roots, 'replace()')
        _check(src, roots, 'replace()')
        return real_replace(src, dst, *args, **kwargs)

    def guarded_remove(path, *args, **kwargs):
        _check(path, roots, 'remove()')
        return real_remove(path, *args, **kwargs)

    def guarded_unlink(path, *args, **kwargs):
        _check(path, roots, 'unlink()')
        return real_unlink(path, *args, **kwargs)

    def guarded_rmdir(path, *args, **kwargs):
        _check(path, roots, 'rmdir()')
        return real_rmdir(path, *args, **kwargs)

    builtins.open = guarded_open
    os.mkdir = guarded_mkdir
    os.makedirs = guarded_makedirs
    os.rename = guarded_rename
    os.replace = guarded_replace
    os.remove = guarded_remove
    os.unlink = guarded_unlink
    os.rmdir = guarded_rmdir
