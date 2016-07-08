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
arch='x86_64'
vendor='Pantheon'
description='drush: Pantheon rpm containing commandline tool for Drupal'

versions=$(cat $bin/../VERSIONS.txt | grep -v '^#')

for version in $versions; do(

	version_untampered=$version
	version=$(echo $version | sed -e 's/\([^-]*\)-\([^-]*\)-\(.*\)/\1.\2.0\-\3/')

	releasenum=${version%%.*}
	releasever=${version%.*}
	name="$shortname-$releasenum"
	expname="$shortname-$releasever"
	iteration="$(date +%Y%m%d%H%M)"
	url="https://github.com/pantheon-systems/${shortname}"
	install_prefix="/opt/pantheon/$name"
	download_dir="$bin/../builds/$name"
	target_dir="$bin/../pkgs/$name"

	# Add the git SHA hash to the rpm build if the local working copy is clean
	if [ -z "$(git diff-index --quiet HEAD --)" ]
	then
		GITSHA=$(git log -1 --format="%h")
		iteration=${iteration}.${GITSHA}
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

	cd -

	mkdir -p "$target_dir"

	fpm -s dir -t rpm	 \
		--package "$target_dir/${expname}-release-${version}-${iteration}.${arch}.rpm" \
		--name "${name}" \
		--version "${version}" \
		--iteration "${iteration}" \
		--epoch "${epoch}" \
		--architecture "${arch}" \
		--url "${url}" \
		--vendor "${vendor}" \
		--description "${description}" \
		--prefix "$install_prefix" \
		-C $download_dir \
		$(ls $download_dir)

	# Finish up by running our tests.
	sh $bin/../tests/confirm-rpm.sh $name
)done
