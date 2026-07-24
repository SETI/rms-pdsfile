#!/bin/bash

set -e

if [[ $# -ne 2 ]]; then
    echo "This script is used to create empty volumes that mirror the structure"
    echo "of a metadata directory so that PdsFile will acknowledge that volumes'"
    echo "existence."
    echo
    echo "Usage: create_fake_volumes_for_metadata.sh <holdings_dir> <volset>"
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

for VOLPATH in $(ls "$HOLDINGS/metadata/$VOLSET"); do
    VOL=$(basename $VOLPATH)
    mkdir -p "$HOLDINGS/volumes/$VOLSET/$VOL"
done
