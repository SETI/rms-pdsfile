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
import pprint

def instantiate_target_pdsfile(cls, path, is_abspath=True):
    """Return the pdsfile instance of the given path.

    Args:
        cls: The class that is used to instantiate the pdsfile instance.
        path: The file path of targeted pdsfile.
        is_abspath: The flag used to determine if the given path is an abspath.

    Returns:
        A pdsfile instance.
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
    Return 0 if the operation is updating the golden copy.

    Args:
        data: The data to be written into the golden copy.
        path: The file path of the golden copy under test results directory.
        update: The flag used to determine if the golden copy should be updated.

    Returns:
        The data from the golden copy. Return 0 if we only write and didn't read the
        golden copy.
    """

    path = Path(path)
    # Create the golden copy by using the current output if the update param is given
    # or the golden copy doesn't exist.
    if update or not path.exists():
        # create the directory to store the golden copy if it doesn't exist.
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # write the output to the file.
        write_data_to_file(data, path)
        return 0

    return read_file(path)

def read_file(path):
    """Return data from the read file.

    Args:
        path: The file path to be read.

    Returns:
        The data of the file.
    """

    with open(path, 'r') as f:
        expected_data = f.read()
        expected_data = ast.literal_eval(expected_data)
        return expected_data

def write_data_to_file(data, path):
    """Write data to the file of the given path.

    Args:
        data: The data to be written to the file.
        path: The file path to be written.
    """

    with open(path, 'w') as f:
        pprint.pp(data, stream=f)
    print('\nWrite the golden copy ', path)

def opus_products_test(cls, input_path, expected, update=False):
    """Run opus products test.

    Args:
        cls: The class that runs the test, either Pds3File or Pds4File.
        input_path: The file path of targeted pdsfile.
        expected: The file path of the golden copy under test results directory.
        update: The flag used to determine if the golden copy should be updated.
    """
    target_pdsfile = instantiate_target_pdsfile(cls, input_path)
    results = target_pdsfile.opus_products()

    res = {}
    # This will make sure keys in results is sorted by 'group' and then 'priority'
    ordered_res = {k: results[k] for k in sorted(results)}
    for prod_category, prod_list in ordered_res.items():
        pdsf_list = []
        for pdsf_li in prod_list:
            for pdsf in pdsf_li:
                pdsf_list.append(pdsf.logical_path)

        # sort the list before storing to the dictionary, this will make sure we don't
        # udpate the golden copy if the list before sorting has a different order.
        pdsf_list.sort()
        res[prod_category] = pdsf_list

    expected_data = read_or_update_golden_copy(res, expected, update)
    if not expected_data:
        return

    for key in ordered_res:
        assert key in expected_data, f'Extra key: {key}'
    for key in expected_data:
        assert key in ordered_res, f'Missing key: {key}'
    for key in ordered_res:
        result_paths = []       # flattened list of logical paths
        for pdsfiles in ordered_res[key]:
            result_paths += cls.logicals_for_pdsfiles(pdsfiles)
        for path in result_paths:
            assert path in expected_data[key], f'Extra file under key {key}: {path}'
        for path in expected_data[key]:
            assert path in result_paths, f'Missing file under key {key}: {path}'

def associated_abspaths_test(cls, input_path, category, expected, update=False):
    """Run associated abspaths test.

    Args:
        cls: The class that runs the test, either Pds3File or Pds4File.
        input_path: The file path of targeted pdsfile.
        category: The category of the associated asbpath.
        expected: The file path of the golden copy under test results directory.
        update: The flag used to determine if the golden copy should be updated.
    """

    target_pdsfile = instantiate_target_pdsfile(cls, input_path)
    res = target_pdsfile.associated_abspaths(
          category=category)

    result_paths = []
    result_paths += cls.logicals_for_abspaths(res)

    # sort the list of paths before we compare or write the golden copy, this will sure
    # we don't update the golden copy if the output before sorting has a different order.
    result_paths.sort()

    expected_data = read_or_update_golden_copy(result_paths, expected, update)
    if not expected_data:
        return

    assert len(result_paths) != 0
    for path in result_paths:
        assert path in expected_data, f'Extra file: {path}'
    for path in expected_data:
        assert path in result_paths, f'Missing file: {path}'
