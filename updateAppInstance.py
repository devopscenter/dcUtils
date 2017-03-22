#!/usr/bin/env python
# import shutil
import sys
import argparse
import subprocess
# from time import time
# import fileinput
# import re
from scripts.process_dc_env import pythonGetEnv
# ==============================================================================
"""
After an update and push to the application repository the code on the
component (ie, docker container or instance) needs have it's code updated from
the repository. This script will perform the necessary actions to get the
destination compoonent up to date.
"""
__version__ = "0.1"

__copyright__ = "Copyright 2016, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================

# - ssh into the instance
# - eval `ssh-agent`
# - ssh-add the deploy-key (may have to get this from the command line and
#      it needs to be in ~/.ssh)
# - cd app/app-utils
# - git pull origin
#  - cd ~/dcUtils
# - ./deployenv.sh --type instance --env $ENV --appName ${CUST_APP_NAME}
# - logout to ensure it takes effect (ie, it may be exported by
#      deployenv.sh which would negate the need to logout and logon)


class UpdateInstance:

    def __init__(self, theAppName, workspaceName, aDeployKey, theTarget,
                 aBranch):
        """UpdateComponent constructor"""
        self.appName = theAppName
        self.workspaceName = workspaceName.upper()
        self.deployKey = aDeployKey
        self.target = theTarget
        self.branch = aBranch

    def run(self):
        cmdToRun = 'scp scripts/updateAppOnComponent.sh ~'
        try:
            appOutput = subprocess.check_output(cmdToRun,
                                                stderr=subprocess.STDOUT,
                                                shell=True)
        except subprocess.CalledProcessError as details:
            print "Error {}\n{}".format(details, appOutput)
            sys.exit(1)

# ==============================================================================


def checkArgs():
    parser = argparse.ArgumentParser(
        description='This script provides an administrative interface to a ' +
        'customers application to perform an update on a target component ' +
        '(ie instance or container).  Once the configuration has been ' +
        'changed and committed to the respository, call this script to ' +
        'have the code be updated on the component. ')
    parser.add_argument('-k', '--deployKey', help='The deploy key that will' +
                        'used to access the repository from the component.',
                        required=True)
    parser.add_argument('-t', '--target', help='The target component ' +
                        '(ie, instance or container) to have the update ' +
                        'performed on.',
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

    if "WORKSPACE_NAME" in retEnvList:
        retWorkspaceName = retEnvList["WORKSPACE_NAME"]
    else:
        retWorkspaceName = ''

    retDeployKey = args.deployKey
    retTarget = args.target
    retBranch = args.branch

    # if we get here then the
    return (retAppName, retWorkspaceName, retDeployKey, retTarget, retBranch)


def main(argv):
    (appName, workspaceName, deployKey, target, branch) = checkArgs()

    customerApp = UpdateInstance(appName, workspaceName, deployKey, target,
                                  branch)
    customerApp.run()


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
