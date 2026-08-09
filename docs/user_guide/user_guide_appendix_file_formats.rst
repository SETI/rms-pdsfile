Appendix: File Formats
======================

This appendix gives the format of every file the programs in this guide write or read
that is not itself published PDS data. Each is plain enough to inspect by hand, which is
the point: a shelf that cannot be read without the package would be a worse thing to
depend on.

Checksum files: ``*_md5.txt``
-----------------------------

Written and read by :doc:`user_guide_pdschecksums` and
:doc:`user_guide_pds4checksums`, and read by the two info shelf programs.

A plain text file, one record per file, in the format ``md5sum`` uses: a 32-character
lower-case hexadecimal digest, two spaces, and the file's path relative to the unit set:

.. code-block:: text

   de39b402ff1fd89e709d3d87e7f9464e  COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT
   7e7a9fea32d2f26898bb2a630b21862f  COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.LBL
   599fd9d01505983a59f7bd1ff2edb26f  COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_33.LBL

Directories have no records; only files do. The path is relative to the unit set
directory, so it begins with the unit name, which is what lets one file cover a whole
unit set in the ``archives-`` categories.

Where the file lives is described in :doc:`user_guide_pdschecksums`. Superseded copies
are kept in the run's log directories under the same basename with ``_v001`` and upward
inserted before the extension.

Shelf files: ``.pickle`` and its ``.py`` sidecar
------------------------------------------------

Every shelf is written twice: a ``.pickle``, which is what the package reads, and a
``.py`` beside it holding the same mapping as readable Python. The two are written in one
pass and travel together -- a task that versions one versions the other -- so the ``.py``
is a reliable way to read a shelf without unpickling anything.

The ``.py`` file is a single assignment. Its variable name is the shelf's basename
without the extension, so a file can be read with ``exec`` or simply looked at.

Info shelves
~~~~~~~~~~~~

Written by :doc:`user_guide_pdsinfoshelf` and :doc:`user_guide_pds4infoshelf`. The
mapping is keyed by each file's path inside the unit, and the value is a five-element
tuple: byte count, child count, modification time, MD5 digest, and a ``(width, height)``
pair.

The three shelf excerpts below are entries taken from real files, with a ``...`` line
where the rest has been left out. Each has had its key column narrowed, because the real
files pad that column to the widest key in the whole file, which for a volume of any size
is far wider than this page. The info shelf and index shelf excerpts are each a file's
first three entries. The link shelf excerpt is two entries chosen to show one of each
value shape rather than the first two, and its second column has been un-padded as well.
Nothing about the values themselves is changed.

.. code-block:: python

   COUVIS_0001_info = {
       ""                                   : (     145262,   3, "2020-05-13 00:30:45.000000", ""                                , (   0,   0)),
       "CALIB"                              : (      17851,   1, "2020-05-11 16:58:25.000000", ""                                , (   0,   0)),
       "CALIB/VERSION_3"                    : (      17851,   1, "2020-05-11 16:58:25.000000", ""                                , (   0,   0)),
       ...
   }

Four properties of the entries are worth knowing:

* **The empty key is the unit itself.** Its byte count is the total over the unit and its
  child count is the number of entries directly inside it. It is the first entry, on the
  second line of the ``.py`` file, which is what lets a question about a whole unit be
  answered by reading one line rather than unpickling the shelf.
* **A directory carries a child count and an empty digest.** A file carries a digest and
  a child count of zero. A zero-byte file is not a special case: it carries the digest of
  the empty string.
* The ``(width, height)`` pair is ``(0, 0)`` for anything that is not an image whose
  dimensions were read.
* **The modification time is formatted in the local time zone**, so a unit shelved under
  one setting of ``TZ`` disagrees with itself when read back under another. How the
  comparison is made depends on the task. ``--validate`` parses both sides and allows
  them to differ by anything under one second, so a sub-second difference is forgiven and
  a difference of a whole second is not; where either side will not parse as a time, the
  two strings are compared instead, which is how the empty string a childless directory
  carries is handled. ``--repair`` does not use that comparison at all: it compares the
  whole shelf against a freshly generated one for exact equality, so a sub-second
  difference ``--validate`` forgives is still enough to make ``--repair`` rewrite.

Link shelves
~~~~~~~~~~~~

Written by :doc:`user_guide_pdslinkshelf` and :doc:`user_guide_pds4linkshelf`. The
mapping is keyed by each file's path inside the unit, and the value takes one of two
shapes:

* for a **label**, a list of the links it carries, each a triple of the record number the
  link was found in counting from zero, the link text after any repair, and the path
  inside the unit that it resolves to;
* for a **file that a label describes**, the single path of that label, as a string
  rather than a list.

