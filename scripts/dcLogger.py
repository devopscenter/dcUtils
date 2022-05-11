#!/usr/bin/env python
"""Log class to a remote rsyslog."""
# ==============================================================================
#
#          FILE: dcLogger.py
#
#         USAGE: dcLogger.py
#
#   DESCRIPTION: logging function to standardize logging
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 01/25/2017 16:54:43
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
import fileinput
from logging.handlers import SysLogHandler
# ==============================================================================
__version__ = "0.1"

__copyright__ = "Copyright 2016, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================


class ContextFilter(logging.Filter):
    """Class that will get and hold the hostname."""

    hostname = socket.gethostname()

    def filter(self, record):
        """Create the filter that holds the hostname."""
        record.hostname = ContextFilter.hostname
        return True


class dcLogger():
    """Class to express logs to a remote server."""

    def __init__(self, app, logLevel="warn"):
        """Construct a dcLogger."""
        self.app = app
        self.message = ""
        self.aFile = ""
        self.logger = logging.getLogger()
        if logLevel == "error":
            self.logger.setLevel(logging.ERROR)
        elif logLevel == "debug":
            self.logger.setLevel(logging.DEBUG)
        elif logLevel == "info":
            self.logger.setLevel(logging.INFO)
        elif logLevel == "warn":
            self.logger.setLevel(logging.WARN)
        elif logLevel == "critical":
            self.logger.setLevel(logging.CRITICAL)
        elif logLevel == "fatal":
            self.logger.setLevel(logging.FATAL)
        else:
            self.logger.setLevel(logging.WARN)

        aFilter = ContextFilter()
        self.logger.addFilter(aFilter)

        syslog = SysLogHandler(address=('logs3.papertrailapp.com', 26597))
        formatterText = '%(asctime)s %(hostname)s {}: %(message)s'.format(app)
        formatter = logging.Formatter(
            formatterText,
            datefmt='%b %d %H:%M:%S')

        syslog.setFormatter(formatter)
        self.logger.addHandler(syslog)

    def logOutput(self, message):
        """Write out a message to the remote log tool."""
        # logger.info("{}".format(message))
        self.logger.warning(message)

    def logFileToOutput(self, aFile):
        """Write out a file to the remote log tool."""
        # read the file and push each line out to the log destination
        if os.path.isfile(aFile):
            for line in fileinput.input(aFile):
                self.logger.warn("{}".format(line))

            fileinput.close()


def checkArgs(inputArgs):
    """Check the input arguments."""
    parser = argparse.ArgumentParser(
        description='This script will log the output to papertrail')
    parser.add_argument('-m', '--message', help='the message to log',
                        nargs='*',
                        required=False)
    parser.add_argument('-a', '--app', help='The application you want to show'
                        ' in the log file',
                        default='dcLogger',
                        required=False)
    parser.add_argument('-f', '--file', help='Write this file to the log',
                        required=False)
    args = parser.parse_args()

    retMessage = ""
    if args.message:
        retMessage = " ".join(args.message)

    retApp = ""
    if args.app:
        retApp = args.app

    retFile = ""
    if args.file:
        retFile = args.file

    return (retApp, retMessage, retFile)


def main(argv):
    """Defined main function."""
    (app, message, aFile) = checkArgs(argv)
    aDCLogger = dcLogger(app)
    if aFile:
        aDCLogger.logFileToOutput(aFile)
    else:
        aDCLogger.logOutput(message)


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
