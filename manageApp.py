#!/usr/bin/env python
# ==============================================================================
#
#          FILE: manageApp.py
#
#         USAGE: manageApp.py
#
#   DESCRIPTION: create and manage an application to be used within the
#                devops.center framework.
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
# ==============================================================================

# flake8: noqa
import os
from os.path import expanduser
import shutil
import sys
import argparse
from argparse import RawDescriptionHelpFormatter
import subprocess
from time import time
import fileinput
import re
from scripts.process_dc_env import pythonGetEnv
# ==============================================================================
"""
This script provides an administrative interface to a customers application set
that is referred to as appName.  The administrative functions implement some of
the CRUD services (ie, Create, Update, Delete).
"""
__version__ = "0.1"

__copyright__ = "Copyright 2016, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================


class ManageAppName:

    def __init__(self, theAppName, baseDirectory, altName, appPath, sharedUtilsFlag,
                 utilsPath, envList):
        """ManageAppName constructor"""
        self.appName = theAppName
        self.dcAppName = ''
        self.appPath = appPath
        self.utilsPath = utilsPath
        self.baseDir = baseDirectory
        self.altName = altName.upper()
        self.dcUtils = os.environ["dcUTILS"]
        self.envList = envList
        self.sharedUtilsFlag = sharedUtilsFlag

        if self.sharedUtilsFlag:
            # set up the defaults for the shared info and check to see if
            # we are using a shared enviornment for this app
            self.sharedUtilsName = "dcShared-utils"
            commonSharedDir = self.envList[
                "dcCOMMON_SHARED_DIR"].replace('"', '')
            self.sharedSettingsPath = commonSharedDir + \
                "/" + self.envList["CUSTOMER_NAME"] + "/shared"
            self.sharedSettingsFile = self.sharedSettingsPath + "/dcSharedSettings"

        # put the baseDirectory path in the users $HOME/.dcConfig/baseDirectory
        # file so that subsequent scripts can use it as a base to work
        # from when determining the environment for a session
        baseConfigDir = expanduser("~") + "/.dcConfig"
        if not os.path.exists(baseConfigDir):
            os.makedirs(baseConfigDir)
        baseConfigFile = baseConfigDir + "/baseDirectory"
        adjustedBaseDir = self.baseDir[:-1]

        if not os.path.isfile(baseConfigFile):
            try:
                fileHandle = open(baseConfigFile, 'w')

                if self.altName:
                    strToWrite = "CURRENT_WORKSPACE=" + self.altName + "\n"
                else:
                    strToWrite = "CURRENT_WORKSPACE=DEFAULT\n"
                fileHandle.write(strToWrite)

                strToWrite = "##### WORKSPACES ######\n"
                fileHandle.write(strToWrite)

                if self.altName:
                    strToWrite = "_" + self.altName + \
                        "_BASE_CUSTOMER_DIR=" + adjustedBaseDir + "\n"
                else:
                    strToWrite = "_DEFAULT_BASE_CUSTOMER_DIR=" + \
                        adjustedBaseDir + "\n"
                fileHandle.write(strToWrite)

                strToWrite = "##### BASE DIR CONSTRUCTION NO TOUCH ######\n"
                fileHandle.write(strToWrite)

                strToWrite = "CONSTRUCTED_BASE_DIR=_${CURRENT_WORKSPACE}" + \
                    "_BASE_CUSTOMER_DIR\n"
                fileHandle.write(strToWrite)

                strToWrite = "BASE_CUSTOMER_DIR=${!CONSTRUCTED_BASE_DIR}\n"
                fileHandle.write(strToWrite)

                fileHandle.close()
            except IOError:
                print("NOTE: There is a file that needs to be created: \n"
                      "$HOME/.dcConfig/baseDirectory and could not be written"
                      "\nPlease report this issue to the devops.center admins.")

        elif os.path.isfile(baseConfigFile) and self.altName:
            # the file exists and they are adding a new base directory
            self.insertIntoBaseDirectoryFile(baseConfigFile, adjustedBaseDir)

    def insertIntoBaseDirectoryFile(self, baseConfigFile, adjustedBaseDir):
        # so we need to read in the file into an array
        with open(baseConfigFile) as f:
            lines = [line.rstrip('\n') for line in f]

        # first go through and check to see if we already have an alternate
        # base directory by this name and if so, set a flag so we dont add
        # again
        flagToAdd = 1
        strToSearch = "_" + self.altName + "_BASE_CUSTOMER_DIR"
        for aLine in lines:
            if strToSearch in aLine:
                flagToAdd = 0
                break

        # then open the same file for writting
        try:
            fileHandle = open(baseConfigFile, 'w')

            # then loop through the  array
            for aLine in lines:
                # look for the CURRENT_WORKSPACE and set it to the new name
                if "CURRENT_WORKSPACE=" in aLine:
                    strToWrite = "CURRENT_WORKSPACE=" + self.altName + "\n"
                    fileHandle.write(strToWrite)
                    continue

                if self.altName in aLine:
                    if flagToAdd == 0:
                        strToWrite = "_" + self.altName + \
                            "_BASE_CUSTOMER_DIR=" + adjustedBaseDir + "\n"
                        fileHandle.write(strToWrite)
                        continue

                # then look for the line that has  WORKSPACES in it
                if "WORKSPACES" in aLine:
                    fileHandle.write(aLine + "\n")
                    if flagToAdd:
                        strToWrite = "_" + self.altName + \
                            "_BASE_CUSTOMER_DIR=" + adjustedBaseDir + "\n"
                        fileHandle.write(strToWrite)
                    continue

                # other wise write the line as it came from the file
                fileHandle.write(aLine + "\n")

            fileHandle.close()
        except IOError:
            print("NOTE: There is a file that needs to be created: \n"
                  "$HOME/.dcConfig/baseDirectory and could not be written"
                  "\nPlease report this issue to the devops.center admins.")
        # and add a new line with the new altName and the adjustBasedir
        # then write out the rest of the file

    def run(self, command, options):
        optionsMap = self.parseOptions(options)
