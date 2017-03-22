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
                    " :scripts/updateAppOnComponent.sh " +
                    self.targetUser + "@" + self.target + ":~")
        self.remoteRun(cmdToRun)

        # ----------------------------------------------------------------------
        # Now do run the command on the instance
        # ----------------------------------------------------------------------
        cmdToRun = ("./updateAppOnComponent.sh " +
                    self.self.appName + " " +
                    self.env + " " +
                    self.deployKey + " ")
        self.remoteRun(cmdToRun)

        # ----------------------------------------------------------------------
        # Now remove the update script on the remote instance
        # ----------------------------------------------------------------------
        self.remoteRun("rm updateAppOnComponent.sh")

    def remoteRun(self, cmdToRun):
        try:
            updateOutput = subprocess.check_output(cmdToRun,
                                                   stderr=subprocess.STDOUT,
                                                   shell=True)
        except subprocess.CalledProcessError as details:
            print "Error {}\n{}".format(details, updateOutput)
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
                        required=True)
    parser.add_argument('-k', '--deployKey', help='The deploy key that will' +
                        ' be used to access the repository from the instance.',
                        required=True)
    parser.add_argument('-t', '--target', help='The target instance to have ' +
                        ' the update performed on.',
                        required=True)
    parser.add_argument('-b', '--branch', help='If you need to be on a' +
                        'certain branch before the update can be run',
                        required=False)

    try:
        args, unknown = parser.parse_known_args()
    except SystemExit:
        pythonGetEnv()
        sys.exit(1)

    retEnvList = pythonGetEnv(initialCreate=True)

    if retEnvList["CUSTOMER_APP_NAME"]:
        retAppName = retEnvList["CUSTOMER_APP_NAME"]

    if retEnvList["ENV"]:
        retEnv = retEnvList["ENV"]

    retAccessKey = args.accessKey
    retDeployKey = args.deployKey
    retTarget = args.target
    retBranch = args.branch

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
