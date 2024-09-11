#! /bin/zsh
################################################################################
# Synchronize one volume set from one pdsdata drive to another.
#
# Usage:
#   pdsdata-sync-volume-metadata <old> <new> <volset> <volume> [--dry-run]
#
# Syncs the specified metadata for the volume <volset/volume> from the drive
# /Volumes/pdsdata-<old> to the drive /Volumes/pdsdata-<new>. Append
# "--dry-run" for a test dry run.
# This only syncs the metadata and associated directories and should be used
# when syncing versioned metadata.
#
# Example:
#   pdsdata-sync-volume-metadata admin raid45 GO_0xxx GO_0023
# copies all files relevant to the metadata for volume "GO_0xxx/GO_0023" from
# the drive pdsdata-admin to the drive pdsdata-raid45.
################################################################################

for voltype in metadata
do
  if [ -d /Volumes/pdsdata-$1/holdings/$voltype/$3/$4 ]; then
    echo "\n\n**** holdings/archives-$voltype/$3/$4*.tar.gz ****"
    rsync -av --include="$4.tar.gz" --include="$4_${voltype}.tar.gz" \
              --exclude="*" \
              /Volumes/pdsdata-$1/holdings/archives-$voltype/$3/ \
              /Volumes/pdsdata-$2/holdings/archives-$voltype/$3/ $5

    echo "\n\n**** holdings/checksums-$voltype/$3/$4*_md5.txt ****"
    rsync -av --include="$4_md5.txt" --include="$4_${voltype}_md5.txt" \
              --exclude="*" \
              /Volumes/pdsdata-$1/holdings/checksums-$voltype/$3/ \
              /Volumes/pdsdata-$2/holdings/checksums-$voltype/$3/ $5

    echo "\n\n**** holdings/checksums-archives-$voltype/$3_*md5.txt ****"
    rsync -av --include="$4_md5.txt" --include="$4_${voltype}_md5.txt" \
              --exclude="*" \
              /Volumes/pdsdata-$1/holdings/checksums-archives-$voltype/ \
              /Volumes/pdsdata-$2/holdings/checksums-archives-$voltype/ $5

    echo "\n\n**** holdings/_infoshelf-$voltype/$3/$4_info.* ****"
    rsync -av --include="$4_info.py" --include="$4_info.pickle" \
              --exclude="*" \
              /Volumes/pdsdata-$1/holdings/_infoshelf-$voltype/$3/ \
              /Volumes/pdsdata-$2/holdings/_infoshelf-$voltype/$3/ $5

    echo "\n\n**** holdings/_infoshelf-archives-$voltype/$3_info.* ****"
    rsync -av --include="$3_info.py" --include="$3_info.pickle" \
              --exclude="*" \
              /Volumes/pdsdata-$1/holdings/_infoshelf-archives-$voltype/ \
              /Volumes/pdsdata-$2/holdings/_infoshelf-archives-$voltype/ $5

    if [ -d /Volumes/pdsdata-$1/holdings/_linkshelf-$voltype/$3 ]; then
      echo "\n\n**** holdings/_linkshelf-$voltype/$3/$4_links.* ****"
      rsync -av --include="$4_links.py" --include="$4_links.pickle" \
                --exclude="*" \
                /Volumes/pdsdata-$1/holdings/_linkshelf-$voltype/$3/ \
                /Volumes/pdsdata-$2/holdings/_linkshelf-$voltype/$3/ $5
    fi

    if [ -d /Volumes/pdsdata-$1/holdings/_indexshelf-$voltype/$3 ]; then
      echo "\n\n**** holdings/_indexshelf-$voltype/$3/$4 ****"
      rsync -av --delete --exclude=".DS_Store" \
                /Volumes/pdsdata-$1/holdings/_indexshelf-$voltype/$3/$4/ \
                /Volumes/pdsdata-$2/holdings/_indexshelf-$voltype/$3/$4/ $5
    fi

    if [ -d /Volumes/pdsdata-$1/holdings/$voltype/$3 ]; then
      echo "\n\n**** holdings/$voltype/$3/$4 ****"
      rsync -av --delete --exclude=".DS_Store" \
                /Volumes/pdsdata-$1/holdings/$voltype/$3/$4/ \
                /Volumes/pdsdata-$2/holdings/$voltype/$3/$4/ $5
    fi

  fi
done

echo
echo ">>> NOTE: This sync did not copy over any changes to the documents or"
echo ">>> _volinfo directories. You must sync the main volset for that to"
echo ">>> occur."

################################################################################

