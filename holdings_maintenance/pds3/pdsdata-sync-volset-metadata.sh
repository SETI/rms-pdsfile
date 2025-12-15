#! /bin/zsh

#########################################################################################
# Synchronize the metadata of one volume set from one pdsdata drive to another.
#
# Usage:
#   pdsdata-sync-volset-metadata [--dry-run] [--delete] <old> <new> <volset>
#
# Syncs the metadata for the specified volume set <volset> from the drive
# /Volumes/pdsdata-<old> to the drive /Volumes/pdsdata-<new>. Use the option "--dry-run" 
# for a test dry run. Use the option "--delete" to delete extraneous files in the remote 
# directory. The rsync options -a (archive) mode and -v (verbose) are included by default.
# This only syncs the metadata and associated directories and should be used when syncing 
# versioned metadata.
#
# Example:
#   pdsdata-sync-volset-metadata --delete admin staging VGx_9xxx
# copies all files relevant to the metadata for volume set "VGx_9xxx" from the drive 
# pdsdata-admin to the drive pdsdata-staging, deleting any extraneous files in the 
# destination directories.
#########################################################################################

ARG1=""
ARG2=""

# Check for the optional flags (--dry-run and --delete)
while [[ $# -gt 0 && $1 == --* ]]; do
  case $1 in
    --dry-run)
      ARG1="--dry-run"
      shift
      ;;
    --delete)
      ARG2="--delete"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Assign the required positional arguments
SRC=$1
DEST=$2
VOLSET=$3

for TYPE in metadata
do
  if [ -d /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET} ]; then
    echo "\n\n**** holdings/archives-${TYPE}/${VOLSET} ****"
    rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
          /Volumes/pdsdata-${SRC}/holdings/archives-${TYPE}/${VOLSET}/ \
          /Volumes/pdsdata-${DEST}/holdings/archives-${TYPE}/${VOLSET}/

    echo "\n\n**** holdings/checksums-${TYPE}/${VOLSET} ****"
    rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
          /Volumes/pdsdata-${SRC}/holdings/checksums-${TYPE}/${VOLSET}/ \
          /Volumes/pdsdata-${DEST}/holdings/checksums-${TYPE}/${VOLSET}/

    echo "\n\n**** holdings/checksums-archives-${TYPE}/${VOLSET}_*md5.txt ****"
    rsync -av ${ARG1} ${ARG2} \
        --include="${VOLSET}_md5.txt" --include="${VOLSET}_${TYPE}_md5.txt" \
        --exclude="*" \
        /Volumes/pdsdata-${SRC}/holdings/checksums-archives-${TYPE}/ \
        /Volumes/pdsdata-${DEST}/holdings/checksums-archives-${TYPE}/

    echo "\n\n**** holdings/_infoshelf-${TYPE}/${VOLSET} ****"
    rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
          /Volumes/pdsdata-${SRC}/holdings/_infoshelf-${TYPE}/${VOLSET}/ \
          /Volumes/pdsdata-${DEST}/holdings/_infoshelf-${TYPE}/${VOLSET}/

    echo "\n\n**** holdings/_infoshelf-archives-${TYPE}/${VOLSET}_info.py ****"
    rsync -av ${ARG1} ${ARG2} \
          --include="${VOLSET}_info.py" --include="${VOLSET}_info.pickle" \
          --exclude="*" \
          /Volumes/pdsdata-${SRC}/holdings/_infoshelf-archives-${TYPE}/ \
          /Volumes/pdsdata-${DEST}/holdings/_infoshelf-archives-${TYPE}/

    if [ -d /Volumes/pdsdata-${SRC}/holdings/_linkshelf-${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/_linkshelf-${TYPE}/${VOLSET} ****"
      rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
            /Volumes/pdsdata-${SRC}/holdings/_linkshelf-${TYPE}/${VOLSET}/ \
            /Volumes/pdsdata-${DEST}/holdings/_linkshelf-${TYPE}/${VOLSET}/
    fi

    if [ -d /Volumes/pdsdata-${SRC}/holdings/_indexshelf-${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/_indexshelf-${TYPE}/${VOLSET} ****"
      rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
            /Volumes/pdsdata-${SRC}/holdings/_indexshelf-${TYPE}/${VOLSET}/ \
            /Volumes/pdsdata-${DEST}/holdings/_indexshelf-${TYPE}/${VOLSET}/
    fi

    echo "\n\n**** holdings/${TYPE}/${VOLSET} ****"
    rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
          /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET}/ \
          /Volumes/pdsdata-${DEST}/holdings/${TYPE}/${VOLSET}/

  fi
done

if [ -f /Volumes/pdsdata-${SRC}/holdings/_volinfo/${VOLSET}.txt ]; then
  echo "\n\n**** holdings/_volinfo/${VOLSET}.txt ****"
  rsync -av ${ARG1} ${ARG2} --include="${VOLSET}.txt" --exclude="*" \
        /Volumes/pdsdata-${SRC}/holdings/_volinfo/ \
        /Volumes/pdsdata-${DEST}/holdings/_volinfo/
fi

if [ -d /Volumes/pdsdata-${SRC}/holdings/documents/${VOLSET} ]; then
  echo "\n\n**** holdings/documents/${VOLSET} ****"
  rsync -av ${ARG1} ${ARG2} --exclude=".DS_Store" --exclude="._*" \
        /Volumes/pdsdata-${SRC}/holdings/documents/${VOLSET}/ \
        /Volumes/pdsdata-${DEST}/holdings/documents/${VOLSET}/
fi

#########################################################################################
