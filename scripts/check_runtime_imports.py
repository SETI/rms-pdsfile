#!/usr/bin/env python3
"""Import the entire public ``pdsfile`` module surface with runtime deps only.

Run inside a venv built from ``pip install .`` **without** any optional extras
(see ``scripts/clean_install_check.sh``). It imports ``pdsfile`` and every module
in the frozen public set -- the fixed top modules plus every rule module under
both ``rules`` packages. If any *runtime* module still imports a dev-only
dependency (e.g. ``pytest`` via a leftover ``from .pytest_support import *`` or a
top-level ``import pytest``), that module fails to import here and this script
exits non-zero.

This is the only gate that catches a runtime-dependency leak: the normal test
runs and ``pip install -e ".[dev]"`` always have pytest present, so they cannot
detect a runtime module that still imports a dev-only dependency; this gate can.
Keep it permanent.

Standalone by design: it imports only ``pdsfile`` and the stdlib, never anything
under ``scripts/`` or ``tests/`` (which are not installed in the clean venv).
"""

import importlib
import pkgutil
import sys

# The fixed top modules of the frozen public set (kept in sync with
# scripts/dump_public_api.py::_TOP_MODULES).
_TOP_MODULES = [
    'pdsfile',
    'pdsfile.pdsfile',
    'pdsfile.pdscache',
    'pdsfile.pdsviewable',
    'pdsfile.preload_and_cache',
    'pdsfile.pds3file',
    'pdsfile.pds4file',
]

_RULES_PACKAGES = ['pdsfile.pds3file.rules', 'pdsfile.pds4file.rules']

# Stems never part of the runtime surface (mirror dump_public_api's exclusions).
# There is no runtime ``pytest_support`` module; guard anyway so a stray copy
# cannot reintroduce a pytest import into this gate.
_EXCLUDED_RULES_STEMS = {'pytest_support', '__init__'}


def _module_set():
    names = list(_TOP_MODULES)
    for pkg_name in _RULES_PACKAGES:
        pkg = importlib.import_module(pkg_name)
        names.append(pkg_name)
        for info in pkgutil.iter_modules(pkg.__path__):
            if info.name in _EXCLUDED_RULES_STEMS:
                continue
            names.append(f'{pkg_name}.{info.name}')
    return names


def main():
    failures = []
    for name in _module_set():
        try:
            importlib.import_module(name)
        except Exception as exc:  # report every import failure
            failures.append((name, f'{type(exc).__name__}: {exc}'))

    if failures:
        print('CLEAN-INSTALL IMPORT CHECK FAILED — runtime-dependency leak:',
              file=sys.stderr)
        for name, err in failures:
            print(f'  {name}: {err}', file=sys.stderr)
        return 1

    print('clean-install import check passed: '
          'all runtime modules import with no dev extras')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
