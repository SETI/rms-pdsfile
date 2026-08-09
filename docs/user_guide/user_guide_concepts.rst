Concepts
========

The programs in this guide all work on one thing: a **holdings tree**, the directory
tree in which the PDS Ring-Moon Systems Node keeps its published data and everything
derived from it. This chapter defines the words the rest of the guide uses. Nothing
here is a command; :doc:`user_guide_installation` follows with the setup, and
:doc:`user_guide_maintenance_tools` with the command line the tools share.

PDS3 and PDS4
-------------

There are two archive standards in play and a holdings tree serves one of them.

* A **PDS3** tree holds *volumes*, grouped into *volume sets*. A volume is one
  published directory tree, such as ``COUVIS_0001``; its volume set is the family it
  belongs to, ``COUVIS_0xxx``. Files carry detached PDS3 labels, which are text files
  in ``KEYWORD = VALUE`` syntax.
* A **PDS4** tree holds *bundles*, grouped into *bundle sets*. A bundle is one
  published directory tree, such as ``cassini_uvis_solarocc_beckerjarmak2023``, and its
  bundle set is the family it belongs to. Labels are XML.

The distinction runs through everything. Each tree has its own root, its own
environment variable, its own :class:`~pdsfile.pds3file.Pds3File` or
:class:`~pdsfile.pds4file.Pds4File` class, and its own half of every pair of maintenance
programs: ``pdschecksums`` works on volumes and ``pds4checksums`` on bundles. Where this
guide needs one word for both it says **unit**, which is what the programs' own help
text calls a volume, a bundle or an index table.

Categories
----------

The top level of a holdings tree is a set of **categories**. A category name is a
*volume type* with two optional prefixes:

.. code-block:: text

   [checksums-][archives-]<volume type>

The volume types are ``volumes``, ``calibrated``, ``diagrams``, ``metadata``,
``previews``, ``documents`` and ``bundles``. Four names are possible for each, except
that ``documents`` takes no prefix at all, because nothing archives or checksums the
documents tree. That gives 25 category names in total, of which any one tree uses the
subset its data needs: a PDS3 tree uses the ``volumes`` family and a PDS4 tree the
``bundles`` family, and both use ``metadata`` and ``previews``.

Inside a category, the depth depends on the category. The bare volume types other than
``documents`` -- ``volumes``, ``calibrated``, ``diagrams``, ``metadata``, ``previews``
and ``bundles`` -- put a unit set directory and then a unit directory under the category,
and the published tree below that:

.. code-block:: text

   <holdings root>/<category>/<unit set>/<unit>/<path inside the unit>

For example, ``$PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001/INDEX/INDEX.TAB``.

Nothing else in the tree has that shape. Each derived product is written per unit, per
unit set or per table rather than as a tree, so where a bare type has a directory a
derived one has a file -- a file per product for the archive and checksum trees, and two
files, a ``.pickle`` and a ``.py``, for each of the three kinds of shelf. The depth
changes with it.

The table below covers every top-level directory of a holdings tree. Four of its rows
name the shelf trees, which are top-level directories but not categories: the 25
category names are the ones the prefix rule above generates, and no shelf tree is among
them.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Top-level directory
     - What a path under it looks like
   * - ``volumes``, ``calibrated``, ``diagrams``, ``metadata``, ``previews``,
       ``bundles``
     - ``<unit set>/<unit>/<path inside the unit>``
   * - ``documents``
     - ``<unit set>/<file>``: no unit level at all, since a document describes the unit
       set as a whole. A unit set may group its files into subdirectories.
   * - ``archives-<type>``, ``checksums-<type>``, ``_infoshelf-<type>``,
       ``_linkshelf-<type>``
     - ``<unit set>/<file named for the unit>``: a file where the bare type has the
       unit's directory, such as ``checksums-volumes/COUVIS_0xxx/COUVIS_0001_md5.txt``.
   * - ``checksums-archives-<type>``, ``_infoshelf-archives-<type>``
     - ``<file named for the unit set>``: no unit set directory either, because these
       describe the unit set's archive files collectively, as in
       ``checksums-archives-volumes/COCIRS_0xxx_md5.txt``.
   * - ``_indexshelf-metadata``
     - ``<unit set>/<unit>/<file named for the table>``: one level deeper than the rest,
       because it holds one shelf per metadata table rather than one per unit.

Depth alone does not tell you which of these you are looking at -- a ``documents`` file
and a checksum file sit at the same depth, and so do a metadata table and its index
shelf. **The first component is what tells you**, and the table above is how to read it.

Published data and derived products
-----------------------------------

Only the bare volume types hold published data. Every *category* beyond them is
**derived**: it is computed from the published data and can be rebuilt from it, and each
kind has a program in this guide that builds and checks it. (``_volinfo/`` is neither
published data nor derived, and is described at the end of this chapter.)

