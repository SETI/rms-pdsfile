##########################################################################################
# pds4file/ruless/pytest_support.py
##########################################################################################

import ast
import os
from pdsfile.pdsfile_test_helper import (associated_abspaths_test,
                                         instantiate_target_pdsfile,
                                         opus_products_test)
import pdsfile.pds4file as pds4file
import translator
import re

TEST_RESULTS_DIR = os.path.dirname(pds4file.__file__) + '/test_results/'

def translate_first(trans, path):
    """Return the logical paths of "first" files found using given translator on path.

    Keyword arguments:
        trans -- a translator instance
        path  -- a file path
    """

    patterns = trans.first(path)
    if not patterns:
        return []

    if isinstance(patterns, str):
        patterns = [patterns]

    patterns = [p for p in patterns if p]       # skip empty translations
    patterns = pds4file.Pds4File.abspaths_for_logicals(patterns)

    abspaths = []
    for pattern in patterns:
        abspaths += pds4file.Pds4File.glob_glob(pattern)

    return abspaths

def translate_all(trans, path):
    """Return logical paths of all files found using given translator on path.

    Keyword arguments:
        trans -- a translator instance
        path  -- a file path
    """

    patterns = trans.all(path)
    if not patterns:
        return []

    if isinstance(patterns, str):
        patterns = [patterns]

    patterns = [p for p in patterns if p]       # skip empty translations
    patterns = pds4file.Pds4File.abspaths_for_logicals(patterns)

    abspaths = []
    for pattern in patterns:
        abspaths += pds4file.Pds4File.glob_glob(pattern)

    return abspaths

def unmatched_patterns(trans, path):
    """Return a list of all translated patterns that did not find a matching path in the
    file system.

    Keyword arguments:
        trans -- a translator instance
        path  -- a file path
    """

    patterns = trans.all(path)
    patterns = [p for p in patterns if p]       # skip empty translations
    patterns = pds4file.Pds4File.abspaths_for_logicals(patterns)

    unmatched = []
    for pattern in patterns:
        abspaths = pds4file.Pds4File.glob_glob(pattern)
        if not abspaths:
            unmatched.append(pattern)

    return unmatched

##########################################################################################
# Dave's test suite helpers
##########################################################################################

def versions_test(input_path, expected, is_abspath=True):
    target_pdsfile = instantiate_target_pdsfile(pds4file.Pds4File, input_path, is_abspath)
    res = target_pdsfile.all_versions()
    keys = list(res.keys())
    keys.sort(reverse=True)
    for key in keys:
        assert key in expected, f'"{key}" not expected'
        assert res[key].logical_path == expected[key], \
               f'value mismatch at "{key}": {expected[key]}'
    keys = list(expected.keys())
    keys.sort(reverse=True)
    for key in keys:
        assert key in res, f'"{key}" missing'
