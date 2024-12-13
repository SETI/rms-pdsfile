##########################################################################################
# pdsfile/pds3file/__init__.py
# pds3file subpackage & Pds3File subclass with PdsFile as the parent class
##########################################################################################

import re

import pdslogger

from pdsfile import pdscache
from pdsfile.pdsfile import PdsFile
from . import rules
from pdsfile.preload_and_cache import cache_lifetime_for_class

class Pds3File(PdsFile):

    PDS_HOLDINGS = 'holdings'
    BUNDLE_DIR_NAME = 'volumes'

    # REGEX
    BUNDLESET_REGEX        = re.compile(r'^([A-Z][A-Z0-9x]{1,5}_[0-9x]{3}x)$')
    BUNDLESET_REGEX_I      = re.compile(BUNDLESET_REGEX.pattern, re.I)
    BUNDLESET_PLUS_REGEX   = re.compile(BUNDLESET_REGEX.pattern[:-1] +
                                        r'(_v[0-9]+\.[0-9]+\.[0-9]+|'+
                                        r'_v[0-9]+\.[0-9]+|_v[0-9]+|'+
                                        r'_in_prep|_prelim|_peer_review|'+
                                        r'_lien_resolution|)' +
                                        r'((|_calibrated|_diagrams|_metadata|_previews)' +
                                        r'(|_md5\.txt|\.tar\.gz))$')
    BUNDLESET_PLUS_REGEX_I = re.compile(BUNDLESET_PLUS_REGEX.pattern, re.I)

    BUNDLENAME_REGEX       = re.compile(r'^([A-Z][A-Z0-9]{1,5}_(?:[0-9]{4}))$')
    BUNDLENAME_REGEX_I     = re.compile(BUNDLENAME_REGEX.pattern, re.I)
    BUNDLENAME_PLUS_REGEX  = re.compile(BUNDLENAME_REGEX.pattern[:-1] +
                                        r'(|_[a-z]+)(|_md5\.txt|\.tar\.gz)$')
    BUNDLENAME_PLUS_REGEX_I = re.compile(BUNDLENAME_PLUS_REGEX.pattern, re.I)
    BUNDLENAME_VERSION     = re.compile(BUNDLENAME_REGEX.pattern[:-1] +
                                        r'(_v[0-9]+\.[0-9]+\.[0-9]+|'+
                                        r'_v[0-9]+\.[0-9]+|_v[0-9]+|'+
                                        r'_in_prep|_prelim|_peer_review|'+
                                        r'_lien_resolution)$')
    BUNDLENAME_VERSION_I   = re.compile(BUNDLENAME_VERSION.pattern, re.I)

    VOLSET_REGEX         = BUNDLESET_REGEX
    VOLSET_REGEX_I       = BUNDLESET_REGEX_I
    VOLSET_PLUS_REGEX    = BUNDLESET_PLUS_REGEX
    VOLSET_PLUS_REGEX_I  = BUNDLESET_PLUS_REGEX_I
    VOLNAME_REGEX        = BUNDLENAME_REGEX
    VOLNAME_REGEX_I      = BUNDLENAME_REGEX_I
    VOLNAME_PLUS_REGEX   = BUNDLENAME_PLUS_REGEX
    VOLNAME_PLUS_REGEX_I = BUNDLENAME_PLUS_REGEX_I
    VOLNAME_VERSION      = BUNDLENAME_VERSION
    VOLNAME_VERSION_I    = BUNDLENAME_VERSION_I

    # Logger
    LOGGER = pdslogger.NullLogger()

    # CACHE
    DICTIONARY_CACHE_LIMIT = 200000
    CACHE = pdscache.DictionaryCache(lifetime=cache_lifetime_for_class,
                                     limit=DICTIONARY_CACHE_LIMIT,
                                     logger=LOGGER)

    LOCAL_PRELOADED = []
    SUBCLASSES = {}

    # Override the rules
    DESCRIPTION_AND_ICON = rules.DESCRIPTION_AND_ICON
    ASSOCIATIONS = rules.ASSOCIATIONS
    VERSIONS = rules.VERSIONS
    INFO_FILE_BASENAMES = rules.INFO_FILE_BASENAMES
    NEIGHBORS = rules.NEIGHBORS
    SIBLINGS = rules.SIBLINGS       # just used by Viewmaster right now
    SORT_KEY = rules.SORT_KEY
    SPLIT_RULES = rules.SPLIT_RULES
    VIEW_OPTIONS = rules.VIEW_OPTIONS
    VIEWABLES = rules.VIEWABLES
    LID_AFTER_DSID = rules.LID_AFTER_DSID
    DATA_SET_ID = rules.DATA_SET_ID

    OPUS_TYPE = rules.OPUS_TYPE
    OPUS_FORMAT = rules.OPUS_FORMAT
    OPUS_PRODUCTS = rules.OPUS_PRODUCTS
    OPUS_ID = rules.OPUS_ID
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = rules.OPUS_ID_TO_PRIMARY_LOGICAL_PATH

    OPUS_ID_TO_SUBCLASS = rules.OPUS_ID_TO_SUBCLASS
    FILESPEC_TO_BUNDLESET = rules.FILESPEC_TO_BUNDLESET

    IDX_EXT = '.tab'
    LBL_EXT = '.lbl'

    def __init__(self):
        super().__init__()

    @classmethod
    def use_shelves_only(cls, status=True):
        """Call before preload(). Status=True to identify files based on their
        presence in the infoshelf files first. Search the file system only if a
        shelf is missing.

        Keyword arguments:
            cls    -- the class with its attribute being updated
            status -- value for the class attribute (default True)
        """

        cls.SHELVES_ONLY = status

    @classmethod
    def require_shelves(cls, status=True):
        """Call before preload(). Status=True to raise exceptions when shelf files
        are missing or incomplete. Otherwise, missing shelf info is only logged as a
        warning instead.

        Keyword arguments:
            cls    -- the class with its attribute being updated
            status -- value for the class attribute (default True)
        """

        cls.SHELVES_REQUIRED = status

    # Alias, compatible with old function/property names
    @property
    def is_volset(self):
        return self.is_bundleset

    @property
    def is_volset_file(self):
        return self.is_bundleset_file

    @property
    def is_volset_dir(self):
        return self.is_bundleset_dir

    @property
    def is_volume(self):
        return self.is_bundle

    @property
    def is_volume_file(self):
        return self.is_bundle_file

    @property
    def is_volume_dir(self):
        return self.is_bundle_dir

    def log_path_for_volset(self, suffix='', task='', dir='', place='default'):
        return self.log_path_for_bundleset(suffix, task, dir, place)

    def log_path_for_volume(self, suffix='', task='', dir='', place='default'):
        return self.log_path_for_bundle(suffix, task, dir, place)

    # Override functions
    def __repr__(self):
        if self.abspath is None:
            return 'Pds3File-logical("' + self.logical_path + '")'
        elif type(self) == Pds3File:
            return 'Pds3File("' + self.abspath + '")'
        else:
            return ('Pds3File.' + type(self).__name__ + '("' +
                    self.abspath + '")')

    @property
    def volset(self):
        return self.bundleset

    @property
    def volset_(self):
        return self.bundleset_

    @property
    def is_volset(self):
        return self.is_bundleset

    @property
    def is_volset_dir(self):
        return self.is_bundleset_dir

    @property
    def is_volset_file(self):
        return self.is_bundleset_file

    @property
    def volname(self):
        return self.bundlename

    @property
    def volname_(self):
        return self.bundlename_

    @property
    def is_volume(self):
        return self.is_bundle

    @property
    def is_volume_dir(self):
        return self.is_bundle_dir

    @property
    def is_volume_file(self):
        return self.is_bundle_file

    def log_path_for_volume(self, suffix='', task='', dir='', place='default'):
        return self.log_path_for_bundle(suffix=suffix, task=task, dir=dir, place=place)

