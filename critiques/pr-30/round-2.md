# PR-30 round 2 — the ten pds4 rule modules, plus the seven functions

## What I read and how

I read all ten files under `src/pdsfile/pds4file/rules/` in the head tree
(`/seti/all_repos/rms-pdsfile-pr30/work`) end to end, and the bodies of the seven named
functions in `pds3file/rules/{GO_0xxx,NHxxxx_xxxx,RPX_xxxx,COUVIS_0xxx,COVIMS_0xxx,COISS_xxxx}.py`,
diffing each against `/seti/all_repos/rms-pdsfile-pr30/base` first so I knew exactly which
prose was new. Every "byte-identical to the table of the same name in
`pds3file/rules/COISS_xxxx.py`" claim was checked by hashing the `ast.get_source_segment`
of each module-level assignment in both files (all three claims — eight tables for
`cassini_iss`, eight for `cassini_vims`, five for `uranus_occs_earthbased` — are true, and
for `uranus_occs_earthbased` five is exactly the number of shared-and-identical names).
Relationship claims were checked by running the translators: I imported the packages under
`/seti/all_repos/rms-pdsfile/venv/bin/python` with `PYTHONPATH=<tree>/src` and fed real PDS4
logical paths through `pds4file.rules.DESCRIPTION_AND_ICON`, `VERSIONS`,
`INFO_FILE_BASENAMES`, `FILESPEC_TO_BUNDLESET` and `LID_AFTER_DSID`; I enumerated
class-body assignments in every pds4 rule module with an AST walk to test the
"only pds4 rule module that ..." claims; I computed `prefix_mapping` prefix collisions and
compared `prefix_mapping` against the bundle directories on disk. Dataset claims were
checked against `/seti/opus/pdsdata/pds4-holdings/bundles/` (both bundle sets present, and
the three `readme.txt` files) and `/seti/opus/pdsdata/holdings/_volinfo/*.txt`. Mechanical
checks (docstring line width > 90, unicode quotes/dashes/arrows anywhere in the `.py`
files, double space after a sentence period, British spellings, time-anchored words) all
came back clean — those four gates pass and are not repeated below.

---

## Prose defects

### `src/pdsfile/pds4file/rules/__init__.py`

**1. Three of the five tables said to be unmatchable by a PDS4 path do match PDS4 paths.**

> "Five of them are written for PDS3 paths and conventions and cannot match a PDS4 path at
> all: ``DESCRIPTION_AND_ICON`` keys on ``volumes/`` and on the PDS3 volume subdirectories,
> ``VERSIONS`` and ``FILESPEC_TO_BUNDLESET`` require an upper-case volume set or volume
> identifier, ``INFO_FILE_BASENAMES`` looks for ``voldesc.cat``, and ``LID_AFTER_DSID`` keys
> on ``volumes/`` as well."

Only `FILESPEC_TO_BUNDLESET` and `LID_AFTER_DSID` are unmatchable. Run against real PDS4
logical paths:

- `DESCRIPTION_AND_ICON.first('bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/uvis_euv_2005_159_solar_time_series_ingress.tab')`
  → `('ASCII table', 'TABLE')`; `.../uranus_occ_support/readme.txt` → `('Text file', 'INFO')`;
  `bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm` → `('Directory', 'FOLDER')`.
  The same docstring's own bullet says the table ends with "a closing block keyed on file
  extension alone" (lines 289–324: `.*\.txt`, `.*\.(tab|csv)`, `.*/[^\.]+`, `.*\..*`), which
  is precisely what makes the "cannot match at all" claim self-refuting.
- `VERSIONS.first('bundles')` → `'bundles'`, via the `(r'([a-z-]+)', 0, r'\1')` rule at
  line 397, which has no upper-case requirement.
- `INFO_FILE_BASENAMES.first('readme.txt')` → `'readme.txt'`, via
  `(r'(README\.txt)', re.I, r'\1')` at line 468. `readme.txt` is not hypothetical: it is
  present at `/seti/opus/pdsdata/pds4-holdings/bundles/uranus_occs_earthbased/uranus_occ_support/readme.txt`,
  `.../uranus_occ_u0_kao_91cm/readme.txt` and
  `.../cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/readme.txt`.
  The docstring picks the one rule of six that is PDS3-only (`voldesc.cat`) and generalises
  from it.

This is the load-bearing sentence of the module docstring's second paragraph, and it is
wrong for three of the five tables it names.

**2. "adds them in front of the ones here ... falls through to these" is false for four
attributes, and the same overstatement is repeated in all six subclass docstrings.**

> "Each dataset module in this package builds its own tables and adds them in front of the
> ones here, so a lookup tries the dataset-specific patterns first and falls through to
> these."

`OPUS_ID`, `OPUS_ID_TO_PRIMARY_LOGICAL_PATH`, `VIEWABLES` and `PRODUCT_LBL_BASENAME_WO_EXT`
are assigned outright, not prepended, so there is no fall-through at all:
`cassini_iss.py:511-514` (`OPUS_ID = opus_id`, `OPUS_ID_TO_PRIMARY_LOGICAL_PATH =
opus_id_to_primary_logical_path`, `VIEWABLES = {'default': default_viewables}`),
`cassini_vims.py:488-491`, `cassini_uvis_solarocc_beckerjarmak2023.py:289-292`,
`uranus_occs_earthbased.py:598-601`,
`cassini_iss_spokes_hedman_hamilton_2024.py:172` (`PRODUCT_LBL_BASENAME_WO_EXT =
product_lbl_basename_wo_ext`), `cassini_iss_fring_mosaics_rsfrench2025.py` likewise.
The identical claim appears in each of the six subclass docstrings as "The class body puts
this module's rule tables **in front of** the class attributes ``Pds4File`` reads", so the
error is duplicated seven times in this slice.

**3. `VIEWABLE_TOOLTIPS`'s one entry is a string, not a null translator.**

