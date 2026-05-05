#! /bin/zsh

#########################################################################################
# Synchronize the metadata of one volume set from one pdsdata drive to another.
#
# Usage:
#   pdsdata-sync-volset-metadata <old> <new> <volset> [--dry-run] [--delete]
#
# Syncs the metadata for the specified volume set <volset> from the drive
# /Volumes/pdsdata-<old> to the drive /Volumes/pdsdata-<new>. Use the "--dry-run" option 
# for a test dry run. Use the "--delete" option to delete extraneous files in the remote 
# directory. The rsync options -a (archive) mode and -v (verbose) are included by default.
#
# Example:
#   pdsdata-sync-volset-metadata admin staging VGx_9xxx --delete
# copies all files relevant to the metadata for volume set "VGx_9xxx" from the drive 
# pdsdata-admin to the drive pdsdata-staging, deleting any extraneous files in the 
# destination directories.
#########################################################################################

SRC=$1
DEST=$2
VOLSET=$3
ARG1=$4
ARG2=$5

set -e

if [ "$DEST" = "production" ]; then
  echo "Remounting pdsdata-production as read-write..."
  if ! sudo mount -u -o rw /Volumes/pdsdata-production; then
    echo "ERROR: unable to remount /Volumes/pdsdata-production as read-write." >&2
    exit 1
  fi
  remount_production_read_only_on_exit() {
    local status=$?
    echo "Remounting pdsdata-production as read-only..."
    if ! sudo mount -u -o ro /Volumes/pdsdata-production; then
      echo "ERROR: unable to remount /Volumes/pdsdata-production as read-only." >&2
      status=1
    fi
    return $status
  }
  trap remount_production_read_only_on_exit EXIT
fi

for TYPE in metadata
do
  if [ -d /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET} ]; then
    echo "\n\n**** holdings/archives-${TYPE}/${VOLSET} ****"
    rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
          /Volumes/pdsdata-${SRC}/holdings/archives-${TYPE}/${VOLSET}/ \
          /Volumes/pdsdata-${DEST}/holdings/archives-${TYPE}/${VOLSET}/
    find /Volumes/pdsdata-${DEST}/holdings/archives-${TYPE}/${VOLSET}/ -name "._*" -delete

    echo "\n\n**** holdings/checksums-${TYPE}/${VOLSET} ****"
    rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
          /Volumes/pdsdata-${SRC}/holdings/checksums-${TYPE}/${VOLSET}/ \
          /Volumes/pdsdata-${DEST}/holdings/checksums-${TYPE}/${VOLSET}/
    find /Volumes/pdsdata-${DEST}/holdings/checksums-${TYPE}/${VOLSET}/ -name "._*" -delete

    echo "\n\n**** holdings/checksums-archives-${TYPE}/${VOLSET}_*md5.txt ****"
    rsync -av ${ARG1} ${ARG2} \
        --include="${VOLSET}_md5.txt" --include="${VOLSET}_${TYPE}_md5.txt" \
        --exclude="*" \
        /Volumes/pdsdata-${SRC}/holdings/checksums-archives-${TYPE}/ \
        /Volumes/pdsdata-${DEST}/holdings/checksums-archives-${TYPE}/
    find /Volumes/pdsdata-${DEST}/holdings/checksums-archives-${TYPE}/ -name "._*" -delete

    echo "\n\n**** holdings/_infoshelf-${TYPE}/${VOLSET} ****"
    rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
          /Volumes/pdsdata-${SRC}/holdings/_infoshelf-${TYPE}/${VOLSET}/ \
          /Volumes/pdsdata-${DEST}/holdings/_infoshelf-${TYPE}/${VOLSET}/
    find /Volumes/pdsdata-${DEST}/holdings/_infoshelf-${TYPE}/${VOLSET}/ -name "._*" -delete

    echo "\n\n**** holdings/_infoshelf-archives-${TYPE}/${VOLSET}_info.py ****"
    rsync -av ${ARG1} ${ARG2} \
          --include="${VOLSET}_info.py" --include="${VOLSET}_info.pickle" \
          --exclude="*" \
          /Volumes/pdsdata-${SRC}/holdings/_infoshelf-archives-${TYPE}/ \
          /Volumes/pdsdata-${DEST}/holdings/_infoshelf-archives-${TYPE}/
    find /Volumes/pdsdata-${DEST}/holdings/_infoshelf-archives-${TYPE}/ -name "._*" -delete

    if [ -d /Volumes/pdsdata-${SRC}/holdings/_linkshelf-${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/_linkshelf-${TYPE}/${VOLSET} ****"
      rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
            /Volumes/pdsdata-${SRC}/holdings/_linkshelf-${TYPE}/${VOLSET}/ \
            /Volumes/pdsdata-${DEST}/holdings/_linkshelf-${TYPE}/${VOLSET}/
      find /Volumes/pdsdata-${DEST}/holdings/_linkshelf-${TYPE}/${VOLSET}/ -name "._*" -delete
    fi

    if [ -d /Volumes/pdsdata-${SRC}/holdings/_indexshelf-${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/_indexshelf-${TYPE}/${VOLSET} ****"
      rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
            /Volumes/pdsdata-${SRC}/holdings/_indexshelf-${TYPE}/${VOLSET}/ \
            /Volumes/pdsdata-${DEST}/holdings/_indexshelf-${TYPE}/${VOLSET}/
      find /Volumes/pdsdata-${DEST}/holdings/_indexshelf-${TYPE}/${VOLSET}/ -name "._*" -delete
    fi

    echo "\n\n**** holdings/${TYPE}/${VOLSET} ****"
    rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
          /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET}/ \
          /Volumes/pdsdata-${DEST}/holdings/${TYPE}/${VOLSET}/
    find /Volumes/pdsdata-${DEST}/holdings/${TYPE}/${VOLSET}/ -name "._*" -delete
  fi
done

if [ -f /Volumes/pdsdata-${SRC}/holdings/_volinfo/${VOLSET}.txt ]; then
  echo "\n\n**** holdings/_volinfo/${VOLSET}.txt ****"
  rsync -av ${ARG1} ${ARG2} --include="${VOLSET}.txt" --exclude="*" \
        /Volumes/pdsdata-${SRC}/holdings/_volinfo/ \
        /Volumes/pdsdata-${DEST}/holdings/_volinfo/
  find /Volumes/pdsdata-${DEST}/holdings/_volinfo/ -name "._*" -delete
fi

if [ -d /Volumes/pdsdata-${SRC}/holdings/documents/${VOLSET} ]; then
  echo "\n\n**** holdings/documents/${VOLSET} ****"
  rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
        /Volumes/pdsdata-${SRC}/holdings/documents/${VOLSET}/ \
        /Volumes/pdsdata-${DEST}/holdings/documents/${VOLSET}/
  find /Volumes/pdsdata-${DEST}/holdings/documents/${VOLSET}/ -name "._*" -delete
fi

#########################################################################################
