#!/usr/bin/env python

"""This is a generic environment reader."""
# =============================================================================
#
#          FILE: process_dc_env.py
#
#         USAGE: process_dc_env.py
#
#   DESCRIPTION: customer appName specific that will drop the indexes
#                identified by the CREATE INDEX lines in the customer
#                appname .sql file
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/21/2016 15:13:37
#      REVISION:  ---
#
# Copyright 2014-2017 devops.center llc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# =============================================================================

import sys
import logging
import os
from os.path import expanduser
import argparse
import subprocess
# ==============================================================================
"""
process_dc_env.py process the arguments and passes them back to put them in the
environment along with other environment variables defined in .env files.
"""
__version__ = "0.2"

__copyright__ = "Copyright 2016-2022, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================


class Process_dc_Env:
    """Process reading in the environment file."""

    def __init__(self, envList, generateEnvFiles=0, forCustomer=None):
        """Constructor for process_dc_env class."""
        self.envList = envList
        self.baseDir = ""
        self.baseAppName = ""
        self.dcBaseConfig = ""
        self.baseAppUtilsDir = ""
        self.forCustomer = forCustomer
        if generateEnvFiles:
            self.generateEnvFiles = True
        else:
            self.generateEnvFiles = False

    def getdcUtilsDirectory(self):
        """Read the utils directory."""
        # read the ~/.dcConfig/settings
        baseSettingsDir = expanduser("~") + "/.dcConfig"
        if not os.path.exists(baseSettingsDir):
            print("You seem to be missing the $HOME/.dcConfig directory,"
                  "you will need to run the RUN-ME-FIRST.sh script that "
                  "established that directory and the settings file that"
                  "contains the initial base directory for you application"
                  "development and where dcUtils is installed.")
            sys.exit(1)

        if os.path.isfile(baseSettingsDir + "/settings"):
            # get the base directory from the settings file
            with open(baseSettingsDir + "/settings") as f:
                lines = [line.rstrip('\n') for line in f]
            for item in lines:
                if "dcUTILS" in item:
                    lineArray = item.split('=')
                    dcUtilsDir = lineArray[1]
                    return(dcUtilsDir)

        # otherwise return current dir
        # this works for the scripts executed from the  dcUtils directory.
        # otherwise make sure it is in your environment
        return(os.getcwd())

    def process_dc_env(self):
        """Process the environment files."""
        # ---------------------------------------------------------------------
        # lets check to see if dcUtils has been set already if not then we are
        #  probably the first time through and it hasn't been set in the
        # environment, so we assume we are in the directory
        # ---------------------------------------------------------------------
        dcUtils = os.getenv("dcUTILS")
        if not dcUtils:
            dcUtils = self.getdcUtilsDirectory()
        self.envList["dcUTILS"] = dcUtils

        # ---------------------------------------------------------------------
        # First we need to get the base location of the customers files.  This
        # was created when the manageApp.py was run as one of the arguments is
        # the directory and it should be an absolute path
        # ---------------------------------------------------------------------
        self.dcBaseConfig = expanduser("~") + "/.dcConfig/baseDirectory"

        # ---------------------------------------------------------------------
        #  get the base directory from the .dcConfig/baseDirectory
        # ---------------------------------------------------------------------
        self.getBaseDir()

        # ---------------------------------------------------------------------
        #  Next get the baseAppName
        # ---------------------------------------------------------------------
        self.getBaseAppName()

        # ---------------------------------------------------------------------
        #  Next get the base App Utilities directory by reading the
        #  .dcDirMap.cnf
        # ---------------------------------------------------------------------
        self.baseAppUtilsDir = self.getBaseAppUtils()

        # ---------------------------------------------------------------------
        # go read the ~/.dcConfig/settings file for any variables we need from
        # there.  Like the customer name
        # ---------------------------------------------------------------------
        getSettings(self.envList)

        # ---------------------------------------------------------------------
        # Need to find what dcEnv files that are in the directory.  We need to
        # get the possible appNames if there is more than one.  And then get
        # any environment (ie, dev, staging, prod, local) files if there are
        # more than one. If it doesn't exist exit and instruct the user to run
        # deployenv.sh
        # ---------------------------------------------------------------------
        if not self.generateEnvFiles:
            self.getEnvFile()

            # -----------------------------------------------------------------
            # check for the DEFAULT_APP_NAME. If not given set it to the
            # appname from the input.  If the --appName is not given then
            # check the # one from the env and make sure it is not the
            # __DEFAULT__ one.
            # -----------------------------------------------------------------
            # if self.envList["dcDEFAULT_APP_NAME"] == "__DEFAULT__":
            #    print ("The dcDEFAULT_APP_NAME environment variable has not "
            #            +
            #           "been set and has not been made available. This " +
            #           "should be identified when running deployenv.sh by " +
            #           "utilizing the option: --appName appname")
            #    sys.exit(1)

        return self.envList

    def getBaseDir(self):
        """Get the base directory."""
        if os.path.exists(self.dcBaseConfig):
            if "WORKSPACE_NAME" in self.envList:
                # open the dcConfig/baseDirectory and read it in directly
                # as we are looking for the alternate workspace name
                with open(self.dcBaseConfig) as f:
                    lines = [line.rstrip('\n') for line in f]

                flagFound = 0
                itemToLookFor = "_" + self.envList["WORKSPACE_NAME"] + \
                                "_BASE_CUSTOMER_DIR="
                for line in lines:
                    if itemToLookFor in line:
                        key, value = line.split('=', 1)
                        self.baseDir = value
                        self.envList["BASE_CUSTOMER_DIR"] = self.baseDir
                        flagFound = 1
                        break

                if not flagFound:
                    print("Could not find a directory for the given " +
                          "--workspaceName value in the " +
                          "$HOME/.dcConfig/baseDirectory. \nHave you run " +
                          "manageApp.py with the --workspaceName to create " +
                          "an alternate base directory?")
                    sys.exit(1)
            else:
                with open(self.dcBaseConfig) as f:
                    lines = [line.rstrip('\n') for line in f]
                workspaceName = ''
                for item in lines:
                    if "CURRENT_WORKSPACE" in item:
                        lineArray = item.split('=')
                        workspaceName = '_' + lineArray[1] + \
                                        '_BASE_CUSTOMER_DIR'

                    if workspaceName in item:
                        anotherLineArray = item.split('=')
                        self.baseDir = anotherLineArray[1]
                        self.envList["BASE_CUSTOMER_DIR"] = self.baseDir
                        return
        else:
            print("ERROR: can not determine the base directory as it "
                  "does not appear that you have run manageApp.py to "
                  "set up your application.  This must be done before "
                  "you can run this script.")
            sys.exit(1)

    def getBaseAppName(self):
        """Get the base name for the application."""
        subDirs = next(os.walk(self.baseDir))[1]

        if len(subDirs) == 0:
            print("The base directory defined in "
                  "$HOME/.dcConfig/basedirectory "
                  "does not have any directories in it.  There is "
                  "configuration issue in that file  you may need to run "
                  "manageApp.py again.")
            sys.exit(1)

        elif len(subDirs) == 1:
            if "CUSTOMER_APP_NAME" in self.envList:
                if subDirs[0] != self.envList["CUSTOMER_APP_NAME"]:
                    print("The appName you provided: " +
                          self.envList["CUSTOMER_APP_NAME"] + " was not " +
                          "found in the base directory: " + self.baseDir)
                    sys.exit(1)
                else:
                    self.baseAppName = self.envList["CUSTOMER_APP_NAME"]
            else:
                self.baseAppName = subDirs[0]
                self.envList["CUSTOMER_APP_NAME"] = self.baseAppName
        else:
            self.handleMultipleDirectories(subDirs)
            # print "baseAppName= " + baseAppName

    def handleMultipleDirectories(self, subDirs):
        """Handle the situation when there are multiple apps."""
        if "CUSTOMER_APP_NAME" in self.envList:
            foundFlag = 0
            for dir in subDirs:
                if dir == self.envList["CUSTOMER_APP_NAME"]:
                    self.baseAppName = self.envList["CUSTOMER_APP_NAME"]
                    foundFlag = 1
                    break

            if not foundFlag:
                print("The appName you provided: " +
                      self.envList["CUSTOMER_APP_NAME"] + " was not found " +
                      "in the base directory: " + self.baseDir)
                sys.exit(1)
        else:
            print("Found multiple applications so you will need to provide " +
                  "the appropriate option (usually --appName) for " +
                  "this script to be able to pass the application name.")
            print("The applications found are:\n")
            for filename in subDirs:
                print(filename)
            print("\n")
            sys.exit(1)

    def getBaseAppUtils(self):
        """Get the application utils."""
        appDir = self.baseDir + "/" + self.baseAppName
        subDirMapFile = appDir + "/" + ".dcDirMap.cnf"
        if os.path.exists(subDirMapFile):
            with open(subDirMapFile) as f:
                lines = [line.rstrip('\n') for line in f]

            for line in lines:
                key, value = line.split('=', 1)
                self.envList[key] = value
                if key == "CUSTOMER_APP_UTILS":
                    if self.forCustomer:
                        retBaseAppUtils = self.baseDir + "/" + \
                            self.baseAppName + "/" + value + "/" + \
                            self.forCustomer
                    elif value == "dcShared-utils":
                        retBaseAppUtils = self.baseDir + "/" + \
                            self.baseAppName + "/" + value
                    else:
                        retBaseAppUtils = self.baseDir + "/" + \
                            self.baseAppName + "/" + value

        else:
            print("Can not read the " + subDirMapFile + " file in the base" +
                  " application directory, have you run manageApp.py yet? ")
            sys.exit(1)

        return retBaseAppUtils

    def getEnvFile(self):
        """Get the Environment file."""
        # check for a dcEnv-${CUSTOMER_APP_NAME}-*.sh file
        envDirToFind = self.baseAppUtilsDir + \
            "/environments/.generatedEnvFiles"
        envFiles = next(os.walk(envDirToFind))[2]

        # if one doesn't exist instruct the user to run deployenv.sh with that
        # app name and try this again and then exit
        # if len(envFiles) == 0 or "dcEnv" not in envFiles[0]:
        if len(envFiles) == 0:
            print("There does not appear to be any env files available " +
                  "for the given appName: " + self.baseAppName + ". " +
                  "You will need to create one by executing the " +
                  "deployenv.sh with the appName")
            sys.exit(1)

        # there is at least a pair there, so now go through the list and
        # look for the application specific env files.  If there, there
        # will be two one each one for .env and .sh and the one we want
        # is the .sh
        flagFound = 0
        for file in envFiles:
            envFileName = "dcEnv-" + self.baseAppName + "-" + \
                self.envList["ENV"] + ".env"
            shEnvFileName = "dcEnv-" + self.baseAppName + "-" + \
                self.envList["ENV"] + ".sh"

            if shEnvFileName in file:
                # found the one needed
                flagFound = 1
                theEnvFileNameToSource = file
                break

        if not flagFound:
            # if there is more than one file (ie, different ENVs) then display
            # the list and ask for the user to select one.
            print("There are multiple sets of environment files with that " +
                  "appName. The difference \nbetween the files is the " +
                  "environment portion. This is one of local, dev, " +
                  "staging \nor prod.  Look at the list below and you will " +
                  "need to know the environment that \nyou want to run in." +
                  " Re-run this script and give the appropriate option to " +
                  "\ndesiginate the env (usually --env) and provide the " +
                  "environment string. \nThe env files found are:")
            for filename in envFiles:
                if "dcEnv-" in filename:
                    print(filename)

            sys.exit(1)
        else:
            # source the .sh env file into the environment as it has the export
            # variables and that will set the environment
            fileToSource = envDirToFind + "/" + theEnvFileNameToSource
            command = '/usr/bin/env bash -c "source ' + fileToSource + \
                      ' && env"'

            try:
                tmpOutput = subprocess.check_output(command,
                                                    stderr=subprocess.STDOUT,
                                                    shell=True)

                theWholeEnv = tmpOutput.split(b'\n')
                # -------------------------------------------------------------
                # now go through the whole environment and only get the ones
                # that are in the envFile that we sourced
                # how this happens is that the sourcing command above spits
                # out the entire environment at that time.  So that will have a
                # bunch of extra  variables that we don't need.  What we need
                # are the keys from the file, so we will read through the file
                # and pull the keys and then match up the sourced value to the
                # needed key.
                # With that, make the dict all str (part of the python 3 update)
                # -------------------------------------------------------------
                theEnvFileToRead = envDirToFind + "/" + envFileName
                with open(theEnvFileToRead, 'rb') as f:
                    lines = [line.rstrip(b'\n') for line in f]

                for line in lines:
                    needKey, needValue = line.split(b'=', 1)
                    for envVar in theWholeEnv:
                        if needKey in envVar:
                            lookKey = needKey.decode()
                            lookValue = needValue.decode()
                            self.envList[lookKey] = lookValue
            except subprocess.CalledProcessError:
                logging.exception("There was an issue with sourcing " +
                                  fileToSource)