> "``VIEWABLES`` and ``VIEWABLE_TOOLTIPS`` -- the viewable sets a product offers and the
> tooltip for each. The one entry, "default", is a null translator."

Line 413: `VIEWABLES = {'default': translator.NullTranslator()}`. Line 415-417:
`VIEWABLE_TOOLTIPS = {'default': 'Default browse product for this observation'}` — a plain
string. The sentence is written to cover both tables and is true only of the first.

**4. "PDS3 archive paths are derived arithmetically from the volume ID" — nothing arithmetic
happens.**

> "``ARCHIVE_PATHS`` -- the archive files that cover a given path. Empty here, and with no
> PDS3 counterpart: PDS3 archive paths are derived arithmetically from the volume ID, while
> a PDS4 bundle set chooses how to split itself."

`_derived_paths.py:217-267` (`archive_path_and_lskip`) builds the path by string
concatenation — `''.join([self.root_, 'archives-', self.category_, self.bundleset_,
self.bundlename, suffix, '.tar.gz'])` — under the rule "one archive file holds one bundle".
There is no arithmetic on the volume ID anywhere in it. The contrast the sentence is
reaching for is real (one archive per volume, versus a PDS4 bundle set choosing its own
split) but "arithmetically" is not a description of any code.

**5. "the header comment says so" misreports the header comment, and "most" undercounts what
differs.**

> "Most of these tables carry the PDS3 defaults unchanged, and the header comment says so."

The header comment (lines 4-5) says "**all** variables have placeholder values the same as
the pds3 general rules", not "most". Comparing every module-level assignment in this file
against `pds3file/rules/__init__.py` by source segment: 20 identical, 3 different
(`ASSOCIATIONS`, `DESCRIPTION_AND_ICON`, `OPUS_TYPE`), 3 with no PDS3 counterpart at all
(`ARCHIVE_PATHS`, `ARCHIVE_DIRS`, `PRODUCT_LBL_BASENAME_WO_EXT`). The docstring is more
accurate than the comment it cites, then attributes its own accuracy to the comment.

**6. `__all__` lists four of the six rule modules, which the sentence does not say.**

> "``__all__`` lists bundle set names, but nothing imports the modules through it"

Lines 82-87 list `uranus_occs_earthbased`, `cassini_iss`,
`cassini_uvis_solarocc_beckerjarmak2023`, `cassini_vims`. The `from .rules import` block in
`pds4file/__init__.py:225-230` names six, adding
`cassini_iss_fring_mosaics_rsfrench2025` and `cassini_iss_spokes_hedman_hamilton_2024`.
A reader who takes the docstring at face value will believe `__all__` enumerates the
package. (The rest of the sentence — that nothing imports through it, and why the import
block sits after the class — is correct; see defect-free list below.)

**7. (minor) `OPUS_ID_TO_SUBCLASS` is not an inverse of the path-to-OPUS-ID translation.**

> "``OPUS_ID``, ``OPUS_ID_TO_SUBCLASS`` and ``OPUS_ID_TO_PRIMARY_LOGICAL_PATH`` -- the
> path-to-OPUS-ID translation and its two inverses, all empty here."

`OPUS_ID_TO_SUBCLASS` maps an OPUS ID to a `PdsFile` subclass (see
`cassini_iss.py:529-530`), not back to a path. Calling it an inverse of a path→ID mapping
is wrong; only `OPUS_ID_TO_PRIMARY_LOGICAL_PATH` inverts it.

### `src/pdsfile/pds4file/rules/cassini_iss.py`

**8. `calibration/` is invented. It is in the docstring and nowhere else in the module.**

> "together with the non-data collections ``bundle.xml``, ``calibration/``, ``context/``,
> ``document/`` and ``xml_schema/``."

The sentence explicitly attributes the layout to "this module's header comment". That
comment (line 341) reads: `'bundle.xml', 'context', 'document', 'xml_schema' (non-data,
non-browse collections)` — no `calibration`. Neither does the code: `archive_paths`'
collection rule is `(context|document|xml_schema|bundle\.xml)` (line 432) and `archive_dirs`
packages `bundle.xml`, `document`, `xml_schema`, `context` (lines 473-478). A grep for
"calibration" in `cassini_iss.py` returns exactly one hit outside the COISS_0011 *report*
strings inherited from COISS_xxxx: line 11, the new docstring. The word is imported from
`cassini_vims.py`, whose header comment (line 337) and archive rules (lines 425, 453) *do*
carry `calibration` — so this is a copy from the sibling module presented as a reading of
this one's comment.

**9. The clock subdivision has two nested levels, not one.**

> "Both data and browse collections are subdivided by the leading three digits of the
> spacecraft clock."

`opus_id` (line 249) shows the real shape:
`.*/cassini_iss/cassini_iss\w*/[a-z]*_raw/\d{3}xxxxxxx/\d{5}xxxxx/(\d{10})(n|w).*` — a
three-digit block *and then* a five-digit block below it. Only the archive split is by the
three-digit block. The sentence describes the directory tree, not the archives (the archive
split gets its own bullet), so it under-describes the tree by a level.

**10. `sort_key` and `opus_format` are not "written against PDS3 ``volumes/COISS_*`` paths".
(Same defect in `cassini_vims.py` and `uranus_occs_earthbased.py`.)**

> "Eight tables here are byte-identical to the tables of the same name in
> `pds3file/rules/COISS_xxxx.py`, and their patterns are written against PDS3
> ``volumes/COISS_*`` paths rather than against ``bundles/cassini_iss`` paths"

The byte-identity is true (verified by hashing). But `sort_key` (lines 173-184) is keyed on
*basenames* — `([NW])([0-9]{10})(.*)_full.png`, and `index.html` — and `opus_format`
(lines 205-208) is keyed on extension alone — `.*\.IMG`, `.*\.jpeg_small`. Neither mentions
`volumes/` or `COISS_`. `cassini_vims.py` makes the same claim for the same eight tables and
`uranus_occs_earthbased.py` for five, of which `sort_key` and `opus_format` are two — so
this sentence is wrong in the same way in three files.

