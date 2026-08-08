##########################################################################################
# pdsfile/pdsfile.py
# General pdsfile package & PdsFile class
##########################################################################################

"""The ``PdsFile`` class, and the map of the modules its methods live in.

A ``PdsFile`` stands for one file or directory in a PDS holdings tree. It knows where
that file sits in the tree's taxonomy -- which category, bundleset, bundle and interior
path it belongs to -- and answers questions about it: its metadata, the files associated
with it, the images that display it, and the paths of its checksum, archive and log
counterparts.

This module holds the ``class PdsFile`` statement, everything that is about a
``PdsFile`` *object* rather than about one subject area, and the imports that put the
package's public names in this module's namespace. Ten private modules beside it hold
the rest. Nine are mixin bases of ``PdsFile``; the tenth, ``_path_utils``, is plain
module functions.

  * ``_associations.py`` -- ``_AssociationsMixin``: the four ``associated_*`` methods,
    which map a file to its counterparts in the other voltypes.
  * ``_derived_paths.py`` -- ``_DerivedPathsMixin``: the checksum, archive and log path
    builders, and ``set_log_root``.
  * ``_index_rows.py`` -- ``_IndexRowsMixin``: index shelves, and the pseudo-children
    that stand for rows of an index table.
  * ``_local_fs.py`` -- ``_LocalFsMixin``: the filesystem layer that answers from the
    info shelves under ``SHELVES_ONLY`` (``os_path_exists``, ``os_path_isdir``,
    ``os_listdir``, ``glob_glob`` and ``_non_checksum_abspath``), and
    ``PATH_EXISTS_CACHE_SIZE``.
  * ``_opus.py`` -- ``_OpusMixin``: ``opus_products``, and the two constructors that
    resolve an OPUS ID (``from_opus_id``) or a bundle-name file specification
    (``from_filespec``).
  * ``_path_utils.py`` -- the path helpers that take no ``PdsFile`` object:
    ``repair_case``, ``abspath_for_logical_path``, ``logical_path_from_abspath``,
    ``construct_category_list``, ``formatted_file_size``, ``selected_path_from_path``,
    the three ``_clean_*`` primitives and ``_needs_glob``, plus ``FILE_BYTE_UNITS`` and
    ``_GLOB_CACHE_SIZE``. Not a mixin.
  * ``_preload.py`` -- ``_PreloadMixin``: ``preload`` and the cache it fills, along with
    ``get_permanent_values``, ``load_volume_info``, ``cache_lifetime`` and
    ``cache_category_merged_dirs``, which is the call at the foot of this file; plus the
    module-level ``cache_lifetime_for_class``, ``is_preloading``, ``pause_caching``,
    ``resume_caching``, the four cache-lifetime constants, ``DICTIONARY_CACHE_LIMIT``
    and ``HAS_PYLIBMC``.
  * ``_properties.py`` -- ``_PropertiesMixin``: the largest group. 64 properties, of
    which 40 are lazy (they fill a private slot on first access and then, in 39 of the
    40, call ``_recache()`` so the cached object keeps the filled value) and 24 are
    recomputed on every access; plus ``version_info``, ``all_versions``,
    ``viewset_lookup`` and ``_repair_width_height``.
  * ``_shelves.py`` -- ``_ShelfMixin``: opening, caching and reading the shelf files
    that hold precomputed metadata, with the ``eval`` of a ``.py`` sidecar isolated in
    one named function.
  * ``_sorting.py`` -- ``_SortingMixin``: the sort rules, the childname selectors, and
    the twelve conversions among absolute paths, logical paths, basenames and
    ``PdsFile`` objects.

``preload_and_cache.py`` is the public module for the preload subsystem; ``_preload.py``
is where that subsystem is implemented.

What this module holds, and why:

  * The ``class PdsFile`` statement. A pickled instance records the module of its **own**
    class, and every object a resolved holdings path produces is a rule subclass, so what
    a Viewmaster memcached entry names is ``pdsfile.pds3file.rules.<dataset>`` rather than
    this module. The exception is ``new_merged_dir()``, which builds ``cls()`` and so
    records this module when it is called on ``PdsFile`` itself. The statement stays here
    because the class attributes below it do, not because moving it would invalidate a
    cache.
  * Every class attribute: the configuration tables, the translator registries, the
    shared ``CACHE`` and ``LOGGER``, ``SHELF_CACHE`` and its companions, ``LOG_ROOT_``
    and ``LATEST_VERSION_RANKS``. A mixin carries behavior only, so the data a mixin
    reads is defined here, or on ``Pds3File`` and ``Pds4File`` where the two PDS versions
    disagree -- ``IDX_EXT`` and ``LBL_EXT`` are the two, and reading either on a bare
    ``PdsFile`` raises AttributeError -- and is reached as ``cls.X`` at run time.
  * ``__init__`` and the private slots it creates, ``_complete``,
    ``_update_ranks_and_vols`` and ``_recache`` -- the object's own lifecycle, which the
    properties in ``_properties.py`` drive through ``self``.
  * The constructors: ``child``, ``parent``, ``from_abspath``, ``from_logical_path``,
    ``from_path``, ``from_lid``, ``from_relative_path``,
    ``_from_absolute_or_logical_path``, ``new_pdsfile``, ``new_merged_dir``,
    ``new_index_row_pdsfile``, ``copy`` and ``__repr__``.
  * The bundle and bundleset utilities, the sort-order setters, the class configuration
    (``use_shelves_only``, ``require_shelves``, ``set_logger``, ``set_easylogger``) and
    ``is_logical_path``.

Mechanics that hold for all nine mixins: a mixin defines no ``__init__`` and no state of
its own; it never imports ``pdsfile.pdsfile`` at module level, because this module
imports the mixins and that would be a cycle, so a method needing the class object uses
a function-local import instead; and the bases in the class statement are listed
alphabetically. ``tests/api/test_mixin_collisions.py`` checks that the mixins are
disjoint, that nothing shadows them, that they hold no state and that the order is
alphabetical. ``tests/api/test_mixin_import_isolation.py`` checks the no-back-import
rule by loading each module in a fresh interpreter.

Every name this module binds is reachable as ``pdsfile.pdsfile.<name>``, and the public
ones among them are part of the package's frozen surface. That is what the import block
below is for: several of its imports are referenced nowhere in this file and exist only to
keep a name reachable, so deleting one because it looks unused removes the name. The
relation runs one way only -- the subclasses, the viewable classes and the preload module
are public and are not attributes of this module, and the nine mixins and the private path
helpers are attributes of it and are not public -- so the manifest in
``tests/api/api_manifest.json``, not this namespace, is what defines the surface. Where a
symbol is really defined shows in ``__module__``, ``__qualname__`` and ``__mro__``.
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
    """One file or directory in a PDS holdings tree.

    An instance is created through one of the alternative constructors --
    ``from_abspath()``, ``from_logical_path()``, ``from_path()``, ``child()``,
    ``parent()`` and their relatives -- never by calling the class, which returns a blank
    object with no path in it.

    A path is held twice. The logical path starts below the ``holdings/`` directory and
    identifies a file no matter which disk holds it; the absolute path names the file on
    this machine. The logical path is split across attributes that name the pieces of the
    tree's taxonomy: ``category_``, made of ``checksums_``, ``archives_`` and
    ``bundletype_``; then ``bundleset_`` with its ``bundleset`` and version ``suffix``;
    then ``bundlename_``; then ``interior``, the part below the bundle directory. An
    attribute whose name ends in an underscore is empty or already carries its own
    trailing separator -- a slash, except on ``checksums_`` and ``archives_``, whose
    separator is the hyphen in ``checksums-`` and ``archives-`` -- so the pieces
    concatenate into a path without any separator logic. With one exception:
    ``new_merged_dir()`` sets ``disk_``, ``root_`` and ``html_root_`` to None, and
    concatenating one of those raises rather than producing a path. The three Nones are
    copied on, so anything built below a merged directory carries them too, until
    ``_complete()`` finds a physical object already cached for the logical path and
    returns that instead.

    Most of what an instance can answer is a property, computed on first access and
    stored on the object. Some of those answers are cached beyond the object: an object
    completed through ``_complete()`` may go into the class-level ``CACHE``, keyed by its
    lowercased logical path, and a later request for the same path then gets the same
    object back rather than repeating the work. Which objects those are depends on
    ``DEFAULT_CACHING``, and under its default of ``'dir'`` an ordinary data file is not
    among them: two constructor calls for the same file give two objects, each of which
    recomputes its own properties. ``preload()`` fills the cache in bulk from a holdings
    tree.

    The cache is per class rather than per package. ``Pds3File`` and ``Pds4File`` each
    define their own ``CACHE``, so the two PDS versions share nothing, and neither shares
    with ``PdsFile``.

    The class is not used directly. ``Pds3File`` and ``Pds4File`` subclass it, one per PDS
    version, and each fills in the configuration tables and the regular expressions that
    make path parsing work; the per-bundleset rule modules subclass those in turn and are
    selected through ``SUBCLASSES`` and ``VOLSET_TRANSLATOR``. Class attributes are read
    as ``cls.X`` throughout, so a subclass changes behavior by redefining them.

    Three class-level switches change how the tree is read. ``SHELVES_ONLY`` answers
    existence and listing questions from the shelf files instead of the filesystem;
    ``SHELVES_REQUIRED`` turns a missing shelf into an error rather than a warning; and
    ``DEFAULT_CACHING`` decides which objects ``_complete()`` caches.
    """

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

    # The time tag every log path built inside a _pinned_log_timetag() block shares.
    # None outside such a block, which is when each path is dated from the clock.
    _LOG_TIMETAG = None

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
        """Choose whether a label file sorts after the data file it describes.

        The setting is stored on this object alone, over a copy of the sort order the
        class supplies, so other objects of the same class are unaffected.

        Parameters:
            labels_after (bool): if True, a label file follows its data file in a sorted
                listing. If False, it sorts by name like any other file.
        """

        self.SORT_ORDER = self.SORT_ORDER.copy()
        self.SORT_ORDER['labels_after'] = labels_after

    def sort_dirs_first(self, dirs_first):
        """Choose whether directories sort before files.

        The setting is stored on this object alone, over a copy of the sort order the
        class supplies, so other objects of the same class are unaffected.

        Parameters:
            dirs_first (bool): if True, every directory precedes every file in a sorted
                listing.
        """

        self.SORT_ORDER = self.SORT_ORDER.copy()
        self.SORT_ORDER['dirs_first'] = dirs_first

    def sort_dirs_last(self, dirs_last):
        """Choose whether directories sort after files.

        The setting is stored on this object alone, over a copy of the sort order the
        class supplies, so other objects of the same class are unaffected.

        Parameters:
            dirs_last (bool): if True, every directory follows every file in a sorted
                listing.
        """

        self.SORT_ORDER = self.SORT_ORDER.copy()
        self.SORT_ORDER['dirs_last'] = dirs_last

    def sort_info_first(self, info_first):
        """Choose whether an info file sorts to the top of a listing.

        The setting is stored on this object alone, over a copy of the sort order the
        class supplies, so other objects of the same class are unaffected.

        Parameters:
            info_first: True or 1 to put the info file first in every listing, False or
                0 never to, or an integer above 1 to put it first only in a directory
                holding at least that many files.
        """

        self.SORT_ORDER = self.SORT_ORDER.copy()
        self.SORT_ORDER['info_first'] = info_first

    ############################################################################
    # Constructor
    ############################################################################

    def __init__(self):
        """Construct a blank object with every attribute at its empty value.

        Nothing here refers to a file. The path attributes are empty strings, the flags
        are False, and every lazy property's storage slot is None so that the first
        access computes it. An alternative constructor is what turns a blank object into
        one that stands for a file.
        """

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
        """Return a blank object of this class, or of the subclass a bundleset selects.

        Selecting a subclass is a two-step lookup: a key that is already a key of
        ``SUBCLASSES`` picks that entry directly, and any other key is put through
        ``VOLSET_TRANSLATOR`` first and the result used instead.

        Parameters:
            key (str): the name of a bundleset registered in ``SUBCLASSES``, or a
                bundleset name that ``VOLSET_TRANSLATOR`` can map to one. None keeps
                this object's own class.
            copypath (bool): if True, copy the path attributes -- everything from the
                basename down to the interior, and the version fields -- from this
                object onto the new one. The lazy properties are not copied, so the new
                object recomputes them.

        Returns:
            PdsFile: the new object.

        Raises:
            KeyError: if the translated key is not registered in ``SUBCLASSES``. It comes
                from the item lookup, ``__getitem__()``, on that dictionary.
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
        """Set ``SHELVES_ONLY`` on every direct subclass of the class this is called on.

        Called on ``PdsFile``, that means ``Pds3File`` and ``Pds4File``. The class it is
        called on is not itself changed, and neither are subclasses further down, which
        inherit the value instead. ``Pds3File`` and ``Pds4File`` each override this with
        a version that sets the attribute on themselves.

        Call it before ``preload()``. A file's existence and a directory's contents are
        then answered from the shelf files, and the filesystem is consulted only where a
        shelf is missing.

        Parameters:
            status (bool): the value to set.
        """

        subclasses = cls.__subclasses__()
        for child_class in subclasses:
            child_class.SHELVES_ONLY = status

    @classmethod
    def require_shelves(cls, status=True):
        """Set ``SHELVES_REQUIRED`` on every direct subclass of the class it is called on.

        Called on ``PdsFile``, that means ``Pds3File`` and ``Pds4File``. The class it is
        called on is not itself changed, and neither are subclasses further down, which
        inherit the value instead. ``Pds3File`` and ``Pds4File`` each override this with
        a version that sets the attribute on themselves.

        Call it before ``preload()``. A missing or incomplete shelf file is then an
        error rather than a logged warning.

        Parameters:
            status (bool): the value to set.
        """

        subclasses = cls.__subclasses__()
        for child_class in subclasses:
            child_class.SHELVES_REQUIRED = status


    @classmethod
    def set_logger(cls, logger=None):
        """Set ``LOGGER`` on every direct subclass of the class this is called on.

        Called on ``PdsFile``, that means ``Pds3File`` and ``Pds4File``. The class it is
        called on keeps the logger it had.

        A cache is unaffected either way. Each holds a direct reference to the logger it
        was constructed with, so nothing done to a class's ``LOGGER`` reaches the logger
        that class's ``CACHE`` writes to.

        Parameters:
            logger: the PdsLogger to install. A false value installs a null logger,
                which discards everything.
        """

        if not logger:
            logger = pdslogger.NullLogger()

        subclasses = cls.__subclasses__()
        for child_class in subclasses:
            child_class.LOGGER = logger


    @classmethod
    def set_easylogger(cls):
        """Send every log message straight to standard output.

        The call is passed down to each direct subclass. ``Pds3File`` and ``Pds4File``
        override it and install the logger on themselves, which is where the recursion
        ends.
        """

        subclasses = cls.__subclasses__()
        for child_class in subclasses:
            child_class.set_easylogger()

    ############################################################################
    # Merged directories, index rows, and object utilities
    ############################################################################
    @classmethod
    def new_merged_dir(cls, basename):
        """Return the category-level directory that merges several physical directories.

        A category directory such as ``volumes/`` or ``archives-volumes/`` can exist on
        more than one disk. The merged object stands for all of them at once: it has a
        logical path but no absolute path, no disk and no root, and its children are
        accumulated from every physical copy as those copies are visited.

        The object is returned mostly filled in, with the lazy properties a category
        directory can answer already set, so those are never computed from a filesystem.
        Seven storage slots are left unset. The properties behind four of them answer
        normally anyway -- ``_volume_info`` falls back to its unknown tuple,
        ``description`` and ``icon_type`` come from the rules, ``index_pdslabel`` is None
        and ``associated_parallel()`` returns this object -- and the other three do not:
        ``html_path`` and ``url`` raise IndexError off the empty child list,
        ``all_version_abspaths`` raises TypeError on the None ``root_``, and
        ``iconset_open`` and ``iconset_closed`` raise KeyError until ``load_icons()`` has
        filled ``pdsviewable.ICON_SET_BY_TYPE`` for this object's icon type.

        Parameters:
            basename (str): the category name, which must be one of ``CATEGORIES``.

        Returns:
            PdsFile: the merged directory.

        Raises:
            ValueError: if the basename is not a category name.
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
        """Return an object standing for one or more rows of this index table.

        The result is a pseudo-child of the index file: its paths are this file's with
        the row key appended, so a large index table can be browsed row by row as though
        each row were a file. No such file exists, and the object carries
        ``is_index_row`` set to True to say so.

        The row object reports itself as an existing, non-directory, plain-text file of
        zero size. It inherits this file's date, version and bundle-level metadata, and
        it gains ``parent_basename``, an attribute only an index row has.

        Parameters:
            filename_key (str): the basename to give the row object, which is the value
                that identifies the row within the table.
            row_dicts (list): the rows this object stands for, each a dictionary of
                column name to value.

        Returns:
            PdsFile: the row object.
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
        """Return a separate object of the same class holding all the same attributes.

        The copy is shallow: the two objects share every attribute value, including the
        lists and dictionaries that hold childnames, index rows and filled-in property
        values. Modifying one of those in place is visible through both.

        Returns:
            PdsFile: the copy.
        """

        cls = type(self)
        this = cls.__new__(cls)

        for (key, value) in self.__dict__.items():
            this.__dict__[key] = value

        return this

    def __repr__(self):
        """Return the object's printable form, which quotes the path it stands for.

        An object whose absolute path is None -- a merged category directory, or one
        built from a logical path alone -- is shown by its logical path and marked as
        logical, with no class name on it. The test is against None specifically, so a
        blank object, whose absolute path is the empty string, takes the other branch and
        prints an empty absolute path instead.

        On the absolute-path branch an instance of a subclass names its class. Neither
        shipped subclass reaches this method, though: ``Pds3File`` and ``Pds4File`` each
        define their own.

        Returns:
            str: the text ``PdsFile("<abspath>")``, ``PdsFile.<subclass>("<abspath>")``
            or ``PdsFile-logical("<logical path>")``.
        """

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
        """Return the bundle-level file or directory this file belongs to.

        The counterpart may be looked up in another category and at another version, so
        the same call reaches this file's own bundle directory, the bundle's checksum
        file, its archive file, or an older version of any of them.

        Unlike ``bundle_abspath()``, this insists the target exist and answers None
        rather than a path when it does not.

        Parameters:
            category (str): the category to look in, such as ``'volumes'`` or
                ``'checksums-archives-volumes'``. None uses this file's own category.
            rank (int): the version rank to look for. None, and any other false value,
                takes the version implied by the category.

        Returns:
            PdsFile: the bundle-level object, or None if it does not exist or has no
            version at the rank asked for.
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
        """Return the bundleset-level file or directory this file belongs to.

        The counterpart may be looked up in another category and at another version, so
        the same call reaches this file's own bundleset directory, the bundleset's
        checksum file, or an older version of either.

        Unlike ``bundleset_abspath()``, this insists the target exist and answers None
        rather than a path when it does not.

        Parameters:
            category (str): the category to look in, such as ``'volumes'`` or
                ``'checksums-archives-volumes'``. None uses this file's own category.
            rank (int): the version rank to look for. None, and any other false value,
                takes the version implied by the category.

        Returns:
            PdsFile: the bundleset-level object, or None if it does not exist or has no
            version at the rank asked for.
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
        """Whether this is a bundle's own top-level directory.

        True for the bundle directory itself and for nothing inside it.

        Returns:
            bool: True if this is a bundle directory.
        """
        # The bool() matters: without it a bundle set would yield the empty string
        # the `and` produces, not False.
        return bool(self.bundlename_ and not self.interior)

    @property
    def is_bundle_file(self):
        """Whether this is a file that stands for a whole bundle.

        That is a bundle's checksum file or its archive file: a path that names a bundle
        but is not a directory holding one.

        Returns:
            bool: True if this is a bundle-level file.
        """
        # The bool() matters: without it a bundle set would yield the empty string
        # the `and` produces, not False.
        return bool(self.bundlename and not self.bundlename_)

    @property
    def is_bundle(self):
        """Whether this stands for a whole bundle, as a directory or as a file.

        Returns:
            bool: True if this is a bundle directory or a bundle-level file.
        """
        return bool(self.is_bundle_dir or self.is_bundle_file)

    @property
    def is_bundleset_dir(self):
        """Whether this is a bundleset's own top-level directory.

        Reading it can consult the filesystem or the shelves, because it may have to know
        whether the path is a directory. That test is last and the conjunction
        short-circuits, so an object that names no bundleset, or that names a bundle,
        answers without asking.

        Returns:
            bool: True if this is a bundleset directory.
        """
        return bool(self.bundleset and not self.bundlename and self.isdir)

    @property
    def is_bundleset_file(self):
        """Whether this is a file that sits at bundleset level rather than in a bundle.

        That is a bundleset's checksum file, or a description file such as an AAREADME.
        Reading it can consult the filesystem or the shelves, because it may have to know
        whether the path is a directory. That test is last and the conjunction
        short-circuits, so an object that names no bundleset, or that names a bundle,
        answers without asking.

        Returns:
            bool: True if this is a bundleset-level file.
        """
        return bool(self.bundleset and not self.bundlename and not self.isdir)

    @property
    def is_bundleset(self):
        """Whether this sits at bundleset level, as a directory or as a file.

        Unlike the two properties it summarizes, this asks nothing of the filesystem.

        Returns:
            bool: True if this names a bundleset and nothing below it.
        """
        return bool(self.bundleset and not self.bundlename)

    @property
    def is_category_dir(self):
        """Whether this sits above bundleset level, at a category such as ``volumes/``.

        The holdings root itself, which names no category either, also answers True.

        Returns:
            bool: True if this names no bundleset.
        """
        return (self.bundleset == '')

    def bundle_abspath(self, category=None):
        """Build the absolute path of the bundle-level counterpart in a given category.

        The path is constructed, not looked up, so it names a file whether or not one is
        there. Where the category's voltype matches this file's, the version suffix is
        carried over; where it does not, the path is built without a suffix, which names
        the most recent version.

        The basename depends on the category: a bundle directory in a plain category, a
        ``.tar.gz`` archive under ``archives-``, and an ``_md5.txt`` checksum file under
        ``checksums-``.

        Parameters:
            category (str): the category to build for, such as ``'volumes'`` or
                ``'archives-previews'``. None uses this file's own category.

        Returns:
            str: the absolute path, or an empty string if this file belongs to no bundle
            or the category is a checksums-of-archives category, which has no
            bundle-level member.
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
        """Build the absolute path of the bundleset-level counterpart in a given category.

        The path is constructed, not looked up, so it names a file whether or not one is
        there. Where the category's voltype matches this file's, the version suffix is
        carried over; where it does not, the path is built without a suffix, which names
        the most recent version.

        A checksums-of-archives category gives a checksum file rather than a directory,
        so the path gains an ``_md5.txt`` ending.

        Parameters:
            category (str): the category to build for, such as ``'volumes'`` or
                ``'checksums-archives-volumes'``. None uses this file's own category.

        Returns:
            str: the absolute path, or None if this file belongs to no bundleset.
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
        """Finish an object off: return the cached one for its path, or cache this one.

        Every alternative constructor ends here, and this is what keeps one object per
        logical path. Where the cache already holds an object for this path, that object
        is returned and this one is discarded -- except when one of the two is a merged
        category directory and the other is physical, in which case they are different
        things and this one is kept.

        Whether this object is cached depends on the caching mode. ``'all'`` caches
        everything below category level, ``'dir'`` caches directories and index files
        only, and any other value caches nothing. A checksums-of-archives path is cached
        whatever the mode, because it is the only path from which the bundleset it
        belongs to can be recorded. Three things are never cached whatever the mode: a
        path above category level, a path *at* category level, and a path that does not
        exist.

        The capitalization of the path must already be correct, because this does not
        repair it. It does not have to match the cache, though: the key is the logical
        path lowercased, so two spellings that differ only in case reach the same entry
        and get back the same object.

        Parameters:
            must_exist (bool): if True, insist that the file exists.
            caching (str): ``'all'``, ``'dir'``, or another value for no caching.
                ``'default'`` takes the class's ``DEFAULT_CACHING``.
            lifetime: how long the cache entry should last, in seconds. Zero makes it
                permanent, and None takes the cache's default.

        Returns:
            PdsFile: the object for this path, which is the cached one where there was
            one and this one otherwise. An object whose basename is blank answers with
            its parent instead.

        Raises:
            OSError: if ``must_exist`` is True and the file does not exist.
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
        """Record this object's version in the cache's rank and path dictionaries.

        Those two dictionaries are what lets a bundleset or bundle name be resolved to a
        path without walking the tree. For each category, one holds the sorted version
        ranks available under each bundleset or bundle name, and the other holds the
        absolute path for each name and rank. Both are stored permanently, so they
        survive any trim.

        Only bundleset-level and bundle-level objects contribute; anything above or
        below is ignored. An object that does contribute has its ``permanent`` attribute
        set, which nothing in the package reads: the cache entry for such an object was
        already written by the caller with an ordinary lifetime, so the paths these
        dictionaries point at can be evicted like any others. Nothing is recorded at all
        until a preload has run, since without one there is no tree to be authoritative
        about.
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
        """Write this object back to the cache, so a filled-in value is not recomputed.

        A lazy property calls this after storing its result. The write happens only if
        the cache already holds an entry for this logical path and that entry agrees
        with this object about being merged or physical; an object the cache never held
        is not added here.

        The entry is rewritten without a lifetime, and what that means depends on which
        cache the class holds. A dictionary cache resolves it to the cache's default, so
        an entry stored as permanent becomes an expiring one. A memcached cache instead
        reuses the lifetime already recorded for the key, so a permanent entry stays
        permanent.
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
        """Return the object for a named entry inside this directory.

        This is the step every downward traversal is built from. Which piece of the
        taxonomy the name fills in depends on what this object already is: a child of the
        holdings root is a category, a child of a category is a bundleset, a child of a
        bundleset is a bundle, and anything deeper is interior path. The subclass of the
        result follows from the bundleset, so descending into a bundleset switches to
        that bundleset's rule class.

        An index file has no real children, and asking one for a child gives a row of the
        table instead unless ``allow_index_row`` says otherwise. That is the one path
        that returns before anything below happens.

        On every other path the cache is paused for the duration and resumed however the
        call ends, so a traversal several levels deep trims or flushes once rather than
        at every level.

        Parameters:
            basename (str): the name of the entry. A trailing slash is ignored.
            fix_case (bool): if True, correct the capitalization of the name against the
                real directory contents. If False, a name whose case is already right is
                still accepted.
            must_exist (bool): if True, insist that the entry exists.
            caching (str): the caching mode to complete the child with, as
                ``_complete()`` uses it.
            lifetime: the cache lifetime to complete the child with, in seconds.
            allow_index_row (bool): if True, a child of an index file is a row of that
                file's table. If False, it is treated as an ordinary name.

        Returns:
            PdsFile: the child object.

        Raises:
            OSError: if ``must_exist`` is True and the entry does not exist.
            ValueError: if the name cannot fill the piece of the taxonomy it would have
                to fill -- a category child that is not a legal bundleset name, a
                category name that is not a category, or a voltype that is not one of
                ``VOLTYPES``.
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
        """Return the object for the directory this one sits in.

        A parent at category level is the merged category directory rather than the
        physical one on this file's own disk, so walking up from a bundleset arrives at
        the category as it appears across every disk.

        The ``caching`` and ``lifetime`` arguments are accepted but not passed on; the
        parent is built with whatever defaults the constructor it reaches applies.

        Parameters:
            must_exist (bool): if True, insist that the parent exists.
            caching (str): accepted and unused.
            lifetime: accepted and unused.

        Returns:
            PdsFile: the parent object, or None if this is a merged category directory,
            which has no parent.

        Raises:
            ValueError: if this is a *physical* category directory. Walking up from one
                asks for the holdings directory itself, which has no logical path, and
                the conversion refuses it. The exception comes from ``from_abspath()``.
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
        """Return the object a PDS logical identifier names.

        The identifier has four colon-separated fields: the dataset ID, the bundle ID,
        the directory path within the bundle, and the file name. The last three are
        joined under ``volumes/`` to give a path, and the dataset ID of the file found
        there is checked against the one the identifier gave.

        Parameters:
            lid_str (str): the identifier, in the form
                ``dataset_id:bundle_id:directory_path:file_name``.

        The path lookup is ``from_path()``, so an identifier naming a bundle no preload
        recorded fails the way that call fails: with an UnboundLocalError rather than
        anything this method names.

        Returns:
            PdsFile: the object the identifier names.

        Raises:
            ValueError: if the identifier does not have exactly four fields, or if the
                file found does not carry the dataset ID the identifier claimed.
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
        """Return the object for a logical path, the path below the holdings directory.

        The cache is tried first, for the path itself and then for each of its ancestors
        in turn. Where an ancestor is found *and it has an absolute path*, the rest of
        the path is walked down from it with ``child()``, which fills in the taxonomy and
        picks the right subclass. Otherwise the logical path is converted to an absolute
        path against the class's holdings root and ``from_abspath()`` is used instead.

        On the ancestor path, the arguments are passed on to every ``child()`` call. On
        the fallback path, none of them is: the absolute-path constructor is called with
        its own defaults, so ``must_exist`` is not enforced there, and a path that does
        not exist comes back as an object rather than as an error.

        The fallback is not confined to a tree with no preload. A merged category
        directory has no absolute path, so any path whose deepest cached ancestor is one
        -- which is what a preloaded tree is left with once the bundleset entry below it
        expires or is trimmed -- takes the fallback too, and silently loses
        ``must_exist`` with it.

        Parameters:
            path (str): the logical path, such as
                ``'volumes/COISS_2xxx/COISS_2001/data'``. A trailing slash is ignored.
            fix_case (bool): if True, correct the capitalization of each component
                against the real directory contents.
            must_exist (bool): if True, insist that each component exists.
            caching (str): the caching mode to complete each object with, as
                ``_complete()`` uses it.
            lifetime: the cache lifetime to complete each object with, in seconds.

        Returns:
            PdsFile: the object for the path, or None if the path is empty.
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
        """Return the object for an absolute path on this machine.

        The path is split at its ``holdings`` component: everything above it becomes the
        disk and root, and everything below it is walked down with ``child()``. Paths use
        forward slashes on every platform; on Windows a leading drive specification is
        accepted.

        The part of the URL that precedes the logical path is worked out here too. With
        at most one holdings directory preloaded it is a fixed prefix; with more, the
        prefix is numbered by the directory's position in the preload list, and a
        directory absent from that list gets the site root and a logged warning.

        A path already in the cache is returned from it, unless the cached object is a
        merged category directory, which stands for something else.

        Parameters:
            abspath (str): the absolute path. A trailing slash is ignored.
            fix_case (bool): if True, correct the capitalization of the disk, the root
                and each component below it against the real directory contents.
            must_exist (bool): if True, insist that the path exists.
            caching (str): the caching mode to complete each object with, as
                ``_complete()`` uses it.
            lifetime: the cache lifetime to complete each object with, in seconds.

        Returns:
            PdsFile: the object for the path.

        Raises:
            ValueError: raised by ``logical_path_from_abspath()``, which runs first, for
                a path with no ``holdings`` component, and for one that names the
                holdings directory itself or anything else with nothing below that
                component. Raised here for a path that survives that conversion and is
                not absolute. Raised by ``child()`` afterwards for a component below the
                holdings directory that is not a legal category, bundleset or voltype.
                The message naming a missing ``holdings`` directory is written here but
                cannot be reached, because a path the conversion accepted contains that
                component by construction.
            OSError: if ``must_exist`` is True and the path does not exist. With
                ``fix_case`` also True, a disk or root whose case cannot be repaired
                raises it first.
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
        """Return the object for a path given relative to this directory.

        The path is split on slashes and walked down one component at a time with
        ``child()``, so it descends only: there is no way to name a parent. The cache is
        paused for the duration and resumed however the call ends.

        Parameters:
            path (str): the relative path, such as ``'COISS_2001/data'``. A trailing
                slash is ignored.
            fix_case (bool): if True, correct the capitalization of each component
                against the real directory contents.
            must_exist (bool): if True, insist that each component exists.
            caching (str): the caching mode to complete each object with, as
                ``_complete()`` uses it.
            lifetime: the cache lifetime to complete each object with, in seconds.

        Returns:
            PdsFile: the object at the end of the path.
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
        """Return the object for a path, whichever of the two kinds of path it is.

        A path containing the holdings directory name with a slash on each side is taken
        as absolute and anything else as logical, with the same case sensitivity and the
        same need for a following component as ``is_logical_path()``.

        The four options below are accepted and then dropped: the constructor this
        forwards to is called with the same four names bound to their default values,
        not to the values passed here. Passing ``must_exist=True`` therefore does not
        make the call insist on anything.

        Parameters:
            path (str): the absolute or logical path.
            fix_case (bool): accepted and dropped.
            must_exist (bool): accepted and dropped.
            caching (str): accepted and dropped.
            lifetime: accepted and dropped.

        Returns:
            PdsFile: the object for the path.
        """

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
        """Return the object for anything that roughly resembles a path.

        Where the other constructors need a well-formed path, this one takes a
        description of a file and fills in what is missing. The category and the version
        suffix can each be written in several ways or left out, and they are recognized
        at the *front* of the description, in any order; what is left over is taken as
        the bundleset, the bundle name and the interior path. A missing *voltype* is
        assumed to be the class's own bundle directory name; a ``checksums`` or
        ``archives`` prefix that was given is kept, and the category is the three
        concatenated. So ``checksums/archives`` resolves to ``checksums-archives-volumes``
        for PDS3 and to ``checksums-archives-bundles`` for PDS4, the two differing only in
        what the class calls its bundle directory.

        Only the front is scanned. A category or version written after the bundleset --
        ``COISS_2xxx/archives`` rather than ``archives/COISS_2xxx`` -- is not recognized
        and becomes part of the interior path.

        The bundleset and version are resolved through the rank and path dictionaries
        that a preload fills, which is why a preload is required. Where the version
        asked for does not exist, the other versions that count as current are tried in
        turn before the call gives up.

        The recognized spellings are:

        * ``archives``, ``tar``, ``targz`` and ``tar.gz`` for an archive path, and
          ``checksums`` or ``md5`` for a checksum path, written as separate components
          or joined with hyphens.
        * a file extension, so a name ending ``.tar.gz`` is an archive and one ending
          ``_md5.txt`` is a checksum, and one containing a voltype names that voltype.
        * ``.targz`` anywhere, which is read as ``.tar.gz``.
        * a version as its own component, so ``COISS_0xxx/v1`` means the bundleset
          ``COISS_0xxx_v1``.

        So ``diagrams/checksums/whatever`` reaches ``checksums-diagrams/whatever``,
        ``checksums/archives/whatever`` reaches ``checksums-archives-volumes/whatever``,
        ``COISS_2001.targz`` reaches
        ``archives-volumes/COISS_2xxx/COISS_2001.tar.gz``, and
        ``COISS_2001_previews.targz`` reaches
        ``archives-previews/COISS_2xxx/COISS_2001_previews.tar.gz``.

        Parameters:
            path: the path-like description. It is converted with ``str()``, so a path
                object is accepted. A trailing slash is ignored, and an empty
                description means the ``volumes`` category.
            must_exist (bool): if True, insist that the file exists.
            caching (str): the caching mode to complete each object with, as
                ``_complete()`` uses it.
            lifetime: the cache lifetime to complete each object with, in seconds.

        Returns:
            PdsFile: the object the description resolves to.

        A description the preload dictionaries cannot answer does not fail cleanly. A
        bundle*set* they do not hold gives KeyError when no version suffix was given,
        because the rank comes from a lookup in the rank table; with a suffix the rank
        comes from ``version_info()`` instead, the lookup that fails is the one for the
        absolute path, and the recovery that follows it ends in ValueError. A bundle
        *name* they do not hold gives UnboundLocalError, because the recovery path that
        follows the KeyError leaves the version rank unassigned when no bundleset matches
        the name. A bundleset whose rank list is empty gives IndexError. None of these is
        caught here, and all but the first reach a caller who is watching for KeyError
        unhandled.

        A bundle name with no underscore in it gives ValueError as well, from the index
        of the underscore. No bundle name either shipped subclass recognizes can reach
        it, because every alternative of both bundle-name patterns requires an
        underscore; a subclass whose pattern does not would.

        Raises:
            OSError: if no preload has been performed.
            ValueError: if the version asked for exists under no rank that was found, or
                if a bundle name has no underscore in it.
            KeyError: if a bundleset is not one a preload recorded, or if the category
                has no entry of its own. It comes from the item lookups,
                ``__getitem__()``, on the preload dictionaries.
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
        """Report whether a path is a logical path rather than an absolute one.

        The test is entirely textual: a path is logical unless it contains the holdings
        directory name with a slash on each side. Nothing is looked up, and a path that
        names no real file is classified just the same.

        Two consequences of that exact spelling. The match is case-sensitive, unlike the
        one ``from_abspath()`` uses to find the same component, so a path spelling it in
        capitals reads as logical. And it needs a component *after* the holdings
        directory, so the holdings directory itself reads as logical too.

        Parameters:
            path (str): the path to classify.

        Returns:
            bool: True if the path is logical.
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