def getSettings(anEnvList):
    """Read the ~/.dcConfig/settings file."""
    baseSettingsFile = expanduser("~") + "/.dcConfig/settings"
    with open(baseSettingsFile, 'r') as f:
        lines = [line.rstrip('\n') for line in f]

    for aLine in lines:
        if "CUSTOMER_NAME=" in aLine:
            anEnvList["CUSTOMER_NAME"] = aLine.split("=")[1]
        if "PROFILE=" in aLine:
            anEnvList["PROFILE"] = aLine.split("=")[1]
        if "REGION=" in aLine:
            anEnvList["REGION"] = aLine.split("=")[1]
        if "USER_NAME=" in aLine:
            anEnvList["USER_NAME"] = aLine.split("=")[1]
        if "dcCOMMON_SHARED_DIR=" in aLine:
            anEnvList["dcCOMMON_SHARED_DIR"] = aLine.split("=")[1]


def pythonGetEnv(initialCreate=False, forCustomer=None):
    """Process env when called from a python script."""
    envList = dcEnvCheckArgs()

    if forCustomer is None:
        if "FOR_CUSTOMER" in envList:
            forCustomer = envList["FOR_CUSTOMER"]

    if initialCreate:
        getSettings(envList)
        returnEnvList = envList
    else:
        anEnv = Process_dc_Env(envList, forCustomer=forCustomer)
        returnEnvList = anEnv.process_dc_env()

    return returnEnvList


