##########################################################################################
# pdsfile/_shelves.py
##########################################################################################

"""Shelf files: the sidecar indexes that answer questions about files without
opening them.

An info or link shelf file is a pickled dictionary covering one bundle, or one bundle set
of archives, and it is keyed by the interior path of each file below that bundle. An
index shelf covers one index table instead of a bundle and is keyed by row selection
keys, so a bundle has as many index shelves as it has index tables, in a directory of its
own. Three kinds exist, and they live in three parallel trees named after them:

  * an **info** shelf, under ``_infoshelf-<category>/``, records each file's size, its
    child count, its modification time, its checksum and, for an image, its dimensions;
  * a **link** shelf, under ``_linkshelf-<category>/``, records which files each label
    points at;
  * an **index** shelf, under ``_indexshelf-<category>/``, records which rows of an
    index table each selection key covers.

Reading them is what makes a holdings tree answerable without touching most of it, and
it is what lets the whole package run against a tree it cannot stat, under the
``SHELVES_ONLY`` setting that ``_local_fs.py`` implements.

``_ShelfMixin`` provides three things: the arithmetic that turns a file's path into the
shelf path and the key within it; the handling of a cache of open shelves, which is class
state on PdsFile, bounded, and trimmed by a serial number that each calling class issues
from a counter of its own; and the lookup that puts the two together. It also provides
two questions about expectation -- whether a file should have an info shelf entry at all,
and whether the one it should have is there.

``_eval_null_key_record()`` is a shortcut past all of that. Every info shelf is written
alongside a readable ``.py`` sidecar of the same dictionary, whose second line is the
entry for the bundle itself, so a question about a bundle can be answered by reading one
line instead of unpickling a whole shelf.
"""

import os
import pickle


##########################################################################################
# Info shelf sidecar records
##########################################################################################
def _eval_null_key_record(rec):
    """Return the values a line of an info shelf sidecar records for the null key.

    Every info shelf "<bundlename>_info.pickle" is written alongside a readable
    "<bundlename>_info.py" sidecar holding the same dictionary as Python source.
    The sidecar's second line is the entry for the null key -- the bundle itself
    -- and it is the only line this reads.

    The line has the form

        "": (nbytes, count, modtime, checksum, (width, height)),

    and the value returned is the tuple to the right of the colon: two ints, two
    strings, and a pair.

    The parse partitions on the *first* colon -- the one after the empty key,
    since the timestamp's colons come later -- then strips the surrounding
    whitespace and the newline, drops the final character (the trailing comma),
    and evaluates what is left. That evaluation is an eval(), so:

    * the sidecar is executable input, and the trust boundary is the holdings
      tree, whose sidecars are written by this package's own maintenance tools;
    * a line with no colon leaves an empty expression, and eval('') raises
      SyntaxError, as does any incomplete expression;
    * a line not ending in the trailing comma loses its last character anyway,
      which can turn a valid expression into a SyntaxError or, less visibly, into
      a different valid expression;
    * a bare name in the expression resolves against this function's locals
      (`rec` and `parts`), then this module's globals, then the builtins, and
      raises NameError if it is in none of them. A record the maintenance tools
      wrote is a tuple of literals and contains no name, so which namespaces are
      in scope is not observable.

    Parameters:
        rec (str): the second line of an info shelf sidecar, as returned by
            ``readline()``, so it still carries its trailing newline.

    Returns:
        tuple: the values the line records, which for a record the maintenance tools
        wrote is the byte count, the child count, the modification time, the checksum
        and the (width, height) pair.

    Raises:
        SyntaxError: raised by ``eval()`` when what is left after the parse is not a
            complete expression, which is what a line with no colon or without the
            expected trailing comma can leave behind.
        NameError: raised by ``eval()`` if the expression uses a bare name that is in
            none of the namespaces above.
    """

    # Format is "": (bytes, count, date, checksum, (0,0)),
    parts = rec.partition(':')
    return eval(parts[2].strip()[:-1])


