##########################################################################################
# pdsfile/pdsfile.py
# General pdsfile package & PdsFile class
##########################################################################################

import bisect
import datetime
import fnmatch
import functools
import glob
import math
import numbers
import os
import pickle
import PIL
import re
import time

import pdslogger
import pdstable
import pdsparser
import translator

from collections import defaultdict
from pdsfile import (pdscache,
                     pdsviewable)

# Import module for memcached if possible, otherwise flag
try: # pragma: no cover
    import pylibmc
    HAS_PYLIBMC = True
except ImportError: # pragma: no cover
    HAS_PYLIBMC = False

from .preload_and_cache import (cache_lifetime_for_class,
                                pause_caching,
                                resume_caching)

# Configuration
_GLOB_CACHE_SIZE = 200
PATH_EXISTS_CACHE_SIZE = 200
FILE_BYTE_UNITS = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

##########################################################################################
# Support functions for pdsfile/__init__.py
##########################################################################################
def construct_category_list(voltypes):
    category_list = []
    for checksums in ('', 'checksums-'):
        for archives in ('', 'archives-'):
            for voltype in voltypes:
                category_list.append(checksums + archives + voltype)

    category_list.remove('checksums-documents')
    category_list.remove('archives-documents')
    category_list.remove('checksums-archives-documents')

    return category_list


def logical_path_from_abspath(abspath, cls):
    """Return the logical path derived from an absolute path.

    Keyword arguments:
        abspath -- the abosulte path of a file
        cls     -- the class calling the other methods inside the function
    """
    parts = abspath.partition('/'+cls.PDS_HOLDINGS+'/')
    if parts[1]:
        return parts[2]

    raise ValueError('Not compatible with a logical path: ', abspath)

def _clean_join(a, b):
#     joined = _clean_join(a,b).replace('\\', '/')
    if a:
        return a + '/' + b
    else:
        return b

def _clean_abspath(path):
    abspath = os.path.abspath(path)
    if os.sep == '\\':
        abspath = abspath.replace('\\', '/')
    return abspath

@functools.lru_cache(maxsize=_GLOB_CACHE_SIZE)
def _clean_glob(cls, pattern, force_case_sensitive=False):
    results = glob.glob(pattern)
    if os.sep == '\\':
        results = [x.replace('\\', '/') for x in results]

    if force_case_sensitive and cls.FS_IS_CASE_INSENSITIVE:
        filtered_results = []
        for result in results:
            result = repair_case(result, cls)
            if fnmatch.fnmatchcase(result, pattern):
                filtered_results.append(result)

        return filtered_results

    else:
        return results

def _needs_glob(pattern):
    """Return True if the given expression contains wildcards

    Keyword arguments:
        pattern -- expression pattern
    """
    return '*' in pattern or '?' in pattern or '[' in pattern

def repair_case(abspath, cls):
    """Return a file's absolute path with capitalization exactly as it appears
    in the file system. Raises IOError if the file is not found.

    Keyword arguments:
        abspath -- an absolute path of a file
        cls     -- the class calling the other methods inside the function
    """

    trailing_slash = abspath.endswith('/')  # must preserve a trailing slash!
    abspath = _clean_abspath(abspath)

    # Fields are separated by slashes
    parts = abspath.split('/')
    if parts[-1] == '':
        parts = parts[:-1]      # Remove trailing slash

    # On Unix, parts[0] is always '' so no need to check case
    # On Windows, this skips over the name of the drive

    # For each subsequent field (between slashes)...
    for k in range(1, len(parts)):

        # Convert it to lower case for matching
        part_lower = parts[k].lower()

        # Construct the name of the parent directory and list its contents.
        # This will raise an IOError if the file does not exist or is not a
        # directory.
        if k == 1:
            basenames = os.listdir('/')
        else:
            basenames = cls.os_listdir('/'.join(parts[:k]))

        # Find the first name that matches when ignoring case
        found = False
        for name in basenames:
            if name.lower() == part_lower:

                # Replace the field with the properly capitalized name
                parts[k] = name
                found = True
                break

    # Reconstruct the full path
    if trailing_slash: parts.append('')
    abspath = '/'.join(parts)

    # Raise an IOError if last field was not found
    if not found:
        with open(abspath, 'rb') as f:
            pass

    return abspath

