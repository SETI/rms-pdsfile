##########################################################################################
# pds4file/rules/cassini_uvis_solarocc_beckerjarmak2023.py
##########################################################################################

"""Rules for the cassini_uvis_solarocc_beckerjarmak2023 bundle set.

This bundle set holds derived radial occultation profiles of Saturn's rings from
solar occultation observations made with the Cassini UVIS instrument between June
2005 and June 2017 (bundle ``readme.txt`` under
``$PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023``). The bundle
set holds a single bundle of the same name. Its readme's own directory-structure
section lists ``readme.txt``, ``bundle.xml``, ``browse/``, ``context/``, ``data/``
with a ``supplemental/`` inside it, ``document/`` and ``xml_schema/``. The
``document/`` collection holds the two volumes of the ring solar occultation atlas
and the UVIS user guide. A data file is named
uvis_euv_<year>_<day>_solar_time_series_<ingress or egress>.

The rule tables:

* ``description_and_icon_by_regex`` -- empty. Descriptions for this bundle set come
  from the defaults in `pds4file/rules/__init__.py`.
* ``default_viewables`` -- points a data or supplemental table at its preview images.
* ``associations_to_bundles``, ``associations_to_previews``,
  ``associations_to_metadata`` and ``associations_to_documents`` -- cross the
  bundles, previews, metadata and documents trees for one occultation.
  ``associations_to_metadata`` matches the data files but returns an empty list, so
  no metadata association is produced.
* ``view_options``, ``neighbors`` and ``sort_key`` -- all three are empty, so the
  view flags, the adjacent directories and the basename sort order are the defaults.
* ``opus_type`` -- four rules, all of them under the "Cassini UVIS Solar
  Occultations" OPUS category: the time series, its supplement, the detailed browse
  and the documentation.
* ``opus_products`` -- the tables, browse products, previews, readme and the three
  named documents OPUS offers with one occultation.
* ``opus_id`` and ``opus_id_to_primary_logical_path`` -- an OPUS ID of the form
  co-uvis-occ-<year>-<day>-sun-<e or i>, and the path of the primary label it names.
* ``filespec_to_bundleset`` -- maps a file specification beginning with the bundle
  set name to the bundle set name itself.
* ``archive_paths`` and ``archive_dirs`` -- the whole bundle set is packaged as one
  archive named after itself, so both tables have a single entry.

`cassini_uvis_solarocc_beckerjarmak2023_primary_filespec.py` holds the list of
primary labels this bundle set offers, which this module re-exports.
"""

import re

import translator

import pdsfile.pds4file as pds4file

from .cassini_uvis_solarocc_beckerjarmak2023_primary_filespec import (
    PRIMARY_FILESPEC_LIST as PRIMARY_FILESPEC_LIST,
)

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
# Archives
##########################################################################################
# Bundle layout:
# - The cassini_uvis_solarocc_beckerjarmak2023 bundle set contains a single bundle
#   with the same name as the bundle set
# - The bundle includes:
#   - 'data/': primary occultation time series data files (tab/xml)
#   - 'data/supplemental/': supplemental data files
#   - 'browse/': browse images (jpg/xml)
#   - 'document/': documentation files (PDFs, XML)
#   - 'readme.txt': bundle readme file
#
# How archives are split:
# - All content is packaged into a single monolithic archive per bundle set
# - Archive name: '{bundle_set_name}.tar.gz' (e.g., 'cassini_uvis_solarocc_beckerjarmak2023.tar.gz')
# - This simple approach is used because:
#   - The bundle set contains a single bundle (not multiple bundles)
#   - The total data volume is relatively small
#   - All collections (data, browse, documents) are packaged together
#
# archive_paths: A TranslatorByRegex object that maps logical paths of bundle sets
# or bundles to lists of logical paths of archive file names. When given a PdsFile
# logical path (e.g., 'bundles/cassini_uvis_solarocc_beckerjarmak2023'), this
# translator returns the corresponding archive file path (e.g.,
# 'archives-bundles/cassini_uvis_solarocc_beckerjarmak2023/
# cassini_uvis_solarocc_beckerjarmak2023.tar.gz'). These archive paths are
# used by the archive_paths() method in Pds4File to determine which archive files
# are associated with a given bundle or bundle set.
archive_paths = translator.TranslatorByRegex([
    # input is the beckerjarmak bundle set
    (r'.*(bundles|metadata|previews|diagrams)/(cassini_uvis_solarocc_beckerjarmak2023)(|/)$', 0, [
        r'archives-\1/\2/\2.tar.gz'
    ]),
])

# archive_dirs: A TranslatorByRegex object that maps logical paths of archive files
# to lists of logical paths of directories included in those archives. When given
# an archive file path (e.g., 'archives-bundles/cassini_uvis_solarocc_beckerjarmak2023/
# cassini_uvis_solarocc_beckerjarmak2023.tar.gz'), this translator returns the
# directory paths that are packaged within that archive (e.g.,
# 'bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023').
# This mapping is used by the archive_dirs() method in Pds4File to determine which
# directories are included in each archive file.
archive_dirs = translator.TranslatorByRegex([
    (r'.*archives-(.*/cassini_uvis_solarocc_beckerjarmak2023)/(.*).tar.gz', 0, [r'\1']),
])

##########################################################################################
# Subclass definition
##########################################################################################

class cassini_uvis_solarocc_beckerjarmak2023(pds4file.Pds4File):
    """The ``Pds4File`` subclass for cassini_uvis_solarocc_beckerjarmak2023.

    The class body and the module tail install this module's rule tables on the class
    attributes ``Pds4File`` reads. `pds4file/rules/__init__.py` sets out the routes a
    table takes and which of them leaves the inherited rules in front. The class
    is registered in ``Pds4File.SUBCLASSES`` under the key
    "cassini_uvis_solarocc_beckerjarmak2023".
    The module docstring describes the bundle set and every table.
    """

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

    ARCHIVE_PATHS = archive_paths + pds4file.Pds4File.ARCHIVE_PATHS
    ARCHIVE_DIRS = archive_dirs + pds4file.Pds4File.ARCHIVE_DIRS

    pds4file.Pds4File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds4file.Pds4File.FILESPEC_TO_BUNDLESET

# Global attribute shared by all subclasses
pds4file.Pds4File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex(
    [(r'co-uvis-occ.*', 0, cassini_uvis_solarocc_beckerjarmak2023)]
) + pds4file.Pds4File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds4file.Pds4File.SUBCLASSES['cassini_uvis_solarocc_beckerjarmak2023'] = cassini_uvis_solarocc_beckerjarmak2023
