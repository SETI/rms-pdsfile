##########################################################################################
# pds3file/rules/JNOJIR_xxxx.py
##########################################################################################

"""Rules for the JNOJIR_xxxx volume set: Juno JIRAM raw data.

JNOJIR_xxxx is described in the holdings as the Juno JIRAM raw image collection.
Each orbit has two volumes, a 1nnn holding the raw data and a 2nnn holding the
reduced, which is why this module's patterns are written for JNOJIR_1 and JNOJIR_2
alike. The series opens with JNOJIR_1000 for the 2013 Moon images and JNOJIR_1001
for orbit insertion. Four data set IDs are in play: JNO-J-JIRAM-2-EDR-V1.0 and
JNO-J-JIRAM-3-RDR-V1.0 for the Jupiter volumes, and JNO-L-JIRAM-2-EDR-V3.0 and
JNO-L-JIRAM-3-RDR-V3.0 for the Moon pair (``_volinfo/JNOJIR_xxxx.txt``). An
observation is a raw or calibrated image or spectrum, and each data file has a log
table of engineering data beside it.

The rule tables:

* ``description_and_icon_by_regex`` -- distinguishes the raw and calibrated images
  from the raw and calibrated spectra, names the engineering data, and names the
  date-ordered data directories.
* ``associations_to_volumes`` and ``associations_to_metadata`` -- cross the volumes
  and metadata trees for one observation. The volumes entry is what pairs a raw file
  with its reduced counterpart, rewriting the volume's leading 1 to a 2 and EDR to
  RDR.
* ``associations_to_documents`` -- the documents tree for one observation. The class
  body installs it as a replacement for the default rather than adding to it, so the
  table re-implements the default behavior itself.
* ``neighbors`` -- the corresponding directories in sibling volumes.
* ``siblings`` -- the basenames treated as adjacent within one directory. This is
  the only rule module that overrides the sibling rule, rather than letting it be
  derived from the split rule.
* ``sort_key`` -- moves the timestamp to the front of a basename so that data files
  order by time; puts a log table after the data file it describes and each label
  after its own data file; sends the long run of JIRAM report PDFs to the end of the
  documents directory; and sorts volumes that share their last three digits
  together.
* ``split_rules`` -- groups a log file with the data file it describes, and groups
  volumes that share their last three digits. It has to work both on a raw basename
  and on the basename ``sort_key`` produces from it, so it carries a "before" and an
  "after" form of each pattern.

This module defines no viewables and no OPUS tables, so previews and OPUS behavior
come from the defaults in `pds3file/rules/__init__.py`.
"""

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/DATA',                     0, ('Data files ordered by date', 'IMAGEDIR')),
    (r'volumes/.*/DATA/JIR_IMG_EDR_.*\.IMG', 0, ('Raw image',                  'IMAGE'   )),
    (r'volumes/.*/DATA/JIR_IMG_RDR_.*\.IMG', 0, ('Calibrated image',           'IMAGE'   )),
    (r'volumes/.*/DATA/JIR_SPE_EDR_.*\.DAT', 0, ('Raw spectrum',               'DATA'    )),
    (r'volumes/.*/DATA/JIR_SPE_RDR_.*\.DAT', 0, ('Calibrated spectrum',        'DATA'    )),
    (r'volumes/.*/DATA/JIR_LOG_.*\.TAB',     0, ('Engineering data',           'DATA'    )),

    (r'volumes/.*/DOCUMENT/JIRAM_SIS_V(.*)\.pdf',                0, (r'Archive description version \1',     'PDFDOC')),
    (r'volumes/.*/DOCUMENT/JIRAM_REPORT_JM000(\d)_V.*\.pdf',     0, (r'JIRAM activity report for orbit \1', 'PDFDOC')),
    (r'volumes/.*/DOCUMENT/JIRAM_REPORT_JM00(\d)[12]_V.*\.pdf',  0, (r'JIRAM activity report for orbit \1', 'PDFDOC')),
    (r'volumes/.*/DOCUMENT/JIRAM_REPORT_JM0(\d\d)[12]_V.*\.pdf', 0, (r'JIRAM activity report for orbit \1', 'PDFDOC')),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    # associate raw and calibrated files of the (almost) same name
    (r'volumes/JNOJIR_xxxx/JNOJIR_[12](\d\d\d/DATA/JIR_\w+)_[ER]DR_(.*)\.(IMG|DAT|TAB)', 0,
            [r'volumes/JNOJIR_xxxx/JNOJIR_1\1_RDR_\2.\3',
             r'volumes/JNOJIR_xxxx/JNOJIR_2\1_EDR_\2.\3'
            ]),
    # associate data files with logs and vice-versa
    (r'volumes/(JNOJIR_xxxx/JNOJIR_[12]\d\d\d/DATA/JIR)_(IMG|SPE)_([ER]DR_.*)\.(IMG|DAT)', 0,
            r'volumes/\1_LOG_\2_\3.TAB'
            ),
    # associate logs with data files
    (r'volumes/(JNOJIR_xxxx/JNOJIR_[12]\d\d\d/DATA/JIR)_LOG_(\w\w\w_[ER]DR_.*)\.TAB', 0,
            [r'volumes/\1_\2.IMG',
             r'volumes/\1_\2.DAT',
            ]),
    # associate orbit report with data volume
    (r'documents/JNOJIR_xxxx/JIRAM-Report-for-JM000([12])-.*',      0, r'volumes/JNOJIR_xxxx/JNOJIR_000\d'),
    (r'documents/JNOJIR_xxxx/JIRAM-Report-for-JM00([3-9])[12]-.*',  0, r'volumes/JNOJIR_xxxx/JNOJIR_000\d'),
    (r'documents/JNOJIR_xxxx/JIRAM-Report-for-JM0([1-9]\d)[12]-.*', 0, r'volumes/JNOJIR_xxxx/JNOJIR_00\d'),

    # associate documents with both root directories
    (r'documents.*', 0, r'volumes/JNOJIR_xxxx'),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/JNOJIR_xxxx/(JNOJIR_[12]\d\d\d)/DATA/(\w+)\.(IMG|DAT|TAB)', 0,
            r'metadata/JNOJIR_xxxx/\1/\1_index.tab/\2.\3',
            ),
])

