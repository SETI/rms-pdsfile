Architecture
============

Almost everything this package does is a method or property of one class.
:class:`~pdsfile.pdsfile.PdsFile` stands for a single file or directory in a PDS
holdings tree, and it answers every question the package can answer: where the file
sits in the tree's taxonomy, what metadata describes it, which files go with it, which
images display it, and where its checksum, archive and log counterparts live. The class
is assembled from nine mixins, one per subject area, each in a private module of its
own; a caller never names a mixin, and every name a mixin defines is reachable through
:class:`~pdsfile.pdsfile.PdsFile`.

Class hierarchy
---------------

.. mermaid::

    classDiagram
        class PdsFile {
            +CACHE
            +SUBCLASSES
            +VOLSET_TRANSLATOR
            +from_abspath(abspath)
            +from_logical_path(path)
            +from_path(path)
            +child(basename)
            +parent()
            +preload(holdings_list)
        }
        class Pds3File {
            +PDS_HOLDINGS holdings
            +BUNDLE_DIR_NAME volumes
            +volume and volset aliases
        }
        class Pds4File {
            +PDS_HOLDINGS pds4-holdings
            +BUNDLE_DIR_NAME bundles
        }
        _AssociationsMixin <|-- PdsFile
        _DerivedPathsMixin <|-- PdsFile
        _IndexRowsMixin <|-- PdsFile
        _LocalFsMixin <|-- PdsFile
        _OpusMixin <|-- PdsFile
        _PreloadMixin <|-- PdsFile
        _PropertiesMixin <|-- PdsFile
        _ShelfMixin <|-- PdsFile
        _SortingMixin <|-- PdsFile
        PdsFile <|-- Pds3File
        PdsFile <|-- Pds4File
        class COISS_xxxx
        class VGISS_xxxx
        class Pds3Rules["...23 more rule subclasses"]
        class cassini_iss
        class uranus_occs_earthbased
        class Pds4Rules["...4 more rule subclasses"]
        Pds3File <|-- COISS_xxxx
        Pds3File <|-- VGISS_xxxx
        Pds3File <|-- Pds3Rules
        Pds4File <|-- cassini_iss
        Pds4File <|-- uranus_occs_earthbased
        Pds4File <|-- Pds4Rules

The base class and its mixins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`~pdsfile.pdsfile.PdsFile` is abstract in practice, though not formally: it
carries all of the shared behavior, but the configuration that makes path parsing work
is missing or ``None`` on the base class -- the rule and translator tables are ``None``
slots the subclasses fill, and the bundle-set name regular expressions exist only on
the subclasses -- so real
objects are always instances of :class:`~pdsfile.pds3file.Pds3File`,
:class:`~pdsfile.pds4file.Pds4File` or one of their rule subclasses. Objects are never
built by calling a class either; the constructors are the class and instance methods
shown in the diagram -- :meth:`~pdsfile.pdsfile.PdsFile.from_abspath`,
:meth:`~pdsfile.pdsfile.PdsFile.from_logical_path`,
:meth:`~pdsfile.pdsfile.PdsFile.from_path`, :meth:`~pdsfile.pdsfile.PdsFile.child` and
:meth:`~pdsfile.pdsfile.PdsFile.parent` and their relatives -- each of which reads the
class-level cache, directly or through the ``_complete`` step every construction ends
with, so that one object per path survives and a cached object's filled-in values are
not recomputed.

