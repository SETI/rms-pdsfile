#!/usr/bin/env python3
################################################################################
# pdsdependency.py library and main program
#
# Syntax:
#   pdsdependency.py volume_path [volume_path ...]
#
# Enter the --help option to see more information.
################################################################################

import sys
import os
import glob
import re
import argparse

import pdslogger
import pdsfile
import translator

LOGNAME = 'pds.validation.dependencies'
LOGROOT_ENV = 'PDS_LOG_ROOT'

BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')

################################################################################
# Translator for tests to apply
#
# Each path to a volume is compared against each regular expression. For those
# regular expressions that match, the associated suite of tests is performed.
# Note that 'general' tests are performed for every volume.
################################################################################

TESTS = translator.TranslatorByRegex([
    ('.*',                          0, ['general']),
    ('.*/COCIRS_0xxx(|_v[3-9])/COCIRS_0[4-9].*',
                                    0, ['cocirs01']),
    ('.*/COCIRS_1xxx(|_v[3-9]).*',  0, ['cocirs01']),
    ('.*/COCIRS_[56]xxx/.*',        0, ['cocirs56']),
    ('.*/COISS_[12]xxx/.*',         0, ['coiss12', 'metadata', 'inventory',
                                        'rings', 'moons' ,'cumindex999']),
    ('.*/COISS_100[1-7]/.*',        0, ['jupiter']),
    ('.*/COISS_100[89]/.*',         0, ['saturn']),
    ('.*/COISS_2xxx/.*',            0, ['saturn']),
    ('.*/COISS_3xxx.*',             0, ['coiss3']),
    ('.*/COUVIS_0xxx/.*',           0, ['couvis', 'metadata', 'supplemental',
                                        'cumindex999']),
    ('.*/COUVIS_0xxx/COUVIS_0006.*',     0, ['saturn', 'rings']),
    ('.*/COUVIS_0xxx/COUVIS_000[7-9].*', 0, ['saturn', 'rings', 'moons']),
    ('.*/COUVIS_0xxx/COUVIS_00[1-9].*',  0, ['saturn', 'rings', 'moons']),
    ('.*/COVIMS_0.*',               0, ['covims', 'metadata', 'cumindex999']),
    ('.*/COVIMS_000[4-9].*',        0, ['saturn', 'rings', 'moons']),
    ('.*/COVIMS_00[1-9].*',         0, ['saturn', 'rings', 'moons']),
    ('.*/CO.*_8xxx/.*',             0, ['metadata', 'supplemental', 'profile']),
    ('.*/CORSS_8xxx/.*',            0, ['corss_8xxx']),
    ('.*/COUVIS_8xxx/.*',           0, ['couvis_8xxx']),
    ('.*/COVIMS_8xxx/.*',           0, ['covims_8xxx']),
    ('.*/EBROCC_xxx/.*',            0, ['ebrocc_xxxx', 'metadata',
                                        'supplemental', 'profile']),
    ('.*/GO_0xxx/GO_000[2-9].*',    0, ['metadata', 'cumindex999',
                                        'go_previews2', 'go_previews3',
                                        'go_previews4', 'go_previews5', 'supplemental',
                                        'inventory', 'sky']),
    ('.*/GO_0xxx/GO_00[12].*',      0, ['metadata', 'cumindex999',
                                        'go_previews2', 'go_previews3',
                                        'go_previews4', 'go_previews5', 'supplemental',
                                        'inventory', 'sky']),
    ('.*/GO_0xxx/GO_000[2-9].*',    0, ['body']),
    ('.*/GO_0xxx/GO_001[0-5].*',    0, ['body']),
    ('.*/GO_0xxx/GO_001[6-9].*',    0, ['jupiter', 'rings', 'moons']),
    ('.*/GO_0xxx/GO_002.*',         0, ['jupiter', 'rings', 'moons']),
    ('.*/GO_0xxx/GO_0016.*',        0, ['sl9']),
    ('.*/GO_0xxx_v1/GO_000[2-9].*', 0, ['go_previews2', 'go_previews3',
                                        'go_previews4', 'go_previews5']),
    ('.*/GO_0xxx_v1/GO_00[12].*',   0, ['go_previews2', 'go_previews3',
                                        'go_previews4', 'go_previews5']),
    (r'.*/JNOJIR_xxxx(|_v[\d.]+)/JNOJIR_(?!(1059|2059|2060)).*',
                                    0, ['metadata', 'cumindex999']),
    ('.*/JNOJNC_0xxx/.*',           0, ['metadata', 'cumindex999']),
    ('.*/HST.x_xxxx/.*',            0, ['hst', 'metadata', 'cumindex9_9999']),
    ('.*/NH..(LO|MV)_xxxx/.*',      0, ['metadata', 'supplemental', 'cumindexNH']),
    ('.*/NH(JU|LA)LO_[12]00.*',     0, ['jupiter', 'rings', 'moons', 'inventory']),
    ('.*/NHP.LO_[12]00.*',          0, ['pluto', 'rings', 'moons', 'inventory']),
    ('.*/NH[LPK].LO_[12]00.*',      0, ['nhbrowse']),
    ('.*(?<!_v[12])/NHJULO_100.*',  0, ['nhbrowse']),       # not NHJULO_1001 _v1-2
    ('.*(?<!_v[123])/NHJULO_200.*', 0, ['nhbrowse']),       # not NHJULO_2001 _v1-3
    ('.*/NH[PK].MV_[12]00.*',       0, ['nhbrowse']),
    ('.*(?<!_v1)/NHLAMV_[12]00.*',  0, ['nhbrowse_vx']),    # not NHLAMV _v1
    ('.*/NHJUMV_100.*',             0, ['nhbrowse_vx']),
    ('.*(?<!_v1)/NHJUMV_200.*',     0, ['nhbrowse_vx']),    # not NHJUMV_2001 _v1
    ('.*/RPX_xxxx/.*',              0, ['metadata']),
    ('.*/RPX_xxxx/RPX_000.*',       0, ['obsindex', 'cumindex99']),
    ('.*/VGISS_[5678]xxx/.*',       0, ['vgiss', 'metadata', 'raw_image',
                                        'supplemental', 'cumindex999']),
    ('.*/VGISS_5(10[4-9]|20[5-9]|11|21)/.*',
                                    0, ['jupiter', 'inventory', 'rings',
                                        'moons']),
    ('.*/VGISS_6(10|11[0-5]|2)/.*', 0, ['saturn', 'inventory', 'rings',
                                        'moons']),
    ('.*/VGISS_7xxx/.*',            0, ['uranus', 'inventory', 'rings',
                                        'moons']),
    ('.*/VGISS_8xxx/.*',            0, ['neptune', 'inventory', 'rings',
                                        'moons']),
    ('.*/VG_28xx/.*',               0, ['metadata', 'vg_28xx']),
])

