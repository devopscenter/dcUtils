#!/usr/bin/env python
# ==============================================================================
#
#          FILE: process_dc_env_test_2.py
#
#         USAGE: process_dc_env_test_2.py
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
pythonGetEnv will return a environment list presented in a dictionary with the
environment variable set as the key and the value, is, well, the value.

Note that the argparse statement for processing arguments needs to be a bit
different than what you probably normally use.  We need to ignore some of the
commands that are processed in the proces_dc_env.py (ie appName, env and
workspaceName if used).  to do this use parse_known_args instead of parse_args
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

    # old way
    # args = parser.parse_args()

    # new way and the extra options are in the unknown part
    args, unknown = parser.parse_known_args()

    # if we get here then the
    return (args.foo, args.workspaceName)


def main(argv):
    #  for manageApp.py only ... or designed to only be used by manageApp.py
    # retVals = pythonGetEnv(initialCreate=True)

    # normal call for all other python scripts
    try:
        (foo, workspaceName) = checkArgs()
    except SystemExit:
        pythonGetEnv()
        sys.exit(1)

    retVals = pythonGetEnv()

    print "=>{}<=".format(retVals)
    print "foo={}".format(foo)
    print "workspaceName={}".format(workspaceName)

    print "CUSTOMER_APP_NAME=" + retVals["CUSTOMER_APP_NAME"]
    print "ENV=" + retVals["ENV"]

if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
