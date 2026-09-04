##########################################################################################
# pds3file/tests/helper.py
#
# Helper functions for tests on pds3file
##########################################################################################

import pdsfile.pds3file as pds3file
from tests.support.holdings import resolve_holdings

# Holdings root for the selected session flavor (see tests.support.holdings). When
# no holdings are available this is a placeholder and every test is skipped, so it
# is never dereferenced.
PDS3_HOLDINGS_DIR = resolve_holdings().pds3_root

def instantiate_target_pdsfile(path, is_abspath=True):
    if is_abspath:
        testfile_path = PDS3_HOLDINGS_DIR + '/' + path
        target_pdsfile = pds3file.Pds3File.from_abspath(testfile_path)
    else:
        testfile_path = path
        target_pdsfile = pds3file.Pds3File.from_logical_path(testfile_path)
    return target_pdsfile