################################################################################
# Class definition
################################################################################

class PdsDependency(object):

    DEPENDENCY_SUITES = {}
    MODTIME_DICT = {}
    COMMANDS_TO_TYPE = []

    def __init__(self, title, glob_pattern, regex, sublist, messages=[],
                 suite=None, newer=True, func=None, args=(), exceptions=[]):
        """Constructor for a PdsDependency.

        Inputs:
            title           a short description of the dependency.
            glob_pattern    a glob pattern for finding files.
            regex           regular expression to match path returned by glob.
            sublist         a list of substitution strings returning paths to
                            files that must exist.
            messages        a list of commands the user must type to solve the
                            problem, with "[c]" replacing the command
                            "initialize" or "repair", [C] replacing
                            "initialize" or "reinitialize", and "[d]"
                            replacing the leading directory path.
            suite           optional name of a test suite to which this
                            dependency belongs.
            newer           True if the file file must be newer; False to
                            suppress a check of the modification date.
            func            A function to transform the volume ID before
                            applying the test. Used to test cumulative indices
                            by transforming, e.g., COISS_1010 to COISS_1999.
            args            Any arguments to pass to `func` after the volume ID.
            exceptions      a list of zero or more regular expressions. If a
                            file path matches one of these patterns, then it
                            will not trigger a test.
        """

        self.glob_pattern = glob_pattern

        if isinstance(regex, str):
            self.regex = re.compile('^' + regex + '$', re.I)
        else:
            self.regex = regex

        self.regex_pattern = self.regex.pattern
        self.sublist = [sublist] if isinstance(sublist, str) else sublist

        if suite is not None:
            if suite not in PdsDependency.DEPENDENCY_SUITES:
                PdsDependency.DEPENDENCY_SUITES[suite] = []

            PdsDependency.DEPENDENCY_SUITES[suite].append(self)

        self.title = title
        self.suite = suite
        self.messages = [messages] if isinstance(messages, str) else messages
        self.newer = newer
        self.func = func
        self.args = args
        self.exceptions = [re.compile(pattern, re.I) for pattern in exceptions]

    @staticmethod
    def purge_cache():
        PdsDependency.MODTIME_DICT = {}

    @staticmethod
    def get_modtime(abspath, logger):
        """Return the Unix-style modification time for a file, recursively for
        a directory. Cache results for directories."""

        if os.path.isfile(abspath):
            return os.path.getmtime(abspath)

        if abspath in PdsDependency.MODTIME_DICT:
            return PdsDependency.MODTIME_DICT[abspath]

        modtime = -1.e99
        files = os.listdir(abspath)
        for file in files:
            absfile = os.path.join(abspath, file)

            if file == '.DS_Store':     # log .DS_Store files; ignore dates
                logger.ds_store('.DS_Store ignored', absfile)
                continue

            if '/._' in absfile:        # log dot-underscore files; ignore dates
                logger.dot_underscore('._* file ignored', absfile)
                continue

                if BACKUP_FILENAME.match(file) or ' copy' in file:
                    logger.error('Backup file skipped', abspath)
                    continue

            modtime = max(modtime, PdsDependency.get_modtime(absfile, logger))

        PdsDependency.MODTIME_DICT[abspath] = modtime
        return modtime

    def test1(self, dirpath, check_newer=True, logger=None, limits={}):
        """Perform one test and log the results."""

        dirpath = os.path.abspath(dirpath)
        pdsdir = pdsfile.Pds3File.from_abspath(dirpath)
        lskip_ = len(pdsdir.root_)

        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.replace_root([pdsdir.root_, pdsdir.disk_])

        # Don't log if the source directory doesn't exist
        pattern = pdsdir.root_ + self.glob_pattern
        pattern = pattern.replace('$', pdsdir.volset_[:-1], 1)
        if '$' in pattern:
            if self.func is None:
                volname = pdsdir.volname
            else:
                volname = self.func(pdsdir.volname, *self.args)
            pattern = pattern.replace('$', volname, 1)

        abspaths = glob.glob(pattern)
        if not abspaths:
            return (0, 0, 0, 0)

        # Remove "Newer" at beginning of title if check_newer is False
        if not check_newer and self.title.startswith('Newer '):
            title = self.title[6:].capitalize()
        else:
            title = self.title

        missing = set()         # prevent duplicated messages
        out_of_date = set()
        confirmed = set()

        logger.open(title, dirpath, limits=limits, force=True)
        try:
            for sub in self.sublist:
                try:
                    for abspath in abspaths:

                        # Check exception list
                        exception_identified = False
                        for regex in self.exceptions:
                            if regex.fullmatch(abspath):
                                logger.info('Test skipped', abspath)
                                exception_identified = True
                                break

                        if exception_identified:
                            continue

                        path = abspath[lskip_:]

                        (requirement, count) = self.regex.subn(sub, path)
                        absreq = (pdsdir.root_ + requirement)
                        if count == 0:
                            logger.error('Invalid test', absreq)
                            continue

                        if not os.path.exists(absreq):
                            if absreq in missing:
                                continue

                            logger.error('Missing file', absreq)
                            for message in self.messages:
                                cmd = self.regex.sub(message, path)
                                cmd = cmd.replace('[c]', 'initialize')
                                cmd = cmd.replace('[C]', 'initialize')
                                cmd = cmd.replace('[d]', pdsdir.root_)
                                if cmd not in PdsDependency.COMMANDS_TO_TYPE:
                                    PdsDependency.COMMANDS_TO_TYPE.append(cmd)

                            missing.add(absreq)
                            continue

                        if self.newer and check_newer:
                            source_modtime = PdsDependency.get_modtime(abspath,
                                                                       logger)
                            requirement_modtime = PdsDependency.get_modtime(absreq,
                                                                            logger)

                            if requirement_modtime < source_modtime:
                                if absreq in out_of_date:
                                    continue

                                logger.error('File out of date', absreq)
                                for message in self.messages:
                                    cmd = self.regex.sub(message, path)
                                    cmd = cmd.replace('[c]', 'repair')
                                    cmd = cmd.replace('[C]', 'reinitialize')
                                    cmd = cmd.replace('[d]', pdsdir.root_)
                                    if cmd not in PdsDependency.COMMANDS_TO_TYPE:
                                        PdsDependency.COMMANDS_TO_TYPE.append(cmd)

                                out_of_date.add(absreq)
                                continue

                        if absreq in confirmed:
                            continue

                        logger.info('Confirmed', absreq)
                        confirmed.add(absreq)

                except (Exception, KeyboardInterrupt) as e:
                    logger.exception(e)
                    raise

        except (Exception, KeyboardInterrupt) as e:
            logger.exception(e)
            raise

        finally:
            (fatal, errors, warnings, tests) = logger.close()

        return (fatal, errors, warnings, tests)

    @staticmethod
    def test_suite(key, dirpath, check_newer=True, logger=None, limits={},
                   handlers=[]):

        dirpath = os.path.abspath(dirpath)
        pdsdir = pdsfile.Pds3File.from_abspath(dirpath)

        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.replace_root(pdsdir.root_)
        logger.open('Dependency test suite "%s"' % key, dirpath, limits=limits,
                    force=True, handler=handlers)

        try:
            for dep in PdsDependency.DEPENDENCY_SUITES[key]:
                dep.test1(dirpath, check_newer, limits=limits, logger=logger)

        except (Exception, KeyboardInterrupt) as e:
            logger.exception(e)
            raise

        finally:
            (fatal, errors, warnings, tests) = logger.close()

        return (fatal, errors, warnings, tests)

