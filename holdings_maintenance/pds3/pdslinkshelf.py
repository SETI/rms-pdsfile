#!/usr/bin/env python3
################################################################################
# # pdslinkshelf.py library and main program
#
# Syntax:
#   pdslinkshelf.py --task path [path ...]
#
# Enter the --help option to see more information.
################################################################################

import argparse
import datetime
import glob
import os
import pickle
import re
import shutil
import sys

import pdslogger
import pdsfile
import translator

LOGNAME = 'pds.validation.links'
LOGROOT_ENV = 'PDS_LOG_ROOT'

# Holds log file directories temporarily, used by move_old_links()
LOGDIRS = []

# Default limits
GENERATE_LINKS_LIMITS = {'debug':200, 'ds_store':10}
LOAD_LINKS_LIMITS = {}
WRITE_LINKDICT_LIMITS = {}
VALIDATE_LINKS_LIMITS = {}

BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')

REPAIRS = translator.TranslatorByRegex([

    # COCIRS
    (r'.*/COCIRS_[01].*/DATAINFO\.TXT', 0,
      translator.TranslatorByDict(
        {'DIAG.FMT'             : 'UNCALIBR/DIAG.FMT',
         'FRV.FMT'              : 'UNCALIBR/FRV.FMT',
         'GEO.FMT'              : 'NAV_DATA/GEO.FMT',
         'HSK.FMT'              : 'HSK_DATA/HSK.FMT',
         'IFGM.FMT'             : 'UNCALIBR/IFGM.FMT',
         'IHSK.FMT'             : 'UNCALIBR/IHSK.FMT',
         'ISPM.FMT'             : 'APODSPEC/ISPM.FMT',
         'OBS.FMT'              : 'UNCALIBR/OBS.FMT',
         'POI.FMT'              : 'NAV_DATA/POI.FMT',
         'RIN.FMT'              : 'NAV_DATA/RIN.FMT',
         'TAR.FMT'              : 'NAV_DATA/TAR.FMT'})),
    (r'.*/COCIRS_[01].*/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'DATASIS.TXT'          : 'DOCUMENT/DATASIS.PDF',
         'VOLSYS.TXT'           : 'DOCUMENT/VOLSYS.PDF'})),
    (r'.*/COCIRS_[01].*/DATASET\.CAT', 0,
      translator.TranslatorByDict(
        {'DATASIS.TXT'          : 'DATASIS.PDF'})),
    (r'.*/COCIRS_[01].*/SOFTWARE/DOC/SDOCINFO\.TXT', 0,
      translator.TranslatorByDict(
        {'vanilla_guide.htm'    : 'vanilla-guide.html',
         'vanilla_guide.pdf'    : 'vanilla-guide.pdf'})),
    (r'.*/COCIRS_[01].*/DOCUMENT/DOCINFO\.TXT', 0,
      translator.TranslatorByDict(
        {'cirs_fov_overview.fig1.tiff' : 'cirs_fov_overview_fig1.tiff',
         'cirs_fov_overview.fig2.tiff' : 'cirs_fov_overview_fig2.tiff',
         'cirs_fov_overview.fig3.tiff' : 'cirs_fov_overview_fig3.tiff'})),
    (r'.*/COCIRS_[01].*/CUBE/.*\.(LBL|lbl)', 0,
      translator.TranslatorByRegex([
        (r'([0-9A-Z_]+)\.DAT', 0, r'\1.tar.gz')])),
    (r'.*/COCIRS_[56].*/TUTORIAL\.TXT', 0,
      translator.TranslatorByDict(
        {'GEODATA.FMT'          : '../DATA/GEODATA/GEODATA.FMT',
         'ISPMDATA.FMT'         : '../DATA/ISPMDATA/ISPMDATA.FMT',
         'POIDATA.FMT'          : '../DATA/POIDATA/POIDATA.FMT',
         'RINDATA.FMT'          : '../DATA/RINDATA/RINDATA.FMT',
         'TARDATA.FMT'          : '../DATA/TARDATA/TARDATA.FMT',
         'filename.FMT'         : ''})),
    (r'.*/COCIRS_[56].*/BROWSE/.*\.LBL', 0,
      translator.TranslatorByRegex([
        (r'(SPEC[0-9]{10}_FP[134]\.DAT)', 0, r'../../DATA/APODSPEC/\1'),
        (r'(ISPM[0-9]{10}_FP[134]\.TAB)', 0, r'../../DATA/ISPMDATA/\1'),
        (r'(RIN[0-9]{10}_FP[134]\.TAB)',  0, r'../../DATA/RINDATA/\1'),
        (r'(POI[0-9]{10}_FP[134]\.TAB)',  0, r'../../DATA/POIDATA/\1'),
        (r'(TAR[0-9]{10}_FP[134]\.TAB)',  0, r'../../DATA/TARDATA/\1'),
        (r'(GEO[0-9]{10}_[0-9]{3}\.TAB)', 0, r'../../DATA/GEODATA/\1')])),
    (r'.*/COCIRS_[56].*/DATA/APODSPEC/.*\.LBL', 0,
      translator.TranslatorByRegex([
        (r'(ISPM[0-9]{10}_FP[134]\.TAB)', 0, r'../ISPMDATA/\1'),
        (r'(RIN[0-9]{10}_FP[134]\.TAB)',  0, r'../RINDATA/\1'),
        (r'(POI[0-9]{10}_FP[134]\.TAB)',  0, r'../POIDATA/\1'),
        (r'(TAR[0-9]{10}_FP[134]\.TAB)',  0, r'../TARDATA/\1')])),
    (r'.*/COCIRS_[56].*/DATA/ISPMDATA/.*\.LBL', 0,
      translator.TranslatorByRegex([
        (r'(SPEC[0-9]{10}_FP[134]\.DAT)', 0, r'../APODSPEC/\1'),
        (r'(RIN[0-9]{10}_FP[134]\.TAB)',  0, r'../RINDATA/\1'),
        (r'(POI[0-9]{10}_FP[134]\.TAB)',  0, r'../POIDATA/\1'),
        (r'(TAR[0-9]{10}_FP[134]\.TAB)',  0, r'../TARDATA/\1')])),
    (r'.*/COCIRS_[56].*/DATA/RINDATA/.*\.LBL', 0,
      translator.TranslatorByRegex([
        (r'(SPEC[0-9]{10}_FP[134]\.DAT)', 0, r'../APODSPEC/\1'),
        (r'(ISPM[0-9]{10}_FP[134]\.TAB)', 0, r'../ISPMDATA/\1'),
        (r'(POI[0-9]{10}_FP[134]\.TAB)',  0, r'../POIDATA/\1'),
        (r'(TAR[0-9]{10}_FP[134]\.TAB)',  0, r'../TARDATA/\1')])),
    (r'.*/COCIRS_[56].*/DATA/POIDATA/.*\.LBL', 0,
      translator.TranslatorByRegex([
        (r'(SPEC[0-9]{10}_FP[134]\.DAT)', 0, r'../APODSPEC/\1'),
        (r'(ISPM[0-9]{10}_FP[134]\.TAB)', 0, r'../ISPMDATA/\1'),
        (r'(RIN[0-9]{10}_FP[134]\.TAB)',  0, r'../RINDATA/\1'),
        (r'(TAR[0-9]{10}_FP[134]\.TAB)',  0, r'../TARDATA/\1')])),
    (r'.*/COCIRS_[56].*/DATA/TARDATA/.*\.LBL', 0,
      translator.TranslatorByRegex([
        (r'(SPEC[0-9]{10}_FP[134]\.DAT)', 0, r'../APODSPEC/\1'),
        (r'(ISPM[0-9]{10}_FP[134]\.TAB)', 0, r'../ISPMDATA/\1'),
        (r'(RIN[0-9]{10}_FP[134]\.TAB)',  0, r'../RINDATA/\1'),
        (r'(POI[0-9]{10}_FP[134]\.TAB)',  0, r'../POIDATA/\1')])),
    (r'.*/COCIRS_[56].*/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'REF.CAT'              : 'CATALOG/CIRSREF.CAT'})),

    # COISS
    (r'.*/COISS_0.*\.lbl', 0,
      translator.TranslatorByDict(
        {'PREFIX8.FMT'          : 'prefix.fmt'})),
    (r'.*/COISS_00.*/aareadme\.txt', 0,
      translator.TranslatorByDict(
        {'calinfo.txt'          : '../COISS_0011/calib/calinfo.txt',
         'extrinfo.txt'         : '../COISS_0011/extras/extrinfo.txt'})),
    (r'.*/COISS_0.*/index\.lbl', 0,
      translator.TranslatorByDict(
        {'CUMINDEX.TAB'         : 'index.tab'})),
    (r'.*/COISS_0011/calib/darkcurrent/wac_\w+_dark_parameters04222\.lbl', 0,
      translator.TranslatorByRegex([
        (r'wac_(\w+)_dark_parameters04228\.xdr', 0, r'wac_\1_dark_parameters04222.xdr')])),
    (r'.*/COISS_[012].*/aareadme\.txt', 0,
      translator.TranslatorByDict(
        {'Calds.CAT'            : '../../COISS_0xxx/COISS_0001/catalog/calds.cat',
         'calds.cat'            : '../../COISS_0xxx/COISS_0001/catalog/calds.cat',
         'Jupiterds.CAT'        : '../../COISS_1xxx/COISS_1001/catalog/jupiterds.cat',
         'jupiterds.cat'        : '../../COISS_1xxx/COISS_1001/catalog/jupiterds.cat',
         'Saturnds.CAT'         : '../../COISS_2xxx/COISS_2001/catalog/saturnds.cat',
         'saturnds.cat'         : '../../COISS_2xxx/COISS_2001/catalog/saturnds.cat',
         'calinfo.txt'          : '../../COISS_0xxx/COISS_0011/calib/calinfo.txt',
         'calib.tar.gz'         : '../../COISS_0xxx/COISS_0011/calib/calib.tar.gz',
         'in_flight_cal.tex'    : '../../COISS_0xxx/COISS_0011/document/in_flight_cal.tex',
         'in_flight_cal.pdf'    : '../../COISS_0xxx/COISS_0011/document/in_flight_cal.pdf',
         'in_flight_cal.lbl'    : '../../COISS_0xxx/COISS_0011/document/in_flight_cal.lbl',
         'theoretical_basis.tex': '../../COISS_0xxx/COISS_0011/document/theoretical_basis.tex',
         'theoretical_basis.pdf': '../../COISS_0xxx/COISS_0011/document/theoretical_basis.pdf',
         'theoretical_basis.lbl': '../../COISS_0xxx/COISS_0011/document/theoretical_basis.lbl',
         'theoretical_basis.ps' : '../../COISS_0xxx/COISS_0011/document/theoretical_basis.pdf',
         'cisscal.tar.gz'       : '../../COISS_0xxx/COISS_0011/extras/cisscal.tar.gz'})),
    (r'.*/COISS_[012].*/archsis\.txt', 0,
      translator.TranslatorByDict(
        {'Calds.CAT'            : '../../../COISS_0xxx/COISS_0001/catalog/calds.cat',
         'calds.cat'            : '../../../COISS_0xxx/COISS_0001/catalog/calds.cat',
         'Jupiterds.CAT'        : '../../../COISS_1xxx/COISS_1001/catalog/jupiterds.cat',
         'jupiterds.cat'        : '../../../COISS_1xxx/COISS_1001/catalog/jupiterds.cat',
         'Saturnds.CAT'         : '../../../COISS_2xxx/COISS_2001/catalog/saturnds.cat',
         'saturnds.cat'         : '../../../COISS_2xxx/COISS_2001/catalog/saturnds.cat'})),

    # COUVIS
    (r'.*/COUVIS_0.*/INDEX\.LBL', 0,
      translator.TranslatorByDict(
        {'CUBEDS.CAT'           : '../CATALOG/SCUBEDS.CAT'})),
    (r'.*/COUVIS_0.*/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'INST.CAT'             : 'CATALOG/UVISINST.CAT',
         'XCALDS.CAT'           : 'CATALOG/SCALDS.CAT',
         'XCUBEDS.CAT'          : 'CATALOG/SCUBEDS.CAT',
         'XSPECDS.CAT'          : 'CATALOG/SSPECDS.CAT',
         'XSSBDS.CAT'           : 'CATALOG/SSSBDS.CAT',
         'XWAVDS.CAT'           : 'CATALOG/SWAVDS.CAT'})),
    (r'.*/COUVIS_0.*/CATALOG/.*\.CAT', 0,
      translator.TranslatorByDict(
        {'SPECDS.CAT'           : 'SSPECDS.CAT',
         'CUBEDS.CAT'           : 'SCUBEDS.CAT'})),
    (r'.*/COUVIS_0.*/SOFTWARE/READERS/READERS_README.TXT', 0,
      translator.TranslatorByDict(
        {'CATALOG/CUBEDS.CAT'   : '../../CATALOG/SCUBEDS.CAT'})),
    (r'.*/COUVIS_0.*/SOFTWARE/READERS/OLD.*/READERS_README.TXT', 0,
      translator.TranslatorByDict(
        {'CATALOG/CUBEDS.CAT'   : '../../../CATALOG/SCUBEDS.CAT'})),
    (r'.*/COUVIS_8xxx/.*/aareadme\.txt', 0,
      translator.TranslatorByDict(
        {'inst.cat'             : 'catalog/uvisinst.cat'})),
    (r'.*/COUVIS_8xxx_v1.*/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'INST.CAT'             : 'CATALOG/UVISINST.CAT'})),
    (r'.*/COUVIS_8xxx_v2.*/voldesc\.cat', 0,
      translator.TranslatorByDict(
        {'UVISINST.CAT'         : 'catalog/inst.cat',
         'PROJREF.CAT'          : ''})),
    (r'.*/COUVIS_8xxx_v1/.*/CATINFO\.TXT', re.I,
      translator.TranslatorByDict(
        {'INST.CAT'             : 'UVISINST.CAT'})),
    (r'.*/COUVIS_8xxx(|_v2\.0)/.*/voldesc\.cat', re.I,
      translator.TranslatorByDict(
        {'PROJREF.CAT'          : ''})),
    (r'.*/metadata/.*/COUVIS_0.*_index\.lbl', 0,
      translator.TranslatorByDict(
        {'CUBEDS.CAT'           : ''})),

    # COVIMS
    (r'.*/COVIMS_0001/aareadme\.txt', 0,
      translator.TranslatorByDict(
        {'band_bin_center.fmt'   : '../COVIMS_0002/label/band_bin_center.fmt',
         'core_description.fmt'  : '../COVIMS_0002/label/core_description.fmt',
         'suffix_description.fmt': '../COVIMS_0002/label/suffix_description.fmt',
         'labinfo.txt'           : '../COVIMS_0002/label/labinfo.txt'})),
    (r'.*/COVIMS_0.../aareadme\.txt', 0,
      translator.TranslatorByDict(
        {'caldoc.txt'            : 'software/doc/caldoc.txt',
         'make_dark.sav'         : 'software/bin/make_dark.sav',
         'ppvl_10_1.zip'         : 'software/lib/ppvl_1_10.zip',
         'ppvl_1_10.zip'         : 'software/lib/ppvl_1_10.zip',
         'libPPVL.a'             : 'software/lib/ppvl_1_10/libPPVL.a',
         'Makefile'              : 'software/lib/ppvl_1_10/Makefile',
         'Makefile.sun'          : 'software/lib/ppvl_1_10/Makefile.sun',
         'PIRL_strings.c'        : 'software/lib/ppvl_1_10/PIRL_strings.c',
         'PIRL_strings.h'        : 'software/lib/ppvl_1_10/PIRL_strings.h',
         'PPVL.c'                : 'software/lib/ppvl_1_10/PPVL.c',
         'PPVL.h'                : 'software/lib/ppvl_1_10/PPVL.h',
         'PPVL-README'           : 'software/lib/ppvl_1_10/PPVL-README',
         'PPVL_report.c'         : 'software/lib/ppvl_1_10/PPVL_report.c',
         'PPVL_selections.c'     : 'software/lib/ppvl_1_10/PPVL_selections.c',
         'PPVL_selections.h'     : 'software/lib/ppvl_1_10/PPVL_selections.h',
         'RANLIB.csh'            : 'software/lib/ppvl_1_10/RANLIB.csh',
         'README'                : 'software/lib/ppvl_1_10/README',
         'PPVL.3'                : 'software/lib/ppvl_1_10/doc/PPVL.3',
         'PPVL_selections.3'     : 'software/lib/ppvl_1_10/doc/PPVL_selections.3',
         'PPVL_report.1'         : 'software/lib/ppvl_1_10/doc/PPVL_report.1',
         'PPVL_get_PDS_EOL.3'    : 'software/lib/ppvl_1_10/doc/PPVL_get_PDS_EOL.3',
         'bp_trans.c'            : 'software/src/c/cube_prep/bp_trans.c',
         'cube_prep.c'           : 'software/src/c/cube_prep/cube_prep.c',
         'error.h'               : 'software/src/c/ir_bg/error.h',
         'fit.c'                 : 'software/src/c/ir_bg/fit.c',
         'ir_bg.c'               : 'software/src/c/ir_bg/ir_bg.c',
         'ir_bg_sub.c'           : 'software/src/c/ir_bg_sub/ir_bg_sub.c',
         'mark_saturated.c'      : 'software/src/c/mark_saturated/mark_saturated.c',
         'make_dark.pro'         : 'software/src/idl/make_dark.pro',
         'vims_cal_pipe.pl'      : 'software/src/perl/vims_cal_pipe.pl',
         'cal_pipe2.pm'          : 'software/src/perl/cal_pipe2/cal_pipe2.pm',
         'cal_occultation.pm'    : 'software/src/perl/cal_pipe2/cal_occultation.pm',
         'cal_point.pm'          : 'software/src/perl/cal_pipe2/cal_point.pm',
         'dark_vis.pm'           : 'software/src/perl/cal_pipe2/dark_vis.pm',
         'flat_ir2.pm'           : 'software/src/perl/cal_pipe2/flat_ir2.pm',
         'flat_vis2.pm'          : 'software/src/perl/cal_pipe2/flat_vis2.pm',
         'isis_geo.pm'           : 'software/src/perl/cal_pipe2/isis_geo.pm',
         'solar_remove.pm'       : 'software/src/perl/cal_pipe2/solar_remove.pm',
         'specific_energy.pm'    : 'software/src/perl/cal_pipe2/specific_energy.pm'})),
    (r'.*/COVIMS_0001/data/.*\.lbl', 0,
      translator.TranslatorByDict(
        {'band_bin_center.fmt'   : '../../../COVIMS_0002/label/band_bin_center.fmt',
         'core_description.fmt'  : '../../../COVIMS_0002/label/core_description.fmt',
         'suffix_description.fmt': '../../../COVIMS_0002/label/suffix_description.fmt',
         'BAND_BIN_CENTER.FMT'   : '../../../COVIMS_0002/label/band_bin_center.fmt',
         'CORE_DESCRIPTION.FMT'  : '../../../COVIMS_0002/label/core_description.fmt',
         'SUFFIX_DESCRIPTION.FMT': '../../../COVIMS_0002/label/suffix_description.fmt'})),
    (r'.*/COVIMS_0001/document/archsis\.txt', 0,
      translator.TranslatorByDict(
        {'band_bin_center.fmt'   : '../../COVIMS_0002/label/band_bin_center.fmt',
         'core_description.fmt'  : '../../COVIMS_0002/label/core_description.fmt',
         'suffix_description.fmt': '../../COVIMS_0002/label/suffix_description.fmt',
         'BAND_BIN_CENTER.FMT'   : '../../COVIMS_0002/label/band_bin_center.fmt',
         'CORE_DESCRIPTION.FMT'  : '../../COVIMS_0002/label/core_description.fmt',
         'SUFFIX_DESCRIPTION.FMT': '../../COVIMS_0002/label/suffix_description.fmt'})),
    (r'.*/COVIMS_0.*/document/archsis\.txt', 0,
      translator.TranslatorByDict(
        {'suffix.cat'            : ''})),
    (r'.*/COVIMS_0.*/errata\.txt', 0,
      translator.TranslatorByDict(
        {'center.fmt'            : 'label/band_bin_center.fmt'})),
    (r'.*/COVIMS_0024/data/2008017T190718_2008017T201544/v1579292302_1\.lbl', 0,
      translator.TranslatorByDict(
        {"v1579292302.qub"      : "v1579292302_1.qub"})),
    (r'.*/metadata/COVIMS.*/.*supplemental_index.lbl', 0,
      translator.TranslatorByDict(
        {'dpsis.txt': '../../../volumes/COVIMS_0xxx/COVIMS_0001/document/dpsis.txt'})),
    (r'.*/COVIMS_8xxx_v2.*/voldesc.cat', 0,
      translator.TranslatorByDict(
        {'PROJREF.CAT'          : ''})),

    # EBROCC
    (r'.*/EBROCC_0001/INDEX/MCD_INDEX\.LBL', 0,
      translator.TranslatorByDict(
        {'LIC_INDEX.TAB'        : 'MCD_INDEX.TAB'})),
    (r'.*/EBROCC_0001/INDEX/PAL_INDEX\.LBL', 0,
      translator.TranslatorByDict(
        {'LIC_INDEX.TAB'        : 'PAL_INDEX.TAB'})),
    (r'.*/EBROCC_0001/SORCDATA/ESO1M/ES1_INGRESS_GEOMETRY\.LBL', 0,
      translator.TranslatorByDict(
        {'ES1_INGRESS_GEOMETRY.LBL': 'ES1_INGRESS_GEOMETRY.DAT'})),

    # GO
    (r'.*/GO_0xxx.*/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'ttds.cat'             : '../GO_0020/CATALOG/TTDS.CAT'})),
    (r'.*/GO_0xxx_v1/GO_00(0[789]|1[0-6])/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'CATSTATUS.TXT'        : 'DOCUMENT/CATSTAT.TXT'})),
    (r'.*/GO_0xxx.*/GO_0001/CATALOG/DATASET\.CAT', 0,
      translator.TranslatorByRegex(
        [(r'(\w\w\w[1-4][sf]_blm02\.img)', 0, r'../BLEMISH/#UPPER#\1'),
         (r'(\w\w\w[sf]_cal0[1-5]\.dat)',  0, r'../SLOPE/#UPPER#\1'),
         (r'([123][sf]\w+_dc0[1-5]\.dat)', 0, r'../DARK/#UPPER#\1'),
         (r'calibration_so02.img',         0, r'../SHUTTER/CALIBRATION_SO02.IMG')])),
    (r'.*/GO_0xxx.*/GO_000[2-6]/CATALOG/DATASET\.CAT', 0,
      translator.TranslatorByDict(
        {'V_E1DS.CAT'           : ''})),
    (r'.*/GO_0xxx.*/GO_0001/DOCUMENT/PDSLABEL\.TXT', 0,
      translator.TranslatorByDict(
        {'RLINEPRX.FMT'         : '../../GO_0002/LABEL/RLINEPRX.FMT',
         'RTLMTAB.FMT'          : '../../GO_0002/LABEL/RTLMTAB.FMT'})),
    (r'.*/GO_0xxx_v1/GO_0001/INDEX/CUMINDEX\.LBL', 0,
      translator.TranslatorByDict(
        {'IMGINDEX.TAB'         : 'CUMINDEX.TAB'})),
    (r'.*/GO_0xxx_v1/GO_0001/INDEX/P1CUMINDEX\.LBL', 0,
      translator.TranslatorByDict(
        {'IMGINDEX.TAB'         : 'P1CUMINDEX.TAB'})),

    # HST
    (r'.*/HSTJ.*/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'NST.CAT'              : 'CATALOG/INST.CAT'})),
    (r'.*/HSTJ.*/CATINFO\.TXT', 0,
      translator.TranslatorByDict(
        {'NST.CAT'              : 'INST.CAT'})),
    (r'.*/HSTJ.*_v.*/HSTJ1_0427/DATA/VISIT_02/.*\.LBL', 0,
      translator.TranslatorByDict(
        {'J96O02JLQ_FLT_WFC1.JPG': '',
         'J96O02JMQ_FLT_WFC1.JPG': '',
         'J96O02JLQ_FLT_WFC2.JPG': 'J96O02JLQ_FLT.JPG',
         'J96O02JMQ_FLT_WFC2.JPG': 'J96O02JMQ_FLT.JPG',
         'J96O02JOQ_FLT_WFC2.JPG': 'J96O02JOQ_FLT.JPG',
         'J96O02JQQ_FLT_WFC2.JPG': 'J96O02JQQ_FLT.JPG',
         'J96O02JSQ_FLT_WFC2.JPG': 'J96O02JSQ_FLT.JPG'})),
    (r'.*/HSTJx_xxxx.*_v.*/HSTJ1_2395/DATA/.*\.LBL', 0,
      translator.TranslatorByDict(
        {'JBNY02SOQ_FLT_WFC1.JPG': '',
         'JBNY02SOQ_FLT_WFC2.JPG': 'JBNY02SOQ_FLT.JPG',
         'JBNY02SQQ_FLT_WFC2.JPG': 'JBNY02SQQ_FLT.JPG',
         'JBNY02SSQ_FLT_WFC2.JPG': 'JBNY02SSQ_FLT.JPG',
         'JBNYA1T2Q_FLT_WFC2.JPG': 'JBNYA1T2Q_FLT.JPG',
         'JBNYA2SUQ_FLT_WFC2.JPG': 'JBNYA2SUQ_FLT.JPG'})),

    # JNOJIR
    (r'.*/JNOJIR.*/AAREADME.TXT', 0,
      translator.TranslatorByDict(
        {'PERSON.CAT'           : 'JNO_JIRAM_PERSON.CAT',
         'DATAINFO.TXT'         : ''})),
    (r'.*/JNOJIR.*/JIR_IMG_\w+_RESPONSIVITY_V03.LBL', 0,
      translator.TranslatorByRegex(
        [(r'(JIR_IMG_\w+_RESPONSIVITY)_V02\.DAT', 0, r'\1_V03.DAT')])),
    (r'.*/JNOJIR_20(2[789]|3\d)/DATA/JIR_\w+.LBL', 0,
      translator.TranslatorByRegex(
        [(r'(JIR_IMG_\w+_RESPONSIVITY)_V02\.DAT', 0, r'../CALIB/\1_V03.DAT')])),
    # Embedded list comprehension
    # Each links a SOURCE_PRODUCT_ID on JNOJIR_2nnn to the associated EDR in
    # the parallel directory on JNOJIR_1nnn. Set up through volume _2049.
    ] + [
        (fr'.*/JNOJIR_xxxx/JNOJIR_20{nn:02d}/DATA/JIR_\w+.LBL', 0,
          translator.TranslatorByRegex(
            [(r'(JIR_\w+_EDR_20\w+)\.(DAT|IMG)', 0,
                fr'../../JNOJIR_10{nn:02d}/DATA/\1.\2')]))
        for nn in range(0,50)] + [

    # JNOJNC
    (r'.*/JNOJNC.*/(AAREADME|CATINFO).TXT', 0,
      translator.TranslatorByDict(
        {'JUNO_REF.CAT'         : 'JUNO_PROJREF.CAT'})),

    # NHSP (and *SP_xxxx)
    (r'.*/NHSP_xxxx_v1.*/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'personel.cat'         : 'CATALOG/PERSONNEL.CAT',
         'spiceds.cat'          : 'CATALOG/SPICE_INST.CAT'})),
    (r'.*SP_xxxx.*/aareadme\.txt', 0,
      translator.TranslatorByDict(
        {'dataset.cat'          : 'catalog/spiceds.cat',
         'ckinfo.txt'           : 'data/ck/ckinfo.txt',
         'ekinfo.txt'           : 'data/ek/ekinfo.txt',
         'fkinfo.txt'           : 'data/fk/fkinfo.txt',
         'ikinfo.txt'           : 'data/ik/ikinfo.txt',
         'lskinfo.txt'          : 'data/lsk/lskinfo.txt',
         'pckinfo.txt'          : 'data/pck/pckinfo.txt',
         'sclkinfo.txt'         : 'data/sclk/sclkinfo.txt',
         'spkinfo.txt'          : 'data/spk/spkinfo.txt',
         'ckdoc.txt'            : 'document/ck/ckdoc.txt',
         'ekdoc.txt'            : 'document/ek/ekdoc.txt',
         'mkinfo.txt'           : 'extras/mk/mkinfo.txt',
         'orbinfo.txt'          : 'extras/orbnum/orbinfo.txt',
         'spkxinfo.txt'         : 'extras/spkxtra/spkxinfo.txt',
         'covinfo.txt'          : 'extras/spkxtra/covtab/covinfo.txt',
         'ckxtinfo.txt'         : 'extras/ckxtra/ckxtinfo.txt',
         'navinfo.txt'          : 'extras/ckxtra/cknav/navinfo.txt',
         'issinfo.txt'          : 'extras/ckxtra/ckiss/issinfo.txt'})),

    # NHxxMV/NHxxLO
    (r'.*/NHxx.._xxxx_v1/NH(JU|LA).*/aareadme\.txt', 0,
      translator.TranslatorByDict(
        {'PAYLOAD_SSR.LBL'      : 'document/payload_ssr/payload_ssr.lbl',
         'RALPH_SSR.LBL'        : 'document/ralph_ssr/ralph_ssr.lbl',
         'SOC_INST_ICD.LBL'     : 'document/soc_inst_icd/soc_inst_icd.lbl'})),
    (r'.*/NHxx.._xxxx_v1/NH(JU|LA).*/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'PAYLOAD_SSR.LBL'      : 'DOCUMENT/PAYLOAD_SSR/PAYLOAD_SSR.LBL',
         'RALPH_SSR.LBL'        : 'DOCUMENT/RALPH_SSR/RALPH_SSR.LBL',
         'SOC_INST_ICD.LBL'     : 'DOCUMENT/SOC_INST_ICD/SOC_INST_ICD.LBL'})),
    (r'.*/NHxxLO_xxxx.*/NH..LO_2001/data/\w+/.*\.lbl', 0,
      translator.TranslatorByRegex(
        [(r'cflat_grnd_SFA_(\w+\.fit)', 0, r'../../calib/cflat_grnd_sfa_\1'),
         (r'(cflat|dead|delta|dsmear|hot|sap)_(\w+\.fit)', 0, r'../../calib/\1_\2')])),
    (r'.*/NHxxMV_xxxx.*/NH..MV_2001/data/\w+/.*\.lbl', 0,
      translator.TranslatorByRegex(
        [(r'(mc[0-3])_(flat_\w+\.fit)s', 0, r'../../calib/mcl/\1_\2'),
         (r'(mp[12])_(flat_\w+\.fit)s',  0, r'../../calib/mp/\1_\2'),
         (r'(mfr_flat_\w+\.fit)s',       0, r'../../calib/mfr/\1')])),

    # RPX
    (r'.*/RPX_0101.*/R_HARRIS\.LBL', 0,
      translator.TranslatorByDict(
        {'R_HARRIS.DF'          : 'R_HARRIS.PDF'})),
    (r'.*/RPX_0101.*/F161225AB\.LBL', 0,
      translator.TranslatorByDict(
        {'F161225RB.GIF'        : 'F161225AB.GIF'})),
    (r'.*/RPX_0201.*/T0808_F1498_CAL\.LBL', 0,
      translator.TranslatorByDict(
        {'T0808_F1497_CAL.IMG'  : 'T0808_F1498_CAL.IMG'})),
    (r'.*/RPX_0401/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'INSTHOST.CAT'         : 'CATALOG/HOST.CAT'})),

    # Any VG
    (r'.*/VG.*/CATALOG/CATINFO\.TXT', 0,
      translator.TranslatorByDict(
        {'VGnNINST.CAT'         : 'VG1NINST.CAT',
         'VGnHOST.CAT'          : 'VG1HOST.CAT'})),

    # VG_20xx (IRIS)
    (r'.*/VG_2001/.*/VG2_SAT\.LBL', 0,
      translator.TranslatorByDict(
        {'IRIS_ROWFMT.FMT'      : '../JUPITER/IRISHEDR.FMT'})),
    (r'.*/VG_2001/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'IRISHEDR.FMT'         : 'JUPITER/IRISHEDR.FMT',
         'IRISTRGP.FMT'         : 'JUPITER/CALIB/IRISTRGP.FMT'})),

    # VG_28xx (ring profiles)
    (r'.*/VG_28[0-9]{2}/.*INFO\.TXT', 0,
      translator.TranslatorByDict(
        {'RS1SINST.CAT'         : 'VG1SINST.CAT',
         'RS2UINST.CAT'         : 'VG2UINST.CAT'})),
    (r'.*/VG_28xx/VG_2801/CALIB/PS2C01\.LBL', 0,
      translator.TranslatorByDict(
        {'PS1C01.TAB'           : 'PS2C01.TAB'})),
    (r'.*/VG_28xx/VG_2801/JITTER/PS1J01\.LBL', 0,
      translator.TranslatorByDict(
        {'PS1J02.TAB'           : 'PS1J01.TAB'})),
    (r'.*/VG_28xx/VG_2801/JITTER/PU2J02\.LBL', 0,
      translator.TranslatorByDict(
        {'PU2J01.TAB'           : 'PU2J02.TAB'})),
    (r'.*/VG_280./.*/L3GUIDE\.TXT', 0,
      translator.TranslatorByDict(
        {'RTLMTAB.FMT'          : ''})),
    (r'.*/VG_2802/EDITDATA/DATAINFO\.TXT', 0,
      translator.TranslatorByDict(
        {'INST.CAT'             : '../CATALOG/VG1INST.CAT'})),
    (r'.*/VG_2802/EDITDATA/US3D01P\.LBL', 0,
      translator.TranslatorByDict(
        {'US3D01I.DAT'          : 'US3D01P.DAT'})),
    (r'.*/VG_2802/SORCDATA/DATAINFO\.TXT', 0,
      translator.TranslatorByDict(
        {'BETAPER.VOY'          : 'BETPER.VOY',
         'BETAPER.LBL'          : 'BETPER.LBL'})),
    (r'.*/VG_2803.*/RS.R1BFV\.LBL', 0,
      translator.TranslatorByDict(
        {'RS_R1BFT.FMT'         : 'RS_R1BFV.FMT'})),

    # VGn_9xxx (RSS)
    (r'.*/VG[12]_9.*/CHECKSUMS.TXT', 0,  # any file referenced in CHECKSUMS.TXT
                                        # already has a full path; don't search
      translator.TranslatorByRegex([(r'(.*)', 0, r'\1')])),
    (r'.*/VG[12]_9.*/ERRATA.TXT', 0,
      translator.TranslatorByDict(
        {'_PERSON.CAT'          : 'CATALOG/VG_RSS_PERSON.CAT'})),
    (r'.*/VG1_9050/CATALOG/CATINFO.TXT', 0,
      translator.TranslatorByDict(
        {'MISSION.CAT'          : 'VG_MISSION.CAT',
         'INST_HOST.CAT'        : 'VG1_INST_HOST.CAT',
         'INST.CAT'             : 'VG1_RSS_INST.CAT',
         'DS.CAT'               : 'VG1_SAT_RSS_DS.CAT',
         'PERSON.CAT'           : 'VG_RSS_PERSON.CAT',
         'REF.CAT'              : 'VG1_S_RSS_REF.CAT',
         'TARGET.CAT'           : 'VG_SAT_TARGET.CAT',
         'VG1_SAT_TARGET.CAT'   : 'VG_SAT_TARGET.CAT'})),
    (r'.*/VG1_9056/CATALOG/CATINFO.TXT', 0,
      translator.TranslatorByDict(
        {'MISSION.CAT'          : 'VG_MISSION.CAT',
         'INSTHOST.CAT'         : 'VG1_INST_HOST.CAT',
         'INST.CAT'             : 'VG1_RSS_INST.CAT',
         'DS.CAT'               : 'VG1_SSA_RSS_DS.CAT',
         'PERSON.CAT'           : 'VG_RSS_PERSON.CAT',
         'REF.CAT'              : 'VG1_SSA_RSS_REF.CAT',
         'TARGET.CAT'           : 'VG_TITAN_TARGET.CAT'})),
    (r'.*/VG2_9065/CATALOG/CATINFO.TXT', 0,
      translator.TranslatorByDict(
        {'MISSION.CAT'          : 'VG_MISSION.CAT',
         'INSTHOST.CAT'         : 'VG2_INST_HOST.CAT',
         'INST.CAT'             : 'VG2_RSS_INST.CAT',
         'DS.CAT'               : 'VG2_S_RSS_DS.CAT',
         'PERSON.CAT'           : 'VG_RSS_PERSON.CAT',
         'REF.CAT'              : 'VG2_S_RSS_REF.CAT',
         'TARGET.CAT'           : 'VG_SAT_TARGET.CAT'})),

    # VGIRIS
    (r'.*/VGIRIS_0001/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'JUPITER_ASCII.FMT'    : 'DATA/JUPITER_VG1/JUPITER_ASCII.FMT',
         'JUPITER_LSB.FMT'      : 'DATA/JUPITER_VG1/JUPITER_LSB.FMT',
         'JUPITER_MSB.FMT'      : 'DATA/JUPITER_VG1/JUPITER_MSB.FMT',
         'SATURN_ASCII.FMT'     : '',
         'SATURN_LSB.FMT'       : '',
         'SATURN_MSB.FMT'       : '',
         'VGnINST.CAT'          : 'CATALOG/VG1INST.CAT',
         'VGnHOST.CAT'          : 'CATALOG/VG1HOST.CAT'})),
    (r'.*/VGIRIS_0001/DATA/DATAINFO\.TXT', 0,
      translator.TranslatorByDict(
        {'JUPITER_ASCII.FMT'    : 'JUPITER_VG1/JUPITER_ASCII.FMT',
         'JUPITER_LSB.FMT'      : 'JUPITER_VG1/JUPITER_LSB.FMT',
         'JUPITER_MSB.FMT'      : 'JUPITER_VG1/JUPITER_MSB.FMT',
         'SATURN_ASCII.FMT'     : '',
         'SATURN_LSB.FMT'       : '',
         'SATURN_MSB.FMT'       : '',
         'VGnINST.CAT'          : '../CATALOG/VG1INST.CAT',
         'VGnHOST.CAT'          : '../CATALOG/VG1HOST.CAT'})),
    (r'.*/VGIRIS_0002/AAREADME\.TXT', 0,
      translator.TranslatorByDict(
        {'JUPITER_ASCII.FMT'    : '',
         'JUPITER_LSB.FMT'      : '',
         'JUPITER_MSB.FMT'      : '',
         'SATURN_ASCII.FMT'     : 'DATA/SATURN_VG1/SATURN_ASCII.FMT',
         'SATURN_LSB.FMT'       : 'DATA/SATURN_VG1/SATURN_LSB.FMT',
         'SATURN_MSB.FMT'       : 'DATA/SATURN_VG1/SATURN_MSB.FMT',
         'VGnINST.CAT'          : 'CATALOG/VG1INST.CAT',
         'VGnHOST.CAT'          : 'CATALOG/VG1HOST.CAT'})),
    (r'.*/VGIRIS_0002/DATA/DATAINFO\.TXT', 0,
      translator.TranslatorByDict(
        {'JUPITER_ASCII.FMT'    : '',
         'JUPITER_LSB.FMT'      : '',
         'JUPITER_MSB.FMT'      : '',
         'SATURN_ASCII.FMT'     : 'SATURN_VG1/SATURN_ASCII.FMT',
         'SATURN_LSB.FMT'       : 'SATURN_VG1/SATURN_LSB.FMT',
         'SATURN_MSB.FMT'       : 'SATURN_VG1/SATURN_MSB.FMT',
         'VGnINST.CAT'          : '../CATALOG/VG1INST.CAT',
         'VGnHOST.CAT'          : '../CATALOG/VG1HOST.CAT'})),

    # VGISS
    (r'.*/VGISS.*/BROWSE/C34801XX/C3480139_.*\.LBL', 0,
      translator.TranslatorByDict(
        {'C3480140_CALIB.JPG'   : 'C3480139_CALIB.JPG',
         'C3480140_CLEANED.JPG' : 'C3480139_CLEANED.JPG',
         'C3480140_GEOMED.JPG'  : 'C3480139_GEOMED.JPG',
         'C3480140_RAW.JPG'     : 'C3480139_RAW.JPG'})),
    (r'.*/VGISS.*/BROWSE/C43892XX/C4389208_.*\.LBL', 0,
      translator.TranslatorByDict(
        {'C4389209_CALIB.JPG'   : 'C4389208_CALIB.JPG',
         'C4389209_CLEANED.JPG' : 'C4389208_CLEANED.JPG',
         'C4389209_GEOMED.JPG'  : 'C4389208_GEOMED.JPG',
         'C4389209_RAW.JPG'     : 'C4389208_RAW.JPG'})),
])

