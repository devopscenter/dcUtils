#!/usr/bin/env python
import sys
import os
import argparse
import subprocess
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


class UpdateInstance:

    def __init__(self, theAppName, theEnv, aDeployKey, theTarget, aBranch,
                 theAccessKey):
        """UpdateComponent constructor"""
        self.appName = theAppName
        self.env = theEnv
        self.deployKey = aDeployKey
        self.target = theTarget
        self.branch = aBranch
        self.accessKey = theAccessKey
        self.targetUser = "ubuntu"

    def run(self):
        if not os.path.isfile(self.accessKey):
            print "ERROR: file not found: {}".format(self.accessKey)
            sys.exit(1)

        # ----------------------------------------------------------------------
        # First copy the update script over to the instance
        # ----------------------------------------------------------------------
        cmdToRun = ("scp -i " + self.accessKey +
                    " scripts/updateAppOnInstance.sh " +
                    self.targetUser + "@" + self.target + ":~")
        self.remoteRun(cmdToRun)

        # ----------------------------------------------------------------------
        # Now do run the command on the instance
        # ----------------------------------------------------------------------
        cmdToRun = ("ssh -i " + self.accessKey + " " +
                    self.targetUser + "@" + self.target +
                    " ./updateAppOnInstance.sh " +
                    "--appName " + self.appName + " " +
                    "--env " + self.env + " " +
                    "--deployKey " + self.deployKey + " ")
        if self.branch:
            cmdToRun += ("--branch " + self.branch)

        self.remoteRun(cmdToRun)

        # ----------------------------------------------------------------------
        # Now remove the update script on the remote instance
        # ----------------------------------------------------------------------
        # self.remoteRun("rm updateAppOnInstance.sh")

    def remoteRun(self, cmdToRun):
        try:
            subprocess.check_output(cmdToRun,
                                    stderr=subprocess.STDOUT,
                                    shell=True)
        except subprocess.CalledProcessError as details:
            print "Error {}\n{}".format(details, details.output)
            sys.exit(1)

# ==============================================================================


def checkArgs():
    parser = argparse.ArgumentParser(
        description='This script provides an administrative interface to a ' +
        'customers application to perform an update on a target instance. ' +
        'Once the configuration has been ' +
        'changed and committed to the respository, call this script to ' +
        'have the code be updated on the instance. ')
    parser.add_argument('-x', '--accessKey', help='The access key to use ' +
                        'when accessing the instance',
                        required=False)
    parser.add_argument('-k', '--deployKey', help='The deploy key that will' +
                        ' be used to access the repository from the instance.',
                        required=False)
    parser.add_argument('-t', '--target', help='The target instance to have ' +
                        ' the update performed on.',
                        required=True)
    parser.add_argument('--custUtilsBranch', help='If you need to be on a' +
                        'certain branch for the customer utiliies repo ' +
                        'before the update can be run. Otherwise it will ' +
                        'just update the current branch that is currently ' +
                        'checked out',
                        required=False)
    parser.add_argument('--dcUtilsBranch', help='If you need to be on a' +
                        'certain branch for the dcUtils repo ' +
                        'before the update can be run. Otherwise it will ' +
                        'just update the current branch that is currently ' +
                        'checked out',
                        required=False)
    parser.add_argument('--dcStackBranch', help='If you need to be on a' +
                        'certain branch for the dcStack repo ' +
                        'before the update can be run. Otherwise it will ' +
                        'just update the current branch that is currently ' +
                        'checked out',
                        required=False)

    try:
        args, unknown = parser.parse_known_args()
    except SystemExit:
        pythonGetEnv()
        sys.exit(1)

    retEnvList = pythonGetEnv()

    if retEnvList["CUSTOMER_APP_NAME"]:
        retAppName = retEnvList["CUSTOMER_APP_NAME"]

    if retEnvList["ENV"]:
        retEnv = retEnvList["ENV"]

    # get the key path in case we need it
    keyPath = retEnvList["BASE_CUSTOMER_DIR"] + '/' + \
        retEnvList["dcDEFAULT_APP_NAME"] + '/' + \
        retEnvList["CUSTOMER_APP_UTILS"] + "/keys/"

    if args.accessKey:
        retAccessKey = args.accessKey
    else:
        retAccessKey = keyPath + retEnvList["CUSTOMER_APP_ENV"] + '/' + \
            retEnvList["dcDEFAULT_APP_NAME"] + '-' + \
            retEnvList["CUSTOMER_APP_ENV"] + "-access.pem"

    if args.deployKey:
        retDeployKey = args.deployKey
    else:
        for file in os.listdir(keyPath):
            if file.endswith(".pub"):
                retDeployKey = file.replace(r".pub", '')
                break

        if not retDeployKey:
            print "ERROR: The deploy key can not be determined " \
                    "automatically you will need to pass the name " \
                    "with the option --deployKey(-k)."

    retTarget = args.target
    # TODO START HERE!!  need to define separate branch name for each of
    # dcStack, dcUtils and app-utils.  ALSO, the app shell will need these
    # branches.  The shell script will also need to pull dcStack and dcUtils
    retBranch = args.custUtilsBranch

    # if we get here then the
    return (retAppName, retEnv, retDeployKey, retTarget, retBranch,
            retAccessKey)


def main(argv):
    (appName, env, deployKey, target, branch, accessKey) = checkArgs()

    customerApp = UpdateInstance(appName, env, deployKey, target, branch,
                                 accessKey)
    customerApp.run()


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