################################################################################
# General test suite
################################################################################

for thing in ['volumes', 'calibrated', 'diagrams', 'metadata', 'previews']:

    if thing == 'volumes':
        thing_ = ''
    else:
        thing_ = '_' + thing

    Thing = thing.capitalize()

    _ = PdsDependency(
        'Newer checksums for %s'             % thing,
        '%s/$/$'                             % thing,
        r'%s/(.*?)/(.*)'                     % thing,
        r'checksums-%s/\1/\2%s_md5.txt'      % (thing, thing_),
        [r'pdschecksums --[c] [d]%s/\1/\2'   % thing,
         r'pdsinfoshelf --[C] [d]%s/\1/\2'   % thing],
        suite='general', newer=True)

    _ = PdsDependency(
        'Newer info shelf files for %s'      % thing,
        'checksums-%s/$/$%s_md5.txt'         % (thing, thing_),
        r'checksums-%s/(.*?)/(.*)%s_md5\.txt' % (thing, thing_),
        [r'_infoshelf-%s/\1/\2_info.pickle'  % thing,
         r'_infoshelf-%s/\1/\2_info.py'      % thing],
        r'pdsinfoshelf --[C] [d]%s/\1/\2'    % thing,
        suite='general', newer=True)

    _ = PdsDependency(
        'Newer archives for %s'              % thing,
        '%s/$/$'                             % thing,
        r'%s/(.*?)/(.*)'                     % thing,
        r'archives-%s/\1/\2%s.tar.gz'        % (thing, thing_),
        [r'pdsarchives --[c] [d]%s/\1/\2'    % thing,
         r'pdschecksums --[c] [d]archives-%s/\1/\2%s.tar.gz' % (thing, thing_),
         r'pdsinfoshelf --[C] [d]archives-%s/\1/\2%s.tar.gz' % (thing, thing_)],
        suite='general', newer=True)

    _ = PdsDependency(
        'Newer checksums for archives-%s'                       % thing,
        'archives-%s/$*/$%s.tar.gz'                             % (thing, thing_),
        r'archives-%s/(.*)/(.*)%s\.tar\.gz'                     % (thing, thing_),
        r'checksums-archives-%s/\1%s_md5.txt'                   % (thing, thing_),
        [r'pdschecksums --[c] [d]archives-%s/\1/\2%s.tar.gz'    % (thing, thing_),
         r'pdsinfoshelf --[C] [d]archives-%s/\1/\2%s.tar.gz'    % (thing, thing_)],
        suite='general', newer=True)

    _ = PdsDependency(
        'Newer info shelf files for archives-%s'                % thing,
        'checksums-archives-%s/$*%s_md5.txt'                    % (thing, thing_),
        r'checksums-archives-%s/(.*)%s_md5\.txt'                % (thing, thing_),
        [r'_infoshelf-archives-%s/\1_info.pickle'               % thing,
         r'_infoshelf-archives-%s/\1_info.py'                   % thing],
        r'pdsinfoshelf --[c] [d]archives-%s/\1'                 % thing,
        suite='general', newer=True)

for thing in ['volumes', 'metadata', 'calibrated']:

    _ = PdsDependency(
        'Newer link shelf files for %s'      % thing,
        '%s/$/$'                             % thing,
        r'%s/(.*?)/(.*)'                     % thing,
        [r'_linkshelf-%s/\1/\2_links.pickle' % thing,
         r'_linkshelf-%s/\1/\2_links.py'     % thing],
        r'pdslinkshelf --[C] [d]%s/\1/\2'    % thing,
        suite='general', newer=True)

################################################################################
# Metadata tests
################################################################################

# General metadata including *_index.tab
_ = PdsDependency(
    'Metadata index table for each volume',
    'volumes/$/$',
    r'volumes/([^/]+?)(?:|_v[\d.]+)/(.*?)',
    r'metadata/\1/\2/\2_index.tab',
    [r'cp [d]volumes/\1/\2/index/index.tab [d]metadata/\1/\2/\2_index.tab',
     r'<EDIT> [d]metadata/\1/\2/\2_index.tab'],
    suite='metadata', newer=False)

_ = PdsDependency(
    'Label for every metadata table',
    'metadata/$*/$/*.[tc][as][bv]',
    r'metadata/(.*)\.(...)',
    r'metadata/\1.lbl',
    r'<LABEL> [d]metadata/\1.\2',
    suite='metadata', newer=False)

