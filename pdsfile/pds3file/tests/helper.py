##########################################################################################
# pds3file/tests/helper.py
#
# Helper functions for tests on pds3file
##########################################################################################

import os
import pdsfile.pds3file as pds3file
from pdsfile.general_helper import (PDS_HOLDINGS_DIR,
                                    get_pdsfiles_for_class,
                                    get_pdsgroups_for_class,
                                    instantiate_target_pdsfile_for_class,
                                    opus_products_test_for_class)

def instantiate_target_pdsfile(path, is_abspath=True):
    return instantiate_target_pdsfile_for_class(path, pds3file.Pds3File,
                                                PDS_HOLDINGS_DIR, is_abspath)

def get_pdsfiles(paths, is_abspath=True):
    return get_pdsfiles_for_class(paths, pds3file.Pds3File, PDS_HOLDINGS_DIR, is_abspath)

def get_pdsgroups(paths_group, is_abspath=True):
    return get_pdsgroups_for_class(paths_group, pds3file.Pds3File,
                                   PDS_HOLDINGS_DIR, is_abspath)

def opus_products_test(input_path, expected):
    return opus_products_test_for_class(input_path, pds3file.Pds3File,
                                        PDS_HOLDINGS_DIR, expected)