def formatted_file_size(size):
    order = int(math.log10(size) // 3) if size else 0
    return f'{size / 1000.**order:.3g} {FILE_BYTE_UNITS[order]}'

def abspath_for_logical_path(path, cls):
    """Return the absolute path derived from the given logical path.

    The logical path starts at the category, below the holdings/ directory. To
    get the absolute path, we need to figure out where the holdings directory is
    located. Note that there can be multiple drives hosting multiple holdings
    directories.

    Keyword arguments:
        path -- the path of a file
        cls  -- the class calling the other methods inside the function
    """

    # Check for a valid logical path
    parts = path.split('/')
    if parts[0] not in cls.CATEGORIES:
        raise ValueError('Not a logical path: ' + path)

    # Use the list of preloaded holdings directories if it is not empty
    if cls.LOCAL_PRELOADED:
        holdings_list = cls.LOCAL_PRELOADED

    elif cls.LOCAL_HOLDINGS_DIRS:
        holdings_list = cls.LOCAL_HOLDINGS_DIRS

    elif 'PDS3_HOLDINGS_DIR' in os.environ:
        holdings_list = [os.environ['PDS3_HOLDINGS_DIR']]
        cls.LOCAL_HOLDINGS_DIRS = holdings_list

    # Without a preload or an environment variable, check the
    # /Library/WebSever/Documents directory for a symlink. This only works for
    # MacOS with the website installed, but that's OK.
    else:
        holdings_dirs = glob.glob('/Library/WebServer/Documents/holdings*')
        holdings_dirs.sort()
        holdings_list = [os.path.realpath(h) for h in holdings_dirs]
        cls.LOCAL_HOLDINGS_DIRS = holdings_list

    # With exactly one holdings/ directory, the answer is easy
    if len(holdings_list) == 1:
        return _clean_join(holdings_list[0], path)

    # Otherwise search among the available holdings directories in order
    for root in holdings_list:
        abspath = _clean_join(root, path)
        matches = cls.glob_glob(abspath)
        if matches: return matches[0]

    # File doesn't exist. Just pick one.
    if holdings_list:
        return _clean_join(holdings_list[0], path)

    raise ValueError('No holdings directory for logical path ' + path)

def selected_path_from_path(path, cls, abspaths=True):
    """Return the logical path or absolute path derived from a logical or
    an absolute path.

    Keyword arguments:
        path     -- the path of a file
        cls      -- the class calling the other methods inside the function
        abspaths -- the flag to determine if the return value is an absolute path (default
                    True)
    """

    if cls.is_logical_path(path):
        if abspaths:
            return abspath_for_logical_path(path, cls)
        else:
            return path

    else:
        if abspaths:
            return path
        else:
            return logical_path_from_abspath(path, cls)

##########################################################################################
# PdsFile class
##########################################################################################

class PdsFile(object):

    # Configuration
    VOLTYPES = ['volumes', 'calibrated', 'diagrams', 'metadata', 'previews',
                'documents', 'bundles']
    VIEWABLE_VOLTYPES = ['previews', 'diagrams']

    VIEWABLE_EXTS = set(['jpg', 'png', 'gif', 'tif', 'tiff', 'jpeg', 'jpeg_small'])
    DATAFILE_EXTS = set(['dat', 'img', 'cub', 'qub', 'fit', 'fits'])

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

    CATEGORY_REGEX      = re.compile(r'^(|checksums\-)(|archives\-)(\w+)$')
    CATEGORY_REGEX_I    = re.compile(CATEGORY_REGEX.pattern, re.I)

    VIEWABLE_ANCHOR_REGEX = re.compile(r'(.*/\w+)_[a-z]+\.(jpg|png)')
    # path/A1234566_thumb.jpg -> path/A1234566

    LOGFILE_TIME_FMT = '%Y-%m-%dT%H-%M-%S'

    PLAIN_TEXT_EXTS = set(['lbl', 'txt', 'asc', 'tab', 'cat', 'fmt', 'f', 'c',
                        'cpp', 'pro', 'for', 'f77', 'py', 'inc', 'h', 'sh',
                        'idl', 'csh', 'tf', 'ti', 'tls', 'lsk', 'tsc'])

    MIME_TYPES_VS_EXT = {
        'fit'       : 'image/fits',
        'fits'      : 'image/fits',
        'jpg'       : 'image/jpg',
        'jpeg'      : 'image/jpg',
        'jpeg_small': 'image/jpg',
        'tif'       : 'image/tiff',
        'tiff'      : 'image/tiff',
        'png'       : 'image/png',
        'bmp'       : 'image/bmp',
        'gif'       : 'image/*',
        'csv'       : 'text/csv',
        'pdf'       : 'application/pdf',
        'xml'       : 'text/xml',
        'rtf'       : 'text/rtf',
        'htm'       : 'text/html',
        'html'      : 'text/html',
    }

    # Key is (voltype, is_bundleset). Return is default icon_type.
    DEFAULT_HIGH_LEVEL_ICONS = {
    ('volumes/',    True ): 'VOLDIR',
    ('volumes/',    False): 'VOLUME',
    ('calibrated/', True ): 'DATADIR',
    ('calibrated/', False): 'DATADIR',
    ('metadata/',   True ): 'INDEXDIR',
    ('metadata/',   False): 'INDEXDIR',
    ('previews/',   True ): 'BROWDIR',
    ('previews/',   False): 'BROWDIR',
    ('diagrams/',   True ): 'DIAGDIR',
    ('diagrams/',   False): 'DIAGDIR',
    ('documents/',  True ): 'INFODIR',
    ('documents/',  False): 'INFO',
    ('archives-volumes/',    True ): 'TARDIR',
    ('archives-volumes/',    False): 'TARBALL',
    ('archives-calibrated/', True ): 'TARDIR',
    ('archives-calibrated/', False): 'TARBALL',
    ('archives-metadata/',   True ): 'TARDIR',
    ('archives-metadata/',   False): 'TARBALL',
    ('archives-previews/',   True ): 'TARDIR',
    ('archives-previews/',   False): 'TARBALL',
    ('archives-diagrams/',   True ): 'TARDIR',
    ('archives-diagrams/',   False): 'TARBALL',
    ('archives-documents/',  True ): 'TARDIR',
    ('archives-documents/',  False): 'TARBALL',
    }


    # Directory prefix and file suffix for shelf files
    SHELF_PATH_INFO = {
        'index': ('_indexshelf-', '_index'),
        'info' : ('_infoshelf-', '_info'),
        'link' : ('_linkshelf-', '_links'),
    }

    PDS_HOLDINGS = 'holdings'
    BUNDLE_DIR_NAME = 'bundles'

    # Flag
    SHELVES_ONLY = False
    SHELVES_REQUIRED = False
    FS_IS_CASE_INSENSITIVE = True

    # Logger
    LOGGER = pdslogger.NullLogger()

    # CACHE
    LOCAL_PRELOADED = []

    # Initialize the cache
    MEMCACHE_PORT = 0           # default is to use a DictionaryCache instead
    DICTIONARY_CACHE_LIMIT = 200000

    # this cache is used if preload() is never called. No filesystem is required.
    CACHE = pdscache.DictionaryCache(lifetime=cache_lifetime_for_class,
                                     limit=DICTIONARY_CACHE_LIMIT,
                                     logger=LOGGER)

    DEFAULT_CACHING = 'dir'     # 'dir', 'all' or 'none';
                                # use 'dir' for Viewmaster without MemCache;
                                # use 'all' for Viewmaster with MemCache;
    PRELOAD_TRIES = 3

    # CATEGORIES contains the name of every subdirectory of holdings/
    CATEGORY_LIST = construct_category_list(VOLTYPES)
    CATEGORIES = set(CATEGORY_LIST)

    # Extra description files that can appear in bundleset directories
    EXTRA_README_BASENAMES = ('AAREADME.txt', 'AAREADME.pdf')

    # Global registry of subclasses
    SUBCLASSES = {}

    # Translator from bundle set ID to key in global registry
    VOLSET_TRANSLATOR = translator.TranslatorByRegex([('.*', 0, 'default')])

    # Default translators, can be overridden by bundleset-specific subclasses
    DESCRIPTION_AND_ICON = None
    ASSOCIATIONS = None
    VERSIONS = None
    INFO_FILE_BASENAMES = None
    NEIGHBORS = None
    SIBLINGS = None     # just used by Viewmaster right now
    SORT_KEY = None
    SPLIT_RULES = None
    VIEW_OPTIONS = None
    VIEWABLES = None
    LID_AFTER_DSID = None
    DATA_SET_ID = None

    OPUS_TYPE = None
    OPUS_FORMAT = None
    OPUS_PRODUCTS = None
    OPUS_ID = None
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = None

    OPUS_ID_TO_SUBCLASS = None

    FILESPEC_TO_BUNDLESET = None

    FILENAME_KEYLEN = 0

    # Global will contain all the physical holdings directories on the system.
    LOCAL_HOLDINGS_DIRS = None

    ############################################################################
    # DEFAULT FILE SORT ORDER
    ############################################################################

    SORT_ORDER = {
        'labels_after': True,
        'dirs_first'  : False,
        'dirs_last'   : False,
        'info_first'  : 20,     # info files first if there are at least this
                                # many files; 0 or False for never, 1 or True
                                # for always.
    }

    def sort_labels_after(self, labels_after):
        """If True, all label files will appear after their associated data
        files when sorted.

        Keyword arguments:
            labels_after -- a flag used to determine if all label files should appear
                            after the associated data files when sorted.
        """

        self.SORT_ORDER = self.SORT_ORDER.copy()
        self.SORT_ORDER['labels_after'] = labels_after

    def sort_dirs_first(self, dirs_first):
        """If True, directories will appear before all files in a sorted list.

        Keyword arguments:
            dirs_first -- a flag used to determine if directories should appear before
                          all files when sorted.
        """

        self.SORT_ORDER = self.SORT_ORDER.copy()
        self.SORT_ORDER['dirs_first'] = dirs_first

    def sort_dirs_last(self, dirs_last):
        """If True, directories will appear after all files in a sorted list.

        Keyword arguments:
            dirs_last -- a flag used to determine if directories should appear after all
                         files when sorted.
        """

        self.SORT_ORDER = self.SORT_ORDER.copy()
        self.SORT_ORDER['dirs_last'] = dirs_last

    def sort_info_first(self, info_first):
        """If True or 1, info files will be listed first in all sorted lists;
        if False or 0, info files will appear alphabetically;
        if an integer bigger than 1, put the info file first only if there are
        at least this many files in the directory.

        Keyword arguments:
            info_first -- a flag used to determine info files will be listed first in all
                          sorted lists.
        """

        self.SORT_ORDER = self.SORT_ORDER.copy()
        self.SORT_ORDER['info_first'] = info_first

    ############################################################################
    # Constructor
    ############################################################################

    def __init__(self):
        """Constructor returns a blank PdsFile object. Not for external use."""

        self.basename     = ''
        self.abspath      = ''
        self.logical_path = ''      # Logical path starting after 'holdings/'

        self.disk_        = ''      # Disk name alone
        self.root_        = ''      # Disk path + '/holdings/'
        self.html_root_   = ''      # '/holdings/', '/holdings2/', etc.

        self.category_    = ''      # Always checksums_ + archives_ + voltype_
        self.checksums_   = ''      # Either 'checksums-' or ''
        self.archives_    = ''      # Either 'archives-' or ''
        self.voltype_     = ''      # One of 'volumes', 'metadata', etc.

        self.bundleset_   = ''      # Bundleset name + suffix + '/'
        self.bundleset    = ''      # Bundleset name, suffix stripped
        self.suffix       = ''      # Bundleset suffix alone
        self.version_message = ''
        self.version_rank = 0       # int; 'v1.2.3' -> 10203; 999999 for latest
        self.version_id   = ''      # E.g., 'v1.2.3'; version number of volume

        self.bundlename_  = ''      # Bundle name + '/'
        self.bundlename   = ''      # Bundle name alone

        self.interior     = ''      # Path starting inside volume directory

        self.is_index_row = False   # True for a "fake" PdsFile describing one
                                    # or more rows inside an index table
        self.row_dicts    = []      # List of row dictionaries if this is an
                                    # index row.
        self.column_names = []      # Ordered list of column names for an index
                                    # row or its parent.

        self.permanent    = False   # If True, never to be removed from cache
        self.is_merged    = False   # If True, a category directory with
                                    # contents merged from multiple phsical
                                    # directories

        self._exists_filled         = None
        self._islabel_filled        = None
        self._isdir_filled          = None
        self._split_filled          = None
        self._global_anchor_filled  = None
        self._childnames_filled     = None
        self._childnames_lc_filled  = None
        self._info_filled           = None  # (bytes, child_count, modtime,
                                            # checksum, size)
        self._date_filled           = None
        self._formatted_size_filled = None
        self._is_viewable_filled    = None
        self._info_basename_filled  = None
        self._label_basename_filled = None
        self._viewset_filled        = None
        self._local_viewset_filled  = None
        self._all_viewsets_filled   = None
        self._iconset_filled        = None
        self._internal_links_filled = None
        self._mime_type_filled      = None
        self._opus_id_filled        = None
        self._opus_type_filled      = None
        self._opus_format_filled    = None
        self._view_options_filled   = None  # (grid, multipage, continuous)
        self._volume_info_filled    = None  # (desc, icon type, version ID,
                                            #  pub date, list of dataset IDs,
                                            # optional MD5 checksum)
        self._all_version_abspaths  = None
        self._html_path_filled      = None
        self._description_and_icon_filled    = None
        self._volume_publication_date_filled = None
        self._volume_version_id_filled       = None
        self._volume_data_set_ids_filled     = None
        self._lid_filled                     = None
        self._lidvid_filled                  = None
        self._data_set_id_filled             = None
        self._version_ranks_filled           = None
        self._exact_archive_url_filled       = None
        self._exact_checksum_url_filled      = None
        self._associated_parallels_filled    = None
        self._filename_keylen_filled         = None
        self._infoshelf_path_and_key         = None
        self._is_index                       = None
        self._indexshelf_abspath             = None
        self._index_pdslabel                 = None

    def new_pdsfile(self, key=None, copypath=False):
        """Return an empty PdsFile of the same subclass or a specified subclass.

        Keyword arguments:
            key      -- the name of a bundleset that exists in the SUBCLASSES dictionary
                        or a bundleset pattern that could be matched by VOLSET_TRANSLATOR.
                        (default None)
            copypath -- a flag to determine if the returned pdsfile instance should copy
                        all the attributes from the instance calling the method. (default
                        False)
        """
        cls = type(self)
        if key is None:
            cls = type(self)
        elif key in cls.SUBCLASSES:
            cls = cls.SUBCLASSES[key]
        else:
            key2 = cls.VOLSET_TRANSLATOR.first(key)
            cls = cls.SUBCLASSES[key2]

        this = cls.__new__(cls)

        source = cls()
        for (key, value) in source.__dict__.items():
            this.__dict__[key] = value

        if copypath:
            this.basename        = self.basename
            this.abspath         = self.abspath
            this.logical_path    = self.logical_path
            this.disk_           = self.disk_
            this.root_           = self.root_
            this.html_root_      = self.html_root_
            this.category_       = self.category_
            this.checksums_      = self.checksums_
            this.archives_       = self.archives_
            this.voltype_        = self.voltype_
            this.bundleset_      = self.bundleset_
            this.bundleset       = self.bundleset
            this.suffix          = self.suffix
            this.version_message = self.version_message
            this.version_rank    = self.version_rank
            this.version_id      = self.version_id
            this.bundlename_     = self.bundlename_
            this.bundlename      = self.bundlename
            this.interior        = self.interior

        return this

    ######################################################################################
    # Set parameters for both Pds3File and Pds4File
    ######################################################################################
    @classmethod
    def use_shelves_only(cls, status=True):
        """Set SHELVES_ONLY for both Pds3File and Pds4File

        Keyword arguments:
            cls    -- the class with its attribute being updated
            status -- value for SHELVES_ONLY (default True)
        """

        subclasses = cls.__subclasses__()
        for child_class in subclasses:
            child_class.SHELVES_ONLY = status

    @classmethod
    def require_shelves(cls, status=True):
        """Set SHELVES_REQUIRED for both Pds3File and Pds4File

        Keyword arguments:
            cls    -- the class with its attribute being updated
            status -- value for SHELVES_REQUIRED (default True)
        """

        subclasses = cls.__subclasses__()
        for child_class in subclasses:
            child_class.SHELVES_REQUIRED = status


    @classmethod
    def set_logger(cls, logger=None):
        """Set the PdsLogger for both Pds3File and Pds4File.

        Keyword arguments:
            logger -- the pdslogger (default None)
            cls    -- the class with its attribute being updated
        """

        if not logger:
            logger = pdslogger.NullLogger()

        subclasses = cls.__subclasses__()
        for child_class in subclasses:
             child_class.LOGGER = logger


    @classmethod
    def set_easylogger(cls):
        """Log all messages directly to stdout.

        Keyword arguments:
            cls -- the class calling the other methods inside the function
        """

        subclasses = cls.__subclasses__()
        for child_class in subclasses:
             child_class.set_easylogger()

    ######################################################################################
    # Preload management
    ######################################################################################
    @classmethod
    def get_permanent_values(cls, holdings_list, port):
        """Load the most obvious set of permanent values from the cache to ensure
        we have current local copies.

        Keyword arguments:
            holdings_list -- the path of holdings dir that we will preload if the permanent
                            value from cache is missing
            port          -- value for the class attribute
            cls           -- the class calling the method
        """

        try:
            pause_caching(cls)

            # For each category...
            for category in cls.CATEGORY_LIST:

                # Get the cached values
                _ = cls.CACHE['$RANKS-' + category + '/']
                _ = cls.CACHE['$VOLS-'  + category + '/']
                pdsf0 = cls.CACHE[category]

                # Also get the bundleset-level PdsFile inside each category
                for bundleset in pdsf0.childnames:
                    if bundleset.endswith('.txt') or bundleset.endswith('.tar.gz'):
                        continue
                    # Get the entry keyed by the logical path
                    pdsf1 = cls.CACHE[category + '/' + bundleset.lower()]

                    # Also get its bundle-level children
                    for bundlename in pdsf1.childnames:
                        if bundlename.endswith('.txt') or bundlename.endswith('.tar.gz'):
                            continue

                        key = (pdsf1.logical_path + '/' + bundlename).lower()
                        pdsf2 = cls.CACHE[key]

        except KeyError as e:
            cls.LOGGER.warn('Permanent value %s missing from Memcache; '
                        'preloading again' % str(e))
            cls.preload(holdings_list, port, force_reload=True)

        else:
            cls.LOGGER.info('Permanent values retrieved from Memcache',
                        str(len(cls.CACHE.permanent_values)))

        finally:
            resume_caching()

    @classmethod
    def load_volume_info(cls, holdings):
        """Load bundle info associated with this holdings directory.

        Each record contains a sequence of values separated by "|":
            key: bundleset, bundleset/bundlename, category/bundleset, or category/bundleset/bundlename
            description
            icon_type or blank for default
            version ID or a string of dashes "-" if not applicable
            publication date or a string of dashes "-" if not applicable
            data set ID (if any) or MD5 checksum if this is in the documents/ tree
            additional data set IDs (if any)

        This creates and caches a dictionary based on the key identified above. Each
        entry is a tuple with five elements:
            description,
            icon_type or blank for default,
            version ID or None,
            publication date or None,
            list of data set IDs,
            MD5 checksum or ''

        A value only containing a string of dashes "-" is replaced by None.
        Blank records and those beginning with "#" are ignored.

        Keyword arguments:
            holdings -- the path of the holdings directory
            cls      -- the class calling the method
        """

        volinfo_path = _clean_join(holdings, '_volinfo')

        volinfo_dict = {}           # the master dictionary of high-level paths vs.
                                    # (description, icon_type, version ID,
                                    #  publication date, optional list of data set
                                    #  IDs, optional checksum)

        keys_without_dsids = []     # internal list of entries without data set IDs
        dsids_vs_key = {}           # global dictionary of data set IDs for entries
                                    # that have them

        # For each file in the volinfo subdirectory...
        children = os.listdir(volinfo_path)
        for child in children:

            # Ignore these
            if child.startswith('.'): continue
            if not child.endswith('.txt'):
                continue

            # Read the file
            table_path = _clean_join(volinfo_path, child)
            with open(table_path, 'r', encoding='utf-8') as f:
                recs = f.readlines()

            # Interpret each record...
            for rec in recs:
                if rec[0] == '#':
                    continue                        # ignore comments

                parts = rec.split('|')              # split by "|"
                parts = [p.strip() for p in parts]  # remove extraneous blanks
                if parts == ['']:
                    continue                        # ignore blank lines

                # Identify missing info
                while len(parts) <= 5:
                    parts.append('')

                if parts[2] == '' or set(parts[2]) == {'-'}:
                    parts[2] = None
                if set(parts[3]) == {'-'}:
                    parts[3] = None
                if set(parts[4]) == {'-'}:
                    parts[4] = None

                if (parts[0].startswith('documents/') or
                    parts[0].rpartition('/')[2] in cls.EXTRA_README_BASENAMES):
                        md5 = parts[5]
                        dsids = []
                else:
                        md5 = ''
                        dsids = list(parts[5:])

                # Update either keys_without_dsids or dsids_vs_key. This is used
                # to fill in data set IDs for voltypes other than "volumes/".
                if dsids == ['']:
                    dsids = []

                if dsids:
                    dsids_vs_key[parts[0]] = dsids
                else:
                    keys_without_dsids.append(parts[0])

                # Fill in the master dictionary
                volinfo = (parts[1], parts[2], parts[3], parts[4], dsids, md5)
                volinfo_dict[parts[0]] = volinfo

        # Update the list of data set IDs wherever it's missing
        for key in keys_without_dsids:
            (category, _, remainder) = key.partition('/')
            if category in cls.VOLTYPES:
                (volset_with_suffix, _, remainder) = remainder.partition('/')
                bundleset = '_'.join(volset_with_suffix.split('_')[:2])
                alt_keys = (bundleset + '/' + remainder,
                            'volumes/' + bundleset + '/' + remainder)
                for alt_key in alt_keys:
                    if alt_key in dsids_vs_key:
                        volinfo_dict[key] = (volinfo_dict[key][:4] +
                                            (dsids_vs_key[alt_key],
                                            volinfo_dict[key][5]))
                        break

        # Save the master dictionary in the cache now
        for key,volinfo in volinfo_dict.items():
            cls.CACHE.set('$VOLINFO-' + key.lower(), volinfo, lifetime=0)

        cls.LOGGER.info('Volume info loaded', volinfo_path)

    @classmethod
    def cache_category_merged_dirs(cls):
        for category in cls.CATEGORY_LIST:
            if category not in cls.CACHE:
                cls.CACHE.set(category, cls.new_merged_dir(category), lifetime=0)

    @classmethod
    def preload(cls, holdings_list, port=0, clear=False, force_reload=False,
                icon_url=None, icon_color='blue'):
        """Cache the top-level directories, starting from the given holdings directories.

        Keyword arguments:
            holdings_list -- a single abslute path to a holdings directory, or else a list
                             of absolute paths
            port          -- port to use for memcached; zero to prevent use of memcached
            clear         -- True to clear the cache before preloading
            force_reload  -- Re-load the cache regardless of whether the cache appears to
                             contain the needed holdings
            icon_url      -- URL root to use for loading icons; defaults to
                             "/holdings/_icons" or "/holdings<n>/_icons" as needed
            icon_color    -- color of the icons to load from each holdings directory
                             (default 'blue')
        """

        # Convert holdings to a list of absolute paths
        if not isinstance(holdings_list, (list,tuple)):
            holdings_list = [holdings_list]

        holdings_list = [_clean_abspath(h) for h in holdings_list]

        # Use cache as requested
        if (port == 0 and cls.MEMCACHE_PORT == 0) or not HAS_PYLIBMC:
            if not isinstance(cls.CACHE, pdscache.DictionaryCache):
                cls.CACHE = pdscache.DictionaryCache(lifetime=cls.cache_lifetime,
                                                     limit=cls.DICTIONARY_CACHE_LIMIT,
                                                     logger=cls.LOGGER)
            cls.LOGGER.info('Using local dictionary cache')

        else:
            cls.MEMCACHE_PORT = cls.MEMCACHE_PORT or port

            for k in range(cls.PRELOAD_TRIES):
                try:
                    cls.CACHE = pdscache.MemcachedCache(cls.MEMCACHE_PORT,
                                                        lifetime=cls.cache_lifetime,
                                                        logger=cls.LOGGER)
                    cls.LOGGER.info('Connecting to PdsFile Memcache [%s]' %
                                    cls.MEMCACHE_PORT)
                    break

                except pylibmc.Error:
                    if k < cls.PRELOAD_TRIES - 1:
                        cls.LOGGER.warn(('Failed to connect PdsFile Memcache [%s]; ' +
                                         'trying again in %d sec') %
                                        (cls.MEMCACHE_PORT, 2**k))
                        time.sleep(2.**k)       # try then wait 1 sec, then 2 sec

                    else:       # give up after three tries
                        cls.LOGGER.error(('Failed to connect PdsFile Memcache [%s]; '+
                                          'using dictionary instead') %
                                         cls.MEMCACHE_PORT)

                        cls.MEMCACHE_PORT = 0
                        if not isinstance(cls.CACHE, pdscache.DictionaryCache):
                            cls.CACHE = pdscache.DictionaryCache(
                                            lifetime=cls.cache_lifetime,
                                            limit=cls.DICTIONARY_CACHE_LIMIT,
                                            logger=cls.LOGGER
                                        )

        # Define default caching based on whether MemCache is active
        if cls.MEMCACHE_PORT == 0:
            cls.DEFAULT_CACHING = 'dir'
        else:
            cls.DEFAULT_CACHING = 'all'

        # This suppresses long absolute paths in the logs
        cls.LOGGER.add_root(holdings_list)

        #### Get the current list of preloaded holdings directories and decide how
        #### to proceed

        if clear:
            cls.CACHE.clear(block=True) # For a MemcachedCache, this will pause for any
                                    # other thread's block, then clear, and retain
                                    # the block until the preload is finished.
            cls.LOCAL_PRELOADED = []
            cls.LOGGER.info('Cache cleared')

        elif force_reload:
            cls.LOCAL_PRELOADED = []
            cls.LOGGER.info('Forcing a complete new preload')
            cls.CACHE.wait_and_block()

        else:
            while True:
                cls.LOCAL_PRELOADED = cls.CACHE.get_now('$PRELOADED') or []

                # Report status
                something_is_missing = False
                for holdings in holdings_list:
                    if holdings in cls.LOCAL_PRELOADED:
                        cls.LOGGER.info('Holdings are already cached', holdings)
                    else:
                        something_is_missing = True

                if not something_is_missing:
                    if cls.MEMCACHE_PORT:
                        cls.get_permanent_values(holdings_list, cls.MEMCACHE_PORT)
                        # Note that if any permanently cached values are missing,
                        # this call will recursively clear the cache and preload
                        # again. This reduces the chance of a corrupted cache.

                    return

                waited = cls.CACHE.wait_and_block()
                if not waited:      # A wait suggests the answer might have changed,
                                    # so try again.
                    break

                cls.CACHE.unblock()

        # At this point, the cache is blocked.

        # Pause the cache before proceeding--saves I/O
        cls.CACHE.pause()       # Paused means no local changes will be flushed to the
                            # external cache until resume() is called.

        ############################################################################
        # Interior function to recursively preload one physical directory
        ############################################################################

        def _preload_dir(pdsdir, cls):
            if not pdsdir.isdir: return

            # Log category directories as info
            if pdsdir.is_category_dir:
                cls.LOGGER.info('Pre-loading: ' + pdsdir.abspath)

            # Log bundlesets as debug
            elif pdsdir.is_bundleset:
                cls.LOGGER.debug('Pre-loading: ' + pdsdir.abspath)

            # Don't go deeper
            else:
                return

            # Preloaded dirs are permanent
            pdsdir.permanent = True

            # Make recursive calls and cache
            for basename in list(pdsdir.childnames):
                try:
                    child = pdsdir.child(basename, fix_case=False, lifetime=0)
                    _preload_dir(child, cls)
                except ValueError:              # Skip out-of-place files
                    pdsdir._childnames_filled.remove(basename)

        #### Fill CACHE

        try:    # we will undo the pause and block in the "finally" clause below

            # Create and cache permanent, category-level merged directories. These
            # are roots of the cache tree and their list of children is merged from
            # multiple physical directories. This makes it possible for our data
            # sets to exist on multiple physical drives in a way that is invisible
            # to the user.
            for category in cls.CATEGORY_LIST:
                cls.CACHE.set(category, cls.new_merged_dir(category), lifetime=0)

            # Initialize RANKS, VOLS and category list
            for category in cls.CATEGORY_LIST:
                category_ = category + '/'
                key = '$RANKS-' + category_
                try:
                    _ = cls.CACHE[key]
                except KeyError:
                    cls.CACHE.set(key, {}, lifetime=0)

                key = '$VOLS-'  + category_
                try:
                    _ = cls.CACHE[key]
                except KeyError:
                    cls.CACHE.set(key, {}, lifetime=0)

            # Cache all of the top-level PdsFile directories
            for h,holdings in enumerate(holdings_list):

                if holdings in cls.LOCAL_PRELOADED:
                    cls.LOGGER.info('Pre-load not needed for ' + holdings)
                    continue

                cls.LOCAL_PRELOADED.append(holdings)
                cls.LOGGER.info('Pre-loading ' + holdings)

                # Load volume info
                # PDS4 will ignore _volinfo directory
                if cls.__name__ != 'Pds4File':
                    cls.load_volume_info(holdings)

                # Load directories starting from here
                holdings_ = holdings.rstrip('/') + '/'

                for c in cls.CATEGORY_LIST:
                    category_abspath = holdings_ + c
                    if not cls.os_path_exists(category_abspath):
                        cls.LOGGER.warn('Missing category dir: ' + category_abspath)
                        continue
                    if not cls.os_path_isdir(category_abspath):
                        cls.LOGGER.warn('Not a directory, ignored: ' + category_abspath)

                    # This is a physical PdsFile, but from_abspath also adds its
                    # childnames to the list of children for the category-level
                    # merged directory.
                    pdsdir = cls.from_abspath(category_abspath, fix_case=False,
                                                caching='all', lifetime=0)
                    _preload_dir(pdsdir, cls)

                # Load the icons
                icon_path = _clean_join(holdings, '_icons')
                if os.path.exists(icon_path):
                    final_icon_url = icon_url
                    if final_icon_url is None:
                        final_icon_url = '/holdings' + (str(h) if h > 0 else '') + '/_icons'
                    pdsviewable.load_icons(icon_path, final_icon_url, icon_color,
                                           cls.LOGGER)

        finally:
            cls.CACHE.set('$PRELOADED', cls.LOCAL_PRELOADED, lifetime=0)
            cls.CACHE.resume()
            cls.CACHE.unblock(flush=True)

        cls.LOGGER.info('PdsFile preloading completed')

        # Determine if the file system is case-sensitive
        # If any physical bundle is case-insensitive, then we treat the whole file
        # system as case-insensitive.
        cls.FS_IS_CASE_INSENSITIVE = False
        for holdings_dir in cls.LOCAL_PRELOADED:
            testfile = holdings_dir.replace('/holdings', '/HoLdInGs')
            if os.path.exists(testfile):
                cls.FS_IS_CASE_INSENSITIVE = True
                break

    @classmethod
    def cache_lifetime(cls, arg):
        return cache_lifetime_for_class(arg, cls)

    @classmethod
    def new_merged_dir(cls, basename):
        """Return a merged directory with the given basename. Merged directories contain
        children from multiple physical directories. Examples are volumes/,
        archives-volumes/, etc.

        Keyword arguments:
            basename -- the basename of the merged directory.
        """

        if basename not in cls.CATEGORIES:
            raise ValueError('Invalid category: ' + basename)

        this = cls()

        this.basename     = basename
        this.abspath      = None
        this.logical_path = basename

        this.disk_        = None
        this.root_        = None
        this.html_root_   = None

        this.category_    = basename.rstrip('/') + '/'
        this.checksums_   = 'checksums-' if 'checksums-' in basename else ''
        this.archives_    = 'archives-'  if 'archives-'  in basename else ''
        this.voltype_     = basename.split('-')[-1].rstrip('/') + '/'

        this.bundleset_   = ''
        this.bundleset    = ''
        this.suffix       = ''
        this.version_message = ''
        this.version_rank = 0
        this.version_id   = ''

        this.bundlename_  = ''
        this.bundlename   = ''

        this.interior     = ''

        this.is_index_row = False
        this.row_dicts    = []
        this.column_names = []

        this.permanent    = True
        this.is_merged    = True

        this._exists_filled         = True
        this._islabel_filled        = False
        this._isdir_filled          = True
        this._split_filled          = (basename, '', '')
        this._global_anchor_filled  = basename
        this._childnames_filled     = []
        this._childnames_lc_filled  = []
        this._info_filled           = [None, None, None, '', (0,0)]
        this._date_filled           = ''
        this._formatted_size_filled = ''
        this._is_viewable_filled    = False
        this._info_basename_filled  = ''
        this._label_basename_filled = ''
        this._viewset_filled        = False
        this._local_viewset_filled  = False
        this._all_viewsets_filled   = {}
        this._internal_links_filled = []
        this._mime_type_filled      = ''
        this._opus_id_filled        = ''
        this._opus_type_filled      = ''
        this._opus_format_filled    = ''
        this._view_options_filled   = (False, False, False)
        this._volume_publication_date_filled = ''
        this._volume_version_id_filled       = ''
        this._volume_data_set_ids_filled     = ''
        this._lid_filled                     = ''
        this._lidvid_filled                  = ''
        this._data_set_id_filled             = ''
        this._version_ranks_filled           = []
        this._exact_archive_url_filled       = ''
        this._exact_checksum_url_filled      = ''
        this._filename_keylen_filled         = 0
        this._infoshelf_path_and_key         = ('', '')
        this._is_index                       = False
        this._indexshelf_abspath             = ''

        return this

    def new_index_row_pdsfile(self, filename_key, row_dicts):
        """Return a PdsFile representing the content of one or more rows of this index
        file. Used to enable views of individual rows within large index files.

        Keyword arguments:
            filename_key -- the basename of the PdsFile.
            row_dicts    -- a dictionary contans the row info of the index file.
        """

        this = self.copy()

        this.basename     = filename_key

        _filename_key = '/' + filename_key
        this.abspath      = this.abspath      + _filename_key
        this.logical_path = this.logical_path + _filename_key
        this.interior     = this.interior     + _filename_key

        this._exists_filled         = True
        this._islabel_filled        = False
        this._isdir_filled          = False
        this._split_filled          = (this.basename, '', '')
        this._global_anchor_filled  = None
        this._childnames_filled     = []
        this._childnames_lc_filled  = []
        this._info_filled           = [0, 0, 0, '', (0,0)]
        this._date_filled           = self.date
        this._formatted_size_filled = ''
        this._is_viewable_filled    = False
        this._info_basename_filled  = ''
        this._label_basename_filled = ''
        this._viewset_filled        = False
        this._local_viewset_filled  = False
        this._all_viewsets_filled   = {}
        this._iconset_filled        = None
        this._internal_links_filled = []
        this._mime_type_filled      = 'text/plain'
        this._opus_id_filled        = ''
        this._opus_type_filled      = ''
        this._opus_format_filled    = ''
        this._view_options_filled   = (False, False, False)
        this._volume_info_filled    = self._volume_info
        this._all_version_abspaths  = None
        this._html_path_filled      = None
        this._description_and_icon_filled    = None
        this._volume_publication_date_filled = self.volume_publication_date
        this._volume_version_id_filled       = self.volume_version_id
        this._volume_data_set_ids_filled     = self.volume_data_set_ids
        this._lid_filled                     = ''
        this._lidvid_filled                  = ''
        this._data_set_id_filled             = None
        this._version_ranks_filled           = self.version_ranks
        this._exact_archive_url_filled       = ''
        this._exact_checksum_url_filled      = ''
        this._associated_parallels_filled    = {}
        this._filename_keylen_filled         = 0
        this._infoshelf_path_and_key         = ('', '')
        this._is_index                       = False
        this._indexshelf_abspath             = ''
        this._index_pdslabel                 = None

        this.is_index_row = True
        this.row_dicts = row_dicts
        this.column_names = self.column_names

        # Special attribute just for index rows
        this.parent_basename = self.basename

        return this

    def copy(self):
        cls = type(self)
        this = cls.__new__(cls)

        for (key, value) in self.__dict__.items():
            this.__dict__[key] = value

        return this

    def __repr__(self):
        if self.abspath is None:
            return 'PdsFile-logical("' + self.logical_path + '")'
        elif type(self) == PdsFile:
            return 'PdsFile("' + self.abspath + '")'
        else:
            return ('PdsFile.' + type(self).__name__ + '("' +
                    self.abspath + '")')

    ############################################################################
    # Local implementations of basic filesystem operations
    ############################################################################

    @classmethod
    def _non_checksum_abspath(cls, abspath):
        """Return the non-checksum path associated with this checksum file. If the given
        absolute path does not point to a checksum file, it returns None.

        Keyword arguments:
            abspath -- the absolute path of the checksum file.
        """

        # Checksum files need special handling
        if f'/{cls.PDS_HOLDINGS}/checksums-' in abspath:
            testpath = abspath.replace('/checksums-', '/')

            for voltype in cls.VOLTYPES:
                testpath = testpath.replace('_' + voltype + '_md5.txt', '')

            return testpath

        else:
            return None

    @classmethod
    @functools.lru_cache(maxsize=PATH_EXISTS_CACHE_SIZE)
    def os_path_exists(cls, abspath, force_case_sensitive=False):
        """Return True if the given absolute path points to a file that exists; Return
        False otherwise. This replaces os.path.exists(path) but might use infoshelf
        files rather than refer to the holdings directory.

        Note: This function is case-insensitive under SHELVES_ONLY. Otherwise,
        its behavior matches that of the file system. For Macs, this usually
        means that it is case insensitive. If force_case_sensitive=True, then
        the check of the basename will be case-sensitive regardless of the file
        system.

        Keyword arguments:
            abspath              -- the absolute path of the file.
            force_case_sensitive -- a flag to determine if the basename will be case
                                    sensitive (default False)
        """

        if f'{cls.PDS_HOLDINGS}/_infoshelf' in abspath:
            return os.path.exists(abspath)

        # Handle index rows
        if f'{cls.IDX_EXT}/' in abspath:
            parts = abspath.partition(f'{cls.IDX_EXT}/')
            if not cls.os_path_exists(parts[0] + cls.IDX_EXT):
                return False
            pdsf = cls.from_abspath(parts[0] + cls.IDX_EXT)
            return (pdsf.exists and
                    pdsf.child_of_index(parts[2], flag='').exists)

        # If it's for documentation, we don't create shelf files, we will just use the
        # os.path.exists
        if cls.SHELVES_ONLY and f'{cls.PDS_HOLDINGS}/documents' not in abspath:
            try:
                (shelf_abspath,
                 key) = cls.shelf_path_and_key_for_abspath(abspath, 'info')

                if key:
                    shelf = cls._get_shelf(shelf_abspath,
                                               log_missing_file=False)
                    return (key in shelf)
                elif cls.os_path_exists(shelf_abspath):
                    return True     # Every shelf file has an entry with an
                                    # empty key, so this avoids an unnecessary
                                    # open of the file.
                else:
                    return False
            except (ValueError, IndexError, IOError, OSError):
                pass

            # Maybe it's associated with something else in the infoshelf tree
            if f'/{cls.PDS_HOLDINGS}/' in abspath:

                # Maybe there's an associated directory in the infoshelf tree
                shelf_abspath = abspath.replace(f'/{cls.PDS_HOLDINGS}/',
                                                f'/{cls.PDS_HOLDINGS}/_infoshelf-')
                if cls.os_path_exists(shelf_abspath):
                    return True

                # Maybe there's an associated shelf file in the infoshelf tree
                if cls.os_path_exists(shelf_abspath + '_info.pickle'):
                    return True

                # Checksum files need special handling, before doing special handling,
                testpath = cls._non_checksum_abspath(abspath)
                if testpath and cls.os_path_exists(testpath):
                    return True

        if force_case_sensitive and cls.FS_IS_CASE_INSENSITIVE:
            test = os.path.exists(abspath)
            if not test:
                return False

            (parent,basename) = os.path.split(abspath)
            childnames = os.listdir(parent)
            return (basename in childnames)

        return os.path.exists(abspath)

    @classmethod
    def os_path_isdir(cls, abspath):
        """Return True if the given absolute path points to a directory; Return False
        otherwise. This replaces os.path.isdir() but might use infoshelf files rather
        than refer to the holdings directory.

        Keyword arguments:
            abspath -- the absolute path of a file or a directory.
        """

        if cls.SHELVES_ONLY:
            try:
                (shelf_abspath,
                 key) = cls.shelf_path_and_key_for_abspath(abspath, 'info')

                if key:
                    shelf = cls._get_shelf(shelf_abspath,
                                               log_missing_file=False)
                    (_, _, _, checksum, _) = shelf[key]
                    return (checksum == '')
                elif cls.os_path_exists(shelf_abspath):
                    return True     # Every shelf file has an entry with an
                                    # empty key, so this avoids an unnecessary
                                    # open of the file.
                else:
                    return False
            except (ValueError, IndexError, IOError, OSError):
                pass

            # Maybe it's associated with something else in the infoshelf tree
            if f'/{cls.PDS_HOLDINGS}/' in abspath:

                # Maybe there's an associated directory in the infoshelf tree
                shelf_abspath = abspath.replace(f'/{cls.PDS_HOLDINGS}/',
                                                f'/{cls.PDS_HOLDINGS}/_infoshelf-')
                if os.path.exists(shelf_abspath):
                    return True

                # Maybe there's an associated shelf file in the infoshelf tree
                if os.path.exists(shelf_abspath + '_info.pickle'):
                    return True

                # Checksum files need special handling
                testpath = cls._non_checksum_abspath(abspath)
                if testpath and cls.os_path_exists(testpath):
                    # If the testpath exists, then whether it is a directory or
                    # not depends on the extension
                    return (not abspath.lower().endswith('.txt'))

        return os.path.isdir(abspath)

    @classmethod
    def os_listdir(cls, abspath):
        """Return a list of the file basenames within a directory, given its absolute
        path. This replaces os.listdir() but might use infoshelf files rather than the
        file system.

        Keyword arguments:
            abspath -- the given absolute path.
        """

        # Make sure there is no trailing slash
        abspath = abspath.rstrip('/')

        if cls.SHELVES_ONLY:
            try:
                (shelf_abspath,
                 key) = cls.shelf_path_and_key_for_abspath(abspath, 'info')

                shelf = cls._get_shelf(shelf_abspath,
                                           log_missing_file=False)
            except (ValueError, IndexError, IOError, OSError):
                pass
            else:
                # Look for paths that begin the same and do not have an
                # additional slash
                prefix = key + '/' if key else ''
                lprefix = len(prefix)
                basenames = []
                for key in shelf.keys():
                    if not key.startswith(prefix): continue
                    if key == '': continue
                    basename = key[lprefix:]
                    if '/' not in basename:
                        basenames.append(basename)

                return basenames

            # Deal with checksums-archives directories
            if f'/{cls.PDS_HOLDINGS}/checksums-archives-' in abspath:
                if abspath.endswith('.txt'):
                    return []

                testpath = abspath.replace('/checksums-','/')
                results = cls.os_listdir(testpath)

                for voltype in cls.VOLTYPES:
                    if '-' + voltype in abspath:
                        if voltype == 'volumes':
                            return [r + '_md5.txt' for r in results]
                        else:
                            return [r + '_' + voltype + '_md5.txt' for r in results]

                raise ValueError('Invalid abspath for os_listdir: ' + abspath)

            # Deal with checksums directories
            if f'/{cls.PDS_HOLDINGS}/checksums-' in abspath:
                if abspath.endswith('_md5.txt'):
                    return []

                testpath = abspath.replace('/checksums-','/')
                results = cls.os_listdir(testpath)

                after = abspath.rpartition(f'/{cls.PDS_HOLDINGS}/checksums-')[-1]
                parts = after.split('/')
                if len(parts) == 1:         # category-level call
                    return results

                voltype = parts[0]
                if voltype == 'volumes' or voltype == 'bundles':
                    return [r + '_md5.txt' for r in results]
                else:
                    return [r + '_' + voltype + '_md5.txt' for r in results]

            # Deal with archive directories
            if f'/{cls.PDS_HOLDINGS}/archives-' in abspath:
                if abspath.endswith('.tar.gz'):
                    return []

                testpath = abspath.replace('/archives-','/')
                results = cls.os_listdir(testpath)

                after = abspath.rpartition(f'/{cls.PDS_HOLDINGS}/archives-')[-1]
                parts = after.split('/')
                if len(parts) == 1:         # category-level call
                    return results

                voltype = parts[0]
                if voltype == 'volumes':
                    return [r + '.tar.gz' for r in results]
                else:
                    return [r + '_' + voltype + '.tar.gz' for r in results]

            # Deal with other holdings directories, e.g., holdings/volumes
            if f'/{cls.PDS_HOLDINGS}/' in abspath:

                # Maybe there's an associated directory in the infoshelf tree
                shelf_abspath = abspath.replace(f'/{cls.PDS_HOLDINGS}/',
                                                f'/{cls.PDS_HOLDINGS}/_infoshelf-')
                try:
                    results = os.listdir(shelf_abspath)
                except FileNotFoundError:
                    # If the shelf file is missing, try the actual file system
                    # For documentation, we have all files available but not the shelf
                    # files, therefore we will check the actual file system for documents.
                    childnames = os.listdir(abspath)
                    return [c for c in childnames
                            if c != '.DS_Store' and not c.startswith('._')]

                if not results:
                    return []

                after = abspath.rpartition(f'/{cls.PDS_HOLDINGS}/')[-1]
                parts = after.split('/')
                if len(parts) == 1:         # category-level call
                    return results

                # Isolate unique bundle names from shelf files
                # This prevent duplicated results for _info.py and _info.pickle
                filtered = []
                for result in results:
                    parts = result.split('_info.')
                    if len(parts) == 1: continue

                    bundlename = parts[0]
                    if bundlename not in filtered:
                        filtered.append(bundlename)

                # Check the actual file system for a bundleset-level AAREADME
                aareadmes = []
                for basename in cls.EXTRA_README_BASENAMES:
                    if os.path.exists(abspath + '/' + basename):
                        aareadmes.append(basename)

                return aareadmes + filtered

        childnames = os.listdir(abspath)
        return [c for c in childnames
                if c != '.DS_Store' and not c.startswith('._')]

    @classmethod
    def glob_glob(cls, abspath, force_case_sensitive=False):
        """Return a list of the existing absolute paths. Works the same as glob.glob(),
        but uses shelf files instead of accessing the filesystem directly.

        Note: This function is case-insensitive under SHELVES_ONLY. Otherwise,
        its behavior matches that of the file system. For Macs, this usually
        means that it is case insensitive. If force_case_sensitive=True, then
        file paths will only match if the case is exact.

        Keyword arguments:
            abspath              -- the given absolute path
            force_case_sensitive -- a flag to determine if the filepath will be case
                                    sensitive (default False)
        """

        # We can save a lot of trouble if there's no match pattern
        # This also enables support for index row notation "index.tab/whatever"
        if not _needs_glob(abspath):
            if cls.os_path_exists(abspath, force_case_sensitive):
                return [abspath]
            else:
                return []

        if not cls.SHELVES_ONLY:
            return _clean_glob(cls, abspath, force_case_sensitive)

        # Find the shelf file(s) if any
        abspath = abspath.rstrip('/')
        try:
            (pattern, key) = cls.shelf_path_and_key_for_abspath(abspath, 'info')
        except ValueError:
            # For a category-level holdings dir, this might still work
            if f'/{cls.PDS_HOLDINGS}/' in abspath:
                pattern = abspath.replace(f'/{cls.PDS_HOLDINGS}/',
                                          f'/{cls.PDS_HOLDINGS}/_infoshelf-')
                key = None  # Below, None indicates that we handled this error
            else:
                pattern = ''

        if not pattern:
            shelf_paths = []
        elif _needs_glob(pattern):
            shelf_paths = _clean_glob(cls, pattern)
        elif os.path.exists(pattern):
            shelf_paths = [pattern]
        else:
            shelf_paths = []

        # If there are no exact infoshelf files, revert to the file system
        if not shelf_paths:
            return _clean_glob(cls, abspath, force_case_sensitive)

        # If the check for an exact shelf file failed, just convert the list
        # of shelf/info directories back to holdings directories
        if key is None:
            return [p.replace(f'/{cls.PDS_HOLDINGS}/_infoshelf-', f'/{cls.PDS_HOLDINGS}/')
                    for p in shelf_paths]

        # Gather the matching entries in each shelf
        abspaths = []
        for shelf_path in shelf_paths:
            shelf = cls._get_shelf(shelf_path)
            parts = shelf_path.split(f'/{cls.PDS_HOLDINGS}/_infoshelf-')
            assert len(parts) == 2

            root_ = parts[0] + f'/{cls.PDS_HOLDINGS}/' + parts[1].split('_info.')[0] + '/'

            if _needs_glob(key):
                # Since shelf files are always in alphabetical order, we can
                # use a binary search to figure out where to start comparing
                # strings. This is useful because there can be a lot of
                # paths to search through, and fnmatchcase is slow.
                w1 = key.find('?')
                w2 = key.find('*')
                w3 = key.find('[')
                wildcard_index = len(key)
                if w1 != -1:
                    wildcard_index = w1
                if w2 != -1:
                    wildcard_index = min(wildcard_index, w2)
                if w3 != -1:
                    wildcard_index = min(wildcard_index, w3)
                key_prefix = key[:wildcard_index]
                interior_paths = list(shelf.keys())
                values = list(shelf.values())
                starting_pos = bisect.bisect_left(interior_paths, key_prefix)
                num_key_slashes = len(key.split('/'))
                for (interior_path, value) in zip(
                                interior_paths[starting_pos:],
                                values[starting_pos:]):
                    # If the key prefix doesn't match the interior_path prefix,
                    # then we're done since the filenames are in alphabetical
                    # order.
                    if (key_prefix.upper() !=
                        interior_path[:wildcard_index].upper()):
                        break
                    # Because fnmatch matches strings instead of filesystems,
                    # it has the unfortunate property that match patterns can
                    # accidentally cross directory boundaries. For example, the
                    # pattern "f*r" will match "foo/bar", when it shouldn't. We
                    # handle this by also checking that the returned result
                    # contains the same number of slashes as the pattern.
                    if (fnmatch.fnmatchcase(interior_path, key) and
                        len(interior_path.split('/')) == num_key_slashes):
                            abspaths.append(root_ + interior_path)
            else:
                if key in shelf:
                    abspaths.append(root_ + key)

        # Remove trailing slashes!
        return [p.rstrip('/') for p in abspaths]

    ############################################################################
    # Properties
    ############################################################################

    @property
    def exists(self):
        """Return True if the file exists."""
        cls = type(self)

        if self._exists_filled is not None:
            return self._exists_filled

        if self.is_merged: # pragma: no cover
            self._exists_filled = True
        elif self.abspath is None:
            self._exists_filled = False
        else:
            self._exists_filled = cls.os_path_exists(self.abspath)

        self._recache()
        return self._exists_filled

    @property
    def isdir(self):
        """Return True if the file is a directory."""

        cls = type(self)

        if self._isdir_filled is not None:
            return self._isdir_filled

        if self.is_merged: # pragma: no cover
            self._isdir_filled = True
        elif self.abspath is None:
            self._isdir_filled = False
        else:
            self._isdir_filled = cls.os_path_isdir(self.abspath)

        self._recache()
        return self._isdir_filled

    @property
    def is_documents(self):
        """Return True if the file is under documents directory."""

        return self.voltype_ == 'documents/'

    @property
    def filespec(self):
        """Return bundlename or bundlename/interior."""

        if self.interior:
            return self.bundlename_ + self.interior
        else:
            return self.bundlename

    @property
    def absolute_or_logical_path(self):
        """Return the absolute path if this has one; otherwise the logical path."""

        if self.abspath:
            return self.abspath
        else:
            return self.logical_path

    @property
    def islabel(self):
        """Return True if the file is a PDS3 label; deprecated name."""

        if self._islabel_filled is not None:
            return self._islabel_filled

        self._islabel_filled = self.basename_is_label(self.basename)

        self._recache()
        return self._islabel_filled

    @property
    def is_label(self):
        """Return True if the file is a PDS3 label; alternative name for islabel."""

        return self.islabel

    @property
    def is_viewable(self):
        """Return True if the file is viewable. Examples of viewable files are JPEGs,
        TIFFs, PNGs, etc.
        """

        if self._is_viewable_filled is not None:
            return self._is_viewable_filled

        self._is_viewable_filled = self.basename_is_viewable(self.basename)

        self._recache()
        return self._is_viewable_filled

    @property
    def html_path(self):
        """Return the URL to this file after the domain name, starting with "/holdings";
        alias for property "url".
        """

        if self._html_path_filled is not None:
            return self._html_path_filled

        # For a merged directory, return the first physical path. Not a great
        # solution but it usually works. This issue will probably never come up.
        if self.abspath is None:
            child_html_path = self.child(self.childnames[0]).html_path
            self._html_path_filled = child_html_path.rpartition('/')[0]

        # For a link file, the internal content is the URL
        elif self.abspath.endswith('.link'):
            try:
                with open(self.abspath, encoding='latin-1') as f:
                    self._html_path_filled = f.read().strip()
            except IOError:
                self._html_path_filled = self.html_root_ + self.logical_path
        else:
            self._html_path_filled = self.html_root_ + self.logical_path

        self._recache
        return self._html_path_filled

    @property
    def url(self):
        """Return the URL to this file after the domain name, starting with "/holdings".
        """

        return self.html_path

    @property
    def split(self):
        """Return (anchor, suffix, extension)"""

        if self._split_filled is not None:
            return self._split_filled

        self._split_filled = self.split_basename()

        self._recache()
        return self._split_filled

    @property
    def anchor(self):
        """Return the anchor for this object. Objects with the same anchor are grouped
        together in the same row of a Viewmaster table.
        """

        # We need a better anchor for index row PdsFiles
        if self.is_index_row:
            return self.parent().split[0] + '-' + self.split[0]

        return self.split[0]

    @property
    def global_anchor(self):
        """Return the global anchor is a unique string across all data products and
        is suitable for use in HTML pages.
        """

        if self._global_anchor_filled is not None:
            return self._global_anchor_filled

        path = self.parent_logical_path + '/' + self.anchor
        self._global_anchor_filled = path.replace('/', '-')

        self._recache()
        return self._global_anchor_filled

    @property
    def extension(self):
        """Return the extension of this file, after the first dot."""

        return self.split[2]

    @property
    def indexshelf_abspath(self):
        """Return the absolute path to the indexshelf file if this is an index file;
        blank otherwise.
        """

        cls = type(self)
        if self._indexshelf_abspath is None:
            if self.extension not in (cls.IDX_EXT, cls.IDX_EXT.upper()):
                self._indexshelf_abspath = ''
            else:
                abspath = self.abspath
                abspath = abspath.replace(f'/{cls.PDS_HOLDINGS}/',
                                          f'/{cls.PDS_HOLDINGS}/_indexshelf-')
                abspath = abspath.replace(cls.IDX_EXT, '.pickle')
                abspath = abspath.replace(cls.IDX_EXT.upper(), '.pickle')
                self._indexshelf_abspath = abspath

            self._recache()

        return self._indexshelf_abspath

    @property
    def is_index(self):
        """Return True if this is an index file. An index file is recognized by the
        presence of the corresponding indexshelf file.
        """

        cls = type(self)
        if self._is_index is None:
            abspath = self.indexshelf_abspath
            if abspath and os.path.exists(abspath):
                self._is_index = True
            else:
                # Second try: it's in the metadata tree and ends in .tab
                # This supports the temporary situation where the indexshelf
                # file is being created.
                # XXX This is a real hack and should be looked at again later
                if ('/metadata/' in self.abspath
                    and self.abspath.lower().endswith(cls.IDX_EXT)):
                    return True  # this value is not cached

                self._is_index = False

            self._recache()

        return self._is_index

    @property
    def index_pdslabel(self):
        """Return the parsed PdsLabel associated with the label of an index."""

        if not self.is_index:
            return None

        cls = type(self)
        if self._index_pdslabel is None:
            label_abspath = self.abspath.replace (cls.IDX_EXT, cls.LBL_EXT)
            label_abspath = label_abspath.replace(cls.IDX_EXT.upper(),
                                                  cls.LBL_EXT.upper())
            try:
              self._index_pdslabel = pdsparser.PdsLabel.from_file(label_abspath)
            except:
              self._index_pdslabel = 'failed'

            self._recache()

        if self._index_pdslabel == 'failed':
            return None

        return self._index_pdslabel

    @property
    def childnames(self):
        """Return a list of all the child names if this is a directory or an index.
        Names are kept in sorted order.
        """

        cls = type(self)

        if self._childnames_filled is not None:
            return self._childnames_filled

        self._childnames_filled = []
        if self.isdir and self.abspath:
            childnames = cls.os_listdir(self.abspath)

            # Save child names in default order
            self._childnames_filled = self.sort_basenames(childnames,
                                                          labels_after=False,
                                                          dirs_first=False,
                                                          dirs_last=False,
                                                          info_first=False)

        # Support for table row views as "children" of index tables
        if self.is_index:
            shelf = self.get_indexshelf()
            childnames = list(shelf.keys())
            self._childnames_filled = self.sort_basenames(childnames)

        self._recache()
        return self._childnames_filled

    @property
    def childnames_lc(self):
        """Return a list of all the child names if this is a directory or an index.
        Names are kept in sorted order. In this version all names are lower case.
        """

        if self._childnames_lc_filled is None:
            self._childnames_lc_filled = [c.lower() for c in self.childnames]
            self._recache()

        return self._childnames_lc_filled

    @property
    def parent_logical_path(self):
        """Return a safe way to get the logical_path of the parent; works for merged
        directories when parent is None.
        """

        parent = self.parent()

        if self.parent() is None:
            return ''
        else:
            return parent.logical_path

    @property
    def _info(self):
        """Return the info from the info shelf file."""

        if self._info_filled is not None:
            return self._info_filled

        cls = type(self)

        # Missing files get no _info
        if not self.exists:
            self._info_filled = (0, 0, None, '', (0,0))
            self._recache()
            return self._info_filled

        # Attempt to return the info from a shelf file
        if self.info_shelf_expected:
            try:
                (file_bytes, child_count,
                 timestring, checksum, size) = self.shelf_lookup('info')
            except (IOError, KeyError, ValueError):
                cls.LOGGER.warn('Missing info shelf', self.abspath)
                if cls.SHELVES_REQUIRED:
                    raise
            else:
                # Note that timestring will be blank for empty directories and
                # for directories containing only empty directories
                if timestring:
                    # Interpret the modtime
                    yr = int(timestring[ 0:4])
                    mo = int(timestring[ 5:7])
                    da = int(timestring[ 8:10])
                    hr = int(timestring[11:13])
                    mi = int(timestring[14:16])
                    sc = int(timestring[17:19])
                    ms = int(timestring[20:])
                    modtime = datetime.datetime(yr, mo, da, hr, mi, sc, ms)
                else:
                    modtime = None

                # A missing checksum is sometimes represented by dashes
                if checksum and checksum[0] == '-':
                    checksum = ''

                self._info_filled = (file_bytes, child_count, modtime,
                                     checksum, size)
                self._recache()
                return self._info_filled

        # Get info for a single file directly from the file system. This will
        # occur for documents and bundleset-level AAREADME files.
        if not self.isdir:

            file_bytes = os.path.getsize(self.abspath)
            timestamp = os.path.getmtime(self.abspath)
            modtime = datetime.datetime.fromtimestamp(timestamp)

            if self.basename_is_viewable():
                # "TBD" indicates that info should be filled in by properties
                # height & width, if requested.
                shape = (0,0,'TBD')
            else:
                shape = (0,0)

            self._info_filled = (file_bytes, 0, modtime, '', shape)
            self._recache()
            return self._info_filled

        # Sum up the info for bundleset-level directories
        elif self.is_bundleset_dir:

            child_count = len(self.childnames)
            latest_modtime = datetime.datetime.min
            total_bytes = 0
            for bundlename in self.childnames:

                # Ignore AAREADME files in this context
                if bundlename in cls.EXTRA_README_BASENAMES:
                    child_count -= 1
                    continue

                try:
                    (file_bytes, _,
                     timestring, _, _) = self.shelf_lookup('info', bundlename)
                except IOError:     # Shelf file for bundlename is missing--maybe
                                    # it's not a bundle name after all
                    file_bytes = os.path.getsize(self.abspath)
                    timestamp = os.path.getmtime(self.abspath)
                    modtime = datetime.datetime.fromtimestamp(timestamp)
                else:
                    # Without this check, we get an error for empty directories
                    if timestring == '' or file_bytes == 0: continue

                    # Convert formatted time to datetime
                    yr = int(timestring[ 0: 4])
                    mo = int(timestring[ 5: 7])
                    da = int(timestring[ 8:10])
                    hr = int(timestring[11:13])
                    mi = int(timestring[14:16])
                    sc = int(timestring[17:19])
                    ms = int(timestring[20:  ])
                    modtime = datetime.datetime(yr, mo, da, hr, mi, sc, ms)

                latest_modtime = max(modtime, latest_modtime)
                total_bytes += file_bytes

            # If no modtimes were found. Shouldn't happen but worth checking.
            if latest_modtime == datetime.datetime.min:
                latest_modtime = None

            self._info_filled = (total_bytes, child_count,
                                 latest_modtime, '', (0,0))

        else:
            self._info_filled = (0, 0, None, '', (0,0))

        self._recache()
        return self._info_filled

    @property
    def size_bytes(self):
        """Return the size in bytes represented as an int."""

        return self._info[0]

    @property
    def modtime(self):
        """Return Datetime object representing this file's modification date."""

        return self._info[2]

    @property
    def checksum(self):
        """Return MD5 checksum of this file."""

        return self._volume_info[5] or self._info[3]

    @property
    def width(self):
        """Return the width of this image in pixels if it is viewable."""

        self._repair_width_height()
        return self._info[4][0]

    @property
    def height(self):
        """Return the height of this image in pixels if it is viewable."""

        self._repair_width_height()
        return self._info[4][1]

    def _repair_width_height(self):
        """Internal function to fill in the shape of viewables, if needed."""
        cls = type(self)

        if len(self._info[4]) > 2:      # (0,0,'TBD') means fill in the size now

            cls.LOGGER.warn('Retrieving viewable shape', self.abspath)
            try:
                im = PIL.Image.open(self.abspath)
                shape = im.size
                im.close()
            except Exception:
                shape = (0,0)

            self._info_filled = self._info[:4] + (shape,)
            self._recache()

    @property
    def alt(self):
        """Return the webpage alt tag to use if this is a viewable object."""

        return self.basename

    @property
    def date(self):
        """Return the modification date/time of this file as a well-formatted string;
        otherwise blank.
        """

        if self._date_filled is None:
            if self.modtime:
                self._date_filled = self.modtime.strftime('%Y-%m-%d %H:%M:%S')
            else:
                self._date_filled = ''

            self._recache()

        return self._date_filled

    @property
    def formatted_size(self):
        """Return the size of this file as a formatted string, e.g., "2.16 MB"."""

        if self._formatted_size_filled is None:
          if self.size_bytes:
            self._formatted_size_filled = formatted_file_size(self.size_bytes)
          else:
            self._formatted_size_filled = ''

          self._recache()

        return self._formatted_size_filled

    @property
    def _volume_info(self):
        """Return the information about this volume, volset, or product as retrieved from
        a table in the volinfo/ directory. Returned tuple is (description, icon_type,
        volume_date, list of data_set_ids, optional checksum].
        """

        cls = type(self)

        if self._volume_info_filled is None:

            base_key = self.bundleset + self.suffix
            if self.bundlename:
                base_key += '/' + self.bundlename

            # Try lookup with and without voltype
            base_key = base_key.lower()
            keys = (self.logical_path.lower(),)
            if self.voltype_ != 'documents/':
                keys += (self.voltype_ + base_key, base_key)

            for key in keys:
                try:
                    self._volume_info_filled = cls.CACHE['$VOLINFO-' + key]
                    break
                except (KeyError, TypeError):
                    pass

            if self._volume_info_filled is None:
                self._volume_info_filled = ('', 'UNKNOWN', '', '', [], '')

            self._recache()

        return self._volume_info_filled

    @property
    def description(self):
        """Return the description text about this file as it appears in Viewmaster."""

        cls = type(self)

        if self._description_and_icon_filled is not None:
            return self._description_and_icon_filled[0]

        # Index row objects always use the same description and icon_type
        if self.is_index_row:
            if len(self.row_dicts) == 1:
                pair = ('Selected row of index', 'INFO')
            else:
                pair = ('Selected rows of index', 'INFO')

        # Bundles and bundlesets get their descriptions from the $VOLINFO cache
        elif self.is_bundleset or self.is_bundle:
            (desc, icon_type) = self._volume_info[:2]

            # Munge the descriptions of bundleset-level directories, if necessary,
            # based on volume type. Example: This changes "Cassini data" to
            # "Previews of Cassini data" for preview data.
            desc_lc = desc.lower()
            if self.voltype_ == 'calibrated/' and 'calib' not in desc_lc:
                desc = 'Calibrated ' + desc
            elif self.voltype_ == 'diagrams/' and 'diagram' not in desc_lc:
                desc = 'Diagrams for ' + desc
            elif self.voltype_ == 'previews/' and 'preview' not in desc_lc:
                desc = 'Previews of ' + desc
            elif self.voltype_ == 'metadata/' and 'metadata' not in desc_lc:
                desc = 'Metadata for ' + desc

            # Fill in missing icon types
            if (icon_type is None and
                self.basename not in cls.EXTRA_README_BASENAMES):
                    key = (self.category_, self.is_bundleset)
                    icon_type = cls.DEFAULT_HIGH_LEVEL_ICONS.get(key, None)

            if icon_type is None:
                pair = self.DESCRIPTION_AND_ICON.first(self.logical_path)
                icon_type = pair[1]

            pair = (desc, icon_type)

        # Descriptions of one-off files might be found in a volinfo file;
        # otherwise, use the rules.
        else:
            try:
                info = cls.CACHE['$VOLINFO-' + self.logical_path.lower()]
                pair = (info[0], info[1])
            except KeyError:
                pair = self.DESCRIPTION_AND_ICON.first(self.logical_path)

        self._description_and_icon_filled = pair

        self._recache()
        return self._description_and_icon_filled[0]

    @property
    def icon_type(self):
        """Return the icon type for this file."""

        _ = self.description
        return self._description_and_icon_filled[1]

    @property
    def mime_type(self):
        """Return a best guess at the MIME type for this file. Blank for not displayable
        in a browser.
        """

        if self._mime_type_filled is not None:
            return self._mime_type_filled

        cls = type(self)

        ext = self.extension[1:].lower()

        if self.isdir:
            self._mime_type_filled = ''
        elif ext in cls.PLAIN_TEXT_EXTS:
            self._mime_type_filled = 'text/plain'
        elif ext in cls.MIME_TYPES_VS_EXT:
            self._mime_type_filled = cls.MIME_TYPES_VS_EXT[ext]
        else:
            self._mime_type_filled = ''

        self._recache()
        return self._mime_type_filled

    @property
    def opus_id(self):
        """Return the OPUS ID of this product if it has one; otherwise an empty string.
        """

        if self._opus_id_filled is None:
            self._opus_id_filled = self.OPUS_ID.first(self.logical_path) or ''
            self._recache()

        return self._opus_id_filled

    @property
    def opus_format(self):
        """Return the OPUS format of this product, e.g., ('ASCII', 'Table') or
        ('Binary', 'FITS').
        """

        if self._opus_format_filled is None:
            self._opus_format_filled = self.OPUS_FORMAT.first(self.logical_path)
            self._recache()

        return self._opus_format_filled

    @property
    def opus_type(self):
        """Return the OPUS type of this product, returned as a tuple: (dataset name,
        priority (where lower comes first), type ID, description)
        If no OPUS type exists, it returns ''

        Examples:
            ('Cassini ISS',   0, 'coiss_raw',  'Raw Image')
            ('Cassini ISS', 130, 'coiss_full', 'Extra preview (full-size)')
        """

        if self._opus_type_filled is None:
            self._opus_type_filled = (self.OPUS_TYPE.first(self.logical_path)
                                      or '')
            self._recache()

        return self._opus_type_filled

    @property
    def data_set_id(self):
        """Return the PDS3 DATA_SET_ID for the file, if it has one; otherwise, blank."""

        if self._data_set_id_filled is not None:
            return self._data_set_id_filled

        # If the volume has no data set id, return ''
        if len(self.volume_data_set_ids) == 0:
            self._data_set_id_filled = ''

        # If the volume has just one, this is it
        elif len(self.volume_data_set_ids) == 1:
            self._data_set_id_filled = self.volume_data_set_ids[0]

        # If the volume has more than one, we need the rule
        else:
            if callable(self.DATA_SET_ID):
                self._data_set_id_filled = self.DATA_SET_ID()
            else:
                self._data_set_id_filled = self.DATA_SET_ID.first(
                                                            self.logical_path)

            if self._data_set_id_filled is None:
                self._data_set_id_filled = ''

        self._recache()
        return self._data_set_id_filled

    @property
    def lid(self):
        """Return the LID for data files under volumes directory. If the volume
        has no LID, it returns ''.

        Format:
        dataset_id:volume_id:directory_path:file_name

        Examples:
        'volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/
        N1460960653_1.IMG'
        -> 'CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2002:data/1460960653_1461048959:
            N1460960653_1.IMG'

        'volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/
        N1460960653_1.LBL'
        -> 'CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2002:data/1460960653_1461048959:
            N1460960653_1.LBL'

        'volumes/COISS_2xxx/COISS_2008/extras/full/1477675247_1477737486/
        N1477691357_1.IMG.png'
        -> 'CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2008:
            extras/full/1477675247_1477737486:N1477691357_1.IMG.png'
        """

        if self._lid_filled is not None:
            return self._lid_filled

        lid_after_data_set_id = self.LID_AFTER_DSID.first(self.logical_path)
        # only the latest versions of PDS3 volumes have LIDs
        if (lid_after_data_set_id and self.data_set_id and
            not self.suffix and self.category_ == 'volumes/'):
            self._lid_filled = self.data_set_id + ':' + lid_after_data_set_id
        else:
            self._lid_filled = ''

        self._recache()
        return self._lid_filled

    @property
    def lidvid(self):
        """Return the LIDVID for data files under volumes directory. If the
        volume has no LID, it returns ''.

        Format:
        dataset_id:volume_id:directory_path:file_name::vid

        Examples:
        'volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/
        N1460960653_1.IMG'
        -> 'CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2002:data/1460960653_1461048959:
            N1460960653_1.IMG::1.0'

        'volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/
        N1460960653_1.LBL'
        -> 'CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2002:data/1460960653_1461048959:
            N1460960653_1.LBL::1.0'

        'volumes/COISS_2xxx/COISS_2008/extras/full/1477675247_1477737486/
        N1477691357_1.IMG.png'
        -> 'CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2008:
            extras/full/1477675247_1477737486:N1477691357_1.IMG.png::1.0'
        """

        if self._lidvid_filled is not None:
            return self._lidvid_filled

        if self.lid:
            # only the last PDS3 version of a product will have a LID.
            self._lidvid_filled = self.lid + "::1.0"
        else:
            self._lidvid_filled = ''

        self._recache()
        return self._lidvid_filled


    @property
    def info_basename(self):
        """Return the basename of an informational file associated with this PdsFile
        object. This could be a file like "VOLDESC.CAT", "CATINFO.TXT", or the label file
        associated with a data product.
        """

        cls = type(self)

        if self._info_basename_filled is not None:
            return self._info_basename_filled

        # Search based on rules
        self._info_basename_filled = \
            self.INFO_FILE_BASENAMES.first(self.childnames)

        # On failure, try the local label
        if not self._info_basename_filled:

            if self.islabel:
                self._info_basename_filled = self.basename

            elif self.label_basename:
                self._info_basename_filled = self.label_basename

        # On failure, look for a bundle set-level AAREADME file
        # Note that this requires a physical check of the bundles tree because
        # these files do not appear in infoshelf files.
        if not self._info_basename_filled and self.is_bundle_dir:
            for info_name in cls.EXTRA_README_BASENAMES:
                if os.path.exists(self.abspath + '/../' + info_name):
                    self._info_basename_filled = info_name

        # Otherwise, there is no info file so change None to ''
        if not self._info_basename_filled:
            self._info_basename_filled = ''

        self._recache()
        return self._info_basename_filled

    @property
    def internal_link_info(self):
        """Return a list of tuples [(recno, basename, abspath), ...], or else the abspath
        of the label for this file.
        """

        if self._internal_links_filled is not None:
            return self._internal_links_filled

        cls = type(self)

        # Some file types never have links
        if self.isdir or self.checksums_ or self.archives_:
            self._internal_links_filled = []

        elif self.voltype_ not in ('volumes/', 'calibrated/', 'metadata/'):
            self._internal_links_filled = []

        # Otherwise, look up the info in the shelf file
        else:
            try:
                values = self.shelf_lookup('link')

            # Shelf file failure
            except (IOError, KeyError, ValueError) as e:

                # This can happen for bundleset-level AAREADME files.
                # Otherwise, it's an error
                if not (self.parent().is_bundleset_dir and
                        self.basename in cls.EXTRA_README_BASENAMES):

                    self._internal_links_filled = ()
                        # An empty _tuple_ indicates that link info is missing
                        # because of a shelf file failure; an empty _list_
                        # object means that the file simply contains no links.
                        # This distinction is there if we ever care.

                    cls.LOGGER.warn('Missing link shelf', self.abspath)

                    if cls.SHELVES_REQUIRED:
                        raise

                else:       # bundleset AAREADME file
                    self._internal_links_filled = []

            else:
                volume_path_ = self.volume_abspath() + '/'

                # A string value means that this is actually the abspath of this
                # file's external PDS label
                if isinstance(values, str):
                    if values:
                        self._internal_links_filled = volume_path_ + values
                    else:
                        self._internal_links_filled = []

                # A list value indicates that each value is a tuple:
                #   (recno, basename, internal_path)
                # The tuple indicates that this label file contains an external
                # link in line <recno>. The occurrence of string <basename> is
                # actually a link to a file with the path <internal_path>.
                # There is one tuple for each internal link in the label file.
                else:
                    new_list = []
                    for (recno, basename, internal_path) in values:
                      if internal_path.startswith('../../../'):
                        abspath = abspath_for_logical_path(internal_path[9:], cls)
                      elif internal_path.startswith('../../'):
                        abspath = abspath_for_logical_path(self.category_ +
                                                           internal_path[6:], cls)
                      elif internal_path.startswith('../'):
                        abspath = (self.volset_abspath() + internal_path[2:])
                      else:
                        abspath = volume_path_ + internal_path
                      new_list.append((recno, basename, abspath))
                    self._internal_links_filled = new_list

        self._recache()
        return self._internal_links_filled

    @property
    def linked_abspaths(self):
        """Return a list of absolute paths linked to this PdsFile. Linked files are those
        whose name appears somewhere in the file, e.g., by being referenced in a label or
        cited in a documentation file.
        """

        cls = type(self)

        # Links from this file
        if not isinstance(self.internal_link_info, str):
            abspaths = []
            for (_, _, abspath) in self.internal_link_info:
                if abspath not in abspaths:
                    abspaths.append(abspath)

            if self.abspath in abspaths:            # don't include self
                abspaths.remove(self.abspath)

            return abspaths

        # Links from the label of this if this isn't a label
        if self.label_abspath:
            label_pdsf = cls.from_abspath(self.label_abspath)
            return label_pdsf.linked_abspaths

        return []

    @property
    def label_basename(self):
        """Return the basename of the label file associated with this data file. If this
        is already a label file, it returns an empty string.
        """
        cls = type(self)

        # Return cached value if any
        if self._label_basename_filled is not None:
            return self._label_basename_filled

        # Label files have no labels
        if self.islabel:
            self._label_basename_filled = ''
            self._recache()
            return ''

        # Take a first guess at the label filename; PDS3 only!
        if self.extension.isupper():
            ext_guesses = (cls.LBL_EXT.upper(), cls.LBL_EXT)
        else:
            ext_guesses = (cls.LBL_EXT, cls.LBL_EXT.upper())

        rootname = self.basename[:-len(self.extension)]
        test_basenames = [rootname + ext for ext in ext_guesses]

        # If one of the guessed files exist, it's the label
        for test_basename in test_basenames:
            test_abspath = self.abspath.rpartition('/')[0] + '/' + test_basename
            if cls.os_path_exists(test_abspath, force_case_sensitive=True):
                self._label_basename_filled = test_basename
                self._recache()
                return self._label_basename_filled

        # If this file doesn't exist, then it's OK to return a nonexistent
        # label basename. Do we really care?
        if not self.exists:
            if self.extension.lower() in ('.fmt', '.cat', '.txt'):
                self._label_basename_filled = ''
            else:
                self._label_basename_filled = test_basenames[0]
            self._recache()
            return self._label_basename_filled

        # Otherwise, check the link shelf
        link_info = self.internal_link_info
        if isinstance(link_info, str):
            self._label_basename_filled = os.path.basename(link_info)
        else:
            self._label_basename_filled = ''

        self._recache()
        return self._label_basename_filled

    @property
    def label_abspath(self):
        """Return the absolute path to the label if it exists; blank otherwise."""

        if self.label_basename:
            parent_path = os.path.split(self.abspath)[0]
            return parent_path + '/' + self.label_basename
        else:
            return ''

    @property
    def data_abspaths(self):
        """Return a list of the targets of a label file; otherwise []."""

        if not self.islabel: return []
        cls = type(self)
        # We know this is the target of a link if it is linked by this label and
        # also target's label is this file. It's complicated.
        label_basename_lc = self.basename.lower()
        linked = self.linked_abspaths
        abspaths = []
        for abspath in linked:
            target_pdsf = cls.from_abspath(abspath)
            if target_pdsf.label_basename.lower() == label_basename_lc:
                abspaths.append(abspath)

        return abspaths

    @property
    def viewset(self):
        """Return PdsViewSet to use for this object."""

        if self._viewset_filled is not None:
            return self._viewset_filled

        # Don't look for PdsViewSets at bundle root; saves time
        if (self.exists and self.bundlename_ and
            not self.archives_ and not self.checksums_ and self.interior):
                self._viewset_filled = self.viewset_lookup('default')

        if self._viewset_filled is None:
            self._viewset_filled = False

        self._recache()
        return self._viewset_filled

    @property
    def local_viewset(self):
        """Return PdsViewSet for this object if it is itself viewable; otherwise False.
        """

        if self._local_viewset_filled is not None:
            return self._local_viewset_filled

        if self.exists and self.basename_is_viewable():
            self._local_viewset_filled = \
                            pdsviewable.PdsViewSet.from_pdsfiles(self)
        else:
            self._local_viewset_filled = False

        self._recache()
        return self._local_viewset_filled

    @property
    def all_viewsets(self):
        """Return a dictionary of every available PdsViewSet for this object."""

        if self._all_viewsets_filled is None:

            viewset_dict = {}

            if self.isdir:
                if self.viewset:
                    viewset_dict['default'] = self.viewset

                # Get viewables for this directory
                for key in self.VIEWABLES:
                    if key != 'default':
                        viewset = self.viewset_lookup(key)
                        if viewset:
                            viewset_dict[key] = viewset

                # Add the unique viewset names of the non-directory children
                for c in self.childnames[:20]:  # first 20 should be enough
                    child = self.child(c)
                    if child.isdir:
                        continue
                    for key in child.VIEWABLES:
                        if key not in viewset_dict and key != 'default':
                            viewset = child.viewset_lookup(key)
                            if viewset:
                                viewset_dict[key] = viewset

            # Otherwise, include every defined viewset starting with "default"
            else:
                if self.local_viewset:
                    viewset_dict['default'] = self.local_viewset
                elif self.viewset:
                    viewset_dict['default'] = self.viewset

                for key in self.VIEWABLES:
                    if key != 'default':
                        viewset = self.viewset_lookup(key)
                        if viewset:
                            viewset_dict[key] = viewset

            self._all_viewsets_filled = viewset_dict
            self._recache()

        return self._all_viewsets_filled

    @property
    def _iconset(self):
        """Return the PdsViewSet for this object's icon whether it is to be displayed
        in a closed or open state.
        """

        if self._iconset_filled is not None:
            return self._iconset_filled[0]

        self._iconset_filled = [
                    pdsviewable.ICON_SET_BY_TYPE[self.icon_type, False],
                    pdsviewable.ICON_SET_BY_TYPE[self.icon_type, True ]]

        self._recache()
        return self._iconset_filled[0]

    @property
    def iconset_open(self):
        """Return PdsViewSet for this object's icon if displayed in an open state."""

        _ = self._iconset
        return self._iconset_filled[1]

    @property
    def iconset_closed(self):
        """Return PdsViewSet for this object's icon if displayed in a closed state."""

        _ = self._iconset
        return self._iconset_filled[0]

    @property
    def volume_publication_date(self):
        """Return the publication date for this volume as a formatted string."""

        if self._volume_publication_date_filled is not None:
            return self._volume_publication_date_filled

        date = self._volume_info[3]
        if date is None:
            return ''

        if date == '':
            try:
                date = self.volume_pdsfile().date[:10]
            except (ValueError, AttributeError):
                pass

        if date == '':
            try:
                date = self.volset_pdsfile().date[:10]
            except (ValueError, AttributeError):
                pass

        if date == '':
            try:
                date = self.date[:10]
            except (ValueError, AttributeError):
                pass

        self._volume_publication_date_filled = date

        self._recache()
        return self._volume_publication_date_filled

    @property
    def volume_version_id(self):
        """Return version ID of this volume."""

        if self._volume_version_id_filled is None:
            if self._volume_info[2] is None:
                self._volume_version_id_filled = ''
            else:
                self._volume_version_id_filled = self._volume_info[2]

            self._recache()

        return self._volume_version_id_filled

    @property
    def volume_data_set_ids(self):
        """Return a list of the dataset IDs found in this volume."""

        if self._volume_data_set_ids_filled is None:
            self._volume_data_set_ids_filled = self._volume_info[4]
            self._recache()

        return self._volume_data_set_ids_filled

    @property
    def version_ranks(self):
        """Return a list of the numeric version ranks associated with the volume on
        which this file resides.

        This is an integer that always sorts versions from oldest to newest.
        """

        if self._version_ranks_filled is not None:
            return self._version_ranks_filled

        cls = type(self)

        if not self.exists:
            version_ranks_filled = []
        else:
            try:
                ranks = cls.CACHE['$RANKS-' + self.category_]

            except KeyError:
                cls.LOGGER.warn('Missing rank info', self.logical_path)
                self._version_ranks_filled = []

            else:
                if self.bundlename:
                    key = self.bundlename.lower()
                    self._version_ranks_filled = ranks[key]

                elif self.bundleset:
                    key = self.bundleset.lower()
                    self._version_ranks_filled = ranks[key]

                else:
                    self._version_ranks_filled = []

        self._recache()
        return self._version_ranks_filled

    @property
    def exact_archive_url(self):
        """Return the URL of an archive file if that archive contains the exact contents
        of this directory tree. Otherwise return blank.
        """

        cls = type(self)

        if self._exact_archive_url_filled is not None:
            return self._exact_archive_url_filled

        if not self.exists:
            self._exact_archive_url_filled = ''

        else:
            abspath = self.archive_path_if_exact()
            if abspath:
                pdsf = cls.from_abspath(abspath)
                self._exact_archive_url_filled = pdsf.url
            else:
                self._exact_archive_url_filled = ''

        self._recache()
        return self._exact_archive_url_filled

    @property
    def exact_checksum_url(self):
        """Return the URL of a checksum file if that checksum contains the exact contents
        of this directory tree. Otherwise return blank.
        """

        if self._exact_checksum_url_filled is not None:
            return self._exact_checksum_url_filled

        cls = type(self)

        if not self.exists:
            self._exact_checksum_url_filled = ''

        else:
            abspath = self.checksum_path_if_exact()
            if abspath:
                pdsf = cls.from_abspath(abspath)
                self._exact_checksum_url_filled = pdsf.url
            else:
                self._exact_checksum_url_filled = ''

        self._recache()
        return self._exact_checksum_url_filled

    @property
    def grid_view_allowed(self):
        """Return True if this directory can be viewed as a grid inside Viewmaster."""

        if self._view_options_filled is not None:
            return self._view_options_filled[0]

        if not self.exists:
            self._view_options_filled = (False, False, False)

        elif self.isdir:
            self._view_options_filled = \
                                self.VIEW_OPTIONS.first(self.logical_path)
        else:
            self._view_options_filled = (False, False, False)

        self._recache()
        return self._view_options_filled[0]

    @property
    def multipage_view_allowed(self):
        """Return True if a multipage view starting from this directory is allowed
        inside Viewmaster.
        """

        _ = self.grid_view_allowed

        return self._view_options_filled[1]

    @property
    def continuous_view_allowed(self):
        """Return True if a continuous view of multiple directories starting from this
        one is allowed inside Viewmaster.
        """

        _ = self.grid_view_allowed

        return self._view_options_filled[2]

    @property
    def has_neighbor_rule(self):
        """Return True if a neighbor rule is available to go to the object just before
        or just after this one.
        """

        parent = self.parent()
        return bool(parent and self.NEIGHBORS.first(parent.logical_path))

    @property
    def filename_keylen(self):
        """Return the length of the keys used to select the rows of an index file."""

        if self._filename_keylen_filled is None:
            if isinstance(self.FILENAME_KEYLEN, int):
                self._filename_keylen_filled = self.FILENAME_KEYLEN
            else:
                self._filename_keylen_filled = self.FILENAME_KEYLEN()

        return self._filename_keylen_filled

    @property
    def infoshelf_path_and_key(self):
        """Return The absolute path to the associated info shelf file, if any, and the
        key to use within that file. If the shelf info does not exist, return a pair of
        empty strings.
        """

        cls = type(self)

        if self._infoshelf_path_and_key is None:
            try:
                self._infoshelf_path_and_key = \
                    cls.shelf_path_and_key_for_abspath(self.abspath, 'info')
            except:
                self._infoshelf_path_and_key = ('', '')

            self._recache()

        return self._infoshelf_path_and_key

    LATEST_VERSION_RANKS = [990100, 990200, 990300, 990400, 999999]

    @staticmethod
    def version_info(suffix):
        """Return a tuple of version info (version rank, version message, version id).
        This is the Procedure to associate a volset suffix with a version rank value.

        Keyword arguments:
            suffix -- a volset suffix
        """

        version_id = ''
        if suffix == '':
            version_message = 'Current version'
            version_rank = 999999
        elif suffix == '_in_prep':
            version_message = 'In preparation'
            version_rank = 990100
        elif suffix == '_prelim':
            version_message = 'Preliminary release'
            version_rank = 990200
        elif suffix == '_peer_review':
            version_message = 'In peer review'
            version_rank = 990300
        elif suffix == '_lien_resolution':
            version_message = 'In lien resolution'
            version_rank = 990400

        elif suffix.startswith('_v'):
            version_message = 'Version ' + suffix[2:] + ' (superseded)'

            # Version ranks:
            #   _v2 -> 20000
            #   _v2.1 -> 201000
            #   _v2.1.3 -> 201030
            subparts = suffix[2:].split('.')
            version_rank = int(subparts[0]) * 10000
            version_id = str(subparts[0])

            if len(subparts) > 1:
                version_rank += int(subparts[1]) * 100
                version_id += '.' + str(subparts[1])

            if len(subparts) > 2:
                version_rank += int(subparts[2])
                version_id += '.' + str(subparts[2])

        else:
            raise ValueError('Unrecognized volume set suffix "%s"' % suffix)

        return (version_rank, version_message, version_id)

    def all_versions(self):
        """Return a dictionary containing all existing versions of this PdsFile, keyed
        by the version ranks of the volumes on which they reside.
        """

        cls = type(self)

        # We only cache the abspaths, not the PdsFiles, because the cache cannot
        # properly maintan links between PdsFiles
        if self._all_version_abspaths is not None:
            version_dict = {}
            for rank, abspath in self._all_version_abspaths.items():
                version_dict[rank] = cls.from_abspath(abspath)

            return version_dict

        # Initialize the dictionaries with this
        version_dict = {self.version_rank: self}
        version_abspaths = {self.version_rank: self.abspath}

        # Search for versions using all match patterns
        patterns = self.VERSIONS.all(self.logical_path)
        abspaths = []
        for pattern in patterns:
            if pattern:
                abspaths += cls.glob_glob(self.root_ + pattern,
                                              force_case_sensitive=True)

        abspaths = set(abspaths)        # remove duplicates
        abspaths = [p for p in abspaths if p != self.abspath]   # remove self

        pdsfiles = cls.pdsfiles_for_abspaths(abspaths, must_exist=True)

        # Fill in the dictionaries
        for pdsf in pdsfiles:
            key = pdsf.version_rank
            if key in version_dict:
                cls.LOGGER.warn('Duplicate version of ' +
                            version_dict[key].logical_path,
                            pdsf.logical_path)
            else:
                version_dict[key] = pdsf
                version_abspaths[key] = pdsf.abspath

        # Save the same abspath dictionary inside all the versions
        for pdsf in version_dict.values():
            pdsf._all_version_abspaths = version_abspaths
            pdsf._recache()

        return version_dict

    @property
    def all_version_abspaths(self):
        """Return a dictionary containing the abspaths for all existing versions of
        this PdsFile, keyed by the version ranks of the volumes on which they reside.
        """

        if self._all_version_abspaths is None:
            _ = self.all_versions()     # This has the side-effect of filling
                                        # _all_version_abspaths

        return self._all_version_abspaths

    def viewset_lookup(self, name='default'):
        """Return the PdsViewSet associated with this file. If multiple
        PdsViewSets are available, they can be selected by name; "default" is
        assumed.

        Keyword arguments:
            name -- a volset name (default 'default')
        """

        cls = type(self)

        if not self.exists: return None

        if (self._all_viewsets_filled is not None and
            name in self._all_viewsets_filled):
                return self._all_viewsets_filled[name]

        # Check for associated viewables
        try:
            patterns = self.VIEWABLES[name].all(self.logical_path)
        except KeyError:
            patterns = []

        if patterns:
            if not isinstance(patterns, (list,tuple)):
                patterns = [patterns]

            # Remove an empty pattern
            patterns = [p for p in patterns if p]

            abspaths = []
            for pattern in patterns:
                abspaths += cls.glob_glob(self.root_ + pattern)

            # Just use the first set of abspaths if there is more than one
            if abspaths:
                match = cls.VIEWABLE_ANCHOR_REGEX.fullmatch(abspaths[0])
                if match:
                    anchor = match.group(1)
                    abspaths = [p for p in abspaths if p.startswith(anchor)]

            # Create and return the viewset
            viewables = cls.pdsfiles_for_abspaths(abspaths, must_exist=True)
            viewset = pdsviewable.PdsViewSet.from_pdsfiles(viewables)
            return viewset

        # If this is a directory, return the PdsViewSet of the first child with
        # having one with this requested name
        if self.isdir:
            basenames = [b for b in self.childnames
                         if os.path.splitext(b)[1][1:].lower() in
                            (cls.VIEWABLE_EXTS | cls.DATAFILE_EXTS)]
            if len(basenames) > 20:     # Stop after 20 files max
                basenames = basenames[:20]

            for basename in basenames:
                pdsf = self.child(basename)
                if pdsf.isdir: continue

                viewset = pdsf.viewset_lookup(name)
                if viewset:
                    return viewset

            return None

        # The default PdsViewSet of a viewable file is the one made from this
        # file and its viewable siblings with the same anchor. This handles
        # files in the previews tree.
        if name == 'default' and self.is_viewable:
            parent = self.parent()
            if parent:
                sibnames = parent.viewable_childnames_by_anchor(self.anchor)
                siblings = parent.pdsfiles_for_basenames(sibnames)
            else:
                siblings = [self]

            return pdsviewable.PdsViewSet.from_pdsfiles(siblings)

        return pdsviewable.PdsViewSet([])

    ############################################################################
    # Utilities
    ############################################################################

    def volume_pdsfile(self, category=None, rank=None):
        """Return PdsFile object for the root volume file or directory associated with
        this or another category and this or another version. It returns None if the file
        does not exist.

        Keyword arguments:
            category -- the category of the bundle (default None)
            rank     -- the version rank of the bundle (default None)
        """

        cls = type(self)

        abspath = self.volume_abspath(category)
        if abspath and cls.os_path_exists(abspath):
            pdsf = cls.from_abspath(abspath)
        else:
            return None

        if rank:
            try:
                return pdsf.all_versions()[rank]
            except KeyError:
                return None

        return pdsf

    def volset_pdsfile(self, category=None, rank=None):
        """Return PdsFile object for the root volume set for this or another category
        and this or another version. It returns None if the file does not exist.

        Keyword arguments:
            category -- the category of the bundleset (default None)
            rank     -- the version rank of the bundleset (default None)
        """

        cls = type(self)

        abspath = self.volset_abspath(category)
        if abspath and cls.os_path_exists(abspath):
            pdsf = cls.from_abspath(abspath)
        else:
            return None

        if rank:
            try:
                return pdsf.all_versions()[rank]
            except KeyError:
                return None

        return pdsf

    ### Warning to Dave: I changed all these to properties because I kept
    ### typing them wrong.

    @property
    def is_bundle_dir(self):
        """Return True if this is the root level directory of a bundle."""
        return bool(self.bundlename_ and not self.interior) # Note that a bundle set will return an empty string '' rather than False
        #return (self.bundlename_ and not self.interior or False) # MJTM: 'or False' account for bundle sets

    @property
    def is_bundle_file(self):
        """Return True if this is a bundle-level checksum or archive file."""
        return bool(self.bundlename and not self.bundlename_) # Note that a bundle set will return an empty string '' rather than False
        #return (self.bundlename and not self.bundlename_ or False) # MJTM: 'or False' account for bundle sets

    @property
    def is_bundle(self):
        """Return True if this is a bundle-level file, be it a directory or a
        checksum or archive file."""
        return bool(self.is_bundle_dir or self.is_bundle_file)

    @property
    def is_bundleset_dir(self):
        """Return True if this is the root level directory of a bundleset."""
        return bool(self.bundleset and not self.bundlename and self.isdir)

    @property
    def is_bundleset_file(self):
        """Return True if this is a bundleset-level checksum or AAREADME file."""
        return bool(self.bundleset and not self.bundlename and not self.isdir)

    @property
    def is_bundleset(self):
        """Return True if this is a bundleset-level directory or file."""
        return bool(self.bundleset and not self.bundlename)

    @property
    def is_category_dir(self):
        """Return True if this is a category-level directory (i.e., above bundleset)."""
        return (self.bundleset == '')

    def volume_abspath(self, category=None):
        """Return the absolute path to the volume file or directory associated with this
        object. It can be in this category or another. If the category's voltype is the
        same as that of self, the returned abspath will have the same version rank;
        otherwise, it will be the abspath of the latest version. The specified file is
        not required to exist.

        Keyword arguments:
            category -- the category of the bundle (default None)
        """

        if not self.bundlename:
            return ''

        if category:
            category_ = category.rstrip('/') + '/'
        else:
            category_ = self.category_

        parts = category_.split('-')
        if len(parts) == 3:         # if checksums-archives-something
            return ''

        if parts[-1] == self.voltype_:
            suffix = self.suffix    # if voltype is unchanged, keep the version
        else:
            suffix = ''             # otherwise, use the most recent version

        if len(parts) == 2:
            if parts[-1] == 'volumes/':
                insert = ''
            else:
                insert = '_' + parts[-1][:-1]

            if parts[0] == 'checksums':
                ext = '_md5.txt'
            else:
                ext = '.tar.gz'
        else:
            insert = ''
            ext = ''

        return (self.root_ + category_ + self.bundleset + suffix + '/' +
                self.bundlename + insert + ext)

    def volset_abspath(self, category=None):
        """Return the absolute path to a volset file or directory associated with this
        object. It can be in this category or another. If the category's voltype is the
        same as that of self, the returned abspath will have the same version rank;
        otherwise, it will be the abspath of the latest version. The specified file is
        not required to exist.

        Keyword arguments:
            category -- the category of the bundleset (default None)
        """

        if not self.bundleset:
            return None

        if category:
            category_ = category.rstrip('/') + '/'
        else:
            category_ = self.category_

        parts = category_.split('-')

        if parts[-1] == self.voltype_:
            suffix = self.suffix    # if voltype is unchanged, keep this version
        else:
            suffix = ''             # otherwise, use the most recent version

        if len(parts) == 3:         # if checksums-archives-something
            if parts[-1] == 'volumes/':
                ext = '_md5.txt'
            else:
                ext = '_' + parts[-1][:-1] + '_md5.txt'
        else:
            ext = ''

        return (self.root_ + category_ + self.bundleset + suffix + ext)

    ############################################################################
    # Support for alternative constructors
    ############################################################################

    def _complete(self, must_exist=False, caching='default', lifetime=None):
        """Return PdsFiles from the cache if available; otherwise it caches this PdsFile
        if appropriate. This is the general procedure to maintain the cls.CACHE.

        If the file exists, then the capitalization must be correct!

        Keyword arguments:
            must_exist -- a flag to determine if the file should exist in file system
                          (default False)
            caching    -- the caching type, 'dir', 'all' or 'none' (default 'default')
            lifetime   -- the cache lifetime in seconds (default None)
        """

        cls = type(self)

        # Confirm existence
        if must_exist and not self.exists:
            raise IOError('File not found', self.abspath)

        if self.basename.strip() == '':     # Shouldn't happen, but just in case
            return self.parent()

        # If we already have a PdsFile keyed by this logical path, return it,
        # unless this one is physical and the cached one has merged content.
        # This ensures that a physical "category" directory is not replaced by
        # the merged directory.
        try:
            pdsf = cls.CACHE[self.logical_path.lower()]
            if pdsf.is_merged == self.is_merged:
                return pdsf
        except KeyError:
            pass

        # Do not cache above the category level
        if not self.category_: return self

        # Do not cache nonexistent objects
        if not self.exists: return self
        # if not self.exists and not self.category_.startswith('checksums-archives-'): return self

        # Otherwise, cache if necessary
        if caching == 'default':
            caching = cls.DEFAULT_CACHING

        # For category 'checksums-archives-.*', the checksum files are under
        # 'checksums-archives-.*/file', not like regular checksum files under
        # 'checksums-.*/bundleset/file', so to make sure '$RANKS-checksums-archives-.*'
        # and '$VOLS-checksums-archives-.*' are properly cached, we need to make sure the
        # following steps are run for 'checksums-archives-.*/file'.
        #
        # This is because for 'checksums-.*/bundleset/', self.bundleset is properly set,
        # and it will be properly cache in _update_ranks_and_vols(). However, for
        # 'checksums-archives-.*/, neither self.bundleset nor self.bundlename is set, the
        # category 'checksums-archives-.*' won't be cached in _update_ranks_and_vols.
        #
        # Therefore, if we make sure the existing 'checksums-archives-.*/file' (file name
        # has bundleset info) can run the following step, in _update_ranks_and_vols,
        # self.bundleset will be properly set due to the fileanme, and
        # 'checksums-archives-.*' category will be cached.
        if (caching == 'all' or
            (caching == 'dir' and (self.isdir or self.is_index)) or
            self.category_.startswith('checksums-archives-')):

            # Never overwrite the top-level merged directories
            if '/' in self.logical_path:
                cls.CACHE.set(self.logical_path.lower(), self, lifetime=lifetime)

            self._update_ranks_and_vols()

        return self

    def _update_ranks_and_vols(self):
        """Maintains the RANKS and VOLS dictionaries. Must be called for all PdsFile
        objects down to the volume name level.
        """

        # cls.CACHE['$RANKS-category_'] is keyed by [bundle set or name] and returns
        # a sorted list of ranks.

        # cls.CACHE['$VOLS-category_'] is keyed by [bundle set or name][rank] and
        # returns a bundleset or bundlename PdsFile.
        cls = type(self)
        if not cls.LOCAL_PRELOADED:     # we don't track ranks without a preload
            return

        if self.bundleset and not self.bundlename:
            key = self.bundleset
        elif self.bundlename and not self.bundlename_:
            key = self.bundlename
        elif self.bundlename_ and not self.interior:
            key = self.bundlename
        else:
            return

        key = key.lower()
        self.permanent = True       # VOLS entries are permanent!

        rank_dict = cls.CACHE['$RANKS-' + self.category_]
        vols_dict = cls.CACHE['$VOLS-'  + self.category_]

        changed = False
        if key not in rank_dict:
            rank_dict[key] = []
            vols_dict[key] = {}
            changed = True

        ranks = rank_dict[key]
        if self.version_rank not in ranks:
            rank_dict[key].append(self.version_rank)
            rank_dict[key].sort()
            changed = True

        if changed:
            vols_dict[key][self.version_rank] = self.abspath
            cls.CACHE.set('$RANKS-' + self.category_, rank_dict, lifetime=0)
            cls.CACHE.set('$VOLS-'  + self.category_, vols_dict, lifetime=0)

    def _recache(self):
        """Update the cache after this object has been modified, e.g., by having a
        previously empty field filled in.
        """

        cls = type(self)

        logical_lc = self.logical_path.lower()
        if logical_lc in cls.CACHE and (self.is_merged ==
                                    cls.CACHE[logical_lc].is_merged):
            cls.CACHE.set(logical_lc, self)

    ############################################################################
    # Alternative constructors
    ############################################################################

    def child(self, basename, fix_case=True, must_exist=False,
              caching='default', lifetime=None, allow_index_row=True):
        """Return a PdsFile of the sproper subclass in this directory.

        Keyword arguments:
            basename        -- name of the child
            fix_case        -- True to fix the case of the child. (If False, it is
                               permissible but not necessary to fix the case
                               anyway) (default True)
            must_exist      -- True to raise an exception if the parent or child
                               does not exist (default False)
            caching         -- Type of caching to use (default 'default')
            lifetime        -- Lifetime parameter for cache (default None)
            allow_index_row -- True to allow the child to be an index row (default True)
        """

        basename = basename.rstrip('/')

        # Handle the special case of index rows
        if self.is_index and allow_index_row:
            flag = '=' if must_exist else ''
            return self.child_of_index(basename, flag=flag)

        cls = type(self)
        ### Pause cache
        cls.CACHE.pause()
        try:
            # Fix the case if necessary
            if fix_case:
                if basename not in self.childnames:
                    try:
                        k = self.childnames_lc.index(basename.lower())
                    except ValueError:
                        pass
                    else:
                        basename = self.childnames[k]

            # Create the logical path and return from cache if available
            child_logical_path = _clean_join(self.logical_path, basename)
            try:
                pdsf = cls.CACHE[child_logical_path.lower()]
            except KeyError:
                pass

            # Confirm existence if necessary
            basename_lc = basename.lower()
            if must_exist and not basename_lc in self.childnames_lc:
                raise IOError('File not found: ' + child_logical_path)

            # Fill in the absolute path if possible. This will fail for children
            # of category-level directories; we address that case later
            if self.abspath:
                child_abspath = _clean_join(self.abspath, basename)
            else:
                child_abspath = None

            # Select the correct subclass for the child...
            if self.bundleset:
                class_key = self.bundleset
            elif self.category_:
                matchobj = cls.BUNDLESET_PLUS_REGEX_I.match(basename)
                if matchobj is None:
                    raise ValueError('Illegal bundle set directory "%s": %s' %
                                     (basename, self.logical_path))
                class_key = matchobj.group(1)
            else:
                class_key = 'default'

            # "this" is a copy of the parent object with internally cached
            # values removed but with path information duplicated.
            this = self.new_pdsfile(key=class_key, copypath=True)

            # Update the path for the child
            this.logical_path = child_logical_path
            this.abspath = child_abspath    # might be None, for now
            this.basename = basename

            if self.interior:               # if parent is inside a bundle
                this.interior = _clean_join(self.interior, basename)
                return this._complete(must_exist, caching, lifetime)

            if self.bundlename_:               # if parent is a bundle
                this.interior = basename
                return this._complete(must_exist, caching, lifetime)

            if self.bundleset_:                # if parent is a bundleset

                # Handle documents directory
                if self.is_documents:
                    this.bundlename_ = ''
                    this.interior = basename
                    return this._complete(must_exist, caching, lifetime)

                # Handle bundle name
                matchobj = cls.BUNDLENAME_PLUS_REGEX_I.match(basename)
                if matchobj:
                    this.bundlename_ = basename + '/'
                    this.bundlename  = matchobj.group(1)

                    if self.checksums_ or self.archives_:
                        this.bundlename_ = ''
                        this.interior = basename

                if self.checksums_ or self.archives_:
                    this.bundlename_ = ''
                    this.interior = basename

                return this._complete(must_exist, caching, lifetime)

            if self.category_:

                # Handle bundle set and suffix
                matchobj = cls.BUNDLESET_PLUS_REGEX_I.match(basename)
                if matchobj is None:
                    raise ValueError('Illegal bundle set directory "%s": %s' %
                                     (basename, this.logical_path))

                this.bundleset_ = basename + '/'
                this.bundleset  = matchobj.group(1)
                this.suffix  = matchobj.group(2)

                if matchobj.group(3):
                    this.bundleset_ = ''
                    this.interior = basename
                    parts = this.suffix.split('_')
                    if parts[-1] == this.voltype_[:-1]:
                        this.suffix = '_'.join(parts[:-1])

                (this.version_rank,
                 this.version_message,
                 this.version_id) = self.version_info(this.suffix)

                # If this is the child of a category, then we must ensure that
                # it is added to the child list of the merged parent.

                if self.abspath:
                    try:
                        merged_parent = cls.CACHE[self.logical_path.lower()]
                    except KeyError:
                        pass
                    else:
                        childnames = merged_parent._childnames_filled
                        if basename not in childnames:
                            merged_parent._childnames_filled.append(basename)
                            merged_parent._childnames_filled.sort()
                            cls.CACHE.set(self.logical_path.lower(), merged_parent,
                                                                 lifetime=0)

                return this._complete(must_exist, caching, lifetime)

            if not self.category_:

                # Handle voltype and category
                this.category_ = basename + '/'
                matchobj = cls.CATEGORY_REGEX_I.match(basename)
                if matchobj is None:
                    raise ValueError('Invalid category "%s": %s' %
                                     (basename, this.logical_path))

                if fix_case:
                    this.checksums_ = matchobj.group(1).lower()
                    this.archives_  = matchobj.group(2).lower()
                    this.voltype_   = matchobj.group(3).lower() + '/'
                else:
                    this.checksums_ = matchobj.group(1)
                    this.archives_  = matchobj.group(2)
                    this.voltype_   = matchobj.group(3) + '/'

                if this.voltype_[:-1] not in cls.VOLTYPES:
                    raise ValueError('Unrecognized volume type "%s": %s' %
                                     (this.voltype_[:-1], this.logical_path))

                return this._complete(must_exist, caching, lifetime)

            raise ValueError('Cannot define child from PDS root: ' +
                             this.logical_path)

        ### Resume caching no matter what
        finally:
            cls.CACHE.resume()

    def parent(self, must_exist=False, caching='default', lifetime=None):
        """Return the parent PdsFile of this PdsFile.

        Keyword arguments:
            must_exist -- True to raise an exception if the parent or child
                          does not exist (default False)
            caching    -- Type of caching to use (default 'default')
            lifetime   -- Lifetime parameter for cache (default None)
        """

        if self.is_merged:      # merged pdsdir
            return None

        cls = type(self)

        # Return the merged parent if there is one
        logical_path = os.path.split(self.logical_path)[0]
        if logical_path in cls.CATEGORIES or not self.abspath:
            return cls.from_logical_path(logical_path,
                                             must_exist=must_exist)
        else:
            abspath = os.path.split(self.abspath)[0]
            return cls.from_abspath(abspath,
                                        must_exist=must_exist)

    @classmethod
    def from_lid(cls, lid_str):
        """Return the PdsFile from a given LID.
        lid_str format: dataset_id:volume_id:directory_path:file_name

        Keyword arguments:
            lid_str -- the lid string
        """

        lid_component = lid_str.split(':')
        if len(lid_component) != 4:
            raise ValueError('%s is not a valid LID.' % lid_str)

        data_set_id = lid_component[0]
        volume_id = lid_component[1]
        logical_path_wo_volset = 'volumes/' + '/'.join(lid_component[1:])

        pdsf = cls.from_path(logical_path_wo_volset)

        if pdsf.data_set_id != data_set_id:
            raise ValueError('Data set id from lid_str: ' + data_set_id +
                             'does not match the one from pdsfile: ' +
                             pdsf.data_set_id)
        return pdsf

    @classmethod
    def from_logical_path(cls, path, fix_case=False, must_exist=False,
                          caching='default', lifetime=None):
        """Return a PdsFile from a logical path.

        Keyword arguments:
            path       -- the logical path
            fix_case   -- True to fix the case of the child. (If False, it is permissible
                          but not necessary to fix the case anyway) (default False)
            must_exist -- True to raise an exception if the parent or child does not
                          exist (default False)
            caching    -- Type of caching to use (default 'default')
            lifetime   -- Lifetime parameter for cache (default None)

        """

        path = path.rstrip('/')
        if not path:
            return None

        # If the PdsFile with this logical path is in the cache, return it
        path_lc = path.lower()
        try:
            return cls.CACHE[path_lc]
        except KeyError:
            pass

        # Work upward through the path until something is found in the cache
        parts_lc = path_lc.split('/')
        ancestor = None

        for lparts in range(len(parts_lc)-1, 0, -1):
            ancestor_path = '/'.join(parts_lc[:lparts])

            try:
                ancestor = cls.CACHE[ancestor_path]
                break
            except KeyError:
                pass

        ### Pause the cache
        cls.CACHE.pause()
        try:

            # Ancestor found. Handle the rest of the tree using child()
            parts = path.split('/')
            if ancestor and ancestor.abspath:       # if not a logical directory
                this = ancestor
                for part in parts[lparts:]:
                    this = this.child(part, fix_case=fix_case,
                                      must_exist=must_exist,
                                      caching=caching, lifetime=lifetime)

                return this

        ### Resume caching no matter what
        finally:
            cls.CACHE.resume()

        # If there was no preload, CACHE will be empty but this still might work
        abspath = abspath_for_logical_path(path, cls)
        return cls.from_abspath(abspath)

    @classmethod
    def from_abspath(cls, abspath, fix_case=False, must_exist=False,
                     caching='default', lifetime=None):
        """Return a PdsFile from an absolute path.

        Keyword arguments:
            abspath    -- the absolute path
            fix_case   -- True to fix the case of the child. (If False, it is permissible
                          but not necessary to fix the case anyway) (default False)
            must_exist -- True to raise an exception if the parent or child does not
                          exist (default False)
            caching    -- Type of caching to use (default 'default')
            lifetime   -- Lifetime parameter for cache (default None)
        """

        abspath = abspath.rstrip('/')

        # Return a value from the cache, if any
        logical_path = logical_path_from_abspath(abspath, cls)
        try:
            pdsf = cls.CACHE[logical_path.lower()]
            if not pdsf.is_merged:     # don't return a merged directory
                return pdsf
        except KeyError:
            pass

        # Make sure this is an absolute path
        # For Unix, it must start with "/"
        # For Windows, the first item must contain a colon
        # Note that all file paths must use forward slashes, not backslashes

        parts = abspath.split('/')

        # Windows can have the first part be '<drive>:' and that's OK
        drive_spec = ''
        if os.sep == '\\' and parts[0][-1] == ':':
            drive_spec = parts[0]
            parts[0] = ''

        if parts[0] != '':
            raise ValueError('Not an absolute path: ' + abspath)

        # Search for "holdings"
        parts_lc = [p.lower() for p in parts]
        try:
            # Change variable name to distinguish from PDS3
            PDS_HOLDINGS_index = parts_lc.index(cls.PDS_HOLDINGS)
        except ValueError:
            raise ValueError(f'"{cls.PDS_HOLDINGS}" directory not found in: {abspath}')
        ### Pause the cache
        cls.CACHE.pause()
        try:
            # Fill in this.disk_, the absolute path to the directory containing
            # subdirectory "holdings"
            # this = PdsFile()
            this = cls()
            this.disk_ = drive_spec + '/'.join(parts[:PDS_HOLDINGS_index]) + '/'
            this.root_ = this.disk_ + cls.PDS_HOLDINGS + '/'

            # Get case right if necessary
            if fix_case:
                try:
                    this.disk_ = repair_case(this.disk_[:-1], cls) + '/'
                    this.root_ = repair_case(this.root_[:-1], cls) + '/'
                except IOError:
                    if must_exist: raise

            # Fill in the HTML root. This is the text between "http://domain/"
            # and the logical path to appear in a URL that points to the file.
            # Viewmaster creates symlinks inside /Library/WebServer/Documents
            # named holdings, holding1, ... holdings9

            if len(cls.LOCAL_PRELOADED) <= 1:   # There's only one holdings dir
                this.html_root_ = '/' + cls.PDS_HOLDINGS +'/'
            else:                       # Find this holdings dir among preloaded
                PDS_HOLDINGS_abspath = this.disk_ + cls.PDS_HOLDINGS
                try:
                    k = cls.LOCAL_PRELOADED.index(PDS_HOLDINGS_abspath)
                except ValueError:
                    cls.LOGGER.warn('No URL: ' + PDS_HOLDINGS_abspath)
                    this.html_root_ = '/'

                else:       # "holdings", "holdings1", ... "holdings9"
                    if k:
                        this.html_root_ = '/' + cls.PDS_HOLDINGS + str(k) + '/'
                    else:
                        this.html_root_ = '/' + cls.PDS_HOLDINGS + '/'

            this.logical_path = ''
            this.abspath = this.disk_ + cls.PDS_HOLDINGS
            this.basename = cls.PDS_HOLDINGS
            # Handle the rest of the tree using child()
            for part in parts[PDS_HOLDINGS_index + 1:]:
                this = this.child(part, fix_case=fix_case, must_exist=must_exist,
                                  caching=caching, lifetime=lifetime)

            if must_exist and not this.exists:
                raise IOError('File not found', this.abspath)

        ### Resume the cache no matter what
        finally:
            cls.CACHE.resume()

        return this

    def from_relative_path(self, path, fix_case=False, must_exist=False,
                           caching='default', lifetime=None):
        """Return a PdsFile given a path relative to this one.

        Keyword arguments:
            path       -- the relative path
            fix_case   -- True to fix the case of the child. (If False, it is permissible
                          but not necessary to fix the case anyway) (default False)
            must_exist -- True to raise an exception if the parent or child does not
                          exist (default False)
            caching    -- Type of caching to use (default 'default')
            lifetime   -- Lifetime parameter for cache (default None)
        """

        path = path.rstrip('/')
        parts = path.split('/')

        if len(parts) == 0:
            return self._complete(must_exist, caching, lifetime)

        cls = type(self)

        ### Pause the cache
        cls.CACHE.pause()
        try:
            this = self
            for part in parts:
                this = this.child(part, fix_case=fix_case,
                                        must_exist=must_exist,
                                        caching=caching, lifetime=lifetime)

        ### Resume caching no matter what
        finally:
            cls.CACHE.resume()

        return this

    @classmethod
    def _from_absolute_or_logical_path(cls, path, fix_case=False, must_exist=False,
                                       caching='default', lifetime=None):
        """Return a PdsFile based on either an absolute or a logical path."""

        if f'/{cls.PDS_HOLDINGS}/' in path:
            return cls.from_abspath(path,
                                    fix_case=False, must_exist=False,
                                    caching='default', lifetime=None)
        else:
            return cls.from_logical_path(path,
                                         fix_case=False, must_exist=False,
                                         caching='default', lifetime=None)

    @classmethod
    def from_path(cls, path, must_exist=False, caching='default', lifetime=None):
        """Return the PdsFile, if possible based on anything roughly resembling an
        actual path in the filesystem, using sensible defaults for missing components.

        Examples:
          diagrams/checksums/whatever -> checksums-diagrams/whatever
          checksums/archives/whatever -> checksums-archives-volumes/whatever
          COISS_2001.targz -> archives-volumes/COISS_2xxx/COISS_2001.tar.gz
          COISS_2001_previews.targz ->
                        archives-previews/COISS_2xxx/COISS_2001_previews.tar.gz'
          COISS_0xxx/v1 -> COISS_0xxx_v1

        Keyword arguments:
            path       -- the given path
            must_exist -- True to raise an exception if the parent or child does not
                          exist (default False)
            caching    -- Type of caching to use (default 'default')
            lifetime   -- Lifetime parameter for cache (default None)
        """

        if not cls.LOCAL_PRELOADED:
            raise IOError('from_path is not supported without a preload')

        path = str(path)    # make sure it's a string
        path = path.rstrip('/')
        # if there is .targz, treat it as .tar.gz
        path = path.replace('.targz', '.tar.gz')
        if path == '': path = 'volumes'     # prevents an error below

        # Make a quick return if possible
        path_lc = path.lower()
        try:
            return cls.CACHE[path_lc]
        except KeyError:
            pass

        # Strip off a "holdings" directory if found
        k = path_lc.find(cls.PDS_HOLDINGS)
        if k >= 0:
            path = path[k:]
            path = path.partition('/')[2]   # remove up to the next slash

        # Interpret leading parts
        # this = PdsFile()
        this = cls()

        # Fix versions in the path like '/v1' or '/v1.2' to '_v1' or '_v1.2'
        version_pattern = r'.*\/(v[0-9]+\.[0-9]*|v[0-9]+)($|\/)'
        is_version_detected = re.match(version_pattern, path)
        if is_version_detected:
            version = is_version_detected[1]
            path = path.replace(f'/{version}', f'_{version}')


        # Look for checksums, archives, voltypes, and an isolated version suffix
        # among the leading items of the pseudo-path
        parts = path.split('/')
        while len(parts) > 0:

            # For this purpose, change "checksums-archives-whatever" to
            # "checksums/archives/whatever"
            if '-' in parts[0]:
                parts = parts[0].split('-') + parts[1:]

            part = parts[0].lower()

            # If the pseudo-path starts with "archives/", "targz/" etc., it's
            # an archive path
            if part in ('archives', 'tar', 'targz', 'tar.gz'):
                this.archives_ = 'archives-'

            # If the pseudo-path starts with "checksums/" or "md5/", it's a
            # checksum path
            elif part in ('checksums', 'md5'):
                this.checksums_ = 'checksums-'

            # If the pseudo-path starts with "volumes/", "diagrams/", etc., this
            # is the volume type
            elif part in cls.VOLTYPES:
                this.voltype_ = part + '/'

            # If the pseudo-path starts with "v1", "v1.1", "peer_review", etc.,
            # this is the version suffix; otherwise, this is something else
            # (such as a bundleset or bundlename) so proceed to the next step
            else:
                try:
                    _ = cls.version_info('_' + part)
                    this.suffix = '_' + part
                except ValueError:
                    break

            # Pop the first entry from the pseudo-path and try again
            parts = parts[1:]

        # Look for checksums, archives, voltypes, and an isolated version suffix
        # among the trailing items of the pseudo-path
        while len(parts) > 0:

            # For this purpose, change "checksums-archives-whatever" to
            # "checksums/archives/whatever"
            part = parts[0].lower()

            # If the pseudo-path starts with "archives/", "targz/" etc., it's
            # an archive path
            if part in ('archives', 'tar', 'targz', 'tar.gz'):
                this.archives_ = 'archives-'

            # If the pseudo-path starts with "checksums/" or "md5/", it's a
            # checksum path
            elif part in ('checksums', 'md5'):
                this.checksums_ = 'checksums-'

            # If the pseudo-path starts with "volumes/", "diagrams/", etc., this
            # is the volume type
            elif part in cls.VOLTYPES:
                this.voltype_ = part + '/'

            # If the pseudo-path starts with "v1", "v1.1", "peer_review", etc.,
            # this is the version suffix; otherwise, this is something else
            # (such as a file path) so proceed to the next step
            else:
                try:
                    _ = cls.version_info('_' + part)
                    this.suffix = '_' + part
                except ValueError:
                    break

            # Pop the last entry from the pseudo-path and try again
            parts = parts[:-1]

        # Look for a bundle set at the beginning of the pseudo-path
        if len(parts) > 0:
            # Parse the next part of the pseudo-path as if it is a bundleset
            # Parts are (bundleset, version_suffix, other_suffix, extension)
            # Example: COISS_0xxx_v1_md5.txt -> (COISS_0xxx, v1, _md5, .txt)
            matchobj = cls.BUNDLESET_PLUS_REGEX_I.match(parts[0])
            if matchobj:
                subparts = matchobj.group(1).partition('_')
                this.bundleset = subparts[0].upper() + '_' + subparts[2].lower()
                suffix    = matchobj.group(2).lower()
                extension = (matchobj.group(3) + matchobj.group(4)).lower()

                # <bundleset>...tar.gz must be an archive file
                if extension.endswith('.tar.gz'):
                    this.archives_ = 'archives-'

                # <bundleset>..._md5.txt must be a checksum file
                elif extension.endswith('_md5.txt'):
                    this.checksums_ = 'checksums-'

                # <bundleset>_diagrams... must be in the diagrams tree, etc.
                for test_type in cls.VOLTYPES:
                    if extension[1:].startswith(test_type):
                        this.voltype_ = test_type + '/'
                        break

                # An explicit suffix here overrides any other; don't change an
                # empty suffix because it might have been specified elsewhhere
                # in the pseudo-path
                if suffix:
                    this.suffix = suffix

                # Pop the first entry from the pseudo-path and try again
                parts = parts[1:]

        # Look for a bundle name
        if len(parts) > 0:
            # Parse the next part of the pseudo-path as if it is a bundlename
            # Parts are (bundlename, suffix, extension)
            # Example: COISS_2001_previews_md5.txt -> (COISS_2001,
            #                                          _previews_md5, .txt)
            matchobj = cls.BUNDLENAME_PLUS_REGEX_I.match(parts[0])
            if matchobj:
                this.bundlename = matchobj.group(1).upper()

                # If there is a matched extension
                # if matchobj.group(2) and matchobj.group(3):
                if matchobj.group(3):
                    this.basename = matchobj.group(0).replace('.targz', '.tar.gz')
                    extension = (matchobj.group(2) + matchobj.group(3)).lower()

                    # <bundlename>...tar.gz must be an archive file
                    if extension.endswith('.tar.gz'):
                        this.archives_ = 'archives-'

                    # <bundlename>..._md5.txt must be a checksum file
                    elif extension.endswith('_md5.txt'):
                        this.checksums_ = 'checksums-'

                    # <bundlename>_diagrams... must be in the diagrams tree, etc.
                    for test_type in cls.VOLTYPES:
                        if extension[1:].startswith(test_type):
                            this.voltype_ = test_type + '/'
                            break

                # Pop the first entry from the pseudo-path and try again
                parts = parts[1:]

        # Look for a bundle name + version. Not standard but has been seen in
        # Viewmaster URLs
        if len(parts) > 0:
            # Parse the next part of the pseudo-path as if it is a bundlename
            # Parts are (bundlename, version)
            # Example: "VGISS_5101_peer_review" -> (VGISS_5101, _peer_review)
            matchobj = cls.BUNDLENAME_VERSION_I.match(parts[0])
            if matchobj:
                this.bundlename = matchobj.group(1).upper()
                this.suffix = matchobj.group(2).lower()

                # Pop the first entry from the pseudo-path and try again
                parts = parts[1:]

        # If the voltype is missing, it must be "volumes" (for PDS3). For PDS4, it's
        # "bundles"
        if this.voltype_ == '':
            # this.voltype_ = 'volumes/'
            this.voltype_ = cls.BUNDLE_DIR_NAME + '/'

        this.category_ = this.checksums_ + this.archives_ + this.voltype_

        # If a bundle name was found, try to find the absolute path
        if this.bundlename:
            is_bundleset_available = False
            # Fill in the rank
            bundlename = this.bundlename.lower()
            if this.suffix:
                rank = cls.version_info(this.suffix)[0]
            else:
                # For the case like 'COISS_2001.targz', if bundlename is not the key to
                # the cache, we try to find the corresponding bundleset in the cache key.
                try:
                    rank = cls.CACHE['$RANKS-' + this.category_][bundlename][-1]
                except KeyError:
                    # Get the actual bundleset in the cache key from the prefix of the
                    # bundlename.
                    prefix, _, _ = bundlename.partition('_')
                    idx = bundlename.index('_') + 1
                    for bundleset in cls.CACHE['$RANKS-' + this.category_].keys():
                        bundleset_prefix, _, _ = bundleset.partition('_')
                        if len(bundleset_prefix) != len(prefix):
                            continue
                        prefix_li = list(prefix)
                        for i in range(idx-1):
                            if bundleset[i] == 'x':
                                prefix_li[i] = 'x'
                        bundleset_prefix = ''.join(prefix_li) + '_'

                        if bundleset.startswith(bundleset_prefix):
                            updated_bundleset_prefix = bundleset_prefix

                            for i in range(idx, len(bundleset)):
                                if bundleset[i] == 'x':
                                    break
                                else:
                                    updated_bundleset_prefix = bundlename[:i+1]

                            if bundleset.startswith(updated_bundleset_prefix):
                                is_bundleset_available = True
                                this.bundleset = bundleset
                                rank = cls.CACHE['$RANKS-' + this.category_]\
                                                [bundleset][-1]

            # Try to get the absolute path
            try:
                if not is_bundleset_available:
                    this_abspath = cls.CACHE['$VOLS-' + this.category_][bundlename][rank]
                else:
                    this_abspath = cls.CACHE['$VOLS-' + this.category_]\
                                            [this.bundleset][rank]

            # On failure, see if an updated suffix will help
            except KeyError:

                # Fill in alt_ranks, a list of alternative version ranks

                # Allow for change from, e.g., _peer_review to _lien_resolution
                if rank in cls.LATEST_VERSION_RANKS[:-1]:
                    k = cls.LATEST_VERSION_RANKS.index(rank)
                    alt_ranks = cls.LATEST_VERSION_RANKS[k+1:]

                # Without a suffix, use the most recent
                elif rank == cls.LATEST_VERSION_RANKS[-1]:
                    alt_ranks = cls.LATEST_VERSION_RANKS[:-1][::-1]

                else:
                    alt_ranks = []

                # See if any of these alternative ranks will work
                this_abspath = None
                for alt_rank in alt_ranks:
                  try:
                    this_abspath = cls.CACHE['$VOLS-' + this.category_][bundlename]\
                                                                   [alt_rank]
                    break
                  except KeyError:
                    continue

                if not this_abspath:
                    raise ValueError('Suffix "%s" not found: %s' %
                                     (this.suffix, path))

            if this.basename and not this_abspath.endswith(this.basename):
                this_abspath += f'/{this.basename}'
            # This is the PdsFile object down to the bundlename
            this = cls.from_abspath(this_abspath, must_exist=must_exist)

        # If a bundleset was found but not a bundlename, try to find the absolute path
        elif this.bundleset:

            # Fill in the rank
            bundleset = this.bundleset.lower()
            if this.suffix:
                rank = cls.version_info(this.suffix)[0]
            else:
                rank = cls.CACHE['$RANKS-' + this.category_][bundleset][-1]

            # Try to get the absolute path
            try:
                this_abspath = cls.CACHE['$VOLS-' + this.category_][bundleset][rank]

            # On failure, see if an updated suffix will help
            except KeyError:

                # Fill in alt_ranks, a list of alternative version ranks

                # Allow for change from, e.g., _peer_review to _lien_resolution
                if rank in cls.LATEST_VERSION_RANKS[:-1]:
                    k = cls.LATEST_VERSION_RANKS.index(rank)
                    alt_ranks = cls.LATEST_VERSION_RANKS[k+1:]

                # Without a suffix, use the most recent
                elif rank == cls.LATEST_VERSION_RANKS[-1]:
                    alt_ranks = cls.LATEST_VERSION_RANKS[:-1][::-1]

                else:
                    alt_ranks = []

                # See if any of these alternative ranks will work
                this_abspath = None
                for alt_rank in alt_ranks:
                  try:
                    this_abspath = cls.CACHE['$VOLS-' + this.category_][bundleset]\
                                                                   [alt_rank]
                    break
                  except KeyError:
                    continue

                if not this_abspath:
                    raise ValueError('Suffix "%s" not found: %s' %
                                     (this.suffix, path))

            # This is the PdsFile object down to the bundleset
            this = cls.from_abspath(this_abspath, must_exist=must_exist)

        # Without a bundlename or bundleset, this must be a very high-level directory
        else:
            this = cls.CACHE[this.category_[:-1]]

        # If there is nothing left in the pseudo-path, return this
        if len(parts) == 0:
            return this._complete(False, caching, lifetime)

        # Otherwise, traverse the directory tree downward to the selected file
        for part in parts:
            this = this.child(part, fix_case=True, must_exist=must_exist,
                                    caching=caching, lifetime=lifetime)

        return this

    ############################################################################
    # Support for PdsFile objects representing index rows
    #
    # These have a path of the form:
    #   .../filename.tab/selection
    # where:
    #   filename.tab    is the name of an ASCII table file, which must end in
    #                   ".tab";
    #   selection       is a string that identifies a row, typically via the
    #                   basename part of a FILE_SPECIFICATION_NAME.
    ############################################################################

    def get_indexshelf(self):
        """Return the shelf dictionary that identifies keys and row numbers in an index.
        """

        cls = type(self)

        # Return the answer quickly if it exists
        try:
            return cls._get_shelf(self.indexshelf_abspath, log_missing_file=False)
        except Exception as e:
            saved_e = e

        # Interpret the error
        if not self.exists:
            raise IOError('Index file does not exist: ' + self.logical_path)

        if not self.is_index:
            raise ValueError('Not supported as an index file: ' +
                             self.logical_path)

        raise saved_e

    def find_selected_row_key(self, selection, flag='=', exact_match=False):
        """Return the key for this selection among the "children" (row
        selection keys) of an index file. The selection need not be an exact
        match but it must be "close" and unique.

        if flag is '=', raise an error if the selection doesn't exist.
        if flag is '>', return the key after, or last if the selection doesn't
                        exist.
        if flag is '<', return the key before, or first, if the selection
                        doesn't exist.
        if flag is '',  return the selected key even if it doesn't exist.

        Keyword arguments:
            selection   -- the selection key
            flag        -- a flag used to determine which key would be returned (default
                           '=')
            exact_match -- a flag to determine if the given selection should be exactly
                           matched to a key of the index file (default False)
        """

        if flag not in ('', '=', '>', '<'):
            raise ValueError(f'Invalid flag "{flag}"' % flag)

        # Truncate the selection key if it is too long
        if self.filename_keylen:
            selection = selection[:self.filename_keylen]

        # Try the most obvious answer
        if selection in self.childnames:
            return selection

        # Try search in lower case
        selection_lc = selection.lower()
        if selection_lc in self.childnames_lc:
            k = self.childnames_lc.index(selection_lc)
            return self.childnames[k]

        # Try partial matches unless an exact match is required
        if not exact_match:
            # Allow for a key inside the selection
            child_keys = []
            for (k,key) in enumerate(self.childnames_lc):
                if selection_lc.startswith(key):
                    child_keys.append(self.childnames[k])

            # If we have a single match, we're done
            if len(child_keys) == 1:
                return child_keys[0]

            # In the case of multiple matches, choose the longest match
            if len(child_keys) > 1:
                longest_match = child_keys[0]
                for key in child_keys[1:]:
                    if len(key) > len(longest_match):
                        longest_match = key

                return longest_match

            # Allow for the selection inside a key
            child_keys = []
            for (k,key) in enumerate(self.childnames_lc):
                if key.startswith(selection_lc):
                    child_keys.append(self.childnames[k])

            # If we have a single match, we're done
            if len(child_keys) == 1:
                return child_keys[0]

            # On failure, return the selection if flag is ''
            if flag == '':
                return selection

            # We disallow multiple matches because this can occur when a key is
            # incomplete
            if len(child_keys) > 1:
                raise IOError('Index selection is ambiguous: ' +
                              self.logical_path + '/' + selection)

        if flag == '=':
            raise KeyError('Index selection not found: ' +
                           self.logical_path + '/' + selection)

        childnames = self.childnames + [selection]
        childnames = self.sort_basenames(childnames)
        k = childnames.index(selection)

        if flag == '<':
            # Return the childname before the selection; if it is first, return
            # the second
            return childnames[k-1] if k > 0 else childnames[1]
        else:
            # Return the childname after the selection; if it is last, return
            # the one before
            return childnames[k+1] if k < len(childnames)-1 else childnames[-2]

    def child_of_index(self, selection, flag='='):
        """Return the PdsFile associated with the selected rows of this
        index. Note that the rows might not exist.

        if flag is '=', raise an error if the selection doesn't exist.
        if flag is '>', return the child after, or last if the selection doesn't
                        exist.
        if flag is '<', return the child before, or first if the selection
                        doesn't exist.
        if flag is '',  return the selected object even if it doesn't exist.

        Keyword arguments:
            selection -- the selection key
            flag      -- a flag used to determine which key would be returned (default
                         '=')
        """

        cls = type(self)

        # Get the selection key for the object
        key = self.find_selected_row_key(selection, flag=flag)

        # If we already have a PdsFile keyed by this absolute path, return it
        new_abspath = _clean_join(self.abspath, key)
        try:
            return cls.CACHE[new_abspath.lower()]
        except KeyError:
            pass

        # Construct the object
        if key in self.childnames:
            shelf = self.get_indexshelf()
            rows = shelf[key]
            if isinstance(rows, numbers.Integral):
                rows = (rows,)

            row_range = (min(rows), max(rows)+1)
            table = pdstable.PdsTable(label_file=self.label_abspath,
                                      label_contents=self.index_pdslabel,
                                      row_range=row_range)
            table_dicts = table.dicts_by_row()

            # Fill in the column names if necessary
            if not self.column_names:
                self.column_names = [c.name for
                                     c in table.info.column_info_list]

            row_dicts = []
            for k in rows:
                row_dicts.append(table_dicts[k - row_range[0]])

            pdsf = self.new_index_row_pdsfile(key, row_dicts)
            pdsf._exists_filled = True

        # For a missing row...
        else:
            pdsf = self.new_index_row_pdsfile(key, [])
            pdsf._exists_filled = False

        return pdsf

    def data_abspath_associated_with_index_row(self):
        """Attempt to infer and return the data PdsFile object associated with this index
        row PdsFile. It will return an empty string on failure.

        If the selected row is missing, the associated data file might still
        exist. In this case, it conducts a search for a data file assuming it
        is on the same volume and parallel to the other files in the index.
        """

        cls = type(self)

        # Internal function identifies the row_dict keys for filespec,
        # path_name (optional), and volume
        def get_keys(row_dict):
            filespec_key = ''

            file_spec_colnames = pdstable.PDS3_FILE_SPECIFICATION_COLUMN_NAMES_lc
            volume_colnames = [x.upper() for x in pdstable.PDS3_VOLUME_COLNAMES_lc]
            if cls.__bases__[0].__name__ == 'Pds4File':
                file_spec_colnames = pdstable.PDS4_FILE_SPECIFICATION_COLUMN_NAMES_lc
                volume_colnames = [x.upper() for x in pdstable.PDS4_BUNDLE_COLNAMES_lc]

            for guess in file_spec_colnames:
                if guess.upper() in row_dict:
                    filespec_key = guess.upper()
                    break

            if not filespec_key:
                return ('', '', '')

            volume_key = ''
            for guess in volume_colnames:
                if guess in row_dict:
                    volume_key = guess

            if 'PATH_NAME' in row_dict:
                path_key = 'PATH_NAME'
            else:
                path_key = ''

            return (volume_key, path_key, filespec_key)

        # Begin active code...

        if not self.is_index_row:
            return ''

        # If the row exists
        if self.row_dicts:
            row_dict = self.row_dicts[0]
            (volume_key, path_key, filespec_key) = get_keys(row_dict)
            if not filespec_key:
                return ''

            parts = [self.volset_abspath('volumes')]
            if volume_key:
                parts.append(row_dict[volume_key].strip('/'))
            if path_key:
                parts.append(row_dict[path_key].strip('/'))

            parts.append(row_dict[filespec_key].strip('/'))
            return '/'.join(parts)

        # If the row doesn't exist, try the rows before it and after it, and
        # then replace the basename
        parent = self.parent()
        for flag in ('<', '>'):
            neighbor = parent.child_of_index(self.basename, flag=flag)
            abspath = neighbor.data_abspath_associated_with_index_row()
            if abspath:
                abspath = abspath.replace(neighbor.basename, self.basename)
                if (neighbor.basename != self.basename and
                    cls.os_path_exists(abspath)):
                        return abspath

        # We should never reach this point, because there should never be a case
        # where an index row exists but the data file doesn't. Nevertheless,
        # I'll let this slide because I can't see a real-world scenario where
        # this would matter.
        return ''

    def data_pdsfile_for_index_row(self):
        """Attempt to infer and return the volume PdsFile object associated with an index
        row PdsFile. It will return None on failure.
        """

        cls = type(self)

        abspath = self.data_abspath_associated_with_index_row()
        if abspath:
            return cls.from_abspath(abspath)
        else:
            return None

    ############################################################################
    # OPUS support methods
    ############################################################################

    @classmethod
    def from_filespec(cls, filespec, fix_case=False):
        """Return the PdsFile object based on a bundle name plus file specification
        path, without the category or prefix specified.

        Keyword arguments:
            filespec -- the file specification
            fix_case -- True to fix the case of the child. (If False, it is permissible
                        but not necessary to fix the case anyway) (default False)
        """

        bundleset = cls.FILESPEC_TO_BUNDLESET.first(filespec)
        if not bundleset:
            raise ValueError('Unrecognized file specification: ' + filespec)

        return cls.from_logical_path(cls.BUNDLE_DIR_NAME + '/' + bundleset + '/'
                                         + filespec, fix_case)

    @classmethod
    def from_opus_id(cls, opus_id):
        """Return the PdsFile of the primary data file associated with this OPUS ID.

        Keyword arguments:
            opus_id -- the given opus id
        """

        pdsfile_class = cls.OPUS_ID_TO_SUBCLASS.first(opus_id)
        if not pdsfile_class:
            raise ValueError('Unrecognized OPUS ID: ' + opus_id)

        # If implemented as a function rather than as a translator...
        if callable(pdsfile_class.OPUS_ID_TO_PRIMARY_LOGICAL_PATH):
            return pdsfile_class.OPUS_ID_TO_PRIMARY_LOGICAL_PATH(opus_id)

        paths = pdsfile_class.OPUS_ID_TO_PRIMARY_LOGICAL_PATH.all(opus_id)
        patterns = [abspath_for_logical_path(p, cls) for p in paths]
        matches = []
        for pattern in patterns:
            if _needs_glob(pattern):
                abspaths = cls.glob_glob(pattern, force_case_sensitive=True)
            elif cls.os_path_exists(pattern, force_case_sensitive=True):
                abspaths = [pattern]
            else:
                abspaths = []

            matches += abspaths

        # One match is easy to handle
        if len(matches) == 1:
            return cls.from_abspath(matches[0])

        if len(matches) == 0:
            raise ValueError('Unrecognized OPUS ID: ' + opus_id)

        # Call a special product prioritizer if available
        pdsfiles = cls.pdsfiles_for_abspaths(matches)
        if hasattr(pdsfiles[0], 'opus_prioritizer'):
            fake_opus_key = ('', 0, '', '', True)
            fake_opus_sublists = [[pdsf] for pdsf in pdsfiles]
            fake_product_dict = {fake_opus_key: fake_opus_sublists}
            fake_product_dict = pdsfiles[0].opus_prioritizer(fake_product_dict)
            return fake_product_dict[fake_opus_key][0][0]

        for k, pdsf in enumerate(pdsfiles):
            cls.LOGGER.warn('Ambiguous primary product for OPUS ID ' + opus_id,
                        pdsf.abspath + (' (selected)' if k == 0 else ''))

        return pdsfiles[0]

    def opus_products(self):
        """For this primary data product or label, return a dictionary keyed
        by a tuple containing this information:
          (group, priority, opus_type, description, default_checked)
        Examples:
          ('Cassini ISS',    0, 'coiss_raw',       'Raw Image',                  True)
          ('Cassini VIMS', 130, 'covims_full',     'Extra Preview (full-size)',  True)
          ('Cassini CIRS', 618, 'cirs_browse_pan', 'Extra Browse Diagram (Pan)', True)
          ('metadata',      40, 'ring_geometry',   'Ring Geometry Index',        True)
          ('browse',        30, 'browse_medium',   'Browse Image (medium)',      True)
        These keys are designed such that OPUS results will be returned in the
        sorted order of these keys.

        For any key, this dictionary returns a list of sublists. Each sublist
        has the form:
            [PdsFile for a data product,
             PdsFile for its label (if any),
             PdsFile for the first embedded .FMT file (if any),
             PdsFile for the second embedded .FMT file (if any), etc.]
        This sublist contains every file that should be added to the OPUS
        results if that data product is requested. The sublists appear in order
        of decreasing version.

        If a class function opus_prioritizer exists, this is called before the
        dictionary is returned. In cases where multiple products with the same
        OPUS ID and version exists, an opus_prioritizer can be used to alter the
        dictionary returned in order to highlight the "best" among the
        alternative products.
        """

        cls = type(self)

        # Get the associated absolute paths
        patterns = self.OPUS_PRODUCTS.all(self.logical_path)

        abs_patterns_and_opus_types = []
        for pattern in patterns:
            if isinstance(pattern, str):    # match string only
                abs_patterns_and_opus_types.append((self.root_ + pattern, None))
            else:                           # (match string, opus_type)
                (p, opus_type) = pattern
                abs_patterns_and_opus_types.append((self.root_ + p, opus_type))

        # Construct a complete list of matching abspaths.
        # Create a dictionary of opus_types based on abspaths where opus_types
        # have already been specified.
        abspaths = []
        opus_type_for_abspath = {}
        for (pattern, opus_type) in abs_patterns_and_opus_types:
            these_abspaths = cls.glob_glob(pattern,
                                           force_case_sensitive=True)
            if opus_type:
                for abspath in these_abspaths:
                    opus_type_for_abspath[abspath] = opus_type

            abspaths += these_abspaths

        # Get PdsFiles for abspaths, organized by labels vs. datafiles
        # label_files[label_abspath] = [label_pdsfile, fmt1_pdsfile, ...]
        # data_files is a list
        label_pdsfiles = {}
        data_pdsfiles = []
        for abspath in abspaths:
            pdsf = cls.from_abspath(abspath)
            if pdsf.islabel:
                # Check if the corresponding link info exists. If not, we issue
                # a warning and skip looking for the .fmt files.
                # Note this means that opus_products might return a different
                # list of products once the link file is available.
                try:
                    pdsf.shelf_lookup('link')
                except (OSError, KeyError, ValueError):
                    cls.LOGGER.warn('Missing links info',
                                pdsf.logical_path)
                    fmt_pdsfiles = []
                else:
                    links = set(pdsf.linked_abspaths)
                    fmts = [f for f in links if f.lower().endswith('.fmt')]
                    fmts.sort()
                    fmt_pdsfiles = cls.pdsfiles_for_abspaths(fmts,
                                                             must_exist=True)
                label_pdsfiles[abspath] = [pdsf] + fmt_pdsfiles
            else:
                data_pdsfiles.append(pdsf)

        # Construct the dictionary to return
        pdsfile_dict = {}
        label_visited = defaultdict(list)
        for pdsf in data_pdsfiles:
            key = opus_type_for_abspath.get(pdsf.abspath, pdsf.opus_type)
            if key == '':
                cls.LOGGER.error('Unknown opus_type for', pdsf.abspath)
            if key not in pdsfile_dict:
                pdsfile_dict[key] = []

            # avoid duplicated label files in one opus type category
            if pdsf.label_abspath and pdsf.label_abspath not in label_visited[key]:
                label_visited[key].append(pdsf.label_abspath)
                sublist = [pdsf] + label_pdsfiles[pdsf.label_abspath]
            else:
                sublist = [pdsf]

            pdsfile_dict[key].append(sublist)

        # Call a special product prioritizer if available
        if hasattr(self, 'opus_prioritizer'):
            self.opus_prioritizer(pdsfile_dict)

        # Sort the return
        for (header, sublists) in pdsfile_dict.items():
            # For the same opus type (header), combine different lists of the same
            # version to one sublist
            new_sublist_dict = {}
            for li in sublists:
                version = li[0].version_rank
                if li[0].version_rank not in new_sublist_dict:
                    new_sublist_dict[version] = li
                else:
                    new_sublist_dict[version] += li

            new_sublists = list(new_sublist_dict.values())

            # Sort the sublist by filepath (alphabetical order)
            for li in new_sublists:
                li.sort(key=lambda x: x.abspath)

            # Sort the list of sublists by version (in the order of decreasing version)
            new_sublists.sort(key=lambda x: x[0].version_rank, reverse=True)

            # update pdsfile_dict with sorted sublists
            pdsfile_dict[header] = new_sublists

        return pdsfile_dict

    ############################################################################
    # Checksum path associations
    ############################################################################

    def checksum_path_and_lskip(self):
        """Return the absolute path to the checksum file associated with this PdsFile.
        Also return the number of characters to skip over in that absolute path to obtain
        the basename of the checksum file.
        """

        if self.checksums_:
            raise ValueError('No checksums of checksum files: ' +
                             self.logical_path)

        if self.voltype_ == 'volumes/':
            suffix = ''
        else:
            suffix = '_' + self.voltype_[:-1]

        if self.archives_:
            abspath = ''.join([self.root_, 'checksums-', self.category_,
                               self.bundleset, self.suffix, suffix, '_md5.txt'])
            lskip = (len(self.root_) + len('checksums_') + len(self.category_))

        elif self.bundlename:
            abspath = ''.join([self.root_, 'checksums-', self.category_,
                               self.bundleset_, self.bundlename, suffix, '_md5.txt'])
            lskip = (len(self.root_) + len('checksums_') + len(self.category_) +
                     len(self.bundleset_))

        else:
            raise ValueError('Missing volume name for checksum file: ' +
                             self.logical_path)

        return (abspath, lskip)

    def checksum_path_if_exact(self):
        """Return the absolute path to the checksum file with the exact same contents as
        this directory; otherwise blank. Determines whether Viewmaster shows a link to a
        checksum file.
        """

        if self.checksums_:
            return ''

        cls = type(self)

        path_if_exact = ''
        if self.archives_ and self.is_bundleset_dir:
            path_if_exact = self.checksum_path_and_lskip()[0]

        if self.is_bundle_dir:
            path_if_exact = self.checksum_path_and_lskip()[0]

        if cls.os_path_exists(path_if_exact):
            return path_if_exact

        return ''

    def dirpath_and_prefix_for_checksum(self):
        """Return tuple (absolute path to the directory associated with this checksum
        path, prefix suppressed from the file path that appears in each row of the file).
        """

        if self.archives_:
            dirpath = ''.join([self.root_, self.archives_, self.voltype_,
                               self.bundleset, self.suffix])
            prefix_ = ''.join([self.root_, self.archives_, self.voltype_,
                               self.bundleset, self.suffix, '/'])
        else:
            dirpath = ''.join([self.root_, self.archives_, self.voltype_,
                               self.bundleset_, self.bundlename])
            prefix_ = ''.join([self.root_, self.voltype_, self.bundleset_])

        return (dirpath, prefix_)

    ############################################################################
    # Archive path associations
    ############################################################################

    def archive_path_and_lskip(self):
        """Return the absolute path to the archive file associated with this PdsFile.
        Also return the number of characters to skip over in that absolute path to obtain
        the basename of the archive file.
        """

        if self.checksums_:
            raise ValueError('No archives for checksum files: ' +
                             self.logical_path)

        if self.archives_:
            raise ValueError('No archives for archive files: ' +
                             self.logical_path)

        if self.voltype_ == 'volumes/':
            suffix = ''
        else:
            suffix = '_' + self.voltype_[:-1]

        if not self.bundlename:
            raise ValueError('Archives require bundle names: ' +
                              self.logical_path)

        abspath = ''.join([self.root_, 'archives-', self.category_,
                           self.bundleset_, self.bundlename, suffix, '.tar.gz'])
        lskip = len(self.root_) + len(self.category_) + len(self.bundleset_)

        return (abspath, lskip)

    def archive_path_if_exact(self):
        """Return the absolute path to the archive file with the exact same contents as
        this directory; otherwise blank.
        """

        if self.checksums_ or self.archives_:
            return ''

        if self.interior:
            return ''

        try:
            path_if_exact = self.archive_path_and_lskip()[0]
        except ValueError:
            return ''

        cls = type(self)

        if cls.os_path_exists(path_if_exact):
            return path_if_exact

        return ''

    def dirpath_and_prefix_for_archive(self):
        """Return the absolute path to the directory associated with this archive path."""

        dirpath = ''.join([self.root_, self.voltype_,
                           self.bundleset_, self.bundlename])

        parent = ''.join([self.root_, self.voltype_, self.bundleset_])

        return (dirpath, parent)

    def archive_logpath(self, task):
        """Return the absolute path to the log file associated with this archive file.

        Keyword arguments:
            task -- part of the log file basename that describes the task
        """

        this = self.copy()
        this.checksums_ = ''
        if this.archives_ == 'archives-':
            this.archives_ = ''
            this.category_ = this.voltype_

        return this.log_path_for_bundle('_targz', task=task, dir='archives')

    ############################################################################
    # Shelf support
    ############################################################################

    SHELF_CACHE = {}
    SHELF_ACCESS = {}
    SHELF_CACHE_SIZE = 120
    SHELF_CACHE_SLOP = 20
    SHELF_ACCESS_COUNT = 0

    SHELF_NULL_KEY_VALUES = {}

    def shelf_path_and_lskip(self, shelf_type='info', bundlename=''):
        """Return the absolute path to the shelf file associated with this PdsFile.
        Also return the number of characters to skip over in that absolute path to obtain
        the key into the shelf.

        Keyword arguments:
            shelf_type -- shelf type ID: 'index', 'info', or 'link' (default 'info')
            bundlename -- an optional bundle name to append to the end of a this path,
                          which can be used if this is a bundleset (default '')
        """

        if self.checksums_:
            raise ValueError('No shelf files for checksums: ' +
                             self.logical_path)

        cls = type(self)

        (dir_prefix, file_suffix) = cls.SHELF_PATH_INFO[shelf_type]

        if self.archives_:
            if not self.bundleset_:
                raise ValueError('Archive shelves require bundle sets: ' +
                                 self.logical_path)

            abspath = ''.join([self.root_, dir_prefix,
                               self.category_, self.bundleset, self.suffix,
                               file_suffix, '.pickle'])
            lskip = (len(self.root_) + len(self.category_) +
                     len(self.bundleset_))

        else:
            if not self.bundlename_ and not bundlename:
                raise ValueError('Non-archive shelves require bundle names: ' +
                                 self.logical_path)

            if bundlename:
                this_bundlename = bundlename.rstrip('/')
            else:
                this_bundlename = self.bundlename

            abspath = ''.join([self.root_, dir_prefix,
                               self.category_, self.bundleset_, this_bundlename,
                               file_suffix, '.pickle'])
            lskip = (len(self.root_) + len(self.category_) +
                     len(self.bundleset_) + len(this_bundlename) + 1)

        return (abspath, lskip)

    def shelf_path_and_key(self, shelf_id='info', bundlename=''):
        """Return the absolute path to a shelf file, plus the key for this item.

        Keyword arguments:
            shelf_id   -- shelf type ID: 'index', 'info', or 'link' (default 'info')
            bundlename -- an optional bundle name to append to the end of a this path,
                          which can be used if this is a bundleset (default '')
        """

        (abspath, lskip) = self.shelf_path_and_lskip(shelf_id, bundlename)
        if bundlename:
            return (abspath, '')
        else:
            return (abspath, self.interior)

    @classmethod
    def _get_shelf(cls, shelf_path, log_missing_file=True):
        """Internal method to open and return a shelf/pickle file. A limited number of
        shelf files are kept open at all times to reduce file IO.

        Use log_missing_file = False to suppress log entries when a nonexistent
        shelf file is requested but the exception is handled externally.

        Keyword arguments:
            shelf_path       -- the path of the shelf file
            log_missing_file -- a flag used to determine if we would like to log the path
                                of the opening pickle file (default True)
        """

        # If the shelf is already open, update the access count and return it
        if shelf_path in cls.SHELF_CACHE:
            cls.SHELF_ACCESS_COUNT += 1
            cls.SHELF_ACCESS[shelf_path] = cls.SHELF_ACCESS_COUNT

            return cls.SHELF_CACHE[shelf_path]

        if log_missing_file or os.path.exists(shelf_path):
            cls.LOGGER.debug('Opening pickle file', shelf_path)

        if not os.path.exists(shelf_path):
            raise IOError('Pickle file not found: %s' % shelf_path)

        try:
            with open(shelf_path, 'rb') as f:
                shelf = pickle.load(f)
        except Exception as e:
            raise IOError('Unable to open pickle file: %s' % shelf_path)

        # The pickle files do not produce dictionaries that are in
        # alphabetical order, so we sort them here in case we want to
        # do a binary search later.
        keys_vals = list(zip(shelf.keys(), shelf.values()))
        keys_vals.sort(key=lambda x: x[0])
        shelf = dict(keys_vals)

        # Save the null key values from the info shelves. This can save a lot of
        # shelf open/close operations when we just need info about a bundle,
        # not an interior file.
        if '' in shelf and shelf_path not in cls.SHELF_NULL_KEY_VALUES:
            cls.SHELF_NULL_KEY_VALUES[shelf_path] = shelf['']

        cls.SHELF_ACCESS_COUNT += 1
        cls.SHELF_ACCESS[shelf_path] = cls.SHELF_ACCESS_COUNT
        cls.SHELF_CACHE[shelf_path] = shelf

        # Trim the cache if necessary
        if len(cls.SHELF_CACHE) > (cls.SHELF_CACHE_SIZE +
                                       cls.SHELF_CACHE_SLOP):
            pairs = [(cls.SHELF_ACCESS[k],k) for k in cls.SHELF_CACHE]
            pairs.sort()

            shelf_paths = [p[1] for p in pairs]
            for shelf_path in shelf_paths[:-cls.SHELF_CACHE_SIZE]:
                cls._close_shelf(shelf_path)

        return shelf

    @classmethod
    def _close_shelf(cls, shelf_path):
        """Internal method to close a shelf file. A limited number of shelf
        files are kept open at all times to reduce file IO.

        Keyword arguments:
            shelf_path -- the path of the shelf file
        """

        # If the shelf is not already open, return
        if shelf_path not in cls.SHELF_CACHE:
            cls.LOGGER.error('Cannot close pickle file; not currently open',
                         shelf_path)
            return

        # Remove from the cache
        del cls.SHELF_CACHE[shelf_path]
        del cls.SHELF_ACCESS[shelf_path]

        cls.LOGGER.debug('Pickle file closed', shelf_path)

    @classmethod
    def close_all_shelves(cls):
        """Close all shelf files."""

        keys = list(cls.SHELF_CACHE.keys())     # save keys so dict can be
        for shelf_path in keys:                     # be modified inside loop!
            cls._close_shelf(shelf_path)

    def shelf_lookup(self, shelf_type='info', bundlename=''):
        """Return the contents of a shelf file associated with this object.

        Keyword arguments:
            shelf_type -- indicates the type of the shelf file: 'info', 'link', or
                          'index' (default 'info')
            bundlename -- can be used to get info about a bundle when the method
                          is applied to its enclosing bundleset (default '')
        """

        cls = type(self)
        (shelf_path, key) = self.shelf_path_and_key(shelf_type, bundlename)

        # This potentially saves the need for a lot of opens and closes when
        # getting info about bundles rather than interior files
        if key == '':
            try:
                return cls.SHELF_NULL_KEY_VALUES[shelf_path]
            except KeyError:
                pass

            # Try the second line of the .py file; this is quicker than reading
            # the whole .pickle file. This is useful because it avoids the need
            # to open every info shelf file during preload.
            if shelf_type == 'info':
                py_path = shelf_path.replace('.pickle', '.py')
                cls.LOGGER.debug('Retrieving key "%s"' % py_path)

                with open(py_path) as f:
                    rec = f.readline()
                    rec = f.readline()

                # Format is "": (bytes, count, date, checksum, (0,0)),
                parts = rec.partition(':')
                values = eval(parts[2].strip()[:-1])
                cls.SHELF_NULL_KEY_VALUES[shelf_path] = values
                return values

        shelf = cls._get_shelf(shelf_path)
        return shelf[key]

    @classmethod
    def shelf_path_and_key_for_abspath(cls, abspath, shelf_type='info'):
        """Return the absolute path to the shelf file associated with this file path.
        Also return the key for indexing into the shelf.

        Keyword arguments:
            abspath    -- the absolute path of the file
            shelf_type -- shelf type, e.g., 'info' or 'link' (default 'info')
        """

        # No checksum shelf files allowed
        (root, _, logical_path) = abspath.partition(f'/{cls.PDS_HOLDINGS}/')
        if logical_path.startswith('checksums'):
            raise ValueError('No shelf files for checksums: ' + logical_path)

        (dir_prefix, file_suffix) = cls.SHELF_PATH_INFO[shelf_type]

        # For archive files, the shelf is associated with the bundleset
        if logical_path.startswith('archives'):
            parts = logical_path.split('/')
            if len(parts) < 2:
                raise ValueError('Archive shelves require bundle sets: ' +
                                 logical_path)

            shelf_abspath = ''.join([root, f'/{cls.PDS_HOLDINGS}/', dir_prefix,
                                     parts[0], '/', parts[1],
                                     file_suffix, '.pickle'])
            key = '/'.join(parts[2:])

        # Otherwise, the shelf is associated with the bundle
        else:
            parts = logical_path.split('/')
            if len(parts) < 3:
                raise ValueError('Non-archive shelves require bundle names: ' +
                                 logical_path)

            shelf_abspath = ''.join([root, f'/{cls.PDS_HOLDINGS}/', dir_prefix,
                                     parts[0], '/', parts[1], '/', parts[2],
                                     file_suffix, '.pickle'])
            key = '/'.join(parts[3:])

        return (shelf_abspath, key)

    @property
    def info_shelf_expected(self):
        """Return True if this object should be associated with an entry in an info
        shelf file.
        """

        # Checksum files have no info shelves
        if self.checksums_:
            return False

        # The document tree does not have info shelves
        if self.is_documents:
            return False

        # Category-level directories are merged
        if self.is_category_dir:
            return False

        # Archives have info shelves from the bundleset level on down
        if self.archives_:
            return True

        # Other files have shelves from the bundlename level on down
        if self.bundlename:
            return True

        # This leaves bundleset-level files and their AAREADMEs
        return False

    def shelf_exists_if_expected(self):
        """Return True if shelf exists for a pdsfile instance expected to have the shelf
        file. False if shelf doesn't exist for a pdsfile instance expected to have one.
        """

        if self.info_shelf_expected:
            try:
                self.shelf_lookup('info')
                return True
            except OSError:
                return False

        # Return None if a pdsfile instance doesn't expect the shelf file
        return None

    ############################################################################
    # Log path associations
    ############################################################################

    LOG_ROOT_ = None

    @classmethod
    def set_log_root(cls, root=None):
        """Define the default root directory for logs. If None, use the "logs" directory
        parallel to "holdings".

        Keyword arguments:
            root -- the root of the log file path (default None)
        """

        if root is None:
            cls.LOG_ROOT_ = None
        else:
            cls.LOG_ROOT_ = root.rstrip('/') + '/'

    def log_path_for_bundle(self, suffix='', task='', dir='', place='default'):
        """Return a complete log file path for this bundle.

        The file name is [dir/]category/bundleset/bundlename_suffix_time[_task].log

         Keyword arguments:
            suffix -- the suffix of the log file (default '')
            task   -- part of the log basename (default '')
            dir    -- the directory of the log file (default '')
            place  -- 'default' or 'parallel', the option provides for a temporary
                      override of the default log root (default 'default')
        """

        cls = type(self)

        # This option provides for a temporary override of the default log root
        if place == 'default':
            temporary_log_root = cls.LOG_ROOT_
        elif place == 'parallel':
            temporary_log_root = None
        else:
            raise ValueError('unrecognized place option: ' + place)

        if temporary_log_root is None:
            parts = [self.disk_, 'logs/']
        else:
            parts = [temporary_log_root]

        if dir:
            parts += [dir.rstrip('/'), '/']

        parts += [self.category_, self.bundleset_, self.bundlename]

        if suffix:
            parts += ['_', suffix.lstrip('_')]  # exactly one "_" before suffix

        timetag = datetime.datetime.now().strftime(cls.LOGFILE_TIME_FMT)
        parts += ['_', timetag]

        if task:
            parts += ['_', task]

        parts += ['.log']

        return ''.join(parts)

    def log_path_for_bundleset(self, suffix='', task='', dir='', place='default'):
        """Return a complete log file path for this bundle set.

        The file name is [dir/]category/bundleset_suffix_time[_task].log.

        Keyword arguments:
            suffix -- the suffix of the log file (default '')
            task   -- part of the log basename (default '')
            dir    -- the directory of the log file (default '')
            place  -- 'default' or 'parallel', the option provides for a temporary
                      override of the default log root (default 'default')
        """

        cls = type(self)

        # This option provides for a temporary override of the default log root
        if place == 'default':
            temporary_log_root = cls.LOG_ROOT_
        elif place == 'parallel':
            temporary_log_root = None
        else:
            raise ValueError('unrecognized place option: ' + place)

        if temporary_log_root is None:
            parts = [self.disk_, 'logs/']
        else:
            parts = [temporary_log_root]

        if dir:
            parts += [dir.rstrip('/'), '/']

        parts += [self.category_, self.bundleset, self.suffix]

        if suffix:
            parts += ['_', suffix.lstrip('_')]  # exactly one "_" before suffix

        timetag = datetime.datetime.now().strftime(cls.LOGFILE_TIME_FMT)
        parts += ['_', timetag]

        if task:
            parts += ['_', task]

        parts += ['.log']

        return ''.join(parts)

    def log_path_for_index(self, task='', dir='index', place='default'):
        """Return a complete log file path for this bundle.

        The file name is [dir/]<logical_path_wo_ext>_timetag[_task].log.

        Keyword arguments:
            task   -- part of the log basename (default '')
            dir    -- the directory of the log file (default 'index')
            place  -- 'default' or 'parallel', the option provides for a temporary
                      override of the default log root (default 'default')
        """

        if not self.is_index:
            raise ValueError('Not an index file: ' + self.logical_path)

        cls = type(self)

        # This option provides for a temporary override of the default log root
        if place == 'default':
            temporary_log_root = cls.LOG_ROOT_
        elif place == 'parallel':
            temporary_log_root = None
        else:
            raise ValueError('unrecognized place option: ' + place)

        if temporary_log_root is None:
            parts = [self.disk_, 'logs/']
        else:
            parts = [temporary_log_root]

        if dir:
            parts += [dir.rstrip('/'), '/']

        parts += [self.logical_path.rpartition('.')[0]]

        timetag = datetime.datetime.now().strftime(cls.LOGFILE_TIME_FMT)
        parts += ['_', timetag]

        if task:
            parts += ['_', task]

        parts += ['.log']

        return ''.join(parts)

    ############################################################################
    # How to split and sort filenames
    ############################################################################

    def split_basename(self, basename=''):
        """Return the tuple with basename info: (anchor, suffix, extension).

        Default behavior is to split a file at first period; split a bundle set name
        before the suffix. Can be overridden.

        Keyword arguments:
            basename -- basename of a file (default '')
        """

        cls = type(self)

        if basename == '':
            basename = self.basename

        if self.SPLIT_RULES is None:
            return basename
        # Special case: bundleset[_...], bundleset[_...]_md5.txt, bundleset[_...].tar.gz
        matchobj = cls.BUNDLESET_PLUS_REGEX.match(basename)
        if matchobj is not None:
            return (matchobj.group(1), matchobj.group(2) + matchobj.group(3),
                    matchobj.group(4))

        # Special case: bundlename[_...]_md5.txt, bundlename[_...].tar.gz
        matchobj = cls.BUNDLENAME_PLUS_REGEX.match(basename)
        if matchobj is not None:
            test = self.SPLIT_RULES.first(basename) # a split rule overrides
                                                    # the default behavior
            if test == basename:
                return (matchobj.group(1), matchobj.group(2), matchobj.group(3))
            else:
                return test

        return self.SPLIT_RULES.first(basename)

    def basename_is_label(self, basename):
        """Return True if this basename is a label. Override if label identification
        ever depends on the data set.

        Keyword arguments:
            basename -- basename of a file
        """

        cls = type(self)
        return (len(basename) > 4) and (basename[-4:].lower() == cls.LBL_EXT)

    def basename_is_viewable(self, basename=None):
        """Return True if this basename is viewable. Override if viewable files can
        have extensions other than the usual set (.png, .jpg, etc.).

        Keyword arguments:
            basename -- basename of a file
        """

        cls = type(self)

        if basename is None:
            basename = self.basename

        parts = basename.rpartition('.')
        if parts[1] != '.': return False

        return (parts[2].lower() in cls.VIEWABLE_EXTS)

    def sort_basenames(self, basenames, labels_after=None, dirs_first=None,
                       dirs_last=None, info_first=None):
        """Return Sorted basenames, including additional options. Input None for
        defaults.

        Keyword arguments:
            basenames    -- a list of file basenames
            labels_after -- a flag used to determine if all label files should appear
                            after the associated data files when sorted (default None)
            dirs_first   -- a flag used to determine if directories should appear before
                            all files when sorted (default None)
            dirs_last    -- a flag used to determine if directories should appear after
                            all files when sorted (default None)
            info_first   -- a flag used to determine info files will be listed first in
                            all sorted lists (default None)
        """

        cls = type(self)

        def modified_sort_key(basename):

            # Volumes of the same name sort by decreasing version number
            matchobj = cls.BUNDLESET_PLUS_REGEX_I.match(basename)
            if matchobj is not None:
                splits = matchobj.groups()
                parts = [splits[0],
                         -cls.version_info(splits[1])[0],
                         matchobj.group(2),
                         matchobj.group(3)]
            else:
                # Otherwise, the sort is based on split_basename()
                modified = self.SORT_KEY.first(basename)
                splits = self.split_basename(modified)
                parts = [splits[0], 0, splits[1], splits[2]]

            if labels_after:
                # Replace (_, _, _, '.LBL') with (_, _, _, True, '.LBL')
                # Replace anything else with (_, _, _, False, _)
                parts[3:] = [self.basename_is_label(basename)] + parts[3:]

            if dirs_first or dirs_last:
                isdir = cls.os_path_isdir(_clean_join(self.abspath,
                                                          basename))
                if dirs_first:
                    # If this is a directory, put False in front of the sort key
                    # Otherwise, put True in front
                    parts = [not isdir] + parts
                else:
                    # If this is a directory, put True in front of the sort key
                    # Otherwise, put False in front
                    parts = [isdir] + parts

            if apply_info_first:
                # If this is an info file, put False in front of the sort key
                # Otherwise, put True in front
                parts = [self.info_basename != basename] + parts

            return tuple(parts)

        if labels_after is None:
            labels_after = self.SORT_ORDER['labels_after']

        if dirs_first is None:
            dirs_first = self.SORT_ORDER['dirs_first']

        if dirs_last is None:
            dirs_last = self.SORT_ORDER['dirs_last']

        if info_first is None:
            info_first = self.SORT_ORDER['info_first']

        # Put info file first only if the number of children exceeds the
        # specified threshold:
        #   info_first = 0 or False: never put info files first
        #   info_first = 1 or True: always put info files first
        #   info_first > 1: put info files first only if the number of files is
        #                   this large or larger
        apply_info_first = (int(info_first) >= 1 and
                            int(info_first) <= len(basenames))

        basenames = list(basenames)
        basenames.sort(key=modified_sort_key)
        return basenames

    def sort_sibnames(self, basenames, labels_after=None, dirs_first=None,
                      dirs_last=None, info_first=None):
        """Return sorted basenames that represent siblings of this object. In the
        returned list of basenames, the name of this object will be first and
        matching file names will always be adjacent.

        When a selected file and its label and/or targets are displayed in
        Viewmaster, this is the order in which they appear.

        Keyword arguments:
            basenames    -- a list of file basenames
            labels_after -- a flag used to determine if all label files should appear
                            after the associated data files when sorted (default None)
            dirs_first   -- a flag used to determine if directories should appear before
                            all files when sorted (default None)
            dirs_last    -- a flag used to determine if directories should appear after
                            all files when sorted (default None)
            info_first   -- a flag used to determine info files will be listed first in
                            all sorted lists (default None)
        """

        # First, sort the names the usual way
        parent = self.parent()

        if self.basename not in basenames:
            basenames.append(self.basename)

        basenames = parent.sort_basenames(basenames, labels_after, dirs_first,
                                                     dirs_last, info_first)

        # Create a new list with the name of self first
        basenames.remove(self.basename)
        new_basenames = [self.basename]

        # Move any set of files with matching names immediately after it
        pattern = self.basename.partition('.')[0] + '.'    # first dot, not last
        matches = [b for b in basenames if b.startswith(pattern)]
        if matches:
            for match in matches:
                basenames.remove(match)
                new_basenames.append(match)

        # Return the reordered and merged lists
        return new_basenames + basenames

    def sort_siblings(self, siblings, labels_after=None, dirs_first=None,
                      dirs_last=None, info_first=None):
        """Return sorted siblings of this object, keeping this object first.

        Keyword arguments:
            siblings     -- a list of file siblings
            labels_after -- a flag used to determine if all label files should appear
                            after the associated data files when sorted (default None)
            dirs_first   -- a flag used to determine if directories should appear before
                            all files when sorted (default None)
            dirs_last    -- a flag used to determine if directories should appear after
                            all files when sorted (default None)
            info_first   -- a flag used to determine info files will be listed first in
                            all sorted lists (default None)
        """

        # Create a dictionary by basename; remove duplicates too
        basename_dict = {pdsf.basename:pdsf for pdsf in siblings}
        basename_dict[self.basename] = self

        # Sort the basenames
        sibnames = self.sort_sibnames(list(basename_dict.keys()),
                                      labels_after, dirs_first, dirs_last,
                                      info_first)

        # Return the PdsFiles in the newly sorted order
        return [basename_dict[basename] for basename in sibnames]

    @classmethod
    def sort_logical_paths(cls, logical_paths):
        """Retrun sorted list of logical paths. Sort a list of logical paths, using the
        sort order at each level in the directory tree. The logical paths must all have
        the same number of directory levels.

        Keyword arguments:
            logical_paths -- a list of logical paths
        """

        # Create a dictionary of PdsFile objects keyed by logical path/subpath.
        # Also create a dictionary with the same key, containing a list of
        # enclosed names.
        pdsf_dict = {}      # pdsf_dict[logical_path] = PdsFile object
        child_names = {}    # child_names[logical_path] = list of child names
        top_level_names = set()
        for path in logical_paths:
            parts = path.split('/')
            top_level_names.add(parts[0])
            for k in range(1,len(parts)):
                path = '/'.join(parts[:k])
                if path not in pdsf_dict:
                    pdsf = cls.from_logical_path(path)
                    pdsf_dict[path] = pdsf
                    child_names[path] = set()

                child_names[path].add(parts[k])

        # Sort the contents of each directory, replacing each set with a list
        for (path, names) in child_names.items():
            child_names[path] = pdsf_dict[path].sort_basenames(list(names))

        # Sort keys at each level, recursively

        def _append_recursively(path):
            for name in child_names[path]:
                newpath = path + '/' + name
                if newpath in child_names:
                    _append_recursively(newpath)
                else:
                    sorted_paths.append(newpath)

        top_level_names = list(top_level_names)     # normally just one
        top_level_names.sort()

        sorted_paths = []
        for key in top_level_names:
            _append_recursively(key)

        # Under normal circumstances, the list of sorted_paths should be
        # complete. However, just in case...
        extras_in_sort = []
        logical_paths = set(logical_paths)
        for path in sorted_paths.copy():    # a copy so we can modify original
            if path in logical_paths:
                logical_paths.remove(path)
            else:
                extras_in_sort.append(path)
                sorted_paths.remove(path)

        if extras_in_sort and cls.LOGGER:
            for extra in extras_in_sort:
                cls.LOGGER.warn('Extra item removed by sort_logical_paths: ' + extra)

        logical_paths = list(logical_paths)
        logical_paths.sort()
        sorted_paths += logical_paths
        if logical_paths and cls.LOGGER:
            for path in logical_paths:
                cls.LOGGER.warn('Overlooked item added by sort_logical_paths: ' + path)

        return sorted_paths

    def sort_childnames(self, labels_after=None, dirs_first=None):
        """Return a sorted list of the contents of this directory.

        Keyword arguments:
            labels_after -- a flag used to determine if all label files should appear
                            after the associated data files when sorted (default None)
            dirs_first   -- a flag used to determine if directories should appear before
                            all files when sorted (default None)
        """

        return self.sort_basenames(self.childnames, labels_after, dirs_first)

    def viewable_childnames(self):
        """Return A sorted list of the files in this directory that are viewable."""

        return [b for b in self.childnames if self.basename_is_viewable(b)]

    def childnames_by_anchor(self, anchor):
        """Return a list of child basenames having the given anchor.

        Keyword arguments:
            anchor -- anchor of a basename
        """

        matches = []
        for basename in self.childnames:
            parts = self.split_basename(basename)
            if parts[0] == anchor:
                matches.append(basename)

        return matches

    def viewable_childnames_by_anchor(self, anchor):
        """Return a list of viewable child names having the given anchor.

        Keyword arguments:
            anchor -- anchor of a basename
        """

        matches = self.childnames_by_anchor(anchor)
        return [m for m in matches if self.basename_is_viewable(m)]

    ############################################################################
    # Transformations
    ############################################################################

    #### ... for pdsfiles

    @staticmethod
    def abspaths_for_pdsfiles(pdsfiles, must_exist=False):
        if must_exist:
            return [p.abspath for p in pdsfiles if p.abspath is not None
                                                and p.exists]
        else:
            return [p.abspath for p in pdsfiles if p.abspath is not None]

    @staticmethod
    def logicals_for_pdsfiles(pdsfiles, must_exist=False):
        if must_exist:
            return [p.logical_path for p in pdsfiles if p.exists]
        else:
            return [p.logical_path for p in pdsfiles]

    @staticmethod
    def basenames_for_pdsfiles(pdsfiles, must_exist=False):
        if must_exist:
            return [p.basename for p in pdsfiles if p.exists]
        else:
            return [p.basename for p in pdsfiles]

    #### ... for abspaths

    @classmethod
    def pdsfiles_for_abspaths(cls, abspaths, must_exist=False):
        pdsfiles = [cls.from_abspath(p) for p in abspaths]
        if must_exist:
            pdsfiles = [pdsf for pdsf in pdsfiles if pdsf.exists]

        return pdsfiles

    @classmethod
    def logicals_for_abspaths(cls, abspaths, must_exist=False):
        if must_exist:
            abspaths = [p for p in abspaths if cls.os_path_exists(p)]

        return [logical_path_from_abspath(p, cls) for p in abspaths]

    @classmethod
    def basenames_for_abspaths(cls, abspaths, must_exist=False):
        if must_exist:
            abspaths = [p for p in abspaths if cls.os_path_exists(p)]

        return [os.path.basename(p) for p in abspaths]

    #### ... for logicals

    @classmethod
    def pdsfiles_for_logicals(cls, logical_paths, must_exist=False):
        pdsfiles = [cls.from_logical_path(p) for p in logical_paths]
        if must_exist:
            pdsfiles = [pdsf for pdsf in pdsfiles if pdsf.exists]

        return pdsfiles

    @classmethod
    def abspaths_for_logicals(cls, logical_paths, must_exist=False):
        abspaths = [abspath_for_logical_path(p, cls) for p in logical_paths]
        if must_exist:
            abspaths = [p for p in abspaths if cls.os_path_exists(p)]

        return abspaths

    @classmethod
    def basenames_for_logicals(cls, logical_paths, must_exist=False):
        if must_exist:
            pdsfiles = cls.pdsfiles_for_logicals(logical_paths,
                                                     must_exist=must_exist)
            return cls.basenames_for_pdsfiles(pdsfiles)
        else:
            return [os.path.basename(p) for p in logical_paths]

    #### ... for basenames

    def pdsfiles_for_basenames(self, basenames, must_exist=False):

        pdsfiles = [self.child(b) for b in basenames]

        if must_exist:
            pdsfiles = [p for p in pdsfiles if p.exists]

        return pdsfiles

    def abspaths_for_basenames(self, basenames, must_exist=False):
        # shortcut
        if self.abspath and not must_exist:
            return [_clean_join(self.abspath, b) for b in basenames]

        pdsfiles = self.pdsfiles_for_basenames(basenames, must_exist=must_exist)
        return [pdsf.abspath for pdsf in pdsfiles]

    def logicals_for_basenames(self, basenames, must_exist=False):
        # shortcut
        if not must_exist:
            return [_clean_join(self.logical_path, b) for b in basenames]

        pdsfiles = self.pdsfiles_for_basenames(basenames, must_exist=must_exist)
        return [pdsf.logical_path for pdsf in pdsfiles]

    ############################################################################
    # Associations
    ############################################################################

    def associated_logical_paths(self, category, must_exist=True):
        cls = type(self)
        abspaths = self.associated_abspaths(category, must_exist=must_exist)
        return cls.logicals_for_abspaths(abspaths)

    def associated_pdsfiles(self, category, must_exist=True):
        cls = type(self)
        abspaths = self.associated_abspaths(category, must_exist=must_exist)
        return cls.pdsfiles_for_abspaths(abspaths)

    def associated_abspaths(self, category, must_exist=True):
        """A list of logical or absolute paths to associated files in the
        specified category.

        Keyword arguments:
            category   -- the category of the associated paths
            must_exist -- True to return only paths that exist (default True)
        """
        cls = type(self)
        category = category.strip('/')

        # Handle special case of an index row
        # Replace self by either the file associated with the row or else by
        # the parent index file.
        if self.is_index_row:
            test_abspath = self.data_abspath_associated_with_index_row()
            if test_abspath and cls.os_path_exists(test_abspath):
                self = cls.from_abspath(test_abspath)
            else:
                self = self.parent()

        # Handle checksums by finding associated files in subcategory
        if category.startswith('checksums-'):
            subcategory = category[len('checksums-'):]
            abspaths = self.associated_abspaths(subcategory,
                                                must_exist=must_exist)

            new_abspaths = []
            for abspath in abspaths:
                pdsf = cls.from_abspath(abspath)
                try:
                    new_abspaths.append(pdsf.checksum_path_and_lskip()[0])
                # This can happen for associations to cumulative metadata files.
                # These are associated with bundlesets, not bundles, and bundlesets
                # have no checksum files.
                except ValueError:
                    pass

            # Remove duplicates
            new_abspaths = [p for (k,p) in enumerate(new_abspaths)
                            if p not in new_abspaths[:k]]
            return new_abspaths

        # Handle archives by finding associated files in subcategory
        if category.startswith('archives-'):
            subcategory = category[len('archives-'):]
            abspaths = self.associated_abspaths(subcategory,
                                                must_exist=must_exist)

            new_abspaths = []
            for abspath in abspaths:
                pdsf = cls.from_abspath(abspath)
                try:
                    new_abspaths.append(pdsf.archive_path_and_lskip()[0])
                # This can happen for associations to cumulative metadata files.
                # These are associated with bundlesets, not bundles, and bundlesets
                # have no archives.
                except ValueError:
                    pass

            # Remove duplicates
            new_abspaths = [p for (k,p) in enumerate(new_abspaths)
                            if p not in new_abspaths[:k]]
            return new_abspaths

        # No more recursive calls...

        # Check for any associations defined by rules
        logical_paths = self.ASSOCIATIONS[category].all(self.logical_path)
        patterns = cls.abspaths_for_logicals(logical_paths)

        # If no rules apply, search in the parallel directory tree
        if not patterns:
            pdsf = self.associated_parallel(category)
            if pdsf and pdsf.abspath:
                patterns = [pdsf.abspath]

        abspaths = []
        for pattern in patterns:

            # Handle an index row by separating the filepath from the suffix
            if f'{cls.IDX_EXT}/' in pattern:
                parts = pattern.rpartition(cls.IDX_EXT)
                pattern = parts[0] + parts[1]
                suffix = parts[2][1:]
            else:
                suffix = ''

            # Find the file(s) that match the pattern
            if not must_exist and not _needs_glob(pattern):
                test_abspaths = [pattern]
            else:
                test_abspaths = cls.glob_glob(pattern, force_case_sensitive=True)
            # With a suffix, make sure it matches a row of the index
            if suffix:
                filtered_abspaths = []
                for abspath in test_abspaths:
                    try:
                        parent = cls.from_abspath(abspath)
                        pdsf = parent.child_of_index(suffix)
                        filtered_abspaths.append(pdsf.abspath)
                    except (KeyError, IOError):
                        pass

                test_abspaths = filtered_abspaths

            abspaths += test_abspaths

        # Include any labels and targets
        if category == self.voltype_[:-1]:
            label_basename = self.label_basename
            if label_basename:
                parent_abspath = os.path.split(self.abspath)[0]
                label_abspath = _clean_join(parent_abspath, label_basename)
                if label_abspath not in abspaths:
                    abspaths.append(label_abspath)

            abspaths += self.data_abspaths

        # Remove duplicates
        abspaths = [p for (k,p) in enumerate(abspaths) if p not in abspaths[:k]]
        return abspaths

    def associated_parallel(self, category=None, rank=None):
        """Return a PdsFile of the "most similar" absolute path in a parallel directory
        tree, specified by category and/or version rank. If the rank is unspecified, it
        will match the version of self when the voltype of the new category matches the
        voltype of self; otherwise, it will return the latest version.

        In addition to numeric values for the rank, values of "next", "previous", and
        "latest" can also be used when the voltype of the returned object matches that
        of this object.

        Keyword arguments:
            category -- the category of the associated paths (default None)
            rank     -- the version rank (default None)
        """

        cls = type(self)

        def _cache_and_return(pdsf):
            """Return a PdsFile. For internal use. Convert to PdsFile if necessary, cache
            under one or two ranks (rank and rankstr), return. Also, if pdsf matches self,
            cache and return None instead.

            Keyword arguments:
                pdsf -- a PdsFile instance
            """

            # Interpret the pdsf and get the abspath (both might be None)
            if isinstance(pdsf, str):
                abspath = pdsf
                pdsf = cls.from_abspath(abspath)
            elif pdsf is None:
                abspath = None
            else:
                abspath = pdsf.abspath

            # Confirm existence; otherwise replace with None
            if pdsf and not pdsf.exists:
                pdsf = None
                abspath = None

            # Cache under rank and (maybe) rankstr
            self._associated_parallels_filled[category, rank] = abspath

            if rankstr:
                self._associated_parallels_filled[category, rankstr] = abspath

            if rank is None and pdsf is not None:
                self._associated_parallels_filled[category,
                                                  pdsf.version_rank] = abspath

            # Re-cache this and return result
            self._recache()
            return pdsf

        # Interpret the category
        if category is None:
            category = self.category_[:-1]
            voltype = self.voltype_[:-1]
        else:
            category = category.rstrip('/')
            voltype = category.rpartition('-')[-1]

        if category not in cls.CATEGORIES:
            return None

        # Handle category-level parallel
        if self.is_category_dir:
            return cls.from_logical_path(category)

        # Handle a change in voltype
        if voltype != self.voltype_[:-1]:

            # Rank "latest" works; "previous" and "next" do not
            if rank == 'latest':
                rank = None

            # Switch to the latest version of self before finding the parallel
            # This re-definition of "self" looks weird but it works fine.
            latest_rank = max(self.all_version_abspaths.keys())
            if self.version_rank != latest_rank:
                self = self.all_versions()[latest_rank]

        # Create the cached dictionary if necessary
        if self._associated_parallels_filled is None:
            self._associated_parallels_filled = {}

        # Return from dictionary if already available
        if (category, rank) in self._associated_parallels_filled:
            abspath = self._associated_parallels_filled[category, rank]
            return cls.from_abspath(abspath) if abspath else None

        # Interpret the rank
        if isinstance(rank, str):
            rankstr = rank

            if voltype != self.voltype_[:-1]:
                raise ValueError(f'rank "{rank}" not supported')

            this_rank = self.version_rank
            all_ranks = list(self.all_version_abspaths.keys())
            all_ranks.sort()
            this_index = all_ranks.index(this_rank)
            if rank == 'latest':
                new_index = len(all_ranks) - 1
            elif rank == 'previous':
                new_index = max(this_index - 1, 0)
            elif rank == 'next':
                new_index = min(this_index + 1, len(all_ranks) - 1)
            else:
                raise ValueError(f'unrecognized rank value "{rank}"')

            rank = all_ranks[new_index]

            if (category, rank) in self._associated_parallels_filled:
                abspath = self._associated_parallels_filled[category, rank]
                return cls.from_abspath(abspath) if abspath else None

        else:
            rankstr = ''

        # Handle a bundleset-level parallel
        if not self.bundlename:
            parallel = self.volset_pdsfile(category, rank)
            return _cache_and_return(parallel)

        # If category is unchanged, use all_versions() instead
        if category == self.category_[:-1]:
            if rank is None:
                rank = max(self.all_version_abspaths.keys())
            return _cache_and_return(self.all_versions().get(rank,None))

        # Prepare for parallel volume tree comparion
        old_root = self.volume_pdsfile()
        new_root = self.volume_pdsfile(category, rank)

        if not new_root:
            # If there's no volume-level match, try the volset-leve match
            # This happens for category = 'checksums-archives-whatever'
            return _cache_and_return(self.volset_pdsfile(category, rank))

        if new_root.abspath == old_root.abspath:
            return _cache_and_return(self)

        if not new_root.isdir:                      # can't match any deeper
            return _cache_and_return(new_root)

        if not self.interior:                       # no reason to go deeper
            return _cache_and_return(new_root)

        # Search down from the volume root for the longest parallel file path
        abspath = new_root.abspath + '/' + self.interior
        while abspath:
            if cls.os_path_exists(abspath):
                return _cache_and_return(abspath)
            abspath = abspath.rpartition('/')[0]

        return _cache_and_return(None)              # This should never happen

    @classmethod
    def is_logical_path(cls, path):
        """Return True if the given path appears to be a logical path; False
        otherwise.

        Keyword arguments:
            path -- the path of a file
        """

        return (f'/{cls.PDS_HOLDINGS}/' not in path)

##########################################################################################
# Initialize the global registry of subclasses
##########################################################################################
PdsFile.SUBCLASSES['default'] = PdsFile

##########################################################################################
# After the constructors are defined, always create and cache permanent,
# category-level merged directories. These are roots of the cache tree and they
# their childen are be assembled from multiple physical directories.

# This is needed in cases where preload() is never called. Each call to
# preload() replaces these.
##########################################################################################
PdsFile.cache_category_merged_dirs()
