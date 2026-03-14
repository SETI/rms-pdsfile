##########################################################################################
# pds4file/rules/cassini_iss_fring_mosaics_rsfrench2025.py
##########################################################################################

import pdsfile.pds4file as pds4file
import translator
import re

from .cassini_iss_fring_mosaics_rsfrench2025_primary_filespec import PRIMARY_FILESPEC_LIST

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([

])

##########################################################################################
# VIEWABLES
##########################################################################################
# Use .png files under browse_mosaic_bkg_sub as previews
default_viewables = translator.TranslatorByRegex([
    (r'.*/(cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*)/(data|browse)_mosaic.*/((iss|iosic)_[a-zA-Z0-9_]*)/(iss|iosic)_[a-zA-Z0-9_]*_mosaic.*\.[a-z]{3,4}', 0,
     [
         r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_full.png',
         r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_med.png',
         r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_small.png',
         r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_thumb.png',
     ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_bundles = translator.TranslatorByRegex([
    (r'.*/(cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*)/(data|browse)_mosaic.*/((iss|iosic)_[a-zA-Z0-9_]*)/(iss|iosic)_[a-zA-Z0-9_]*_mosaic.*\.[a-z]{3,4}', 0,
        [
            # data_mosaic
            r'bundles/\1/data_mosaic/\3/\3_mosaic_metadata_params.tab',
            r'bundles/\1/data_mosaic/\3/\3_mosaic_metadata_src_imgs.tab',
            r'bundles/\1/data_mosaic/\3/\3_mosaic.img',
            r'bundles/\1/data_mosaic/\3/\3_mosaic.lblx',
            # data_mosaic_bkg_sub
            r'bundles/\1/data_mosaic_bkg_sub/\3/\3_mosaic_bkg_sub_metadata_params.tab',
            r'bundles/\1/data_mosaic_bkg_sub/\3/\3_mosaic_bkg_sub_metadata_src_imgs.tab',
            r'bundles/\1/data_mosaic_bkg_sub/\3/\3_mosaic_bkg_sub.img',
            r'bundles/\1/data_mosaic_bkg_sub/\3/\3_mosaic_bkg_sub.lblx',
            # browse_mosaic
            r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_full.png',
            r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_med.png',
            r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_small.png',
            r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_thumb.png',
            r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic.lblx',
            # browse_mosaic_bkg_sub
            r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_full.png',
            r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_med.png',
            r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_small.png',
            r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_thumb.png',
            r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub.lblx',
        ]),
])

# Use .png files under browse_mosaic and browse_mosaic_bkg_sub as previews
associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*)/(data|browse)_mosaic.*/((iss|iosic)_[a-zA-Z0-9_]*)/(iss|iosic)_[a-zA-Z0-9_]*_mosaic.*\.[a-z]{3,4}', 0,
        [
            # browse_mosaic
            r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_full.png',
            r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_med.png',
            r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_small.png',
            r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_thumb.png',
            r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic.lblx',
            # browse_mosaic_bkg_sub
            r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_full.png',
            r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_med.png',
            r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_small.png',
            r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_thumb.png',
            r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub.lblx',
        ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'.*/(cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*)/(data|browse)_mosaic.*/((iss|iosic)_[a-zA-Z0-9_]*)/(iss|iosic)_[a-zA-Z0-9_]*_mosaic.*\.[a-z]{3,4}', 0,
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
    # data_mosaic
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/data_mosaic/(iss|iosic)_.*/(iss|iosic)_.*\.(img|lblx)',              0, ('Cassini ISS F Ring Mosaics', 10, 'coiss_f_ring_mosaic', 'Mosaic', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/data_mosaic/(iss|iosic)_.*/(iss|iosic)_.*metadata.*\.tab',              0, ('Cassini ISS F Ring Mosaics', 20, 'coiss_f_ring_mosaic_metadata', 'Mosaic Metadata', True)),

    # data_mosaic_bkg_sub
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/data_mosaic_bkg_sub/(iss|iosic)_.*/(iss|iosic)_.*\.(img|lblx)', 0, ('Cassini ISS F Ring Mosaics', 30, 'coiss_f_ring_mosaic_bkg_sub', 'Background-Subtracted Mosaic', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/data_mosaic_bkg_sub/(iss|iosic)_.*/(iss|iosic)_.*metadata.*\.tab', 0, ('Cassini ISS F Ring Mosaics', 40, 'coiss_f_ring_mosaic_bkg_sub_metadata', 'Background-Subtracted Mosaic Metadata', True)),

    # browse_mosaic
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic/(iss|iosic)_.*/(iss|iosic)_.*thumb.*\.png',            0, ('Cassini ISS F Ring Mosaics', 50, 'coiss_f_ring_mosaic_browse_thumb', 'Browse Mosaic Image (thumbnail)', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic/(iss|iosic)_.*/(iss|iosic)_.*small.*\.png',            0, ('Cassini ISS F Ring Mosaics', 60, 'coiss_f_ring_mosaic_browse_small', 'Browse Mosaic Image (small)', True)),    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic/(iss|iosic)_.*/(iss|iosic)_.*med.*\.png',            0, ('Cassini ISS F Ring Mosaics', 70, 'coiss_f_ring_mosaic_browse_med', 'Browse Mosaic Image (medium)', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic/(iss|iosic)_.*/(iss|iosic)_.*full.*\.png',            0, ('Cassini ISS F Ring Mosaics', 80, 'coiss_f_ring_mosaic_browse_full', 'Browse Mosaic Image (full)', True)),

    # browse_mosaic_bkg_sub
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic_bkg_sub/(iss|iosic)_.*/(iss|iosic)_.*thumb.*\.png',            0, ('Cassini ISS F Ring Mosaics', 90, 'coiss_f_ring_mosaic_browse_bkg_sub_thumb', 'Browse Background-Subtracted Mosaic Image (thumbnail)', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic_bkg_sub/(iss|iosic)_.*/(iss|iosic)_.*small.*\.png',            0, ('Cassini ISS F Ring Mosaics', 100, 'coiss_f_ring_mosaic_browse_bkg_sub_small', 'Browse Background-Subtracted Mosaic Image (small)', True)),    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic_bkg_sub/(iss|iosic)_.*/(iss|iosic)_.*med.*\.png',            0, ('Cassini ISS F Ring Mosaics', 110, 'coiss_f_ring_mosaic_browse_bkg_sub_med', 'Browse Background-Subtracted Mosaic Image (medium)', True)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_mosaic_bkg_sub/(iss|iosic)_.*/(iss|iosic)_.*full.*\.png',            0, ('Cassini ISS F Ring Mosaics', 120, 'coiss_f_ring_mosaic_browse_bkg_sub_full', 'Browse Background-Subtracted Mosaic Image (full)', True)),

    # index under document/
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/document/supplemental/.*_index\.(lblx|tab)',               0, ('Cassini ISS F Ring Mosaics', 130, 'coiss_f_ring_global_index', 'Global Index', False)),

    # document
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/(readme.txt|document/user_guide/.*mosaic.*\.(lblx|pdf))',               0, ('Cassini ISS F Ring Mosaics', 140, 'coiss_f_ring_documentation', 'Documentation', False)),

    # Reprojected Images
    # data_reproj_img from cassini_iss_fring_mosaics_rsfrench2025
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/data_reproj_img/(iss|iosic)_.*/.*_reproj_.*.*\.(img|lblx|txt)',              0, ('Cassini ISS F Ring Reprojected Image', 150, 'coiss_f_ring_reproj_img', 'Reprojected Image', False)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/data_reproj_img/(iss|iosic)_.*/.*_reproj_img_metadata_params\.tab',              0, ('Cassini ISS F Ring Reprojected Image', 160, 'coiss_f_ring_reproj_img_metadata', 'Reprojected Image Metadata', False)),
    # brose_reproj_img cassini_iss_fring_mosaics_rsfrench2025
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_reproj_img/(iss|iosic)_.*/.*_browse_reproj_img_thumb\.png',              0, ('Cassini ISS F Ring Reprojected Image', 170, 'coiss_f_ring_browse_reproj_img_thumb', 'Browse Reprojected Image (thumbnail)', False)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_reproj_img/(iss|iosic)_.*/.*_browse_reproj_img_small\.png',              0, ('Cassini ISS F Ring Reprojected Image', 180, 'coiss_f_ring_browse_reproj_img_small', 'Browse Reprojected Image (small)', False)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_reproj_img/(iss|iosic)_.*/.*_browse_reproj_img_med\.png',              0, ('Cassini ISS F Ring Reprojected Image', 190, 'coiss_f_ring_browse_reproj_img_med', 'Browse Reprojected Image (medium)', False)),
    (r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/browse_reproj_img/(iss|iosic)_.*/.*_browse_reproj_img_full\.png',              0, ('Cassini ISS F Ring Reprojected Image', 200, 'coiss_f_ring_browse_reproj_img_full', 'Browse Reprojected Image (full)', False)),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

opus_products = translator.TranslatorByRegex([
    (r'bundles/(cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*)/(data|browse)_mosaic.*/((iss|iosic)_[a-zA-Z0-9_]*)/(iss|iosic)_[a-zA-Z0-9_]*_mosaic.*\.[a-z]{3,4}', 0,
     [
        # bundles data_mosaic/
        r'bundles/\1/data_mosaic/\3/\3_mosaic.img',
        r'bundles/\1/data_mosaic/\3/\3_mosaic.lblx',
        # r'bundles/\1/data_mosaic/\3/\3_mosaic_metadata.*.tab',
        r'bundles/\1/data_mosaic/\3/\3_mosaic_metadata_params.tab',
        r'bundles/\1/data_mosaic/\3/\3_mosaic_metadata_src_imgs.tab',
        # bundles data_mosaic_bkg_sub
        r'bundles/\1/data_mosaic_bkg_sub/\3/\3_mosaic_bkg_sub.img',
        r'bundles/\1/data_mosaic_bkg_sub/\3/\3_mosaic_bkg_sub.lblx',
        r'bundles/\1/data_mosaic_bkg_sub/\3/\3_mosaic_bkg_sub_metadata_params.tab',
        r'bundles/\1/data_mosaic_bkg_sub/\3/\3_mosaic_bkg_sub_metadata_src_imgs.tab',
        # bundles readme.txt
        r'bundles/\1/readme.txt',
        # document
        r'bundles/\1/document/user_guide/f-ring-mosaics-user-guide.lblx',
        r'bundles/\1/document/user_guide/f-ring-mosaics-user-guide.pdf',
        r'bundles/\1/document/supplemental/global_mosaic_bkg_sub_index.lblx',
        r'bundles/\1/document/supplemental/global_mosaic_bkg_sub_index.tab',
        r'bundles/\1/document/supplemental/global_mosaic_index.lblx',
        r'bundles/\1/document/supplemental/global_mosaic_index.tab',
        # bundles browse_mosaic/
        r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic.lblx',
        # bundles browse_mosaic_bkg_sub/
        r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub.lblx',
        # previews (under browse_mosaic*)
        r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_full.png',
        r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_med.png',
        r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_small.png',
        r'bundles/\1/browse_mosaic/\3/\3_browse_mosaic_thumb.png',
        r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_full.png',
        r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_med.png',
        r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_small.png',
        r'bundles/\1/browse_mosaic_bkg_sub/\3/\3_browse_mosaic_bkg_sub_thumb.png',
     ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025[^/]*/(data|browse)_mosaic.*/((iss|iosic)_[a-zA-Z0-9_]*)/(iss|iosic)_[a-zA-Z0-9_]*_mosaic.*\.[a-z]{3,4}', 0, r'co-iss-fring-mosaic-\2')
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
# Archives
##########################################################################################
archive_paths = translator.TranslatorByRegex([
    # input is the cassini_iss_fring_mosaics_rsfrench2025 bundle set
    (r'.*(bundles|metadata|previews|diagrams)/(cassini_iss_fring_mosaics_rsfrench2025)(|/)$', 0, [
        r'archives-\1/\2/\2/bundle_non_data_browse_collections.tar.gz',
        r'archives-\1/\2/\2/data_browse_mosaic.tar.gz',
        r'archives-\1/\2/\2/data_browse_reproj.tar.gz',
    ]),
])

archive_dirs = translator.TranslatorByRegex([
    (r'.*archives-(.*/cassini_iss_fring_mosaics_rsfrench2025)/(cassini_iss_fring_mosaics_rsfrench2025)/bundle_non_data_browse_collections\.tar\.gz', 0, [
        r'\1/\2/bundle.lblx',
        r'\1/\2/context',
        r'\1/\2/document',
        r'\1/\2/readme.txt',
        r'\1/\2/spice_kernels',
        r'\1/\2/xml_schema',
    ]),
    (r'.*archives-(.*/cassini_iss_fring_mosaics_rsfrench2025)/(cassini_iss_fring_mosaics_rsfrench2025)/data_browse_mosaic\.tar\.gz', 0, [
        r'\1/\2/browse_mosaic',
        r'\1/\2/browse_mosaic_bkg_sub',
        r'\1/\2/data_mosaic',
        r'\1/\2/data_mosaic_bkg_sub',
    ]),
    (r'.*archives-(.*/cassini_iss_fring_mosaics_rsfrench2025)/(cassini_iss_fring_mosaics_rsfrench2025)/data_browse_reproj\.tar\.gz', 0, [
        r'\1/\2/browse_reproj_img',
        r'\1/\2/data_reproj_img',
    ]),
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
