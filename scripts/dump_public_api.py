#!/usr/bin/env python3
"""Dump the public API surface of the ``pdsfile`` package to a deterministic manifest.

This is the generator behind the public-API freeze (PR-02 of the modernization
plan, ``plans/2026-07-17-modernization-plan.md``). It records the *names and
kinds* of every public attribute of a fixed set of modules, plus the public
member surface of every class those modules define. It records **names and
kinds only, never values** -- translator tables, dicts, and other data compare
by name alone -- so that the mechanical decomposition of ``pdsfile.py`` into
mixin modules cannot show up as an API change.

The output is byte-reproducible: keys sorted, 2-space indent, trailing newline.
``tests/api/test_api_freeze.py`` compares a fresh ``build_manifest()`` against
the committed ``tests/api/api_manifest.json`` and fails on any unforgiven diff.

Run ``python scripts/dump_public_api.py`` to print the manifest to stdout, or
``python scripts/dump_public_api.py --write`` to (re)write the committed
manifest. The manifest is a frozen contract: do not regenerate it to make a
build pass (see the plan, section 6.4 prohibitions).
"""

import argparse
import importlib
import inspect
import json
import os
import sys

# --- The frozen module set -------------------------------------------------

# Fixed top-level modules. The two ``rules`` packages and their submodules are
# discovered dynamically (see ``_rules_modules``) so the set is deterministic
# across machines without hardcoding the (growing) list of dataset rule files.
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

# Excluded everywhere: test infrastructure and version stamp are not external
# API. ``pdsfile_test_helper`` and the two ``rules/pytest_support.py`` modules
# support this repo's own tests only (ground rule 1 exception); ``_version`` is
# a build artifact. Excluding ``pytest_support`` here also keeps the manifest
# from recording its star-imported ``os``/``re``/``translator``/``pds3file``
# names, whose later removal (PR-08) would otherwise read as an API break.
_EXCLUDED_RULES_STEMS = {'pytest_support', '__init__'}


def _is_excluded_module_ref(value):
    """True if a module-typed attribute points at a module the freeze excludes
    (the ``tests`` subpackages, ``_version``, ``pdsfile_test_helper``, or a
    ``pytest_support``). Such references appear as public attributes only when
    some *other* code (e.g. the test conftest importing
    ``pdsfile.pds3file.tests.helper``) has imported the subpackage, binding its
    name into the parent module. Skipping them keeps the manifest independent of
    what happens to be imported in the process that runs this dumper -- the
    contract is the import-time surface of the frozen module set alone."""
    if not inspect.ismodule(value):
        return False
    name = getattr(value, '__name__', '')
    if not name.startswith('pdsfile.'):
        return False
    return (
        '.tests' in name
        or name.endswith('._version')
        or name.endswith('.pdsfile_test_helper')
        or name.endswith('.pytest_support')
    )

# Path to the hand-maintained list of underscore-prefixed names that a consumer
# is known to import (seeded empty). Resolved relative to this script so the
# dumper works from any CWD.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MANIFEST_PATH = os.path.join(_REPO_ROOT, 'tests', 'api', 'api_manifest.json')
_CONSUMER_PRIVATE_NAMES_PATH = os.path.join(
    _REPO_ROOT, 'tests', 'api', 'consumer_used_private_names.json')


def _rules_modules():
    """Return the sorted list of rule modules: each ``rules`` package's
    ``__init__`` (which holds the shared TranslatorByRegex default tables) plus
    every ``*.py`` under it except ``pytest_support.py``."""
    names = []
    for pkg_name in _RULES_PACKAGES:
        pkg = importlib.import_module(pkg_name)
        names.append(pkg_name)  # the package __init__ itself is public surface
        pkg_dir = os.path.dirname(pkg.__file__)
        for filename in sorted(os.listdir(pkg_dir)):
            if not filename.endswith('.py'):
                continue
            stem = filename[:-len('.py')]
            if stem in _EXCLUDED_RULES_STEMS:
                continue
            names.append(f'{pkg_name}.{stem}')
    return names


def module_set():
    """The full, deterministic list of modules whose public surface is frozen."""
    return list(_TOP_MODULES) + _rules_modules()


# --- Attribute / member classification -------------------------------------

def _attr_kind(obj):
    """Classify a module-level attribute value: class, function, translator,
    module, or data. Order matters -- a Translator is an instance, checked
    after the structural kinds and before the ``data`` catch-all."""
    if inspect.isclass(obj):
        return 'class'
    if inspect.isroutine(obj):  # functions, builtins, methods
        return 'function'
    if inspect.ismodule(obj):
        return 'module'
    if 'Translator' in type(obj).__name__:
        return 'translator'
    return 'data'


