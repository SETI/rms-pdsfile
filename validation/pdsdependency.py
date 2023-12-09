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
                                        'go_previews4', 'go_previews5']),
    ('.*/GO_0xxx/GO_00[12].*',      0, ['metadata', 'cumindex999',
                                        'go_previews2', 'go_previews3',
                                        'go_previews4', 'go_previews5']),
    ('.*/GO_0xxx_v1/GO_000[2-9].*', 0, ['go_previews2', 'go_previews3',
                                        'go_previews4', 'go_previews5']),
    ('.*/GO_0xxx_v1/GO_00[12]..*',  0, ['go_previews2', 'go_previews3',
                                        'go_previews4', 'go_previews5']),
    ('.*/JNCJIR_[12]xxx/.*',        0, ['metadata', 'cumindex999']),
    ('.*/JNCJNC_0xxx/.*',           0, ['metadata', 'cumindex999']),
    ('.*/HST.x_xxxx/.*',            0, ['hst', 'metadata', 'cumindex9_9999']),
    ('.*/NH..(LO|MV)_xxxx/.*',      0, ['nh', 'metadata', 'supplemental']),
    ('.*/NH..LO_xxxx/NH[^K].*',     0, ['inventory', 'rings', 'moons']),
    ('.*/NH(JU|LA)MV_xxxx/.*',      0, ['nhbrowse_vx', 'jupiter']),
    ('.*/NH(PC|PE)MV_xxxx/.*',      0, ['nhbrowse', 'pluto']),
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
    ('.*/VG_28xx/.*',               0, ['metadata']),
])

################################################################################
# Class definition
################################################################################

class PdsDependency(object):

    DEPENDENCY_SUITES = {}
    MODTIME_DICT = {}

    def __init__(self, title, glob_pattern, regex, sublist, suite=None,
                       newer=True, exceptions=[]):
        """Constructor for a PdsDependency.

        Inputs:
            title           a short description of the dependency.
            glob_pattern    a glob pattern for finding files.
            regex           regular expression to match path returned by glob.
            sublist         a list of substitution strings returning paths to
                            files that must exist.
            suite           optional name of a test suite to which this
                            dependency belongs.
            newer           True if the file file must be newer; False to
                            suppress a check of the modification date.
            exceptions      a list of zero or more regular expressions. If a
                            file path matches one of these patterns, then it
                            will not trigger a test.
        """

        self.glob_pattern = glob_pattern

        if type(regex) == str:
            self.regex = re.compile('^' + regex + '$', re.I)
        else:
            self.regex = regex

        self.regex_pattern = self.regex.pattern

        if type(sublist) == str:
            self.sublist = [sublist]
        else:
            self.sublist = list(sublist)

        self.title = title
        self.suite = suite
        self.newer = newer

        if suite is not None:
            if suite not in PdsDependency.DEPENDENCY_SUITES:
                PdsDependency.DEPENDENCY_SUITES[suite] = []

            PdsDependency.DEPENDENCY_SUITES[suite].append(self)

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

            modtime = max(modtime, PdsDependency.get_modtime(absfile, logger))

        PdsDependency.MODTIME_DICT[abspath] = modtime
        return modtime

    def test1(self, dirpath, check_newer=True, limit=200, logger=None):
        """Perform one test and log the results."""

        dirpath = os.path.abspath(dirpath)
        pdsdir = pdsfile.PdsFile.from_abspath(dirpath)
        lskip_ = len(pdsdir.root_)

        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.replace_root([pdsdir.root_, pdsdir.disk_])

        # Remove "Newer" at beginning of title if check_newer is False
        if not check_newer and self.title.startswith('Newer '):
            logger.open(self.title[6:].capitalize(), dirpath)
        else:
            logger.open(self.title, dirpath)

        try:
            pattern = pdsdir.root_ + self.glob_pattern

            pattern = pattern.replace('$', pdsdir.volset_[:-1], 1)
            if '$' in pattern:
                pattern = pattern.replace('$', pdsdir.volname, 1)

            abspaths = glob.glob(pattern)

            if len(abspaths) == 0:
                logger.info('No files found')

            else:
              for sub in self.sublist:
                logger.open('%s >> %s' % (self.regex_pattern[1:-1], sub),
                            limits={'normal': limit})
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
                            logger.error('Invalid file path', absreq)
                            continue

                        if not os.path.exists(absreq):
                            logger.error('Missing file', absreq)
                            continue

                        if self.newer and check_newer:
                            source_modtime = PdsDependency.get_modtime(abspath,
                                                                       logger)
                            requirement_modtime = \
                                            PdsDependency.get_modtime(absreq,
                                                                      logger)

                            if requirement_modtime < source_modtime:
                                logger.error('File out of date', absreq)
                                continue

                        logger.normal('Confirmed', absreq)

                except (Exception, KeyboardInterrupt) as e:
                    logger.exception(e)
                    raise

                finally:
                    logger.close()

        except (Exception, KeyboardInterrupt) as e:
            logger.exception(e)
            raise

        finally:
            (fatal, errors, warnings, tests) = logger.close()

        return (fatal, errors, warnings, tests)

    @staticmethod
    def test_suite(key, dirpath, check_newer=True, limit=200, logger=None):

        dirpath = os.path.abspath(dirpath)
        pdsdir = pdsfile.PdsFile.from_abspath(dirpath)

        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.replace_root(pdsdir.root_)
        logger.open('Dependency test suite "%s"' % key, dirpath)

        try:
            for dep in PdsDependency.DEPENDENCY_SUITES[key]:
                dep.test1(dirpath, check_newer, limit=limit, logger=logger)

        except (Exception, KeyboardInterrupt) as e:
            logger.exception(e)
            raise

        finally:
            (fatal, errors, warnings, tests) = logger.close()

        return (fatal, errors, warnings, tests)