#   for testing purposes
#        if len(optionsMap.keys()):
#            for item in optionsMap.keys():
#                print "[{}] =>{}<=".format(item, optionsMap[item])

        if command == "join":
            self.joinExistingDevelopment()
        elif command == "create":
            self.create(optionsMap)
        elif command == "update":
            self.update(optionsMap)
        elif command == "delete":
            self.delete(optionsMap)
        elif command == "getUniqueID":
            print(self.getUniqueStackID())

        if self.sharedUtilsFlag:
            self.writeToSharedSettings()

    def parseOptions(self, options):
        """options is string of comma separate key=value pairs. If there is
        only one then it won't have a comma.  And it could be blank"""
        retMap = {}

        if options:
            # first they are comma se
            optionsList = options.split(",")
            for item in optionsList:
                (key, val) = item.split('=', 1)
                key = key.strip()
                retMap[key] = val

        return retMap

    def joinExistingDevelopment(self):  # noqa
        """This expects that the user is new and is joining development of an
        already exsiting repository.  So, this pulls down that existing repo
        with the given appName and puts it in the given baseDirectory.
        NOTE: the pound noqa after the method name will turn off the warning
        that the method is to complex."""

        if (not self.appPath):
            print("ERROR: you must provide both --appPath"
                  " to join and existing application.")
            sys.exit(1)

        # create the dataload directory...this is a placeholder and can
        # be a link to somewhere else with more diskspace.  But that is
        # currently up to the user.
        basePath = self.baseDir + self.appName
        dataLoadDir = basePath + "/dataload"
        if not os.path.exists(dataLoadDir):
            os.makedirs(dataLoadDir, 0755)

        # change to the baseDirectory
        os.chdir(basePath)

        if re.match("http", self.appPath) or re.search(".git$", self.appPath):
            # they have entered a git repo for the existing front end directory
            self.joinWithGit(basePath, "web", self.appPath)
        else:
            # they have entered a path to an existing front end directory
            self.joinWithPath(basePath, "web", self.appPath)

        if self.sharedUtilsFlag:
            gitUtilsPath = None
            try:
                with open(self.sharedSettingsFile) as fp:
                    for aLine in fp:
                        strippedLine = aLine.strip()
                        if "SHARED_APP_REPO" in strippedLine:
                            gitUtilsPath = strippedLine.split("=")[1]
                            break
                if gitUtilsPath:
                    # since this is a shared repo for the app-utils it resides in a
                    # different place (peer to the app directories in the baseDir)
                    # hence we need to pass this path on to the next methods and they
                    # will do the right thing in the right place (ie they will clone
                    # if the directory doesn't exist, otherwise it will do a
                    # pull)
                    basePath = self.baseDir + self.sharedUtilsName
                    if re.match("http", gitUtilsPath) or re.search(".git$", gitUtilsPath):
                        # they have entered a git repo for the existing utilities
                        # directory
                        self.joinWithGit(basePath, "utils", gitUtilsPath)
                    else:
                        # TODO need to remove the app-web that was pulled down if
                        # we get to here.
                        print('ERROR: the URL for the shared app-utils repository '
                              ' is invalid or unsupported: ' + gitUtilsPath +
                              '\n You will need retry this command after that is '
                              'corrected.')
            except IOError as error:
                print('Error: trying to get the shared file that contains the '
                      'respository that has this\napplications devops.center '
                      'utilities could not be found. \nThis could either be '
                      'because this application hasnt been created yet or you\n'
                      'dont have acces to the share drive that contians the file.')
                sys.exit(1)
        else:
            if re.match("http", self.utilsPath) or re.search(".git$", self.utilsPath):
                # they have entered a git repo for the existing utilities
                # directory
                self.joinWithGit(basePath, "utils", self.utilsPath)
            else:
                # they have entered a path to an existing utilies directory
                self.joinWithPath(basePath, "utils", self.utilsPath)

        # and the environments directory
        envDir = basePath + "/" + self.utilsDirName + "/environments"
        if not os.path.exists(envDir):
            os.makedirs(envDir, 0755)

            print("Creating environment files")
            # and then create the individiual env files in that directory
            self.createEnvFiles(envDir)
        else:
            print("Creating personal.env file")
            # the environments directory exists so as long as there is a
            # personal.env make a change to the dcHOME  defined there
            # to be the one that is passed into this script.
            self.createPersonalEnv(envDir)

        # create a directory to hold the generated env files
        generatedEnvDir = envDir + "/.generatedEnvFiles"
        if not os.path.exists(generatedEnvDir):
            os.makedirs(generatedEnvDir, 0755)
            open(generatedEnvDir + "/.keep", 'a').close()

        # TODO need to ensure any keys that are pulled down have the correct
        # permissions

        print("Completed successfully\n")

    def create(self, optionsMap):
        """creates the directory structure and sets up the appropriate
        templates necessary to run a customers appliction set."""
        self.createBaseDirectories()
        self.createWebDirectories()
        self.createUtilDirectories()
        self.tmpGetStackDirectory()
        self.createDockerComposeFiles()
        print("\n\nDone")
        # self.createStackDirectory()
        # self.createAWSProfile()

        # TODO need to decide if there is a git init at the top level
        # of do it in each of the sub directories (ie, appName-utils,
        # appName-web, and uniqueID-stack).  I think it should be the separate
        # ones. So the .gitignore may need to be down in the appropriate sub
        # directory.

    def createBaseDirectories(self):
        basePath = self.baseDir + self.appName
        try:
            os.makedirs(basePath, 0755)
        except OSError:
            print('Error creating the base directory, if it exists this '
                  'will not re-create it.\nPlease check to see that this '
                  'path does not already exist: \n' + basePath)
            sys.exit(1)

    def createUtilDirectories(self):
        basePath = ''
        if self.sharedUtilsFlag:
            basePath = self.baseDir + self.sharedUtilsName
        else:
            basePath = self.baseDir + self.appName
        commonDirs = ["local", "dev", "staging", "prod"]

        # create the dataload directory...this is a placeholder and can
        # be a link to somewhere else with more diskspace.  But that is
        # currently up to the user.
        dataLoadDir = self.baseDir + self.appName + "/dataload"
        if not os.path.exists(dataLoadDir):
            os.makedirs(dataLoadDir, 0755)

        # utils path to be created
        baseUtils = basePath + "/" + self.appName + \
            "-utils/"

        # and then the config directory and all the sub directories
        configDir = baseUtils + "config/"
        for item in commonDirs:
            if not os.path.exists(configDir + item):
                os.makedirs(configDir + item, 0755)
                # and touch a file so that this isn't an empty directory
                open(configDir + item + "/.keep", 'a').close()

        # and the environments directory
        envDir = baseUtils + "environments"
        if not os.path.exists(envDir):
            os.makedirs(envDir, 0755)

        # and then create the individiual env files in that directory
        self.createEnvFiles(envDir)

        # create a directory to hold the generated env files
        generatedEnvDir = envDir + "/.generatedEnvFiles"
        if not os.path.exists(generatedEnvDir):
            os.makedirs(generatedEnvDir, 0755)
            open(generatedEnvDir + "/.keep", 'a').close()

        # create the certs directory
        keyDir = baseUtils + "certs/"
        for item in commonDirs:
            if not os.path.exists(keyDir + item):
                os.makedirs(keyDir + item, 0755)
                # and touch a file so that this isn't an empty directory
                open(keyDir + item + "/.keep", 'a').close()

        # and then the keys directory and all the sub directories
        keyDir = baseUtils + "keys/"
        for item in commonDirs:
            if not os.path.exists(keyDir + item):
                os.makedirs(keyDir + item, 0755)
                # and touch a file so that this isn't an empty directory
                open(keyDir + item + "/.keep", 'a').close()

        fileToWrite = ''
        if self.sharedUtilsFlag:
            fileToWrite = self.baseDir + self.appName + "/.dcDirMap.cnf"
        else:
            fileToWrite = basePath + "/.dcDirMap.cnf"
        try:
            fileHandle = open(fileToWrite, 'a')
            strToWrite = "CUSTOMER_APP_UTILS=" + self.appName + "-utils\n"
            fileHandle.write(strToWrite)
            fileHandle.close()
        except IOError:
            print("NOTE: There is a file that needs to be created: \n" +
                  basePath + "/.dcDirMap.cnf and could not be written. \n"
                  "Please report this issue to the devops.center admins.")

        # put a .gitignore file in the appName directory to properly ignore
        # some files that will be created that don't need to go into the
        # repository
        if self.sharedUtilsFlag:
            gitIgnoreFile = basePath + "/.gitignore"
        else:
            gitIgnoreFile = baseUtils + "/.gitignore"

        try:
            fileHandle = open(gitIgnoreFile, 'w')
            strToWrite = (".DS_Store\n"
                          "personal.env\n"
                          "environments/.generatedEnvFiles/*\n"
                          "!environments/.generatedEnvFiles/.keep\n")

            fileHandle.write(strToWrite)
            fileHandle.close()
        except IOError:
            if self.sharedUtilsFlag:
                aPath = basePath
            else:
                aPath = baseUtils

            print("NOTE: There is a file that needs to be created: \n" +
                  aPath + "/.gitignore and could not be written. \n"
                  "Please report this issue to the devops.center admins.")

        # and now run the git init on the Utils directory
        if not self.sharedUtilsFlag:
            originalDir = os.getcwd()
            os.chdir(baseUtils)
            subprocess.check_call("git init .", shell=True)
            os.chdir(originalDir)
        else:
            # make a symbolic link from the newly created directory in
            # the shared utils directory to the web
            originalDir = os.getcwd()
            os.chdir(self.baseDir + self.appName)
            sourceUtilsDir = "../" + self.sharedUtilsName + "/" + \
                self.appName + "-utils/"
            targetUtilsDir = self.baseDir + "/" + self.appName + "/" + \
                self.appName + "-utils"
            os.symlink(sourceUtilsDir, targetUtilsDir)
            os.chdir(originalDir)

            # and do the git init if it hasn't been done before:w
            gitDir = basePath + "/.git"
            if not os.path.exists(gitDir):
                originalDir = os.getcwd()
                os.chdir(basePath)
                subprocess.check_call("git init .", shell=True)
                os.chdir(originalDir)

    def createWebDirectories(self):
        webName = self.appName + "-web"

        userResponse = raw_input(
            "\n\nEnter the name of the web directory that you want to use\n"
            "and a directory will be created with that name.\n\n"
            "NOTE: If you already have a repository checked out on this \n"
            "machine, we can create a link from there into our directory\n"
            "structure.  Provide the full path to your "
            "existing directory.\nOr press return to accept the "
            "default name: (" + webName + ")\n")
        if userResponse:
            if '/' not in userResponse:
                #  is just a name
                webName = userResponse
                # web path to be created
                self.baseWeb = self.baseDir + self.appName + "/" + userResponse
                if not os.path.exists(self.baseWeb):
                    os.makedirs(self.baseWeb, 0755)

                # and now run the git init on the Utils directory
                originalDir = os.getcwd()
                os.chdir(self.baseWeb)
                subprocess.check_call("git init .", shell=True)
                os.chdir(originalDir)

