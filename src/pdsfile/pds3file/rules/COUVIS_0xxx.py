##########################################################################################
# pds3file/rules/COUVIS_0xxx.py
##########################################################################################

"""Rules for the COUVIS_0xxx volume set: Cassini UVIS data.

COUVIS_0xxx is described in the holdings as the Cassini UVIS (Ultraviolet
Spectrometer) data collection (``_volinfo/COUVIS_0xxx.txt``). Its volumes group data
files by date. A product is a binary data file with a detached PDS3 label, and the
same observation can appear in more than one version of the volume set under a
different data set ID.

The rule tables:

* ``description_and_icon_by_regex`` -- names the date-grouped directories, the time
  series and the binary and spectral data cubes, and labels the versions table in
  the metadata tree that ties data files to their data set IDs.
* ``default_viewables`` -- points a data file at its preview images.
* ``associations_to_volumes``, ``associations_to_previews``,
  ``associations_to_metadata`` and ``associations_to_documents`` -- cross the
  volumes, previews, metadata and documents trees for one observation.
* ``view_options``, ``neighbors`` and ``sort_key`` -- the view flags, the
  corresponding directories in sibling volumes, and the basename sort order.
* ``opus_type``, ``opus_format`` and ``opus_products`` -- file products under the
  "Cassini UVIS" OPUS category as "Raw Data" and "Calibration Data", and list what
  OPUS offers with each.
* ``opus_id`` and ``opus_id_to_primary_logical_path`` -- the OPUS ID and its
  inverse.

This volume set is the reason the data set ID cannot always be a translator. The
class body defines ``COUVIS_0xxx.DATA_SET_ID`` as a method, and a companion class
attribute ``COUVIS_0xxx.VERSIONS_PATH_AND_KEY`` that gives, for a data file, the
metadata versions table to read and the row key to read it at.
"""

