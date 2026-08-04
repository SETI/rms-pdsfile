import pytest

import pdsfile.pds3file as pds3file
from pdsfile.pds3file.rules.COCIRS_xxxx import (
    associations_to_diagrams,
    associations_to_volumes,
)
from tests.rules.support import (
    PDS3_TEST_RESULTS_DIR as TEST_RESULTS_DIR,
)
from tests.rules.support import (
    associated_abspaths_test,
    opus_products_test,
    translate_all,
)


def test_associations_to_volumes():
    test_cases = [
        ( 1, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE'),
        ( 1, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/DIONE'),
        (14, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/DIONE/POI0512240325_FP3_604.LBL'),
        (14, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/DIONE/POI0512240325_FP3_604.PNG'),
        (12, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/S_RINGS/RIN0512011549_FP3.PNG'),
        (12, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/S_RINGS/RIN0512011549_FP4.PNG'),
        (14, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/SATURN/POI0512010000_FP1.LBL'),
        (24, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/TARGETS/IMG0512010000_FP1.LBL'),
        ( 1, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA'),
        ( 7, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC'),
        ( 7, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/GEODATA'),
        (24, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC/SPEC0512010000_FP1.DAT'),
        (26, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/GEODATA/GEO0512010000_601.LBL'),
        (24, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/ISPMDATA/ISPM0512010000_FP1.LBL'),
        (24, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/POIDATA/POI0512010000_FP1.LBL'),
        (10, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/RINDATA/RIN0512010000_FP3.LBL'),
        (24, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/TARDATA/TAR0512010000_FP1.LBL'),
        ( 1, 'diagrams/COCIRS_5xxx/COCIRS_5512/BROWSE'),
        ( 1, 'diagrams/COCIRS_5xxx/COCIRS_5512/BROWSE/S_RINGS'),
        (12, 'diagrams/COCIRS_5xxx/COCIRS_5912/BROWSE/S_RINGS/RIN0912010101_FP4_full.jpg'),
        (14, 'diagrams/COCIRS_5xxx/COCIRS_5912/BROWSE/SATURN/POI0912010101_FP1_thumb.jpg'),
        (32, 'diagrams/COCIRS_5xxx/COCIRS_5912/BROWSE/TARGETS/IMG0912010101_FP1_full.jpg'),
        (14, 'diagrams/COCIRS_5xxx/COCIRS_5912/BROWSE/TITAN/POI0912111106_FP1_606_small.jpg'),
    ]

    for (count, path) in test_cases:
        abspaths = translate_all(associations_to_volumes, path)
        assert len(abspaths) == count, f'Miscount: {path} {len(abspaths)} {abspaths}'


def test_associations_to_diagrams():
    test_cases = [
        ( 1, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE'),
        ( 1, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/DIONE'),
        ( 4, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/DIONE/POI0512240325_FP3_604.LBL'),
        ( 4, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/DIONE/POI0512240325_FP3_604.PNG'),
        ( 4, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/S_RINGS/RIN0512011549_FP3.PNG'),
        ( 4, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/S_RINGS/RIN0512011549_FP4.PNG'),
        ( 4, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/SATURN/POI0512010000_FP1.LBL'),
        ( 4, 'volumes/COCIRS_5xxx/COCIRS_5512/BROWSE/TARGETS/IMG0512010000_FP1.LBL'),
        ( 1, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA'),
        ( 1, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC'),
        ( 1, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/GEODATA'),
        ( 1, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/RINDATA'),
        (12, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC/SPEC0512010000_FP1.DAT'),
        (12, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/GEODATA/GEO0512010000_601.LBL'),
        (12, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/ISPMDATA/ISPM0512010000_FP1.LBL'),
        (12, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/POIDATA/POI0512010000_FP1.LBL'),
        ( 8, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/RINDATA/RIN0512010000_FP3.LBL'),
        (12, 'volumes/COCIRS_5xxx/COCIRS_5512/DATA/TARDATA/TAR0512010000_FP1.LBL'),
        ( 0, 'diagrams/COCIRS_5xxx/COCIRS_5512/BROWSE'),
        ( 0, 'diagrams/COCIRS_5xxx/COCIRS_5512/BROWSE/S_RINGS'),
        (12, 'diagrams/COCIRS_5xxx/COCIRS_5912/BROWSE/S_RINGS/RIN0912010101_FP4_full.jpg'),
        ( 8, 'diagrams/COCIRS_5xxx/COCIRS_5912/BROWSE/SATURN/POI0912010101_FP1_thumb.jpg'),
        (12, 'diagrams/COCIRS_5xxx/COCIRS_5912/BROWSE/SATURN/POI0912010101_FP4_thumb.jpg'),
        ( 8, 'diagrams/COCIRS_5xxx/COCIRS_5912/BROWSE/TARGETS/IMG0912010101_FP1_full.jpg'),
        (12, 'diagrams/COCIRS_5xxx/COCIRS_5912/BROWSE/TARGETS/IMG0912010101_FP4_full.jpg'),
        ( 8, 'diagrams/COCIRS_5xxx/COCIRS_5912/BROWSE/TITAN/POI0912111106_FP1_606_small.jpg'),
        ( 8, 'diagrams/COCIRS_5xxx/COCIRS_5512/BROWSE/RHEA/POI0512231930_FP1_605.LBL'),
    ]

    for (count, path) in test_cases:
        abspaths = translate_all(associations_to_diagrams, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == count, f'Miscount: {path} {len(abspaths)} {trimmed}'

@pytest.mark.parametrize(
    ('input_path', 'expected'),
    [
        ('volumes/COCIRS_5xxx/COCIRS_5408/DATA/POIDATA/POI0408010000_FP1.LBL',
         'COCIRS_xxxx/opus_products/POI0408010000_FP1.txt'),
        # COCIRS_0xxx
        ('volumes/COCIRS_0xxx/COCIRS_0406/DATA/CUBE/POINT_PERSPECTIVE/000IA_PRESOI001____RI____699_F4_038P.LBL',
         'COCIRS_xxxx/opus_products/000IA_PRESOI001____RI____699_F4_038P.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    ('input_path', 'category', 'expected'),
    [
        ('volumes/COCIRS_5xxx/COCIRS_5408/DATA/POIDATA/POI0408010000_FP1.LBL',
         'volumes',
         'COCIRS_xxxx/associated_abspaths/volumes_POI0408010000_FP1.txt')
    ]
)
def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds3file.Pds3File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    test_cases = [
        'volumes/COCIRS_5xxx/COCIRS_5912/DATA/APODSPEC/SPEC0912010101_FP1.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5912/DATA/APODSPEC/SPEC0912111106_FP3.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5912/DATA/APODSPEC/SPEC0912111106_FP1.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5912/DATA/APODSPEC/SPEC0912010101_FP3.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5912/DATA/APODSPEC/SPEC0912111106_FP4.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5912/DATA/APODSPEC/SPEC0912010101_FP4.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5408/DATA/APODSPEC/SPEC0408010000_FP1.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC/SPEC0512011549_FP1.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC/SPEC0512011549_FP3.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC/SPEC0512011549_FP4.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC/SPEC0512240325_FP3.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC/SPEC0512240325_FP1.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC/SPEC0512240325_FP4.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC/SPEC0512010000_FP1.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC/SPEC0512010000_FP3.DAT',
        'volumes/COCIRS_5xxx/COCIRS_5512/DATA/APODSPEC/SPEC0512010000_FP4.DAT',
        # COCIRS_0xxx
        'volumes/COCIRS_0xxx/COCIRS_0406/DATA/CUBE/POINT_PERSPECTIVE/000IA_PRESOI001____RI____699_F4_038P.tar.gz'
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

        parts = pdsf.abspath.split('_FP')
        fpx = '_FP' + parts[1][0]
        for pdsf in product_pdsfiles:
            # Every version is in the product set
            for version_pdsf in pdsf.all_versions().values():
                assert version_pdsf.abspath in opus_id_abspaths

            # Every viewset is in the product set
            if fpx in pdsf.abspath:
                for viewset in pdsf.all_viewsets.values():
                    for viewable in viewset.viewables:
                        assert viewable.abspath in opus_id_abspaths

            # Every associated product is in the product set except metadata
            for category in ('volumes', 'calibrated', 'previews', 'diagrams'):
                for abspath in pdsf.associated_abspaths(category):
                    if fpx in abspath:
                        assert abspath in opus_id_abspaths

##########################################################################################