_ = PdsDependency(
    'Newer index shelf for every metadata table',
    'metadata/$*/$/*.tab',
    r'metadata/(.*)\.tab',
    [r'_indexshelf-metadata/\1.pickle',
     r'_indexshelf-metadata/\1.py'],
    r'pdsindexshelf --[C] [d]metadata/\1.tab',
    suite='metadata', newer=True,
    exceptions=[r'.*GO_0xxx_v1.*', r'.*_inventory\.tab'])

# More metadata suites
for (name, suffix, newer) in [
            ('supplemental'  , 'supplemental_index.tab' , True),
            ('inventory'     , 'inventory.csv'          , False),
            ('jupiter'       , 'jupiter_summary.tab'    , False),
            ('saturn'        , 'saturn_summary.tab'     , False),
            ('uranus'        , 'uranus_summary.tab'     , False),
            ('neptune'       , 'neptune_summary.tab'    , False),
            ('pluto'         , 'pluto_summary.tab'      , False),
            ('pluto'         , 'charon_summary.tab'     , False),
            ('rings'         , 'ring_summary.tab'       , False),
            ('moons'         , 'moon_summary.tab'       , False),
            ('sky'           , 'sky_summary.tab'        , False),
            ('body'          , 'body_summary.tab'       , False),
            ('raw_image'     , 'raw_image_index.tab'    , False),
            ('profile'       , 'profile_index.tab'      , False),
            ('obsindex'      , 'obsindex.tab'           , False),
            ('sl9'           , 'sl9_index.tab'          , False)]:

    _ = PdsDependency(
        name.capitalize() + ' metadata required',
        'volumes/$/$',
        r'volumes/([^/]+?)(?:|_v[\d.]+)/(.*?)',
        r'metadata/\1/\2/\2_' + suffix,
        r'<METADATA> [d]volumes/\1/\2 -> [d]metadata/\1/\2/\2_' + suffix,
        suite=name, newer=newer)

################################################################################
# Cumulative index tests where the suffix is "99", "999", or "9_9999"
################################################################################

def cumname(volname, nines):
    if nines[0] == '9':
        return volname[:-len(nines)] + nines
    return 'NHxx' + volname[4:8] + '999'

for nines in ('99', '999', '9_9999'):

    digits = nines.replace('9', r'\d')
    if nines == '9_9999':
        questions = '[01]_????'
    else:
        questions = nines.replace('9', '?')
    name = 'cumindex' + nines

    _ = PdsDependency(
        'Cumulative version of every metadata table',
        'metadata/$/$/*.[tc][as][bv]',
        rf'metadata/(.*?)/(.*){digits}/\2{digits}(_.*?)\.(tab|csv)',
        rf'metadata/\1/\g<2>{nines}/\g<2>{nines}\3.\4',
        [(rf'cat [d]metadata/\1/\2{questions}/\2{questions}\3.\4 '
          rf'> [d]metadata/\1/\g<2>{nines}/\g<2>{nines}\3.\4'),
          rf'<LABEL> [d]metadata/\1/\g<2>{nines}/\g<2>{nines}\3.\4'],
        suite=name, newer=True, exceptions=[r'.*_sl9_.*\.tab'])

_ = PdsDependency(
    'Cumulative version of every metadata table',
    'metadata/$/$/*.[tc][as][bv]',
    r'metadata/(.*?)/NH(..)(..)_([12])(\d\d\d)/NH\2\3_\4\5(_.*?)\.(tab|csv)',
    r'metadata/\1/NHxx\3_\g<4>999/NHxx\3_\g<4>999\6.\7',
    (r'cat [d]metadata/\1/NH??\3_\4???/NH??\3_\4???\6.\7 '
     r'> [d]metadata/\1/NHxx\3_\g<4>999/NHxx\3_\g<4>999\6.\7'),
    suite='cumindexNH', newer=True)

for nines in ('99', '999', '9_9999', 'NH'):
    name = 'cumindex' + nines

    _ = PdsDependency(
        'Label for every cumulative metadata table',
        'metadata/$/$/*.[tc][as][bv]',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.(tab|csv)',
        r'metadata/\1/\2/\2\3.lbl',
        r'<LABEL> [d]metadata/\1/\2/\2\3.\4',
        suite=name, newer=False, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer checksums for cumulative metadata',
        'metadata/$/$/*.[tc][as][bv]',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.(tab|csv)',
        r'checksums-metadata/\1/\2_metadata_md5.txt',
        [r'pdschecksums --[c] [d]metadata/\1/\2',
         r'pdsinfoshelf --[C] [d]metadata/\1/\2'],
        suite=name, newer=True, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer info shelf files for cumulative metadata',
        'metadata/$/$/*.[tc][as][bv]',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.(tab|csv)',
        [r'_infoshelf-metadata/\1/\2_info.pickle',
         r'_infoshelf-metadata/\1/\2_info.py'],
        r'pdsinfoshelf --[C] [d]metadata/\1/\2',
        suite=name, newer=True, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer index shelf files for cumulative metadata',
        'metadata/$/$/*.tab',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.tab',
        [r'_indexshelf-metadata/\1/\2/\2\3.pickle',
         r'_indexshelf-metadata/\1/\2/\2\3.py'],
        r'pdsindexshelf --[C] [d]metadata/\1/\2/\2\3.tab',
        suite=name, newer=True, func=cumname, args=(nines,),
        exceptions=[r'.*_inventory\.tab'])

    _ = PdsDependency(
        'Newer link shelf files for cumulative metadata',
        'metadata/$/$/*.[tc][as][bv]',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.(tab|csv)',
        [r'_linkshelf-metadata/\1/\2_links.pickle',
         r'_linkshelf-metadata/\1/\2_links.py'],
        r'pdslinkshelf --[C] [d]metadata/\1/\2',
        suite=name, newer=True, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer archives for cumulative metadata',
        'metadata/$/$/*.[tc][as][bv]',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.(tab|csv)',
        r'archives-metadata/\1/\2_metadata.tar.gz',
        [r'pdsarchives --[c] [d]metadata/\1/\2',
         r'pdschecksums --[c] [d]archives-metadata/\1/\2_metadata.tar.gz',
         r'pdsinfoshelf --[C] [d]archives-metadata/\1/\2_metadata.tar.gz'],
        suite=name, newer=True, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer checksums for cumulative archives-metadata',
        'archives-metadata/$/$_metadata.tar.gz',
        r'archives-metadata/(.*?)/(.*)_metadata.tar.gz',
        r'checksums-archives-metadata/\1_metadata_md5.txt',
        [r'pdschecksums --[c] [d]archives-metadata/\1/\2_metadata.tar.gz',
         r'pdsinfoshelf --[C] [d]archives-metadata/\1/\2_metadata.tar.gz'],
        suite=name, newer=True, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer info shelf files for cumulative archives-metadata',
        'archives-metadata/$/$_metadata.tar.gz',
        r'archives-metadata/(.*?)/(.*)_metadata.tar.gz',
        r'checksums-archives-metadata/\1_metadata_md5.txt',
        r'pdsinfoshelf --[C] [d]archives-metadata/\1/\2_metadata.tar.gz',
        suite=name, newer=True, func=cumname, args=(nines,))

