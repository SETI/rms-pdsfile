##########################################################################################
# pdsfile/_index_rows.py
##########################################################################################

"""PdsFile objects that stand for one selected row of an index table.

An index file is an ASCII table, one row per data file, that a bundle ships so that a
whole bundle can be searched without opening every file it describes. A row of such a
table is addressable as a file of its own, with a path of the form
``.../filename.tab/selection``, where the selection identifies the row -- normally
through the basename part of its file specification.

``_IndexRowsMixin`` is what makes those paths work. ``get_indexshelf()`` opens the shelf
that maps a selection to its row numbers; ``find_selected_row_key()`` turns a
user-supplied, possibly incomplete selection into an exact key; ``child_of_index()``
builds the PdsFile for a row, reading the table only for a row that exists; and
``data_abspath_associated_with_index_row()`` and ``data_pdsfile_for_index_row()`` go
back the other way, from a row to the data file the row describes.
"""

import numbers

import pdstable

from ._path_utils import _clean_join


##########################################################################################
# Index row mixin
##########################################################################################
class _IndexRowsMixin:
    """Support for PdsFile objects representing index rows.

    A mixin of PdsFile; it holds methods only and defines no state of its own.

    These have a path of the form::

      .../filename.tab/selection

    where::

      filename.tab    is the name of an ASCII table file, which must end in
                      ".tab";
      selection       is a string that identifies a row, typically via the
                      basename part of a FILE_SPECIFICATION_NAME.

    Every attribute these methods read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, list and pdstable methods are not in
    scope::

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
                                  parent, from_abspath

    All of them are defined on PdsFile. Three more come from sibling mixins:
    get_indexshelf reaches _ShelfMixin's _get_shelf, find_selected_row_key
    reaches _SortingMixin's sort_basenames, and
    data_abspath_associated_with_index_row reaches _LocalFsMixin's
    os_path_exists. The sort_basenames reach brings the most with it: that method
    matches each name against BUNDLESET_PLUS_REGEX_I, which only Pds3File and
    Pds4File define, so the neighbor search works on a subclass instance and
    raises AttributeError on a bare PdsFile. Every one of these is an attribute
    lookup on self or on type(self) at run time, not an import, which is what lets
    the halves live in different modules.

    data_abspath_associated_with_index_row chooses between the PDS3 and PDS4
    column-name tables by comparing type(self).__bases__[0].__name__ against the
    string 'Pds4File'. That reads a rule subclass's direct base, which mixin
    bases on PdsFile do not change. It is fragile all the same: a subclass one
    level deeper, or one whose first base is not the PDS3/PDS4 class, silently
    gets the PDS3 table. One of those cases is the class the PDS4 registry hands
    out for a bundle set with no rule module of its own: that class is Pds4File
    itself, whose first base is named 'PdsFile', so a row of such a bundle set is
    read with the PDS3 column names, which are not the same list.

    child_of_index neither writes the shared cache nor effectively reads it. The
    read is keyed by the row's absolute path, and the cache holds only lowercased
    logical paths, so it always misses; the object built is returned to the caller
    and is not stored. Two calls for one row therefore build two objects and read
    the index table twice.
    """

    def get_indexshelf(self):
        """Return the shelf dictionary mapping each row key of an index to its rows.

        The shelf is opened through the shared open-shelf cache, so a second call on the
        same index normally does not touch the filesystem. A missing shelf file is not
        logged, because the failure is interpreted here instead: a file that does not
        exist and a file that exists but is not an index each get an error naming the
        logical path, and anything else is re-raised exactly as the shelf machinery
        raised it.

        Returns:
            dict: the row key mapped to a row number or a sequence of row numbers.

        Raises:
            OSError: if the index file does not exist.
            ValueError: if the file exists but is not usable as an index.
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
        """Return the row key of this index that a selection identifies.

        The selection is first truncated to the class's ``filename_keylen`` if that is
        set, so a full basename can be handed in where the keys are truncated ones. It
        is then matched against the index's row keys in this order, and the first match
        wins: exactly; ignoring case; a key that is a prefix of the selection, taking
        the **longest** such key if there are several; and a key the selection is a
        prefix of, only if that key is unique.

        What happens when nothing matches depends on the flag:

          * ``'='`` raises, which is the default.
          * ``'>'`` returns the key that would follow the selection in sorted order, or
            the index's own last key if the selection would sort last.
          * ``'<'`` returns the key that would precede it, or the index's own first key
            if the selection would sort first.
          * ``''`` returns the selection itself, unchanged.

        The ``''`` case is reached only when partial matching was allowed. With an exact
        match required, an unmatched selection falls through to the neighbor search
        instead, so ``''`` then behaves like ``'>'``.

        What a flag outside those four raises depends on the flag's own text. The guard
        interpolates the flag into an f-string and then applies ``%`` to the result, with
        the flag again as the argument, so the outcome turns on whether that text carries
        a conversion. A flag with none, such as ``'bogus'``, makes ``%`` raise TypeError
        for the argument it cannot consume, before the ValueError can be constructed; a
        flag that is exactly one string conversion, such as ``'%s'``, makes ``%`` succeed
        and the ValueError is raised as written; and a flag carrying a numeric conversion
        such as ``'%d'`` raises TypeError from the conversion itself.

        Parameters:
            selection (str): the row key to look for, exact or partial.
            flag (str): what to do when nothing matches, as above.
            exact_match (bool): whether to skip the two partial-match passes.

        Returns:
            str: the row key.

        Raises:
            KeyError: under flag ``'='``, if nothing matched.
            OSError: if the selection is a prefix of more than one key, which makes it
                ambiguous. The longest-match rule resolves the other direction but not
                this one.
            IndexError: raised by the neighbor lookup, which is item syntax, when the
                index has no keys at all. The list indexed is the index's own keys with
                the selection appended, so a single key is enough for either fallback to
                land on it, and only an empty key list leaves nothing to return. It comes
                from ``__getitem__()`` on the sorted key list.
            ValueError: for a flag outside the four, reached when the flag's text is
                exactly one string conversion, as above.
            TypeError: for a flag outside the four whose text carries no conversion or a
                numeric one. The ``%`` applied to the guard's message then fails while
                the argument to ``ValueError()`` is being evaluated, so the ValueError
                above is never constructed for such a flag.
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
        """Return the PdsFile for one selected row of this index.

        The selection is resolved to a row key first, with partial matching allowed, so
        the flag means here exactly what it means there: ``'='`` raises when nothing
        matches, ``'>'`` and ``'<'`` fall back to a neighboring key, and ``''`` accepts
        the selection as given. The object this returns can therefore stand for a row
        that is not in the index at all, and its ``exists`` is already filled in to say
        which case it is.

        The shared cache is consulted first, under the row's absolute path, but nothing
        is ever stored under a key of that shape: the cache is keyed by lowercased
        logical paths, so this lookup always misses and the row is always built. Building
        it means the shelf gives the row numbers for the key, the table is read over just
        the span those numbers cover, and the resulting row dictionaries are attached to
        the new object. Reading the table also fills in this index's ``column_names`` if
        they were still empty. A key that is not among the index's own keys skips all of
        that and yields an object with no row dictionaries.

        The object built is **not** written to the cache either, so two calls for one row
        return two objects and read the table twice.

        Parameters:
            selection (str): the row key to look for, exact or partial.
            flag (str): what to do when nothing matches, as in
                ``find_selected_row_key()``.

        Returns:
            PdsFile: the object for that row.

        Raises:
            KeyError: raised by ``find_selected_row_key()`` under flag ``'='`` when
                nothing matches. The shelf lookup that follows uses a key that came from
                the index's own key list, so it does not add a second source of KeyError.
            OSError: raised by ``find_selected_row_key()`` on an ambiguous selection, and
                by ``get_indexshelf()`` when the index file is missing.
            ValueError: raised by ``get_indexshelf()`` when the file is not an index, and
                by ``find_selected_row_key()`` for a flag outside the four whose text is
                exactly one string conversion.
            TypeError: raised by ``find_selected_row_key()`` for a flag outside the four
                whose text carries no conversion or a numeric one.
            IndexError: raised by ``find_selected_row_key()`` when a neighbor was asked
                for and the index has no keys at all.
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
        """Return the absolute path of the data file this index row describes.

        The row's own columns are the first source: the file specification column names
        the file, and the volume and path columns, when the table has them, say where
        under the bundles tree it sits. The path is assembled from this object's own
        bundle set, in the ``volumes`` category, so a row of an index that lives
        somewhere else still points into the bundles tree. The version does not travel
        with it: a bundle set's suffix is carried into another category only where that
        category's volume type is this object's own, so a row of a ``metadata`` index
        names the unversioned ``volumes`` bundle set, which is the most recent version,
        whatever version the index itself belongs to.

        A row that is not in the index has no columns to read, and then the neighbors
        are tried instead: the row before it and the row after it are resolved through
        the parent index, each is asked the same question recursively, and the answer is
        rewritten by substituting this row's basename for the neighbor's. That rewrite
        is accepted only if the neighbor really is a different row and the rewritten
        path exists, which is what keeps a guess from being returned as a fact.

        An empty string is the answer for three failures: an object that is not an index
        row, a table with no recognizable file specification column, and a missing row
        whose neighbors were resolved but yielded nothing. It is not the answer for
        everything that can go wrong, because the neighbor path is unguarded: resolving
        a neighbor goes through ``child_of_index()``, and what that raises propagates.

        Returns:
            str: the absolute path, or an empty string.

        Raises:
            OSError: raised through ``child_of_index()`` when this row's own basename is
                a prefix of more than one of the index's keys, which makes the neighbor
                lookup ambiguous, and when the index file behind the parent is missing.
            ValueError: raised through ``child_of_index()`` when the parent's file is not
                usable as an index.
            IndexError: raised through ``child_of_index()`` when the parent index has no
                keys at all, so the neighbor lookup has nothing to return.
        """

        cls = type(self)

        # Internal function identifies the row_dict keys for filespec,
        # path_name (optional), and volume
        def get_keys(row_dict):
            """Return the column names this row uses for volume, path and file spec.

            Which names to look for depends on whether this is a PDS3 or a PDS4 index,
            which is decided from the name of the enclosing object's first base class.
            The file specification column is the first candidate the row has; the volume
            column is the **last** one it has, because that loop does not stop at its
            first hit. A path column is recognized only under the exact name
            ``PATH_NAME``.

            Parameters:
                row_dict (dict): one row of the table, keyed by column name.

            Returns:
                tuple: the volume, path and file specification column names, each an
                empty string when the row has no such column. All three are empty when
                there is no file specification column, because the other two are then
                not looked for.
            """

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
        """Return the PdsFile for the data file this index row describes.

        It is the object for the path ``data_abspath_associated_with_index_row()``
        works out, so everything that makes that path an empty string makes this None,
        and everything that makes it raise raises here too. The object is constructed
        from the path, so it is returned whether or not the file is there.

        Returns:
            PdsFile: the data file, or None if no path could be inferred.

        Raises:
            OSError: raised by ``data_abspath_associated_with_index_row()`` when a
                missing row's neighbor lookup is ambiguous, and when the index file
                behind the parent is missing.
            ValueError: raised by ``data_abspath_associated_with_index_row()`` when the
                parent's file is not usable as an index.
            IndexError: raised by ``data_abspath_associated_with_index_row()`` when the
                parent index has no keys at all.
        """

        cls = type(self)

        abspath = self.data_abspath_associated_with_index_row()
        if abspath:
            return cls.from_abspath(abspath)
        else:
            return None
