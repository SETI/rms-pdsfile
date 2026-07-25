import pytest
import os
import translator

import pdsfile.pds3file as pds3file

from tests.rules.support import (
    PDS3_TEST_RESULTS_DIR as TEST_RESULTS_DIR,
    associated_abspaths_test,
    opus_products_test,
    translate_all,
    unmatched_patterns,
)
from pdsfile.pds3file.rules.CORSS_8xxx import (
    associations_to_diagrams,
    associations_to_documents,
    associations_to_metadata,
    associations_to_previews,
    associations_to_volumes,
    default_viewables,
    diagram_viewables,
    dsntrack_viewables,
    profile_viewables,
    skyview_viewables,
    timeline_viewables,
)


def test_default_viewables():
    # ((number of default viewables, diagrams, profiles, skyviews, dsntracks, timelines), logical_path)
    TESTS = [
        ((4, 0, 0, 0, 4, 0), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007_DSN_Elevation.LBL'),
        ((4, 0, 0, 0, 4, 0), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007_DSN_Elevation.pdf'),
        ((4, 0, 0, 0, 0, 4), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007_TimeLine_Figure.pdf'),
        ((4, 0, 0, 0, 0, 0), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007_TimeLine_Table.pdf'),
        ((4, 0, 0, 4, 4, 4), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E'),
        ((4, 4, 4, 4, 4, 4), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E'),
        ((0, 0, 0, 0, 0, 0), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_CAL.TAB'),
        ((0, 0, 0, 0, 0, 0), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_DLP_500M.TAB'),
        ((4, 4, 0, 0, 0, 0), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_GEO.TAB'),
        ((4, 4, 4, 0, 0, 0), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_TAU_01KM.TAB'),
        ((4, 4, 4, 0, 0, 0), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_TAU_10KM.TAB'),
        ((4, 4, 4, 0, 0, 0), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev137/Rev137E/Rev137E_RSS_2010_245_S24_E/RSS_2010_245_S24_E_TAU_1600M.TAB'),
        ((4, 0, 0, 4, 0, 0), 'volumes/CORSS_8xxx/CORSS_8001/browse/Rev007_OccTrack_Geometry.pdf'),
        ((4, 0, 0, 0, 0, 0), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/Rev07E_RSS_2005_123_X43_E_Summary.pdf'),
        ((0, 0, 0, 0, 0, 0), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_CAL.TAB'),
        ((4, 4, 0, 0, 0, 0), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_GEO.TAB'),
        ((4, 4, 4, 0, 0, 0), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_TAU_01KM.TAB'),
        ((4, 4, 4, 0, 0, 0), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_TAU_10KM.TAB'),
    ]

    for (counts, path) in TESTS:
        abspaths = translate_all(default_viewables, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == counts[0], f'{path} {len(abspaths)} {trimmed}'

        abspaths = translate_all(diagram_viewables, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == counts[1], f'{path} {len(abspaths)} {trimmed}'

        abspaths = translate_all(profile_viewables, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == counts[2], f'{path} {len(abspaths)} {trimmed}'

        abspaths = translate_all(skyview_viewables, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == counts[3], f'{path} {len(abspaths)} {trimmed}'

        abspaths = translate_all(dsntrack_viewables, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == counts[4], f'{path} {len(abspaths)} {trimmed}'

        abspaths = translate_all(timeline_viewables, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == counts[5], f'{path} {len(abspaths)} {trimmed}'

def test_associations():
    # ((number of volume associations, previews, diagrams, metadata, documents), logical_path)
    TESTS = [
        (( 2, 2, 1, 1, 1), 'volumes/CORSS_8xxx/CORSS_8001/data'),
        (( 2, 2, 1, 0, 1), 'volumes/CORSS_8xxx/CORSS_8001/browse'),
        (( 2, 2, 1, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data'),
        (( 2, 2, 1, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/browse'),
        (( 2, 2, 1, 0, 0), 'diagrams/CORSS_8xxx/CORSS_8001/data'),
        (( 2, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/browse/Rev007_OccTrack_Geometry_full.jpg'),
        (( 2, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007_DSN_Elevation_full.jpg'),
        (( 1, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E_full.jpg'),
        (( 2, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/Rev007E_RSS_2005_123_K34_E_Summary_thumb.jpg'),
        (( 2, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_GEO_thumb.jpg'),
        (( 4, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_TAU_thumb.jpg'),
        (( 2, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/browse/Rev054_OccTrack_Geometry_full.jpg'),
        (( 2, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054_DSN_Elevation_full.jpg'),
        (( 2, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054_TimeLine_Figure_full.jpg'),
        (( 2, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054_TimeLine_Table_full.jpg'),
        (( 1, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE_full.jpg'),
        (( 2, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E/Rev054CE_RSS_2007_353_K55_E_Summary_thumb.jpg'),
        (( 2, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E/RSS_2007_353_K55_E_GEO_thumb.jpg'),
        (( 4, 4, 0, 0, 0), 'previews/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E/RSS_2007_353_K55_E_TAU_thumb.jpg'),
        (( 1, 0, 4, 0, 0), 'diagrams/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E_RSS_2005_123_K34_E_full.jpg'),
        (( 1, 0, 4, 0, 0), 'diagrams/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE_RSS_2007_353_K55_E_full.jpg'),
        (( 1, 5, 0, 0, 1), 'volumes/CORSS_8xxx/CORSS_8001/browse/Rev007_OccTrack_Geometry.pdf'),
        (( 1, 5, 0, 0, 1), 'volumes/CORSS_8xxx/CORSS_8001/browse/Rev007_OccTrack_Geometry.LBL'),
        (( 2, 5, 1, 0, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007'),
        (( 8, 5, 0, 0, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E'),
        (( 8, 1, 4, 0, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E'),
        ((20, 1, 4, 2, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_TAU_01KM.TAB'),
        ((20, 1, 4, 2, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_TAU_01KM.LBL'),
        ((20, 1, 4, 2, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_TAU_10KM.TAB'),
        ((20, 1, 4, 1, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_CAL.TAB'),
        ((20, 1, 4, 1, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_DLP_500M.TAB'),
        ((20, 1, 4, 1, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_GEO.TAB'),
        (( 8, 5, 0, 0, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE'),
        (( 8, 1, 4, 0, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E'),
        ((20, 1, 4, 2, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E/RSS_2007_353_K55_E_TAU_01KM.TAB'),
        ((20, 1, 4, 2, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E/RSS_2007_353_K55_E_TAU_01KM.LBL'),
        ((20, 1, 4, 2, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E/RSS_2007_353_K55_E_TAU_10KM.TAB'),
        ((20, 1, 4, 1, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E/RSS_2007_353_K55_E_CAL.TAB'),
        ((20, 1, 4, 1, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E/RSS_2007_353_K55_E_DLP_500M.TAB'),
        ((20, 1, 4, 1, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E/RSS_2007_353_K55_E_GEO.TAB'),
        ((20, 1, 4, 1, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E/Rev054CE_RSS_2007_353_K55_E_Summary.pdf'),
        (( 2, 2, 1, 1, 1), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA'),
        (( 1, 1, 4, 0, 1), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_K34_E'),
        (( 1, 1, 4, 2, 1), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_TAU_01KM.TAB'),
        (( 1, 1, 4, 2, 1), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_TAU_01KM.LBL'),
        (( 1, 1, 4, 2, 1), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_TAU_10KM.TAB'),
        (( 1, 1, 4, 1, 1), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_CAL.TAB'),
        (( 1, 1, 4, 1, 1), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_GEO.TAB'),
        (( 1, 1, 4, 0, 1), 'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/Rev07E_RSS_2005_123_X43_E_Summary.pdf'),
        (( 1, 1, 4, 0, 1), 'volumes/CORSS_8xxx/CORSS_8001/data/Rev054/Rev054CE/test_unmatched.pdf'),
    ]

    for (counts, path) in TESTS:
        # This is to test the translated pattern that does not find a matching path in
        # the file system.
        if 'test_unmatched' in path:
            dummy_unmatched_pattern = translator.TranslatorByRegex([
                (r'.*/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data|browse)/.*', 0,
                    [r'volumes/CORSS_8xxx\1/\2/data/x',
                    r'volumes/CORSS_8xxx\1/\2/browse/x',
                    ]),
            ])
            unmatched = unmatched_patterns(dummy_unmatched_pattern, path)
            trimmed = [p.rpartition('holdings/')[-1] for p in unmatched]
            assert len(unmatched) != 0
            # https://github.com/nedbat/coveragepy/issues/198
            # continue will be ignore by coverage, and shows not run, so we ignore the
            # the coverage check here.
            continue # pragma: no cover

        unmatched = unmatched_patterns(associations_to_volumes, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in unmatched]
        assert len(unmatched) == 0, f'Unmatched: {path} {trimmed}'

        abspaths = translate_all(associations_to_volumes, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == counts[0], f'Miscount: {path} {len(abspaths)} {trimmed}'

        unmatched = unmatched_patterns(associations_to_previews, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in unmatched]
        assert len(unmatched) == 0, f'Unmatched: {path} {trimmed}'

        abspaths = translate_all(associations_to_previews, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == counts[1], f'Miscount: {path} {len(abspaths)} {trimmed}'

        unmatched = unmatched_patterns(associations_to_diagrams, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in unmatched]
        assert len(unmatched) == 0, f'Unmatched: {path} {trimmed}'

        abspaths = translate_all(associations_to_diagrams, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == counts[2], f'Miscount: {path} {len(abspaths)} {trimmed}'

        abspaths = translate_all(associations_to_metadata, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == counts[3], f'Miscount: {path} {len(abspaths)} {trimmed}'

        abspaths = translate_all(associations_to_documents, path)
        trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
        assert len(abspaths) == counts[4], f'Miscount: {path} {len(abspaths)} {trimmed}'

@pytest.mark.parametrize(
    'input_path,expected',
    [
        ('volumes/CORSS_8xxx/CORSS_8001/data/Rev009/Rev009E/Rev009E_RSS_2005_159_K55_E/RSS_2005_159_K55_E_TAU_01KM.TAB',
         'CORSS_8xxx/opus_products/RSS_2005_159_K55_E_TAU_01KM.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    'input_path,category,expected',
    [
        ('volumes/CORSS_8xxx/CORSS_8001/data/Rev009/Rev009E/Rev009E_RSS_2005_159_K55_E/RSS_2005_159_K55_E_TAU_01KM.TAB',
         'volumes',
         'CORSS_8xxx/associated_abspaths/volumes_RSS_2005_159_K55_E_TAU_01KM.txt')
    ]
)
def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds3file.Pds3File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    TESTS = [
        'Rev009/Rev009E/Rev009E_RSS_2005_159_K55_E/RSS_2005_159_K55_E_TAU_01KM.TAB',
        'Rev007/Rev007E/Rev007E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_TAU_01KM.TAB',
        'Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_TAU_01KM.TAB',
        'Rev054/Rev054CE/Rev054CE_RSS_2007_353_K55_E/RSS_2007_353_K55_E_TAU_01KM.TAB',
        'Rev137/Rev137E/Rev137E_RSS_2010_245_S24_E/RSS_2010_245_S24_E_TAU_1600M.TAB',
    ]

    for file_path in TESTS:
        logical_path = 'volumes/CORSS_8xxx/CORSS_8001/data/' + file_path
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
                    if 'diagrams/' in viewable.abspath: continue    # skip diagrams
                    assert viewable.abspath in opus_id_abspaths

            # Every associated product is in the product set except metadata
            for category in ('volumes', 'calibrated', 'previews'):
                for abspath in pdsf.associated_abspaths(category):
                    if '.' not in os.path.basename(abspath): continue   # skip dirs
                    assert abspath in opus_id_abspaths

##########################################################################################
