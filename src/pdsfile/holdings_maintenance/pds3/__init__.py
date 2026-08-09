"""The maintenance tools for a PDS3 holdings tree, and the shell scripts beside them.

Ten Python modules live here. Five of them -- ``pdsarchives``, ``pdschecksums``,
``pdsindexshelf``, ``pdsinfoshelf`` and ``pdslinkshelf`` -- are the PDS3 half of the five
tool families, each declaring a ``ToolSpec`` and a table of task functions and handing
both to a driver in ``pdsfile.holdings_maintenance``. Each has a PDS4 twin in the
sibling ``pds4`` package, and all five are console scripts named in
``[project.scripts]``.

Four more parse their own command lines and reach no shared driver:

  * ``pdsdependency`` checks that every file a volume implies actually exists and is no
    older than the file it is derived from. It is a console script.
  * ``re_validate`` re-runs the checksum, archive, shelf and dependency validations over
    whole volumes, either on a named list or, in batch mode, on whichever volumes have
    gone longest without one.
  * ``crlf`` reports and repairs the CRLF line terminators PDS3 requires of a text file.
  * ``shelf_consistency_check`` reports shelf files with nothing in holdings to describe.

The last two take nothing from any other module in this package and read neither
holdings root; the first two build their log paths through
``pdsfile.holdings_maintenance._common``. All four are run with ``python -m`` except
``pdsdependency``.

The tenth module, ``linkshelf_repairs``, is a table of known bad links in the published
volumes rather than a tool; ``pdslinkshelf`` reads it.

The shell scripts here copy, sync and set up holdings trees. They invoke the tools above
as commands rather than importing them, so nothing in Python reaches them.

This module is a namespace and defines nothing. Import a tool by its module path.
"""
