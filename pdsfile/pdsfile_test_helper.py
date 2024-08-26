##########################################################################################
# pdsfile/pdsfile_test_helper.py
# Store general pdsfile test functions or helpers that can be applied to both Pds3File and
# Pds4File testings. This will help us avoid maintaining the same testing functions at
# different places.
##########################################################################################

from .pdsfile import abspath_for_logical_path
import ast
import os
from pathlib import Path

def instantiate_target_pdsfile(cls, path, is_abspath=True):
    """Return the pdsfile instance of the given path

    Keyword arguments:
        cls        -- the class that is used to instantiate the pdsfile instance
        path       -- the file path of targeted pdsfile
        is_abspath -- the flag used to determine if the given path is an abspath
    """

    if is_abspath:
        TESTFILE_PATH = abspath_for_logical_path(path, cls)
        target_pdsfile = cls.from_abspath(TESTFILE_PATH)
    else:
        TESTFILE_PATH = path
        target_pdsfile = cls.from_logical_path(TESTFILE_PATH)
    return target_pdsfile

def read_or_update_golden_copy(data, path, update):
    """Return data if the operation is reading from the golden copy of test results.
    Return 0 if the operation is updating the golden copy

    Keyword arguments:
        data   -- the data to be written into the golden copy
        path   -- the file path of the golden copy under test results directory
        update -- the flag used to determine if the golden copy should be updated
    """

    path = Path(path)
    # Create the golden copy by using the current output
    if update or not path.exists():
        # create the directory to store the golden copy if it doesn't exist.
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # write the associated_abspaths output to the file.
        with open(path, 'w') as f:
            f.write(repr(data))
        print('\nCreate the golden copy', path)
        return 0

    with open(path, 'r') as f:
        expected_data = f.read()
        expected_data = ast.literal_eval(expected_data)
        return expected_data

def opus_products_test(cls, input_path, expected, update=False):
    """Run opus products test

    Keyword arguments:
        cls          -- the class that runs the test, either Pds3File or Pds4File
        input_path   -- the file path of targeted pdsfile
        expected     -- the file path of the golden copy under test results directory
        update       -- the flag used to determine if the golden copy should be updated
    """
    target_pdsfile = instantiate_target_pdsfile(cls, input_path)
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
            result_paths += cls.logicals_for_pdsfiles(pdsfiles)
        for path in result_paths:
            assert path in expected_data[key], f'Extra file under key {key}: {path}'
        for path in expected_data[key]:
            assert path in result_paths, f'Missing file under key {key}: {path}'

def associated_abspaths_test(cls, input_path, category, expected, update=False):
    """Run associated abspaths test

    Keyword arguments:
        cls          -- the class that runs the test, either Pds3File or Pds4File
        input_path   -- the file path of targeted pdsfile
        category     -- the category of the associated asbpath
        expected     -- the file path of the golden copy under test results directory
        update       -- the flag used to determine if the golden copy should be updated
    """

    target_pdsfile = instantiate_target_pdsfile(cls, input_path)
    res = target_pdsfile.associated_abspaths(
          category=category)

    result_paths = []
    result_paths += cls.logicals_for_abspaths(res)

    expected_data = read_or_update_golden_copy(result_paths, expected, update)
    if not expected_data:
        return

    assert len(result_paths) != 0
    for path in result_paths:
        assert path in expected_data, f'Extra file: {path}'
    for path in expected_data:
        assert path in result_paths, f'Missing file: {path}'
