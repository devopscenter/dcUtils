#!/usr/bin/env python
import sys
import os
import argparse
from argparse import RawDescriptionHelpFormatter
import subprocess
import json
# from time import time
# import fileinput
# import re
from scripts.process_dc_env import pythonGetEnv
# ==============================================================================
"""
After an update and push to the application repository the code on the
instance  needs have it's code updated from the repository. This script will
perform the necessary actions to get the destination compoonent up to date.
"""
__version__ = "0.1"

__copyright__ = "Copyright 2016, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================
# NEED TO READ IN appArchitecture that was used to build the instance
# we are about to upate.  There are to many variables that are already
# defined that we wouldn't have to define again.  Also, this would imply
# that the file would be put in the customers appUtils (say in config/$ENV)
# and have it read only to make it give language that says hey while I know
# you can change this but it wasn't meant to be modified.  devops.center
# owns the master and this is for reference only


class UpdateInstance:

    def __init__(self, theAppName, theEnv, Destination, theConfigFile,
                 accessKey, pathToKeys, test):

        """UpdateComponent constructor"""

        self.appName = theAppName
        self.env = theEnv
        self.dest = Destination
        self.targetUser = "ubuntu"
        self.accessKey = accessKey
        self.pathToKeys = pathToKeys
        self.test = test
        self.configList = self.readConfigFile(theConfigFile)

    def run(self):
        # first remove the log file from a previous run if it exists
        logFile = "create-instance.log"
        if not self.test:
            logFileAndPath = "ec2/" + logFile
            if os.path.isfile(logFileAndPath):
                os.remove(logFileAndPath)

        # go through each element found in the configList
        for component in self.configList:
            componentInfo = component[0]
            componentItem = component[1]

            numberToCreate = 1

            # go through the environemnt variables and print them out
            print "Environment Variables for the component:\n"
            for item in componentInfo.keys():
                print "{}={}\n".format(item, componentInfo[item]),

            # now print out the elements for the component
            if componentItem["type"] == 'db':
                print ("Name=" + componentItem["name"] + " "
                       "Number=" + str(numberToCreate) + " "
                       "Version=" + self.appName + " "
                       "Environment=" + componentInfo["ENVIRONMENT"] + " "
                       "Type=" + componentItem["type"] + " "
                       "Role=" + componentItem["ROLE"] + " ")
            else:
                print ("Name=" + componentItem["name"] + " "
                       "Number=" + str(numberToCreate) + " "
                       "Version=" + self.appName + " "
                       "Environment=" + componentInfo["ENVIRONMENT"] + " "
                       "Type=" + componentItem["type"] + " ")

            # and now print out the separate components and their count
            if componentItem["type"] == 'db':
                print ("\nThere will be " + str(numberToCreate) +
                       " instances of type: " + componentItem["type"] + " "
                       "and role: " + componentItem["ROLE"])
            else:
                print ("\nThere will be " + str(numberToCreate) +
                       " instances of type: " + componentItem["type"] + " ")
        # set up the cmd to run
        cmdToRun = self.buildCmdToRun(componentInfo, "updateAppInstance")

        # and now execute it
        if self.test:
            print "Command to Run: \n" + cmdToRun
        else:
            print "Running this command: \n" + cmdToRun
            subprocess.call(cmdToRun, shell=True)

    def buildCmdToRun(self, componentInfo, optionToAdd):
        cmdToRun = "cd scripts; ./updateApp.sh"
        cmdToRun += " --accessKey " + self.accessKey
        cmdToRun += " --destination " + self.dest
        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
                                     "APPNAME", "appName")
        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
                                     "PROFILE", "profile")
        cmdToRun = self.addToCommand(cmdToRun, componentInfo, "REGION",
                                     "region")
        cmdToRun = self.addToCommand(cmdToRun, componentInfo, "ROLE",
                                     "role")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "BACKUP_S3_REGION",
#                                     "backupS3Region")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "AVAILABILITYZONE", "az")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo, "VPCID",
#                                     "vpcid")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "SUBNETID", "subnetid")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "CIDR_BLOCK", "cidrBlock")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "CUSTWEBGITBRANCH",
#                                     "custwebgitbranch")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "DCSTACK_GITBRANCH",
#                                     "dcstackgitbranch")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "UTILSGITBRANCH",
#                                     "utilsgitbranch")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "DBNAME", "dbname")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "BACKUPFILE", "backupfile")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "PGVERSION", "pgversion")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "STACK", "stack")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "UTILS", "utils")
#    CUSTOMER_UTILS has the git string
        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
                                     "CUSTOMER_UTILS", "gitString")
        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
                                     "CUSTUTILSGITBRANCH",
                                     "custutilsgitbranch")
        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
                                     "DEPLOYMENT_KEYPAIR", "deploykey")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "DNS_METHOD", "dns")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "REDIS", "redis")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "REDISFOLLOWER", "redisfollower")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "ROUTE53ZONE", "route53zone")
        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
                                     "ENVIRONMENT", "env")
        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
                                     "LOCAL_KEYPAIR_DIR",
                                     "localKeyPairDir")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "LOCAL_KEYPAIR",
