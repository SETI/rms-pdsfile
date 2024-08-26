##########################################################################################
# pds3file/rules/pytest_support.py
##########################################################################################

import ast
import os
from pdsfile.pdsfile import abspath_for_logical_path
import pdsfile.pds3file as pds3file
from pathlib import Path
import re
import translator

TEST_RESULTS_DIR = os.path.dirname(pds3file.__file__) + '/test_results/'

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
    patterns = pds3file.Pds3File.abspaths_for_logicals(patterns)

    abspaths = []
    for pattern in patterns:
        abspaths += pds3file.Pds3File.glob_glob(pattern)

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
    patterns = pds3file.Pds3File.abspaths_for_logicals(patterns)

    abspaths = []
    for pattern in patterns:
        abspaths += pds3file.Pds3File.glob_glob(pattern)

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
    patterns = pds3file.Pds3File.abspaths_for_logicals(patterns)

    unmatched = []
    for pattern in patterns:
        abspaths = pds3file.Pds3File.glob_glob(pattern)
        if not abspaths:
            unmatched.append(pattern)

    return unmatched

##########################################################################################
# Dave's test suite helpers
##########################################################################################

def instantiate_target_pdsfile(path, is_abspath=True):
    if is_abspath:
        TESTFILE_PATH = abspath_for_logical_path(path, pds3file.Pds3File)
        target_pdsfile = pds3file.Pds3File.from_abspath(TESTFILE_PATH)
    else:
        TESTFILE_PATH = path
        target_pdsfile = pds3file.Pds3File.from_logical_path(TESTFILE_PATH)
    return target_pdsfile

def get_pdsfiles(paths, holdings_dir, is_abspath=True):
    pdsfiles_arr = []
    if is_abspath:
        for path in paths:
            TESTFILE_PATH = abspath_for_logical_path(path, pds3file.Pds3File)
            target_pdsfile = pds3file.Pds3File.from_abspath(TESTFILE_PATH)
            pdsfiles_arr.append(target_pdsfile)
    else:
        for path in paths:
            TESTFILE_PATH = path
            target_pdsfile = pds3file.Pds3File.from_logical_path(TESTFILE_PATH)
            pdsfiles_arr.append(target_pdsfile)
    return pdsfiles_arr

def opus_products_test(
    input_path, expected, update=False, is_abspath=True
):
    target_pdsfile = instantiate_target_pdsfile(input_path, is_abspath)
    results = target_pdsfile.opus_products()

    res = {}
    for prod_category, prod_list in results.items():
        pdsf_list = []
        for pdsf_li in prod_list:
            for pdsf in pdsf_li:
                pdsf_list.append(pdsf.logical_path)
        res[prod_category] = pdsf_list

    expected_data = read_or_update_golden_copy(res, expected, update)
    if not expected_data:
        return

    for key in results:
        assert key in expected_data, f'Extra key: {key}'
    for key in expected_data:
        assert key in results, f'Missing key: {key}'
    for key in results:
        result_paths = []       # flattened list of logical paths
        for pdsfiles in results[key]:
            result_paths += pds3file.Pds3File.logicals_for_pdsfiles(pdsfiles)
        for path in result_paths:
            assert path in expected_data[key], f'Extra file under key {key}: {path}'
        for path in expected_data[key]:
            assert path in result_paths, f'Missing file under key {key}: {path}'

def versions_test(input_path, expected, is_abspath=True):
    target_pdsfile = instantiate_target_pdsfile(input_path, is_abspath)
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

def associated_abspaths_test(input_path, category, expected, update=False):
    target_pdsfile = instantiate_target_pdsfile(input_path)
    res = target_pdsfile.associated_abspaths(
          category=category)

    result_paths = []
    result_paths += pds3file.Pds3File.logicals_for_abspaths(res)

    expected_data = read_or_update_golden_copy(result_paths, expected, update)
    if not expected_data:
        return

    assert len(result_paths) != 0
    for path in result_paths:
        assert path in expected_data, f'Extra file: {path}'
    for path in expected_data:
        assert path in result_paths, f'Missing file: {path}'

def read_or_update_golden_copy(data, path, update):
    """Return data if the operation is reading from the golden copy of test results.
    Return 0 if the operation is updating the golden copy

    Keyword arguments:
        data   -- the data to be written into the golden copy
        path   -- the file path of the golden copy under test results directory
        udpate -- the flag used to determine if the golden copy should be updated
    """

    data_file_path = Path(TEST_RESULTS_DIR + path)
    # Create the golden copy by using the current output
    if update or not data_file_path.exists():
        # create the directory to store the golden copy if it doesn't exist.
        os.makedirs(os.path.dirname(data_file_path), exist_ok=True)

        # write the associated_abspaths output to the file.
        with open(data_file_path, 'w') as f:
            f.write(repr(data))
        print('\nCreate the golden copy', path)
        return 0

    with open(data_file_path, 'r') as f:
        expected_data = f.read()
        expected_data = ast.literal_eval(expected_data)
        return expected_data
