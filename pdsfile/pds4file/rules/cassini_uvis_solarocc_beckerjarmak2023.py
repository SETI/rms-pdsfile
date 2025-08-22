##########################################################################################
# pds4file/rules/cassini_uvis_solarocc_beckerjarmak2023.py
##########################################################################################

import pdsfile.pds4file as pds4file
import translator
import re

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([

])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'.*/(cassini_uvis_solarocc_beckerjarmak2023*)/data(|/supplemental)/(uvis_euv.*)\.[a-z]{3}', 0,
        [r'previews/\1/data\2/\3_preview_full.png',
         r'previews/\1/data\2/\3_preview_med.png',
         r'previews/\1/data\2/\3_preview_small.png',
         r'previews/\1/data\2/\3_preview_thumb.png',
    ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_bundles = translator.TranslatorByRegex([
    (r'.*/(cassini_iss/cassini_iss\w*)/(data|browse)(.*|_[a-z]*]/.*)\.[a-z]{3}', 0,
        [r'bundles/\1/data\3.img',
         r'bundles/\1/data\3.xml',
         r'bundles/\1/browse\3-full.png',
         r'bundles/\1/browse\3-full.xml',
        ]),
    (r'documents/cassini_iss.*', 0,
        [r'bundles/cassini_iss',
         r'bundles/cassini_iss',
         r'bundles/cassini_iss',
        ]),
])

associations_to_calibrated = translator.TranslatorByRegex([
    (r'.*/((cassini_iss/cassini_iss\w*)/(data|browse)(.*|_[a-z]*]/.*))\.[a-z]{3}', 0,
        [r'calibrated/\1_CALIB.IMG',
         r'calibrated/\1_CALIB.LBL',
        ]),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(cassini_iss/cassini_iss\w*/(data|browse)(.*|_[a-z]*])/.*)\.[a-z]{3}', 0,
        [r'previews/\1_full.png',
         r'previews/\1_med.png',
         r'previews/\1_small.png',
         r'previews/\1_thumb.png',
        ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'.*/(cassini_iss)/(cassini_iss\w*)/(data|browse)(.*|_[a-z]*])/(.*)\.[a-z]{3}', 0,
        [r'metadata/\1/\2/\2_index.tab/\5',
         r'metadata/\1/\2/\2_ring_summary.tab/\5',
         r'metadata/\1/\2/\2_moon_summary.tab/\5',
         r'metadata/\1/\2/\2_saturn_summary.tab/\5',
         r'metadata/\1/\2/\2_jupiter_summary.tab/\5',
        ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'(bundles|calibrated)/cassini_iss/.*', 0,
         r'documents/cassini_iss/*'),
    (r'(bundles|calibrated)/cassini_iss', 0,
         r'documents/cassini_iss'),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'.*/COISS_[12].../(data|extras/w+)(|/\w+)',     0, (True, True,  True )),
    (r'.*/COISS_3.../(data|extras/w+)/(images|maps)', 0, (True, False, False)),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'(.*)/COISS_[12]xxx(.*)/COISS_..../(data|extras/\w+)/\w+', 0, r'\1/COISS_[12]xxx\2/*/\3/*'),
    (r'(.*)/COISS_[12]xxx(.*)/COISS_..../(data|extras/\w+)',     0, r'\1/COISS_[12]xxx\2/*/\3'),
    (r'(.*)/COISS_[12]xxx(.*)/COISS_....',                       0, r'\1/COISS_[12]xxx\2/*'),

    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data',               0, r'volumes/COISS_0xxx\1/*/data'),
    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data/(\w+)',         0, r'volumes/COISS_0xxx\1/*/data/\2'),
    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data/(\w+/\w+)',     0, r'volumes/COISS_0xxx\1/*/data/\2'),
    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data/(\w+/\w+)/\w+', 0, r'volumes/COISS_0xxx\1/*/data/\2/*'),
])

##########################################################################################
# SORT_KEY
##########################################################################################

sort_key = translator.TranslatorByRegex([

    # Skips over N or W, placing files into chronological order
    (r'([NW])([0-9]{10})(.*)_full.png',  0, r'\2\1\3_1full.jpg'),
    (r'([NW])([0-9]{10})(.*)_med.jpg',   0, r'\2\1\3_2med.jpg'),
    (r'([NW])([0-9]{10})(.*)_small.jpg', 0, r'\2\1\3_3small.jpg'),
    (r'([NW])([0-9]{10})(.*)_thumb.jpg', 0, r'\2\1\3_4thumb.jpg'),
    (r'([NW])([0-9]{10})(.*)', 0, r'\2\1\3'),

    # Used inside COISS_0011/document/report
    ('index.html', 0, '000index.html'),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'bundles/cassini_uvis_.*beckerjarmak2023*/data/uvis_euv_.*\.(tab|xml)',              0, ('Cassini UVIS Solar Occultations', 10, 'couvis_solar_occ_ring', 'Occultation Ring Time Series', True)),
    (r'bundles/cassini_uvis_.*beckerjarmak2023*/data/supplemental/uvis_euv_.*\.(tab|xml)', 0, ('Cassini UVIS Solar Occultations', 20, 'couvis_solar_occ_ring_supp', 'Occultation Ring Time Series Supplemental', True)),
    (r'bundles/cassini_uvis_.*beckerjarmak2023*/browse/uvis_euv_.*\.(jpg|xml)',            0, ('Cassini UVIS Solar Occultations', 40, 'couvis_solar_occ_browse', 'Detailed Browse', True)),
    (r'bundles/cassini_uvis_.*beckerjarmak2023*/document/[12].*\.(pdf|xml)',               0, ('Cassini UVIS Solar Occultations', 30, 'couvis_solar_occ_documentation', 'Documentation', False)),

])

