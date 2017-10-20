#!/usr/bin/env python
# ==============================================================================
#
#          FILE: log.py
#
#         USAGE: .log.py
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

import sys
import argparse
import logging
import socket
from logging.handlers import SysLogHandler
# ==============================================================================
"""
watchdog cmd script to log the output to a file
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
        description='This script will log the output of the watchmedo script')
    parser.add_argument('-s', '--srcPath', help='event source path',
                        required=True)
    parser.add_argument('-e', '--eventType', help='modified, deleted, ' +
                        'created,added', required=True)
    parser.add_argument('-o', '--objectType', help='either file or directory',
                        required=True)
    parser.add_argument('-c', '--containers',
                        help='other hosts or containers to run the action on',
                        required=False)
    args = parser.parse_args()
    return args


def logOutput(inputArgs):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    aFilter = ContextFilter()
    logger.addFilter(aFilter)

    syslog = SysLogHandler(address=('logs3.papertrailapp.com', 26597))
    formatter = logging.Formatter(
        '%(asctime)s %(hostname)s dcWatcher-log: %(message)s',
        datefmt='%b %d %H:%M:%S')

    syslog.setFormatter(formatter)
    logger.addHandler(syslog)

    logger.info("event-<{}> object-<{}> src_path-<{}>".format(
        inputArgs.eventType, inputArgs.objectType, inputArgs.srcPath))
    # print "event-<{}> object-<{}> src_path-<{}>".format(
    #    inputArgs.eventType, inputArgs.objectType, inputArgs.srcPath)


def main(argv):
    args = checkArgs(argv)
    if args:
        logOutput(args)


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
