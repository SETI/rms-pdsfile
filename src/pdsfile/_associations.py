##########################################################################################
# pdsfile/_associations.py
# The category-crossing lookup layer: given one PdsFile, the files associated with it in
# another category of the holdings tree
##########################################################################################

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
    another version rank, and caches its answer on the object.

    The association rules themselves are not here: the ASSOCIATIONS translator
    and the CATEGORIES set stay on PdsFile, where each rule subclass supplies its
    own, and these methods read them off the class.

    Every attribute these methods read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, list, dict and translator methods are
    not in scope:

      lazy properties read        all_version_abspaths, data_abspaths, exists,
                                  is_category_dir, isdir, label_basename
      instance attributes read    abspath, bundlename, bundletype_, category_,
                                  interior, is_index_row, logical_path,
                                  version_rank
      instance attributes WRITTEN _associated_parallels_filled, on self, which
                                  associated_parallel initializes to {} on first
                                  use and then fills; _recache() writes the
                                  object back to the cache afterwards
      class attributes read       ASSOCIATIONS, CATEGORIES
      other methods called        _recache, all_versions, bundle_pdsfile,
                                  bundleset_pdsfile, parent, from_abspath,
                                  from_logical_path

    All of those are defined on PdsFile. Nine more come from sibling mixins, and
    they are why this is the deepest layer in the class:

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
    far -- ASSOCIATIONS is None on it, so the same method raises TypeError on the
    line above -- but neither method works on anything but a subclass instance.
    That is how they have always behaved.
    """

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
                        except (KeyError, IOError):
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
