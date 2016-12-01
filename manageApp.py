#!/usr/bin/env python
import os
from os.path import expanduser
import sys
import argparse
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

    def joinExistingDevelopment(self):
        """pulls down an existing repo with the given appName and
        puts it in the given baseDirectory"""

    def create(self):
        """creates the directory structure and sets up the appropriate
        templates necessary to run a customers appliction set."""
        self.createUtilDirectories()
        self.createWebDirectories()

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
        for item in commonDirs:
            os.makedirs(keyDir + item, 0755)

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

    def createWebDirectories(self):
        # TODO ask them if they need to have  a web directory created
        # if no then ask them for the path/name of the web repository
        webName = self.appName + "-web"

        userResponse = raw_input(
            "Enter the name of the web directory that you want to use and "
            "a directory will be created with that name.\n"
            "Or press return to accept the default name: (" + webName + ")\n")
        if userResponse:
            webName = userResponse

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
                "#\n"
                "dcDEFAULT_APP_NAME=" + self.appName + "\n"
                "dcHOME=" + self.baseDir + self.appName + "\n"
                "\n"
                "# change dcUTILS to where you have put the devops.center\n"
                "# dcUtils directory\n"
                'dcUTILS=${dcHOME}/dcUtils\n'
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

    def update(self, whatToUpdate, updateOptions):
        """takes an argument that dictates what needs to be updated and then
        what items that are associated with the change"""

    def delete(self):
        """delete all the necessary items that are associated with the
        appName"""


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
                                 "delete"],
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
#    print 'options is: ' + options

    customerApp = ManageAppName(appName, baseDir)
    if command == "join":
        customerApp.joinExistingDevelopment()
    elif command == "create":
        customerApp.create()
    elif command == "update":
        customerApp.update()
    elif command == "delete":
        customerApp.delete()

if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
