#!/usr/bin/env python
import sys
import argparse
import json
from pprint import pprint
import subprocess
import re
from datetime import datetime
# ==============================================================================
"""
This script will access AWS for a given profile and check for any reserved
instances that will expire within a month from the script is run.
"""
__version__ = "0.1"

__copyright__ = "Copyright 2016, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================


class AWSCommand:
    """Class that takes a list of ActionableWatchers and executes separate
       watchdog processes for each item in the list"""

    def __init__(self, profileNameIn):
        """Creates the instance with the given profile name and cmmand"""
        self.profileName = profileNameIn
        self.cmdToRun = ""

    def run(self, cmdToRunIn):
        self.cmdToRun = cmdToRunIn
        method = getattr(self, self.cmdToRun, lambda: "nothing")
        return method()

    def getListOfInstances(self):
        awsCmd = ("aws --profile " + self.profileName +
                  " ec2 describe-instances")

        data = subprocess.check_output(awsCmd, shell=True)
        awsOutput = json.loads(data)
        return awsOutput

    def getReservedTypeAndDate(self):
        awsCmd = ("aws --profile " + self.profileName +
                  " ec2 describe-reserved-instances | grep " +
                  "-e InstanceType -e End")

        awsOutput = subprocess.check_output(awsCmd, shell=True)
        # split the output on the comman giving a list of start and instance
        # type.  Because we know that we are just going through the string
        # as it comes we know that the start and instanceType will end up
        # next to each other.
        awsOutputList = awsOutput.split(',')
        reservedList = []
        i = 0
        while i < len(awsOutputList):
            # print "[{}] =>{}<=".format(i, awsOutputList[i])
            if "End" in awsOutputList[i]:
                # the end line initially looks something like:
                # "End": "2016-03-04T22:33:31.659Z"
                # quotes and all.  So the regular expression below will
                # find all the strings in side each of the double quotes.
                # that returns a list.  We want the second one so we pull
                # the index of 1.  Then from that result we only want the
                # first 10 characters.  and that gives the date we can use
                fullEndDateAndTime = re.findall('"(.*?)"', awsOutputList[i])[1]
                endDate = re.findall('"(.*?)"', awsOutputList[i])[1][:10]
                # print endDate
                # now we want to increase the index count to get the associated
                # instanceType for this date
                i += 1
                instanceType = re.findall('"(.*?)"', awsOutputList[i])[1]
                # print instanceType
                # and finally put the tuple in the list
                reservedList.append((endDate, instanceType, fullEndDateAndTime))

            i += 1

        return(reservedList)

    def checkReservedInstanceRenewal(self):
        reservedTypeAndDateList = self.getReservedTypeAndDate()
        # for item in reservedTypeAndDateList:
        #    print "[{}] date: {}".format(item[1], item[0])

        instanceList = self.getListOfInstances()

        returnList = []
        for key in instanceList["Reservations"]:
            for inst in key['Instances']:
                if inst["State"]["Name"] == "running":
                    # get the name
                    for tags in inst["Tags"]:
                        if tags["Key"] == "Name":
                            instanceName = tags["Value"]
                            # if there is a name then get the instanceType
                            instanceType = inst["InstanceType"]

                            # push them onto the list
                            returnList.append((instanceName, instanceType))

        # go through the reserved list and check for any dates that are going
        # to expire one month from now.  And then print out the names that
        # are in that class that will/could be associated
        now = datetime.now()
        date_format = '%Y-%m-%d'
        for reservedItem in reservedTypeAndDateList:
            reservedDate = datetime.strptime(reservedItem[0], date_format)
            diff = reservedDate - now
            # print "diff: {} reservedDate: {} and now: {} ".format(
            #    diff.days, reservedDate, now)
            # now if any of those days are between 330-365 go through the
            # instance list and get the name
            if diff.days < 30 and diff.days > -30:
                if diff.days <= -2:
                    print "These appear to be past due:"
                elif diff.days >= -1 and diff.days <= 0:
                    print "These appear to be due today:."
                else:
                    print "These appear to be coming due:."
                # go through the instance list and get the name
                for instance in returnList:
                    if reservedItem[1] == instance[1]:
                        print "[{}] {} reserved instance ends: {}".format(
                            reservedItem[1], instance[0], reservedItem[2])

    def listInstances(self):
        print "going to do listInstances"
        instanceList = self.getListOfInstances()

        for item in instanceList["Reservations"]:
            pprint(item)


def checkArgs():
    parser = argparse.ArgumentParser(
        description='Script that provides a facility to execute various ' +
                    'AWS commands and show the output')
    parser.add_argument('--customerAppName', help='Name of the appName  ' +
                        'in which to execute the AWS command',
                        required=True)
    parser.add_argument('-c', '--command', help='The AWS command action ' +
                        'to be performed:',
                        choices=["listInstances",
                                 "checkReservedInstanceRenewal"],
                        required=True,
                        default='container')
    args = parser.parse_args()

    retProfileName = args.customerAppName
    retCommand = args.command

    # if we get here then the
    return (retProfileName, retCommand)


def main(argv):
    (profileName, cmdToRun) = checkArgs()
#    print 'customerAppName/profileName is: ' + profileName
#    print 'cmdToRun is: ' + cmdToRun

    awsCmd = AWSCommand(profileName)
    awsCmd.run(cmdToRun)


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