################################################################################
# General test suite
################################################################################

for thing in pdsfile.VOLTYPES:

    if thing == 'volumes':
        thing_ = ''
    else:
        thing_ = '_' + thing

    Thing = thing.capitalize()

    _ = PdsDependency(
        'Newer archives and checksums for %s'       % thing,
        '%s/$/$'                                    % thing,
        r'%s/(.*?)/(.*)'                            % thing,
        [r'archives-%s/\1/\2%s.tar.gz'              % (thing, thing_),
         r'checksums-%s/\1/\2%s_md5.txt'            % (thing, thing_)],
        suite='general', newer=True,
    )

    _ = PdsDependency(
        'Newer checksum files for archives-%s'      % thing,
        'archives-%s/$/$*'                          % thing,
        r'archives-%s/(.*?)/(.*)%s.tar.gz'          % (thing, thing_),
        r'checksums-archives-%s/\1%s_md5.txt'       % (thing, thing_),
        suite='general', newer=True,
    )

    _ = PdsDependency(
        'Newer info shelf files for %s'             % thing,
        'checksums-%s/$/$%s_md5.txt'                % (thing, thing_),
        r'checksums-%s/(.*?)/(.*)%s_md5.txt'        % (thing, thing_),
        [r'_infoshelf-%s/\1/\2_info.pickle'        % thing,
         r'_infoshelf-%s/\1/\2_info.py'            % thing],
        suite='general', newer=True,
    )

    _ = PdsDependency(
        'Newer info shelf files for archives-%s'    % thing,
        'checksums-archives-%s/$%s_md5.txt'         % (thing, thing_),
        r'checksums-archives-%s/(.*)%s_md5.txt'     % (thing, thing_),
        [r'_infoshelf-archives-%s/\1_info.pickle'  % thing,
         r'_infoshelf-archives-%s/\1_info.py'      % thing],
        suite='general', newer=True,
    )

for thing in ['volumes', 'metadata', 'calibrated']:

    _ = PdsDependency(
        'Newer link shelf files for %s'             % thing,
        '%s/$/$'                                    % thing,
        r'%s/(.*?)/(.*)'                            % thing,
        [r'_linkshelf-%s/\1/\2_links.pickle'       % thing,
         r'_linkshelf-%s/\1/\2_links.py'           % thing],
        suite='general', newer=True,
    )

################################################################################
# Metadata tests
################################################################################

# General metadata including *_index.tab
_ = PdsDependency(
    'Metadata index table for each volume',
    'volumes/$/$',
    r'volumes/([^/]+?)(|_v[0-9.]+)/(.*?)',
    r'metadata/\1/\3/\3_index.tab',
    suite='metadata', newer=False,
)

_ = PdsDependency(
    'Label for every metadata table or CSV',
    'metadata/$*/$/*.(tab|csv)',
    r'metadata/(.*)\....',
    r'metadata/\1.lbl',
    suite='metadata', newer=False,
)

