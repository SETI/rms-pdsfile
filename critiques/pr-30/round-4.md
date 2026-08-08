# PR-30 round 4: the 10 pds4 rule modules and the seven functions

Second independent read. Slice: `src/pdsfile/pds4file/rules/*.py` (10 modules), plus
`GO_0xxx.opus_prioritizer`, `NHxxxx_xxxx.opus_prioritizer`, `RPX_xxxx.FILENAME_KEYLEN`,
`COVIMS_0xxx.FILENAME_KEYLEN`, `COISS_xxxx.FILENAME_KEYLEN`, `COUVIS_0xxx.DATA_SET_ID`
and `COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH`.

## What I read and how

I read `git show d108bae` first and treated every line it added to my files as unverified.
Then the rest of the prose. Almost nothing here was settled by reading alone; the
findings below came from instrumentation:

- **AST comparison of table source segments.** Extracted every top-level `Assign` from
  each pds4 module and from `pds3file/rules/COISS_xxxx.py` and
  `pds3file/rules/__init__.py`, and compared `ast.get_source_segment` text, to settle the
  "byte-identical" and "20 identical / three differ / three have no counterpart" claims.
- **Running the translators.** Imported the package with `PYTHONPATH=src`,
  `PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings`,
  `PDS4_HOLDINGS_DIR=/seti/opus/pdsdata/pds4-holdings`, and ran
  `DESCRIPTION_AND_ICON`, `VERSIONS`, `INFO_FILE_BASENAMES`, `FILESPEC_TO_BUNDLESET`,
  `LID_AFTER_DSID`, `OPUS_PRODUCTS`, `opus_id`, `opus_id_to_primary_logical_path` and the
  per-module tables over real and synthetic `bundles/` paths.
- **Measuring the merge order.** For each subclass, located the module's own rule tuples
  inside the merged translator's `.tuples` list and recorded whether they land at index 0
  or after the inherited ones.
- **Exercising the two prioritizers** with stub objects to reproduce every exception the
  `Raises:` sections name.
- **The holdings.** `_volinfo/RPX_xxxx.txt`; the `uranus_occs_earthbased` and
  `cassini_uvis_solarocc_beckerjarmak2023` bundle trees and their `readme.txt` files; a
  `find` over `volumes/COVIMS_0xxx` for cube basenames.
- **Mechanical gates**, run over docstring line spans only: unicode punctuation, >90
  columns, British spelling, double space after a period, time-anchored words. All clean;
  no findings from these.

The four pds4 bundle sets absent from the limited holdings copy (`cassini_iss`,
`cassini_vims`, the fring mosaics, the spokes bundle) were checked against module
comments and regexes only, and their absence is not treated as evidence.

---

## Defects in sentences the correction commit introduced

### C1. `pds4file/rules/__init__.py`: "added in front" is false for `ASSOCIATIONS`

> Each dataset module in this package builds its own tables and installs them on the
> subclass. Most are added in front of the table here, so a lookup tries the
> dataset-specific patterns first and falls through to these

The `ASSOCIATIONS` dict is merged the other way round. Every module writes
`ASSOCIATIONS['bundles'] += associations_to_bundles`, which is
`inherited + module`, and `TranslatorByRegex.append` returns
`TranslatorByRegex(self.tuples + translator.tuples)` — the *inherited* rules first.
Measured, by locating each module's own tuple inside the merged `.tuples`:

| module | `bundles` | `metadata` | `documents` | `previews` |
|---|---|---|---|---|
| cassini_iss | default first (own at 1) | default first (own at 4) | default first (own at 5) | own first |
| fring mosaics | default first | default first | default first | own first |
| uvis solarocc | default first | default first | default first | own first |
| cassini_vims | default first | default first | default first | own first |
| uranus occs | default first | default first | default first | own first |

Only the three keys whose default is a `NullTranslator` (`previews`, `calibrated`,
`diagrams`) put the module's rules first, and that is because
`NullTranslator.append(x)` returns `x` outright. For `bundles`, `metadata` and
`documents` the PDS3-shaped default patterns are tried before anything the dataset
module wrote. The previous version of this sentence was wrong in a different way; the
correction did not reach this case.

### C2. The rewritten class-docstring boilerplate repeats C1, in five modules

> The class body wires this module's rule tables onto the class attributes ``Pds4File``
> reads. Where a table is added to the inherited one, a lookup tries this module's
> patterns first and falls through to the defaults; where it is assigned outright there
> is no fall-through.

