#!/usr/bin/env python
import os
from os.path import expanduser
import shutil
import sys
import argparse
import subprocess
from time import time
import fileinput
import re
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

    def __init__(self, theAppName, baseDirectory):
        """ManageAppName constructor"""
        self.appName = theAppName
        self.baseDir = baseDirectory

        # put the baseDirectory path in the users $HOME/.devops.center
        # directory so that subsequent scripts can use it as a base to work
        # from when determining the environment for a session
        baseConfigDir = expanduser("~") + "/.devops.center"
        if not os.path.exists(baseConfigDir):
                os.makedirs(baseConfigDir)
        baseConfigFile = baseConfigDir + "/config"

        try:
            fileHandle = open(baseConfigFile, 'w')
            adjustedBaseDir = self.baseDir[:-1]
            strToWrite = "BASE_CUSTOMER_DIR=" + adjustedBaseDir + "\n"
            fileHandle.write(strToWrite)
            fileHandle.close()
        except IOError:
            print "NOTE: There is a file that needs to be created: \n" + \
                "$HOME/.devops.center/config and could not be written. \n" + \
                "Please report this issue to the devops.center admins."

    def run(self, command, options):
        optionsMap = self.parseOptions(options)
#   for testing purposes
#        if len(optionsMap.keys()):
#            for item in optionsMap.keys():
#                print "[{}] =>{}<=".format(item, optionsMap[item])

        if command == "join":
            self.joinExistingDevelopment(optionsMap)
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

    def joinExistingDevelopment(self, optionsMap):
        """This expects that the user is new and is joining development of an
        already exsiting repository.  So, this pulls down that existing repo
        with the given appName and puts it in the given baseDirectory"""

        # in order to get the files we need to know where the appName
        # repository is.  It had to be put in an owner directory, so that
        # has to be passed on the command line in the -o argument and would
        # be of the format owner=something
        if not len(optionsMap.keys()):
            print "In order to join an existing development effort, you" + \
                " will need to provide the option \n" + \
                "  -o 'owner=repositoryBaseName'" + \
                " \nThis is required in order to do a git clone" + \
                " of the appName repository. "
            sys.exit(1)
        if len(optionsMap.keys()) and "owner" not in optionsMap:
            print "The owner=repositoryBaseName was not given in the -o" + \
                " argument. This is required in order to do a git clone" + \
                " of the appName repository. "
            sys.exit(1)

        # create the base Directory
        self.createUtilDirectories()

        # change to the baseDirectory
        os.chdir(self.baseDir + "/" + self.appName)

        webName = self.appName + "-web"

        userResponse = raw_input(
            "\n\nEnter the name of the web repository that has been set up\n"
            "and it will be cloned from github. Or press return to accept\n"
            "the default name: (" + webName + ")\n")
        if userResponse:
            webName = userResponse

        # execute git clone on theAppName and put it in the baseDirectory
        cmdToRun = "git clone https://github.com/" + optionsMap["owner"] + \
            "/" + webName + ".git"
        # print "[{}] =>{}<=".format(os.getcwd(), cmdToRun)
        try:
            subprocess.check_call(cmdToRun, shell=True)
        except subprocess.CalledProcessError:
            print "There was an issue with cloning the application you " + \
                "specified.  Check that you specified\nthe correct owner " + \
                "and respository name."

    def create(self, optionsMap):
        """creates the directory structure and sets up the appropriate
        templates necessary to run a customers appliction set."""
        self.createUtilDirectories()
        self.createWebDirectories()
        self.createDockerComposeFiles()
        # self.createStackDirectory()
        # self.createAWSProfile()

        # TODO need to decide if there is a git init at the top level
        # of do it in each of the sub directories (ie, appName-utils,
        # appName-web, and uniqueID-stack).  I think it should be the separate
        # ones. So the .gitignore may need to be down in the appropriate sub
        # directory.

    def createUtilDirectories(self):
        basePath = self.baseDir + self.appName
        try:
            os.makedirs(basePath, 0755)
        except OSError:
            print 'Error creating the base directory, if it exists this ' + \
                'will not re-create it.\nPlease check to see that this ' + \
                'path does not already exist: \n' + basePath
            sys.exit(1)

        commonDirs = ["local", "dev", "staging", "prod"]

        # create the dataload directory...this is a placeholder and can
        # be a link to somewhere else with more diskspace.  But that is
        # currently up to the user.
        dataLoadDir = basePath + "/dataload"
        os.makedirs(dataLoadDir, 0755)

        # utils path to be created
        baseUtils = self.baseDir + self.appName + "/" + self.appName + \
            "-utils/"

        # and then the config directory and all the sub directories
        configDir = baseUtils + "config/"
        for item in commonDirs:
            os.makedirs(configDir + item, 0755)

        # and the enviornments directory
        envDir = baseUtils + "environments"
        os.makedirs(envDir, 0755)

        # and then create the individiual env files in that directory
        self.createEnvFiles(envDir)

        # create a directory to hold the generated env files
        generatedEnvDir = envDir + "/.generatedEnvFiles"
        os.makedirs(generatedEnvDir, 0755)

        # and then the keys directory and all the sub directories
        keyDir = baseUtils + "keys/"
        os.makedirs(keyDir, 0755)

        fileToWrite = basePath + "/.dcDirMap.cnf"
        try:
            fileHandle = open(fileToWrite, 'w')
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
                          "environments/.generatedEnvDir/*\n")

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
        # TODO ask them if they need to have  a web directory created
        # if no then ask them for the path/name of the web repository
        webName = self.appName + "-web"

        userResponse = raw_input(
            "\n\nEnter the name of the web directory that you want to use\n"
            "and a directory will be created with that name.\n\n"
            "NOTE: If you already have a repository checked out on this \n"
            "machine, we can create a link from there into our directory\n"
            "structure.  Provide the full path to your"
            "existing directory.\nOr press return to accept the \n"
            "default name: (" + webName + ")\n")
        if userResponse:
            if '/' not in userResponse:

                # web path to be created
                baseWeb = self.baseDir + self.appName + "/" + userResponse
                os.makedirs(baseWeb, 0755)
            else:
                if '~' in userResponse or '$HOME' in userResponse:
                    userRepo = userResponse.replace("~", expanduser("~"))
                if not os.path.exists(userRepo):
                    print "ERROR: That directory does not exist: {}".format(
                        userRepo)
                    sys.exit(1)

                # other wise get the name of the repository
                webName = os.path.basename(userRepo)

                baseWeb = self.baseDir + self.appName + "/" + webName
                print "\nThis directory: {}".format(userRepo)
                print "will be linked to: {}\n\n".format(
                    baseWeb)

                # and the destination directory
                os.symlink(userRepo, baseWeb)
        else:
            # web path to be created
            baseWeb = self.baseDir + self.appName + "/" + webName
            os.makedirs(baseWeb, 0755)

        fileToWrite = self.baseDir + self.appName + "/.dcDirMap.cnf"
        try:
            fileHandle = open(fileToWrite, 'a')
            strToWrite = "CUSTOMER_APP_WEB=" + webName + "\n"
            fileHandle.write(strToWrite)
            fileHandle.close()
        except IOError:
            print "NOTE: There is a file that needs to be created: \n" + \
                self.basedir + self.appName + "/.dcDirMap.cnf and " + \
                "could not be written. \n" + \
                "Please report this issue to the devops.center admins."

    def createStackDirectory(self):
        """create the dcStack directory that will contain the necessary files
        to create the web and worker containers"""

        uniqueStackName = self.getUniqueStackID()
        stackName = uniqueStackName + "-stack"
        self.registerStackID(stackName)

        # stack path to be created
        baseStack = self.baseDir + self.appName + "/" + stackName
        os.makedirs(baseStack, 0755)

        # make the web and worker directories
        for item in ["web", "web-debug", "worker"]:
            os.makedirs(baseStack + "/" + item, 0755)

        # create the  web/wheelhouse directory
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
        commonFiles = ["dev", "local", "staging", "prod"]
        for name in commonFiles:
            envFile = envDir + "/" + name + ".env"
            try:
                fileHandle = open(envFile, 'w')
                strToWrite = (
                    "#\n"
                    "# ENV vars specific to the " + name + " environment\n"
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
                "#\n"
                "# Papertrail settings\n"
                "#\n"
                "SYSLOG_SERVER='yourserver.papertrailapp.com'\n"
                "SYSLOG_PORT='48809'\n"
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
                'dcDATA=${dcHOME}/dataload\n'
                'dcAPP=${dcHOME}/' + self.appName + "-web\n"
                "\n"
                "LOG_NAME=" + self.appName + "\n"
                '#AWS_ACCESS_KEY_ID="put aws access key here"\n'
                "#AWS_SECRET_ACCESS_KEY='put secret access key here'\n"
            )
            fileHandle.write(strToWrite)
        except IOError:
            print 'Unable to write to the {} file in the' + \
                ' given configDir: {} \n'.format(personalFile, envDir)
            sys.exit(1)

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

        # need to change the env file name and path to represent what is created
        # with this script
        for line in fileinput.input(composeFile, inplace=1):
            print line.replace("APP_NAME-ENV", targetEnvFile),
        for line in fileinput.input(composeDebugFile, inplace=1):
            print line.replace("APP_NAME-ENV", targetEnvFile),

    def update(self, optionsMap):
        """takes an argument that dictates what needs to be updated and then
        what items that are associated with the change"""

    def delete(self, optionsMap):
        """delete all the necessary items that are associated with the
        appName"""
        # TODO items to delete:
        #   - self.baseDir/self.appName
        #   - unregister the appName (ie, remove it from .mapAppStack)
        #   - remove the entry from the .aws config and credentials files

    def getUniqueStackID(self):
            return hex(int(time()*10000000))[9:]

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


