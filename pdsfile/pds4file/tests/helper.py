##########################################################################################
# pds4file/tests/helper.py
#
# Helper functions for tests on pds4file
##########################################################################################

import os
import pdsfile.pds4file as pds4file

try:
    PDS4_HOLDINGS_DIR = os.environ['PDS4_HOLDINGS_DIR']
except KeyError: # pragma: no cover
    # TODO: update this when we know the actual path of pds4 holdings on the webserver
    raise KeyError("'PDS4_HOLDINGS_DIR' environment variable not set")

PDS4_BUNDLES_DIR = f'{PDS4_HOLDINGS_DIR}/bundles'

def instantiate_target_pdsfile(path, is_abspath=True):
    if is_abspath:
        TESTFILE_PATH = PDS4_BUNDLES_DIR + '/' + path
        target_pdsfile = pds4file.Pds4File.from_abspath(TESTFILE_PATH)
    else:
        TESTFILE_PATH = path
        target_pdsfile = pds4file.Pds4File.from_logical_path(TESTFILE_PATH)
    return target_pdsfile
