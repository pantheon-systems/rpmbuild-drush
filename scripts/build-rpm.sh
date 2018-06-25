#!/bin/sh

set -ex
bin="$(cd -P -- "$(dirname -- "$0")" && pwd -P)"

# Set "channel" to "dev" for non-Circle builds, and "release" for Circle builds
CHANNEL="dev"
if [ -n "$CIRCLECI" ] ; then
	CHANNEL="release"
fi

# epoch to use for -revision
epoch=$(date +%s)

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
	#iteration="$(date +%Y%m%d%H%M)"
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

	mkdir -p "$target_dir"

	fpm -s dir -t rpm	 \
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
		-C $download_dir \
		$(ls $download_dir)

	# Finish up by running our tests.
	sh $bin/../tests/confirm-rpm.sh $name
)done
