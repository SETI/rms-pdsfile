##########################################################################################
# pds3file/rules/EBROCC_xxxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
import translator
import re

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/DATA',         re.I, ('Data files by observatory',      'SERIESDIR')),
    (r'volumes/.*/DATA/\w+',     re.I, ('Data files by observatory',      'SERIESDIR')),
    (r'volumes/.*/GEOMETRY/\w+', re.I, ('Geometry files by observatory',  'GEOMDIR' )),
    (r'volumes/.*/BROWSE/\w+',   re.I, ('Browse diagrams by observatory', 'BROWDIR' )),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'.*\.lbl', re.I, ''),
    (r'volumes/EBROCC_xxxx(|_v[0-9\.]+)/(EBROCC_....)/(DATA|BROWSE)/(\w+/\w+)\.(TAB|LBL)', 0,
            [r'previews/EBROCC_xxxx/\2/\3/\4_full.jpg',
             r'previews/EBROCC_xxxx/\2/\3/\4_med.jpg',
             r'previews/EBROCC_xxxx/\2/\3/\4_small.jpg',
             r'previews/EBROCC_xxxx/\2/\3/\4_thumb.jpg',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    (r'.*/EBROCC_xxxx(|_v[0-9\.]+)/(EBROCC_....)/(DATA|BROWSE|SORCDATA|GEOMETRY)(|/\w+)', 0,
            [r'volumes/EBROCC_xxxx\1/\2/DATA\4',
             r'volumes/EBROCC_xxxx\1/\2/BROWSE\4',
             r'volumes/EBROCC_xxxx\1/\2/GEOMETRY\4',
             r'volumes/EBROCC_xxxx\1/\2/SORCDATA\4',
            ]),
    (r'.*/EBROCC_xxxx(|_v[0-9\.]+)/(EBROCC_....)/(DATA|BROWSE|SORCDATA|GEOMETRY)/(\w+/\w{3}_[EI]).*', 0,
            [r'volumes/EBROCC_xxxx\1/\2/DATA\4PD.LBL',
             r'volumes/EBROCC_xxxx\1/\2/DATA\4PD.TAB',
             r'volumes/EBROCC_xxxx\1/\2/BROWSE\4GB.LBL',
             r'volumes/EBROCC_xxxx\1/\2/BROWSE\4GB.PDF',
             r'volumes/EBROCC_xxxx\1/\2/BROWSE\4GB.PS',
             r'volumes/EBROCC_xxxx\1/\2/GEOMETRY\4GD.LBL',
             r'volumes/EBROCC_xxxx\1/\2/GEOMETRY\4GD.TAB',
             r'volumes/EBROCC_xxxx\1/\2/SORCDATA\4*',
            ]),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/EBROCC_xxxx(|_v[0-9\.]+)/(EBROCC_....)/(DATA|BROWSE|SORCDATA|GEOMETRY)(|/\w+)', 0,
           [r'previews/EBROCC_xxxx/\2/DATA\4',
            r'previews/EBROCC_xxxx/\2/BROWSE\4',
            r'previews/EBROCC_xxxx/\2/GEOMETRY\4',
            r'previews/EBROCC_xxxx/\2/SORCDATA\4',
           ]),
    (r'.*/EBROCC_xxxx(|_v[0-9\.]+)/(EBROCC_....)/(DATA|BROWSE|SORCDATA|GEOMETRY)/(\w+/\w{3}_[EI]).*', 0,
           [r'previews/EBROCC_xxxx/\2/DATA\4PD_full.jpg',
            r'previews/EBROCC_xxxx/\2/DATA\4PD_med.jpg',
            r'previews/EBROCC_xxxx/\2/DATA\4PD_small.jpg',
            r'previews/EBROCC_xxxx/\2/DATA\4PD_thumb.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE\4GB_full.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE\4GB_med.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE\4GB_small.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE\4GB_thumb.jpg',
           ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/EBROCC_xxxx(|_v[0-9\.]+)/(EBROCC_....)/(DATA|BROWSE|SORCDATA|GEOMETRY)/\w+/(\w+)\.\w+', 0,
           r'metadata/EBROCC_xxxx/\2/\2_index.tab/\4'),
    (r'volumes/EBROCC_xxxx(|_v[0-9\.]+)/(EBROCC_....)/DATA/\w+/(\w+)\.\w+', 0,
           [r'metadata/EBROCC_xxxx/\2/\2_profile_index.tab/\4',
            r'metadata/EBROCC_xxxx/\2/\2_supplemental_index.tab/\4',
           ]),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'(volumes|previews)/EBROCC_xxxx.*/(DATA|BROWSE|SORCDATA|GEOMETRY)/.*', 0, (True, True, False)),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'volumes/.*/DATA/\w+/\w+\.(TAB|LBL)',          0, ('Earth-based Occultations',  0, 'ebro_profile', 'Occultation Profile', True)),
    (r'volumes/.*/GEOMETRY/\w+/\w+\.(TAB|LBL)',      0, ('Earth-based Occultations', 10, 'ebro_geom',    'Geometry Table',      True)),
    (r'volumes/.*/BROWSE/\w+/\w+PB\.(PDF|PS|LBL)',   0, ('Earth-based Occultations', 20, 'ebro_preview', 'Preview Plot',        True)),
    (r'volumes/.*/BROWSE/\w+/\w+GB\.(PDF|PS|LBL)',   0, ('Earth-based Occultations', 30, 'ebro_diagram', 'Geometry Diagram',    False)),
    (r'volumes/.*/SORCDATA/\w+/\w+_GEOMETRY\..*',    0, ('Earth-based Occultations', 40, 'ebro_source',  'Source Data',         False)),
    (r'volumes/.*/SORCDATA/\w+/\w+GRESS\.(OUT|LBL)', 0, ('Earth-based Occultations', 40, 'ebro_source',  'Source Data',         False)),
])

