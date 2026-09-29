Subsystem Reference
===================

This chapter states, for each module directly under ``src/pdsfile/``, what the module
is responsible for and what a developer must not break while editing it. The
:doc:`dev_guide_architecture` chapter draws how the pieces fit; the
:doc:`/api/index` documents every member. Each mixin's class docstring additionally
enumerates every attribute its methods read or write on a
:class:`~pdsfile.pdsfile.PdsFile` object or class -- its state contract -- and that
enumeration, not this chapter, is the authoritative fine print.

Invariants that cross every module
----------------------------------

Five rules hold everywhere, and most subtle bugs in this package are a violation of
one of them.

**Logical versus absolute paths.** Every file is named two ways. The *absolute path*
says where the file sits on this machine; the *logical path* is what follows the
holdings directory, starting at a category name such as ``volumes/``, and is identical
on every machine hosting the same holdings. Cache keys are lower-cased logical paths;
info and link shelf keys are interior paths (the tail of the logical path below the
bundle; index shelves are keyed by row selection instead);
everything user-facing prefers logical paths. Converting logical to absolute is the
hard direction, because a machine can host several holdings directories --
:func:`~pdsfile._path_utils.abspath_for_logical_path` is the one place that search
lives.

**The ranks and vols bookkeeping.** For each category, the class cache holds
``$RANKS-<category>/`` (lower-cased bundle set or bundle name, to the sorted list of
integer version ranks) and ``$VOLS-<category>/`` (the same keys, to the directory path
per rank). Everything that resolves a version -- a path with no version suffix, the
:attr:`~pdsfile._properties._PropertiesMixin.version_ranks` property, the OPUS
constructors -- reads these tables, and
``_update_ranks_and_vols`` in :mod:`pdsfile.pdsfile` maintains them as objects are
built. Code that constructs objects by a route that skips the bookkeeping produces a
tree in which the newest version is invisible.

**Merged versus physical category directories.** The cache entry for a category name
(``volumes``, ``metadata``, ...) is a *merged* directory built by
:meth:`~pdsfile.pdsfile.PdsFile.new_merged_dir`: its child list is the union of that
category's children across every preloaded holdings directory, and it has no single
absolute path of its own. Everything below it is *physical* -- one file, one path.
Code that treats a category-level object like a physical directory (asking for its
shelf, its checksum, its absolute path) is wrong by construction, and the properties
that would answer generally special-case
:attr:`~pdsfile.pdsfile.PdsFile.is_category_dir`.

**The shelves-only switch is class-level global state.** ``SHELVES_ONLY`` is a class attribute,
``False`` by default, flipped by :meth:`~pdsfile.pdsfile.PdsFile.use_shelves_only`; it
changes what the four filesystem questions in :mod:`pdsfile._local_fs` answer for
*every* object of that class in the process, not per object or per call. The test
suite runs the whole session in one mode for the same reason (``--mode`` in
:doc:`dev_guide_testing`). Anything cached while one setting was live -- existence
answers, constructed objects -- describes that setting's view of the tree.

**Thread safety is a single-process, single-thread assumption.** Class-level mutable
state is everywhere: the object cache, the shelf cache and its access stamps, the
memoized existence and glob caches, ``LOCAL_PRELOADED``, the icon registry in
:mod:`pdsfile.pdsviewable`. None of it is locked. One process serving one request at a
time is the design point; sharing across *processes* is what
:class:`~pdsfile.pdscache.MemcachedCache` exists for, and its blocking protocol
coordinates whole preloads, not fine-grained access.

``pdsfile.pdsfile`` -- the class statement and the object lifecycle
-------------------------------------------------------------------

:mod:`pdsfile.pdsfile` holds the ``class PdsFile`` statement, every class attribute
(the rule-table slots the subclasses fill, the shared caches, the registries), the
``__init__`` that creates the ~40 private slots the lazy properties fill, and the
constructors: :meth:`~pdsfile.pdsfile.PdsFile.child`,
:meth:`~pdsfile.pdsfile.PdsFile.parent`,
:meth:`~pdsfile.pdsfile.PdsFile.from_abspath`,
:meth:`~pdsfile.pdsfile.PdsFile.from_logical_path`,
:meth:`~pdsfile.pdsfile.PdsFile.from_path`,
:meth:`~pdsfile.pdsfile.PdsFile.from_lid` and their relatives, plus
:meth:`~pdsfile.pdsfile.PdsFile.new_pdsfile`,
:meth:`~pdsfile.pdsfile.PdsFile.new_merged_dir` and
:meth:`~pdsfile.pdsfile.PdsFile.new_index_row_pdsfile`. The contract every
constructor honors: consult ``cls.CACHE`` first; select the rule subclass through
``SUBCLASSES``/``VOLSET_TRANSLATOR`` when crossing into a bundle set; call
``_complete`` so the finished object is cached and the ranks/vols tables are updated.
Calling a class directly yields a blank object with no path, which is a building block
for the constructors and not a usable value.

The nine mixins
---------------

