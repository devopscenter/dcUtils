#!/usr/bin/env python
import os
import sys
import subprocess
import argparse

# ==============================================================================
"""
this script will pull the files from S3 for a customer and allow them to
look through the files to see which one they would want to download
"""
__version__ = "0.1"

__copyright__ = "Copyright 2016, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================


class EnvironmentDescription:
    """Class to provide a devops.center specific, very simplistic, AWS S3
    browsing with file transfer capability."""
    envType = ''
    appName = ''
    topLevel = ''
    topLevelInstanceName = ''
    destinationDir = ''

    def __init__(self, appNameIn,  envTypeIn, destDirIn, profileIn, dbNameIn):
        """creates an instance of EnvironmentDescription that takes the
        customer or application name, environmentType (dev,test,staging,prod)
        and the destination directory for where the selected backup file will be
        downloaded to."""
        self.envType = envTypeIn
        self.appName = appNameIn
        self.profile = profileIn
        self.destinationDir = destDirIn
        self.dbName = dbNameIn
        self.topLevel = self.appName + "-" + self.envType + "-postgres-backup"

    def getInstanceNames(self):
        cmdToRun = 'aws --profile ' +  \
            self.profile + ' s3 ls s3://' + self.topLevel
        try:
            tmpNames = subprocess.check_output(cmdToRun, shell=True)
        except subprocess.CalledProcessError:
            print "There was an problem retrieving the instances for the " + \
                  "path: {}".format(self.topLevel)
            sys.exit(1)

        tmpNamesList = tmpNames.split()
        i = 0
        returnNameList = []
        while i < len(tmpNamesList):
            if(tmpNamesList[i] != 'PRE'):
                returnNameList.append(tmpNamesList[i].replace('/', ''))

            i += 1
        return returnNameList

    def getBackupFilesList(self, topLevelInstanceNameIn):
        self.topLevelInstanceName = topLevelInstanceNameIn

        cmdToRun = 'aws --profile ' +  \
            self.appName + \
            ' s3 ls --recursive s3://' + \
            self.topLevel
        tmpNames = subprocess.check_output(cmdToRun, shell=True)
        tmpNamesList = tmpNames.split()
        # now go through the list and get the specific backup file

        i = 0
        fileToLookFor = self.dbName + '.sql.gz'
        returnBackupFileList = []
        while i < len(tmpNamesList):
            if(tmpNamesList[i].startswith(self.topLevelInstanceName)):
                if(tmpNamesList[i].find(fileToLookFor) >= 0):
                    instanceNameToRemove = self.topLevelInstanceName + '/'
                    returnBackupFileList.append(
                        (tmpNamesList[i].replace(instanceNameToRemove, ''),
                         tmpNamesList[i-1]))
            i += 1
        return returnBackupFileList

    def downloadBackupFile(self, backupFileName):
        print "Downloaded to " + self.destinationDir + " ...please wait"
        cmdToRun = 'aws --profile ' +  \
            self.appName + \
            ' s3 cp s3://' + \
            self.topLevel + '/' + \
            self.topLevelInstanceName + '/' + \
            backupFileName + ' ' + \
            self.destinationDir

        # print cmdToRun
        subprocess.check_output(cmdToRun, shell=True)
        print "complete\nNOTE: Use this name for input to restoredb.sh:"
        print os.path.basename(backupFileName)

    def setType(self, envTypeIn):
        EnvironmentDescription.envType = envTypeIn

    def getType(self):
        return EnvironmentDescription.envType

    def getTopLevelName(self):
        return self.topLevel


def checkArgs(inputArgs):
    parser = argparse.ArgumentParser(
        description='this script will pull the files from S3 for a customer ' +
        'and allow them to look through the files to see which one they ' +
        'would want to download')
    parser.add_argument('-d', '--destDir', help='Destination directory to ' +
                        'put the downloaded backup file into', required=True)
    parser.add_argument('-e', '--env', help='Provide the environment name' +
                        'to use to look for in the s3 bucket', required=False)
    parser.add_argument('-D', '--dbName', help='Provide the database name',
                        required=True)
    parser.add_argument('-p', '--profile', help='Provide the AWS profile ' +
                        'name to use when looking for in the s3 bucket',
                        required=False)
    parser.add_argument('-a', '--appName', help='application or database name' +
                        'for the customer.  This name will be used to filter' +
                        'the files on the S3 server.  THis is also the ' +
                        'value that is defined in your .aws config',
                        required=True)
    args = parser.parse_args()

    print 'Destination directory is: ', args.destDir
    print 'Application name is: ', args.appName
    print 'Environment name is: ', args.env
    print 'AWS Profile name is: ', args.profile

    # before going further we need to check whether there is a slash at the
    # end of the value in destinationDir
    if(args.destDir.endswith('/')):
        destinationDir = args.destDir
    else:
        destinationDir = args.destDir + '/'

    try:
        # lets try to write to that directory
        tmpFile = destinationDir + '.removeme'
        tmpFileHandle = open(tmpFile, 'w')
        tmpFileHandle.close()
        os.remove(tmpFile)

    except IOError:
        print 'Unable to access destination directory: ' + \
            destinationDir
        sys.exit(1)

    return destinationDir, args.appName, args.env, args.profile, args.dbName


def main(argv):
    # get the destination directory for the backup file download and
    # make sure it is available and writeable by this user
    (destDir, appName, env, profile, dbName) = checkArgs(argv)

    envToUse = env

    print "You selected: ", envToUse

    anEnv = EnvironmentDescription(appName, envToUse, destDir, profile,
                                   dbName)
    print anEnv.getTopLevelName()
    instanceNames = anEnv.getInstanceNames()

    for num, instantType in enumerate(instanceNames, start=1):
        print('{}. {}'.format(num, instantType))

    instanceResponse = int(raw_input(
        "Enter the number of the instance for the backup (0 to exit): "))
    if(instanceResponse == 0):
        sys.exit(1)
    instanceToUse = instanceNames[instanceResponse-1]
    # print "You selected: ", instanceToUse

    # get the backup files list for this instance
    backupFiles = anEnv.getBackupFilesList(instanceToUse)
    for num, backupFile in enumerate(backupFiles, start=1):
        print('{}. {} (size=> {})'.format(num, backupFile[0], backupFile[1]))

    # have the user select one
    backupFileResponse = int(raw_input(
        "Enter the number of the backupfile to download (0 to exit): "))
    if(backupFileResponse == 0):
        sys.exit(1)
    backupToUse = backupFiles[backupFileResponse-1][0]
    # print "You selected: ", backupToUse

    # and now download it
    anEnv.downloadBackupFile(backupToUse)

if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
