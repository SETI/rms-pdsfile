show_opus_products
==================

``show_opus_products`` prints the OPUS products of the files named on the command line:
for each path it builds a :class:`~pdsfile.pds3file.Pds3File` or a
:class:`~pdsfile.pds4file.Pds4File` and shows what
:meth:`~pdsfile._opus._OpusMixin.opus_products` returns for it -- the files OPUS would
offer alongside that one, grouped by OPUS type.

It is not a console script. Run it as a module:

.. code-block:: text

   python -m pdsfile.tools.show_opus_products --paths <path> [<path> ...] [options]

It needs the ``dev`` extra
--------------------------

This program formats its output with ``tabulate``, which is not a runtime dependency of
the package. Install the extra before running it:

.. code-block:: bash

   pip install "rms-pdsfile[dev]"

Both holdings roots are required
--------------------------------

``PDS3_HOLDINGS_DIR`` **and** ``PDS4_HOLDINGS_DIR`` are read straight from the
environment, and both are needed whichever kind of path is asked about. **This is the
only program in the guide that reads either variable**, and it fails immediately with a
``KeyError`` if one is unset; the other fourteen work from the absolute paths on their
command lines and never consult the environment.

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Option
     - Meaning
   * - ``--paths <path> ...``
     - **Required.** The absolute paths or logical paths of the files to ask about. One
       or more.
   * - ``--opus-types <type> ...``
     - Show only the products of the given OPUS types. One or more.
   * - ``--table``, ``-t``
     - Show the products in a table. This is the default.
   * - ``--narrow-table``
     - Show the table in a narrower shape, with the type above its products rather than
       beside them.
   * - ``--pprint``, ``-p``
     - Show the dictionary through ``pprint``. The result is comparable with this
       package's OPUS-products golden files.
   * - ``--raw``, ``-r``
     - Show the raw dictionary.
   * - ``--debug``
     - Ask for a traceback when building a :class:`~pdsfile.pdsfile.PdsFile` fails.
       Default: off. The ``WARNING:`` line and the move to the next path happen either
       way; see below for what it actually prints.

There is no positional argument: paths go after ``--paths``, and omitting it is an error
rather than a request for help.

.. code-block:: console

   $ python -m pdsfile.tools.show_opus_products
   usage: show_opus_products.py [-h] --paths PATHS [PATHS ...]
                                [--opus-types OPUS_TYPES [OPUS_TYPES ...]]
                                [--table] [--narrow-table] [--pprint] [--raw]
                                [--debug]
   show_opus_products.py: error: the following arguments are required: --paths

``--table``, ``--narrow-table``, ``--pprint`` and ``--raw`` are four output forms; naming
none of them gives the table.

Absolute and logical paths
--------------------------

A path may be absolute or **logical** -- that is, starting at the category name, the form
this package works in internally. The two give the same answer:

.. code-block:: console

   $ python -m pdsfile.tools.show_opus_products --paths volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT --opus-types browse_thumb
   ##########################################################################################
   Pdsfile: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT
   ##########################################################################################
   +--------------+-----------------------------------------------------------------------------+
   | opus_type    | opus_products                                                               |
   +==============+=============================================================================+
   | browse_thumb | previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57_thumb.png |
   +--------------+-----------------------------------------------------------------------------+

The default table
-----------------

