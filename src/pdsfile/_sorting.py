##########################################################################################
# pdsfile/_sorting.py
# Splitting, sorting, and bulk conversion between PdsFile objects, abspaths, logical
# paths and basenames
##########################################################################################

import os

from ._path_utils import _clean_join, abspath_for_logical_path, logical_path_from_abspath


##########################################################################################
# Sorting mixin
##########################################################################################
class _SortingMixin:
    """Splitting and sorting filenames, and bulk conversion between representations.

    A mixin of PdsFile; it holds methods only and defines no state of its own.

    Two groups of methods, kept together because they are one domain -- bulk
    operations over lists of basenames, logical paths, abspaths and PdsFile
    objects. None of them reads the filesystem itself: the four that need to
    probe it delegate to _LocalFsMixin, as the contract below records.

      splitting and sorting   split_basename, basename_is_label,
                              basename_is_viewable, sort_basenames,
                              sort_sibnames, sort_siblings, sort_logical_paths,
                              sort_childnames, viewable_childnames,
                              childnames_by_anchor, viewable_childnames_by_anchor
      bulk conversion         the twelve <plural>_for_<plural> methods, which
                              convert any of PdsFile objects, abspaths, logical
                              paths and basenames into any other

    The sort *configuration* is not here: SORT_ORDER, SORT_KEY and the
    sort_labels_after / sort_dirs_first / sort_dirs_last / sort_info_first
    setters stay on PdsFile, which is what these methods read them off.

    Every attribute these methods read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, list, set, dict, regex, translator,
    os.path and logger methods are not in scope:

      lazy properties read        childnames, exists, info_basename
      instance attributes read    abspath, basename, logical_path
      instance attributes written none
      class attributes read       LOGGER, SORT_KEY, SORT_ORDER, SPLIT_RULES,
                                  VIEWABLE_EXTS
      other methods called        child, parent, from_abspath,
                                  from_logical_path, version_info

    All of those are defined on PdsFile. Two more come from a sibling mixin:
    sort_basenames reaches _LocalFsMixin's os_path_isdir, and
    logicals_for_abspaths, basenames_for_abspaths and abspaths_for_logicals
    reach its os_path_exists. Every one of these is an attribute lookup on self
    or on type(self) at run time, not an import, which is what lets the halves
    live in different modules.

    Four more class attributes are defined only on Pds3File and Pds4File, not on
    PdsFile: split_basename reads BUNDLENAME_PLUS_REGEX and BUNDLESET_PLUS_REGEX,
    sort_basenames reads BUNDLESET_PLUS_REGEX_I, and basename_is_label reads
    LBL_EXT. So basename_is_label and sort_basenames raise AttributeError on a
    bare PdsFile; split_basename does not, because SPLIT_RULES is None there and
    it returns before reaching either regex. That is how they have always
    behaved.
    """

    ############################################################################
    # How to split and sort filenames
    ############################################################################

    def split_basename(self, basename=''):
        """Return the tuple with basename info: (anchor, suffix, extension).

        Default behavior is to split a file at first period; split a bundle set name
        before the suffix. Can be overridden.

        Keyword arguments:
            basename -- basename of a file (default '')
        """

        cls = type(self)

        if basename == '':
            basename = self.basename

        if self.SPLIT_RULES is None:
            return basename
        # Special case: bundleset[_...], bundleset[_...]_md5.txt, bundleset[_...].tar.gz
        matchobj = cls.BUNDLESET_PLUS_REGEX.match(basename)
        if matchobj is not None:
            # For PDS4, we capture bundle set + version, so two groups
            if len(matchobj.groups()) == 2:
                return (matchobj.group(1), matchobj.group(2), '')
            else:
                return (matchobj.group(1), matchobj.group(2) + matchobj.group(3),
                        matchobj.group(4))

        # Special case: bundlename[_...]_md5.txt, bundlename[_...].tar.gz
        matchobj = cls.BUNDLENAME_PLUS_REGEX.match(basename)
        if matchobj is not None:
            test = self.SPLIT_RULES.first(basename) # a split rule overrides
                                                    # the default behavior
            if test == basename:
                # For PDS4, we capture bundle name + version, so two groups
                if len(matchobj.groups()) == 2:
                    return (matchobj.group(1), matchobj.group(2), '')
                else:
                    return (matchobj.group(1), matchobj.group(2), matchobj.group(3))
            else:
                return test

        return self.SPLIT_RULES.first(basename)

    def basename_is_label(self, basename):
        """Return True if this basename is a label. Override if label identification
        ever depends on the data set.

        Keyword arguments:
            basename -- basename of a file
        """

        cls = type(self)
        _, _, lbl_ext = basename.rpartition('.')
        return (len(basename) > 4) and (f'.{lbl_ext}'.lower() in cls.LBL_EXT)

    def basename_is_viewable(self, basename=None):
        """Return True if this basename is viewable. Override if viewable files can
        have extensions other than the usual set (.png, .jpg, etc.).

        Keyword arguments:
            basename -- basename of a file
        """

        cls = type(self)

        if basename is None:
            basename = self.basename

        parts = basename.rpartition('.')
        if parts[1] != '.':
            return False

        return (parts[2].lower() in cls.VIEWABLE_EXTS)

    def sort_basenames(self, basenames, labels_after=None, dirs_first=None,
                       dirs_last=None, info_first=None):
        """Return Sorted basenames, including additional options. Input None for
        defaults.

        Keyword arguments:
            basenames    -- a list of file basenames
            labels_after -- a flag used to determine if all label files should appear
                            after the associated data files when sorted (default None)
            dirs_first   -- a flag used to determine if directories should appear before
                            all files when sorted (default None)
            dirs_last    -- a flag used to determine if directories should appear after
                            all files when sorted (default None)
            info_first   -- a flag used to determine info files will be listed first in
                            all sorted lists (default None)
        """

        cls = type(self)

        def modified_sort_key(basename):

            # Volumes of the same name sort by decreasing version number
            matchobj = cls.BUNDLESET_PLUS_REGEX_I.match(basename)
            if matchobj is not None:
                splits = matchobj.groups()
                # For PDS4, we capture bundle set + version, so two groups
                if len(splits) == 2:
                    parts = [splits[0], -cls.version_info(splits[1])[0], '', '']
                else:
                    parts = [
                        splits[0],
                        -cls.version_info(splits[1])[0],
                        matchobj.group(2),
                        matchobj.group(3)
                    ]
            else:
                # Otherwise, the sort is based on split_basename()
                modified = self.SORT_KEY.first(basename)
                splits = self.split_basename(modified)
                parts = [splits[0], 0, splits[1], splits[2]]

            if labels_after:
                # Replace (_, _, _, '.LBL') with (_, _, _, True, '.LBL')
                # Replace anything else with (_, _, _, False, _)
                parts[3:] = [self.basename_is_label(basename), *parts[3:]]

            if dirs_first or dirs_last:
                isdir = cls.os_path_isdir(_clean_join(self.abspath,
                                                          basename))
                if dirs_first:
                    # If this is a directory, put False in front of the sort key
                    # Otherwise, put True in front
                    parts = [not isdir, *parts]
                else:
                    # If this is a directory, put True in front of the sort key
                    # Otherwise, put False in front
                    parts = [isdir, *parts]

            if apply_info_first:
                # If this is an info file, put False in front of the sort key
                # Otherwise, put True in front
                parts = [self.info_basename != basename, *parts]

            return tuple(parts)

        if labels_after is None:
            labels_after = self.SORT_ORDER['labels_after']

        if dirs_first is None:
            dirs_first = self.SORT_ORDER['dirs_first']

        if dirs_last is None:
            dirs_last = self.SORT_ORDER['dirs_last']

        if info_first is None:
            info_first = self.SORT_ORDER['info_first']

        # Put info file first only if the number of children exceeds the
        # specified threshold:
        #   info_first = 0 or False: never put info files first
        #   info_first = 1 or True: always put info files first
        #   info_first > 1: put info files first only if the number of files is
        #                   this large or larger
        apply_info_first = (int(info_first) >= 1 and
                            int(info_first) <= len(basenames))

        basenames = list(basenames)
        basenames.sort(key=modified_sort_key)
        return basenames

    def sort_sibnames(self, basenames, labels_after=None, dirs_first=None,
                      dirs_last=None, info_first=None):
        """Return sorted basenames that represent siblings of this object. In the
        returned list of basenames, the name of this object will be first and
        matching file names will always be adjacent.

        When a selected file and its label and/or targets are displayed in
        Viewmaster, this is the order in which they appear.

        Keyword arguments:
            basenames    -- a list of file basenames
            labels_after -- a flag used to determine if all label files should appear
                            after the associated data files when sorted (default None)
            dirs_first   -- a flag used to determine if directories should appear before
                            all files when sorted (default None)
            dirs_last    -- a flag used to determine if directories should appear after
                            all files when sorted (default None)
            info_first   -- a flag used to determine info files will be listed first in
                            all sorted lists (default None)
        """

        # First, sort the names the usual way
        parent = self.parent()

        if self.basename not in basenames:
            basenames.append(self.basename)

        basenames = parent.sort_basenames(basenames, labels_after, dirs_first,
                                                     dirs_last, info_first)

        # Create a new list with the name of self first
        basenames.remove(self.basename)
        new_basenames = [self.basename]

        # Move any set of files with matching names immediately after it
        pattern = self.basename.partition('.')[0] + '.'    # first dot, not last
        matches = [b for b in basenames if b.startswith(pattern)]
        if matches:
            for match in matches:
                basenames.remove(match)
                new_basenames.append(match)

        # Return the reordered and merged lists
        return new_basenames + basenames

    def sort_siblings(self, siblings, labels_after=None, dirs_first=None,
                      dirs_last=None, info_first=None):
        """Return sorted siblings of this object, keeping this object first.

        Keyword arguments:
            siblings     -- a list of file siblings
            labels_after -- a flag used to determine if all label files should appear
                            after the associated data files when sorted (default None)
            dirs_first   -- a flag used to determine if directories should appear before
                            all files when sorted (default None)
            dirs_last    -- a flag used to determine if directories should appear after
                            all files when sorted (default None)
            info_first   -- a flag used to determine info files will be listed first in
                            all sorted lists (default None)
        """

        # Create a dictionary by basename; remove duplicates too
        basename_dict = {pdsf.basename:pdsf for pdsf in siblings}
        basename_dict[self.basename] = self

        # Sort the basenames
        sibnames = self.sort_sibnames(list(basename_dict.keys()),
                                      labels_after, dirs_first, dirs_last,
                                      info_first)

        # Return the PdsFiles in the newly sorted order
        return [basename_dict[basename] for basename in sibnames]

    @classmethod
    def sort_logical_paths(cls, logical_paths):
        """Retrun sorted list of logical paths. Sort a list of logical paths, using the
        sort order at each level in the directory tree. The logical paths must all have
        the same number of directory levels.

        Keyword arguments:
            logical_paths -- a list of logical paths
        """

        # Create a dictionary of PdsFile objects keyed by logical path/subpath.
        # Also create a dictionary with the same key, containing a list of
        # enclosed names.
        pdsf_dict = {}      # pdsf_dict[logical_path] = PdsFile object
        child_names = {}    # child_names[logical_path] = list of child names
        top_level_names = set()
        for path in logical_paths:
            parts = path.split('/')
            top_level_names.add(parts[0])
            for k in range(1,len(parts)):
                path = '/'.join(parts[:k])
                if path not in pdsf_dict:
                    pdsf = cls.from_logical_path(path)
                    pdsf_dict[path] = pdsf
                    child_names[path] = set()

                child_names[path].add(parts[k])

        # Sort the contents of each directory, replacing each set with a list
        for (path, names) in child_names.items():
            child_names[path] = pdsf_dict[path].sort_basenames(list(names))

        # Sort keys at each level, recursively

        def _append_recursively(path):
            for name in child_names[path]:
                newpath = path + '/' + name
                if newpath in child_names:
                    _append_recursively(newpath)
                else:
                    sorted_paths.append(newpath)

        top_level_names = list(top_level_names)     # normally just one
        top_level_names.sort()

        sorted_paths = []
        for key in top_level_names:
            _append_recursively(key)

        # Under normal circumstances, the list of sorted_paths should be
        # complete. However, just in case...
        extras_in_sort = []
        logical_paths = set(logical_paths)
        for path in sorted_paths.copy():    # a copy so we can modify original
            if path in logical_paths:
                logical_paths.remove(path)
            else:
                extras_in_sort.append(path)
                sorted_paths.remove(path)

        if extras_in_sort and cls.LOGGER:
            for extra in extras_in_sort:
                cls.LOGGER.warn('Extra item removed by sort_logical_paths: ' + extra)

        logical_paths = list(logical_paths)
        logical_paths.sort()
        sorted_paths += logical_paths
        if logical_paths and cls.LOGGER:
            for path in logical_paths:
                cls.LOGGER.warn('Overlooked item added by sort_logical_paths: ' + path)

        return sorted_paths

    def sort_childnames(self, labels_after=None, dirs_first=None):
        """Return a sorted list of the contents of this directory.

        Keyword arguments:
            labels_after -- a flag used to determine if all label files should appear
                            after the associated data files when sorted (default None)
            dirs_first   -- a flag used to determine if directories should appear before
                            all files when sorted (default None)
        """

        return self.sort_basenames(self.childnames, labels_after, dirs_first)

    def viewable_childnames(self):
        """Return A sorted list of the files in this directory that are viewable."""

        return [b for b in self.childnames if self.basename_is_viewable(b)]

    def childnames_by_anchor(self, anchor):
        """Return a list of child basenames having the given anchor.

        Keyword arguments:
            anchor -- anchor of a basename
        """

        matches = []
        for basename in self.childnames:
            parts = self.split_basename(basename)
            if parts[0] == anchor:
                matches.append(basename)

        return matches

    def viewable_childnames_by_anchor(self, anchor):
        """Return a list of viewable child names having the given anchor.

        Keyword arguments:
            anchor -- anchor of a basename
        """

        matches = self.childnames_by_anchor(anchor)
        return [m for m in matches if self.basename_is_viewable(m)]

    ############################################################################
    # Transformations
    ############################################################################

    #### ... for pdsfiles

    @staticmethod
    def abspaths_for_pdsfiles(pdsfiles, must_exist=False):
        if must_exist:
            return [p.abspath for p in pdsfiles if p.abspath is not None
                                                and p.exists]
        else:
            return [p.abspath for p in pdsfiles if p.abspath is not None]

    @staticmethod
    def logicals_for_pdsfiles(pdsfiles, must_exist=False):
        if must_exist:
            return [p.logical_path for p in pdsfiles if p.exists]
        else:
            return [p.logical_path for p in pdsfiles]

    @staticmethod
    def basenames_for_pdsfiles(pdsfiles, must_exist=False):
        if must_exist:
            return [p.basename for p in pdsfiles if p.exists]
        else:
            return [p.basename for p in pdsfiles]

    #### ... for abspaths

    @classmethod
    def pdsfiles_for_abspaths(cls, abspaths, must_exist=False):
        pdsfiles = [cls.from_abspath(p) for p in abspaths]
        if must_exist:
            pdsfiles = [pdsf for pdsf in pdsfiles if pdsf.exists]

        return pdsfiles

    @classmethod
    def logicals_for_abspaths(cls, abspaths, must_exist=False):
        if must_exist:
            abspaths = [p for p in abspaths if cls.os_path_exists(p)]

        return [logical_path_from_abspath(p, cls) for p in abspaths]

    @classmethod
    def basenames_for_abspaths(cls, abspaths, must_exist=False):
        if must_exist:
            abspaths = [p for p in abspaths if cls.os_path_exists(p)]

        return [os.path.basename(p) for p in abspaths]

    #### ... for logicals

    @classmethod
    def pdsfiles_for_logicals(cls, logical_paths, must_exist=False):
        pdsfiles = [cls.from_logical_path(p) for p in logical_paths]
        if must_exist:
            pdsfiles = [pdsf for pdsf in pdsfiles if pdsf.exists]

        return pdsfiles

    @classmethod
    def abspaths_for_logicals(cls, logical_paths, must_exist=False):
        abspaths = [abspath_for_logical_path(p, cls) for p in logical_paths]
        if must_exist:
            abspaths = [p for p in abspaths if cls.os_path_exists(p)]

        return abspaths

    @classmethod
    def basenames_for_logicals(cls, logical_paths, must_exist=False):
        if must_exist:
            pdsfiles = cls.pdsfiles_for_logicals(logical_paths,
                                                     must_exist=must_exist)
            return cls.basenames_for_pdsfiles(pdsfiles)
        else:
            return [os.path.basename(p) for p in logical_paths]

    #### ... for basenames

    def pdsfiles_for_basenames(self, basenames, must_exist=False):

        pdsfiles = [self.child(b) for b in basenames]

        if must_exist:
            pdsfiles = [p for p in pdsfiles if p.exists]

        return pdsfiles

    def abspaths_for_basenames(self, basenames, must_exist=False):
        # shortcut
        if self.abspath and not must_exist:
            return [_clean_join(self.abspath, b) for b in basenames]

        pdsfiles = self.pdsfiles_for_basenames(basenames, must_exist=must_exist)
        return [pdsf.abspath for pdsf in pdsfiles]

    def logicals_for_basenames(self, basenames, must_exist=False):
        # shortcut
        if not must_exist:
            return [_clean_join(self.logical_path, b) for b in basenames]

        pdsfiles = self.pdsfiles_for_basenames(basenames, must_exist=must_exist)
        return [pdsf.logical_path for pdsf in pdsfiles]