_ = PdsDependency(
    'Newer index shelf for every metadata table',
    'metadata/$*/$/*.tab',
    r'metadata/(.*)\.tab',
    [r'_indexshelf-metadata/\1.pickle',
     r'_indexshelf-metadata/\1.py'],
    suite='metadata', newer=True,
    exceptions=[r'.*_inventory.tab',
                r'.*GO_0xxx_v1.*']
)

# More metadata suites
for (name, suffix) in [('supplemental'  , 'supplemental_index.tab'),
                       ('inventory'     , 'inventory.csv'),
                       ('jupiter'       , 'jupiter_summary.tab'),
                       ('saturn'        , 'saturn_summary.tab'),
                       ('uranus'        , 'uranus_summary.tab'),
                       ('neptune'       , 'neptune_summary.tab'),
                       ('pluto'         , 'pluto_summary.tab'),
                       ('pluto'         , 'charon_summary.tab'),
                       ('rings'         , 'ring_summary.tab'),
                       ('moons'         , 'moon_summary.tab'),
                       ('raw_image'     , 'raw_image_index.tab'),
                       ('profile'       , 'profile_index.tab'),
                       ('obsindex'      , 'obsindex.tab')]:

    _ = PdsDependency(
        name.capitalize() + ' metadata required',
        'volumes/$/$',
        r'volumes/([^/]+?)(|_v[0-9.]+)/(.*?)',
        r'metadata/\1/\3/\3_' + suffix,
        suite=name, newer=False,
    )

################################################################################
# Cumulative index tests where the suffix is "99", "999", or "9_9999"
################################################################################

for nines in ('99', '999', '9_9999'):

    dots = nines.replace('9', '.')
    name = 'cumindex' + nines

    _ = PdsDependency(
        'Cumulative version of every metadata table',
        'metadata/$*/$/*.(tab|csv)',
        r'metadata/(.*?)/(.*)' + dots + r'/(.*)' + dots + r'(.*)\.(tab|csv)',
        [r'metadata/\1/\g<2>' + nines + r'/\g<3>' + nines + r'\4.\5',
         r'metadata/\1/\g<2>' + nines + r'/\g<3>' + nines + r'\4.lbl'],
        suite=name, newer=False,
    )

    _ = PdsDependency(
        'Newer archives and checksums for cumulative metadata',
        'metadata/$*/*' + nines,
        r'metadata/(.*?)/(.*)',
        [r'archives-metadata/\1/\2_metadata.tar.gz',
         r'checksums-metadata/\1/\2_metadata_md5.txt'],
        suite=name, newer=True,
    )

    _ = PdsDependency(
        'Newer checksums for cumulative archives-metadata',
        'archives-metadata/$*/*' + nines + '_metadata.tar.gz',
        r'archives-metadata/(.*?)/.*_metadata.tar.gz',
        r'checksums-archives-metadata/\1_metadata_md5.txt',
        suite=name, newer=True,
    )

    _ = PdsDependency(
        'Newer info shelf files for cumulative metadata',
        'checksums-metadata/$*/*' + nines + '_metadata_md5.txt',
        r'checksums-metadata/(.*?)/(.*)_metadata_md5.txt',
        [r'_infoshelf-metadata/\1/\2_info.pickle',
         r'_infoshelf-metadata/\1/\2_info.py'],
        suite=name, newer=True,
    )

    _ = PdsDependency(
        'Newer info shelf files for cumulative archives-metadata',
        'checksums-archives-metadata/$*_metadata_md5.txt',
        r'checksums-archives-metadata/(.*)_metadata_md5.txt',
        [r'_infoshelf-archives-metadata/\1_info.pickle',
         r'_infoshelf-archives-metadata/\1_info.py'],
        suite=name, newer=True,
    )

    _ = PdsDependency(
        'Newer link shelf files for cumulative metadata',
        'metadata/$/*' + nines,
        r'metadata/(.*?)/(.*)',
        [r'_linkshelf-metadata/\1/\2_links.pickle',
         r'_linkshelf-metadata/\1/\2_links.py'],
        suite=name, newer=True,
    )

    _ = PdsDependency(
        'Newer index shelf files for cumulative metadata',
        'metadata/$/*' + nines + '/*.tab',
        r'metadata/(.*)\.tab',
        [r'_indexshelf-metadata/\1.pickle',
         r'_indexshelf-metadata/\1.py'],
        suite=name, newer=True,
        exceptions=[r'.*GO_0xxx_v1.*']
    )

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
    suite='cocirs01', newer=True,
)