################################################################################
# Preview tests
################################################################################

# For COCIRS_0xxx and COCIRS_1xxx
_ = PdsDependency(
    'Preview versions of every cube file',
    'volumes/$/$/EXTRAS/CUBE_OVERVIEW/*/*.JPG',
    r'volumes/(.*)/EXTRAS/CUBE_OVERVIEW/(.*)\.JPG',
    [r'previews/\1/DATA/CUBE/\2_thumb.jpg',
     r'previews/\1/DATA/CUBE/\2_small.jpg',
     r'previews/\1/DATA/CUBE/\2_med.jpg',
     r'previews/\1/DATA/CUBE/\2_full.jpg'],
    (r'<PREVIEW> [d]volumes/\1/EXTRAS/CUBE_OVERVIEW/(.*)\.JPG '
     r'-> [d]previews/\1/DATA/CUBE/\2_*.jpg'),
    suite='cocirs01', newer=True)

# For COCIRS_5xxx and COCIRS_6xxx
_ = PdsDependency(
    'Diagrams for every interferogram file',
    'volumes/$/$/BROWSE/*/*.PNG',
    r'volumes/(.*)/BROWSE/(.*?)\.PNG',
    [r'diagrams/\1/BROWSE/\2_thumb.jpg',
     r'diagrams/\1/BROWSE/\2_small.jpg',
     r'diagrams/\1/BROWSE/\2_med.jpg',
     r'diagrams/\1/BROWSE/\2_full.jpg'],
    r'<DIAGRAM> [d]volumes/\1/BROWSE/\2.PNG -> [d]diagrams/\1/BROWSE/*/\2_.jpg',
    suite='cocirs56', newer=False)

# For COISS_1xxx and COISS_2xxx
_ = PdsDependency(
    'Previews of every COISS image file',
    'volumes/$/$/data/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.png'],
    r'<PREVIEW> [d]volumes/\1.IMG -> [d]previews/\1*.jpg',
    suite='coiss12', newer=False)

_ = PdsDependency(
    'Calibrated versions of every COISS image file',
    'volumes/$/$/data/*/*.IMG',
    r'volumes/(.*)\.IMG',
    r'calibrated/\1_CALIB.IMG',
    r'<CALIBRATE> [d]volumes/\1.IMG -> [d]calibrated/\1_CALIB.IMG',
    suite='coiss12', newer=False)

# For COISS_3xxx
_ = PdsDependency(
    'Previews of every COISS derived map image',
    'volumes/$/$/data/images/*.IMG',
    r'volumes/(.*?)/data/images/(.*)\.IMG',
    [r'previews/\1/data/images/\2_thumb.jpg',
     r'previews/\1/data/images/\2_small.jpg',
     r'previews/\1/data/images/\2_med.jpg',
     r'previews/\1/data/images/\2_full.jpg'],
    r'<PREVIEW> [d]volumes/\1/data/images/\2.IMG -> [d]previews/\1/data/images/\2*.jpg',
    suite='coiss3', newer=True)

_ = PdsDependency(
    'Previews of every COISS derived map PDF',
    'volumes/$/$/data/maps/*.PDF',
    r'volumes/(.*?)/data/maps/(.*)\.PDF',
    [r'previews/\1/data/maps/\2_thumb.png',
     r'previews/\1/data/maps/\2_small.png',
     r'previews/\1/data/maps/\2_med.png',
     r'previews/\1/data/maps/\2_full.png'],
    r'<PREVIEW> [d]volumes/\1/data/maps/\2.PDF -> [d]previews/\1/data/maps/\2*.png',
    suite='coiss3', newer=True)

# For COUVIS_0xxx
_ = PdsDependency(
    'Previews of every COUVIS data file',
    'volumes/$/$/DATA/*/*.DAT',
    r'volumes/COUVIS_0xxx(|_v[\.\d]+)/(.*)\.DAT',
    [r'previews/COUVIS_0xxx/\2_thumb.png',
     r'previews/COUVIS_0xxx/\2_small.png',
     r'previews/COUVIS_0xxx/\2_med.png',
     r'previews/COUVIS_0xxx/\2_full.png'],
    r'<PREVIEW> [d]volumes/COUVIS_0xxx\1/\2.DAT -> [d]previews/COUVIS_0xxx/\2_*.png',
    suite='couvis', newer=False)

# For COVIMS_0xxx
_ = PdsDependency(
    'Previews of every COVIMS cube',
    'volumes/$/$/data/*/*.qub',
    r'volumes/(.*)\.qub',
    [r'previews/\1_thumb.png',
     r'previews/\1_small.png',
     r'previews/\1_med.png',
     r'previews/\1_full.png'],
    r'<PREVIEW> [d]volumes/\1.qub -> [d]previews/\1_*.png',
    suite='covims', newer=False)

