##########################################################################################
# pdsfile/_shelves.py
# Shelf file support: locating a shelf file and the key into it, opening and
# caching shelf files, and looking up the values they hold
##########################################################################################

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

    Keyword arguments:
        rec -- the second line of an info shelf sidecar, as returned by
               readline(), so it still carries its trailing newline.

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
    The open-shelf cache lives on PdsFile as the SHELF_CACHE, SHELF_ACCESS,
    SHELF_CACHE_SIZE, SHELF_CACHE_SLOP, SHELF_ACCESS_COUNT and
    SHELF_NULL_KEY_VALUES class attributes, so every subclass shares one cache.
    The other class attributes these methods read are LOGGER and PDS_HOLDINGS,
    also on PdsFile, and SHELF_PATH_INFO -- which maps a shelf type to its
    directory prefix and file suffix -- on the Pds3File and Pds4File subclasses.
    """

    def shelf_path_and_lskip(self, shelf_type='info', bundlename=''):
        """Return the absolute path to the shelf file associated with this PdsFile.
        Also return the number of characters to skip over in that absolute path to obtain
        the key into the shelf.

        Keyword arguments:
            shelf_type -- shelf type ID: 'index', 'info', or 'link' (default 'info')
            bundlename -- an optional bundle name to append to the end of a this path,
                          which can be used if this is a bundleset (default '')
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
        """Return the absolute path to a shelf file, plus the key for this item.

        Keyword arguments:
            shelf_id   -- shelf type ID: 'index', 'info', or 'link' (default 'info')
            bundlename -- an optional bundle name to append to the end of a this path,
                          which can be used if this is a bundleset (default '')
        """

        (abspath, _lskip) = self.shelf_path_and_lskip(shelf_id, bundlename)
        if bundlename:
            return (abspath, '')
        else:
            return (abspath, self.interior)

    @classmethod
    def _get_shelf(cls, shelf_path, log_missing_file=True):
        """Internal method to open and return a shelf/pickle file. A limited number of
        shelf files are kept open at all times to reduce file IO.

        Use log_missing_file = False to suppress log entries when a nonexistent
        shelf file is requested but the exception is handled externally.

        Keyword arguments:
            shelf_path       -- the path of the shelf file
            log_missing_file -- a flag used to determine if we would like to log the path
                                of the opening pickle file (default True)
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
        """Internal method to close a shelf file. A limited number of shelf
        files are kept open at all times to reduce file IO.

        Keyword arguments:
            shelf_path -- the path of the shelf file
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
        """Close all shelf files."""

        keys = list(cls.SHELF_CACHE.keys())     # save keys so dict can be
        for shelf_path in keys:                     # be modified inside loop!
            cls._close_shelf(shelf_path)

    def shelf_lookup(self, shelf_type='info', bundlename=''):
        """Return the contents of a shelf file associated with this object.

        Keyword arguments:
            shelf_type -- indicates the type of the shelf file: 'info', 'link', or
                          'index' (default 'info')
            bundlename -- can be used to get info about a bundle when the method
                          is applied to its enclosing bundleset (default '')
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
        """Return the absolute path to the shelf file associated with this file path.
        Also return the key for indexing into the shelf.

        Keyword arguments:
            abspath    -- the absolute path of the file
            shelf_type -- shelf type, e.g., 'info' or 'link' (default 'info')
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
        """Return True if this object should be associated with an entry in an info
        shelf file.
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
        """Return True if shelf exists for a pdsfile instance expected to have the shelf
        file. False if shelf doesn't exist for a pdsfile instance expected to have one.
        """

        if self.info_shelf_expected:
            try:
                self.shelf_lookup('info')
                return True
            except OSError:
                return False

        # Return None if a pdsfile instance doesn't expect the shelf file
        return None