Same measurement. The sentence is true for `DESCRIPTION_AND_ICON`, `VIEW_OPTIONS`,
`NEIGHBORS`, `SORT_KEY`, `OPUS_TYPE`, `OPUS_FORMAT`, `OPUS_PRODUCTS`, `ARCHIVE_PATHS`,
`ARCHIVE_DIRS` and the two `Pds4File`-level tables, and false for the three
`ASSOCIATIONS` keys, in `cassini_iss.py`,
`cassini_iss_fring_mosaics_rsfrench2025.py`,
`cassini_uvis_solarocc_beckerjarmak2023.py`, `cassini_vims.py` and
`uranus_occs_earthbased.py`. (The spokes module sets no `ASSOCIATIONS`, so its copy of
the boilerplate is correct.) This is the sentence the commit message calls "the largest
single one"; it was corrected for the assigned-outright case and left wrong for the
added-behind case.

### C3. `pds4file/rules/__init__.py`: "Two of the copied tables cannot match a PDS4 path at all"

> Two of the copied tables cannot match a PDS4 path at all: ``FILESPEC_TO_BUNDLESET``
> requires an upper-case volume identifier, and ``LID_AFTER_DSID`` keys on ``volumes/``.
> The others still answer for PDS4 paths, through their least specific rules rather than
> through anything written for a bundle

Three, not two. `OPUS_PRODUCTS` is one of the 20 byte-identical copies and its sole rule
is `(r'volumes/([A-Z0-9a-z]+_[A-Z0-9a-z]+).*', 0, [r'documents/\1/*.[!lz]*'])`, anchored on
`volumes/`. Run over six real `bundles/`, `previews/` and `metadata/` PDS4 paths it
returns `None` every time.

The second sentence is also false for five more copied tables:
`CROSS_PDS3_PDS4_PRODUCTS`, `OPUS_ID`, `OPUS_ID_TO_PRIMARY_LOGICAL_PATH` and
`OPUS_ID_TO_SUBCLASS` are copied and identical but hold zero entries, and `DATA_SET_ID`
is a `NullTranslator`. None of them "still answers for PDS4 paths"; they answer for
nothing.

### C4. `pds4file/rules/__init__.py`: the "Directory" example is wrong twice over

> ``DESCRIPTION_AND_ICON`` falls to its closing extension-only block, so a ``.tab`` file
> is an "ASCII table" and a bundle directory is a "Directory"

The `.tab` half is right. The other half fails on both counts.

(a) The `('Directory', 'FOLDER')` answer comes from `(r'.*/[^\.]+', 0, ...)`, one of the
three closing catch-alls that sit *after* the block the table's own comment labels
"Standard file extensions, if nothing else worked". It keys on the last component having
no dot, not on an extension.

(b) A bundle or bundle-set directory never reaches `DESCRIPTION_AND_ICON` at all.
`_properties.description` branches on `elif self.is_bundleset or self.is_bundle:` and
reads `self._volume_info`. Measured:

```
bundles/uranus_occs_earthbased                        desc='' icon='UNKNOWN'
bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm desc='' icon='UNKNOWN'
```

The raw translator does return `('Directory', 'FOLDER')` for those two paths; the class
that reads the table never asks it.

### C5. `pds4file/rules/__init__.py`: the 20/3/3 arithmetic does not cover every assignment

> Comparing every top-level assignment against `pds3file/rules/__init__.py`: 20 are
> identical, three differ (``ASSOCIATIONS``, ``DESCRIPTION_AND_ICON`` and ``OPUS_TYPE``)
> and three have no PDS3 counterpart

The module has 27 top-level `Assign` nodes, not 26. `__all__` is the 27th and it differs
too (four pds4 bundle set names against the pds3 volume set list). The three named
categories are otherwise exactly right; the sentence's own quantifier, "every top-level
assignment", is what it fails.

### C6. `pds4file/rules/__init__.py`: two adjacent corrected paragraphs contradict each other

Paragraph two puts `DESCRIPTION_AND_ICON` in the group that **differs** from the PDS3
table. Paragraph three then says "Two of the **copied** tables cannot match a PDS4 path
at all … **The others** still answer for PDS4 paths … `DESCRIPTION_AND_ICON` falls to its
closing extension-only block". `DESCRIPTION_AND_ICON` cannot be both not-copied and one
of the copied others. `VERSIONS` and `INFO_FILE_BASENAMES`, the two tables that share
that sentence with it, genuinely are copies.

### C7. `cassini_iss.py`: "Six of the eight key on PDS3 paths", and the next sentence says otherwise

> Six of the eight key on PDS3 paths -- on ``volumes/`` or on a COISS volume ID --
> rather than on ``bundles/cassini_iss``; … They describe the same Cassini ISS
> observations in their PDS3 locations: … ``opus_id_to_primary_logical_path`` resolves an
> OPUS ID to a path under ``volumes/COISS_1xxx`` or ``volumes/COISS_2xxx``.

