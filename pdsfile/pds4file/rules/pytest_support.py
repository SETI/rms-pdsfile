##########################################################################################
# pds4file/ruless/pytest_support.py
##########################################################################################

import os
from pdsfile.pdsfile_test_helper import (associated_abspaths_test,
                                         instantiate_target_pdsfile,
                                         opus_products_test)
import pdsfile.pds4file as pds4file

TEST_RESULTS_DIR = os.path.dirname(pds4file.__file__) + '/test_results/'
