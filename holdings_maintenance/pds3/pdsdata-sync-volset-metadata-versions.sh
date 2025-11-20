#! /bin/zsh
################################################################################
# Synchronize one volume set from one pdsdata drive to another.
#
# Usage:
#   pdsdata-sync-volset-metadata-versions <old> <new> <volset> [--dry-run]
#
# Syncs the metadata for the specified volume set <volset> from the drive
# /Volumes/pdsdata-<old> to the drive /Volumes/pdsdata-<new>, including old
# versions. Append "--dry-run" for a test dry run. This only syncs the metadata
# and associated directories and should be used when syncing versioned metadata.
#
# Example:
#   pdsdata-sync-volset-metadata-versions admin raid45 VGx_9xxx
# copies all files relevant to the metadata for volume set "VGx_9xxx" from the
# drive pdsdata-admin to the drive pdsdata-raid45.
################################################################################

SRC=$1
DEST=$2
VOLSET=$3
ARGS=$4

for TYPE in metadata
do
  if [ -d /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET} ]; then
    echo "\n\n**** holdings/archives-${TYPE}/${VOLSET}* ****"
    rsync -av --exclude=".DS_Store" --exclude="._*" \
              /Volumes/pdsdata-${SRC}/holdings/archives-${TYPE}/${VOLSET}* \
              /Volumes/pdsdata-${DEST}/holdings/archives-${TYPE}/ ${ARGS}

    echo "\n\n**** holdings/checksums-${TYPE}/${VOLSET}* ****"
    rsync -av --exclude=".DS_Store" --exclude="._*" \
              /Volumes/pdsdata-${SRC}/holdings/checksums-${TYPE}/${VOLSET}* \
              /Volumes/pdsdata-${DEST}/holdings/checksums-${TYPE}/ ${ARGS}

    echo "\n\n**** holdings/checksums-archives-${TYPE}/${VOLSET}*_md5.txt ****"
    rsync -av --include="${VOLSET}*_md5.txt" --include="${VOLSET}*_${TYPE}_md5.txt" \
              --exclude="*" --exclude=".DS_Store" --exclude="._*" \
              /Volumes/pdsdata-${SRC}/holdings/checksums-archives-${TYPE}/ \
              /Volumes/pdsdata-${DEST}/holdings/checksums-archives-${TYPE}/ ${ARGS}

    echo "\n\n**** holdings/_infoshelf-${TYPE}/${VOLSET}* ****"
    rsync -av --exclude=".DS_Store" --exclude="._*" \
              /Volumes/pdsdata-${SRC}/holdings/_infoshelf-${TYPE}/${VOLSET}* \
              /Volumes/pdsdata-${DEST}/holdings/_infoshelf-${TYPE}/ ${ARGS}

    echo "\n\n**** holdings/_infoshelf-archives-${TYPE}/${VOLSET}*_info.py ****"
    rsync -av --include="${VOLSET}*_info.py" --include="${VOLSET}*_info.pickle" \
              --exclude="*" --exclude=".DS_Store" --exclude="._*" \
              /Volumes/pdsdata-${SRC}/holdings/_infoshelf-archives-${TYPE}/ \
              /Volumes/pdsdata-${DEST}/holdings/_infoshelf-archives-${TYPE}/ ${ARGS}

    if [ -d /Volumes/pdsdata-${SRC}/holdings/_linkshelf-${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/_linkshelf-${TYPE}/${VOLSET}* ****"
      rsync -av --exclude=".DS_Store" --exclude="._*" \
                /Volumes/pdsdata-${SRC}/holdings/_linkshelf-${TYPE}/${VOLSET}* \
                /Volumes/pdsdata-${DEST}/holdings/_linkshelf-${TYPE}/ ${ARGS}
    fi

    if [ -d /Volumes/pdsdata-${SRC}/holdings/_indexshelf-${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/_indexshelf-${TYPE}/${VOLSET}* ****"
      rsync -av --exclude=".DS_Store" --exclude="._*" \
                /Volumes/pdsdata-${SRC}/holdings/_indexshelf-${TYPE}/${VOLSET}* \
                /Volumes/pdsdata-${DEST}/holdings/_indexshelf-${TYPE}/ ${ARGS}
    fi

    echo "\n\n**** holdings/${TYPE}/${VOLSET}* ****"
    rsync -av --exclude=".DS_Store" --exclude="._*" \
              /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET}* \
              /Volumes/pdsdata-${DEST}/holdings/${TYPE}/ ${ARGS}

  fi
done

if [ -f /Volumes/pdsdata-${SRC}/holdings/_volinfo/${VOLSET}.txt ]; then
  echo "\n\n**** holdings/_volinfo/${VOLSET}.txt ****"
  rsync -av --include="${VOLSET}.txt" --exclude="*" \
        /Volumes/pdsdata-${SRC}/holdings/_volinfo/ \
        /Volumes/pdsdata-${DEST}/holdings/_volinfo/ ${ARGS}
fi

if [ -d /Volumes/pdsdata-${SRC}/holdings/documents/${VOLSET} ]; then
  echo "\n\n**** holdings/documents/${VOLSET} ****"
  rsync -av --delete --exclude=".DS_Store" --exclude="._*" \
        /Volumes/pdsdata-${SRC}/holdings/documents/${VOLSET}/ \
        /Volumes/pdsdata-${DEST}/holdings/documents/${VOLSET}/ ${ARGS}
fi

################################################################################
