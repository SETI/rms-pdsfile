##########################################################################################
# pds3file/rules/EBROCC_xxxx.py
##########################################################################################

"""Rules for the EBROCC_xxxx volume set: Earth-based ring occultation data.

EBROCC_xxxx is described in the holdings as Earth-based ring occultation data. Its
one volume, EBROCC_0001, holds data from the 28 Sgr occultation of Saturn's rings
and carries six data set IDs, one per observatory: ESO1M, ESO22M, IRTF, LICK1M,
MCD27M and PAL200 (``_volinfo/EBROCC_xxxx.txt``). The volume is laid out with one
directory per observatory under each of its data, geometry and browse trees, which
is why this module needs a ``data_set_id`` table of its own: the data set ID depends
on which observatory directory a file sits in, not on which volume.

The rule tables:

* ``description_and_icon_by_regex`` -- names the per-observatory data, geometry and
  browse directories.
* ``default_viewables`` -- the preview plots for a product, and an empty viewable for
  a label file.
* ``associations_to_volumes``, ``associations_to_previews`` and
  ``associations_to_metadata`` -- cross the volumes, previews and metadata trees for
  one occultation.
* ``view_options`` -- the grid, multipage and continuous view flags.
* ``opus_type``, ``opus_format`` and ``opus_products`` -- file products under the
  "Earth-based Occultations" OPUS category as the occultation profile, the geometry
  table, the geometry diagram, the preview plot and the source data, and list what
  OPUS offers with each.
* ``opus_id`` and ``opus_id_to_primary_logical_path`` -- the OPUS ID and its
  inverse.
* ``data_set_id`` -- the PDS3 data set ID for a path, keyed on the observatory
  directory. `EBROCC_xxxx.py` and `COCIRS_xxxx.py` are the only two rule modules
  that define this table as a translator; `COUVIS_0xxx.py` overrides the same
  attribute with a method.
* ``filespec_to_bundleset`` -- maps a file specification beginning with the
  EBROCC_0001 volume ID to the volume set name EBROCC_xxxx.

The PDS4 counterpart for Earth-based occultations, of Uranus rather than Saturn, is
`uranus_occs_earthbased.py`.
"""

import re

import translator

import pdsfile.pds3file as pds3file

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
           r'metadata/EBROCC_xxxx/\2/\2_supplemental_index.tab/\4'),
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
    (r'volumes/.*/DATA/\w+/\w+\.(TAB|LBL)',          0, ('Earth-based Occultations',  0, 'ebro_occ_profile', 'Occultation Profile', True)),
    (r'volumes/.*/GEOMETRY/\w+/\w+\.(TAB|LBL)',      0, ('Earth-based Occultations', 10, 'ebro_occ_geom',    'Geometry Table',      True)),
    (r'volumes/.*/BROWSE/\w+/\w+PB\.(PDF|PS|LBL)',   0, ('Earth-based Occultations', 20, 'ebro_occ_preview', 'Preview Plot',        True)),
    (r'volumes/.*/BROWSE/\w+/\w+GB\.(PDF|PS|LBL)',   0, ('Earth-based Occultations', 30, 'ebro_occ_diagram', 'Geometry Diagram',    False)),
    (r'volumes/.*/SORCDATA/\w+/\w+_GEOMETRY\..*',    0, ('Earth-based Occultations', 40, 'ebro_occ_source',  'Source Data',         False)),
    (r'volumes/.*/SORCDATA/\w+/\w+GRESS\.(OUT|LBL)', 0, ('Earth-based Occultations', 40, 'ebro_occ_source',  'Source Data',         False)),
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
            r'metadata/EBROCC_xxxx/\2/\2_supplemental_index.lbl',
            r'metadata/EBROCC_xxxx/\2/\2_supplemental_index.tab',
           ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/EBROCC_xxxx.*/\w+/ESO1M/ES1_(I|E).*',  0, r'esosil1m04-apph-occ-1989-184-28sgr-#LOWER#\1'),
    (r'.*/EBROCC_xxxx.*/\w+/ESO22M/ES2_(I|E).*', 0, r'esosil2m2-apph-occ-1989-184-28sgr-#LOWER#\1'),
    (r'.*/EBROCC_xxxx.*/\w+/IRTF/IRT_(I|E).*',   0, r'irtf3m2-urac-occ-1989-184-28sgr-#LOWER#\1'),
    (r'.*/EBROCC_xxxx.*/\w+/LICK1M/LIC_(I|E).*', 0, r'lick1m-ccdc-occ-1989-184-28sgr-#LOWER#\1'),
    (r'.*/EBROCC_xxxx.*/\w+/MCD27M/MCD_(I|E).*', 0, r'mcd2m7-iirar-occ-1989-184-28sgr-#LOWER#\1'),
    (r'.*/EBROCC_xxxx.*/\w+/PAL200/PAL_(I|E).*', 0, r'pal5m08-circ-occ-1989-184-28sgr-#LOWER#\1')
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'esosil1m04-apph-occ-1989-184-28sgr-(.*)',   0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_#UPPER#\1PD.TAB'),
    (r'esosil2m2-apph-occ-1989-184-28sgr-(.*)',  0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO22M/ES2_#UPPER#\1PD.TAB'),
    (r'irtf3m2-urac-occ-1989-184-28sgr-(.*)',    0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/IRTF/IRT_#UPPER#\1PD.TAB'),
    (r'lick1m-ccdc-occ-1989-184-28sgr-(.*)',  0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/LICK1M/LIC_#UPPER#\1PD.TAB'),
    (r'mcd2m7-iirar-occ-1989-184-28sgr-(.*)', 0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/MCD27M/MCD_#UPPER#\1PD.TAB'),
    (r'pal5m08-circ-occ-1989-184-28sgr-(.*)',  0, r'volumes/EBROCC_xxxx/EBROCC_0001/DATA/PAL200/PAL_#UPPER#\1PD.TAB'),
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
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'EBROCC_0001.*', 0, r'EBROCC_xxxx'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class EBROCC_xxxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for EBROCC_xxxx.

    The class body and the module tail install this module's rule tables on the class
    attributes ``Pds3File`` reads. `pds3file/rules/__init__.py` sets out the routes a
    table takes and which of them leaves the inherited rules in front. The class
    is registered in ``Pds3File.SUBCLASSES`` under the key
    "EBROCC_xxxx".
    The module docstring describes the volume set and every table.
    """

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

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['EBROCC_xxxx'] = EBROCC_xxxx
