##########################################################################################
# pds3file/rules/CORSS_8xxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
import translator
import re

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/data/Rev(...)',               re.I, (r'Data for Cassini orbit \1',         'DATADIR')),
    (r'volumes/.*/data/Rev(...)/Rev\w+E',       re.I, (r'Data for Cassini orbit \1 egress',  'SERIESDIR')),
    (r'volumes/.*/data/Rev(...)/Rev\w+I',       re.I, (r'Data for Cassini orbit \1 ingress', 'SERIESDIR')),
    (r'volumes/.*/Rev\w+_([KSX])(\d\d)_[IE]',   re.I, (r'\1-band data from DSN ground station \2', 'SERIESDIR')),

    (r'volumes/.*/RSS\w+_CAL\.TAB',             re.I, ('Calibration parameters',       'TABLE')),
    (r'volumes/.*/RSS\w+_DLP_.*\.TAB',          re.I, ('Diffraction-limited profile',  'TABLE')),
    (r'volumes/.*/RSS\w+_GEO\.TAB',             re.I, ('Geometry table',               'TABLE')),
    (r'volumes/.*/RSS\w+_TAU.*\.TAB',           re.I, ('Optical depth profile',        'SERIES')),
    (r'volumes/.*/Rev\w+_Summary.*\.pdf',       re.I, ('Observation description',      'INFO')),

    (r'previews/.*/Rev\d\d\dC?[IE]_full\.jpg',    re.I, ('Large observation diagram',    'DIAGRAM')),
    (r'previews/.*/Rev\d\d\dC?[IE]_med\.jpg',     re.I, ('Medium observation diagram',   'DIAGRAM')),
    (r'previews/.*/Rev\d\d\dC?[IE]_small\.jpg',   re.I, ('Small observation diagram',    'DIAGRAM')),
    (r'previews/.*/Rev\d\d\dC?[IE]_thumb\.jpg',   re.I, ('Thumbnail obervation diagram', 'DIAGRAM')),

    (r'previews/.*/Rev\d\d\dC?[IE]_full\.jpg',    re.I, ('Large observation diagram',    'DIAGRAM')),
    (r'previews/.*/Rev\d\d\dC?[IE]_med\.jpg',     re.I, ('Medium observation diagram',   'DIAGRAM')),
    (r'previews/.*/Rev\d\d\dC?[IE]_small\.jpg',   re.I, ('Small observation diagram',    'DIAGRAM')),
    (r'previews/.*/Rev\d\d\dC?[IE]_thumb\.jpg',   re.I, ('Thumbnail obervation diagram', 'DIAGRAM')),

    (r'volumes/.*/document/archived_rss_ring_profiles.*\.pdf', 0, ('&#11013; <b>Calibration Procedures</b>', 'INFO')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(browse|data)/(.*)\.(pdf|LBL)', 0,
            [r'previews/CORSS_8xxx/\2/\3/\4_full.jpg',
             r'previews/CORSS_8xxx/\2/\3/\4_med.jpg',
             r'previews/CORSS_8xxx/\2/\3/\4_small.jpg',
             r'previews/CORSS_8xxx/\2/\3/\4_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/data/(Rev...)', 0,
            [r'previews/CORSS_8xxx/\2/browse/\3_OccTrack_Geometry_full.jpg',
             r'previews/CORSS_8xxx/\2/browse/\3_OccTrack_Geometry_med.jpg',
             r'previews/CORSS_8xxx/\2/browse/\3_OccTrack_Geometry_small.jpg',
             r'previews/CORSS_8xxx/\2/browse/\3_OccTrack_Geometry_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data/Rev.../Rev...C?[IE])', 0,
            [r'previews/CORSS_8xxx/\2/\3_full.jpg',
             r'previews/CORSS_8xxx/\2/\3_med.jpg',
             r'previews/CORSS_8xxx/\2/\3_small.jpg',
             r'previews/CORSS_8xxx/\2/\3_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data/Rev.../Rev...C?[IE])/(Rev...C?[IE])_(RSS\w+)', 0,
            [r'previews/CORSS_8xxx/\2/\3/\4_\5/\5_GEO_full.jpg',
             r'previews/CORSS_8xxx/\2/\3/\4_\5/\5_GEO_med.jpg',
             r'previews/CORSS_8xxx/\2/\3/\4_\5/\5_GEO_small.jpg',
             r'previews/CORSS_8xxx/\2/\3/\4_\5/\5_GEO_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data/.*)_(TAU|GEO).*\.(TAB|LBL)', 0,
            [r'previews/CORSS_8xxx/\2/\3_\4_full.jpg',
             r'previews/CORSS_8xxx/\2/\3_\4_med.jpg',
             r'previews/CORSS_8xxx/\2/\3_\4_small.jpg',
             r'previews/CORSS_8xxx/\2/\3_\4_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev(..)(C?[IE])_RSS_(\w+)/(\w+)_(GEO|TAU)(\.\w+|_.*M\.\w+)', 0,
            [r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/\4_\5_full.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/\4_\5_med.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/\4_\5_small.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/\4_\5_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev(..)(C?[IE])_RSS_(\w+)/Rev..[IE]_(RSS.*Summary).(pdf|LBL)', 0,
            [r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/Rev0\1\2_\4_full.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/Rev0\1\2_\4_med.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/Rev0\1\2_\4_small.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/Rev0\1\2_\4_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev(..)(C?[IE])_RSS_(\w+)', 0,
            [r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/RSS_\3_GEO_full.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/RSS_\3_GEO_med.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/RSS_\3_GEO_small.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_RSS_\3/RSS_\3_GEO_thumb.jpg',
            ]),
])

diagram_viewables = translator.TranslatorByRegex([
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/.*/(Rev...)(C?[IE]_RSS_2..._..._..._[IE])(|/.*GEO.*|/.*TAU.*)', 0,
            [r'diagrams/CORSS_8xxx/\2/data/\3/\3\4_full.jpg',
             r'diagrams/CORSS_8xxx/\2/data/\3/\3\4_med.jpg',
             r'diagrams/CORSS_8xxx/\2/data/\3/\3\4_small.jpg',
             r'diagrams/CORSS_8xxx/\2/data/\3/\3\4_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx_v1/(CORSS_8...)/.*/Rev(\d\d)(C?[IE]_RSS_2..._..._..._[IE])(|/.*GEO.*|/.*TAU.*)', 0,
            [r'diagrams/CORSS_8xxx/\1/data/Rev0\2/Rev0\2\3_full.jpg',
             r'diagrams/CORSS_8xxx/\1/data/Rev0\2/Rev0\2\3_med.jpg',
             r'diagrams/CORSS_8xxx/\1/data/Rev0\2/Rev0\2\3_small.jpg',
             r'diagrams/CORSS_8xxx/\1/data/Rev0\2/Rev0\2\3_thumb.jpg',
            ]),
])

profile_viewables = translator.TranslatorByRegex([
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/.*/(Rev\d\d\d)(C?[IE])_(RSS_2..._..._..._[IE])(|/.*TAU.*)', 0,
            [r'previews/CORSS_8xxx/\2/data/\3/\3\4/\3\4_\5/\5_TAU_full.jpg',
             r'previews/CORSS_8xxx/\2/data/\3/\3\4/\3\4_\5/\5_TAU_med.jpg',
             r'previews/CORSS_8xxx/\2/data/\3/\3\4/\3\4_\5/\5_TAU_small.jpg',
             r'previews/CORSS_8xxx/\2/data/\3/\3\4/\3\4_\5/\5_TAU_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx_v1/(CORSS_8...)/.*/Rev(\d\d)(C?[IE])_(RSS_2..._..._..._[IE])(|/.*TAU.*)', 0,
            [r'previews/CORSS_8xxx/\1/data/Rev0\2/Rev0\2\3/Rev0\2\3_\4/\4_TAU_full.jpg',
             r'previews/CORSS_8xxx/\1/data/Rev0\2/Rev0\2\3/Rev0\2\3_\4/\4_TAU_med.jpg',
             r'previews/CORSS_8xxx/\1/data/Rev0\2/Rev0\2\3/Rev0\2\3_\4/\4_TAU_small.jpg',
             r'previews/CORSS_8xxx/\1/data/Rev0\2/Rev0\2\3/Rev0\2\3_\4/\4_TAU_thumb.jpg',
            ]),
])

skyview_viewables = translator.TranslatorByRegex([
    (r'volumes/.*/Rev(\d\d\d)([^\.]*|.*OccTrack_Geometry.\w+)', 0,
            [r'previews/CORSS_8xxx/CORSS_8001/browse/Rev\1_OccTrack_Geometry_full.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/browse/Rev\1_OccTrack_Geometry_med.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/browse/Rev\1_OccTrack_Geometry_small.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/browse/Rev\1_OccTrack_Geometry_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx_v1/.*/Rev(\d\d)[CIE][^\.]*', 0,
            [r'previews/CORSS_8xxx/CORSS_8001/browse/Rev0\1_OccTrack_Geometry_full.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/browse/Rev0\1_OccTrack_Geometry_med.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/browse/Rev0\1_OccTrack_Geometry_small.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/browse/Rev0\1_OccTrack_Geometry_thumb.jpg',
            ]),
])

dsntrack_viewables = translator.TranslatorByRegex([
    (r'volumes/.*/Rev(\d\d\d)([^\.]*|.*DSN_Elevation.\w+)', 0,
            [r'previews/CORSS_8xxx/CORSS_8001/data/Rev\1/Rev\1_DSN_Elevation_full.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev\1/Rev\1_DSN_Elevation_med.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev\1/Rev\1_DSN_Elevation_small.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev\1/Rev\1_DSN_Elevation_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx_v1/.*/Rev(\d\d)[CIE][^\.]*', 0,
            [r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1_DSN_Elevation_full.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1_DSN_Elevation_med.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1_DSN_Elevation_small.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1_DSN_Elevation_thumb.jpg',
            ]),
])

timeline_viewables = translator.TranslatorByRegex([
    (r'volumes/.*/Rev(\d\d\d)([^\.]*|.*TimeLine_Figure.\w+)', 0,
            [r'previews/CORSS_8xxx/CORSS_8001/data/Rev\1/Rev\1_TimeLine_Figure_full.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev\1/Rev\1_TimeLine_Figure_med.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev\1/Rev\1_TimeLine_Figure_small.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev\1/Rev\1_TimeLine_Figure_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx_v1/.*/Rev(\d\d)[CIE][^\.]*', 0,
            [r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1_TimeLine_Figure_full.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1_TimeLine_Figure_med.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1_TimeLine_Figure_small.jpg',
             r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1_TimeLine_Figure_thumb.jpg',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    (r'.*/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data|browse)', 0,
            [r'volumes/CORSS_8xxx\1/\2/data',
             r'volumes/CORSS_8xxx\1/\2/browse',
            ]),
    (r'previews/(CORSS_8xxx/CORSS_8.../.*)_[a-z]+\.jpg', 0,
            r'volumes/\1*'),
    (r'previews/(CORSS_8xxx/CORSS_8.../[^\.]+)', 0,
            r'volumes/\1'),
    (r'diagrams/(CORSS_8xxx/CORSS_8.../data/Rev...)/(Rev...C?[IE])(_RSS.*)_[a-z]+\.jpg', 0,
            r'volumes/\1/\2/\2\3'),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/browse/(Rev...).*', 0,
            r'volumes/CORSS_8xxx\1/\2/data/\3'),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/data/(Rev...).*', 0,
            r'volumes/CORSS_8xxx\1/\2/browse/\3_OccTrack_Geometry.*'),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/data/(Rev...)/(Rev...C?[EI]).*', 0,
            r'volumes/CORSS_8xxx\1/\2/data/\3/\3_*'),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/data/(Rev.../Rev...C?[EI]/\w+)/.*', 0,
            r'volumes/CORSS_8xxx\1/\2/data/\3/*'),
    (r'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA', 0,
            [r'volumes/CORSS_8xxx/CORSS_8001/data',
             r'volumes/CORSS_8xxx/CORSS_8001/browse',
            ]),
    (r'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev(\d\d)(C?[EI])(\w+)(|/.*)', 0,
            r'volumes/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2\3'),
    (r'documents/CORSS_8xxx.*', 0,
            r'volumes/CORSS_8xxx'),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data|browse|EASYDATA)', 0,
            [r'previews/CORSS_8xxx/\2/data',
             r'previews/CORSS_8xxx/\2/browse'
            ]),
    (r'.*/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data|browse|EASYDATA)/(Rev...)', 0,
            r'previews/CORSS_8xxx/\2/data/\4'),
    (r'.*/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data|browse|EASYDATA)/(Rev.../Rev...C?[IE])', 0,
            [r'previews/CORSS_8xxx/\2/data/\4',
             r'previews/CORSS_8xxx/\2/data/\4_full.jpg',
             r'previews/CORSS_8xxx/\2/data/\4_med.jpg',
             r'previews/CORSS_8xxx/\2/data/\4_small.jpg',
             r'previews/CORSS_8xxx/\2/data/\4_thumb.jpg',
            ]),
    (r'previews/CORSS_8xxx/(CORSS_8.../.*)_[a-z]+\.jpg', 0,
            [r'previews/CORSS_8xxx/\1_full.jpg',
             r'previews/CORSS_8xxx/\1_med.jpg',
             r'previews/CORSS_8xxx/\1_small.jpg',
             r'previews/CORSS_8xxx/\1_thumb.jpg'
            ]),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/.*/(Rev\d\d\d)(|_.*)', 0,
            [r'previews/CORSS_8xxx/\2/data/\3',
             r'previews/CORSS_8xxx/\2/browse/\3_OccTrack_Geometry_full.jpg',
             r'previews/CORSS_8xxx/\2/browse/\3_OccTrack_Geometry_med.jpg',
             r'previews/CORSS_8xxx/\2/browse/\3_OccTrack_Geometry_small.jpg',
             r'previews/CORSS_8xxx/\2/browse/\3_OccTrack_Geometry_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/data/(Rev...)/(Rev...C?[IE])(|_.*)', 0,
            [r'previews/CORSS_8xxx/\2/data/\3/\4',
             r'previews/CORSS_8xxx/\2/data/\3/\4_full.jpg',
             r'previews/CORSS_8xxx/\2/data/\3/\4_med.jpg',
             r'previews/CORSS_8xxx/\2/data/\3/\4_small.jpg',
             r'previews/CORSS_8xxx/\2/data/\3/\4_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/.*/(Rev...)(C?[IE])_(RSS_2..._..._..._[IE])(|/.*)', 0,
            r'previews/CORSS_8xxx/\2/data/\3/\3\4/\3\4_\5'),
    (r'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev(\d\d)(C?[EI])_(RSS_2..._..._..._[EI])(|/.*)', 0,
            r'previews/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2/Rev0\1\2_\3'),
])

associations_to_diagrams = translator.TranslatorByRegex([
    (r'.*/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data|browse|EASYDATA)', 0,
            r'diagrams/CORSS_8xxx/\2/data'),
    (r'.*/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data|browse|EASYDATA)/(Rev...)', 0,
            r'diagrams/CORSS_8xxx/\2/data/\4'),
    (r'diagrams/CORSS_8xxx/(CORSS_8.../.*)_[a-z]+\.jpg', 0,
            [r'diagrams/CORSS_8xxx/\1_full.jpg',
             r'diagrams/CORSS_8xxx/\1_med.jpg',
             r'diagrams/CORSS_8xxx/\1_small.jpg',
             r'diagrams/CORSS_8xxx/\1_thumb.jpg'
            ]),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/.*/(Rev...)(C?[IE]_RSS_2..._..._..._[IE]).*', 0,
            [r'diagrams/CORSS_8xxx/\2/data/\3/\3\4_full.jpg',
             r'diagrams/CORSS_8xxx/\2/data/\3/\3\4_med.jpg',
             r'diagrams/CORSS_8xxx/\2/data/\3/\3\4_small.jpg',
             r'diagrams/CORSS_8xxx/\2/data/\3/\3\4_thumb.jpg',
            ]),
    (r'volumes/CORSS_8xxx_v1/CORSS_8001/EASYDATA/Rev(\d\d)(C?[EI])_(RSS_2..._..._..._[IE]).*', 0,
            [r'diagrams/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2_\3_full.jpg',
             r'diagrams/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2_\3_med.jpg',
             r'diagrams/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2_\3_small.jpg',
             r'diagrams/CORSS_8xxx/CORSS_8001/data/Rev0\1/Rev0\1\2_\3_thumb.jpg',
            ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data|EASYDATA)', 0,
            r'metadata/CORSS_8xxx/\2'),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data|EASYDATA).*/(\w+)\..*', 0,
            r'metadata/CORSS_8xxx/\2/\2_index.tab/\4'),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data|EASYDATA).*/(\w+)_TAU.*', 0,
            [r'metadata/CORSS_8xxx/\2/\2_supplemental_index.tab/\4_TAU_01KM',
             r'metadata/CORSS_8xxx/\2/\2_supplemental_index.tab/\4_TAU_1400M',
             r'metadata/CORSS_8xxx/\2/\2_supplemental_index.tab/\4_TAU_1600M',
             r'metadata/CORSS_8xxx/\2/\2_supplemental_index.tab/\4_TAU_2400M',
             r'metadata/CORSS_8xxx/\2/\2_supplemental_index.tab/\4_TAU_3000M',
             r'metadata/CORSS_8xxx/\2/\2_supplemental_index.tab/\4_TAU_4000M',
            ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'volumes/CORSS_8xxx/CORSS_8001.*', 0,
            r'volumes/CORSS_8xxx/CORSS_8001/document/archived_rss_ring_profiles_2018.pdf'),
    (r'volumes/CORSS_8xxx_v1/CORSS_8001.*', 0,
            r'volumes/CORSS_8xxx_v1/CORSS_8001/DOCUMENT/archived_rss_ring_profiles.pdf'),
])

