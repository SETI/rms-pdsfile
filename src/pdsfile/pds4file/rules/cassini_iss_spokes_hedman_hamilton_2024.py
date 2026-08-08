##########################################################################################
# pds4file/rules/cassini_iss_spokes_hedman_hamilton_2024.py
##########################################################################################

"""cassini_iss_spokes_hedman_hamilton_2024: rules for the B-ring spokes bundle set.

The bundle set on disk is named cassini_iss_spokes_hedman-hamilton-2024, with
hyphens; this module and its class are named
cassini_iss_spokes_hedman_hamilton_2024, with underscores, because a hyphen cannot
appear in a Python identifier. The bundle set is registered in
``Pds4File.SUBCLASSES`` under the hyphenated name.

It holds reprojected images of Saturn's B ring, in a ``data_derived/`` collection of
FITS files with ``.lblx`` labels and a text file of SPICE pointing for each, and a
``browse_derived/`` collection of PNG browse products. OPUS files the image and its
SPICE pointing file under the "Cassini ISS B Ring Reprojected Images" category and
the browse product under "browse", and offers all three with the PDS3 Cassini ISS
images rather than as products of this bundle; the tables in
`pds3file/rules/COISS_xxxx.py` are what reach them from the PDS3 side.

The rule tables:

* ``description_and_icon_by_regex``, ``view_options``, ``neighbors`` and
  ``sort_key`` -- all four are empty, so descriptions, view flags, adjacent
  directories and basename sort order are the defaults from
  `pds4file/rules/__init__.py`.
* ``opus_type`` -- the reprojected image and its SPICE pointing file, under the
  "Cassini ISS B Ring Reprojected Images" category, and its browse product under
  "browse".
* ``archive_paths`` and ``archive_dirs`` -- three archives: one for the whole
  bundle, one for ``data_derived/`` and one for ``browse_derived/``. The two partial
  archives also carry the bundle label, context, spice_kernels, schema and readme
  files a reader needs with them.
* ``product_lbl_basename_wo_ext`` -- pairs a ``_rprj_suppl.txt`` SPICE pointing file
  with the ``*_rprj`` label, whose basename it does not otherwise match.

``archive_paths`` and ``archive_dirs`` are defined here but the class body assigns
neither ``ARCHIVE_PATHS`` nor ``ARCHIVE_DIRS``, which is what the other four pds4
rule modules with archive tables do, so this bundle set uses the empty archive
tables from `pds4file/rules/__init__.py`. It is
also the only pds4 rule module with a subclass that defines no associations, no
viewables and no OPUS ID tables, and the only one that adds nothing to
``Pds4File.FILESPEC_TO_BUNDLESET``.
"""

import re

import translator

import pdsfile.pds4file as pds4file

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([

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
    (r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024[^/]*/data_derived/.*/.*_rprj\.(fits|lblx)',              0, ('Cassini ISS B Ring Reprojected Images', 150, 'coiss_b_ring_reproj_img', 'B Ring Reprojected Image', False)),
    (r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024[^/]*/data_derived/.*/.*_rprj_suppl\.txt',              0, ('Cassini ISS B Ring Reprojected Images', 160, 'coiss_b_ring_reproj_img_spice_pointing', 'B Ring Reprojected Image SPICE Pointing', False)),
    (r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024[^/]*/browse_derived/.*/.*_rprj_browse\.png',              0, ('browse', 170, 'coiss_b_ring_browse_reproj_img', 'B Ring Browse Reprojected Image', False)),
])

##########################################################################################
# Archives
##########################################################################################
# Three archive files
# - One archive for the entire bundle.
# - One archive for data_derived.
# - One archive for browse_derived.
archive_paths = translator.TranslatorByRegex([
    (r'.*(bundles|metadata|previews|diagrams)/(cassini_iss_spokes_hedman-hamilton-2024)(|/)$', 0, [
        r'archives-\1/\2/\2.tar.gz',
        r'archives-\1/\2/data_derived.tar.gz',
        r'archives-\1/\2/browse_derived.tar.gz',
    ]),
])

archive_dirs = translator.TranslatorByRegex([
    # include the entire bundle
    (r'.*archives-(.*/cassini_iss_spokes_hedman-hamilton-2024)/cassini_iss_spokes_hedman-hamilton-2024\.tar\.gz', 0, [
        r'\1',
    ]),
    # include:
    # - data_derived dir
    # - all files under document
    # - all the top-level support stuff (readme, bundle.xml, spice kernels, xml schema, etc.)
    (r'.*archives-(.*)/(cassini_iss_spokes_hedman-hamilton-2024)/data_derived\.tar\.gz', 0, [
        r'\1/\2/\2/data_derived',
        r'\1/\2/\2/bundle.lblx',
        r'\1/\2/\2/context',
        r'\1/\2/\2/readme.txt',
        r'\1/\2/\2/spice_kernels',
        r'\1/\2/\2/xml_schema',
    ]),
     # include:
    # - browse_derived dir
    # - all files under document
    # - all the top-level support stuff (readme, bundle.xml, spice kernels, xml schema, etc.)
    (r'.*archives-(.*)/(cassini_iss_spokes_hedman-hamilton-2024)/browse_derived\.tar\.gz', 0, [
        r'\1/\2/\2/browse_derived',
        r'\1/\2/\2/bundle.lblx',
        r'\1/\2/\2/context',
        r'\1/\2/\2/readme.txt',
        r'\1/\2/\2/spice_kernels',
        r'\1/\2/\2/xml_schema',
    ]),
])

##########################################################################################
# PRODUCT_LBL_BASENAME_WO_EXT
##########################################################################################

product_lbl_basename_wo_ext = translator.TranslatorByRegex([
    # Reprojected SPICE pointing (*_rprj_suppl.txt): paired label is *_rprj, not
    # *_rprj_suppl.
    (r'(.*_rprj)_suppl\.txt$', 0, [r'\1',]),
])

##########################################################################################
# Subclass definition
##########################################################################################

class cassini_iss_spokes_hedman_hamilton_2024(pds4file.Pds4File):
    """The ``Pds4File`` subclass for cassini_iss_spokes_hedman_hamilton_2024.

    The class body wires this module's rule tables onto the class attributes
    ``Pds4File`` reads. Where a table is added to the inherited one, a lookup tries
    this module's patterns first and falls through to the defaults; where it is
    assigned outright there is no fall-through. The module tail registers the class
    in ``Pds4File.SUBCLASSES`` under the key
    "cassini_iss_spokes_hedman-hamilton-2024".
    The module docstring describes the bundle set and every table.
    """

    pds4file.Pds4File.VOLSET_TRANSLATOR = translator.TranslatorByRegex(
        [('cassini_iss_spokes_hedman-hamilton-2024', re.I,
          'cassini_iss_spokes_hedman-hamilton-2024')]
    ) + pds4file.Pds4File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds4file.Pds4File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds4file.Pds4File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds4file.Pds4File.NEIGHBORS
    SORT_KEY = sort_key + pds4file.Pds4File.SORT_KEY

    OPUS_TYPE = opus_type + pds4file.Pds4File.OPUS_TYPE

    PRODUCT_LBL_BASENAME_WO_EXT = product_lbl_basename_wo_ext

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds4file.Pds4File.SUBCLASSES['cassini_iss_spokes_hedman-hamilton-2024'] = cassini_iss_spokes_hedman_hamilton_2024
