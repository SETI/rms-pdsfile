Installation and Setup
======================

Supported Python versions
-------------------------

``rms-pdsfile`` requires **Python 3.10 or later**.

Installing
----------

For use as a library, install into the environment that will import it:

.. code-block:: bash

   pip install rms-pdsfile

To have the command-line programs available system-wide without putting the package on
any project's dependency list, install it as an application instead:

.. code-block:: bash

   pipx install rms-pdsfile

Either way the eleven console scripts land on ``PATH``:

.. code-block:: text

   pdsarchives    pdschecksums   pdsdependency  pdsindexshelf  pdsinfoshelf   pdslinkshelf
   pds4archives   pds4checksums  pds4indexshelf pds4infoshelf  pds4linkshelf

Four further programs ship as modules rather than as console scripts and are run with
``python -m``: ``crlf``, ``re_validate``, ``shelf_consistency_check`` and
``show_opus_products``. Their chapters give the full module path each one needs.

One program needs the ``dev`` extra
-----------------------------------

``show_opus_products`` formats its output with ``tabulate``, which is not a runtime
dependency of the package. Install the ``dev`` extra to run it:

.. code-block:: bash

   pip install "rms-pdsfile[dev]"

Without it, every other program in this guide works and ``show_opus_products`` fails at
import.

Environment variables
---------------------

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Variable
     - What it names
   * - ``PDS3_HOLDINGS_DIR``
     - The root of the PDS3 holdings tree. Its basename must be ``holdings``.
   * - ``PDS4_HOLDINGS_DIR``
     - The root of the PDS4 holdings tree. Its basename must be ``pds4-holdings``.
   * - ``PDS_LOG_ROOT``
     - Optional. The root of a duplicate log tree, used when ``--log`` is not given.

The basenames are a requirement of the *directory*, not of the variable, and they are a
requirement rather than a habit. Every absolute path is turned into
the *logical path* the package works in by splitting it at the first ``/holdings/`` or
``/pds4-holdings/`` component, so a root directory named anything else makes every path
under it unusable. The thirteen programs that resolve holdings paths all fail on such a
path, but not alike: the checksum and info shelf programs print ``Not a holdings
subdirectory:`` and exit 1, while the archive, link shelf, index shelf and dependency
programs end in an unhandled :exc:`ValueError` traceback, also with status 1.
:doc:`user_guide_crlf` and :doc:`user_guide_shelf_consistency_check` are the two that
never resolve a holdings path at all, and a root's name is nothing to them.

**Only one of the fifteen programs reads the two holdings variables directly:**
:doc:`user_guide_show_opus_products`, which reads both, whichever kind of path it is
asked about, and fails with a :exc:`KeyError` if either is unset.

The other fourteen take absolute paths on their command lines, and the thirteen of them
that work in a holdings tree find their way around it by splitting the path at its
``/holdings/`` or ``/pds4-holdings/`` component rather than by consulting a variable.
Every run in this guide was made with both variables set, and the runs that resolve a
path this way behave the same with them unset. Setting them is worth doing in any case --
it is what lets you write ``$PDS3_HOLDINGS_DIR/volumes/...`` rather than typing the root
each time, which is how every example in this guide is written.

One qualification, because "reads no environment variable" is easy to overstate: the
library underneath these programs does have a path that reads a holdings root from the
environment. It is reached when a shelved link has to be resolved back to an absolute
path from a logical one. No example in this guide exercises it, and no run recorded here
needed it, but a command over data that does reach it may.

.. code-block:: bash

   export PDS3_HOLDINGS_DIR=/path/to/holdings
   export PDS4_HOLDINGS_DIR=/path/to/pds4-holdings

``PDS_LOG_ROOT`` and ``--log`` are two ways of setting the same thing, and the flag wins:
a program takes ``--log`` if it is given, falls back to ``PDS_LOG_ROOT`` if it is not,
and writes no duplicate log tree if neither is set.
:doc:`user_guide_maintenance_tools` covers what a log root does.

The holdings tree layout
------------------------

