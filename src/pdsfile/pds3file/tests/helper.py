##########################################################################################
# pds3file/tests/helper.py
#
# Helper functions for tests on pds3file
##########################################################################################

import os
import pdsfile.pds3file as pds3file

try:
    PDS3_HOLDINGS_DIR = os.environ['PDS3_HOLDINGS_DIR']
except KeyError: # pragma: no cover
    raise KeyError("'PDS3_HOLDINGS_DIR' environment variable not set")

def instantiate_target_pdsfile(path, is_abspath=True):
    if is_abspath:
        TESTFILE_PATH = PDS3_HOLDINGS_DIR + '/' + path
        target_pdsfile = pds3file.Pds3File.from_abspath(TESTFILE_PATH)
    else:
        TESTFILE_PATH = path
        target_pdsfile = pds3file.Pds3File.from_logical_path(TESTFILE_PATH)
    return target_pdsfile
