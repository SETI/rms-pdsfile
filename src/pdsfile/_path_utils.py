##########################################################################################
# pdsfile/_path_utils.py
##########################################################################################

"""Path arithmetic and small helpers the PdsFile classes share.

Nothing here is a method, and every function that needs a setting reads it off a class
handed in as an argument, usually named ``cls``, so this module can be imported by
``pdsfile.pdsfile`` and by every mixin without importing any of them back. One function
does hold state of its own: ``_clean_glob()`` memoizes its answers, up to
``_GLOB_CACHE_SIZE`` of them, so a wildcard search it has already made is not made again.

Three of the ten functions convert between the two ways a file is named. An **absolute
path** is where the file sits on this machine; a **logical path** is what follows the
holdings directory, starting at a category name such as ``volumes`` or ``previews``, and
is the same string on every machine that hosts the same holdings.
``logical_path_from_abspath()`` goes one way, ``abspath_for_logical_path()`` the other,
and ``selected_path_from_path()`` accepts either and returns whichever kind the caller
asks for. Turning a logical path into an absolute one is the harder direction, because
a machine can host several holdings directories and the file could be in any of them.

The other seven are utilities: ``construct_category_list()`` builds the category names a
holdings tree can contain, ``repair_case()`` recovers the capitalization the filesystem
actually used, ``formatted_file_size()`` renders a byte count for display, and
``_clean_join()``, ``_clean_abspath()``, ``_clean_glob()`` and ``_needs_glob()`` are the
small path and wildcard primitives the rest of the package builds on.

``FILE_BYTE_UNITS`` names the size units, and ``_GLOB_CACHE_SIZE`` is how many wildcard
searches ``_clean_glob()`` remembers.

There is no class here to carry a state contract, so it sits in this docstring. Every
attribute these functions read or write on the PdsFile class handed to them, and nothing
else -- str, list, os, os.path, glob, fnmatch, math and functools methods are not in
scope::

  class attributes read       CATEGORIES, FS_IS_CASE_INSENSITIVE,
                              LOCAL_HOLDINGS_DIRS, LOCAL_PRELOADED, PDS_HOLDINGS,
                              _HOLDINGS_ENV
  class attributes WRITTEN    LOCAL_HOLDINGS_DIRS, rebound with the single
                              directory the environment variable named, or with
                              the targets the symlink search turned up, which is
                              an empty list where it turned up nothing
  other methods called        glob_glob, is_logical_path, os_listdir

By function: ``logical_path_from_abspath()`` reaches ``PDS_HOLDINGS``; ``_clean_glob()``
reaches ``FS_IS_CASE_INSENSITIVE``; ``repair_case()`` reaches ``os_listdir()``;
``abspath_for_logical_path()`` reaches ``CATEGORIES``, ``LOCAL_HOLDINGS_DIRS``,
``LOCAL_PRELOADED``, ``_HOLDINGS_ENV`` and ``glob_glob()``; and
``selected_path_from_path()`` reaches ``is_logical_path()``. The six class attributes are
defined on PdsFile, with ``PDS_HOLDINGS``, ``_HOLDINGS_ENV`` and ``LOCAL_PRELOADED``
overridden on the subclasses as well; ``is_logical_path()`` is a PdsFile classmethod, and
``glob_glob()`` and ``os_listdir()`` are ``_LocalFsMixin`` classmethods. The other five
functions take no class argument and reach nothing on one. Every one of these is an
attribute lookup on the class object at run time, not an import, which is what keeps this
module free of any dependency on the package it serves.
"""

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
    """Return every category name a holdings tree can contain.

    A category name is a volume type with an optional ``archives-`` prefix and an
    optional ``checksums-`` prefix, so each volume type yields four names. The three
    that would decorate ``documents`` are then dropped, because no archive or checksum
    is made for the documents tree: the result holds ``documents`` itself and no
    ``archives-documents``, ``checksums-documents`` or ``checksums-archives-documents``.
    A list of *n* volume types therefore gives 4*n* - 3 categories.

    The order is the order the loops produce, not alphabetical: the bare volume types
    first, then the ``archives-`` names, then the ``checksums-`` names, then the
    ``checksums-archives-`` names, each group in the order the volume types were given.

    Parameters:
        voltypes: the volume type names. They are iterated four times, once per
            combination of the two prefixes, so a one-shot iterator such as a generator
            yields only the bare names and then fails the removals below. Each name is
            concatenated with the prefixes, so each must be a string. ``documents`` must
            be among them.

    Returns:
        list: the category names.

    Raises:
        ValueError: raised by ``remove()`` when ``documents`` is not one of the volume
            types, because the three names it removes are then not in the list.
    """

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

    The logical path is whatever follows the first occurrence of the holdings directory
    name, which the class supplies as ``PDS_HOLDINGS``. What is looked for is that name
    with a slash on each side, so an absolute path that ends at the holdings directory
    yields an empty string only when it carries the trailing slash; written without one
    there is nothing to match and the path is rejected. A path that names the holdings
    directory twice is split at the first.

    Parameters:
        abspath (str): the absolute path of a file.
        cls: the PdsFile subclass whose ``PDS_HOLDINGS`` name is looked for.

    Returns:
        str: the logical path, starting at a category name.

    Raises:
        ValueError: if the absolute path does not contain the holdings directory name.
            It is constructed from two arguments, so the offending path is the
            exception's second argument rather than part of its message text.
    """
    parts = abspath.partition('/'+cls.PDS_HOLDINGS+'/')
    if parts[1]:
        return parts[2]

    raise ValueError('Not compatible with a logical path: ', abspath)

def _clean_join(a, b):
    """Join two path fragments with a slash, tolerating an empty first fragment.

    Nothing is normalized: a first fragment that already ends in a slash produces a
    double slash, and a second fragment that starts with one does the same.

    Parameters:
        a (str): the leading fragment. An empty string means the result is ``b`` alone.
        b (str): the trailing fragment.

    Returns:
        str: the joined path.
    """
    if a:
        return a + '/' + b
    else:
        return b

def _clean_abspath(path):
    """Return an absolute path written with forward slashes.

    The path is resolved against the working directory the way ``os.path.abspath()``
    resolves it, and on a platform whose separator is a backslash the separators are
    then rewritten as forward slashes, so callers see one spelling everywhere.

    Parameters:
        path: the path to resolve, in any form ``os.path.abspath()`` accepts.

    Returns:
        str: the absolute path.
    """
    abspath = os.path.abspath(path)
    if os.sep == '\\':
        abspath = abspath.replace('\\', '/')
    return abspath

@functools.lru_cache(maxsize=_GLOB_CACHE_SIZE)
def _clean_glob(cls, pattern, force_case_sensitive=False):
    """Return the paths matching a wildcard pattern, written with forward slashes.

    The answer is memoized on all three arguments, up to ``_GLOB_CACHE_SIZE`` distinct
    calls, so a repeated search does not touch the filesystem again and a file created
    or deleted afterwards is not seen. The memoized list is the same object every time,
    so a caller that mutates it changes what every later caller receives.

    The order is whatever ``glob.glob()`` returns, which is the filesystem's, not sorted.

    Parameters:
        cls: the PdsFile subclass whose ``FS_IS_CASE_INSENSITIVE`` flag and
            ``os_listdir()`` are used. It is part of the memoization key, so it must be
            hashable, which a class is.
        pattern (str): the wildcard pattern to match.
        force_case_sensitive (bool): whether to insist that a match agree with the
            pattern in case. It has an effect only on a filesystem the class marks as
            case-insensitive; elsewhere the matches already agree in case.

    Returns:
        list: the matching paths.

    Raises:
        OSError: raised by ``repair_case()`` on the case-sensitive path, if a matched
            file is gone by the time its capitalization is checked.
    """
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
    """Return True if a path expression contains a wildcard.

    The three wildcard characters are ``*``, ``?`` and ``[``. A closing ``]`` on its own
    is not one, so a pattern is treated as a wildcard from its opening bracket alone.

    Parameters:
        pattern (str): the path expression to inspect.

    Returns:
        bool: True if the expression contains a wildcard character.
    """
    return '*' in pattern or '?' in pattern or '[' in pattern

def repair_case(abspath, cls):
    """Return an absolute path capitalized the way the filesystem capitalizes it.

    Each component below the root is looked up in its parent directory and replaced by
    the first entry that matches it ignoring case. A trailing slash on the argument is
    preserved on the result. The path is resolved to an absolute one first, so a
    relative argument is repaired relative to the working directory.

    Only the **last** component decides whether the path is reported as missing: the
    match flag is reset on every component, so a middle component that matched nothing
    is left as it was given. That component is not reported here. What happens instead
    is that the next component's directory listing is taken through the unrepaired name,
    which is where the OSError comes from on a case-insensitive lookup that failed.

    A path with no component below the root -- the root itself -- raises
    ``UnboundLocalError``, because the loop that sets the match flag does not run.

    Parameters:
        abspath (str): the path to repair.
        cls: the PdsFile subclass whose ``os_listdir()`` reads each directory below the
            first. The first component is looked for in ``/`` itself, which is read with
            ``os.listdir()`` directly rather than through the class.

    Returns:
        str: the repaired absolute path.

    Raises:
        OSError: raised by ``os_listdir()`` when a directory along the path does not
            exist or is not a directory, and by ``open()`` when every directory could be
            read but the final component matched nothing.
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
        # This will raise an OSError if the file does not exist or is not a
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
    if trailing_slash:
        parts.append('')
    abspath = '/'.join(parts)

    # Raise an OSError if last field was not found
    if not found:
        with open(abspath, 'rb'):
            pass

    return abspath

