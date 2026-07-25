import pytest

import pdsfile.pds4file as pds4file

from tests.rules.support import (
    PDS4_TEST_RESULTS_DIR as TEST_RESULTS_DIR,
    associated_abspaths_test,
    opus_products_test,
)
from pdsfile.pds4file.rules.cassini_uvis_solarocc_beckerjarmak2023 import PRIMARY_FILESPEC_LIST


@pytest.mark.parametrize(
    ('input_path', 'expected'),
    [
        ('bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2005_159_solar_time_series_ingress.xml',
         'cassini_uvis_solarocc_beckerjarmak2023/opus_products/uvis_euv_2005_159_solar_time_series_ingress.txt'),
        ('bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2008_083_solar_time_series_egress.xml',
         'cassini_uvis_solarocc_beckerjarmak2023/opus_products/uvis_euv_2008_083_solar_time_series_egress.txt'),
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds4file.Pds4File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    ('input_path', 'category', 'expected'),
    [
        ('bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2006_257_solar_time_series_ingress.xml',
         'bundles',
         'cassini_uvis_solarocc_beckerjarmak2023/associated_abspaths/bundles_uvis_euv_2006_257_solar_time_series_ingress.txt'),
        ('bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2008_083_solar_time_series_egress.xml',
         'bundles',
         'cassini_uvis_solarocc_beckerjarmak2023/associated_abspaths/bundles_uvis_euv_2008_083_solar_time_series_egress.txt'),
        ('bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2006_257_solar_time_series_ingress.xml',
         'previews',
         'cassini_uvis_solarocc_beckerjarmak2023/associated_abspaths/previews_uvis_euv_2006_257_solar_time_series_ingress.txt'),
        ('bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2008_083_solar_time_series_egress.xml',
         'previews',
         'cassini_uvis_solarocc_beckerjarmak2023/associated_abspaths/previews_uvis_euv_2008_083_solar_time_series_egress.txt'),
    ]
)

def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds4file.Pds4File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    for logical_path in PRIMARY_FILESPEC_LIST:
        test_pdsf = pds4file.Pds4File.from_logical_path(logical_path)
        opus_id = test_pdsf.opus_id
        opus_id_pdsf = pds4file.Pds4File.from_opus_id(opus_id)
        assert opus_id_pdsf.logical_path == logical_path



##########################################################################################