def shellGetEnv():
    """Process env when called via a shell script."""
    (envList, initialCreate, generateEnvFiles) = dcEnvCheckArgs(type=1)

    customerNameToSpecialize = None
    if "FOR_CUSTOMER" in envList:
        customerNameToSpecialize = envList["FOR_CUSTOMER"]

    print('initialCreate',initialCreate,'\n')

    if initialCreate:
        returnEnvList = envList
    else:
        anEnv = Process_dc_Env(envList, generateEnvFiles,
                               forCustomer=customerNameToSpecialize)
        returnEnvList = anEnv.process_dc_env()

    returnStr = "export"
    for key, value in returnEnvList.items():
        if '\"' in value or '\'' in value:
            returnStr += " " + key + '=' + value
        else:
            returnStr += " " + key + '="' + value + '"'

    curDir = os.path.dirname(sys.argv[0])
    with open(curDir + '/shellfunctions.incl', 'r') as includeFile:
        data = includeFile.read()

    returnStr += " ; {}".format(data)
    print(returnStr)


def dcEnvCheckArgs(type=0):
    """Check the arguments passed into this script."""
    parser = argparse.ArgumentParser(
        description='The core argument processing is handled by a separate '
        'process (process_dc_env.py) and is called by this script.  This core '
        'process will ensure that there is an environment file that is set '
        'and can be utilized for the running of this session.  The intent of '
        'this script is that it would be put at the top of any devops.center '
        'scripts that will need the full application environment to ensure '
        'that the environment variables that are needed will be available to '
        'the script.  This is done to help avoid polluting the users '
        'environment. Another main purpose of this is to be able to isolate '
        'sessions such that a user could run one app in terminal session '
        'and a second one in parallel in a separate terminal '
        'session while using the same code.')

    parser.add_argument('-a', '--appName', help='The application name'
                        'of the application that you want to run as the '
                        'default app for the current session.  This is '
                        'optional as by default the appName will be set '
                        'when deployenv.sh is run',
                        required=False)
    parser.add_argument('-e', '--env', help='the env is one of local, dev, '
                        'staging, prod. DEFAULT: local',
                        default='local',
                        required=False)
    parser.add_argument('-w', '--workspaceName',
                        help='A unique name that identifies an alternate '
                        'workspace. By default only one base directory is '
                        'created and all applications created are put into '
                        'that directory. By specifying this option an '
                        'alternate base directory can be identified and it '
                        'will be kept separate from any other base  '
                        'directories. One usage is if you have multiple '
                        'clients that you are building apps for then the '
                        'apps can be in separate base directories '
                        '(essentially applications associated by client)'
                        'with this option.',
                        required=False)
    parser.add_argument('-i', '--initialCreate',
                        # help='The flag to say ' +
                        # 'that this is being invoked by a start up script'
                        # 'NOTE: if it came in this way it came from a shell'
                        # 'script and probably should not be run this way',
                        action="store_true",
                        help=argparse.SUPPRESS,
                        required=False)
    parser.add_argument('-g', '--generateEnvFiles',
                        # help='The flag to say ' +
                        # 'that this is being invoked by deployEnv.sh '
                        # 'and that we need to generate the env files rather '
                        # 'then read them.',
                        action="store_true",
                        help=argparse.SUPPRESS,
                        required=False)
    parser.add_argument('--forCustomer',
                        # help='This is used only'
                        # 'when creating a dcAuthorization instance.',
                        help=argparse.SUPPRESS,
                        required=False)

    # args, unknown = parser.parse_known_args()
    try:
        args, unknown = parser.parse_known_args()
    except SystemExit:
        sys.exit(1)

    returnList = {}

    if args.appName:
        returnList["CUSTOMER_APP_NAME"] = args.appName

    if args.env:
        returnList["ENV"] = args.env

    if args.workspaceName:
        returnList["WORKSPACE_NAME_ORIGINAL"] = args.workspaceName
        returnList["WORKSPACE_NAME"] = args.workspaceName.upper()

    if args.forCustomer:
        returnList["FOR_CUSTOMER"] = args.forCustomer
    # if we get here then the return the necessary arguments
    if type:
        return (returnList, args.initialCreate, args.generateEnvFiles)
    else:
        return (returnList)


def main(argv):
    """Execute this script."""
    shellGetEnv()


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