#                                     "localKeyPair")
#        cmdToRun = self.addToCommand(cmdToRun, componentInfo,
#                                     "COMBINED_WEB_WORKER",
#                                     "combinedWebWorker")
#

        return cmdToRun

    def addToCommand(self, string, componentInfo, aKey, cmdOption):
        returnStr = string
        if componentInfo[aKey]:
            keyValue = ""
            if isinstance(componentInfo[aKey], (int, long)):
                keyValue = str(componentInfo[aKey])
            else:
                keyValue = componentInfo[aKey]

            returnStr += " --" + cmdOption + " " + keyValue
        return returnStr

    def readConfigFile(self, aConfigFile):
        """read the json config file and return a List of the elements found
        defined in the file"""

        # first read in the file
        data = []
        with open(aConfigFile) as data_file:
            data = json.load(data_file)

        # now parse the data and make the list of components
        returnList = []

        # going through the components need to check if there is an
        # variable that needs to overwrite one of the default ones
        for item in data["components"]:
            # a single element in the list will consist of the component-info
            # and the component details, all of which are just key value pairs
            componentInfo = dict(data["component-info"])

            # overwrite the appropriate variables with the appropriate command
            # line version of the options
            # componentInfo["PROFILE"] = self.appName
            if self.env:
                componentInfo["ENVIRONMENT"] = self.env

            if "type" in item:
                componentInfo["SUFFIX"] = item["type"]

            if "ROLE" in item:
                componentInfo["ROLE"] = item["ROLE"]

            if "DEPLOYMENT_KEYPAIR" in componentInfo:
                # need to get the "keys' path and create new
                pathAndDeployKey = self.pathToKeys + "/" + \
                    componentInfo["DEPLOYMENT_KEYPAIR"]
                componentInfo["DEPLOYMENT_KEYPAIR"] = pathAndDeployKey

            if "LOCAL_KEYPAIR" in componentInfo:
                componentInfo["LOCAL_KEYPAIR_DIR"] = self.pathToKeys

            for aKey in item.keys():
                if aKey in componentInfo:
                    componentInfo[aKey] = item[aKey]
                else:
                    componentInfo[aKey] = item[aKey]

            returnList.append((componentInfo, item))

        return returnList


def checkArgs():
    parser = argparse.ArgumentParser(
        description='This script provides an administrative interface to a ' +
        'customers application to perform an update on a target instance. ' +
        'Once the configuration has been ' +
        'changed and committed to the respository, call this script to ' +
        'have the code be updated on the instance. \n\n'

        'Example cmd line to update an application with a new environment:\n'
        './updateAppInstance.py --baseDirectory ~/someDir/YourAppDir\n'
        '            --appName YourApp\n'
        '            --command update\n'
        '            --option "newEnv = UAT"\n',

        formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-c', '--configFile', help='The json config file ' +
                        'that defines the architecture for the appName',
                        required=True)
    parser.add_argument('-d', '--destination', help='The target instance to ' +
                        'have the update performed on.',
                        required=True)
    parser.add_argument('-x', '--accessKey', help='the access key to get to ' +
                        'the instance.',
                        required=True)
    parser.add_argument('-t', '--test', help='Will run the script but ' +
                        'will not actually execute the shell commands.' +
                        'Think of this as a dry run or a run to be used' +
                        ' with a testing suite',
                        action="store_true",
                        required=False)

    try:
        args, unknown = parser.parse_known_args()
    except SystemExit:
        pythonGetEnv()
        sys.exit(1)

    retEnvList = pythonGetEnv()

    retTest = ""
    if args.test:
        retTest = args.test
        print "testing: True"

    retConfigFile = args.configFile

    if retEnvList["CUSTOMER_APP_NAME"]:
        retAppName = retEnvList["CUSTOMER_APP_NAME"]

    if retEnvList["ENV"]:
        retEnv = retEnvList["ENV"]

    if not os.path.isfile(retConfigFile):
        print 'ERROR: Unable to find config file: ' + retConfigFile + "\n"
        sys.exit(1)

    # get the key path in case we need it
    keyPath = retEnvList["BASE_CUSTOMER_DIR"] + '/' + \
        retEnvList["dcDEFAULT_APP_NAME"] + '/' + \
        retEnvList["CUSTOMER_APP_UTILS"] + "/keys/"

    retAccessKey = keyPath + retEnvList["CUSTOMER_APP_ENV"] + '/' + \
        retEnvList["dcDEFAULT_APP_NAME"] + '-' + \
        retEnvList["CUSTOMER_APP_ENV"] + "-access.pem"

    for file in os.listdir(keyPath):
        if file.endswith(".pub"):
            retDeployKey = file.replace(r".pub", '')
            break

    if not retDeployKey:
        print "ERROR: The deploy key can not be determined " \
                "automatically you will need to pass the name " \
                "with the option --deployKey(-k)."

    retDest = args.destination

    # if we get here then the
    return (retAppName, retEnv, retDest, retConfigFile, retAccessKey, keyPath,
            retTest)


def main(argv):
    (appName, env, dest, configFile, accessKey, keyPath, test) = checkArgs()

    if test:
        print 'appName is: {}'.format(appName)
        print 'configFile is: {}'.format(configFile)
        print 'the env is: {}'.format(env)
        print 'running in testing mode'
        print "destination is: {}".format(dest)
        print "path for keys: {}".format(keyPath)

    customerApp = UpdateInstance(appName, env, dest, configFile, accessKey,
                                 keyPath, test)
    customerApp.run()


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
