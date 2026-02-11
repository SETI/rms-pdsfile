##########################################################################################
# pds4file/rules/cassini_iss_fring_mosaics_rsfrench2025.py
##########################################################################################

import pdsfile.pds4file as pds4file
import translator
import re

# from .cassini_iss_fring_mosaics_rsfrench2025_primary_filespec import PRIMARY_FILESPEC_LIST

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([

])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'.*/(cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*)/data(|/supplemental)/(uvis_euv.*)\.[a-z]{3}', 0,
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
    (r'.*/(cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*)/data(|/supplemental)/(uvis_euv_.*_(egress|ingress))(|_supplement)\.[a-z]{3}', 0,
        [
            r'bundles/\1/data/\3.tab',
            r'bundles/\1/data/\3.xml',
            r'bundles/\1/data/supplemental/\3_supplement.tab',
            r'bundles/\1/data/supplemental/\3_supplement.xml',
            r'bundles/\1/browse/\3.jpg',
            r'bundles/\1/browse/\3.xml',
        ]),
    (r'documents/cassini_iss_fring_mosaics_rsfrench2025[^/]*', 0,
        r'bundles/cassini_iss_fring_mosaics_rsfrench2025'),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*)/data(|/supplemental)/(uvis_euv_.*_(egress|ingress))(|_supplement)\.[a-z]{3}', 0,
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
    (r'.*/(cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*)/data(|/supplemental)/(uvis_euv_.*_(egress|ingress))(|_supplement)\.[a-z]{3}', 0,
        [
        ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025[^/]*', 0,
        [
            r'documents/cassini_iss_fring_mosaics_rsfrench2025[^/]*',
            r'documents/cassini_iss_fring_mosaics_rsfrench2025[^/]*/.*',
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
    # data
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/data_mosaic/iss_.*/iss_.*\.(img|lblx)',              0, ('Cassini ISS F Ring Mosaics', 10, 'coiss_f_ring_mosaic', 'Data Mosaic', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/data_mosaic/iss_.*/iss_.*metadata.*\.tab',              0, ('Cassini ISS F Ring Mosaics', 20, 'coiss_f_ring_mosaic_metadata', 'Data Mosaic Metadata', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/data_mosaic_bkg_sub/iss_.*/iss_.*\.(img|lblx)', 0, ('Cassini ISS F Ring Mosaics', 30, 'coiss_f_ring_mosaic_bkg_sub', 'Background-Subtracted Data Mosaic', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/data_mosaic_bkg_sub/iss_.*/iss_.*metadata.*\.tab', 0, ('Cassini ISS F Ring Mosaics', 40, 'coiss_f_ring_mosaic_bkg_sub_metadata', 'Background-Subtracted Data Mosaic Metadata', True)),
    # browse
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic/iss_.*/iss_.*\.(img|lblx)',            0, ('Cassini ISS F Ring Mosaics', 50, 'coiss_f_ring_mosaic_browse', 'Browse Mosaic', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic/iss_.*/iss_.*metadata.*\.tab',            0, ('Cassini ISS F Ring Mosaics', 60, 'coiss_f_ring_mosaic_browse_metadata', 'Browse Mosaic Metadata', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic_bkg_sub/iss_.*/iss_.*\.(img|lblx)',            0, ('Cassini ISS F Ring Mosaics', 70, 'coiss_f_ring_mosaic_browse_bkg_sub', 'Background-Subtracted Browse Mosaic', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic_bkg_sub/iss_.*/iss_.*metadata.*\.tab',            0, ('Cassini ISS F Ring Mosaics', 80, 'coiss_f_ring_mosaic_browse_bkg_sub_metadata', 'Background-Subtracted Browse Mosaic Metadata', True)),
    # document
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/(readme.txt|document/.*/.*mosaic.*\.(pdf|xml))',               0, ('Cassini ISS F Ring Mosaics', 90, 'coiss_f_ring_documentation', 'Documentation', False)),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

opus_products = translator.TranslatorByRegex([
    (r'bundles/(cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*)/data(|/supplemental)/(uvis_euv_.*_(egress|ingress))(|_supplement)\.[a-z]{3}', 0,
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
    (r'.*/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/data_mosaic.*/(iss_[a-zA-Z0-9_]*)/iss_[a-zA-Z0-9_]*_mosaic.*\.[a-z]{3,4}', 0, r'co-iss-fring-mosaic-\1')
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'(cassini_iss_fring_mosaics_rsfrench2025).*', 0, r'\1'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

# primary filespec will be the data label file under data_mosaic for each opus id
opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'co-iss-fring-mosaic-(.*)',     0,  r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data_mosaic/\1/\1_mosaic.lblx'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class cassini_iss_fring_mosaics_rsfrench2025(pds4file.Pds4File):

    pds4file.Pds4File.VOLSET_TRANSLATOR = translator.TranslatorByRegex(
        [('cassini_iss_fring_mosaics_rsfrench2025', re.I,
          'cassini_iss_fring_mosaics_rsfrench2025')]
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
    [(r'co-iss-fring-mosaic.*', 0, cassini_iss_fring_mosaics_rsfrench2025)]
) + pds4file.Pds4File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds4file.Pds4File.SUBCLASSES['cassini_iss_fring_mosaics_rsfrench2025'] = cassini_iss_fring_mosaics_rsfrench2025

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

# @pytest.mark.parametrize(
#     ('input_path', 'expected'),
#     [
#         ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data/uvis_euv_2005_159_solar_time_series_ingress.xml',
#          'cassini_iss_fring_mosaics_rsfrench2025/opus_products/uvis_euv_2005_159_solar_time_series_ingress.txt'),
#         ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data/uvis_euv_2008_083_solar_time_series_egress.xml',
#          'cassini_iss_fring_mosaics_rsfrench2025/opus_products/uvis_euv_2008_083_solar_time_series_egress.txt'),
#     ]
# )
# def test_opus_products(request, input_path, expected):
#     update = request.config.option.update
#     opus_products_test(pds4file.Pds4File, input_path, TEST_RESULTS_DIR+expected, update)

# @pytest.mark.parametrize(
#     ('input_path', 'category', 'expected'),
#     [
#         ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data/uvis_euv_2006_257_solar_time_series_ingress.xml',
#          'bundles',
#          'cassini_iss_fring_mosaics_rsfrench2025/associated_abspaths/bundles_uvis_euv_2006_257_solar_time_series_ingress.txt'),
#         ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data/uvis_euv_2008_083_solar_time_series_egress.xml',
#          'bundles',
#          'cassini_iss_fring_mosaics_rsfrench2025/associated_abspaths/bundles_uvis_euv_2008_083_solar_time_series_egress.txt'),
#         ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data/uvis_euv_2006_257_solar_time_series_ingress.xml',
#          'previews',
#          'cassini_iss_fring_mosaics_rsfrench2025/associated_abspaths/previews_uvis_euv_2006_257_solar_time_series_ingress.txt'),
#         ('bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data/uvis_euv_2008_083_solar_time_series_egress.xml',
#          'previews',
#          'cassini_iss_fring_mosaics_rsfrench2025/associated_abspaths/previews_uvis_euv_2008_083_solar_time_series_egress.txt'),
#     ]
# )

# def test_associated_abspaths(request, input_path, category, expected):
#     update = request.config.option.update
#     associated_abspaths_test(pds4file.Pds4File, input_path, category,
#                              TEST_RESULTS_DIR+expected, update)

# def test_opus_id_to_primary_logical_path():
#     for logical_path in PRIMARY_FILESPEC_LIST:
#         test_pdsf = pds4file.Pds4File.from_logical_path(logical_path)
#         opus_id = test_pdsf.opus_id
#         opus_id_pdsf = pds4file.Pds4File.from_opus_id(opus_id)
#         assert opus_id_pdsf.logical_path == logical_path



##########################################################################################
