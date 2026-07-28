##########################################################################################
# pdsfile/_properties.py
# The lazy properties of a PdsFile: values derived on first access, held in the
# object's _X_filled slots, and written back to the shared cache
##########################################################################################

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

    Sixty-four of the sixty-eight members are lazy properties with the same
    shape: return the already-filled _X_filled slot if there is one, otherwise
    derive the value, store it in that slot, and call self._recache() so the
    shared cache keeps the filled object. The slots are created by
    PdsFile.__init__ and _recache lives in PdsFile, both of which stay in core,
    which is what makes the split transparent. The other four are not
    properties: version_info, a staticmethod mapping a bundleset suffix to a
    (rank, message, id) triple; all_versions, which collects the same file across
    version ranks; viewset_lookup, which picks a named PdsViewSet; and
    _repair_width_height, which reopens an image whose shelf-recorded dimensions
    are missing.

    Every attribute these bodies read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, list, dict, file, os, os.path,
    datetime, PIL, pdsparser, pdsviewable and logger methods are not in scope,
    and neither is any name this mixin defines itself:

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
      core lazy properties read   is_bundle, is_bundle_dir, is_bundleset,
                                  is_bundleset_dir
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

    The receivers are not all self and cls: all_versions writes through a
    sibling pdsf, viewset_lookup reads through child and through the parent it
    fetches, and internal_link_info reads through self.parent(). They are why the
    lists above are derived by walking every attribute node rather than only
    self.X and cls.X.

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

        return self.bundletype_ == 'documents/'

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

        self._recache()
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
                if '/metadata/' in self.abspath:
                    for ext in cls.IDX_EXT:
                        if self.abspath.lower().endswith(ext):
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

        elif self.bundletype_ not in ('volumes/', 'calibrated/', 'metadata/'):
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
    def bundle_publication_date(self):
        """Return the publication date for this bundle as a formatted string."""

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
        """Return version ID of this bundle."""

        if self._bundle_version_id_filled is None:
            if self._volume_info[2] is None:
                self._bundle_version_id_filled = ''
            else:
                self._bundle_version_id_filled = self._volume_info[2]

            self._recache()

        return self._bundle_version_id_filled

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
            except Exception:
                self._infoshelf_path_and_key = ('', '')

            self._recache()

        return self._infoshelf_path_and_key

    @staticmethod
    def version_info(suffix):
        """Return a tuple of version info (version rank, version message, version id).
        This is the Procedure to associate a volset suffix with a version rank value.

        Keyword arguments:
            suffix -- a volset suffix
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