### `src/pdsfile/pds4file/rules/cassini_vims.py`

**11. The OPUS ID form is wrong for one of the two alternatives the same sentence describes.**

> "``opus_id`` -- builds an OPUS ID of the form co-vims-v<clock> from a PDS4 data file name,
> in two alternatives so that a cube filed under a clock-prefixed subdirectory and one filed
> directly under the clock block both resolve."

The template is `r'co-vims-v\1\2'` (line 245), where group 1 is `(\d{10}_\d{3})` — clock,
underscore, and a three-digit sub-observation number. Running the table:

```
.../data_raw/154xxxxxxx/15488xxxxx/1548812345_xxx/1548812345_001.qub -> co-vims-v1548812345_001
.../data_raw/154xxxxxxx/15488xxxxx/1548812345.qub                    -> co-vims-v1548812345
```

The clock-prefixed-subdirectory alternative — the one the sentence names first — produces
`co-vims-v<clock>_<nnn>`, not `co-vims-v<clock>`. The PDS3 counterpart
(`COVIMS_0xxx.py` `opus_id`, `r'co-vims-\1\2'` with `(|_[0-9]{3})`) has the same two shapes,
so the omission is not a PDS4 quirk the author could have been describing away.

**12. (minor) The Saturn bundle is not split only by clock block.**

> "The cruise bundle is packaged as a single archive; the Saturn bundle is split by the
> leading three digits of the spacecraft clock."

`ARCHIVE_PATHS_DICT['cassini_vims_saturn']` (lines 377-389) has three keys: `other_col`
holds a single `bundle_xml_non_data_browse_collections.tar.gz` that is not keyed on the
clock at all, alongside the 44 `browse_raw_*` and 44 `data_raw_*` archives. The
corresponding `cassini_iss` docstring bullet gets this right by naming `other_col`
separately; this one collapses it.

### `src/pdsfile/pds4file/rules/cassini_uvis_solarocc_beckerjarmak2023.py`

**13. The stated bundle layout omits three members the cited `readme.txt` lists.**

> "The bundle set holds a single bundle of the same name, laid out as ``data/`` for the time
> series tables, ``data/supplemental/`` for the supplemental tables, ``browse/`` for the
> plots, ``document/`` for the two volumes of the ring solar occultation atlas and the UVIS
> user guide, and a ``readme.txt``."

The sentence before it cites `bundle readme.txt under
$PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023` as the source. That
readme's own "4. Directory Structure" section (lines 44-115) lists `readme.txt`,
`bundle.xml`, `browse/`, `context/`, `data/` (with `supplemental/`), `document/` and
`xml_schema/`, and `ls` of the bundle confirms all seven. The docstring drops `bundle.xml`,
`context/` and `xml_schema/` while presenting the list as the layout. (The `document/`
contents are right, and better than the readme, which does not name the UVIS user guide.)

**14. (minor) "the supplemental tables" is plural; there is one.**

`ls .../data/supplemental/` returns exactly `uvis_euv_2008_083_solar_time_series_egress_supplement.tab`
and its `.xml`. The bundle readme calls it "supplemental ring occultation profile for
Rev 62 E", singular. `data/` itself holds 41 `.tab` files.

### `src/pdsfile/pds4file/rules/cassini_iss_spokes_hedman_hamilton_2024.py`

**15. (minor) The browse products are not filed under the named OPUS category.**

> "OPUS files them under the "Cassini ISS B Ring Reprojected Images" category"

`opus_type` (lines 86-88) files `_rprj.(fits|lblx)` and `_rprj_suppl.txt` under
`'Cassini ISS B Ring Reprojected Images'`, but `_rprj_browse.png` under `'browse'`. The
bullet two paragraphs down — "``opus_type`` -- the reprojected image, its SPICE pointing
file and its browse product" — lists all three without distinguishing them either. The
sibling `cassini_iss_fring_mosaics_rsfrench2025.py` docstring does call out the `browse`
category explicitly, so the convention exists and is not followed here.

**16. (minor) "does not assign them to ``Pds4File.ARCHIVE_PATHS``" names the wrong attribute.
(Same wording in `cassini_iss_fring_mosaics_rsfrench2025.py`.)**

> "``archive_paths`` and ``archive_dirs`` are defined here but the class body does not assign
> them to ``Pds4File.ARCHIVE_PATHS`` or ``Pds4File.ARCHIVE_DIRS``"

What the other four modules do is assign the *subclass's* attribute — e.g.
`cassini_iss.py:523`, `ARCHIVE_PATHS = archive_paths + pds4file.Pds4File.ARCHIVE_PATHS`,
inside `class cassini_iss`. Nothing anywhere assigns `Pds4File.ARCHIVE_PATHS` itself
(unlike `pds4file.Pds4File.FILESPEC_TO_BUNDLESET` and
`pds4file.Pds4File.VOLSET_TRANSLATOR`, which genuinely are rebound on the base class). The
conclusion drawn — that this bundle set therefore uses the empty tables from
`__init__.py` — is correct; only the attribute named is wrong.

### `src/pdsfile/pds4file/rules/cassini_iss_fring_mosaics_rsfrench2025.py`

**17. `associations_to_previews` returns paths in the bundles tree, not the previews tree.**

> "``associations_to_bundles``, ``associations_to_previews``, ``associations_to_metadata``
> and ``associations_to_documents`` -- cross the bundles, previews, metadata and documents
> trees for one mosaic."

