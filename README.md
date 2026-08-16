# rms-pdsfile

[![GitHub release; latest by date](https://img.shields.io/github/v/release/SETI/rms-pdsfile)](https://github.com/SETI/rms-pdsfile/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/SETI/rms-pdsfile)](https://github.com/SETI/rms-pdsfile/releases)
[![Test Status](https://img.shields.io/github/actions/workflow/status/SETI/rms-pdsfile/run-tests.yml?branch=main)](https://github.com/SETI/rms-pdsfile/actions)
[![Documentation Status](https://readthedocs.org/projects/rms-pdsfile/badge/?version=latest)](https://rms-pdsfile.readthedocs.io/en/latest/?badge=latest)
[![Code coverage](https://img.shields.io/codecov/c/github/SETI/rms-pdsfile/main?logo=codecov)](https://codecov.io/gh/SETI/rms-pdsfile)
<br />
[![PyPI - Version](https://img.shields.io/pypi/v/rms-pdsfile)](https://pypi.org/project/rms-pdsfile)
[![PyPI - Format](https://img.shields.io/pypi/format/rms-pdsfile)](https://pypi.org/project/rms-pdsfile)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/rms-pdsfile)](https://pypi.org/project/rms-pdsfile)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rms-pdsfile)](https://pypi.org/project/rms-pdsfile)
<br />
[![GitHub commits since latest release](https://img.shields.io/github/commits-since/SETI/rms-pdsfile/latest)](https://github.com/SETI/rms-pdsfile/commits/main/)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/SETI/rms-pdsfile)](https://github.com/SETI/rms-pdsfile/commits/main/)
[![GitHub last commit](https://img.shields.io/github/last-commit/SETI/rms-pdsfile)](https://github.com/SETI/rms-pdsfile/commits/main/)
<br />
[![Number of GitHub open issues](https://img.shields.io/github/issues-raw/SETI/rms-pdsfile)](https://github.com/SETI/rms-pdsfile/issues)
[![Number of GitHub closed issues](https://img.shields.io/github/issues-closed-raw/SETI/rms-pdsfile)](https://github.com/SETI/rms-pdsfile/issues)
[![Number of GitHub open pull requests](https://img.shields.io/github/issues-pr-raw/SETI/rms-pdsfile)](https://github.com/SETI/rms-pdsfile/pulls)
[![Number of GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed-raw/SETI/rms-pdsfile)](https://github.com/SETI/rms-pdsfile/pulls)
<br />
[![GitHub License](https://img.shields.io/github/license/SETI/rms-pdsfile)](https://github.com/SETI/rms-pdsfile/blob/main/LICENSE)
[![Number of GitHub stars](https://img.shields.io/github/stars/SETI/rms-pdsfile)](https://github.com/SETI/rms-pdsfile/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/SETI/rms-pdsfile)](https://github.com/SETI/rms-pdsfile/forks)

<!-- start-after-point -->

## Introduction

`rms-pdsfile` is the interface to a **holdings tree**: the directory tree in
which the PDS Ring-Moon Systems Node keeps the planetary data it publishes —
images, spectra and other observations of the outer planets from missions such
as Cassini, Voyager and New Horizons — together with everything derived from
that data: preview images, diagrams, index tables, checksum files, downloadable
archives, and the precomputed caches that describe them.

Given any file in such a tree, the package answers the questions a data service
asks over and over: what is this file, what is its size,
checksum and modification date, where are its label, its previews and its
metadata, and which other files belong to the same observation — all without
opening the file, and mostly without touching the file system at all, by
reading the tree's precomputed caches instead. It also ships the command-line
programs the Node uses to build and validate those caches.

It is written for the Node's own services — it is the layer beneath the
[OPUS](https://opus.pds-rings.seti.org) search engine and the Viewmaster
browser at [pds-rings.seti.org](https://pds-rings.seti.org) — and for anyone
who maintains or mirrors a Ring-Moon Systems holdings tree.

`rms-pdsfile` is a product of the
[PDS Ring-Moon Systems Node](https://pds-rings.seti.org).

## Features

- **One object per file.** A `PdsFile` represents one file or directory in a
  holdings tree and is the entry point to everything else: parent, children,
  associated files, metadata, previews.
- **Both PDS standards.** `Pds3File` reads a PDS3 tree of volumes;
  `Pds4File` reads a PDS4 tree of bundles. The two share one interface.
- **Metadata without I/O.** Size, child count, modification date and MD5
  checksum come from the tree's shelf files, so answering does not require
  reading — or even statting — the data file itself.
- **Associations.** From any product, find the files that belong with it in
  another category of the tree: its label, its previews, its diagrams, its
  calibrated version, its index-table rows.
- **OPUS support.** Map any product to its OPUS ID and back, and enumerate
  every file OPUS should offer for an observation.
- **Index tables as directories.** A metadata index table behaves as a
  directory whose children are its rows, so a single observation's row is
  addressable like a file.
- **Preview sets.** The preview images of a product are collected into a view
  set that picks the best size on request.
- **Maintenance tools.** Eleven console scripts build, validate and repair the
  derived parts of a tree: `pdsarchives`, `pdschecksums`, `pdsdependency`,
  `pdsindexshelf`, `pdsinfoshelf` and `pdslinkshelf` for PDS3, and
  `pds4archives`, `pds4checksums`, `pds4indexshelf`, `pds4infoshelf` and
  `pds4linkshelf` for PDS4. Four more programs run as modules with
  `python -m`: `crlf`, `re_validate`, `shelf_consistency_check` and
  `show_opus_products`. The
  [user guide](https://rms-pdsfile.readthedocs.io/en/latest) has a chapter on
  each.

## Installation

`rms-pdsfile` requires Python 3.11 or later.

```sh
pip install rms-pdsfile
```

To use the command-line programs without adding the package to any project's
dependency list, install it as an application instead:

```sh
pipx install rms-pdsfile
```

The package is only as useful as the holdings tree it reads: point it at a
locally accessible tree, complete or partial, such as a mirror of the Node's
holdings. Two environment variables conventionally name the tree roots, and
the examples below use them:

```sh
export PDS3_HOLDINGS_DIR=/path/to/pdsdata/holdings
export PDS4_HOLDINGS_DIR=/path/to/pdsdata/pds4-holdings
```

The directory basenames `holdings` and `pds4-holdings` are required — the
package splits every absolute path at that component. The
[installation chapter](https://rms-pdsfile.readthedocs.io/en/latest) of the
user guide covers the tree layout and which programs read which variable.

## Quick Start

Load a PDS3 holdings tree and ask about one Cassini image (replace the root
with your own tree's; every path below it is real):

```python
import pdsfile

pdsfile.Pds3File.preload('/path/to/pdsdata/holdings')

f = pdsfile.Pds3File.from_logical_path(
    'volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960653_1.IMG')
print(f.description)      # Narrow-angle image, VICAR
print(f.opus_id)          # co-iss-n1460960653
print(f.label_basename)   # N1460960653_1.LBL
print(f.viewset)          # the four preview images of this observation
```

From the command line, validate one volume's cached file information against
the volume itself:

```sh
pdsinfoshelf --validate $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
```

## Documentation

The user guide (the fifteen command-line programs), the developer guide and
the API reference are at
[rms-pdsfile.readthedocs.io](https://rms-pdsfile.readthedocs.io/en/latest).
To build them locally, install the `dev` extra and run `make html` in `docs/`.

## Contributing

See the
[contribution guide](https://github.com/SETI/rms-pdsfile/blob/main/CONTRIBUTING.md).

## License

[Apache-2.0](https://github.com/SETI/rms-pdsfile/blob/main/LICENSE).
