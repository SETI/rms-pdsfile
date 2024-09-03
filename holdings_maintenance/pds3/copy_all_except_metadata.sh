#!/bin/bash

if [[ $# -ne 3 ]]; then
    echo "This script is used to copy existing shelf files for all categories except"
    echo "metadata, plus the contents of the documents directory, from one holdings"
    echo "directory to another."
    echo
    echo "Usage: copy_all_except_metadata.sh <src_holdings_dir> <dest_holdings_dir> <volset>"
    exit -1
fi

./copy_documents.sh "$1" "$2" "$3"
./copy_shelves.sh "$1" "$2" "$3" volumes
./copy_shelves.sh "$1" "$2" "$3" calibrated
./copy_shelves.sh "$1" "$2" "$3" previews
./copy_shelves.sh "$1" "$2" "$3" diagrams
