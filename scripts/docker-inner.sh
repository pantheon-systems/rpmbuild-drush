#!/bin/sh
#
#
set -ex
bin="$(cd -P -- "$(dirname -- "$0")" && pwd -P)"

if [ "$#" -lt 4 ]; then
  echo "Usage: $0 channel rpm_dir build_num epoch [fedora_release]"
  exit 1
fi

rpm_dir=$2
build=$3
epoch=$4
fedora_release=$5

if [ -z "$fedora_release" ]
then
    fedora_release=$(rpm -q --queryformat '%{VERSION}\n' fedora-release)
fi

shortname="drush"
target_dir="$rpm_dir/$fedora_release/drush"
versions=$(cat $bin/../VERSIONS.txt | grep -v '^#')

for version in $versions; do
    channel=${version%%.*}
    name="$shortname-$channel"
    iteration=${epoch}
    arch='x86_64'
    url="https://github.com/pantheon-systems/${shortname}"
    vendor='Pantheon'
    description='drush: Pantheon rpm containing commandline tool for Drupal'
    install_prefix="/opt/pantheon/$shortname"
    download_dir="$bin/../build$channel"

    GITSHA=$(git log -1 --format="%h")
    iteration=${iteration}.${GITSHA}

    # Add the git SHA hash to the rpm build if the local working copy is clean
    if [ -z "$(git status --porcelain)" ]
    then
        GITSHA=$(git log -1 --format="%h")
        iteration=${iteration}.${GITSHA}
    else
        # Allow non-clean builds in dev mode; for anything else, fail if there
        # are uncommitted changes.
        if [ "$channel" != "dev" ]
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

    git clone https://github.com/drush-ops/drush.git $download_dir/$name
    [ $? == 0 ] || (echo "Git repository could not be cloned!"; exit 1)
    
    cd $download_dir/$name
    composer install
    [ $? == 0 ] || (echo "Install failed!"; exit 1)
    cd -

    mkdir -p "$target_dir"
    
    cd $download_dir

    fpm -s dir -t rpm  \
        --package "$target_dir/${name}-${version}-${iteration}.${arch}.rpm" \
        --name "${name}" \
        --version "${version}" \
        --iteration "${iteration}" \
        --epoch "${epoch}" \
        --architecture "${arch}" \
        --url "${url}" \
        --vendor "${vendor}" \
        --description "${description}" \
        --prefix "$install_prefix" \
        -C /$download_dir \
        $name
    done

# Finish up by running our tests.
$bin/../tests/confirm-rpm.sh $fedora_release