import os
import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/DATA',                re.I, ('Data files grouped by date', 'CUBEDIR')),
    (r'volumes/.*/DATA/\w+',            re.I, ('Data files grouped by date', 'CUBEDIR')),
    (r'volumes/.*/HSP\w+\.DAT',         re.I, ('Time series data',           'DATA')),
    (r'volumes/.*/HDAC\w+\.DAT',        re.I, ('Binary data cube',           'DATA')),
    (r'volumes/.*/\w+\.DAT',            re.I, ('Spectral data cube',         'CUBE')),
    (r'volumes/.*\.txt_[0-9].*',        re.I, ('Text file',                  'INFO')),
    (r'volumes/.*OLD.DIR',              re.I, ('Directory',                  'FOLDER')),
    (r'metadata/.*versions\.tab',       0,    ('Table to associate data files with DATA_SET_IDs and versions',
                                                                             'INDEX')),
    (r'volumes/.*/DOCUMENT/UVIS.TXT',   re.I, ('PDS3 Archive Description',   'INFO' )),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'volumes/COUVIS_0xxx(|_v[0-9\.]+)/(COUVIS_0.../DATA/\w+/\w+)\.(DAT|LBL)', 0,
            [r'previews/COUVIS_0xxx/\2_full.png',
             r'previews/COUVIS_0xxx/\2_med.png',
             r'previews/COUVIS_0xxx/\2_small.png',
             r'previews/COUVIS_0xxx/\2_thumb.png',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    (r'volumes/COUVIS_0xxx(.*/COUVIS_0...)/(DATA|CALIB/VERSION_.)/(\w+)/(.*_\d\d)(|_CAL_.)\..*', 0,
            [r'volumes/COUVIS_0xxx\1/DATA/\3/\4.DAT',
             r'volumes/COUVIS_0xxx\1/DATA/\3/\4.LBL',
             r'volumes/COUVIS_0xxx\1/CALIB/VERSION_3/\3/\4_CAL_3.DAT',
             r'volumes/COUVIS_0xxx\1/CALIB/VERSION_3/\3/\4_CAL_3.LBL',
             r'volumes/COUVIS_0xxx\1/CALIB/VERSION_4/\3/\4_CAL_4.DAT',
             r'volumes/COUVIS_0xxx\1/CALIB/VERSION_4/\3/\4_CAL_4.LBL',
             r'volumes/COUVIS_0xxx\1/CALIB/VERSION_5/\3/\4_CAL_5.DAT',
             r'volumes/COUVIS_0xxx\1/CALIB/VERSION_5/\3/\4_CAL_5.LBL',
            ]),
    (r'volumes/COUVIS_0xxx(.*/COUVIS_0...)/(DATA|CALIB/VERSION_.)(|/\w+)', 0,
            [r'volumes/COUVIS_0xxx\1/DATA\3',
             r'volumes/COUVIS_0xxx\1/CALIB/VERSION_3\3',
             r'volumes/COUVIS_0xxx\1/CALIB/VERSION_4\3',
             r'volumes/COUVIS_0xxx\1/CALIB/VERSION_5\3',
            ]),
    (r'previews/COUVIS_0xxx(|_v[0-9\.]+)/(COUVIS_0...)/DATA(|/\w+)', 0,
            r'volumes/COUVIS_0xxx/\2/DATA\3'),
    (r'previews/COUVIS_0xxx(|_v[0-9\.]+)/(COUVIS_0.../DATA/\w+/\w+)_[a-z]+\.png', 0,
            [r'volumes/COUVIS_0xxx/\2.DAT',
             r'volumes/COUVIS_0xxx/\2.LBL',
            ]),
    (r'.*/COUVIS_0999.*', 0,
            r'volumes/COUVIS_0xxx'),
    (r'documents/COUVIS_0xxx.*', 0,
             r'volumes/COUVIS_0xxx'),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'volumes/COUVIS_0xxx(|_v[0-9\.]+)/(COUVIS_0.../DATA/\w+/\w+)\..*', 0,
            [r'previews/COUVIS_0xxx/\2_full.png',
             r'previews/COUVIS_0xxx/\2_med.png',
             r'previews/COUVIS_0xxx/\2_small.png',
             r'previews/COUVIS_0xxx/\2_thumb.png',
            ]),
    (r'volumes/COUVIS_0xxx(|_v[0-9\.]+)/(COUVIS_0.../DATA/\w+)', 0,
            r'previews/COUVIS_0xxx/\2'),
    (r'.*/COUVIS_0999.*', 0, r'previews/COUVIS_0xxx'),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/COUVIS_0xxx(|_v[0-9\.]+)/(COUVIS_0...)/DATA/\w+/(\w+)\..*', 0,
            [r'metadata/COUVIS_0xxx/\2/\2_index.tab/\3',
             r'metadata/COUVIS_0xxx/\2/\2_supplemental_index.tab/\3',
             r'metadata/COUVIS_0xxx/\2/\2_ring_summary.tab/\3',
             r'metadata/COUVIS_0xxx/\2/\2_moon_summary.tab/\3',
             r'metadata/COUVIS_0xxx/\2/\2_saturn_summary.tab/\3',
            ]),
    (r'metadata/COUVIS_0xxx(|_v[0-9\.]+)/COUVIS_0[^9]..', 0,
            r'metadata/COUVIS_0xxx\1/COUVIS_0999'),
    (r'metadata/COUVIS_0xxx(|_v[0-9\.]+)/COUVIS_0[^9].._(\w+)\..*', 0,
            [r'metadata/COUVIS_0xxx\1/COUVIS_0999/COUVIS_0999_\2.tab',
             r'metadata/COUVIS_0xxx\1/COUVIS_0999/COUVIS_0999_\2.csv',
             r'metadata/COUVIS_0xxx\1/COUVIS_0999/COUVIS_0999_\2.lbl',
            ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'volumes/COUVIS_0xxx(|_[^/]+)/COUVIS_0\d\d\d',    0, r'documents/COUVIS_0xxx/*'),
    (r'volumes/COUVIS_0xxx(|_[^/]+)/COUVIS_0\d\d\d/.+', 0, r'documents/COUVIS_0xxx'),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'(volumes|previews)/COUVIS_0xxx(|_v[0-9\.]+)/COUVIS_0.../DATA(|/\w+)', 0, (True, True, True)),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'(volumes|previews)/COUVIS_0xxx(|_v[0-9\.]+)/COUVIS_..../DATA',     0, r'\1/COUVIS_0xxx\2/*/DATA'),
    (r'(volumes|previews)/COUVIS_0xxx(|_v[0-9\.]+)/COUVIS_..../DATA/\w+', 0, r'\1/COUVIS_0xxx\2/*/DATA/*'),
    (r'volumes/COUVIS_0xxx(|_v[0-9\.]+)/COUVIS_.../CALIB/VERSION_.',      0, r'volumes/COUVIS_0xxx\1/CALIB/VERSION*'),
    (r'volumes/COUVIS_0xxx(|_v[0-9\.]+)/COUVIS_.../CALIB/VERSION_./\w+',  0, r'volumes/COUVIS_0xxx\1/CALIB/VERSION*/*'),
])

##########################################################################################
# SORT_KEY
##########################################################################################

