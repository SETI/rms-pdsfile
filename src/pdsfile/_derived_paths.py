##########################################################################################
# pdsfile/_derived_paths.py
# Paths a PdsFile derives from its own path: the checksum file that covers it, the
# archive file that contains it, and the log files written about it
##########################################################################################

import datetime


##########################################################################################
# Derived paths mixin
##########################################################################################
class _DerivedPathsMixin:
    """Builders for the paths PdsFile derives from its own path.

    A mixin of PdsFile; it holds methods only and defines no state of its own. The
    class attributes these methods read -- LOG_ROOT_ and LOGFILE_TIME_FMT -- are
    defined on PdsFile, and set_log_root writes LOG_ROOT_ back onto the class it is
    called on.

    checksum_path_if_exact and archive_path_if_exact call os_path_exists, which
    _LocalFsMixin supplies. That call resolves through the class at run time, so
    both mixins have to be bases of the same class.
    """

    ############################################################################
    # Checksum path associations
    ############################################################################

    def checksum_path_and_lskip(self):
        """Return the absolute path to the checksum file associated with this PdsFile.
        Also return the number of characters to skip over in that absolute path to obtain
        the basename of the checksum file.
        """

        if self.checksums_:
            raise ValueError('No checksums of checksum files: ' +
                             self.logical_path)

        if self.bundletype_ == 'volumes/' or self.bundletype_ == 'bundles/':
            suffix = ''
        else:
            suffix = '_' + self.bundletype_[:-1]

        if self.archives_:
            abspath = ''.join([self.root_, 'checksums-', self.category_,
                               self.bundleset, self.suffix, suffix, '_md5.txt'])
            lskip = (len(self.root_) + len('checksums_') + len(self.category_))

        elif self.bundlename:
            abspath = ''.join([self.root_, 'checksums-', self.category_,
                               self.bundleset_, self.bundlename, suffix, '_md5.txt'])
            lskip = (len(self.root_) + len('checksums_') + len(self.category_) +
                     len(self.bundleset_))

        # for non bundle directories under a bundleset
        elif (self.basename.startswith('checksums_') or
              self.basename.startswith('superseded') or
              self.basename.endswith('_support')):

            abspath = ''.join([self.root_, 'checksums-', self.category_,
                               self.bundleset_, self.basename, suffix, '_md5.txt'])
            lskip = (len(self.root_) + len('checksums_') + len(self.category_) +
                     len(self.bundleset_))
        else:
            raise ValueError('Missing volume name for checksum file: ' +
                             self.logical_path)

        return (abspath, lskip)

    def checksum_path_if_exact(self):
        """Return the absolute path to the checksum file with the exact same contents as
        this directory; otherwise blank. Determines whether Viewmaster shows a link to a
        checksum file.
        """

        if self.checksums_:
            return ''

        cls = type(self)

        path_if_exact = ''
        if self.archives_ and self.is_bundleset_dir:
            path_if_exact = self.checksum_path_and_lskip()[0]

        if self.is_bundle_dir:
            path_if_exact = self.checksum_path_and_lskip()[0]

        if cls.os_path_exists(path_if_exact):
            return path_if_exact

        return ''

    def dirpath_and_prefix_for_checksum(self):
        """Return tuple (absolute path to the directory associated with this checksum
        path, prefix suppressed from the file path that appears in each row of the file).
        """

        if self.archives_:
            dirpath = (f'{self.root_}{self.archives_}{self.bundletype_}' +
                       f'{self.bundleset}{self.suffix}')
            prefix_ = f'{dirpath}/'
        else:
            dirpath = (f'{self.root_}{self.archives_}{self.bundletype_}' +
                       f'{self.bundleset_}{self.bundlename}')
            prefix_ = f'{self.root_}{self.bundletype_}{self.bundleset_}'

        return (dirpath, prefix_)

    ############################################################################
    # Archive path associations
    ############################################################################

    def archive_path_and_lskip(self):
        """Return the absolute path to the archive file associated with this PdsFile.
        Also return the number of characters to skip over in that absolute path to obtain
        the basename of the archive file.
        """

        if self.checksums_:
            raise ValueError('No archives for checksum files: ' +
                             self.logical_path)

        if self.archives_:
            raise ValueError('No archives for archive files: ' +
                             self.logical_path)

        if self.bundletype_ == 'volumes/' or self.bundletype_ == 'bundles/':
            suffix = ''
        else:
            suffix = '_' + self.bundletype_[:-1]

        if not self.bundlename:
            raise ValueError('Archives require bundle names: ' +
                              self.logical_path)

        abspath = ''.join([self.root_, 'archives-', self.category_,
                           self.bundleset_, self.bundlename, suffix, '.tar.gz'])
        lskip = len(self.root_) + len(self.category_) + len(self.bundleset_)

        return (abspath, lskip)

    def archive_path_if_exact(self):
        """Return the absolute path to the archive file with the exact same contents as
        this directory; otherwise blank.
        """

        if self.checksums_ or self.archives_:
            return ''

        if self.interior:
            return ''

        try:
            path_if_exact = self.archive_path_and_lskip()[0]
        except ValueError:
            return ''

        cls = type(self)

        if cls.os_path_exists(path_if_exact):
            return path_if_exact

        return ''

    def dirpath_and_prefix_for_archive(self):
        """Return the absolute path to the directory associated with this archive path."""

        dirpath = f'{self.root_}{self.bundletype_}{self.bundleset_}{self.bundlename}'
        parent  = f'{self.root_}{self.bundletype_}{self.bundleset_}'

        return (dirpath, parent)

    def archive_logpath(self, task):
        """Return the absolute path to the log file associated with this archive file.

        Keyword arguments:
            task -- part of the log file basename that describes the task
        """

        this = self.copy()
        this.checksums_ = ''
        if this.archives_ == 'archives-':
            this.archives_ = ''
            this.category_ = this.bundletype_

        return this.log_path_for_bundle('_targz', task=task, dir='archives')

    ############################################################################
    # Log path associations
    ############################################################################

    @classmethod
    def set_log_root(cls, root=None):
        """Define the default root directory for logs. If None, use the "logs" directory
        parallel to "holdings".

        Keyword arguments:
            root -- the root of the log file path (default None)
        """

        if root is None:
            cls.LOG_ROOT_ = None
        else:
            cls.LOG_ROOT_ = root.rstrip('/') + '/'

    def _log_path_for(self, target, suffix, task, subdir, place):
        """Return a complete log file path, given the parts that name what is logged.

        The three log_path_for_* methods differ only in the parts that name their
        target and in whether they accept a suffix. Everything else -- resolving
        the log root, the optional subdirectory, the time tag, the task tag and the
        ".log" extension -- is the same for all three and is done here.

        Keyword arguments:
            target -- the parts naming what is being logged, appended after the
                      optional subdirectory
            suffix -- the suffix of the log file; '' appends nothing, which is what
                      log_path_for_index passes because it takes no suffix
            task   -- part of the log basename; '' appends nothing
            subdir -- the directory of the log file; '' appends nothing. This is the
                      log_path_for_* methods' "dir" argument under a name that does
                      not shadow the builtin; theirs is frozen by the public API
            place  -- 'default' or 'parallel', the option provides for a temporary
                      override of the default log root
        """

        cls = type(self)

        # This option provides for a temporary override of the default log root
        if place == 'default':
            temporary_log_root = cls.LOG_ROOT_
        elif place == 'parallel':
            temporary_log_root = None
        else:
            raise ValueError('unrecognized place option: ' + place)

        if temporary_log_root is None:
            parts = [self.disk_, 'logs/']
        else:
            parts = [temporary_log_root]

        if subdir:
            parts += [subdir.rstrip('/'), '/']

        parts += target

        if suffix:
            parts += ['_', suffix.lstrip('_')]  # exactly one "_" before suffix

        timetag = datetime.datetime.now().strftime(cls.LOGFILE_TIME_FMT)
        parts += ['_', timetag]

        if task:
            parts += ['_', task]

        parts += ['.log']

        return ''.join(parts)

    def log_path_for_bundle(self, suffix='', task='', dir='', place='default'):
        """Return a complete log file path for this bundle.

        The file name is [dir/]category/bundleset/bundlename_suffix_time[_task].log

         Keyword arguments:
            suffix -- the suffix of the log file (default '')
            task   -- part of the log basename (default '')
            dir    -- the directory of the log file (default '')
            place  -- 'default' or 'parallel', the option provides for a temporary
                      override of the default log root (default 'default')
        """

        return self._log_path_for([self.category_, self.bundleset_, self.bundlename],
                                  suffix, task, dir, place)

    def log_path_for_bundleset(self, suffix='', task='', dir='', place='default'):
        """Return a complete log file path for this bundle set.

        The file name is [dir/]category/bundleset_suffix_time[_task].log.

        Keyword arguments:
            suffix -- the suffix of the log file (default '')
            task   -- part of the log basename (default '')
            dir    -- the directory of the log file (default '')
            place  -- 'default' or 'parallel', the option provides for a temporary
                      override of the default log root (default 'default')
        """

        return self._log_path_for([self.category_, self.bundleset, self.suffix],
                                  suffix, task, dir, place)

    def log_path_for_index(self, task='', dir='index', place='default'):
        """Return a complete log file path for this bundle.

        The file name is [dir/]<logical_path_wo_ext>_timetag[_task].log.

        Keyword arguments:
            task   -- part of the log basename (default '')
            dir    -- the directory of the log file (default 'index')
            place  -- 'default' or 'parallel', the option provides for a temporary
                      override of the default log root (default 'default')
        """

        # This check precedes the place option's validation, so a non-index file
        # reports that before an unrecognized place
        if not self.is_index:
            raise ValueError('Not an index file: ' + self.logical_path)

        return self._log_path_for([self.logical_path.rpartition('.')[0]],
                                  '', task, dir, place)
