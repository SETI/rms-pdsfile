##########################################################################################
# pdsfile/pds4file/__init__.py
##########################################################################################

"""The pds4file subpackage, and the Pds4File class that reads a PDS4 holdings tree.

``Pds4File`` is one of the two subclasses of ``PdsFile`` that a caller instantiates.
Everything that reads or writes a file is inherited; what this class supplies is
everything that says the tree is a PDS4 one:

  * **Where the tree is.** ``PDS_HOLDINGS`` is "pds4-holdings", ``BUNDLE_DIR_NAME`` is
    "bundles", and ``_HOLDINGS_ENV`` names the PDS4_HOLDINGS_DIR environment variable
    that locates the tree on disk.
  * **What a name looks like.** A PDS4 bundle set is not a pattern but a list: six names
    are spelled out in ``BUNDLESET_REGEX``, so a new bundle set has to be added here
    before it can be read. Bundle names are patterns, one per family of bundles.
  * **Which rules apply.** Every rule table the base class leaves as None is filled in
    from ``pds4file.rules``, including ``PRODUCT_LBL_BASENAME_WO_EXT``, which the base
    declares and ``Pds3File`` leaves None. Three more are not declared on ``PdsFile``
    at all: ``ARCHIVE_PATHS`` and ``ARCHIVE_DIRS``, which this class introduces and the
    PDS3 side has no use for, and ``CROSS_PDS3_PDS4_PRODUCTS``, which both subclasses
    introduce.
  * **Its own cache and registry.** ``CACHE``, ``LOCAL_PRELOADED`` and ``SUBCLASSES``
    are assigned here rather than inherited, so a preload of a PDS4 tree does not
    disturb ``Pds3File``.

The class carries no second vocabulary. The shared code is already written in the PDS4
terms -- bundle, bundle set -- so the nineteen aliases ``Pds3File`` needs have no
counterpart here, and the two methods this class adds beyond the overrides are the
archive-path pair at the end of the class body.

The module ends with three statements. The class registers itself in its own
``SUBCLASSES`` under "default", which is the entry a path no rule module claims resolves
to; the per-bundle-set rule modules are imported, and each of them adds its own entry to
that same registry as it is imported; and one cache entry is created for each category
that has none, holding a directory whose children are the union of that category's
children across every holdings directory. Those entries never expire and an existing one
is left alone, so the call is safe at any time; before a preload has filled anything they
are empty, so they are what makes several trees look like one rather than what makes a
tree readable at all.

**One of the three orderings is load-bearing and the file says which.** The import has to
follow the class body, because every rule module subclasses ``Pds4File`` and so needs a
class that is already built. Nothing forces the other two into their places. Every rule
module does reach ``SUBCLASSES`` -- each ends by assigning its own key into it -- but
none reads the "default" entry, so registering that entry after the import would serve
equally; and the merged-directory call reads only the category list and the
cache, both bound before any rule module is imported.

The import is wrapped in a handler for ``AttributeError``. The in-code comment beside it
says that is what a recursive import of ``pdsfile`` raises when a rule module is tested
on its own; that mechanism does not occur on any Python this package supports, since
``import pdsfile.pds4file as pds4file`` binds from ``sys.modules`` during a circular
import rather than raising. A run that did take the handler would finish with no rule
subclasses registered at all.
"""

import re
import pdslogger

from pdsfile import pdscache
from pdsfile.pdsfile import PdsFile
from . import rules
from pdsfile.preload_and_cache import cache_lifetime_for_class

