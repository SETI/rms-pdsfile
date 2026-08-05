##########################################################################################
# pdsfile/_index_rows.py
# Support for PdsFile objects that represent one selected row of an index table
##########################################################################################

import numbers

import pdstable

from ._path_utils import _clean_join


##########################################################################################
# Index row mixin
##########################################################################################
class _IndexRowsMixin:
    """Support for PdsFile objects representing index rows.

    A mixin of PdsFile; it holds methods only and defines no state of its own.

    These have a path of the form:
      .../filename.tab/selection
    where:
      filename.tab    is the name of an ASCII table file, which must end in
                      ".tab";
      selection       is a string that identifies a row, typically via the
                      basename part of a FILE_SPECIFICATION_NAME.

    Every attribute these methods read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, list and pdstable methods are not in
    scope:

      lazy properties read        childnames, childnames_lc, exists,
                                  filename_keylen, index_pdslabel,
                                  indexshelf_abspath, is_index, label_abspath
      instance attributes read    abspath, basename, column_names, is_index_row,
                                  logical_path, row_dicts
      instance attributes WRITTEN column_names, on self, filled from the table's
                                  own column info when it is still empty; and
                                  _exists_filled, on each newly built row object
      class attribute read        CACHE, and __bases__ -- see below
      other methods called        bundleset_abspath, new_index_row_pdsfile,
                                  parent, sort_basenames, from_abspath

    All of them are defined on PdsFile. Two more come from sibling mixins:
    get_indexshelf reaches _ShelfMixin's _get_shelf, and
    data_abspath_associated_with_index_row reaches _LocalFsMixin's
    os_path_exists. Every one of these is an attribute lookup on self or on
    type(self) at run time, not an import, which is what lets the halves live in
    different modules.

    data_abspath_associated_with_index_row chooses between the PDS3 and PDS4
    column-name tables by comparing type(self).__bases__[0].__name__ against the
    string 'Pds4File'. That reads a rule subclass's direct base, which mixin
    bases on PdsFile do not change. It is fragile all the same: a subclass one
    level deeper, or one whose first base is not the PDS3/PDS4 class, silently
    gets the PDS3 table.
    """

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
            raise OSError('Index file does not exist: ' + self.logical_path)

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
                raise OSError('Index selection is ambiguous: ' +
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

            parts = [self.bundleset_abspath('volumes')]
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
