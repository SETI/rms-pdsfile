##########################################################################################
# pds4file/rules/cassini_iss_spokes_hedman_hamilton_2024.py
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
    (r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024[^/]*/(readme.txt|document/.*\.(pdf|txt|xml|lblx))',               0, ('Cassini ISS B Ring Reprojected Images', 160, 'coiss_b_ring_documentation', 'Documentation', False)),
    (r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024[^/]*/data_derived/.*/.*_rprj\.(fits|lblx)',              0, ('Cassini ISS B Ring Reprojected Images', 170, 'coiss_b_ring_reproj_img', 'Reprojected Image', False)),
    (r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024[^/]*/data_derived/.*/.*_rprj_suppl\.txt',              0, ('Cassini ISS B Ring Reprojected Images', 180, 'coiss_b_ring_reproj_img_spice_pointing', 'Reprojected Image SPICE Pointing', False)),
    (r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024[^/]*/browse_derived/.*/.*_rprj_browse\.png',              0, ('browse', 190, 'coiss_b_ring_browse_reproj_img', 'Browse Reprojected Image', False)),
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