class Pds4File(PdsFile):
    """A file or directory in a PDS4 holdings tree.

    Construct one with an inherited constructor -- ``from_abspath()``,
    ``from_logical_path()`` or one of the OPUS constructors -- rather than by calling
    the class. What comes back is this class for a path no rule module claims, and a
    subclass of it, from ``pds4file.rules``, for a path whose bundle set has one; the
    ``SUBCLASSES`` registry and ``VOLSET_TRANSLATOR`` are what choose.

    **Class state is per class, and this class has its own.** ``CACHE``,
    ``LOCAL_PRELOADED`` and ``SUBCLASSES`` are assigned in the class body rather than
    inherited from ``PdsFile``, so preloading a PDS4 tree fills this class's cache and
    leaves ``Pds3File``'s alone. The four setters below are overridden for the same
    reason. The base version of each writes its attribute onto every direct subclass and
    not onto the class it was called on; these write it onto the class the call names.
    ``set_easylogger()`` differs only in route: the base passes the call down to each
    direct subclass, and this override ends the recursion by installing the logger
    through its own ``set_logger()``, which writes ``LOGGER`` on the class named.

    A rule subclass inherits all of it, so a setting made on ``Pds4File`` reaches every
    bundle set, and one made on a rule subclass reaches that bundle set alone.

    The class-attribute groups are:

      * ``PDS_HOLDINGS``, ``BUNDLE_DIR_NAME`` and ``_HOLDINGS_ENV``, which say the tree
        is a "pds4-holdings" tree whose data category is "bundles" and which is located
        by the PDS4_HOLDINGS_DIR environment variable.
      * Five regular expressions naming a bundle set and a bundle, with a
        case-insensitive twin of three of them. ``BUNDLESET_REGEX`` enumerates the six
        bundle sets by name rather than matching a shape. Its "plus" form appends the
        same three groups the PDS3 side's does -- a version group, a category suffix
        and an archive or checksum ending, so ``uranus_occs_earthbased_md5.txt`` and
        ``cassini_vims.tar.gz`` match and the archive-side products those endings name
        can be resolved -- with two differences: the version group admits the two PDS4
        suffix forms rather than PDS3's seven, quantified with a star so that repeats
        match (``cassini_iss_v1.0_v2.0``, whose group is then the whole
        ``_v1.0_v2.0``), and the category alternatives are the three category
        directories a pds4-holdings tree has beside ``bundles/``, without PDS3's
        ``_calibrated``. The group structure is PDS3's exactly -- name, version,
        combined tail, category, ending -- which is what the shared consumers in
        ``pdsfile.py`` and ``_sorting.py`` index into.
        ``BUNDLENAME_PLUS_REGEX`` is built exactly as the PDS3 one is: it appends an
        optional lower-case word and then an optional ``.tar.gz`` or ``_md5.txt``, so
        it takes the names sitting beside a bundle and no version suffix at all.
      * ``LOGGER`` and ``CACHE``, the second built with the shared cache-lifetime rule
        and holding a direct reference to the logger, which is why replacing ``LOGGER``
        later does not change where the cache logs.
      * The rule tables, every one of them taken from ``pds4file.rules``.
      * ``IDX_EXT`` and ``LBL_EXT``. A PDS4 index table is a ``.csv``, and ``.tab`` is
        admitted as well; a PDS4 label is an ``.xml``, and ``.lblx`` as well.
    """

    PDS_HOLDINGS = 'pds4-holdings'
    BUNDLE_DIR_NAME = 'bundles'
    _HOLDINGS_ENV = 'PDS4_HOLDINGS_DIR'

    BUNDLESET_REGEX = re.compile(r'^(uranus_occs_earthbased|' +
                                 r'cassini_uvis_solarocc_beckerjarmak2023|' +
                                 r'cassini_iss|' +
                                 r'cassini_iss_fring_mosaics_rsfrench2025|' +
                                 r'cassini_iss_spokes_hedman-hamilton-2024|' +
                                 r'cassini_vims)$')
    BUNDLESET_PLUS_REGEX   = re.compile(BUNDLESET_REGEX.pattern[:-1] +
                                        r'((?:_v[0-9]+\.[0-9]+\.[0-9]+|' +
                                        r'_v[0-9]+\.[0-9]+)*)' +
                                        r'((|_diagrams|_metadata|_previews)' +
                                        r'(|_md5\.txt|\.tar\.gz))$')
    BUNDLESET_PLUS_REGEX_I = re.compile(BUNDLESET_PLUS_REGEX.pattern, re.I)

    BUNDLENAME_REGEX = re.compile(r'^(uranus_occ_u\d{0,4}._[a-z]*_(fos|\d{2,3}cm)|' +
                                  r'cassini_[a-z]{3,4}_(cruise|saturn)|' +
                                  r'cassini_iss_fring_mosaics_rsfrench2025(|_.*)|'
                                  r'cassini_iss_spokes_hedman-hamilton-2024(|_.*)|'
                                  r'cassini_uvis_solarocc_beckerjarmak2023(|_.*))$')
    BUNDLENAME_PLUS_REGEX  = re.compile(BUNDLENAME_REGEX.pattern[:-1] +
                                        r'(|_[a-z]+)(|_md5\.txt|\.tar\.gz)$')
    BUNDLENAME_PLUS_REGEX_I = re.compile(BUNDLENAME_PLUS_REGEX.pattern, re.I)
    BUNDLENAME_VERSION     = re.compile(BUNDLENAME_REGEX.pattern[:-1] +
                                        r'(_v[0-9]+\.[0-9]+\.[0-9]+|'+
                                        r'_v[0-9]+\.[0-9]+|_v[0-9]+)*$')
    BUNDLENAME_VERSION_I   = re.compile(BUNDLENAME_VERSION.pattern, re.I)

    # Logger
    LOGGER = pdslogger.NullLogger()

    # CACHE
    DICTIONARY_CACHE_LIMIT = 200000
    CACHE = pdscache.DictionaryCache(lifetime=cache_lifetime_for_class,
                                     limit=DICTIONARY_CACHE_LIMIT,
                                     logger=LOGGER)

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
    CROSS_PDS3_PDS4_PRODUCTS = rules.CROSS_PDS3_PDS4_PRODUCTS
    OPUS_ID = rules.OPUS_ID
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = rules.OPUS_ID_TO_PRIMARY_LOGICAL_PATH

    OPUS_ID_TO_SUBCLASS = rules.OPUS_ID_TO_SUBCLASS
    FILESPEC_TO_BUNDLESET = rules.FILESPEC_TO_BUNDLESET

    LOCAL_PRELOADED = []
    SUBCLASSES = {}

    IDX_EXT = ('.csv', '.tab')
    LBL_EXT = ('.xml', '.lblx')

    PRODUCT_LBL_BASENAME_WO_EXT = rules.PRODUCT_LBL_BASENAME_WO_EXT

    ARCHIVE_PATHS = rules.ARCHIVE_PATHS
    ARCHIVE_DIRS = rules.ARCHIVE_DIRS

    def __init__(self):
        """Return a blank object, with every slot at the value the base class gives it.

        This is not how a caller gets an object; the inherited class methods are.
        ``from_abspath()``, ``from_path()`` and ``from_logical_path()`` all look in the
        class cache first and all build a blank object here on a miss, so whether a
        given call reaches this depends on what the cache holds rather than on which
        constructor was called. ``new_pdsfile()`` reaches it too. ``copy()`` is the one
        that does not: it builds its result with ``__new__`` and never runs this.

        A blank object has no path in either form, and its absolute path is the empty
        string rather than None, which is what its representation shows.
        """

        super().__init__()

    @classmethod
    def use_shelves_only(cls, status=True):
        """Choose whether file existence is answered from the info shelves.

        Call it before ``preload()``. With the setting on, a file's existence and a
        directory's contents come from the info shelf files, and the filesystem is
        consulted only where a shelf is missing.

        The attribute is written onto the class this is called on, unlike the
        ``PdsFile`` version, which writes it onto every direct subclass of the class it
        is called on and not onto that class itself. Subclasses further down inherit
        the value rather than being written to, so a call on ``Pds4File`` reaches every
        bundle set and a call on one rule subclass reaches that one.

        Parameters:
            status (bool): the value to set.
        """

        cls.SHELVES_ONLY = status

    @classmethod
    def require_shelves(cls, status=True):
        """Choose whether a missing or incomplete shelf file is an error.

        Call it before ``preload()``. With the setting on, missing shelf information
        raises; with it off, it is logged as a warning and the run carries on.

        The attribute is written onto the class this is called on, on the same terms as
        ``use_shelves_only()`` above.

        Parameters:
            status (bool): the value to set.
        """

        cls.SHELVES_REQUIRED = status

    # Override functions
    def __repr__(self):
        """Return a representation naming the class and the path.

        Three forms are produced, and which one appears says what the object is: an
        object whose absolute path is **None** is written as ``Pds4File-logical("...")``
        around its logical path; one of this class exactly is written as
        ``Pds4File("...")`` around its absolute path; and one of a rule subclass names
        that subclass after a dot, as ``Pds4File.uranus_occs_earthbased("...")``.

        The first test is against None specifically, so a blank object, whose absolute
        path is the empty string, takes the second branch and prints an empty absolute
        path: ``repr(Pds4File())`` is ``Pds4File("")``.

        Returns:
            str: the representation.
        """

        if self.abspath is None:
            return 'Pds4File-logical("' + self.logical_path + '")'
        elif type(self) is Pds4File:
            return 'Pds4File("' + self.abspath + '")'
        else:
            return ('Pds4File.' + type(self).__name__ + '("' +
                    self.abspath + '")')

    ######################################################################################
    # PdsLogger support
    ######################################################################################
    @classmethod
    def set_logger(cls, logger=None):
        """Install the PdsLogger this class writes through.

        The logger is written onto the class this is called on, unlike the ``PdsFile``
        version, which writes it onto every direct subclass of the class it is called on
        and leaves that class with the logger it had.

        A cache is unaffected either way. Each holds a direct reference to the logger it
        was constructed with, so replacing this class's ``LOGGER`` does not change where
        its ``CACHE`` logs.

        Parameters:
            logger: the PdsLogger to install. A false value installs a null logger,
                which discards everything.
        """
        if not logger:
            logger = pdslogger.NullLogger()

        cls.LOGGER = logger

    @classmethod
    def set_easylogger(cls):
        """Send every log message straight to standard output.

        This is where the base class's recursion ends. ``PdsFile.set_easylogger()``
        calls itself on each direct subclass, and this override installs the logger on
        the class it was called on instead of passing the call further down.
        """
        cls.set_logger(pdslogger.EasyLogger())

    ############################################################################
    # Archive path associations
    ############################################################################
    def archive_paths(self):
        """Return the absolute paths of the archive files that cover this file.

        A PDS4 bundle set chooses how to split itself into archives, so there is no
        structural rule of the kind the PDS3 side has, where one archive covers one
        volume. The answer is looked up instead: this file's **logical** path is put
        through the ``ARCHIVE_PATHS`` translator and every logical archive path it
        returns has this file's root directory put in front of it.

        The table comes from the rule subclass of the bundle set this file belongs to.
        The one this class carries is empty, so a bundle set whose rule module does not
        install a table of its own gets nothing back here, and so does a path no rule in
        the installed table matches.

        Nothing is checked for existence; the paths are what the table names.

        Returns:
            list[str]: the absolute paths of the archive files, typically .tar.gz
            files, or an empty list where no rule matched.
        """

        # pdsf = self.bundle_pdsfile()
        # if not pdsf:
        #     pdsf = self.bundleset_pdsfile()
        archive_paths = [self.root_ + p
                         for p in self.ARCHIVE_PATHS.all(self.logical_path)]

        return archive_paths

    def archive_dirs(self):
        """Return, for each archive covering this file, the directories inside it.

        This is the inverse of ``archive_paths()`` and is built on top of it: every
        archive path that method returns becomes a key, and the ``ARCHIVE_DIRS``
        translator says which directories that archive packages.

        The two translators are fed differently. ``ARCHIVE_PATHS`` is given a logical
        path and ``ARCHIVE_DIRS`` is given the **absolute** archive path this method
        already built, so a rule in either table has to allow for whatever precedes the
        part it matches. Both tables return logical paths, and this method puts the root
        directory in front of each of those in turn.

        Unlike ``archive_paths()``, the result is filtered by what is there: each
        directory pattern is globbed, so a pattern matching nothing on disk contributes
        nothing. The glob is case-sensitive.

        The table comes from the rule subclass of the bundle set this file belongs to.
        The one this class carries is empty, so a bundle set whose rule module does not
        install a table of its own maps each of its archive paths, if it has any, to an
        empty list.

        Returns:
            dict[str, list[str]]: the absolute path of each archive that covers this
            file, mapped to the absolute paths of the directories it packages. An
            archive whose patterns match nothing that exists maps to an empty list.

        Raises:
            OSError: raised by ``glob_glob()``, and under either setting. With
                SHELVES_ONLY on, from a shelf file its search has already located and
                cannot open or read back; with it off, from the directory listings the
                filesystem glob makes while repairing the case of a pattern.
            AssertionError: raised by the same ``glob_glob()`` call, under SHELVES_ONLY,
                for a shelf path that does not hold the info shelf directory prefix
                exactly once. Under ``python -O`` nothing is raised there.
        """

        archive_paths = self.archive_paths()

        archive_dirs = {}
        for p in archive_paths:
            dir_abs_patterns = [self.root_ + dir_pattern
                                for dir_pattern in self.ARCHIVE_DIRS.all(p)]

            # Get the existing paths included in each archive file
            dir_abspaths = []
            for pattern in dir_abs_patterns:
                these_abspaths = self.glob_glob(pattern, force_case_sensitive=True)
                dir_abspaths += these_abspaths

            archive_dirs[p] = dir_abspaths

        return archive_dirs


##########################################################################################
# Initialize the global registry of subclasses
##########################################################################################
Pds4File.SUBCLASSES['default'] = Pds4File

##########################################################################################
# This import must wait until after the Pds4File class has been fully initialized
# because all bundle set specific rules are the subclasses of Pds4File
##########################################################################################

try:
    # Data set-specific rules are implemented as subclasses of Pds4File
    # from pdsfile_reorg.Pds4File.rules import *
    from .rules import (cassini_iss,
                        cassini_iss_fring_mosaics_rsfrench2025,
                        cassini_iss_spokes_hedman_hamilton_2024,
                        cassini_uvis_solarocc_beckerjarmak2023,
                        cassini_vims,
                        uranus_occs_earthbased)
except AttributeError:
    pass                    # This occurs when running pytests on individual
                            # rule subclasses, where pdsfile can be imported
                            # recursively.


Pds4File.cache_category_merged_dirs()