# For COCIRS_5xxx and COCIRS_6xxx
_ = PdsDependency(
    'Diagrams for every interferogram file',
    'volumes/$/$/BROWSE/*/*.PNG',
    r'volumes/(.*)\.PNG',
    [r'diagrams/\1_thumb.jpg',
     r'diagrams/\1_small.jpg',
     r'diagrams/\1_med.jpg',
     r'diagrams/\1_full.jpg'],
    suite='cocirs56', newer=False,
)

# For COISS_1xxx and COISS_2xxx
_ = PdsDependency(
    'Previews and calibrated versions of every COISS image file',
    'volumes/$/$/data/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.png',
     r'calibrated/\1_CALIB.IMG'],
    suite='coiss12', newer=False,
)

# For COISS_3xxx
_ = PdsDependency(
    'Previews of every COISS derived map image',
    'volumes/$/$/data/images/*.IMG',
    r'volumes/(.*?)/data/images/(.*)\.IMG',
    [r'previews/\1/data/images/\2_thumb.jpg',
     r'previews/\1/data/images/\2_small.jpg',
     r'previews/\1/data/images/\2_med.jpg',
     r'previews/\1/data/images/\2_full.jpg'],
    suite='coiss3', newer=True,
)

_ = PdsDependency(
    'Previews of every COISS derived map PDF',
    'volumes/$/$/data/maps/*.PDF',
    r'volumes/(.*?)/data/maps/(.*)\.PDF',
    [r'previews/\1/data/maps/\2_thumb.png',
     r'previews/\1/data/maps/\2_small.png',
     r'previews/\1/data/maps/\2_med.png',
     r'previews/\1/data/maps/\2_full.png'],
    suite='coiss3', newer=True,
)

# For COUVIS_0xxx
_ = PdsDependency(
    'Previews of every COUVIS data file',
    'volumes/$/$/DATA/*/*.DAT',
    r'volumes/COUVIS_0xxx(|_v[\.0-9]+)/(.*)\.DAT',
    [r'previews/COUVIS_0xxx/\2_thumb.png',
     r'previews/COUVIS_0xxx/\2_small.png',
     r'previews/COUVIS_0xxx/\2_med.png',
     r'previews/COUVIS_0xxx/\2_full.png'],
    suite='couvis', newer=False,
)

# For COVIMS_0xxx
_ = PdsDependency(
    'Previews and calibrated versions of every COVIMS cube',
    'volumes/$/$/data/*/*.qub',
    r'volumes/(.*)\.qub',
    [r'previews/\1_thumb.png',
     r'previews/\1_small.png',
     r'previews/\1_med.png',
     r'previews/\1_full.png'],
    suite='covims', newer=False,
)

# For CORSS_8xxx
_ = PdsDependency(
    'Previews and diagrams for every CORSS_8xxx data directory',
    'volumes/$/$/data/Rev*/Rev*/*',
    r'volumes/CORSS_8xxx[^/]*/(CORSS_8001/data/Rev.../Rev.....?)/(Rev.....?)_(RSS_...._..._..._.)',
    [r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_thumb.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_small.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_med.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_full.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_thumb.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_small.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_med.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_full.jpg',
     r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg',
     r'diagrams/CORSS_8xxx/\1_\3_thumb.jpg',
     r'diagrams/CORSS_8xxx/\1_\3_small.jpg',
     r'diagrams/CORSS_8xxx/\1_\3_med.jpg',
     r'diagrams/CORSS_8xxx/\1_\3_full.jpg'],
    suite='corss_8xxx', newer=False,
)