def formatted_file_size(size):
    """Return a byte count written for display, with a unit.

    The units step by factors of 1000, not 1024, so ``KB`` here is a thousand bytes. The
    number is written to three significant digits, so a size is rounded rather than
    truncated, and the unit is chosen before that rounding. A value that rounds up to a
    thousand of its own unit therefore keeps the smaller unit and is written in
    scientific notation, which shows one digit rather than three: 999999 comes out as
    ``1e+03 KB``, not as ``1000 KB`` and not as ``1 MB``. A size of zero is reported as
    ``0 bytes``.

    Parameters:
        size: the number of bytes. It is compared for truth and used arithmetically, so
            an int and a float are both accepted. A whole number of bytes is what the
            result means, and a value between zero and one exclusive is not one: the unit
            order goes negative there and indexes ``FILE_BYTE_UNITS`` from its end, so
            0.5 comes out as ``500 YB`` with no error raised.

    Returns:
        str: the size and its unit, separated by a space.

    Raises:
        ValueError: raised by ``log10()`` on a negative size.
        IndexError: for a size of 1e27 or more, because ``FILE_BYTE_UNITS`` stops at
            ``YB``, and for a positive size below 1e-27, because the negative order then
            reaches past the front of the same list. Both come from the unit lookup, the
            item read ``__getitem__()`` on that list.
    """
    order = int(math.log10(size) // 3) if size else 0
    return f'{size / 1000.**order:.3g} {FILE_BYTE_UNITS[order]}'

def abspath_for_logical_path(path, cls):
    """Return the absolute path derived from a logical path.

    A logical path begins at a category name, below the holdings directory, so turning
    it into an absolute path means deciding which holdings directory it belongs to. This
    machine can host several. They are looked for in this order, and the first source
    that yields a non-empty list wins:

      1. the holdings directories a preload has loaded, ``LOCAL_PRELOADED``;
      2. the ones already found and remembered on the class, ``LOCAL_HOLDINGS_DIRS``;
      3. the single directory named by the environment variable whose name the class
         holds as ``_HOLDINGS_ENV``;
      4. the targets of the ``holdings*`` symlinks under
         ``/Library/WebServer/Documents``, sorted by link name, which exist only on a
         Mac with the website installed.

    Sources 3 and 4 write what they found back onto the class as
    ``LOCAL_HOLDINGS_DIRS``, so the search is done once per class; source 4 writes an
    empty list when it finds nothing, which leaves the next call to search again.

    With exactly one holdings directory the answer is that directory joined to the
    logical path, and **the file is not checked for existence**. With more than one,
    each is tried in turn and the first that has a match wins, taking the first match
    if the wildcard search returned several; if none has a match, the first directory is
    used anyway, so the return value is again a path that may not exist.

    Parameters:
        path (str): the logical path, beginning with a category name.
        cls: the PdsFile subclass whose ``CATEGORIES``, ``LOCAL_PRELOADED``,
            ``LOCAL_HOLDINGS_DIRS``, ``_HOLDINGS_ENV`` and ``glob_glob()`` are used.

    Returns:
        str: the absolute path.

    Raises:
        ValueError: if the first component of the path is not one of the class's
            categories, or if no holdings directory could be found at all.
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
        if matches:
            return matches[0]

    # File doesn't exist. Just pick one.
    if holdings_list:
        return _clean_join(holdings_list[0], path)

    raise ValueError('No holdings directory for logical path ' + path)

def selected_path_from_path(path, cls, abspaths=True):
    """Return either the absolute path or the logical path, from either kind of path.

    Which kind the argument is decides nothing about the answer: the class's
    ``is_logical_path()`` tells the two apart, and the caller's flag says which kind to
    return. A path already of the requested kind is returned unchanged.

    Parameters:
        path (str): a logical path or an absolute path.
        cls: the PdsFile subclass whose ``is_logical_path()`` classifies the argument
            and whose settings the conversion reads.
        abspaths (bool): whether to return an absolute path. False returns a logical
            path.

    Returns:
        str: the path, of the requested kind.

    Raises:
        ValueError: raised by ``abspath_for_logical_path()`` when no holdings directory
            can be found for a logical path, and by ``logical_path_from_abspath()``
            when an absolute path does not contain the holdings directory name.
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
