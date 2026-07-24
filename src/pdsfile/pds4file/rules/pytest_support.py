##########################################################################################
# pds4file/ruless/pytest_support.py
##########################################################################################

import os
from pdsfile.pdsfile_test_helper import (associated_abspaths_test,
                                         instantiate_target_pdsfile,
                                         opus_products_test)
import pdsfile.pds4file as pds4file

# Golden opus/associated-path results moved to the top-level tests/ tree in PR-07
# (tests/golden/full/pds4/); the package dir is src/pdsfile/pds4file, so the repo
# root is three levels up.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(pds4file.__file__),
                                          '..', '..', '..'))
TEST_RESULTS_DIR = os.path.join(_REPO_ROOT, 'tests', 'golden', 'full', 'pds4') + '/'
