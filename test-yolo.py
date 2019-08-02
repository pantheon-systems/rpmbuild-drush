#!/usr/bin/env python
# coding=utf-8

#
# Usage:
#
# Run all tests against PHP 7.3:
#
#   ./test-yolo.py ci-drupal-8


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

#drupal7Site = "ci-drupal-7"
#drupal8Site = "ci-drupal-8"

class EnvCacheClearTestCase(unittest.TestCase):
    def fixtureCommand(self):
        return "terminus env:clear-cache " + siteName + ".dev"

    def getFixtureResult(self):
        command = shlex.split(self.fixtureCommand())
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        return output

    def testEnvcacheClear(self):
        print("testEnvcacheClear")
        url = "http://dev-%s.pantheonsite.io/" % siteName
        header = requests.get(url)
        time.sleep(5)
        header = requests.get(url)
        assert header.headers['Age'] != 0
        result = self.getFixtureResult()
        assert "Caches cleared" in result
        header = requests.get(url)
        assert int(header.headers['Age']) == 0

class CronTestCase(unittest.TestCase):

    def fixtureCommand(self):
        return commandPrefix + siteName + ".dev" + " cron"

    def getFixtureResult(self):
        command = shlex.split(self.fixtureCommand())
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        return output

    def testCron(self):
        print("testCron")
        result = self.getFixtureResult()
        assert "Cron run successful." in result


class SiteAuditTestCase(unittest.TestCase):
    def fixtureCommand(self):
        return commandPrefix + siteName + ".dev" + " aa"

    def getFixtureResult(self):
        command = shlex.split(self.fixtureCommand())
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        return output

    def testSiteAudit(self):
        print("SiteAuditTestCase")
        result = self.getFixtureResult()
        assert "Best practices" in result
        assert "Block" in result
        assert "Watchdog" in result

class UpdateTestCase(unittest.TestCase):
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
        command = shlex.split("terminus env:clone %s.dev test" % siteName)
        subprocess.call(command)

        # test that deploy caused updates
        command = shlex.split("terminus drush %s.test updatedb" % siteName)
        err2 = subprocess.check_output(command, stderr=subprocess.STDOUT)
        assert "No database updates required" in err2

        #reset to original state
        self.resetRoutine()


class CacheClearTestCase(unittest.TestCase):
    def makeMultidev(self):
        command = shlex.split("terminus multidev:create %s.dev temp" % siteName)
        subprocess.call(command)
        command = shlex.split("terminus --yes multidev:merge-from-dev --updatedb %s.temp" % siteName)
        subprocess.check_output(command)

    #note: I think env:deploy --cc doesn't actually clear the cache (looking at workflows doesn't show a cache clearing workflow happening)
    # def testCacheClearOnDeploy():
    #     makeMultidev()
    #     url = "http://temp-%s.pantheonsite.io/" % siteName
    #     header = requests.get(url)
    #     time.sleep(5)
    #     header = requests.get(url)
    #     assert header.headers['Age'] != 0
    #     command = shlex.split("terminus env:deploy --cc %s.temp" % siteName)
    #     subprocess.check_output(command)
    #     header = requests.get(url)
    #     assert header.headers['Age'] == 0

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
    def fixtureCommand(self):
        return commandPrefix + siteName + ".dev" + " uli"

    def getFixtureResult(self):
        command = shlex.split(self.fixtureCommand())
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        return output

    def testDrupalAdminLoginLink(self):
        loginLink = self.getFixtureResult()
        assert "http://" in loginLink


if __name__ == "__main__":
    unittest.main()
