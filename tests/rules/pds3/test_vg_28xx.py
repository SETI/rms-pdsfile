import pytest

import pdsfile.pds3file as pds3file

from tests.rules.support import (
    PDS3_TEST_RESULTS_DIR as TEST_RESULTS_DIR,
    associated_abspaths_test,
    opus_products_test,
)


@pytest.mark.parametrize(
    'input_path,expected',
    [
        # VG_2801
        ('volumes/VG_28xx/VG_2801/EASYDATA/KM000_2/PS1P0107.TAB',
         'VG_28xx/opus_products/PS1P0107.txt'),
        ('volumes/VG_28xx/VG_2801/EASYDATA/KM000_1/PU1P01DE.TAB',
         'VG_28xx/opus_products/PU1P01DE.txt'),
        # VG_2802
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/US1F01.TAB',
         'VG_28xx/opus_products/US1F01.txt'),
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/UU1F01EE.TAB',
         'VG_28xx/opus_products/UU1F01EE.txt'),
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/UN1F01.TAB',
         'VG_28xx/opus_products/UN1F01.txt'),
        # VG_2803
        ('volumes/VG_28xx/VG_2803/S_RINGS/EASYDATA/KM000_2/RS1P2X07.LBL',
         'VG_28xx/opus_products/RS1P2X07.txt'),
        ('volumes/VG_28xx/VG_2803/U_RINGS/EASYDATA/KM00_2/RU1P2X4I.TAB',
         'VG_28xx/opus_products/RU1P2X4I.txt'),
        # VG_2810
        ('volumes/VG_28xx/VG_2810/DATA/IS2_P0001_V01_KM002.TAB',
         'VG_28xx/opus_products/IS2_P0001_V01_KM002.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    'input_path,category,expected',
    [
        ('volumes/VG_28xx/VG_2801/EASYDATA/KM000_2/PS1P0107.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_PS1P0107.txt'),
        ('volumes/VG_28xx/VG_2801/EASYDATA/KM000_2/PU1P01DE.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_PU1P01DE.txt'),
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/US1F01.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_US1F01.txt'),
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/UU1F01EE.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_UU1F01EE.txt'),
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/UN1F01.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_UN1F01.txt'),
        ('volumes/VG_28xx/VG_2803/S_RINGS/EASYDATA/KM000_2/RS1P2X07.LBL',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_RS1P2X07.txt'),
        ('volumes/VG_28xx/VG_2803/U_RINGS/EASYDATA/KM00_2/RU1P2X4I.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_RU1P2X4I.txt'),
        ('volumes/VG_28xx/VG_2810/DATA/IS2_P0001_V01_KM002.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_IS2_P0001_V01_KM002.txt'),
    ]
)
def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds3file.Pds3File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    TESTS = [
        'VG_2803/U_RINGS/EASYDATA/KM00_25/RU4P2XEI.TAB',
        'VG_2801/EASYDATA/KM000_1/PU1P01LI.TAB',
        'VG_2802/EASYDATA/FILTER01/UN1F01.TAB',
        'VG_2802/EASYDATA/FILTER01/US3F01.TAB',
        'VG_2803/S_RINGS/EASYDATA/KM002_5/RS3P2S.TAB',
        'VG_2803/U_RINGS/EASYDATA/KM00_25/RU4P2XEI.TAB',
        'VG_2810/DATA/IS1_P0001_V01_KM002.TAB',
    ]

    for filepath in TESTS:
        logical_path = 'volumes/VG_28xx/' + filepath
        test_pdsf = pds3file.Pds3File.from_logical_path(logical_path)
        opus_id = test_pdsf.opus_id
        opus_id_pdsf = pds3file.Pds3File.from_opus_id(opus_id)
        assert opus_id_pdsf.logical_path == logical_path
