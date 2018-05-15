#!/usr/bin/env python
"""
Docstring for instanceinfo.py. This script will act as an abstraction layer
between the connection information for AWS instances and private instances that
might reside beyond a proxy server.

Several namedtuples are used in the script and are defined as:

InstanceDetails defines the elements of an instance that can be used as input modeled after the need of the CodeDeploy
module.
InstanceDetails = namedtuple('InstanceDetails', 'IPAddressDetails, InstanceName, DestLogin, DestKey, Shard')

IPAddressSet defines the elements for the private and public dns, ip and ports.  This set of data is added to
the InstanceDetails tuple as the IPAddressDetails.
IPAddressSet = namedtuple('IPAddressSet', 'PublicIpAddress, PublicDnsName, PublicPort, PrivateIpAddress,
                                           PrivateDnsName, PrivatePort' )

ConnectParts are the elements that can be combined to form an SSH or SCP connect string for an instance.
ConnectParts = namedtuple('ConnectParts', 'DestHost, DestSSHPort, DestSCPPort, DestKey, JumpServerPart')
"""

import sys
import argparse
import json
import re
from collections import namedtuple
from os.path import expanduser

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


class InstanceInfo:

    def __init__(self, customerIn, regionIn, keysDir, fileName):
        """Construct an instance of the InstanceInfo class."""
        self.customer = customerIn
        self.region = regionIn
        self.keysDirectory = keysDir
        self.configFileName = fileName
        self.allInstances = {}
        self.instances = {}
        self.jumpServers = {}
        self.filters = {}
        self.lastReturnedListOfInstances = {}
        self.lastReturnedListOfIPAddresses = []
        self.lastReturnedListOfKeyAndPaths = []


    def getInstanceIPs(self, filterList):
        """Create a list of IPs for the instances that are found based upon the filters."""
        # read and split up the instances and jumpservers into two dictionaries
        # that are made into instance variables.
        if self.configFileName:
            self.readInstanceConfigFile()
            self.applyFilters(filterList)
        else:
            self.getInstancesFromAWS()

        for theKey in self.lastReturnedListOfInstances:
            anInst = self.lastReturnedListOfInstances[theKey]

            # set up the IP address structure for returning
            IPAddressSet = namedtuple('IPAddressSet',
                                     'PublicIpAddress, PublicDnsName, PublicPort, PrivateIpAddress, PrivateDnsName, PrivatePort' )
            IPAddresses = IPAddressSet(PublicIpAddress=(anInst["PublicIpAddress"] if "PublicIpAddress" in anInst else ''),
                         PublicDnsName=(anInst["PublicDnsName"] if "PublicDnsName" in anInst else ''),
                         PublicPort=(anInst["PublicPort"] if "PublicPort" in anInst else ''),
                         PrivateIpAddress=(anInst["PrivateIpAddress"] if "PrivateIpAddress" in anInst else ''),
                         PrivateDnsName=(anInst["PrivateDnsName"] if "PrivateDnsName" in anInst else ''),
                         PrivatePort=(anInst["PrivatePort"] if "PrivatePort" in anInst else ''))

            # prepend the path if we have it.  And if so, then the key doesn't have the extension either so add it
            theKey = anInst["KeyName"]
            if self.keysDirectory:
                theKey = self.keysDirectory + "/" + anInst["KeyName"] + ".pem"

            # store these away if needed later
            self.lastReturnedListOfKeyAndPaths.append(theKey)

            # return named tuple of (IPAddress, name, userLoginName, keyname, shard,)

            InstanceDetails = namedtuple('InstanceDetails', 'IPAddressDetails, InstanceName, DestLogin, DestKey, Shard')

            self.lastReturnedListOfIPAddresses.append(InstanceDetails(IPAddressDetails=IPAddresses,
                            InstanceName=anInst["TagsDict"]["Name"],
                            DestLogin=anInst["UserLogin"] if "UserLogin" in anInst else '',
                            DestKey=theKey,
                            Shard=anInst["shard"] if "shard" in anInst else ''))

        return self.lastReturnedListOfIPAddresses

    def getInstancesFromAWS(self):
        """Create a list of IPs for the instances that are found based upon the filters from AWS."""
        print("Yet to be implemented")
        # use the filters to make a call to AWS using boto3 to get the the list of IPs

    def readInstanceConfigFile(self):
        """read the json config file and return a List of the elements found
        defined in the file"""

        # first read in the file
        try:
            with open(expanduser(self.configFileName)) as data_file:
                self.data = json.load(data_file)
        except IOError as e:
            print("Config file error: {}".format(e))
            sys.exit(1)

        self.createAllInstances()
        self.getServersFromConfig()

    def createAllInstances(self):
        """Create a true dictionary for each set of tags per instance."""
        for instance in self.data["Instances"]:
            tagsDict = {}
            for tags in instance["Tags"]:
                tagsDict[tags["Key"]] = tags["Value"]

            instance["TagsDict"] = tagsDict
            instanceName = tagsDict["Name"]
            self.allInstances[instanceName] = instance.copy()

    def getServersFromConfig(self):
        """Extract all the jump servers from the config and create a dictionary of jump servers by name."""
        for instance in self.allInstances:
            if self.allInstances[instance]["TagsDict"]["Type"] == "jumpserver":
                self.jumpServers[instance] = self.allInstances[instance].copy()
            else:
                self.instances[instance] = self.allInstances[instance].copy()

    def checkInstanceForTags(self, anInstance, filterList):
        """Iterate through the instances looking for the set of filters."""
        numFilters = len(filterList)

        c = 0
        for k, v in filterList.iteritems():
            if k in anInstance['TagsDict']:
                if re.search(v, anInstance['TagsDict'][k]):
                    c += 1

        if c == numFilters:
            return anInstance
        else:
            return None

    def applyFilters(self, filterList):
        """Create a list of instances based upon the filters."""
        for anInstance in self.instances:
            tmpInstance = self.checkInstanceForTags(self.instances[anInstance], filterList)
            if tmpInstance:
                self.lastReturnedListOfInstances[anInstance] = tmpInstance

    def getConnectString(self, anInstanceName):
        """Return the connection strings that can be then used to build ssh/scp commands to access an instance."""
        ConnectParts = namedtuple('ConnectParts', 'DestHost, DestSSHPort, DestSCPPort, DestKey, JumpServerPart')
        try:
            anInstInfo = self.lastReturnedListOfInstances[anInstanceName.InstanceName]

            jumpServerPart = ""
            if "JumpServer" in anInstInfo:
                # get the JumpServer info
                jumpServerInfo = self.jumpServers[anInstInfo["JumpServer"]]

                # TODO: determine if we want to support that if they provide a directory for the keys that both the
                # jumpserver key and the instance key will be in the same directory.
                jumpServerPart = " -o ProxyCommand=\"ssh -i " + anInstanceName.DestKey + " -W %h:%p -p " + \
                                 str(jumpServerInfo["PublicPort"]) + " " + jumpServerInfo["UserLogin"] + \
                                 "@" + jumpServerInfo["PublicIpAddress"] + "\""

                destHost = ""
                destSSHPort = " -p " + str(anInstanceName.IPAddressDetails.PrivatePort) + " "
                destSCPPort = " -P " + str(anInstanceName.IPAddressDetails.PrivatePort) + " "
                destKey = " -i " + anInstanceName.DestKey + " "
                if anInstanceName.DestLogin:
                    destHost = anInstanceName.DestLogin + "@" + anInstanceName.IPAddressDetails.PrivateIpAddress
                else:
                    destHost = anInstanceName.IPAddressDetails.PrivateIpAddress

            else:
                destHost = ""
                destSSHPort = " -p " + str(anInstanceName.IPAddressDetails.PublicPort) + " "
                destSCPPort = " -P " + str(anInstanceName.IPAddressDetails.PublicPort) + " "
                destKey = " -i " + anInstanceName.DestKey + " "
                if anInstanceName.DestLogin:
                    destHost = anInstanceName.DestLogin + "@" + anInstanceName.IPAddressDetails.PublicIpAddress
                else:
                    destHost = anInstanceName.IPAddressDetails.PublicIpAddress

            retParts = ConnectParts(DestHost=destHost, DestSSHPort=destSSHPort, DestSCPPort=destSCPPort,
                                    DestKey=destKey, JumpServerPart=jumpServerPart if jumpServerPart else "")

        except SystemError as e:
            print("=>{}<=".format(e))

        return retParts

    def getListOfKeys(self):
        """Return a list of keys with their path for the last returned set of instances."""
        # trim out any duplicates before returning the list of keys with their path
        # retList = list(set(self.lastReturnedListOfKeyAndPaths))
        # or is list comprehension more efficient...?
        retList = []
        [retList.append(item) for item in self.lastReturnedListOfKeyAndPaths if item not in retList]
        return retList