#     def volset_abspath(self):
#         return self.bundleset_abspath()
#
#     def volset_pdsfile(self):
#         return self.bundleset_pdsfile()
#
#     def volume_abspath(self):
#         return self.bundle_abspath()
#
#     def volume_pdsfile(self):
#         return self.bundle_pdsfile()
#
#     @property
#     def voltype_(self):
#         return self.bundletype_
#
#     @property
#     def volume_publication_date(self):
#         return self.bundle_publication_date
#
#     @property
#     def volume_version_id(self):
#         return self.bundle_version_id

    ######################################################################################
    # PdsLogger support
    ######################################################################################
    @classmethod
    def set_logger(cls, logger=None):
        """Set the PdsLogger.

        Keyword arguments:
            logger -- the pdslogger (default None)
            cls    -- the class with its attribute being updated
        """
        if not logger:
            logger = pdslogger.NullLogger()

        cls.LOGGER = logger

    @classmethod
    def set_easylogger(cls):
        """Log all messages directly to stdout.

        Keyword arguments:
            cls -- the class calling the other methods inside the function
        """
        cls.set_logger(pdslogger.EasyLogger())


##########################################################################################
# Initialize the global registry of subclasses
##########################################################################################
Pds3File.SUBCLASSES['default'] = Pds3File

##########################################################################################
# This import must wait until after the Pds3File class has been fully initialized because
# all instruments specific rules are the subclasses of Pds3File
##########################################################################################

try:
    # Data set-specific rules are implemented as subclasses of Pds3File
    # from pdsfile_reorg.pds3file.rules import *
    from .rules import (ASTROM_xxxx,
                        COCIRS_xxxx,
                        COISS_xxxx,
                        CORSS_8xxx,
                        COSP_xxxx,
                        COUVIS_0xxx,
                        COUVIS_8xxx,
                        COVIMS_0xxx,
                        COVIMS_8xxx,
                        EBROCC_xxxx,
                        GO_0xxx,
                        HSTxx_xxxx,
                        JNOJIR_xxxx,
                        JNOJNC_xxxx,
                        JNOSP_xxxx,
                        NHSP_xxxx,
                        NHxxxx_xxxx,
                        RES_xxxx,
                        RPX_xxxx,
                        VG_0xxx,
                        VG_20xx,
                        VG_28xx,
                        VGIRIS_xxxx,
                        VGISS_xxxx)
except AttributeError:
    pass                    # This occurs when running pytests on individual
                            # rule subclasses, where pdsfile can be imported
                            # recursively.

Pds3File.cache_category_merged_dirs()
