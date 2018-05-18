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
import boto3
from botocore.exceptions import ClientError
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

    def __init__(self, customerIn, keysDir, instType,  source, regions=None):
        """Construct an instance of the InstanceInfo class."""
        self.customer = customerIn
        self.instanceType = instType
        self.source = source
        self.keysDirectory = keysDir
        self.allInstances = {}
        self.instances = {}
        self.jumpServers = {}
        self.filters = {}
        self.configFileName = None
        self.lastReturnedListOfInstances = {}
        self.lastReturnedListOfIPAddresses = []
        self.lastReturnedListOfKeyAndPaths = []

        if self.instanceType == "AWS":
            self.regions = regions
        elif self.instanceType == "VM":
            self.configFileName = source["configFileName"]

    def getInstanceInfo(self, filterList):
        """Create a list of IPs for the instances that are found based upon the filters."""
        # read and split up the instances and jumpservers into two dictionaries
        # that are made into instance variables.
        if self.configFileName:
            self.readInstanceConfigFile()
            self.applyFilters(filterList)
        else:
            self.getInstancesFromAWS(filterList)

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

    def createAWSFilterListFromDict(self, filterList):
        """Break down the filterList dictionary sent in to construct the AWS filter list"""
        returnList = []

        # for each k,v pair in the passed in filterList make a dictionary of {'Name':'tag:'k, 'Values':[v1,v2...]}
        # and then append them to the returnList
        for filterKey in filterList:
            anonDict = {}
            anonDict['Name'] = 'tag:' + filterKey
            anonDict['Values'] = filterList[filterKey]
            returnList.append(anonDict)

        return returnList

    def getInstancesFromAWS(self, filterList):
        """Create a list of IPs for the instances that are found based upon the filters from AWS."""
        # AWS wants the filters to be a specific way, so we need to convert the passed in filterList
        filterListToSend = self.createAWSFilterListFromDict(filterList)

        # - we couldn't get here if we didn't have a customer name, so we'll use that as the profile name
        # - next we need to see if they passed in any regions.  If they have not, then we default to what
        #   they have defined in the ~/.aws/config
        # - if there are one or more regions then we will loop through all the regions getting all the
        #   instances that match the filterList
        if len(self.regions) > 0:
            # looping through regions gathering data
            for aRegion in self.regions:
                aSession = boto3.Session(profile_name=self.customer, region_name=aRegion)
                self.getInstancesFromAWSForRegion(aSession, filterListToSend)

        elif self.customer:
            aSession = boto3.Session(profile_name=self.customer)
            self.getInstancesFromAWSForRegion(aSession, filterListToSend)
        else:
            # Don't know if we will ever have this situation with no customer, but it's here just in case
            aSession = boto3.Session()
            self.getInstancesFromAWSForRegion(aSession, filterListToSend)

    def getInstancesFromAWSForRegion(self, awsSession, filterList):
        client = awsSession.client('ec2')
        # use the filters to make a call to AWS using boto3 to get the the list of IPs
        response = client.describe_instances(Filters=filterList)

        for tmpInst in response['Reservations']:
            self.createAllInstances(tmpInst['Instances'])

        self.getServersFromConfig()
        for anInstance in self.allInstances:
            self.lastReturnedListOfInstances[anInstance] = self.allInstances[anInstance]

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

        self.createAllInstances(self.data['Instances'])
        self.getServersFromConfig()

    def createAllInstances(self, aSetOfInstances):
        """Create a true dictionary for each set of tags per instance."""
        for instance in aSetOfInstances:
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
        for k, v in filterList.items():
            if k in anInstance['TagsDict']:
                # since each value should be a list we need to go through each of them
                for eachValue in v:
                    if re.match(eachValue, anInstance['TagsDict'][k]):
                        c += 1
                        break

        if c == numFilters:
            return anInstance
        else:
            return None

    def applyFilters(self, filterList):
        """Create a list of instances based upon the filters."""
        for anInstance in self.allInstances:
            tmpInstance = self.checkInstanceForTags(self.allInstances[anInstance], filterList)
            if tmpInstance:
                self.lastReturnedListOfInstances[anInstance] = tmpInstance

    def getConnectString(self, anInstanceName):
        """Return the connection strings that can be then used to build ssh/scp commands to access an instance."""

        retParts = None
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
        description=('This script will return a list of instances based upon filters (tags of key=value pairs) '))
    parser.add_argument('-c', '--customer', help='The customer name, which will also be used as the lookup for the '
                                                   'profile, if needed',
                        required=True)
    parser.add_argument('-i', '--instanceType', help='The name of the location where the instance resides.  For '
                                                     'example: AWS, internal, VM, Azure etc.',
                        required=False)
    parser.add_argument('-r', '--regions', help='The region(s) to search in for customer instances customer',
                        required=False)
    parser.add_argument('-s', '--source', help='The an overloaded dictionary of items that will be interpreted based '
                                               'upon the instanceType.',
                        required=False)
    parser.add_argument('-t', '--tags', help='A list of key=value pairs separated by a space (no space before or after '
                                             'the equal sign).  This will be used to filter list to return ',
                        required=False)
    parser.add_argument('-kd', '--keysDirectory', help='This is the path to where the key resides on your system ',
                        required=False)
    parser.add_argument('-sc', '--shellCommand', help='If this python script is run from a shell command line or shell '
                                                      'script then this would execute one method with a given set of '
                                                      'tags/filters.  You would have to provide the filter set each '
                                                      'time as the object would go away once the python script ends, '
                                                      'which would be with each invocation of this script.',
                        choices=['connectParts', 'sshConnect', 'scpConnect', 'listOfIPAddresses', 'listOfKeys'],
                        required=False)
    args, unknown = parser.parse_known_args()

    retCustomer = ''
    if args.customer:
        retCustomer = args.customer

    retInstanceType = ''
    if args.instanceType:
        retInstanceType = args.instanceType

    retSource = {}
    if args.source:
        # first change the spaces that need to be there to something that shouldn't be in the string
        # looking for backslash space
        spacedOutString = re.sub(r"[\\]\s", "!+!", args.source)
        # make a dictionary out of the string now
        tmpDict = dict(item.split("=") for item in spacedOutString.split(" "))
        # and use a dict comprehension to get the spaces back in at the appropriate place
        retSource = {k: re.sub(r"\!\+\!", " ", v) for k, v in tmpDict.items()}

    retRegions = ''
    if args.regions:
        # first change the spaces that need to be there to something that shouldn't be in the string
        # looking for backslash space
        spacedOutString = re.sub(r"[\\]\s", "!+!", args.regions)
        # make a dictionary out of the string now
        tmpList = spacedOutString.split(" ")
        # and use a dict comprehension to get the spaces back in at the appropriate place
        retRegions = [re.sub(r"\!\+\!", " ", k) for k in tmpList]


    retTags = {}
    if args.tags:
        # first change the spaces that need to be there to something that shouldn't be in the string
        # looking for backslash space
        spacedOutString = re.sub(r"[\\]\s", "!+!", args.tags)
        # make a dictionary out of the string now
        tmpDict = dict(item.split("=") for item in spacedOutString.split(" "))
        # and use a dict comprehension to get the spaces back in at the appropriate place
        retTags = {k: re.sub(r"\!\+\!", " ", v).split(" ") for k, v in tmpDict.items()}

    retKeysDirectory = ''
    if args.keysDirectory:
        retKeysDirectory = args.keysDirectory

    retCommand = ''
    if args.shellCommand:
        retCommand = args.shellCommand

    return(retCustomer, retInstanceType, retRegions, retKeysDirectory, retSource, retTags, retCommand )


