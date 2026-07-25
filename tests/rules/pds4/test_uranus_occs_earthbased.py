import pytest

import pdsfile.pds4file as pds4file

from tests.rules.support import (
    PDS4_TEST_RESULTS_DIR as TEST_RESULTS_DIR,
    associated_abspaths_test,
    opus_products_test,
)
from pdsfile.pds4file.rules.uranus_occs_earthbased import PRIMARY_FILESPEC_LIST


@pytest.mark.parametrize(
    'input_path,expected',
    [
        # rings
        ('bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_delta_egress_100m.xml',
         'uranus_occs_earthbased/opus_products/u0_kao_91cm_734nm_radius_delta_egress_100m.txt'),
        # atmosphere
        ('bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_ingress.xml',
         'uranus_occs_earthbased/opus_products/u0_kao_91cm_734nm_counts-v-time_atmos_ingress.txt'),
        # global
        ('bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_ingress_100m.xml',
         'uranus_occs_earthbased/opus_products/u0_kao_91cm_734nm_radius_equator_ingress_100m.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds4file.Pds4File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    'input_path,category,expected',
    [
        ('bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
         'bundles',
         'uranus_occs_earthbased/associated_abspaths/bundles_u0_kao_91cm_734nm_counts-v-time_atmos_egress.txt'),
        ('bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
         'diagrams',
         'uranus_occs_earthbased/associated_abspaths/diagrams_u0_kao_91cm_734nm_counts-v-time_atmos_egress.txt'),
        # TODO: when we have index shelf files available, we can test the following cases
        # ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_100m.xml',
        #  'metadata',
        #  [
        #     'metadata/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/uranus_occ_u0_kao_91cm_rings_index.csv/u0_kao_91cm_734nm_radius_alpha_egress_100m',
        #  ]),
        # ('uranus_occs_earthbased/data/rings/u0_kao_91cm_734nm_radius_delta_ingress_1000m.tab',
        #  'metadata',
        #  [
        #     'metadata/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/uranus_occ_u0_kao_91cm_rings_index.csv/u0_kao_91cm_734nm_radius_delta_ingress_1000ms',
        #  ]),
        # ('uranus_occs_earthbased/data/global/u0_kao_91cm_734nm_radius_equator_ingress_500m.tab',
        #  'metadata',
        #  [
        #     'metadata/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/uranus_occ_u0_kao_91cm_global_index.csv/u0_kao_91cm_734nm_radius_equator_ingress_500m',
        #  ]),
        # ('uranus_occs_earthbased/data/global/u0_kao_91cm_734nm_radius_equator_egress_100m.xml',
        #  'metadata',
        #  [
        #     'metadata/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/uranus_occ_u0_kao_91cm_global_index.csv/u0_kao_91cm_734nm_radius_equator_egress_100m',
        #  ]),
        # TODO: add test case for documents when correct document files are added
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
        # Temporarily, before writing OPUS products code, comment out remaining code below

        # Gather all the associated OPUS products
        #product_dict = test_pdsf.opus_products()
        #product_pds4files = []
        #for pdsf_lists in product_dict.values():
        #    for pdsf_list in pdsf_lists:
        #        product_pdsfiles += pdsf_list

        # Filter out the metadata/documents products and format files
        #product_pdsfiles = [pdsf for pdsf in product_pdsfiles
        #                         if pdsf.voltype_ != 'metadata/'
        #                         and pdsf.voltype_ != 'documents/']
        #product_pdsfiles = [pdsf for pdsf in product_pdsfiles
        #                         if pdsf.extension.lower() != '.fmt']

        # Gather the set of absolute paths
        #opus_id_abspaths = set()
        #for pdsf in product_pdsfiles:
        #    opus_id_abspaths.add(pdsf.abspath)

        #for pdsf in product_pdsfiles:
            # Every version is in the product set
        #    for version_pdsf in pdsf.all_versions().values():
        #        assert version_pdsf.abspath in opus_id_abspaths

            # Every viewset is in the product set
        #    for viewset in pdsf.all_viewsets.values():
        #        for viewable in viewset.viewables:
        #            assert viewable.abspath in opus_id_abspaths

            # Every associated product is in the product set except metadata
        #    for category in ('volumes', 'calibrated', 'previews'):
        #        for abspath in pdsf.associated_abspaths(category):
        #            assert abspath in opus_id_abspaths

##########################################################################################
