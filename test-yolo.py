#!/usr/bin/env python
# coding=utf-8

#
# Usage:
#
# Run all tests against drupal 8
#
#   ./test-yolo.py ci-drupal-8
#
# Run all tests against drupal 7
#
#   ./test-yolo.py ci-drupal-7

import os
import pwd
import errno
import pprint
import re
import subprocess
import random
import signal
import sys
import time
import json

import requests
import unittest
import shlex

# pass in site name as an argument to specify a Drupal 7 or Drupal 8 site

siteName = sys.argv[1]
del sys.argv[1]

commandPrefix = "terminus drush "

# drupal7Site = "ci-drupal-7"
# drupal8Site = "ci-drupal-8"


class EnvCacheClearTestCase(unittest.TestCase):
    # Confirm that using the command "terminus env:clear-cache" really does clear the cache by 
    # confirming that the test page gets cached and has a non-zero age, 
    # then running the command and confirming that the age is now 0 (the page has been reset/re-cached)
    def command(self):
        return "terminus env:clear-cache " + siteName + ".dev"

    def getCommandResult(self):
        command = shlex.split(self.command())
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        return output

    def testEnvCacheClear(self):
        print("testEnvCacheClear")
        url = "http://dev-%s.pantheonsite.io/" % siteName
        header = requests.get(url)
        time.sleep(5)
        header = requests.get(url)
        assert header.headers['Age'] != 0
        result = self.getCommandResult()
        assert "Caches cleared" in result
        header = requests.get(url)
        assert int(header.headers['Age']) == 0

class CronTestCase(unittest.TestCase):
    # Confirm that the command "terminus drush cron" succeeds.
    def command(self):
        return commandPrefix + siteName + ".dev" + " cron"

    def getCommandResult(self):
        command = shlex.split(self.command())
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        return output

    def testCron(self):
        print("testCron")
        result = self.getCommandResult()
        assert "Cron run successful." in result


class SiteAuditTestCase(unittest.TestCase):
    # Comfirm that the command "terminus drush aa" successfully runs the site audit tests
    def command(self):
        return commandPrefix + siteName + ".dev" + " aa"

    def getCommandResult(self):
        command = shlex.split(self.command())
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        return output

    def testSiteAudit(self):
        print("SiteAuditTestCase")
        result = self.getCommandResult()
        assert "Best practices" in result
        assert "Block" in result
        assert "Watchdog" in result

class UpdateTestCase(unittest.TestCase):
    # Comfirm that commands "terminus env:deploy --updatedb" and "terminus env:clone" successfully perform updates on the database if needed. 
    # Tested by setting up a fixture site with an old version of a module (easy_breadcrumb) that requires a database updates, then performing the code update and 
    # deploying/cloning to the test environment and checking to confirm that no more database updates are required (implying that the database has been updated)
    def resetRoutine(self):
        #reset the test fixture at the end of every test
        curr = os.getcwd()
        os.chdir(curr + '/%s' % siteName)
        command = shlex.split("terminus --yes env:clone %s.live dev" % siteName)
        subprocess.check_output(command)
        command = shlex.split("terminus --yes env:clone %s.live test" % siteName)
        subprocess.check_output(command)

        command = shlex.split("terminus --yes connection:set %s.dev git" % siteName)
        subprocess.call(command)
        command = shlex.split("git reset --hard reset-test")
        subprocess.check_output(command)
        command = shlex.split("git push origin master -f")
        subprocess.check_output(command)
        command = shlex.split("terminus --yes connection:set %s.dev sftp" % siteName)
        subprocess.call(command)
        command = shlex.split("rm -rf %s" % siteName)
        subprocess.call(command)


    def testUpdateOnDeploy(self):
        print("testUpdateOnDeploy")
        
        # retreive local copy of the repo:
        command = shlex.split("terminus site:info %s --field=id" % siteName)
        siteID = subprocess.check_output(command)
        command = shlex.split("terminus connection:set %s.dev git" % siteName)
        subprocess.call(command)
        command = ['git', 'clone', 'ssh://codeserver.dev.%s@codeserver.dev.%s.drush.in:2222/~/repository.git' % (siteID[:-1], siteID[:-1]), '%s' % siteName]
        subprocess.call(command)
        curr = os.getcwd()
        os.chdir(curr + '/%s' % siteName)

        #set up the site environment:
        if siteName == "ci-drupal-7":
            version = "7.x-2.12"
        else:
            version = "8.x-1.7"

        command = shlex.split("terminus connection:set %s.dev sftp" % siteName)
        subprocess.call(command)
        command = shlex.split("terminus --yes drush -- %s.dev en easy_breadcrumb -y" % siteName)
        subprocess.call(command)
        command = shlex.split("terminus --yes drush -- %s.dev dl easy_breadcrumb-%s -y" % (siteName, version))
        subprocess.call(command)
        command = shlex.split("terminus env:commit %s.dev --message 'easy_breadcrumb'" % siteName)
        subprocess.check_output(command)

        # update the code and database, and deploy to test 
        command = shlex.split("terminus --yes drush -- %s.dev pm-updatecode -y" % siteName)
        subprocess.check_output(command)
        command = shlex.split("terminus env:commit %s.dev --message 'updated code'" % siteName)
        subprocess.check_output(command)
        command = shlex.split("terminus --yes drush -- %s.dev updatedb -y" % siteName)
        subprocess.check_output(command)
        command = shlex.split("terminus env:deploy --updatedb %s.test" % siteName)
        subprocess.check_output(command)

        # test that deploy caused updates
        command = shlex.split("terminus drush %s.test updatedb" % siteName)
        err2 = subprocess.check_output(command, stderr=subprocess.STDOUT)
        assert "No database updates required" in err2

        #reset to original state
        os.chdir(curr)
        self.resetRoutine()

    def testUpdateOnClone(self):
        print("testUpdateOnClone")
        
        # retreive local copy of the dev repo:
        command = shlex.split("terminus site:info %s --field=id" % siteName)
        siteID = subprocess.check_output(command)
        command = shlex.split("terminus connection:set %s.dev git" % siteName)
        subprocess.call(command)
        command = ['git', 'clone', 'ssh://codeserver.dev.%s@codeserver.dev.%s.drush.in:2222/~/repository.git' % (siteID[:-1], siteID[:-1]), '%s' % siteName]
        subprocess.call(command)
        curr = os.getcwd()
        os.chdir(curr + '/%s' % siteName)

        #set up the site environment:
        if siteName == "ci-drupal-7":
            version = "7.x-2.12"
        else:
            version = "8.x-1.7"

        command = shlex.split("terminus connection:set %s.dev sftp" % siteName)
        subprocess.call(command)
        command = shlex.split("terminus --yes drush -- %s.dev en easy_breadcrumb -y" % siteName)
        subprocess.call(command)
        command = shlex.split("terminus --yes drush -- %s.dev dl easy_breadcrumb-%s -y" % (siteName, version))
        subprocess.call(command)

        # update the code, but not the database yet, and deploy to test
        command = shlex.split("terminus --yes drush -- %s.dev pm-updatecode -y" % siteName)
        subprocess.check_output(command)
        command = shlex.split("terminus env:commit %s.dev --message 'updated code'" % siteName)
        subprocess.check_output(command)
        command = shlex.split("terminus env:deploy %s.test" % siteName)
        subprocess.call(command)

        # check that database updates are needed
        command = shlex.split("terminus drush -- %s.test updatedb -n" % siteName)
        test1, err1 = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        print(test1)
        assert "updates" in test1
        assert "pending" in test1
        
        # update the database on dev, clone to test
        command = shlex.split("terminus --yes drush -- %s.dev updatedb -y" % siteName)
        subprocess.call(command)
        command = shlex.split("terminus --yes env:clone %s.dev test" % siteName)
        subprocess.call(command)

        # test that deploy caused updates
        command = shlex.split("terminus drush %s.test updatedb" % siteName)
        err2 = subprocess.check_output(command, stderr=subprocess.STDOUT)
        assert "No database updates required" in err2

        #reset to original state
        os.chdir(curr)
        self.resetRoutine()


