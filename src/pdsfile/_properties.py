##########################################################################################
# pdsfile/_properties.py
##########################################################################################

"""The values a PdsFile works out about itself rather than reading off its path.

A ``PdsFile``'s taxonomy -- its category, bundle set, bundle and interior path -- is
fixed when the object is built. Everything else it can answer is derived, and this is
where the derivations live: whether the file exists, how large it is and when it changed,
what describes it, what displays it, what its label is, which versions of it exist, and
what OPUS calls it.

Most of these are properties, and most of those are lazy in one particular sense. Each
holds a slot that ``PdsFile.__init__()`` creates and sets to None; the first access
derives the value, stores it in the slot, and calls ``self._recache()`` so that the copy
of this object in the shared cache is the filled one rather than the empty one. A second
access returns the slot. The saving is not the arithmetic but the shelf reads, the
filesystem calls and the globs the derivations make, and ``_recache()`` is what spreads
it past the lifetime of one object.

Three consequences run through the whole module and are worth knowing before reading any
one docstring:

  * **Reading one property fills others.** ``mime_type`` fills the slot behind ``split``
    and the slot behind ``isdir``; ``date`` fills the slot behind ``_info``. Each
    docstring names the slots its own derivation fills, because that is what a caller
    measuring cost, or writing a test that counts shelf reads, needs.

  * **A miss is stored as a value.** An empty string, an empty list or False is written
    where nothing was found, so the derivation is not repeated. Which falsy value stands
    for "nothing" differs by property and is stated in each. Where the slot is left at
    None instead, the whole derivation runs again on every access, and those cases are
    called out where they arise.

  * **Two kinds of object arrive with the slots already filled.** A merged directory,
    which stands for one category across several disks, and an index row, which stands
    for rows of an index table, are both built by filling most slots in advance, so many
    of these bodies are never reached on them. Each docstring says what its own slot
    holds on those two, because "born with the slot set" and "derives it" are different
    answers to what a property costs and to whether it can fail.

The rest are properties with no slot, recomputed on each access because they only read
another property or an attribute; and four members that are not properties at all:
``version_info()``, which reads a bundle set suffix as a version; ``all_versions()``,
which finds this file across versions; ``viewset_lookup()``, which searches for a named
set of images; and ``_repair_width_height()``, which measures an image the shelves did
not.

The class here is a mixin of ``PdsFile``. It defines no state: every slot it writes is
created by ``PdsFile.__init__()`` and ``_recache()`` is defined in ``PdsFile``, both of
which stay in the core module. ``_PropertiesMixin``'s own docstring enumerates every
attribute these bodies read or write, which is the contract that makes the split safe.
"""

import datetime
import os

import pdsparser
import PIL

from pdsfile import pdsviewable

from ._path_utils import abspath_for_logical_path, formatted_file_size


