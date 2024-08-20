#!/bin/bash

set -e

if [[ $# -ne 1 ]]; then
    echo "This script creates empty versions of all of the standard directories"
    echo "that appear under /holdings. It is used to initialize a brand new"
    echo "holdings directory from scratch."
    echo
    echo "Usage: setup_new_holdings.sh <holdings_dir>"
    exit -1
fi

HOLDINGS="$(realpath $1)"

if [[ ! -d "$HOLDINGS" ]]; then
    echo "Directory does not exist: '$HOLDINGS'"
    exit -1
fi

echo "Setting up holdings directory: $HOLDINGS"

mkdir -p "$HOLDINGS/archives-calibrated"
mkdir -p "$HOLDINGS/archives-diagrams"
mkdir -p "$HOLDINGS/archives-metadata"
mkdir -p "$HOLDINGS/archives-previews"
mkdir -p "$HOLDINGS/archives-volumes"
mkdir -p "$HOLDINGS/calibrated"
mkdir -p "$HOLDINGS/checksums-archives-calibrated"
mkdir -p "$HOLDINGS/checksums-archives-diagrams"
mkdir -p "$HOLDINGS/checksums-archives-metadata"
mkdir -p "$HOLDINGS/checksums-archives-previews"
mkdir -p "$HOLDINGS/checksums-archives-volumes"
mkdir -p "$HOLDINGS/checksums-calibrated"
mkdir -p "$HOLDINGS/checksums-diagrams"
mkdir -p "$HOLDINGS/checksums-metadata"
mkdir -p "$HOLDINGS/checksums-previews"
mkdir -p "$HOLDINGS/checksums-volumes"
mkdir -p "$HOLDINGS/diagrams"
mkdir -p "$HOLDINGS/documents"
mkdir -p "$HOLDINGS/_indexshelf-metadata"
mkdir -p "$HOLDINGS/_infoshelf-archives-calibrated"
mkdir -p "$HOLDINGS/_infoshelf-archives-diagrams"
mkdir -p "$HOLDINGS/_infoshelf-archives-metadata"
mkdir -p "$HOLDINGS/_infoshelf-archives-previews"
mkdir -p "$HOLDINGS/_infoshelf-archives-volumes"
mkdir -p "$HOLDINGS/_infoshelf-calibrated"
mkdir -p "$HOLDINGS/_infoshelf-diagrams"
mkdir -p "$HOLDINGS/_infoshelf-metadata"
mkdir -p "$HOLDINGS/_infoshelf-previews"
mkdir -p "$HOLDINGS/_infoshelf-volumes"
mkdir -p "$HOLDINGS/_linkshelf-calibrated"
mkdir -p "$HOLDINGS/_linkshelf-metadata"
mkdir -p "$HOLDINGS/_linkshelf-volumes"
mkdir -p "$HOLDINGS/metadata"
mkdir -p "$HOLDINGS/previews"
mkdir -p "$HOLDINGS/_volinfo"
mkdir -p "$HOLDINGS/volumes"
