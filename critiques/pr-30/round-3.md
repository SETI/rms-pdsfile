# PR-30 round 3 — the 26 pds3 rule modules, second independent read

## What I read and how

Slice: `src/pdsfile/pds3file/rules/*.py` (26 files, 9,947 lines) in
`/seti/all_repos/rms-pdsfile-pr30/work`.

Order of work, deliberately front-loading the corrections:

1. `git show d108bae -- src/pdsfile/pds3file/rules/` in full (1,283 diff lines), and then
   each added sentence checked against the code and the holdings as if new.
2. Every module read in the tree, not the diff, so that pre-existing prose got a read too.
3. Instrumentation rather than reading wherever a claim was mechanically checkable:
   - the rule tables imported and run on real logical paths under
     `PDS3_HOLDINGS_DIR=/seti/opus/pdsdata/holdings` (`DESCRIPTION_AND_ICON.first`,
     `versions.all`, `associations_to_volumes.all`) to settle "never fires", "falls
     through to", "rewrites";
   - an AST walk over the 25 dataset modules to enumerate every class-body assignment and
     classify it as added (`x + Base.X`) or assigned outright, to settle the
     fall-through sentence in `rules/__init__.py`;
   - AST entry counts for `opus_id_to_primary_logical_path` (COISS, COVIMS_0xxx),
     `opus_id` (VG_0xxx), `FILE_CODE_PRIORITY` (NHxxxx), the VG_28xx string-dicts, and
     the distinct OPUS categories per module;
   - `ast.unparse` hashes to compare VGIRIS_xxxx's and VG_20xx's tables.
4. Holdings evidence from `_volinfo/*.txt` for every dataset assertion, and from
   `_infoshelf-volumes/*/*.pickle` for file naming where `volumes/` is thin in this
   testing copy (VGIRIS, JNOJIR, COISS_0xxx, RPX, VG_28xx).
5. Mechanical gates run over docstrings only: line width, non-ASCII, sentence spacing,
   British spellings.

I did not re-run the rule-table checker; per the brief its result is taken as given.

---

## Defects in sentences the correction commit (d108bae) introduced

### A1. COISS_xxxx.py — the browse extras fall to the wrong description, and to the wrong table

> "The browse extras get no entry of their own and fall to the generic
> "Preview image collection"."

Wrong twice, and it is a differently-wrong replacement for the wrong claim the first
reviewer removed ("names ... the thumbnail, browse, full and TIFF extras").

Measured:

```
volumes/COISS_2xxx/COISS_2002/extras/browse
  module table  -> None
  class table   -> ('Browse image collection', 'BROWDIR')
```

The browse extras fall through to the **default** table's `.*/browse(/\w+)*` entry in
`rules/__init__.py`, which yields **"Browse image collection"**, not "Preview image
collection".

Worse, "Preview image collection" is not generic at all: it is this module's own entry at
`COISS_xxxx.py:71`, `(r'volumes/.*/data/.*/extras(/\w+)*(|/)', ...)`. That pattern
requires an `extras` directory *below* a `data` directory. No such layout exists —
`find /seti/opus/pdsdata/holdings/volumes -maxdepth 5 -path '*/data/*/extras'` returns
nothing; the real layout is `COISS_2002/extras/browse`, a sibling of `data`. So the
sentence names a string produced by a dead pattern and calls it the fall-through.

### A2. COISS_xxxx.py — "the three image volume sets" is two

> "In the three image volume sets a data file is a VICAR image whose basename begins with
> N for the narrow-angle camera or W for the wide-angle camera, followed by the ten-digit
> spacecraft clock. COISS_3xxx is not named that way, which is why
> ``COISS_xxxx.FILENAME_KEYLEN`` returns 0 for it."

COISS_0xxx is not named that way either. From `_infoshelf-volumes/COISS_0xxx/COISS_0001_info.pickle`:

```
data/nacfm/bias/121811.img
data/nacfm/bias/121811.lbl
```

Six-digit basenames under per-camera, per-test subdirectories. Only COISS_0011 (the
volume that carries the calibration report) uses `N1465676754_2.IMG` names. The module's
own patterns agree: `default_viewables`, `opus_id`, `associations_to_*` and
`cross_pds3_pds4_products` are all keyed `COISS_[12]xxx`.

The correction narrowed a too-broad claim by one volume set and stopped one short. And
the causal clause is misleading in the other direction: `FILENAME_KEYLEN` returns 11 for
COISS_0xxx as well, over basenames that have no eleven-character key.

### A3. COVIMS_0xxx.py — "an integer on every other class that sets it" is wrong twice over

Module docstring:

> "``FILENAME_KEYLEN``, which is a method here and a plain integer on every other class
> that sets it."

Class docstring:

> "``FILENAME_KEYLEN`` is an integer on every other class that sets it."

