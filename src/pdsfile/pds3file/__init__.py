##########################################################################################
# pdsfile/pds3file/__init__.py
##########################################################################################

"""The pds3file subpackage, and the Pds3File class that reads a PDS3 holdings tree.

``Pds3File`` is one of the two subclasses of ``PdsFile`` that a caller instantiates.
Everything that reads or writes a file is inherited; what this class supplies is
everything that says the tree is a PDS3 one:

  * **Where the tree is.** ``PDS_HOLDINGS`` is "holdings", ``BUNDLE_DIR_NAME`` is
    "volumes", and ``_HOLDINGS_ENV`` names the PDS3_HOLDINGS_DIR environment variable
    that locates the tree on disk.
  * **What a name looks like.** A PDS3 volume set is an uppercase mission code and a
    digit-and-x suffix, ``COISS_1xxx``; a volume is a mission code and four digits,
    ``COISS_1001``. Five regular expressions match those, each with a case-insensitive
    twin, and three of the five admit a version suffix, a category suffix, an archive
    extension or a checksum basename as well.
  * **Which rules apply.** Every rule table the base class leaves as None is filled in
    from ``pds3file.rules``, which is where the per-dataset behavior lives.
  * **Its own cache and registry.** ``CACHE``, ``LOCAL_PRELOADED`` and ``SUBCLASSES``
    are assigned here rather than inherited, so a preload of a PDS3 tree does not
    disturb ``Pds4File``.

**The class also carries the PDS3 vocabulary.** A volume is what the shared code calls
a bundle, and a volume set a bundle set, so a dozen properties and methods here are
one-line aliases forwarding to the bundle-named member of the base class, and ten class
attributes are second names for the bundle-named regular expressions above them. They
are what a PDS3 caller writes, and the PDS3 maintenance tools write them too:
``pdsarchives`` names ``log_path_for_volume`` in its specification and reaches
``volume_pdsfile()`` and ``volset_pdsfile()`` to expand a command-line path, and
``re_validate`` reads ``volname`` and ``volset_``. The checksum, info shelf and link
shelf tools use the bundle-named methods instead, because those are the ones the PDS3
and PDS4 halves can share.

The module ends with three statements. The class registers itself in its own
``SUBCLASSES`` under "default", which is the entry a path no rule module claims resolves
to; the per-volume-set rule modules are imported, and each of them adds its own entry to
that same registry as it is imported; and the merged directory of each category is
created, so that a tree can be read before any preload has run.

**One of the three orderings is load-bearing and the file says which.** The import has to
follow the class body, because every rule module subclasses ``Pds3File`` and so needs a
class that is already built. It is wrapped in a handler for ``AttributeError``, which is
what a recursive import of ``pdsfile`` raises when a rule module is tested on its own,
and a run that takes that path finishes with no rule subclasses registered at all.
"""

import re
import pdslogger

from pdsfile import pdscache
from pdsfile.pdsfile import PdsFile
from . import rules
from pdsfile.preload_and_cache import cache_lifetime_for_class