##########################################################################################
# Shelf support mixin
##########################################################################################
class _ShelfMixin:
    """Shelf file support for PdsFile.

    A mixin of PdsFile; it holds methods only and defines no state of its own.

    The open-shelf cache is class state, not instance state, and it is defined on
    PdsFile itself. The four dictionaries are genuinely shared, because none of
    them is ever rebound: SHELF_CACHE maps a shelf path to the dictionary it holds,
    SHELF_ACCESS maps it to the serial number of its last use, and
    SHELF_NULL_KEY_VALUES remembers the one entry per shelf that describes the
    bundle as a whole, each of the three mutated in place; SHELF_PATH_INFO, which
    maps a shelf type to its directory prefix and file suffix, is only ever read.
    SHELF_CACHE_SIZE and SHELF_CACHE_SLOP bound the cache. SHELF_ACCESS_COUNT,
    which issues the serial numbers, is not shared: it is an int, so incrementing
    it rebinds it onto the class the call was made on, which for a real object is
    a per-bundleset rule subclass. Each such subclass counts from its own zero
    while writing into the one shared SHELF_ACCESS, so the serial numbers in that
    dictionary order the shelves by the activity of whichever class opened each
    one, not by when each was last used.

    This is the innermost layer in all but one respect, which is what lets
    _LocalFsMixin call into it without a cycle. The exception is the reach into
    _PropertiesMixin named below, and it is mutual: _PropertiesMixin calls
    info_shelf_expected, shelf_lookup and shelf_path_and_key_for_abspath from
    here. It costs nothing, because is_documents is one comparison of an instance
    attribute and reaches no further.

    Every attribute these methods read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, dict, os.path, pickle, file and logger
    methods are not in scope::

      class attributes read       LOGGER, PDS_HOLDINGS, SHELF_ACCESS,
                                  SHELF_ACCESS_COUNT, SHELF_CACHE,
                                  SHELF_CACHE_SIZE, SHELF_CACHE_SLOP,
                                  SHELF_NULL_KEY_VALUES, SHELF_PATH_INFO
      class attributes WRITTEN    SHELF_ACCESS_COUNT, rebound on every use onto
                                  the calling class. SHELF_ACCESS, SHELF_CACHE and
                                  SHELF_NULL_KEY_VALUES are mutated rather than
                                  rebound, so they are reads, and SHELF_PATH_INFO
                                  is only ever subscripted
      core properties read        is_category_dir
      instance attributes read    archives_, basename, bundlename, bundlename_,
                                  bundleset, bundleset_, category_, checksums_,
                                  interior, logical_path, root_, suffix
      instance attributes WRITTEN none

    All of those are defined on PdsFile. One more comes from a sibling mixin:
    info_shelf_expected reads _PropertiesMixin's is_documents, which holds no slot
    of its own and is recomputed on every access. Every one of these is an
    attribute lookup on self or on type(self) at run time, not an import, which is
    what lets the halves live in different modules.
    """

    def shelf_path_and_lskip(self, shelf_type='info', bundlename=''):
        """Return this file's shelf path, and the prefix length of the tree it covers.

        One shelf covers one bundle, or one bundle set of archives, so the shelf path is
        built from this file's bundle set and bundle rather than from the file itself. A
        bundle set can name one of its bundles explicitly, which is how a shelf is
        located from the level above it; on an archive file the name is never read, since
        one shelf already covers the whole bundle set. Three directories that sit under a
        bundle set without being bundles -- a name starting ``checksums_``, a name
        starting ``superseded``, or a name ending ``_support`` -- get a shelf of their own
        under their own name.

        The second value is a character count, and **it does not index the shelf path**.
        It is the length of the prefix that a *data* path under the covered tree carries
        before its shelf key begins, so slicing it off a file's own absolute path leaves
        the interior path that keys the shelf. Sliced off the shelf path instead it
        lands somewhere arbitrary, because that path carries a directory prefix such as
        ``_infoshelf-`` that the count does not account for.

        All three shelf types are accepted, but only 'info' and 'link' name a file a
        holdings tree holds. An index shelf is written one per index table, inside a
        directory named for the bundle, so what this builds for 'index' -- the bundle's
        own name under its bundle set in ``_indexshelf-<category>/`` -- sits one level
        above the real shelves and names nothing that exists. The ``indexshelf_abspath``
        property is what finds a real index shelf.

        Parameters:
            shelf_type (str): which shelf: 'index', 'info' or 'link'.
            bundlename (str): a bundle below this one to build the path for, with any
                trailing slash ignored. An empty string uses this file's own bundle. It
                is read only on the non-archive path; an archive file's shelf covers its
                whole bundle set whatever is passed here.

        Returns:
            tuple: the absolute path of the shelf file, and the prefix length described
            above.

        Raises:
            ValueError: if this is a checksum file, since checksums have no shelves; if
                it is an archive file with no bundle set; or if it is neither an archive
                nor anything a bundle name can be found for.
            KeyError: raised by the shelf-type lookup, the item read
                ``__getitem__()`` on SHELF_PATH_INFO, for a type that is not one of the
                three.
        """

        if self.checksums_:
            raise ValueError('No shelf files for checksums: ' +
                             self.logical_path)

        cls = type(self)

        (dir_prefix, file_suffix) = cls.SHELF_PATH_INFO[shelf_type]

        if self.archives_:
            if not self.bundleset_:
                raise ValueError('Archive shelves require bundle sets: ' +
                                 self.logical_path)

            abspath = ''.join([self.root_, dir_prefix,
                               self.category_, self.bundleset, self.suffix,
                               file_suffix, '.pickle'])
            lskip = (len(self.root_) + len(self.category_) +
                     len(self.bundleset_))

        else:
            if bundlename:
                this_bundlename = bundlename.rstrip('/')
            else:
                this_bundlename = self.bundlename

            if not self.bundlename_ and not bundlename:
                # for non-bundle directories under a bundleset
                if (self.basename.startswith('checksums_') or
                    self.basename.startswith('superseded') or
                    self.basename.endswith('_support')):
                    this_bundlename = self.basename
                else:
                    raise ValueError('Non-archive shelves require bundle names: ' +
                                     self.logical_path)

            abspath = ''.join([self.root_, dir_prefix,
                               self.category_, self.bundleset_, this_bundlename,
                               file_suffix, '.pickle'])
            lskip = (len(self.root_) + len(self.category_) +
                     len(self.bundleset_) + len(this_bundlename) + 1)

        return (abspath, lskip)

    def shelf_path_and_key(self, shelf_id='info', bundlename=''):
        """Return this file's shelf path and the key that finds it in that shelf.

        The key is this file's interior path -- what is left of its logical path below
        the bundle -- which is the empty string for the bundle directory itself. Naming
        a bundle explicitly asks about that bundle rather than about a file inside it,
        so the key is then the empty string whatever this file is. On an archive object
        the name does not reach the path, which is the bundle set's shelf whatever is
        passed; it does reach the key, which is emptied as it is anywhere else, so the
        answer describes the whole bundle set rather than the bundle that was named.

        Parameters:
            shelf_id (str): which shelf: 'index', 'info' or 'link'. Only 'info' and
                'link' name a file that exists; see ``shelf_path_and_lskip()``.
            bundlename (str): a bundle below this one to ask about. An empty string asks
                about this file.

        Returns:
            tuple: the absolute path of the shelf file, and the key into it.

        Raises:
            ValueError: raised by ``shelf_path_and_lskip()`` for a checksum file, an
                archive file with no bundle set, or a file with no bundle name.
            KeyError: raised by ``shelf_path_and_lskip()`` for an unrecognized shelf
                type.
        """

        (abspath, _lskip) = self.shelf_path_and_lskip(shelf_id, bundlename)
        if bundlename:
            return (abspath, '')
        else:
            return (abspath, self.interior)

    @classmethod
    def _get_shelf(cls, shelf_path, log_missing_file=True):
        """Return the dictionary a shelf file holds, opening it if it is not open.

        The open shelves are held in a cache shared by every PdsFile subclass, so a
        second request for the same shelf costs nothing but a bookkeeping update.
        Opening a shelf that was not cached reads and unpickles the whole file, sorts
        the dictionary by key so that a caller may binary-search it, remembers the entry
        for the bundle itself if the shelf has one and none was remembered before, and
        adds the result to the cache.

        The bookkeeping update stamps the shelf with the next serial number from
        SHELF_ACCESS_COUNT. That counter is an int, so incrementing it rebinds it onto
        the class the call was made on, which is normally a per-bundleset rule subclass,
        and each such class counts from its own zero into the one shared SHELF_ACCESS.

        The cache is then trimmed if it has grown past its size plus its slop, which is
        what keeps the trim from running on every open: the shelves are put in order of
        their stamps and all but the newest SHELF_CACHE_SIZE of them are closed. Because
        the stamps come from per-class counters, that order is the activity of each
        opening class rather than the order of use across the tree, and the shelf just
        opened can carry a lower stamp than shelves a busier class opened before it. It
        is then the one discarded, and the next request for it reopens the file.

        The debug line announcing the open is written before the check that reports a
        missing file, so a request for a missing shelf is logged and then fails.
        Suppressing the logging of that case turns the debug line's own guard into an
        existence test, so the line is then written only for a shelf that is there.

        Parameters:
            shelf_path (str): the absolute path of the shelf file.
            log_missing_file (bool): whether to log the attempt even when the file is
                not there. False suits a caller that expects the failure and handles it.

        Returns:
            dict: the shelf contents, in order of key. An info or link shelf is keyed by
            interior path; an index shelf, which this opens too, is keyed by row
            selection key.

        Raises:
            OSError: if the file does not exist, or if reading or unpickling it fails
                for any reason at all. The second case raises inside the handler, so the
                original is attached as the new exception's ``__context__`` and a
                traceback still prints it under "During handling of the above exception".
                What is missing is the explicit ``raise ... from``, which would make it
                the cause rather than the context.
        """

        # If the shelf is already open, update the access count and return it
        if shelf_path in cls.SHELF_CACHE:
            cls.SHELF_ACCESS_COUNT += 1
            cls.SHELF_ACCESS[shelf_path] = cls.SHELF_ACCESS_COUNT

            return cls.SHELF_CACHE[shelf_path]

        if log_missing_file or os.path.exists(shelf_path):
            cls.LOGGER.debug('Opening pickle file', shelf_path)

        if not os.path.exists(shelf_path):
            raise OSError(f'Pickle file not found: {shelf_path}')

        try:
            with open(shelf_path, 'rb') as f:
                shelf = pickle.load(f)
        except Exception:
            raise OSError(f'Unable to open pickle file: {shelf_path}')

        # The pickle files do not produce dictionaries that are in
        # alphabetical order, so we sort them here in case we want to
        # do a binary search later.
        keys_vals = list(zip(shelf.keys(), shelf.values(), strict=False))
        keys_vals.sort(key=lambda x: x[0])
        shelf = dict(keys_vals)

        # Save the null key values from the info shelves. This can save a lot of
        # shelf open/close operations when we just need info about a bundle,
        # not an interior file.
        if '' in shelf and shelf_path not in cls.SHELF_NULL_KEY_VALUES:
            cls.SHELF_NULL_KEY_VALUES[shelf_path] = shelf['']

        cls.SHELF_ACCESS_COUNT += 1
        cls.SHELF_ACCESS[shelf_path] = cls.SHELF_ACCESS_COUNT
        cls.SHELF_CACHE[shelf_path] = shelf

        # Trim the cache if necessary
        if len(cls.SHELF_CACHE) > (cls.SHELF_CACHE_SIZE +
                                       cls.SHELF_CACHE_SLOP):
            pairs = [(cls.SHELF_ACCESS[k],k) for k in cls.SHELF_CACHE]
            pairs.sort()

            shelf_paths = [p[1] for p in pairs]
            for shelf_path in shelf_paths[:-cls.SHELF_CACHE_SIZE]:
                cls._close_shelf(shelf_path)

        return shelf

    @classmethod
    def _close_shelf(cls, shelf_path):
        """Drop a shelf from the open-shelf cache.

        Closing a shelf that is not open is not an error: it is logged as one and the
        call returns.

        What is dropped is the shelf dictionary and its access record. The entry for the
        bundle itself, remembered separately when the shelf was opened, is **not**
        dropped, so a question about a bundle keeps being answerable from memory after
        its shelf has been closed, and that store is never trimmed.

        Parameters:
            shelf_path (str): the absolute path of the shelf file.
        """

        # If the shelf is not already open, return
        if shelf_path not in cls.SHELF_CACHE:
            cls.LOGGER.error('Cannot close pickle file; not currently open',
                         shelf_path)
            return

        # Remove from the cache
        del cls.SHELF_CACHE[shelf_path]
        del cls.SHELF_ACCESS[shelf_path]

        cls.LOGGER.debug('Pickle file closed', shelf_path)

    @classmethod
    def close_all_shelves(cls):
        """Drop every shelf from the open-shelf cache.

        The cache is shared by every PdsFile subclass, so this empties it for all of
        them. The remembered entries for the bundles themselves are kept, as they are by
        a single close.
        """

        keys = list(cls.SHELF_CACHE.keys())     # save keys so dict can be
        for shelf_path in keys:                     # be modified inside loop!
            cls._close_shelf(shelf_path)

    def shelf_lookup(self, shelf_type='info', bundlename=''):
        """Return what a shelf file records about this file.

        A question about a bundle rather than about a file inside it has two shortcuts
        before the shelf itself is opened. The first is the store of bundle entries
        already read. The second applies to info shelves only: the readable ``.py``
        sidecar beside the shelf carries the bundle's own entry on its second line, so
        that line is read and remembered instead of unpickling the whole shelf. This is
        what keeps a preload from opening every info shelf in the tree.

        Anything else opens the shelf, through the shared cache, and reads one key.

        Parameters:
            shelf_type (str): which shelf: 'info', 'link' or 'index'. Only 'info' and
                'link' name a file that exists; see ``shelf_path_and_lskip()``.
            bundlename (str): a bundle below this one to ask about, which is how a
                bundle set asks about one of its bundles. An empty string asks about
                this file. On an archive object the name is ignored and the answer is
                about the bundle set.

        Returns:
            the value the shelf records for this file, whose shape depends on which
            shelf was asked.

        Raises:
            ValueError: raised by ``shelf_path_and_key()`` for a checksum file, an
                archive file with no bundle set, or a file with no bundle name.
            KeyError: raised by ``shelf_path_and_key()`` for an unrecognized shelf type,
                and by the final item read ``__getitem__()`` when the shelf opened but
                holds no such key.
            OSError: raised by ``_get_shelf()`` when the shelf file is missing or
                unreadable, and by ``open()`` when the sidecar shortcut is taken and the
                ``.py`` file is missing. The sidecar is tried before the shelf, so a
                bundle whose sidecar is missing fails there rather than falling back.
            SyntaxError: raised by ``_eval_null_key_record()`` when the sidecar's second
                line is not the record it expects, which includes a sidecar with fewer
                than two lines.
            NameError: raised by ``_eval_null_key_record()`` when that line parses as a
                complete expression but uses a bare name, which is the other way a
                sidecar the maintenance tools did not write can fail.
        """

        cls = type(self)
        (shelf_path, key) = self.shelf_path_and_key(shelf_type, bundlename)

        # This potentially saves the need for a lot of opens and closes when
        # getting info about bundles rather than interior files
        if key == '':
            try:
                return cls.SHELF_NULL_KEY_VALUES[shelf_path]
            except KeyError:
                pass

            # Try the second line of the .py file; this is quicker than reading
            # the whole .pickle file. This is useful because it avoids the need
            # to open every info shelf file during preload.
            if shelf_type == 'info':
                py_path = shelf_path.replace('.pickle', '.py')
                cls.LOGGER.debug('Retrieving key "%s"', py_path)

                with open(py_path) as f:
                    rec = f.readline()
                    rec = f.readline()

                values = _eval_null_key_record(rec)
                cls.SHELF_NULL_KEY_VALUES[shelf_path] = values
                return values

        shelf = cls._get_shelf(shelf_path)
        return shelf[key]

    @classmethod
    def shelf_path_and_key_for_abspath(cls, abspath, shelf_type='info'):
        """Return the shelf path and key for an absolute path, without a PdsFile.

        This asks ``shelf_path_and_key()``'s question of a path directly, without
        building a PdsFile, which is what lets the filesystem layer use shelves while it
        is still deciding whether a PdsFile can be built at all.

        The path is split at the holdings directory name. An archive path is covered by
        its bundle set's shelf, so two components are consumed and the key is what
        follows; anything else is covered by its bundle's shelf, so three are consumed.
        The key for the covered directory itself is the empty string.

        The two do not always agree, because counting components is not the same as
        reading a parsed bundle name. In the documents tree a PdsFile carries no bundle
        name, so the instance method raises ValueError there while this one consumes
        three components and returns a shelf path built from the file's own basename,
        which no holdings tree holds. Of the filesystem layer's four entry points only
        ``os_path_exists()`` excludes the documents tree before it calls;
        ``os_path_isdir()``, ``os_listdir()`` and ``glob_glob()`` hand documents paths
        straight through, and ``_PropertiesMixin`` calls this for any absolute path at
        all.

        Parameters:
            abspath (str): the absolute path of the file.
            shelf_type (str): which shelf: 'index', 'info' or 'link'. Only 'info' and
                'link' name a file that exists: an index shelf is written one per index
                table, one directory below the path this builds.

        Returns:
            tuple: the absolute path of the shelf file, and the key into it.

        Raises:
            ValueError: if the path is under checksums, since checksums have no shelves;
                or if it has too few components for the kind of shelf that covers it,
                which includes a path with no holdings directory in it at all.
            KeyError: raised by the shelf-type lookup, the item read
                ``__getitem__()`` on SHELF_PATH_INFO, for a type that is not one of the
                three.
        """

        # No checksum shelf files allowed
        (root, _, logical_path) = abspath.partition(f'/{cls.PDS_HOLDINGS}/')
        if logical_path.startswith('checksums'):
            raise ValueError('No shelf files for checksums: ' + logical_path)

        (dir_prefix, file_suffix) = cls.SHELF_PATH_INFO[shelf_type]

        # For archive files, the shelf is associated with the bundleset
        if logical_path.startswith('archives'):
            parts = logical_path.split('/')
            if len(parts) < 2:
                raise ValueError('Archive shelves require bundle sets: ' +
                                 logical_path)

            shelf_abspath = ''.join([root, f'/{cls.PDS_HOLDINGS}/', dir_prefix,
                                     parts[0], '/', parts[1],
                                     file_suffix, '.pickle'])
            key = '/'.join(parts[2:])

        # Otherwise, the shelf is associated with the bundle
        else:
            parts = logical_path.split('/')
            if len(parts) < 3:
                raise ValueError('Non-archive shelves require bundle names: ' +
                                 logical_path)

            shelf_abspath = ''.join([root, f'/{cls.PDS_HOLDINGS}/', dir_prefix,
                                     parts[0], '/', parts[1], '/', parts[2],
                                     file_suffix, '.pickle'])
            key = '/'.join(parts[3:])

        return (shelf_abspath, key)

    @property
    def info_shelf_expected(self):
        """Whether this file should have an entry in an info shelf.

        Four things have none: a checksum file, anything in the documents tree, a
        category-level directory, which is merged across holdings directories and so
        belongs to no single tree, and anything at bundle-set level outside the archives
        tree. An archive has one from its bundle set downward, and everything else has
        one from its bundle downward.

        The last of the four is decided by the bundle name alone, so it takes in more
        than the bundle set's own directory and the files beside it, including its
        AAREADME. It also takes in the three directories that sit under a bundle set
        without being bundles -- a name starting ``checksums_``, a name starting
        ``superseded``, or a name ending ``_support`` -- for which
        ``shelf_path_and_lskip()`` does build a shelf path of their own. This answers
        False for them all the same, so ``shelf_exists_if_expected()`` returns None for
        such a directory rather than looking for the shelf that path names.

        This is a claim about what ought to exist, not about what does.
        ``shelf_exists_if_expected()`` is the one that looks.

        Returns:
            bool: True if an info shelf entry is expected.
        """

        # Checksum files have no info shelves
        if self.checksums_:
            return False

        # The document tree does not have info shelves
        if self.is_documents:
            return False

        # Category-level directories are merged
        if self.is_category_dir:
            return False

        # Archives have info shelves from the bundleset level on down
        if self.archives_:
            return True

        # Other files have shelves from the bundlename level on down. That
        # leaves bundleset-level files and their AAREADMEs, which have none.
        return bool(self.bundlename)

    def shelf_exists_if_expected(self):
        """Whether the info shelf entry this file should have is really there.

        Three answers, not two: True if an entry is expected and was found, False if one
        is expected and the shelf could not be read, and None if none is expected, which
        is not a failure and should not be reported as one.

        False comes only from an OSError, which is what a missing or unreadable shelf or
        sidecar raises. A shelf that opens but has no entry for this file raises KeyError
        instead, and a sidecar that is present but malformed raises SyntaxError or
        NameError, so False means the shelf could not be read rather than that the entry
        is not in it.

        Returns:
            bool: True or False as above, or None if no entry is expected.
        """

        if self.info_shelf_expected:
            try:
                self.shelf_lookup('info')
                return True
            except OSError:
                return False

        # Return None if a pdsfile instance doesn't expect the shelf file
        return None
