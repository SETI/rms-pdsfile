#!/bin/bash

set -e

if [[ $# -ne 4 ]]; then
    echo "This script is used to copy existing shelf files from one holdings"
    echo "directory to another."
    echo
    echo "Usage: copy_shelves.sh <src_holdings_dir> <dest_holdings_dir> <volset> <shelf_type>"
    exit -1
fi

SRC_HOLDINGS="$(realpath $1)"
DEST_HOLDINGS="$(realpath $2)"
VOLSET=$3
TYPE=$4

if [[ ! -d "$SRC_HOLDINGS/$TYPE/$VOLSET" ]]; then
    echo "Directory does not exist: '$SRC_HOLDINGS/$TYPE/$VOLSET'"
    exit -1
fi

if [[ ! -d "$DEST_HOLDINGS/$TYPE" ]]; then
    echo "Directory does not exist: '$DEST_HOLDINGS/$TYPE/$VOLSET'"
    exit -1
fi

if [[ -d "$SRC_HOLDINGS/_infoshelf-$TYPE/$VOLSET" ]]; then
    echo "Copying to: $DEST_HOLDINGS/_infoshelf-$TYPE/$VOLSET"
    rm -rf "$DEST_HOLDINGS/_infoshelf-$TYPE/$VOLSET"
    cp -r "$SRC_HOLDINGS/_infoshelf-$TYPE/$VOLSET" "$DEST_HOLDINGS/_infoshelf-$TYPE/$VOLSET"
fi

if [[ -d "$SRC_HOLDINGS/_indexshelf-$TYPE/$VOLSET" ]]; then
    echo "Copying to: $DEST_HOLDINGS/_indexshelf-$TYPE/$VOLSET"
    rm -rf "$DEST_HOLDINGS/_indexshelf-$TYPE/$VOLSET"
    cp -r "$SRC_HOLDINGS/_indexshelf-$TYPE/$VOLSET" "$DEST_HOLDINGS/_indexshelf-$TYPE/$VOLSET"
fi

if [[ -d "$SRC_HOLDINGS/_linkshelf-$TYPE/$VOLSET" ]]; then
    echo "Copying to: $DEST_HOLDINGS/_linkshelf-$TYPE/$VOLSET"
    rm -rf "$DEST_HOLDINGS/_linkshelf-$TYPE/$VOLSET"
    cp -r "$SRC_HOLDINGS/_linkshelf-$TYPE/$VOLSET" "$DEST_HOLDINGS/_linkshelf-$TYPE/$VOLSET"
fi
