##########################################################################################
# pdsfile/pdsfile.py
# General pdsfile package & PdsFile class
##########################################################################################

"""The PdsFile class and the modules its method groups live in.

This module holds the `class PdsFile` statement, everything that is about a
PdsFile *object* rather than about one subject area, and re-exports every name it
has ever exported. Ten private modules beside it hold the rest -- nine of them
mixin bases of PdsFile, the tenth (_path_utils) plain module functions:

    _associations.py    _AssociationsMixin -- the four associated_* methods that
                        map a file to its counterparts in the other voltypes
    _derived_paths.py   _DerivedPathsMixin -- checksum, archive and log path
                        builders, and set_log_root
    _index_rows.py      _IndexRowsMixin -- index shelves and the pseudo-children
                        that stand for rows of an index table
    _local_fs.py        _LocalFsMixin -- the case-repairing, SHELVES_ONLY-aware
                        filesystem layer (os_path_exists, os_path_isdir,
                        os_listdir, glob_glob and _non_checksum_abspath) and
                        PATH_EXISTS_CACHE_SIZE
    _opus.py            _OpusMixin -- opus_products, and the two constructors
                        that resolve an OPUS ID (from_opus_id) or a bundle-name
                        file specification (from_filespec)
    _path_utils.py      the path helpers that take no PdsFile object:
                        repair_case, abspath_for_logical_path,
                        logical_path_from_abspath, construct_category_list,
                        formatted_file_size, selected_path_from_path, the
                        _clean_* primitives and _needs_glob, plus
                        FILE_BYTE_UNITS and _GLOB_CACHE_SIZE. Not a mixin
    _preload.py         _PreloadMixin -- preload and the cache it fills, plus the
                        module-level cache_lifetime_for_class, is_preloading,
                        pause_caching, resume_caching, the four cache-lifetime
                        constants, DICTIONARY_CACHE_LIMIT and HAS_PYLIBMC
    _properties.py      _PropertiesMixin -- the largest group: 64 properties, 40
                        of them lazy (fill an _X_filled slot, then -- in 39 of the
                        40 -- _recache() so the cache keeps the filled object) and
                        24 recomputed on every access, plus version_info,
                        all_versions, viewset_lookup and _repair_width_height
    _shelves.py         _ShelfMixin -- opening, caching and reading the shelf
                        files that hold precomputed metadata, with the eval of a
                        .py sidecar isolated in one named function
    _sorting.py         _SortingMixin -- the sort rules, the childname selectors,
                        and the twelve conversions among abspaths, logical paths,
                        basenames and PdsFile objects

`preload_and_cache.py` is public and stays public; it is now a re-export shim
over _preload.py.

What stays here, and why:

  * The `class PdsFile` statement. Pickled PdsFile instances -- Viewmaster's
    memcached cache holds live ones -- record `pdsfile.pdsfile` as the class's
    module, so moving the statement would invalidate them.
  * Every class attribute: the configuration tables, the translator registries,
    the shared CACHE and LOGGER, SHELF_CACHE and friends, LOG_ROOT_,
    LATEST_VERSION_RANKS. A mixin carries behavior only, so the data a mixin
    reads is defined here and reached as cls.X at run time.
  * __init__ and the _X_filled slots it creates, _complete,
    _update_ranks_and_vols and _recache -- the object's own lifecycle, which the
    properties in _properties.py drive through self.
  * The constructors: child, parent, from_abspath, from_logical_path, from_path,
    from_lid, from_relative_path, _from_absolute_or_logical_path, new_pdsfile,
    new_merged_dir, new_index_row_pdsfile, copy, __repr__.
  * The bundle and bundleset utilities, the sort-order setters, the
    use_shelves_only / require_shelves / set_logger / set_easylogger class
    configuration, and is_logical_path.

Mechanics that hold for all nine modules: a mixin defines no __init__ and no new
state; it never imports pdsfile.pdsfile at module level (pdsfile.py imports the
mixins, so that would be a cycle -- a method needing the class object uses a
function-local import instead); and the bases below are listed alphabetically.
tests/api/test_mixin_collisions.py checks that the mixins are disjoint, that
nothing shadows them, that they hold no state and that the order is alphabetical;
tests/api/test_mixin_import_isolation.py checks the no-back-import rule by
loading each module in a fresh interpreter.

The split is invisible to a caller's code: pdsfile.pdsfile.<name> still resolves
for every name it resolved for before, and nothing a caller imports or calls has
moved or been renamed. It does show in __module__, __qualname__ and __mro__.
"""

import os
import re

# None of these ten is referenced below; they are re-exported for callers that
# reach them as pdsfile.pdsfile.<name>. The redundant `as` alias is the explicit
# re-export form.
import bisect as bisect
import datetime as datetime
import fnmatch as fnmatch
import functools as functools
import glob as glob
import math as math
import numbers as numbers
import pickle as pickle
import PIL as PIL
import time as time

