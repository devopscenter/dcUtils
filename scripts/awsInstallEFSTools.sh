#!/usr/bin/env bash
#===============================================================================
#
#          FILE: awsInstallEFSTools.sh
#
#         USAGE: awsInstallEFSTools.sh
#
#   DESCRIPTION: Install AWS EFS helper tools
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 12/17/2018 
#      REVISION:  ---
#
# Copyright 2018-2019 devops.center llc
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
set -o errexit      # exit immediately if command exits with a non-zero status
set -x             # essentially debug mode



git clone https://github.com/aws/efs-utils
pushd efs-utils
sed -i 's/env sh/env bash/' build-deb.sh                # fix problem in script
./build-deb.sh
sudo apt -y install ./build/amazon-efs-utils*deb

popd

sudo rm -R efs-utils/