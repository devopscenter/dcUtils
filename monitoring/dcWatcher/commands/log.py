#!/usr/bin/env python
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
