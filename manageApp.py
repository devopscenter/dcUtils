#!/usr/bin/env python
# flake8: noqa
import os
from os.path import expanduser
import shutil
import sys
import argparse
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

    def __init__(self, theAppName, baseDirectory, altName, appURL, utilsURL):
        """ManageAppName constructor"""
        self.appName = theAppName
        self.dcAppName = ''
        self.appURL = appURL
        self.utilsURL = utilsURL
        self.baseDir = baseDirectory
        self.altName = altName.upper()

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
                print "NOTE: There is a file that needs to be created: \n" + \
                    "$HOME/.dcConfig/baseDirectory and could not be written" +\
                    "\nPlease report this issue to the devops.center admins."

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
            print "NOTE: There is a file that needs to be created: \n" + \
                "$HOME/.dcConfig/baseDirectory and could not be written" + \
                "\nPlease report this issue to the devops.center admins."
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
            print self.getUniqueStackID()

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

    def joinExistingDevelopment(self): # noqa
        """This expects that the user is new and is joining development of an
        already exsiting repository.  So, this pulls down that existing repo
        with the given appName and puts it in the given baseDirectory.
        NOTE: the pound noqa after the method name will turn off the warning
        that the method is to complex."""

        if (not self.appURL) or (not self.utilsURL):
            print "ERROR: you must provide both --appURL and --utilsURL to" + \
                " join and existing application."
            sys.exit(1)

        # create the dataload directory...this is a placeholder and can
        # be a link to somewhere else with more diskspace.  But that is
        # currently up to the user.
        basePath = self.baseDir + self.appName
        dataLoadDir = basePath + "/dataload"
        if not os.path.exists(dataLoadDir):
            os.makedirs(dataLoadDir, 0755)

        # change to the baseDirectory
        os.chdir(self.baseDir + "/" + self.appName)

        print "Cloning: " + self.appURL
        cmdToRun = "git clone " + self.appURL

        appOutput = ''
        try:
            appOutput = subprocess.check_output(cmdToRun,
                                                stderr=subprocess.STDOUT,
                                                shell=True)

            # get the newly created directory and put it in the
            # CUSTOMER_APP_WEB in the dcDirMap.cnf
            if "Cloning" in appOutput:
                self.dcAppName = re.search("(?<=')[^']+(?=')",
                                           appOutput).group(0)

                fileToWrite = basePath + "/.dcDirMap.cnf"
                try:
                    fileHandle = open(fileToWrite, 'w')
                    strToWrite = "CUSTOMER_APP_WEB=" + self.dcAppName + "\n"
                    fileHandle.write(strToWrite)
                    fileHandle.close()
                except IOError:
                    print ("NOTE: There is a file that needs to be " +
                           "created: \n" + self.basedir + self.appName +
                           "/.dcDirMap.cnf and could not be written. \n" +
                           "Please report this issue to the devops.center " +
                           "admins.")

        except subprocess.CalledProcessError:
            print "There was an issue with cloning the application you " + \
                "specified: " + self.appURL + \
                "\nCheck that you specified\nthe correct owner " + \
                "and respository name."

        print "Done\n\nCloning: " + self.utilsURL
        cmdToRun = "git clone " + self.utilsURL

        utilsOutput = ''
        try:
            utilsOutput = subprocess.check_output(cmdToRun,
                                                  stderr=subprocess.STDOUT,
                                                  shell=True)

            # get the newly created directory and put it in the
            # CUSTOMER_APP_UTILS in the dcDirMap.cnf
            if "Cloning" in utilsOutput:
                self.utilsDirName = re.search("(?<=')[^']+(?=')",
                                              utilsOutput).group(0)

                fileToWrite = basePath + "/.dcDirMap.cnf"
                try:
                    fileHandle = open(fileToWrite, 'a')
                    strToWrite = "CUSTOMER_APP_UTILS=" + self.utilsDirName + \
                                 "\n"
                    fileHandle.write(strToWrite)
                    fileHandle.close()
                except IOError:
                    print ("NOTE: There is a file that needs to be created: " +
                           "\n" + self.basedir + self.appName +
                           "/.dcDirMap.cnf and could not be written. \n"
                           "Please report this issue to the devops.center " +
                           "admins.")

        except subprocess.CalledProcessError:
            print "There was an issue with cloning the application you " + \
                "specified: " + self.utilsURL + \
                "\nCheck that you specified\nthe correct owner " + \
                "and respository name."

        print "Done\n"
        # and the environments directory
        envDir = basePath + "/" + self.utilsDirName + "/environments"
        if not os.path.exists(envDir):
            os.makedirs(envDir, 0755)

            print "Creating environment files"
            # and then create the individiual env files in that directory
            self.createEnvFiles(envDir)
        else:
            print "Creating personal.env file"
            # the environments directory exists so as long as there is a
            # personal.env make a change to the dcHOME  defined there
            # to be the one that is passed into this script.
            self.createPersonalEnv(envDir)

        # create a directory to hold the generated env files
        generatedEnvDir = envDir + "/.generatedEnvFiles"
        if not os.path.exists(generatedEnvDir):
            os.makedirs(generatedEnvDir, 0755)

        print "Completed successfully\n"

    def create(self, optionsMap):
        """creates the directory structure and sets up the appropriate
        templates necessary to run a customers appliction set."""
        self.createBaseDirectories()
        self.createWebDirectories()
        self.createUtilDirectories()
        self.tmpGetStackDirectory()
        self.createDockerComposeFiles()
        print "\n\nDone"
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
            print 'Error creating the base directory, if it exists this ' + \
                'will not re-create it.\nPlease check to see that this ' + \
                'path does not already exist: \n' + basePath
            sys.exit(1)

    def createUtilDirectories(self):
        basePath = self.baseDir + self.appName
        commonDirs = ["local", "dev", "staging", "prod"]

        # create the dataload directory...this is a placeholder and can
        # be a link to somewhere else with more diskspace.  But that is
        # currently up to the user.
        dataLoadDir = basePath + "/dataload"
        if not os.path.exists(dataLoadDir):
            os.makedirs(dataLoadDir, 0755)

        # utils path to be created
        baseUtils = self.baseDir + self.appName + "/" + self.appName + \
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

        # and then the keys directory and all the sub directories
        keyDir = baseUtils + "keys/"
        for item in commonDirs:
            if not os.path.exists(keyDir + item):
                os.makedirs(keyDir + item, 0755)
                # and touch a file so that this isn't an empty directory
                open(keyDir + item + "/.keep", 'a').close()

        fileToWrite = basePath + "/.dcDirMap.cnf"
        try:
            fileHandle = open(fileToWrite, 'a')
            strToWrite = "CUSTOMER_APP_UTILS=" + self.appName + "-utils\n"
            fileHandle.write(strToWrite)
            fileHandle.close()
        except IOError:
            print "NOTE: There is a file that needs to be created: \n" + \
                basePath + "/.dcDirMap.cnf and could not be written. \n" + \
                "Please report this issue to the devops.center admins."

        # put a .gitignore file in the appName directory to properly ignore
        # some files that will be created that don't need to go into the
        # repository
        gitIgnoreFile = baseUtils + "/.gitignore"

        try:
            fileHandle = open(gitIgnoreFile, 'w')
            strToWrite = (".DS_Store\n"
                          "personal.env\n"
                          "environments/.generatedEnvFiles/*\n")

            fileHandle.write(strToWrite)
            fileHandle.close()
        except IOError:
            print "NOTE: There is a file that needs to be created: \n" + \
                basePath + "/.gitignore and could not be written. \n" + \
                "Please report this issue to the devops.center admins."

        # and now run the git init on the Utils directory
        originalDir = os.getcwd()
        os.chdir(baseUtils)
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
                webName = userResponse
                # web path to be created
                baseWeb = self.baseDir + self.appName + "/" + userResponse
                if not os.path.exists(baseWeb):
                    os.makedirs(baseWeb, 0755)
            else:
                if '~' in userResponse:
                    userRepo = userResponse.replace("~", expanduser("~"))
                elif '$HOME' in userResponse:
                    userRepo = userResponse.replace("$HOME", expanduser("~"))
                else:
                    userRepo = userResponse
                if not os.path.exists(userRepo):
                    print "ERROR: That directory does not exist: {}".format(
                        userRepo)
                    sys.exit(1)

                # other wise get the name of the repository
                webName = os.path.basename(userRepo)

                baseWeb = self.baseDir + self.appName + "/" + webName
                print "\nThis directory: {}".format(userRepo)
                print "will be linked to: {}\n".format(
                    baseWeb)
                yesResponse = raw_input(
                    "If this is correct press Y/y (Any other response"
                    " will NOT create this directory): ")
                if yesResponse.lower() == 'y':
                    # and the destination directory
                    os.symlink(userRepo, baseWeb)
                else:
                    print "The symlink was NOT created."
        else:
            # web path to be created
            baseWeb = self.baseDir + self.appName + "/" + webName
            if not os.path.exists(baseWeb):
                os.makedirs(baseWeb, 0755)

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
            print "NOTE: There is a file that needs to be created: \n" + \
                self.basedir + self.appName + "/.dcDirMap.cnf and " + \
                "could not be written. \n" + \
                "Please report this issue to the devops.center admins."

    def tmpGetStackDirectory(self):
        """This method is put in place to be called instead of the
        createStackDirectory method.  This will just ask for the unique stack
        name that you want to use for this appliacation"""
        userResponse = raw_input(
            "\n\nEnter the name of the unique stack repository that has been "
            "set up for this app\nand it will be used in the "
            "docker-compoase.yml files\n"
            "for the web and worker images:\n")
        if userResponse:
            # take the userResponse and use it to edit the docker-compose.yml
            self.uniqueStackName = userResponse
        else:
            print "You will need to have a stack name that corresponds " + \
                "with the name of a repository that has the web " + \
                "(and worker) that is with dcStack"
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
            print "NOTE: There is a file that needs to be created: \n" + \
                baseStack + "web/.gitignore and could not be written. \n" + \
                "Please report this issue to the devops.center admins."

        # and get the template Dockerfile, requirements for each of the sub
        # directories
        webDockerFile = baseStack + "/web/Dockerfile"
        shutil.copyfile("templates/Dockerfile-web", webDockerFile)

        workerDockerFile = baseStack + "/worker/Dockerfile"
        shutil.copyfile("templates/Dockerfile-worker", workerDockerFile)

        webShFile = baseStack + "/web/web.sh"
        shutil.copyfile("templates/web.sh", webShFile)

        supervisorConfFile = baseStack + \
            "/worker/supervisor-djangorq-worker.conf"
        shutil.copyfile("templates/supervisor-djangorq-worker.conf",
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
                    "APP_UTILS_KEYS=${dcHOME}/" + appUtilsDir + "config/" +
                    name + "\n"
                    "\n# Papertrail settings\n"
                    "#\n"
                    "SYSLOG_SERVER='yourserver.papertrailapp.com'\n"
                    "SYSLOG_PORT='99999'\n"
                    "SYSLOG_PROTO='udp'\n"
                    "\n#\n"
                    "#\n")
                fileHandle.write(strToWrite)
            except IOError:
                print 'Unable to write to the {} file in the' + \
                    ' given configDir: {} \n'.format(envFile, envDir)
                sys.exit(1)

        # fill the local file with some default value
        envLocalFile = envDir + "/local.env"
        try:
            fileHandle = open(envLocalFile, 'w')
            strToWrite = (
                "# some app env vars specific to the environment\n"
                "APP_UTILS_CONFIG=${dcHOME}/" + appUtilsDir + "config/local\n"
                "APP_UTILS_KEYS=${dcHOME}/" + appUtilsDir + "config/keys\n"
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
            print 'Unable to write to the {} file in the' + \
                ' given configDir: {} \n'.format(envLocalFile, envDir)
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
            print "NOTE: There is a file that needs to be created: \n" + \
                "$HOME/.aws/config and could not be written. \n" + \
                "Please report this issue to the devops.center admins."

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
            print "NOTE: There is a file that needs to be created: \n" + \
                "$HOME/.aws/credentials and could not be written. \n" + \
                "Please report this issue to the devops.center admins."

        print "\nYou will need to add your AWS access and secret key to \n" + \
            "the ~/.aws/credentials file and will need to check the \n" + \
            "region in the ~/.aws/config file to ensure it is set to  \n" + \
            "correct AWS region that your instances are created in.\n" + \
            "Look for these entries under the profile name: \n" + \
            self.appName + "\n\n"

    def createDockerComposeFiles(self):
        """This method will create the Dockerfile(s) as necessary for this
        appName.  It will take a template file and update it with the specific
        directory updates for created with this script."""

        # set up the base config directory path
        # NOTE: it will only put these in the "local" directory
        baseConfig = self.baseDir + self.appName + "/" + self.appName + \
            "-utils/config/local"

        # copy the docker-compose template files
        composeFile = baseConfig + "/docker-compose.yml"
        shutil.copyfile("templates/docker-compose.yml", composeFile)

        composeDebugFile = baseConfig + "/docker-compose-debug.yml"
        shutil.copyfile("templates/docker-compose-debug.yml", composeDebugFile)

        # set up the targetEnvFile name based upon  the name and the
        # path to get there
        targetEnvFile = self.baseDir + self.appName + "/" + self.appName + \
            "-utils/environments/.generatedEnvFiles/dcEnv-" + \
            self.appName + "-local"

        # need to change the env file name and path to represent what is
        # created with this script
        for line in fileinput.input(composeFile, inplace=1):
            print line.replace("APP_NAME-ENV", targetEnvFile),
        for line in fileinput.input(composeFile, inplace=1):
            print line.replace("DC_UNIQUE_ID", self.uniqueStackName),
        for line in fileinput.input(composeDebugFile, inplace=1):
            print line.replace("APP_NAME-ENV", targetEnvFile),
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
                "# change dcUTILS to where you have put the devops.center\n"
                "# dcUtils directory\n"
                "dcUTILS=" + self.baseDir + "dcUtils\n"
                'dcDATA=${dcHOME}/${dcDEFAULT_APP_NAME}/dataload\n'
                'dcAPP=${dcHOME}/${dcDEFAULT_APP_NAME}/' + self.dcAppName + "\n"
                "\n"
                "#LOG_NAME=put the name you want to see in papertrail, "
                "the default is hostname\n"
                '#AWS_ACCESS_KEY_ID="put aws access key here"\n'
                "#AWS_SECRET_ACCESS_KEY='put secret access key here'\n"
            )
            fileHandle.write(strToWrite)
        except IOError:
            print 'Unable to write to the {} file in the' + \
                ' given configDir: {} \n'.format(personalFile, envDir)
            sys.exit(1)

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
                "APP_UTILS_KEYS=${dcHOME}/" + appUtilsDir + "config/" +
                newEnvName + "\n"
                "\n# Papertrail settings\n"
                "#\n"
                "SYSLOG_SERVER='yourserver.papertrailapp.com'\n"
                "SYSLOG_PORT='99999'\n"
                "SYSLOG_PROTO='udp'\n"
                "\n#\n"
                "#\n")
            fileHandle.write(strToWrite)
        except IOError:
            print 'Unable to write to the {} file in the' + \
                ' given configDir: {} \n'.format(envFile, envDir)
            sys.exit(1)

        # and then the keys directory and all the sub directories
        keyDir = baseUtils + "keys/"
        if not os.path.exists(keyDir + newEnvName):
            os.makedirs(keyDir + newEnvName, 0755)
            # and touch a file so that this isn't an empty directory
            open(keyDir + newEnvName + "/.keep", 'a').close()

        print "New Environment created: " + newEnvName

    def delete(self, optionsMap):
        """delete all the necessary items that are associated with the
        appName"""
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
                    print re.sub("=(.*)-stack", "=" + stackName, line),
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
                    print "NOTE: There is a file that needs to be " + \
                        "created:\n./.mapAppStack\n And it could not be" + \
                        "written. \n" + \
                        "Please report this issue to the devops.center admins."
        else:
            try:
                fileHandle = open(mappingFile, 'w')
                strToWrite = (self.appName + "=" + stackName + "\n")

                fileHandle.write(strToWrite)
                fileHandle.close()
            except IOError:
                print "NOTE: There is a file that needs to be created: \n" + \
                    "./.mapAppStack and could not be written. \n" + \
                    "Please report this issue to the devops.center admins."


