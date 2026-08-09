crlf
====

The PDS3 standard requires every record of a text file to end in a carriage return
followed by a line feed, and requires the last record to be terminated like the rest. A
file edited on a system that terminates with a bare line feed, or saved without a final
newline, no longer conforms. ``crlf`` classifies files as conforming or not, and can
rewrite the ones that are not.

It is not a console script. Run it as a module:

.. code-block:: text

   python -m pdsfile.holdings_maintenance.pds3.crlf [--repair] [--verbose] [file ...]

**It reads no holdings root.** Neither ``PDS3_HOLDINGS_DIR`` nor ``PDS4_HOLDINGS_DIR`` is
consulted: the files it works on are exactly the ones named on the command line, and it
never looks for their place in a holdings tree. Any path the shell can produce is a valid
argument.

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Option
     - Meaning
   * - ``--repair``
     - Rewrite every file whose line terminators are invalid. Without it, files are only
       reported.
   * - ``--verbose``
     - List every file examined, not just the ones that are invalid or were repaired.

There are no short forms, and **abbreviations are rejected**: an unambiguous prefix of an
option name is an error rather than a request to rewrite files, which is not true of
:doc:`user_guide_re_validate`. The two options may appear anywhere among the file paths.

The four verdicts
-----------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Verdict
     - Meaning
   * - ``OK``
     - Every record ends in CR LF, including the last.
   * - ``INVALID``
     - At least one does not. Reported, and rewritten under ``--repair``.
   * - ``REPAIRED``
     - The file was invalid and has been rewritten. Only under ``--repair``.
   * - ``BINARY``
     - The file has no line terminators to be wrong about and was left alone.

**A binary file is recognized and never rewritten.** The recognition is a fraction: the
file is read as bytes and decoded with a single-byte codec, so every byte is one
character, and the file is treated as binary when more than one percent of its characters
are counted as non-ASCII. What is counted is every byte below 32 and every byte from 128
up, less carriage return, line feed and tab. Byte 127 falls in neither range and is
therefore counted as text.

Reporting
---------

The runs below are in a directory holding two files made for the purpose: ``BAD.LBL``,
whose records end in a bare line feed, and ``GOOD.LBL``, whose records end in CR LF. To
reproduce them, and the empty-file case further down:

.. code-block:: bash

   printf 'PDS_VERSION_ID = PDS3\nEND\n'     > BAD.LBL
   printf 'PDS_VERSION_ID = PDS3\r\nEND\r\n' > GOOD.LBL
   : > EMPTY.LBL

The three runs below are consecutive rather than independent: each starts where the one
before it left off. ``--repair`` rewrites ``BAD.LBL`` in place, which is exactly why the
third run finds it ``OK``. To run any of them on its own, re-create the files from the
recipe above first.

Without ``--verbose``, only ``INVALID`` and ``REPAIRED`` files are listed:

.. code-block:: console

   $ python -m pdsfile.holdings_maintenance.pds3.crlf BAD.LBL GOOD.LBL
   BAD.LBL INVALID
   1/2 files invalid

With ``--repair``, the invalid file is rewritten in place:

.. code-block:: console

   $ python -m pdsfile.holdings_maintenance.pds3.crlf --repair BAD.LBL GOOD.LBL
   BAD.LBL REPAIRED
   1/2 files repaired

And afterwards both conform. ``--verbose`` shows the files that were already ``OK``:

.. code-block:: console

   $ python -m pdsfile.holdings_maintenance.pds3.crlf --verbose BAD.LBL GOOD.LBL
   BAD.LBL OK
   GOOD.LBL OK
   2 files tested

A binary file named alongside a text one is reported as such under ``--verbose``:

.. code-block:: console

   $ python -m pdsfile.holdings_maintenance.pds3.crlf --verbose $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.LBL $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT
   $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.LBL OK
   $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT BINARY
   2 files tested

The summary line
----------------

The last line is a summary, and it appears **only when two or more files were named**.
Naming one file, or none, prints no summary whatever the verdicts were.

Which summary appears follows three exclusive rules, and one case falls through all
three:

* if exactly one file was repaired, ``1/N files repaired``;
* otherwise, if any file was invalid, ``n/N files invalid``;
* otherwise, ``N files tested``.

**A run that repairs two or more files prints no summary at all.** A repair run also never
reports an invalid file, because a file needing repair is repaired and so counts as a
repair; the invalid count can only be nonzero in a run without ``--repair``.

Exit status
-----------

**0, whatever the files turn out to be.** Nothing a file can contain, including being
binary or invalid, changes the status. 2 for a command line :mod:`argparse` cannot
classify, and 0 for ``--help``.

Two file conditions end the run in a traceback, and the interpreter's status is then 1:

* a **zero-byte** file raises :exc:`ZeroDivisionError`, because the binary fraction is
  computed over the file's length;
* a file that cannot be read, or under ``--repair`` cannot be rewritten, raises
  :exc:`OSError`.

Either leaves the files named after it unexamined and prints no summary:

.. code-block:: console

   $ python -m pdsfile.holdings_maintenance.pds3.crlf EMPTY.LBL GOOD.LBL
   Traceback (most recent call last):
     ...
     File ".../pdsfile/holdings_maintenance/pds3/crlf.py", line 117, in test_crlf
       if non_asciis/len(content) > threshold:
          ~~~~~~~~~~^~~~~~~~~~~~~
   ZeroDivisionError: division by zero

Rejected abbreviations
----------------------

.. code-block:: console

   $ python -m pdsfile.holdings_maintenance.pds3.crlf --rep BAD.LBL GOOD.LBL
   usage: crlf.py [-h] [--repair] [--verbose] [file ...]
   crlf.py: error: unrecognized arguments: --rep

Where the name comes from
-------------------------

Run through ``python -m``, the program's own usage line calls it ``crlf.py``:

.. code-block:: text

   usage: crlf.py [-h] [--repair] [--verbose] [file ...]