def _member_kind(cls, name):
    """Classify a class member via ``inspect.getattr_static`` (never invoking
    descriptors): method, classmethod, staticmethod, property, or data."""
    try:
        static = inspect.getattr_static(cls, name)
    except AttributeError:
        return 'data'
    if isinstance(static, staticmethod):
        return 'staticmethod'
    if isinstance(static, classmethod):
        return 'classmethod'
    if isinstance(static, property):
        return 'property'
    if inspect.isroutine(static):
        return 'method'
    return 'data'


def _signature_of(cls, name):
    """String form of a callable member's signature, or ``<unsignaturable>``."""
    try:
        obj = getattr(cls, name)
    except Exception:  # noqa: BLE001 -- a broken descriptor must not abort the dump
        return '<unsignaturable>'
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return '<unsignaturable>'


def _load_consumer_private_names():
    """Load the (module, name) underscore-prefixed names a consumer imports.

    Seeded empty; entries here are additionally recorded even though they start
    with an underscore."""
    if not os.path.exists(_CONSUMER_PRIVATE_NAMES_PATH):
        return []
    with open(_CONSUMER_PRIVATE_NAMES_PATH) as f:
        data = json.load(f)
    # Accept a list of {"module": ..., "name": ...} records.
    return [(rec['module'], rec['name']) for rec in data]


# --- Manifest construction -------------------------------------------------

def build_manifest():
    """Import the module set and return the public-API manifest as a dict.

    Structure::

        {
          "modules": { "<module>": { "<name>": "<kind>", ... }, ... },
          "classes": { "<module>.<qualname>": {
                          "<member>": {"kind": ..., "signature": ...}, ... }, ... }
        }

    ``signature`` is present only for callable members (method / classmethod /
    staticmethod). Classes are keyed by ``__module__`` + ``__qualname__`` and
    expanded once, so a class reachable under several module names (or via a
    star-import) is not double-counted, and mixin refactoring -- which changes
    only *which* base defines a member -- is invisible here.
    """
    mods = module_set()
    mod_set = set(mods)
    private_names = _load_consumer_private_names()
    private_by_module = {}
    for module_name, attr in private_names:
        private_by_module.setdefault(module_name, set()).add(attr)

    manifest = {'modules': {}, 'classes': {}}
    classes_to_expand = {}  # class_key -> class object

    for module_name in mods:
        module = importlib.import_module(module_name)
        namespace = vars(module)
        wanted = private_by_module.get(module_name, set())
        module_record = {}
        for name, value in namespace.items():
            if name.startswith('_') and name not in wanted:
                continue
            if _is_excluded_module_ref(value):
                continue
            kind = _attr_kind(value)
            module_record[name] = kind
            # Queue classes actually defined within the frozen module set for
            # member expansion (imported stdlib/translator classes are not).
            if kind == 'class' and getattr(value, '__module__', None) in mod_set:
                class_key = f'{value.__module__}.{value.__qualname__}'
                classes_to_expand.setdefault(class_key, value)
        manifest['modules'][module_name] = module_record

    for class_key, cls in classes_to_expand.items():
        member_record = {}
        for name in dir(cls):
            # Only public (non-underscore) class members are frozen. The
            # consumer_used_private_names.json override is intentionally NOT
            # consulted here: it forgives module-level underscore names a
            # consumer *imports*, not a class's underscore internals (which a
            # consumer does not reach into). Extend it to members only if a
            # real consumer ever depends on a private class member.
            if name.startswith('_'):
                continue
            kind = _member_kind(cls, name)
            entry = {'kind': kind}
            if kind in ('method', 'classmethod', 'staticmethod'):
                entry['signature'] = _signature_of(cls, name)
            member_record[name] = entry
        manifest['classes'][class_key] = member_record

    return manifest


def render(manifest):
    """Byte-reproducible JSON: sorted keys, 2-space indent, trailing newline."""
    return json.dumps(manifest, sort_keys=True, indent=2) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true',
                        help=f'write the manifest to {_MANIFEST_PATH} instead of stdout')
    args = parser.parse_args(argv)
    text = render(build_manifest())
    if args.write:
        os.makedirs(os.path.dirname(_MANIFEST_PATH), exist_ok=True)
        with open(_MANIFEST_PATH, 'w') as f:
            f.write(text)
        print(f'wrote {_MANIFEST_PATH}', file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