def checkArgs():
    """Check the command line arguments."""
    parser = argparse.ArgumentParser(
        description=('Thist script will return a list of instances based upon filters (tags of key=value pairs) '))
    parser.add_argument('-c', '--customer', help='The customer name, which will also be used as the lookup for the '
                                                   'profile, if needed',
                        required=True)
    parser.add_argument('-r', '--region', help='The region to search in for customer instances customer ',
                        required=False)
    parser.add_argument('-f', '--configFile', help='The json config file '
                                                   'that defines the architecture for the appName',
                        required=False)
    parser.add_argument('-t', '--tags', help='A list of key=value pairs separated by a space (no space before or after '
                                             'the equal sign).  This will be used to filter list to return ',
                        required=False)
    parser.add_argument('-kd', '--keysDirectory', help='This is the path to where the key resides on your system ',
                        required=False)
    args, unknown = parser.parse_known_args()

    retConfigFile = ""
    if args.configFile:
        retConfigFile = args.configFile

    retTags = {}
    if args.tags:
        retTags = dict(item.split("=") for item in args.tags.split(" "))

    retCustomer = ""
    if args.customer:
        retCustomer = args.customer

    retRegion = ""
    if args.region:
        retRegion = args.region

    retKeysDirectory = ""
    if args.keysDirectory:
        retKeysDirectory = args.keysDirectory

    return(retCustomer, retRegion, retKeysDirectory, retConfigFile, retTags)

def main(argv):
    """Main code goes here."""
    (customer, region, keysDir, configFile, tagList) = checkArgs()

    instances = InstanceInfo(customer, region, keysDir, configFile)
    listOfIPs = instances.getInstanceIPs(tagList)
    print("Looping through list of instances:")
    for item in listOfIPs:
        print("\nInstanceInfo (getInstanceIPs({}))\n=>{}<=".format(tagList,item))
        print("Connect String (getConnectString(InstanceDetails):")
        parts = instances.getConnectString(item)
        print("For ssh:\nssh " + (parts.JumpServerPart if parts.JumpServerPart else '') + parts.DestSSHPort + \
              parts.DestKey + parts.DestHost)
        print("For scp /tmp/foobar to destination home directory:")
        print("scp " + parts.DestSCPPort + parts.DestKey + (parts.JumpServerPart if parts.JumpServerPart else '') + \
              " /tmp/foobar " + parts.DestHost + ":~")

    print("\n\nList of unique keys (with path) to try:")
    keys = instances.getListOfKeys()
    for aKey in keys:
        print("{}".format(aKey))
    print("THE END")


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4