Five key on PDS3 paths, not six. `opus_id_to_primary_logical_path`'s 52 patterns are all
of the form `co-iss-([nw]18n.*)`: it keys on an **OPUS ID** and *returns* a `volumes/`
path. Measured:

```
opus_id_to_primary_logical_path.first('volumes/COISS_2xxx/COISS_2001/data/x/N1234.IMG') -> None
opus_id_to_primary_logical_path.first('co-iss-n1460960653')
    -> volumes/COISS_2xxx/COISS_200[1-5]/data/*/N1460960653_*.IMG
```

The paragraph's closing sentence states this correctly, so the docstring contradicts
itself four lines apart. The count of six only works if the OPUS-ID table is miscounted
as path-keyed.

### C8. `cassini_vims.py`: same wrong six, plus a "cannot fire" that does fire

> Six of the eight key on PDS3 paths -- on ``volumes/`` or on a COISS volume ID -- so
> they cannot fire for a ``bundles/cassini_vims`` path

Two errors. `opus_id_to_primary_logical_path` is OPUS-ID-keyed, exactly as in C7. And
`description_and_icon_by_regex` **does** fire for a `bundles/` path: four of its rules
(`.*/thumbnail(/\w+)*`, `.*/thumbnail/.*\.(gif|jpg|…)`, `.*/(tiff|full)(/\w+)*`,
`.*/(tiff|full)/.*\.(tif|tiff|png)`) carry no `volumes/` or COISS anchor. Measured:

```
'bundles/cassini_vims/cassini_vims_saturn/browse_raw/thumbnail'
    -> ('Small browse images', 'BROWDIR')
'bundles/cassini_iss/cassini_iss_saturn/browse_raw/136xxxxxxx/13600xxxxx/thumbnail/x.jpg'
    -> ('Small browse image', 'BROWSE')
```

`cassini_iss.py`'s version of the sentence stops at "rather than on
`bundles/cassini_iss`" and so escapes this half; `cassini_vims.py` upgraded it to
"cannot fire", which is the claim the code refutes.

### C9. `uranus_occs_earthbased.py`: the same "cannot fire" over-claim

> Three of the five key on PDS3 ``volumes/COISS_*`` paths and so cannot fire for a
> ``bundles/uranus_occs_earthbased`` path

`description_and_icon_by_regex` is one of the three, and it fires:

```
'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/browse/full/x.png'
    -> ('Full-size browse image', 'BROWSE')
```

Every uranus bundle has a `browse/` collection on disk, so this is not a hypothetical
path shape. "`volumes/COISS_*`" is also too narrow for that table: six of its rules key on
`volumes/` without COISS and three key on `calibrated/`.

### C10. `uranus_occs_earthbased.py`: the described emission rule does not produce 163

> the list is built by looping over ``prefix_mapping``, emitting one pattern each for
> ``data/atmosphere/``, ``data/global/`` and ``data/rings/`` where a bundle's ingress and
> egress share a prefix, and separate ingress and egress patterns for the last two where
> they do not. … ``opus_id`` is the translator built from the resulting 163 entries.

163 is right (measured: `len(opus_id_list) == 163`). The rule as described is not. The
`else` branch emits the atmosphere pattern only under a nested
`if opus_id_prefix_a is not None`, so:

- 47 bundles share the prefix: 3 patterns each = 141
- 2 bundles do not share and have a separate atmosphere prefix
  (`u12_ctio_400cm`, `u12_eso_360cm`): 5 each = 10
- 3 bundles do not share and have no atmosphere prefix
  (`u12_lco_250cm`, `u36_irtf_320cm`, `u36_maunakea_380cm`): **4 each = 12**, with
  nothing at all emitted for `data/atmosphere/`

141 + 10 + 12 = 163. Read as "four patterns in the non-sharing case" the stated rule
gives 161; read as "atmosphere plus four" it gives 166. The docstring goes on to say
"Nothing is emitted for `data/ring_models/`" while leaving unsaid that nothing is
emitted for `data/atmosphere/` for three of the five split bundles.

### C11. fring and spokes: "which is what the other four … do" says the opposite of what is meant, and four is the wrong number

> ``archive_paths`` and ``archive_dirs`` are defined here but the class body assigns
> neither ``ARCHIVE_PATHS`` nor ``ARCHIVE_DIRS``, which is what the other four pds4 rule
> modules with archive tables do, so this bundle set uses the empty archive tables from
> `pds4file/rules/__init__.py`.

