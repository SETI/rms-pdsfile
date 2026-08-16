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
import io
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

    # realpath, not abspath: abspath keeps symlink components, so a path that reaches
    # a protected root through a symlink elsewhere would compare as being outside it.
    return tuple(os.path.realpath(r) for r in raw.split(os.pathsep) if r)


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
        target = os.path.realpath(os.fspath(path))
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


class _Guarded:
    """A write call that refuses targets inside a protected root.

    Deliberately a callable object rather than a function. A plain Python function
    implements the descriptor protocol, so storing one on a class turns it into a
    method and inserts the instance as a first argument; a builtin does not bind that
    way. Replacing a builtin with a function therefore changes the arity of every call
    that reaches it through a class attribute, and the standard library does hold these
    functions on classes -- `pathlib` did exactly that until Python 3.11 removed its
    `_accessor`, and one such caller was enough to break every tool subprocess. The
    interpreters this package supports no longer include that one, so the property is
    kept because the pattern is general rather than because a supported version needs
    it.
    """

    def __init__(self, real, roots, what, args_to_check=(0,)):
        self._real = real
        self._roots = roots
        self._what = what
        self._args_to_check = args_to_check

    def __call__(self, *args, **kwargs):
        for index in self._args_to_check:
            if index < len(args):
                _check(args[index], self._roots, self._what)
        return self._real(*args, **kwargs)


class _GuardedOpen(_Guarded):
    """`open()`, checked only when the mode can create or change the file."""

    def __call__(self, file, mode='r', *args, **kwargs):
        if _WRITE_FLAGS.intersection(mode):
            _check(file, self._roots, self._what)
        return self._real(file, mode, *args, **kwargs)


class _GuardedOsOpen(_Guarded):
    """`os.open()`, checked on the flags rather than a mode string.

    Nothing in the tools calls it directly, but it is the floor every other write
    stands on: a guard that only wraps `open()` is bypassed by one `os.open()` call.
    """

    def __call__(self, path, flags, *args, **kwargs):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC):
            _check(path, self._roots, self._what)
        return self._real(path, flags, *args, **kwargs)


def install():
    """Wrap the write entry points so a protected root cannot be written to.

    Reads are untouched: the tests read the real holdings constantly, to stage their
    source subsets. Only calls that can create or change something are checked, and
    only against the roots named in the environment, so everything outside them --
    the temporary tree, pytest's caches, coverage data -- is unaffected.

    Calling this more than once is harmless: it restores the real entry points before
    wrapping, so re-installing over a different set of roots works and nothing is ever
    wrapped twice.
    """

    roots = _roots()
    uninstall()
    if not roots:
        return

    builtins.open = _GuardedOpen(builtins.open, roots, 'open()')
    # pathlib goes through io.open, which is a separate reference to the same builtin,
    # so patching builtins.open alone leaves Path.write_text() unguarded.
    io.open = _GuardedOpen(io.open, roots, 'io.open()')
    os.open = _GuardedOsOpen(os.open, roots, 'os.open()')
    os.mkdir = _Guarded(os.mkdir, roots, 'mkdir()')
    os.makedirs = _Guarded(os.makedirs, roots, 'makedirs()')
    os.remove = _Guarded(os.remove, roots, 'remove()')
    os.unlink = _Guarded(os.unlink, roots, 'unlink()')
    os.rmdir = _Guarded(os.rmdir, roots, 'rmdir()')
    os.rename = _Guarded(os.rename, roots, 'rename()', args_to_check=(0, 1))
    os.replace = _Guarded(os.replace, roots, 'replace()', args_to_check=(0, 1))


def uninstall():
    """Put the real write entry points back, if this module replaced them.

    Installing is idempotent because it uninstalls first, which also lets a caller
    re-install over a different set of roots -- what the tests of this module do.
    """

    if isinstance(builtins.open, _Guarded):
        builtins.open = builtins.open._real

    if isinstance(io.open, _Guarded):
        io.open = io.open._real

    for name in ('open', 'mkdir', 'makedirs', 'remove', 'unlink', 'rmdir', 'rename',
                 'replace'):
        current = getattr(os, name)
        if isinstance(current, _Guarded):
            setattr(os, name, current._real)


def installed():
    """Report whether the guard is currently in place.

    Returns:
        bool: True if the write entry points are wrapped.
    """

    return isinstance(builtins.open, _Guarded)
