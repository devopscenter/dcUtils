#!/usr/bin/env python
"""Docstring for module."""

import sys
import argparse
import json
from os.path import expanduser
# ==============================================================================
__version__ = "0.1"

__copyright__ = "Copyright 2018, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = ' \
   # Copyright 2014-2018 devops.center llc                                    \
   #                                                                          \
   # Licensed under the Apache License, Version 2.0 (the "License");          \
   # you may not use this file except in compliance with the License.         \
   # You may obtain a copy of the License at                                  \
   #                                                                          \
   #   http://www.apache.org/licenses/LICENSE-2.0                             \
   #                                                                          \
   # Unless required by applicable law or agreed to in writing, software      \
   # distributed under the License is distributed on an "AS IS" BASIS,        \
   # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. \
   # See the License for the specific language governing permissions and      \
   # limitations under the License.                                           \
   # '
__status__ = "Development"
# ==============================================================================

class SharedSettings:

    def __init__(self, fileName):
        """Construct an instance to utilize the shared settings file."""
        self.settingsAll = None
        self.customerInfo = []
        self.regionInfo = []
        self.applicationInfo = []
        self.customerInfoNew = {} 
        self.applicationInfoNew = {} 
        self.regionInfoNew = {} 
        self.updatedCustomerInfo = False
        self.updatedApplicationInfo = False
        self.updatedRegionInfo = False
        self.readSharedSettingsFile(fileName)

    def createCustomerInfo(self, name, vcsServiceName = None, vcsAccountName = None):
        self.updatedCustomerInfo = True
        self.customerInfoNew["Name"] = name
        if vcsServiceName:
            self.customerInfoNew["VCSServiceName"] = vcsServiceName,
        if vcsAccountName:
            self.customerInfoNew["VCSAccountName"] = vcsAccountName
    
    def addCustomerVCSInfo(self, vcsServiceName, vcsAccountName):
        self.updatedCustomerInfo = True
        self.customerInfoNew["VCSServiceName"] = vcsServiceName
        self.customerInfoNew["VCSAccountName"] = vcsAccountName

    def getCustomerInfo(self):
        if "Customer" in self.settingsAll:
            return self.customerInfo

    def getCustomerName(self):
        if "Customer" in self.settingsAll:
            return self.customerInfo["Name"]

    def getCustomerVCSServiceName(self):
        if "Customer" in self.settingsAll:
            if "VCSServiceName" in self.customerInfo:
                return self.customerInfo["VCSServiceName"]
            else:
                return None

    def getCustomerVCSAccountName(self):
        if "Customer" in self.settingsAll:
            if "VCSAccountName" in self.customerInfo:
                return self.customerInfo["VCSAccountName"]
            else:
                return None

    def listApplications(self):
        """Return the list customer's application names."""
        retArray = []
        for item in self.applicationInfo:
            retArray.append(item['Name'])
        return retArray
    
    def getApplicationInfo(self, app):
        """Return all the information associated with the specified application."""
        appInfo = None
        for item in self.applicationInfo:
            if item["Name"] == app:
                appInfo = item
        return appInfo
    
    def addApplicationInfo(self, name,  utilsRepo, appRepoList, vcsServiceName = None, vcsAccountName = None):
        """Adds the items that make up the application info."""
        self.updatedApplicationInfo = True
        self.applicationInfoNew["Name"] = name
        self.applicationInfoNew["UTILS_REPO"] = utilsRepo
        if isinstance(appRepoList, basestring):
            # make sure it is an array
            self.applicationInfoNew["APP_REPO"] = [ appRepoList ]
        else:
            self.applicationInfoNew["APP_REPO"] = appRepoList
        if "Shared" in utilsRepo: 
            self.applicationInfoNew["shared"] = "true"
        if vcsServiceName:
            self.applicationInfoNew["VCSServiceName"] = vcsServiceName,
        if vcsAccountName:
            self.applicationInfoNew["VCSAccountName"] = vcsAccountName

    def getApplicationRepoList(self, app):
        """Return the list of application repository URLs for a given application."""
        anItem = self.getApplicationInfo(app)
        if anItem:
            return anItem["APP_REPO"]
        else:
            return None

    def getUtilitiesRepo(self, app):
        """Return the utilities repository URL for a given application."""
        anItem = self.getApplicationInfo(app)
        if anItem:
            return anItem["UTILS_REPO"]
        else:
            return None
    
    def isShared(self, app):
        """Return where this app is using shared utilizies."""
        anItem = self.getApplicationInfo(app)
        if anItem:
            if anItem["shared"] == "true":
                return True
            else:
                return False
        else:
            return False
    
    def getVCSServiceName(self, app=None):
        """Return the version control system service name for this application."""
        if app:
            anItem = self.getApplicationInfo(app)
            if anItem:
                # NOTE: the service name can be defined in the Customer info section so
                # it could be possible that it is not be duplicated in the app section
                if "VCSServiceName" in anItem:
                    return anItem["VCSServiceName"]
                else:
                    return None
        else:
            if "VCSServiceName" in self.customerInfo:
                return self.customerInfo["VCSServiceName"]
            else:
                return None

    def getVCSAccountName(self, app=None):
        """Return the version control system accountname for this application."""
        anItem = self.getApplicationInfo(app)
        if app:
            if anItem:
                # NOTE: the service name can be defined in the Customer info section so
                # it could be possible that it is not be duplicated in the app section
                if "VCSAccountName" in anItem:
                    return anItem["VCSAccountName"]
                else:
                    return None
        else:
            if "VCSAccountName" in self.customerInfo:
                return self.customerInfo["VCSAccountName"]
            else:
                return None

    def readSharedSettingsFile(self, fileName):
        """Read in the shared settings file."""
        try:
            with open(expanduser(fileName)) as data_file:
                self.settingsAll = json.load(data_file)
                if 'Customer' in self.settingsAll:
                    self.customerInfo = self.settingsAll['Customer']
                if 'Applications' in self.settingsAll:
                    self.applicationInfo = self.settingsAll['Applications']
                if 'Regions' in self.settingsAll:
                    self.regionInfo = self.settingsAll['Regions']
        except IOError as e:
            print("ERROR trying to read the shared settings file")
            print("Shared dcConfig settings file error: {}".format(e))
            sys.exit(1)
        
    def checkCustomerInfo(self):
        """Check to see what has changed and make a merged section."""
        tmpCusInfo = {}
        # Name
        tmpCusInfo["Name"] = self.customerInfoNew["Name"] if self.customerInfoNew["Name"] != self.customerInfo["Name"] else  self.customerInfo["Name"]

        # VCSServiceName
        tmpCusInfo["VCSServiceName"] = self.customerInfoNew["VCSServiceName"] if self.customerInfoNew["VCSServiceName"] != self.customerInfo["VCSServiceName"] else self.customerInfo["VCSServiceName"]

        # VCSAccountName
        tmpCusInfo["VCSAccountName"] = self.customerInfoNew["VCSAccountName"] if self.customerInfoNew["VCSAccountName"] != self.customerInfo["VCSAccountName"] else self.customerInfo["VCSAccountName"]
        
        self.writeSettingsAll['Customer'] = tmpCusInfo

    def checkApplicationInfo(self):
        """Check to see what has changed and make a merged section."""
        tmpAppList = []
        for anApp in self.applicationInfo:
            if self.applicationInfoNew["Name"] != anApp["Name"]:
                tmpAppList.append(anApp)

        tmpAppInfo = {}
        # Name
        tmpAppInfo["Name"] = self.applicationInfoNew["Name"] 

        # VCSServiceName
        if "VCSServiceName" in self.applicationInfoNew:
            tmpAppInfo["VCSServiceName"] = self.applicationInfoNew["VCSServiceName"] 

        # VCSAccountName
        if "VCSAccountName" in self.applicationInfoNew:
            tmpAppInfo["VCSAccountName"] = self.applicationInfoNew["VCSAccountName"]

        # shared
        tmpAppInfo["shared"] = self.applicationInfoNew["shared"]

        # UTILS_REPO
        tmpAppInfo["UTILS_REPO"] = self.applicationInfoNew["UTILS_REPO"]

        # APP_REPO
        tmpAppInfo["APP_REPO"] = self.applicationInfoNew["APP_REPO"]

        tmpAppList.append(tmpAppInfo)

        self.writeSettingsAll['Applications'] = tmpAppList

    def checkRegionInfo(self):
        """Check to see what has changed and make a merged section."""
        if self.regionInfo:
            self.writeSettingsAll['Regions'] = self.regionInfo

    def writeSharedSettingsFile(self, fileName):
        """Write the shared settings file with any new updated information."""
        if self.updatedCustomerInfo or self.updatedApplicationInfo or self.updatedRegionInfo:
            # now check each section and merge into a new writeable data structure
            self.writeSettingsAll = {}
            self.checkCustomerInfo()
            self.checkApplicationInfo()
            self.checkRegionInfo()
            
            # now convert the structure to json and write the file
            with open(expanduser(fileName), 'w') as outfile:
                json.dump(self.writeSettingsAll, outfile, indent = 2, ensure_ascii = False)

        else:
            print("Nothing updated, not writing.")


