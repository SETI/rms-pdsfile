##########################################################################################
# pds4file/rules/uranus_occs_earthbased.py
##########################################################################################

import pdsfile.pds4file as pds4file
import translator
import re

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/data/.*/N[0-9_]+\.IMG',                        0, ('Narrow-angle image, VICAR',      'IMAGE'   )),
    (r'volumes/.*/data/.*/W[0-9_]+\.IMG',                        0, ('Wide-angle image, VICAR',        'IMAGE'   )),
    (r'volumes/.*/data/.*/extras(/\w+)*(|/)',                    0, ('Preview image collection',       'BROWDIR' )),
    (r'volumes/.*/data/.*/extras/.*\.(jpeg|jpeg_small|tiff)',    0, ('Preview image',                  'BROWSE'  )),
    (r'volumes/.*/COISS_0011/document/.*/[0-9]+\.[0-9]+(|/)',    0, ('Calibration report',             'INFODIR' )),
    (r'volumes/.*/data(|/\w*)',                                  0, ('Images grouped by SC clock',     'IMAGEDIR')),
    (r'calibrated/.*_calib\.img',                                0, ('Calibrated image, VICAR',        'IMAGE'   )),
    (r'calibrated/.*/data(|/\w+)',                               0, ('Calibrated images by SC clock',  'IMAGEDIR')),
    (r'calibrated/\w+(|/\w+)',                                   0, ('Calibrated image collection',    'IMAGEDIR')),
    (r'.*/thumbnail(/\w+)*',                                     0, ('Small browse images',            'BROWDIR' )),
    (r'.*/thumbnail/.*\.(gif|jpg|jpeg|jpeg_small|tif|tiff|png)', 0, ('Small browse image',             'BROWSE'  )),
    (r'.*/(tiff|full)(/\w+)*',                                   0, ('Full-size browse images',        'BROWDIR' )),
    (r'.*/(tiff|full)/.*\.(tif|tiff|png)',                       0, ('Full-size browse image',         'BROWSE'  )),
    (r'volumes/COISS_0xxx.*/COISS_0011/document/report',         0, ('&#11013; <b>ISS Calibration Report</b>',
                                                                                                       'INFO')),
    (r'(volumes/COISS_0xxx.*/COISS_0011/document/report/index.html)', 0,
            ('&#11013; <b>CLICK "index.html"</b> to view the ISS Calibration Report', 'INFO')),
    (r'volumes/COISS_0xxx.*/COISS_0011/document/.*user_guide.*\.pdf',
                                                                 0, ('&#11013; <b>ISS User Guide</b>', 'INFO')),
    (r'volumes/COISS_0xxx.*/COISS_0011/extras',                  0, ('CISSCAL calibration software',   'CODE')),
    (r'volumes/COISS_0xxx.*/COISS_0011/extras/cisscal',          0, ('CISSCAL source code (IDL)',      'CODE')),
    (r'volumes/COISS_0xxx.*/COISS_0011/extras/cisscal\.tar\.gz', 0, ('CISSCAL source code (download)', 'TARBALL')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
        (r'.*/(uranus_occs_earthbased/uranus_occ_u.*/data(.*|_[a-z]*])/.*)\.[a-z]{3}', 0,
        [r'previews/\1_full.png',
         r'previews/\1_med.png',
         r'previews/\1_small.png',
         r'previews/\1_thumb.png',
        ])
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([

    # COISS_1xxx and COISS_2xxx
    (r'.*/(COISS_[12]xxx.*/COISS_....)/(data|extras/\w+)/(\w+/[NW][0-9]{10}_[0-9]+).*', 0,
            [r'volumes/\1/data/\3.IMG',
             r'volumes/\1/data/\3.LBL',
             r'volumes/\1/extras/thumbnail/\3.IMG.jpeg_small',
             r'volumes/\1/extras/browse/\3.IMG.jpeg',
             r'volumes/\1/extras/full/\3.IMG.png',
             r'volumes/\1/extras/tiff/\3.IMG.tiff',
            ]),
    (r'.*/(COISS_[12]xxx.*/COISS_....)/(data|extras/\w+)(|/\w+)', 0,
            [r'volumes/\1/data\3',
             r'volumes/\1/extras/thumbnail\3',
             r'volumes/\1/extras/browse\3',
             r'volumes/\1/extras/full\3',
            ]),
    (r'.*/(COISS_[12]xxx.*/COISS_....)/extras', 0,
            r'volumes/\1/data'),
    (r'.*/(COISS_[12])999.*', 0,
            r'volumes/\1xxx'),
    (r'documents/COISS_0xxx.*', 0,
            [r'volumes/COISS_0xxx',
             r'volumes/COISS_1xxx',
             r'volumes/COISS_2xxx',
            ]),

    # COISS_3xxx
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)/(images/\w+[A-Z]+)(|_[a-z]+)\..*', 0,
            [r'volumes/\1/data/\3.IMG',
             r'volumes/\1/extras/browse/\3.IMG.jpeg',
             r'volumes/\1/extras/thumbnail/\3.IMG.jpeg_small',
             r'volumes/\1/extras/full/\3.IMG.png',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)/(maps/\w+_SMN).*', 0,
            [r'volumes/\1/data/\3.lbl',
             r'volumes/\1/data/\3.PDF',
             r'volumes/\1/extras/browse/\3.jpg',
             r'volumes/\1/extras/browse/\3_browse.jpg',
             r'volumes/\1/extras/browse/\3.PDF.jpeg',
             r'volumes/\1/extras/thumbnail/\3.jpg',
             r'volumes/\1/extras/thumbnail/\3_thumb.jpg',
             r'volumes/\1/extras/thumbnail/\3.PDF.jpeg',
             r'volumes/\1/extras/full/\3.PDF.png',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)(|/images|/maps)', 0,
            [r'volumes/\1/data/\3',
             r'volumes/\1/extras/browse/\3',
             r'volumes/\1/extras/thumbnail/\3',
             r'volumes/\1/extras/full/\3',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/extras', 0,
            r'volumes/\1/data'),
])