#            elif (re.match("http", userResponse) or
#                  re.match("git", userResponse)):
#                # its a URL so we need to get a git clone
#                originalDir = os.getcwd()
#                os.chdir(self.baseDir + self.appName)
#                print "Cloning: " + userResponse
#                cmdToRun = "git clone " + userResponse
#
#                try:
#                    subprocess.check_output(cmdToRun,
#                                            stderr=subprocess.STDOUT,
#                                            shell=True)
#                except subprocess.CalledProcessError:
#                    print ("There was an issue with cloning the "
#                           "application you specified: " + userResponse +
#                           "\nCheck that you specified the correct owner "
#                           "and respository name.")
#                # TODO PROBABLY NEED TO GET THE NAME OF THE NEW WEB DIRECTORY
#                #      HERE AND SET IT ACCORDINGLY
#                os.chdir(originalDir)

            else:
                # is is a local directory so we need to sym-link it
                if '~' in userResponse:
                    userRepo = userResponse.replace("~", expanduser("~"))
                elif '$HOME' in userResponse:
                    userRepo = userResponse.replace("$HOME", expanduser("~"))
                else:
                    userRepo = userResponse
                if not os.path.exists(userRepo):
                    print("ERROR: That directory does not exist: {}".format(
                        userRepo))
                    sys.exit(1)

                # other wise get the name of the repository
                webName = os.path.basename(userRepo)

                self.baseWeb = self.baseDir + self.appName + "/" + webName
                print("\nThis directory: {}".format(userRepo))
                print("will be linked to: {}\n".format(
                    self.baseWeb))
                yesResponse = raw_input(
                    "If this is correct press Y/y (Any other response"
                    " will NOT create this directory): ")
                if yesResponse.lower() == 'y':
                    # and the destination directory
                    os.symlink(userRepo, self.baseWeb)
                else:
                    print("The symlink was NOT created.")
        else:
            # web path to be created
            self.baseWeb = self.baseDir + self.appName + "/" + webName
            if not os.path.exists(self.baseWeb):
                os.makedirs(self.baseWeb, 0755)

        # set up the web name as the name for dcAPP that will be used to
        # write in the personal.env file
        self.dcAppName = webName

        fileToWrite = self.baseDir + self.appName + "/.dcDirMap.cnf"
        try:
            fileHandle = open(fileToWrite, 'w')
            strToWrite = "CUSTOMER_APP_WEB=" + self.dcAppName + "\n"
            fileHandle.write(strToWrite)
            fileHandle.close()
        except IOError:
            print("NOTE: There is a file that needs to be created: \n" +
                  self.basedir + self.appName + "/.dcDirMap.cnf and "
                  "could not be written. \n"
                  "Please report this issue to the devops.center admins.")

    def tmpGetStackDirectory(self):
        """This method is put in place to be called instead of the
        createStackDirectory method.  This will just ask for the unique stack
        name that you want to use for this appliacation"""
        userResponse = raw_input(
            "\n\nEnter the name of the unique stack repository that has been "
            "set up for this app\nand it will be used in the "
            "docker-compose.yml files\n"
            "for the web and worker images:\n")
        if userResponse:
            # take the userResponse and use it to edit the docker-compose.yml
            self.uniqueStackName = userResponse
        else:
            print("You will need to have a stack name that corresponds "
                  "with the name of a repository that has the web "
                  "(and worker) that is with dcStack")
            sys.exit(1)

    def createStackDirectory(self):
        """create the dcStack directory that will contain the necessary files
        to create the web and worker containers"""

        uniqueStackName = self.getUniqueStackID()
        stackName = uniqueStackName + "-stack"
        self.registerStackID(stackName)

        # stack path to be created
        baseStack = self.baseDir + self.appName + "/" + stackName
        if not os.path.exists(baseStack):
            os.makedirs(baseStack, 0755)

        # make the web and worker directories
        for item in ["web", "web-debug", "worker"]:
            if not os.path.exists(baseStack + "/" + item):
                os.makedirs(baseStack + "/" + item, 0755)

        # create the  web/wheelhouse directory
        if not os.path.exists(baseStack + "/web/wheelhouse"):
            os.makedirs(baseStack + "/web/wheelhouse", 0755)

        # and the .gitignore to ignore the wheelhouse directoryo
        gitIgnoreFile = baseStack + "/web/.gitignore"
        try:
            fileHandle = open(gitIgnoreFile, 'w')
            strToWrite = ("wheelhouse\n")

            fileHandle.write(strToWrite)
            fileHandle.close()
        except IOError:
            print("NOTE: There is a file that needs to be created: \n" +
                  baseStack + "web/.gitignore and could not be written. \n"
                  "Please report this issue to the devops.center admins.")

        # and get the template Dockerfile, requirements for each of the sub
        # directories
        webDockerFile = baseStack + "/web/Dockerfile"
        shutil.copyfile(self.dcUtils + "/templates/Dockerfile-web",
                        webDockerFile)

        workerDockerFile = baseStack + "/worker/Dockerfile"
        shutil.copyfile(self.dcUtils + "/templates/Dockerfile-worker",
                        workerDockerFile)

        webShFile = baseStack + "/web/web.sh"
        shutil.copyfile(self.dcUtils + "/templates/web.sh", webShFile)

        supervisorConfFile = baseStack + \
            "/worker/supervisor-djangorq-worker.conf"
        shutil.copyfile(self.dcUtils +
                        "/templates/supervisor-djangorq-worker.conf",
                        supervisorConfFile)

        # need to change the entry in the work Dockerfile that references the
        # stackName-web image to build from.  So, there is a CUSTOMER_STACK
        # variable that needs to be changed
        for line in fileinput.input(workerDockerFile, inplace=1):
            print line.replace("CUSTOMER_STACK", uniqueStackName),

    def createEnvFiles(self, envDir):
        appUtilsDir = self.appName + "-utils/"
        commonFiles = ["dev", "local", "staging", "prod"]
        for name in commonFiles:
            envFile = envDir + "/" + name + ".env"
            try:
                fileHandle = open(envFile, 'w')
                strToWrite = (
                    "#\n"
                    "# ENV vars specific to the " + name + " environment\n"
                    "#\n"
                    "APP_UTILS_CONFIG=${dcHOME}/" + appUtilsDir + "config/" +
                    name + "\n"
                    "APP_UTILS_KEYS=${dcHOME}/" + appUtilsDir + "/keys/" +
                    name + "\n"
                    "#\n")
                fileHandle.write(strToWrite)
            except IOError:
                print('Unable to write to the {} file in the'
                      ' given configDir: {} \n'.format(envFile, envDir))
                sys.exit(1)

        # fill the local file with some default value
        envLocalFile = envDir + "/common.env"
        try:
            fileHandle = open(envLocalFile, 'w')
            strToWrite = (
                "# some app env vars specific to the environment\n"
                "dcHOME=~/" + self.appName + "\n"
                "\n#\n"
                "# Papertrail settings\n"
                "#\n"
                "SYSLOG_SERVER='yourserver.papertrailapp.com'\n"
                "SYSLOG_PORT='99999'\n"
                "SYSLOG_PROTO='udp'\n"
                "\n"
                "#\n"
                "# Default pgpool config - single backend\n"
                "#\n"
                "PGPOOL_CONFIG_FILE='/etc/pgpool2/pgpool.conf.one'\n"
            )
            fileHandle.write(strToWrite)
        except IOError:
            print('Unable to write to the {} file in the'
                  ' given configDir: {} \n'.format(envLocalFile, envDir))
            sys.exit(1)

        # fill the local file with some default value
        envLocalFile = envDir + "/local.env"
        try:
            fileHandle = open(envLocalFile, 'w')
            strToWrite = (
                "# some app env vars specific to the environment\n"
                "APP_UTILS_CONFIG=${dcHOME}/" + appUtilsDir + "config/local\n"
                "APP_UTILS_KEYS=${dcHOME}/" + appUtilsDir + "keys\n"
                "\n#\n"
                "# Papertrail settings\n"
                "#\n"
                "SYSLOG_SERVER='yourserver.papertrailapp.com'\n"
                "SYSLOG_PORT='99999'\n"
                "SYSLOG_PROTO='udp'\n"
                "\n"
                "#\n"
                "# Default pgpool config - single backend\n"
                "#\n"
                "PGPOOL_CONFIG_FILE='/etc/pgpool2/pgpool.conf.one'\n"
            )
            fileHandle.write(strToWrite)
        except IOError:
            print('Unable to write to the {} file in the'
                  ' given configDir: {} \n'.format(envLocalFile, envDir))
            sys.exit(1)

        # and now for the personal.env file
        self.createPersonalEnv(envDir)

    def createAWSProfile(self):
        """This method will create the necessary skeleton in the .aws directory
        for the new appName which will be used as the profile name"""

        # TODO determine if this is a good thing to do...By doing this the
        # .aws config and credentials could be set up and then the user would
        # have to fill it in.  But the region wouldn't be known and the keys
        # would not be known.  The reason for doing this is that if the user
        # goes through the aws configure steps and doesn't do the profile or
        # gives a different profile name than the appName then things wont
        # work right.

        # first check for the existance of the .aws directory
        configFileWriteFlag = 'w'
        credentialFileWriteFlag = 'w'
        awsBaseDir = expanduser("~") + "/.aws"
        if os.path.exists(awsBaseDir):
            # and then check for the existance of the config and credentials
            # files
            if os.path.isfile(awsBaseDir + "/config"):
                configFileWriteFlag = 'a'
            if os.path.isfile(awsBaseDir + "/credentials"):
                credentialFileWriteFlag = 'a'
        else:
            # create the directory
            if not os.path.exists(awsBaseDir):
                os.makedirs(awsBaseDir)

        # now add the necessary entries in config
        awsConfigFile = awsBaseDir + "/config"
        try:
            fileHandle = open(awsConfigFile, configFileWriteFlag)
            strToWrite = ("[profile " + self.appName + "]\n"
                          "output = json\n"
                          "region = us-west-2\n")
            fileHandle.write(strToWrite)
            fileHandle.close()
        except IOError:
            print("NOTE: There is a file that needs to be created: \n"
                  "$HOME/.aws/config and could not be written. \n"
                  "Please report this issue to the devops.center admins.")

        # now add the necessary entries in credentials
        awsCredentialsFile = awsBaseDir + "/credentials"
        try:
            fileHandle = open(awsCredentialsFile, credentialFileWriteFlag)
            strToWrite = "[" + self.appName + "]\n" + \
                "aws_access_key_id = YOUR_ACCESS_KEY_ID_HERE\n" + \
                "aws_secret_access_key = YOUR_SECRET_ACCESS_KEY_HERE\n"
            fileHandle.write(strToWrite)
            fileHandle.close()
        except IOError:
            print("NOTE: There is a file that needs to be created: \n"
                  "$HOME/.aws/credentials and could not be written. \n"
                  "Please report this issue to the devops.center admins.")

        print("\nYou will need to add your AWS access and secret key to \n"
              "the ~/.aws/credentials file and will need to check the \n"
              "region in the ~/.aws/config file to ensure it is set to  \n"
              "correct AWS region that your instances are created in.\n"
              "Look for these entries under the profile name: \n" +
              self.appName + "\n\n")

    def createDockerComposeFiles(self):
        """This method will create the Dockerfile(s) as necessary for this
        appName.  It will take a template file and update it with the specific
        directory updates for created with this script."""

        # set up the base config directory path
        # NOTE: it will only put these in the "local" directory
        if self.sharedUtilsFlag:
            baseConfig = self.baseDir + self.sharedUtilsName + "/" + \
                self.appName + "-utils/config/local"
        else:
            baseConfig = self.baseDir + self.appName + "/" + self.appName + \
                "-utils/config/local"

        # copy the docker-compose template files
        composeFile = baseConfig + "/docker-compose.yml"
        shutil.copyfile(self.dcUtils + "/templates/docker-compose.yml",
                        composeFile)

        composeDebugFile = baseConfig + "/docker-compose-debug.yml"
        shutil.copyfile(self.dcUtils + "/templates/docker-compose-debug.yml",
                        composeDebugFile)

        composeSubnetFile = baseConfig + "/docker-subnet.conf"
        shutil.copyfile(self.dcUtils + "/templates/docker-subnet.conf",
                        composeSubnetFile)

        # need to change the env file name and path to represent what is
        # created with this script
        for line in fileinput.input(composeFile, inplace=1):
            print line.replace("DC_UNIQUE_ID", self.uniqueStackName),
        for line in fileinput.input(composeDebugFile, inplace=1):
            print line.replace("DC_UNIQUE_ID", self.uniqueStackName),

    def createPersonalEnv(self, envDir):
        """create the personal.env file when joinExistingDevelopment"""
        personalFile = envDir + "/personal.env"
        try:
            fileHandle = open(personalFile, 'w')
            strToWrite = (
                "#\n"
                "# Personal env settings that take precedence over other\n"
                "# env files.\n"
                "# NOTE: if you change anything in this file you will need\n"
                "#       to run deployenv.sh to make sure the environment\n"
                "#       files get genereated with the latest changes\n"
                "#\n"
                "dcDEFAULT_APP_NAME=" + self.appName + "\n"
                "dcHOME=" + self.baseDir + self.appName + "\n"
                "\n"
                'dcDATA=${dcHOME}/dataload\n'
                'dcAPP=${dcHOME}/' + self.dcAppName + "\n"
                "\n"
                "#LOG_NAME=put the name you want to see in papertrail, "
                "the default is hostname\n"
                '#AWS_ACCESS_KEY_ID="put aws access key here"\n'
                "#AWS_SECRET_ACCESS_KEY='put secret access key here'\n"
            )
            fileHandle.write(strToWrite)
        except IOError:
            print('Unable to write to the {} file in the'
                  ' given configDir: {} \n'.format(personalFile, envDir))
            sys.exit(1)

    def joinWithGit(self, basePath, theType, theURL):
        cloneOrPull = " clone "
        if self.sharedUtilsFlag and theType == "utils":
            # the basePath includes the standard shared repo named
            # directory
            if os.path.exists(basePath):
                print("Pulling: " + theURL)
                cloneOrPull = " pull "
            else:
                print("Cloning: " + theURL)
        else:
            print("Cloning: " + theURL)

        cmdToRun = "git" + cloneOrPull + theURL
        appOutput = ''
        try:
            appOutput = subprocess.check_output(cmdToRun,
                                                stderr=subprocess.STDOUT,
                                                shell=True)

            # if using the shared repo then we need to make a symlink
            # from the app-utils name under the dcShared-utils to the
            # correct place in the app directory
            if self.sharedUtilsFlag and theType == "utils":
                sourceUtilsDir = "../" + self.sharedUtilsName + "/" + \
                    self.appName + "-utils/"
                targetUtilsDir = self.baseDir + "/" + self.appName + "/" + \
                    self.appName + "-utils"
                os.symlink(sourceUtilsDir, targetUtilsDir)

            # get the newly created directory and put it in the
            # appropriate ENV variable in the dcDirMap.cnf
            if "Cloning" in appOutput:
                aName = re.search("(?<=')[^']+(?=')", appOutput).group(0)

                if theType == "web":
                    theEnvVarToWrite = "CUSTOMER_APP_WEB="
                    self.dcAppName = aName
                    # NOTE VERY dependent on the order in which this method
                    # is called.  Web is assumed to be first ... see the
                    # joinExistingDevelopment method
                    fileWriteMode = 'w'
                else:
                    theEnvVarToWrite = "CUSTOMER_APP_UTILS="
                    self.utilsDirName = aName
                    # NOTE VERY dependent on the order in which this method
                    # is called.  Web is assumed to be first ... see the
                    # joinExistingDevelopment method
                    fileWriteMode = 'a'

                fileToWrite = self.baseDir + self.appName + "/.dcDirMap.cnf"
                try:
                    fileHandle = open(fileToWrite, fileWriteMode)
                    strToWrite = theEnvVarToWrite + aName + "\n"
                    fileHandle.write(strToWrite)
                    fileHandle.close()
                except IOError:
                    print("NOTE: There is a file that needs to be "
                          "created: \n" + self.basedir + self.appName +
                          "/.dcDirMap.cnf and could not be written. \n"
                          "Please report this issue to the devops.center "
                          "admins.")

        except subprocess.CalledProcessError:
            print("There was an issue with cloning the application you "
                  "specified: " + theURL +
                  "\nCheck that you have provided the correct credentials "
                  "and respository name.")
            sys.exit(1)

        print("Done\n")

    def joinWithPath(self, basePath, theType, thePath):
        if thePath.startswith("~"):
            adjustedPath = thePath.replace('~', expanduser('~'))
        elif thePath.startswith("$HOME"):
            adjustedPath = thePath.replace('$HOME', expanduser('~'))
        elif thePath.startswith("${HOME}"):
            adjustedPath = thePath.replace('${HOME}', expanduser('~'))
        else:
            adjustedPath = thePath

        # and get the name at the end of the path
        aName = os.path.basename(adjustedPath)
        destPath = basePath + "/" + aName

        print("Linking the path: " + adjustedPath)
        print("  to directory: " + destPath)
        os.symlink(adjustedPath, destPath)

        # and now update the .dcDirMap.conf
        if theType == "web":
            theEnvVarToWrite = "CUSTOMER_APP_WEB="
            self.dcAppName = aName
            # NOTE VERY dependent on the order in which this method
            # is called.  Web is assumed to be first ... see the
            # joinExistingDevelopment method
            fileWriteMode = 'w'
        else:
            theEnvVarToWrite = "CUSTOMER_APP_UTILS="
            self.utilsDirName = aName
            # NOTE VERY dependent on the order in which this method
            # is called.  Web is assumed to be first ... see the
            # joinExistingDevelopment method
            fileWriteMode = 'a'

        fileToWrite = basePath + "/.dcDirMap.cnf"
        try:
            fileHandle = open(fileToWrite, fileWriteMode)
            strToWrite = theEnvVarToWrite + self.dcAppName + "\n"
            fileHandle.write(strToWrite)
            fileHandle.close()
        except IOError:
            print("NOTE: There is a file that needs to be "
                  "created: \n" + self.basedir + self.appName +
                  "/.dcDirMap.cnf and could not be written. \n"
                  "Please report this issue to the devops.center "
                  "admins.")

        print("Done\n")

    def update(self, optionsMap):
        """takes an argument that dictates what needs to be updated and then
        what items that are associated with the change"""
        if "newEnv" in optionsMap:
            self.createNewEnvDirs(optionsMap["newEnv"])

    def createNewEnvDirs(self, newEnvName):
        # utils path to be created
        baseUtils = self.baseDir + self.appName + "/" + self.appName + \
            "-utils/"
        appUtilsDir = self.appName + "-utils/"

        # and then the config directory and all the sub directories
        configDir = baseUtils + "config/"
        if not os.path.exists(configDir + newEnvName):
            os.makedirs(configDir + newEnvName, 0755)
            # and touch a file so that this isn't an empty directory
            open(configDir + newEnvName + "/.keep", 'a').close()

        # and the environments directory
        envDir = baseUtils + "environments"
        if not os.path.exists(envDir):
            os.makedirs(envDir, 0755)

        # and then create the individiual env files in that directory
        envFile = envDir + "/" + newEnvName + ".env"
        try:
            fileHandle = open(envFile, 'w')
            strToWrite = (
                "#\n"
                "# ENV vars specific to the " + newEnvName + " environment\n"
                "#\n"
                "APP_UTILS_CONFIG=${dcHOME}/" + appUtilsDir + "config/" +
                newEnvName + "\n"
                "APP_UTILS_KEYS=${dcHOME}/" + appUtilsDir + "keys/" +
                newEnvName + "\n"
                "#\n")
            fileHandle.write(strToWrite)
        except IOError:
            print('Unable to write to the {} file in the'
                  ' given configDir: {} \n'.format(envFile, envDir))
            sys.exit(1)

        # and then the keys directory and all the sub directories
        keyDir = baseUtils + "keys/"
        if not os.path.exists(keyDir + newEnvName):
            os.makedirs(keyDir + newEnvName, 0755)
            # and touch a file so that this isn't an empty directory
            open(keyDir + newEnvName + "/.keep", 'a').close()

        certsDir = baseUtils + "/certs/"
        if not os.path.exists(certsDir + newEnvName):
            os.makedirs(certsDir + newEnvName, 0755)
            # and touch a file so that this isn't an empty directory
            open(keyDir + newEnvName + "/.keep", 'a').close()

        print("New Environment created: " + newEnvName)

    def delete(self, optionsMap):
        """delete all the necessary items that are associated with the
        appName"""
        print("Currently under construcution\n")
        sys.exit(1)
        # TODO items to delete:
        #   - self.baseDir/self.appName
        #   - unregister the appName (ie, remove it from .mapAppStack)
        #   - remove the entry from the .aws config and credentials files

    def getUniqueStackID(self):
        return hex(int(time() * 10000000))[9:]

    def registerStackID(self, stackName):
        """This will make not of the mapping between appName and stackName"""
        # TODO: send this to a server to register in the devops.center database
        # for now put it in a private file in this directory
        mappingFile = ".mapAppStack"
        if os.path.isfile(mappingFile):
            foundALine = 0
            for line in fileinput.input(mappingFile, inplace=1):
                if line == "\n":
                    continue
                if self.appName in line:
                    foundALine = 1
                    printre.sub("=(.*)-stack", "=" + stackName, line),
                else:
                    # NOTE the comma doesn't print out an extra newline
                    print line,
            fileinput.close()

            if foundALine == 0:
                try:
                    fileHandle = open(mappingFile, 'a')
                    strToWrite = (self.appName + "=" + stackName + "\n")

                    fileHandle.write(strToWrite)
                    fileHandle.close()
                except IOError:
                    print("NOTE: There is a file that needs to be "
                          "created:\n./.mapAppStack\n And it could not be"
                          "written. \n"
                          "Please report this issue to the devops.center admins.")
        else:
            try:
                fileHandle = open(mappingFile, 'w')
                strToWrite = (self.appName + "=" + stackName + "\n")

                fileHandle.write(strToWrite)
                fileHandle.close()
            except IOError:
                print("NOTE: There is a file that needs to be created: \n"
                      "./.mapAppStack and could not be written. \n"
                      "Please report this issue to the devops.center admins.")

    def writeToSharedSettings(self):
        if not os.path.exists(self.sharedSettingsPath):
            try:
                os.makedirs(self.sharedSettingsPath, 0755)
            except OSError:
                print('Error creating the shared directory: '
                      + self.sharedSettingsPath +
                      '\nSo the information about this app utilizing the shared'
                      'app utils will not be saved. ')
                return

        sharedRepoURL = ("git@github.com:" + self.envList["CUSTOMER_NAME"] +
                         "/dcShared-utils.git\n")
        print('\nGenerating a git repo and put it into a shared settings file:\n'
              + sharedRepoURL)
        # before we write out to the file check to see if the customer name has
        # any characters that aren't alphanumeric and let them know that the
        # generated git URL may not be correct
        if re.findall('\w+', self.envList["CUSTOMER_NAME"]):
            print('\nNOTE: this URL may not be correct as it has characters '
                  'that are not letters or numbers.\nSo you may have to edit '
                  'this file manually to reflect the actual git repo URL '
                  'for the dcShared-utils.git.\n'
                  'The path to the file is: ' + self.sharedSettingsFile + '\n\n')

        # if we get here then the shared drive and directory are set up so append
        # this app-utils information that it is shared
        try:
            if os.path.isfile(self.sharedSettingsFile):
                # it exists so check to see if the app has already been added
                strToSearch = self.appName + "-utils=shared"
                if strToSearch not in open(self.sharedSettingsFile).read():
                    # then append this information
                    fileHandle = open(self.sharedSettingsFile, 'a')
                    strToWrite = (strToSearch + "\n")
                    fileHandle.write(strToWrite)
                    fileHandle.close()
            else:
                # it doesn't exist so we need to create it and add the shared repo
                # URL and then the app-utils and that it is shared
                fileHandle = open(self.sharedSettingsFile, 'w')
                strToWrite = ("SHARED_APP_REPO=git@github.com:" +
                              self.envList["CUSTOMER_NAME"] +
                              "/dcShared-utils.git\n")
                strToWrite += (self.appName + "-utils=shared\n")
                fileHandle.write(strToWrite)
                fileHandle.close()
        except IOError:
            print("NOTE: There is a file that needs to be created: \n"
                  + self.sharedSettingsFile +
                  "\n and it could not be written. \n"
                  "Please report this issue to the devops.center admins.")