The nine mixin bases hold methods and properties only: no mixin defines ``__init__``
or any per-object state of its own (the one stateful thing a mixin body carries is
the memoizing decorator on the existence check, documented with its module in
:doc:`dev_guide_subsystems`), every attribute a mixin method reads or writes is defined on
:class:`~pdsfile.pdsfile.PdsFile` (or on a subclass) and reached through ``self`` or
``cls`` at run time, and each mixin's class docstring enumerates exactly which
attributes those are. That contract is what lets the nine live in separate modules
without a module-level import of :mod:`pdsfile.pdsfile` back (a method that needs the
class object itself uses a function-local import instead): :mod:`pdsfile._local_fs`
can call into :mod:`pdsfile._shelves`, and :mod:`pdsfile._properties` into both,
through attribute lookup on the object. The mixins are, in their base-class order (which is
alphabetical, and which ``tests/api/test_mixin_collisions.py`` pins along with the rule
that no two mixins define the same name):
:class:`~pdsfile._associations._AssociationsMixin`,
:class:`~pdsfile._derived_paths._DerivedPathsMixin`,
:class:`~pdsfile._index_rows._IndexRowsMixin`,
:class:`~pdsfile._local_fs._LocalFsMixin`, :class:`~pdsfile._opus._OpusMixin`,
:class:`~pdsfile._preload._PreloadMixin`,
:class:`~pdsfile._properties._PropertiesMixin`,
:class:`~pdsfile._shelves._ShelfMixin` and
:class:`~pdsfile._sorting._SortingMixin`. Because no name is defined twice, the
method resolution order never has to break a tie and the alphabetical order carries no
behavior; :doc:`dev_guide_subsystems` walks each mixin's contract in turn.

The two concrete subclasses
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`~pdsfile.pds3file.Pds3File` and :class:`~pdsfile.pds4file.Pds4File` say what
kind of tree is being read. Each names its holdings directory (``holdings`` versus
``pds4-holdings``), its data category (``volumes`` versus ``bundles``), the
environment variable that locates the tree (``PDS3_HOLDINGS_DIR`` versus
``PDS4_HOLDINGS_DIR``), the regular expressions a bundle set and bundle name must
match, and the rule tables, which each subclass fills from its own ``rules``
subpackage. Each also assigns ``CACHE``, ``LOCAL_PRELOADED`` and ``SUBCLASSES`` in its
own class body rather than inheriting them, which is what keeps the two trees' state
apart: preloading a PDS3 tree fills ``Pds3File.CACHE`` and leaves ``Pds4File.CACHE``
alone. :class:`~pdsfile.pds3file.Pds3File` additionally carries the PDS3 vocabulary --
``volume`` for bundle and ``volset`` for bundle set -- as one-line aliases forwarding
to the bundle-named members.

The rule subclasses
~~~~~~~~~~~~~~~~~~~

Below each concrete class sit the rule subclasses, one per bundle set family, defined
in the modules under :mod:`pdsfile.pds3file.rules` and :mod:`pdsfile.pds4file.rules`.
``Pds3File.SUBCLASSES`` holds 25 of them plus the ``default`` entry (which is
:class:`~pdsfile.pds3file.Pds3File` itself), and ``Pds4File.SUBCLASSES`` holds 6 plus
its ``default``. A rule subclass adds no behavior of its own beyond its tables: it
installs dataset-specific rows in front of, behind, or in place of the inherited rule
tables, and (in a few modules) overrides ``FILENAME_KEYLEN``. Every object built for a
path inside a recognized bundle set is an instance of that set's rule subclass, which
is how one lookup on ``self`` finds the right table with no dispatch code anywhere.
The selection mechanism is drawn at the end of this chapter.

The cache layers
----------------

Building a :class:`~pdsfile.pdsfile.PdsFile` costs filesystem calls and shelf reads,
so every constructor caches what it builds and consults the cache first. The cache is
class state -- one per concrete class -- and it holds two kinds of entry: the objects
themselves, keyed by lower-cased logical path, and a small set of permanent
bookkeeping entries whose keys begin with ``$``.

.. mermaid::

    flowchart TD
        P["preload()"] -->|"pylibmc importable and<br/>a nonzero memcached port"| M["MemcachedCache<br/>(shared across processes,<br/>values pickled, writes buffered)"]
        P -->|otherwise| D["DictionaryCache<br/>(one process, plain dict,<br/>trimmed to a size limit)"]
        M --> CACHE[("cls.CACHE")]
        D --> CACHE
        CACHE --> PERM["permanent entries (lifetime 0)<br/>$RANKS-&lt;category&gt;/ : version ranks<br/>$VOLS-&lt;category&gt;/ : paths per version<br/>$VOLINFO-... : bundle descriptions<br/>$PRELOADED : holdings already walked<br/>merged category dirs, and everything<br/>stored during a preload walk"]
        CACHE --> OBJ["PdsFile objects, keyed by<br/>lower-cased logical path"]
        OBJ --> L7A["bundle sets and bundles:<br/>7 days"]
        OBJ --> L7B["directories named *data:<br/>7 days"]
        OBJ --> L2["other directories: 2 days"]
        OBJ --> L12["files, index rows and<br/>rendered pages: 12 hours"]