associations_to_calibrated = translator.TranslatorByRegex([
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_....)/(data|extras/\w+)/(\w+/[NW][0-9]{10}_[0-9]+).*', 0,
            [r'calibrated/\1/\3/data/\5_CALIB.IMG',
             r'calibrated/\1/\3/data/\5_CALIB.LBL',
            ]),
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_....)/(data|extras/\w+)(|/\w+)', 0,
            r'calibrated/\1/\3/data\5'),
    (r'.*/(COISS_[12])999.*', 0,
            r'calibrated/\1xxx'),
])

associations_to_previews = translator.TranslatorByRegex([

    # COISS_1xxx and COISS_2xxx
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_....)/(data|extras/\w+)/(\w+/[NW][0-9]{10}_[0-9]+).*', 0,
            [r'previews/\1/\3/data/\5_full.png',
             r'previews/\1/\3/data/\5_med.jpg',
             r'previews/\1/\3/data/\5_small.jpg',
             r'previews/\1/\3/data/\5_thumb.jpg',
            ]),
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_....)/(data|extras/\w+)(|/\w+)', 0,
            r'previews/\1/\3/data\5'),
    (r'.*/(COISS_[12])999.*', 0,
            r'previews/\1xxx'),

    # COISS_3xxx
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)/(images/\w+[A-Z]+)(|_[a-z]+)\..*', 0,
            [r'previews/\1/data/\3_full.jpg',
             r'previews/\1/data/\3_med.jpg',
             r'previews/\1/data/\3_small.jpg',
             r'previews/\1/data/\3_thumb.jpg',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)/(maps/\w+_SMN).*', 0,
            [r'previews/\1/data/\3_full.png',
             r'previews/\1/data/\3_med.png',
             r'previews/\1/data/\3_small.png',
             r'previews/\1/data/\3_thumb.png',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)(|/images|/maps)', 0,
            [r'previews/\1/data/\3',
             r'previews/\1/extras/browse/\3',
             r'previews/\1/extras/thumbnail/\3',
             r'previews/\1/extras/full/\3',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/extras', 0,
            r'previews/\1/data'),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_....)/(data|extras/w+)/\w+/([NW][0-9]{10}_[0-9]+).*', 0,
            [r'metadata/\1/\3/\3_index.tab/\5',
             r'metadata/\1/\3/\3_ring_summary.tab/\5',
             r'metadata/\1/\3/\3_moon_summary.tab/\5',
             r'metadata/\1/\3/\3_saturn_summary.tab/\5',
             r'metadata/\1/\3/\3_jupiter_summary.tab/\5',
            ]),
    (r'metadata/(COISS_.xxx/COISS_[12])...', 0,
            r'metadata/\g<1>999'),
    (r'metadata/(COISS_.xxx/COISS_[12]).../(COISS_.)..._(.*)\..*', 0,
            [r'metadata/\g<1>999/\g<2>999_\3.tab',
             r'metadata/\g<1>999/\g<2>999_\3.csv',
             r'metadata/\g<1>999/\g<2>999_\3.lbl',
            ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'(volumes|calibrated)/COISS_[0-3]xxx(|_[\w\.]+)(|/COISS_[0-3]\d\d\d)', 0,
            r'documents/COISS_0xxx/*'),
    (r'(volumes|calibrated)/COISS_[0-3]xxx.*/COISS_[0-3]\d\d\d/.+', 0,
            r'documents/COISS_0xxx'),
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
    (r'volumes/.*\.(IMG|LBL)',                      0, ('Cassini ISS',  0,  'coiss_raw',    'Raw Image',                 True )),
    (r'calibrated/.*_CALIB\.(IMG|LBL)',             0, ('Cassini ISS', 10,  'coiss_calib',  'Calibrated Image',          True )),
    (r'volumes/.*/extras/thumbnail/.*\.jpeg_small', 0, ('Cassini ISS', 110, 'coiss_thumb',  'Extra Preview (thumbnail)', False)),
    (r'volumes/.*/extras/browse/.*\.jpeg',          0, ('Cassini ISS', 120, 'coiss_medium', 'Extra Preview (medium)',    False)),
    (r'volumes/.*/extras/(tiff|full)/.*\.\w+',      0, ('Cassini ISS', 130, 'coiss_full',   'Extra Preview (full)',      False)),
    (r'volumes/.*/extras/(tiff|full)/.*\.\w+',      0, ('Cassini ISS', 130, 'coiss_full',   'Extra Preview (full)',      False)),
    # Documentation
    (r'documents/COISS_0xxx/.*',                    0, ('Cassini ISS', 140, 'coiss_documentation', 'Documentation', False)),
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
# Note: instead of "Generic InSb High Speed Photometer" that the ground-based telescopes use, the KAO uses "Generic Visual High Speed Photometer", hence using "vis" instead of "insb" in the instrument component of the OPUS ID
opus_id = translator.TranslatorByRegex([
    (r'.*/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_([ei])(gress|ngress)\.[a-z]{3}', 0, r'kao0m91-vis-occ-1977-069-u0-uranus-\1'), 
    (r'.*/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_counts-v-time_occult\.[a-z]{3}', 0, r'kao0m91-vis-occ-1977-069-u0-ringpl-b'), # entire occultation hence "-b" and entire ring system hence "ringpl"? 
    (r'.*/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_([ei])(gress|ngress)_\d{3,4}m\.[a-z]{3}', 0, r'kao0m91-vis-occ-1977-069-u0-ringpl-\1'), # entire ring system, hence "ringpl"? 
    (r'.*/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_counts-v-time_rings_([ei])(gress|ngress)\.[a-z]{3}', 0, r'kao0m91-vis-occ-1977-069-u0-\1'), # for ring only, if no ring name is specified then more than one ring is covered 
    (r'.*/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_([a-z]+)_([ei])(gress|ngress)_\d{3,4}m\.[a-z]{3}', 0, r'kao0m91-vis-occ-1977-069-u0-\1-\2'),
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'(uranus_occ)_.*', 0, r'\1s_earthbased'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'kao0m91-vis-occ-1977-069-u0-uranus-([ei])', 0, r'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_\1*gress.tab'),
    (r'kao0m91-vis-occ-1977-069-u0-ringpl-b', 0, r'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_counts-v-time_occult.tab'),
    (r'kao0m91-vis-occ-1977-069-u0-ringpl-([ei])', 0, r'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_\1*gress_100m.tab'), # highest resolution is primary filespec
    (r'kao0m91-vis-occ-1977-069-u0-([ei])', 0, r'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_counts-v-time_rings_\1*.tab'),
    (r'kao0m91-vis-occ-1977-069-u0-([a-z]*)-([ei])', 0, r'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_\1_\2*_100m.tab'), 
])

