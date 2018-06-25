#!/bin/bash
#
#  wrapper for pushing rpm's up to both repos
#
repo_versions=(22)

bin="$(cd -P -- "$(dirname -- "$0")" && pwd -P)"

if [ -z "$(which package_cloud)" ]; then
  echo "Error no 'package_cloud' found in PATH"
  exit 1
fi

if [ -z "$1" ] ; then
  echo "Need to specify target repo: internal, internal-staging"
  exit 1
fi

versions=$(cat $bin/../VERSIONS.txt | grep -v '^#')
shortname=drush
arch=noarch

for version_with_datecode in $versions; do(

  version=$(echo $version_with_datecode | cut -d : -f 1)
  iteration=$(echo $version_with_datecode | cut -d : -f 2)
  version_untampered=$version
  version=$(echo $version | sed -e 's/\([^-]*\)-\([^-]*\)-\(.*\)/\1.\2.0\-\3/')

  releasenum=${version%%.*}
  name="$shortname$releasenum"
  #iteration="$(date +%Y%m%d%H%M)"
  url="https://github.com/pantheon-systems/${shortname}"
  install_prefix="/opt/pantheon/$name"
  download_dir="$bin/../builds/$name"
  target_dir="$bin/../pkgs/$name"

  rpm_name=${name}-${version}-${iteration}.${arch}.rpm

  for fedora_version in ${repo_versions[@]} ; do
    package_cloud push "pantheon/$1/fedora/$fedora_version" $target_dir/$rpm_name
  done

)done