##########################################################################################
# OPUS_FORMAT
##########################################################################################

opus_format = translator.TranslatorByRegex([
    (r'.*\_GEOMETRY.DAT',    0, ('ASCII', 'Text')),
    (r'.*\_(E|IN)GRESS.OUT', 0, ('ASCII', 'Text')),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

opus_products = translator.TranslatorByRegex([
    (r'.*/EBROCC_xxxx(|_v[0-9\.]+)/(EBROCC_....)/(DATA|BROWSE|SORCDATA|GEOMETRY)/(\w+/\w{3}_[EI]).*', 0,
           [r'volumes/EBROCC_xxxx*/\2/DATA/\4PD.LBL',
            r'volumes/EBROCC_xxxx*/\2/DATA/\4PD.TAB',
            r'volumes/EBROCC_xxxx*/\2/BROWSE/\4GB.LBL',
            r'volumes/EBROCC_xxxx*/\2/BROWSE/\4GB.PDF',
            r'volumes/EBROCC_xxxx*/\2/BROWSE/\4GB.PS',
            r'volumes/EBROCC_xxxx*/\2/BROWSE/\4PB.LBL',
            r'volumes/EBROCC_xxxx*/\2/BROWSE/\4PB.PDF',
            r'volumes/EBROCC_xxxx*/\2/BROWSE/\4PB.PS',
            r'volumes/EBROCC_xxxx*/\2/GEOMETRY/\4GD.LBL',
            r'volumes/EBROCC_xxxx*/\2/GEOMETRY/\4GD.TAB',
            r'volumes/EBROCC_xxxx*/\2/SORCDATA/\4*',
            r'previews/EBROCC_xxxx/\2/DATA/\4PD_full.jpg',
            r'previews/EBROCC_xxxx/\2/DATA/\4PD_med.jpg',
            r'previews/EBROCC_xxxx/\2/DATA/\4PD_small.jpg',
            r'previews/EBROCC_xxxx/\2/DATA/\4PD_thumb.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE/\4GB_full.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE/\4GB_med.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE/\4GB_small.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE/\4GB_thumb.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE/\4PB_full.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE/\4PB_med.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE/\4PB_small.jpg',
            r'previews/EBROCC_xxxx/\2/BROWSE/\4PB_thumb.jpg',
            r'metadata/EBROCC_xxxx/\2/\2_index.lbl',
            r'metadata/EBROCC_xxxx/\2/\2_index.tab',
            r'metadata/EBROCC_xxxx/\2/\2_profile_index.lbl',
            r'metadata/EBROCC_xxxx/\2/\2_profile_index.tab',
            r'metadata/EBROCC_xxxx/\2/\2_supplemental_index.lbl',
            r'metadata/EBROCC_xxxx/\2/\2_supplemental_index.tab',
           ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/EBROCC_xxxx.*/\w+/ESO1M/ES1_(I|E).*',  0, r'eso1m-apph-occ-1989-184-28sgr-#LOWER#\1'),
    (r'.*/EBROCC_xxxx.*/\w+/ESO22M/ES2_(I|E).*', 0, r'eso22m-apph-occ-1989-184-28sgr-#LOWER#\1'),
    (r'.*/EBROCC_xxxx.*/\w+/IRTF/IRT_(I|E).*',   0, r'irtf-urac-occ-1989-184-28sgr-#LOWER#\1'),
    (r'.*/EBROCC_xxxx.*/\w+/LICK1M/LIC_(I|E).*', 0, r'lick1m-ccdc-occ-1989-184-28sgr-#LOWER#\1'),
    (r'.*/EBROCC_xxxx.*/\w+/MCD27M/MCD_(I|E).*', 0, r'mcd27m-iirar-occ-1989-184-28sgr-#LOWER#\1'),
    (r'.*/EBROCC_xxxx.*/\w+/PAL200/PAL_(I|E).*', 0, r'pal200-circ-occ-1989-184-28sgr-#LOWER#\1')
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'eso1m-apph-occ-1989-184-28sgr-(.*)',   0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_#UPPER#\1PD.TAB'),
    (r'eso22m-apph-occ-1989-184-28sgr-(.*)',  0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO22M/ES2_#UPPER#\1PD.TAB'),
    (r'irtf-urac-occ-1989-184-28sgr-(.*)',    0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/IRTF/IRT_#UPPER#\1PD.TAB'),
    (r'lick1m-ccdc-occ-1989-184-28sgr-(.*)',  0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/LICK1M/LIC_#UPPER#\1PD.TAB'),
    (r'mcd27m-iirar-occ-1989-184-28sgr-(.*)', 0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/MCD27M/MCD_#UPPER#\1PD.TAB'),
    (r'pal200-circ-occ-1989-184-28sgr-(.*)',  0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/PAL200/PAL_#UPPER#\1PD.TAB'),
])

##########################################################################################
# DATA_SET_ID
##########################################################################################

data_set_id = translator.TranslatorByRegex([
    (r'.*volumes/EBROCC_xxxx/EBROCC_0001.*/(ES1|ESO1M).*',  0, r'ESO1M-SR-APPH-4-OCC-V1.0'),
    (r'.*volumes/EBROCC_xxxx/EBROCC_0001.*/(ES2|ESO22M).*', 0, r'ESO22M-SR-APPH-4-OCC-V1.0'),
    (r'.*volumes/EBROCC_xxxx/EBROCC_0001.*/IRT.*',          0, r'IRTF-SR-URAC-4-OCC-V1.0'),
    (r'.*volumes/EBROCC_xxxx/EBROCC_0001.*/LIC.*',          0, r'LICK1M-SR-CCDC-4-OCC-V1.0'),
    (r'.*volumes/EBROCC_xxxx/EBROCC_0001.*/MCD.*',          0, r'MCD27M-SR-IIRAR-4-OCC-V1.0'),
    (r'.*volumes/EBROCC_xxxx/EBROCC_0001.*/PAL.*',          0, r'PAL200-SR-CIRC-4-OCC-V1.0')
])

##########################################################################################
# FILESPEC_TO_VOLSET
##########################################################################################

filespec_to_volset = translator.TranslatorByRegex([
    (r'EBROCC_0001.*', 0, r'EBROCC_xxxx'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class EBROCC_xxxx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('EBROCC_xxxx', re.I, 'EBROCC_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_FORMAT = opus_format + pds3file.Pds3File.OPUS_FORMAT
    OPUS_PRODUCTS = opus_products
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    DATA_SET_ID = data_set_id

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']  += associations_to_volumes
    ASSOCIATIONS['previews'] += associations_to_previews
    ASSOCIATIONS['metadata'] += associations_to_metadata

# Global attribute shared by all subclasses
pds3file.Pds3File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'.*-28sgr-.*', 0, EBROCC_xxxx)]) + \
                                        pds3file.Pds3File.OPUS_ID_TO_SUBCLASS

pds3file.Pds3File.FILESPEC_TO_VOLSET = filespec_to_volset + pds3file.Pds3File.FILESPEC_TO_VOLSET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['EBROCC_xxxx'] = EBROCC_xxxx

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

def test_opus_products_count():

    TESTS = [
        (2, 'volumes.*/DATA/.*'),
        (6, 'volumes.*/BROWSE/.*'),
        (2, 'volumes.*/GEOMETRY/.*'),
        (4, 'volumes.*/SORCDATA/.*'),
        (4, 'previews.*/DATA/.*'),
        (8, 'previews/.*/BROWSE/.*'),
        (6, 'metadata.*index.*'),
        (2, 'metadata.*profile.*'),
        (2, 'metadata.*supplemental.*'),
    ]

    PATH = 'volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD.LBL'
    abspaths = translate_all(opus_products, PATH)
    trimmed = [p.rpartition('holdings/')[-1] for p in abspaths]
    for (count, pattern) in TESTS:
        subset = [p for p in trimmed if re.fullmatch(pattern, p)]
        assert len(subset) == count, f'Miscount: {pattern} {len(subset)} {trimmed}'

@pytest.mark.parametrize(
# Allow duplicated '/volumes/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EGB.LBL'
# and '/volumes/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EPB.LBL' here. OPUS
# will ignore the duplicated items
    'input_path,expected',
    [
        ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD.TAB',
        {('Earth-based Occultations',
          0,
          'ebro_profile',
          'Occultation Profile',
          True): ['volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD.TAB',
                  'volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD.LBL'],
         ('Earth-based Occultations',
          30,
          'ebro_diagram',
          'Geometry Diagram',
          False): ['volumes/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EGB.PS',
                   'volumes/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EGB.PDF',
                   'volumes/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EGB.LBL',
                   'volumes/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EGB.LBL'],
         ('Earth-based Occultations',
          20,
          'ebro_preview',
          'Preview Plot',
          True): ['volumes/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EPB.PS',
                  'volumes/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EPB.PDF',
                  'volumes/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EPB.LBL',
                  'volumes/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EPB.LBL'],
         ('Earth-based Occultations',
          10,
          'ebro_geom',
          'Geometry Table',
          True): ['volumes/EBROCC_xxxx/EBROCC_0001/GEOMETRY/ESO1M/ES1_EGD.TAB',
                  'volumes/EBROCC_xxxx/EBROCC_0001/GEOMETRY/ESO1M/ES1_EGD.LBL'],
         ('Earth-based Occultations',
          40,
          'ebro_source',
          'Source Data',
          False): ['volumes/EBROCC_xxxx/EBROCC_0001/SORCDATA/ESO1M/ES1_EGRESS_GEOMETRY.DAT',
                   'volumes/EBROCC_xxxx/EBROCC_0001/SORCDATA/ESO1M/ES1_EGRESS_GEOMETRY.LBL',
                   'volumes/EBROCC_xxxx/EBROCC_0001/SORCDATA/ESO1M/ES1_EGRESS.OUT',
                   'volumes/EBROCC_xxxx/EBROCC_0001/SORCDATA/ESO1M/ES1_EGRESS.LBL'],
         ('browse',
          40,
          'browse_full',
          'Browse Image (full)',
          True): ['previews/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD_full.jpg',
                  'previews/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EPB_full.jpg',
                  'previews/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EGB_full.jpg'],
         ('browse',
          30,
          'browse_medium',
          'Browse Image (medium)',
          False): ['previews/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD_med.jpg',
                   'previews/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EPB_med.jpg',
                   'previews/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EGB_med.jpg'],
         ('browse',
          20,
          'browse_small',
          'Browse Image (small)',
          False): ['previews/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD_small.jpg',
                   'previews/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EPB_small.jpg',
                   'previews/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EGB_small.jpg'],
         ('browse',
          10,
          'browse_thumb',
          'Browse Image (thumbnail)',
          False): ['previews/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD_thumb.jpg',
                   'previews/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EPB_thumb.jpg',
                   'previews/EBROCC_xxxx/EBROCC_0001/BROWSE/ESO1M/ES1_EGB_thumb.jpg'],
         ('metadata',
          5,
          'rms_index',
          'RMS Node Augmented Index',
          False): ['metadata/EBROCC_xxxx/EBROCC_0001/EBROCC_0001_index.tab',
                   'metadata/EBROCC_xxxx/EBROCC_0001/EBROCC_0001_index.lbl'],
         ('metadata',
          8,
          'profile_index',
          'Profile Index',
          False): ['metadata/EBROCC_xxxx/EBROCC_0001/EBROCC_0001_profile_index.tab',
                   'metadata/EBROCC_xxxx/EBROCC_0001/EBROCC_0001_profile_index.lbl'],
         ('metadata',
          9,
          'supplemental_index',
          'Supplemental Index',
          False): ['metadata/EBROCC_xxxx/EBROCC_0001/EBROCC_0001_supplemental_index.tab',
                   'metadata/EBROCC_xxxx/EBROCC_0001/EBROCC_0001_supplemental_index.lbl']}
        )
    ]
)
def test_opus_products(input_path, expected):
    opus_products_test(input_path, expected)

def test_opus_id_to_primary_logical_path():
    TESTS = [
        'volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_IPD.TAB',
        'volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD.TAB',
        'volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO22M/ES2_IPD.TAB',
        'volumes/EBROCC_xxxx/EBROCC_0001/DATA/MCD27M/MCD_IPD.TAB',
        'volumes/EBROCC_xxxx/EBROCC_0001/DATA/IRTF/IRT_IPD.TAB',
        'volumes/EBROCC_xxxx/EBROCC_0001/DATA/LICK1M/LIC_EPD.TAB',
        'volumes/EBROCC_xxxx/EBROCC_0001/DATA/PAL200/PAL_IPD.TAB',
    ]

    for logical_path in TESTS:
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
            for category in ('volumes', 'previews', 'diagrams'):
                for abspath in pdsf.associated_abspaths(category):
                    assert abspath in opus_id_abspaths

##########################################################################################