A PDS3 holdings tree, at its top level, looks like this. Every directory is optional in
the sense that a tree holds the ones its data needs:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/
       volumes/                        published PDS3 volumes
       calibrated/                     calibrated versions of them
       diagrams/                       diagram images
       metadata/                       index tables and other metadata
       previews/                       preview images
       documents/                      documentation, not archived or checksummed
       archives-volumes/               one .tar.gz per volume
       archives-calibrated/
       archives-diagrams/
       archives-metadata/
       archives-previews/
       checksums-volumes/              one *_md5.txt per volume
       checksums-calibrated/
       checksums-diagrams/
       checksums-metadata/
       checksums-previews/
       checksums-archives-volumes/     one *_md5.txt per volume set of archives
       checksums-archives-calibrated/
       checksums-archives-diagrams/
       checksums-archives-metadata/
       checksums-archives-previews/
       _infoshelf-volumes/             info shelves, one tree per category above
       _infoshelf-calibrated/
       _infoshelf-diagrams/
       _infoshelf-metadata/
       _infoshelf-previews/
       _infoshelf-archives-volumes/
       _infoshelf-archives-calibrated/
       _infoshelf-archives-diagrams/
       _infoshelf-archives-metadata/
       _infoshelf-archives-previews/
       _linkshelf-volumes/             link shelves
       _linkshelf-calibrated/
       _linkshelf-metadata/
       _indexshelf-metadata/           index shelves, for metadata tables only
       _volinfo/                       one text file per volume set

A PDS4 tree uses the same category vocabulary -- the volume types and the two prefixes
are one shared set -- with ``bundles`` in place of ``volumes``. What any given tree holds
is the subset its data needs:

.. code-block:: text

   $PDS4_HOLDINGS_DIR/
       bundles/
       metadata/
       previews/
       diagrams/
       documents/
       archives-bundles/
       checksums-bundles/
       _infoshelf-bundles/
       _linkshelf-bundles/
       _indexshelf-metadata/

Which of these a tree actually holds is up to its data. The three link shelf
directories above are the ones :doc:`user_guide_pdsdependency` requires of a volume, but
nothing in :doc:`user_guide_pdslinkshelf` restricts it to those three: point it at a
``previews`` volume and it writes ``_linkshelf-previews/``.

``setup_new_holdings.sh``, described in :doc:`user_guide_shell_scripts`, creates the
empty PDS3 directories in one command.

The log tree
------------

Every maintenance program writes a log file per target, and it writes it in a directory
that is **not** inside the holdings tree. The default place is a ``logs`` directory
beside the holdings root:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/../logs/<program>/<category>/<unit set>/<log file>

A log root, from ``--log`` or ``PDS_LOG_ROOT``, adds a second copy of the same file
under that root, in the same shape. :doc:`user_guide_maintenance_tools` gives the file
names and the ``ERRORS.log`` and ``WARNINGS.log`` files that accompany them.

.. _reading-the-examples:

How to read the examples in this guide
--------------------------------------

Every command shown in this guide was run, and every block of output is what that run
printed. Three kinds of substitution are made in what is published, and nothing else is
changed:

* the PDS3 and PDS4 holdings roots are written ``$PDS3_HOLDINGS_DIR`` and
  ``$PDS4_HOLDINGS_DIR``, and the directory containing a root -- where the log tree
  sits -- is written ``$PDS3_HOLDINGS_DIR/..`` or ``$PDS4_HOLDINGS_DIR/..``, according
  to which root the program derived it from. The two roots shared one parent directory
  in these runs, so both forms name the same directory there and would name two in a
  tree whose roots sit apart;
* the directory the installed program was run from is dropped, so a console script
  appears by name even where the program echoes the absolute path it was invoked with,
  and the directory the package was imported from is written ``<source root>``, which is
  visible in the :doc:`user_guide_re_validate` example because a ``python -m`` run echoes
  the module's own file path;
* where a run's output is too long to show whole, the lines left out are replaced by a
  line reading ``...`` and the surrounding prose says what was cut.

The runs were made against a copy of a holdings tree rather than a production one, since
several of the tasks write into the tree. A timestamp, an elapsed time and an MD5 digest
in an example are that run's, and will differ in yours.
