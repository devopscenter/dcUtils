#!/usr/bin/env bash
#===============================================================================
#
#          FILE: start-dcWatcher.sh
# 
#         USAGE: ./start-dcWatcher.sh 
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
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/02/2016 15:45:23
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
#===============================================================================

#set -o nounset     # Treat unset variables as an error
#set -o errexit      # exit immediately if command exits with a non-zero status
#set -x             # essentially debug mode

./dcWatcher.py
tail -f /dev/null
