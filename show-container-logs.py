#!/usr/bin/env python
# flake8: noqa
import sys
import subprocess
import argparse

# ==============================================================================
"""
This script will read the available local docker containers and show it's logs
"""
__version__ = "0.1"

__copyright__ = "Copyright 2016, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================


def checkArgs():
    parser = argparse.ArgumentParser(
        description=('This script will show the container log for a selected '
                     'docker container that is running.'))
    parser.parse_args()


def main(argv):
    try:
        checkArgs()
    except SystemExit:
        sys.exit(1)

    # Create an array from the current running Docker containers
    cmdToRun = 'docker ps --format "{{.Names}}"'
    runningContainers = subprocess.check_output(cmdToRun, shell=True)
    containerList = runningContainers.split()

    if(len(containerList) < 1):
        print "There are no containers running. exiting"
        sys.exit(1)

    # Display the menu to have the user select the container to log in to
    for num, container in enumerate(containerList, start=1):
        print('{}. {}'.format(num, container))

    # get the one they want
    containerResponse = raw_input("Enter the number (return to quit): ")
    # check to see if they don't want to continue
    if containerResponse.isdigit():
        containerResponse = int(containerResponse)
    else:
        sys.exit()

    containerToUse = containerList[containerResponse-1]

    # and now do it log into a container
    print "\nDumping logs for: " + containerToUse
    print
    dockerCmdToRun = "docker logs -t " + containerToUse
    subprocess.check_call(dockerCmdToRun, shell=True)


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4