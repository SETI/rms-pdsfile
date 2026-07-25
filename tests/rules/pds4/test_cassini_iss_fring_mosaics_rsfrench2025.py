import pytest

import pdsfile.pds4file as pds4file

from tests.rules.support import (
    PDS4_TEST_RESULTS_DIR as TEST_RESULTS_DIR,
    associated_abspaths_test,
    opus_products_test,
)
from pdsfile.pds4file.rules.cassini_iss_fring_mosaics_rsfrench2025 import PRIMARY_FILESPEC_LIST


# TODO: When cassini_iss_fring_mosaics_rsfrench2025 bundle is available, remove pytestmark
# and enable these rule unit tests.
pytestmark = pytest.mark.skip(reason='cassini_iss_fring_mosaics_rsfrench2025 rule tests skipped')

@pytest.mark.parametrize(
    ('input_path', 'expected'),
    [
        ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data_mosaic/iosic_276rb_complitb4001_si/iosic_276rb_complitb4001_si_mosaic.lblx',
         'cassini_iss_fring_mosaics_rsfrench2025/opus_products/iosic_276rb_complitb4001_si_mosaic.txt'),
        ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data_mosaic/iss_006ri_lphrlfmov001_prime/iss_006ri_lphrlfmov001_prime_mosaic.lblx',
         'cassini_iss_fring_mosaics_rsfrench2025/opus_products/iss_006ri_lphrlfmov001_prime_mosaic.txt'),
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds4file.Pds4File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    ('input_path', 'category', 'expected'),
    [
        ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data_mosaic/iosic_276rb_complitb4001_si/iosic_276rb_complitb4001_si_mosaic.lblx',
         'bundles',
         'cassini_iss_fring_mosaics_rsfrench2025/associated_abspaths/bundles_iosic_276rb_complitb4001_si_mosaic.txt'),
        ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data_mosaic/iosic_276rb_complitb4001_si/iosic_276rb_complitb4001_si_mosaic.lblx',
         'previews',
         'cassini_iss_fring_mosaics_rsfrench2025/associated_abspaths/previews_iosic_276rb_complitb4001_si_mosaic.txt'),
        ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data_mosaic/iss_006ri_lphrlfmov001_prime/iss_006ri_lphrlfmov001_prime_mosaic.lblx',
         'bundles',
         'cassini_iss_fring_mosaics_rsfrench2025/associated_abspaths/bundles_iss_006ri_lphrlfmov001_prime_mosaic.txt'),
        ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data_mosaic/iss_006ri_lphrlfmov001_prime/iss_006ri_lphrlfmov001_prime_mosaic.lblx',
         'previews',
         'cassini_iss_fring_mosaics_rsfrench2025/associated_abspaths/previews_iss_006ri_lphrlfmov001_prime_mosaic.txt'),
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