# For CORSS_8xxx
_ = PdsDependency(
    'Previews for every CORSS_8xxx data directory',
    'volumes/$/$/data/Rev*/Rev*/*',
    r'volumes/CORSS_8xxx[^/]*/(CORSS_8001/data/Rev.../Rev.....?)/(Rev.....?)_(RSS_...._..._..._.)',
    [r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1 -> [d]previews/CORSS_8xxx/\1_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'GEO previews for every CORSS_8xxx data directory',
    'volumes/$/$/data/Rev*/Rev*/*',
    r'volumes/CORSS_8xxx[^/]*/(CORSS_8001/data/Rev.../Rev.....?)/(Rev.....?)_(RSS_...._..._..._.)',
    [r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_thumb.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_small.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_med.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1/\2_\3/ -> [d]previews/CORSS_8xxx/\1/\2_\3/\3_GEO_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'TAU previews for every CORSS_8xxx data directory',
    'volumes/$/$/data/Rev*/Rev*/*',
    r'volumes/CORSS_8xxx[^/]*/(CORSS_8001/data/Rev.../Rev.....?)/(Rev.....?)_(RSS_...._..._..._.)',
    [r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_thumb.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_small.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_med.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1/\2_\3/ -> [d]previews/CORSS_8xxx/\1/\2_\3/\3_TAU_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'Diagrams for every CORSS_8xxx data directory',
    'volumes/$/$/data/Rev*/Rev*/*',
    r'volumes/CORSS_8xxx[^/]*/(CORSS_8001/data/Rev.../Rev.....?)/(Rev.....?)_(RSS_...._..._..._.)',
    [r'diagrams/CORSS_8xxx/\1_\3_thumb.jpg',
     r'diagrams/CORSS_8xxx/\1_\3_small.jpg',
     r'diagrams/CORSS_8xxx/\1_\3_med.jpg',
     r'diagrams/CORSS_8xxx/\1_\3_full.jpg'],
    r'<DIAGRAM> [d]volumes/CORSS_8xxx*/\1 -> [d]diagrams/CORSS_8xxx/\1_\3_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'Previews of every CORSS_8xxx browse PDF',
    'volumes/$/$/browse/*.pdf',
    r'volumes/CORSS_8xxx[^/]*/(.*)\.pdf',
    [r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1.pdf -> [d]previews/CORSS_8xxx/\1_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'Previews of every CORSS_8xxx Rev PDF',
    'volumes/$/$/data/Rev*/*.pdf',
    r'volumes/CORSS_8xxx[^/]*/(.*)\.pdf',
    [r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1.pdf -> [d]previews/CORSS_8xxx/\1_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'Previews of every CORSS_8xxx data PDF',
    'volumes/$/$/data/Rev*/Rev*/Rev*/*.pdf',
    r'volumes/CORSS_8xxx[^/]*/(.*)\.pdf',
    [r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1.pdf -> [d]previews/CORSS_8xxx/\1_*.jpg',
    suite='corss_8xxx', newer=False)

# For COUVIS_8xxx
_ = PdsDependency(
    'Previews of every COUVIS_8xxx profile',
    'volumes/$/$/data/*_TAU01KM.TAB',
    r'volumes/COUVIS_8xxx[^/]*/(.*)_TAU01KM\.TAB',
    [r'previews/COUVIS_8xxx/\1_thumb.jpg',
     r'previews/COUVIS_8xxx/\1_small.jpg',
     r'previews/COUVIS_8xxx/\1_med.jpg',
     r'previews/COUVIS_8xxx/\1_full.jpg',
     r'diagrams/COUVIS_8xxx/\1_thumb.jpg'],
    r'<PREVIEW> [d]volumes/COUVIS_8xxx/\1_TAU01KM.TAB -> [d]previews/COUVIS_8xxx/\1_*.jpg',
    suite='couvis_8xxx', newer=False,
    exceptions=['.*2005_139_PSICEN_E.*',
                '.*2005_139_THEHYA_E.*',
                '.*2007_038_SAO205839_I.*',
                '.*2010_148_LAMAQL_E.*'])

_ = PdsDependency(
    'Diagrams of every COUVIS_8xxx profile',
    'volumes/$/$/data/*_TAU01KM.TAB',
    r'volumes/COUVIS_8xxx[^/]*/(.*)_TAU01KM\.TAB',
    [r'diagrams/COUVIS_8xxx/\1_thumb.jpg',
     r'diagrams/COUVIS_8xxx/\1_small.jpg',
     r'diagrams/COUVIS_8xxx/\1_med.jpg',
     r'diagrams/COUVIS_8xxx/\1_full.jpg'],
    r'<DIAGRAM> [d]volumes/COUVIS_8xxx/\1_TAU01KM.TAB -> [d]diagrams/COUVIS_8xxx/\1_*.jpg',
    suite='couvis_8xxx', newer=False,
    exceptions=['.*2005_139_PSICEN_E.*',
                '.*2005_139_THEHYA_E.*',
                '.*2007_038_SAO205839_I.*',
                '.*2010_148_LAMAQL_E.*'])

# For COVIMS_8xxx
_ = PdsDependency(
    'Previews of every COVIMS_8xxx profile',
    'volumes/$/$/data/*_TAU01KM.TAB',
    r'volumes/COVIMS_8xxx[^/]*/(.*)_TAU01KM\.TAB',
    [r'previews/COVIMS_8xxx/\1_thumb.jpg',
     r'previews/COVIMS_8xxx/\1_small.jpg',
     r'previews/COVIMS_8xxx/\1_med.jpg',
     r'previews/COVIMS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/COVIMS_8xxx/\1_TAU01KM.TAB -> [d]previews/COVIMS_8xxx/\1_*.jpg',
    suite='covims_8xxx', newer=False)

_ = PdsDependency(
    'Diagrams of every COVIMS_8xxx profile',
    'volumes/$/$/data/*_TAU01KM.TAB',
    r'volumes/COVIMS_8xxx[^/]*/(.*)_TAU01KM\.TAB',
    [r'diagrams/COVIMS_8xxx/\1_thumb.jpg',
     r'diagrams/COVIMS_8xxx/\1_small.jpg',
     r'diagrams/COVIMS_8xxx/\1_med.jpg',
     r'diagrams/COVIMS_8xxx/\1_full.jpg'],
    r'<DIAGRAM> [d]volumes/COVIMS_8xxx/\1_TAU01KM.TAB -> [d]diagrams/COVIMS_8xxx/\1_*.jpg',
    suite='covims_8xxx', newer=False)

_ = PdsDependency(
    'Previews of every COVIMS_8xxx PDF',
    'volumes/$/$/browse/*.PDF',
    r'volumes/COVIMS_8xxx[^/]*/(.*)\.PDF',
    [r'previews/COVIMS_8xxx/\1_thumb.jpg',
     r'previews/COVIMS_8xxx/\1_small.jpg',
     r'previews/COVIMS_8xxx/\1_med.jpg',
     r'previews/COVIMS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/COVIMS_8xxx/\1.PDF -> [d]previews/COVIMS_8xxx/\1_*.jpg',
    suite='covims_8xxx', newer=False)

# For EBROCC_xxxx
_ = PdsDependency(
    'Previews of every EBROCC browse PDF',
    'volumes/$/$/BROWSE/*.PDF',
    r'volumes/EBROCC_xxxx[^/]*/(.*)\.PDF',
    [r'previews/EBROCC_xxxx/\1_thumb.jpg',
     r'previews/EBROCC_xxxx/\1_small.jpg',
     r'previews/EBROCC_xxxx/\1_med.jpg',
     r'previews/EBROCC_xxxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/EBROCC_xxxx/\1.PDF -> [d]previews/EBROCC_xxxx/\1_*.jpg',
    suite='ebrocc_xxxx', newer=False)

_ = PdsDependency(
    'Previews of every EBROCC profile',
    'volumes/$/$/data/*/*.TAB',
    r'volumes/EBROCC_xxxx[^/]*/(.*)\.TAB',
    [r'previews/EBROCC_xxxx/\1_thumb.jpg',
     r'previews/EBROCC_xxxx/\1_small.jpg',
     r'previews/EBROCC_xxxx/\1_med.jpg',
     r'previews/EBROCC_xxxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/EBROCC_xxxx/\1.TAB -> [d]previews/EBROCC_xxxx/\1_*.jpg',
    suite='ebrocc_xxxx', newer=False)

# For GO_xxxx
_ = PdsDependency(
    'Previews of every GO image file, depth 2',
    'volumes/$/$/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/\1.IMG -> [d]previews/\1_*.jpg',
    suite='go_previews2', newer=True)

_ = PdsDependency(
    'Previews of every GO image file, depth 3',
    'volumes/$/$/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/\1.IMG -> [d]previews/\1_*.jpg',
    suite='go_previews3', newer=True)

_ = PdsDependency(
    'Previews of every GO image file, depth 4',
    'volumes/$/$/*/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/\1.IMG -> [d]previews/\1_*.jpg',
    suite='go_previews4', newer=True)

_ = PdsDependency(
    'Previews of every GO image file, depth 5',
    'volumes/$/$/*/*/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/\1.IMG -> [d]previews/\1_*.jpg',
    suite='go_previews5', newer=True)

# For HST*x_xxxx
_ = PdsDependency(
    'Previews of every HST image label',
    'volumes/$/$/data/*/*.LBL',
    r'volumes/(HST.._....)(|_v[\.\d]+)/(HST.*)\.LBL',
    [r'previews/\1/\3_thumb.jpg',
     r'previews/\1/\3_small.jpg',
     r'previews/\1/\3_med.jpg',
     r'previews/\1/\3_full.jpg'],
    r'<PREVIEW> [d]volumes/\1/\3.LBL -> [d]previews/\1/\3_*.jpg',
    suite='hst', newer=False)

# For NHxxLO_xxxx and NHxxMV_xxxx browse, stripping version number if present
_ = PdsDependency(
    'Previews of every NH image file',
    'volumes/$/$/data/*/*.fit',
    r'volumes/(NHxx.._....)(|_v[\.\d]+)/(NH\w+/data/\w+/\w{24})(|_[0-9]+)\.fit',
    [r'previews/\1/\3_thumb.jpg',
     r'previews/\1/\3_small.jpg',
     r'previews/\1/\3_med.jpg',
     r'previews/\1/\3_full.jpg'],
    r'<PREVIEW> [d]volumes/\1\2/\3\4.fit -> [d]previews/\1/\3_*.jpg',
    suite='nhbrowse', newer=False)

# For NHxxLO_xxxx and NHxxMV_xxxx browse, retaining version number
_ = PdsDependency(
    'Previews of every NH image file',
    'volumes/$/$/data/*/*.fit',
    r'volumes/(NHxx.._....)(|_v[\.\d]+)/(NH.*?)\.fit',
    [r'previews/\1/\3_thumb.jpg',
     r'previews/\1/\3_small.jpg',
     r'previews/\1/\3_med.jpg',
     r'previews/\1/\3_full.jpg'],
    r'<PREVIEW> [d]volumes/\1\2/\3.fit -> [d]previews/\1/\3_*.jpg',
    suite='nhbrowse_vx', newer=False)

# For VGISS_[5678]xxx
_ = PdsDependency(
    'Previews of every VGISS image file',
    'volumes/$/$/data/*/*RAW.IMG',
    r'volumes/(.*)_RAW\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/\1_RAW.IMG -> [d]previews/\1_*.jpg',
    suite='vgiss', newer=True)

# For VG_28xxx
_ = PdsDependency(
    'Previews of every VG_28xx data file',
    'volumes/$/VG_280[12]/*DATA/*/[PU][SUN][0-9]*.LBL',
    r'volumes/([^/]+)/([^/]+)(.*)/([PUR][SUN]\d)(...)(\w+)\.LBL',
    [r'previews/\1/\2/\4xxx\6_preview_thumb.png',
     r'previews/\1/\2/\4xxx\6_preview_small.png',
     r'previews/\1/\2/\4xxx\6_preview_med.png',
     r'previews/\1/\2/\4xxx\6_preview_full.png'],
    r'<PREVIEW> [d]volumes/\1/\2\3/\4\5\6.* -> [d]previews/\1/\2/\4xxx\6_preview_*.png',
    suite='vg_28xx', newer=True, exceptions=[r'.*/[PUR].*[01]\d\.LBL'])

_ = PdsDependency(
    'Previews of every VG_28xx data file',
    'volumes/$/VG_2803/*RINGS/*DATA/*/R[SUN][0-9]*.LBL',
    r'volumes/([^/]+)/([^/]+)(.*)/([PUR][SUN])(\d..)(\w+)\.LBL',
    [r'previews/\1/\2/\4xxx\6_preview_thumb.png',
     r'previews/\1/\2/\4xxx\6_preview_small.png',
     r'previews/\1/\2/\4xxx\6_preview_med.png',
     r'previews/\1/\2/\4xxx\6_preview_full.png'],
    r'<PREVIEW> [d]volumes/\1/\2\3/\4\5\6.* -> [d]previews/\1/\2/\4xxx\6_preview_*.png',
    suite='vg_28xx', newer=True, exceptions=[r'.*/[PUR].*[01]\d\.LBL'])

_ = PdsDependency(
    'Previews of every VG_28xx data file',
    'volumes/$/VG_2810/DATA/IS[0-9]_P[0-9][0-9][0-9][0-9]*.LBL',
    r'volumes/([^/]+)/([^/]+)(.*)/(IS\d_P\d\d\d\d)(.*)\.LBL',
    [r'previews/\1/\2/\4_preview_thumb.png',
     r'previews/\1/\2/\4_preview_small.png',
     r'previews/\1/\2/\4_preview_med.png',
     r'previews/\1/\2/\4_preview_full.png'],
    r'<PREVIEW> [d]volumes/\1/\2\3/\4\5.* -> [d]previews/\1/\2/\4_preview_*.png',
    suite='vg_28xx', newer=True, exceptions=[r'.*/[PUR].*[01]\d\.LBL'])

################################################################################
################################################################################

def test(pdsdir, logger=None, limits={}, check_newer=True, handlers=[]):
    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    path = pdsdir.abspath
    for suite in TESTS.all(path):
        _ = PdsDependency.test_suite(suite, path, check_newer=check_newer,
                                     limits=limits, logger=logger,
                                     handlers=handlers)

################################################################################
################################################################################

def main():

    # Set up parser
    parser = argparse.ArgumentParser(
        description='pdsdependency: Check all required files associated with ' +
                    'with a volume, confirming that they exist and that '      +
                    'their creation dates are consistent.')

    parser.add_argument('volume', nargs='+', type=str,
                        help='The path to the root directory of a volume or '  +
                             'a volume set.')

    parser.add_argument('--log', '-l', type=str, default='',
                        help='Optional root directory for a duplicate of the ' +
                             'log files. If not specified, the value of '      +
                             'environment variable "%s" ' % LOGROOT_ENV        +
                             'is used. In addition, individual logs are '      +
                             'written into the "logs" directory parallel to '  +
                             '"holdings". Logs are created inside the '        +
                             '"pdsdependency" subdirectory of each log root '  +
                             'directory.'
                             )

    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Do not also log to the terminal.')

    # Parse and validate the command line
    args = parser.parse_args()

    status = 0

    # Define the logging directory
    if args.log == '':
        try:
            args.log = os.environ[LOGROOT_ENV]
        except KeyError:
            args.log = None

    # Validate the paths
    for path in args.volume:
        path = os.path.abspath(path)
        pdsdir = pdsfile.Pds3File.from_abspath(path)
        if not pdsdir.is_volume_dir and not pdsdir.is_volset_dir:
          print('pdsdependency error: '
                'not a volume or volume set directory: ' + pdsdir.logical_path)
          sys.exit(1)

        if pdsdir.category_ != 'volumes/':
          print('pdsdependency error: '
                'not a volume or volume set directory: ' + pdsdir.logical_path)
          sys.exit(1)

    # Initialize the logger
    logger = pdslogger.PdsLogger(LOGNAME)
    pdsfile.Pds3File.set_log_root(args.log)

    if not args.quiet:
        logger.add_handler(pdslogger.stdout_handler)

    if args.log:
        path = os.path.join(args.log, 'pdsdependency')
        error_handler = pdslogger.error_handler(path)
        logger.add_handler(error_handler)

    # Generate a list of file paths before logging
    paths = []
    for path in args.volume:

        if not os.path.exists(path):
            print('No such file or directory: ' + path)
            sys.exit(1)

        path = os.path.abspath(path)
        pdsf = pdsfile.Pds3File.from_abspath(path)

        if pdsf.checksums_:
            print('No pdsdependency for checksum files: ' + path)
            sys.exit(1)

        if pdsf.archives_:
            print('No pdsdependency for archive files: ' + path)
            sys.exit(1)

        if pdsf.is_volset_dir:
            paths += [os.path.join(path, c) for c in pdsf.childnames]

        else:
            paths.append(os.path.abspath(path))

    # Check for valid volume IDs
    for path in paths:
        basename = os.path.basename(path)
        if not pdsfile.Pds3File.VOLNAME_REGEX_I.match(basename):
            print('Invalid volume ID: ' + path)
            sys.exit(1)

    # Only show paths starting with "holdings/"
    roots = set()
    for path in paths:
        parts = path.partition('/holdings/')
        if parts[1]:
            roots.add(parts[0] + parts[1])

    logger.add_root(*roots)

    # Loop through paths...
    args = list(sys.argv)
    args[0] = args[0].rpartition('/')[-1]
    logger.open(' '.join(args))
    try:
        for path in paths:
            pdsdir = pdsfile.Pds3File.from_abspath(path)

            # Save logs in up to two places
            logfiles = set([pdsdir.log_path_for_volume('_dependency',
                                                       dir='pdsdependency'),
                            pdsdir.log_path_for_volume('_dependency',
                                                       dir='pdsdependency',
                                                       place='parallel')])

            # Create all the handlers for this level in the logger
            local_handlers = []
            for logfile in logfiles:
                logfile = logfile.replace('/volumes/', '/')
                local_handlers.append(pdslogger.file_handler(logfile))
                logdir = os.path.split(logfile)[0]

                # These handlers are only used if they don't already exist
                error_handler = pdslogger.error_handler(logdir)
                local_handlers += [error_handler]

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                test(pdsdir, logger=logger, handlers=local_handlers)

            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                raise

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        status = 1
        raise

    finally:
        (fatal, errors, warnings, tests) = logger.close()
        if fatal or errors:
            status = 1

        if PdsDependency.COMMANDS_TO_TYPE:
            print('Steps required:')
            for cmd in PdsDependency.COMMANDS_TO_TYPE:
                print('  ', cmd)

    sys.exit(status)

if __name__ == '__main__':
    main()