##########################################################################################
# Subclass definition
##########################################################################################

class uranus_occs_earthbased(pds4file.Pds4File):

    pds4file.Pds4File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('uranus_occ_u0_kao_91cm', re.I, 'uranus_occs_earthbased')]) + \
                                          pds4file.Pds4File.VOLSET_TRANSLATOR

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
    ASSOCIATIONS['volumes']    += associations_to_volumes
    ASSOCIATIONS['calibrated'] += associations_to_calibrated
    ASSOCIATIONS['previews']   += associations_to_previews
    ASSOCIATIONS['metadata']   += associations_to_metadata
    ASSOCIATIONS['documents']  += associations_to_documents

    pds4file.Pds4File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds4file.Pds4File.FILESPEC_TO_BUNDLESET

#    def FILENAME_KEYLEN(self):
#        if self.volset[:10] == 'COISS_3xxx':
#            return 0
#        else:
#            return 11   # trim off suffixes

# Global attribute shared by all subclasses
pds4file.Pds4File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'kao0m91-vis-occ-1977-069-u0.*', 0, uranus_occs_earthbased)]) + \
                                        pds4file.Pds4File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds4file.Pds4File.SUBCLASSES['uranus_occs_earthbased'] = uranus_occs_earthbased

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

@pytest.mark.parametrize(
    'input_path,expected',
    [
        ('volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.IMG',
         {('Cassini ISS',
           0,
           'coiss_raw',
           'Raw Image',
           True): ['volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.IMG',
                   'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                   'volumes/COISS_1xxx/COISS_1001/label/prefix.fmt',
                   'volumes/COISS_1xxx/COISS_1001/label/tlmtab.fmt'],
          ('Cassini ISS',
           110,
           'coiss_thumb',
           'Extra Preview (thumbnail)',
           False): ['volumes/COISS_1xxx/COISS_1001/extras/thumbnail/1294561143_1295221348/W1294561202_1.IMG.jpeg_small'],
          ('Cassini ISS',
           120,
           'coiss_medium',
           'Extra Preview (medium)',
           False): ['volumes/COISS_1xxx/COISS_1001/extras/browse/1294561143_1295221348/W1294561202_1.IMG.jpeg'],
          ('Cassini ISS',
           10,
           'coiss_calib',
           'Calibrated Image',
           True): ['calibrated/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1_CALIB.IMG',
                   'calibrated/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1_CALIB.LBL',
                   'calibrated/COISS_1xxx_v1/COISS_1001/data/1294561143_1295221348/W1294561202_1_CALIB.IMG',
                   'calibrated/COISS_1xxx_v1/COISS_1001/data/1294561143_1295221348/W1294561202_1_CALIB.LBL',
                   'calibrated/COISS_1xxx_v2/COISS_1001/data/1294561143_1295221348/W1294561202_1_CALIB.IMG',
                   'calibrated/COISS_1xxx_v2/COISS_1001/data/1294561143_1295221348/W1294561202_1_CALIB.LBL'],
          ('browse',
           10,
           'browse_thumb',
           'Browse Image (thumbnail)',
           False): ['previews/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1_thumb.jpg'],
          ('browse',
           20,
           'browse_small',
           'Browse Image (small)',
           False): ['previews/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1_small.jpg'],
          ('browse',
           30,
           'browse_medium',
           'Browse Image (medium)',
           False): ['previews/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1_med.jpg'],
          ('browse',
           40,
           'browse_full',
           'Browse Image (full)',
           True): ['previews/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1_full.png'],
          ('metadata',
           20,
           'planet_geometry',
           'Planet Geometry Index',
           False): ['metadata/COISS_1xxx/COISS_1001/COISS_1001_jupiter_summary.tab',
                    'metadata/COISS_1xxx/COISS_1001/COISS_1001_jupiter_summary.lbl'],
          ('metadata',
           30,
           'moon_geometry',
           'Moon Geometry Index',
           False): ['metadata/COISS_1xxx/COISS_1001/COISS_1001_moon_summary.tab',
                    'metadata/COISS_1xxx/COISS_1001/COISS_1001_moon_summary.lbl'],
          ('metadata',
           40,
           'ring_geometry',
           'Ring Geometry Index',
           False): ['metadata/COISS_1xxx/COISS_1001/COISS_1001_ring_summary.tab',
                    'metadata/COISS_1xxx/COISS_1001/COISS_1001_ring_summary.lbl'],
          ('metadata',
           10,
           'inventory',
           'Target Body Inventory',
           False): ['metadata/COISS_1xxx/COISS_1001/COISS_1001_inventory.csv',
                    'metadata/COISS_1xxx/COISS_1001/COISS_1001_inventory.lbl'],
          ('metadata',
           5,
           'rms_index',
           'RMS Node Augmented Index',
           False): ['metadata/COISS_1xxx/COISS_1001/COISS_1001_index.tab',
                    'metadata/COISS_1xxx/COISS_1001/COISS_1001_index.lbl'],
          ('Cassini ISS',
           140,
           'coiss_documentation',
           'Documentation',
           False): ['documents/COISS_0xxx/VICAR-File-Format.pdf',
                    'documents/COISS_0xxx/ISS-Users-Guide.pdf',
                    'documents/COISS_0xxx/ISS-Users-Guide.docx',
                    'documents/COISS_0xxx/Data-Product-SIS.txt',
                    'documents/COISS_0xxx/Data-Product-SIS.pdf',
                    'documents/COISS_0xxx/Cassini-ISS-Final-Report.pdf',
                    'documents/COISS_0xxx/Calibration-Theoretical-Basis.pdf',
                    'documents/COISS_0xxx/Calibration-Plan.pdf',
                    'documents/COISS_0xxx/CISSCAL-Users-Guide.pdf',
                    'documents/COISS_0xxx/Archive-SIS.txt',
                    'documents/COISS_0xxx/Archive-SIS.pdf']}
        ),
    ]
)
def xtest_opus_products(input_path, expected):
    opus_products_test(input_path, expected)

def test_opus_id_to_primary_logical_path():
    TESTS = [
 	'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_ingress.tab',
        'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.tab',
        'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_counts-v-time_occult.tab',
 	'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_egress_100m.tab', # highest-resolution used as primary
  	'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_ingress_100m.tab',
   	'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_counts-v-time_rings_egress.tab',
   	'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_counts-v-time_rings_ingress.tab',
        'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_100m.tab',
]

    for logical_path in TESTS:
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