associations_to_documents = translator.TranslatorByRegex([
    # Note: this is a full replacement of the default rule

    (r'volumes/JNOJIR_xxxx', 0, r'documents/JNOJIR_xxxx/*'),

    # For a volname, only match the one relevant JIRAM report for that orbit, but match all the other documents
    (r'volumes/JNOJIR_xxxx/JNOJIR_[12]00([12])',          0, r'documents/JNOJIR_xxxx/JIRAM-Report-for-JM000\1-*.pdf'),
    (r'volumes/JNOJIR_xxxx/JNOJIR_[12]0(0[3-9]|[1-9]\d)', 0, r'documents/JNOJIR_xxxx/JIRAM-Report-for-JM0\1*.pdf'),
    (r'volumes/JNOJIR_xxxx/JNOJIR_[12]\d\d\d',            0,
        [r'documents/JNOJIR_xxxx/[a-zA-IK-Z0-9_-]*',        # match anything but a JIRAM report; note "[^J]" doesn't work in glob
         r'documents/JNOJIR_xxxx/J[a-zA-HJ-Z0-9_-]*',
         r'documents/JNOJIR_xxxx/JI[a-zA-QS-Z0-9_-]*',
         r'documents/JNOJIR_xxxx/JIR[a-zB-Z0-9_-]*',
         r'documents/JNOJIR_xxxx/JIRA[a-zA-LN-Z0-0_-]*',
         r'documents/JNOJIR_xxxx/JIRAM[a-zA-Z0-9_]*',
         r'documents/JNOJIR_xxxx/JIRAM-[a-zA-QS-Z0-9_-]*',
         r'documents/JNOJIR_xxxx/JIRAM-R[a-df-zA-Z0-9_-]*', # enough already!
        ]),

    # Below the volume level, only match the directory
    (r'volumes/JNOJIR_xxxx/JNOJIR_[12]\d\d\d/.+', 0,
            r'documents/JNOJIR_xxxx'),

    # This fills in default behavior of the general association rule
    (r'volumes/(JNOJIR_xxxx/JNOJIR_[12]\d\d\d)(|/.*)', 0,
            [r'volumes/\1/DOCUMENT',
             r'volumes/\1/CATALOG',
             r'volumes/\1/AAREADME.TXT',
             r'volumes/\1/ERRATA.TXT',
             r'volumes/\1/VOLDESC.CAT',
            ]),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'volumes/(JNOJIR_xxxx/JNOJIR_[12])\d\d\d',      0, r'volumes/\1???'),
    (r'volumes/(JNOJIR_xxxx/JNOJIR_[12])\d\d\d/DATA', 0, r'volumes/\1???/DATA'),
])

##########################################################################################
# SIBLINGS
##########################################################################################

