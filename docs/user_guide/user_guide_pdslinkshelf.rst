pdslinkshelf
============

``pdslinkshelf`` finds the links inside a PDS3 volume's files and records them. For each
file the shelf holds either the list of files that file points at, or -- for a data file
-- the label that describes it, so the package can answer "what goes with this file"
without opening anything.

The command line is the shared one, described in
:doc:`user_guide_maintenance_tools`, with no options of its own.

.. code-block:: text

   pdslinkshelf <task> <volume> [<volume> ...] [--log LOG] [--quiet]

What it writes
--------------

Two files per volume, in the ``_linkshelf-`` parallel of whatever category the target
came from. In practice a holdings tree carries ``_linkshelf-volumes/``,
``_linkshelf-calibrated/`` and ``_linkshelf-metadata/``, because those are the three
categories :doc:`user_guide_re_validate` re-validates and the three
``setup_new_holdings.sh`` creates. Nothing in this program restricts it to them: pointed
at a ``previews/`` volume it will build ``_linkshelf-previews/``.

.. code-block:: text

   $PDS3_HOLDINGS_DIR/_linkshelf-volumes/COUVIS_0xxx/COUVIS_0001_links.pickle
   $PDS3_HOLDINGS_DIR/_linkshelf-volumes/COUVIS_0xxx/COUVIS_0001_links.py

The ``.py`` sidecar shows the shape of the mapping. A label's entry is a list of the
links it carries, each a triple of the record number the link was found in, counting from
zero; the link text as it stands after any repair; and the path inside the volume that it
resolves to. A data file's entry is not a list at all but the single path of its label:

.. code-block:: python

   COUVIS_0001_links = {
     "DATA/D1999_007/FUV1999_007_16_57.LBL"                 : [(  58, "FUV1999_007_16_57.DAT"      , "DATA/D1999_007/FUV1999_007_16_57.DAT")],
     "DATA/D1999_007/FUV1999_007_16_57.DAT"                 : "DATA/D1999_007/FUV1999_007_16_57.LBL",
   }

What counts as a link
---------------------

A PDS3 label names the file it describes in ``KEYWORD = FILENAME`` syntax, and that is
what the scan looks for. Five extensions are searched: ``.LBL``, ``.CAT``, ``.TXT``,
``.FMT`` and ``.SFD``. The same five are the extensions a file is *not* required to have
a label of its own for -- one test serves both, which is why a ``.TXT`` file that does
have a label is reported as carrying an unnecessary one rather than as satisfying a
requirement.

Two tables adjust what the scan concludes:

* A list of files a label is not looked for, each with a reason: "missing" for a file
  that has none and is not expected to, and "unneeded" for one that carries its PDS3
  label inside itself.
* A repair table of published links that are known to be wrong, and what each was meant
  to say. A published volume is not corrected, so the correction is applied as the scan
  reads it. It covers 141 path patterns today and grows whenever another volume is found
  to carry a bad link.

What a path may name
--------------------

A volume, or a volume set. A volume set is expanded into its volumes and each is shelved
separately.

Checking a shelf
----------------

.. code-block:: console

   $ pdslinkshelf --validate $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:43:24.000120 | pds.validation.links || HEADER | pdslinkshelf --validate $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:43:24.000653 | pds.validation.links |-| HEADER | Task validate for: $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:43:24.000719 | pds.validation.links |--| INFO | Log file: $PDS3_HOLDINGS_DIR/../logs/pdslinkshelf/volumes/COUVIS_0xxx/COUVIS_0001_links_2026-08-09T01-43-24_validate.log
   2026-08-09 01:43:24.000841 | pds.validation.links |--| HEADER | Reading link shelf file for: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:43:24.000871 | pds.validation.links |---| INFO | Link shelf file: _linkshelf-volumes/COUVIS_0xxx/COUVIS_0001_links.pickle
   2026-08-09 01:43:24.001098 | pds.validation.links |--| HEADER | Finding link shelf files: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:43:24.001184 | pds.validation.links |---| DEBUG | *** REVIEWING: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.LBL
   2026-08-09 01:43:24.001684 | pds.validation.links |---| DEBUG | Substring "CO-J-UVIS-2-SPEC-V1.2" is not a link, ignored: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.LBL
   2026-08-09 01:43:24.001753 | pds.validation.links |---| DEBUG | Label identified for FUV1999_007_16_57.DAT: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.LBL
   ...
   2026-08-09 01:43:24.005715 | pds.validation.links || SUMMARY | Completed: pdslinkshelf --validate $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:43:24.005733 | pds.validation.links || SUMMARY | Elapsed time = 0:00:00.005585
   2026-08-09 01:43:24.005745 | pds.validation.links || SUMMARY | 3 ERROR messages
   2026-08-09 01:43:24.005756 | pds.validation.links || SUMMARY | 3 INFO messages
   2026-08-09 01:43:24.005765 | pds.validation.links || SUMMARY | 15 DEBUG messages

The ``DEBUG`` lines are the scan narrating itself, and they are the most useful part of
the output when a result is surprising: every string the scan considered and rejected is
reported with the reason, so ``Substring "..." is not a link, ignored`` names a value that
looked like a filename and was not one.

.. note::

   **Errors here are usually about the data, not about the shelf.** The three errors
   above recur on every run over this volume:

   .. code-block:: text

      ... | ERROR | Label HDAC1999_007_16_33.LBL does not point to file: .../HDAC1999_007_16_33.DAT
      ... | ERROR | Label is missing: .../HDAC1999_007_16_33.DAT
      ... | ERROR | Label is missing: .../INDEX/INDEX.TAB

   The first two are the volume's own: both files are there in full, and the label simply
   does not name the file beside it, which leaves that file with no label pointing at it.
   The third is not the volume's fault at all -- it is an artifact of the tree these runs
   were made against, where ``INDEX/INDEX.LBL`` is absent and ``INDEX.TAB`` is a
   zero-length stand-in. A complete published volume has both.

   ``--initialize`` writes the shelf and reports them, then exits 1. A nonzero status
   from this program means the scan logged something, which for a volume with known link
   problems is the normal outcome rather than a failure to shelve.

Log file naming
---------------

Under ``logs/pdslinkshelf/``, with ``_links`` as the suffix. :doc:`user_guide_pdsarchives`
uses the same suffix under its own directory, so a search for ``*_links_*.log`` finds
both programs' logs.

Exit status
-----------

0 when the run logged no error, 1 when it did -- including when the errors are the
volume's own link problems rather than anything about the shelf.

Superseded shelves are kept
---------------------------

The existing ``.pickle`` and its ``.py`` sidecar are copied into each of the run's log
directories, with ``_v001`` and upward appended, before either is replaced.
