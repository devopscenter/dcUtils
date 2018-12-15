#!/usr/bin/env bash
#===============================================================================
#
#          FILE: pgpool.sh
#
#         USAGE: pgpool.sh
#
#   DESCRIPTION: Update pgpool, assuming previous dcStack pgpool installation
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 12/15/2018 
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

PGPOOL_VERSION=3.7.7

sudo mkdir -p /installs
pushd /installs
sudo wget --quiet http://www.pgpool.net/download.php?f=pgpool-II-$PGPOOL_VERSION.tar.gz -O pgpool-II-$PGPOOL_VERSION.tar.gz
sudo tar -xvf pgpool-II-$PGPOOL_VERSION.tar.gz && \
pushd pgpool-II-$PGPOOL_VERSION 
sudo ./configure && sudo make --silent && sudo make --silent install

popd
popd

sudo rm -R /installs/

sudo supervisorctl restart pgpool

/usr/local/bin/pgpool --version

