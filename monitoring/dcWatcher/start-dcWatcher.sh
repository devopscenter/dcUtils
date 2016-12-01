#!/bin/bash - 
#===============================================================================
#
#          FILE: start.sh
# 
#         USAGE: ./start.sh 
# 
#   DESCRIPTION: start dcWatcher script that can be executed by docker when the
#                container started.  This way the dcWatcher.py can run and then
#                a separate process will keep the image running and not terminate
#                as soon as the dcWatcher.py finishes spawning off the watchmedo
#                processes.
#
#                NOTE: this is NOT intended to be used for running in an instance
#                      or a local host (ie, anything except running in a container)
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/02/2016 15:45:23
#      REVISION:  ---
#===============================================================================
./dcWatcher.py
tail -f /dev/null