def checkArgs():
    """Check the command line arguments."""
    parser = argparse.ArgumentParser(
        description=('comment'))
    parser.parse_args()

def testSharedSettings(theSettings):
    """Get the values from the settings file."""
    print("Customer info: {}").format(theSettings.getCustomerInfo())
    print("Applications: {}").format(theSettings.listApplications())
    print("Customer level VCS service: {}").format(theSettings.getVCSServiceName())
    print("Customer level VCS account: {}").format(theSettings.getVCSAccountName())
    
    for theApp in theSettings.listApplications():
        print("VCS service:[{}] {}").format(theApp, theSettings.getVCSServiceName(theApp))
        print("VCS account:[{}] {}").format(theApp, theSettings.getVCSAccountName(theApp))
        if theSettings.isShared(theApp):
            print("Shared utilities found at {}").format(theSettings.getUtilitiesRepo(theApp))
        else:
            print("NOT using the shared utilities facility.")

        print("The list of application repos is:")
        for item in theSettings.getApplicationRepoList(theApp):
            print("\t{}").format(item)


def main(argv):
    """Main code goes here."""
    checkArgs()

    commonSharedSettingsFile = "~/devops/testscripts/python-stuff/shared-settings/settings.json"
    theSettings = SharedSettings(commonSharedSettingsFile)
    testSharedSettings(theSettings)

# If you want to see how to add new information
#    outputSettingsFile = "~/devops/testscripts/python-stuff/shared-settings/settings-new.json"
#    print("Now create a new customer info section")
#    theSettings.createCustomerInfo("clEAR")
#    theSettings.addCustomerVCSInfo("newGitService", "clearsys")
#
#    print("Now create an all new set of application information")
#    theSettings.addApplicationInfo("moonride", "git@github.com:quasarsys/dcSharedUtils.git", 
#                                   "git@github.com:quasarsys/moonride")
#
#    theSettings.writeSharedSettingsFile(outputSettingsFile)


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

