"""The maintenance tools for a PDS4 holdings tree.

Five modules live here -- ``pds4archives``, ``pds4checksums``, ``pds4indexshelf``,
``pds4infoshelf`` and ``pds4linkshelf`` -- and they are the PDS4 half of the five tool
families. Each declares a ``ToolSpec`` and a table of task functions and hands both to a
driver in ``pdsfile.holdings_maintenance``, and each is a console script named in
``[project.scripts]``.

Every one has a PDS3 twin in the sibling ``pds3`` package, and each pair keeps the same
five tasks and the same command line. For four of the five pairs a target names a
different unit on this side; the index shelf pair is the exception, because both halves
of it take a table. Each module's docstring says where its own behavior parts company
with its twin's.

There is nothing here corresponding to the four standalone tools ``pds3`` also carries.
``pds4linkshelf`` has no repair table to read either, for the reason its own docstring
gives.

This module is a namespace and defines nothing. Import a tool by its module path.
"""