def checkBaseDirectory(baseDirectory, envList):
    if(baseDirectory.endswith('/')):
        if baseDirectory.startswith('~'):
            retBaseDir = baseDirectory.replace("~", expanduser("~"))
        elif baseDirectory.startswith("$HOME"):
            retBaseDir = baseDirectory.replace("$HOME", expanduser("~"))
        else:
            retBaseDir = baseDirectory
    else:
        tmpBaseDir = baseDirectory + '/'
        if tmpBaseDir.startswith('~'):
            retBaseDir = tmpBaseDir.replace("~", expanduser("~"))
        elif tmpBaseDir.startswith("$HOME"):
            retBaseDir = tmpBaseDir.replace("$HOME", expanduser("~"))
        else:
            retBaseDir = tmpBaseDir

    newBaseDir = retBaseDir
    if "WORKSPACE_NAME" in envList:
        newBaseDir = retBaseDir + envList["WORKSPACE_NAME_ORIGINAL"] + "/"
        if not os.path.exists(newBaseDir):
            print('Createing base directory associated with the workspace '
                  'name:' + newBaseDir)
            os.makedirs(newBaseDir, 0755)
    else:
        try:
            # lets try to write to that directory
            tmpFile = newBaseDir + '.removeme'
            tmpFileHandle = open(tmpFile, 'w')
            tmpFileHandle.close()
            os.remove(tmpFile)

        except IOError:
            print('Unable to access base directory: ' + newBaseDir)
            sys.exit(1)

    return newBaseDir


