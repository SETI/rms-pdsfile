"""The tools that build and check the derived files a holdings tree carries.

A holdings tree is not only the delivered PDS3 volumes and PDS4 bundles. Beside them it
carries files derived from them: MD5 checksum files, ``.tar.gz`` archives, and the info,
link and index shelves that let the rest of this package answer questions about a file
without opening it. These tools create those derived files, validate them against what
they describe, and repair or update them.

The subpackage is laid out in three parts:

  * ``pds3/`` and ``pds4/`` hold one module per tool. Ten of them are pairs -- archives,
    checksums, index shelves, info shelves and link shelves, each in a PDS3 flavor and a
    PDS4 flavor -- and each declares a ``ToolSpec`` and a table of task functions and
    hands both to a shared driver. Eleven modules are console scripts, named in
    ``[project.scripts]``.
  * The five ``_*_common.py`` modules hold everything the two flavors of a tool would
    otherwise say twice. ``_common.py`` is the specification, the command line and one of
    the three drivers; ``_archives_common.py``, ``_shelf_common.py``,
    ``_indexshelf_common.py`` and ``_linkshelf_common.py`` hold what one family shares,
    and two of them hold the other two drivers.
  * ``pds3/`` also holds four tools that declare no specification and reach no driver,
    parsing their own command lines instead: ``crlf.py``, ``pdsdependency.py``,
    ``re_validate.py`` and ``shelf_consistency_check.py``. Two of the four still build
    their log paths through ``_common.py``, and the other two -- ``crlf.py`` and
    ``shelf_consistency_check.py`` -- take nothing from any shared module and read
    neither holdings root. ``pds3/`` holds one more Python file,
    ``linkshelf_repairs.py``, which is a table of known bad links rather than a tool.

Every tool that shares the skeleton takes the same five tasks -- initialize,
reinitialize, validate, repair and update -- one or more target paths, and the ``--log``
and ``--quiet`` options. A run writes each target's log beside the holdings tree that
target is in, and, when ``--log`` or the PDS_LOG_ROOT environment variable names a log
root, under that root as well.

This module is a namespace and defines nothing. Import a tool by its module path.
"""
