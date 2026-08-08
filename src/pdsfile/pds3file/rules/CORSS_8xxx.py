##########################################################################################
# pds3file/rules/CORSS_8xxx.py
##########################################################################################

"""Rules for the CORSS_8xxx volume set: Cassini RSS ring occultation profiles.

CORSS_8xxx is described in the holdings as Cassini RSS radio occultation profiles of
Saturn's rings, 2005-2010. Its one volume, CORSS_8001, carries data set ID
CO-SR-RSS-4/5-OCC-V2.0 (``_volinfo/CORSS_8xxx.txt``). Data are organized by
spacecraft revolution: a "Rev" directory per orbit, and within it a directory per
occultation direction, holding the optical depth profile, the diffraction-limited
profile, the geometry table and the calibration parameters.

The rule tables:

* ``description_and_icon_by_regex`` -- names the calibration, geometry, optical
  depth and diffraction-limited products and the observation description, and gives
  the browse diagrams their sizes.
* ``default_viewables`` -- the preview images for a product.
* ``diagram_viewables``, ``profile_viewables``, ``skyview_viewables``,
  ``dsntrack_viewables`` and ``timeline_viewables`` -- five further viewable sets,
  which the class offers under the keys "diagram", "profile", "skyview", "dsntrack"
  and "timeline" alongside "default". The class's own tooltips say what each is:
  "diagram" illustrates the observation footprints on the target, "profile" is the
  radial profile derived from the occultation, "skyview" is the occultation track of
  Cassini behind the rings as seen from Earth, "dsntrack" is the elevation angle of
  Saturn as seen from the DSN stations, and "timeline" is the timeline of events
  during the experiment. ``skyview_viewables`` and ``dsntrack_viewables`` are defined
  by no other rule module. Only `COCIRS_xxxx.py`, with twenty-one, offers more named
  viewables than these six.
* ``associations_to_volumes``, ``associations_to_previews``,
  ``associations_to_diagrams``, ``associations_to_metadata`` and
  ``associations_to_documents`` -- cross the five trees for one occultation.
* ``versions`` -- the paths of the same product in the other version of this volume
  set, which cannot be found by wildcarding the version suffix alone: the earlier
  version put the data under ``EASYDATA/`` rather than ``data/``, used two digits
  after "Rev" where the current version uses three, and nested the per-occultation
  directories differently. The data file basenames are upper case in both versions;
  what the table's ``#UPPER#`` directive rewrites is the directory component.
* ``view_options``, ``neighbors`` and ``split_rules`` -- the view flags, the
  corresponding directories in sibling volumes, and the basename grouping.
* ``opus_type``, ``opus_products``, ``opus_id`` and
  ``opus_id_to_primary_logical_path`` -- file products under the "Cassini RSS" OPUS
  category, list what OPUS offers with each, and give the OPUS ID and its inverse.

`COUVIS_8xxx.py` and `COVIMS_8xxx.py` serve the stellar occultation profiles of the
same rings from the two Cassini spectrometers.
"""

import re

import translator

import pdsfile.pds3file as pds3file

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
    """The ``Pds3File`` subclass for CORSS_8xxx.

    The class body wires this module's rule tables onto the class attributes
    ``Pds3File`` reads. Where a table is added to the inherited one, a lookup tries
    this module's patterns first and falls through to the defaults; where it is
    assigned outright there is no fall-through. The module tail registers the class
    in ``Pds3File.SUBCLASSES`` under the key
    "CORSS_8xxx". The module docstring describes the volume set and every table.
    """

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