def getBaseDirectory():
    # read the ~/.dcConfig/settings
    baseSettingsDir = expanduser("~") + "/.dcConfig"
    if not os.path.exists(baseSettingsDir):
        print("You seem to be missing the $HOME/.dcConfig directory,"
              "you will need to run the RUN-ME-FIRST.sh script that "
              "established that directory and the settings file that"
              "contains the initial base directory for you application"
              "development.")
        sys.exit(1)

    if os.path.isfile(baseSettingsDir + "/baseDirectory"):
        # TODO check to see if they have entered a --workspace option
        #      otherwise  take the base directory from the current  workspace
        with open(baseSettingsDir + "/baseDirectory") as f:
            lines = [line.rstrip('\n') for line in f]
        workspaceName = ''
        for item in lines:
            if "CURRENT_WORKSPACE" in item:
                lineArray = item.split('=')
                workspaceName = '_' + lineArray[1] + '_BASE_CUSTOMER_DIR'

            if workspaceName in item:
                anotherLineArray = item.split('=')
                developmentBaseDir = anotherLineArray[1] + '/'
                return(developmentBaseDir)

    if os.path.isfile(baseSettingsDir + "/settings"):
        # get the base directory from the settings file
        with open(baseSettingsDir + "/settings") as f:
            lines = [line.rstrip('\n') for line in f]
        for item in lines:
            if "DEV_BASE_DIR" in item:
                lineArray = item.split('=')
                developmentBaseDir = lineArray[1] + '/'
                return(developmentBaseDir)

    else:
        print("You will need to re-run this command with the -d option to"
              "specify the base directory to continue.")
        sys.exit(1)


