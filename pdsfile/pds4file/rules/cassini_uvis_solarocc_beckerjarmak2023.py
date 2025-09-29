##########################################################################################
# pds4file/rules/cassini_uvis_solarocc_beckerjarmak2023.py
##########################################################################################

import pdsfile.pds4file as pds4file
import translator
import re

from .cassini_uvis_solarocc_beckerjarmak2023_primary_filespec import PRIMARY_FILESPEC_LIST

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([

])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'.*/(cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023[^/]*)/data(|/supplemental)/(uvis_euv.*)\.[a-z]{3}', 0,
     [
         r'previews/\1/data\2/\3_preview_full.png',
         r'previews/\1/data\2/\3_preview_med.png',
         r'previews/\1/data\2/\3_preview_small.png',
         r'previews/\1/data\2/\3_preview_thumb.png',
     ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_bundles = translator.TranslatorByRegex([
    (r'.*/(cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023[^/]*)/data(|/supplemental)/(uvis_euv_.*_(egress|ingress))(|_supplement)\.[a-z]{3}', 0,
        [
            r'bundles/\1/data/\3.tab',
            r'bundles/\1/data/\3.xml',
            r'bundles/\1/data/supplemental/\3_supplement.tab',
            r'bundles/\1/data/supplemental/\3_supplement.xml',
            r'bundles/\1/browse/\3.jpg',
            r'bundles/\1/browse/\3.xml',
        ]),
    (r'documents/cassini_uvis_solarocc_beckerjarmak2023[^/]*', 0,
        r'bundles/cassini_uvis_solarocc_beckerjarmak2023'),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023[^/]*)/data(|/supplemental)/(uvis_euv_.*_(egress|ingress))(|_supplement)\.[a-z]{3}', 0,
        [
            r'previews/\1/data/\3_preview_full.png',
            r'previews/\1/data/\3_preview_med.png',
            r'previews/\1/data/\3_preview_small.png',
            r'previews/\1/data/\3_preview_thumb.png',
            r'previews/\1/data/supplemental/\3_supplement_preview_full.png',
            r'previews/\1/data/supplemental/\3_supplement_preview_med.png',
            r'previews/\1/data/supplemental/\3_supplement_preview_small.png',
            r'previews/\1/data/supplemental/\3_supplement_preview_thumb.png',
        ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'.*/(cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023[^/]*)/data(|/supplemental)/(uvis_euv_.*_(egress|ingress))(|_supplement)\.[a-z]{3}', 0,
        [
        ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'bundles/cassini_uvis_solarocc_beckerjarmak2023[^/]*', 0,
        [
            r'documents/cassini_uvis_solarocc_beckerjarmak2023[^/]*',
            r'documents/cassini_uvis_solarocc_beckerjarmak2023[^/]*/.*',
        ]),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([

])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([

])

##########################################################################################
# SORT_KEY
##########################################################################################

sort_key = translator.TranslatorByRegex([

])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023[^/]*/data/uvis_euv_.*\.(tab|xml)',              0, ('Cassini UVIS Solar Occultations', 10, 'couvis_solar_occ_ring', 'Occultation Ring Time Series', True)),
    (r'bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023[^/]*/data/supplemental/uvis_euv_.*\.(tab|xml)', 0, ('Cassini UVIS Solar Occultations', 20, 'couvis_solar_occ_ring_supp', 'Occultation Ring Time Series Supplemental', True)),
    (r'bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023[^/]*/(readme.txt|document/.*\.(pdf|xml))',               0, ('Cassini UVIS Solar Occultations', 30, 'couvis_solar_occ_documentation', 'Documentation', False)),
    (r'bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023[^/]*/browse/uvis_euv_.*\.(jpg|xml)',            0, ('Cassini UVIS Solar Occultations', 40, 'couvis_solar_occ_browse', 'Detailed Browse', True)),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

opus_products = translator.TranslatorByRegex([
    (r'bundles/(cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023[^/]*)/data(|/supplemental)/(uvis_euv_.*_(egress|ingress))(|_supplement)\.[a-z]{3}', 0,
     [
         # bundles data/
         r'bundles/\1/data/\3.tab',
         r'bundles/\1/data/\3.xml',
         # bundles data/supplemental
         r'bundles/\1/data/supplemental/\3_supplement.tab',
         r'bundles/\1/data/supplemental/\3_supplement.xml',
         # bundles browse/
         r'bundles/\1/browse/\3.jpg',
         r'bundles/\1/browse/\3.xml',
         # bundles readme.txt
         r'bundles/\1/readme.txt',
         # document
         r'bundles/\1/document/1-RingSolarOccAtlasVol1V1.0.pdf',
         r'bundles/\1/document/1-RingSolarOccAtlasVol1V1.0.xml',
         r'bundles/\1/document/2-RingSolarOccAtlasVol2V1.0.pdf',
         r'bundles/\1/document/2-RingSolarOccAtlasVol2V1.0.xml',
         r'bundles/\1/document/Cassini_UVIS_Users_Guide_20180706.pdf',
         r'bundles/\1/document/Cassini_UVIS_Users_Guide_20180706.xml',
         # previews
         r'previews/\1/data/\3_preview_full.png',
         r'previews/\1/data/\3_preview_med.png',
         r'previews/\1/data/\3_preview_small.png',
         r'previews/\1/data/\3_preview_thumb.png',
         # previews data/supplemental
         r'previews/\1/data/supplemental/\3_supplement_preview_full.png',
         r'previews/\1/data/supplemental/\3_supplement_preview_med.png',
         r'previews/\1/data/supplemental/\3_supplement_preview_small.png',
         r'previews/\1/data/supplemental/\3_supplement_preview_thumb.png',
     ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023[^/]*/data(|/supplemental)/uvis_euv_(\d{4})_(\d{3})_.*_([ei])(gress|ngress)(|_supplement)\.[a-z]{3}', 0, r'co-uvis-occ-\2-\3-sun-\4')
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'(cassini_uvis_solarocc_beckerjarmak2023).*', 0, r'\1'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'co-uvis-occ-(\d{4})-(\d{3})-sun-([ei])',     0,  r'bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_\1_\2_solar_time_series_\3*gress.xml'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class cassini_uvis_solarocc_beckerjarmak2023(pds4file.Pds4File):

    pds4file.Pds4File.VOLSET_TRANSLATOR = translator.TranslatorByRegex(
        [('cassini_uvis_solarocc_beckerjarmak2023', re.I,
          'cassini_uvis_solarocc_beckerjarmak2023')]
    ) + pds4file.Pds4File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds4file.Pds4File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds4file.Pds4File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds4file.Pds4File.NEIGHBORS
    SORT_KEY = sort_key + pds4file.Pds4File.SORT_KEY

    OPUS_TYPE = opus_type + pds4file.Pds4File.OPUS_TYPE
    OPUS_PRODUCTS = opus_products + pds4file.Pds4File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds4file.Pds4File.ASSOCIATIONS.copy()
    ASSOCIATIONS['bundles']    += associations_to_bundles
    ASSOCIATIONS['previews']   += associations_to_previews
    ASSOCIATIONS['metadata']   += associations_to_metadata
    ASSOCIATIONS['documents']  += associations_to_documents

    pds4file.Pds4File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds4file.Pds4File.FILESPEC_TO_BUNDLESET

# Global attribute shared by all subclasses
pds4file.Pds4File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex(
    [(r'co-uvis-occ.*', 0, cassini_uvis_solarocc_beckerjarmak2023)]
) + pds4file.Pds4File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds4file.Pds4File.SUBCLASSES['cassini_uvis_solarocc_beckerjarmak2023'] = cassini_uvis_solarocc_beckerjarmak2023

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

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
