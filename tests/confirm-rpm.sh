#!/bin/bash
# confirm-rpm.sh

fedora_release=$1
drush_version=$2

expectedName=drush
pkgDir="pkg/$fedora_release/drush"

if [ ! -d "$pkgDir" ]
then
  echo 'Package directory not found.'
  exit 1
fi

rpmName=$(ls $pkgDir | grep $drush_version)

if [ -z "$rpmName" ]
then
  echo 'No build found.'
  exit 1
fi

echo
echo "RPM info:"
echo "-------------------------------"
echo "RPM is $rpmName"
rpm -qpi "$pkgDir/$rpmName"
echo
echo "RPM contents:"
echo "-------------------------------"
rpm -qpl "$pkgDir/$rpmName"
echo

name=$(rpm -qp --queryformat '%{NAME}\n' "$pkgDir/$rpmName")
if [ "$(echo "$name" | sed -e 's/-[a-z0-9]*$//')" != "$expectedName" ]
then
  echo "Name is not $expectedName"
  exit 1
fi

if [ "$name" == "$expectedName" ]
then
  echo "Name does not have channel (dev, prod, etc.) appended."
  exit 1
fi

epoch=$(rpm -qp --queryformat '%{EPOCH}\n' "$pkgDir/$rpmName")
if [ -z "$(echo "$epoch" | grep '^[0-9]\{10\}$')" ]
then
  echo "Epoch $epoch does not look like an epoch"
  exit 1
fi

release=$(rpm -qp --queryformat '%{RELEASE}\n' "$pkgDir/$rpmName")
if [ -z "$(echo "$release" | grep '^\([0-9]\{10\}\.[0-9a-f]\{7\}\|[0-9]\{10\}\)$')" ]
then
  echo "Release $release does not match our expected format"
  exit 1
fi

# This semver regex just ignores the pre-release section without validating it
version=$(rpm -qp --queryformat '%{VERSION}\n' "$pkgDir/$rpmName")
if [ -z "$(echo "$version" | grep '^[0-9]\+\.[0-9]\+\.[0-9]\+')" ]
then
  echo "Version $version does not follow SemVer"
  exit 1
fi

contents=$(rpm -qpl "$pkgDir/$rpmName")
if [ -z "$(echo "$contents" | grep '/opt/pantheon/drush-[0-9]*/drush')" ]
then
  echo "RPM contents not correct"
  exit 1
fi

echo 'Basic rpm validation checks all passed.'
exit 0
