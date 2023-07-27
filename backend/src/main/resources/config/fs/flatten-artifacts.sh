#!/bin/bash

# Read flags
while getopts h: flag
do
    case "${flag}" in
        h) giskard_home=${OPTARG};;
        a*) exit 1;;
    esac
done

# No migration necessary on new environments
if ! [ -d "$giskard_home" ]
then
    exit 0;
fi

# Read migration version and skip if already executed
cd "$giskard_home" || exit 1;
if [ -f "$giskard_home/fs-logs" ] && grep -q -F "flatten-artifacts" "$giskard_home/fs-logs";
then
    exit 0;
fi

# Execute migration
# Create new artifacts folders
artifacts_types=("tests" "slices" "transformations" "datasets" "models");
mkdir "$giskard_home/artifacts";
for type in "${artifacts_types[@]}" ; do
   mkdir "$giskard_home/artifacts/$type";
done

# No projects existing
cd "$giskard_home/projects" || exit 0;

# move all artifacts
for project in */ ; do
    for type in "${artifacts_types[@]}" ; do
       if [ -d "$giskard_home/projects/$project/$type" ]
       then
           cd "$giskard_home/projects/$project/$type" || exit 2;
           for artifact in */ ; do
               if ! [ -d "$giskard_home/artifacts/$type/$artifact" ]
               then
                   mv "$giskard_home/projects/$project/$type/$artifact" "$giskard_home/artifacts/$type/$artifact";
               fi
           done
       fi
    done
done

# Cleanup
rm -r "$giskard_home/projects";
echo "flatten-artifacts" > "$giskard_home/fs-logs";
