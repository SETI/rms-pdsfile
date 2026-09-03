##########################################################################################
# tests/core/test_preload_bundleset_boundary.py
#
# The preload walk stops below the bundle set: it visits every category directory and
# every bundle set, constructs their children so that every bundle is cached, and reads
# nothing deeper. What bounds it is the bundle-set test each directory answers, so these
# tests measure the walk and the answers together.
#
# The tree is built here rather than taken from a holdings root, so it can hold the two
# cases that separate the answers: a directory below the bundle set that no bundle-name
# pattern matches, which is not a bundle set and must not be walked, and a bundle-set
# level AAREADME, which is a bundle-set file and must still say so.
#
# The preload runs in a subprocess. It writes the class-level cache, keyed by logical
# path, and a test session has the real holdings preloaded into that same cache, so an
# in-process call could resolve a temporary-tree path back to a real one.
##########################################################################################

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.holdings_free

# tests/core/test_preload_bundleset_boundary.py -> repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]

PROBE_TIMEOUT = 120

# Preload the tree named by argv[1], recording every directory listed on the way, then
# report the bundle-set answers for the paths named by argv[2:]. Both halves come from
# one preload because the answers are what the walk branched on.
_PROBE = """
import json, sys
from pdsfile import Pds4File

root = sys.argv[1]
listed = []
_os_listdir = Pds4File.os_listdir.__func__
Pds4File.os_listdir = classmethod(
    lambda cls, abspath: (listed.append(abspath), _os_listdir(cls, abspath))[1])

Pds4File.preload(root)

facts = {}
for logical_path in sys.argv[2:]:
    pdsf = Pds4File.from_logical_path(logical_path)
    facts[logical_path] = {'interior': pdsf.interior,
                           'is_bundleset': pdsf.is_bundleset,
                           'is_bundleset_dir': pdsf.is_bundleset_dir,
                           'is_bundleset_file': pdsf.is_bundleset_file,
                           'is_bundle_dir': pdsf.is_bundle_dir}

print(json.dumps({'listed': sorted({p[len(root):].strip('/') for p in listed}),
                  'facts': facts}))
"""

# cassini_iss is a name Pds4File.BUNDLESET_REGEX accepts and cassini_iss_cruise one
# BUNDLENAME_REGEX accepts, so the tree below is a legal one. "superseded" is neither,
# and it is the shape that issue #163 was about: a real bundle set holds one, and its
# contents are further copies of bundles.
TREE_DIRS = [
    'bundles/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx',
    'bundles/cassini_iss/superseded/cassini_iss_cruise_v1.0/data_raw/130xxxxxxx',
]
TREE_FILES = ['bundles/cassini_iss/AAREADME.txt']

PROBED_PATHS = [
    'bundles',
    'bundles/cassini_iss',
    'bundles/cassini_iss/AAREADME.txt',
    'bundles/cassini_iss/cassini_iss_cruise',
    'bundles/cassini_iss/cassini_iss_cruise/data_raw',
    'bundles/cassini_iss/superseded',
    'bundles/cassini_iss/superseded/cassini_iss_cruise_v1.0',
]


@pytest.fixture(scope='module')
def probe(tmp_path_factory):
    """Build the tree, preload it once in a subprocess, and return what it reported."""

    # The directory must be named pds4-holdings: that is the name Pds4File finds in an
    # absolute path to cut the logical path out of it.
    root = tmp_path_factory.mktemp('boundary') / 'pds4-holdings'
    for relpath in TREE_DIRS:
        (root / relpath).mkdir(parents=True)
    for relpath in TREE_FILES:
        (root / relpath).write_text('Read me first.\n')

    env = dict(os.environ)
    # PYTHONPATH names this checkout's src/, so the subprocess runs the code these
    # tests belong to rather than whatever an editable install happens to point at.
    env['PYTHONPATH'] = str(REPO_ROOT / 'src')
    env['PDS4_HOLDINGS_DIR'] = str(root)
    for name in ('PDS3_HOLDINGS_DIR', 'PDS_LOG_ROOT', 'PDSFILE_TEST_HOLDINGS',
                 'PDSFILE_TEST_DATA_DIR'):
        env.pop(name, None)

    argv = [sys.executable, '-c', _PROBE, str(root)]
    argv += PROBED_PATHS
    proc = subprocess.run(argv, env=env, capture_output=True, timeout=PROBE_TIMEOUT,
                          check=False)
    stdout = proc.stdout.decode('utf-8', errors='replace')
    stderr = proc.stderr.decode('utf-8', errors='replace')
    assert proc.returncode == 0, f'probe failed ({proc.returncode}):\n{stderr}'

    return json.loads(stdout)


##########################################################################################
# How deep the walk goes
##########################################################################################
class TestPreloadWalkDepth:

    def test_the_walk_stops_below_the_bundle_set(self, probe):
        # The category directory and the bundle set, and nothing under either. Listing
        # bundles/cassini_iss is what caches every bundle; listing anything below it is
        # the defect, and an unmatched name used to carry the walk to the leaves.
        assert probe['listed'] == ['bundles', 'bundles/cassini_iss']


##########################################################################################
# What the walk branches on
##########################################################################################
class TestBundlesetBoundary:

    @pytest.mark.parametrize(
        ('logical_path', 'expected'),
        [
            ('bundles',
             {'interior': '', 'is_bundleset': False, 'is_bundleset_dir': False,
              'is_bundleset_file': False, 'is_bundle_dir': False}),
            ('bundles/cassini_iss',
             {'interior': '', 'is_bundleset': True, 'is_bundleset_dir': True,
              'is_bundleset_file': False, 'is_bundle_dir': False}),
            # A file beside the bundles, not below one: still a bundle-set file.
            ('bundles/cassini_iss/AAREADME.txt',
             {'interior': 'AAREADME.txt', 'is_bundleset': True,
              'is_bundleset_dir': False, 'is_bundleset_file': True,
              'is_bundle_dir': False}),
            ('bundles/cassini_iss/cassini_iss_cruise',
             {'interior': '', 'is_bundleset': False, 'is_bundleset_dir': False,
              'is_bundleset_file': False, 'is_bundle_dir': True}),
            ('bundles/cassini_iss/cassini_iss_cruise/data_raw',
             {'interior': 'data_raw', 'is_bundleset': False,
              'is_bundleset_dir': False, 'is_bundleset_file': False,
              'is_bundle_dir': False}),
            # The unmatched directory and what it holds: interior to the bundle set,
            # and no part of it a bundle set.
            ('bundles/cassini_iss/superseded',
             {'interior': 'superseded', 'is_bundleset': False,
              'is_bundleset_dir': False, 'is_bundleset_file': False,
              'is_bundle_dir': False}),
            ('bundles/cassini_iss/superseded/cassini_iss_cruise_v1.0',
             {'interior': 'superseded/cassini_iss_cruise_v1.0',
              'is_bundleset': False, 'is_bundleset_dir': False,
              'is_bundleset_file': False, 'is_bundle_dir': False}),
        ]
    )
    def test_bundleset_answers(self, probe, logical_path, expected):
        assert probe['facts'][logical_path] == expected

##########################################################################################
