shelf_consistency_check
=======================

A shelf file summarizes a directory or an index table so that the rest of the package can
answer questions about it without opening it. When the thing a shelf describes is deleted
or renamed, nothing deletes the shelf, and the stale file goes on being loaded.
``shelf_consistency_check`` walks one or more directory trees, works out what each shelf
file it finds would have to describe, and reports the ones for which that no longer
exists.

It is not a console script. Run it as a module:

.. code-block:: text

   python -m pdsfile.holdings_maintenance.pds3.shelf_consistency_check [--verbose] [<shelf_root> ...]

**It reads no holdings root.** The trees to walk are the ones named on the command line,
and every conclusion is drawn from the path strings alone. Nothing is opened.

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Option
     - Meaning
   * - ``--verbose``
     - Also print the holdings path that each shelf maps to.

There is no short form, and **abbreviations are rejected**. The option may appear
anywhere among the roots.

.. warning::

   **The layout this program looks for is not the layout the holdings trees in this
   package use.**

   A directory is examined only if ``shelves`` appears anywhere in its path -- as a
   substring of the whole path string, so ``myshelves-backup`` matches as surely as
   ``shelves`` does -- and only if the first path component after ``shelves/`` is
   ``info``, ``links`` or ``index``. A holdings tree keeps its shelves in
   ``_infoshelf-volumes/``, ``_linkshelf-volumes/`` and ``_indexshelf-metadata/``, which
   contain no such substring anywhere.

   So a run over a holdings tree walks every directory in it, examines nothing, and
   reports a clean result:

   .. code-block:: console

      $ python -m pdsfile.holdings_maintenance.pds3.shelf_consistency_check "$PDS3_HOLDINGS_DIR"
      Tests performed: 0
      Errors found: 0

   **That is a clean report about an empty search, not a clean report about the
   shelves.** ``Tests performed: 0`` is the line to read.

What it does where the layout matches
-------------------------------------

Given a tree that does hold a ``shelves/`` directory, the counterpart of a shelf is
derived by textual substitution:

* ``shelves/<kind>`` is replaced by ``holdings`` wherever it occurs in the shelf's path,
  and the extension is dropped;
* for ``index``, what must then exist is that path plus ``.lbl``, the label of the index
  table;
* for ``info`` and ``links``, everything after the last underscore goes too -- the
  ``_info`` or ``_links`` on a shelf named the way these programs name one -- and what
  must exist is the resulting path, as a file or a directory alike, since only existence
  is asked.

A shelf path with no underscore anywhere loses its whole path to that last rule, leaving
the empty string, which exists nowhere, so such a shelf is always reported.

Three things are errors:

* a directory under ``shelves/`` whose first component is none of ``info``, ``links`` or
  ``index``;
* a file that is neither a ``.py`` nor a ``.pickle``;
* a shelf whose counterpart is missing.

A ``.DS_Store`` is counted as examined and passed over without being an error.

A worked example
----------------

A tree holding one info shelf under ``shelves/info/`` whose counterpart does not exist,
plus an unrelated ``holdings/`` directory:

.. code-block:: console

   $ python -m pdsfile.holdings_maintenance.pds3.shelf_consistency_check "$PDS3_HOLDINGS_DIR/../shelves-demo"
   *** Not a valid shelves directory: $PDS3_HOLDINGS_DIR/../shelves-demo
   *** Extraneous shelf: $PDS3_HOLDINGS_DIR/../shelves-demo/shelves/info/COUVIS_0xxx/COUVIS_0001_info.pickle
   *** Not a valid shelves directory: $PDS3_HOLDINGS_DIR/../shelves-demo/holdings
   *** Not a valid shelves directory: $PDS3_HOLDINGS_DIR/../shelves-demo/holdings/COUVIS_0xxx
   Tests performed: 4
   Errors found: 4

Three of those four errors are not about shelves at all. Naming a root whose own path
contains ``shelves`` makes the whole tree eligible, and every directory in it whose
first component after ``shelves/`` is unrecognized is reported -- one error per
directory, not one per tree, because the walk is not pruned at the first. Directories
whose own name ends in ``shelves`` are skipped without comment.

The two counts
--------------

Both lines are printed always, whatever was found and even when no root was named at all.

``Tests performed`` counts files -- one per file inside a directory of a recognized kind
-- plus one for each directory of an unrecognized kind. Directories of a recognized kind
are not counted, so a ``shelves/info`` subtree of four directories holding no files
reports zero. Both counts run across every root of the run rather than being reset per
root.

A root that does not exist reports nothing and contributes nothing to either count: the
walk yields nothing for it and raises nothing, so a typo in a path looks exactly like a
clean tree.

Exit status
-----------

1 if any error was reported, 0 otherwise. 2 for a command line :mod:`argparse` cannot
classify. A run naming no root at all is accepted, examines nothing and exits 0.