##########################################################################################
# VERSIONS
##########################################################################################

# _v1 had upper case file names and used "EASYDATA" in place of "data"
# Directory tree structure was massively changed; number of digits after "Rev" was changed
# Case conversions are inconsistent, sometimes mixed case file names are unchanged
versions = translator.TranslatorByRegex([
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(data|EASYDATA)', 0,
            [r'volumes/CORSS_8xxx*/\2/data',
             r'volumes/CORSS_8xxx_v1/\2/EASYDATA',
            ]),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/.*/(Rev\d?)(\d\d)(C?[IE])_(RSS_...._..._..._[EI])(|/.*)', 0,
            [r'volumes/CORSS_8xxx*/\2/data/\3\4/\3\4\5/\3\4\5_\6\7',
             r'volumes/CORSS_8xxx*/\2/data/Rev0\4/Rev0\4\5/Rev0\4\5_\6\7',
             r'volumes/CORSS_8xxx_v1/\2/EASYDATA/Rev\4\5_\6\7',
            ]),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/.*/(Rev\d?)(\d\d)(C?[IE])_(RSS_...._..._..._[EI])/Rev.*_(RSS.*)', 0,
            [r'volumes/CORSS_8xxx*/\2/data/\3\4/\3\4\5/\3\4\5_\6/\3\4\5_\7',
             r'volumes/CORSS_8xxx*/\2/data/Rev0\4/Rev0\4\5/Rev0\4\5_\6/Rev0\4\5_\7',
             r'volumes/CORSS_8xxx_v1/\2/EASYDATA/Rev\4\5_\6/Rev\4\5_\7',
            ]),
    (r'volumes/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/(\w+)(|/.*)', 0,
            [r'volumes/CORSS_8xxx*/\2/#LOWER#\3\4',
             r'volumes/CORSS_8xxx*/\2/#LOWER#\3#MIXED#\4',
             r'volumes/CORSS_8xxx_v1/\2/#UPPER#\3\4',
             r'volumes/CORSS_8xxx_v1/\2/#UPPER#\3#MIXED#\4',
            ]),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'(volumes|diagrams|previews)/.*/(data|browse)/.*', 0, (True, True, True)),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'(.*)/Rev...',                    0, r'\1/Rev*'),
    (r'(.*)/Rev.../Rev...C?[IE]',       0, r'\1/Rev*/Rev*[IE]'),
    (r'(.*)/Rev.../Rev...C?[IE]/Rev.*', 0, r'\1/Rev*/Rev*/Rev*'),
    (r'(.*)/EASYDATA/Rev\w+',           0, r'\1/EASYDATA/*'),
])

