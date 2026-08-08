##########################################################################################
# pdsfile/_local_fs.py
##########################################################################################

"""The four filesystem questions PdsFile asks, answered from the tree or from shelves.

Every part of this package that needs to know whether a file exists, whether a path is a
directory, what a directory contains, or which paths match a wildcard goes through this
module rather than through ``os`` and ``glob``. The indirection buys one thing: under the
``SHELVES_ONLY`` setting the same four questions are answered out of the info shelf
files, so the package can serve a holdings tree that is described but not present.

``_LocalFsMixin`` implements them as ``os_path_exists()``, ``os_path_isdir()``,
``os_listdir()`` and ``glob_glob()``, plus ``_non_checksum_abspath()``, the mapping from
a checksum file back to what it covers, which the shelf-backed answers fall back on.

Two things a caller should know. Existence answers are memoized in a cache of
``PATH_EXISTS_CACHE_SIZE`` entries that is never invalidated, so a file created or
deleted after the first question about it keeps its old answer until its entry is
evicted; a single preload asks tens of times that many distinct questions, so the cache
runs full and evicts throughout. And the shelf-backed answers match keys exactly, so they
are case-sensitive whatever the filesystem is; the case-repair machinery applies only to
the answers that come from the filesystem.

``PATH_EXISTS_CACHE_SIZE`` is how many existence answers are remembered.
"""

import bisect
import fnmatch
import functools
import os

from ._path_utils import _clean_glob, _needs_glob

# Configuration
PATH_EXISTS_CACHE_SIZE = 200

