API reference
=============

Every module the package ships, one page per top-level package and subpackage. The
entries are generated from the docstrings in the source, and the documentation gate
fails when a module has no entry, so no module is missing from this page set. That is a
claim about modules and not about their contents: a member the source does not export,
or that no directive asks for, is absent from these pages without anything saying so.

.. toctree::
   :maxdepth: 2

   core
   holdings_maintenance
   pds3file
   pds4file
   tools