sort_key = translator.TranslatorByRegex([
    (r'(EUV|FUV|HSP|HDAC)([0-9]{4}_[0-9]{3}_[0-9]{2}_[0-9]{2}.*)_full(\..*)',   0, r'\2\1_1full\3'),
    (r'(EUV|FUV|HSP|HDAC)([0-9]{4}_[0-9]{3}_[0-9]{2}_[0-9]{2}.*)_med(\..*)',    0, r'\2\1_2med\3'),
    (r'(EUV|FUV|HSP|HDAC)([0-9]{4}_[0-9]{3}_[0-9]{2}_[0-9]{2}.*)_small(\..*)',  0, r'\2\1_3small\3'),
    (r'(EUV|FUV|HSP|HDAC)([0-9]{4}_[0-9]{3}_[0-9]{2}_[0-9]{2}.*)_thumb(\..*)',  0, r'\2\1_4thumb\3'),
    (r'(EUV|FUV|HSP|HDAC)([0-9]{4}_[0-9]{3}_[0-9]{2}_[0-9]{2}.*)',              0, r'\2\1'),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'volumes/.*/DATA/.*\.DAT',  0, ('Cassini UVIS', 10, 'couvis_raw',        'Raw Data',         True)),
    (r'volumes/.*/CALIB/.*\.DAT', 0, ('Cassini UVIS', 20, 'couvis_calib_corr', 'Calibration Data', True)),
    # Documentation
    (r'documents/COUVIS_0xxx/.*', 0, ('Cassini UVIS', 30, 'couvis_documentation', 'Documentation', False)),
])

##########################################################################################
# OPUS_FORMAT
##########################################################################################

opus_format = translator.TranslatorByRegex([
    (r'.*\.DAT', 0, ('Binary', 'Unformatted')),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

opus_products = translator.TranslatorByRegex([
    (r'.*/COUVIS_0xxx(|_v[0-9\.]+)/(COUVIS_0...)/DATA/(\w+/\w+[0-9])(|_CAL.*|_[a-z]+)\..*', 0,
            [r'volumes/COUVIS_0xxx*/\2/DATA/\3.DAT',
             r'volumes/COUVIS_0xxx*/\2/DATA/\3.LBL',
             r'volumes/COUVIS_0xxx*/\2/CALIB/VERSION_3/\3_CAL_3.DAT',
             r'volumes/COUVIS_0xxx*/\2/CALIB/VERSION_3/\3_CAL_3.LBL',
             r'volumes/COUVIS_0xxx*/\2/CALIB/VERSION_4/\3_CAL_4.DAT',
             r'volumes/COUVIS_0xxx*/\2/CALIB/VERSION_4/\3_CAL_4.LBL',
             r'volumes/COUVIS_0xxx*/\2/CALIB/VERSION_5/\3_CAL_5.DAT',
             r'volumes/COUVIS_0xxx*/\2/CALIB/VERSION_5/\3_CAL_5.LBL',
             r'previews/COUVIS_0xxx/\2/DATA/\3_full.png',
             r'previews/COUVIS_0xxx/\2/DATA/\3_med.png',
             r'previews/COUVIS_0xxx/\2/DATA/\3_small.png',
             r'previews/COUVIS_0xxx/\2/DATA/\3_thumb.png',
             r'metadata/COUVIS_0xxx/\2/\2_moon_summary.tab',
             r'metadata/COUVIS_0xxx/\2/\2_moon_summary.lbl',
             r'metadata/COUVIS_0xxx/\2/\2_ring_summary.tab',
             r'metadata/COUVIS_0xxx/\2/\2_ring_summary.lbl',
             r'metadata/COUVIS_0xxx/\2/\2_saturn_summary.tab',
             r'metadata/COUVIS_0xxx/\2/\2_saturn_summary.lbl',
             r'metadata/COUVIS_0xxx/\2/\2_index.tab',
             r'metadata/COUVIS_0xxx/\2/\2_index.lbl',
             r'metadata/COUVIS_0xxx/\2/\2_supplemental_index.tab',
             r'metadata/COUVIS_0xxx/\2/\2_supplemental_index.lbl',
            ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/COUVIS_0.*/(EUV|FUV|HDAC|HSP)(\d{4}_\d{3}_\d\d_\d\d)(|_\d\d)(|_CAL_\d|_[a-z]+)\..*',  0, r'co-uvis-#LOWER#\1\2\3'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'co-uvis-(euv|fuv|hdac|hsp)(19.._...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_0001/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2000_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_0001/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2001_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_000[23]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2002_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_0004/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2003_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_000[56]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2004_...)_(.*)', 0, [r'volumes/COUVIS_0xxx/COUVIS_000[6-9]/DATA/D\2/#UPPER#\1\2_\3.DAT',
                                                       r'volumes/COUVIS_0xxx/COUVIS_0010/DATA/D\2/#UPPER#\1\2_\3.DAT']),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2005_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_001[0-3]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2006_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_001[4-7]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2007_...)_(.*)', 0, [r'volumes/COUVIS_0xxx/COUVIS_001[8-9]/DATA/D\2/#UPPER#\1\2_\3.DAT',
                                                       r'volumes/COUVIS_0xxx/COUVIS_002[0-1]/DATA/D\2/#UPPER#\1\2_\3.DAT']),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2008_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_002[2-5]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2009_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_002[6-9]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2010_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_003[0-3]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2011_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_003[4-7]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2012_...)_(.*)', 0, [r'volumes/COUVIS_0xxx/COUVIS_003[8-9]/DATA/D\2/#UPPER#\1\2_\3.DAT',
                                                       r'volumes/COUVIS_0xxx/COUVIS_004[0-1]/DATA/D\2/#UPPER#\1\2_\3.DAT']),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2013_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_004[2-5]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2014_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_004[6-9]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2015_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_005[0-3]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2016_...)_(.*)', 0,  r'volumes/COUVIS_0xxx/COUVIS_005[4-7]/DATA/D\2/#UPPER#\1\2_\3.DAT'),
    (r'co-uvis-(euv|fuv|hdac|hsp)(2017_...)_(.*)', 0, [r'volumes/COUVIS_0xxx/COUVIS_005[8-9]/DATA/D\2/#UPPER#\1\2_\3.DAT',
                                                       r'volumes/COUVIS_0xxx/COUVIS_0060/DATA/D\2/#UPPER#\1\2_\3.DAT']),
])

