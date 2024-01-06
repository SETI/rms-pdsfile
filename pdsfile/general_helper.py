##########################################################################################
# pdsfile/general_helper.py
# Helper functions being used in tests, the parent class & both pds3 & pds4 subclasses
##########################################################################################
import os

##########################################################################################
# Configurations
##########################################################################################
try:
    PDS_HOLDINGS_DIR = os.environ['PDS_HOLDINGS_DIR']
except KeyError: # pragma: no cover
    raise KeyError("Missing 'PDS_HOLDINGS_DIR' in the environment variable")

try:
    PDS4_HOLDINGS_DIR = os.environ['PDS4_HOLDINGS_DIR']
except KeyError: # pragma: no cover
    # TODO: update this when we know the actual path of pds4 holdings on the webserver
    raise KeyError("Missing 'PDS4_HOLDINGS_DIR' in the environment variable")

PDS4_BUNDLES_DIR = f'{PDS4_HOLDINGS_DIR}/bundles'

##########################################################################################
# For tests under /tests
##########################################################################################
def instantiate_target_pdsfile_for_class(path, cls, holdings_dir, is_abspath=True):
    if is_abspath:
        TESTFILE_PATH = holdings_dir + '/' + path
        target_pdsfile = cls.from_abspath(TESTFILE_PATH)
    else:
        TESTFILE_PATH = path
        target_pdsfile = cls.from_logical_path(TESTFILE_PATH)
    return target_pdsfile

def get_pdsfiles_for_class(paths, cls, holdings_dir, is_abspath=True):
    pdsfiles_arr = []
    if is_abspath:
        for path in paths:
            TESTFILE_PATH = holdings_dir + '/' +  path
            target_pdsfile = cls.from_abspath(TESTFILE_PATH)
            pdsfiles_arr.append(target_pdsfile)
    else:
        for path in paths:
            TESTFILE_PATH = path
            target_pdsfile = cls.from_logical_path(TESTFILE_PATH)
            pdsfiles_arr.append(target_pdsfile)
    return pdsfiles_arr

def opus_products_test_for_class(
    input_path, cls, holdings_dir, expected, is_abspath=True
):
    target_pdsfile = instantiate_target_pdsfile_for_class(input_path, cls,
                                                          holdings_dir, is_abspath)
    results = target_pdsfile.opus_products()
    # Note that messages are more useful if extra values are identified before
    # missing values. That's because extra items are generally more diagnostic
    # of the issue at hand.
    for key in results:
        assert key in expected, f'Extra key: {key}'
    for key in expected:
        assert key in results, f'Missing key: {key}'
    for key in results:
        result_paths = []       # flattened list of logical paths
        for pdsfiles in results[key]:
            result_paths += cls.logicals_for_pdsfiles(pdsfiles)
        for path in result_paths:
            assert path in expected[key], f'Extra file under key {key}: {path}'
        for path in expected[key]:
            assert path in result_paths, f'Missing file under key {key}: {path}'

def versions_test_for_class(input_path, cls, holdings_dir, expected, is_abspath=True):
    target_pdsfile = instantiate_target_pdsfile_for_class(input_path, cls,
                                                          holdings_dir, is_abspath)
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

##########################################################################################
# For tests under rules
##########################################################################################
def translate_first_for_class(trans, path, cls):
    """Return the logical paths of "first" files found using given translator on path.

    Keyword arguments:
        trans -- a translator instance
        path  -- a file path
        cls   -- the class calling the other methods inside the function
    """

    patterns = trans.first(path)
    if not patterns:
        return []

    if isinstance(patterns, str):
        patterns = [patterns]

    patterns = [p for p in patterns if p]       # skip empty translations
    patterns = cls.abspaths_for_logicals(patterns)

    abspaths = []
    for pattern in patterns:
        abspaths += cls.glob_glob(pattern)

    return abspaths

def translate_all_for_class(trans, path, cls):
    """Return logical paths of all files found using given translator on path.

    Keyword arguments:
        trans -- a translator instance
        path  -- a file path
        cls   -- the class calling the other methods inside the function
    """

    patterns = trans.all(path)
    if not patterns:
        return []

    if isinstance(patterns, str):
        patterns = [patterns]

    patterns = [p for p in patterns if p]       # skip empty translations
    patterns = cls.abspaths_for_logicals(patterns)

    abspaths = []
    for pattern in patterns:
        abspaths += cls.glob_glob(pattern)

    return abspaths

def unmatched_patterns_for_class(trans, path, cls):
    """Return a list of all translated patterns that did not find a matching path in the
    file system.

    Keyword arguments:
        trans -- a translator instance
        path  -- a file path
        cls   -- the class calling the other methods inside the function
    """

    patterns = trans.all(path)
    patterns = [p for p in patterns if p]       # skip empty translations
    patterns = cls.abspaths_for_logicals(patterns)

    unmatched = []
    for pattern in patterns:
        abspaths = cls.glob_glob(pattern)
        if not abspaths:
            unmatched.append(pattern)

    return unmatched