.. list-table::
   :header-rows: 1
   :widths: 22 26 30 22

   * - Derived product
     - Where it lives
     - What it records
     - Program
   * - Checksum file
     - ``checksums-<category>/``
     - one MD5 digest per file
     - :doc:`user_guide_pdschecksums`
   * - Archive file
     - ``archives-<category>/``
     - the whole unit as one ``.tar.gz``
     - :doc:`user_guide_pdsarchives`
   * - Info shelf
     - ``_infoshelf-<category>/``
     - each file's size, child count, modification time, digest and image shape
     - :doc:`user_guide_pdsinfoshelf`
   * - Link shelf
     - ``_linkshelf-<category>/``
     - which files each label points at
     - :doc:`user_guide_pdslinkshelf`
   * - Index shelf
     - ``_indexshelf-<category>/``
     - which rows of a metadata table belong to each product
     - :doc:`user_guide_pdsindexshelf`

The three shelf trees have names beginning with an underscore, and the archive and
checksum trees do not, because the shelves are an implementation of this package and the
other two are products the node publishes.

A sixth program, :doc:`user_guide_pdsdependency`, builds nothing. It owns the
*relationships* among the products above -- which of them a given volume implies, and
whether each is present and no older than what it describes.

Why the derived products exist
------------------------------

Checksums and archives are what a PDS archive is expected to ship: a manifest that says
what the bytes were, and a single file that can be moved or downloaded as a unit.

The shelves exist for speed. :class:`~pdsfile.pdsfile.PdsFile` is asked constantly how
big a file is, when it changed, what its digest is and what its label points at.
Answering from the filesystem means a ``stat`` per question and a full read of a metadata
table to find one product's rows. A shelf answers all of it from one pickled dictionary,
so the tree becomes answerable without being touched. That also lets the package run
against a tree it cannot stat at all, reading only the shelves.

The order in which they must be built
-------------------------------------

The products are not independent, and one dependency is hard:

* An **info shelf reads the checksum file** rather than computing digests itself. A unit
  with no checksum file cannot be shelved; the run reports a missing checksum entry for
  every file and then fails. So ``pdschecksums`` runs before ``pdsinfoshelf``, always.
  ``pdschecksums --infoshelf`` exists to chain the two in one command.
* An archive is a file like any other, so it gets a checksum file and an info shelf of
  its own, under ``checksums-archives-<category>/`` and
  ``_infoshelf-archives-<category>/``. Those come after the archive is written.
* Link shelves and index shelves depend on nothing but the published data.

The order a full build takes is therefore: checksums, then info shelves, then archives,
then the archives' own checksums and info shelves, then link shelves and index shelves.
(``update_holdings_for_new_metadata.sh``, described in
:doc:`user_guide_shell_scripts`, does not follow this order.)
:doc:`user_guide_pdsdependency` checks that ordering after the fact and prints the exact
commands that would repair it.

Tasks
-----

Ten of the fifteen programs -- the five kinds of derived product, in their PDS3 and PDS4
flavors -- take the same five **tasks**, and a run does exactly one of them:

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Task
     - What it does
   * - ``--initialize``
     - Build the product. Stop if it already exists.
   * - ``--reinitialize``
     - Build the product, replacing one that already exists.
   * - ``--validate``
     - Compare the product against what it describes. Change nothing.
   * - ``--repair``
     - Compare, and rewrite the product if it disagrees.
   * - ``--update``
     - Add entries for anything new. Leave existing entries alone.

:doc:`user_guide_maintenance_tools` covers the shared command line in full, including
what happens when a command line names more than one task and where each run writes its
logs.

Unit set versions
-----------------

A category may hold more than one version of the same unit set, and the version is
carried in the directory name as a suffix. An unsuffixed name is the current version. A
numbered suffix ``_v<major>``, ``_v<major>.<minor>`` or ``_v<major>.<minor>.<micro>``
names a superseded one, so ``COUVIS_0xxx`` and ``COUVIS_0xxx_v1`` are the current and the
first version of one unit set. Four further suffixes name a release stage rather than a
number: ``_in_prep``, ``_prelim``, ``_peer_review`` and ``_lien_resolution``. Any other
suffix is rejected.

Every one of them is an ordinary unit set to the programs in this guide: none treats a
suffixed name specially, and each version is checksummed, archived and shelved on its
own.

Two further kinds of directory sit under a unit set without being a unit: a name
beginning ``checksums_`` or ``superseded``, and a name ending ``_support``. Each gets a
checksum file of its own, which is why a unit set can hold more checksum files than it
has units.

The volume information file
---------------------------

``_volinfo/`` is a small text tree, one file per unit set, that supplies what the data
itself does not say: a one-line description of each unit set and unit, an optional icon
type, a version ID, a publication date and the data set IDs. It is not derived and no
program in this guide writes it. :doc:`user_guide_appendix_file_formats` gives its
format.
