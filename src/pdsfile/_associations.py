##########################################################################################
# pdsfile/_associations.py
##########################################################################################

"""Given one file, the files that go with it elsewhere in the holdings tree.

A holdings tree keeps parallel copies of the same structure under different category
names: the data itself under ``volumes`` or ``bundles``, and beside it ``previews``,
``diagrams``, ``calibrated``, ``metadata``, and the ``checksums-`` and ``archives-``
variants of each. A question this module answers is of the form "given this data file,
which previews go with it", and the answer is a list rather than a single file, because
one data file can have several previews and one metadata table can cover many data
files.

Two mechanisms produce the answer. The rule modules define association tables that map a
logical path to the wildcard patterns naming its counterparts, and those patterns are
matched against the tree. Where no rule applies, the same interior path is looked for in
the parallel tree, and the deepest part of it that exists is used, so a file with no
counterpart yields its directory rather than nothing.

``associated_abspaths()`` is the general answer, with
``associated_logical_paths()`` and ``associated_pdsfiles()`` as conversions of it.
``associated_parallel()`` answers the narrower question of the single most similar file
in one parallel tree, optionally at another version, and caches its answer on the object
it resolves the question against, which is not always the one it was asked about.
"""

import os

from ._path_utils import _clean_join, _needs_glob