KNOWN_MISSING_LABELS = translator.TranslatorByRegex([
    (r'.*/document/.*',                                     re.I, 'missing'),
    (r'.*/COCIRS_.*\.VAR',                                  0,    'missing'),
    (r'.*/COCIRS_.*VANILLA.*',                              re.I, 'missing'),
    (r'.*/COCIRS_0209/DATA/NAV_DATA/RIN02101300.DAT',       0,    'missing'),
    (r'.*/COCIRS_0602/DATA/UNCALIBR/FIFM06021412.DAT',      0,    'missing'),
    (r'.*/COISS_00.*/document/report/.*',                   0,    'missing'),
    (r'.*/COISS_0011/calib.*\.tab',                         0,    'missing'),
    (r'.*/COISS_0011/calib/calib.tar.gz',                   0,    'missing'),
    (r'.*/COISS_0011/extras/.*\.pro',                       0,    'missing'),
    (r'.*/COISS_0011/extras/cisscal.*',                     0,    'missing'),
    (r'.*/CO(ISS|VIMS)_.*/extras/.*\.(tiff|png|jpg|jpeg|jpeg_small)',
                                                            0,    'missing'),
    (r'.*/COSP_xxxx.*\.(pdf|zip|tm|orb)',                   0,    'missing'),
    (r'.*/COUVIS_.*/SOFTWARE/.*\.(PRO|pro|DAT|IDL|JAR|SAV)',0,    'missing'),
    (r'.*/COUVIS_.*/CALIB/.*\.DOC',                         0,    'missing'),
    (r'.*/COUVIS_0xxx.*/SOFTWARE/CALIB/VERSION_4/t.t',      0,    'missing'),
    (r'.*/COVIMS_0xxx.*/index/index.csv',                   0,    'missing'),
    (r'.*/COVIMS_0xxx.*/software/.*',                       0,    'missing'),
    (r'.*/COVIMS_0xxx.*/calib/example.*',                   0,    'missing'),
    (r'.*/COVIMS_0xxx.*/calib/.*\.(tab|qub|cub|bin|lbl)',   0,    'missing'),
    (r'.*/COVIMS_0xxx.*/browse/.*\.pdf',                    0,    'missing'),
    (r'.*/COVIMS_0xxx.*\.(lbl|qub)-old_V[0-9]+',            0,    'missing'),
    (r'.*/GO_0xxx_v1/GO_0001/CATALOG/REF.CAT.BAK',          0,    'missing'),
    (r'.*/GO_0xxx.*/GO_0001/SOFTWARE/GALSOS2.EXE',          0,    'missing'),
    (r'.*/GO_0xxx_v1/GO_0016/AAREADME.SL9',                 0,    'missing'),
    (r'.*/JNOJNC_0xxx.*/EXTRAS/.*\.PNG',                    0,    'missing'),
    (r'.*/NH.*/browse/.*\.jpg',                             0,    'missing'),
    (r'.*/NH.*/index/newline',                              0,    'missing'),
    (r'.*/NHxxMV.*/calib/.*\.png',                          0,    'missing'),
    (r'.*/NHSP_xxxx.*/DATASET.HTML',                        0,    'missing'),
    (r'.*/RPX.*/UNZIP532.*',                                0,    'missing'),
    (r'.*/RPX_xxxx/RPX_0201/CALIB/.*/(-180|128)',           0,    'missing'),
    (r'.*/VG.*/VG..NESR\.DAT',                              0,    'missing'),
    (r'.*/VG_0xxx.*/CUMINDEX.TAB',                          0,    'missing'),
    (r'.*/VG_0xxx.*/SOFTWARE/.*',                           0,    'missing'),
    (r'.*/VG._9xxx.*/SOFTWARE/.*',                          0,    'missing'),
    (r'.*/VG2_9065/BROWSE/C0SR01AA.LOG',                    0,    'missing'),

# These files have internal PDS3 labels, so these are not errors
    (r'.*/COISS_3xxx.*\.IMG',                               0,    'unneeded'),
    (r'.*/COUVIS_.*/SOFTWARE/.*\.txt_.*',                   0,    'unneeded'),
    (r'.*/VG_.*\.(IMQ|IRQ|IBG)',                            0,    'unneeded'),
    (r'.*/VG_0xxx.*/(AAREADME.VMS|VTOC.SYS|IMGINDEX.DBF)',  0,    'unneeded'),
])