Identical text in `cassini_iss_fring_mosaics_rsfrench2025.py` and
`cassini_iss_spokes_hedman_hamilton_2024.py`. The relative clause attaches to "assigns
neither `ARCHIVE_PATHS` nor `ARCHIVE_DIRS`", so as written it asserts that the other four
modules also assign neither — the reverse of the intended contrast, and false.

The number is wrong too. All six pds4 dataset modules define archive tables. From either
file's point of view there are **five** other modules with archive tables, of which four
assign them and one (the other of this pair) does not. "The other four" is only right if
"other" silently excludes both non-assigners, which it cannot do in both files at once.

### C12. `cassini_vims.py`: "split three ways" understates by an order of magnitude

> The Saturn bundle is split three ways: one archive for the non-data, non-browse
> collections, and then one per leading three-digit clock block for each of the raw data
> and raw browse collections.

`ARCHIVE_PATHS_DICT['cassini_vims_saturn']` holds 1 + 44 + 44 = **89** archive patterns
(`range(45, 89)` twice). The module's own comment says "the bundle is split into multiple
archives". "Three ways" reads as three archives; the clause that follows repairs it, but
the phrase is the one a reader carries away, and the sibling `cassini_iss.py` sentence for
the same layout does not use it.

### C13. `cassini_iss.py`: `bundle.xml` is not a collection

> together with the non-data collections ``bundle.xml``, ``context/``, ``document/`` and
> ``xml_schema/``

The correction removed `calibration/` from this list (right — it appears in
`cassini_vims.py`, not here) but left `bundle.xml`, a single label file, in a list of
collections, and left the trailing slash off it while every real collection keeps one.
The module's header comment has the same slip, which is presumably where it came from;
`cassini_vims.py` repeats it uncorrected.

---

## Other prose defects

1. **`pds4file/rules/__init__.py`**: "``DESCRIPTION_AND_ICON`` -- … covering the category
   directories". The one category directory a PDS4 reader needs, `bundles`, has **no**
   entry — the copied table covers `volumes`, `calibrated`, `diagrams`, `metadata`,
   `previews` and `documents`. Measured through the class:
   `Pds4File.from_logical_path('bundles').description` raises `TypeError`, while
   `previews`, `metadata` and `diagrams` return their descriptions (see code defect K1).

2. **`pds4file/rules/__init__.py`**: "``GENERIC_VOLSET_DESC`` and ``GENERIC_VOLUME_DESC``
   -- the descriptions used for a bundle set and a bundle when nothing more specific
   matches." They are never used for a PDS4 bundle set or bundle. Their only two readers
   are `DESCRIPTION_AND_ICON`'s `volumes/[^/]+` and `volumes/[^/]+/[^/]+` rules, which no
   `bundles/` path can reach, and their literal values are `'Volume collection'` and
   `'Data volume'`. Measured: a PDS4 bundle set and bundle both come back `''`/`UNKNOWN`.
   (The companion claim "Both are read only by `DESCRIPTION_AND_ICON` itself" is correct —
   `grep` finds no other reader in `src/`.)

3. **`pds4file/rules/__init__.py`**: "``OPUS_TYPE`` -- … covering previews, diagrams and
   the metadata indices." The table has 17 rules: 4 previews, 4 diagrams, 8 metadata, and
   a first rule `^test/.*_thumb\..*$` that the sentence does not account for.

4. **`uranus_occs_earthbased.py`**, module docstring and class docstring both: "The class
   body builds its volume set translator entries by looping over ``prefix_mapping``, so a
   bundle prefix has to appear there for its paths to resolve to this subclass" /
   "so a bundle whose prefix is not listed there does not resolve to this class." False,
   measured. `uranus_occ_support` is absent from `prefix_mapping`, yet

   ```
   Pds4File.from_logical_path(
       'bundles/uranus_occs_earthbased/uranus_occ_support/document/user_guide/occgeom_example1.pro')
   -> class=uranus_occs_earthbased
   ```

   Subclass selection is `new_pdsfile(key=class_key)` with `class_key = self.bundleset`
   (`pdsfile.py:1482`), and `new_pdsfile` consults `VOLSET_TRANSLATOR` only when the key
   is *not* already a `SUBCLASSES` key. `'uranus_occs_earthbased'` is a `SUBCLASSES` key,
   so the `prefix_mapping`-built entries — which map *bundle* names to the bundle set
   name — are never reached by path resolution at all. `VOLSET_TRANSLATOR.first('uranus_occ_support')`
   returns `'default'`, and it makes no difference.

