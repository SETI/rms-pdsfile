#! /bin/zsh
################################################################################
# Synchronize one volume set from one pdsdata drive to another.
#
# Usage:
#   pdsdata-sync-volume <old> <new> <volset> <volume> [--dry-run]
#
# Syncs the specified volume <volset/volume> from the drive
# /Volumes/pdsdata-<old> to the drive /Volumes/pdsdata-<new>. Append
# "--dry-run" for a test dry run.
#
# Example:
#   pdsdata-sync-volume admin raid45 GO_0xxx GO_0023
# copies all files relevant to the volume "GO_0xxx/GO_0023" from the drive
# pdsdata-admin to the drive pdsdata-raid45.
################################################################################

SRC=$1
DEST=$2
VOLSET=$3
VOLUME=$4
ARGS=$5

for TYPE in metadata previews calibrated diagrams volumes
do
  if [ -d /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET}/${VOLUME} ]; then
    echo "\n\n**** holdings/archives-${TYPE}/${VOLSET}/${VOLUME}*.tar.gz ****"
    rsync -av --include="${VOLUME}.tar.gz" --include="${VOLUME}_${TYPE}.tar.gz" \
              --exclude="*" \
              /Volumes/pdsdata-${SRC}/holdings/archives-${TYPE}/${VOLSET}/ \
              /Volumes/pdsdata-${DEST}/holdings/archives-${TYPE}/${VOLSET}/ ${ARGS}

    echo "\n\n**** holdings/checksums-${TYPE}/${VOLSET}/${VOLUME}*_md5.txt ****"
    rsync -av --include="${VOLUME}_md5.txt" --include="${VOLUME}_${TYPE}_md5.txt" \
              --exclude="*" \
              /Volumes/pdsdata-${SRC}/holdings/checksums-${TYPE}/${VOLSET}/ \
              /Volumes/pdsdata-${DEST}/holdings/checksums-${TYPE}/${VOLSET}/ ${ARGS}

    echo "\n\n**** holdings/checksums-archives-${TYPE}/${VOLSET}_*md5.txt ****"
    rsync -av --include="${VOLSET}_md5.txt" --include="${VOLSET}_${TYPE}_md5.txt" \
              --exclude="*" \
              /Volumes/pdsdata-${SRC}/holdings/checksums-archives-${TYPE}/ \
              /Volumes/pdsdata-${DEST}/holdings/checksums-archives-${TYPE}/ ${ARGS}

    echo "\n\n**** holdings/_infoshelf-${TYPE}/${VOLSET}/${VOLUME}_info.* ****"
    rsync -av --include="${VOLUME}_info.py" --include="${VOLUME}_info.pickle" \
              --exclude="*" \
              /Volumes/pdsdata-${SRC}/holdings/_infoshelf-${TYPE}/${VOLSET}/ \
              /Volumes/pdsdata-${DEST}/holdings/_infoshelf-${TYPE}/${VOLSET}/ ${ARGS}

    echo "\n\n**** holdings/_infoshelf-archives-${TYPE}/${VOLSET}_info.* ****"
    rsync -av --include="${VOLSET}_info.py" --include="${VOLSET}_info.pickle" \
              --exclude="*" \
              /Volumes/pdsdata-${SRC}/holdings/_infoshelf-archives-${TYPE}/ \
              /Volumes/pdsdata-${DEST}/holdings/_infoshelf-archives-${TYPE}/ ${ARGS}

    if [ -d /Volumes/pdsdata-${SRC}/holdings/_linkshelf-${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/_linkshelf-${TYPE}/${VOLSET}/${VOLUME}_links.* ****"
      rsync -av --include="${VOLUME}_links.py" --include="${VOLUME}_links.pickle" \
                --exclude="*" \
                /Volumes/pdsdata-${SRC}/holdings/_linkshelf-${TYPE}/${VOLSET}/ \
                /Volumes/pdsdata-${DEST}/holdings/_linkshelf-${TYPE}/${VOLSET}/ ${ARGS}
    fi

    if [ -d /Volumes/pdsdata-${SRC}/holdings/_indexshelf-${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/_indexshelf-${TYPE}/${VOLSET}/${VOLUME} ****"
      rsync -av --delete --exclude=".DS_Store" \
                /Volumes/pdsdata-${SRC}/holdings/_indexshelf-${TYPE}/${VOLSET}/${VOLUME}/ \
                /Volumes/pdsdata-${DEST}/holdings/_indexshelf-${TYPE}/${VOLSET}/${VOLUME}/ ${ARGS}
    fi

    if [ -d /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/${TYPE}/${VOLSET}/${VOLUME} ****"
      rsync -av --delete --exclude=".DS_Store" \
                /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET}/${VOLUME}/ \
                /Volumes/pdsdata-${DEST}/holdings/${TYPE}/${VOLSET}/${VOLUME}/ ${ARGS}
    fi

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
  rsync -av --delete --exclude=".DS_Store" \
        /Volumes/pdsdata-${SRC}/holdings/documents/${VOLSET}/ \
        /Volumes/pdsdata-${DEST}/holdings/documents/${VOLSET}/ ${ARGS}
fi

echo
echo ">>> NOTE: If you are syncing a versioned volset, you will also need"
echo ">>> to sync the non-versioned volset in order to copy over any"
echo ">>> changes to the documents or _volinfo directories."

################################################################################