.. code-block:: console

   $ python -m pdsfile.tools.show_opus_products --paths $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT
   ##########################################################################################
   Pdsfile: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT
   ##########################################################################################
   +----------------------+---------------------------------------------------------------------------------------+
   | opus_type            | opus_products                                                                         |
   +======================+=======================================================================================+
   | couvis_raw           | volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT                  |
   |                      | volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.LBL                  |
   +----------------------+---------------------------------------------------------------------------------------+
   | couvis_calib_corr    | volumes/COUVIS_0xxx/COUVIS_0001/CALIB/VERSION_3/D1999_007/FUV1999_007_16_57_CAL_3.DAT |
   |                      | volumes/COUVIS_0xxx/COUVIS_0001/CALIB/VERSION_3/D1999_007/FUV1999_007_16_57_CAL_3.LBL |
   +----------------------+---------------------------------------------------------------------------------------+
   | browse_full          | previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57_full.png            |
   +----------------------+---------------------------------------------------------------------------------------+
   | browse_medium        | previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57_med.png             |
   +----------------------+---------------------------------------------------------------------------------------+
   | browse_small         | previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57_small.png           |
   +----------------------+---------------------------------------------------------------------------------------+
   | browse_thumb         | previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57_thumb.png           |
   +----------------------+---------------------------------------------------------------------------------------+
   | rms_index            | metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_index.lbl                                |
   |                      | metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_index.tab                                |
   +----------------------+---------------------------------------------------------------------------------------+
   | supplemental_index   | metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_supplemental_index.lbl                   |
   |                      | metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_supplemental_index.tab                   |
   +----------------------+---------------------------------------------------------------------------------------+
   | couvis_documentation | documents/COUVIS_0xxx/Cassini-UVIS-Final-Report.pdf                                   |
   |                      | documents/COUVIS_0xxx/UVIS-Archive-SIS.pdf                                            |
   |                      | documents/COUVIS_0xxx/UVIS-Archive-SIS.txt                                            |
   |                      | documents/COUVIS_0xxx/UVIS-Preview-Interpretation-Guide.txt                           |
   |                      | documents/COUVIS_0xxx/UVIS-Users-Guide.docx                                           |
   |                      | documents/COUVIS_0xxx/UVIS-Users-Guide.pdf                                            |
   +----------------------+---------------------------------------------------------------------------------------+

The products are reported as logical paths whatever form the input took.

The other three forms
---------------------

``--narrow-table`` puts the type on its own row above its products, which fits a terminal
where the two-column table does not:

.. code-block:: console

   $ python -m pdsfile.tools.show_opus_products --paths $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT --narrow-table --opus-types browse_full
   ##########################################################################################
   Pdsfile: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT
   ##########################################################################################
   +----------------------------------------------------------------------------+
   | opus_type and its corresponding opus_products                              |
   +============================================================================+
   | browse_full                                                                |
   +----------------------------------------------------------------------------+
   | previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57_full.png |
   +----------------------------------------------------------------------------+

``--pprint`` shows the dictionary as returned, whose keys are the full OPUS type tuples
rather than the short names the table shows:

.. code-block:: console

   $ python -m pdsfile.tools.show_opus_products --paths $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT --pprint --opus-types browse_full
   ##########################################################################################
   Pdsfile: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT
   ##########################################################################################
   {('browse', 40, 'browse_full', 'Browse Image (full)', True): ['previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57_full.png']}

``--raw`` shows the same dictionary broken across lines:

.. code-block:: console

   $ python -m pdsfile.tools.show_opus_products --paths $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT --raw --opus-types browse_full
   ##########################################################################################
   Pdsfile: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT
   ##########################################################################################
   {
    ('browse',
     40,
     'browse_full',
     'Browse Image (full)',
     True): [
       'previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57_full.png',
     ],
   }

``--opus-types`` narrows every form, and is matched against the short name -- the third
element of the key tuple.

.. warning::

   **It is a process, not a library call.** Running its ``main()`` inside a Python session
   changes state that belongs to the whole interpreter and does not change back: it turns
   shelves-only mode on for :class:`~pdsfile.pds3file.Pds3File` and off for
   :class:`~pdsfile.pds4file.Pds4File`, and it preloads both trees into the caches those
   classes hold as class attributes. Those caches are keyed by logical path, so a session
   that has preloaded one tree resolves a logical path to that tree whatever root a later
   caller has in mind. Run it in a subprocess.

Exit status
-----------

0 for a run that produced output, 2 for a command line ``argparse`` cannot classify --
including one with no ``--paths``.

A path that cannot be turned into a :class:`~pdsfile.pdsfile.PdsFile`, and one that
resolves to a file that does not exist, are each reported as a ``WARNING:`` line and the
run continues to the next path. Neither changes the status, so a run in which every path
failed still exits 0. ``--debug`` is meant to add a traceback to the first of the two, and does not: it prints
the line ``NoneType: None`` instead, because the traceback is requested after the failure
has already been handled. The ``WARNING:`` line still follows and the run still continues.

An ``--opus-types`` value that is not among the types the file actually has is likewise a
``WARNING:``, and a run in which none of the given types matched prints the valid values
and skips that file.