# Match pattern for any file name, but possibly things that are not file names
PATTERN = r'\'?\"?([A-Z0-9][-\w]*\.[A-Z0-9][-\w\.]*)\'?\"?'

# Match pattern for the file name in anything of the form "keyword = filename"
TARGET_REGEX1 = re.compile(r'^ *\^?\w+ *= *\(?\{? *' + PATTERN, re.I)

# Match pattern for a file name on a line by itself
TARGET_REGEX2 = re.compile(r'^ *,? *' + PATTERN, re.I)

# Match pattern for one or more file names embedded in a row of a text file.
# A file name begins with a letter, followed by any number of letters, digits,
# underscore or dash. Unless the name is "Makefile", it must have one or more
# extensions, each containing one or more characters. It can also have any
# number of directory prefixes separate by slashes.

LINK_REGEX = re.compile(r'(?:|.*?[^/@\w\.])/?(?:\.\./)*(([A-Z0-9][-\w]+/)*' +
                        r'(makefile\.?|[A-Z0-9][\w-]*(\.[\w-]+)+))', re.I)

EXTS_WO_LABELS = set(['.LBL', '.CAT', '.TXT', '.FMT', '.SFD'])

################################################################################

class LinkInfo(object):
    """Used internally to describe a link within a specified record of a file.
    """

    def __init__(self, recno, linkname, is_target):

        self.recno = recno          # record number
        self.linktext = linkname    # substring within this record that looks
                                    # like a link.
        self.linkname = linkname    # link text after possible repair for known
                                    # errors.
        self.is_target = is_target  # True if, based on the local context, this
                                    # might be a target of a label file
        self.target = ''            # abspath to target of link, if any.
                                    # If not blank, this file must exist.

    def remove_path(self):
        """Remove any leading directory path from this LinkInfo object."""

        if '/' in self.linktext:
            self.linktext = self.linktext.rpartition('/')[2]
            self.linkname = self.linktext

    def __str__(self):
        return ('%d %s %s %s' % (self.recno, self.linktext, str(self.is_target),
                                 self.target or '[' + self.linkname + ']'))

