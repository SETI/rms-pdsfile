##########################################################################################
# tests/holdings_maintenance/__init__.py
#
# Tests for the holdings-maintenance CLI tools (issue #82).
#
# Every tool is driven as a subprocess against a disposable copy of an explicitly
# declared subset of real holdings (see subsets.py and conftest.py). Subprocesses
# are not a convenience: PdsFile.CACHE is a class-level cache keyed by *logical*
# path and the test session preloads the real holdings tree, so an in-process
# call would resolve a temporary-tree path back to the real tree.
#
# test_re_validate.py is the exception: it runs in-process and needs no holdings at
# all. Most of what it covers is pure over text, paths and an argparse namespace;
# where it drives a function that builds a PdsFile or writes Pds3File class state,
# it replaces the class with a stub first. Its own header names those five
# functions and says what forgetting the stub would cost.
#
# Deliberately NOT covered here:
#
#   * the five sibling tools re_validate.validate_one_volume() calls against a real
#     volume -- each has its own module here -- and send_email(), which opens a
#     socket. The message that one builds is covered through format_email().
#   * holdings_maintenance/pds3/*.sh -- the sync/setup shell scripts are
#     document-only; they are covered by prose in the user guide, not by tests.
##########################################################################################