`associations_to_previews` (lines 126-142) returns ten patterns, every one of them beginning
`bundles/\1/browse_mosaic...` or `bundles/\1/browse_mosaic_bkg_sub...`. Nothing under
`previews/` is produced. This bundle set keeps its browse products inside the bundle, which
is exactly why the `default_viewables` bullet one line earlier is careful to say "the
background-subtracted browse PNGs" rather than "previews" — the same care was not applied
here. For contrast, `cassini_iss.py:119-126`, `cassini_vims.py:112-119`,
`cassini_uvis_solarocc_beckerjarmak2023.py:94-106` and `uranus_occs_earthbased.py:146-160`
all really do emit `previews/...`.

**18. "Its collections, as named by this module's tables" omits three collections this
module's tables name.**

> "Its collections, as named by this module's tables, are ``data_mosaic/`` and
> ``data_mosaic_bkg_sub/`` ..., ``browse_mosaic/`` and ``browse_mosaic_bkg_sub/`` ...,
> ``data_reproj_img/`` and ``browse_reproj_img/`` ..., ``miscellaneous/`` ...,
> ``document/user_guide/`` ..., and a ``readme.txt``."

`archive_dirs` in this same module (lines 329-380) names `context`, `spice_kernels`,
`xml_schema` and `bundle.lblx` in every one of its three partial-archive lists, plus
`document/collection_document.csv` and `.lblx`. The qualifier "as named by this module's
tables" is what makes this a defect rather than a permissible simplification: the claim is
about what the tables name, and three named collections are missing.

**19. The list of what the partial archives carry is incomplete, and inconsistent with the
sibling module.**

> "Each of the three partial archives also carries the document, context, schema and readme
> files a reader needs with it."

Each of lines 329-380 also lists `\1/\2/\2/bundle.lblx` and `\1/\2/\2/spice_kernels`, and
each carries its own `miscellaneous/` index pair. The parallel sentence in
`cassini_iss_spokes_hedman_hamilton_2024.py` says "the bundle label, context, spice_kernels,
schema and readme files", i.e. it includes the two this one drops.

**20. (minor) The `opus_type` bullet omits the Documentation entry and mis-describes the
Reprojected Images category.**

> "``opus_type`` -- files the mosaics and their metadata under the "Cassini ISS F Ring
> Mosaics" OPUS category and the reprojected images under "Cassini ISS F Ring Reprojected
> Images", puts every browse product under the "browse" category and every global index under
> "metadata"."

Line 207 also files `readme.txt` and `document/user_guide/*mosaic*.(lblx|pdf)` under
"Cassini ISS F Ring Mosaics" as `'Documentation'`, which the bullet does not mention; and
"Cassini ISS F Ring Reprojected Images" holds three types, not one — the image (rank 170),
its SPICE pointing file (180) and its metadata table (190), lines 220-222. (The browse and
metadata halves of the sentence are exactly right.)

### `src/pdsfile/pds4file/rules/uranus_occs_earthbased.py`

**21. `opus_products` has nine entries in six groups, not five, and the two groups left out
are the previews and the diagrams.**

> "``opus_products`` -- what OPUS offers with one product, in five groups: the ring-specific
> products, the atmosphere-specific products, the global products, the support-bundle
> products available only with a ring or global product, and the support-bundle products
> available with everything."

The table runs from line 285 to line 370 and holds nine tuples. The five named correspond to
the comments `# Rings-specific products`, `# Atmosphere-specific products`,
`# Global-specific products`, `# Only available for rings & global occs` and
`# Available for all occs`. The sixth comment, `# Previews and diagrams` at line 345, heads
four further entries returning `previews/..._preview_{full,med,small,thumb}.png` and
`diagrams/..._diagram_{full,med,small,thumb}.png`. Those are files OPUS offers, so the
sentence both miscounts and omits a product class.

**22. The reason given for `opus_id_to_subclass_set` being a set is not the reason.**

> "``opus_id_to_subclass_set`` -- the set of OPUS ID prefixes that route to this subclass,
> added to ``Pds4File.OPUS_ID_TO_SUBCLASS``. It is a set rather than a list because two
> bundles can share an OPUS ID prefix."

No two bundles share a prefix. Computed over `prefix_mapping` (52 entries, 59 non-`None`
prefixes, 57 distinct entries in the resulting set): the only two prefixes that appear twice
are `ctio4m0-insb-occ-1980-228-u12` and `esosil3m6-insb-occ-1980-229-u12`, and grouping by
bundle shows **zero** prefixes shared across two different bundles. Both collisions are
*within a single entry* — for `u12_ctio_400cm` the ingress prefix equals the atmosphere
prefix (line 398), and for `u12_eso_360cm` the egress prefix equals the atmosphere prefix
(line 399). The set deduplicates a bundle against itself, not against another bundle.

**23. "one pattern per data directory" is wrong for five bundles, and there is no pattern for
one of the four data directories.**

> "``opus_id_list`` and ``opus_id`` -- the list is built by looping over ``prefix_mapping``
> and emitting one pattern per data directory"

In the `opus_id_prefix_i is None` branch (lines 447-452) it is one each for `atmosphere`,
`global` and `rings`. In the else branch (lines 458-463), taken by the five bundles with a
distinct ingress prefix, `global` and `rings` get **two** patterns each — an egress pattern
using `opus_id_prefix_e` and an ingress pattern using `opus_id_prefix_i`. And no branch
emits any pattern for `data/ring_models/`, which the same docstring names as one of the four
data directories two paragraphs above. (`len(opus_id_list)` is 163, not 3 x 52 = 156.)

**24. The stated bundle-naming scheme does not fit two of the 52 bundles.**

> "A bundle is named uranus_occ_<event>_<observatory>_<aperture>, as in uranus_occ_u0_kao_91cm
> and uranus_occ_u14_ctio_400cm"

`uranus_occ_u137_hst_fos` and `uranus_occ_u138_hst_fos` are on disk under
`/seti/opus/pdsdata/pds4-holdings/bundles/uranus_occs_earthbased/`, and their last component
is an instrument, not an aperture. The code knows this: `Pds4File.BUNDLENAME_REGEX`
(`pds4file/__init__.py:31`) is
`uranus_occ_u\d{0,4}._[a-z]*_(fos|\d{2,3}cm)` — the alternation with `fos` exists for exactly
these two.

