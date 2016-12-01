#!/usr/bin/env python
import sys
import argparse
from collections import OrderedDict
# ==============================================================================
"""
this script is called by deployenv.sh as a helper script to read a file,
remove duplicates and put the output into a second file.  Both files will be
given by the deployenv.sh
"""
__version__ = "0.1"

__copyright__ = "Copyright 2016, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================


def checkArgs():
    parser = argparse.ArgumentParser(
        description='Script that removes duplicates out of a file that only' +
                    ' as key=value pairs on each line')
    parser.add_argument('-i', '--inputFile', help='Input file that will be ' +
                        'read which is assumed to have just key=value pairs ' +
                        'one per line',
                        required=True)
    parser.add_argument('-o', '--outputFile', help='The outpu file name that' +
                        ' the calling program will expect the values to be' +
                        ' written to',
                        required=True)
    args = parser.parse_args()

    # try to read the configuration to make sure it is there
    retOutputFile = args.outputFile
    retInputFile = args.inputFile
    try:
        tmpFileHandle = open(retInputFile, 'r')
        tmpFileHandle.close()

    except IOError:
        print 'Unable to access the input file: \n' + \
            retInputFile
        sys.exit(1)

    # if we get here then the
    return (retInputFile, retOutputFile)


def main(argv):
    (inputFile, outputFile) = checkArgs()

    envDict = OrderedDict()

    with open(inputFile) as envFile:
        for line in envFile:
            (key, val) = line.rstrip('\n').split('=', 1)
            envDict[key] = val

    with open(outputFile, 'w') as outEnvFile:
        for item in envDict:
            strToWrite = '{}={}\n'.format(item, envDict[item])
            outEnvFile.write(strToWrite)


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
