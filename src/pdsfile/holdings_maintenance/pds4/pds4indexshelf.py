#!/usr/bin/env python3
################################################################################
# pds4indexshelf.py library and main program
#
# Syntax:
#   pds4indexshelf.py --task index_path.csv [index_path.csv ...]
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
#
# progname is 'pdsindexshelf', not this module's name: the tool announces itself,
# names its log directory and titles its --help output that way, and every one of
# those is part of what a run looks like today.
################################################################################

SPEC = _common.ToolSpec(
    progname='pdsindexshelf',
    logname=LOGNAME,
    pdsfile_cls=pdsfile.Pds4File,
    unit='table',
    holdings_sentinel='/pds4-holdings/',
    index_ext='.csv',
    file_log_level='normal',
    description=_indexshelf_common.INDEXSHELF_DESCRIPTION,
    task_help=_indexshelf_common.INDEXSHELF_TASK_HELP,
    positional_help=_indexshelf_common.INDEXSHELF_POSITIONAL_HELP,
    log_suffix='',
    handler_factories=(pdslogger.warning_handler, pdslogger.error_handler))

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
