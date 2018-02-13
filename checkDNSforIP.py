#!/usr/bin/env python
"""Gets the IP for a given hostname."""

import sys
import argparse
import socket
# ==============================================================================
__version__ = "0.1"

__copyright__ = "Copyright 2017, devops.center"
__credits__ = ["Bob Lozano", "Gregg Jensen"]
__license__ = ' \
   # Copyright 2014-2017 devops.center llc                                    \
   #                                                                          \
   # Licensed under the Apache License, Version 2.0 (the "License");          \
   # you may not use this file except in compliance with the License.         \
   # You may obtain a copy of the License at                                  \
   #                                                                          \
   #   http://www.apache.org/licenses/LICENSE-2.0                             \
   #                                                                          \
   # Unless required by applicable law or agreed to in writing, software      \
   # distributed under the License is distributed on an "AS IS" BASIS,        \
   # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. \
   # See the License for the specific language governing permissions and      \
   # limitations under the License.                                           \
   # '
__status__ = "Development"
# ==============================================================================


def checkArgs():
    """Check the command line arguments."""
    parser = argparse.ArgumentParser(
        description=('Gets the IP for the given hostname'))
    parser.add_argument('-n', '--nameOfHost', help='The fully qualified '
                        'name and domain of the host that you want the '
                        'IP for.',
                        required=True)

    args = parser.parse_args()

    retHostname = None
    if args.nameOfHost:
        retHostname = args.nameOfHost

    return(retHostname)


def main(argv):
    """Main code goes here."""
    theHostname = checkArgs()

    try:
        ipReturned = socket.gethostbyname(theHostname)
        print(ipReturned)
    except socket.gaierror:
        print("ERROR")


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