**25. The per-bundle layout omits `browse/`, which this module's own header comment lists.**

> "A bundle holds ``data/rings/`` ..., ``data/global/`` ..., ``data/atmosphere/`` ..., and
> ``data/ring_models/`` for the square-well models and the fitted and predicted ring
> positions."

The module's archive header comment at line 512 lists `- 'browse/': browse products (images,
PDFs, XML)` as part of what each bundle typically includes, and
`/seti/opus/pdsdata/pds4-holdings/bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/browse/`
exists with `atmosphere`, `global`, `ring_models`, `rings` and its collection files under it.
`associations_to_bundles`, `associations_to_previews` and `associations_to_diagrams` all
match `(data|browse)` explicitly (lines 134, 147, 153, 163, 169), so the tables the docstring
is summarising depend on the collection it leaves out.

**26. `data/ring_models/` holds ring *event times*, not "ring positions".**

Same sentence as 25. The files in
`.../uranus_occ_u0_kao_91cm/data/ring_models/` are `*_fitted_ring_event_times.{tab,xml}` and
`*_predicted_ring_event_times.{pdf,tab,txt,xml}`, alongside the `*_sqw*` square-well files.
The `opus_type` rule that covers them is `.*(fitted|predicted)_.*` (line 245). "Fitted and
predicted ring positions" is a plausible-sounding substitution for what the archive actually
calls event times, and nothing in the repository or the holdings supports it.

**27. The `opus_type` bullet claims a single OPUS category and skips two product types.**

> "``opus_type`` -- files products under the "Uranus Earth-based Occultations" OPUS category,
> with a type for each sampling of the ring and ring-plane profiles, the atmosphere time
> series, the ring models, and each kind of support product."

The last rule of the table (line 269) files `metadata/uranus_occs.*/.*/.*_index.csv` under
the `'metadata'` category with slug `rms_index` — not "Uranus Earth-based Occultations". And
two types are missing from the enumeration: `'Occultation Ring Time Series'` (rank 40,
line 243) and `'Occultation Ring-Plane Time Series'` (rank 100, line 255), neither of which
is a "sampling" of a profile.

**28. (minor) HST is listed among the "telescopes" of an Earth-based bundle set with no
comment.**

> "the bundle set spans observations from 1977 to 2002 made at telescopes from the KAO and
> Palomar to CTIO, ESO, IRTF, SAAO and HST."

Every named observatory is real and the date range is right (`prefix_mapping` runs from
`kao0m91-vis-occ-1977-069-u0` to `pal5m08-insb-occ-2002-210-u0201`). But `hst-fos-occ-1996-076-u137`
and `hst-fos-occ-1996-101-u138` are Hubble, and the module and bundle set are named
*earthbased*. Published as API reference, the sentence reads as an error; it needs a clause
saying the bundle set includes two HST/FOS observations despite its name.

### The seven functions

**29. Both prioritizer `Parameters:` entries describe a key shape that the caller does not
guarantee, and the resulting `IndexError` is undocumented.
(`pds3file/rules/GO_0xxx.py` `opus_prioritizer`, `pds3file/rules/NHxxxx_xxxx.py`
`opus_prioritizer` — identical wording in both.)**

> "Parameters:
>     pdsfile_dict (dict): the OPUS product dictionary, keyed by a (category, rank, slug,
>     title, selected) tuple, whose values are lists of lists of PdsFile objects."

`_opus.py`'s own `opus_products` docstring states the contract: "Each key is a five-element
tuple, **or the empty string** for a product whose type no rule matches", and further down,
"A product whose type comes out empty is logged as an error and is still filed, under the
empty key". `_opus.py:360-384` implements exactly that (`key = opus_type_for_abspath.get(...,
pdsf.opus_type)`, which is `''` when no rule matched) and then calls
`self.opus_prioritizer(pdsfile_dict)` on the whole dict. Under an empty-string key with more
than one sublist and `voltype_ == 'volumes/'`, `header[0]` raises `IndexError` (and
`header[1] + 10` would raise `TypeError`). Neither `Raises:` section lists `IndexError`. The
`Parameters:` entry, by asserting the key shape without qualification, is what hides it.

**30. `pds3file/rules/COUVIS_0xxx.py` `DATA_SET_ID` — ungrammatical `Raises:` clause.**

> "ValueError: if no versions table covers this file's logical path, and if the table that
> does covers it holds no row under the key."

"the table that does covers it" is not English. Also "and" should be "or": the two are
alternative causes, not simultaneous ones (the first `raise` returns before the second can
be reached).

**31. `pds3file/rules/COUVIS_0xxx.py` `DATA_SET_ID` — two undocumented subscript exceptions
in the return expression.**

The final statement is `return row.row_dicts[0]['DATA_SET_ID']`. `row_dicts[0]` raises
`IndexError` on an empty list and `['DATA_SET_ID']` raises `KeyError` if the versions table
lacks that column. The `Raises:` section names only `ValueError` and `FileNotFoundError`.
The `if not row.exists` guard immediately above is marked `# pragma: no cover` precisely
because the code cannot rule these out from inside; the docstring's Raises section should
say so or say that the guard is trusted.

**32. `pds3file/rules/RPX_xxxx.py` `FILENAME_KEYLEN` — "their masks" over-counts by one.**

> "the raw image, the calibrated image, the engineering data, the header file and their masks
> all share it."

The module's `description_and_icon_by_regex` (lines 51-58) names exactly three mask
directories — `RAWMASK` ("Raw image masks"), `CALMASK` ("Calibrated image masks") and
`ENGMASK` ("Engineering data masks") — alongside `RAWIMAGE`, `CALIMAGE`, `ENGDATA` and
`HEADER`. There is no header mask. Four items followed by "and their masks" asserts four
masks.

