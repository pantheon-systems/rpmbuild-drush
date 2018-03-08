[![CircleCI](https://circleci.com/gh/pantheon-systems/rpmbuild-drush.svg?style=shield)](https://circleci.com/gh/pantheon-systems/rpmbuild-drush)

# RPMs for Drush

This repository builds RPMs for drush.

The RPM filenames built by this repository are formatted:
```
drush8-8.1.2-201607081150.gitc14c267.noarch.rpm
{name}-{ver}-{iteration }.{ commit }.{arch}.rpm
```
The iteration number is a timestamp (year month day hour minute). The build script will refuse to make an RPM when there are uncommitted changes to the working tree, since the commit hash is included in the RPM name.

This rpm installs:

https://github.com/pantheon-systems/drush.git (Drush versions 5 and 6, forked for Pantheon)
https://github.com/drush-ops/drush.git (Drush versions 7 and 8)

## Picking drush versions

To specify drush versions to build, add to or comment out versions listed in VERSIONS.txt. For the convenience of future reference, please do not delete versions. Commenting them out will be sufficient to exclude them from the build script.

ALWAYS COMMENT OUT ANY VERSION NUMBER THAT IS NOT CHANGING.  This will prevent the creation of additional redundant RPMs on PackageCloud.

## Building locally

Simply update the VERSIONS.txt file and commit. Run `make all`. The rpms build will be in the `pkg` directory.

## Releasing to Package Cloud

Any time a commit is merged on a tracked branch, then a drush RPM is built and pushed up to Package Cloud.

Branch       | Target
------------ | ---------------
master       | pantheon/internal/fedora/#
*            | pantheon/internal-staging/fedora/#

In the table above, # is the fedora build number (22). Note that drush is only installed on app servers, and there are no app servers on anything prior to f22; therefore, at the moment, we are only publishing for f22. Note also that these are noarch RPMs.

To release new versions of drush, simply update the VERSIONS.txt file and create a pull request. The rpm will be build on Circle and deployed to pantheon/internal-staging on PakcageCloud, which will cause it to automatically be deployed to the Yolo environment.  Merge the PR and the rpm will be pushed to pantheon/internal, which will cause it to automatically be deployed to production.

## Provisioning drush on Pantheon

Pantheon will automatically install any new RPM that is deployed to Package Cloud. This is controlled by [pantheon-cookbooks/drush](https://github.com/pantheon-cookbooks/drush/blob/master/recipes/default.rb).
