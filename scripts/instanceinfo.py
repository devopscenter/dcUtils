#!/usr/bin/env python
"""
Docstring for instanceinfo.py. This script will act as an abstraction layer
between the connection information for AWS instances and private instances that
might reside beyond a proxy server.

Several namedtuples are used in the script and are defined as:

IPAddressSet defines the elements for the private and public dns, ip and ports.
IPAddressSet = namedtuple('IPAddressSet', 'PublicIpAddress, PublicDnsName, PublicPort, PrivateIpAddress,
                                           PrivateDnsName, PrivatePort',  InstanceName, DestLogin, DestKey, Shard')

ConnectParts are the elements that can be combined to form an SSH or SCP connect string for an instance.
ConnectParts = namedtuple('ConnectParts', 'DestHost, DestSSHPort, DestSCPPort, DestLogin, DestKey, JumpServerPart')
"""

import os
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

    def __init__(self, customerIn, keysDir, regions=None, sharedDir=None):
        """Construct an instance of the InstanceInfo class."""
        self.customer = customerIn
        self.keysDirectory = keysDir
        self.regionsToSearch = regions
        self.customerRegionsToSearch = []
        self.allInstances = {}
        self.allRegions = []
        self.instances = {}
        self.jumpServers = {}
        self.filters = {}
        self.sharedDirectory = sharedDir
        self.lastReturnedListOfInstances = {}
        self.lastReturnedListOfIPAddresses = []
        self.lastReturnedListOfKeyAndPaths = []


        self.getCustomerRegions()

    def getCustomerRegions(self):
        """read the customers shared settings file to get the regions they have instances in."""
        # first get the shard directory from the users specific settings file
        if not self.sharedDirectory:
            checkForDCInternal = self.getSettingsValue("dcInternal")
            commonSharedDir = self.getSettingsValue("dcCOMMON_SHARED_DIR")
            if commonSharedDir:
                # now we need to check if this is being run internally the common dir will have a customer name
                # at the end and we need to strip that off and put the customer name from this run there instead.
                if not checkForDCInternal:
                    commonSharedFile = commonSharedDir + "/devops.center/dcConfig/settings.json"
                else:
                    commonSharedFile = os.path.dirname(commonSharedDir) + "/" + self.customer + \
                                       "/devops.center/dcConfig/settings.json"
            else:
                print('The key dcCOMMON_SHARED_DIR was not found in the ~/.dcConfig/settings file.  You can specify '
                      'a shared directory with the --sharedDirectory option.')
                sys.exit(1)
        else:
            commonSharedFile = self.sharedDirectory + "/devops.center/dcConfig/settings.json"

        # read in the shared settings file
        try:
            with open(expanduser(commonSharedFile)) as data_file:
                settingsRaw = json.load(data_file)
        except IOError as e:
            print("ERROR trying to read the shared settings file for {}".format(self.customer))
            print("Shared dcConfig settings file error: {}".format(e))
            sys.exit(1)

        self.allRegions = settingsRaw['Regions']

    def getSettingsValue(self,theKey):
        """Read the ~/.dcConfig/settings file."""
        baseSettingsFile = expanduser("~") + "/.dcConfig/settings"
        try:
            with open(baseSettingsFile, 'r') as f:
                lines = [line.rstrip('\n') for line in f]
        except IOError as e:
            print("ERROR trying to read the personal settings file to get key: {}".format(theKey))
            print("Personal dcConfig settings file error: {}".format(e))
            sys.exit(1)

        retValue = None
        for aLine in lines:
            if re.search("^"+theKey+"=", aLine):
                retValue = aLine.split("=")[1].replace('"', '')
                break

        return retValue

    def getRegionsToSearch(self):
        """Match up the regions passed in with the regions that the user has defined."""
        if not self.regionsToSearch or len(self.regionsToSearch) == 0:
            self.customerRegionsToSearch = self.allRegions
        else:
            # match up the regions passed in to use with the all the possible regions for the customer
            # to create a set of regions to search for instances.
            for x in self.regionsToSearch:
                for item in self.allRegions:
                    if x == item['RegionName']:
                        self.customerRegionsToSearch.append(item)

        if len(self.customerRegionsToSearch) == 0:
            print("No regions matched the regions that the customer has instances in. Exiting...")
            sys.exit(1)

    def getInstanceInfo(self, filterList):
        """Create a list of IPs for the instances that are found based upon the filters."""
        # select the regions based upon the regions the user passed in
        self.getRegionsToSearch()

        # if we get here there are customer regions that match the regions we need to search in
        # so we need to loop through all the regions to search, looking for the instances that match the filters
        for regionInfo in self.customerRegionsToSearch:
            if regionInfo['InstanceType'] == "AWS":
                self.getInstancesFromAWS(filterList)
            elif regionInfo['InstanceType'] == "VM":
                self.readInstanceConfigFile(regionInfo['configFileName'])
                self.applyFilters(filterList)
            else:
                print("Error: Unknown InstanceType({}) for region: {}".format(regionInfo['InstanceType'],
                                                                              regionInfo['RegionName']),
                      regionInfo['RegionName'])

        for theInstanceName in self.lastReturnedListOfInstances:
            anInst = self.lastReturnedListOfInstances[theInstanceName]

            # prepend the path if we have it.  And if so, then the key doesn't have the extension either so add it
            theKey = anInst["KeyName"]
            if self.keysDirectory:
                theKey = self.keysDirectory + "/" + anInst["KeyName"] + ".pem"

            # store these away if needed later
            self.lastReturnedListOfKeyAndPaths.append(theKey)

            # and see if this instance has a jumpserver associated with it and add that jump servers keyName to the
            # list
            if "JumpServer" in anInst:
                jumpServerInfo = self.getJumpServerInfo(theInstanceName)

                if jumpServerInfo:
                    if self.keysDirectory:
                        jumpServerKey = self.keysDirectory + "/" + jumpServerInfo['KeyName'] + ".pem"
                    else:
                        jumpServerKey = jumpServerInfo['KeyName']

                    # and store this away if needed later
                    self.lastReturnedListOfKeyAndPaths.append(jumpServerKey)

            # create a named tuple to return
            InstanceDetails = namedtuple('InstanceDetails', 'PublicIpAddress, PublicDnsName, PublicPort, '
                                                            'PrivateIpAddress, PrivateDnsName, PrivatePort, ' 
                                                            'InstanceName, DestLogin, DestKey, Shard, Tags')

            self.lastReturnedListOfIPAddresses.append(InstanceDetails(
                PublicIpAddress=(anInst["PublicIpAddress"] if "PublicIpAddress" in anInst else ''),
                PublicDnsName=(anInst["PublicDnsName"] if "PublicDnsName" in anInst else ''),
                PublicPort=(anInst["PublicPort"] if "PublicPort" in anInst else ''),
                PrivateIpAddress=(anInst["PrivateIpAddress"] if "PrivateIpAddress" in anInst else ''),
                PrivateDnsName=(anInst["PrivateDnsName"] if "PrivateDnsName" in anInst else ''),
                PrivatePort=(anInst["PrivatePort"] if "PrivatePort" in anInst else ''),
                InstanceName=anInst["TagsDict"]["Name"],
                DestLogin=anInst["UserLogin"] if "UserLogin" in anInst else '',
                DestKey=theKey,
                Shard=anInst["TagsDict"]["Shard"] if "Shard" in anInst["TagsDict"] else '',
                Tags=anInst["TagsDict"]))

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
        if self.customerRegionsToSearch and len(self.customerRegionsToSearch) > 0:
            # looping through regions gathering data
            for aRegion in self.customerRegionsToSearch:
                if aRegion['InstanceType'] == 'AWS':
                    aSession = boto3.Session(profile_name=self.customer, region_name=aRegion['RegionName'])
                    self.getInstancesFromAWSForRegion(aSession, filterListToSend)

        elif self.customer:
            aSession = boto3.Session(profile_name=self.customer)
            self.getInstancesFromAWSForRegion(aSession, filterListToSend)
        else:
            # Don't know if we will ever have this situation with no customer, but it's here just in case
            aSession = boto3.Session()
            self.getInstancesFromAWSForRegion(aSession, filterListToSend)

    def getInstancesFromAWSForRegion(self, awsSession, filterList):
        try:
            client = awsSession.client('ec2')
            # use the filters to make a call to AWS using boto3 to get the the list of IPs
            response = client.describe_instances(Filters=filterList)
        except ClientError as e:
            print("Could not make a client session to AWS: \nReason: {0}".format(e))

        for tmpInst in response['Reservations']:
            self.createAllInstances(tmpInst['Instances'])

        for anInstance in self.allInstances:
            tmpInst = self.allInstances[anInstance]
            if "instance-association" not in tmpInst["TagsDict"]:
                self.lastReturnedListOfInstances[anInstance] = self.allInstances[anInstance]

    def readInstanceConfigFile(self, configFileName):
        """read the json config file and return a List of the elements found
        defined in the file"""

        # need to determine the path to the configFileName as it should be in the dcCOMMON_SHARED_DIR path
        if not self.sharedDirectory:
            checkForDCInternal = self.getSettingsValue("dcInternal")
            commonSharedDir = self.getSettingsValue("dcCOMMON_SHARED_DIR")
            if commonSharedDir:
                # now we need to check if this is being run internally the common dir will have a customer name
                # at the end and we need to strip that off and put the customer name from this run there instead.
                if not checkForDCInternal:
                    sharedInstanceInfo = commonSharedDir + "/devops.center/dcConfig/" + configFileName
                else:
                    sharedInstanceInfo = os.path.dirname(commonSharedDir) + "/" + self.customer + \
                                       "/devops.center/dcConfig/" + configFileName
        else:
            sharedInstanceInfo = self.sharedDirectory + "/devops.center/dcConfig/" + configFileName

        # first read in the file
        try:
            with open(expanduser(sharedInstanceInfo)) as data_file:
                self.data = json.load(data_file)
        except IOError as e:
            print("ERORR: with InstanceInfo.json file: {}".format(e))
            sys.exit(1)

        self.createAllInstances(self.data['Instances'])

    def createAllInstances(self, aSetOfInstances):
        """Create a true dictionary for each set of tags per instance."""
        for instance in aSetOfInstances:
            tagsDict = {}
            for tags in instance["Tags"]:
                tagsDict[tags["Key"]] = tags["Value"]

            instance["TagsDict"] = tagsDict
            instanceName = tagsDict["Name"]
            self.allInstances[instanceName] = instance.copy()

    def checkInstanceForTags(self, anInstance, filterList):
        """Iterate through the instances looking for the set of filters."""
        numFilters = len(filterList)

        c = 0
        for k, v in filterList.items():
            if k in anInstance['TagsDict']:
                # since each value should be a list we need to go through each of them
                for eachValue in v:
                    if '*' in eachValue:
                        # update the search mechanism to make this behave like AWS search.
                        regexValue = '^' + eachValue.replace('*', '.*')
                        if re.match(regexValue, anInstance['TagsDict'][k]):
                            c += 1
                            break
                    else:
                        if eachValue == anInstance['TagsDict'][k]:
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


    def getJumpServerInfo(self, anInstanceName):
        """Return the jumpserver/gateway connect information like: user@IP:port."""
        try:
            anInstInfo = self.lastReturnedListOfInstances[anInstanceName]

            if "JumpServer" in anInstInfo:
                # go through each of the customer regions to search
                for region in self.customerRegionsToSearch:
                    # looking for a Gatway section
                    if "Gateway" in region:
                        # and if found go through the list to find the jumpserver match
                        for jumpServer in region["Gateway"]:
                            if jumpServer["JumpServerName"] == anInstInfo["JumpServer"]:
                                return jumpServer

        except SystemError as e:
            print("=>{}<=".format(e))

        return None

    def getGatewayInfo(self, anInstanceName):
        """Return the jumpserver/gateway connect information like: user@IP:port."""
        # get the JumpServer info
        jumpServerInfo = self.getJumpServerInfo(anInstanceName.InstanceName)
        gatewayString = None
        if jumpServerInfo:
            gatewayString = jumpServerInfo["UserLogin"] + "@" + jumpServerInfo["PublicIpAddress"] + ":" + \
                        str(jumpServerInfo["PublicPort"])

        return gatewayString

    def getConnectString(self, anInstanceName):
        """Return the connection strings that can be then used to build ssh/scp commands to access an instance."""

        retParts = None
        ConnectParts = namedtuple('ConnectParts', 'DestHost, DestSSHPort, DestSCPPort, DestLogin, DestKey, JumpServerPart')
        try:
            anInstInfo = self.lastReturnedListOfInstances[anInstanceName.InstanceName]

            jumpServerPart = ""
            if "JumpServer" in anInstInfo:
                # get the JumpServer info
                jumpServerInfo = self.getJumpServerInfo(anInstanceName.InstanceName)

                # TODO: determine if we want to support that if they provide a directory for the keys that both the
                # jumpserver key and the instance key will be in the same directory.

                if self.keysDirectory:
                    jumpServerKey = self.keysDirectory + "/" + jumpServerInfo["KeyName"] + ".pem"
                else:
                    print("ERROR: a path to the key is required to generate the appropriate information for this "
                          "option.\nPlease run again and provide the --keysDirectory (-kd) option")
                    sys.exit(1)

                jumpServerPart = "ProxyCommand=\"ssh -i " + jumpServerKey + " -W %h:%p -p " + \
                                 str(jumpServerInfo["PublicPort"]) + " " + jumpServerInfo["UserLogin"] + \
                                 "@" + jumpServerInfo["PublicIpAddress"] + "\""

                destSSHPort = ""
                destSCPPort = ""
                destKey = ""
                if anInstanceName.PrivatePort:
                    destSSHPort = str(anInstanceName.PrivatePort)
                    destSCPPort = str(anInstanceName.PrivatePort)

                if anInstanceName.DestKey:
                    destKey = anInstanceName.DestKey

                destLogin = ""
                if anInstanceName.DestLogin:
                    destLogin = anInstanceName.DestLogin

                destHost = anInstanceName.PrivateIpAddress

            else:
                destSSHPort = ""
                destSCPPort = ""
                destKey = ""
                if anInstanceName.PublicPort:
                    destSSHPort = str(anInstanceName.PublicPort)
                    destSCPPort = str(anInstanceName.PublicPort)

                if anInstanceName.DestKey:
                    destKey = anInstanceName.DestKey

                destLogin = ""
                if anInstanceName.DestLogin:
                    destLogin = anInstanceName.DestLogin

                destHost = anInstanceName.PublicIpAddress

            retParts = ConnectParts(DestHost=destHost, DestSSHPort=destSSHPort, DestSCPPort=destSCPPort,
                                    DestLogin=destLogin, DestKey=destKey,
                                    JumpServerPart=jumpServerPart if jumpServerPart else "")

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
    parser.add_argument('-r', '--regions', help='The region(s) to search in for customer instances customer',
                        required=False)
    parser.add_argument('-t', '--tags', help='A list of key=value pairs separated by a space (no space before or after '
                                             'the equal sign).  This will be used to filter list to return ',
                        required=False)
    parser.add_argument('-kd', '--keysDirectory', help='This is the path to where the key resides on your system ',
                        required=False)
    parser.add_argument('-sd', '--sharedDirectory', help='This is the path to the shared drive on the system this is '
                                                         'running on.  If this machine does not have a shared drive '
                                                         'use this to point to where the shared files have been copied'
                                                         'to. ',
                        required=False)
    parser.add_argument('-sc', '--shellCommand', help='If this python script is run from a shell command line or shell '
                                                      'script then this would execute one method with a given set of '
                                                      'tags/filters.  You would have to provide the filter set each '
                                                      'time as the object would go away once the python script ends, '
                                                      'which would be with each invocation of this script.',
                        choices=['connectParts', 'sshConnect', 'scpConnect', 'listOfIPAddresses', 'listOfKeys', 'gatewayInfo'],
                        required=False)
    args, unknown = parser.parse_known_args()

    retCustomer = ''
    if args.customer:
        retCustomer = args.customer

    retRegions = []
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

    retSharedDirectory = ''
    if args.sharedDirectory:
        retSharedDirectory = args.sharedDirectory

    retCommand = ''
    if args.shellCommand:
        retCommand = args.shellCommand

    return(retCustomer, retRegions, retKeysDirectory, retSharedDirectory, retTags, retCommand )


def main(argv):
    """Main code goes here."""
    (customer, regions, keysDir, sharedDir, tagList, shellCommand) = checkArgs()

    instances = InstanceInfo(customer, keysDir, regions, sharedDir)
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
            jsonObj = json.dumps(listOfIPs)
            print("{}".format(jsonObj))

        if shellCommand == "listOfKeys":
            keys = instances.getListOfKeys()
            for aKey in keys:
                print("{}".format(aKey))

        if shellCommand == "gatewayInfo":
            import simplejson as json
            for item in listOfIPs:
                gatewayInfo = instances.getGatewayInfo(item)
                print("Gateway/JumpServer info: {}".format(gatewayInfo))
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