**33. `pds3file/rules/COVIMS_0xxx.py` `OPUS_ID_TO_PRIMARY_LOGICAL_PATH` — the only function
in the slice with a real parameter and no `Parameters:` section.**

> "The one argument is the OPUS ID string. This function is reached off the class rather than
> off an instance, so no receiver is supplied and the string arrives as the first positional
> parameter."

The substance is correct — `_opus.py:156-157` does
`if callable(pdsfile_class.OPUS_ID_TO_PRIMARY_LOGICAL_PATH): return
pdsfile_class.OPUS_ID_TO_PRIMARY_LOGICAL_PATH(opus_id)`, off the class. But the two
prioritizers in the same PR document their one argument in a `Parameters:` block, and this
one buries the same information in prose, so a generated API page will show a function with
an undocumented parameter.

---

## Code defects noticed (not fixed, not edited)

1. **`cassini_uvis_solarocc_beckerjarmak2023.py:114-120` and
   `cassini_iss_fring_mosaics_rsfrench2025.py:150-156`: regex metacharacters in
   `associations_to_documents` output.** The replacement values are
   `r'documents/cassini_uvis_solarocc_beckerjarmak2023[^/]*'` and
   `r'documents/cassini_uvis_solarocc_beckerjarmak2023[^/]*/.*'` (and the fring equivalents).
   Replacement values are consumed as logical paths / fnmatch globs, where `[^/]` is a
   character class matching a literal `^` or `/`, and `.*` is not a glob. Every other module
   emits a plain `documents/<name>/*` (see `cassini_iss.py:139-143`,
   `cassini_vims.py:132-139`, `uranus_occs_earthbased.py:186-191`).

