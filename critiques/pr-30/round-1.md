# PR-30 adversarial documentation review, round 1: the 26 pds3 rule modules

## What I read and how

I read the full diff of `base` against `work` for
`src/pdsfile/pds3file/rules/*.py` (26 files, 58 docstrings, 1742 diff lines), then
read each module's tables in the head tree and checked every factual claim against
three sources: the code itself, the holdings tree at `/seti/opus/pdsdata/holdings`
(especially `_volinfo/*.txt` and the real directory listings under `volumes/`), and
runtime behaviour under `/seti/all_repos/rms-pdsfile/venv/bin/python` with
`PYTHONPATH=<work>/src` and `PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings`.
Mechanically checkable claims were scripted rather than eyeballed: an AST census of
every top-level and class-level name across all 36 rule modules (pds3 and pds4) to
test the "only module that ..." and "defined by no other rule module" claims; a
runtime count of `VIEWABLES` keys per subclass; a runtime evaluation of
`FILESPEC_TO_BUNDLESET`, `SORT_KEY`, `INFO_FILE_BASENAMES`, `DESCRIPTION_AND_ICON`
and each module's `versions` table on real paths; regex-shape counts over the
`opus_id_to_primary_logical_path` and `FILE_CODE_PRIORITY` tables; and a
docstring-only scan for non-ASCII characters, lines over 90 columns, double spaces
after a sentence period, and time-anchored words. Those four mechanical style gates
pass: no non-ASCII character anywhere in the 26 files, no docstring line over 90
columns, no double space after a period, and no British spellings. The only
time-anchored word I found is "still" in `RPX_xxxx.py` (item 40 below). I did not
re-run the rule-table name checker, per the brief.

---

## Prose defects

### A. The docstring names the wrong output, table or file

**1. `VG_20xx.py` — the table does not produce the name the docstring gives.**
> "``filespec_to_bundleset`` -- maps a file specification beginning with a VG_20nn
> volume ID to the volume set name VG_20xx, ..."

The table's replacement string is `r'VG__20xx'` — two underscores (`VG_20xx.py`
line 54). Runtime confirms it:
`Pds3File.FILESPEC_TO_BUNDLESET.first('VG_2001/x')` returns `'VG__20xx'`, and there
is no `VG__20xx` under `holdings/volumes/`. The docstring documents the intent, not
the code. (See code defect C1.)

**2. `VGIRIS_xxxx.py` — same shape, and the docstring contradicts itself.**
> "``filespec_to_bundleset`` -- maps a file specification beginning with a
> VGIRIS_nnnn volume ID to the volume set name VGIRIS_xxxx."

The table returns `'VGIRIS_xxxx_peer_review'` (line 55), which is confirmed at
runtime and is the directory that actually exists
(`holdings/volumes/VGIRIS_xxxx_peer_review`). The same docstring says, three
paragraphs earlier, that the volumes sit "under the volume set name
VGIRIS_xxxx_peer_review", so the module states both the right answer and the wrong
one.

**3. `VGIRIS_xxxx.py` — the description table does not name the directories it is
said to name.**
> "``description_and_icon_by_regex`` -- names the directories of a volume, which are
> split first by planet and then by spacecraft, so that a directory reads as
> "Voyager 2 Neptune data" rather than as a bare code."

The table's directory patterns are `.*/JUPITER`, `.*/SATURN`, `.*/URANUS`,
`.*/NEPTUNE`, and `translator.TranslatorByRegex` anchors every pattern as
`^...$`. The real directories are named for planet *and* spacecraft:
`VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1`. Runtime:

```
volumes/VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1 -> ('Data files', 'DATADIR')
volumes/VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER     -> ('Jupiter data', 'DATADIR')
```

So the actual directories fall through to the default `Data files`, and the
directory patterns that do fire match names that do not exist here. Separately,
"Voyager 2 Neptune data" is the description of the *file* `VG2_NEP.DAT` (icon type
`DATA`), not of a directory.

**4. `VG_20xx.py` — the same "a directory reads as" sentence, same error.**
> "... so that a directory reads as "Voyager 2 Uranus data" rather than as a bare
> code."

Runtime on the real tree:
`volumes/VG_20xx/VG_2001/URANUS -> ('Uranus data', 'DATADIR')` but
`volumes/VG_20xx/VG_2001/URANUS/VG2_URA.DAT -> ('Voyager 2 Uranus data', 'DATA')`.
The directory level is split by planet only; the per-spacecraft split is a file
name. The clause "split first by planet and then by spacecraft" is true of the
table's two halves, but not of its directories.

**5. `CORSS_8xxx.py` — the five viewable sets are glossed against the wrong tables.**
> "``diagram_viewables``, ``profile_viewables``, ``skyview_viewables``,
> ``dsntrack_viewables`` and ``timeline_viewables`` -- ... They are the occultation
> track geometry, the radial profile figure, the sky view, the DSN elevation track
> and the observation timeline."

Read positionally, `diagram_viewables` is "the occultation track geometry". It is
not. `diagram_viewables` produces
`diagrams/CORSS_8xxx/<vol>/data/RevNNN/RevNNN{C}{I|E}_*.jpg`, and the class's own
tooltip for the `diagram` key is "Diagram illustrating observation footprints on the
target". The occultation track geometry is what `skyview_viewables` produces —
`previews/CORSS_8xxx/CORSS_8001/browse/RevNNN_OccTrack_Geometry_*.jpg`, backed by
the real files `holdings/volumes/CORSS_8xxx/CORSS_8001/browse/Rev007_OccTrack_Geometry.pdf`
— and its tooltip is "Occultation track of Cassini behind the rings as seen from
Earth". The list has the first and third glosses swapped, and "the sky view" is
merely the key name restated rather than a description of any product.

**6. `COCIRS_xxxx.py` — the description table has no per-body diagram directories.**
> "``description_and_icon_by_regex`` -- names the TSDR and CUBE trees and their
> contents, the simplified-format tables, and the per-body diagram directories."

I extracted the 57 entries of that table and grepped them: the only BROWSE entries
are two generic ones (`volumes/COCIRS_[56].*/BROWSE` and
`diagrams/COCIRS_[56].*/BROWSE`, both "Observation diagrams"), and there is no
entry containing `S_RINGS`, `SATURN` or `TARGETS`. The table's per-body run is 24
`GEODATA/.*NNN\.TAB` entries described as "Body viewing geometry (Mimas)" and so
on, with icon type `INDEX` — those are geometry index *tables*, not diagram
directories.

**7. `VG_0xxx.py` — the browse extension is wrong, twice.**
> "each has a compressed browse image beside it in IBQ form"
> "``opus_format`` -- gives the IMQ and IBQ extensions their interchange and file
> formats."

`opus_format` has exactly two entries and neither mentions IBQ:
`(r'.*\.IBG', 0, ('Binary', 'Compressed Voyager browse'))` and
`(r'.*\.IMQ', ...)`. Every other table in the module uses `.IBG` too —
`description_and_icon_by_regex` line 48, all twelve `default_viewables` entries
(lines 62-73), and `associations_to_volumes` (lines 81-83) — and
`src/pdsfile/holdings_maintenance/pds3/pdslinkshelf.py:70` lists
`(IMQ|IRQ|IBG)`. The only place `IBQ` appears in the code is `opus_type`, which is
almost certainly the defect (see code defect C10). The docstring picked the odd one
out and stated it as fact twice.

