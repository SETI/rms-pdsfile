#! /bin/zsh

#########################################################################################
# Synchronize the metadata for one volume set from one pdsdata drive to another.
#
# Usage:
#   pdsdata-sync-volume-metadata <old> <new> <volset> <volume> [--dry-run] [--delete]
#
# Syncs the specified metadata for the volume <volset/volume> from the drive 
# /Volumes/pdsdata-<old> to the drive /Volumes/pdsdata-<new>. Use the "--dry-run" option 
# for a test dry run. Use the "--delete" option to delete extraneous files in the remote 
# directory. The rsync options -a (archive) mode and -v (verbose) are included by default.
#
# Example:
#   pdsdata-sync-volume-metadata admin staging GO_0xxx GO_0023 --delete
# copies all files relevant to the metadata for volume "GO_0xxx/GO_0023" from the drive 
# pdsdata-admin to the drive pdsdata-staging, deleting any extraneous files in the 
# destination directories.
#########################################################################################

SRC=$1
DEST=$2
VOLSET=$3
VOLUME=$4
ARG1=$5
ARG2=$6

for TYPE in metadata
do
  if [ -d /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET}/${VOLUME} ]; then
    echo "\n\n**** holdings/archives-${TYPE}/${VOLSET}/${VOLUME}*.tar.gz ****"
    rsync -av ${ARG1} ${ARG2} \
          --include="${VOLUME}.tar.gz" --include="${VOLUME}_${TYPE}.tar.gz" \
          --exclude="*" \
          /Volumes/pdsdata-${SRC}/holdings/archives-${TYPE}/${VOLSET}/ \
          /Volumes/pdsdata-${DEST}/holdings/archives-${TYPE}/${VOLSET}/

    echo "\n\n**** holdings/checksums-${TYPE}/${VOLSET}/${VOLUME}*_md5.txt ****"
    rsync -av ${ARG1} ${ARG2} \
          --include="${VOLUME}_md5.txt" --include="${VOLUME}_${TYPE}_md5.txt" \
          --exclude="*" \
          /Volumes/pdsdata-${SRC}/holdings/checksums-${TYPE}/${VOLSET}/ \
          /Volumes/pdsdata-${DEST}/holdings/checksums-${TYPE}/${VOLSET}/ 

    echo "\n\n**** holdings/checksums-archives-${TYPE}/${VOLSET}_*md5.txt ****"
    rsync -av ${ARG1} ${ARG2} \
          --include="${VOLSET}_md5.txt" --include="${VOLSET}_${TYPE}_md5.txt" \
          --exclude="*" \
          /Volumes/pdsdata-${SRC}/holdings/checksums-archives-${TYPE}/ \
          /Volumes/pdsdata-${DEST}/holdings/checksums-archives-${TYPE}/

    echo "\n\n**** holdings/_infoshelf-${TYPE}/${VOLSET}/${VOLUME}_info.* ****"
    rsync -av ${ARG1} ${ARG2} \
          --include="${VOLUME}_info.py" --include="${VOLUME}_info.pickle" \
          --exclude="*" \
          /Volumes/pdsdata-${SRC}/holdings/_infoshelf-${TYPE}/${VOLSET}/ \
          /Volumes/pdsdata-${DEST}/holdings/_infoshelf-${TYPE}/${VOLSET}/

    echo "\n\n**** holdings/_infoshelf-archives-${TYPE}/${VOLSET}_info.* ****"
    rsync -av ${ARG1} ${ARG2} \
          --include="${VOLSET}_info.py" --include="${VOLSET}_info.pickle" \
          --exclude="*" \
          /Volumes/pdsdata-${SRC}/holdings/_infoshelf-archives-${TYPE}/ \
          /Volumes/pdsdata-${DEST}/holdings/_infoshelf-archives-${TYPE}/

    if [ -d /Volumes/pdsdata-${SRC}/holdings/_linkshelf-${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/_linkshelf-${TYPE}/${VOLSET}/${VOLUME}_links.* ****"
      rsync -av ${ARG1} ${ARG2} \
            --include="${VOLUME}_links.py" --include="${VOLUME}_links.pickle" \
            --exclude="*" \
            /Volumes/pdsdata-${SRC}/holdings/_linkshelf-${TYPE}/${VOLSET}/ \
            /Volumes/pdsdata-${DEST}/holdings/_linkshelf-${TYPE}/${VOLSET}/
    fi

    if [ -d /Volumes/pdsdata-${SRC}/holdings/_indexshelf-${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/_indexshelf-${TYPE}/${VOLSET}/${VOLUME} ****"
      rsync -av ${ARG1} ${ARG2} \
            --exclude=".DS_Store" --exclude="._*" \
            /Volumes/pdsdata-${SRC}/holdings/_indexshelf-${TYPE}/${VOLSET}/${VOLUME}/ \
            /Volumes/pdsdata-${DEST}/holdings/_indexshelf-${TYPE}/${VOLSET}/${VOLUME}/
    fi

    if [ -d /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET} ]; then
      echo "\n\n**** holdings/${TYPE}/${VOLSET}/${VOLUME} ****"
      rsync -av ${ARG1} ${ARG2} \
            --exclude=".DS_Store" --exclude="._*" \
            /Volumes/pdsdata-${SRC}/holdings/${TYPE}/${VOLSET}/${VOLUME}/ \
            /Volumes/pdsdata-${DEST}/holdings/${TYPE}/${VOLSET}/${VOLUME}/
    fi

  fi
done

if [ -f /Volumes/pdsdata-${SRC}/holdings/_volinfo/${VOLSET}.txt ]; then
  echo "\n\n**** holdings/_volinfo/${VOLSET}.txt ****"
  rsync -av ${ARG1} ${ARG2} \
        --include="${VOLSET}.txt" --exclude="*" \
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
