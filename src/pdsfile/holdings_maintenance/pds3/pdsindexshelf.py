#!/usr/bin/env python3
################################################################################
# pdsindexshelf.py library and main program
#
# Syntax:
#   pdsindexshelf.py --task index_path.tab [index_path.tab ...]
#
# Enter the --help option to see more information.
################################################################################

import sys

import pdslogger

import pdsfile
from pdsfile.holdings_maintenance import _common, _indexshelf_common

LOGNAME = _indexshelf_common.INDEXSHELF_LOGNAME

################################################################################
# Executable program
################################################################################

SPEC = _common.ToolSpec(
    progname='pdsindexshelf',
    logname=LOGNAME,
    pdsfile_cls=pdsfile.Pds3File,
    unit='table',
    holdings_sentinel='/holdings/',
    index_ext='.tab',
    file_log_level='info',
    description=_indexshelf_common.INDEXSHELF_DESCRIPTION,
    task_help=_indexshelf_common.INDEXSHELF_TASK_HELP,
    positional_help=_indexshelf_common.INDEXSHELF_POSITIONAL_HELP,
    log_path_method='log_path_for_index',
    log_suffix='',
    handler_factories=(pdslogger.error_handler,))

TASKS = _indexshelf_common.index_tasks(SPEC)

# The task functions, under the names this module carries them as a library.
# Each is the shared task with this tool's spec bound in.
initialize = TASKS['initialize']
reinitialize = TASKS['reinitialize']
validate = TASKS['validate']
repair = TASKS['repair']
update = TASKS['update']

def main():
    _indexshelf_common.run_index_main(SPEC, TASKS, sys.argv)

if __name__ == '__main__':
    main()
