"""Public-API freeze test.

Regenerates the public-API manifest with ``scripts/dump_public_api.py`` and
asserts it is identical to the committed ``api_manifest.json``, modulo the
forgiveness rules in ``manifest_allowlist.json``. This is the compatibility
contract for the whole modernization rewrite (PR-02 of
``plans/2026-07-17-modernization-plan.md``): the public surface reachable via
``import pdsfile`` must not change except through pre-approved allowlist entries.

The test needs no holdings data. (Until PR-09 makes the root ``conftest.py``
skip-aware, *collecting* the suite still imports that conftest, which requires
the holdings env vars; the self-hosted gate and local runs set them. From PR-14
the hermetic CI runs this test with no holdings at all.)

The fresh manifest is generated in a **child subprocess** (a clean interpreter
running ``scripts/dump_public_api.py``), never in this process. This is
deliberate: the frozen contract is the *import-time* public surface, and
``PdsFile.preload()`` -- run by the session-autouse fixture in the root
conftest whenever holdings are present -- injects extra runtime class
attributes into the live classes. Regenerating in-process would pick those up
and make the test pass hermetically (no preload) but fail on the self-hosted
holdings gate (preload). A fresh subprocess imports ``pdsfile`` without the
conftest or any preload, so the result is identical in both environments and
matches how the committed manifest was produced.

Do not edit ``api_manifest.json``, ``manifest_allowlist.json``, or this file /
``scripts/dump_public_api.py`` to make a diff disappear -- see section 6.4
prohibitions in the plan. Allowlist entries are added only under the two
pre-approved forgiveness categories (section 6.1) or with new owner approval.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DUMPER_PATH = _REPO_ROOT / 'scripts' / 'dump_public_api.py'
_MANIFEST_PATH = _REPO_ROOT / 'tests' / 'api' / 'api_manifest.json'
_ALLOWLIST_PATH = _REPO_ROOT / 'tests' / 'api' / 'manifest_allowlist.json'


def _fresh_manifest():
    """Generate the manifest in a clean child interpreter (no conftest, no
    preload) so the result reflects the import-time surface only."""
    result = subprocess.run(
        [sys.executable, str(_DUMPER_PATH)],
        capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _diff_manifests(old, new):
    """Yield the differences between two manifests as ``(path, change, kind)``
    tuples. ``path`` is ``"<location>::<name>"`` (location = module name or
    class key); ``change`` is ``added`` / ``removed`` / ``changed``; ``kind`` is
    the attribute/member kind involved (for ``changed``, the new kind)."""
    for section in ('modules', 'classes'):
        old_sec = old.get(section, {})
        new_sec = new.get(section, {})
        for location in sorted(set(old_sec) | set(new_sec)):
            old_members = old_sec.get(location, {})
            new_members = new_sec.get(location, {})
            for name in sorted(set(old_members) | set(new_members)):
                in_old = name in old_members
                in_new = name in new_members
                if in_old and not in_new:
                    yield (f'{location}::{name}', 'removed', _kind_of(old_members[name]))
                elif in_new and not in_old:
                    yield (f'{location}::{name}', 'added', _kind_of(new_members[name]))
                elif old_members[name] != new_members[name]:
                    yield (f'{location}::{name}', 'changed', _kind_of(new_members[name]))


def _kind_of(entry):
    """A manifest value is either a bare kind string (module attrs) or a dict
    with a ``kind`` key (class members)."""
    if isinstance(entry, dict):
        return entry.get('kind')
    return entry


def _is_forgiven(path, kind, allowlist):
    """True if a diff at ``path`` with ``kind`` is covered by an exact record or
    a category predicate in the allowlist."""
    location, _, name = path.partition('::')
    for record in allowlist.get('exact', []):
        if record['module'] == location and record['name'] == name:
            return True
    for predicate in allowlist.get('categories', []):
        if predicate.get('kind') not in (None, '*', kind):
            continue
        if re.search(predicate['pattern'], path):
            return True
    return False


def test_public_api_frozen():
    fresh = _fresh_manifest()
    committed = json.loads(_MANIFEST_PATH.read_text())
    allowlist = json.loads(_ALLOWLIST_PATH.read_text())

    unforgiven = [
        (path, change, kind)
        for path, change, kind in _diff_manifests(committed, fresh)
        if not _is_forgiven(path, kind, allowlist)
    ]

    if unforgiven:
        lines = [f'  {change:8} {kind or "?":12} {path}' for path, change, kind in unforgiven]
        raise AssertionError(
            'Public API surface changed vs tests/api/api_manifest.json '
            f'({len(unforgiven)} unforgiven diff(s)).\n'
            'If this change is intended and pre-approved, add an entry to '
            'tests/api/manifest_allowlist.json (never edit the manifest, the '
            'dumper, or this test to hide a diff -- see plan section 6.4).\n'
            + '\n'.join(lines))
