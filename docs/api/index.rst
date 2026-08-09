API reference
=============

Every module the package ships, on five pages: one for :mod:`pdsfile` itself and one for
each of its four subpackages. The entries are generated from the docstrings in the
source, and the documentation gate fails when a module is documented by no page at all,
so the reference has no missing modules. That is a claim about modules and not about
their contents: a member the source does not export, or that no directive asks for, is
absent from these pages without anything saying so.

.. toctree::
   :maxdepth: 2

   core
   holdings_maintenance
   pds3file
   pds4file
   tools
