##########################################################################################
# pds4file/tests/helper.py
#
# Helper functions for tests on pds4file
##########################################################################################

import os
import pdsfile.pds4file as pds4file

from pdsfile.general_helper import (PDS4_BUNDLES_DIR,
                                    instantiate_target_pdsfile_for_class)

def instantiate_target_pdsfile(path, is_abspath=True):
    return instantiate_target_pdsfile_for_class(path, pds4file.Pds4File,
                                                PDS4_BUNDLES_DIR, is_abspath)