##########################################################################################
# Properties mixin
##########################################################################################
class _PropertiesMixin:
    """The derived values a PdsFile object computes once and remembers.

    A mixin of PdsFile; it holds methods only and defines no state of its own.

    Sixty-four of the sixty-eight members are properties, and 40 of those are
    lazy: return the already-filled _X_filled slot if there is one, otherwise
    derive the value, store it in that slot, and call self._recache() so the
    shared cache keeps the filled object. The slots are created by
    PdsFile.__init__ and _recache lives in PdsFile, both of which stay in core,
    which is what makes the split transparent. (39 of the 40 do both halves;
    filename_keylen fills its slot without the _recache() call.) The remaining 24
    properties hold no slot of their own and derive their value on every access:
    is_documents, filespec, absolute_or_logical_path, is_label, url, anchor,
    extension, parent_logical_path, size_bytes, modtime, checksum, width, height,
    alt, icon_type, linked_abspaths, label_abspath, data_abspaths, iconset_open,
    iconset_closed, multipage_view_allowed, continuous_view_allowed,
    has_neighbor_rule and all_version_abspaths.

    The other four members are not properties: version_info, a staticmethod
    mapping a bundleset suffix to a (rank, message, id) triple; all_versions,
    which collects the same file across version ranks; viewset_lookup, which
    picks a named PdsViewSet; and _repair_width_height, which reopens an image
    whose shelf-recorded dimensions are missing.

    Every attribute these bodies read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, list, dict, file, os, os.path,
    datetime, PIL, pdsparser, pdsviewable and logger methods are not in scope,
    and neither is any name this mixin defines itself::

      class attributes read       CACHE, DATAFILE_EXTS, DATA_SET_ID,
                                  DEFAULT_HIGH_LEVEL_ICONS, DESCRIPTION_AND_ICON,
                                  EXTRA_README_BASENAMES, FILENAME_KEYLEN,
                                  INFO_FILE_BASENAMES, LID_AFTER_DSID, LOGGER,
                                  MIME_TYPES_VS_EXT, NEIGHBORS, OPUS_FORMAT,
                                  OPUS_ID, OPUS_TYPE, PDS_HOLDINGS,
                                  PLAIN_TEXT_EXTS, PRODUCT_LBL_BASENAME_WO_EXT,
                                  SHELVES_REQUIRED, VERSIONS, VIEWABLES,
                                  VIEWABLE_ANCHOR_REGEX, VIEWABLE_EXTS,
                                  VIEW_OPTIONS
      class attributes WRITTEN    none
      instance attributes read    abspath, archives_, basename, bundlename,
                                  bundlename_, bundleset, bundletype_, category_,
                                  checksums_, html_root_, interior, is_index_row,
                                  is_merged, logical_path, root_, row_dicts,
                                  suffix, version_rank, plus the 41 slots below
      instance attributes WRITTEN 41 lazy-value slots: _all_version_abspaths,
                                  _all_viewsets_filled,
                                  _bundle_publication_date_filled,
                                  _bundle_version_id_filled, _childnames_filled,
                                  _childnames_lc_filled, _data_set_id_filled,
                                  _date_filled, _description_and_icon_filled,
                                  _exact_archive_url_filled,
                                  _exact_checksum_url_filled, _exists_filled,
                                  _filename_keylen_filled, _formatted_size_filled,
                                  _global_anchor_filled, _html_path_filled,
                                  _iconset_filled, _index_pdslabel,
                                  _indexshelf_abspath, _info_basename_filled,
                                  _info_filled, _infoshelf_path_and_key,
                                  _internal_links_filled, _is_index,
                                  _is_viewable_filled, _isdir_filled,
                                  _islabel_filled, _label_basename_filled,
                                  _lid_filled, _lidvid_filled,
                                  _local_viewset_filled, _mime_type_filled,
                                  _opus_format_filled, _opus_id_filled,
                                  _opus_type_filled, _split_filled,
                                  _version_ranks_filled, _view_options_filled,
                                  _viewset_filled, _volume_data_set_ids_filled,
                                  _volume_info_filled -- the same 41 the list
                                  above ends with. Every one is created by
                                  PdsFile.__init__, so this mixin adds no
                                  attribute of its own, which is what "no new
                                  state" means. Forty are written on self;
                                  _all_version_abspaths is the exception, written
                                  by all_versions onto each sibling PdsFile it
                                  builds, alongside that sibling's _recache()
      core properties read        is_bundle, is_bundle_dir, is_bundleset,
                                  is_bundleset_dir -- none of them lazy in the
                                  sense above; they hold no slot
      other core methods called   _recache, bundle_abspath, bundle_pdsfile,
                                  bundleset_abspath, bundleset_pdsfile, child,
                                  from_abspath, parent

    Seventeen more come from sibling mixins: archive_path_if_exact and
    checksum_path_if_exact from _DerivedPathsMixin; get_indexshelf from
    _IndexRowsMixin; glob_glob, os_listdir, os_path_exists and os_path_isdir from
    _LocalFsMixin; info_shelf_expected, shelf_lookup and
    shelf_path_and_key_for_abspath from _ShelfMixin; basename_is_label,
    basename_is_viewable, pdsfiles_for_abspaths, pdsfiles_for_basenames,
    sort_basenames, split_basename and viewable_childnames_by_anchor from
    _SortingMixin. All of them are attribute lookups on cls or on a PdsFile
    object at run time, not imports, which is what lets the layers live in
    different modules; nothing here needs the PdsFile class object, so this
    module makes no deferred import either.

    The receivers are not all self and cls: all_versions writes through a sibling
    pdsf, viewset_lookup reads through a pdsf and through the parent it fetches,
    all_viewsets reads through a child, and internal_link_info reads through
    self.parent(). They are why the lists above are derived by walking every
    attribute node rather than only self.X and cls.X.

    Two names are read off cls but defined only on Pds3File and Pds4File, not on
    PdsFile: IDX_EXT, read by index_pdslabel, indexshelf_abspath and is_index,
    and LBL_EXT, read by index_pdslabel and label_basename. Both raise
    AttributeError on a bare PdsFile, before this move and after it; the same
    arrangement is documented in _local_fs.py, _associations.py and _sorting.py.
    """

    ############################################################################
    # Properties
    ############################################################################

    @property
    def exists(self):
        """Whether this file exists.

        The answer is derived on the first access, stored in ``_exists_filled`` and
        returned unchanged afterwards; ``PdsFile.__init__()`` sets that slot to None, and
        deriving the value also calls ``_recache()`` so the shared cache holds the filled
        object. A merged directory and an index row are both born with the slot already
        set to True, so neither reaches the derivation.

        Where the derivation does run, an object with no absolute path is False and
        anything else is asked of ``os_path_exists()``, which under SHELVES_ONLY answers
        from the info shelves rather than from the filesystem, for everything outside the
        documents tree, for which no shelves are written. That answer is memoized in an
        LRU of PATH_EXISTS_CACHE_SIZE entries that nothing invalidates, so a file created
        or removed after the first question about it keeps its old answer until the entry
        is evicted.

        Returns:
            bool: True if the file exists.
        """
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
        """Whether this file is a directory.

        The answer is derived on the first access, stored in ``_isdir_filled`` and
        returned unchanged afterwards; deriving it calls ``_recache()``. A merged
        directory is born with the slot set to True and an index row with False, so
        neither reaches the derivation.

        Where the derivation does run, an object with no absolute path is False and
        anything else is asked of ``os_path_isdir()``, which under SHELVES_ONLY reads the
        info shelf rather than the filesystem. That lookup raises KeyError for a path the
        shelf covers and holds no entry for, where ``exists`` would have answered False,
        so this is the less forgiving of the two questions.

        Returns:
            bool: True if the file is a directory.
        """

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
        """Whether this file lies in the documents tree.

        The test is on ``bundletype_``, which is fixed when the object is built, so this
        is recomputed on every access, holds no slot of its own, and is as true of the
        ``documents`` category directory as of a file below it. It says nothing about
        whether the file exists.

        Returns:
            bool: True if this object's bundle type is ``documents``.
        """

        return self.bundletype_ == 'documents/'

    @property
    def filespec(self):
        """This file's path below its bundle set, starting at the bundle name.

        This is the part of a path that a bundle's own documentation quotes: the bundle
        name, followed by the interior path where there is one. It is recomputed on every
        access from attributes fixed at construction, and it is an empty string for
        anything above a bundle.

        Returns:
            str: the bundle name, or the bundle name and the interior path joined by a
            slash.
        """

        if self.interior:
            return self.bundlename_ + self.interior
        else:
            return self.bundlename

    @property
    def absolute_or_logical_path(self):
        """The absolute path where there is one, and the logical path otherwise.

        Recomputed on every access. A merged directory has no absolute path, and neither
        does an object built from a logical path that no holdings directory holds; this is
        what a caller uses to name such an object without testing which kind it has.

        Returns:
            str: the absolute path, or the logical path.
        """

        if self.abspath:
            return self.abspath
        else:
            return self.logical_path

    @property
    def islabel(self):
        """Whether this file is a PDS3 label, judged by its name alone.

        The answer is derived on the first access from ``basename_is_label()``, stored in
        ``_islabel_filled`` and returned unchanged afterwards; deriving it calls
        ``_recache()``. A merged directory and an index row are born with the slot set to
        False.

        Nothing here looks at the file or tests that it exists, so a name that matches is
        a label whether or not anything is there. ``is_label`` is the same value under
        another name, and this is the one that holds the slot.

        Returns:
            bool: True if the basename is a label name.
        """

        if self._islabel_filled is not None:
            return self._islabel_filled

        self._islabel_filled = self.basename_is_label(self.basename)

        self._recache()
        return self._islabel_filled

    @property
    def is_label(self):
        """Whether this file is a PDS3 label, judged by its name alone.

        This returns ``islabel``, which is where the derivation and the slot are, so
        reading either of them fills ``_islabel_filled`` for both.

        Returns:
            bool: True if the basename is a label name.
        """

        return self.islabel

    @property
    def is_viewable(self):
        """Whether this file is an image a browser can display, judged by its name.

        The answer is derived on the first access from ``basename_is_viewable()``, which
        tests the extension against the class's VIEWABLE_EXTS, stored in
        ``_is_viewable_filled`` and returned unchanged afterwards; deriving it calls
        ``_recache()``. A merged directory and an index row are born with the slot set to
        False.

        Nothing here opens the file or tests that it exists, so a file that is viewable by
        name and absent from disk still answers True. ``local_viewset`` is where the
        existence test is applied.

        Returns:
            bool: True if the basename is a viewable name.
        """

        if self._is_viewable_filled is not None:
            return self._is_viewable_filled

        self._is_viewable_filled = self.basename_is_viewable(self.basename)

        self._recache()
        return self._is_viewable_filled

    @property
    def html_path(self):
        """Where this file is served, as a URL or as a path below the HTML root.

        The value is derived once, stored in ``_html_path_filled`` and returned unchanged
        afterwards; deriving it calls ``_recache()``. ``url`` returns the same value under
        another name. Nothing here tests whether the file exists, so a path this
        installation would serve is returned whether or not anything is there to serve.

        Three cases. An object with no absolute path, normally a merged directory, takes
        the path of its first child and drops the last component; one whose child list is
        still empty therefore raises IndexError rather than answering. A file whose path
        ends in ``.link`` holds a URL as its contents, and those contents, read as latin-1
        and stripped, are the answer: that is a complete external URL, scheme and host
        included, and not a path below this installation's HTML root. A ``.link`` file
        that cannot be opened falls back to the third case, which is everything else:
        ``html_root_`` followed by the logical path.

        Returns:
            str: a path below the HTML root, or the whole URL held by a ``.link`` file.

        Raises:
            IndexError: raised by ``__getitem__()`` on the child-name list of an object
                with no absolute path and no children.
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
            except OSError:
                self._html_path_filled = self.html_root_ + self.logical_path
        else:
            self._html_path_filled = self.html_root_ + self.logical_path

        self._recache()
        return self._html_path_filled

    @property
    def url(self):
        """Where this file is served, as a URL or as a path below the HTML root.

        This returns ``html_path``, which is where the derivation and the slot are. See
        that property for the three cases, one of which gives a complete external URL
        rather than a path.

        Returns:
            str: a path below the HTML root, or the whole URL held by a ``.link`` file.
        """

        return self.html_path

    @property
    def split(self):
        """This basename divided into the three parts the sort order is built from.

        The value is derived on the first access from ``split_basename()``, stored in
        ``_split_filled`` and returned unchanged afterwards; deriving it calls
        ``_recache()``. A merged directory and an index row are born with the slot set to
        ``(basename, '', '')``.

        The three parts are the anchor, which groups a file with its relatives, the
        suffix, and a third part that is the extension for most names and the volume type
        for a bundle-set name that carries one. ``anchor`` and ``extension`` are the first
        and third read back out of here.

        **The result is not always a triple.** A class with no split rules, which is a
        bare PdsFile, gets back the basename it passed in.

        Returns:
            tuple: the anchor, the suffix and the third part; or the basename itself for a
            class with no split rules.
        """

        if self._split_filled is not None:
            return self._split_filled

        self._split_filled = self.split_basename()

        self._recache()
        return self._split_filled

    @property
    def anchor(self):
        """The string that groups this object with the files displayed beside it.

        A data file, its label and its previews share an anchor, which is what puts them
        in one row of a Viewmaster table. This holds no slot of its own but reads
        ``split``, so the first access fills ``_split_filled`` and calls ``_recache()``.

        A row key alone would not distinguish one index row from a row of another table,
        so an index row's anchor is its table's anchor and its own joined by a hyphen.
        Building that reads the parent, so an index row's anchor also costs the parent
        object's construction.

        Returns:
            str: the anchor.
        """

        # We need a better anchor for index row PdsFiles
        if self.is_index_row:
            return self.parent().split[0] + '-' + self.split[0]

        return self.split[0]

    @property
    def global_anchor(self):
        """An anchor unique across the whole tree, in a form an HTML page can hold.

        Where ``anchor`` is unique only among the files beside it, this prefixes the
        parent's logical path and replaces every slash with a hyphen, which leaves a
        string with no character an HTML fragment identifier would object to.

        The value is derived on the first access, stored in ``_global_anchor_filled`` and
        returned unchanged afterwards; deriving it calls ``_recache()``, and fills
        ``_split_filled`` by way of ``anchor``. A merged directory is born with the slot
        set to its own basename. An index row is born with it set to None, so an index row
        does reach this body.

        Returns:
            str: the global anchor.
        """

        if self._global_anchor_filled is not None:
            return self._global_anchor_filled

        path = self.parent_logical_path + '/' + self.anchor
        self._global_anchor_filled = path.replace('/', '-')

        self._recache()
        return self._global_anchor_filled

    @property
    def extension(self):
        """The third part of this basename as ``split_basename()`` divides it.

        This holds no slot of its own but reads ``split``, so the first access fills
        ``_split_filled`` and calls ``_recache()`` as a side effect. Under the split rule
        that catches most names the third part is the text from the **last** period
        onward, including the period, and an empty string for a name with no period.

        A bundle-set name is not split by the rules at all: the bundle-set regular
        expression matches first, and where the name carries a volume type that
        expression puts the volume type in the third part, so
        ``COISS_2xxx_previews.tar.gz`` gives ``_previews``. A bundle-set name carrying
        only a version, ``COISS_2xxx_v1``, gives an empty string.

        A merged directory and an index row are born with ``_split_filled`` set to
        ``(basename, '', '')``, so both report an empty string.

        A class with no split rules, which is a bare PdsFile, makes ``split`` return the
        basename itself rather than a triple, and this then returns its third character.

        Returns:
            str: the third part of the split. For a name the default rule handles that is
            the extension including its period, and an empty string where there is none;
            for a bundle-set name it is the volume type or an empty string; for a class
            with no split rules it is one character of the basename.

        Raises:
            IndexError: raised by ``__getitem__()`` on a class with no split rules whose
                basename is shorter than three characters, where the subscript indexes
                the basename itself.
        """

        return self.split[2]

    @property
    def indexshelf_abspath(self):
        """The absolute path of the index shelf that records this index table's rows.

        The value is derived on the first access, stored in ``_indexshelf_abspath`` and
        returned unchanged afterwards; deriving it calls ``_recache()``. A merged
        directory is born with the slot set to an empty string.

        A file whose extension is not one of the class's index extensions, in either case,
        gets an empty string. Anything else gets this file's own absolute path with the
        holdings directory renamed to the parallel ``_indexshelf-`` tree and the extension
        replaced by ``.pickle``.

        The path is built by text substitution and is never tested, so a non-empty answer
        says the name is an index name and not that any shelf exists; ``is_index`` is the
        property that tests it. Reading this on a bare PdsFile raises AttributeError,
        because only the subclasses define index extensions.

        Returns:
            str: the shelf path, or an empty string.
        """

        cls = type(self)
        if self._indexshelf_abspath is None:
            if self.extension not in (
                *cls.IDX_EXT,
                *tuple(ext.upper() for ext in cls.IDX_EXT)
            ):
                self._indexshelf_abspath = ''
            else:
                abspath = self.abspath
                abspath = abspath.replace(f'/{cls.PDS_HOLDINGS}/',
                                          f'/{cls.PDS_HOLDINGS}/_indexshelf-')
                abspath = abspath.replace(self.extension, '.pickle')
                abspath = abspath.replace(self.extension.upper(), '.pickle')
                self._indexshelf_abspath = abspath

            self._recache()

        return self._indexshelf_abspath

    @property
    def is_index(self):
        """Whether this file is an index table whose rows can be browsed as children.

        The answer is derived on the first access, stored in ``_is_index`` and returned
        unchanged afterwards; deriving it calls ``_recache()``, and fills
        ``_indexshelf_abspath`` on the way. A merged directory is born with the slot set
        to False.

        The test is that ``indexshelf_abspath`` names a file that exists, so an index
        table whose shelf has not been written is not an index by this measure. A second
        test catches a table while its shelf is being built: a path in the metadata tree
        whose name ends in an index extension answers True. **That second answer is
        returned without being stored**, so a file recognized only that way runs the whole
        derivation again on every access, and it is the one answer this property gives
        that is not remembered.

        The second test reads the absolute path as text, so an object that has none raises
        TypeError there rather than answering False.

        Returns:
            bool: True if this is an index table.
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
                if '/metadata/' in self.abspath:
                    for ext in cls.IDX_EXT:
                        if self.abspath.lower().endswith(ext):
                            return True  # this value is not cached

                self._is_index = False

            self._recache()

        return self._is_index

    @property
    def index_pdslabel(self):
        """The parsed PDS label that describes this index table.

        A file that is not an index gets None with no slot written, so that question is
        asked again on every access. Otherwise the value is derived once, stored in
        ``_index_pdslabel`` and returned unchanged afterwards; deriving it calls
        ``_recache()``. An index row is born with the slot set to None and is not itself
        an index, so it takes the first case.

        The label's path is guessed by replacing each index extension in this file's path
        with each label extension, in both cases, and parsing the first that opens. A
        parse that fails records the marker string ``'failed'``, which is what makes the
        failure remembered rather than retried, and which this reports as None.

        **A class with more than one label extension can discard a label it parsed**: the
        successful parse leaves the inner loop only, so the outer loop tries the next
        label extension and its failure overwrites the value. The PDS3 subclass has one
        label extension and cannot reach this; the PDS4 subclass has two.

        Returns:
            the parsed label, as the ``PdsLabel`` object ``pdsparser`` builds, or None
            where this is not an index or no label could be parsed.
        """

        if not self.is_index:
            return None

        cls = type(self)
        if self._index_pdslabel is None:
            for lbl_ext in cls.LBL_EXT:
                for idx_ext in cls.IDX_EXT:
                    label_abspath = self.abspath.replace(idx_ext, lbl_ext)
                    label_abspath = label_abspath.replace(idx_ext.upper(),
                                                          lbl_ext.upper())
                    try:
                        self._index_pdslabel = pdsparser.PdsLabel.from_file(label_abspath)
                        break
                    except OSError:
                        self._index_pdslabel = 'failed'
                        continue

            self._recache()

        if self._index_pdslabel == 'failed':
            return None

        return self._index_pdslabel

    @property
    def childnames(self):
        """The basenames of this object's children, in display order.

        The value is derived on the first access, stored in ``_childnames_filled`` and
        returned unchanged afterwards; deriving it calls ``_recache()`` and fills
        ``_isdir_filled``, ``_indexshelf_abspath`` and ``_is_index``. A merged directory
        is born with the slot set to an empty list, which the preload appends to as it
        visits each physical copy; an index row is born with an empty list and keeps it.

        A directory with an absolute path is listed through ``os_listdir()``, which under
        SHELVES_ONLY reads the info shelf, and the names are sorted with every grouping
        option off, so the order is the sort rules' own. Anything else starts from an
        empty list.

        **An index table then replaces that list entirely** with the row keys its index
        shelf holds, sorted with the default options, so the rows of an index appear as
        its children. The two cases are consecutive rather than alternative, so a name
        read from the filesystem cannot survive into an index table's answer.

        Returns:
            list: the child basenames, sorted.
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
        """The basenames of this object's children, lowercased, in the same order.

        The value is derived on the first access from ``childnames``, stored in
        ``_childnames_lc_filled`` and returned unchanged afterwards; deriving it calls
        ``_recache()`` and fills ``_childnames_filled`` and the slots that reads. A merged
        directory and an index row are born with the slot set to an empty list.

        The order is ``childnames``' order rather than a fresh sort, and no name is
        dropped, so two names differing only in case both appear and appear as duplicates.

        Returns:
            list: the child basenames, lowercased.
        """

        if self._childnames_lc_filled is None:
            self._childnames_lc_filled = [c.lower() for c in self.childnames]
            self._recache()

        return self._childnames_lc_filled

    @property
    def parent_logical_path(self):
        """The parent's logical path, or an empty string where there is no parent.

        Recomputed on every access, and it builds the parent object twice to answer. This
        is what callers use in place of ``parent().logical_path``, which raises on the
        objects that have no parent; a category-level merged directory is the case it
        exists for.

        Returns:
            str: the parent's logical path, or an empty string.
        """

        parent = self.parent()

        if self.parent() is None:
            return ''
        else:
            return parent.logical_path

    @property
    def _info(self):
        """The size, child count, modification time, checksum and shape of this file.

        This is the derivation behind ``size_bytes``, ``modtime``, ``date``,
        ``formatted_size``, ``width`` and ``height``, and the fallback behind
        ``checksum``, which prefers the MD5 the volume-info table carries and reads this
        only where that is empty. The value is derived once, stored in ``_info_filled``
        and returned unchanged afterwards, and deriving it calls ``_recache()``; the one
        later write is ``_repair_width_height()``, which replaces the fifth element in
        place when ``width`` or ``height`` is read on a viewable whose shape is the
        ``'TBD'`` marker, so those two do reach the filesystem where the others do not. A
        merged directory and an index row are born with the slot already filled, with a
        list rather than a tuple, so neither reaches this body.

        A file that does not exist gets zeros, no modification time and no checksum, so
        the properties above answer rather than fail on it.

        Otherwise the info shelf is asked first, wherever ``info_shelf_expected`` says one
        should cover this file. A shelf that cannot be read logs a warning and re-raises
        when SHELVES_REQUIRED is set; otherwise the derivation falls through to the
        filesystem cases below rather than failing. A shelf that answers gives the
        modification time as text, which is read by fixed offsets into a datetime whose
        last field is microseconds, and an empty time string, which is what an empty
        directory gets, becomes None. A checksum written as dashes becomes an empty
        string.

        Three filesystem cases remain. Anything that is not a directory is measured with
        ``os.path.getsize()`` and ``os.path.getmtime()``, and a viewable one gets the
        three-element shape ``(0, 0, 'TBD')``, the marker that ``width`` and ``height``
        replace by opening the image. A bundle-set directory sums the sizes its bundles'
        shelves report and takes the latest of their modification times, skipping the
        names in EXTRA_README_BASENAMES and counting them out of the child count; a bundle
        whose own shelf is missing contributes this directory's size and time instead of
        its own, and one whose shelf reports no time or no bytes contributes nothing. Any
        other directory gets zeros.

        Returns:
            tuple: the size in bytes, the child count, the modification time or None, the
            checksum or an empty string, and the shape, which is a pair except on a
            viewable whose dimensions have not been read. A merged directory and an index
            row return instead the list they were born with.

        Raises:
            OSError: raised by ``shelf_lookup()`` and re-raised where SHELVES_REQUIRED is
                set and the shelf file is missing, and by ``os.path.getsize()`` for a file
                the shelves report as existing that the filesystem does not hold.
            KeyError: raised by ``shelf_lookup()`` and re-raised under the same setting
                where the shelf opened but holds no entry for this file.
            ValueError: raised by ``shelf_lookup()`` and re-raised under the same setting;
                raised by ``int()`` or ``datetime()`` on a shelf time string that is not
                of the expected shape; and raised by ``shelf_lookup()`` out of the
                bundle-set loop whatever that setting is, because that loop's handler
                catches OSError alone. The last is what a checksums bundle-set directory
                does, for which no shelf exists at all, so the properties above fail on
                one rather than answering.
            SyntaxError: raised by ``shelf_lookup()`` where the readable sidecar it reads
                before the shelf itself does not hold the record it expects. Neither
                handler here catches it, so it escapes whatever SHELVES_REQUIRED is set
                to.
            NameError: raised by ``shelf_lookup()`` from the same sidecar, and escaping
                the same way, where that line parses but uses a bare name.
        """

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
            except (OSError, KeyError, ValueError):
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
                except OSError:     # Shelf file for bundlename is missing--maybe
                                    # it's not a bundle name after all
                    file_bytes = os.path.getsize(self.abspath)
                    timestamp = os.path.getmtime(self.abspath)
                    modtime = datetime.datetime.fromtimestamp(timestamp)
                else:
                    # Without this check, we get an error for empty directories
                    if timestring == '' or file_bytes == 0:
                        continue

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
        """This file's size in bytes.

        Read out of ``_info``, so the first access derives that and fills
        ``_info_filled``. A file that does not exist is zero, and so is a directory that
        is neither a bundle set nor covered by a shelf; a bundle-set directory reports the
        sum over its bundles.

        Returns:
            int: the size in bytes.
        """

        return self._info[0]

    @property
    def modtime(self):
        """When this file was last modified.

        Read out of ``_info``, so the first access derives that and fills
        ``_info_filled``. A file that does not exist gets None, and so does a directory
        whose shelf records no time, which is what an empty directory gets. A bundle-set
        directory reports the latest of the times its bundles record.

        Returns:
            datetime.datetime: the modification time, or None where none is recorded.
        """

        return self._info[2]

    @property
    def checksum(self):
        """The MD5 checksum recorded for this file.

        Two sources, in that order: the volume-info table, which is where the documents
        tree's checksums live, and then ``_info``, which is where a shelf-covered file's
        lives. The first access therefore fills ``_volume_info_filled``, and fills
        ``_info_filled`` as well wherever the first source carries nothing.

        Returns:
            str: the checksum, or an empty string where neither source records one.
        """

        return self._volume_info[5] or self._info[3]

    @property
    def width(self):
        """This image's width in pixels.

        Read out of ``_info``, whose fifth element is the shape. Where that shape is the
        ``'TBD'`` marker the info derivation writes for a viewable it measured from the
        filesystem, reading this opens the image with PIL, rewrites ``_info_filled`` and
        calls ``_recache()``, so this is one of the two properties that reaches the
        filesystem after ``_info`` is already filled.

        Anything that is not a measured viewable is zero: a file that does not exist, a
        directory, and an image PIL could not open.

        Returns:
            int: the width in pixels, or zero.
        """

        self._repair_width_height()
        return self._info[4][0]

    @property
    def height(self):
        """This image's height in pixels.

        Read out of ``_info`` exactly as ``width`` is, with the same side effect: a shape
        still carrying the ``'TBD'`` marker is measured by opening the image, which
        rewrites ``_info_filled`` and calls ``_recache()``. Reading either property
        measures both dimensions at once.

        Anything that is not a measured viewable is zero.

        Returns:
            int: the height in pixels, or zero.
        """

        self._repair_width_height()
        return self._info[4][1]

    def _repair_width_height(self):
        """Measure a viewable whose shape the shelves left marked, and record it.

        The marker is a third element in ``_info``'s shape, which the info derivation
        writes as ``(0, 0, 'TBD')`` for a viewable it measured from the filesystem rather
        than from a shelf. Where it is present the image is opened with PIL, its size
        replaces the whole shape, and ``_recache()`` stores the object again; where it is
        absent this does nothing, so ``width`` and ``height`` may call it on every access
        at no cost.

        An image that cannot be opened, for any reason at all, is recorded as ``(0, 0)``,
        which is indistinguishable from a file that was never a viewable and which stops
        the measurement being retried.
        """
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
        """The text an HTML ``alt`` attribute should carry for this file.

        This is the basename, recomputed on every access. Nothing tests whether the file
        is viewable, so every object answers.

        Returns:
            str: the basename.
        """

        return self.basename

    @property
    def date(self):
        """This file's modification time, written for display.

        The value is derived on the first access from ``modtime``, stored in
        ``_date_filled`` and returned unchanged afterwards; deriving it calls
        ``_recache()`` and fills ``_info_filled``. A merged directory is born with the
        slot set to an empty string, and an index row inherits its table's value.

        A file with no recorded modification time gets an empty string rather than a
        placeholder date, so a caller can test the result for truth.

        Returns:
            str: the time as ``YYYY-MM-DD HH:MM:SS``, or an empty string.
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
        """This file's size, written for display with a unit.

        The value is derived on the first access from ``size_bytes``, stored in
        ``_formatted_size_filled`` and returned unchanged afterwards; deriving it calls
        ``_recache()`` and fills ``_info_filled``. A merged directory and an index row are
        born with the slot set to an empty string.

        A size of zero gets an empty string rather than ``0 bytes``, because the size is
        tested for truth before it is formatted, so a file that does not exist and an
        empty file read alike here. Anything else is ``formatted_file_size()``'s three
        significant digits and a unit stepping by factors of a thousand.

        Returns:
            str: the size and its unit, or an empty string.
        """

        if self._formatted_size_filled is None:
            if self.size_bytes:
                self._formatted_size_filled = formatted_file_size(self.size_bytes)
            else:
                self._formatted_size_filled = ''

            self._recache()

        return self._formatted_size_filled

    @property
    def _volume_info(self):
        """What the volume-info tables record about this bundle, bundle set or product.

        The tables are read by the preload and held in the shared cache; this is the
        lookup into them. The value is derived on the first access, stored in
        ``_volume_info_filled`` and returned unchanged afterwards; deriving it calls
        ``_recache()``. An index row inherits its table's value. A merged directory is
        born without this slot and does reach the body, where it finds nothing and takes
        the fallback.

        Up to three keys are tried in order: this object's own logical path, and then, for
        anything outside the documents tree, the bundle set and bundle name with the
        volume type in front and then without it. The first key the cache holds wins. A
        file the tables say nothing about gets a fallback whose icon type is ``UNKNOWN``
        and whose every other field is empty, so this never raises and every reader of it
        gets a value of the right shape.

        ``description``, ``icon_type``, ``bundle_version_id``,
        ``bundle_publication_date``, ``volume_data_set_ids`` and ``checksum`` are the six
        fields read back out of here, in that order.

        Returns:
            tuple: the description, the icon type, the version id, the publication date,
            the list of data set ids, and the MD5 checksum. Six elements, of which the
            last is empty for everything the checksum tables do not cover.
        """

        cls = type(self)

        if self._volume_info_filled is None:

            base_key = self.bundleset + self.suffix
            if self.bundlename:
                base_key += '/' + self.bundlename

            # Try lookup with and without voltype
            base_key = base_key.lower()
            keys = (self.logical_path.lower(),)
            if self.bundletype_ != 'documents/':
                keys += (self.bundletype_ + base_key, base_key)

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
        """The sentence describing this file, as a Viewmaster page shows it.

        This and ``icon_type`` are two halves of one derivation: the pair is computed on
        the first access to either, stored in ``_description_and_icon_filled`` and
        returned unchanged afterwards; deriving it calls ``_recache()``. A merged
        directory and an index row both reach the body.

        Three sources, by what the object is. An index row gets a fixed phrase naming how
        many rows it stands for. A bundle or bundle set gets the volume-info table's
        description, with the volume type prefixed where the description does not already
        say it, so a preview tree's description reads ``Previews of ...`` rather than
        repeating the volume's own; where the table gives no icon type, one is taken from
        the class's high-level icon table and then from the description rules. Anything
        else is looked up in the volume-info tables by its own logical path and falls back
        to the description rules.

        Returns:
            str: the description, which is HTML rather than plain text.
        """

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
            if self.bundletype_ == 'calibrated/' and 'calib' not in desc_lc:
                desc = 'Calibrated ' + desc
            elif self.bundletype_ == 'diagrams/' and 'diagram' not in desc_lc:
                desc = 'Diagrams for ' + desc
            elif self.bundletype_ == 'previews/' and 'preview' not in desc_lc:
                desc = 'Previews of ' + desc
            elif self.bundletype_ == 'metadata/' and 'metadata' not in desc_lc:
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
        """The name of the icon a page should show for this file.

        This is the second half of ``description``'s derivation, so reading it computes
        the description too and fills ``_description_and_icon_filled``. It holds no slot
        of its own and is recomputed from that pair on every access.

        The value is a name such as ``ROOT`` or ``INFO``, which ``iconset_for()`` and the
        ``_iconset`` property turn into an icon set. It is never empty: where no table and
        no rule supply one, the description rules' own fallback does.

        Returns:
            str: the icon type name.
        """

        _ = self.description
        return self._description_and_icon_filled[1]

    @property
    def mime_type(self):
        """A best guess at the MIME type of this file, or an empty string.

        The value is derived once from the extension, stored in ``_mime_type_filled`` and
        returned unchanged afterwards; deriving it calls ``_recache()``, reading
        ``extension`` fills ``_split_filled``, and testing ``isdir`` fills
        ``_isdir_filled``. A merged directory is born with the slot set to an empty string
        and an index row with ``text/plain``, so neither reaches this body.

        A directory gets an empty string. Otherwise the extension **without its first
        character**, lowercased, is looked for in PLAIN_TEXT_EXTS, which gives
        ``text/plain``, and then in MIME_TYPES_VS_EXT, which gives the type recorded
        there. Dropping the first character is right for an extension, whose first
        character is the period, and wrong for the volume type ``extension`` returns for a
        bundle-set name: ``COISS_2xxx_previews_md5.txt`` is looked up as ``previews``, so
        it gets an empty string rather than ``text/plain``. An extension in neither table
        gets an empty string.

        Reading ``isdir`` is what makes this able to fail: under SHELVES_ONLY it raises
        KeyError for a path the info shelf covers and holds no entry for, which is a path
        ``exists`` would have answered False for.

        Returns:
            str: the MIME type, or an empty string.
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
        """The OPUS identifier of the product this file belongs to.

        The value is derived on the first access from the class's OPUS_ID rules, stored in
        ``_opus_id_filled`` and returned unchanged afterwards; deriving it calls
        ``_recache()``. A merged directory is born with the slot set to an empty string.

        The rules read the logical path, so nothing here tests that the file exists. A
        path no rule matches gets an empty string rather than None, which is what lets a
        caller test the result for truth.

        Returns:
            str: the OPUS ID, or an empty string.
        """

        if self._opus_id_filled is None:
            self._opus_id_filled = self.OPUS_ID.first(self.logical_path) or ''
            self._recache()

        return self._opus_id_filled

    @property
    def opus_format(self):
        """How the data in this file is encoded, as OPUS describes it.

        The value is derived on the first access from the class's OPUS_FORMAT rules,
        stored in ``_opus_format_filled`` and returned unchanged afterwards; deriving it
        calls ``_recache()``. A merged directory is born with the slot set to an empty
        string.

        **A path no rule matches gets None, not an empty string**, because the rules'
        answer is stored as it comes. That makes this the one OPUS property whose miss is
        not falsy-but-a-string, and it also means the slot stays None and the derivation
        runs again on every access for such a file.

        Returns:
            tuple: a pair such as ``('ASCII', 'Table')`` or ``('Binary', 'FITS')``, or
            None where no rule matches.
        """

        if self._opus_format_filled is None:
            self._opus_format_filled = self.OPUS_FORMAT.first(self.logical_path)
            self._recache()

        return self._opus_format_filled

    @property
    def opus_type(self):
        """Which OPUS product category this file belongs to, and how it is ranked.

        The value is derived on the first access from the class's OPUS_TYPE rules, stored
        in ``_opus_type_filled`` and returned unchanged afterwards; deriving it calls
        ``_recache()``. A merged directory is born with the slot set to an empty string.

        The tuple has five elements: the data set's display name, a priority in which the
        lower number sorts first, the type id OPUS keys on, a description, and a flag
        saying whether OPUS checks this type by default. ``('Cassini ISS', 0, 'coiss_raw',
        'Raw Image', True)`` is one, and ``('Cassini ISS', 130, 'coiss_full', 'Extra
        preview (full-size)', False)`` is another.

        A path no rule matches gets an empty string rather than a tuple, so a caller has
        to test the result before unpacking it.

        Returns:
            tuple: the five-element OPUS type, or an empty string where no rule matches.
        """

        if self._opus_type_filled is None:
            self._opus_type_filled = (self.OPUS_TYPE.first(self.logical_path)
                                      or '')
            self._recache()

        return self._opus_type_filled

    @property
    def data_set_id(self):
        """The PDS3 data set identifier this file belongs to.

        The value is derived on the first access, stored in ``_data_set_id_filled`` and
        returned unchanged afterwards; deriving it calls ``_recache()`` and fills
        ``_volume_data_set_ids_filled`` and ``_volume_info_filled``. A merged directory is
        born with the slot set to an empty string; an index row is born with it set to
        None and so does reach the body.

        The bundle's own list of data set ids decides. An empty list gives an empty string
        and a list of one gives that one, both without consulting any rule. Only a bundle
        carrying more than one needs the class's DATA_SET_ID rule to say which of them
        this file belongs to, and a rule that answers with nothing gives an empty string.

        Returns:
            str: the data set id, or an empty string.
        """

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
        """The PDS4-style logical identifier of this file, where it has one.

        The value is derived on the first access, stored in ``_lid_filled`` and returned
        unchanged afterwards; deriving it calls ``_recache()``, and fills
        ``_data_set_id_filled`` and the slots that reads. A merged directory and an index
        row are born with the slot set to an empty string.

        Four conditions must all hold, and an empty string is the answer when any of them
        fails: the class's LID_AFTER_DSID rules must answer for this path, the file must
        have a data set id, its bundle set must carry no version suffix, and it must be in
        the ``volumes`` category. The last two are what restrict LIDs to the current
        version of a PDS3 volume; a superseded version and anything in the previews,
        calibrated or metadata trees get an empty string however good a path they have.

        The identifier is the data set id and the rules' answer joined by a colon, so it
        reads as ``<data set id>:<bundle>:<directory path>:<file name>``. A label and the
        file it describes get different LIDs, because the file name is the last field.

        Returns:
            str: the LID, or an empty string.
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
        """This file's logical identifier with a version appended.

        The value is derived on the first access from ``lid``, stored in
        ``_lidvid_filled`` and returned unchanged afterwards; deriving it calls
        ``_recache()`` and fills ``_lid_filled``. A merged directory and an index row are
        born with the slot set to an empty string.

        A file with no LID gets an empty string. Everything else gets its LID with
        ``::1.0`` appended. The version is that literal and is not read from anywhere:
        only the current version of a PDS3 bundle has a LID at all, so there is no second
        version for this to name.

        Returns:
            str: the LIDVID, or an empty string.
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
        """The basename of the file that describes this one, for a page to link to.

        The value is derived on the first access, stored in ``_info_basename_filled`` and
        returned unchanged afterwards; deriving it calls ``_recache()`` and fills the
        slots behind ``childnames``, ``islabel`` and ``label_basename``. A merged
        directory and an index row are born with the slot set to an empty string.

        Three sources are tried in order and the first that answers wins. The class's
        INFO_FILE_BASENAMES rules pick one of this object's own child names, which is how
        a directory finds its ``VOLDESC.CAT`` or ``CATINFO.TXT``. Failing that, a label
        file describes itself and any other file is described by its own label. Failing
        that, a bundle directory looks one level above itself on the filesystem for each
        of EXTRA_README_BASENAMES, which is a real ``os.path.exists()`` test because those
        files are not in any info shelf, and it keeps the last that matches rather than
        the first.

        A file none of the three answers for gets an empty string.

        Returns:
            str: the basename of the informational file, or an empty string.
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
        """What the link shelf records about the files this one points at.

        The value is derived on the first access, stored in ``_internal_links_filled`` and
        returned unchanged afterwards; deriving it calls ``_recache()``. A merged
        directory and an index row are born with the slot set to an empty list.

        **The result has three shapes and the caller has to tell them apart.** A label
        file gets a list of triples, one for each link it holds: the line number the link
        is on, the text that appears there, and the absolute path it resolves to. A file
        that has an external label gets that label's absolute path, as a string. A file
        that has neither gets an empty list.

        A fourth shape says the answer is missing rather than empty: an empty *tuple* is
        stored where the shelf could not be read, which an empty list would not
        distinguish from a file with no links. That path logs a warning and re-raises
        where SHELVES_REQUIRED is set. A bundle-set AAREADME file, which no shelf covers,
        is excepted from all of it and gets an empty list.

        Directories, checksum files, archive files and anything outside the volumes,
        calibrated and metadata trees are answered with an empty list without the shelf
        being opened. The paths in the triples are resolved from the shelf's relative form
        against this file's bundle, bundle set or holdings root, by how many levels the
        recorded path climbs.

        Returns:
            list: the triples, or the label's absolute path as a string, or an empty list,
            or an empty tuple where the shelf failed.
        """

        if self._internal_links_filled is not None:
            return self._internal_links_filled

        cls = type(self)

        # Some file types never have links, and neither do bundle types other
        # than volumes, calibrated and metadata
        if (self.isdir or self.checksums_ or self.archives_ or
            self.bundletype_ not in ('volumes/', 'calibrated/', 'metadata/')):
            self._internal_links_filled = []

        # Otherwise, look up the info in the shelf file
        else:
            try:
                values = self.shelf_lookup('link')

            # Shelf file failure
            except (OSError, KeyError, ValueError):

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
                volume_path_ = self.bundle_abspath() + '/'

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
                            abspath = (self.bundleset_abspath() + internal_path[2:])
                        else:
                            abspath = volume_path_ + internal_path
                        new_list.append((recno, basename, abspath))
                    self._internal_links_filled = new_list

        self._recache()
        return self._internal_links_filled

    @property
    def linked_abspaths(self):
        """The absolute paths of every file this one points at.

        This holds no slot of its own and is recomputed on every access, but the first
        access fills ``_internal_links_filled`` through ``internal_link_info``, whose
        three shapes it sorts out.

        Where that gives triples, this is their paths, in the order they appear, with
        duplicates dropped and this file itself removed. Where it gives a string, this
        file is not a label but has one, so the question is passed to the label instead
        and the answer is the label's links: a data file therefore reports the same list
        as the label that describes it, this file included. Where it gives neither, the
        answer is an empty list.

        An empty tuple from a failed shelf takes the first branch and yields an empty
        list, so a shelf failure is indistinguishable here from a file with no links.

        Returns:
            list: the absolute paths, without duplicates.
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
        """The basename of the PDS3 label that describes this data file.

        The value is derived once, stored in ``_label_basename_filled`` and returned
        unchanged afterwards; deriving it calls ``_recache()``. Deriving it also fills
        four slots that belong to other properties, because the body reads ``islabel``,
        ``extension``, ``exists`` and, on one path, ``internal_link_info``. A merged
        directory and an index row are born with the slot set to an empty string, and a
        label file gets an empty string too, because a label has no label of its own.

        Otherwise the name is guessed before it is looked up. The guesses are this
        basename with its extension replaced by each of LBL_EXT in turn, in both cases,
        the case of this file's own extension deciding which order is tried first; where
        PRODUCT_LBL_BASENAME_WO_EXT answers for this basename, its answer is the stem
        instead. Each guess is tested beside this file with ``os_path_exists()``,
        insisting on a case-sensitive match, and the first that exists is the answer.

        Where no guess exists the result depends on this file. A file that does not itself
        exist gets an empty string for the format, catalog and text extensions and its
        first guess otherwise, so the name returned there is one that need not exist. A
        file that does exist falls back to the link shelf: where ``internal_link_info``
        gives a string, which is how the shelf records an external label, the basename of
        that path is the answer, and anything else gives an empty string.

        A basename whose extension is empty makes the stem empty as well, so the guesses
        are the bare label extensions.

        The link-shelf fallback is the one path that can fail: reading
        ``internal_link_info`` re-raises OSError, KeyError or ValueError from the link
        shelf where SHELVES_REQUIRED is set, so an existing file none of whose guesses
        exists is where this raises rather than answering.

        Returns:
            str: the label basename, or an empty string where there is none.
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
        uppercase_lbl_ext = [ext.upper() for ext in cls.LBL_EXT]
        if self.extension.isupper():
            ext_guesses = (*uppercase_lbl_ext, *cls.LBL_EXT)
        else:
            ext_guesses = (*cls.LBL_EXT, *uppercase_lbl_ext)

        if (self.PRODUCT_LBL_BASENAME_WO_EXT is not None and
            self.PRODUCT_LBL_BASENAME_WO_EXT.first(self.basename)):
            rootname = self.PRODUCT_LBL_BASENAME_WO_EXT.first(self.basename)
        else:
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
        """The absolute path of this file's PDS3 label.

        This holds no slot of its own and is recomputed on every access, but the first
        access fills ``_label_basename_filled`` through ``label_basename``. The path is
        that name beside this file, which is not always where the name came from. Two
        cases give a path that need not exist: a file that does not itself exist, for
        which ``label_basename`` returns a guess, and a name the link shelf supplied,
        which the shelf may have recorded in another directory of the bundle and which
        nothing tests before it is rebuilt here.

        Returns:
            str: the absolute path of the label, or an empty string where there is none.
        """

        if self.label_basename:
            parent_path = os.path.split(self.abspath)[0]
            return parent_path + '/' + self.label_basename
        else:
            return ''

    @property
    def data_abspaths(self):
        """The absolute paths of the data files this label describes.

        This is the inverse of ``label_abspath`` and it holds no slot of its own. Anything
        that is not itself a label gets an empty list at once.

        A link is a target only where the pointing is mutual: each path this label links
        to is built into a PdsFile and kept only where that file names this label as its
        own. That is what separates the files a label describes from the files it merely
        mentions -- a format file it includes, or another label it cites. Building each
        candidate makes this the most expensive of the link properties.

        The comparison is on the basename and is case-insensitive, so a label and a data
        file whose recorded label name differs only in case still pair up.

        Returns:
            list: the absolute paths of the data files, in the order the links appear.
        """

        if not self.islabel:
            return []
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
        """The set of images that stands in for this file on a page.

        The value is derived on the first access, stored in ``_viewset_filled`` and
        returned unchanged afterwards; deriving it calls ``_recache()``. A merged
        directory and an index row are born with the slot set to False.

        The lookup is skipped, and False stored, for anything that is not an existing file
        inside a bundle: the bundle and bundle-set levels, the archive and checksum trees.
        Everything else asks ``viewset_lookup()`` for the default view set, which for a
        directory is inherited from a child. **A miss is stored as False rather than
        None**, which is what stops the lookup being repeated, so a caller must test the
        result and not assume a set.

        Returns:
            pdsviewable.PdsViewSet: the view set, or False where there is none.
        """

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
        """The set made from this file itself, where this file is an image.

        The value is derived on the first access, stored in ``_local_viewset_filled`` and
        returned unchanged afterwards; deriving it calls ``_recache()``. A merged
        directory and an index row are born with the slot set to False.

        Where ``viewset`` finds the images that *represent* this file, this one is the
        file itself as an image, and it is the only one of the two that tests both that
        the file exists and that its name is viewable. Anything else is stored as False
        rather than None, so the derivation is not repeated.

        Returns:
            pdsviewable.PdsViewSet: a set holding this file alone, or False.
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
        """Every named set of images available for this file, keyed by name.

        The value is derived on the first access, stored in ``_all_viewsets_filled`` and
        returned unchanged afterwards; deriving it calls ``_recache()``. A merged
        directory and an index row are born with the slot set to an empty dictionary.

        A file's own dictionary holds its default set, which is itself where it is a
        viewable and its representative images otherwise, plus one entry for each other
        name the class's VIEWABLES table defines that answers for this path. A name that
        answers with nothing is left out, so a key's presence means a set exists.

        A directory's dictionary is the same for its own names, and is then widened by the
        names its children offer: **the first twenty child names only**, and only those
        that are not directories, so a directory whose viewables sort past the twentieth
        name reports fewer kinds than it holds. A child contributes only names not already
        present, and never the default.

        This is the expensive property of the group: every candidate name costs a lookup,
        and a directory builds up to twenty children to ask them.

        Returns:
            dict: view set name mapped to the ``pdsviewable.PdsViewSet`` for it.
        """

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
        """The pair of icon sets for this file, closed and open.

        Both are derived together on the first access, stored in ``_iconset_filled`` as a
        two-element list, and returned unchanged afterwards; deriving them calls
        ``_recache()`` and fills ``_description_and_icon_filled`` by way of ``icon_type``.
        A merged directory reaches this body, and so does an index row, which is born with
        the slot set to None.

        The two sets come out of ``pdsviewable.ICON_SET_BY_TYPE``, which ``load_icons()``
        fills, so reading this before that has run for this file's icon type raises
        KeyError. Both entries are read at once, which is why ``iconset_open`` and
        ``iconset_closed`` cost nothing after either of them.

        This property returns the closed set, the same as ``iconset_closed``; the open one
        is reached only through the slot.

        Returns:
            pdsviewable.PdsViewSet: the icon set for the closed state.
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
        """The icon set for this file shown expanded.

        This holds no slot of its own: it reads ``_iconset`` for the side effect of
        filling ``_iconset_filled`` and then takes the second of the pair. It raises the
        same KeyError as ``_iconset`` where ``load_icons()`` has not supplied this icon
        type.

        An icon type with no ``_open`` variant is served the closed set here, because
        ``load_icons()`` files a closed set under the open key as well when nothing is
        there.

        Returns:
            pdsviewable.PdsViewSet: the icon set for the open state.
        """

        _ = self._iconset
        return self._iconset_filled[1]

    @property
    def iconset_closed(self):
        """The icon set for this file shown collapsed.

        This holds no slot of its own: it reads ``_iconset`` for the side effect of
        filling ``_iconset_filled`` and then takes the first of the pair, which is the
        value ``_iconset`` itself returns. It raises the same KeyError as ``_iconset``
        where ``load_icons()`` has not supplied this icon type.

        Returns:
            pdsviewable.PdsViewSet: the icon set for the closed state.
        """

        _ = self._iconset
        return self._iconset_filled[0]

    @property
    def bundle_publication_date(self):
        """When this file's bundle was published, as a date.

        The value is derived on the first access, stored in
        ``_bundle_publication_date_filled`` and returned unchanged afterwards; deriving it
        calls ``_recache()`` and fills ``_volume_info_filled``. A merged directory is born
        with the slot set to an empty string and an index row inherits its table's value.

        The volume-info table's own date is used where it has one. Where it is empty,
        three fallbacks are tried in order and the first that answers wins: the
        modification date of this file's bundle, then of its bundle set, then of this file
        itself, each cut to its first ten characters so a timestamp becomes a date. A file
        above the bundle level, for which the first two have no object to ask, falls
        through to the third.

        **A date recorded as None short-circuits all of it**: an empty string is returned
        without the slot being written, so the derivation runs again on every access for
        such a file. The fallback the volume-info lookup supplies is an empty string
        rather than None, so only a table that stores None reaches this.

        Returns:
            str: the publication date as ``YYYY-MM-DD``, or an empty string.
        """

        if self._bundle_publication_date_filled is not None:
            return self._bundle_publication_date_filled

        date = self._volume_info[3]
        if date is None:
            return ''

        if date == '':
            try:
                date = self.bundle_pdsfile().date[:10]
            except (ValueError, AttributeError):
                pass

        if date == '':
            try:
                date = self.bundleset_pdsfile().date[:10]
            except (ValueError, AttributeError):
                pass

        if date == '':
            try:
                date = self.date[:10]
            except (ValueError, AttributeError):
                pass

        self._bundle_publication_date_filled = date

        self._recache()
        return self._bundle_publication_date_filled

    @property
    def bundle_version_id(self):
        """The version identifier the volume-info table records for this bundle.

        The value is derived on the first access, stored in ``_bundle_version_id_filled``
        and returned unchanged afterwards; deriving it calls ``_recache()`` and fills
        ``_volume_info_filled``. A merged directory is born with the slot set to an empty
        string and an index row inherits its table's value.

        This is the version the archive itself declares, which is not the version suffix
        ``version_info()`` reads out of a bundle set name and not the rank derived from
        it. A table recording None gives an empty string, so the result is always a
        string.

        Returns:
            str: the version id, or an empty string.
        """

        if self._bundle_version_id_filled is None:
            if self._volume_info[2] is None:
                self._bundle_version_id_filled = ''
            else:
                self._bundle_version_id_filled = self._volume_info[2]

            self._recache()

        return self._bundle_version_id_filled

    @property
    def volume_data_set_ids(self):
        """Every PDS3 data set identifier this file's bundle covers.

        The value is derived on the first access, stored in
        ``_volume_data_set_ids_filled`` and returned unchanged afterwards; deriving it
        calls ``_recache()`` and fills ``_volume_info_filled``. A merged directory is born
        with the slot set to an empty string and an index row inherits its table's value.

        It is the volume-info table's field, passed through unexamined, so a bundle the
        tables do not cover gets that lookup's fallback, an empty list. ``data_set_id``
        reads this to decide whether it needs a rule at all.

        Returns:
            list: the data set ids, which is empty where the tables record none.
        """

        if self._volume_data_set_ids_filled is None:
            self._volume_data_set_ids_filled = self._volume_info[4]
            self._recache()

        return self._volume_data_set_ids_filled

    @property
    def version_ranks(self):
        """The version ranks recorded for the bundle or bundle set this file lies in.

        A version rank is the integer ``version_info()`` derives from a bundle set suffix,
        and it sorts versions oldest to newest. The list describes the bundle rather than
        the file: it holds one entry for each version of the bundle the preload found.

        For a file that exists the value is derived once, stored in
        ``_version_ranks_filled`` and returned unchanged afterwards; deriving it calls
        ``_recache()``. A merged directory is born with the slot set to an empty list, and
        an index row takes whatever its table's value is.

        **A file that does not exist yields None rather than a list.** The derivation
        leaves the slot at the None it started with and returns that, so a caller that
        iterates the result without testing it raises TypeError. Because the slot stays
        None, the guard at the top never fires either, and the body -- including
        ``exists`` and ``_recache()`` -- runs again on every access. An object that exists
        but names neither a bundle nor a bundle set gets an empty list, and so does one
        whose category has no rank table, which also logs a warning.

        Returns:
            list: the version ranks, or None for a file that does not exist.

        Raises:
            KeyError: raised by ``__getitem__()`` on the rank table for an existing file
                whose bundle or bundle set name the preload did not record.
        """

        if self._version_ranks_filled is not None:
            return self._version_ranks_filled

        cls = type(self)

        # When the file does not exist, _version_ranks_filled is left as None
        # rather than set to [], so the property returns None in that case.
        if self.exists:
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
        """The URL of the archive file holding exactly this directory, where one exists.

        The value is derived on the first access, stored in ``_exact_archive_url_filled``
        and returned unchanged afterwards; deriving it calls ``_recache()`` and fills
        ``_exists_filled``. A merged directory and an index row are born with the slot set
        to an empty string.

        The word that carries the meaning is *exact*: ``archive_path_if_exact()`` answers
        only where an archive file covers this directory and nothing more, so a
        subdirectory inside a bundle gets an empty string even though an archive of its
        bundle exists. A file that does not exist gets an empty string without the
        question being asked, and so does anything the archive tree does not cover.

        Where an archive is found, the answer is that archive's own ``url``, so building
        it constructs a second PdsFile.

        Returns:
            str: the archive's URL, or an empty string.
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
        """The URL of the checksum file covering exactly this directory, where one exists.

        The value is derived on the first access, stored in ``_exact_checksum_url_filled``
        and returned unchanged afterwards; deriving it calls ``_recache()`` and fills
        ``_exists_filled``. A merged directory and an index row are born with the slot set
        to an empty string.

        This is ``exact_archive_url``'s shape with ``checksum_path_if_exact()`` in place
        of the archive lookup, and the same *exact* condition governs it: a checksum file
        that covers more than this directory does not count. A file that does not exist
        gets an empty string without the question being asked.

        Returns:
            str: the checksum file's URL, or an empty string.
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
        """Whether a page may show this directory's children as a grid.

        This is the first of three flags derived together on the first access to any of
        them, stored in ``_view_options_filled`` as a triple and returned unchanged
        afterwards; deriving them calls ``_recache()`` and fills ``_exists_filled`` and
        ``_isdir_filled``. A merged directory and an index row are born with the slot set
        to ``(False, False, False)``.

        Only an existing directory can be anything but all three False, and for one the
        class's VIEW_OPTIONS rules decide. Both shipped subclasses end those rules with a
        catch-all that answers ``(False, False, False)``, so a directory no specific rule
        names is single-page.

        Returns:
            bool: True if a grid view is allowed.
        """

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
        """Whether a page may run this directory's children across several pages.

        This holds no slot of its own: it reads ``grid_view_allowed`` for the side effect
        of filling ``_view_options_filled`` and then takes the second of the triple. The
        three flags are independent of each other; a directory may allow this and not the
        grid.

        Returns:
            bool: True if a multipage view is allowed.
        """

        _ = self.grid_view_allowed

        return self._view_options_filled[1]

    @property
    def continuous_view_allowed(self):
        """Whether a page may run this directory and the ones after it together.

        This holds no slot of its own: it reads ``grid_view_allowed`` for the side effect
        of filling ``_view_options_filled`` and then takes the third of the triple. Where
        the other two flags describe one directory, this one says a page may carry on past
        its end into the directories beside it, which is what ``has_neighbor_rule`` says
        is possible at all.

        Returns:
            bool: True if a continuous view is allowed.
        """

        _ = self.grid_view_allowed

        return self._view_options_filled[2]

    @property
    def has_neighbor_rule(self):
        """Whether the tree can say which directories come before and after this one.

        Recomputed on every access, and it builds the parent object to answer, because the
        rule is written about the parent's path rather than this one's: the class's
        NEIGHBORS rules turn a directory path into a pattern matching its siblings.

        An object with no parent is False. Both shipped subclasses carry one rule,
        matching any path with a slash in it, so what decides is whether the **parent's**
        path has one: a bundle set directory is False, because its parent is the bare
        category, and everything from the bundle level down is True.

        Returns:
            bool: True if a neighbor rule answers for the parent.
        """

        parent = self.parent()
        return bool(parent and self.NEIGHBORS.first(parent.logical_path))

    @property
    def filename_keylen(self):
        """How many leading characters of a row key select a row of this index.

        The value is derived on the first access and stored in
        ``_filename_keylen_filled``. **This is the one lazy property that does not call**
        ``_recache()``, so the value is kept on this object and not written back to the
        shared cache; another object for the same path derives it again. A merged
        directory and an index row are born with the slot set to zero.

        The class's FILENAME_KEYLEN is either the number itself or something callable that
        returns it, and both are accepted here. Zero means the whole basename is the key,
        which is what every object outside an index uses.

        Returns:
            int: the key length in characters.
        """

        if self._filename_keylen_filled is None:
            if isinstance(self.FILENAME_KEYLEN, int):
                self._filename_keylen_filled = self.FILENAME_KEYLEN
            else:
                self._filename_keylen_filled = self.FILENAME_KEYLEN()

        return self._filename_keylen_filled

    @property
    def infoshelf_path_and_key(self):
        """Which info shelf covers this file, and the key to read out of it.

        The value is derived on the first access, stored in ``_infoshelf_path_and_key``
        and returned unchanged afterwards; deriving it calls ``_recache()``. A merged
        directory and an index row are born with the slot set to a pair of empty strings.

        **Every exception the derivation can raise is swallowed** and recorded as a pair
        of empty strings, so this never raises and never distinguishes a file no shelf
        covers from one whose shelf path could not be worked out. That is what makes it
        safe to read on any object, and it is why a caller wanting the reason has to call
        ``shelf_path_and_key_for_abspath()`` itself.

        Returns:
            tuple: the shelf's absolute path and the key within it, or two empty strings.
        """

        cls = type(self)

        if self._infoshelf_path_and_key is None:
            try:
                self._infoshelf_path_and_key = \
                    cls.shelf_path_and_key_for_abspath(self.abspath, 'info')
            except Exception:
                self._infoshelf_path_and_key = ('', '')

            self._recache()

        return self._infoshelf_path_and_key

    @staticmethod
    def version_info(suffix):
        """Read a bundle set suffix as a version.

        The rank is what orders versions, oldest first, and the current version ranks
        above every other at 999999. The four suffixes that name a release stage rank
        between 990100 and 990400, in the order in which a bundle passes through them.

        A numbered suffix ``_v<major>[.<minor>[.<micro>]]`` ranks at ten thousand times
        the major number plus a hundred times the minor plus the micro, so a version can
        be compared with any other of its own bundle set by rank alone for as long as the
        minor and micro numbers stay below 100: ``_v1.100`` and ``_v2`` both rank 20000.
        The id is the number without the leading ``_v``, rebuilt from the same parts, so a
        fourth part is dropped from both the id and the rank while staying in the message,
        and ``_v2.1.3`` and ``_v2.1.3.4`` are indistinguishable by either.

        Every other suffix is rejected. Only the current version and the four stage
        suffixes get an empty version id.

        Parameters:
            suffix: a bundle set suffix. An empty string and None both name the current
                version.

        Returns:
            tuple: the version rank, a phrase describing the version, and the version id.

        Raises:
            ValueError: for a suffix that is neither empty, None, one of the four stage
                names, nor a numbered version; and raised by ``int()`` for a suffix that
                begins ``_v`` whose parts are not whole numbers.
        """

        version_id = ''
        if suffix == '' or suffix is None:
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
            raise ValueError(f'Unrecognized volume set suffix "{suffix}"')

        return (version_rank, version_message, version_id)

    def all_versions(self):
        """Every version of this file that exists, keyed by version rank.

        The dictionary always holds this object under its own rank, whether or not the
        file exists, and one entry for each other version found. The ranks are
        ``version_info()``'s, so they sort oldest to newest and the current version is
        highest.

        **What is remembered is the paths, not the objects.** The first call globs for
        every pattern the class's VERSIONS rules give, builds a PdsFile for each existing
        match, and then writes the path dictionary into ``_all_version_abspaths`` on
        **every** version it found, calling ``_recache()`` on each, so one call fills the
        slot on a whole family of objects. A later call rebuilds the objects from those
        paths rather than globbing again. The objects are deliberately not cached, because
        the shared cache cannot keep the links between them.

        Two versions that reach the same rank cannot both be kept: the second is logged as
        a duplicate and dropped. ``version_info()`` is what makes that possible, by
        ranking only the first three parts of a version suffix.

        Returns:
            dict: version rank mapped to the PdsFile for that version.
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
        """The absolute path of every version of this file, keyed by version rank.

        This is the slot ``all_versions()`` fills, read directly. Where it is empty the
        whole search runs, for its side effect alone; the objects that call builds are
        discarded and only the paths are kept. Afterwards this costs nothing.

        A merged directory reaches this body and fails: the glob is rooted at ``root_``,
        which is None on such an object, so building the pattern raises TypeError.

        Returns:
            dict: version rank mapped to the absolute path of that version.
        """

        if self._all_version_abspaths is None:
            _ = self.all_versions()     # This has the side-effect of filling
                                        # _all_version_abspaths

        return self._all_version_abspaths

    def viewset_lookup(self, name='default'):
        """Find one named set of images for this file, without caching the answer.

        This is the search behind ``viewset`` and ``all_viewsets``, and unlike them it
        stores nothing: every call repeats the work, except for the one shortcut that
        reads an answer ``all_viewsets`` already recorded. A file that does not exist gets
        None at once.

        Four ways of answering are tried in order. The class's VIEWABLES table may give
        glob patterns for this name and path, in which case the matches are globbed, and
        where the first match has a recognizable anchor the rest are narrowed to the files
        sharing it, so one product's images are not mixed with a neighbor's. Failing that,
        a directory asks its children, taking the first non-directory child that answers,
        and **stopping after twenty candidate names**, so a large directory can answer
        None where a viewable exists further down its list. Failing that, a viewable file
        asked for its default set is grouped with the siblings sharing its anchor, which
        is what builds a preview set out of a directory of sizes. Failing all of it, an
        empty view set is returned.

        **The three misses are not the same value.** A file that does not exist and a
        directory whose children all decline give None; everything else that fails gives
        an empty ``PdsViewSet``, which is falsy but is not None.

        Parameters:
            name (str): which view set to look for. It is a key of the class's VIEWABLES
                table, and 'default' is the one every other property asks for.

        Returns:
            pdsviewable.PdsViewSet: the view set, an empty one, or None.
        """

        cls = type(self)

        if not self.exists:
            return None

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
                if pdsf.isdir:
                    continue

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