import pdslogger
import translator

# pdstable is used by the index-row methods, defaultdict by the OPUS methods and
# pdsparser by the lazy properties, which live in _index_rows.py, _opus.py and
# _properties.py; all three are also reachable as pdsfile.pdsfile.<name>, so they
# are bound here in the same redundant-alias form as the ten above.
import pdsparser as pdsparser
import pdstable as pdstable

from collections import defaultdict as defaultdict
from pdsfile import pdscache

from ._preload import cache_lifetime_for_class

# The path helpers live in a private module. Importing them here is also what
# keeps pdsfile.pdsfile.<name> resolving for callers.
from ._path_utils import (_clean_join,
                          abspath_for_logical_path,
                          construct_category_list,
                          logical_path_from_abspath,
                          repair_case)

# Nine groups of PdsFile methods live in private modules as mixins, and the class
# statement below takes them as bases. The bases are listed alphabetically: the
# mixins share no attribute name and none shadows a name PdsFile defines itself
# (tests/api/test_mixin_collisions.py asserts both), so the order carries no
# meaning and a mechanical rule keeps it checkable as more mixins arrive.
from ._associations import _AssociationsMixin
from ._derived_paths import _DerivedPathsMixin
from ._index_rows import _IndexRowsMixin
from ._local_fs import _LocalFsMixin
from ._opus import _OpusMixin
from ._preload import _PreloadMixin
from ._properties import _PropertiesMixin
from ._shelves import _ShelfMixin
from ._sorting import _SortingMixin

# Re-exported only; nothing below references these. FILE_BYTE_UNITS,
# formatted_file_size, HAS_PYLIBMC, PATH_EXISTS_CACHE_SIZE, pause_caching,
# pdsviewable, resume_caching and selected_path_from_path are public;
# _GLOB_CACHE_SIZE, _clean_abspath, _clean_glob and _needs_glob are private. All
# are carried so that no name reachable as pdsfile.pdsfile.<name> is lost. The
# redundant `as` alias is the explicit re-export form, so they do not read as
# unused imports.
from pdsfile import pdsviewable as pdsviewable

from ._local_fs import PATH_EXISTS_CACHE_SIZE as PATH_EXISTS_CACHE_SIZE
from ._path_utils import (FILE_BYTE_UNITS as FILE_BYTE_UNITS,
                          _GLOB_CACHE_SIZE as _GLOB_CACHE_SIZE,
                          _clean_abspath as _clean_abspath,
                          _clean_glob as _clean_glob,
                          _needs_glob as _needs_glob,
                          formatted_file_size as formatted_file_size,
                          selected_path_from_path as selected_path_from_path)
from ._preload import (HAS_PYLIBMC as HAS_PYLIBMC,
                       pause_caching as pause_caching,
                       resume_caching as resume_caching)

##########################################################################################
# PdsFile class
##########################################################################################