```
$ grep -n "def FILENAME_KEYLEN\|FILENAME_KEYLEN = " *.py
HSTxx_xxxx.py:259:    FILENAME_KEYLEN = 9
VGISS_xxxx.py:657:    FILENAME_KEYLEN = 8
COISS_xxxx.py:816:    def FILENAME_KEYLEN(self):
COVIMS_0xxx.py:432:    def FILENAME_KEYLEN(self):
NHxxxx_xxxx.py:570:    FILENAME_KEYLEN = 14
VG_0xxx.py:220:    FILENAME_KEYLEN = 8
GO_0xxx.py:807:    FILENAME_KEYLEN = 11
RPX_xxxx.py:271:    def FILENAME_KEYLEN(self):
```

Three classes define it as a method, not one: COISS_xxxx, COVIMS_0xxx and RPX_xxxx. Both
modules' own docstrings say so — `COISS_xxxx.py` "defines ``FILENAME_KEYLEN``, which
returns 0 for COISS_3xxx and 11 elsewhere" and `RPX_xxxx.py` "defines
``FILENAME_KEYLEN``, which returns the length of the HST group ID" — so the new sentence
contradicts two sibling files in the same commit.

### A4. VG_0xxx.py — the IBG count is wrong, and so is the table count

> "Four of this module's five tables spell the browse extension IBG; ``opus_type`` alone
> spells it IBQ, and the two cannot both be right."

Five tables spell IBG, not four: `description_and_icon_by_regex` (line 53),
`default_viewables` (67-78), `associations_to_volumes` (86-107),
`associations_to_previews` (111-122) and `opus_format` (158). And the module does not
have five tables; it has nine (`description_and_icon_by_regex`, `default_viewables`,
`associations_to_volumes`, `associations_to_previews`, `view_options`, `neighbors`,
`opus_type`, `opus_format`, `opus_id`). The observation that the two spellings cannot
both be right is sound; every number attached to it is not.

### A5. VG_0xxx.py — the spacecraft does not come from the volume

> "``opus_id`` -- builds the OPUS ID from the volume and the image number together. The
> image number comes from the file name; the spacecraft and the target come from the
> volume, which is why the table has seventeen entries keyed on volume-number ranges
> rather than one."

Seventeen is right. The rest is not. Nine of the seventeen entries discriminate on the
*image number* to pick the spacecraft:

```
(r'.*/VG_000[45]/.*/C(3[0-9]{6})\..*', 0, r'vg-iss-1-s-c\1'),
(r'.*/VG_000[45]/.*/C(4[0-9]{6})\..*', 0, r'vg-iss-2-s-c\1'),
```

and the same shape for `VG_000[6-8]` (three entries), `VG_0020` (two) and `VG_0033`
(two). The holdings say why: `_volinfo/VG_0xxx.txt` gives VG_0004/0005 both
`VG1-S-ISS-2-EDR-V1.0` and `VG2-S-ISS-2-EDR-V1.0`, and VG_0020 is "Voyager 1 and 2
Jupiter images". The volume fixes the target; it does not fix the spacecraft.

### A6. GO_0xxx.py — the version split is inverted

> "``versions`` -- ... whose file names differ: the earlier version puts the last four
> characters of an image name in a directory of their own."

It is the first seven characters that become the directory. On disk:

```
GO_0xxx/GO_0002/RAW_CAL/C0003061100R.IMG
GO_0xxx_v1/GO_0002/RAW_CAL/C000306/1100R.IMG
```

and the rule reads `(r'volumes/GO_0xxx.*/(GO_0.../.*/C\d{6})/?(\d{4}[A-Z]\..*)', ...)` —
group 1 is `.../C000306` and becomes the directory in v1; group 2, `1100R.IMG`, is what
remains as the file name. The sentence names the wrong half.

### A7. GO_0xxx.py — "one path component short" is not why all six fail

> "It carries entries for the calibration, Earth-Moon, optical-experiment, top-level
> target and reprocessed-image directories too, but those six patterns are one path
> component short of a real logical path, so they never fire and those directories fall
> through to the generic "Directory"."

The conclusion is right — I ran it:

```
volumes/GO_0xxx/GO_0002/VENUS    module=None  class=('Directory', 'FOLDER')
volumes/GO_0xxx/GO_0002/RAW_CAL  module=None  class=('Directory', 'FOLDER')
volumes/GO_0xxx/GO_0004/EMCONJ   module=None  class=('Directory', 'FOLDER')
volumes/GO_0xxx/GO_0002/GOPEX    module=None  class=('Directory', 'FOLDER')
volumes/GO_0xxx/GO_0006/REDO     module=None  class=('Directory', 'FOLDER')
volumes/GO_0xxx/GO_0018/REDO     module=None  class=('Directory', 'FOLDER')
```

but the stated reason does not hold for all six. `volumes/\w+/GO_00(0\d|1[0-6])\w+/REDO`
has exactly four components, the same as the real `volumes/GO_0xxx/GO_0006/REDO`; it
fails because of the mandatory `\w+` after the volume ID, which demands at least one more
character after "GO_0006". And `volumes/\w+/GO_00(1[789]|2\d)REDO` fails because it has no
slash before REDO — it is looking for a single directory literally named "GO_0018REDO".
A single mechanism is asserted for three different bugs.

### A8. COUVIS_8xxx.py — `#UPPER#` is not what rewrites DATA/EASYDATA, and it never fires

