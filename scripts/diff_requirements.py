#!/usr/bin/env python
import os
import os.path
import sys
import argparse
# ==============================================================================
"""
This script will do a diff between the customers requirments.txt file(s) and
the requirements.txt files that are given for the devops.center web
stack.  There could be multiple files from each and it will read the contents
of each file make 2 lists of key/value pairs.  These two lists will be diff'ed
and output from each pass (one from customer requirments and then again from
the devops.center requirements) will be shown in a way that could be
interpreted by a downstream processing agent.  Then appropriate notification
can be made based upon the output
"""
__version__ = "0.1"

__copyright__ = "Copyright 2017, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================


def diffFiles(customerFiles, dcFiles):
    customerList = readFilesIntoList(customerFiles)
#   print "=>{}<=".format(customerList)
    dcList = readFilesIntoList(dcFiles)
#   print "=>{}<=\n\n".format(dcList)
    diffFromCustomerFiles(customerList, dcList)
    diffFromDCFiles(customerList, dcList)


def diffFromCustomerFiles(customerList, dcList):
    # check what is in the customer files that is not in the devop.center files
    for element in customerList:
        if element not in dcList:
            # C: => denotes in customer file but not in devops.center file
            print "C:{}=={}".format(element, customerList[element])


def diffFromDCFiles(customerList, dcList):
    # check what is in the customer files that is not in the devop.center files
    for element in dcList:
        if element not in customerList:
            # D: => denotes in devops.center file but not in customer file
            print "D:{}=={}".format(element, dcList[element])
        elif customerList[element] != dcList[element]:
            # NOTE: customer element is first in the output
            print "V:{}=={}|{}=={}".format(element, customerList[element],
                                           element, dcList[element])


def readFilesIntoList(fileList):
    data = {}
    for aFile in fileList:
        if os.path.isfile(aFile) and os.access(aFile, os.R_OK):
            with open(aFile) as inFile:
                for line in inFile:
                    tmpLine = line[:-1]
                    if not tmpLine.startswith('#'):
                        (key, value) = tmpLine.split('==', 1)
                        data[key] = value
        else:
            print "ERROR: file access error: " + aFile
            sys.exit(1)
    return data


def checkArgs(inputArgs):
    parser = argparse.ArgumentParser(
        description='This script will log the output of the watchmedo script')
    parser.add_argument('-c', '--customerFiles', help='The customers '
                        'requirements.txt files.  Should be given as a '
                        'comma separated list (ie, "file1, file2, file3")',
                        nargs='+',
                        required=True)
    parser.add_argument('-d', '--dcFiles', help='The devops.center'
                        ' requirements.txt files.  Should be given as a'
                        'comma separated list (ie, "file1, file2, file3")',
                        nargs='+',
                        required=True)
    args = parser.parse_args()

    retCustFiles = args.customerFiles
    retDCFiles = args.dcFiles

    return (retCustFiles, retDCFiles)


def main(argv):
    (customerFiles, dcFiles) = checkArgs(argv)
#    print "customer files: =>{}<=".format(customerFiles)
#    print "devops.center files: =>{}<=".format(dcFiles)

    diffFiles(customerFiles, dcFiles)

if __name__ == "__main__":
    main(sys.argv[1:])


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