##########################################################################################
# SPLIT_RULES
##########################################################################################

split_rules = translator.TranslatorByRegex([
    (r'(RSS_...._..._\w+_[IE])_(TAU\w+)\.(.*)', 0, (r'\1', r'_\2', r'.\3')),
])

##########################################################################################
# OPUS_TYPE
#
# Used for indicating the type of a data file as it will appear in OPUS, e.g., "Raw Data", "Calibrated Data", etc. The tuple
# returned is (category, rank, slug, title, selected) where:
#   category is 'browse', 'diagram', or a meaningful header for special cases like 'Voyager ISS', 'Cassini CIRS'
#   rank is the sort order within the category
#   slug is a short string that will appear in URLs
#   title is a meaning title for product, e.g., 'Raw Data (when calibrated is unavailable)'
#   selected is True if the type is selected by default, False otherwise.
#
# These translations take a file's logical path and return a string indicating the file's OPUS_TYPE.
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'volumes/.*_TAU_01KM\.(TAB|LBL)',  0, ('Cassini RSS', 10, 'corss_occ_best_res', 'Occultation Profile (~1 km)', True)),
    (r'volumes/.*_TAU_1400M\.(TAB|LBL)', 0, ('Cassini RSS', 10, 'corss_occ_best_res', 'Occultation Profile (~1 km)', True)),
    (r'volumes/.*_TAU_1600M\.(TAB|LBL)', 0, ('Cassini RSS', 10, 'corss_occ_best_res', 'Occultation Profile (~1 km)', True)),
    (r'volumes/.*_TAU_2400M\.(TAB|LBL)', 0, ('Cassini RSS', 10, 'corss_occ_best_res', 'Occultation Profile (~1 km)', True)),
    (r'volumes/.*_TAU_3000M\.(TAB|LBL)', 0, ('Cassini RSS', 10, 'corss_occ_best_res', 'Occultation Profile (~1 km)', True)),
    (r'volumes/.*_TAU_4000M\.(TAB|LBL)', 0, ('Cassini RSS', 10, 'corss_occ_best_res', 'Occultation Profile (~1 km)', True)),
    (r'volumes/.*_TAU_10KM\.(TAB|LBL)',  0, ('Cassini RSS', 20, 'corss_occ_10km_res', 'Occultation Profile (10 km)', True)),

    (r'volumes/.*_DLP_500M\.(TAB|LBL)',  0, ('Cassini RSS', 30, 'corss_occ_dlp', 'Diffraction-Ltd Occultation Profile', True)),
    (r'volumes/.*_CAL\.(TAB|LBL)',       0, ('Cassini RSS', 40, 'corss_occ_cal', 'Occultation Calibration Parameters',  True)),
    (r'volumes/.*_GEO\.(TAB|LBL)',       0, ('Cassini RSS', 50, 'corss_occ_geo', 'Occultation Geometry Parameters',     True)),

    (r'volumes/.*_(DSN_Elevation|TimeLine_Figure|TimeLine_Table|Summary|OccTrack_Geometry)\.(pdf|LBL)',
                                         0, ('Cassini RSS', 60, 'corss_occ_doc', 'Occultation Documentation', True)),
    # Documentation
    (r'documents/CORSS_8xxx/.*',         0, ('Cassini RSS', 70, 'corss_occ_documentation', 'Documentation',     False)),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