:mod:`pdsfile._associations` -- ``_AssociationsMixin``
    Given one file, the files that go with it elsewhere in the tree: the family of
    :meth:`~pdsfile._associations._AssociationsMixin.associated_abspaths`,
    :meth:`~pdsfile._associations._AssociationsMixin.associated_logical_paths` and
    :meth:`~pdsfile._associations._AssociationsMixin.associated_pdsfiles`,
    and :meth:`~pdsfile._associations._AssociationsMixin.associated_parallel`
    for the single most similar file in one
    parallel category, optionally at another version. Two mechanisms produce answers:
    the rule modules' ``ASSOCIATIONS`` tables map a logical path to wildcard patterns,
    and where no rule applies the same interior path is looked for in the parallel
    tree, falling back to the deepest part of it that exists. Contract: answers are
    lists (one data file can have many previews; one metadata table covers many data
    files), and the parallel lookup caches its answer on the object it resolved the
    question against, which is not always the object it was asked about.

:mod:`pdsfile._derived_paths` -- ``_DerivedPathsMixin``
    Pure path arithmetic from a file's own parts to the paths derived from it: the
    checksum file that covers it, the archive file that contains it, the directory
    each was made from, and the maintenance tools' log paths. Contract: these methods
    *construct* paths and do not check existence; asking for a checksum path of a
    file that has none (a checksum file itself, ``documents/``) raises ``ValueError``.
    The log-path builders carry a time tag, pinned for the duration of a run by a
    context manager so that one run's log lands under one tag everywhere it is
    written.

:mod:`pdsfile._index_rows` -- ``_IndexRowsMixin``
    The pseudo-files that stand for one row of an index table, with paths of the form
    ``.../table.tab/selection``. Opens index shelves
    (:meth:`~pdsfile._index_rows._IndexRowsMixin.get_indexshelf`), completes a
    partial selection to an exact key
    (:meth:`~pdsfile._index_rows._IndexRowsMixin.find_selected_row_key`), builds the
    child object for a row
    (:meth:`~pdsfile._index_rows._IndexRowsMixin.child_of_index`), and maps a row
    back to the data file it
    describes. Contract: a row object has no absolute path of its own -- it is
    addressable, cacheable and describable, but not a file on disk.

:mod:`pdsfile._local_fs` -- ``_LocalFsMixin``
    The four filesystem questions the package asks --
    :meth:`~pdsfile._local_fs._LocalFsMixin.os_path_exists`,
    :meth:`~pdsfile._local_fs._LocalFsMixin.os_path_isdir`,
    :meth:`~pdsfile._local_fs._LocalFsMixin.os_listdir`,
    :meth:`~pdsfile._local_fs._LocalFsMixin.glob_glob` -- and the one mapping they need
    (``_non_checksum_abspath``, from a checksum file back to what it covers). Under
    ``SHELVES_ONLY`` the same four questions are answered from the info shelves, with
    the filesystem as fallback. Two caveats are the module's own: existence answers
    are memoized in an ``lru_cache`` of ``PATH_EXISTS_CACHE_SIZE`` (200) entries that
    is never invalidated, so a file created or deleted after the first question keeps
    its old answer until eviction; and shelf-backed answers match keys exactly, so
    they are case-sensitive whatever the filesystem is.

:mod:`pdsfile._opus` -- ``_OpusMixin``
    The OPUS-facing surface: :meth:`~pdsfile._opus._OpusMixin.from_opus_id` and
    :meth:`~pdsfile._opus._OpusMixin.from_filespec` resolve OPUS's identifiers to
    objects, and :meth:`~pdsfile._opus._OpusMixin.opus_products` returns, for one data
    product, every file OPUS should offer alongside it, grouped by product type. The
    tables that drive all three (``OPUS_ID``, ``OPUS_PRODUCTS``,
    ``OPUS_ID_TO_SUBCLASS``, ``FILESPEC_TO_BUNDLESET``, ...) live in the rule
    modules. Contract: ``opus_products`` keys are tuples describing each product
    group, and a key can also be the empty string for products that carry no OPUS
    type -- a consumer must not assume every key has the tuple shape.

:mod:`pdsfile._preload` -- ``_PreloadMixin``
    :meth:`~pdsfile._preload._PreloadMixin.preload` and everything it maintains; drawn
    and narrated in :doc:`dev_guide_architecture`. Also the module-level lifetime
    machinery re-exported through :mod:`pdsfile.preload_and_cache`. Contract: preload
    is idempotent per holdings directory (``$PRELOADED`` records what was walked); the
    walk stops below the bundle level; everything it stores is permanent.

:mod:`pdsfile._properties` -- ``_PropertiesMixin``
    The 64 derived properties: existence, size, dates, descriptions, view sets,
    labels, versions, OPUS naming. Most are lazy: the first access fills a private
    slot created by ``__init__`` and calls ``_recache()`` so the copy in the shared
    cache keeps the filled value (``filename_keylen`` is the one that fills its slot
    without recaching). Three contracts to keep in mind when editing: reading one
    property may fill others' slots (each docstring names which); a miss is stored as
    a value (an empty string or list is an answer, not an absence, so a wrong answer
    persists); and merged directories and index rows are born with some slots
    pre-set, so not every body runs for every object.