Both cache classes implement the same dictionary-like interface, and each implements
it independently: their common base :class:`~pdsfile.pdscache.PdsCache` has no methods
and no attributes, existing only so the two share a type an ``isinstance()`` can test
for. :class:`~pdsfile.pdscache.DictionaryCache` keeps values in a
plain dictionary in this process: entries expire lazily, permanent entries are exempt
from trimming, and trimming discards the soonest-to-expire entries once the count
exceeds the limit by a slop margin. :class:`~pdsfile.pdscache.MemcachedCache` keeps
values in a memcached server shared across processes: writes are buffered locally and
flushed in batches, a copy of every permanent entry is kept locally and restored to
the server if one goes missing, and the whole cache can be blocked for exclusive use
during a preload. It is reached only when ``pylibmc`` is importable and a nonzero port
is supplied (Viewmaster's deployment does; nothing in this repository's test
environment does), so no test here reaches a live memcached server -- the memcached
coverage that exists runs against a stand-in client.

The lifetimes in the diagram come from
:func:`~pdsfile._preload.cache_lifetime_for_class` (re-exported as
:mod:`pdsfile.preload_and_cache`'s public name), the lifetime function
every cache in the package is built with: bookkeeping entries live forever, bundle sets, bundles and ``*data``
directories live ``LONG_FILE_CACHE_LIFETIME`` (7 days), other directories
``SHORT_FILE_CACHE_LIFETIME`` (2 days), and everything else -- including the rendered
HTML pages Viewmaster stores -- ``DEFAULT_FILE_CACHE_LIFETIME`` (12 hours). During a
preload the walk stores everything it visits with an explicit lifetime of zero, so the
top of the tree never expires whichever bucket it would otherwise fall into.

The ``$RANKS`` and ``$VOLS`` entries are the version bookkeeping: for each category,
``$RANKS-<category>/`` maps a lower-cased bundle set or bundle name to the sorted list
of its version ranks (an integer per version, higher is later), and
``$VOLS-<category>/`` maps the same keys to the directory path of each version. They
are created empty at preload and updated by ``_update_ranks_and_vols`` as objects are
built, and they are what lets a path with no version suffix resolve to the latest
version. The ``$VOLINFO-`` entries hold the descriptions read from the ``_volinfo``
tables of a PDS3 tree; ``$PRELOADED`` is the list of holdings directories already
walked, which is what makes a second :meth:`~pdsfile._preload._PreloadMixin.preload` call a
no-op.

The shelf subsystem
-------------------

A holdings tree ships **shelf files**: pickled dictionaries, written by the
maintenance tools, that answer questions about files without opening them. Three kinds
exist, in three parallel trees named after them. An **info** shelf
(``_infoshelf-<category>/``) records each file's size, child count, modification time,
checksum and image dimensions; a **link** shelf (``_linkshelf-<category>/``) records
which files each PDS3 label points at; an **index** shelf
(``_indexshelf-<category>/``) records which rows of an index table each selection key
covers. An info or link shelf covers one bundle (or one bundle set of archives) and is
keyed by interior path; an index shelf covers one index table and is keyed by row
selection key.

.. mermaid::

    flowchart TD
        Q["shelf_lookup(shelf_type)"] --> PK["shelf_path_and_key():<br/>path arithmetic from bundle set,<br/>bundle and interior path"]
        PK --> NK{"key is '' <br/>(the bundle itself)?"}
        NK -->|yes| NKV{"already in<br/>SHELF_NULL_KEY_VALUES?"}
        NKV -->|yes| A1["answer from memory"]
        NKV -->|"no, and shelf_type<br/>is 'info'"| SIDE["read line 2 of the .py sidecar,<br/>eval() the record, remember it"]
        SIDE --> A1
        NK -->|no| GS["_get_shelf(shelf_path)"]
        NKV -->|"no, other types"| GS
        GS --> OPEN{"already in<br/>SHELF_CACHE?"}
        OPEN -->|yes| KEYED["shelf[key]"]
        OPEN -->|no| LOAD["open + pickle.load the whole<br/>shelf, sort by key, cache it,<br/>trim by SHELF_ACCESS stamps"]
        LOAD --> KEYED

:class:`~pdsfile._shelves._ShelfMixin` provides the three layers the diagram shows:
the path arithmetic that turns a file's path into a shelf path and a key within it
(:meth:`~pdsfile._shelves._ShelfMixin.shelf_path_and_lskip`,
:meth:`~pdsfile._shelves._ShelfMixin.shelf_path_and_key`, and the
object-free :meth:`~pdsfile._shelves._ShelfMixin.shelf_path_and_key_for_abspath`); the
cache of open shelves, which is class state on :class:`~pdsfile.pdsfile.PdsFile`
shared by every subclass, bounded by ``SHELF_CACHE_SIZE`` plus ``SHELF_CACHE_SLOP``
and trimmed by the access stamps in ``SHELF_ACCESS``; and the lookup that puts the two
together, :meth:`~pdsfile._shelves._ShelfMixin.shelf_lookup`.

The sidecar branch is the one non-obvious edge. Every info shelf ``.pickle`` is
written alongside a readable ``.py`` sidecar holding the same dictionary as Python
source, and the sidecar's second line is the entry for the bundle itself (the null
key). A question about a bundle -- which is what a preload asks over and over -- is
answered by reading that one line and evaluating it with ``eval()``, instead of
unpickling the whole shelf; the parse and its trust boundary are isolated in
``_eval_null_key_record()`` in :mod:`pdsfile._shelves`. The answers are remembered in
``SHELF_NULL_KEY_VALUES``, which is never trimmed, so closing a shelf does not forget
what was learned about its bundle.