##########################################################################################
# Local filesystem mixin
##########################################################################################
class _LocalFsMixin:
    """Local implementations of the basic filesystem operations PdsFile needs.

    A mixin of PdsFile; it holds methods only and defines no state of its own.

    Every attribute these methods read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, list, dict, os, os.path, glob, fnmatch
    and bisect functions are not in scope::

      class attributes read       EXTRA_README_BASENAMES, FS_IS_CASE_INSENSITIVE,
                                  IDX_EXT, PDS_HOLDINGS, SHELVES_ONLY, VOLTYPES
      lazy properties read        exists
      instance attributes read    none
      instance attributes WRITTEN none
      other methods called        from_abspath

    All of those but one are defined on PdsFile. IDX_EXT is defined only on
    Pds3File and Pds4File, so os_path_exists raises AttributeError on a bare
    PdsFile for every path except the one its opening test answers first: a path
    inside the info shelf tree, which that test sends straight to the filesystem
    before the index-row loop reads IDX_EXT.

    Three more come from sibling mixins, and they are what makes the shelf-backed
    answers possible: shelf_path_and_key_for_abspath and _get_shelf from
    _ShelfMixin, and child_of_index from _IndexRowsMixin, which is how a path
    naming one row of an index table is tested for existence. Every one of these
    is an attribute lookup on cls at run time, not an import, which is what lets
    the layers live in different modules.
    """

    @classmethod
    def _non_checksum_abspath(cls, abspath):
        """Return the path a checksum file covers, or None if it is not a checksum file.

        A path counts as a checksum file only if it holds the holdings directory
        followed immediately by ``checksums-``. Every ``/checksums-`` in the path is then
        removed, not just that one, and the basename's ``_<voltype>_md5.txt`` ending is
        dropped.

        **Only an ending that names one of the class's volume types is dropped.** A
        checksum file whose basename carries no volume type keeps its ``_md5.txt``, so
        the path returned names nothing: ``.../checksums-volumes/SET/BUNDLE_md5.txt``
        comes back as ``.../volumes/SET/BUNDLE_md5.txt`` rather than as the bundle
        directory. The ``checksums-volumes`` and ``checksums-archives-volumes``
        categories are the ones whose files are named that way; a checksum file in any
        other checksums category carries its volume type and does reduce to the path it
        covers.

        Parameters:
            abspath (str): the absolute path to map back.

        Returns:
            str: the covered path, or None if the argument is not a checksum path.
        """

        # Checksum files need special handling
        if f'/{cls.PDS_HOLDINGS}/checksums-' in abspath:
            testpath = abspath.replace('/checksums-', '/')

            for voltype in cls.VOLTYPES:
                testpath = testpath.replace('_' + voltype + '_md5.txt', '')

            return testpath

        else:
            return None

    @classmethod
    @functools.lru_cache(maxsize=PATH_EXISTS_CACHE_SIZE)
    def os_path_exists(cls, abspath, force_case_sensitive=False):
        """Whether a path names something that exists.

        This stands in for ``os.path.exists()`` and can answer without touching the
        filesystem. Four paths through it, in order:

          * a path inside the info shelf tree is tested directly on the filesystem,
            because a shelf cannot describe itself;
          * a path naming one row of an index table -- recognized by an index extension
            followed by a slash -- exists if the table exists and the table has that row;
          * under SHELVES_ONLY, and only for a path outside the ``documents`` tree, for
            which no shelves are written, the info shelf covering the path is consulted:
            a path with a key exists if the shelf holds that key, and a path that is
            itself a covered directory exists if its shelf file does. If that fails,
            three fallbacks are tried in turn, looking for a directory in the shelf tree,
            a shelf file for it, and, for a checksum path, the thing it covers;
          * anything still unanswered is tested on the filesystem.

        **The answer is memoized and never invalidated**, up to
        ``PATH_EXISTS_CACHE_SIZE`` distinct calls, so a file created or removed after the
        first question about it keeps its old answer for the life of the process. The
        flag is part of the key, and so is the class, so the same path asked about two
        ways is remembered twice.

        The case rules are not the same on all four paths. On the shelf path a key is
        matched exactly, so the answer is case-sensitive whatever the filesystem is, and
        the flag has no effect there. On the filesystem path the answer is the
        filesystem's own, which on a Mac is usually case-insensitive, and the flag then
        forces the basename to be compared against the real directory listing.

        Parameters:
            abspath (str): the absolute path to test.
            force_case_sensitive (bool): whether to insist the basename match in case.
                It applies only where the filesystem answers and the class marks the
                filesystem case-insensitive.

        Returns:
            bool: True if the path names something that exists.
        """

        if f'{cls.PDS_HOLDINGS}/_infoshelf' in abspath:
            return os.path.exists(abspath)

        # Handle index rows
        for ext in cls.IDX_EXT:
            if f'{ext}/' in abspath:
                parts = abspath.partition(f'{ext}/')
                if not cls.os_path_exists(parts[0] + ext):
                    return False
                pdsf = cls.from_abspath(parts[0] + ext)
                return (pdsf.exists and
                        pdsf.child_of_index(parts[2], flag='').exists)

        # If it's for documentation, we don't create shelf files, we will just use the
        # os.path.exists
        if cls.SHELVES_ONLY and f'{cls.PDS_HOLDINGS}/documents' not in abspath:
            try:
                (shelf_abspath,
                 key) = cls.shelf_path_and_key_for_abspath(abspath, 'info')

                if key:
                    shelf = cls._get_shelf(shelf_abspath,
                                               log_missing_file=False)
                    return (key in shelf)
                # Every shelf file has an entry with an empty key, so
                # this avoids an unnecessary open of the file.
                return bool(cls.os_path_exists(shelf_abspath))
            except (ValueError, IndexError, OSError):
                pass

            # Maybe it's associated with something else in the infoshelf tree
            if f'/{cls.PDS_HOLDINGS}/' in abspath:

                # Maybe there's an associated directory in the infoshelf tree
                shelf_abspath = abspath.replace(f'/{cls.PDS_HOLDINGS}/',
                                                f'/{cls.PDS_HOLDINGS}/_infoshelf-')
                if cls.os_path_exists(shelf_abspath):
                    return True

                # Maybe there's an associated shelf file in the infoshelf tree
                if cls.os_path_exists(shelf_abspath + '_info.pickle'):
                    return True

                # Checksum files need special handling, before doing special handling,
                testpath = cls._non_checksum_abspath(abspath)
                if testpath and cls.os_path_exists(testpath):
                    return True

        if force_case_sensitive and cls.FS_IS_CASE_INSENSITIVE:
            test = os.path.exists(abspath)
            if not test:
                return False

            (parent,basename) = os.path.split(abspath)
            childnames = os.listdir(parent)
            return (basename in childnames)

        return os.path.exists(abspath)

    @classmethod
    def os_path_isdir(cls, abspath):
        """Whether a path names a directory.

        This stands in for ``os.path.isdir()``. Under SHELVES_ONLY the info shelf
        answers, for every path including one in the ``documents`` tree, which the
        existence test excludes: a shelf records an empty checksum for a directory and a
        real one for a file, so the checksum column is the test, and a path that is
        itself a covered directory is a directory if its shelf file exists.

        **A path whose shelf does not hold its key raises KeyError**, where the existence
        test answers False, because the handler around the shelf read catches ValueError,
        IndexError and OSError only. The same three fallbacks as the existence test
        follow when one of those three is raised instead, and a checksum path is decided
        by its extension, ``.txt`` being a file and anything else a directory.

        This answer is not memoized. Of the three fallbacks, the first two consult the
        filesystem directly and the third, the checksum one, goes back through the
        memoized existence test, as does the covered-directory case above them.

        Parameters:
            abspath (str): the absolute path to test.

        Returns:
            bool: True if the path names a directory.

        Raises:
            KeyError: from the item read ``__getitem__()`` on the shelf, for a path
                under SHELVES_ONLY whose covering shelf does not hold its key.
        """

        if cls.SHELVES_ONLY:
            try:
                (shelf_abspath,
                 key) = cls.shelf_path_and_key_for_abspath(abspath, 'info')

                if key:
                    shelf = cls._get_shelf(shelf_abspath,
                                               log_missing_file=False)
                    (_, _, _, checksum, _) = shelf[key]
                    return (checksum == '')
                # Every shelf file has an entry with an empty key, so
                # this avoids an unnecessary open of the file.
                return bool(cls.os_path_exists(shelf_abspath))
            except (ValueError, IndexError, OSError):
                pass

            # Maybe it's associated with something else in the infoshelf tree
            if f'/{cls.PDS_HOLDINGS}/' in abspath:

                # Maybe there's an associated directory in the infoshelf tree
                shelf_abspath = abspath.replace(f'/{cls.PDS_HOLDINGS}/',
                                                f'/{cls.PDS_HOLDINGS}/_infoshelf-')
                if os.path.exists(shelf_abspath):
                    return True

                # Maybe there's an associated shelf file in the infoshelf tree
                if os.path.exists(shelf_abspath + '_info.pickle'):
                    return True

                # Checksum files need special handling
                testpath = cls._non_checksum_abspath(abspath)
                if testpath and cls.os_path_exists(testpath):
                    # If the testpath exists, then whether it is a directory or
                    # not depends on the extension
                    return (not abspath.lower().endswith('.txt'))

        return os.path.isdir(abspath)

    @classmethod
    def os_listdir(cls, abspath):
        """Return the basenames a directory contains.

        This stands in for ``os.listdir()``. The filesystem answer drops ``.DS_Store``
        and the ``._`` files a Mac leaves behind; the shelf-backed answers do not,
        because a shelf never records them.

        Under SHELVES_ONLY the info shelf covering the path answers first: its keys that
        begin with this directory's key and hold no further slash are its children. When
        no shelf covers the path, the parallel trees are derived instead, each from the
        listing of the tree it parallels:

          * a checksums-archives directory lists the archive directory and appends
            ``_md5.txt``, or ``_<voltype>_md5.txt`` outside volumes;
          * a checksums directory does the same against the tree it checksums, except
            that it reserves the bare ``_md5.txt`` for bundles as well as for volumes,
            and except at the category level, where it passes the listing through
            unchanged;
          * an archives directory lists the bundle tree and appends ``.tar.gz``, or
            ``_<voltype>.tar.gz`` outside volumes;
          * any other holdings directory lists the matching directory in the info shelf
            tree, reduces the ``_info.pickle`` and ``_info.py`` pair for each bundle to
            the bundle name, and puts any AAREADME the real filesystem has in front. At
            the category level that listing is returned unchanged.

        A file rather than a directory yields an empty list on the three parallel-tree
        branches, recognized by its extension. If the shelf tree has no matching
        directory at all, the real filesystem answers, which is what serves the
        documents tree, for which no shelves are written.

        Parameters:
            abspath (str): the absolute path of the directory, with any trailing slash
                ignored.

        Returns:
            list: the basenames, in the order the underlying listing gave them.

        Raises:
            ValueError: for a checksums-archives path naming no recognized volume type.
            OSError: raised by ``listdir()`` when the filesystem is the one answering
                and the directory is not there.
        """

        # Make sure there is no trailing slash
        abspath = abspath.rstrip('/')

        if cls.SHELVES_ONLY:
            try:
                (shelf_abspath,
                 key) = cls.shelf_path_and_key_for_abspath(abspath, 'info')

                shelf = cls._get_shelf(shelf_abspath,
                                           log_missing_file=False)
            except (ValueError, IndexError, OSError):
                pass
            else:
                # Look for paths that begin the same and do not have an
                # additional slash
                prefix = key + '/' if key else ''
                lprefix = len(prefix)
                basenames = []
                for key in shelf:
                    if not key.startswith(prefix):
                        continue
                    if key == '':
                        continue
                    basename = key[lprefix:]
                    if '/' not in basename:
                        basenames.append(basename)

                return basenames

            # Deal with checksums-archives directories
            if f'/{cls.PDS_HOLDINGS}/checksums-archives-' in abspath:
                if abspath.endswith('.txt'):
                    return []

                testpath = abspath.replace('/checksums-','/')
                results = cls.os_listdir(testpath)

                for voltype in cls.VOLTYPES:
                    if '-' + voltype in abspath:
                        if voltype == 'volumes':
                            return [r + '_md5.txt' for r in results]
                        else:
                            return [r + '_' + voltype + '_md5.txt' for r in results]

                raise ValueError('Invalid abspath for os_listdir: ' + abspath)

            # Deal with checksums directories
            if f'/{cls.PDS_HOLDINGS}/checksums-' in abspath:
                if abspath.endswith('_md5.txt'):
                    return []

                testpath = abspath.replace('/checksums-','/')
                results = cls.os_listdir(testpath)

                after = abspath.rpartition(f'/{cls.PDS_HOLDINGS}/checksums-')[-1]
                parts = after.split('/')
                if len(parts) == 1:         # category-level call
                    return results

                voltype = parts[0]
                if voltype == 'volumes' or voltype == 'bundles':
                    return [r + '_md5.txt' for r in results]
                else:
                    return [r + '_' + voltype + '_md5.txt' for r in results]

            # Deal with archive directories
            if f'/{cls.PDS_HOLDINGS}/archives-' in abspath:
                if abspath.endswith('.tar.gz'):
                    return []

                testpath = abspath.replace('/archives-','/')
                results = cls.os_listdir(testpath)

                after = abspath.rpartition(f'/{cls.PDS_HOLDINGS}/archives-')[-1]
                parts = after.split('/')
                if len(parts) == 1:         # category-level call
                    return results

                voltype = parts[0]
                if voltype == 'volumes':
                    return [r + '.tar.gz' for r in results]
                else:
                    return [r + '_' + voltype + '.tar.gz' for r in results]

            # Deal with other holdings directories, e.g., holdings/volumes
            if f'/{cls.PDS_HOLDINGS}/' in abspath:

                # Maybe there's an associated directory in the infoshelf tree
                shelf_abspath = abspath.replace(f'/{cls.PDS_HOLDINGS}/',
                                                f'/{cls.PDS_HOLDINGS}/_infoshelf-')
                try:
                    results = os.listdir(shelf_abspath)
                except FileNotFoundError:
                    # If the shelf file is missing, try the actual file system
                    # For documentation, we have all files available but not the shelf
                    # files, therefore we will check the actual file system for documents.
                    childnames = os.listdir(abspath)
                    return [c for c in childnames
                            if c != '.DS_Store' and not c.startswith('._')]

                if not results:
                    return []

                after = abspath.rpartition(f'/{cls.PDS_HOLDINGS}/')[-1]
                parts = after.split('/')
                if len(parts) == 1:         # category-level call
                    return results

                # Isolate unique bundle names from shelf files
                # This prevent duplicated results for _info.py and _info.pickle
                filtered = []
                for result in results:
                    parts = result.split('_info.')
                    if len(parts) == 1:
                        continue

                    bundlename = parts[0]
                    if bundlename not in filtered:
                        filtered.append(bundlename)

                # Check the actual file system for a bundleset-level AAREADME
                aareadmes = []
                for basename in cls.EXTRA_README_BASENAMES:
                    if os.path.exists(abspath + '/' + basename):
                        aareadmes.append(basename)

                return aareadmes + filtered

        childnames = os.listdir(abspath)
        return [c for c in childnames
                if c != '.DS_Store' and not c.startswith('._')]

    @classmethod
    def glob_glob(cls, abspath, force_case_sensitive=False):
        """Return the existing absolute paths a pattern matches.

        This stands in for ``glob.glob()``. A pattern with no wildcard in it is not
        globbed at all: it is tested for existence, which is what makes the index-row
        notation ``index.tab/whatever`` work here, since a real glob would not match it.

        Without SHELVES_ONLY the search is the memoized filesystem glob. With it, the
        info shelves are searched instead: the shelf files covering the pattern are
        found, and each one's keys are matched against the interior part of the pattern.
        The keys are sorted, so the search starts at the first key that could match the
        pattern's fixed prefix and stops at the first that cannot. A match must also
        have as many slashes as the pattern, because ``fnmatch`` matches text and would
        otherwise let ``f*r`` match ``foo/bar``. If no shelf file covers the pattern, the
        filesystem glob answers after all.

        **The shelf-backed search is case-sensitive**, whatever the filesystem is and
        whatever the flag says: the prefix scan folds case only to decide where to stop,
        and the match itself is exact. The flag reaches the filesystem glob and the
        existence test the no-wildcard shortcut makes; nothing else consults it.

        The shelf-backed search removes any trailing slash from the paths it returns.
        The other four returns do not: the no-wildcard shortcut, either of the two that
        fall back to the filesystem glob, and the conversion of a category-level shelf
        listing all pass their paths on as they are.

        A shelf path that does not hold the info shelf directory prefix exactly once
        trips an assert, and so raises AssertionError, or nothing at all under
        python -O.

        Parameters:
            abspath (str): the absolute path, with or without wildcards.
            force_case_sensitive (bool): whether a filesystem match must agree in case.

        Returns:
            list: the matching absolute paths.

        Raises:
            OSError: raised by ``_get_shelf()`` when a shelf file the search has already
                located cannot be opened or unpickled. That call sits outside any
                handler.
        """

        # We can save a lot of trouble if there's no match pattern
        # This also enables support for index row notation "index.tab/whatever"
        if not _needs_glob(abspath):
            if cls.os_path_exists(abspath, force_case_sensitive):
                return [abspath]
            else:
                return []

        if not cls.SHELVES_ONLY:
            return _clean_glob(cls, abspath, force_case_sensitive)

        # Find the shelf file(s) if any
        abspath = abspath.rstrip('/')
        try:
            (pattern, key) = cls.shelf_path_and_key_for_abspath(abspath, 'info')
        except ValueError:
            # For a category-level holdings dir, this might still work
            if f'/{cls.PDS_HOLDINGS}/' in abspath:
                pattern = abspath.replace(f'/{cls.PDS_HOLDINGS}/',
                                          f'/{cls.PDS_HOLDINGS}/_infoshelf-')
                key = None  # Below, None indicates that we handled this error
            else:
                pattern = ''

        if not pattern:
            shelf_paths = []
        elif _needs_glob(pattern):
            shelf_paths = _clean_glob(cls, pattern)
        elif os.path.exists(pattern):
            shelf_paths = [pattern]
        else:
            shelf_paths = []

        # If there are no exact infoshelf files, revert to the file system
        if not shelf_paths:
            return _clean_glob(cls, abspath, force_case_sensitive)

        # If the check for an exact shelf file failed, just convert the list
        # of shelf/info directories back to holdings directories
        if key is None:
            return [p.replace(f'/{cls.PDS_HOLDINGS}/_infoshelf-', f'/{cls.PDS_HOLDINGS}/')
                    for p in shelf_paths]

        # Gather the matching entries in each shelf
        abspaths = []
        for shelf_path in shelf_paths:
            shelf = cls._get_shelf(shelf_path)
            parts = shelf_path.split(f'/{cls.PDS_HOLDINGS}/_infoshelf-')
            assert len(parts) == 2

            root_ = parts[0] + f'/{cls.PDS_HOLDINGS}/' + parts[1].split('_info.')[0] + '/'

            if _needs_glob(key):
                # Since shelf files are always in alphabetical order, we can
                # use a binary search to figure out where to start comparing
                # strings. This is useful because there can be a lot of
                # paths to search through, and fnmatchcase is slow.
                w1 = key.find('?')
                w2 = key.find('*')
                w3 = key.find('[')
                wildcard_index = len(key)
                if w1 != -1:
                    wildcard_index = w1
                if w2 != -1:
                    wildcard_index = min(wildcard_index, w2)
                if w3 != -1:
                    wildcard_index = min(wildcard_index, w3)
                key_prefix = key[:wildcard_index]
                interior_paths = list(shelf.keys())
                values = list(shelf.values())
                starting_pos = bisect.bisect_left(interior_paths, key_prefix)
                num_key_slashes = len(key.split('/'))
                for (interior_path, _value) in zip(
                                interior_paths[starting_pos:],
                                values[starting_pos:], strict=False):
                    # If the key prefix doesn't match the interior_path prefix,
                    # then we're done since the filenames are in alphabetical
                    # order.
                    if (key_prefix.upper() !=
                        interior_path[:wildcard_index].upper()):
                        break
                    # Because fnmatch matches strings instead of filesystems,
                    # it has the unfortunate property that match patterns can
                    # accidentally cross directory boundaries. For example, the
                    # pattern "f*r" will match "foo/bar", when it shouldn't. We
                    # handle this by also checking that the returned result
                    # contains the same number of slashes as the pattern.
                    if (fnmatch.fnmatchcase(interior_path, key) and
                        len(interior_path.split('/')) == num_key_slashes):
                        abspaths.append(root_ + interior_path)
            else:
                if key in shelf:
                    abspaths.append(root_ + key)

        # Remove trailing slashes!
        return [p.rstrip('/') for p in abspaths]
