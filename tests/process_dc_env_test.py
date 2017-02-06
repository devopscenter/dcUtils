#!/usr/bin/env python
import sys
import os
import argparse
sys.path.append(os.path.abspath('../scripts'))
# There is a PEP8 warning about this next line not being at the top of the file.
# The better answer is to append the $dcUTILS/scripts directory to the sys.path
# but I wanted to illustrate it here...so your mileage may vary how you want
from process_dc_env import pythonGetEnv
# ==============================================================================
"""
This script provides an example of how to use the process_dc_env.py in a python
script.   In a python script, the  pythonGetEnv is imported from the
process_dc_env script and then called directly in the script. That function will
do the necessary handling of some of the arguments on behalf of the python
script.  Any other arguments passed in are ignored by the process_dc_env script
and it is expected that the python script would handle the rest of them.  The
pythonGetEnv will return a enviornment list presented in a dictionary with the
environment variable set as the key and the value, is, well, the value.
"""
__version__ = "0.1"

__copyright__ = "Copyright 2016, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = "GPL"
__status__ = "Development"
# ==============================================================================


def checkArgs():
    parser = argparse.ArgumentParser(
        description='Script that provides a facility to watch for file ' +
                    'changes and then perform actions based upon the files' +
                    ' that change.')
    parser.add_argument('-f', '--foo', help='foo option',
                        required=False)
    parser.add_argument('-w', '--workspaceName', help='The alternate ' +
                        'directory name to find the application env files ' +
                        'in. This will not change the .dcConfig/' +
                        'baseDiretory file but will read it for the ' +
                        'alternate path and use it directly',
                        required=False)

    # args = parser.parse_args()
    # args, unknown = parser.parse_known_args(['--foo', '--bar'])
    args, unknown = parser.parse_known_args()

    # if we get here then the
    return (args.foo, args.workspaceName)


def main(argv):
    #  for manageApp.py only ... or designed to only be used by manageApp.py
    # retVals = pythonGetEnv(initialCreate=True)

    # normal call for all other python scripts
    retVals = pythonGetEnv()
    (foo, workspaceName) = checkArgs()

    print "=>{}<=".format(retVals)
    print "foo={}".format(foo)
    print "workspaceName={}".format(workspaceName)

    print "CUSTOMER_APP_NAME=" + retVals["CUSTOMER_APP_NAME"]
    print "ENV=" + retVals["ENV"]

if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
