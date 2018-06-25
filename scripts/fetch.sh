#!/bin/sh

set -ex
bin="$(cd -P -- "$(dirname -- "$0")" && pwd -P)"

# set a default build -> 0 for when it doesn't exist
CIRCLE_BUILD_NUM=${CIRCLE_BUILD_NUM:-0}

# epoch to use for -revision
epoch=$(date +%s)

case $CIRCLE_BRANCH in
"master")
  CHANNEL="release"
  ;;
"stage")
  CHANNEL="stage"
  ;;
"yolo")
  CHANNEL="yolo"
  ;;
*)
  CHANNEL="dev"
  ;;
esac

shortname="drush"
arch='noarch'
vendor='Pantheon'
description='drush: Pantheon rpm containing commandline tool for Drupal'

versions=$(cat $bin/../VERSIONS.txt | grep -v '^#')

for version_with_datecode in $versions; do(

  version=$(echo $version_with_datecode | cut -d : -f 1)
  iteration=$(echo $version_with_datecode | cut -d : -f 2)
  version_untampered=$version
  version=$(echo $version | sed -e 's/\([^-]*\)-\([^-]*\)-\(.*\)/\1.\2.0\-\3/')

  releasenum=${version%%.*}
  name="$shortname$releasenum"
  url="https://github.com/pantheon-systems/${shortname}"
  install_prefix="/opt/pantheon/$name"
  download_dir="$bin/../builds/$name"
  target_dir="$bin/../pkgs/$name"

  # Add the git SHA hash to the rpm build if the local working copy is clean
  if [ -z "$(git diff-index --quiet HEAD --)" ]
  then
    GITSHA=$(git log -1 --format="%h")
    iteration=${iteration}.git${GITSHA}
  else
    # Allow non-clean builds in dev mode; for anything else, fail if there
    # are uncommitted changes.
    if [ "$CHANNEL" != "dev" ]
    then
      echo >&2
      echo "Error: uncommitted changes present. Please commit to continue." >&2
      echo "Git commithash is included in rpm, so working tree must be clean to build." >&2
      exit 1
    fi
  fi

  # We wastefully re-download the same file for each version of Fedora. Oh well.
  rm -rf $download_dir
  mkdir -p $download_dir

  if [ $releasenum -le "6" ]
  then
    git_dir="https://github.com/pantheon-systems/drush.git"
  else
    git_dir="https://github.com/drush-ops/drush.git"
  fi

  git clone $git_dir $download_dir
  cd $download_dir
  git checkout $version_untampered

  [ -f composer.json ] && composer install

  # For Drush 5 only, install external Drush extensions to
  # /opt/pantheon/drush5/commands. In general, we want to put
  # extensions in a different RPM from the main executable (Drush);
  # however, in this case, these extensions are legacy support only.
  # We do not expect to update the versions hereafter.
  # Note that `commands` is the legacy location Pantheon used to
  # install extensions in Drush 5.
  if [ $releasenum -le "5" ]
  then
    drush5="$download_dir/drush"
    drush5_external_extensions="$download_dir/commands"
    mkdir -p "$drush5_external_extensions"
    $drush5 dl --package-handler=git_drupalorg -y --destination="$drush5_external_extensions" --default-major=6 drush_make
    $drush5 dl --package-handler=git_drupalorg -y --destination="$drush5_external_extensions" --default-major=7 registry_rebuild-7.x-2.3
    $drush5 dl --package-handler=git_drupalorg -y --destination="$drush5_external_extensions" --default-major=7 site_audit-7.x-1.10
    # Allegedly this directory is necessary
    mkdir -p "$download_dir/aliases"
  fi

  cd -

)done