class PdsFile(_AssociationsMixin, _DerivedPathsMixin, _IndexRowsMixin, _LocalFsMixin,
              _OpusMixin, _PreloadMixin, _PropertiesMixin, _ShelfMixin, _SortingMixin):

    # Configuration
    VOLTYPES = ['volumes', 'calibrated', 'diagrams', 'metadata', 'previews',
                'documents', 'bundles']
    VIEWABLE_VOLTYPES = ['previews', 'diagrams']

    VIEWABLE_EXTS = {'jpg', 'png', 'gif', 'tif', 'tiff', 'jpeg', 'jpeg_small'}
    DATAFILE_EXTS = {'dat', 'img', 'cub', 'qub', 'fit', 'fits'}

    CATEGORY_REGEX      = re.compile(r'^(|checksums\-)(|archives\-)(\w+)$')
    CATEGORY_REGEX_I    = re.compile(CATEGORY_REGEX.pattern, re.I)

    VIEWABLE_ANCHOR_REGEX = re.compile(r'(.*/\w+)_[a-z]+\.(jpg|png)')
    # path/A1234566_thumb.jpg -> path/A1234566

    LOGFILE_TIME_FMT = '%Y-%m-%dT%H-%M-%S'

    PLAIN_TEXT_EXTS = {'lbl', 'txt', 'asc', 'tab', 'cat', 'fmt', 'f', 'c',
                       'cpp', 'pro', 'for', 'f77', 'py', 'inc', 'h', 'sh',
                       'idl', 'csh', 'tf', 'ti', 'tls', 'lsk', 'tsc'}

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

    PRODUCT_LBL_BASENAME_WO_EXT = None

    OPUS_ID_TO_SUBCLASS = None

    FILESPEC_TO_BUNDLESET = None

    FILENAME_KEYLEN = 0

    # Global will contain all the physical holdings directories on the system.
    LOCAL_HOLDINGS_DIRS = None

    # Name of the environment variable that locates this class's holdings tree.
    # Each subclass names its own; see abspath_for_logical_path().
    _HOLDINGS_ENV = 'PDS3_HOLDINGS_DIR'

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

        self.category_    = ''      # Always checksums_ + archives_ + bundletype_
        self.checksums_   = ''      # Either 'checksums-' or ''
        self.archives_    = ''      # Either 'archives-' or ''
        self.bundletype_     = ''      # One of 'volumes', 'metadata', etc.

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
        self._bundle_publication_date_filled = None
        self._bundle_version_id_filled       = None
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
            this.bundletype_        = self.bundletype_
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

    ############################################################################
    # Set parameters for both Pds3File and Pds4File
    ############################################################################
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

    ############################################################################
    # Merged directories, index rows, and object utilities
    ############################################################################
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
        this.bundletype_     = basename.split('-')[-1].rstrip('/') + '/'

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
        this._bundle_publication_date_filled = ''
        this._bundle_version_id_filled       = ''
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
        this._bundle_publication_date_filled = self.bundle_publication_date
        this._bundle_version_id_filled       = self.bundle_version_id
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
        elif type(self) is PdsFile:
            return 'PdsFile("' + self.abspath + '")'
        else:
            return ('PdsFile.' + type(self).__name__ + '("' +
                    self.abspath + '")')

    ############################################################################
    # Version ranks
    ############################################################################

    # The ranks that mean "not superseded". The version methods live in
    # _properties.py; the alternative constructors below read this off the class.
    LATEST_VERSION_RANKS = [990100, 990200, 990300, 990400, 999999]

    ############################################################################
    # Utilities
    ############################################################################

    def bundle_pdsfile(self, category=None, rank=None):
        """Return PdsFile object for the root bundle file or directory associated with
        this or another category and this or another version. It returns None if the file
        does not exist.

        Keyword arguments:
            category -- the category of the bundle (default None)
            rank     -- the version rank of the bundle (default None)
        """

        cls = type(self)

        abspath = self.bundle_abspath(category)
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

    def bundleset_pdsfile(self, category=None, rank=None):
        """Return PdsFile object for the root bundle set for this or another category
        and this or another version. It returns None if the file does not exist.

        Keyword arguments:
            category -- the category of the bundleset (default None)
            rank     -- the version rank of the bundleset (default None)
        """

        cls = type(self)

        abspath = self.bundleset_abspath(category)
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
        # The bool() matters: without it a bundle set would yield the empty string
        # the `and` produces, not False.
        return bool(self.bundlename_ and not self.interior)

    @property
    def is_bundle_file(self):
        """Return True if this is a bundle-level checksum or archive file."""
        # The bool() matters: without it a bundle set would yield the empty string
        # the `and` produces, not False.
        return bool(self.bundlename and not self.bundlename_)

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

    def bundle_abspath(self, category=None):
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

        if parts[-1] == self.bundletype_:
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

    def bundleset_abspath(self, category=None):
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

        if parts[-1] == self.bundletype_:
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
            raise OSError('File not found', self.abspath)

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
        if not self.category_:
            return self

        # Do not cache nonexistent objects
        if not self.exists:
            return self

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
        elif ((self.bundlename and not self.bundlename_) or
              (self.bundlename_ and not self.interior)):
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
            if fix_case and basename not in self.childnames:
                try:
                    k = self.childnames_lc.index(basename.lower())
                except ValueError:
                    pass
                else:
                    basename = self.childnames[k]

            # Create the logical path and touch the cache entry if there is
            # one. The looked-up object is discarded, not returned, so the
            # child is rebuilt below either way.
            child_logical_path = _clean_join(self.logical_path, basename)
            try:
                _ = cls.CACHE[child_logical_path.lower()]
            except KeyError:
                pass

            # Confirm existence if necessary
            basename_lc = basename.lower()
            if must_exist and basename_lc not in self.childnames_lc:
                raise OSError('File not found: ' + child_logical_path)

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
                    raise ValueError('Illegal bundle set directory '
                                     f'"{basename}": {self.logical_path}')
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
                    raise ValueError('Illegal bundle set directory '
                                     f'"{basename}": {this.logical_path}')

                this.bundleset_ = basename + '/'
                this.bundleset  = matchobj.group(1)
                this.suffix  = '' if matchobj.group(2) is None else matchobj.group(2)

                if len(matchobj.groups()) > 2 and matchobj.group(3):
                    this.bundleset_ = ''
                    this.interior = basename
                    parts = this.suffix.split('_')
                    if parts[-1] == this.bundletype_[:-1]:
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
                    raise ValueError(f'Invalid category "{basename}": '
                                     f'{this.logical_path}')

                if fix_case:
                    this.checksums_ = matchobj.group(1).lower()
                    this.archives_  = matchobj.group(2).lower()
                    this.bundletype_   = matchobj.group(3).lower() + '/'
                else:
                    this.checksums_ = matchobj.group(1)
                    this.archives_  = matchobj.group(2)
                    this.bundletype_   = matchobj.group(3) + '/'

                if this.bundletype_[:-1] not in cls.VOLTYPES:
                    raise ValueError('Unrecognized volume/bundle ' +
                                     f'type "{this.bundletype_[:-1]}": ' +
                                     f'{this.logical_path}')

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
            raise ValueError(f'{lid_str} is not a valid LID.')

        data_set_id = lid_component[0]
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
            pds_holdings_index = parts_lc.index(cls.PDS_HOLDINGS)
        except ValueError:
            raise ValueError(f'"{cls.PDS_HOLDINGS}" directory not found in: {abspath}')
        ### Pause the cache
        cls.CACHE.pause()
        try:
            # Fill in this.disk_, the absolute path to the directory containing
            # subdirectory "holdings"
            this = cls()
            this.disk_ = drive_spec + '/'.join(parts[:pds_holdings_index]) + '/'
            this.root_ = this.disk_ + cls.PDS_HOLDINGS + '/'

            # Get case right if necessary
            if fix_case:
                try:
                    this.disk_ = repair_case(this.disk_[:-1], cls) + '/'
                    this.root_ = repair_case(this.root_[:-1], cls) + '/'
                except OSError:
                    if must_exist:
                        raise

            # Fill in the HTML root. This is the text between "http://domain/"
            # and the logical path to appear in a URL that points to the file.
            # Viewmaster creates symlinks inside /Library/WebServer/Documents
            # named holdings, holding1, ... holdings9

            if len(cls.LOCAL_PRELOADED) <= 1:   # There's only one holdings dir
                this.html_root_ = '/' + cls.PDS_HOLDINGS +'/'
            else:                       # Find this holdings dir among preloaded
                pds_holdings_abspath = this.disk_ + cls.PDS_HOLDINGS
                try:
                    k = cls.LOCAL_PRELOADED.index(pds_holdings_abspath)
                except ValueError:
                    cls.LOGGER.warn('No URL: ' + pds_holdings_abspath)
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
            for part in parts[pds_holdings_index + 1:]:
                this = this.child(part, fix_case=fix_case, must_exist=must_exist,
                                  caching=caching, lifetime=lifetime)

            if must_exist and not this.exists:
                raise OSError('File not found', this.abspath)

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
            raise OSError('from_path is not supported without a preload')

        path = str(path)    # make sure it's a string
        path = path.rstrip('/')
        # if there is .targz, treat it as .tar.gz
        path = path.replace('.targz', '.tar.gz')
        if path == '':
            path = 'volumes'    # prevents an error below

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
                this.bundletype_ = part + '/'

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
                this.bundletype_ = part + '/'

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
                suffix    = matchobj.group(2).lower() if matchobj.group(2) else ''
                extension = ((matchobj.group(3) + matchobj.group(4)).lower()
                             if len(matchobj.groups()) > 2 else '')

                # <bundleset>...tar.gz must be an archive file
                if extension.endswith('.tar.gz'):
                    this.archives_ = 'archives-'

                # <bundleset>..._md5.txt must be a checksum file
                elif extension.endswith('_md5.txt'):
                    this.checksums_ = 'checksums-'

                # <bundleset>_diagrams... must be in the diagrams tree, etc.
                for test_type in cls.VOLTYPES:
                    if extension[1:].startswith(test_type):
                        this.bundletype_ = test_type + '/'
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
                if len(matchobj.groups()) > 2 and matchobj.group(3):
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
                            this.bundletype_ = test_type + '/'
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
        if this.bundletype_ == '':
            this.bundletype_ = cls.BUNDLE_DIR_NAME + '/'

        this.category_ = this.checksums_ + this.archives_ + this.bundletype_

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
                    for bundleset in cls.CACHE['$RANKS-' + this.category_]:
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
                    raise ValueError(f'Suffix "{this.suffix}" not found: '
                                     f'{path}')

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
                    raise ValueError(f'Suffix "{this.suffix}" not found: '
                                     f'{path}')

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
    # Shelf support
    ############################################################################

    SHELF_CACHE = {}
    SHELF_ACCESS = {}
    SHELF_CACHE_SIZE = 120
    SHELF_CACHE_SLOP = 20
    SHELF_ACCESS_COUNT = 0

    SHELF_NULL_KEY_VALUES = {}

    ############################################################################
    # Log path associations
    ############################################################################

    # The methods that build a log path live in _derived_paths.py; they read this
    # off the class, and set_log_root writes it back onto the class.
    LOG_ROOT_ = None

    ############################################################################
    # Logical path test
    ############################################################################

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
