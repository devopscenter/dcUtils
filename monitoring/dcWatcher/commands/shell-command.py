#!/usr/bin/env python
# ==============================================================================
#
#          FILE: shell-command.sh
#
#         USAGE:
#
#   DESCRIPTION:
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

import os
import sys
import argparse
import logging
import socket
import subprocess
from logging.handlers import SysLogHandler
from os.path import expanduser
# ==============================================================================
"""
watchdog cmd script to run a set of shell commands(s) given as the argument
to the action when the file pattern is triggered.  This could be used to restart
processes or execute shell commands to maybe sync files between two places.
The shell commands are given in the dcWatcher.conf and will be executed here.
"""
__version__ = "0.1"

__copyright__ = "Copyright 2016, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================


class ContextFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True


def checkArgs(inputArgs):
    parser = argparse.ArgumentParser(
        description="""
watchdog cmd script to run a set of shell commands(s) given as the argument
to the action when the file pattern is triggered.  This could be used to restart
processes or execute shell commands to maybe sync files between two places.
The shell commands are given in the dcWatcher.conf and will be executed here.
        """)
    parser.add_argument('-s', '--srcFile', help='event source path',
                        required=True)
    parser.add_argument('-e', '--eventType', help='modified, deleted, ' +
                        'created,added', required=True)
    parser.add_argument('-o', '--objectType', help='either file or directory',
                        required=True)
    parser.add_argument('-c', '--containers',
                        help='other hosts or containers to run the action on',
                        required=False)
    parser.add_argument('-a', '--args',
                        help='a set of shell commands to restart processes',
                        required=True)
    args = parser.parse_args()
    return args


def addPathsToCmdToRun(argsIn, cmdToRunIn):
    destFile = os.path.basename(argsIn.srcFile)
    retCmdToRun = cmdToRunIn.replace("$srcFile", argsIn.srcFile)
    retCmdToRun = retCmdToRun.replace("$destFile", destFile)
    retCmdToRun = retCmdToRun.replace("$HOME", expanduser("~"))
    return (retCmdToRun)


def executeCommand(inputArgs):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    aFilter = ContextFilter()
    logger.addFilter(aFilter)

    syslog = SysLogHandler(address=('logs3.papertrailapp.com', 26597))
    formatter = logging.Formatter(
        '%(asctime)s %(hostname)s dcWatcher-shell-command: %(message)s',
        datefmt='%b %d %H:%M:%S')

    syslog.setFormatter(formatter)
    logger.addHandler(syslog)

    cmdToRun = '/bin/bash -c "' + inputArgs.args + '"'

    containerList = []
    if inputArgs.containers:
        if "," in inputArgs.containers:
            containerList = inputArgs.containers.split(",")
        else:
            containerList.append(inputArgs.containers)

        # now we determine if we nneed to run the restart command on a container
        # or do it locally.  The container command will be different that
        # running it locally
        if len(containerList) > 0:
            # lets do it for each container
            for container in containerList:
                cmdToRunWithContainer = "docker exec -it " + \
                    container + " " + cmdToRun

                # substitue the srcFile and destFile if they exist in the
                # command to run
                finalCmdToRun = addPathsToCmdToRun(
                    inputArgs, cmdToRunWithContainer)

                # and now execute the command
                logger.info("command with container to execute-< {} >".format(
                    finalCmdToRun))
                theProcess = subprocess.Popen(finalCmdToRun, shell=True)
                theProcess.wait()
                logger.info("finished execution of-< {} >".format(
                    finalCmdToRun))

    else:

        # substitue the srcFile and destFile if they exist in the
        # command to run
        finalCmdToRun = addPathsToCmdToRun(inputArgs, cmdToRun)

        # and now execute the command
        logger.info("command to execute-< {} >".format(finalCmdToRun))
        theProcess = subprocess.Popen(finalCmdToRun, shell=True)
        theProcess.wait()
        logger.info("finished execution of-< {} >".format(finalCmdToRun))


def main(argv):
    args = checkArgs(argv)
    if args:
        executeCommand(args)


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
