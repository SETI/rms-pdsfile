##########################################################################################
# tests/holdings_maintenance/__init__.py
#
# Tests for the holdings-maintenance CLI tools (issue #82).
#
# Which tools are driven how, and why:
#
#   * The eleven console-script tools, and show_opus_products, are driven as
#     subprocesses against a disposable copy of an explicitly declared subset of
#     real holdings (see subsets.py and conftest.py). Subprocesses are not a
#     convenience: PdsFile.CACHE is a class-level cache keyed by *logical* path and
#     the test session preloads the real holdings tree, so an in-process call would
#     resolve a temporary-tree path back to the real tree. show_opus_products also
#     calls Pds3File.use_shelves_only(True) and preloads both roots itself, which
#     in-process would outlive the test and change how every later test resolves.
#   * crlf and shelf_consistency_check are driven in-process, through
#     support.run_tool_in_process(). They import no PdsFile class and read neither
#     holdings root -- they read or walk exactly the paths on their command line --
#     so the hazard above cannot arise. support.HOLDINGS_FREE_TOOLS is the list,
#     and both helpers assert against it. Each still keeps a subprocess test,
#     through support.run_tool_without_holdings() -- one for
#     shelf_consistency_check and two for crlf -- because only a subprocess can
#     show that `python -m <module>` reaches main(), that the process exit code is
#     what main() returned, and what an uncaught exception leaves the process at.
#   * test_re_validate.py runs in-process and needs no holdings at all. Most of
#     what it covers is pure over text, paths and an argparse namespace; where it
#     drives a function that builds a PdsFile or writes Pds3File class state, it
#     replaces the class with a stub first. Its own header names those five
#     functions and says what forgetting the stub would cost.
#
# Deliberately NOT covered here:
#
#   * the five sibling tools re_validate.validate_one_volume() calls against a real
#     volume -- each has its own module here -- and send_email(), which opens a
#     socket. The message that one builds is covered through format_email().
#   * holdings_maintenance/pds3/*.sh -- the sync/setup shell scripts are
#     document-only; they are covered by prose in the user guide, not by tests.
#     The exception is update_holdings_for_new_metadata.sh, whose delete-and-rebuild
#     bookkeeping is pinned by test_update_holdings_script.py, which parses the
#     script's text and runs nothing.
##########################################################################################