class Pds3File(PdsFile):
    """A file or directory in a PDS3 holdings tree.

    Construct one with an inherited constructor -- ``from_abspath()``,
    ``from_logical_path()`` or one of the OPUS constructors -- rather than by calling
    the class. What comes back is this class for a path no rule module claims, and a
    subclass of it, from ``pds3file.rules``, for a path whose volume set has one; the
    ``SUBCLASSES`` registry and ``VOLSET_TRANSLATOR`` are what choose.

    **Class state is per class, and this class has its own.** ``CACHE``,
    ``LOCAL_PRELOADED`` and ``SUBCLASSES`` are assigned in the class body rather than
    inherited from ``PdsFile``, so preloading a PDS3 tree fills this class's cache and
    leaves ``Pds4File``'s alone. The four setters below are overridden for the same
    reason: the base class writes each attribute onto every direct subclass, and these
    write it onto the class the call names.

    A rule subclass inherits all of it, so a setting made on ``Pds3File`` reaches every
    volume set, and one made on a rule subclass reaches that volume set alone.

    The class-attribute groups are:

      * ``PDS_HOLDINGS``, ``BUNDLE_DIR_NAME`` and ``_HOLDINGS_ENV``, which say the tree
        is a "holdings" tree whose data category is "volumes" and which is located by
        the PDS3_HOLDINGS_DIR environment variable.
      * Five regular expressions naming a volume set and a volume, each with a
        case-insensitive twin, and ten aliases of the ten under the volume vocabulary.
        ``BUNDLESET_PLUS_REGEX`` and ``BUNDLENAME_PLUS_REGEX`` extend the plain forms to
        the version suffixes, category suffixes, ``.tar.gz`` and ``_md5.txt`` names that
        appear beside a volume set, each of those parts being optional;
        ``BUNDLENAME_VERSION`` matches a volume name and requires a version suffix on
        it.
      * ``LOGGER`` and ``CACHE``, the second built with the shared cache-lifetime rule
        and holding a direct reference to the logger, which is why replacing ``LOGGER``
        later does not change where the cache logs.
      * The rule tables, every one of them taken from ``pds3file.rules``.
      * ``IDX_EXT`` and ``LBL_EXT``, the extensions a PDS3 index table and a PDS3 label
        carry.
    """

    PDS_HOLDINGS = 'holdings'
    BUNDLE_DIR_NAME = 'volumes'
    _HOLDINGS_ENV = 'PDS3_HOLDINGS_DIR'

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
    CROSS_PDS3_PDS4_PRODUCTS = rules.CROSS_PDS3_PDS4_PRODUCTS
    OPUS_ID = rules.OPUS_ID
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = rules.OPUS_ID_TO_PRIMARY_LOGICAL_PATH

    OPUS_ID_TO_SUBCLASS = rules.OPUS_ID_TO_SUBCLASS
    FILESPEC_TO_BUNDLESET = rules.FILESPEC_TO_BUNDLESET

    IDX_EXT = ('.tab',)
    LBL_EXT = ('.lbl',)

    def __init__(self):
        """Return a blank object, with every slot at the value the base class gives it.

        This is not how a caller gets an object. The constructors are the inherited
        class methods, and each of them builds a blank object this way and then fills it
        in, so calling the class directly gives something with no path and no contents.
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
        the value rather than being written to, so a call on ``Pds3File`` reaches every
        volume set and a call on one rule subclass reaches that one.

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

    # Alias, compatible with old function/property names
    def log_path_for_volset(self, suffix='', task='', dir='', place='default'):
        """Return the log file path for this file's volume set.

        The PDS3 name for ``log_path_for_bundleset()``, which it forwards to
        positionally. The four arguments and the path built from them are that method's.

        Parameters:
            suffix (str): the suffix of the log file basename. An empty string appends
                nothing.
            task (str): part of the log basename. An empty string appends nothing.
            dir (str): a subdirectory of the log root. An empty string appends nothing.
            place (str): 'default' to build under the class's log root, or 'parallel'
                to build under a "logs" directory beside this file's holdings directory.

        Returns:
            str: the absolute path of the log file.

        Raises:
            ValueError: raised by ``log_path_for_bundleset()`` if the place option is
                neither of the two.
        """

        return self.log_path_for_bundleset(suffix, task, dir, place)

    # Override functions
    def __repr__(self):
        """Return a representation naming the class and the path.

        Three forms are produced, and which one appears says what the object is: an
        object with no absolute path is written as ``Pds3File-logical("...")`` around its
        logical path; one of this class exactly is written as ``Pds3File("...")`` around
        its absolute path; and one of a rule subclass names that subclass after a dot,
        as ``Pds3File.COISS_xxxx("...")``.

        Returns:
            str: the representation.
        """

        if self.abspath is None:
            return 'Pds3File-logical("' + self.logical_path + '")'
        elif type(self) is Pds3File:
            return 'Pds3File("' + self.abspath + '")'
        else:
            return ('Pds3File.' + type(self).__name__ + '("' +
                    self.abspath + '")')

    @property
    def volset(self):
        """The PDS3 name for ``bundleset``, whose value it returns.

        Returns:
            str: this file's volume set name with any version suffix stripped, or the
            empty string for a path above volume-set level.
        """

        return self.bundleset

    @property
    def volset_(self):
        """The PDS3 name for ``bundleset_``, whose value it returns.

        Returns:
            str: the volume set name with its version suffix and a trailing slash, ready
            to be concatenated into a path, or the empty string.
        """

        return self.bundleset_

    @property
    def is_volset(self):
        """The PDS3 name for ``is_bundleset``, whose value it returns.

        Returns:
            bool: True if this stands for a whole volume set, as a directory or as a
            volume-set-level file.
        """

        return self.is_bundleset

    @property
    def is_volset_dir(self):
        """The PDS3 name for ``is_bundleset_dir``, whose value it returns.

        Returns:
            bool: True if this is a volume set's own top-level directory.
        """

        return self.is_bundleset_dir

    @property
    def is_volset_file(self):
        """The PDS3 name for ``is_bundleset_file``, whose value it returns.

        Returns:
            bool: True if this is a file at volume-set level, such as the volume set's
            checksum file or an AAREADME.
        """

        return self.is_bundleset_file

    @property
    def volname(self):
        """The PDS3 name for ``bundlename``, whose value it returns.

        Returns:
            str: this file's volume name, or the empty string for a path above volume
            level.
        """

        return self.bundlename

    @property
    def volname_(self):
        """The PDS3 name for ``bundlename_``, whose value it returns.

        Returns:
            str: the volume name with a trailing slash, ready to be concatenated into a
            path, or the empty string.
        """

        return self.bundlename_

    @property
    def is_volume(self):
        """The PDS3 name for ``is_bundle``, whose value it returns.

        Returns:
            bool: True if this stands for a whole volume, as a directory or as a
            volume-level file.
        """

        return self.is_bundle

    @property
    def is_volume_dir(self):
        """The PDS3 name for ``is_bundle_dir``, whose value it returns.

        Returns:
            bool: True if this is a volume's own top-level directory.
        """

        return self.is_bundle_dir

    @property
    def is_volume_file(self):
        """The PDS3 name for ``is_bundle_file``, whose value it returns.

        Returns:
            bool: True if this is a file standing for a whole volume, which is that
            volume's archive file or its checksum file.
        """

        return self.is_bundle_file

    def log_path_for_volume(self, suffix='', task='', dir='', place='default'):
        """Return the log file path for this file's volume.

        The PDS3 name for ``log_path_for_bundle()``, which it forwards to by keyword.
        The four arguments and the path built from them are that method's.

        Parameters:
            suffix (str): the suffix of the log file basename. An empty string appends
                nothing.
            task (str): part of the log basename. An empty string appends nothing.
            dir (str): a subdirectory of the log root. An empty string appends nothing.
            place (str): 'default' to build under the class's log root, or 'parallel'
                to build under a "logs" directory beside this file's holdings directory.

        Returns:
            str: the absolute path of the log file.

        Raises:
            ValueError: raised by ``log_path_for_bundle()`` if the place option is
                neither of the two.
        """

        return self.log_path_for_bundle(suffix=suffix, task=task, dir=dir, place=place)

    def volset_abspath(self, category=None):
        """Build the absolute path of the volume-set-level counterpart in a category.

        The PDS3 name for ``bundleset_abspath()``, which it forwards to positionally.
        The path is constructed rather than looked up, so it names a file whether or not
        one is there.

        Parameters:
            category (str): the category to build for, such as 'volumes' or
                'checksums-archives-volumes'. None uses this file's own category.

        Returns:
            str: the absolute path, or None if this file belongs to no volume set.
        """

        return self.bundleset_abspath(category)

    def volset_pdsfile(self, category=None, rank=None):
        """Return the volume-set-level object this file belongs to.

        The PDS3 name for ``bundleset_pdsfile()``, which it forwards to positionally.
        Unlike ``volset_abspath()``, this insists the target exist.

        Parameters:
            category (str): the category to look in. None uses this file's own.
            rank (int): the version rank to look for. None, and any other false value,
                takes the version implied by the category.

        Returns:
            Pds3File: the volume-set-level object, or None if it does not exist or has
            no version at the rank asked for.
        """

        return self.bundleset_pdsfile(category, rank)

    def volume_abspath(self, category=None):
        """Build the absolute path of the volume-level counterpart in a category.

        The PDS3 name for ``bundle_abspath()``, which it forwards to positionally. The
        path is constructed rather than looked up, so it names a file whether or not one
        is there.

        Parameters:
            category (str): the category to build for, such as 'volumes' or
                'archives-previews'. None uses this file's own category.

        Returns:
            str: the absolute path, or an empty string if this file belongs to no volume
            or the category is a checksums-of-archives category, which has no
            volume-level member.
        """

        return self.bundle_abspath(category)

    def volume_pdsfile(self, category=None, rank=None):
        """Return the volume-level object this file belongs to.

        The PDS3 name for ``bundle_pdsfile()``, which it forwards to positionally.
        Unlike ``volume_abspath()``, this insists the target exist.

        Parameters:
            category (str): the category to look in. None uses this file's own.
            rank (int): the version rank to look for. None, and any other false value,
                takes the version implied by the category.

        Returns:
            Pds3File: the volume-level object, or None if it does not exist or has no
            version at the rank asked for.
        """

        return self.bundle_pdsfile(category, rank)

    @property
    def voltype_(self):
        """The PDS3 name for ``bundletype_``, whose value it returns.

        Returns:
            str: the volume type with a trailing slash, "volumes/" for the data
            themselves and the matching name for each derived type. It is what is left
            of ``category_`` once any "checksums-" and "archives-" prefixes are taken
            off, so it does not say which of the parallel trees this file is in.
        """

        return self.bundletype_

    @property
    def volume_publication_date(self):
        """The PDS3 name for ``bundle_publication_date``, whose value it returns.

        Returns:
            str: the publication date as "YYYY-MM-DD", or an empty string. The
            volume-info table's date is used where it has one, and a modification date
            is the fallback where it does not.
        """

        return self.bundle_publication_date

    @property
    def volume_version_id(self):
        """The PDS3 name for ``bundle_version_id``, whose value it returns.

        Returns:
            str: the version the archive itself declares, or an empty string. It is not
            the version suffix carried in a volume set name, and not the rank derived
            from that suffix.
        """

        return self.bundle_version_id

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
                        JNOSRU_xxxx,
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
