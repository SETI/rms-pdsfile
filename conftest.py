##########################################################################################
# pds-webtools/conftest.py
#
# Configuration & setup before running tests on pds4file
##########################################################################################

import os
from pdsfile import (Pds3File,
                     Pds4File)
from pdsfile.pds3file.tests.helper import PDS3_HOLDINGS_DIR
from pdsfile.pds4file.tests.helper import PDS4_HOLDINGS_DIR
import pdslogger
import pytest

##########################################################################################
# Setup before all tests
##########################################################################################
def pytest_addoption(parser):
    parser.addoption("--mode", action="store")
    parser.addoption("--update", action="store_true")

def turn_on_logger(filename):
    LOGGER = pdslogger.PdsLogger(filename)
    Pds3File.set_logger(LOGGER)
    Pds4File.set_logger(LOGGER)

@pytest.fixture(scope='session', autouse=True)
def setup(request):
    mode = request.config.option.mode
    if mode == 's':
        Pds3File.use_shelves_only(True)
        Pds4File.use_shelves_only(True)
    elif mode == 'ns':
        Pds3File.use_shelves_only(False)
        Pds4File.use_shelves_only(False)
    else: # pragma: no cover
        Pds3File.use_shelves_only(True)
        Pds4File.use_shelves_only(False)

    # turn_on_logger("test_log.txt")
    Pds3File.preload(PDS3_HOLDINGS_DIR)
    Pds4File.preload(PDS4_HOLDINGS_DIR)