> "The earliest version put the data under ``DATA/EASYDATA/`` rather than ``data/``,
> which is what the table's ``#UPPER#`` directive rewrites"

The `DATA/EASYDATA` path is produced by a literal in the fourth and fifth entries:

```
r'volumes/COUVIS_8xxx_v1/COUVIS_8001/DATA/EASYDATA/\3_\4',
```

`#UPPER#` appears only in the sixth entry, whose in-code comment is
`# don't match "data" directory`. So the directive explicitly excludes the case the
sentence attributes to it.

It is worse than that: that sixth entry's pattern begins `volumes/COVIMS_8xxx` — VIMS,
not UVIS — while requiring the volume `COUVIS_8001`, a combination no path can have.
Measured:

```
COUVIS versions.all on 'volumes/COUVIS_8xxx/COUVIS_8001/document/foo.pdf'
   (nothing)
```

The only `#UPPER#` rule in the module is unreachable, so the sentence describes behavior
that does not exist at all.

### A9. COVIMS_8xxx.py — same claim, same error, demonstrable output

> "the earliest version put the data under ``EASYDATA/`` rather than ``data/``, which is
> what the table's ``#UPPER#`` directive rewrites."

Run on a real data path:

```
volumes/COVIMS_8xxx*/COVIMS_8001/data/VIMS_2005_144_OMICET_E_TAU_01KM.TAB
volumes/COVIMS_8xxx_v1/COVIMS_8001/EASYDATA/VIMS_2005_144_OMICET_E_TAU_01KM.TAB   <- rule 1, literal
volumes/COVIMS_8xxx*/COVIMS_8001/data/vims_2005_144_omicet_e_tau_01km.tab         <- rule 2, #LOWER#
volumes/COVIMS_8xxx_v1/COVIMS_8001/DATA/VIMS_2005_144_OMICET_E_TAU_01KM.TAB       <- rule 2, #UPPER#
```

`#UPPER#` turns `data` into `DATA`, not into `EASYDATA`, and `COVIMS_8xxx_v1/COVIMS_8001`
has no `DATA` directory (its one child is `EASYDATA`). The EASYDATA rewrite is the
literal in the first rule.

### A10. CORSS_8xxx.py — `#UPPER#` rewrites more than the directory component

> "The data file basenames are upper case in both versions; what the table's ``#UPPER#``
> directive rewrites is the directory component."

The first half is right (`RSS_2005_123_X43_E_CAL.TAB` in both). The second half describes
only one of the two paths the rule emits:

```
r'volumes/CORSS_8xxx_v1/\2/#UPPER#\3\4',
r'volumes/CORSS_8xxx_v1/\2/#UPPER#\3#MIXED#\4',
```

`\4` is the whole tail including the basename, so the first variant uppercases directory
*and* file name. That is not incidental: `CORSS_8xxx_v1/CORSS_8001/DOCUMENT/` holds both
`DOCINFO.TXT` and `archived_rss_ring_profiles.pdf`, and only the first variant finds
`DOCINFO.TXT`. The sentence explains away the alternative that does half the work.

### A11. JNOJIR_xxxx.py — the pairing sentence describes intent, not the table

> "The volumes entry is what pairs a raw file with its reduced counterpart, rewriting the
> volume's leading 1 to a 2 and EDR to RDR."

The table rewrites the volume digit and the product tag *independently*, and crossed:

```
(r'volumes/JNOJIR_xxxx/JNOJIR_[12](\d\d\d/DATA/JIR_\w+)_[ER]DR_(.*)\.(IMG|DAT|TAB)', 0,
        [r'volumes/JNOJIR_xxxx/JNOJIR_1\1_RDR_\2.\3',
         r'volumes/JNOJIR_xxxx/JNOJIR_2\1_EDR_\2.\3'
        ]),
```

Volume 1 with an RDR name, volume 2 with an EDR name. Run on a real file:

```
volumes/JNOJIR_xxxx/JNOJIR_1001/DATA/JIR_IMG_EDR_2016192T080312_V01.IMG ->
   volumes/JNOJIR_xxxx/JNOJIR_1001/DATA/JIR_IMG_RDR_2016192T080312_V01.IMG
   volumes/JNOJIR_xxxx/JNOJIR_2001/DATA/JIR_IMG_EDR_2016192T080312_V01.IMG
```

