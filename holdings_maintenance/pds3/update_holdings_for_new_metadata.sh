#!/bin/bash

set -e

if [[ $# -ne 2 ]]; then
    echo "This script is used to update all of the archives, checksums, shelf,"
    echo "and link files for a new set of metadata. All of the existing files"
    echo "are deleted and the new versions are created from scratch."
    echo
    echo "Usage: update_holdings_for_new_metadata.sh <holdings_dir> <volset>"
    exit -1
fi

HOLDINGS="$(realpath $1)"
VOLSET=$2

if [[ ! -d "$HOLDINGS" ]]; then
    echo "Directory does not exist: '$HOLDINGS'"
    exit -1
fi

if [[ ! -d "$HOLDINGS/metadata/$VOLSET" ]]; then
    echo "Directory does not exist: '$HOLDINGS/metadata/$VOLSET'"
    exit -1
fi

rm -rf "$HOLDINGS/archives-metadata/$VOLSET"
rm -f "$HOLDINGS"/checksums-archives-metadata/${VOLSET}_*
rm -rf "$HOLDINGS/checksums-metadata/$VOLSET"
rm -rf "$HOLDINGS/_indexshelf-metadata/$VOLSET"
rm -rf "$HOLDINGS/_infoshelf-archives-metadata/$VOLSET"
rm -rf "$HOLDINGS/_infoshelf-metadata/$VOLSET"
rm -rf "$HOLDINGS/_linkshelf-metadata/$VOLSET"

python pdsarchives.py --initialize "$HOLDINGS/metadata/$VOLSET"
python pdschecksums.py --initialize "$HOLDINGS/archives-metadata/$VOLSET"
python pdschecksums.py --initialize "$HOLDINGS/metadata/$VOLSET"
python pdsinfoshelf.py --initialize "$HOLDINGS/metadata/$VOLSET"
python pdsindexshelf.py --initialize "$HOLDINGS/metadata/$VOLSET"
python pdslinkshelf.py --initialize "$HOLDINGS/metadata/$VOLSET"

echo "ALL COMPLETED WITH NO ERRORS"