def main(argv):
    """Main code goes here."""
    (customer, instType, regions, keysDir, source, tagList, shellCommand) = checkArgs()

    instances = InstanceInfo(customer, keysDir, instType, source, regions)
    listOfIPs = instances.getInstanceInfo(tagList)
    if shellCommand:
        if shellCommand == "connectParts":
            import simplejson as json
            partsList = []
            for item in listOfIPs:
                parts = instances.getConnectString(item)
                partsList.append(parts)

            jsonObj = json.dumps(partsList)
            print("{}".format(jsonObj))

        if shellCommand == "sshConnect":
            if len(listOfIPs) > 1:
                print("ERROR: Filter list returned more than one result")
                sys.exit(1)
            for item in listOfIPs:
                parts = instances.getConnectString(item)
                print("ssh " + (parts.JumpServerPart if parts.JumpServerPart else '') + parts.DestSSHPort +
                      parts.DestKey + parts.DestHost)

        if shellCommand == "scpConnect":
            if len(listOfIPs) > 1:
                print("ERROR: Filter list returned more than one result")
                sys.exit(1)
            for item in listOfIPs:
                parts = instances.getConnectString(item)
                print("scp " + parts.DestSCPPort + parts.DestKey +
                      (parts.JumpServerPart if parts.JumpServerPart else '') + " REPLACE_WITH_YOUR_FILE " +
                      parts.DestHost + ":~")

        if shellCommand == "listOfIPAddresses":
            import simplejson as json
            for item in listOfIPs:
                jsonObj = json.dumps(item)
                print("{}".format(jsonObj))

        if shellCommand == "listOfKeys":
            keys = instances.getListOfKeys()
            for aKey in keys:
                print("{}".format(aKey))
    else:
        print("Example Mode\nLooping through list of instances:")
        for item in listOfIPs:
            print("\nInstanceInfo (getInstanceIPs({}))\n=>{}<=".format(tagList, item))
            print("Connect String (getConnectString(InstanceDetails):")
            parts = instances.getConnectString(item)
            print("For ssh:\nssh " + (parts.JumpServerPart if parts.JumpServerPart else '') + parts.DestSSHPort +
                  parts.DestKey + parts.DestHost)
            print("For scp /tmp/foobar to destination home directory:")
            print("scp " + parts.DestSCPPort + parts.DestKey + (parts.JumpServerPart if parts.JumpServerPart else '') +
                  " /tmp/foobar " + parts.DestHost + ":~")

        print("\n\nList of unique keys (with path) to try:")
        keys = instances.getListOfKeys()
        for aKey in keys:
            print("{}".format(aKey))
        print("THE END")


if __name__ == "__main__":
    main(sys.argv[1:])

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