##########################################################################################
# Associations mixin
##########################################################################################
class _AssociationsMixin:
    """The files associated with this one in another category of the holdings tree.

    A mixin of PdsFile; it holds methods only and defines no state of its own.

    Given a PdsFile and a target category -- volumes, previews, metadata,
    diagrams, calibrated, checksums-*, archives-* -- these methods return the
    files in that category that go with it, as abspaths
    (associated_abspaths), logical paths (associated_logical_paths) or PdsFile
    objects (associated_pdsfiles). associated_parallel answers the narrower
    question of the single "most similar" file in a parallel tree, optionally at
    another version rank, and caches its answer on the object it resolves the
    question against, which is not always the one it was asked about.

    The association rules themselves are not here: the ASSOCIATIONS translator
    and the CATEGORIES set stay on PdsFile, where each rule subclass supplies its
    own, and these methods read them off the class.

    Every attribute these methods read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, list, dict, translator and os.path
    methods are not in scope::

      lazy properties read        all_version_abspaths, data_abspaths, exists,
                                  is_category_dir, isdir, label_basename
      instance attributes read    abspath, bundlename, bundletype_, category_,
                                  interior, is_index_row, logical_path,
                                  version_rank
      instance attributes WRITTEN _associated_parallels_filled, which
                                  associated_parallel initializes to {} on first
                                  use and then fills; _recache() writes the
                                  object back to the cache afterwards. The object
                                  written is the one the request resolved to, not
                                  necessarily the one asked
      class attributes read       ASSOCIATIONS, CATEGORIES
      other methods called        _recache, all_versions, bundle_pdsfile,
                                  bundleset_pdsfile, parent, from_abspath,
                                  from_logical_path

    All of those are defined on PdsFile. Nine more come from sibling mixins, and
    they are why this is the deepest layer in the class::

      _DerivedPathsMixin          archive_path_and_lskip,
                                  checksum_path_and_lskip
      _IndexRowsMixin             child_of_index,
                                  data_abspath_associated_with_index_row
      _LocalFsMixin               glob_glob, os_path_exists
      _SortingMixin               abspaths_for_logicals, logicals_for_abspaths,
                                  pdsfiles_for_abspaths

    Every one of these is an attribute lookup on self or on type(self) at run
    time, not an import, which is what lets the layers live in different modules.
    The dependency runs one way: nothing in _SortingMixin calls back into this
    module.

    One more class attribute, IDX_EXT, is defined only on Pds3File and Pds4File,
    not on PdsFile; associated_abspaths reads it. A bare PdsFile never gets that
    far: ASSOCIATIONS is None on it, so the same method raises TypeError earlier,
    at the ASSOCIATIONS lookup, and never reaches IDX_EXT. Either way
    associated_abspaths works on a subclass instance and not on a bare PdsFile.

    associated_parallel is the only method here that writes anything. It fills
    _associated_parallels_filled on the object the request resolved to -- this
    one where the volume type is unchanged, and this file's latest version where
    it is not -- and calls _recache, so a lookup changes a cached object; the
    other three read only.
    """

    ############################################################################
    # Associations
    ############################################################################

    def associated_logical_paths(self, category, must_exist=True):
        """Return the logical paths of the files associated with this one.

        The same answer as ``associated_abspaths()``, converted. The conversion drops the
        holdings root from each path, so the result is the same on any machine hosting
        the same holdings.

        Parameters:
            category (str): the category to look in, with any surrounding slashes
                ignored.
            must_exist (bool): whether to return only paths that exist.

        Returns:
            list: the logical paths, in the order ``associated_abspaths()`` produced
            them. The duplicates were removed from the absolute paths, so two paths
            under different holdings directories that share one logical path both
            survive into this list.

        Raises:
            TypeError: raised by ``associated_abspaths()`` on a bare PdsFile, whose
                association table is None.
            ValueError: raised by ``logicals_for_abspaths()`` if an associated path does
                not lie under a holdings directory.
        """

        cls = type(self)
        abspaths = self.associated_abspaths(category, must_exist=must_exist)
        return cls.logicals_for_abspaths(abspaths)

    def associated_pdsfiles(self, category, must_exist=True):
        """Return PdsFile objects for the files associated with this one.

        The same answer as ``associated_abspaths()``, converted. Each object is
        constructed from its path, so asking with ``must_exist`` False yields objects for
        files that are not there.

        Parameters:
            category (str): the category to look in, with any surrounding slashes
                ignored.
            must_exist (bool): whether to return only paths that exist.

        Returns:
            list: the PdsFile objects, without duplicates, in the order
            ``associated_abspaths()`` produced them.

        Raises:
            TypeError: raised by ``associated_abspaths()`` on a bare PdsFile, whose
                association table is None.
            ValueError: raised by ``pdsfiles_for_abspaths()`` if an associated path does
                not lie under a holdings directory.
        """

        cls = type(self)
        abspaths = self.associated_abspaths(category, must_exist=must_exist)
        return cls.pdsfiles_for_abspaths(abspaths)

    def associated_abspaths(self, category, must_exist=True):
        """Return the absolute paths of the files associated with this one.

        Absolute paths only, never logical ones; ``associated_logical_paths()`` is the
        one that converts.

        An index row is not itself associated with anything, so it is first replaced by
        the data file its row describes, or, where that cannot be found, by the index
        file that holds it. A checksums or archives category is answered by asking for
        its plain category first and then mapping each answer to its checksum or archive
        file; an answer that has none -- a cumulative metadata file, which belongs to a
        bundle set rather than to a bundle -- is dropped rather than reported.

        Otherwise the class's association table turns this file's logical path into
        patterns, which are matched against the tree, case-sensitively. If the table
        yields nothing, the parallel-tree search is used instead, and its single answer
        becomes the whole list. A pattern naming a row of an index table is split at the
        extension and the row part is resolved through the index, so a row that the
        index does not hold is dropped.

        The matching runs once per index extension the class defines, so a class with
        two of them does the work twice. Duplicates are removed at the end, which is what
        keeps the repetition invisible where both passes match the same files. It is not
        invisible for a pattern naming an index row: the pass that recognizes the row
        rewrites the pattern down to the index file itself, and that rewrite persists
        into the next pass, which finds no extension of its own in the shortened pattern
        and so matches the bare index file. The row and the index file are different
        paths, so the dedup keeps both.

        Asking for this file's own volume type also brings in its label, if it has one,
        and the data files it points at.

        Parameters:
            category (str): the category to look in, with any surrounding slashes
                ignored.
            must_exist (bool): whether to return only paths that exist. False still
                globs a pattern that holds a wildcard, because there is nothing else to
                expand it against; it changes the answer only for a pattern that names
                one file.

        Returns:
            list: the absolute paths, without duplicates, in the order they were found.

        Raises:
            TypeError: on a bare PdsFile, whose association table is None, from the
                item read ``__getitem__()`` on it.
            KeyError: from the same item read ``__getitem__()``, if the class has an
                association table but no entry for the category asked for.
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
            for ext in cls.IDX_EXT:
                if f'{ext}/' in pattern:
                    parts = pattern.rpartition(ext)
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
                        except (OSError, KeyError):
                            pass

                    test_abspaths = filtered_abspaths

                abspaths += test_abspaths

        # Include any labels and targets
        if category == self.bundletype_[:-1]:
            label_basename = self.label_basename
            if label_basename:
                parent_abspath = os.path.split(self.abspath)[0]
                label_abspath = _clean_join(parent_abspath, label_basename)
                if label_abspath not in abspaths:
                    abspaths.append(label_abspath)

            if must_exist:
                for path in self.data_abspaths:
                    if cls.os_path_exists(path):
                        abspaths.append(path)
            else:
                abspaths += self.data_abspaths

        # Remove duplicates
        abspaths = [p for (k,p) in enumerate(abspaths) if p not in abspaths[:k]]
        return abspaths

    def associated_parallel(self, category=None, rank=None):
        """Return the single most similar file in one parallel tree.

        Where ``associated_abspaths()`` returns every counterpart, this returns one: the
        deepest path in the requested tree that exists and matches this file as far as
        it can. A file whose exact counterpart is missing yields the deepest directory
        above it that is there. A file whose bundle has no counterpart falls back to its
        bundle set's, and the answer is None only where that too is missing or does not
        exist.

        Asking for no category asks about this file's own, which is how the version
        ranks are reached. Asking for a category with a different volume type first
        moves to this file's latest version, because a cross-type match is defined only
        against the latest; that is also why the word ranks are rejected for such a
        request, apart from "latest", which is what the move already did.

        A rank of None means the latest version wherever the category asked for is this
        file's own, and wherever the volume type differs, since the move to the latest
        has already happened by then. It means the version this object already has only
        where the category differs and the volume type does not, because the path built
        for the counterpart carries the version suffix over. A numeric rank names a
        version directly. The words "latest", "previous" and "next" are resolved against
        the list of versions this file has, and "previous" at the oldest and "next" at
        the newest return that same version rather than failing.

        Answers are cached under the category and rank asked for, on the object the
        request resolved to: this one where the volume type is unchanged, and this file's
        latest version where it is not. That object is written back to the shared cache
        when an answer is recorded. The deepest-directory search caches both of its
        outcomes, what it finds and the None it reaches by running off the top.

        Two paths return without caching anything, both of them before the caching
        begins: a category the class does not recognize returns None, and a category
        directory returns the requested category's own directory.

        Parameters:
            category (str): the category to look in, with any trailing slash ignored,
                or None for this file's own.
            rank: the version to look for. None, an integer rank, or one of the words
                "latest", "previous" and "next".

        Returns:
            PdsFile: the parallel file, or None.

        Raises:
            ValueError: for a word rank when the volume type is changing, and for a
                string rank that is not one of the three words.
        """

        cls = type(self)

        def _cache_and_return(pdsf):
            """Record one answer in the cache of the object the request resolved to.

            The argument may be a PdsFile, an absolute path, or None; a path is turned
            into a PdsFile. An object whose file does not exist is replaced by None, and
            None is what gets cached, so a later call gets the same answer without
            looking again.

            The answer is filed under the numeric rank asked for, and also under the
            spelling asked for when that was a word such as "latest", and also under the
            answer's own version rank when no rank was asked for at all. The object is
            then written back to the shared cache, because the dictionary it just
            changed lives on the object.

            An answer equal to this object is cached and returned like any other; it is
            not turned into None.

            Parameters:
                pdsf: the answer, as a PdsFile, an absolute path, or None.

            Returns:
                PdsFile: the answer, or None if it does not exist.
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
            voltype = self.bundletype_[:-1]
        else:
            category = category.rstrip('/')
            voltype = category.rpartition('-')[-1]

        if category not in cls.CATEGORIES:
            return None

        # Handle category-level parallel
        if self.is_category_dir:
            return cls.from_logical_path(category)

        # Handle a change in voltype
        if voltype != self.bundletype_[:-1]:

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

            if voltype != self.bundletype_[:-1]:
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
            parallel = self.bundleset_pdsfile(category, rank)
            return _cache_and_return(parallel)

        # If category is unchanged, use all_versions() instead
        if category == self.category_[:-1]:
            if rank is None:
                rank = max(self.all_version_abspaths.keys())
            return _cache_and_return(self.all_versions().get(rank,None))

        # Prepare for parallel volume tree comparion
        old_root = self.bundle_pdsfile()
        new_root = self.bundle_pdsfile(category, rank)

        if not new_root:
            # If there's no volume-level match, try the volset-leve match
            # This happens for category = 'checksums-archives-whatever'
            return _cache_and_return(self.bundleset_pdsfile(category, rank))

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
