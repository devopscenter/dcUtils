#!/usr/bin/env python
import os
import sys
import argparse
import json
import subprocess
from os.path import expanduser

# ==============================================================================
"""
Script that provides a facility to watch for file changes and then perform
actions based upon the files that change.
"""
__version__ = "0.1"

__copyright__ = "Copyright 2016, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================


class DCWatchDog:
    """Class that takes a list of ActionableWatchers and executes separate
       watchdog processes for each item in the list"""
    actionableItemList = ()

    def __init__(self, actionableItemListIn):
        """Creates the instance with the given list of ActionableWatchers"""
        self.actionableItemList = actionableItemListIn
        self.pidsFile = "./.dcWatcher.pids"
        self.actionDir = "./commands/"

    def checkForPidFile(self):
        if os.path.isfile(self.pidsFile):
            print "There is a prior dcWatcher running as there is an " + \
                "existing pid file:\n" + self.pidsFile + \
                "\nIt would be wise to check to see if any of watchmedo " + \
                "processes are still running. If not then you will need " + \
                "to remove the pids file manually or by running " + \
                "stop-dcWatcher.sh before trying to execute dcWatcher.py again."
            sys.exit(1)

    def run(self):
        self.checkForPidFile()
        # create a watchmedo command line for each item in the
        # actionableItemList
        for anItem in self.actionableItemList:
            patternList = anItem.getPatterns()
            for pattern in patternList:
                cmdToRun = 'watchmedo shell-command '

                # put a pattern for this command
                cmdToRun += '--patterns="' + pattern[0] + '" '

                # get any options if they exist
                options = anItem.getOptions()
                if options:
                    for key in options:
                        cmdToRun += '--' + key
                        if options[key] == '' or options[key] == 'True':
                            cmdToRun += ' '
                        else:
                            cmdToRun += '=' + options[key] + ' '

                # get the command to run when the pattern is triggered
                cmdToRun = self.processActions(anItem, cmdToRun)

                # before continuing check to see that the cmdToRun string that
                # was returned still has something in it.  If not then  the
                # processActions method couldn't find the action script to run
                # and a message was printed to the console that this item
                # will not be processed.  So, we need to stop working on this
                # element and forge on to the next
                if cmdToRun == '':
                    continue

                # add the directory for this pattern
                cmdToRun += pattern[1]

                # execute the watchdog watchmedo process for this pattern
                pid = subprocess.Popen(cmdToRun, shell=True).pid
                print "[{}] {}\n".format(pid, cmdToRun)

                # write out the pid in a well known place so that we can kill
                # this later with another script
                with open(self.pidsFile, 'a') as pFile:
                    pFile.write(str(pid) + " ")

    def processActions(self, anItem, cmdToRunIn):
        retCmdToRun = cmdToRunIn
        (actionToRun, actionToRunArgs) = self.convertActionToRun(
            anItem.getAction())

        if not os.path.isfile(actionToRun):
            # the action doesn't exist so do not contine and go to
            # the next item in the list
            print "WARN: " + anItem.getAction() + "could not be " + \
                "found. So this watched item will not be performed"
            return ''

        retCmdToRun += "--command='" + actionToRun + " "

        # add any of the arguments that come along with the actionToRun
        if len(actionToRunArgs) > 0:
            retCmdToRun += '-a "'
            for num, arg in enumerate(actionToRunArgs):
                retCmdToRun += arg
                if (num + 1) < len(actionToRunArgs):
                    retCmdToRun += ","
            retCmdToRun += '" '

        # and add the standard options
        retCmdToRun += ("-s ${watch_src_path} -e ${watch_event_type} "
                        "-o ${watch_object} ")

        #  add any container to the standard options list
        containers = anItem.getOtherHosts()
        if containers:
            retCmdToRun += '-c "'
            for num, aContainer in enumerate(containers):
                retCmdToRun += aContainer
                if (num + 1) < len(containers):
                    retCmdToRun += ","
            retCmdToRun += '"'

        retCmdToRun += "' "

        return retCmdToRun

    def convertActionToRun(self, actions):
        """will change the action into a python script in a specific
        directory"""
        returnAction = ''
        returnArguments = []
        # need to check to see if the action has multiple arguments.  That
        # would make this a dictionary rather than a key/value pair
        if type(actions) is dict:
            key = actions.keys()

            # set the returnAction to the key
            returnAction = self.actionDir + key[0] + ".py"

            # and we are only interested in the first key (right now)
            if type(actions[key[0]]) is list:
                returnArguments = actions[key[0]]
            else:
                returnArguments.append(actions[key[0]])
        else:
            returnAction = self.actionDir + actions + ".py"

        returnArgs = []
        for argItem in returnArguments:
            tmpItem = argItem.replace("$srcFile", "\$srcFile")
            finalItem = tmpItem.replace("$destFile", "\$destFile")
            returnArgs.append(finalItem)

        return (returnAction, returnArgs)