def checkArgs():
    parser = argparse.ArgumentParser(
        description='This script provides an administrative interface to a ' +
        'customers application set that is referred to as appName.  The ' +
        'administrative functions implement some of the CRUD services ' +
        '(ie, Create, Update, Delete).')
    parser.add_argument('-a', '--appName', help='Name of the application ' +
                        'to manage .',
                        required=True)
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
    parser.add_argument('-o', '--cmdOptions', help='Options for the ' +
                        'command arg',
                        default='',
                        required=False)
    args = parser.parse_args()

    retAppName = args.appName
    retCommand = args.command
    retOptions = args.cmdOptions

    # before going further we need to check whether there is a slash at the
    # end of the value in destinationDir
    if(args.baseDirectory.endswith('/')):
        if args.baseDirectory.startswith('~'):
            retBaseDir = args.baseDirectory.replace("~", expanduser("~"))
        elif args.baseDirectory.startswith("$HOME"):
            retBaseDir = args.baseDirectory.replace("$HOME", expanduser("~"))
        else:
            retBaseDir = args.baseDirectory
    else:
        tmpBaseDir = args.baseDirectory + '/'
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
    # if we get here then the
    return (retAppName, retBaseDir, retCommand, retOptions)


def main(argv):
    (appName, baseDir, command, options) = checkArgs()
#    print 'appName is: ' + appName
#    print 'baseDir is: ' + baseDir
#    print 'command is: ' + command
#    print 'options are: ' + options

    customerApp = ManageAppName(appName, baseDir)
    customerApp.run(command, options)

if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
