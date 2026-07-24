#!/bin/bash

set -e

if [[ $# -ne 3 ]]; then
    echo "This script is used to copy existing documentation files from one holdings"
    echo "directory to another."
    echo
    echo "Usage: copy_documentation.sh <src_holdings_dir> <dest_holdings_dir> <volset>"
    exit -1
fi

SRC_HOLDINGS="$(realpath $1)"
DEST_HOLDINGS="$(realpath $2)"
VOLSET=$3

if [[ ! -d "$SRC_HOLDINGS/documents/$VOLSET" ]]; then
    echo "Directory does not exist: '$SRC_HOLDINGS/documents/$VOLSET'"
    exit -1
fi

if [[ ! -d "$DEST_HOLDINGS/documents" ]]; then
    echo "Directory does not exist: '$DEST_HOLDINGS/documents'"
    exit -1
fi

cp -r "$SRC_HOLDINGS/documents/$VOLSET" "$DEST_HOLDINGS/documents/$VOLSET"
