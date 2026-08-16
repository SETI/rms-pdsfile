The Shell Scripts
=================

Twelve shell scripts ship alongside the PDS3 programs. They are operator tools rather
than parts of the package: nothing imports them, and ``pip`` puts none of them on
``PATH``.

They do ship, so an installed copy has them: they land in the installed package, at
``<site-packages>/pdsfile/holdings_maintenance/pds3/``. In a checkout of this repository
the same twelve are at ``src/pdsfile/holdings_maintenance/pds3/``. Ten of them can be
run from anywhere, whether they take holdings paths or the drive names the
``pdsdata-sync-*`` scripts take. **Two must be run from that directory**:
``copy_all_except_metadata.sh``, which calls its siblings as ``./copy_documents.sh`` and
``./copy_shelves.sh``, and ``update_holdings_for_new_metadata.sh``, which invokes the
programs as ``python pdsarchives.py`` and so on. Each is flagged again where it is
described below.

They fall into four groups, which are the four sections below.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Script
     - What it does
   * - ``setup_new_holdings.sh``
     - Creates the empty standard directories of a new holdings tree.
   * - ``copy_documents.sh``
     - Copies one volume set's ``documents/`` subtree between two holdings trees.
   * - ``copy_shelves.sh``
     - Copies one volume set's shelves, for one category, between two holdings trees.
   * - ``copy_all_except_metadata.sh``
     - Runs the two above over ``volumes``, ``calibrated``, ``previews`` and ``diagrams``.
   * - ``create_fake_volumes_for_metadata.sh``
     - Creates empty volume directories mirroring a metadata directory.
   * - ``update_holdings_for_new_metadata.sh``
     - Deletes and rebuilds every derived product of one volume set's metadata.
   * - ``pdsdata-sync-volset.sh``
     - Syncs one volume set between two ``pdsdata`` drives.
   * - ``pdsdata-sync-volume.sh``
     - Syncs one volume between two ``pdsdata`` drives.
   * - ``pdsdata-sync-volset-metadata.sh``
     - Syncs one volume set's metadata only.
   * - ``pdsdata-sync-volset-metadata-versions.sh``
     - The same, including superseded versions.
   * - ``pdsdata-sync-volume-metadata.sh``
     - Syncs one volume's metadata only.
   * - ``pdsdata-sync-volset-previews.sh``
     - Syncs one volume set's previews only.

The table is in that order: the first six rows are the first three groups and the last
six are the fourth. Those first six print their usage and exit when given the wrong
number of arguments, so running one of them bare is a safe way to see what it wants. The
six ``pdsdata-sync-*`` scripts do not check their arguments at all: run one bare and it
proceeds with empty drive and volume-set names, against paths such as
``/Volumes/pdsdata-/holdings/``. Read the usage comment at the top of the file instead.

Setting up a holdings tree
--------------------------

.. code-block:: text

   setup_new_holdings.sh <holdings_dir>

The directory must already exist; the script creates the 36 standard subdirectories
inside it and nothing else. It is the definition of what a complete PDS3 holdings tree's
top level looks like, and the layout in :doc:`user_guide_installation` is that list.

Copying between two holdings trees
----------------------------------

.. code-block:: text

   copy_documents.sh          <src_holdings_dir> <dest_holdings_dir> <volset>
   copy_shelves.sh            <src_holdings_dir> <dest_holdings_dir> <volset> <shelf_type>
   copy_all_except_metadata.sh <src_holdings_dir> <dest_holdings_dir> <volset>

``copy_shelves.sh`` copies whichever of ``_infoshelf-<type>/``, ``_indexshelf-<type>/``
and ``_linkshelf-<type>/`` exist for the named volume set, **replacing** the destination
directory outright: it removes the destination before copying, so anything there that the
source does not have is lost.

``copy_all_except_metadata.sh`` is a wrapper that calls the other two, once for
``documents`` and once for each of ``volumes``, ``calibrated``, ``previews`` and
``diagrams``. It calls them as ``./copy_documents.sh``, so **it only works when run from
the directory it lives in**.

Rebuilding a volume set's metadata products
-------------------------------------------

.. code-block:: text

   create_fake_volumes_for_metadata.sh <holdings_dir> <volset>
   update_holdings_for_new_metadata.sh <holdings_dir> <volset>