def generate_links(dirpath, old_links={}, *, logger=None, limits={}):
    """Generate a dictionary keyed by the absolute file path for files in the
    given directory tree, which must correspond to a volume.

    Keys ending in .LBL, .CAT and .TXT return a list of tuples
        (recno, link, target)
    for each link found. Here,
        recno = record number in file;
        link = the text of the link;
        target = absolute path to the target of the link.

    Other keys return a single string, which indicates the absolute path to the
    label file describing this file.

    Unlabeled files not ending in .LBL, .CAT or .TXT return an empty string.

    Also return the latest modification date among all the files checked.
    """

    dirpath = os.path.abspath(dirpath)
    pdsdir = pdsfile.Pds3File.from_abspath(dirpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = GENERATE_LINKS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Finding link shelf files', dirpath, limits=merged_limits)

    try:

      linkinfo_dict = old_links.copy()      # abspath: list of LinkInfo objects
      label_dict = {k:v for k,v in old_links.items() if isinstance(v,str)}
                                            # abspath: label for this file
      abspaths = []                         # list of all abspaths

      latest_mtime = 0.

      # Walk the directory tree, one subdirectory "root" at a time...
      for (root, dirs, files) in os.walk(dirpath):

        local_basenames = []            # Tracks the basenames in this directory
        local_basenames_uc = []         # Same as above, but upper case
        for basename in files:
            abspath = os.path.join(root, basename)
            latest_mtime = max(latest_mtime, os.path.getmtime(abspath))

            if basename == '.DS_Store':         # skip .DS_Store files
                logger.ds_store('.DS_Store file skipped', abspath)
                continue

            if basename.startswith('._'):       # skip dot_underscore files
                logger.dot_underscore('dot_underscore file skipped',
                                      abspath)
                continue

            if BACKUP_FILENAME.match(basename) or ' copy' in basename:
                logger.error('Backup file skipped', abspath)
                continue

            if basename.startswith('.'):    # skip invisible files
                logger.invisible('Invisible file skipped', abspath)
                continue

            abspaths.append(abspath)
            local_basenames.append(basename)
            local_basenames_uc.append(basename.upper())

        # Update linkinfo_dict, searching each relevant file for possible links.
        # If the linking file is a label and the target file has a matching
        # name, update the label_dict entry for the target.
        candidate_labels = {}       # {target: list of possible label basenames}
        for basename in local_basenames:

            abspath = os.path.join(root, basename)
            if abspath in linkinfo_dict:    # for update op, skip existing links
                continue

            basename_uc = basename.upper()

            # Only check LBL, CAT, TXT, etc.
            ext = basename_uc[-4:] if len(basename) >= 4 else ''
            if ext not in EXTS_WO_LABELS:
                continue

            # Get list of link info for all possible linked filenames
            logger.debug('*** REVIEWING', abspath)
            linkinfo_list = read_links(abspath, logger=logger)

            # Apply repairs
            repairs = REPAIRS.all(abspath)
            for info in linkinfo_list:
                for repair in repairs:
                    linkname = repair.first(info.linktext)
                    if linkname is None:

                        # Attempt repair with leading directory path removed
                        if '/' in info.linktext:
                            info.remove_path()
                            linkname = repair.first(info.linktext)

                        if linkname is None:
                            continue            # no repair found

                    info.linkname = linkname
                    if linkname == '':
                        logger.info('Ignoring link "%s"' %
                                    info.linktext, abspath, force=True)
                    else:
                        logger.info('Repairing link "%s"->"%s"' %
                                    (info.linktext, linkname),
                                    abspath, force=True)

                    # Validate non-local targets of repairs
                    if '/' in linkname:
                      target = os.path.join(root, linkname)
                      if os.path.exists(target):
                        info.target = os.path.abspath(target)
                      else:
                        logger.error('Target of repaired link is missing',
                                     target)

                    break       # apply only one repair per found link

            # Validate or remove other targets
            new_linkinfo_list = []
            baseroot_uc = basename_uc.partition('.')[0]
            ltest = len(baseroot_uc)
            for info in linkinfo_list:
                if info.target:         # Non-local, repaired links have targets
                    new_linkinfo_list.append(info)
                    continue

                # A blank linkname is from a repair; indicates to ignore
                if info.linkname == '':
                    continue

                # Ignore self-references
                linkname_uc = info.linkname.upper()
                if linkname_uc == basename_uc:
                    continue

                # Check for target inside this directory
                try:
                    match_index = local_basenames_uc.index(linkname_uc)
                except ValueError:
                    match_index = None

                # If not found, maybe it is a non-local reference (.FMT perhaps)
                if match_index is None:

                    # It's easy to pick up floats as link candidates; ignore
                    try:
                        _ = float(info.linkname)
                        continue            # Yup, it's just a float
                    except ValueError:
                        pass

                    if info.linkname[-1] in ('e', 'E'):
                      try:
                        _ = float(info.linkname[:-1])
                        continue            # Float with exponent
                      except ValueError:
                        pass

                    # Also ignore format specifications (e.g., "F10.3")
                    if info.linkname[0] in ('F', 'E', 'G'):
                      try:
                        _ = float(info.linkname[1:])
                        continue            # Format
                      except ValueError:
                        pass

                    # Search non-locally
                    if '/' in info.linkname:
                        nonlocal_target = locate_link_with_path(abspath,
                                                                info.linkname)
                    else:
                        nonlocal_target = locate_nonlocal_link(abspath,
                                                               info.linkname)

                    # Report the outcome
                    if nonlocal_target:
                        logger.debug('Located "%s"' % info.linkname,
                                     nonlocal_target)
                        info.target = nonlocal_target
                        new_linkinfo_list.append(info)
                        continue

                    if linkname_uc.endswith('.FMT'):
                        logger.error('Unable to locate .FMT file "%s"' %
                                     info.linkname, abspath)
                    elif linkname_uc.endswith('.CAT'):
                        logger.error('Unable to locate .CAT file "%s"' %
                                     info.linkname, abspath)
                    else:
                        logger.debug('Substring "%s" is not a link, ignored' %
                                     info.linkname, abspath)

                    continue

                # Save the match
                info.linkname = local_basenames[match_index]    # update case
                info.target = os.path.join(root, info.linkname)
                new_linkinfo_list.append(info)

                # Could this be the label?
                if ext != '.LBL':       # nope
                    continue

                # If names match up to '.LBL', then yes
                if (len(linkname_uc) > ltest and
                    linkname_uc[:ltest] == baseroot_uc and
                    linkname_uc[ltest] == '.'):
                        label_dict[info.target] = abspath
                        logger.debug('Label identified for %s' % info.linkname,
                                     abspath)
                        continue

                # Otherwise, then maybe
                if info.is_target:
                    if info.linkname in candidate_labels:
                      if basename not in candidate_labels[info.linkname]:
                        candidate_labels[info.linkname].append(basename)
                    else:
                        candidate_labels[info.linkname] = [basename]

                    logger.debug('Candidate label found for ' +
                                 info.linkname, abspath)

            linkinfo_dict[abspath] = new_linkinfo_list

        # Identify labels for files
        for basename in local_basenames:

            basename_uc = basename.upper()
            ext = basename_uc[-4:] if len(basename) >= 4 else ''
            if ext in (".LBL", ".FMT"):     # these can't have labels
                continue

            abspath = os.path.join(root, basename)
            if abspath in label_dict:
                continue                    # label already found

            # Maybe we already know the label is missing
            test = KNOWN_MISSING_LABELS.first(abspath)
            if test == 'unneeded':
                logger.debug('Label is not neeeded', abspath)
                continue

            if test == 'missing':
                logger.debug('Label is known to be missing', abspath)
                continue

            # Determine if a label is required
            label_is_required = (ext not in EXTS_WO_LABELS)

            # Get the list of candidate labels in this directory
            candidates = candidate_labels.get(basename, [])

            # Determine if the obvious label file exists
            label_guess_uc = basename_uc.partition('.')[0] + '.LBL'
            if label_guess_uc in local_basenames_uc:
                k = local_basenames_uc.index(label_guess_uc)
                obvious_label_basename = local_basenames[k]
            else:
                obvious_label_basename = ''

            # Simplest case...
            if obvious_label_basename in candidates:
                if not label_is_required:
                    logger.debug('Unnecessary label found', abspath, force=True)

                label_dict[abspath] = os.path.join(root, obvious_label_basename)
                continue

            # More cases...
            if not label_is_required:
                continue                # leave abspath out of label_dict

            # Report a phantom label
            if obvious_label_basename:
                logger.error('Label %s does not point to file' %
                             local_basenames[k], abspath)

            if len(candidates) == 1:
                logger.debug('Label found as ' + candidates[0], abspath,
                             force=True)
                label_dict[abspath] = os.path.join(root, candidates[0])
                continue

            # or errors...
            label_dict[abspath] = ""
            if len(candidates) == 0:
                logger.error('Label is missing', abspath)
            else:
                logger.error('Ambiguous label found as %s' % candidates[0],
                             abspath, force=True)
                for candidate in candidates[1:]:
                    logger.debug('Alternative label found as %s' % candidate,
                                 abspath, force=True)

      # Merge the dictionaries
      # There are cases where a file can have both a list of links and a label.
      # This occurs when a .TXT or .CAT file has a label, even though it didn't
      # need one. In the returned dictionary, link lists take priority.
      link_dict = {}
      for key in abspaths:
        if key in linkinfo_dict:
            # If this is a new entry, it's a list of LinkInfo objects
            # If this was copied from old_links, it's already a list of tuples
            values = linkinfo_dict[key]
            if isinstance(values, list):
                new_list = []
                for item in values:
                  if isinstance(item, LinkInfo):
                    new_list.append((item.recno, item.linktext, item.target))
                  else:
                    new_list.append(item)
                link_dict[key] = new_list
            else:
                link_dict[key] = values
        elif key in label_dict:
            link_dict[key] = label_dict[key]
        else:
            link_dict[key] = ''

      dt = datetime.datetime.fromtimestamp(latest_mtime)
      logger.info('Lastest holdings file modification date',
                  dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

      return (link_dict, latest_mtime)

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

def read_links(abspath, logger=None):
    """Return a list of LinkInfo objects for anything linked or labeled by this
    file.
    """

    with open(abspath, 'r', encoding='latin-1') as f:
        recs = f.readlines()

    links = []
    multiple_targets = False
    for recno,rec in enumerate(recs):

        while True:

            # Search for the target of a link
            is_target = True
            matchobj = TARGET_REGEX1.match(rec)
            if matchobj:
                subrec = rec[:matchobj.end()]
                if '(' in subrec or '{' in subrec:
                    multiple_targets = True

            # ... on the same line or the next line
            elif multiple_targets:
                matchobj = TARGET_REGEX2.match(rec)

            # If not found, search for any other referenced file name or path
            if not matchobj:
                if ')' in rec or '}' in rec:
                    multiple_targets = False

                is_target = False
                matchobj = LINK_REGEX.match(rec)
                if matchobj:
                    multiple_targets = False

            # No more matches in this record
            if not matchobj:
                break

            linktext = matchobj.group(1)
            links.append(LinkInfo(recno, linktext, is_target))

            rec = rec[matchobj.end():]

    return links

def locate_nonlocal_link(abspath, filename):
    """Return the absolute path associated with a link in a PDS file. This is
    done by searching up the tree and also by looking inside the LABEL,
    CATALOG and INCLUDE directories if they exist."""

    filename_uc = filename.upper()

    parts = abspath.split('/')[:-1]

    # parts are [..., 'holdings', 'volumes', volset, volname, ...]
    # Therefore, if 'holdings' is in parts[:-3], then there's a volname in this
    # path.
    while 'holdings' in parts[:-3]:
        testpath = '/'.join(parts)
        basenames = os.listdir(testpath)
        basenames_uc = [b.upper() for b in basenames]
        try:
            k = basenames_uc.index(filename_uc)
            return testpath + '/' + basenames[k]
        except ValueError:
            pass

        for dirname in ['LABEL', 'CATALOG', 'INCLUDE', 'INDEX', 'DOCUMENT',
                        'DATA', 'CALIB', 'EXTRAS', 'SOFTWARE']:
            try:
                k = basenames_uc.index(dirname)
                subnames = os.listdir(testpath + '/' + basenames[k])
                subupper = [s.upper() for s in subnames]
                try:
                    kk = subupper.index(filename_uc)
                    return testpath + '/' + basenames[k] + '/' + subnames[kk]
                except ValueError:
                    pass
            except ValueError:
                pass

        parts = parts[:-1]

    return ''

def locate_link_with_path(abspath, filename):
    """Return the absolute path associated with a link that contains a leading
    directory path.
    """

    parts = filename.split('/')
    link_path = locate_nonlocal_link(abspath, parts[0])
    if not link_path:
        return ''

    for part in parts[1:]:
        basenames = os.listdir(link_path)
        if part in basenames:
            link_path += '/' + part
        else:
            basenames_uc = [b.upper() for b in basenames]
            part_uc = part.upper()
            if part_uc in basenames_uc:
                k = basenames_uc.index(part_uc)
                link_path += '/' + basenames[k]
            else:
                return ''

    return link_path

################################################################################

def load_links(dirpath, *, logger=None, limits={}):
    """Load link dictionary from a shelf file, converting interior paths to
    absolute paths."""

    dirpath = os.path.abspath(dirpath)
    pdsdir = pdsfile.Pds3File.from_abspath(dirpath)

    dirpath_ = dirpath.rstrip('/') + '/'

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = LOAD_LINKS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Reading link shelf file for', dirpath, limits=merged_limits)

    try:
        (link_path, lskip) = pdsdir.shelf_path_and_lskip('link')
        prefix_ = pdsdir.volume_abspath() + '/'

        logger.info('Link shelf file', link_path)

        if not os.path.exists(link_path):
            raise IOError('File not found: ' + link_path)

        # Read the shelf file and convert to a dictionary
        with open(link_path, 'rb') as f:
            interior_dict = pickle.load(f)

        # Convert interior paths to absolute paths
        link_dict = {}
        for (key, values) in interior_dict.items():
            long_key = dirpath_ + key

            if isinstance(values, list):
                new_list = []
                for (recno, basename, interior_path) in values:
                    abspath = dirpath_ + str(interior_path)
                    if '../' in abspath:
                        abspath = os.path.abspath(abspath)

                    new_list.append((recno, str(basename), abspath))

                link_dict[long_key] = new_list
            else:
                values = str(values)
                if values == '':
                    link_dict[long_key] = ''
                else:
                    link_dict[long_key] = dirpath_ + values

        return link_dict

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################

def write_linkdict(dirpath, link_dict, *, logger=None, limits={}):
    """Write a new link shelf file for a directory tree."""

    # Initialize
    dirpath = os.path.abspath(dirpath)
    pdsdir = pdsfile.Pds3File.from_abspath(dirpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = WRITE_LINKDICT_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Writing link shelf file for', dirpath, limits=merged_limits)

    try:
        (link_path, lskip) = pdsdir.shelf_path_and_lskip('link')
        logger.info('Link shelf file', link_path)

        # Create a dictionary using interior paths instead of absolute paths
        interior_dict = {}
        prefix = (dirpath + '/')[:lskip]
        for (key, values) in link_dict.items():
            if isinstance(values, list):
                new_list = []
                for (basename, recno, link_abspath) in values:
                    if link_abspath[:lskip] == prefix:
                        new_list.append((basename, recno, link_abspath[lskip:]))
                    else:      # link outside this volume
                        link = pdsfile.Pds3File.from_abspath(link_abspath)
                        if (link.category_ == pdsdir.category_ and
                            link.bundleset == pdsdir.bundleset and
                            link.suffix == pdsdir.suffix):
                            link_relpath = '../' + link.bundlename_ + link.interior
                        elif link.category_ == pdsdir.category_:
                            link_relpath = ('../../' + link.bundleset_ +
                                            link.bundlename_ + link.interior)
                        else:
                            link_relpath = ('../../../' + link.category_ +
                                            link.bundleset_ +
                                            link.bundlename_ + link.interior)
                        new_list.append((basename, recno, link_relpath))

                interior_dict[key[lskip:]] = new_list
            else:
                interior_dict[key[lskip:]] = values[lskip:]

        # Create parent directory if necessary
        parent = os.path.split(link_path)[0]
        if not os.path.exists(parent):
            logger.info('Creating directory', parent)
            os.makedirs(parent)

        # Write the shelf
        with open(link_path, 'wb') as f:
            pickle.dump(interior_dict, f)

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

    logger.open('Writing Python dictionary', dirpath)
    try:
        # Determine the maximum length of the file path and basename
        len_key = 0
        len_base = 0
        for (key, value) in interior_dict.items():
            len_key = max(len_key, len(key))
            if isinstance(value, list):
                tuples = value
                for (recno, basename, interior_path) in tuples:
                    len_base = max(len_base, len(basename))

        len_key = min(len_key, 60)

        # Write the python dictionary version
        python_path = link_path.rpartition('.')[0] + '.py'
        name = os.path.basename(python_path)
        parts = name.split('_')
        name = '_'.join(parts[:2]) + '_links'
        keys = list(interior_dict.keys())
        keys.sort()

        with open(python_path, 'w', encoding='latin-1') as f:
            f.write(name + ' = {\n')
            for valtype in (list, str):
              for key in keys:
                if not isinstance(interior_dict[key], valtype): continue

                f.write('  "%s"' % key)
                if len(key) < len_key:
                    f.write((len_key - len(key)) * ' ')
                f.write(': ')
                tuple_indent = max(len(key),len_key) + 7

                values = interior_dict[key]
                if isinstance(values, str):
                    f.write('"%s",\n' % values)
                elif len(values) == 0:
                    f.write('[],\n')
                else:
                    f.write('[')
                    for k in range(len(values)):
                        (recno, basename, interior_path) = values[k]
                        f.write('(%4d, ' % recno)
                        f.write('"%s, ' % (basename + '"' +
                                           (len_base-len(basename)) * ' '))
                        f.write('"%s")' % interior_path)

                        if k < len(values) - 1:
                            f.write(',\n' + tuple_indent * ' ')
                        else:
                            f.write('],\n')

            f.write('}\n\n')

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################

def validate_links(dirpath, dirdict, shelfdict, *, logger=None, limits={}):

    dirpath = os.path.abspath(dirpath)
    pdsdir = pdsfile.Pds3File.from_abspath(dirpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = VALIDATE_LINKS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Validating link shelf file for', dirpath, limits=merged_limits)

    try:
        keys = list(dirdict.keys())
        for key in keys:
            if key in shelfdict:
                dirinfo = dirdict[key]
                shelfinfo = shelfdict[key]

                if type(dirinfo) == list:
                    dirinfo.sort()

                if type(shelfinfo) == list:
                    shelfinfo.sort()

                if dirinfo != shelfinfo:
                    logger.error('Link target mismatch', key)

                del shelfdict[key]
                del dirdict[key]

        keys = list(dirdict.keys())
        keys.sort()
        for key in keys:
            logger.error('Missing link shelf file entry for', key)

        keys = list(shelfdict.keys())
        keys.sort()
        for key in keys:
            logger.error('Link shelf file entry found for missing file', key)

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        return logger.close()

################################################################################

def move_old_links(shelf_file, logger=None):
    """Move a file to the /logs/ directory tree and append a time tag."""

    if not os.path.exists(shelf_file): return

    shelf_basename = os.path.basename(shelf_file)
    (shelf_prefix, shelf_ext) = os.path.splitext(shelf_basename)

    if logger is None:
        logger = pdslogger.PdsLogger.get_logger(LOGNAME)

    from_logged = False
    for log_dir in LOGDIRS:
        dest_template = log_dir + '/' + shelf_prefix + '_v???' + shelf_ext
        version_paths = glob.glob(dest_template)

        max_version = 0
        lskip = len(shelf_ext)
        for version_path in version_paths:
            version = int(version_path[-lskip-3:-lskip])
            max_version = max(max_version, version)

        new_version = max_version + 1
        dest = dest_template.replace('???', '%03d' % new_version)
        shutil.copy(shelf_file, dest)

        if not from_logged:
            logger.info('Link shelf file moved from: ' + shelf_file)
            from_logged = True

        logger.info('Link shelf file moved to ' + dest)

        python_src = shelf_file.rpartition('.')[0] + '.py'
        python_dest = dest.rpartition('.')[0] + '.py'
        shutil.copy(python_src, python_dest)

        pickle_src = shelf_file.rpartition('.')[0] + '.pickle'
        pickle_dest = dest.rpartition('.')[0] + '.pickle'
        shutil.copy(pickle_src, pickle_dest)

################################################################################
# Simplified functions to perform tasks
################################################################################

def initialize(pdsdir, *, logger=None, limits={}):

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure file does not exist
    if os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.error('Link shelf file already exists', link_path)
        return

    # Generate link info
    (link_dict, _) = generate_links(pdsdir.abspath, logger=logger,
                                    limits=limits)

    # Move old file if necessary
    if os.path.exists(link_path):
        move_old_links(link_path, logger=logger)

    # Save link files
    write_linkdict(pdsdir.abspath, link_dict, logger=logger, limits=limits)

def reinitialize(pdsdir, *, logger=None, limits={}):

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Warn if shelf file does not exist
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.warning('Link shelf file does not exist; initializing',
                       link_path)
        initialize(pdsdir, logger=logger, limits=limits)
        return

    # Generate link info
    (link_dict, _) = generate_links(pdsdir.abspath, logger=logger,
                                    limits=limits)

    # Move old file if necessary
    if os.path.exists(link_path):
        move_old_links(link_path, logger=logger)

    # Save link files
    write_linkdict(pdsdir.abspath, link_dict, logger=logger, limits=limits)

def validate(pdsdir, *, logger=None, limits={}):

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure file exists
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.error('Link shelf file does not exist', link_path)
        return

    # Read link shelf file
    shelf_linkdict = load_links(pdsdir.abspath, logger=logger, limits=limits)

    # Generate link dict
    (dir_linkdict, _) = generate_links(pdsdir.abspath, logger=logger,
                                       limits=limits)

    # Validate
    validate_links(pdsdir.abspath, dir_linkdict, shelf_linkdict, logger=logger,
                   limits=limits)

def repair(pdsdir, *, logger=None, limits={}):

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure file exists
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.warning('Link shelf file does not exist; initializing',
                       link_path)
        initialize(pdsdir, logger=logger, limits=limits)
        return

    # Read link shelf file
    shelf_linkdict = load_links(pdsdir.abspath, logger=logger, limits=limits)

    # Generate link dict
    (dir_linkdict, latest_mtime) = generate_links(pdsdir.abspath, logger=logger,
                                                  limits=limits)

    # Compare
    canceled = (dir_linkdict == shelf_linkdict)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)

        link_pypath = link_path.replace('.pickle', '.py')
        link_mtime = min(os.path.getmtime(link_path),
                         os.path.getmtime(link_pypath))
        if latest_mtime > link_mtime:
            logger.info('!!! Link shelf file content is up to date',
                        link_path, force=True)

            dt = datetime.datetime.fromtimestamp(latest_mtime)
            logger.info('!!! Latest holdings file modification date',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

            dt = datetime.datetime.fromtimestamp(link_mtime)
            logger.info('!!! Link shelf file modification date',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

            delta = latest_mtime - link_mtime
            if delta >= 86400/10:
                logger.info('!!! Link shelf file is out of date %.1f days' %
                            (delta / 86400.), force=True)
            else:
                logger.info('!!! Link shelf file is out of date %.1f minutes' %
                            (delta / 60.), force=True)

            dt = datetime.datetime.now()
            os.utime(link_path)
            os.utime(link_pypath)
            logger.info('!!! Time tag on link shelf files set to',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)
        else:
            logger.info(f'!!! Link shelf file is up to date; repair canceled',
                        link_path, force=True)
        return

    # Move files and write new links
    move_old_links(link_path, logger=logger)
    write_linkdict(pdsdir.abspath, dir_linkdict, logger=logger, limits=limits)

def update(pdsdir, *, logger=None, limits={}):

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure link shelf file exists
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.warning('Link shelf file does not exist; initializing',
                       link_path)
        initialize(pdsdir, logger=logger)
        return

    # Read link shelf file
    shelf_linkdict = load_links(pdsdir.abspath, logger=logger, limits=limits)

    # Generate link dict
    (dir_linkdict,
     latest_mtime) = generate_links(pdsdir.abspath, shelf_linkdict,
                                    logger=logger, limits=limits)

    # Compare
    canceled = (dir_linkdict == shelf_linkdict)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.info('!!! Link shelf file content is complete; update canceled',
                    link_path, force=True)
        return

    # Move files and write new links
    move_old_links(link_path, logger=logger)
    write_linkdict(pdsdir.abspath, dir_linkdict, logger=logger, limits=limits)

################################################################################

def main():

    # Set up parser
    parser = argparse.ArgumentParser(
        description='pdslinkshelf: Create, maintain and validate shelves of '  +
                    'links between files.')

    parser.add_argument('--initialize', '--init', const='initialize',
                        default='', action='store_const', dest='task',
                        help='Create a link shelf file for a volume. Abort '   +
                             'if the checksum file already exists.')

    parser.add_argument('--reinitialize', '--reinit', const='reinitialize',
                        default='', action='store_const', dest='task',
                        help='Create a link shelf file for a volume. Replace ' +
                             'the file if it already exists.')

    parser.add_argument('--validate', const='validate',
                        default='', action='store_const', dest='task',
                        help='Validate every link in a volume directory tree ' +
                             'against its link shelf file.')

    parser.add_argument('--repair', const='repair',
                        default='', action='store_const', dest='task',
                        help='Validate every link in a volume directory tree ' +
                             'against its link shelf file. If any '            +
                             'disagreement  is found, replace the shelf '      +
                             'file; otherwise leave it unchanged. If any of '  +
                             'the files checked are newer than the link shelf '+
                             'file, update shelf file\'s modification date')

    parser.add_argument('--update', const='update',
                        default='', action='store_const', dest='task',
                        help='Search a directory for any new files and add '   +
                             'their links to the link shelf file. Links of '   +
                             'pre-existing files are not checked.')

    parser.add_argument('volume', nargs='+', type=str,
                        help='The path to the root directory of a volume.')

    parser.add_argument('--log', '-l', type=str, default='',
                        help='Optional root directory for a duplicate of the ' +
                             'log files. If not specified, the value of '      +
                             'environment variable "%s" ' % LOGROOT_ENV        +
                             'is used. In addition, individual logs are '      +
                             'written into the "logs" directory parallel to '  +
                             '"holdings". Logs are created inside the '        +
                             '"pdslinkshelf" subdirectory of each log root '   +
                             'directory.'
                             )

    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Do not also log to the terminal.')

    # Parse and validate the command line
    args = parser.parse_args()

    if not args.task:
        print('pdslinkshelf error: Missing task')
        sys.exit(1)

    status = 0

    # Define the logging directory
    if args.log == '':
        try:
            args.log = os.environ[LOGROOT_ENV]
        except KeyError:
            args.log = None

    # Initialize the logger
    logger = pdslogger.PdsLogger(LOGNAME)
    pdsfile.Pds3File.set_log_root(args.log)

    if not args.quiet:
        logger.add_handler(pdslogger.stdout_handler)

    if args.log:
        path = os.path.join(args.log, 'pdslinkshelf')
        error_handler = pdslogger.error_handler(path)
        logger.add_handler(error_handler)

    # Generate a list of file paths before logging
    paths = []
    for path in args.volume:

        if not os.path.exists(path):
            print('No such file or directory: ' + path)
            sys.exit(1)

        path = os.path.abspath(path)
        pdsf = pdsfile.Pds3File.from_abspath(path)

        if pdsf.checksums_:
            print('No link shelf files for checksum files: ' + path)
            sys.exit(1)

        if pdsf.archives_:
            print('No link shelf files for archive files: ' + path)
            sys.exit(1)

        if pdsf.is_volset_dir:
            paths += [os.path.join(path, c) for c in pdsf.childnames]

        else:
            paths.append(os.path.abspath(path))

    # Loop through tuples...
    logger.open(' '.join(sys.argv))
    try:
        for path in paths:

            pdsdir = pdsfile.Pds3File.from_abspath(path)
            if not pdsdir.isdir:    # skip volset-level readme files
                continue

            # Save logs in up to two places
            logfiles = set([pdsdir.log_path_for_volume('_links',
                                                       task=args.task,
                                                       dir='pdslinkshelf'),
                            pdsdir.log_path_for_volume('_links',
                                                       task=args.task,
                                                       dir='pdslinkshelf',
                                                       place='parallel')])

            # Create all the handlers for this level in the logger
            local_handlers = []
            LOGDIRS = []            # used by move_old_links()
            for logfile in logfiles:
                local_handlers.append(pdslogger.file_handler(logfile))
                logdir = os.path.split(logfile)[0]
                LOGDIRS.append(os.path.split(logfile)[0])

                # These handlers are only used if they don't already exist
                error_handler = pdslogger.error_handler(logdir)
                local_handlers += [error_handler]

            # Open the next level of the log
            if len(paths) > 1:
                logger.blankline()

            logger.open('Task "' + args.task + '" for', path,
                        handler=local_handlers)

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                if args.task == 'initialize':
                    initialize(pdsdir)

                elif args.task == 'reinitialize':
                    reinitialize(pdsdir)

                elif args.task == 'validate':
                    validate(pdsdir)

                elif args.task == 'repair':
                    repair(pdsdir)

                else:       # update
                    update(pdsdir)

            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                raise

            finally:
                _ = logger.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        status = 1
        raise

    finally:
        (fatal, errors, warnings, tests) = logger.close()
        if fatal or errors: status = 1

    sys.exit(status)

if __name__ == '__main__':
    main()
