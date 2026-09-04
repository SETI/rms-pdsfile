#!/usr/bin/env python3
################################################################################
# pdsfile/holdings_maintenance/pds3/pdsindexshelf.py
################################################################################

"""pdsindexshelf: shelve where each product's rows are in a PDS3 metadata index table.

A PDS3 metadata directory holds index tables that list one row per product, or several
rows for a product observed in more than one way. Looking a product up in such a table
means reading the whole of it, so this tool records, once, which row numbers belong to
which product, and PdsFile reads that shelf instead of the table.

**Everything this tool does is in** ``_indexshelf_common``, which holds the five tasks and
the driver, and this module and its PDS4 twin are the two shortest of the ten because
nothing about shelving an index table differs between the two PDS versions: what a row is,
how a key is made from one and how a shelf is compared against its table are all
properties of ``pdstable``. What is here is the specification that says which flavor to
be, and a ``main()`` that hands it to the driver.

Its target is a table rather than a volume, which is why ``unit`` is 'table': a
command-line path names an index table or a metadata directory, and a directory
expands to the tables inside it. That is also why it is one of the two tools on
``_indexshelf_common.run_index_main()`` rather than on either driver the other eight use.

**Six fields of this specification differ from** ``pds4indexshelf``'s **and only
four of them reach anything.** ``progname`` is this module's own name, where the
PDS4 tool carries its own; ``pdsfile_cls`` is ``Pds3File``, so every path
resolves through the PDS3 rules; ``index_ext`` is '.tab', which is the extension a
metadata directory is globbed for and a command-line file is checked against; and
``handler_factories`` is the error handler alone, where the pds4 tool adds a warning
handler as well, so a PDS3 run
writes one fewer file per log directory. The other two, ``holdings_sentinel`` and
``file_log_level``, are read nowhere along this tool's path: no code that a run of this
tool reaches ever looks at them.

``log_path_for_index`` builds the log path, from the table's own logical path, and
``log_suffix`` is empty because that method takes no suffix argument; an empty
``log_suffix`` is how a specification says so, and its driver passes a suffix only when
there is one. ``progname`` is what the tool calls itself in its ``--help`` text and what
names its subdirectory under each log root.

Every remaining field of the specification is left at its default -- there is no
``expand_target``, no ``lskip_for``, no link machinery, no extra command-line argument and
none of the three rejection messages -- because nothing this tool reaches reads any of
them.

The five shared tasks are also bound to this module's own names, each with this
specification supplied, so that one can be called directly on an index table without going
through the task table or the driver. Nothing in this package calls them that way; the
PDS3 tool that does reach another tool as a library, ``re_validate``, checks checksums,
archives, info shelves and link shelves and never index shelves.
"""

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
    """Run the tool: hand this module's specification and tasks to the index driver.

    This is the ``pdsindexshelf`` console script's entry point. It does not return: the
    driver exits with status 1 if the run logged a fatal or an error and 0 otherwise, and
    exits before opening a log for a command line that names no task or a path it rejects.

    Raises:
        SystemExit: from ``_indexshelf_common.run_index_main()``, on every path out of a
            run that is not an exception.
    """

    _indexshelf_common.run_index_main(SPEC, TASKS, sys.argv)

if __name__ == '__main__':
    main()
