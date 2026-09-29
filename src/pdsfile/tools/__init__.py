"""Command-line utilities that inspect what a PdsFile object reports.

These are not holdings-maintenance tools: nothing here creates, validates or repairs a
file in the holdings tree. They exist to show what the package itself computes for a
path that is already there.

``show_opus_products.py`` is the only one. It instantiates a Pds3File or a Pds4File for
each path it is given and prints the products OPUS would associate with it, in a table,
through pprint, or as the raw dictionary.

This module is a namespace and defines nothing. Import a tool by its module path.
"""