##########################################################################################
# OPUS_FORMAT
##########################################################################################

opus_format = translator.TranslatorByRegex([
    (r'.*\.IMG',        0, ('Binary', 'VICAR')),
    (r'.*\.jpeg_small', 0, ('Binary', 'JPEG')),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

opus_products = translator.TranslatorByRegex([
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_[12]...)/data/(\w+/[NW][0-9]{10}_[0-9]+).*', 0,
            [r'volumes/\1*/\3/data/\4.IMG',
             r'volumes/\1*/\3/data/\4.LBL',
             r'volumes/\1*/\3/extras/thumbnail/\4.IMG.jpeg_small',
             r'volumes/\1*/\3/extras/browse/\4.IMG.jpeg',
             r'volumes/\1*/\3/extras/full/\4.IMG.png',
             r'volumes/\1*/\3/extras/tiff/\4.IMG.tiff',
             r'calibrated/\1*/\3/data/\4_CALIB.IMG',
             r'calibrated/\1*/\3/data/\4_CALIB.LBL',
             r'previews/\1/\3/data/\4_full.png',
             r'previews/\1/\3/data/\4_med.jpg',
             r'previews/\1/\3/data/\4_small.jpg',
             r'previews/\1/\3/data/\4_thumb.jpg',
             r'metadata/\1/\3/\3_moon_summary.tab',
             r'metadata/\1/\3/\3_moon_summary.lbl',
             r'metadata/\1/\3/\3_ring_summary.tab',
             r'metadata/\1/\3/\3_ring_summary.lbl',
             r'metadata/\1/\3/\3_saturn_summary.tab',
             r'metadata/\1/\3/\3_saturn_summary.lbl',
             r'metadata/\1/\3/\3_jupiter_summary.tab',
             r'metadata/\1/\3/\3_jupiter_summary.lbl',
             r'metadata/\1/\3/\3_inventory.csv',
             r'metadata/\1/\3/\3_inventory.lbl',
             r'metadata/\1/\3/\3_index.tab',
             r'metadata/\1/\3/\3_index.lbl',
             r'documents/COISS_0xxx/*.[!lz]*',
            ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
     (r'.*/cassini_uvis_.*beckerjarmak2023*/(data|supplemental)/uvis_euv_(\d{4})_(\d{3})_.*_([ei])(gress|ngress).*\.[a-z]{3}', 0, r'co-uvis-occ-\2-\3-sun-\4')
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
    (r'co-uvis-occ-(\d{4})-(\d{3})-sun-([ei])',     0,  r'bundles/cassini_uvis_solarocc_beckerjarmak2023*/data/uvis_euv_\1_\2_solar_time_series_\3*gress.xml'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class cassini_uvis_solarocc_beckerjarmak2023(pds4file.Pds4File): # Cassini_ISS

    pds4file.Pds4File.VOLSET_TRANSLATOR = translator.TranslatorByRegex(
        [('cassini_uvis_solarocc_beckerjarmak2023', re.I,
          'cassini_uvis_solarocc_beckerjarmak2023')]
    ) + pds4file.Pds4File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds4file.Pds4File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds4file.Pds4File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds4file.Pds4File.NEIGHBORS
    SORT_KEY = sort_key + pds4file.Pds4File.SORT_KEY

    OPUS_TYPE = opus_type + pds4file.Pds4File.OPUS_TYPE
    OPUS_FORMAT = opus_format + pds4file.Pds4File.OPUS_FORMAT
    OPUS_PRODUCTS = opus_products + pds4file.Pds4File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds4file.Pds4File.ASSOCIATIONS.copy()
    ASSOCIATIONS['bundles']    += associations_to_bundles
    ASSOCIATIONS['calibrated'] += associations_to_calibrated
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

# @pytest.mark.parametrize(
#     'input_path,category,expected',
#     [
#         ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
#          'bundles',
#          [
#             'bundles/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.img',
#             'bundles/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
#             'bundles/cassini_iss/cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947228n-full.png',
#             'bundles/cassini_iss/cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947228n-full.xml'
#          ]),
#         ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
#          'previews',
#          [
#             'previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_full.png',
#             'previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_med.png',
#             'previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_small.png',
#             'previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_thumb.png'
#          ]),
#         ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
#          'calibrated',
#          [
#             'calibrated/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_CALIB.IMG',
#             'calibrated/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_CALIB.LBL'
#          ]),
#         ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
#          'documents',
#          [
#             'documents/cassini_iss/Calibration-Plan.pdf',
#             'documents/cassini_iss/Data-Product-SIS.txt',
#             'documents/cassini_iss/ISS-Users-Guide.docx',
#             'documents/cassini_iss/Data-Product-SIS.pdf',
#             'documents/cassini_iss/Calibration-Theoretical-Basis.pdf',
#             'documents/cassini_iss/VICAR-File-Format.pdf',
#             'documents/cassini_iss/Calibration-Report.link',
#             'documents/cassini_iss/Press-Releases-at-RMS.link',
#             'documents/cassini_iss/VICAR-Home-Page-at-JPL.link',
#             'documents/cassini_iss/Press-Releases-at-JPL-Photojournal.link',
#             'documents/cassini_iss/Porco-etal-2004-SSR.link',
#             'documents/cassini_iss/ISS-Users-Guide.pdf',
#             'documents/cassini_iss/Archive-SIS.pdf',
#             'documents/cassini_iss/PDS-ISS-Home-Page.link',
#             'documents/cassini_iss/CISSCAL-Users-Guide.pdf',
#             'documents/cassini_iss/PDS-ISS-Home-Page-at-RMS.link',
#             'documents/cassini_iss/Archive-SIS.txt',
#             'documents/cassini_iss/Cassini-ISS-Final-Report.pdf',
#             'documents/cassini_iss/Calibration-Report.zip'
#          ]),
#         # TODO: add test case for metadata when correct index files & _indexshelf-metadata
#         # are added
#     ]
# )
# def test_associated_abspaths(input_path, category, expected):
#     target_pdsfile = instantiate_target_pdsfile(input_path)
#     res = target_pdsfile.associated_abspaths(category=category)
#     result_paths = []
#     result_paths += pds4file.Pds4File.logicals_for_abspaths(res)
#     assert len(result_paths) != 0
#     for path in result_paths:
#         assert path in expected

##########################################################################################
