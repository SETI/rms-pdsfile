##########################################################################################
# pdsfile/_path_utils.py
# Module-level path helpers shared by the PdsFile classes
##########################################################################################

import fnmatch
import functools
import glob
import math
import os

# Configuration
_GLOB_CACHE_SIZE = 200
FILE_BYTE_UNITS = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

##########################################################################################
# Support functions
##########################################################################################
def construct_category_list(voltypes):
    category_list = []
    for checksums in ('', 'checksums-'):
        for archives in ('', 'archives-'):
            for voltype in voltypes:
                category_list.append(checksums + archives + voltype)

    category_list.remove('checksums-documents')
    category_list.remove('archives-documents')
    category_list.remove('checksums-archives-documents')

    return category_list


def logical_path_from_abspath(abspath, cls):
    """Return the logical path derived from an absolute path.

    Keyword arguments:
        abspath -- the abosulte path of a file
        cls     -- the class calling the other methods inside the function
    """
    parts = abspath.partition('/'+cls.PDS_HOLDINGS+'/')
    if parts[1]:
        return parts[2]

    raise ValueError('Not compatible with a logical path: ', abspath)

def _clean_join(a, b):
#     joined = _clean_join(a,b).replace('\\', '/')
    if a:
        return a + '/' + b
    else:
        return b

def _clean_abspath(path):
    abspath = os.path.abspath(path)
    if os.sep == '\\':
        abspath = abspath.replace('\\', '/')
    return abspath

@functools.lru_cache(maxsize=_GLOB_CACHE_SIZE)
def _clean_glob(cls, pattern, force_case_sensitive=False):
    results = glob.glob(pattern)
    if os.sep == '\\':
        results = [x.replace('\\', '/') for x in results]

    if force_case_sensitive and cls.FS_IS_CASE_INSENSITIVE:
        filtered_results = []
        for result in results:
            result = repair_case(result, cls)
            if fnmatch.fnmatchcase(result, pattern):
                filtered_results.append(result)

        return filtered_results

    else:
        return results

def _needs_glob(pattern):
    """Return True if the given expression contains wildcards

    Keyword arguments:
        pattern -- expression pattern
    """
    return '*' in pattern or '?' in pattern or '[' in pattern

def repair_case(abspath, cls):
    """Return a file's absolute path with capitalization exactly as it appears
    in the file system. Raises IOError if the file is not found.

    Keyword arguments:
        abspath -- an absolute path of a file
        cls     -- the class calling the other methods inside the function
    """

    trailing_slash = abspath.endswith('/')  # must preserve a trailing slash!
    abspath = _clean_abspath(abspath)

    # Fields are separated by slashes
    parts = abspath.split('/')
    if parts[-1] == '':
        parts = parts[:-1]      # Remove trailing slash

    # On Unix, parts[0] is always '' so no need to check case
    # On Windows, this skips over the name of the drive

    # For each subsequent field (between slashes)...
    for k in range(1, len(parts)):

        # Convert it to lower case for matching
        part_lower = parts[k].lower()

        # Construct the name of the parent directory and list its contents.
        # This will raise an IOError if the file does not exist or is not a
        # directory.
        if k == 1:
            basenames = os.listdir('/')
        else:
            basenames = cls.os_listdir('/'.join(parts[:k]))

        # Find the first name that matches when ignoring case
        found = False
        for name in basenames:
            if name.lower() == part_lower:

                # Replace the field with the properly capitalized name
                parts[k] = name
                found = True
                break

    # Reconstruct the full path
    if trailing_slash: parts.append('')
    abspath = '/'.join(parts)

    # Raise an IOError if last field was not found
    if not found:
        with open(abspath, 'rb') as f:
            pass

    return abspath

def formatted_file_size(size):
    order = int(math.log10(size) // 3) if size else 0
    return f'{size / 1000.**order:.3g} {FILE_BYTE_UNITS[order]}'

def abspath_for_logical_path(path, cls):
    """Return the absolute path derived from the given logical path.

    The logical path starts at the category, below the holdings/ directory. To
    get the absolute path, we need to figure out where the holdings directory is
    located. Note that there can be multiple drives hosting multiple holdings
    directories.

    Keyword arguments:
        path -- the path of a file
        cls  -- the class calling the other methods inside the function
    """

    # Check for a valid logical path
    parts = path.split('/')
    if parts[0] not in cls.CATEGORIES:
        raise ValueError('Not a logical path: ' + path)

    # Use the list of preloaded holdings directories if it is not empty
    if cls.LOCAL_PRELOADED:
        holdings_list = cls.LOCAL_PRELOADED

    elif cls.LOCAL_HOLDINGS_DIRS:
        holdings_list = cls.LOCAL_HOLDINGS_DIRS

    elif cls._HOLDINGS_ENV in os.environ:
        holdings_list = [os.environ[cls._HOLDINGS_ENV]]
        cls.LOCAL_HOLDINGS_DIRS = holdings_list

    # Without a preload or an environment variable, check the
    # /Library/WebSever/Documents directory for a symlink. This only works for
    # MacOS with the website installed, but that's OK.
    else:
        holdings_dirs = glob.glob('/Library/WebServer/Documents/holdings*')
        holdings_dirs.sort()
        holdings_list = [os.path.realpath(h) for h in holdings_dirs]
        cls.LOCAL_HOLDINGS_DIRS = holdings_list

    # With exactly one holdings/ directory, the answer is easy
    if len(holdings_list) == 1:
        return _clean_join(holdings_list[0], path)

    # Otherwise search among the available holdings directories in order
    for root in holdings_list:
        abspath = _clean_join(root, path)
        matches = cls.glob_glob(abspath)
        if matches: return matches[0]

    # File doesn't exist. Just pick one.
    if holdings_list:
        return _clean_join(holdings_list[0], path)

    raise ValueError('No holdings directory for logical path ' + path)

def selected_path_from_path(path, cls, abspaths=True):
    """Return the logical path or absolute path derived from a logical or
    an absolute path.

    Keyword arguments:
        path     -- the path of a file
        cls      -- the class calling the other methods inside the function
        abspaths -- the flag to determine if the return value is an absolute path (default
                    True)
    """

    if cls.is_logical_path(path):
        if abspaths:
            return abspath_for_logical_path(path, cls)
        else:
            return path

    else:
        if abspaths:
            return path
        else:
            return logical_path_from_abspath(path, cls)