.. code-block:: python

   COUVIS_0001_links = {
     "DATA/D1999_007/FUV1999_007_16_57.LBL"  : [(  58, "FUV1999_007_16_57.DAT", "DATA/D1999_007/FUV1999_007_16_57.DAT")],
     "DATA/D1999_007/FUV1999_007_16_57.DAT"  : "DATA/D1999_007/FUV1999_007_16_57.LBL",
     ...
   }

A file that is neither a label nor described by one still gets an entry, whose value is
the empty string. In the volume above, the unlabeled ``HDAC1999_007_16_33.DAT`` and
``INDEX/INDEX.TAB`` both appear that way -- which is the same fact
:doc:`user_guide_pdslinkshelf` reports as two ``Label is missing`` errors.

Index shelves
~~~~~~~~~~~~~

Written by :doc:`user_guide_pdsindexshelf` and :doc:`user_guide_pds4indexshelf`. Unlike
the other two, an index shelf covers **one table** rather than one unit, so a unit has as
many of them as it has metadata tables and they sit one directory deeper.

The mapping is keyed by a row selection key -- the product name the table's rows are
looked up by -- and the value is the row number, counting from zero, or the list of row
numbers where one product covers more than one row:

.. code-block:: python

   COUVIS_0001_index = {
       "HSP1999_007_16_53"   : 0,
       "HDAC1999_007_16_31"  : 1,
       "HDAC1999_007_16_33"  : 2,
       ...
   }

Archive files: ``.tar.gz``
--------------------------

Written by :doc:`user_guide_pdsarchives` and :doc:`user_guide_pds4archives`. An ordinary
gzip-compressed tar file, readable with ``tar tzf`` and any tar implementation.

What differs between the two programs is where the member names begin. The PDS3 program
packs one volume per archive and its member names begin at the volume name, so unpacking
gives a ``COUVIS_0001/`` directory. The PDS4 program packs whatever its bundle set's
rules say, and the member names begin at the bundle set.

Directories are archived as members in their own right, not only implied by the files
inside them, which is why an archive of a volume holding nine files lists sixteen
members.

Two kinds of file are dropped as the archive is written, each reported in the log: a
``.DS_Store``, and a dot-underscore file, recognized by its own basename or by any
component of its path.

Other invisible files -- those whose basename or any path component begins with a dot --
are **archived**, and reported as ``Invisible file archived``. The programs take an
argument that would skip them instead, but no command line exposes it, so from the
command line an invisible file always goes in.

Every member's ownership is rewritten to ``root`` before it is added, so an archive does
not record who ran the program.

The volume information file: ``_volinfo/<unit set>.txt``
---------------------------------------------------------

One text file per unit set, in ``_volinfo/``. It is not derived from anything, no program
in this guide writes it, and it supplies what the data does not say about itself: the
descriptions that appear beside a unit set and each of its units.

Records are ``|``-separated. Blank records, and records beginning with ``#``, are
ignored; the first line of each file is conventionally a ``#`` record naming the fields:

.. code-block:: text

   # volset or volset/volname | description | optional icon type | version ID | publication date | data set ID if any | additional data set IDs if any, or checksum

   COISS_2xxx            | Cassini Saturn image collection                                                     || 1.0 | 2018-07-01
   COISS_2xxx/COISS_2001 | Cassini ISS Saturn images 2004-02-06 to 2004-04-18 (SC clock 1454725799-1460960370) || 1.0 | 2005-07-01 | CO-S-ISSNA/ISSWA-2-EDR-V1.0
   ...

The fields, in order:

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Field
     - Meaning
   * - key
     - ``<unit set>``, ``<unit set>/<unit>``, ``<category>/<unit set>`` or
       ``<category>/<unit set>/<unit>``.
   * - description
     - The text shown beside that key.
   * - icon type
     - Blank for the default.
   * - version ID
     - Or a string of dashes where it does not apply.
   * - publication date
     - Or a string of dashes where it does not apply.
   * - data set ID
     - Or, for an entry in the ``documents/`` tree, an MD5 digest.
   * - further data set IDs
     - Any number, each in its own field.

A field holding only dashes is read as "not applicable" and becomes ``None``; an empty
version ID or publication date stays an empty string, which is a different value. An
empty data set ID field gives an empty list rather than a list holding an empty string.

An entry with no data set IDs of its own inherits them from the same unit in another
category, by reducing the unit set name to its first two underscore-separated parts and
looking for the entry with no category, then the one under ``volumes/``.

Every ``.txt`` file directly inside ``_volinfo/`` is read, and files whose names begin
with a period are skipped.

Log files
---------

Described in :doc:`user_guide_maintenance_tools`. They are plain text, one record per
message, in the format:

.. code-block:: text

   <timestamp> | <logger name> |<depth>| <level> | <message>

``ERRORS.log`` and ``WARNINGS.log`` are **thresholds, not filters**: each holds every
record at its level or above. So ``WARNINGS.log`` contains all of the errors as well, and
on a run with no warnings the two files hold the same records. Both accumulate across
runs rather than being replaced.