class ActionableWatcher:
    """Class that defines what a pattern to watch and the action associated
        with that pattern"""

    def __init__(self):
        """creates an ActionableWatcher with a given set of directory(ies)
           to watch for changes for files with a given a pattern and the action
           script to execute when the trigger is found"""
        self.patterns = []
        self.action = []
        self.otherHosts = []
        self.directories = []
        self.options = {}
        self.platformType = ''

    def addOtherHosts(self, otherHostList):
        self.otherHosts = otherHostList

    def addAction(self, anAction):
        self.action = anAction

    def addOptions(self, optionSet):
        self.options = optionSet

    def getOtherHosts(self):
        return self.otherHosts

    def getPatterns(self):
        return self.patterns

    def getAction(self):
        return self.action

    def getOptions(self):
        return self.options

    def getPlatformType(self):
        return self.platformType

    def getDirectories(self):
        return self.directories

    def __str__(self):
        printStr = "Host type: " + self.platformType + " \n"

        # set up the string for each of the lists in the class
        if self.patterns:
            printStr += "Patterns: \n"
            for p in self.patterns:
                printStr += " " + p[0] + " in directory: " + p[1] + " \n"

        if self.directories:
            printStr += "Directories: \n"
            for d in self.directories:
                printStr += " " + d[0] + " and " + d[1] + " \n"

        # set up the string for the actions
        if self.actions:
            printStr += "Actions: \n"
            for a in self.actions:
                printStr += " " + a + " \n"

        # set up the string for the containers
        if self.otherHosts:
            printStr += "OtherHosts: \n"
            for c in self.otherHosts:
                printStr += " " + c + " \n"

        # set up the string for the options
        if self.options:
            printStr += "Options: \n"
            for key in self.options:
                printStr += " " + key + ": " + self.options[key] + "\n"

        return printStr


class ContainerActionableWatcher(ActionableWatcher):
    """ Subclass of ActionableWatcher that is used when running in a
    container"""

    def __init__(self):
        ActionableWatcher.__init__(self)
        self.platformType = "container"

    def addPatterns(self, patternList):
        for aPattern in patternList:
            # separate out the directory from the pattern
            aDirectory = os.path.dirname(aPattern)

            # and if the directory has an evironment variable, change it out
            if aDirectory.startswith("$HOME"):
                replacementDir = aDirectory.replace("$HOME", "")
                aDirectory = aDirectory.replace("$HOME", expanduser("~"))

            # convert the given directory to a container directory
            # prepend the dcWatch directory to the directory and when the
            # aDirectory is mounted in the container it will be in a place
            # that is known to the watchdog process
            aContainerDirectory = '/dcWatcher/volumes' + replacementDir

            # add the directory if there isn't one already there
            if (aDirectory, aContainerDirectory) not in self.directories:
                self.directories.append((aDirectory, aContainerDirectory))

            # and now get the pattern
            justThePattern = os.path.basename(aPattern)
            self.patterns.append((justThePattern, aContainerDirectory))


class InstanceActionableWatcher(ActionableWatcher):
    """ Subclass of ActionableWatcher that is used when running in a
    instance"""

    def __init__(self):
        ActionableWatcher.__init__(self)
        self.platformType = "instance"

    def addPatterns(self, patternList):
        for aPattern in patternList:
            # separate out the directory from the pattern
            aDirectory = os.path.dirname(aPattern)

            # and if the directory has an evironment variable, change it out
            if aDirectory.startswith("$HOME"):
                replacementDir = aDirectory.replace("$HOME", expanduser("~"))
                aDirectory = replacementDir

            # add the directory if there isn't one already there
            if (aDirectory, aDirectory) not in self.directories:
                self.directories.append((aDirectory, aDirectory))

            # and now get the pattern
            justThePattern = os.path.basename(aPattern)
            self.patterns.append((justThePattern, aDirectory))