class CacheClearTestCase(unittest.TestCase):
    # confirm that the commands "terminus env:deploy --cc" and "terminus env:clone --cc" sucessfully clear the cache by checking 
    # that the AGE header is not zero when the site is initially cached during a GET request, then running the commands with the cache clear
    # flag, then confirming that the AGE is reset to 0 (implying that the cache was cleared)
    def makeMultidev(self):
        command = shlex.split("terminus multidev:create %s.dev temp" % siteName)
        subprocess.call(command)
        command = shlex.split("terminus --yes multidev:merge-from-dev --updatedb %s.temp" % siteName)
        subprocess.check_output(command)

    #note: I think env:deploy --cc doesn't actually clear the cache (looking at workflows doesn't show a cache clearing workflow happening)
    @unittest.skip("Known bug: env:deploy does not clear the cache")
    def testCacheClearOnDeploy():
        makeMultidev()
        url = "http://temp-%s.pantheonsite.io/" % siteName
        header = requests.get(url)
        time.sleep(5)
        header = requests.get(url)
        assert header.headers['Age'] != 0
        command = shlex.split("terminus env:deploy --cc %s.temp" % siteName)
        subprocess.check_output(command)
        header = requests.get(url)
        assert header.headers['Age'] == 0
        command = shlex.split("terminus --yes multidev:delete %s.temp" % siteName)
        subprocess.check_output(command)

    @unittest.skip("Known bug causing appearance of multiple AGE headers: BUGS-2628")
    def testCacheClearOnClone(self):
        print("testCacheClearOnClone")
        self.makeMultidev()
        url = "http://temp-%s.pantheonsite.io/" % siteName
        header = requests.get(url)
        time.sleep(5)
        header = requests.get(url)
        command = shlex.split("terminus --yes env:clone --cc %s.dev temp" % siteName)
        subprocess.check_output(command)
        header = requests.get(url)
        assert int(header.headers['Age']) == 0
        command = shlex.split("terminus --yes multidev:delete %s.temp" % siteName)
        subprocess.check_output(command)

class DrupalAdminLoginLinkTestCase(unittest.TestCase):
    # confirm that the command "terminus drush uli" successfully produces a login URL. Note that this doesn't confirm that the login URL 
    # is correct/works, just that the command works. 
    def command(self):
        return commandPrefix + siteName + ".dev" + " uli"

    def getCommandResult(self):
        command = shlex.split(self.command())
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        return output

    def testDrupalAdminLoginLink(self):
        loginLink = self.getCommandResult()
        assert "http://" in loginLink


if __name__ == "__main__":
    unittest.main()