def checkArgs():
    parser = argparse.ArgumentParser(
        description='This script provides an administrative interface to a '
        'customers application\nset that is referred to as appName. The '
        'functions deal with manipulation of\nthe directory structure and '
        'content of the appUtils and website, mainly the\nappUtils.  This '
        'script does not deal with the instances or containers that\nare the '
        'end running product.\n\n'
        'The '
        'create command will take the\nbaseDirectory as the path to put the '
        'files that will be associated with the\napplication. This directory '
        'structure serves as a logical grouping of the\nfiles for the web '
        'site and all the configuration and utilities that support\nbuilding '
        'the appliction on the destination (either cloud instances or\n'
        'containers or both.\n\n'
        'The join option is a way to have someone else join in on the '
        'development\nafter someone has created the initial application files '
        'and checked them\ninto a git repository. It will create the '
        'directory structure just like\nthe create command but it will get the '
        'appUtils and web from a git\nrepository instead of starting from '
        'scratch. The git URL to clone,\nfor each of the two options can '
        'either be https or git and using one\nover the other depends on your '
        'credentials\n\n'
        'The update command supports the ability to create a new '
        'environment\nname in the appUtils directory.  So, if you have an '
        'environment that is\ndifferent from dev,staging, or prod, you can use '
        'this option and it will\navailable to be able to be used by all '
        'subsequent commands and utilities.\nSee below for how to use.\n\n'

        'Example command line to create an application:\n'
        './manageApp.py --appName YourApp\n'
        '               --command create\n\n'
        'Example command line to join with an application:\n'
        './manageApp.py --appName YourApp\n'
        '            --command join\n'
        '            --appPath git@git.assembla.com:website.git \n'
        '            --utilsPath https://zsoqe@bitbucket.org/team/appUtils.git'
        '\n\n'
        'Example cmd line to update an application with a new environment:\n'
        './manageApp.py --appName YourApp\n'
        '            --command update\n'
        '            --option "newEnv=UAT"\n',

        formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-d', '--baseDirectory', help='The base directory '
                        'to be used to access the appName. This needs to be '
                        'an absolute path unless the first part of the path '
                        'is a tilde or $HOME.   This option is not required '
                        'but is needed when using the workspaceName option.',
                        required=False)
    parser.add_argument('-c', '--command', help='Command to execute' +
                        'on the appName. Default [join]',
                        choices=["join",
                                 "create",
                                 "update",
                                 "delete"],
                        default='join',
                        required=False)
    parser.add_argument('-p', '--appPath', help='The customer application '
                        'repo URL or a path to an existing directory that '
                        'houses the application front end. If you provide a '
                        'path it should be an the full absolute path as it '
                        'will be symobolically linked to the base directory '
                        'given in this command. NOTE: tilde(~) or $HOME will '
                        'be expanded appropriately',
                        default='',
                        required=False)
    parser.add_argument('-u', '--utilsPath', help='The customer utils '
                        'repo URL or a path to an existing directory that '
                        'houses the application utilities. If you provide a '
                        'path it should be an the full absolute path as it '
                        'will be symobolically linked to the base directory '
                        'given or into the app directory if the --sharedUtils'
                        ' option is given. NOTE: tilde(~) or $HOME will '
                        'be expanded appropriately',
                        default='',
                        required=False)
    parser.add_argument('-o', '--cmdOptions', help='Options for the '
                        'command arg',
                        default='',
                        required=False)
    parser.add_argument('-s', '--separateUtils', help='Flag to determine that '
                        'you do NOT want to to use a shared application utils. ',
                        action="store_true",
                        required=False)

    try:
        args, unknown = parser.parse_known_args()
    except SystemExit:
        pythonGetEnv()
        sys.exit(1)

    retEnvList = pythonGetEnv(initialCreate=True)

    # before going further we need to check whether there is a slash at the
    # end of the value in destinationDir
    if args.baseDirectory:
        retBaseDir = checkBaseDirectory(args.baseDirectory, retEnvList)
    else:
        retBaseDir = getBaseDirectory()
        if not retBaseDir:
            print("Could not determine the baseDirectory, you will need to "
                  "re-run this script and provide the -d option.")
            sys.exit(1)

    if retEnvList["CUSTOMER_APP_NAME"]:
        retAppName = retEnvList["CUSTOMER_APP_NAME"]
    retCommand = args.command
    retOptions = args.cmdOptions
    retAppURL = args.appPath
    retUtilsURL = args.utilsPath

    retSharedUtils = True
    if args.separateUtils:
        retSharedUtils = False

    if "WORKSPACE_NAME" in retEnvList:
        retWorkspaceName = retEnvList["WORKSPACE_NAME"]
    else:
        retWorkspaceName = ''

    # if we get here then the
    return (retAppName, retBaseDir, retWorkspaceName, retCommand, retAppURL,
            retUtilsURL, retSharedUtils, retEnvList,  retOptions)


def main(argv):
    (appName, baseDir, workspaceName, command, appPath, utilsPath,
     sharedUtilsFlag, envList, options) = checkArgs()

    customerApp = ManageAppName(appName, baseDir, workspaceName, appPath,
                                sharedUtilsFlag, utilsPath, envList)
    customerApp.run(command, options)


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
