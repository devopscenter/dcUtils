#!/usr/bin/env python
# import shutil
import sys
import argparse
# import subprocess
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


class UpdateComponent:

    def __init__(self, theAppName, workspaceName):
        """UpdateComponent constructor"""
        self.appName = theAppName
        self.workspaceName = workspaceName.upper()

    def run(self):
        print "hello"
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


# ==============================================================================


def checkArgs():
    parser = argparse.ArgumentParser(
        description='This script provides an administrative interface to a ' +
        'customers application set that is referred to as appName.  The ' +
        'administrative functions implement some of the CRUD services ' +
        '(ie, Create, Update, Delete).')
    parser.add_argument('-k', '--deployKey', help='The deploy key that will' +
                        'used to access the repository from the component.',
                        required=True)

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

    # if we get here then the
    return (retAppName, retWorkspaceName)


def main(argv):
    (appName, workspaceName) = checkArgs()

    customerApp = UpdateComponent(appName, workspaceName)
    customerApp.run()


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