siblings = translator.TranslatorByRegex([
    # Data files are siblings of data files; log files are siblings of log files
    (r'volumes/JNOJIR_xxxx/JNOJIR_[12]\d\d\d/DATA/JIR_(IMG|SPE)_[ER]DR_20\d{5}T\d{6}_V\d\d\.LBL',       0, r'JIR_[IS]*.LBL'),
    (r'volumes/JNOJIR_xxxx/JNOJIR_[12]\d\d\d/DATA/JIR_(IMG|SPE)_[ER]DR_20\d{5}T\d{6}_V\d\d\.(IMG|DAT)', 0, r'JIR_[IS]*.[ID]*'),
    (r'volumes/JNOJIR_xxxx/JNOJIR_[12]\d\d\d/DATA/JIR_LOG_(IMG|SPE)_[ER]DR_20\d{5}T\d{6}_V\d\d\.LBL',   0, r'JIR_LOG_*.LBL'),
    (r'volumes/JNOJIR_xxxx/JNOJIR_[12]\d\d\d/DATA/JIR_LOG_(IMG|SPE)_[ER]DR_20\d{5}T\d{6}_V\d\d\.TAB',   0, r'JIR_LOG_*.TAB'),

    # Volume siblings should match 1xxx or 2xxx
    (r'.*/JNOJIR_xxxx/JNOJIR_([12])\d\d\d([^/]*)', 0, r'JNOJIR_\1???\2'),
])

##########################################################################################
# SORT_KEY
##########################################################################################

sort_key = translator.TranslatorByRegex([
    # Order data files by time, data before log, each before its own label
    (r'JIR_(IMG|SPE)_([ER]DR)_(20\d{5}T\d{6})_(V\d\d)\.(DAT|IMG)', 0, r'JIR_\3_\1_\2_\4.\5'),
    (r'JIR_(IMG|SPE)_([ER]DR)_(20\d{5}T\d{6})_(V\d\d)\.(LBL)'    , 0, r'JIR_\3_\1_\2_\4.zzz_\5'),
    (r'JIR_LOG_(IMG|SPE)_([ER]DR)_(20\d{5}T\d{6})_(V\d\d)\.(TAB)', 0, r'JIR_\3_\1_\2_\4_zzz_LOG.\5'),
    (r'JIR_LOG_(IMG|SPE)_([ER]DR)_(20\d{5}T\d{6})_(V\d\d)\.(LBL)', 0, r'JIR_\3_\1_\2_\4_zzz_LOG.zzz_\5'),

    # Locate the long list of JIRAM reports at the end of the documents directory
    (r'(JIRAM-Report-for-JM.*\.pdf)', 0, r'zzz-\1'),

    # Sort volumes with the same last three digits together
    (r'JNOJIR_([12])(\d\d\d)', 0, r'JNOJIR_\2\1'),
])

##########################################################################################
# SPLIT_RULES
##########################################################################################

split_rules = translator.TranslatorByRegex([
    # Group LOG files with their associated data files.
    # Note that this rule has to work for file names both before and after the sort_key has been applied.
    #   before:     JIR[_LOG]_<IMG|SPE>_<RDR|EDR>_<date>_Vnn.<ext>
    #   after:      JIR_<date>_<IMG|SPE>_<RDR|EDR>_Vnn_[_zzz_LOG].[zzz_]<ext>

    # before...
    (r'JIR_(\w\w\w_\wDR_20\d{5}T\d{6}_V\d\d)\.(\w+)',     0, (r'JIR_\1', '',     r'.\2')),
    (r'JIR_LOG_(\w\w\w_\wDR_20\d{5}T\d{6}_V\d\d)\.(\w+)', 0, (r'JIR_\1', '_LOG', r'.\2')),

    # after...
    (r'JIR_(20\d{5}T\d{6}_\w\w\w_\wDR_V\d\d)\.(\w+)',         0, (r'JIR_\1', '',         r'.\2')),
    (r'JIR_(20\d{5}T\d{6}_\w\w\w_\wDR_V\d\d)_zzz_LOG\.(\w+)', 0, (r'JIR_\1', '_zzz_LOG', r'.\2')),

    # Group volumes with the same last three digits
    (r'JNOJIR_([12])(\d\d\d)(|_[a-z]+)(|_md5\.txt|\.tar\.gz)', 0, (r'JNOJIR_x\2', r'_\1xxx\3', r'\4')),
])

##########################################################################################
# Subclass definition
##########################################################################################

class JNOJIR_xxxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for JNOJIR_xxxx.

    The class body wires this module's rule tables onto the class attributes
    ``Pds3File`` reads. Where a table is added to the inherited one, a lookup tries
    this module's patterns first and falls through to the defaults; where it is
    assigned outright there is no fall-through. The module tail registers the class
    in ``Pds3File.SUBCLASSES`` under the key
    "JNOJIR_xxxx". The module docstring describes the volume set and every table.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('JNOJIR_xxxx', re.I, 'JNOJIR_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS
    SIBLINGS = siblings + pds3file.Pds3File.SIBLINGS
    SORT_KEY = sort_key + pds3file.Pds3File.SORT_KEY
    SPLIT_RULES = split_rules + pds3file.Pds3File.SPLIT_RULES

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']   += associations_to_volumes
    ASSOCIATIONS['metadata']  += associations_to_metadata
    ASSOCIATIONS['documents'] = associations_to_documents   # this is a replacement, not an override

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['JNOJIR_xxxx'] = JNOJIR_xxxx

##########################################################################################
