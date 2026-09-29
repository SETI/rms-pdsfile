"""The maintenance tools for a PDS3 holdings tree, and the shell scripts beside them.

Nine Python modules live here. Five of them -- ``pdsarchives``, ``pdschecksums``,
``pdsindexshelf``, ``pdsinfoshelf`` and ``pdslinkshelf`` -- are the PDS3 half of the five
tool families, each declaring a ``ToolSpec`` and a table of task functions and handing
both to a driver in ``pdsfile.holdings_maintenance``. Each has a PDS4 twin in the
sibling ``pds4`` package, and all five are console scripts named in
``[project.scripts]``.

Three more parse their own command lines and reach no shared driver:

  * ``pdsdependency`` checks that every file a volume implies actually exists and is no
    older than the file it is derived from. It is a console script.
  * ``re_validate`` re-runs the checksum, archive, shelf and dependency validations over
    whole volumes, either on a named list or, in batch mode, on whichever volumes have
    gone longest without one.
  * ``crlf`` reports and repairs the CRLF line terminators PDS3 requires of a text file.

``crlf`` takes nothing from any other module in this package and reads neither
holdings root; the other two build their log paths through
``pdsfile.holdings_maintenance._common``. All three are run with ``python -m`` except
``pdsdependency``.

The ninth module, ``linkshelf_repairs``, is a table of known bad links in the published
volumes rather than a tool; ``pdslinkshelf`` reads it.

Twelve shell scripts sit beside these modules. They copy, sync and set up holdings trees,
and one of them, ``update_holdings_for_new_metadata.sh``, also runs five of the tools
above, by source file name rather than by console-script name. No Python in this package
imports or executes any of the twelve.

This module is a namespace and defines nothing. Import a tool by its module path.
"""
