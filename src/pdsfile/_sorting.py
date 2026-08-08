##########################################################################################
# pdsfile/_sorting.py
##########################################################################################

"""Splitting and sorting filenames, and converting between the four ways to name a file.

Two jobs live here because they are one domain: operating on many files at once rather
than on one.

The first is **order**. A directory listing that reads well is not alphabetical: a file
should sit next to its label, the newest version of a bundle should come before the
older ones, and a directory of a thousand files should put its AAREADME at the top.
``sort_basenames()`` is where those rules are applied, from a sort key built out of a
name's parts rather than out of the name; ``split_basename()`` is what produces those
parts; and the other sorters are variations -- keeping one file first, sorting whole
paths level by level, sorting a directory's own contents.

The second is **bulk conversion**. A file can be named by a PdsFile object, an absolute
path, a logical path or a basename, and different callers hold different ones. The
twelve ``<plural>_for_<plural>()`` methods convert a list of any of the four into a list
of any other, each with the same option to drop the ones that do not exist.

Nothing here reads the filesystem itself. Four methods reach ``_LocalFsMixin``
directly: ``sort_basenames()`` to tell a directory from a file, and three of the bulk
converters to drop what does not exist. Six more converters drop what does not exist
through the ``exists`` lazy property, which reaches the same place, and the last three
do so through one of those six.
"""

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
    objects. None of them reads the filesystem itself: four reach _LocalFsMixin
    directly, six more reach it through the exists lazy property, and the last
    three reach it through one of those six, as the contract below records::

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
    os.path and logger methods are not in scope::

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
    bare PdsFile, sort_basenames only once it has a name to build a key for;
    split_basename does not, because SPLIT_RULES is None there and it returns
    before reaching either regex.

    Two extension sets are spelled differently and are not interchangeable:
    LBL_EXT holds extensions with their leading dot and VIEWABLE_EXTS holds them
    without, which is why basename_is_label puts a dot back on and
    basename_is_viewable does not.
    """

    ############################################################################
    # How to split and sort filenames
    ############################################################################

    def split_basename(self, basename=''):
        """Split a basename into the parts the sort order is built from.

        The parts are an anchor, a suffix and an extension. The anchor is what groups a
        file with its relatives -- a data file, its label and its previews share one.
        The split rules are what produce it, and the rule that catches everything else
        splits at the **last** period; a bundle set name splits before its version
        suffix instead.

        A rule module can override the split for its own data set, and which of the two
        mechanisms wins depends on the kind of name. A bundle set name is split by the
        regular expression alone, and the split rules are never consulted for it. A
        bundle name consults the split rules first, and their answer is returned wherever
        it differs from the name given; otherwise the regular expression's groups are.
        Every other name is split by the rules alone.

        **The result is not always a tuple.** A class with no split rules at all, which
        is a bare PdsFile, returns the basename it was given, unchanged; and a split rule
        that rewrites a name returns whatever that rule produced.

        Parameters:
            basename (str): the basename to split. An empty string splits this object's
                own basename.

        Returns:
            tuple: the anchor, the suffix and the extension, for a name the default
            split handles.
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
        """Whether a basename is a label file.

        A label is decided by extension alone: the part after the last period, with a
        period put back in front of it, has to be one of the class's label extensions,
        matched without regard to case. A name of four characters or fewer is not a
        label whatever its extension, so a file called ``.LBL`` is not one.

        A name with no period at all is tested as though the whole name were the
        extension, which no label extension matches.

        A rule module can override this where a data set identifies labels some other
        way.

        Parameters:
            basename (str): the basename to test.

        Returns:
            bool: True if the basename is a label.
        """

        cls = type(self)
        _, _, lbl_ext = basename.rpartition('.')
        return (len(basename) > 4) and (f'.{lbl_ext}'.lower() in cls.LBL_EXT)

    def basename_is_viewable(self, basename=None):
        """Whether a basename is a file a browser can display.

        Decided by extension: the part after the last period, without a leading period,
        has to be one of the class's viewable extensions, matched without regard to case.
        A name with no period at all is not viewable.

        A rule module can override this where a data set has viewable files with other
        extensions.

        Parameters:
            basename (str): the basename to test. None tests this object's own basename.

        Returns:
            bool: True if the basename is viewable.
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
        """Return the basenames in the order this directory should show them.

        The order is not alphabetical. Each name is turned into a sort key from its
        parts rather than from its text, so a file sorts next to the files that share
        its anchor, and a bundle set with a version suffix sorts by **decreasing**
        version, which puts the newest first.

        Four options reorder groups on top of that, and each one takes the class's
        default when it is left as None. A label can be made to follow the file it
        describes rather than to sort by its own name. Directories can be pulled to the
        front or pushed to the back; asking for both puts them at the front. And the
        directory's own info file can be pulled to the very front, either always or only
        once the directory has grown past a threshold, which is what keeps a short
        listing from being reordered for no reason.

        Sorting by directory-or-file reads the filesystem once per name. Pulling the
        info file to the front reads it too, through the ``info_basename`` lazy property,
        but that property is cached, so it costs one read for the whole sort rather than
        one per name.

        Parameters:
            basenames (list): the basenames to sort. It is not modified.
            labels_after (bool): whether a label sorts after the file it describes. None
                takes the class's default.
            dirs_first (bool): whether directories sort before files. None takes the
                class's default.
            dirs_last (bool): whether directories sort after files. None takes the
                class's default. Ignored where directories are already sorting first.
            info_first: whether the directory's info file sorts before everything.
                None takes the class's default. Zero or False never, one or True always,
                and a larger number only once the list is at least that long.

        Returns:
            list: a new list of the basenames, sorted.
        """

        cls = type(self)

        def modified_sort_key(basename):
            """Return the tuple one basename sorts on.

            The tuple begins with the parts of the name -- for a bundle set, its stem and
            the negated version rank, so that newer sorts first; for anything else, the
            anchor, a zero, the suffix and the extension. The options then wrap it: the
            label test is inserted before the extension, and the directory and info tests
            are put in front of the whole thing.

            Parameters:
                basename (str): the name to build a key for.

            Returns:
                tuple: the sort key.
            """

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
                parts[3:] = [self.basename_is_label(basename)] + parts[3:]

            if dirs_first or dirs_last:
                isdir = cls.os_path_isdir(_clean_join(self.abspath,
                                                          basename))
                if dirs_first:
                    # If this is a directory, put False in front of the sort key
                    # Otherwise, put True in front
                    parts = [not isdir] + parts
                else:
                    # If this is a directory, put True in front of the sort key
                    # Otherwise, put False in front
                    parts = [isdir] + parts

            if apply_info_first:
                # If this is an info file, put False in front of the sort key
                # Otherwise, put True in front
                parts = [self.info_basename != basename] + parts

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
        """Return sibling basenames sorted, with this object's own name first.

        The names are sorted the usual way first, in the parent directory's order rather
        than in this file's, and then this file's own name is moved to the front and the
        names sharing its anchor -- everything up to its first period -- are moved
        immediately after it. Names with any other anchor keep the order the sort gave
        them. This is the order a viewer shows a selected file, its label and its
        targets in.

        This file's own name is included whether or not it was in the list.
        **The list passed in is appended to** when it was not, so a caller's list can
        come back one item longer than it went in; the returned list is a different one.

        Parameters:
            basenames (list): the basenames to sort. This object's own basename is
                appended to it where the list does not already hold it.
            labels_after (bool): whether a label sorts after the file it describes. None
                takes the class's default.
            dirs_first (bool): whether directories sort before files. None takes the
                class's default.
            dirs_last (bool): whether directories sort after files. None takes the
                class's default. Ignored where directories are already sorting first.
            info_first: whether the directory's info file sorts before everything.
                None takes the class's default. Zero or False never, one or True always,
                and a larger number only once the list is at least that long.

        Returns:
            list: a new list of the basenames, sorted, with this object's first.
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
        """Return sibling PdsFile objects sorted, with this object first.

        The same order as ``sort_sibnames()``, applied to objects. The siblings are
        keyed by basename first, so two objects with the same basename collapse to the
        one given last, and this object always displaces any sibling that shares its
        name. This object is included whether or not it was in the list.

        Parameters:
            siblings (list): the sibling PdsFile objects, iterated once.
            labels_after (bool): whether a label sorts after the file it describes. None
                takes the class's default.
            dirs_first (bool): whether directories sort before files. None takes the
                class's default.
            dirs_last (bool): whether directories sort after files. None takes the
                class's default. Ignored where directories are already sorting first.
            info_first: whether the directory's info file sorts before everything.
                None takes the class's default. Zero or False never, one or True always,
                and a larger number only once the list is at least that long.

        Returns:
            list: the objects, sorted, with this one first.
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
        """Return logical paths sorted level by level down the directory tree.

        Sorting paths as strings would put them in an order no directory would show. So
        the paths are taken apart into a tree, each directory's children are sorted the
        way that directory would sort them, and the tree is then walked in order. Paths
        that share a top-level name come out together, and the top-level names themselves
        are sorted alphabetically.

        Paths of differing depth are handled. **No path may be a directory of another
        path in the list**: such a path is treated as a directory, so it is not emitted
        in place; it is caught at the end as an overlooked item, appended alphabetically
        after everything else, and logged as a warning. The same end check drops anything
        the walk produced that was not asked for, also with a warning. Both warnings are
        skipped where the class has no logger.

        Parameters:
            logical_paths (list): the logical paths to sort. It is iterated twice and is
                not modified.

        Returns:
            list: a new list of the same paths, sorted.

        Raises:
            KeyError: from the item read ``__getitem__()`` on the table of child names,
                for a path with no slash in it. Such a path becomes a top-level name but
                gets no entry in that table, and the walk subscripts one for every
                top-level name.
            ValueError: raised by ``from_logical_path()`` if a path's first component is
                not one of the class's categories, or if no holdings directory can be
                found at all.
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
            """Append one directory's paths to the result, in its own sorted child order.

            A child that is itself a directory of the tree being built is descended into
            at the point where its name falls in that order, so a deeper path can be
            emitted before a shallower one; a child that is not is a leaf and is
            appended.

            Parameters:
                path (str): the logical path of the directory to walk.
            """

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
        """Return this directory's own contents, sorted.

        The two options this does not take, for pushing directories to the back and for
        pulling an info file to the front, fall back to the class's defaults.

        Parameters:
            labels_after (bool): whether a label sorts after the file it describes. None
                takes the class's default.
            dirs_first (bool): whether directories sort before files. None takes the
                class's default.

        Returns:
            list: the child basenames, sorted.
        """

        return self.sort_basenames(self.childnames, labels_after, dirs_first)

    def viewable_childnames(self):
        """Return the children of this directory a browser can display.

        The order is the one the child list already carries. For a directory that is the
        class's sort with all four grouping options off, rather than the order
        ``sort_childnames()`` would give; for an index table, whose child list is the
        rows, it is the class's sort with its own defaults, which is the order
        ``sort_childnames()`` gives.

        Returns:
            list: the viewable child basenames.
        """

        return [b for b in self.childnames if self.basename_is_viewable(b)]

    def childnames_by_anchor(self, anchor):
        """Return the children of this directory that share an anchor.

        The anchor is the first part of the split of a basename, so this collects a data
        file with its label and its other relatives. The comparison is exact, including
        case.

        Parameters:
            anchor (str): the anchor to match.

        Returns:
            list: the matching child basenames, in the child list's order.
        """

        matches = []
        for basename in self.childnames:
            parts = self.split_basename(basename)
            if parts[0] == anchor:
                matches.append(basename)

        return matches

    def viewable_childnames_by_anchor(self, anchor):
        """Return the children sharing an anchor that a browser can display.

        The anchor match and the viewable test, applied in that order.

        Parameters:
            anchor (str): the anchor to match.

        Returns:
            list: the matching viewable child basenames, in the child list's order.
        """

        matches = self.childnames_by_anchor(anchor)
        return [m for m in matches if self.basename_is_viewable(m)]

    ############################################################################
    # Transformations
    ############################################################################

    #### ... for pdsfiles

    @staticmethod
    def abspaths_for_pdsfiles(pdsfiles, must_exist=False):
        """Return the absolute paths of a list of PdsFile objects.

        An object with no absolute path -- a merged directory, which stands for several
        real ones -- is dropped either way, so the result can be shorter than the input
        even without the existence test.

        Parameters:
            pdsfiles (list): the objects, iterated once.
            must_exist (bool): whether to drop the objects whose files are not there.

        Returns:
            list: the absolute paths.
        """

        if must_exist:
            return [p.abspath for p in pdsfiles if p.abspath is not None
                                                and p.exists]
        else:
            return [p.abspath for p in pdsfiles if p.abspath is not None]

    @staticmethod
    def logicals_for_pdsfiles(pdsfiles, must_exist=False):
        """Return the logical paths of a list of PdsFile objects.

        Every object has a logical path, including a merged directory, so nothing is
        dropped unless the existence test drops it.

        Parameters:
            pdsfiles (list): the objects, iterated once.
            must_exist (bool): whether to drop the objects whose files are not there.

        Returns:
            list: the logical paths.
        """

        if must_exist:
            return [p.logical_path for p in pdsfiles if p.exists]
        else:
            return [p.logical_path for p in pdsfiles]

    @staticmethod
    def basenames_for_pdsfiles(pdsfiles, must_exist=False):
        """Return the basenames of a list of PdsFile objects.

        Basenames are not unique across directories, so a list drawn from more than one
        directory can hold the same name twice; nothing is deduplicated.

        Parameters:
            pdsfiles (list): the objects, iterated once.
            must_exist (bool): whether to drop the objects whose files are not there.

        Returns:
            list: the basenames.
        """

        if must_exist:
            return [p.basename for p in pdsfiles if p.exists]
        else:
            return [p.basename for p in pdsfiles]

    #### ... for abspaths

    @classmethod
    def pdsfiles_for_abspaths(cls, abspaths, must_exist=False):
        """Return PdsFile objects for a list of absolute paths.

        Every path yields an object, whether or not the file is there; the existence
        test is applied to the objects afterwards, so it costs one existence check each.

        Parameters:
            abspaths (list): the absolute paths, iterated once.
            must_exist (bool): whether to drop the paths whose files are not there.

        Returns:
            list: the PdsFile objects.
        """

        pdsfiles = [cls.from_abspath(p) for p in abspaths]
        if must_exist:
            pdsfiles = [pdsf for pdsf in pdsfiles if pdsf.exists]

        return pdsfiles

    @classmethod
    def logicals_for_abspaths(cls, abspaths, must_exist=False):
        """Return the logical paths of a list of absolute paths.

        No PdsFile is built: each path is cut at the holdings directory directly, which
        is why this is the cheap direction.

        Parameters:
            abspaths (list): the absolute paths, iterated once.
            must_exist (bool): whether to drop the paths whose files are not there. The
                test is applied before the conversion.

        Returns:
            list: the logical paths.

        Raises:
            ValueError: raised by ``logical_path_from_abspath()`` if a path does not lie
                under a holdings directory. With the existence test on, a path that does
                not exist is dropped before it can raise.
        """

        if must_exist:
            abspaths = [p for p in abspaths if cls.os_path_exists(p)]

        return [logical_path_from_abspath(p, cls) for p in abspaths]

    @classmethod
    def basenames_for_abspaths(cls, abspaths, must_exist=False):
        """Return the basenames of a list of absolute paths.

        The names are taken from the paths as text, so nothing has to exist unless the
        existence test is asked for.

        Parameters:
            abspaths (list): the absolute paths, iterated once.
            must_exist (bool): whether to drop the paths whose files are not there.

        Returns:
            list: the basenames.
        """

        if must_exist:
            abspaths = [p for p in abspaths if cls.os_path_exists(p)]

        return [os.path.basename(p) for p in abspaths]

    #### ... for logicals

    @classmethod
    def pdsfiles_for_logicals(cls, logical_paths, must_exist=False):
        """Return PdsFile objects for a list of logical paths.

        Resolving a logical path means deciding which holdings directory it belongs to,
        so this is the expensive direction. Every path yields an object, and the
        existence test is applied to the objects afterwards.

        Parameters:
            logical_paths (list): the logical paths, iterated once.
            must_exist (bool): whether to drop the paths whose files are not there.

        Returns:
            list: the PdsFile objects.
        """

        pdsfiles = [cls.from_logical_path(p) for p in logical_paths]
        if must_exist:
            pdsfiles = [pdsf for pdsf in pdsfiles if pdsf.exists]

        return pdsfiles

    @classmethod
    def abspaths_for_logicals(cls, logical_paths, must_exist=False):
        """Return the absolute paths of a list of logical paths.

        No PdsFile is built, but each path still has to be resolved against the holdings
        directories this machine hosts.

        Parameters:
            logical_paths (list): the logical paths, iterated once.
            must_exist (bool): whether to drop the paths whose files are not there. The
                test is applied after the conversion.

        Returns:
            list: the absolute paths.

        Raises:
            ValueError: raised by ``abspath_for_logical_path()`` if a path does not start
                with a category name, or if no holdings directory can be found at all.
                It is raised before the existence test, so it is raised either way.
        """

        abspaths = [abspath_for_logical_path(p, cls) for p in logical_paths]
        if must_exist:
            abspaths = [p for p in abspaths if cls.os_path_exists(p)]

        return abspaths

    @classmethod
    def basenames_for_logicals(cls, logical_paths, must_exist=False):
        """Return the basenames of a list of logical paths.

        Without the existence test the names are taken from the paths as text. With it,
        a PdsFile is built for each path first, which is what makes the test possible and
        what makes this the expensive branch.

        Parameters:
            logical_paths (list): the logical paths, iterated once.
            must_exist (bool): whether to drop the paths whose files are not there.

        Returns:
            list: the basenames.
        """

        if must_exist:
            pdsfiles = cls.pdsfiles_for_logicals(logical_paths,
                                                     must_exist=must_exist)
            return cls.basenames_for_pdsfiles(pdsfiles)
        else:
            return [os.path.basename(p) for p in logical_paths]

    #### ... for basenames

    def pdsfiles_for_basenames(self, basenames, must_exist=False):
        """Return PdsFile objects for basenames in this directory.

        Each name is resolved as a child of this object, so the answer depends on which
        directory this is.

        Parameters:
            basenames (list): the basenames, iterated once.
            must_exist (bool): whether to drop the names whose files are not there.

        Returns:
            list: the PdsFile objects.
        """

        pdsfiles = [self.child(b) for b in basenames]

        if must_exist:
            pdsfiles = [p for p in pdsfiles if p.exists]

        return pdsfiles

    def abspaths_for_basenames(self, basenames, must_exist=False):
        """Return the absolute paths of basenames in this directory.

        Where this directory has an absolute path of its own and nothing has to be
        checked, the paths are joined directly and no PdsFile is built. Otherwise a
        child object is built for each name, which is also what serves a merged
        directory, whose children can be on different disks. A child that still has no
        absolute path contributes None.

        Parameters:
            basenames (list): the basenames, iterated once.
            must_exist (bool): whether to drop the names whose files are not there.

        Returns:
            list: the absolute paths.
        """

        # shortcut
        if self.abspath and not must_exist:
            return [_clean_join(self.abspath, b) for b in basenames]

        pdsfiles = self.pdsfiles_for_basenames(basenames, must_exist=must_exist)
        return [pdsf.abspath for pdsf in pdsfiles]

    def logicals_for_basenames(self, basenames, must_exist=False):
        """Return the logical paths of basenames in this directory.

        Where nothing has to be checked the paths are joined directly, which works for a
        merged directory too, since a logical path does not name a disk. Otherwise a
        child object is built for each name.

        Parameters:
            basenames (list): the basenames, iterated once.
            must_exist (bool): whether to drop the names whose files are not there.

        Returns:
            list: the logical paths.
        """

        # shortcut
        if not must_exist:
            return [_clean_join(self.logical_path, b) for b in basenames]

        pdsfiles = self.pdsfiles_for_basenames(basenames, must_exist=must_exist)
        return [pdsf.logical_path for pdsf in pdsfiles]
