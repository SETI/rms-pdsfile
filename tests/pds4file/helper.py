##########################################################################################
# pds4file/tests/helper.py
#
# Helper functions for tests on pds4file
##########################################################################################

import pdsfile.pds4file as pds4file
from tests.support.holdings import resolve_holdings

# Holdings root for the selected session flavor (see tests.support.holdings). When
# no holdings are available this is a placeholder and every test is skipped, so it
# is never dereferenced.
PDS4_HOLDINGS_DIR = resolve_holdings().pds4_root
PDS4_BUNDLES_DIR = f'{PDS4_HOLDINGS_DIR}/bundles'

def instantiate_target_pdsfile(path, is_abspath=True):
    if is_abspath:
        testfile_path = PDS4_BUNDLES_DIR + '/' + path
        target_pdsfile = pds4file.Pds4File.from_abspath(testfile_path)
    else:
        testfile_path = path
        target_pdsfile = pds4file.Pds4File.from_logical_path(testfile_path)
    return target_pdsfile