def checkBaseDirectory(baseDirectory):
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

    try:
        # lets try to write to that directory
        tmpFile = retBaseDir + '.removeme'
        tmpFileHandle = open(tmpFile, 'w')
        tmpFileHandle.close()
        os.remove(tmpFile)

    except IOError:
        print 'Unable to access base directory: ' + \
            retBaseDir
        sys.exit(1)

    return retBaseDir


def checkArgs():
    parser = argparse.ArgumentParser(
        description='This script provides an administrative interface to a ' +
        'customers application set that is referred to as appName.  The ' +
        'administrative functions implement some of the CRUD services ' +
        '(ie, Create, Update, Delete).')
    parser.add_argument('-d', '--baseDirectory', help='The base directory ' +
                        'to be used to access the appName. This needs to ' +
                        'an absolute path unless the first part of the path ' +
                        'is a tilde or $HOME',
                        required=True)
    parser.add_argument('-c', '--command', help='Command to execute' +
                        'on the appName. Default [join]',
                        choices=["join",
                                 "create",
                                 "update",
                                 "delete",
                                 "getUniqueID"],
                        default='join',
                        required=False)
    parser.add_argument('-p', '--appURL', help='The customer application ' +
                        'repo URL to use for the join command',
                        default='',
                        required=False)
    parser.add_argument('-u', '--utilsURL', help='The customer utils ' +
                        'repo URL to use for the join command',
                        default='',
                        required=False)
    parser.add_argument('-o', '--cmdOptions', help='Options for the ' +
                        'command arg',
                        default='',
                        required=False)
    parser.add_argument('-n', '--workspaceName',
                        help='A unique name that identifies an alternate ' +
                        'workspace. By default only one base directory is ' +
                        'created and all applications created are put into ' +
                        'that directory. By specifying this option an ' +
                        'alternate base directory can be identified and it ' +
                        'will be kept separate from any other base  ' +
                        'directories. One usage is if you have multiple ' +
                        'clients that you are building apps for then the ' +
                        'apps can be in separate base directories ' +
                        '(essentially applications associated by client)' +
                        'with this option.',
                        required=False)

    try:
        args, unknown = parser.parse_known_args()
    except SystemExit:
        pythonGetEnv()
        sys.exit(1)

    retEnvList = pythonGetEnv(initialCreate=True)

    if retEnvList["CUSTOMER_APP_NAME"]:
        retAppName = retEnvList["CUSTOMER_APP_NAME"]
    retCommand = args.command
    retOptions = args.cmdOptions
    retAppURL = args.appURL
    retUtilsURL = args.utilsURL

    # before going further we need to check whether there is a slash at the
    # end of the value in destinationDir
    if args.baseDirectory:
        retBaseDir = checkBaseDirectory(args.baseDirectory)

    if args.workspaceName:
        retWorkspaceName = args.workspaceName
    else:
        retWorkspaceName = ''

    # if we get here then the
    return (retAppName, retBaseDir, retWorkspaceName, retCommand, retAppURL,
            retUtilsURL, retOptions)


def main(argv):
    (appName, baseDir, workspaceName, command, appURL, utilsURL,
     options) = checkArgs()

    customerApp = ManageAppName(appName, baseDir, workspaceName, appURL,
                                utilsURL)
    customerApp.run(command, options)


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