5. **`uranus_occs_earthbased.py`**: "The detector codes are listed in the comment above the
   mapping." The comment lists five (`ir`, `vis`, `insb`, `gaas`, `ccd`). The mapping uses
   seven: `hst-fos-occ-1996-076-u137` and `hst-fos-occ-1996-101-u138` use `fos`, and
   `caha1m23-nicmos-occ-1997-273-u144` uses `nicmos`. The docstring vouches for a list
   that is missing two of the codes a reader would look up.

6. **`COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH`**: "That comparison is alphabetic, which
   orders correctly here because no cube carries a two-digit version number." One does:
   `/seti/opus/pdsdata/holdings/volumes/COVIMS_0xxx/COVIMS_0038/data/2009249T070528_2009252T065256/v1630912046_17.qub`
   (found by a `find` over all 197 `.qub` files in the limited copy; the distinct version
   suffixes are `_1` … `_9` and `_17`). The docstring restates an in-code comment that
   asserts the same thing; see code defect K3.

7. **`COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH`**: no `Parameters:` section. The
   function takes one argument and the docstring describes it in running prose ("The one
   argument is the OPUS ID string"), while the two prioritizers in this same slice use a
   `Parameters:` block for theirs. The brief's premise that "the `Raises:` sections were
   all rewritten in the correction commit" is also not true of this one — `d108bae` does
   not touch this function.

8. **`COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH`**: "the one whose version number sorts
   highest is returned". The sort key is `os.path.basename(p)[11:]` — everything after the
   ten-digit clock, so the underscore, the version, any `_NNN` sub-observation number and
   the extension. It is not the version number, and for two matches that differ only in
   sub-observation number the version plays no part.

9. **`COUVIS_0xxx.DATA_SET_ID`**: "The two subscripts in that expression are guarded by the
   existence check above them rather than by anything this method does." Self-contradictory
   — the existence check (`if not row.exists: raise ValueError(...)`) *is* in this method,
   nine lines above. And it does not guard them: `row.exists` says nothing about
   `row_dicts` being non-empty or about the index having a `DATA_SET_ID` column, so
   `row.row_dicts[0]['DATA_SET_ID']` can still raise `IndexError` or `KeyError`, neither of
   which the `Raises:` section lists. The sentence draws attention to the two subscripts
   and then mis-describes what stands behind them.

10. **`GO_0xxx.opus_prioritizer` and `NHxxxx_xxxx.opus_prioritizer`**: both now describe a
    key as a `(category, rank, slug, title, selected)` tuple and then describe the
    alternative heading as differing in rank, slug and title only. The body also forces the
    fifth element: `alt_header = (header[0], header[1] + 10, header[2] + '_alternate',
    header[3] + ' (Superseded Processing)', True)`. A superseded or alternate-downlink
    heading is therefore always default-selected, whatever the original heading's flag
    was, and neither docstring says so.

11. **`cassini_iss_fring_mosaics_rsfrench2025.py`**: "Each of the three partial archives
    also carries the bundle label, the context, spice_kernels, schema and readme files, the
    document collection files and its own index pair from ``miscellaneous/``." The
    reprojected-image archive also carries `miscellaneous/collection_miscellaneous.csv` and
    `miscellaneous/collection_miscellaneous.lblx`, which the other two do not. The sentence
    reads as though the three archives take the same non-data set plus one index pair each.

12. **`cassini_uvis_solarocc_beckerjarmak2023.py`**: "``opus_type`` -- files all four of its
    products under the "Cassini UVIS Solar Occultations" OPUS category". The four are OPUS
    *types* (four rules, four slugs); the bundle holds 41 occultations and their browse and
    document products. "All four of its products" reads as a count of products.

13. **`cassini_iss_spokes_hedman_hamilton_2024.py`**: "The bundle set on disk is named
    cassini_iss_spokes_hedman-hamilton-2024, with hyphens; this module and its class are
    named cassini_iss_spokes_hedman_hamilton_2024, with underscores". Both names contain
    three underscores; only the last two separators differ. As written it says the disk
    name has no underscores.

---

## Code defects

**K1. `Pds4File.from_logical_path('bundles').description` raises `TypeError`.**
`pds4file/rules/__init__.py`'s `DESCRIPTION_AND_ICON` inherits the PDS3 category rules
(`volumes`, `calibrated`, `diagrams`, `metadata`, `previews`, `documents`) and never gained
one for `bundles`, so nothing matches and `_description_and_icon_filled` stays `None`:

```
File ".../src/pdsfile/_properties.py", line 1314, in description
    return self._description_and_icon_filled[0]
TypeError: 'NoneType' object is not subscriptable
```

Same for `archives-bundles` and `checksums-bundles`. `previews`, `metadata` and `diagrams`
return their text, and `Pds3File.from_logical_path('volumes').description` works, so this
is specific to the PDS4 category directory.

**K2. `Pds4File.FILESPEC_TO_BUNDLESET` maps a spokes filespec to the wrong bundle set.**

```
'cassini_iss_spokes_hedman-hamilton-2024/data_derived/x/y.fits' -> 'cassini_iss'
```

The spokes module adds nothing to the table (which its docstring correctly notes), so
`cassini_iss.py`'s `^(cassini_iss)_.*$` swallows it. The fring module escapes only because
it is imported after `cassini_iss` and each module *prepends*, putting
`^(cassini_iss_fring_mosaics_rsfrench2025).*$` in front. A spokes rule would have to be
added, or the `cassini_iss` rule narrowed.

**K3. `COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH`'s version tie-break is unsound.** The
in-code comment "Note: There is no case where this involves a two-digit version number, so
we can use alphabetic sort" is falsified by `v1630912046_17.qub` in COVIMS_0038.
`'_17.qub' < '_9.qub'`, so if any single-digit sibling of a two-digit-version cube ever
appears under one OPUS ID, `version_tuples.sort()` picks the lower version. Only `_17`
exists for that clock in this holdings copy, so no live failure is demonstrable here, but
the premise the code rests on is false.

**K4. Stale comments in `cassini_iss_spokes_hedman_hamilton_2024.archive_dirs`.** Both
partial-archive entries carry the comment `# - all files under document`, and neither
entry lists a `document` path — they list `data_derived`/`browse_derived`, `bundle.lblx`,
`context`, `readme.txt`, `spice_kernels`, `xml_schema`. The docstring, correctly, does not
mention documents; the comment does.

**K5. `TranslatorByRegex.append()` silently discards the receiver when the argument is a
`NullTranslator`.**

```python
def append(self, translator):
    if translator.TAG == 'NULL':
        return translator
```

`X + NullTranslator()` returns the null translator, throwing away `X`; `prepend` has the
mirror image. Nothing in the rule modules currently adds a null on the right, so this is
latent, but it is the same operator the `ASSOCIATIONS` merges rely on and it is not
commutative in the way a reader of `+` would assume.

**K6. `opus_prioritizer` forces `selected=True` on the alternative heading** in both
`GO_0xxx.py` and `NHxxxx_xxxx.py`, so superseded processing and alternate downlinks are
default-selected in OPUS regardless of the original heading's flag. This may be deliberate;
it is not recorded anywhere.

---

## Claims I checked and found correct

**Byte-identical claims** — AST source-segment comparison against
`pds3file/rules/COISS_xxxx.py`: all 8 named in `cassini_iss.py`, all 8 in
`cassini_vims.py`, all 5 in `uranus_occs_earthbased.py`. Also `sort_key` keys on
basenames and `opus_format` on extensions, as all three modules now say; both fire for
`bundles/` paths.

**`pds4file/rules/__init__.py`** — the three tables that differ are exactly
`ASSOCIATIONS`, `DESCRIPTION_AND_ICON`, `OPUS_TYPE`; the three with no PDS3 counterpart
are exactly `PRODUCT_LBL_BASENAME_WO_EXT`, `ARCHIVE_PATHS`, `ARCHIVE_DIRS`; 20 are
byte-identical. The header comment does say "all". `VIEWABLE_TOOLTIPS` has one entry, the
plain string `'Default browse product for this observation'`. `VIEWABLES` is one null
`'default'`. `VIEW_OPTIONS` is `(False, False, False)`. `ASSOCIATIONS`'s other five keys
are byte-identical to the PDS3 ones; `previews`, `calibrated`, `diagrams` are
`NullTranslator`s and are genuinely replaced. `VERSIONS` answers at the category level
through `([a-z-]+)` and nowhere else on a PDS4 path. `INFO_FILE_BASENAMES` matches
`readme.txt`, and every bundle in the holdings has one. `FILESPEC_TO_BUNDLESET` and
`LID_AFTER_DSID` return `None` for every PDS4 path tried. `__all__` lists four names, the
`from .rules import` block names six, and the two extra are the fring and spokes modules.
The `_derived_paths.py` account of PDS3 archive paths matches `archive_path_and_lskip`,
and `ARCHIVE_PATHS`/`ARCHIVE_DIRS` are read only by `Pds4File.archive_paths()`/
`archive_dirs()`.

**`cassini_iss.py`** — `opus_id` reads `\d{3}xxxxxxx/\d{5}xxxxx` under `[a-z]*_raw/` and
produces `co-iss-<camera><clock>` (measured: `co-iss-n1360000000`); the archive split uses
`1{num}` with `num` two digits, i.e. the three-digit block alone; the data and browse
entries are built by comprehension. `opus_type` files under "Cassini ISS";
`opus_id_to_primary_logical_path` resolves to `volumes/COISS_1xxx` or `COISS_2xxx`.

**`cassini_vims.py`** — both `opus_id` alternatives verified:
`…/1490874598_xxx/1490874598_001.qub -> co-vims-v1490874598_001` and
`…/14908xxxxx/1490874598.qub -> co-vims-v1490874598`. The documents association does send
a preview to `VIMS-Preview-Interpretation-Guide.pdf`. The cruise bundle is one archive.

**`cassini_uvis_solarocc_beckerjarmak2023.py`** — the readme confirms "derived radial
occultation profiles of the rings of Saturn based on solar occultation observations made
with the Cassini UVIS instrument between June 2005 and June 2017", and its section 4 lists
exactly `readme.txt`, `bundle.xml`, `browse/`, `context/`, `data/` with `supplemental/`,
`document/`, `xml_schema/`. `document/` on disk holds
`1-RingSolarOccAtlasVol1V1.0.pdf`, `2-RingSolarOccAtlasVol2V1.0.pdf` and
`Cassini_UVIS_Users_Guide_20180706.pdf` — the two atlas volumes and the UVIS user guide,
and the same three are the "three named documents" in `opus_products`. Data files are
`uvis_euv_<year>_<day>_solar_time_series_<ingress|egress>`. All four `opus_type` rules use
the "Cassini UVIS Solar Occultations" category. `associations_to_metadata` matches and
returns `[]`. One archive entry in each table.

**`uranus_occs_earthbased.py`** — `len(prefix_mapping) == 52`, matching the 52
`uranus_occ_*` bundles on disk beside `uranus_occ_support`; exactly two end in `hst_fos`;
`Pds4File.BUNDLENAME_REGEX` is
`^(uranus_occ_u\d{0,4}._[a-z]*_(fos|\d{2,3}cm)|…` — the `fos` alternation is there. Event
years span 1977–2002 and there are 16 distinct observatory tokens.
`len(opus_id_list) == len(opus_id_to_primary_filespec_list) == 163`;
59 prefix strings, 57 set entries; the two collisions are `u12_ctio_400cm` (ingress ==
atmosphere) and `u12_eso_360cm` (egress == atmosphere), and no prefix is shared between
bundles. All five ingress prefixes do fall on a different day-of-year from their egress.
`opus_products` has 9 rules under 6 comment headings, the last four being previews and
diagrams. `opus_type`'s last rule is the only one outside the "Uranus Earth-based
Occultations" category and it files `*_index.csv` under `metadata`.
`data/ring_models/` on disk holds `*_fitted_ring_event_times.*` and
`*_predicted_ring_event_times.*` beside the `*_sqw*` files, so "the square-well models and
the fitted and predicted ring event times" is right; `browse/` exists in every bundle. The
support bundle holds the ring fit, `uranus_occultations_index.tab`, the quality ratings,
the rings dictionary definitions, the user guide with `.pro`/`.py` plotting software, and
`spice_kernels/fk` and `spice_kernels/spk`. The primary product for an atmosphere OPUS ID
is the time series itself and for the others the `_100m` label.

**`cassini_iss_spokes_hedman_hamilton_2024.py`** — verified by walking every pds4 class
body: it is the only one that sets no `ASSOCIATIONS`, no `VIEWABLES` and no `OPUS_ID*`, and
the only one that does not extend `Pds4File.FILESPEC_TO_BUNDLESET`. `opus_type` files the
`_rprj` image and `_rprj_suppl.txt` under "Cassini ISS B Ring Reprojected Images" and the
browse PNG under "browse". The three archives and the two partial archives' contents match.
`COISS_xxxx.cross_pds3_pds4_products` does reach both the spokes and the fring products
from the PDS3 side.

**`cassini_iss_fring_mosaics_rsfrench2025.py`** — `opus_type`'s category assignments are
exactly as described (mosaics/metadata/readme/user guide under "Cassini ISS F Ring
Mosaics"; reproj image, SPICE pointing and metadata under "…Reprojected Images"; every
browse under "browse"; all three indices under "metadata"). `opus_products` offers both
mosaic forms, their metadata, both browse sets, the readme, the user guide and exactly the
two global mosaic indices — not the reproj index. `associations_to_previews` does return
`bundles/` paths under `browse_mosaic/` and `browse_mosaic_bkg_sub/`;
`associations_to_metadata` matches and returns `[]`. `product_lbl_basename_wo_ext`'s three
rules are described correctly. Neither `ARCHIVE_PATHS` nor `ARCHIVE_DIRS` is assigned.

**The three `*_primary_filespec.py` modules** — 302 fring entries, every one a
`*_mosaic.lblx` under `data_mosaic/`; 41 uvis entries, all `.xml` in `data/` and none in
`data/supplemental/`; 772 uranus entries covering all 52 observation bundles and no support
bundle, every one either under `data/atmosphere/` or ending `_100m.xml` (636 rings, 93
global, 43 atmosphere). All three named test modules exist and do walk the list through
`opus_id` and `from_opus_id` back to the same logical path. The fring file is the only
entry in `pyproject.toml`'s `W191` per-file ignores.

**The two prioritizers** — every `Raises:` entry reproduced with stub objects:

```
GO empty-string key   -> IndexError: string index out of range
GO equal priority     -> TypeError: '<' not supported between instances
NH empty-string key   -> IndexError: string index out of range
NH unlisted file code -> KeyError: 'ZZZ'
NH equal file code    -> TypeError: '<' not supported between instances
```

`Pds3File` defines neither `__lt__` nor `__eq__`, so the fall-through to the sublists does
raise. The empty string really is a key: `_opus.py:361-380` uses
`pdsf.opus_type` as the key and logs an error rather than skipping when it is `''`. Rank
+10/+50, `_alternate`, `' (Superseded Processing)'`/`' Alternate Downlink'`, the
single-copy skip, the `voltype_ != 'volumes/'` skip, the per-rank survivor, and "modified
in place as well as returned" all match the bodies. Each prioritizer describes its own
constants.

**`RPX_xxxx.FILENAME_KEYLEN`** — `description_and_icon_by_regex` names `RAWIMAGE`,
`CALIMAGE`, `ENGDATA`, `HEADER` and exactly three mask directories, `RAWMASK`, `CALMASK`,
`ENGMASK`. "There is no header mask" is right, and the corrected "a mask for the first
three" matches. `_volinfo/RPX_xxxx.txt` confirms RPX_0001–0005 are the HST WFPC2 volumes
and RPX_0101/0201/0301/0401 the ground-based ones, so `/RPX_000` does select the HST five.

**`COVIMS_0xxx.FILENAME_KEYLEN`** — `BASENAME_REGEX = re.compile(r'(v?\d{10}_\d+)(_0[0-6][0-9]|).*')`
matches the prose exactly, including "between 000 and 069". Group 2 is an alternation with
an empty branch, so it is `''` rather than `None` when absent and
`match.group(1) + match.group(2)` cannot raise `TypeError`.

**`COISS_xxxx.FILENAME_KEYLEN`** — `self.bundleset[:10] == 'COISS_3xxx'` → 0, else 11;
camera letter plus ten clock digits is eleven characters.

**`COUVIS_0xxx.DATA_SET_ID`** — the `Returns:` line and the two `ValueError` conditions and
the `FileNotFoundError` are all right, and the `and` → `or` correction was needed.

**Mechanical** — across all 16 files in this slice: no unicode smart quotes, em-dashes or
arrows; no docstring line over 90 columns; no British spellings; no double space after a
sentence period; no time-anchored prose.

---

## Could not verify either way

- Everything about `cassini_iss`, `cassini_vims`, the fring mosaics and the spokes bundle
  that rests on the archive layout: the collection lists, the two nested clock levels, the
  `1{num}` block ranges (cruise 29–45, saturn 45–88) and the `iss_`/`iosic_` observation
  names. These four bundle sets are not in the limited holdings copy, so the module header
  comments and the regexes are the only witnesses, and the docstrings say so ("The archive
  layout described in this module's header comment").
- Whether `<sub-observation>` is the right name for the VIMS `_NNN` suffix, and whether the
  three digits in a NH file code are guaranteed hexadecimal. Both are plausible and neither
  is stated anywhere in the repo.
- Whether the fring mosaics really are "built from Cassini ISS images, together with the
  reprojected images they are built from", and whether the spokes bundle really holds
  "reprojected images of Saturn's B ring". Both bundle sets are absent from the holdings
  and have no readme to check; the names and the OPUS titles are consistent with the
  claims.
- Whether K6 (`selected=True` on the alternative heading) is intended behavior.
- `prefix_mapping` is a `set`, so `opus_id_list`, `opus_id_to_primary_filespec_list`,
  `opus_id_to_subclass_set` and the volset entries are built in an order that changes with
  `PYTHONHASHSEED` (confirmed: the first entry of `opus_id_list` differs under seeds 0, 1
  and 2). I could not make it change any answer — resolving all 399 synthetic reverse OPUS
  IDs under two seeds gives byte-identical output, because within one mapping entry the
  emission order is fixed and the only duplicate prefixes are inside a single entry. Worth
  knowing, not demonstrably a bug.
