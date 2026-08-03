##########################################################################################
# pdsfile/_local_fs.py
# Local implementations of basic filesystem operations, which consult info shelf
# files instead of the file system when SHELVES_ONLY is set
##########################################################################################

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
    The class attributes these methods read -- PDS_HOLDINGS, VOLTYPES, IDX_EXT,
    SHELVES_ONLY, FS_IS_CASE_INSENSITIVE, EXTRA_README_BASENAMES -- are defined on
    PdsFile and its subclasses.

    Under SHELVES_ONLY these methods answer from the info shelf files rather than
    the holdings tree, which is why they call into _ShelfMixin
    (shelf_path_and_key_for_abspath, _get_shelf). Those calls resolve through the
    class at run time, so both mixins have to be bases of the same class.
    """

    @classmethod
    def _non_checksum_abspath(cls, abspath):
        """Return the non-checksum path associated with this checksum file. If the given
        absolute path does not point to a checksum file, it returns None.

        Keyword arguments:
            abspath -- the absolute path of the checksum file.
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
        """Return True if the given absolute path points to a file that exists; Return
        False otherwise. This replaces os.path.exists(path) but might use infoshelf
        files rather than refer to the holdings directory.

        Note: This function is case-insensitive under SHELVES_ONLY. Otherwise,
        its behavior matches that of the file system. For Macs, this usually
        means that it is case insensitive. If force_case_sensitive=True, then
        the check of the basename will be case-sensitive regardless of the file
        system.

        Keyword arguments:
            abspath              -- the absolute path of the file.
            force_case_sensitive -- a flag to determine if the basename will be case
                                    sensitive (default False)
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
                elif cls.os_path_exists(shelf_abspath):
                    return True     # Every shelf file has an entry with an
                                    # empty key, so this avoids an unnecessary
                                    # open of the file.
                else:
                    return False
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
        """Return True if the given absolute path points to a directory; Return False
        otherwise. This replaces os.path.isdir() but might use infoshelf files rather
        than refer to the holdings directory.

        Keyword arguments:
            abspath -- the absolute path of a file or a directory.
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
                elif cls.os_path_exists(shelf_abspath):
                    return True     # Every shelf file has an entry with an
                                    # empty key, so this avoids an unnecessary
                                    # open of the file.
                else:
                    return False
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
        """Return a list of the file basenames within a directory, given its absolute
        path. This replaces os.listdir() but might use infoshelf files rather than the
        file system.

        Keyword arguments:
            abspath -- the given absolute path.
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
        """Return a list of the existing absolute paths. Works the same as glob.glob(),
        but uses shelf files instead of accessing the filesystem directly.

        Note: This function is case-insensitive under SHELVES_ONLY. Otherwise,
        its behavior matches that of the file system. For Macs, this usually
        means that it is case insensitive. If force_case_sensitive=True, then
        file paths will only match if the case is exact.

        Keyword arguments:
            abspath              -- the given absolute path
            force_case_sensitive -- a flag to determine if the filepath will be case
                                    sensitive (default False)
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