##########################################################################################
# Subclass definition
##########################################################################################

class COUVIS_0xxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for COUVIS_0xxx.

    The class body puts this module's rule tables in front of the class attributes
    ``Pds3File`` reads, and the module tail registers the class in
    ``Pds3File.SUBCLASSES`` under the key "COUVIS_0xxx".
    The module docstring describes the volume set and every table.

    It also carries ``VERSIONS_PATH_AND_KEY`` and defines ``DATA_SET_ID`` as a
    method rather than as a translator.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('COUVIS_0xxx', re.I, 'COUVIS_0xxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS
    SORT_KEY = sort_key + pds3file.Pds3File.SORT_KEY

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_FORMAT = opus_format + pds3file.Pds3File.OPUS_FORMAT
    OPUS_PRODUCTS = opus_products + pds3file.Pds3File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']  += associations_to_volumes
    ASSOCIATIONS['previews'] += associations_to_previews
    ASSOCIATIONS['metadata'] += associations_to_metadata
    ASSOCIATIONS['documents']  += associations_to_documents

    ############################################################################
    # DATA_SET_ID is defined as a function rather than a translator
    ############################################################################

    # Version tables reside in shelves/more_metadata/COUVIS_0xxx and _0xxx_v1
    VERSIONS_PATH_AND_KEY = translator.TranslatorByRegex([
        (r'volumes/COUVIS_0xxx(|_v\d)/(COUVIS_0...)/(.*)/(\w+)\.(DAT|LBL)', 0,
                    (r'metadata/COUVIS_0xxx/\2/\2\1_versions.tab', r'\4.LBL'))
    ])

    def DATA_SET_ID(self):
        """Return the PDS3 data set ID of this product.

        A COUVIS_0xxx data file's data set ID depends on which version of the volume
        set it belongs to, so it is looked up rather than derived from the path.
        ``VERSIONS_PATH_AND_KEY`` gives the metadata versions table that covers this
        file and the row key within it; the row is read from that table and its
        DATA_SET_ID column returned.

        Returns:
            str: the data set ID, and the empty string for an object that does not
            exist and for a directory.

        Raises:
            ValueError: if no versions table covers this file's logical path, and if
                the table that does covers it holds no row under the key.
            FileNotFoundError: if the versions table the lookup names is not on disk.
        """

        if not self.exists or self.isdir:
            return ''

        result = COUVIS_0xxx.VERSIONS_PATH_AND_KEY.first(self.logical_path)
        if not result:
            raise ValueError(f'Undefined DATA_SET_ID index for {self.logical_path}')

        (versions_path, key) = result

        # Confirm the file really exists, so we need to use os.path.exists, not
        # PdsFile.os_path_exists.
        abspath = self.root_ + versions_path

        # This block will never hit unless we have missing version files. Since all
        # version files exist in Dropbox, there is no way to test this.
        if not os.path.exists(abspath): # pragma: no cover
            raise FileNotFoundError(
                f'Missing DATA_SET_ID index for {self.logical_path}: {abspath}')

        versions_table = pds3file.Pds3File.from_abspath(abspath)
        row = versions_table.child_of_index(key, flag='')

        # This block will never hit unless we modify the version files or have a wrong
        # version file.
        if not row.exists: # pragma: no cover
            raise ValueError(
                f'DATA_SET_ID for {self.logical_path} not found in index: {versions_table}')

        return row.row_dicts[0]['DATA_SET_ID']

# Global attribute shared by all subclasses
pds3file.Pds3File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'co-uvis-[efh].*', 0, COUVIS_0xxx)]) + \
                                        pds3file.Pds3File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['COUVIS_0xxx'] = COUVIS_0xxx