def readConfigFile(configFileNameIn, platformTypeIn):
    """Read the configuration file and create a list ActionableWatcher
        instances based upon the hostTypeIn"""
    data = []
    with open(configFileNameIn) as data_file:
        data = json.load(data_file)

        # for line in data_file:
        #     data.append(json.loads(line))

    returnList = []
    for item in data:
        # first create an instance of an ActionableWatcher
        actionableItem = ''
        if platformTypeIn == 'instance':
            actionableItem = InstanceActionableWatcher()
        else:
            actionableItem = ContainerActionableWatcher()

        # and now fill it
        if 'otherHosts' in item.keys():
            actionableItem.addOtherHosts(item['otherHosts'])
        if 'action' in item.keys():
            actionableItem.addAction(item['action'])
        if 'patterns' in item.keys():
            actionableItem.addPatterns(item['patterns'])
        if 'options' in item.keys():
            actionableItem.addOptions(item['options'])

        # and now add it to the list that will be returned
        returnList.append(actionableItem)

    # and return the list that was created
    return returnList


def generateComposeYML(anActionableList):
    """ generate the  yml file that can be used with docker-compose
        and by default put in the $HOME/.devops.center/dcWatcher directory."""

    # ok lets try to open the file for writing
    generateFile = "dcWatcher-compose.yml"
    try:
        fileHandle = open(generateFile, 'w')
        strToWrite = (
            "version: '2'\n"
            "#\n"
            "# Compose definition for dcWatcher containers\n"
            "#\n"
            "services:\n"
            "   dcWatcher:\n"
            '       container_name: "dcWatcher"\n'
            '       hostname: "dcWatcher"\n'
            '       image: "devopscenter/dcwatcher:${CONTAINER_VERSION}"\n'
            "       volumes:\n"
            "         - ./config:/dcWatcher/config\n")
        fileHandle.write(strToWrite)

        # get the directories from each of actionable items
        localDirList = []
        for anItem in anActionableList:
            dirList = anItem.getDirectories()
            for dir in dirList:
                # and build up a local dir list that will have unique
                # directries that will be used to mount to the container
                # ie, we don't need duplicates
                if (dir[0], dir[1]) not in localDirList:
                    localDirList.append(dir)

        # and put this unique list out in the compose file
        for outDir in localDirList:
            fileHandle.write("         - {}:{}\n".format(outDir[0], outDir[1]))

        # close out the fileHandle properly
        fileHandle.close()

    except IOError:
        print 'Unable to write to the dcWatcher-compose.yml file in the' + \
            ' given configDir: \n' + generateFile
        sys.exit(1)


def checkArgs():
    parser = argparse.ArgumentParser(
        description='Script that provides a facility to watch for file ' +
                    'changes and then perform actions based upon the files' +
                    ' that change.')
    parser.add_argument('-c', '--configFile', help='Directory that contains ' +
                        'the dcWatcher configuration file and the action ' +
                        'scripts. (Default: ./config/dcWatcher.json)',
                        required=False,
                        default='./config/dcWatcher.json')
    parser.add_argument('-p', '--platformType', help='This is either the word' +
                        ' instance or container to give direction on how' +
                        ' to use the directories in the config. ' +
                        '(Default: instance)',
                        choices=['instance', 'container'],
                        required=False,
                        default='container')
    parser.add_argument('-g', '--generate', help='This option will tell the' +
                        ' script to ONLY generate the dcWatcher-compose.yml' +
                        ' that can be used to bring up a container running' +
                        ' this dcWatcher.py script using this same config' +
                        ' and will terminate.  It will not run the watchdog' +
                        ' process.  This would be used if the platformType ' +
                        ' will be of type "container" ',
                        action='store_true')
    args = parser.parse_args()

    # try to read the configuration to make sure it is there
    retConfFile = args.configFile
    try:
        tmpFileHandle = open(retConfFile, 'r')
        tmpFileHandle.close()

    except IOError:
        print 'Unable to access the config file in the given configDir: \n' + \
            retConfFile
        sys.exit(1)

    # need to see if the option to generate is used and if so assign the
    # platformType to container just in case it is not that way.  Otherwise
    # just take whatever the args.platformType is
    if args.generate:
        platformType = 'container'
    else:
        platformType = args.platformType

    # if we get here then the
    return (retConfFile, platformType, args.generate)


def main(argv):
    (configFileName, platformType, generateCompose) = checkArgs()
    # print 'Configuration file is: ' + configFileName
    # print 'Host type is: ' + hostType

    # read the config file and load up the ActionableWatcher list
    actionableList = readConfigFile(configFileName, platformType)

    # check to see if we only want to generate the dcWatch-compose.yml
    # and if so just run it and not the watchdog.  This is usually done
    # prior to running the dcWatcher.py in a container so that the container
    # can be started first and then once inside the container it will run
    # the watchdog process
    if generateCompose:
        # generate the compose.yml that can be used with docker-compose
        generateComposeYML(actionableList)
    else:
        theWatcher = DCWatchDog(actionableList)
        theWatcher.run()


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