_ = PdsDependency(
    'Previews of every CORSS_8xxx browse PDF',
    'volumes/$/$/browse/*.pdf',
    r'volumes/CORSS_8xxx[^/]*/(.*)\.pdf',
    [r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg'],
    suite='corss_8xxx', newer=False,
)
_ = PdsDependency(
    'Previews of every CORSS_8xxx Rev PDF',
    'volumes/$/$/data/Rev*/*.pdf',
    r'volumes/CORSS_8xxx[^/]*/(.*)\.pdf',
    [r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg'],
    suite='corss_8xxx', newer=False,
)

_ = PdsDependency(
    'Previews of every CORSS_8xxx data PDF',
    'volumes/$/$/data/Rev*/Rev*/Rev*/*.pdf',
    r'volumes/CORSS_8xxx[^/]*/(.*)\.pdf',
    [r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg'],
    suite='corss_8xxx', newer=False,
)

# For COUVIS_8xxx
_ = PdsDependency(
    'Previews and diagrams of every COUVIS_8xxx profile',
    'volumes/$/$/data/*_TAU01KM.TAB',
    r'volumes/COUVIS_8xxx[^/]*/(.*)_TAU01KM\.TAB',
    [r'previews/COUVIS_8xxx/\1_thumb.jpg',
     r'previews/COUVIS_8xxx/\1_small.jpg',
     r'previews/COUVIS_8xxx/\1_med.jpg',
     r'previews/COUVIS_8xxx/\1_full.jpg',
     r'diagrams/COUVIS_8xxx/\1_thumb.jpg',
     r'diagrams/COUVIS_8xxx/\1_small.jpg',
     r'diagrams/COUVIS_8xxx/\1_med.jpg',
     r'diagrams/COUVIS_8xxx/\1_full.jpg'],
    suite='couvis_8xxx', newer=False,
    exceptions=['.*2005_139_PSICEN_E.*',
                '.*2005_139_THEHYA_E.*',
                '.*2007_038_SAO205839_I.*',
                '.*2010_148_LAMAQL_E.*']
)

# For COVIMS_8xxx
_ = PdsDependency(
    'Previews and diagrams of every COVIMS_8xxx profile',
    'volumes/$/$/data/*_TAU01KM.TAB',
    r'volumes/COVIMS_8xxx[^/]*/(.*)_TAU01KM\.TAB',
    [r'previews/COVIMS_8xxx/\1_thumb.jpg',
     r'previews/COVIMS_8xxx/\1_small.jpg',
     r'previews/COVIMS_8xxx/\1_med.jpg',
     r'previews/COVIMS_8xxx/\1_full.jpg',
     r'diagrams/COVIMS_8xxx/\1_thumb.jpg',
     r'diagrams/COVIMS_8xxx/\1_small.jpg',
     r'diagrams/COVIMS_8xxx/\1_med.jpg',
     r'diagrams/COVIMS_8xxx/\1_full.jpg'],
    suite='covims_8xxx', newer=False,
)

_ = PdsDependency(
    'Previews of every COVIMS_8xxx PDF',
    'volumes/$/$/browse/*.PDF',
    r'volumes/COVIMS_8xxx[^/]*/(.*)\.PDF',
    [r'previews/COVIMS_8xxx/\1_thumb.jpg',
     r'previews/COVIMS_8xxx/\1_small.jpg',
     r'previews/COVIMS_8xxx/\1_med.jpg',
     r'previews/COVIMS_8xxx/\1_full.jpg'],
    suite='covims_8xxx', newer=False,
)

# For EBROCC_xxxx
_ = PdsDependency(
    'Previews of every EBROCC browse PDF',
    'volumes/$/$/BROWSE/*.PDF',
    r'volumes/EBROCC_xxxx[^/]*/(.*)\.PDF',
    [r'previews/EBROCC_xxxx/\1_thumb.jpg',
     r'previews/EBROCC_xxxx/\1_small.jpg',
     r'previews/EBROCC_xxxx/\1_med.jpg',
     r'previews/EBROCC_xxxx/\1_full.jpg'],
    suite='ebrocc_xxxx', newer=False,
)
_ = PdsDependency(
    'Previews of every EBROCC profile',
    'volumes/$/$/data/*/*.TAB',
    r'volumes/EBROCC_xxxx[^/]*/(.*)\.TAB',
    [r'previews/EBROCC_xxxx/\1_thumb.jpg',
     r'previews/EBROCC_xxxx/\1_small.jpg',
     r'previews/EBROCC_xxxx/\1_med.jpg',
     r'previews/EBROCC_xxxx/\1_full.jpg'],
    suite='ebrocc_xxxx', newer=False,
)

# For GO_xxxx
_ = PdsDependency(
    'Previews of every GO image file, depth 2',
    'volumes/$/$/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    suite='go_previews2', newer=True,
)

_ = PdsDependency(
    'Previews of every GO image file, depth 3',
    'volumes/$/$/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    suite='go_previews3', newer=True,
)

_ = PdsDependency(
    'Previews of every GO image file, depth 4',
    'volumes/$/$/*/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    suite='go_previews4', newer=True,
)

_ = PdsDependency(
    'Previews of every GO image file, depth 5',
    'volumes/$/$/*/*/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    suite='go_previews5', newer=True,
)

# For HST*x_xxxx
_ = PdsDependency(
    'Previews of every HST image label',
    'volumes/$/$/data/*/*.LBL',
    r'volumes/(HST.._....)(|_v[0-9.]+)/(HST.*)\.LBL',
    [r'previews/\1/\3_thumb.jpg',
     r'previews/\1/\3_small.jpg',
     r'previews/\1/\3_med.jpg',
     r'previews/\1/\3_full.jpg'],
    suite='hst', newer=False,
)

# For NHxxLO_xxxx and NHxxMV_xxxx browse, stripping version number
_ = PdsDependency(
    'Previews of every NH image file',
    'volumes/$/$/data/*/*.fit',
    r'volumes/(NHxx.._....)(|_v[0-9.]+)/(NH.*?)(|_[0-9]+).fit',
    [r'previews/\1/\3_thumb.jpg',
     r'previews/\1/\3_small.jpg',
     r'previews/\1/\3_med.jpg',
     r'previews/\1/\3_full.jpg'],
    suite='nhbrowse', newer=False,
)

# For NHxxLO_xxxx and NHxxMV_xxxx browse, without stripping version number
_ = PdsDependency(
    'Previews of every NH image file',
    'volumes/$/$/data/*/*.fit',
    r'volumes/(NHxx.._....)(|_v[0-9.]+)/(NH.*?).fit',
    [r'previews/\1/\3_thumb.jpg',
     r'previews/\1/\3_small.jpg',
     r'previews/\1/\3_med.jpg',
     r'previews/\1/\3_full.jpg'],
    suite='nhbrowse_vx', newer=False,
)

_ = PdsDependency(
    'Newer supplemental index for every NH volume',
    'volumes/$/$/data/*/*.lbl',
    r'volumes/(NHxx.._....)(|_v[0-9.]+)/(NH...._.00)(.)/.*\.lbl',
    r'metadata/\1/\g<3>1/\g<3>1_supplemental_index.tab',
    suite='nh', newer=True,
)

# For VGISS_[5678]xxx
_ = PdsDependency(
    'Previews of every VGISS image file',
    'volumes/$/$/data/*/*RAW.IMG',
    r'volumes/(.*)_RAW\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    suite='vgiss', newer=True,
)

################################################################################
################################################################################

def test(pdsdir, logger=None, check_newer=True):
    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    path = pdsdir.abspath
    for suite in TESTS.all(path):
        _ = PdsDependency.test_suite(suite, path, check_newer=check_newer,
                                                  logger=logger)

################################################################################
################################################################################

if __name__ == '__main__':

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
        pdsdir = pdsfile.PdsFile.from_abspath(path)
        if not pdsdir.is_volume_dir and not pdsdir.is_volset_dir:
          print('pdsdependency error: ' + \
                'not a volume or volume set directory: ' + pdsdir.logical_path)
          sys.exit(1)

        if pdsdir.category_ != 'volumes/':
          print('pdsdependency error: ' + \
                'not a volume or volume set directory: ' + pdsdir.logical_path)
          sys.exit(1)

    # Initialize the logger
    logger = pdslogger.PdsLogger(LOGNAME)
    pdsfile.PdsFile.set_log_root(args.log)

    if not args.quiet:
        logger.add_handler(pdslogger.stdout_handler)

    if args.log:
        path = os.path.join(args.log, 'pdsdependency')
        warning_handler = pdslogger.warning_handler(path)
        logger.add_handler(warning_handler)

        error_handler = pdslogger.error_handler(path)
        logger.add_handler(error_handler)

    # Generate a list of file paths before logging
    paths = []
    for path in args.volume:

        if not os.path.exists(path):
            print('No such file or directory: ' + path)
            sys.exit(1)

        path = os.path.abspath(path)
        pdsf = pdsfile.PdsFile.from_abspath(path)

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

    # Loop through paths...
    logger.open(' '.join(sys.argv))
    try:
        for path in paths:

            pdsdir = pdsfile.PdsFile.from_abspath(path)

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
                warning_handler = pdslogger.warning_handler(logdir)
                error_handler = pdslogger.error_handler(logdir)
                local_handlers += [warning_handler, error_handler]

            # Open the next level of the log
            if len(paths) > 1:
                logger.blankline()

            logger.open('Dependency tests', path, handler=local_handlers)

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                test(pdsdir, logger=logger)

            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                raise

            finally:
                _ = logger.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        status = 1
        raise

    finally:
        (fatal, errors, warnings, tests) = logger.close()
        if fatal or errors: status = 1

    sys.exit(status)