opus_products = translator.TranslatorByRegex([
    (r'.*/CORSS_8xxx(|_v[0-9\.]+)/(CORSS_8...)/.*/(Rev.)(..)(C?[IE])_(RSS_...._..._..._[EI]).*', 0,
            [r'volumes/CORSS_8xxx*/\2/data/\3\4/\3\4\5/\3\4\5_\6/*',
             r'volumes/CORSS_8xxx_v1/\2/EASYDATA/Rev\4\5_\6/*',
             r'volumes/CORSS_8xxx*/\2/data/\3\4/\3\4_DSN_Elevation.LBL',
             r'volumes/CORSS_8xxx*/\2/data/\3\4/\3\4_DSN_Elevation.pdf',
             r'volumes/CORSS_8xxx*/\2/data/\3\4/\3\4_TimeLine_Figure.LBL',
             r'volumes/CORSS_8xxx*/\2/data/\3\4/\3\4_TimeLine_Figure.pdf',
             r'volumes/CORSS_8xxx*/\2/data/\3\4/\3\4_TimeLine_Table.LBL',
             r'volumes/CORSS_8xxx*/\2/data/\3\4/\3\4_TimeLine_Table.pdf',
             r'volumes/CORSS_8xxx*/\2/browse/\3\4_OccTrack_Geometry.LBL',
             r'volumes/CORSS_8xxx*/\2/browse/\3\4_OccTrack_Geometry.pdf',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4\5/\3\4\5_\6/*',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_DSN_Elevation_full.jpg',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_DSN_Elevation_med.jpg',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_DSN_Elevation_small.jpg',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_DSN_Elevation_thumb.jpg',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_TimeLine_Figure_full.jpg',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_TimeLine_Figure_med.jpg',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_TimeLine_Figure_small.jpg',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_TimeLine_Figure_thumb.jpg',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_TimeLine_Table_full.jpg',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_TimeLine_Table_med.jpg',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_TimeLine_Table_small.jpg',
             r'previews/CORSS_8xxx/\2/data/\3\4/\3\4_TimeLine_Table_thumb.jpg',
             r'previews/CORSS_8xxx/\2/browse/\3\4_OccTrack_Geometry_full.jpg',
             r'previews/CORSS_8xxx/\2/browse/\3\4_OccTrack_Geometry_med.jpg',
             r'previews/CORSS_8xxx/\2/browse/\3\4_OccTrack_Geometry_small.jpg',
             r'previews/CORSS_8xxx/\2/browse/\3\4_OccTrack_Geometry_thumb.jpg',
             r'metadata/CORSS_8xxx/\2/CORSS_8001_index.lbl',
             r'metadata/CORSS_8xxx/\2/CORSS_8001_index.tab',
             r'metadata/CORSS_8xxx/\2/CORSS_8001_supplemental_index.lbl',
             r'metadata/CORSS_8xxx/\2/CORSS_8001_supplemental_index.tab',
            ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/CORSS_8xxx.*/CORSS_8.../(data|browse).*/(Rev...C?)[IE]_RSS_(....)_(...)_(...)_([IE]).*', 0,
            r'co-rss-occ-\3-\4-#LOWER#\2-\5-\6'),
    (r'.*/CORSS_8xxx_v1/CORSS_8.../EASYDATA.*/Rev(\d\d)(C?)[IE]_RSS_(....)_(...)_(...)_([IE]).*', 0,
            r'co-rss-occ-\3-\4-#LOWER#rev0\1\2-\5-\6'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

opus_id_to_primary_logical_path = translator.TranslatorByRegex([
  (r'co-rss-occ-(\d{4})-(\d{3})-rev(...)(c?)-(...)-(i|e)', 0,
    [r'volumes/CORSS_8xxx/CORSS_8001/data/Rev\3/Rev\3#UPPER#\4\6/#MIXED#Rev\3#UPPER#\4\6_RSS_\1_\2_\5_\6/RSS_\1_\2_\5_\6_TAU_01KM.TAB',
     r'volumes/CORSS_8xxx/CORSS_8001/data/Rev\3/Rev\3#UPPER#\4\6/#MIXED#Rev\3#UPPER#\4\6_RSS_\1_\2_\5_\6/RSS_\1_\2_\5_\6_TAU_*00M.TAB',
    ]),
])

##########################################################################################
# Subclass definition
##########################################################################################

class CORSS_8xxx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('CORSS_8xxx', re.I, 'CORSS_8xxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS
    SPLIT_RULES = split_rules + pds3file.Pds3File.SPLIT_RULES

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_PRODUCTS = opus_products + pds3file.Pds3File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {
        'default' : default_viewables,
        'diagram' : diagram_viewables,
        'profile' : profile_viewables,
        'timeline': timeline_viewables,
        'skyview' : skyview_viewables,
        'dsntrack': dsntrack_viewables,
    }

    VIEWABLE_TOOLTIPS = {
        'default' : 'Default browse product for this file',
        'diagram' : 'Diagram illustrating observation footprints on the target',
        'profile' : 'Radial profile derived from the occultation data',
        'timeline': 'Timeline of events during the experiment',
        'skyview' : 'Occultation track of Cassini behind the rings as seen from Earth',
        'dsntrack': 'Elevation angle of Saturn as seen from the DSN stations',
    }

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']   += associations_to_volumes
    ASSOCIATIONS['previews']  += associations_to_previews
    ASSOCIATIONS['diagrams']  += associations_to_diagrams
    ASSOCIATIONS['metadata']  += associations_to_metadata
    ASSOCIATIONS['documents'] += associations_to_documents

    VERSIONS = versions + pds3file.Pds3File.VERSIONS

# Global attribute shared by all subclasses
pds3file.Pds3File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'co-rss-occ-.*', 0, CORSS_8xxx)]) + \
                                        pds3file.Pds3File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['CORSS_8xxx'] = CORSS_8xxx

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

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
