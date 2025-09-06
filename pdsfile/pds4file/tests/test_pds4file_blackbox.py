##########################################################################################
# pds4file/tests/test_pds4file_blackbox.py
# Blackbox tests for pds4file
##########################################################################################

import os
import pdsfile.pds4file as pds4file
from pdsfile import pdsviewable
import pytest

from .helper import (PDS4_BUNDLES_DIR,
                     instantiate_target_pdsfile)
PDS4_HOLDINGS_NAME = 'pds4-holdings'

##########################################################################################
# Blackbox tests for pds4file.py
##########################################################################################
class TestPds4FileBlackBox:
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.img',
            #  'co-iss-n1308947228'),
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947880n.xml',
            #  'co-iss-n1308947880'),
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947440w.img',
            #  'co-iss-w1308947440'),
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947440w.img',
            #  'co-iss-w1308947440'),
            # ('cassini_iss/cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947440w-full.png',
            #  'co-iss-w1308947440'),
            # ('cassini_iss/cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947880n-full.xml',
            #  'co-iss-n1308947880'),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308946681_xxx/1308946681_002.qub',
            #  'co-vims-v1308946681_002'),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947235.qub',
            #  'co-vims-v1308947235'),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947009_xxx/1308947009_002.qub',
            #  'co-vims-v1308947009_002'),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947715.xml',
            #  'co-vims-v1308947715'),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947926_xxx/1308947926_008.qub',
            #  'co-vims-v1308947926_008'),
            # ('cassini_vims/cassini_vims_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947235-full.png',
            #  'co-vims-v1308947235'),
            # ('cassini_vims/cassini_vims_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947079_xxx/1308947079_001-full.xml',
            #  'co-vims-v1308947079_001'),
            # ('cassini_vims/cassini_vims_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947009_xxx/1308947009_002-full.png',
            #  'co-vims-v1308947009_002'),
            # ('cassini_vims/cassini_vims_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947715-full.png',
            #  'co-vims-v1308947715'),
            # cassini_uvis_solarocc_beckerjarmak2023
            ('cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2005_159_solar_time_series_ingress.tab',
             'co-uvis-occ-2005-159-sun-i'),
            ('cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2008_083_solar_time_series_egress.xml',
             'co-uvis-occ-2008-083-sun-e'),
            ('cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/supplemental/uvis_euv_2008_083_solar_time_series_egress_supplement.tab',
             'co-uvis-occ-2008-083-sun-e'),
            #  uranus_occs_earthbased
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
             'kao0m91-vis-occ-1977-069-u0-uranus-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_ingress.tab',
             'kao0m91-vis-occ-1977-069-u0-uranus-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_egress_100m.xml',
             'kao0m91-vis-occ-1977-069-u0-ringpl-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_ingress_1000m.tab',
             'kao0m91-vis-occ-1977-069-u0-ringpl-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_egress_500m.xml',
             'kao0m91-vis-occ-1977-069-u0-ringpl-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_alpha_ingress_100m.xml',
             'kao0m91-vis-occ-1977-069-u0-alpha-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_alpha_ingress_500m.tab',
             'kao0m91-vis-occ-1977-069-u0-alpha-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.tab',
             'kao0m91-vis-occ-1977-069-u0-alpha-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_beta_egress_1000m.xml',
             'kao0m91-vis-occ-1977-069-u0-beta-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_beta_ingress_100m.tab',
             'kao0m91-vis-occ-1977-069-u0-beta-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_beta_ingress_500m.xml',
             'kao0m91-vis-occ-1977-069-u0-beta-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_delta_ingress_500m.tab',
             'kao0m91-vis-occ-1977-069-u0-delta-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_delta_ingress_100m.xml',
             'kao0m91-vis-occ-1977-069-u0-delta-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_delta_egress_1000m.xml',
             'kao0m91-vis-occ-1977-069-u0-delta-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_epsilon_ingress_1000m.xml',
             'kao0m91-vis-occ-1977-069-u0-epsilon-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_epsilon_egress_500m.tab',
             'kao0m91-vis-occ-1977-069-u0-epsilon-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_epsilon_egress_100m.xml',
             'kao0m91-vis-occ-1977-069-u0-epsilon-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_eta_egress_500m.tab',
             'kao0m91-vis-occ-1977-069-u0-eta-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_eta_ingress_1000m.xml',
             'kao0m91-vis-occ-1977-069-u0-eta-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_eta_egress_100m.xml',
             'kao0m91-vis-occ-1977-069-u0-eta-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_five_egress_500m.xml',
             'kao0m91-vis-occ-1977-069-u0-five-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_five_egress_100m.tab',
             'kao0m91-vis-occ-1977-069-u0-five-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_five_ingress_1000m.tab',
             'kao0m91-vis-occ-1977-069-u0-five-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_four_egress_1000m.tab',
             'kao0m91-vis-occ-1977-069-u0-four-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_four_ingress_100m.xml',
             'kao0m91-vis-occ-1977-069-u0-four-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_four_ingress_500m.xml',
             'kao0m91-vis-occ-1977-069-u0-four-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_gamma_ingress_500m.tab',
             'kao0m91-vis-occ-1977-069-u0-gamma-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_gamma_egress_1000m.xml',
             'kao0m91-vis-occ-1977-069-u0-gamma-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_gamma_ingress_100m.tab',
             'kao0m91-vis-occ-1977-069-u0-gamma-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_six_ingress_100m.xml',
             'kao0m91-vis-occ-1977-069-u0-six-i'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_six_egress_1000m.tab',
             'kao0m91-vis-occ-1977-069-u0-six-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_six_egress_500m.tab',
             'kao0m91-vis-occ-1977-069-u0-six-e'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_six_ingress_100m.xml',
             'kao0m91-vis-occ-1977-069-u0-six-i'),
        ]
    )
    def test_opus_id(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.opus_id
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm',
             f'{PDS4_BUNDLES_DIR}/uranus_occs_earthbased/uranus_occ_u0_kao_91cm'),
            #  ('cassini_iss/cassini_iss_cruise',
            #  f'{PDS4_BUNDLES_DIR}/cassini_iss/cassini_iss_cruise'),
            #  ('cassini_vims/cassini_vims_cruise',
            #  f'{PDS4_BUNDLES_DIR}/cassini_vims/cassini_vims_cruise'),
        ]
    )
    def test_abspath(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.abspath
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
           ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.xml',
           'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.xml'),
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.img',
            # 'bundles/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.img'),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308946681_xxx/1308946681_002.qub',
            # 'bundles/cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308946681_xxx/1308946681_002.qub'),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947235.qub',
            # 'bundles/cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947235.qub'),
        ]
    )
    def test_logical_path(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.logical_path
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.xml',
             True),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/non-existent-filename.txt',
             False),
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
            # True),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947235.xml',
            # True),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947009_xxx/1308947009_002.qub',
            # True),
    ]
    )
    def test_exists(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.exists
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('uranus_occs_earthbased/',
             False),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm',
             True),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/bundle.xml',
             False),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
             False),
            # ('cassini_iss',
            #  ''), # bundlesets currently have empty string instead of False
            # ('cassini_iss/cassini_iss_cruise',
            #  True),
            # ('cassini_iss/cassini_iss_cruise/bundle.xml',
            #  False),
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.img',
            #  False),
            # ('cassini_vims',
            #  ''), # bundlesets currently have empty string instead of False
            # ('cassini_vims/cassini_vims_cruise',
            #  True),
            # ('cassini_vims/cassini_vims_cruise/bundle.xml',
            #  False),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947235.qub',
            #  False),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947926_xxx/1308947926_008.xml',
            #  False),
        ]
    )
    def test_is_bundle(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_bundle
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm',
             True), # This test fails with `ValueError: Illegal bundle set directory "": bundles`, because of match failure with BUNDLE_SET_PLUS_REGEX_I on line 3254 of pds4file.py
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/browse',
             False),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/xml_schema/collection_xml_schema.csv',
             False),
            ('uranus_occs_earthbased',
             False),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/bundle.xml',
             False),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
             False),
            ('uranus_occs_earthbased/',
             False),
            # ('cassini_iss',
            #  ''), # bundlesets currently have empty string instead of False
            # ('cassini_iss/cassini_iss_cruise',
            #  True),
            # ('cassini_iss/cassini_iss_cruise/browse',
            #  False),
            # ('cassini_iss/cassini_iss_cruise/xml_schema/collection_xml_schema.csv',
            #  False),
            # ('cassini_iss/cassini_iss_cruise',
            #  True),
            # ('cassini_iss/cassini_iss_cruise/bundle.xml',
            #  False),
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.img',
            #  False),
            # ('cassini_iss/cassini_iss_cruise/',
            #  True),
            # ('cassini_vims',
            #  ''), # bundlesets currently have empty string instead of False
            # ('cassini_vims/cassini_vims_cruise',
            #  True),
            # ('cassini_vims/cassini_vims_cruise/calibration',
            #  False),
            # ('cassini_vims/cassini_vims_cruise/xml_schema/collection_xml_schema.csv',
            #  False),
            # ('cassini_vims/cassini_vims_cruise',
            #  True),
            # ('cassini_vims/cassini_vims_cruise/bundle.xml',
            #  False),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947926_xxx/1308947926_008.qub',
            #  False),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx//1308947715.xml',
            #  False),
            # ('cassini_vims/cassini_vims_cruise/',
            #  True),
        ]
    )
    def test_is_bundle_dir(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_bundle_dir
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.xml',
             False),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/bundle.xml',
             False),
            #  ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.img',
            #  False),
            #  ('cassini_iss/cassini_iss_cruise/bundle.xml',
            #  False),
            #  ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947926_xxx/1308947926_008.qub',
            #  False),
            #  ('cassini_vims/cassini_vims_cruise/bundle.xml',
            #  False),
        ]
    )
    def test_is_bundle_file(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_bundle_file
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('uranus_occs_earthbased',
             True),
            ('uranus_occs_earthbased/',
             True),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/bundle.xml',
             False),
            # ('cassini_iss',
            #  True),
            # ('cassini_vims/',
            #  True),
            # ('cassini_iss/cassini_iss_cruise/bundle.xml',
            #  False),
            # ('cassini_iss/cassini_iss_cruise/',
            #  False),
            # ('cassini_vims/cassini_vims_cruise',
            #  False),
      ]
    )
    def test_is_bundleset(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_bundleset
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('uranus_occs_earthbased',
             True),
            ('uranus_occs_earthbased/',
             True),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/bundle.xml',
             False),
            # ('cassini_vims',
            #  True),
            # ('cassini_iss/',
            #  True),
            # ('cassini_iss/cassini_iss_cruise/bundle.xml',
            #  False),
            # ('cassini_iss/cassini_iss_cruise',
            #  False),
            # ('cassini_vims/cassini_vims_cruise',
            #  False),
        ]
    )
    def test_is_bundleset_dir(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_bundleset_dir
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('uranus_occs_earthbased/',
             'uranus_occs_earthbased'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm',
             'uranus_occs_earthbased'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/bundle.xml',
             'uranus_occs_earthbased'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_ingress.tab',
             'uranus_occs_earthbased'),
            # ('cassini_iss/',
            #  'cassini_iss'),
            # ('cassini_iss/cassini_iss_cruise',
            #  'cassini_iss'),
            # ('cassini_iss/cassini_iss_cruise/bundle.xml',
            #  'cassini_iss'),
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.img',
            #  'cassini_iss'),
            # ('cassini_vims/',
            #  'cassini_vims'),
            # ('cassini_vims/cassini_vims_cruise',
            #  'cassini_vims'),
            # ('cassini_vims/cassini_vims_cruise/bundle.xml',
            #  'cassini_vims'),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947926_xxx/1308947926_008.qub',
            #  'cassini_vims'),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947235.qub',
            #  'cassini_vims'),
        ]
    )
    def test_bundleset(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.bundleset
        assert res == expected


    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # expected bundles for uranus are coming from staging server
            # /volumes/pdsdata-admin/pds4-holdings/bundles/uranus_occs_earthbased
            ('uranus_occs_earthbased/',
             ['checksums_uranus_occs_earthbased',
              'superseded',
              'uranus_occ_support',
              'uranus_occ_u11_ctio_400cm',
              'uranus_occ_u23_ctio_400cm',
              'uranus_occ_u149_lowell_180cm',
              'uranus_occ_u138_palomar_508cm',
              'uranus_occ_u36_sso_390cm',
              'uranus_occ_u12_eso_360cm',
              'uranus_occ_u15_mso_190cm',
              'uranus_occ_u0_kao_91cm',
              'uranus_occ_u36_sso_230cm',
              'uranus_occ_u14_ctio_400cm',
              'uranus_occ_u12_lco_250cm',
              'uranus_occ_u138_hst_fos',
              'uranus_occ_u23_teide_155cm',
              'uranus_occ_u14_eso_104cm',
              'uranus_occ_u102a_irtf_320cm',
              'uranus_occ_u9539_ctio_400cm',
              'uranus_occ_u14_lco_250cm',
              'uranus_occ_u14_lco_100cm',
              'uranus_occ_u103_eso_220cm',
              'uranus_occ_u14_opmt_200cm',
              'uranus_occ_u14_opmt_106cm',
              'uranus_occ_u5_lco_250cm',
              'uranus_occ_u13_sso_390cm',
              'uranus_occ_u2_teide_155cm',
              'uranus_occ_u9_lco_250cm',
              'uranus_occ_u103_palomar_508cm',
              'uranus_occ_u23_mcdonald_270cm',
              'uranus_occ_u25_ctio_400cm',
              'uranus_occ_u83_irtf_320cm',
              'uranus_occ_u36_maunakea_380cm',
              'uranus_occ_u28_irtf_320cm',
              'uranus_occ_u14_teide_155cm',
              'uranus_occ_u25_palomar_508cm',
              'uranus_occ_u36_irtf_320cm',
              'uranus_occ_u137_irtf_320cm',
              'uranus_occ_u25_mcdonald_270cm',
              'uranus_occ_u12_ctio_400cm',
              'uranus_occ_u16_palomar_508cm',
              'uranus_occ_u149_irtf_320cm',
              'uranus_occ_u34_irtf_320cm',
              'uranus_occ_u65_irtf_320cm',
              'uranus_occ_u0201_palomar_508cm',
              'uranus_occ_u1052_irtf_320cm',
              'uranus_occ_u36_ctio_400cm',
              'uranus_occ_u134_saao_188cm',
              'uranus_occ_u144_caha_123cm',
              'uranus_occ_u17b_saao_188cm',
              'uranus_occ_u137_hst_fos',
              'uranus_occ_u14_ctio_150cm',
              'uranus_occ_u144_saao_188cm',
              'uranus_occ_u102b_irtf_320cm',
              'uranus_occ_u84_irtf_320cm']),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/bundle.xml',
             []),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
             []),
            # ('cassini_iss/',
            #  ['cassini_iss_cruise']),
            # ('cassini_iss/cassini_iss_cruise',
            #  ['browse_raw', 'bundle.xml', 'context', 'data_raw', 'document','xml_schema']),
            # ('cassini_iss/cassini_iss_cruise/bundle.xml',
            #  []),
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
            #  []),
            # ('cassini_vims/',
            #  ['bundleset_member_index.csv', 'cassini_vims_cruise']),
            # ('cassini_vims/cassini_vims_cruise',
            #  ['browse_raw', 'bundle.xml', 'bundle_member_index.csv', 'calibration', 'context', 'data_raw', 'document', 'xml_schema']),
            # ('cassini_vims/cassini_vims_cruise/bundle.xml',
            #  []),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308946681_xxx/1308946681_002.qub',
            #  []),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/13089xxxxx/1308947235.xml',
            #  []),
        ]
    )
    def test_childnames(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.childnames
        assert res.sort() == expected.sort()

    @pytest.mark.parametrize(
    'input_path,expected',
        [
            # ('cassini_iss/cassini_iss_cruise',
            #  f'{PDS4_BUNDLES_DIR}/cassini_iss/cassini_iss_cruise'),
            # ('cassini_iss_cruise',
            #  f'{PDS4_BUNDLES_DIR}/cassini_iss/cassini_iss_cruise'),
            # ('cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947228n-full.xml',
            #  f'{PDS4_BUNDLES_DIR}/cassini_iss/cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947228n-full.xml'),
            # ('cassini_iss/cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947228n-full.xml',
            #  f'{PDS4_BUNDLES_DIR}/cassini_iss/cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947228n-full.xml'),
            # ('cassini_vims/cassini_vims_cruise',
            #  f'{PDS4_BUNDLES_DIR}/cassini_vims/cassini_vims_cruise'),
            # ('cassini_vims_cruise',
            #  f'{PDS4_BUNDLES_DIR}/cassini_vims/cassini_vims_cruise'),
            # ('cassini_vims_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308946681_xxx/1308946681_001-full.xml',
            #  f'{PDS4_BUNDLES_DIR}/cassini_vims/cassini_vims_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308946681_xxx/1308946681_001-full.xml'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm',
             f'{PDS4_BUNDLES_DIR}/uranus_occs_earthbased/uranus_occ_u0_kao_91cm'),
            ('uranus_occ_u0_kao_91cm',
             f'{PDS4_BUNDLES_DIR}/uranus_occs_earthbased/uranus_occ_u0_kao_91cm'),
            ('uranus_occ_u0_kao_91cm/data/atmosphere',
             f'{PDS4_BUNDLES_DIR}/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere'),
            ('uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
             f'{PDS4_BUNDLES_DIR}/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml'),
            ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
             f'{PDS4_BUNDLES_DIR}/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml'),
        ]
    )
    def test_from_path(self, input_path, expected):
        res = pds4file.Pds4File.from_path(path=input_path)
        assert isinstance(res, pds4file.PdsFile)
        assert res.abspath == expected

    @pytest.mark.parametrize(
        'filespec,expected',
        [
            # ('cassini_iss_cruise', f'{PDS4_BUNDLES_DIR}/cassini_iss/cassini_iss_cruise'),
            # ('cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947228n-full.xml',
            #  f'{PDS4_BUNDLES_DIR}/cassini_iss/cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947228n-full.xml'),
            # ('cassini_vims_cruise', f'{PDS4_BUNDLES_DIR}/cassini_vims/cassini_vims_cruise'),
            # ('cassini_vims_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308946681_xxx/1308946681_001-full.xml',
            #  f'{PDS4_BUNDLES_DIR}/cassini_vims/cassini_vims_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308946681_xxx/1308946681_001-full.xml'),
            ('uranus_occ_u0_kao_91cm',
             f'{PDS4_BUNDLES_DIR}/uranus_occs_earthbased/uranus_occ_u0_kao_91cm'),
            ('uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
             f'{PDS4_BUNDLES_DIR}/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml'),
        ]
    )
    def test_from_filespec(self, filespec, expected):
        res = pds4file.Pds4File.from_filespec(filespec=filespec)
        print(res)
        assert isinstance(res, pds4file.PdsFile)
        assert res.abspath == expected


    # For now we fake all the images files under previews dir
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
            #  [
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_full.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_med.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_small.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_thumb.png',
            #  ]
            # ),
            # ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947273n.img',
            #  [
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947273n_full.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947273n_med.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947273n_small.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947273n_thumb.png',
            #  ]
            # ),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947223.xml',
            #  [
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947223_full.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947223_med.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947223_small.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947223_thumb.png',
            #  ]
            # ),
            # ('cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947079_xxx/1308947079_003.qub',
            #  [
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947079_xxx/1308947079_003_full.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947079_xxx/1308947079_003_med.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947079_xxx/1308947079_003_small.png',
            #      f'/{PDS4_HOLDINGS_NAME}/previews/cassini_vims/cassini_vims_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947079_xxx/1308947079_003_thumb.png',
            #  ]
            # ),
            # cassini_uvis_solarocc_beckerjarmak2023
            (
                'cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2005_159_solar_time_series_ingress.xml',
                [
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2005_159_solar_time_series_ingress_preview_full.png',
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2005_159_solar_time_series_ingress_preview_med.png',
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2005_159_solar_time_series_ingress_preview_small.png',
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2005_159_solar_time_series_ingress_preview_thumb.png'
                ]
            ),
            (
                'cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2008_083_solar_time_series_egress.xml',
                [
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2008_083_solar_time_series_egress_preview_full.png',
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2008_083_solar_time_series_egress_preview_med.png',
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2008_083_solar_time_series_egress_preview_small.png',
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2008_083_solar_time_series_egress_preview_thumb.png',
                ]
            ),
            (
                'cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/supplemental/uvis_euv_2008_083_solar_time_series_egress_supplement.xml',
                [
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/supplemental/uvis_euv_2008_083_solar_time_series_egress_supplement_preview_full.png',
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/supplemental/uvis_euv_2008_083_solar_time_series_egress_supplement_preview_med.png',
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/supplemental/uvis_euv_2008_083_solar_time_series_egress_supplement_preview_small.png',
                    f'/{PDS4_HOLDINGS_NAME}/previews/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/supplemental/uvis_euv_2008_083_solar_time_series_egress_supplement_preview_thumb.png',
                ]
            ),
            # TODO: change these test cases to previews when available
            # uranus_occs_earthbased
            (
                'uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_delta_egress_100m.xml',
                [
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_delta_egress_diagram_full.png',
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_delta_egress_diagram_med.png',
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_delta_egress_diagram_small.png',
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_delta_egress_diagram_thumb.png'
                ]
            ),
            (
                'uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
                [
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress_diagram_full.png',
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress_diagram_med.png',
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress_diagram_small.png',
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress_diagram_thumb.png'
                ]
            ),
            (
                'uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_ingress_100m.xml',
                [
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_ingress_diagram_full.png',
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_ingress_diagram_med.png',
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_ingress_diagram_small.png',
                    f'/{PDS4_HOLDINGS_NAME}/diagrams/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_ingress_diagram_thumb.png'
                ]
            ),
            (
                'uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global', False
            ),
        ]
    )
    def test_viewset(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.viewset
        if res != False:
            assert isinstance(res, pdsviewable.PdsViewSet)
            viewables = res.to_dict()['viewables']
            for viewable in viewables:
                assert viewable['url'] in expected
        else:
            # For the case when viewset is None, the function will return False
            assert res == expected

    @pytest.mark.parametrize(
    'input_path,expected',
    [
        # cassini_uvis_solarocc_beckerjarmak2023
        (
            'bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2005_159_solar_time_series_ingress.xml',
            'couvis_solar_occ_ring'
        ),
        (
            'bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/supplemental/uvis_euv_2008_083_solar_time_series_egress_supplement.xml',
            'couvis_solar_occ_ring_supp'
        ),
        (
            'bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/browse/uvis_euv_2007_114_solar_time_series_ingress.jpg',
            'couvis_solar_occ_browse'
        ),
        (
            'bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/document/2-RingSolarOccAtlasVol2V1.0.pdf',
            'couvis_solar_occ_documentation'
        ),

        # uranus_occs_earthbased
        # Rings/ring models
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_100m.xml',
            'ebur_occ_ring_0100'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_beta_ingress_500m.tab',
            'ebur_occ_ring_0500'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_delta_ingress_1000m.xml',
            'ebur_occ_ring_1000'),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_counts-v-time_rings_ingress.tab',
            'ebur_occ_ring_time'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/ring_models/u0_kao_91cm_734nm_fitted_ring_event_times.tab',
            'ebur_occ_ring_sqw_model'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/ring_models/u0_kao_91cm_734nm_ring_six_egress_sqw.txt',
            'ebur_occ_ring_sqw_model'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/ring_models/u0_kao_91cm_734nm_ring_six_egress_sqw_h.tab',
            'ebur_occ_ring_sqw_model'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/ring_models/u0_kao_91cm_734nm_wavelengths.csv',
            'ebur_occ_ring_sqw_model'
        ),
        # Atmosphere
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_ingress.tab',
            'ebur_occ_atmos'
        ),
        # Global
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_egress_100m.tab',
            'ebur_occ_global_0100'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_ingress_500m.tab',
            'ebur_occ_global_0500'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_egress_1000m.xml',
            'ebur_occ_global_1000'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_counts-v-time_occult.xml',
            'ebur_occ_global_time'
        ),
        # Uranus occ support
        (
            'bundles/uranus_occs_earthbased/uranus_occ_support/data/uranus_occultation_ring_fit_rfrench_20201201.xml',
            'ebur_occ_global_ring_fit'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_support/document/supplemental_docs/uranus_occultations_index.xml',
            'ebur_occ_orig_index'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_support/document/supplemental_docs/uranus_ringocc_bundles_quality_rating.csv',
            'ebur_occ_quality_rating'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_support/document/user_guide/earth-based-uranus-stellar-occultation-user-guide.pdf',
            'ebur_occ_documentation'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_support/document/user_guide/ring_longitude_example.py',
            'ebur_occ_software'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_support/document/user_guide/plot_epsilon_ring_example.pro',
            'ebur_occ_software'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_support/document/user_guide/plot_epsilon_ring_example_IDL.pdf',
            'ebur_occ_software'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_support/spice_kernels/fk/uranus_ringframes_french_et_al_1988_v1.tf',
            'ebur_occ_kernels'
        ),
        (
            'bundles/uranus_occs_earthbased/uranus_occ_support/spice_kernels/spk/urkao_v1.bsp',
            'ebur_occ_kernels'
        ),
        # TODO: Add preview and diagram images when they are available
    ]
    )
    def test_opus_type(self, input_path, expected):
        """opus_type: return self._opus_type_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path, False)
        res = target_pdsfile.opus_type
        assert res != '', 'No opus_type returned'
        assert res[2] == expected