2. **`cassini_iss_spokes_hedman_hamilton_2024.py:112-113` and `:124-125`: comment contradicts
   the list it heads.** Both partial-archive entries are prefaced with "`# - all files under
   document`", but neither list contains `document`; they contain `bundle.lblx`, `context`,
   `readme.txt`, `spice_kernels` and `xml_schema`. The `cassini_iss_fring_mosaics_rsfrench2025.py`
   equivalents do include `document/...`, so the comment looks copied from there.

3. **`cassini_iss_fring_mosaics_rsfrench2025.py:198` and `:203`: two `opus_type` tuples on one
   physical line.** The `coiss_f_ring_mosaic_browse_small` entry and the
   `coiss_f_ring_mosaic_browse_med` entry share line 198, and
   `coiss_f_ring_mosaic_browse_bkg_sub_small` and `..._bkg_sub_med` share line 203. Both
   `_med` entries are the ones with `default_selected=True`, so the entries hardest to see
   are the ones that change OPUS behaviour.

4. **`uranus_occs_earthbased.py:543-563`: `archive_paths` and `archive_dirs` disagree about
   versioned bundle sets.** `archive_paths` matches `(uranus_occs_earthbased[^/]*)`, so it
   answers for `uranus_occs_earthbased_v2`; `archive_dirs` matches
   `.*archives-(.*/uranus_occs_earthbased)/(.*).tar.gz`, which cannot match
   `archives-bundles/uranus_occs_earthbased_v2/uranus_occs_earthbased_v2.tar.gz`. The header
   comment at lines 521-525 explicitly anticipates the `_v2` case.

5. **Stray `]` inside an alternation, in three modules.** `cassini_iss.py:86, 99, 113, 120,
   129`, `cassini_vims.py:86, 99, 113, 122` and `uranus_occs_earthbased.py:134` all contain
   the group `(.*|_[a-z]*])`. The second alternative requires a literal `]` in the path and is
   dead in any case because the first alternative is `.*`. It reads like a typo for
   `(.*|_[a-z]*)`.

6. **`cassini_iss.py:191-196` and `cassini_vims.py:187-192`: duplicated `opus_type` entry.**
   `(r'volumes/.*/extras/(tiff|full)/.*\.\w+', 0, ('Cassini ISS', 130, 'coiss_full', ...))`
   appears twice in a row. Inherited from `pds3file/rules/COISS_xxxx.py`, which is why the
   byte-identity claim still holds.

7. **`cassini_iss.py:378, 382` vs `:391, 395`: overlapping clock-block ranges.** Cruise uses
   `range(29,46)` and Saturn `range(45,89)`, so both bundles claim archive names for clock
   block `145`. The header comment (lines 355-356) states the same overlapping bounds, so this
   may be deliberate; I could not check it against holdings because `cassini_iss` is not in
   this testing copy.

---

## Claims I checked and found correct

- Every "byte-identical to the table of the same name in `pds3file/rules/COISS_xxxx.py`"
  claim: eight tables in `cassini_iss.py`, eight in `cassini_vims.py`, five in
  `uranus_occs_earthbased.py` — all verified by source-segment hash, and for
  `uranus_occs_earthbased` five is exactly the count of shared-and-identical module-level
  names, so the "five" is not an undercount.
- `pds4file/rules/__init__.py`: "``GENERIC_VOLSET_DESC`` and ``GENERIC_VOLUME_DESC`` ... Both
  are read only by ``DESCRIPTION_AND_ICON`` itself" — a repo-wide grep finds no other reader.
- `pds4file/rules/__init__.py`: the `ASSOCIATIONS` key comparison (PDS4 `bundles` where PDS3
  has `volumes`; the other five identical) — confirmed against
  `pds3file/rules/__init__.py`'s `['volumes', 'previews', 'calibrated', 'diagrams',
  'metadata', 'documents']`.
- `pds4file/rules/__init__.py`: "``previews``, ``calibrated`` and ``diagrams`` are null
  translators that a dataset module **replaces**". "Replaces" is the exactly right word:
  `NullTranslator.append()` in the installed `translator` package returns the *other*
  translator outright, so `ASSOCIATIONS['previews'] += ...` discards the null.
- `pds4file/rules/__init__.py`: `CROSS_PDS3_PDS4_PRODUCTS` empty here; `DATA_SET_ID` a null
  translator; `PRODUCT_LBL_BASENAME_WO_EXT`, `ARCHIVE_PATHS` and `ARCHIVE_DIRS` having no
  PDS3 counterpart (none of the three is defined in `pds3file/rules/__init__.py`, while
  `CROSS_PDS3_PDS4_PRODUCTS` is).
- `pds4file/rules/__init__.py`: "nothing imports the modules through [`__all__`];
  `pds4file/__init__.py` names each one explicitly in a `from .rules import` block, because
  importing a rule module is what registers its subclass and that has to happen after
  `Pds4File` itself is built" — `pds4file/__init__.py:217-230`, comment and all.
- `cassini_iss.py`: `opus_id` really does build `co-iss-<camera><clock>` (template
  `r'co-iss-\2\1'`, camera first); `opus_id_to_primary_logical_path` really does resolve only
  into `volumes/COISS_1xxx` and `volumes/COISS_2xxx`; `opus_type` really is under the
  "Cassini ISS" category; the archive dictionary really does build the clock-block entries
  with a comprehension.
- `cassini_uvis_solarocc_beckerjarmak2023.py`: "derived radial occultation profiles of
  Saturn's rings from solar occultation observations made with the Cassini UVIS instrument
  between June 2005 and June 2017" is a faithful paraphrase of the bundle `readme.txt`
  ("derived radial occultation profiles of the rings of Saturn based on solar occultation
  observations made with the Cassini UVIS instrument between June 2005 and June 2017"); the
  data-file naming `uvis_euv_<year>_<day>_solar_time_series_<ingress or egress>` matches all
  41 files on disk; the three named documents are the two atlas volumes and
  `Cassini_UVIS_Users_Guide_20180706.pdf`; `description_and_icon_by_regex`, `view_options`,
  `neighbors` and `sort_key` really are empty; `associations_to_metadata` really does match
  and return `[]`; both archive tables really do have a single entry.
- `cassini_iss_spokes_hedman_hamilton_2024.py`: the hyphen/underscore naming explanation and
  the `SUBCLASSES` key are right; and the three-part "only" claim is right — an AST walk over
  all six pds4 subclasses confirms it is the only one whose class body assigns no
  `ASSOCIATIONS`, no `VIEWABLES` and no `OPUS_ID`/`OPUS_ID_TO_PRIMARY_LOGICAL_PATH`, and the
  only one that does not rebind `pds4file.Pds4File.FILESPEC_TO_BUNDLESET`. The
  "``archive_paths`` and ``archive_dirs`` are defined here but the class body does not assign
  them ... so this bundle set uses the empty archive tables" conclusion is right too.
- Both cross-PDS3 claims: `pds3file/rules/COISS_xxxx.py` `cross_pds3_pds4_products`
  (lines 670-687, plus `_f_ring_cross_products_list` built at 649-667) really is what reaches the
  `cassini_iss_fring_mosaics_rsfrench2025`
  reprojected images and the `cassini_iss_spokes_hedman-hamilton-2024` derived products from
  the PDS3 side, and `cassini_iss_fring_mosaics_rsfrench2025.py`'s own `opus_products`
  deliberately excludes them (its code comment at lines 235-236 says so).
- `cassini_iss_fring_mosaics_rsfrench2025.py`: `product_lbl_basename_wo_ext`'s three rules
  are described exactly right (size suffix dropped, everything from `_metadata` dropped,
  `_reproj_suppl.txt` → `_reproj_img`); `opus_id`/`opus_id_to_primary_logical_path` really do
  give `co-iss-fring-mosaic-<observation>` and the `data_mosaic/.../*_mosaic.lblx` label;
  `opus_products` really does offer exactly the two global mosaic indices.
- `uranus_occs_earthbased.py`: the opening "Each bundle ... holds the data from a single
  occultation observation of the Uranian system, and a support bundle holds the documentation
  and the Uranian ring models behind them" is a faithful paraphrase of both
  `uranus_occ_u0_kao_91cm/readme.txt` and `uranus_occ_support/readme.txt`. The support-bundle
  inventory is verified item by item against the holdings: the global ring orbital fit
  (`data/uranus_occultation_ring_fit_rfrench_20201201.*`), the original index
  (`document/supplemental_docs/uranus_occultations_index.*`), the quality ratings
  (`uranus_ringocc_bundles_quality_rating.*`), the ring dictionary definitions
  (`rings-dictionary-attribute-definitions.*`), the user guide and its plotting software
  (`document/user_guide/earth-based-uranus-stellar-occultation-user-guide.pdf` plus the
  `.pro`/`.py` files), and SPICE frame and trajectory kernels (`spice_kernels/fk`,
  `spice_kernels/spk`). The 100 m / 500 m / 1 km samplings under `data/rings/` and
  `data/global/` are confirmed (18 and 2 `.tab` files at each of the three samplings in
  `uranus_occ_u0_kao_91cm`). `prefix_mapping` is genuinely a Python `set`, and its 52 bundle
  prefixes are exactly the 52 `uranus_occ_u*` directories on disk — no extras, no gaps.
  `default_viewables` really does point at `diagrams/`, not `previews/`.
  `opus_id_to_primary_filespec_list` really does resolve to the `_100m.xml` label for rings
  and ring-plane profiles and the time series itself for atmosphere.
  `filespec_to_bundleset` (`(uranus_occ)_.*` → `\1s_earthbased`) matches its description.
- All three `*_primary_filespec.py` docstrings: the tests named really do exist and really do
  walk `PRIMARY_FILESPEC_LIST` asserting `logical_path -> opus_id -> logical_path`
  (`tests/rules/pds4/test_*.py`); the fring list is one `_mosaic.lblx` per mosaic under
  `data_mosaic/`; the uvis list is 41 entries, one per `data/` time series, in `data/`; the
  uranus list is 772 entries split `data/rings` 636, `data/global` 93, `data/atmosphere` 43,
  and every rings/global entry ends `_100m.xml` while the atmosphere entries are the time
  series themselves. And the tab claim is exactly right:
  `cassini_iss_fring_mosaics_rsfrench2025_primary_filespec.py` is the only file under `src/`
  containing a tab, and `pyproject.toml:271` is the only per-file `W191` exemption in the
  project.
- `GO_0xxx.opus_prioritizer`: the `sort()` direction is correct — priority 0 goes to the
  reprocessed copy (`TIRETRACK`/`REPAIRED`/`REDO`), `prioritizer.sort()` is ascending, and
  `prioritizer[0]` is what stays under the original heading; rank +10, slug `_alternate`,
  title `' (Superseded Processing)'` all match the code; the single-sublist and
  non-`volumes/` early exits are described correctly; the dictionary is both mutated and
  returned. The `TypeError` claim is real: no class in `src/` defines `__lt__`, `__gt__` or
  `__eq__`, so a tuple comparison that falls through to two `list`s of `PdsFile` raises.
  "`NHxxxx_xxxx.py` is the only other rule module that defines a prioritizer" is true — a
  repo-wide grep finds `def opus_prioritizer` in exactly those two files.
- `NHxxxx_xxxx.opus_prioritizer`: rank +50, slug `_alternate`, title `' Alternate Downlink'`;
  the three-hex-character code taken from after `_0x`; `FILE_CODE_PRIORITY[code]` as the
  `KeyError` site; and the `TypeError` needing two copies with the *same* code (two different
  codes with equal priority values fall through to the code strings and compare fine). The two
  prioritizer docstrings do describe their own constants — I checked each against its own
  body.
- `COVIMS_0xxx.FILENAME_KEYLEN`: `BASENAME_REGEX = re.compile(r'(v?\d{10}_\d+)(_0[0-6][0-9]|).*')`
  — optional `v`, ten-digit clock, underscore, version number; optional `_0[0-6][0-9]`, which
  is 000 to 069 exactly as stated. Group 2 is an alternation with an empty branch, so it is
  always a string and never `None`; there is no hidden `TypeError` in
  `match.group(1) + match.group(2)`, and "or 0 if the basename does not match it at all" is
  right.
- `COISS_xxxx.FILENAME_KEYLEN`: `'COISS_3xxx'` is ten characters, matching
  `self.bundleset[:10]`; a freshly constructed object has `bundleset == ''` so the comparison
  is safe; `_volinfo/COISS_3xxx.txt` confirms COISS_3xxx is "Cassini cartographic maps".
- `RPX_xxxx.FILENAME_KEYLEN`: `_volinfo/RPX_xxxx.txt` confirms RPX_0001–RPX_0005 are the HST
  WFPC2 volumes and RPX_0101/0201/0301/0401 the ground-based ones, so `'/RPX_000'` does select
  exactly RPX_0001 through RPX_0005 among the volumes present (`metadata/.../RPX_0099` does not
  contain `/RPX_000`). `self.abspath` defaults to `''`, not `None`, on a freshly constructed
  object, so the `in` test does not raise.
- `COUVIS_0xxx.DATA_SET_ID`: `VERSIONS_PATH_AND_KEY` (lines 302-306) really does return a
  `(metadata/..._versions.tab, <basename>.LBL)` pair; the empty-string return for a
  non-existent object and for a directory is right; and the `ValueError`/`FileNotFoundError`
  causes named are the two `raise` statements in the body.
- `COVIMS_0xxx.OPUS_ID_TO_PRIMARY_LOGICAL_PATH`: `LOWER_VERSION_PRIORITIZED` is consulted
  first and its purpose matches the code comment at lines 350-351 verbatim in substance;
  `glob_glob(..., force_case_sensitive=True)`; one match returned as-is; several sorted by
  `os.path.basename(p)[11:]`, which is alphabetic and lands after the `v` + ten-digit clock;
  `ValueError` on zero matches. Being reached off the class is confirmed at `_opus.py:156`.

---

## Could not verify either way

- Anything about the internal directory layout of `cassini_iss`, `cassini_vims`,
  `cassini_iss_fring_mosaics_rsfrench2025` or `cassini_iss_spokes_hedman-hamilton-2024`
  beyond what the modules themselves assert. Those four bundle sets are not in the limited
  testing copy at `/seti/opus/pdsdata/pds4-holdings/bundles/`, so for `cassini_iss` and
  `cassini_vims` I could only check the docstrings against the modules' own header comments
  and tables (which is where defects 8, 9 and 12 come from), and for the two derived bundle
  sets only against `opus_type`, the archive tables and the PDS3 cross-product table.
- Whether 52 of the 53 uranus bundles genuinely lack `data/ring_models/` and `browse/`, or
  whether the testing copy is pruned. Only `uranus_occ_u0_kao_91cm` carries `browse/`,
  `bundle.xml`, `context/`, `document/`, `readme.txt`, `xml_schema/` and
  `data/ring_models/`; the other 52 hold `data/` alone. That pattern reads like a
  deliberately pruned sample, so I treated `uranus_occ_u0_kao_91cm` as the reference layout
  and drew no conclusion from the others' absences.
- Whether the `cassini_iss` cruise/Saturn clock-block overlap at `145` (code defect 7) is a
  real double-claim or intended: it needs the real archive listing, which is not present.
- Whether the nine-character "HST group ID" in `RPX_xxxx.FILENAME_KEYLEN` is nine because of
  the HST rootname convention or for some RPX-specific reason. The code comment says "Use the
  length of the HST group ID", and the only RPX directory in the holdings is
  `RPX_xxxx/RPX_0001/CALIB` with no data files under it, so I could not confirm the length
  against a real basename.
