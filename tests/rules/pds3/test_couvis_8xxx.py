import pytest

import pdsfile.pds3file as pds3file
from tests.rules.support import (
    PDS3_TEST_RESULTS_DIR as TEST_RESULTS_DIR,
)
from tests.rules.support import (
    associated_abspaths_test,
    opus_products_test,
    versions_test,
)


@pytest.mark.parametrize(
    ('input_path', 'expected'),
    [
        ('volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2005_139_126TAU_E_TAU01KM.TAB',
         'COUVIS_8xxx/opus_products/UVIS_HSP_2005_139_126TAU_E_TAU01KM.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    ('input_path', 'category', 'expected'),
    [
        ('volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2005_139_126TAU_E_TAU01KM.TAB',
         'volumes',
         'COUVIS_8xxx/associated_abspaths/volumes_UVIS_HSP_2005_139_126TAU_E_TAU01KM.txt')
    ]
)
def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds3file.Pds3File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    test_cases = [
        'volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2005_139_126TAU_E_TAU01KM.TAB',
    ]

    for logical_path in test_cases:
        test_pdsf = pds3file.Pds3File.from_logical_path(logical_path)
        opus_id = test_pdsf.opus_id
        opus_id_pdsf = pds3file.Pds3File.from_opus_id(opus_id)
        assert opus_id_pdsf.logical_path == logical_path

        # Gather all the associated OPUS products
        product_dict = test_pdsf.opus_products()
        product_pdsfiles = []
        for pdsf_lists in product_dict.values():
            for pdsf_list in pdsf_lists:
                product_pdsfiles += pdsf_list

        # Filter out the metadata/documents products and format files
        product_pdsfiles = [pdsf for pdsf in product_pdsfiles
                                 if pdsf.voltype_ != 'metadata/'
                                 and pdsf.voltype_ != 'documents/']
        product_pdsfiles = [pdsf for pdsf in product_pdsfiles
                                 if pdsf.extension.lower() != '.fmt']

        # Gather the set of absolute paths
        opus_id_abspaths = set()
        for pdsf in product_pdsfiles:
            opus_id_abspaths.add(pdsf.abspath)

        for pdsf in product_pdsfiles:
            # Every version is in the product set
            for version_pdsf in pdsf.all_versions().values():
                assert version_pdsf.abspath in opus_id_abspaths

            # Every viewset is in the product set
            for viewset in pdsf.all_viewsets.values():
                for viewable in viewset.viewables:
                    assert viewable.abspath in opus_id_abspaths

            # Every associated product is in the product set except metadata
            for category in ('volumes', 'previews'):
                for abspath in pdsf.associated_abspaths(category):
                    assert abspath in opus_id_abspaths

@pytest.mark.parametrize(
    ('input_path', 'expected'),
    [
        ('volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2009_062_THEHYA_E_TAU10KM.LBL',
            {999999: 'volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2009_062_THEHYA_E_TAU10KM.LBL',
              20100: 'volumes/COUVIS_8xxx_v2.1/COUVIS_8001/data/UVIS_HSP_2005_139_THEHYA_E_TAU10KM.LBL',
              20000: 'volumes/COUVIS_8xxx_v2.0/COUVIS_8001/data/UVIS_HSP_2005_139_THEHYA_E_TAU10KM.LBL'
            }),
        ('volumes/COUVIS_8xxx_v2.0/COUVIS_8001/data/UVIS_HSP_2007_038_SAO205839_I_TAU10KM.TAB',
            {999999: 'volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2008_026_SAO205839_I_TAU10KM.TAB',
              20100: 'volumes/COUVIS_8xxx_v2.1/COUVIS_8001/data/UVIS_HSP_2007_038_SAO205839_I_TAU10KM.TAB',
              20000: 'volumes/COUVIS_8xxx_v2.0/COUVIS_8001/data/UVIS_HSP_2007_038_SAO205839_I_TAU10KM.TAB',
            }),
        ('volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2010_149_LAMAQL_E_TAU01KM.TAB',
            {999999: 'volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2010_149_LAMAQL_E_TAU01KM.TAB',
              20100: 'volumes/COUVIS_8xxx_v2.1/COUVIS_8001/data/UVIS_HSP_2010_148_LAMAQL_E_TAU01KM.TAB',
              20000: 'volumes/COUVIS_8xxx_v2.0/COUVIS_8001/data/UVIS_HSP_2010_148_LAMAQL_E_TAU01KM.TAB',
            }),
        ('volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2005_141_ALPVIR_E_TAU01KM.LBL',
            {999999: 'volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2005_141_ALPVIR_E_TAU01KM.LBL',
              20100: 'volumes/COUVIS_8xxx_v2.1/COUVIS_8001/data/UVIS_HSP_2005_141_ALPVIR_E_TAU01KM.LBL',
              20000: 'volumes/COUVIS_8xxx_v2.0/COUVIS_8001/data/UVIS_HSP_2005_141_ALPVIR_E_TAU01KM.LBL',
              10000: 'volumes/COUVIS_8xxx_v1/COUVIS_8001/DATA/EASYDATA/UVIS_HSP_2005_141_ALPVIR_E_TAU_01KM.LBL',
            }),
        ('volumes/COUVIS_8xxx_v1/COUVIS_8001/DATA/EASYDATA/UVIS_HSP_2005_141_ALPVIR_E_TAU_01KM.LBL',
            {999999: 'volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2005_141_ALPVIR_E_TAU01KM.LBL',
              20100: 'volumes/COUVIS_8xxx_v2.1/COUVIS_8001/data/UVIS_HSP_2005_141_ALPVIR_E_TAU01KM.LBL',
              20000: 'volumes/COUVIS_8xxx_v2.0/COUVIS_8001/data/UVIS_HSP_2005_141_ALPVIR_E_TAU01KM.LBL',
              10000: 'volumes/COUVIS_8xxx_v1/COUVIS_8001/DATA/EASYDATA/UVIS_HSP_2005_141_ALPVIR_E_TAU_01KM.LBL',
            }),
    ])
def test_versions(input_path, expected):
    versions_test(input_path, expected)

##########################################################################################
