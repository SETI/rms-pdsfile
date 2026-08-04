##########################################################################################
# tests/api/test_mixin_import_isolation.py
#
# One rule governs how the mixin modules may import: a mixin module must NOT do
# a module-level `from pdsfile.pdsfile import ...`.
# pdsfile/pdsfile.py imports the mixin modules to build the class, so a top-level
# back-import is a cycle; a method that needs the PdsFile class object uses a
# function-local import inside the method body instead.
#
# Two spellings of the mistake announce themselves: importing PdsFile itself
# raises "cannot import name 'PdsFile' from partially initialized module" and
# fails the whole suite at collection. Importing some OTHER name that pdsfile.py
# has already bound by that point is silent -- the package imports, the suite
# stays green, and the cycle sits there. That silent case is what this module is
# for.
#
# The check is behavioral, not syntactic. An AST walk over import statements has
# to learn every spelling and every nesting -- relative vs absolute, aliased,
# inside try/if/with, inside a class body, inside the else branch of
# if TYPE_CHECKING, inside match/case -- and still cannot see __import__ or
# importlib.import_module. Loading the module and asking sys.modules cannot be
# fooled by any of them.
#
# tests/api/conftest.py marks everything collected here holdings_free, so this
# module also runs in the hosted no-holdings job. Nothing below reads a holdings
# tree.
##########################################################################################

import os
import subprocess
import sys

import pytest

from pdsfile.pdsfile import PdsFile

# Importing any pdsfile submodule normally runs pdsfile/__init__.py, whose
# `from .pds3file import *` pulls in pdsfile.pdsfile -- so a probe that simply
# imported the module would report a back-import for every module, always. The
# probe therefore installs a stub `pdsfile` package: a real ModuleSpec whose
# submodule_search_locations point at the package directory, with no __init__
# executed. Relative imports (from ._path_utils import ...) and absolute
# in-package imports (from pdsfile import pdscache) both still resolve through
# those search locations, so the module under test loads exactly as it would in
# the real package -- only the package __init__'s star-imports are excluded.
_PROBE = '''
import importlib
import importlib.machinery
import importlib.util
import sys

pkg_dir, modname = sys.argv[1], sys.argv[2]

spec = importlib.machinery.ModuleSpec('pdsfile', None, is_package=True)
spec.submodule_search_locations = [pkg_dir]
sys.modules['pdsfile'] = importlib.util.module_from_spec(spec)

importlib.import_module(modname)

print('FILE:' + sys.modules[modname].__file__)
print('CORE_PRESENT:' + str('pdsfile.pdsfile' in sys.modules))
'''


def _mixin_modules():
    """(module name, file) for every mixin base of PdsFile, discovered not listed."""

    out = []
    for base in PdsFile.__bases__:
        if base is object:
            continue
        module = sys.modules[base.__module__]
        out.append((base.__module__, module.__file__))
    return sorted(out)


_MODULES = _mixin_modules()
_IDS = [name.rpartition('.')[2] for name, _ in _MODULES]


def test_the_mixin_modules_are_found():
    # Without this the parametrization below could shrink to nothing and every
    # case would pass by not existing.
    assert len(_MODULES) >= 9, (
        f'expected at least the nine mixin modules, found {_MODULES}')


@pytest.mark.parametrize(('module_name', 'module_file'), _MODULES, ids=_IDS)
def test_a_mixin_module_does_not_import_pdsfile_pdsfile(module_name, module_file):
    """Load one mixin module in a fresh interpreter and require that
    pdsfile.pdsfile did not come with it."""

    # One subprocess per module, deliberately. A single interpreter importing all
    # of them in turn would let the first module's back-import hide every later
    # module's, and would let module A importing module B mask B's own violation.
    # A process that has loaded exactly one of them can do neither.
    # The timeout keeps a module that blocks at import time -- a lock, a socket,
    # a read from stdin -- a failure rather than a hang, in a job that has no
    # other watchdog.
    pkg_dir = os.path.dirname(module_file)
    completed = subprocess.run([sys.executable, '-c', _PROBE, pkg_dir, module_name],
                               capture_output=True, text=True, timeout=60)

    assert completed.returncode == 0, (
        f'importing {module_name} on its own failed, which is what a module-level '
        f'back-import into pdsfile.pdsfile looks like when pdsfile.py has not yet '
        f'bound the name:\n{completed.stdout}{completed.stderr}')

    out = dict(line.split(':', 1) for line in completed.stdout.splitlines()
               if ':' in line)

    # The subprocess must have loaded the same file the parent did; otherwise a
    # stale copy elsewhere on sys.path could answer for it.
    assert out.get('FILE') == module_file, (
        f'the probe loaded {out.get("FILE")!r}, not {module_file!r}')

    assert out.get('CORE_PRESENT') == 'False', (
        f'{module_name} pulls pdsfile.pdsfile into sys.modules at import time. A '
        f'mixin module may not import pdsfile.pdsfile at module level -- '
        f'pdsfile.py imports the mixins, so that is a cycle. Use a '
        f'function-local import inside the method that needs the class object.')

##########################################################################################
