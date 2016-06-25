# RPM for drush

This repository builds RPMs for drush.

The RPM filename built by this repository is:
```
drush-x-release-8.1.2-1466798938.2339402.x86_64.rpm
{  name  }-{ type}-{vers}-{iteration}.{ commit }.{arch}.rpm
```
The iteration number is the Circle build number for official builds, and a timestamp (seconds since the epoch) for locally-produced builds. The build script will refuse to make an RPM when there are uncommitted changes to the working tree, since the commit hash is included in the RPM name.

## Install Location

This rpm installs:

/opt/pantheon/drush-x/drush-x/drush.phar

## Releasing to Package Cloud

Any time a commit is merged on a tracked branch, then a drush RPM is built and pushed up to Package Cloud.

Branch       | Target
------------ | ---------------
master       | pantheon/internal/fedora/#
stage        | pantheon/internal-staging/fedora/#

In the table above, # is the fedora build number (19, 20, 22). Note that drush is only installed on app servers, and there are no app servers on anything prior to f22; therefore, at the moment, we are only building for f22.

To release new versions of drush, simply update the VERSIONS.txt file and commit. Run `make` to build locally with docker, or `make with-native-tools` to build without docker. Push to one of the branches above to have an official RPM built and pushed to Package Cloud via Circle CI.

## Provisioning drush on Pantheon

Pantheon will automatically install any new RPM that is deployed to Package Cloud. This is controlled by [pantheon-cookbooks/drush](https://github.com/pantheon-cookbooks/drush/blob/master/recipes/default.rb).

## drush RPM versioning strategy

If drush ever releases a x.x build that accidentally breaks backwards compatibility with old Pantheon sites, then we simply will not install that version until the bug is fixed in a future x.x release.  If drush ever makes a permanent change to the x.x line that breaks backwards compatibility with old Pantheon sites without bumping up its version number, then we will simply need to make a new RPM.