**8. `VG_0xxx.py` — the OPUS ID summary drops the load-bearing half.**
> "``opus_id`` -- derives the OPUS ID from the image number in the file name."

The table has 17 entries, and every one keys on a *volume-number range* in order to
supply the spacecraft and the target: `VG_000[1-3]` → `vg-iss-2-u-`,
`VG_000[45]` with a leading 3 → `vg-iss-1-s-`, `VG_000[6-8]` with `1[0-7]` →
`vg-iss-1-j-`, and so on. The image number is the only part taken from the file
name; the spacecraft and planet come entirely from the path.

**9. `NHxxxx_xxxx.py` — wrong tree.**
> "... and points at the instrument and payload descriptions in the documents tree."

The three entries are `volumes/.*/document/lorri_ssr\.pdf`,
`volumes/.*/document/ralph_ssr\.pdf` and `volumes/.*/document/payload_ssr\.pdf` —
the volume's own `document/` subdirectory under `volumes/`, not the top-level
`documents/` category that the rest of this PR's prose calls "the documents tree"
(for example the same module's own bullet "cross the volumes, previews, metadata
and documents trees").

**10. `JNOJNC_xxxx.py` — the viewable is singular and the label rule is unmentioned.**
> "``default_viewables`` -- points an image at its browse PNGs."

`default_viewables` has two entries. The first is `(r'.*\.LBL', re.I, '')`, which
gives every label an empty viewable — the same construct that `EBROCC_xxxx.py`'s
docstring does describe ("and an empty viewable for a label file"). The second
returns a single path, `EXTRAS/THUMBNAIL/\3.PNG`, with the in-code comment "the
internal previews can work for now". So it is one PNG, not "its browse PNGs", and
the label rule is dropped.

**11. `JNOSRU_xxxx.py` — the stated reason is not a reason.**
> "A data file is FITS here, which is why this module names it rather than leaving
> it to the default table."

The default `DESCRIPTION_AND_ICON` in `rules/__init__.py` line 310 is
`(r'.*\.fits{0,1}', re.I, ('FITS data file', 'DATA'))`, which matches `.FIT` and
`.FITS`. The default table handles FITS perfectly well; the module overrides it to
get a better description and a different icon (`Image file, FITS` / `IMAGE`), not
because FITS is unhandled.

### B. Numbers, counts and enumerations that do not re-derive

**12. `VG_28xx.py` — "Sixteen" should be eighteen.**
> "Sixteen of the module's top-level names exist for that translation."

The bullet list that follows names eighteen: `SUN_DICT`, `SU_DICT`, `URING_DICT`,
`URING_INV_DICT`, `IE_DICT`, `KIND`, `KIND_UC`, `ICON`, `NEXT`, `SRSS_DICT`,
`URSS_DICT`, `FRAME_DICT`, `COORD_DICT`, `CU_DICT`, `VIP_DICT`, `POLE_DICT`,
`US23_DICT`, `USTAR_DICT`. An AST walk of the module's top-level assignments finds
exactly those eighteen names and no others of that kind. The count contradicts the
list immediately below it.

**13. `NHxxxx_xxxx.py` — the MVIC range is not contiguous.**
> "``FILE_CODE_PRIORITY`` -- the hexadecimal file codes mapped to a sort priority,
> covering the LORRI codes 630 through 63B and the MVIC codes 530 through 54A."

The dictionary has 36 entries: 12 LORRI (630-63B, genuinely contiguous) and 24
MVIC. The hex range 530 through 54A is 27 values; `53C`, `53D` and `53E` are
absent. "covering ... 530 through 54A" reads as complete coverage of that range and
is not.

**14. `COISS_xxxx.py` — "one entry per leading three digits" is false for four of 52.**
> "The reverse table is written as one entry per leading three digits of the
> spacecraft clock, each naming the small range of volumes that can hold it."

`opus_id_to_primary_logical_path` has 52 entries. Four do not have that shape:
`co-iss-([nw]14[123].*)`, `co-iss-([nw]13[789].*)`, `co-iss-([nw]13[0-4].*)` — each
covering several three-digit prefixes — and `co-iss-([nw]12.*)`, which keys on only
two digits.

**15. `COVIMS_0xxx.py` — the identical sentence, the identical error.**
Same claim, same wording. Its `opus_id_to_primary_logical_path` has 49 entries, of
which `co-vims-(v14[0-6].{7})`, `co-vims-(v13[7-9].{7})`, `co-vims-(v13[0-4].{7})`
and `co-vims-(v12..{7})` break the rule; the last keys on two digits.

**16. `COCIRS_xxxx.py` — "one entry per observed body" over- and under-counts.**
> "The type table carries one "Extra Browse Diagram" entry per observed body."

`opus_type` has 21 "Extra Browse Diagram" entries: 18 keyed on NAIF IDs 601-618,
plus `(Default)`, `(Saturn)` and `(Rings)`. "Rings" is not a body and "Default" is
not a body. And unlike the description table's per-body run, which the same
paragraph describes as running "from Jupiter and the Galilean moons through Saturn
and its satellites out to Pan", `opus_type` has no Jupiter or Galilean entries at
all — so the two "per observed body" statements in one bullet list mean two
different, unequal sets.

**17. `VG_28xx.py` — `ICON` does not cover "the same product kind codes".**
> "``ICON`` -- the same product kind codes mapped to the icon type each gets."

`KIND` and `KIND_UC` each have 11 keys (C, D, F, G, J, N, P, R, T, V, W). `ICON`
has 10: it omits `"P"` (calibrated profile), which is the single most common
product kind in this volume set. "the same product kind codes" is wrong.

**18. `RPX_xxxx.py` — there is no mask for the header.**
> "The HST volumes hold FITS files in matched sets: raw image, calibrated image,
> engineering data, HST header file, and a mask for each."

`description_and_icon_by_regex` names four data directories (`RAWIMAGE`,
`CALIMAGE`, `ENGDATA`, `HEADER`) and three mask directories (`RAWMASK`, `CALMASK`,
`ENGMASK`). There is no `HEADERMASK`. "a mask for each" over-counts by one.

**19. `GO_0xxx.py` — "every such image and the image it supersedes" has exceptions.**
> "The module header enumerates every such image and the image it supersedes."

Two lines of that header give no counterpart:
`# GO_0007/REDO/C0059466445R.IMG (no counterpart)` and
`# GO_0023/REDO/E11/IO/C0420361500R.IMG (no counterpart)`.

**20. `rules/__init__.py` — `__all__` is short by one, and the sentence hides it.**
> "``__all__`` lists dataset modules of this package, but nothing imports them
> through it: ``pds3file/__init__.py`` names each one explicitly in a ``from .rules
> import`` block ..."

There are 25 dataset modules; `__all__` has 24 entries. `JNOSRU_xxxx` is missing
from it. `pds3file/__init__.py` lines 243-268 do name all 25 explicitly, so the
second half of the sentence is correct — but the deliberately unquantified "lists
dataset modules" conceals a real gap that a reader would want flagged. Say the
number, or say which one is absent. (See code defect C8.)

### C. Dataset facts contradicted by the holdings

**21. `JNOJIR_xxxx.py` — the volume named in the sentence carries a different data
set ID.**
> "Its volumes are numbered one per orbit, starting from JNOJIR_1000 for the 2013
> Moon images and JNOJIR_1001 for orbit insertion, and carry data set ID
> JNO-J-JIRAM-2-EDR-V1.0 (``_volinfo/JNOJIR_xxxx.txt``)."

`_volinfo/JNOJIR_xxxx.txt`:

```
JNOJIR_xxxx/JNOJIR_1000 | Juno JIRAM raw Moon images, 2013-10-09 || 1.0 | 2015-11-16 | JNO-L-JIRAM-2-EDR-V3.0
JNOJIR_xxxx/JNOJIR_1001 | Juno JIRAM raw images from orbit insertion, ... | JNO-J-JIRAM-2-EDR-V1.0
```

The Moon volume carries `JNO-L-JIRAM-2-EDR-V3.0` (L for Luna, version 3.0), not the
ID the same sentence assigns it. Counting the whole file, the volume set carries
four data set IDs: `JNO-J-JIRAM-2-EDR-V1.0` (64 volumes),
`JNO-J-JIRAM-3-RDR-V1.0` (63), `JNO-L-JIRAM-2-EDR-V3.0` (1) and
`JNO-L-JIRAM-3-RDR-V3.0` (1).

**22. `JNOJIR_xxxx.py` — the 2nnn volumes are invisible in the prose.**
> "Its volumes are numbered one per orbit ..."

Every orbit has two volumes: `JNOJIR_1nnn` (raw) and `JNOJIR_2nnn` (reduced), per
`_volinfo`. That pairing is the entire reason the module's patterns say
`JNOJIR_[12]\d\d\d` and the reason `associations_to_volumes` rewrites `1` to `2`
while swapping `EDR` for `RDR`. The docstring's "An observation is a raw or
calibrated image or spectrum" hints at it but the volume-numbering sentence
contradicts it.

**23. `VG_20xx.py` — Voyager 1 never reached Uranus or Neptune.**
> "The one volume, VG_2001, carries four data set IDs, one each for the Jupiter,
> Saturn, Uranus and Neptune encounters of Voyager 1 and Voyager 2."

`_volinfo/VG_20xx.txt` gives the four IDs as `VG1/VG2-J-IRIS-3-RDR-V1.0`,
`VG1/VG2-S-IRIS-3-RDR-V1.0`, `VG2-N-IRIS-3-RDR-V1.0` and
`VG2-U-IRIS-3-RDR-V1.0`. Only the Jupiter and Saturn IDs cover both spacecraft; the
Uranus and Neptune IDs are Voyager 2 alone. The module's own description table says
the same thing — it has `VG1_JUP`, `VG2_JUP`, `VG1_SAT`, `VG2_SAT` but only
`VG2_URA` and `VG2_NEP`.

**24. `CORSS_8xxx.py`, `COUVIS_8xxx.py`, `COVIMS_8xxx.py` — "upper-case file names"
is false in all three.**
> CORSS: "the earlier version used upper-case file names, put the data under
> ``EASYDATA/`` rather than ``data/``, ..."
> COUVIS: "earlier versions used upper-case file names, put the data under
> ``DATA/EASYDATA/`` rather than ``data/``, and wrote an underscore after "TAU"."
> COVIMS: "the earliest version used upper-case file names and put the data under
> ``EASYDATA/`` rather than ``data/``."

The holdings show the *data file basenames are upper case in both versions*; what
changed is the directory names.

```
COUVIS_8xxx_v1/COUVIS_8001/DATA/EASYDATA/UVIS_HSP_2005_139_126TAU_E_TAU_01KM.TAB
COUVIS_8xxx   /COUVIS_8001/data/         UVIS_HSP_2005_139_126TAU_E_TAU01KM.TAB
COVIMS_8xxx_v1/COVIMS_8001/EASYDATA/     VIMS_2005_144_OMICET_E_TAU_01KM.TAB
COVIMS_8xxx   /COVIMS_8001/data/         VIMS_2005_144_OMICET_E_TAU_01KM.TAB
CORSS_8xxx_v1 /CORSS_8001/EASYDATA/Rev07E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_TAU_01KM.TAB
CORSS_8xxx    /CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_X43_E/RSS_2005_123_X43_E_TAU_01KM.TAB
```

The `#UPPER#` directive in those `versions` tables is applied to the captured
*directory* component (`data`→`DATA`, `browse`→`BROWSE`, `document`→`DOCUMENT`);
the all-upper variant it also emits matches nothing in the v1 trees, whose
`Rev07E_..._Summary.pdf` names are mixed case. The three modules all state the
directory rename as a file-name rename.

**25. `COUVIS_8xxx.py` — "earlier versions" is one version.**
The plural implies at least `_v1`, `_v2.0` and `_v2.1`. Only `_v1` uses
`DATA/EASYDATA/`; `holdings/volumes/COUVIS_8xxx_v2.0/COUVIS_8001/` and
`_v2.1/COUVIS_8001/` both contain `data`. The parallel sentence in
`COVIMS_8xxx.py` correctly says "the earliest version".

**26. `VG_28xx.py` — `US23_DICT` holds Saturn observations, not Uranus.**
> "``US23_DICT`` -- two Uranus data files whose descriptions do not follow from
> their codes."

```python
US23_DICT = """{
3:"Voyager 1 iota Her C ring egress",
2:"Saturn delta Sco ingress"}"""
```

The C ring is Saturn's, and the second value says "Saturn" outright. The dictionary
is keyed off the file-name prefix `US(2|3)` — U for UVS, S for Saturn — and is used
only by two entries whose patterns are `.*/US(2|3)...`. Neither file is Uranus.

**27. `VG_28xx.py` — `SUN_DICT` does not give a star for two of its four keys.**
> "``SUN_DICT`` -- the occultation star codes N1, S1, U1 and U2 mapped to the planet
> and star they stand for."

`"N1": "Neptune"` and `"S1": "Saturn"` name only a planet. Only `"U1": "Uranus
sigma Sgr"` and `"U2": "Uranus beta Per"` name a star. (The star names for N1 and S1
do appear elsewhere in the module — "Neptune sigma Sgr ring profile", "Saturn delta
Sco ring profile" — but not in this dictionary, which is what the sentence is
about.)

**28. `GO_0xxx.py` — "Shoemaker-Levy 9" is an expansion no file in the tree states.**
> "... and the images carrying a Shoemaker-Levy 9 graphics overlay."

`grep -ri shoemaker` over `work/src`, `_volinfo/` and
`holdings/volumes/GO_0xxx/` returns exactly one hit: this new docstring line. The
code says `SL9` throughout (`'Image with SL9 graphics overlay, VICAR'`,
`'Index for SL9 multiple exposures'`), and so does the OPUS title the same
docstring quotes two bullets later ("Image with SL9 graphics overlay"). The
expansion is almost certainly right, but it is unsourced in this repository and in
the holdings, and it makes the docstring assert something the code never does.

**29. `NHxxxx_xxxx.py` — "command and data handling units" is likewise unsourced,
and the mode list is wrong for MVIC.**
> "The comment on each entry names the mode it stands for: lossless, packetized or
> lossy, high-resolution or binned, and which of the two command and data handling
> units produced it."

The code writes `CDH 1` / `CDH 2` and never expands it; nothing in the tree does
either. And "high-resolution or binned" describes only the twelve LORRI comments.
The 24 MVIC comments name "Panchromatic TDI", "Panchromatic TDI 3x3 Binned", "Color
TDI" and "Panchromatic Frame Transfer" — four modes, of which only one is a binning
distinction and none is "high-resolution".

**30. `JNOJNC_xxxx.py` — volumes are not numbered by orbit.**
> "its volumes are numbered by orbit ..."

`_volinfo/JNOJNC_0xxx.txt`: `JNOJNC_0001` is "cruise and orbit 0", `JNOJNC_0002` is
"orbits 0-2", `JNOJNC_0024` is "orbits 45-47", `JNOJNC_0029` is "orbits 59-62". The
volumes are numbered sequentially and each spans a variable range of orbits.

### D. Relationship claims that do not hold

**31. `CORSS_8xxx.py` — not the largest set of named viewables.**
> "``skyview_viewables`` and ``dsntrack_viewables`` are defined by no other rule
> module, and this is the largest set of named viewables any of them offers."

The first half is correct (AST census over all 36 rule modules). The second half is
false. At runtime, `CORSS_8xxx.VIEWABLES` has 6 keys; `COCIRS_xxxx.VIEWABLES` has
21 (`atlas, calypso, default, dione, enceladus, epimetheus, helene, hyperion,
iapetus, janus, mimas, pan, pandora, phoebe, prometheus, rhea, rings, saturn,
telesto, tethys, titan`). `COCIRS_xxxx.py`'s own docstring says "twenty-one named
viewables" in this same PR, so the two files contradict each other.

**32. `rules/__init__.py` — three volume sets falsify the override rule.**
> "``FILESPEC_TO_BUNDLESET`` -- ... A volume set whose name does not end in exactly
> three x's overrides it."

Eleven modules define `filespec_to_bundleset`. `JNOJIR_xxxx.py`, `JNOSRU_xxxx.py`
and `RES_xxxx.py` do not, and all three have volume set names that the default
cannot produce. Runtime, with only the default in play:

```
JNOJIR_1000/DATA/x.dat -> JNOJIR_1xxx   (volume set is JNOJIR_xxxx)
JNOSRU_0001/data/x.fit -> JNOSRU_0xxx   (volume set is JNOSRU_xxxx)
RES_0001/x.tab         -> RES_0xxx      (volume set is RES_xxxx_prelim)
```

The sentence states a rule the package does not follow. (See code defect C9.)

**33. `HSTxx_xxxx.py` — the stated reason is not the reason.**
> "``filespec_to_bundleset`` -- maps a file specification beginning with an
> HSTnx_nnnn volume ID to its volume set name, which the default rule cannot do
> because these volume set names do not end in three x's."

`HSTIx_xxxx` *does* end in three x's. The default rule
(`([A-Z0-9]{2,6}_\d)\d{3}.*` → `\1xxx`) fails here because it only replaces the
last three characters of the volume ID: `HSTI1_1000` would become `HSTI1_1xxx`,
whereas the volume set is `HSTIx_xxxx` — the digit in position 5 must become an "x"
too. That is what the module's `HST([A-Z])[01]_\d{4}.*` → `HST\1x_xxxx` actually
does.

**34. `JNOJNC_xxxx.py` — "unusual" is not supported.**
> "The subclass and this module are named JNOJNC_xxxx, and the volume set translator
> is what maps the volume set name JNOJNC_0xxx onto that subclass; the two names are
> not the same string, which is unusual among these modules."

Module/subclass names differ from the volume set name in `RES_xxxx.py`
(`RES_xxxx_prelim`), `VGIRIS_xxxx.py` (`VGIRIS_xxxx_peer_review`), and in every
multi-volume-set module: `COCIRS_xxxx`, `COISS_xxxx`, `VGISS_xxxx`, `HSTxx_xxxx`,
`NHxxxx_xxxx`. That is at least 7 of 25 — common enough that "unusual" misleads.

**35. `COVIMS_0xxx.py` — `FILENAME_KEYLEN` is never a translator.**
> module docstring: "... because this volume set's grouping rule is computed by
> ``COVIMS_0xxx.FILENAME_KEYLEN`` rather than expressed as a translator."
> class docstring: "... defines ``OPUS_ID_TO_PRIMARY_LOGICAL_PATH`` and
> ``FILENAME_KEYLEN`` as functions rather than as translators."

`pdsfile.py:382` sets `FILENAME_KEYLEN = 0`, an integer, and
`_properties.py:2507-2510` accepts an `int` or a callable and nothing else. Five
rule modules set it to a plain integer (`GO_0xxx`=11, `HSTxx_xxxx`=9,
`VG_0xxx`=8, `VGISS_xxxx`=8, `NHxxxx_xxxx`=14). The contrast is
function-versus-integer, not function-versus-translator. The parallel claim about
`OPUS_ID_TO_PRIMARY_LOGICAL_PATH` is correct — that one really is a translator by
default.

**36. `ASTROM_xxxx.py` and `RES_xxxx.py` — the class docstring boilerplate is false.**
> "The class body puts this module's rule tables in front of the class attributes
> ``Pds3File`` reads, and the module tail registers the class in
> ``Pds3File.SUBCLASSES`` under the key "X". The module docstring describes the
> volume set and every table."

An AST scan of every class body shows these two assign no rule attribute at all.
`ASTROM_xxxx`'s class body only mutates the parent's `VOLSET_TRANSLATOR`; its one
table is added at module level on line 51, outside the class. `RES_xxxx` has no
tables whatsoever — its own module docstring says "``RES_xxxx.py`` defines no rule
tables at all" — so the class docstring contradicts the module docstring on the
same page, and its last sentence promises a description of tables that do not
exist. (`ASTROM_xxxx.py`'s module docstring gets this right: "The class body puts
ASTROM_xxxx in front of ``Pds3File.VOLSET_TRANSLATOR``".)

**37. `VG_28xx.py` — two documented tables are never installed.**
> "``sort_key`` and ``split_rules`` -- the basename sort order and the basename
> grouping."

`VG_28xx.py` defines `split_rules` (line 562) and `sort_key` (line 571), but the
`class VG_28xx` body assigns `DESCRIPTION_AND_ICON`, `OPUS_TYPE`, `OPUS_FORMAT`,
`OPUS_PRODUCTS`, `OPUS_ID`, `OPUS_ID_TO_PRIMARY_LOGICAL_PATH`, `VIEWABLES`,
`ASSOCIATIONS` and `VERSIONS` — and neither `SORT_KEY` nor `SPLIT_RULES`. Both
tables are dead. The bullet presents them as effective rules, and the class
docstring's "The class body puts this module's rule tables in front of the class
attributes ``Pds3File`` reads" is false for them. (See code defect C5.)

**38. `GO_0xxx.py` — the directories the docstring says are named are not named.**
> "``description_and_icon_by_regex`` -- names the orbit and target directories, the
> calibration, Earth-Moon and optical-experiment directories, the reprocessed-image
> directories, and the images carrying a Shoemaker-Levy 9 graphics overlay."

Six rules in that table are one path component short and can never fire on a real
logical path, because `\w` does not span `/`. Runtime against the real tree:

```
volumes/GO_0xxx/GO_0006/RAW_CAL       -> None   (rule is volumes/\w+/RAW_CAL)
volumes/GO_0xxx/GO_0004/GOPEX         -> None   (rule is volumes/\w+/GOPEX)
volumes/GO_0xxx/GO_0006/REDO          -> None
volumes/GO_0xxx/GO_0018/REDO          -> None
volumes/GO_0xxx/GO_0022/I24/IO/REPAIRED -> None
```

and end-to-end, `Pds3File.from_abspath(.../GO_0xxx/GO_0002/RAW_CAL).description`
is the generic `"Directory"`, as is `GO_0002/VENUS`. So of the five things the
sentence claims, only "the orbit and target directories" (the nested
`.../E26/EUROPA` form) and the SL9 overlay images are actually named; the
calibration, Earth-Moon, optical-experiment, top-level-target and reprocessed-image
directories are not. (See code defect C6.)

**39. `rules/__init__.py` — previews sort by *decreasing* size.**
> "``SORT_KEY`` -- ... It orders previews by increasing size, ..."

`SORT_KEY` maps `_thumb`→`_4thumb`, `_small`→`_3small`, `_med`→`_2med`,
`_full`→`_1full`, so `_full` sorts first. Runtime:
`sort_basenames(['x_thumb.jpg','x_small.jpg','x_med.jpg','x_full.jpg'])` returns
`['x_full.jpg', 'x_med.jpg', 'x_small.jpg', 'x_thumb.jpg']`. The docstring repeats
the base file's own comment `# Previews sort into increasing size`, which is itself
wrong; a docstring pass is where that should have been caught rather than
propagated.

**40. `rules/__init__.py` — `INFO_FILE_BASENAMES` does not match "any basename
ending in" those five.**
> "``INFO_FILE_BASENAMES`` -- which basenames count as the information file for the
> directory they sit in: ``voldesc.cat``, ``voldesc.sfd``, and any basename ending
> in ``INFO.txt``, ``INF.txt``, ``DOC.txt``, ``AAREADME.txt`` or ``README.txt``."

The translator anchors every pattern as `^...$` (`translator/__init__.py:438-441`).
The rules are `(\w+INFO\.txt)`, `(\w+INF\.txt)`, `(\w+DOC\.txt)`,
`(AAREADME\.txt)` and `(README\.txt)`. So the first three need at least one
*word* character in front — `INFO.txt` on its own does not match, and neither does
`VOL-INFO.txt` — and the last two are exact matches, not suffixes. Runtime:

```
AAREADME.txt  -> AAREADME.txt      VOLINFO.txt -> VOLINFO.txt
XAAREADME.txt -> None              INFO.txt    -> None
MYREADME.txt  -> None              INF.txt     -> None
```

### E. Incomplete enumerations presented as complete

**41. `COUVIS_8xxx.py` — the `versions` reason list omits the largest group.**
> "``versions`` -- ... which cannot be found by wildcarding the version suffix
> alone: earlier versions used upper-case file names, put the data under
> ``DATA/EASYDATA/`` rather than ``data/``, and wrote an underscore after "TAU"."

The colon promises a complete account of why. It omits the first three entries of
the table, which repair *misnamed* files in early versions by pairing observations
whose dates differ: `2005_139` with `2009_062` for THEHYA, `2007_038` with
`2008_026` for SAO205839, and `2010_148` with `2010_149` for LAMAQL. That is a
fourth and quite different reason, and it is the only one the reader could not
guess.

**42. `rules/__init__.py` — `SIBLINGS` is described by its first rule only.**
> "``SIBLINGS`` -- the pattern matching basenames treated as adjacent within one
> directory. All files in ``document/``, ``calib/``, ``catalog/``, ``index/`` and
> ``label/`` are siblings of one another."

That is rule 1 of 4. Rules 2-4 are
`(r'(\w+-?\w+-?\w+)/[^/]+/[^/]+/[^/]+', re.I, '*')` and its two shorter forms,
which make *every* file at depth 2, 3 or 4 under any category a sibling of every
other — which is most of what the table does. The docstring describes the special
case and drops the general one.

**43. `rules/__init__.py` — `OPUS_PRODUCTS` is not "the contents".**
> "``OPUS_PRODUCTS`` -- glob patterns for every file OPUS offers alongside a
> product, which here is the contents of the volume set's document directory."

The single rule emits `documents/\1/*.[!lz]*`, a glob that excludes any basename
whose extension begins with `l` or `z` (labels, zips) and any basename with no dot
at all. It is the contents minus a filter, and the filter is the only interesting
part of the rule.

**44. `COISS_xxxx.py` — the PDS4 cross-products list one index, not two.**
> "``cross_pds3_pds4_products`` -- the PDS4 products OPUS offers alongside a PDS3
> Cassini ISS image: the reprojected images, their browse products and their indices
> from the cassini_iss_fring_mosaics_rsfrench2025 and
> cassini_iss_spokes_hedman-hamilton-2024 bundles."

The plural "their indices ... from [both bundles]" is wrong. The only index
products are two files from the fring bundle
(`miscellaneous/global_reproj_img_index.lblx` and `.tab`); the spokes bundle
contributes only `data_derived/` and `browse_derived/` products, no index.

**45. `COISS_xxxx.py` — only three of the four "extras" get their own entry.**
> "``description_and_icon_by_regex`` -- ... names the calibrated products and the
> thumbnail, browse, full and TIFF extras, ..."

The table names `thumbnail` ("Small browse images"), `(tiff|full)` ("Full-size
browse images") and their files. `extras/browse` gets no entry of its own; it falls
to the generic `volumes/.*/data/.*/extras(/\w+)*(|/)` → "Preview image collection".

**46. `COVIMS_0xxx.py` — the description table also names two program binaries.**
The bullet lists the data directories, cubes, browse collections, browse images and
the preview-interpretation guide. It omits
`volumes/.*/software.*cube_prep/cube_prep` and
`volumes/.*/software.*/PPVL_report`, both → `('Program binary', 'CODE')`.

**47. `COCIRS/COISS/VGISS` — the quoted volume-set pattern is not the code's
pattern.**
> COCIRS: "matched by the pattern COCIRS_[0156]xxx"
> COISS: "matched by the pattern COISS_[0123]xxx"
> VGISS: "matched by the pattern VGISS_[5678]xxx"

The `VOLSET_TRANSLATOR` patterns are `COCIRS_[0156x]xxx`, `COISS_[0123x]xxx` and
`VGISS_[5678x]xxx` — each also matches the all-x form. `HSTxx_xxxx.py`
("HST.x_xxxx") and `NHxxxx_xxxx.py` ("NHxx.._xxxx") quote theirs character for
character, so within one PR the same construct is quoted two different ways.

**48. `NHxxxx_xxxx.py` and `HSTxx_xxxx.py` — the volume-ID shorthand is wrong.**
> NHxxxx: "maps a file specification beginning with an NHxxnn_nnn volume ID"
> HSTxx: "maps a file specification beginning with an HSTnx_nnnn volume ID"

NH's pattern is `NH..(MV|LO)_\d{4}.*`: the two characters after `NH` are the
mission phase (JU, PC, PE, KC, KE, LA), the next two are the *letters* MV or LO,
and the number is four digits, not three. HST's is `HST([A-Z])[01]_\d{4}.*`:
letter then digit, i.e. `HSTLd_nnnn`, not `HSTnx_nnnn`.

**49. `COCIRS_xxxx.py` — "one COCIRS observation" is only half the volume sets.**
> "... and it is why one COCIRS observation offers twenty-one named viewables."

True for COCIRS_5xxx/6xxx. Runtime on
`volumes/COCIRS_5xxx/COCIRS_5912/DATA/APODSPEC/SPEC0912111106_FP1.DAT`: all 21
viewable sets return a pattern. But on
`volumes/COCIRS_0xxx/COCIRS_0406/DATA/CUBE/POINT_PERSPECTIVE/000IA_PRESOI001____RI____699_F4_038P.LBL`
only `default` returns anything — every satellite, saturn and rings entry is
`volumes/(COCIRS_[56]...)`-only. The module serves four volume sets and the
sentence is true of two.

**50. `COISS_xxxx.py` — COISS_3xxx data files are not N/W images.**
> "A data file is a VICAR image whose basename begins with N for the narrow-angle
> camera or W for the wide-angle camera, followed by the ten-digit spacecraft
> clock."

The preceding sentence in the same paragraph says COISS_3xxx holds Cassini
cartographic maps, and the module's own `default_viewables` has a separate
`COISS_3xxx.../data/(images|maps)/(\w+)` branch, while `FILENAME_KEYLEN` returns 0
for COISS_3xxx precisely because those basenames are not clock-keyed. The
statement is unqualified and false for one of the four volume sets.

**51. `JNOJNC_xxxx.py` — the raw/calibrated split does not reach the global maps.**
> "``description_and_icon_by_regex`` -- distinguishes raw from calibrated and RGB
> from methane-band, for both the images and the derived global maps; ..."

The four `DATA/[ER]DR/...` entries do both distinctions. The two
`DATA/GLOBAL_MAPS/...` entries distinguish only methane-band (`_\d\dH`) from RGB
(`_\d\dP`) and say nothing about raw versus calibrated. "for both" is wrong.

**52. `JNOJIR_xxxx.py` — the documents association is a replacement and the
docstring never says so.**
> "``associations_to_volumes``, ``associations_to_metadata`` and
> ``associations_to_documents`` -- cross the volumes, metadata and documents trees
> for one observation."

The class body reads
`ASSOCIATIONS['documents'] = associations_to_documents   # this is a replacement,
not an override`, and the table itself carries the comment "Note: this is a full
replacement of the default rule" plus a block explicitly re-implementing the
default behaviour. `COVIMS_0xxx.py` and `COVIMS_8xxx.py` both call out exactly this
("The documents entry replaces the default rather than adding to it"), so the
omission here is inconsistent within the PR.

**53. Class docstrings — `FILENAME_KEYLEN` is reported for four modules and silently
dropped for four others.**
The "It also ..." sentence in a class docstring is written as the full list of what
the class adds beyond its tables. `COISS_xxxx`, `RPX_xxxx`, `COVIMS_0xxx` and
`NHxxxx_xxxx` all name `FILENAME_KEYLEN`. `GO_0xxx` (11), `HSTxx_xxxx` (9),
`VG_0xxx` (8) and `VGISS_xxxx` (8) all set it and none of their docstrings mentions
it — `GO_0xxx`'s even has an "It also carries ..." sentence that lists
`METADATA_PATH_TRANSLATOR` and `opus_prioritizer` and stops.

### F. Wording

**54. `COUVIS_0xxx.DATA_SET_ID` — "and" should be "or", and the clause is
ungrammatical.**
> "Raises:
>     ValueError: if no versions table covers this file's logical path, and if the
>         table that does covers it holds no row under the key."

These are two independent conditions; either alone raises (`if not result: raise`
at line 330, `if not row.exists: raise` at line 350). "and" says both must hold.
"the table that does covers it" should be "the table that does cover it" or "the one
that does".

**55. `RPX_xxxx.py` — "still" anchors to a moment in time.**
> "``description_and_icon_by_regex`` -- distinguishes those FITS forms from one
> another, marks the ones **still** held as zipped FITS, ..."

The table has ten `\.ZIP` entries ("Image mask, zipped FITS" and so on). "still"
implies an unzipping in progress and dates the sentence; the neutral phrasing is
"the ones held as zipped FITS".

**56. `COVIMS_0xxx.py` — the module docstring drops the leading "v".**
> "A data file is an ISIS2 spectral image cube whose basename is a ten-digit
> spacecraft clock, a version number, and sometimes a three-digit sub-observation
> number."

Every regex in the module writes `v[0-9]{10}_[0-9]+`, and the module's own
`FILENAME_KEYLEN` docstring says "opens with an optional 'v'". The module docstring
omits it, so its description of a basename does not match any real basename
(`v1465673806_2.qub`).

**57. `VG_28xx.py` — the worked example does not decompose the way the sentence
says.**
> "A basename such as PU1P01AI.TAB encodes the experiment, the occultation star, the
> kind of product, the ring and the occultation direction in single characters, and
> every one of those characters has to be turned into English ..."

The file exists and the description resolves
(`('Uranus sigma Sgr ingress profile for ring alpha', 'SERIES')`), so the example is
sound — but the decomposition is `P` `U1` `P` `01` `A` `I`. The star code is two
characters, not one, and there is a two-character field (`01`, matched by `..` and
discarded) that the list of five fields never mentions.

---

## Code defects noticed

These are pre-existing; the PR changed no executable statement. Listed because they
are what several of the prose defects above are anchored to.

**C1. `VG_20xx.py:54` — `filespec_to_bundleset` returns a volume set that does not
exist.** `(r'VG_20\d{2}.*', 0, r'VG__20xx')` — two underscores. Runtime:
`FILESPEC_TO_BUNDLESET.first('VG_2001/x')` → `'VG__20xx'`, while the tree has
`holdings/volumes/VG_20xx`.

**C2. `COUVIS_8xxx.py` — the last `versions` entry names the wrong mission and is
dead.** Its pattern is
`r'volumes/COVIMS_8xxx(|_v[0-9\.]+)/COUVIS_8001/(\w+[^aA])(|/.*)'` — `COVIMS` in a
COUVIS module. Runtime: `COUVIS_8xxx.versions.all('volumes/COUVIS_8xxx/COUVIS_8001/browse')`
returns `[]`, whereas the parallel `COVIMS_8xxx.versions.all(...)` returns
`['volumes/COVIMS_8xxx*/COVIMS_8001/browse', 'volumes/COVIMS_8xxx_v1/COVIMS_8001/BROWSE']`.
COUVIS_8xxx therefore has no cross-version rule for any directory other than
`data`.

**C3. `JNOJNC_xxxx.py:94` — a space inside a volume ID makes the rule dead.**
`(r'volumes/(JNOJNC_0xxx/JNOJNC _0\d\d\d)/...` — note `JNOJNC _0`. The "associate
global maps with browse products" rule can never match.

**C4. `VG_28xx.py:183-185` — `FRAME_DICT` is a truncated literal and is never used.**

```python
FRAME_DICT = """{
1: "B1950",
2: "J2000""".replace('\n','')
```

The closing `"}` is missing, so the value is `{1: "B1950",2: "J2000`. Nothing would
parse it; the name appears nowhere else in the module (only in the new docstring),
so the breakage is latent.

**C5. `VG_28xx.py` — `sort_key` and `split_rules` are defined and never installed.**
The class body assigns no `SORT_KEY` and no `SPLIT_RULES`. Both tables are dead.

**C6. `GO_0xxx.py` — six description rules are one path component short.**
`volumes/\w+/(MOON|EARTH|VENUS|IDA|GASPRA|SL9)`, `volumes/\w+/RAW_CAL`,
`volumes/\w+/EMCONJ`, `volumes/\w+/GOPEX` need `volumes/\w+/\w+/...` to reach a real
logical path such as `volumes/GO_0xxx/GO_0002/RAW_CAL`. Two more are unreachable for
a different reason: `volumes/\w+/GO_00(0\d|1[0-6])\w+/REDO` requires at least one
extra word character after the volume number (`GO_0006x/REDO`), and
`volumes/\w+/GO_00(1[789]|2\d)REDO` requires `GO_0018REDO` with no separator. All
six return `None` at runtime and the directories fall through to `"Directory"`.

**C7. `rules/__init__.py` — `SPLIT_RULES` cannot match what `SORT_KEY` produces.**
`SORT_KEY` emits `_4thumb`, `_3small`, `_2med`, `_1full`, but the "after sort key"
split rule is `(r'(.*)_(1thumb|2small|3med|9full)\.(jpg|png)', ...)`. No preview
sort key ever matches it. (The comment on `SPLIT_RULES` says "they must also work
for the sort keys of basenames".)

**C8. `rules/__init__.py:76-101` — `__all__` omits `JNOSRU_xxxx`.** 24 entries for
25 modules. Harmless today because nothing imports through it, but it is a list that
claims to be a list.

**C9. `FILESPEC_TO_BUNDLESET` gives a non-existent volume set for three volume
sets.** `JNOJIR_1000` → `JNOJIR_1xxx`, `JNOSRU_0001` → `JNOSRU_0xxx`, `RES_0001`
→ `RES_0xxx`. The correct answers are `JNOJIR_xxxx`, `JNOSRU_xxxx` and
`RES_xxxx_prelim`, and no module overrides the default for any of the three.

**C10. `VG_0xxx.py` — `opus_type` is the only table in the package using `.IBQ`.**
`(r'volumes/.*/C[0-9]{7}\.IBQ', 0, ('Voyager ISS', 120, 'vgiss_ibq', 'Small Preview
(IBQ)', True))`. The module's other four tables and
`holdings_maintenance/pds3/pdslinkshelf.py:70` all use `.IBG`. Either the OPUS type
never fires or the other four tables never do. (I could not settle this from the
tree: `holdings/volumes/VG_0xxx` is empty in the testing copy.)

**C11. `EBROCC_xxxx.py` — an unreachable branch in `default_viewables`.** The first
entry `(r'.*\.lbl', re.I, '')` is case-insensitive and anchored, so it consumes
every `.LBL`; the `(DATA|BROWSE)/...\.(TAB|LBL)` entry's `LBL` alternative can never
be reached.

**C12. `RPX_xxxx.py` — `xxxx*` in two source patterns.** Two `versions` entries
begin `r'volumes/RPX_xxxx*/...'`. In a regex the `*` quantifies the preceding `x`,
so the pattern means `RPX_xxx` followed by any number of `x`. It happens to match
`RPX_xxxx`, but it is not the wildcard it was written to be, and unlike the
replacement side (where `*` is a glob) the source side is compiled as a regex.

**C13. Duplicated entries.** `VGISS_xxxx.py` `opus_type` repeats the
`BROWSE/.*/C\d{7}_GEOMED\..*` line verbatim; `CORSS_8xxx.py`
`description_and_icon_by_regex` repeats a four-line preview block (lines 67-70 and
72-75); `HSTxx_xxxx.py` repeats `volumes/.*/index/hstfiles\..*`;
`rules/__init__.py` repeats `(r'volumes/[^/]+', 0, (GENERIC_VOLSET_DESC, 'VOLDIR'))`.

**C14. Typos in user-facing description strings.** `COCIRS_xxxx.py`:
"Interopolated ousekeeping data". `NHxxxx_xxxx.py`: "Raw imag, FITS" and
"Calibrated imag, FITS". `VG_28xx.py`: "Ring intercept geomemtry", "Raw data with
anomalies identifed". `CORSS_8xxx.py`: "Thumbnail obervation diagram".
`rules/__init__.py`: "Checksum index of indices and metadatas", "GIF vewable image".

**C15. `COCIRS_xxxx.py` `split_rules` has unescaped dots.**
`(r'(.*)\.tar.gz', 0, (r'\1', '', '.tar.gz'))` — the second and third dots are
wildcards.

**C16. `COUVIS_0xxx.VERSIONS_PATH_AND_KEY` handles only single-digit version
suffixes.** `r'volumes/COUVIS_0xxx(|_v\d)/...'` matches `_v1` but not the
`_v1.0`/`_v2.1` forms that the archive uses for other volume sets and that
`versions` tables elsewhere in the package spell `(|_v[0-9\.]+)`.

---

## Claims I checked and found correct

Recorded so the review's coverage is visible.

- Every "only module" / "defined by no other rule module" claim, tested by an AST
  census of all 36 rule modules (pds3 + pds4): `s_rings_viewables` (COCIRS only),
  `skyview_viewables` and `dsntrack_viewables` (CORSS only), `FILE_CODE_PRIORITY`
  (NHxxxx only), `cross_pds3_pds4_products` (COISS only), `siblings` (JNOJIR only),
  `data_set_id` (COCIRS and EBROCC only), `opus_prioritizer` (GO_0xxx and NHxxxx
  only), `BASENAME_REGEX` as the only top-level `re.compile` in any rule module
  (COVIMS_0xxx only), and COCIRS as the only module that builds its viewable
  dictionary in a loop (the other module-level `for` loops, in COISS and in
  `pds4file/rules/uranus_occs_earthbased.py`, build OPUS lists, not viewables).
- `COUVIS_8xxx.py` and `COVIMS_8xxx.py` "defines a table of each of these same
  names": both modules define exactly the same 15 top-level names, in both
  directions.
- `COSP_xxxx.py`, `JNOSP_xxxx.py`, `NHSP_xxxx.py` are exactly the three SPICE-kernel
  modules defining `associations_to_documents`, `filespec_to_bundleset` and
  `info_file_basenames`; all three companion document directories exist with a SPICE
  Toolkit link and a per-mission kernel selection tool
  (`_volinfo/{COSP,JNOSP,NHSP}_xxxx.txt`).
- `NHSP_xxxx.py` "the only one of the three written with a trailing wildcard, so it
  also matches a versioned volume set name such as NHSP_xxxx_v1": the pattern is
  `NHSP_xxxx.*`, the other two are exact, and `NHSP_xxxx_v1` exists in `_volinfo`.
- The `info_file_basenames` precedence claim in all three SPICE modules: runtime on
  `['voldesc.cat','aareadme.txt','data']` gives `voldesc.cat` for the default and
  `aareadme.txt` for `COSP_xxxx`.
- `VG_28xx.py` "``opus_type`` -- files products under four OPUS categories ... No
  other rule module spans four": VG_28xx has 4 (`Voyager ISS/PPS/RSS/UVS`); the next
  highest is COCIRS with 3, two of which are the generic `browse` and `metadata`.
- `VG_28xx.py` `NEXT` "the integers 5 through 13 mapped to the next integer as a
  string" — exactly 5..13 → "6".."14".
- `VG_28xx.py` `URING_DICT` "six through epsilon, plus X for the ring plane"
  (`X` → `ringpl`), `COORD_DICT`, `CU_DICT`, `VIP_DICT`, `POLE_DICT`, `USTAR_DICT`,
  `SRSS_DICT`/`URSS_DICT`, `KIND`/`KIND_UC`, and the "dictionary written as a string
  with its newlines stripped, concatenated into the replacement pattern and
  subscripted by a captured group" mechanism.
- `VG_28xx.py` the four volumes and their data set IDs, verbatim against
  `_volinfo/VG_28xx.txt`; and "names the source-image directories of VG_2810 and
  their raw, cleaned, geometrically corrected and TIFF forms" (`RAW`, `CLEANED`,
  `GEOMED`, `RAWTIFF`, `GEOMTIFF`, `ANNOTATED`, `SOURCE`, `SCANS`).
- `COCIRS_xxxx.py` `spice_lookup` "NAIF body IDs 601 through 618 ... from Mimas
  through Pan" — 18 entries, 601 Mimas, 618 Pan; and `viewables` holding "default",
  "saturn", "rings" plus one per satellite, giving 21 keys at runtime.
- `COCIRS_xxxx.py` `data_set_id` "one volume carries different data set IDs for its
  TSDR and CUBE trees, and ... the early COCIRS_0xxx volumes are Jupiter data while
  the later ones are Saturn data": `COCIRS_0[0-3]` → `CO-J-CIRS-...`,
  `COCIRS_0[4-9]` → `CO-S-CIRS-...`, with TSDR and CUBE splitting to different IDs.
- `COCIRS_xxxx.py` `versions` "allowing for a TSDR subdirectory that is present in
  some versions and absent in others" — the `(TSDR/|)` capture and the two-way
  output.
- `COISS_xxxx.py` `sort_key` "skips the leading N or W"; `FILENAME_KEYLEN` "returns
  0 for COISS_3xxx and 11 elsewhere"; the CISSCAL software and ISS calibration
  report in COISS_0011 (both `_volinfo/COISS_0xxx.txt` and the description table);
  `range_regex` being inclusive of both endpoints (`range_regex(10,12)` matches 10,
  11 and 12), which is what "each inclusive range of ten-digit product IDs" rests
  on.
- `COVIMS_0xxx.py` `FILENAME_KEYLEN` "a three-digit sub-observation number between
  000 and 069" (`_0[0-6][0-9]`); the documents override (`=` not `+=`); and the
  `OPUS_ID_TO_PRIMARY_LOGICAL_PATH` description of the glob-then-alphabetic-version
  path.
- `GO_0xxx.py` and `NHxxxx_xxxx.py` `opus_prioritizer` docstrings: rank +10 / +50,
  `_alternate` slug, " (Superseded Processing)" / " Alternate Downlink" title,
  single-copy and non-`volumes/` early exits, in-place mutation, grouping by version
  rank, the `_0x` three-hex-character extraction, and both `Raises:` analyses
  (`KeyError` from `FILE_CODE_PRIORITY[code]`; `TypeError` from `sort()` falling
  through to lists of `PdsFile`, which define no ordering).
- `NHxxxx_xxxx.py` "A raw volume is numbered 1nnn and its calibrated counterpart
  2nnn" and the two example volume names — `NHJULO_1001` (Jupiter flyby, LORRI) and
  `NHKEMV_1001` (Arrokoth flyby, MVIC) — both present in `_volinfo`.
- `RPX_xxxx.py` volume-by-volume: RPX_0001-0005 HST WFPC2 October 1994 to November
  1995, and RPX_0101/0201/0301/0401 as William Herschel, IRTF, Canada-France-Hawaii
  and WIYN at Kitt Peak (the docstring even corrects the archive's "Willam"
  misspelling); and the `FILENAME_KEYLEN` hedge "which of the volumes present
  selects RPX_0001 through RPX_0005", which is the right way to state a claim that
  depends on `'/RPX_000' in abspath`.
- `EBROCC_xxxx.py` "six data set IDs, one per observatory: ESO1M, ESO22M, IRTF,
  LICK1M, MCD27M and PAL200" and "the 28 Sgr occultation of Saturn's rings"
  (`_volinfo/EBROCC_xxxx.txt`); the five OPUS types; and
  `pds4file/rules/uranus_occs_earthbased.py` existing as named.
- `HSTxx_xxxx.py` the five instrument mappings (WFC3/ACS/NICMOS/STIS/WFPC2) against
  `_volinfo/HST{I,J,N,O,U}x_xxxx.txt`, and the "placeholder volumes for OPUS
  queries" framing.
- `JNOJNC_xxxx.py` "from JNOJNC_0007 on, JUNO-J-JUNOCAM-4-RDR-L1B-V1.0": 0001-0006
  carry two data set IDs, 0007 onward carry three.
- `ASTROM_xxxx.py`, `COSP_xxxx.py`, `JNOSP_xxxx.py`, `NHSP_xxxx.py`,
  `JNOSRU_xxxx.py`, `CORSS_8xxx.py`, `COVIMS_0xxx.py`, `RES_xxxx.py` volume names,
  descriptions and data set IDs, each checked line by line against `_volinfo`.
  `RES_xxxx.py`'s "defines no rule tables at all" is true: the file is 47 lines and
  its single `TranslatorByRegex` is the volume set translator.
- `JNOJIR_xxxx.py` `sort_key` (all four behaviours), `split_rules` (the "before" and
  "after" forms), and the `siblings` override.
- All 26 `SUBCLASSES['<key>'] = <Class>` registrations match the key each class
  docstring names.
- Style gates: no non-ASCII character in any of the 26 files; no docstring line over
  90 columns; no double space after a sentence period; American spelling throughout.

---

## Could not verify either way

- **`VG_0xxx.py` IBG versus IBQ.** `holdings/volumes/VG_0xxx` contains no files in
  this testing copy, so I cannot read the real extension off disk. The weight of the
  code (four tables plus `pdslinkshelf.py`) is on `IBG`, which is why I filed the
  docstring's `IBQ` as a defect, but the archive itself did not settle it.
- **`VG_0xxx.py` "The same observations appear decompressed, and with calibrated
  versions, under the VGISS_5xxx through VGISS_8xxx volume sets".** The volume-set
  correspondence is confirmed by the module's `default_viewables` (VG_000[1-3] →
  VGISS_7xxx, VG_000[45] → VGISS_6xxx, and so on), but whether the *sets of
  observations* coincide is not checkable from the tree, and no file in the
  repository states it.
- **`GO_0xxx.py` "Volumes group images by orbit and by target, with separate
  directories for calibration images, for the Earth-Moon conjunction and for the
  Galileo Optical Experiment."** `RAW_CAL` and the orbit/target directories are in
  the testing copy; `EMCONJ` and `GOPEX` are not, and per the brief their absence is
  not evidence. The description table does contain entries for both names (even
  though those entries never fire — C6), so the claim is at least sourced.
- **`COUVIS_0xxx.py` "This volume set is the reason the data set ID cannot always be
  a translator."** A causal claim about the design. It is consistent with the code
  (COUVIS_0xxx is one of only two modules that make `DATA_SET_ID` a method) but
  nothing in the repository states the causation, and `EBROCC_xxxx.py` reaches the
  same problem with a translator.
- **`CORSS_8xxx.py` "used a different number of digits after "Rev", and had a
  different directory tree".** Both are visible in the tree (`Rev07E` versus
  `Rev007E`; `EASYDATA/Rev07E_RSS_.../` versus
  `data/Rev007/Rev007E/Rev007E_RSS_.../`) and I count them as correct, but I could
  not confirm the third clause about `browse/` because `CORSS_8xxx_v1` in the
  testing copy holds only `DOCUMENT` and `EASYDATA`.
- **`RPX_xxxx.py` "A basename in the HST volumes of this volume set opens with a
  nine-character HST group ID".** Consistent with the `versions` patterns
  (`(U...)XXXX` plus `(\w{4}).`) and with `FILENAME_KEYLEN` returning 9, but there
  are no RPX HST data files in the testing copy to measure a real basename against.
- **`HSTxx_xxxx.py` "16-bit TIFFs of raw images".** The table says "16-bit unscaled
  TIFF of raw image" and the OPUS type says "Raw Data Preview (lossless)". The
  "16-bit" figure comes from the code's own string, so the docstring is faithful to
  the repository; whether the archive's TIFFs really are 16-bit I did not check.