``create_fake_volumes_for_metadata.sh`` creates an empty ``volumes/<volset>/<volume>``
directory for each volume the metadata tree has, so that
:class:`~pdsfile.pds3file.Pds3File` acknowledges those volumes exist. Nothing is copied;
the directories stay empty.

``update_holdings_for_new_metadata.sh`` is the destructive one. It **deletes** the volume
set's entries under seven directories -- ``archives-metadata/``,
``checksums-archives-metadata/``, ``checksums-metadata/``, ``_indexshelf-metadata/``,
``_infoshelf-archives-metadata/``, ``_infoshelf-metadata/`` and ``_linkshelf-metadata/``
-- and then runs seven ``--initialize`` commands that rebuild exactly those seven
products, in an order the dependency graph in :doc:`user_guide_concepts` permits:
``pdschecksums``, ``pdsinfoshelf`` and ``pdsarchives`` over ``metadata/``, then
``pdschecksums`` and ``pdsinfoshelf`` over ``archives-metadata/``, then ``pdslinkshelf``
and ``pdsindexshelf`` over ``metadata/``. It is the PDS3 command sequence that chapter
shows, run for one volume set, with the old products deleted first because
``--initialize`` refuses to replace a product that already exists. It ends with
``ALL COMPLETED WITH NO ERRORS``.

.. note::

   The rebuild invokes the programs as ``python pdsarchives.py`` and so on -- by module
   file, from the script's own directory -- rather than through the console scripts
   ``pip`` installs. Run it from the directory it lives in, in an environment where the
   package imports.

Syncing between drives
----------------------

The six ``pdsdata-sync-*`` scripts move a volume set, or a volume, between two mounted
drives named ``/Volumes/pdsdata-<name>``. They take the two drives' short names rather
than paths:

.. code-block:: text

   pdsdata-sync-volset.sh                   <old> <new> <volset> [--dry-run] [--delete]
   pdsdata-sync-volset-metadata.sh          <old> <new> <volset> [--dry-run] [--delete]
   pdsdata-sync-volset-metadata-versions.sh <old> <new> <volset> [--dry-run] [--delete]
   pdsdata-sync-volset-previews.sh          <old> <new> <volset> [--dry-run] [--delete]
   pdsdata-sync-volume.sh                   <old> <new> <volset> <volume> [--dry-run] [--delete]
   pdsdata-sync-volume-metadata.sh          <old> <new> <volset> <volume> [--dry-run] [--delete]

So this copies everything belonging to one volume set from the ``admin`` drive to the
``staging`` drive, deleting anything at the destination the source does not have:

.. code-block:: bash

   ./pdsdata-sync-volset.sh admin staging VGx_9xxx --delete

Four things are worth knowing before running one.

* **They are zsh scripts, and they assume macOS.** The interpreter line is
  ``#! /bin/zsh``, the paths are ``/Volumes/pdsdata-<name>``, and the ``._*`` files they
  exclude and then delete at the destination are the resource forks a Mac leaves behind.
* ``--dry-run`` and ``--delete`` are passed through to ``rsync`` rather than parsed.
  They are read as positional arguments -- the fourth and fifth for the four volume-set
  scripts, the fifth and sixth for the two volume scripts -- so they must come after the
  required arguments and cannot be given in any other position. ``-a`` and ``-v`` are
  always included.
* A destination drive named ``production`` is remounted read-write for the duration
  and remounted read-only on exit, through ``sudo``. If either remount fails the script
  stops and says so.
* **Syncing a versioned volume set is not enough by itself.** The ``documents/`` and
  ``_volinfo/`` entries belong to the unversioned name, so that has to be synced too.
  Two of the six say so when they finish -- ``pdsdata-sync-volset.sh`` and
  ``pdsdata-sync-volume.sh`` print a ``>>> NOTE:`` to that effect as their last act. The
  other four print nothing about it, so the caveat is one to remember rather than one to
  be reminded of.

Each script walks the categories it covers in a fixed order -- for the full volume-set
sync, ``metadata``, ``previews``, ``calibrated``, ``diagrams`` and ``volumes``, and inside
each, the archives, checksums, checksums-archives, info shelves, archive info shelves,
link shelves, index shelves and finally the data itself -- and prints a
``**** holdings/... ****`` banner before each. A category the source does not have is
skipped silently.