Neither exists, and neither can: the info shelves show JNOJIR_1001 holds 0 keys
containing "RDR" and JNOJIR_2001 holds 0 keys containing "EDR". The counterpart the
sentence promises would be `JNOJIR_2001/.../JIR_IMG_RDR_<same timestamp>.IMG`, and those
timestamps do line up (888 of JNOJIR_1001's 976 EDR timestamps recur in JNOJIR_2001) — so
the rewrite the sentence describes is exactly the fix the code is missing. The prose was
written from the intent, not from the table.

### A12. VGIRIS_xxxx.py — the example file is the wrong planet and the wrong volume set

> "``description_and_icon_by_regex`` -- names data files by spacecraft and planet, so that
> ``VG2_NEP.DAT`` reads as "Voyager 2 Neptune data", and carries four bare planet
> directory patterns. Those four do not fire on this volume set..."

VGIRIS has no Neptune. `_volinfo/VGIRIS_xxxx.txt` gives exactly two volumes, VGIRIS_0001
Jupiter and VGIRIS_0002 Saturn — the module's own opening paragraph says so three lines
above.

And it is not four dead patterns, it is all ten. VGIRIS holds no `VG*_*.DAT` files. From
the info shelves:

```
VGIRIS_0001: DATA/JUPITER_VG1/C1547XXX.TAB, C1547XXX_LSB.DAT, C1547XXX_MSB.DAT, ...
VGIRIS_0002: DATA/SATURN_VG1/C3429XXX.TAB, ...
```

`ast.unparse` hashes confirm this module's `description_and_icon_by_regex` is identical to
`VG_20xx.py`'s (md5 `95c8bf54...` for both). The whole table is VG_20xx's, and every
entry in it is dead for VGIRIS. The correction identified four dead patterns and then
illustrated the "live" half with a file from the other module.

### A13. pds3file/rules/__init__.py — the outright-assignment list names three of six

> "Most are added in front of the table here, so a lookup tries the dataset-specific
> patterns first and falls through to these; ``OPUS_ID``,
> ``OPUS_ID_TO_PRIMARY_LOGICAL_PATH`` and ``VIEWABLES`` are assigned outright wherever a
> module defines them, and for those there is no fall-through."

An AST walk over every class body in the 25 dataset modules, classifying each assignment
as `x + Base.X` or outright, returns three more tables from this file's own bullet list:

| table | assigned outright by |
|---|---|
| `VIEWABLE_TOOLTIPS` | COCIRS_xxxx, CORSS_8xxx, NHxxxx_xxxx (3 of 3 that set it) |
| `DATA_SET_ID` | COCIRS_xxxx, EBROCC_xxxx (2 of 2 that set it) |
| `OPUS_PRODUCTS` | EBROCC_xxxx, VG_28xx (2 outright, 11 added) |

`OPUS_PRODUCTS` is the sharpest of the three, because it is the one table where the same
name is added by some modules and replaced by others, which is precisely the distinction
the sentence exists to draw. The commit message says the corrected sentence names four
attributes (adding `PRODUCT_LBL_BASENAME_WO_EXT`); the pds3 file names three, and the
true count for tables defined in this file is six.

### A14. pds3file/rules/__init__.py — the SIBLINGS depths are off by one

> "the other three make every file at depth two, three or four under any category a
> sibling of every other"

The three rules are `(\w+-?\w+-?\w+)/[^/]+/[^/]+/[^/]+`, `.../[^/]+/[^/]+` and
`.../[^/]+`, i.e. three, two and one component *under* the category. Two, three and four
is the total component count including the category itself, which is not what "under any
category" says.

### A15. VG_28xx.py — FRAME_DICT is missing more than a brace

> "``FRAME_DICT`` -- 1 and 2 intended for B1950 and J2000. Its string literal is missing
> the closing brace, and no table reads it."

The literal is

```python
FRAME_DICT = """{
1: "B1950",
2: "J2000""".replace('\n','')
```

so it lacks the closing double quote on the value as well as the closing brace. "Missing
the closing brace" reads as one stray character; the string is two characters short and
`eval` would fail on the quote first. ("No table reads it" is correct — `grep FRAME_DICT`
finds only the definition and the docstring.)

### A16. HSTxx_xxxx.py — "a digit" is 0 or 1

> "maps a file specification beginning with a volume ID of the form HST, an instrument
> letter, a digit, an underscore and four digits, as in HSTI1_1556"

The pattern is `(r'HST([A-Z])[01]_\d{4}.*', 0, r'HST\1x_xxxx')`. The character after the
instrument letter is restricted to `[01]`, not any digit. The reasoning that follows about
the default rule is correct.

### A17. Class-docstring boilerplate — "the class body wires this module's rule tables" is false in ten modules

The rewritten boilerplate opens:

> "The class body wires this module's rule tables onto the class attributes ``Pds3File``
> reads."

An AST walk for module-level assignments to `pds3file.Pds3File.*` shows eleven modules
install `FILESPEC_TO_BUNDLESET` *below* the class, at module level: ASTROM_xxxx,
COSP_xxxx, EBROCC_xxxx, HSTxx_xxxx, JNOSP_xxxx, NHSP_xxxx, NHxxxx_xxxx, RPX_xxxx,
VGIRIS_xxxx, VG_20xx, VG_28xx.

The correction noticed this for ASTROM_xxxx and wrote it a bespoke sentence ("this
module's one table is added to ``Pds3File.FILESPEC_TO_BUNDLESET`` at module level, below
the class"). It did not propagate the observation to the other ten, all of which now carry
a generic sentence that the same commit proves wrong. For COSP_xxxx, JNOSP_xxxx and
NHSP_xxxx this is a third of their tables.

### A18. COUVIS_0xxx.py — only one of the two subscripts is guarded

> "the row is read from that table and the DATA_SET_ID column of its first row dictionary
> returned. The two subscripts in that expression are guarded by the existence check above
> them rather than by anything this method does."

The expression is `row.row_dicts[0]['DATA_SET_ID']`. The guard above it is
`if not row.exists: raise ValueError(...)`. `row.exists` speaks to whether the index row
is present; it says nothing about which columns the versions table carries, so
`['DATA_SET_ID']` is unguarded and a `KeyError` is reachable from a table with a renamed
column. The `Raises:` section, which the same commit edited, does not list it. The
sentence claims a guard for both subscripts when there is one for at most the first.

### A19. Class-docstring boilerplate — the registration key is orphaned in all 22 rewrites

Every rewritten class docstring now reads:

```
    assigned outright there is no fall-through. The module tail registers the class
    in ``Pds3File.SUBCLASSES`` under the key
    "COCIRS_xxxx". The module docstring describes the volume set and every table.
```

The line ending "under the key" is 46 columns wide against a 90-column budget, and the key
sits alone on the next line. This is in all 22 modules the commit touched with the
boilerplate. Cosmetic, but it is 22 instances of the same thing and it was introduced
here.

### A20. GO_0xxx.py — the description bullet now omits what the table mostly does

> "``description_and_icon_by_regex`` -- names the nested orbit and target directories and
> the images carrying an SL9 graphics overlay."

The rewrite dropped the parts of the table that actually fire on data files: `.*R\.IMG` →
"Raw image, VICAR", `.*S\.IMG` and `REDO/.*R\.IMG` → "Repaired raw image, VICAR", the
`C\d{6}` SC-clock directories, and two `metadata/GO_0xxx/GO_0016/...` index entries. What
survives in the bullet is two live patterns and a six-pattern dead zone. Replacing
"Shoemaker-Levy 9" with "SL9" was the right call (the tree nowhere expands it), but the
sentence lost its subject in the process.

### A21. JNOJIR_xxxx.py — "each orbit has two volumes" does not cover the pair it names

> "Each orbit has two volumes, a 1nnn holding the raw data and a 2nnn holding the reduced
> ... The series opens with JNOJIR_1000 for the 2013 Moon images"

JNOJIR_1000/2000 is the 2013 lunar flyby (`_volinfo`: "Juno JIRAM raw Moon images,
2013-10-09"), which is not an orbit; the same sentence pair names it. Related: the
module's summary line still reads "Rules for the JNOJIR_xxxx volume set: Juno JIRAM raw
data", which the new paragraph contradicts by establishing that half the volumes are
reduced.

---

## Other prose defects

1. **JNOJIR_xxxx.py**, description bullet — "distinguishes the raw and calibrated images
   from the raw and calibrated spectra, names the engineering data, and names the
   date-ordered data directories" accounts for six of the table's ten entries. The other
   four name the archive-description PDF and the JIRAM activity reports under
   `DOCUMENT/`, and are what makes the table's replacement strings interesting
   (`r'JIRAM activity report for orbit \1'`).

2. **JNOJIR_xxxx.py**, siblings bullet — "This is the only rule module that overrides the
   sibling rule". The class body does `SIBLINGS = siblings + pds3file.Pds3File.SIBLINGS`
   (line 222): it adds in front, it does not override. "Only rule module" is correct.

3. **RPX_xxxx.py**, `FILENAME_KEYLEN` docstring — "the raw image, the calibrated image,
   the engineering data, the header file and the three masks all share it" lists seven of
   the eight files that share the nine-character group ID. `BROWSE/U2IQ0101T.GIF` shares
   it too, and it is the eighth per-observation directory (BROWSE, CALIMAGE, CALMASK,
   ENGDATA, ENGMASK, HEADER, RAWIMAGE, RAWMASK, 70 files each in RPX_0001).

4. **RPX_xxxx.py**, description bullet — the table's `.*/RPX_00.*/BROWSE` → "Browse GIFs"
   and `.*/RPX_00.*/[0-9]{6}XX` → "Data files by year and month" entries go unmentioned.

5. **COCIRS_xxxx.py**, `data_set_id` bullet — "`COCIRS_xxxx.py` and `EBROCC_xxxx.py` are
   the only two rule modules that define this table". `COUVIS_0xxx.py` also overrides
   `DATA_SET_ID`, as a method. The sentence is true only if "table" is read strictly as
   "translator", and `rules/__init__.py` lists `DATA_SET_ID` under the heading "The
   tables", so the strict reading is not the one a reader arrives with.

6. **COCIRS_xxxx.py, CORSS_8xxx.py, NHxxxx_xxxx.py** — the boilerplate promises "The
   module docstring describes the volume set and every table", but `VIEWABLE_TOOLTIPS`,
   a class-body dict in all three, is described in only one of the three module
   docstrings (CORSS's, and there only obliquely as "The class's own tooltips").

7. **VG_28xx.py**, description bullet — "names the directories of each volume and every
   product form" is a universal claim over a 66-entry table with eleven kind codes and
   four experiments; nothing in the module supports "every", and `ICON`'s missing "P"
   entry (which the same docstring notes) is a counter-signal.

8. **HSTxx_xxxx.py**, class docstring — "sets ``FILENAME_KEYLEN`` to 9, so that the
   several previews of one observation group together". The volumes also hold `.TIF`,
   `.ASC` and `.LBL` files sharing the same nine-character rootname, per the module's own
   description table; "previews" understates the group.

9. **COVIMS_0xxx.py**, description bullet — "the browse image collections and the small
   and full-size browse images" is served by three live entries and one dead one
   (`volumes/.*/data/.*/extras/\w+`, the same wrong shape as COISS's, since
   `COVIMS_0006/extras` is a sibling of `data`). The prose reads as though all four fire.

10. **JNOJNC_xxxx.py** — "its volumes are numbered sequentially, each covering a range of
    orbits". `_volinfo` gives JNOJNC_0001 as "cruise and orbit 0" — one orbit, not a
    range. The correction is a clear improvement over "numbered by orbit", but it
    overshoots at the first volume.

---

## Code defects

1. **COUVIS_8xxx.py:~270** — the last `versions` entry is
   `(r'volumes/COVIMS_8xxx(|_v[0-9\.]+)/COUVIS_8001/(\w+[^aA])(|/.*)', ...)`. `COVIMS`
   should be `COUVIS`. No path can have a COVIMS volume set and a COUVIS volume, so the
   rule is unreachable and COUVIS_8xxx has no version mapping at all for `document/`,
   `browse/` or any non-`data` directory. Verified: `versions.all()` on
   `volumes/COUVIS_8xxx/COUVIS_8001/document/foo.pdf` returns `[]`.

2. **JNOJIR_xxxx.py:77-80** — `associations_to_volumes` crosses the volume digit with the
   product tag: it emits `JNOJIR_1nnn/..._RDR_...` and `JNOJIR_2nnn/..._EDR_...`. Both are
   always nonexistent (JNOJIR_1nnn holds only EDR, JNOJIR_2nnn only RDR). The intended
   pair, `JNOJIR_2nnn/..._RDR_<same timestamp>`, does exist for 888 of JNOJIR_1001's 976
   EDR products. Fix: swap `_RDR_` and `_EDR_` in the two replacements.

3. **JNOJNC_xxxx.py:96** — `r'volumes/(JNOJNC_0xxx/JNOJNC _0\d\d\d)/...'` contains a space
   in the volume ID. The "associate global maps with browse products" rule is dead;
   `associations_to_volumes.all()` on a `DATA/GLOBAL_MAPS/JNCR_*.IMG` path returns `[]`.

4. **COISS_xxxx.py:71-72** — `volumes/.*/data/.*/extras...` describes a layout no COISS
   volume has (`extras` is a sibling of `data`). Both entries, "Preview image collection"
   and "Preview image", are unreachable.

5. **GO_0xxx.py** description table — six entries never fire (measured, see A7):
   `volumes/\w+/(MOON|EARTH|VENUS|IDA|GASPRA|SL9)`, `.../RAW_CAL`, `.../EMCONJ`,
   `.../GOPEX`, `volumes/\w+/GO_00(0\d|1[0-6])\w+/REDO` and
   `volumes/\w+/GO_00(1[789]|2\d)REDO`. The first four need one more `\w+/` component; the
   fifth needs its trailing `\w+` dropped; the sixth needs a `/` before `REDO`.

6. **VG_20xx.py:56** — `filespec_to_bundleset` replaces with `VG__20xx` (two
   underscores). No such directory. The docstring reports the bug faithfully, but it is
   still a bug, and the sibling `VG_28xx.py` gets it right (`VG_28xx`).

7. **VGIRIS_xxxx.py:39-51** — `description_and_icon_by_regex` is an unmodified copy of
   VG_20xx's (identical `ast.unparse` output) and no entry in it can match a VGIRIS path:
   the directories are `DATA/JUPITER_VG1` and `DATA/SATURN_VG1`, and the data basenames
   are `C####XXX.TAB` / `C####XXX_{LSB,MSB}.DAT`. The whole table is dead weight.

8. **rules/__init__.py:164-165** — the entry
   `(r'volumes/[^/]+', 0, (GENERIC_VOLSET_DESC, 'VOLDIR'))` appears twice in a row.

9. **VG_28xx.py:188-190** — `FRAME_DICT`'s string literal is malformed (unterminated value
   string, no closing brace) and unused. Either finish it or delete it.

10. Typos in user-facing description strings (these reach the web pages):
    `NHxxxx_xxxx.py` "Raw imag, FITS" and "Calibrated imag, FITS";
    `COCIRS_xxxx.py:99` "Interopolated ousekeeping data";
    `rules/__init__.py:139` "Checksum index of indices and metadatas" and
    `:335` "GIF vewable image";
    `VG_28xx.py` "Ring intercept geomemtry" and "Raw data with anomalies identifed";
    `RPX_xxxx.py` proposal descriptions padded with trailing spaces
    ("Data from proposal 5219, PI Trauger  ").

---

## Claims I checked and found correct

Corrections that survive:

- **COCIRS_xxxx.py**: `COCIRS_[0156x]xxx` matches the translator; the description table's
  longest run is exactly 24 GEODATA entries (599, 501-504, 699, 601-618 — Jupiter and the
  Galileans through Saturn out to Pan); `opus_type` carries exactly 21 "Extra Browse
  Diagram" entries, 18 NAIF-keyed plus rings, Saturn and default, with no Jupiter or
  Galilean entry; `viewables` has 21 keys and every one but "default" is keyed
  `COCIRS_[56]`, so a COCIRS_0xxx/1xxx product gets one; `s_rings_viewables` appears in no
  other module; COCIRS is the only module that builds its viewable dict in a loop;
  volinfo wording ("raw and calibrated ... map cubes, 2000-2009 / 2010-2017", "simplified
  formats, from 2010 calibration") is quoted accurately; the `data_set_id` rationale
  (TSDR vs CUBE, early COCIRS_0xxx Jupiter vs later Saturn) matches the table.
- **COISS_xxxx.py**: 52 reverse-OPUS-ID entries, of which three cover several three-digit
  prefixes (`14[123]`, `13[789]`, `13[0-4]`) and one keys on two digits (`12`);
  `COISS_[0123x]xxx`; `cross_pds3_pds4_products` is the only definition of that table and
  the two `global_reproj_img_index.*` files do come from the fring bundle alone.
- **COVIMS_0xxx.py**: 49 reverse entries with the same three-wide-plus-one-two-digit
  shape; `BASENAME_REGEX` is the only `re.compile` at top level in any rule module (grep
  returns one hit across 26 files); cube basenames do open with "v" and the
  sub-observation suffix is three digits.
- **CORSS_8xxx.py**: six named viewables and the tooltip paraphrase matches
  `VIEWABLE_TOOLTIPS` word for word in substance; COCIRS with 21 is the only module
  offering more (all others: NHxxxx 3, COUVIS_8xxx 2, COVIMS_8xxx 2, rest 1); `EASYDATA/`
  vs `data/`, two digits after "Rev" (`Rev07E`) against three now (`Rev007/Rev007E`), and
  the different nesting all check out on disk; the data file basenames really are upper
  case in both versions.
- **COUVIS_8xxx.py**: the first three entries do pair observations with differing dates
  (2005_139/2009_062, 2007_038/2008_026, 2010_148/149); the underscore after "TAU" is real
  (`..._TAU_01KM.TAB` in v1 vs `..._TAU01KM.TAB` now); `DATA/EASYDATA/` for COUVIS versus
  plain `EASYDATA/` for COVIMS is a real and correctly-drawn distinction.
- **NHxxxx_xxxx.py**: `FILE_CODE_PRIORITY` holds exactly 36 codes, 12 contiguous LORRI
  (630-63B) and 24 MVIC between 530 and 54A with a 53C-53E gap; the LORRI and MVIC mode
  vocabularies and the CDH-unit annotation are exactly what the comments say; the
  instrument and payload PDFs are under each volume's own `document/`, not the documents
  tree; `filespec_to_bundleset` and the default-rule rationale check out
  (NHJULO_1001 → NHJULO_1xxx); NHJULO_1001 is the Jupiter flyby with LORRI and NHKEMV_1001
  the Arrokoth flyby with MVIC, per `_volinfo`.
- **VG_28xx.py**: exactly 18 top-level string-dicts; `ICON` covers 10 of `KIND`'s 11 codes
  and omits "P"; `FRAME_DICT` is read by nothing; `US23_DICT` is keyed on the digit after
  "US" (`.*/US(2|3)...` → `US23_DICT + r'[\1]'`) and both entries are Saturn UVS;
  PU1P01AI.TAB does decompose P / U1 / P / 01 / A / I against
  `.*/[PU](U1|U2)P..([654ABNGDLE])(I|E)\.(TAB|DAT)` and the translator renders it "Uranus
  sigma Sgr ingress profile for ring alpha"; four OPUS categories, and no other module
  spans more than two (NHxxxx); the class body installs neither `SORT_KEY` nor
  `SPLIT_RULES`; it is the longest module (1,115 lines against GO_0xxx's 914); the four
  volumes' data set IDs match `_volinfo` exactly.
- **rules/__init__.py**: eleven modules override `FILESPEC_TO_BUNDLESET`; exactly three
  volume sets need an override and lack one, and the default's answers are the ones
  named (JNOJIR_1000 → JNOJIR_1xxx, JNOSRU_0001 → JNOSRU_0xxx, RES_0001 → RES_0xxx, none
  of which is a directory — RES sits under `RES_xxxx_prelim`); `__all__` has 24 entries
  and `JNOSRU_xxxx` is the one missing, while `pds3file/__init__.py` names all 25;
  `SORT_KEY` does order previews largest first (`_full` → `_1full`, `_thumb` → `_4thumb`),
  which contradicts the code comment above it and is a genuine catch;
  `INFO_FILE_BASENAMES` patterns are anchored (`'^' + pattern + '$'` in
  `translator/__init__.py:438-441`), so a bare `INFO.txt` and a `MYREADME.txt` both fail.
- **GO_0xxx.py / NHxxxx_xxxx.py** `opus_prioritizer` `Raises:` sections: the `IndexError`
  is real (`header[0]` on the empty-string key, which `_opus.py` can produce — it logs
  "Unknown opus_type" and still uses `''` as a key); the `TypeError` is real (PdsFile
  defines no `__lt__`, `__gt__` or `total_ordering`, so a tie on the leading tuple
  elements falls through to comparing lists of PdsFile); NHxxxx's `KeyError` on
  `FILE_CODE_PRIORITY` is real.
- **JNOSRU_xxxx.py**: the default table does already name a `.FIT` file
  (`.*\.fits{0,1}` with `re.I` → "FITS data file"), so what this module adds is the
  "Image file, FITS" wording and the IMAGE icon; `JNOSRU_....` is six letters, underscore,
  four characters.
- **RPX_xxxx.py**: raw image, calibrated image, engineering data and header, with a mask
  for the first three and no header mask — the eight per-observation directories are
  BROWSE, CALIMAGE, CALMASK, ENGDATA, ENGMASK, HEADER, RAWIMAGE, RAWMASK, exactly 70 files
  each; the nine-character group ID (`U2IQ0101T`) is right; the volume roster and
  telescope list match `_volinfo`.
- **EBROCC_xxxx.py**: six data set IDs, one per observatory, named correctly; one
  directory per observatory under DATA, GEOMETRY and BROWSE; the empty viewable for a
  label; `filespec_to_bundleset` really is keyed on the literal `EBROCC_0001`.
- **COSP/JNOSP/NHSP**: the same three tables in each; the curated document directories and
  their SPICE-Toolkit and kernel-selection links are in `_volinfo`; the data set IDs
  match; NHSP's is the only one of the three with a trailing wildcard; the
  `aareadme.txt`-over-`voldesc.cat` preference is real, because
  `TranslatorByRegex.first(childnames)` iterates rules outermost and the module's rule is
  prepended.
- **COUVIS_0xxx.py**: "Cassini UVIS (Ultraviolet Spectrometer)" is quoted from
  `_volinfo/COUVIS_0xxx.txt` verbatim and is attributed to the holdings, so the
  non-standard expansion is the source's, not the prose's.
- **VG_20xx.py**: the four data set IDs split VG1/VG2-J and VG1/VG2-S against VG2-U and
  VG2-N exactly as described; VG_2001's top-level directories really are JUPITER, SATURN,
  URANUS, NEPTUNE with `VG1_JUP.DAT` etc. inside, so the "split by spacecraft at the file
  level, by planet at the directory level" sentence is right and the `VG__20xx` bug report
  is right.
- **VGISS_xxxx.py**: `VGISS_[5678x]xxx`; the four volset descriptions in `_volinfo` are
  "Voyager Jupiter / Saturn / Voyager 2 Uranus / Voyager 2 Neptune image collection, raw
  and calibrated", exactly as paraphrased; `FILENAME_KEYLEN = 8`.
- **Mechanical gates**: no docstring line exceeds 90 columns in any of the 26 files; no
  non-ASCII character anywhere in the slice (no smart quotes, em-dashes or arrows); no
  double space after a sentence period inside a docstring; no British spellings; no prose
  anchored to change history or to a date.

---

## Could not verify either way

1. **VG_0xxx.py, IBG versus IBQ.** The docstring is right that the two cannot both be
   correct, but this holdings copy has no `volumes/VG_0xxx` directory and no
   `metadata/VG_0xxx`, only `_volinfo/VG_0xxx.txt` and an info shelf directory name. I
   could not establish which spelling the archive uses, so I cannot say whether
   `opus_type` or the other five tables carry the bug.
2. **VG_28xx.py, "A basename such as PU1P01AI.TAB".** The testing copy's VG_2801 holds
   PU1P01 files only with the ring codes D, E, L and X (48 `.TAB` files); no "A" variant
   is present. Absence in a limited copy is not evidence, and the pattern and translator
   both accept the example, so I treat this as unresolved rather than wrong.
3. **HSTxx_xxxx.py, `FILENAME_KEYLEN = 9`.** The two HST volumes present
   (HSTI1_1556, HSTI1_1559, HSTU0_5167) were not opened; I checked the volume-ID shape but
   not that observation rootnames are nine characters.
4. **COVIMS_0xxx.py, "ISIS2 spectral image cube".** `_volinfo/COVIMS_0xxx.txt` says
   "Cassini VIMS visual/near-IR cube collection" and the data set ID is
   `CO-E/V/J/S-VIMS-2-QUBE-V1.0`; neither states ISIS2. The module's own description
   string says "Spectral image cube (ISIS2)", so the docstring is at least quoting the
   code, but the holdings do not confirm the format name.
5. **NHxxxx_xxxx.py, the LORRI/MVIC mode vocabulary.** I confirmed the docstring matches
   the in-code comments exactly. Whether the comments themselves are right about the
   instrument modes is outside anything in the repository or the holdings.
6. **JNOJIR_xxxx.py volume count.** `_volinfo` lists 66 volumes on each side; the info
   shelf directory holds 138 files (69 per side). The docstring makes no count claim, so
   this is only a note that the two sources disagree.