One quirk of the trim is worth knowing when reading cache behavior in tests:
``SHELF_ACCESS_COUNT`` is an integer, so incrementing it rebinds it onto the class the
call was made on -- normally a rule subclass -- and each such class counts from its
own zero into the one shared ``SHELF_ACCESS`` dictionary. The trim order is therefore
the activity of whichever class opened each shelf, not the order of last use across
the tree.

The shelves matter beyond speed: under the ``SHELVES_ONLY`` setting (see
:doc:`dev_guide_subsystems`), the filesystem layer answers existence, directory and
listing questions from the info shelves, so the package can serve a tree that is
described but not physically present.

The preload
-----------

A process that will serve many requests walks the top of each holdings tree once at
startup and keeps what it found. That walk is
:meth:`~pdsfile._preload._PreloadMixin.preload`, a class method called on
:class:`~pdsfile.pds3file.Pds3File` or :class:`~pdsfile.pds4file.Pds4File` with one or
more holdings directories.

.. mermaid::

    sequenceDiagram
        participant C as Caller
        participant F as Pds3File (cls)
        participant K as cls.CACHE
        participant H as holdings tree
        C->>F: preload(holdings_list, port=0)
        F->>F: choose cache (MemcachedCache if pylibmc and a port, else DictionaryCache) and set DEFAULT_CACHING
        F->>K: get_now('$PRELOADED')
        alt every holdings directory already listed
            F-->>C: return (memcached: re-read permanent values first)
        end
        F->>K: wait_and_block(), then pause()
        F->>K: set merged directory per category (lifetime 0)
        F->>K: create empty $RANKS-/$VOLS- per category where absent
        loop per holdings directory not yet preloaded
            F->>H: load_volume_info(): read _volinfo/*.txt (skipped for Pds4File)
            F->>K: set $VOLINFO- entries (lifetime 0)
            loop per category directory that exists
                F->>H: from_abspath(category, caching='all', lifetime=0)
                F->>H: _preload_dir(): walk category, bundle sets, bundles, then stop
                F->>K: cache each directory visited (lifetime 0)
            end
            F->>H: load_icons() from _icons/
        end
        F->>K: set('$PRELOADED', ...), resume(), unblock(flush=True)
        F->>F: probe case sensitivity, set FS_IS_CASE_INSENSITIVE

Three properties of the walk shape everything downstream. It is **shallow**: it
constructs the children of every bundle set, so every bundle is cached, and it goes no
deeper -- anything inside a bundle is built on demand later. It is **permanent**:
everything it caches is stored with a lifetime of zero. And it is **merged**: for each
category there is one cache entry, built by
:meth:`~pdsfile.pdsfile.PdsFile.new_merged_dir`, whose children are the union of that
category's children across every holdings directory passed in, which is what makes
several physical trees look like one logical tree. The merged entries also exist
before any preload:
:meth:`~pdsfile._preload._PreloadMixin.cache_category_merged_dirs` runs at import
time and creates an empty merged directory for each category that has none, so a tree
that is never preloaded still has them. The preload itself does not go through that
method: it rebuilds every category's merged directory unconditionally, discarding
whatever the import-time call left there.

The cache is blocked and paused for the duration and released in a ``finally`` block,
so a preload that fails part way does not leave a shared cache blocked. On a memcached
cache, a second process arriving during the walk waits on the block; a process whose
shared cache has been trimmed or restarted is repaired by
:meth:`~pdsfile._preload._PreloadMixin.get_permanent_values`, which re-reads the
bookkeeping entries and preloads again if any is missing.

Rules resolution: from volume set name to subclass
--------------------------------------------------

Every constructor funnels subclass selection through one method:
:meth:`~pdsfile.pdsfile.PdsFile.new_pdsfile`, called with the bundle set name as its
key whenever a path crosses into a bundle set.

.. mermaid::

    flowchart TD
        A["child() / from_abspath() / from_path():<br/>path enters a bundle set,<br/>e.g. volumes/COISS_2xxx"] --> B["class_key = bundle set name<br/>e.g. 'COISS_2xxx'"]
        B --> C["new_pdsfile(key)"]
        C --> D{"key in cls.SUBCLASSES?"}
        D -->|yes| E["cls = SUBCLASSES[key]"]
        D -->|no| F["key2 = VOLSET_TRANSLATOR.first(key)<br/>e.g. 'COISS_2xxx' -> 'COISS_xxxx'"]
        F --> G["cls = SUBCLASSES[key2]"]
        E --> H["blank object of the rule subclass,<br/>path fields copied from the parent"]
        G --> H
        R["import pdsfile.pds3file:<br/>each rule module prepends its regex to<br/>VOLSET_TRANSLATOR and registers itself<br/>in SUBCLASSES; 'default' maps to Pds3File"] -.-> D
        R -.-> F

The two tables are populated at import time. ``pdsfile/pds3file/__init__.py`` first
registers :class:`~pdsfile.pds3file.Pds3File` itself under the key ``default``, then
imports the rule modules; each rule module, as a side effect of its class body and
module tail, prepends one entry to ``VOLSET_TRANSLATOR`` -- a regular expression
mapping its family of bundle set names to its registry key, such as
``COISS_[0123x]xxx`` to ``COISS_xxxx`` -- and assigns its class into ``SUBCLASSES``
under that key. The base class's own ``VOLSET_TRANSLATOR`` ends with a catch-all
mapping everything to ``default``, so the lookup cannot fail to produce a key; a
bundle set no rule module claims resolves to the concrete class itself, with the
default rule tables. :mod:`pdsfile.pds4file` does the same with its own registry.

At lookup time, :meth:`~pdsfile.pdsfile.PdsFile.child` derives the key from the
parent's own ``bundleset`` where the parent is already inside one, or by matching the
child's basename against ``BUNDLESET_PLUS_REGEX_I`` at category level. A version
suffix such as ``_v1.0`` or ``_peer_review`` is accepted by that match but excluded
from the group the key is read from, and the ``bundleset`` attribute strips it too,
so ``COISS_2xxx_v1`` yields the same key as ``COISS_2xxx``. Every object below a
bundle set lands on the same subclass by the same route: a child of a
:class:`~pdsfile.pds3file.rules.COISS_xxxx.COISS_xxxx` object derives the same
``bundleset`` key from its parent, translates to the same registry entry, and is
built by the same class.

This chapter is the map; :doc:`dev_guide_subsystems` states each module's contract,
and :doc:`dev_guide_extending_rules` walks the registration machinery from the other
side, as a recipe for adding a rule module. The full API surface drawn here is
documented in the :doc:`/api/index`.