:mod:`pdsfile._shelves` -- ``_ShelfMixin``
    Shelf path arithmetic, the shared open-shelf cache, and
    :meth:`~pdsfile._shelves._ShelfMixin.shelf_lookup`; drawn and narrated in
    :doc:`dev_guide_architecture`. Contract: the open-shelf cache and the remembered
    null-key values are shared class state on :class:`~pdsfile.pdsfile.PdsFile`;
    ``shelf_lookup`` on a bundle prefers the remembered entry, then the ``.py``
    sidecar (info shelves only), then the pickle; the ``eval()`` of a sidecar line is
    confined to ``_eval_null_key_record()``, whose trust boundary is the holdings
    tree itself.

:mod:`pdsfile._sorting` -- ``_SortingMixin``
    Order and bulk conversion.
    :meth:`~pdsfile._sorting._SortingMixin.sort_basenames` applies the rule modules'
    sort keys (labels next to data, newest version first, AAREADME on top);
    :meth:`~pdsfile._sorting._SortingMixin.split_basename` produces the parts those
    keys are built from; and the twelve
    ``<plural>_for_<plural>`` methods convert lists among the four namings of a file
    (object, absolute path, logical path, basename), each with the option to drop
    what does not exist. Contract: nothing here reads the filesystem except through
    :mod:`pdsfile._local_fs` and the ``exists`` property.

The plain modules
-----------------

:mod:`pdsfile._path_utils`
    Module functions, not a mixin: the absolute/logical conversions, category-list
    construction, case repair, size formatting, and the small join/abspath/glob
    primitives. Any function needing class configuration takes the class as an
    argument, so this module imports none of the modules that import it. It holds one
    piece of state: the memoized glob cache (``_GLOB_CACHE_SIZE`` entries), which,
    like the existence cache, is never invalidated.

:mod:`pdsfile.pdscache`
    :class:`~pdsfile.pdscache.DictionaryCache` and
    :class:`~pdsfile.pdscache.MemcachedCache` behind the do-nothing common base
    :class:`~pdsfile.pdscache.PdsCache`. The two are close but not substitutable --
    :meth:`~pdsfile.pdscache.DictionaryCache.delete_multi` works only on the
    dictionary flavor (the memcached version raises ``AttributeError`` on every
    call), :meth:`~pdsfile.pdscache.DictionaryCache.set_multi` differs in signature
    and defaults, a lifetime of ``None`` means different things, and only the
    memcached flavor accepts a bound method as a lifetime function -- and the
    module docstring is the catalogue of those differences. Contract for callers:
    treat entries as expiring unless stored with lifetime zero, and empty a
    dictionary cache only with :meth:`~pdsfile.pdscache.DictionaryCache.clear`.

:mod:`pdsfile.pdsviewable`
    :class:`~pdsfile.pdsviewable.PdsViewable` (one displayable image),
    :class:`~pdsfile.pdsviewable.PdsViewSet` (the same subject at several sizes,
    queried by width, height, bounding box or name), and the icon registry
    ``ICON_SET_BY_TYPE`` that :func:`~pdsfile.pdsviewable.load_icons` fills during a
    preload. Contract: a size lookup returns a scaled *copy* whose requested
    dimension is exact and whose other dimension is derived, so its numbers do not
    necessarily describe a file on disk, while its ``abspath`` and ``url`` always
    name the file that was chosen.

:mod:`pdsfile.preload_and_cache`
    The public face of the preload subsystem: nine re-exported names (the pause,
    resume and is-preloading calls, the lifetime function and its four constants,
    and ``DICTIONARY_CACHE_LIMIT``). It contains no logic; edits belong in
    :mod:`pdsfile._preload`.

:mod:`pdsfile` (the package initializer)
    Binds ``__version__``, :class:`~pdsfile.pdsfile.PdsFile`, and the public names of
    both subpackages -- including the side effect that matters: importing the package
    imports the rule modules, which is what populates the subclass registries. The
    two star imports in it, and the explicit aliased re-export of
    :class:`~pdsfile.pdsfile.PdsFile` above them, are load-bearing for the frozen
    public surface; do not "clean them up".

The frozen surface
------------------

The public API -- everything reachable via ``import pdsfile``, as recorded in
``tests/api/api_manifest.json`` -- may not change at all. The freeze is mechanical:
``tests/api/test_api_freeze.py`` regenerates the manifest in a subprocess and diffs
it, and the manifest, the allowlist, the dumper and the checker may not be edited to
make a diff vanish. New internals are given underscore-prefixed names, which the
freeze does not see. The companion tests in ``tests/api/`` pin the mixin mechanics
this chapter relies on: no two mixins define the same name, the base order stays
alphabetical, the class statement stays in :mod:`pdsfile.pdsfile`, and no mixin
module imports it back at module level (a method that needs the class object uses a
function-local import, which is the sanctioned pattern and the one
:meth:`~pdsfile._opus._OpusMixin.opus_products` uses).
