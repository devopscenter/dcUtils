# Project Name

dcWatcher is a script that provides a facility to watch for file changes and then perform
actions based upon the files that change.  The current actions that can be taken are:

    - log
    - shell-command

This script has been written as wrapper around the python utility watchdog in order to 
provide a config file that provides the necessary elements for the **devops.center** environment.  This includes the ability to identify docker containers in the config to run the action in rather than just locally.  This also handles the log output to go to a centralized server which then ends up on the customers log reporter (ie, like papertrail).


## Installation

dcWatcher is part of the utils repository for devops.center in the monitoring directory. 

## Usage
- First off change to the directory that contains the dcWatcher script and the accompanying files.

- Edit the config/dcWatcher.json file to define the directories and file patterns to watch, and then the actions that you want to take when one of the patterns was changed or modified.

- If you are going to be running this in a docker container, you will need to generate
the dcWatcher-compose.yml to bring up the container properly.  This is done by executing
 dcWather.py with *--generate* option:

        ./dcWatcher.py --generate

    * If there is a reason that you would want to build the dcWatcher container run the build:

            docker build --rm -t devopscenter/dcwatcher:${devops_version}  .

    * To bring up the container use the docker-compose command:

            docker-compose -f dcWatcher-compose.yml

- Next you can run the dcWatcher.py command.  By default it will run as if it is running
in a container so there are no arguments that you need to provide.  Just run it as:

        ./dcWatcher.py

  and if you want to run it on your local machine or inside an instance, you will specify 
the *--platformtype*  type:

        ./dcWatcher.py --platformType instance

- To stop dcWatcher.py when running on an instance or local machine use the stop-dcWatcher.sh script to stop any running watchers.

- If you want to use a different dcWatcher.json config script you can provide *--configFile* to point to a different config file.


## Config file explained
The dcWatcher config file is a JSON structured file that contains a list of elements that define various config keys:
- patterns
- action
- options
- otherHosts

### patterns
Patterns are a list of paths that specify a directory end with a file name or wild-card pattern identifying possibly multiple files.  The list can contain multiple directory/file name patterns and each of the directories will be watched.  And when dcWatcher is run in a container the directories will each be mounted to the container to be watched.  When the file name/wild-card pattern is modified/updated the action will be executed.

### action
An action is the dcWatcher command that you want to run when the pattern is triggered.  It will then take any other elements from the config as needed to fulfill the action to run.

For example if the action is to log to the central logging service than the only element that will be used will be the pattern and the action (of "log")

Another example, if you want to restart a service based upon a config file changed, then the pattern would be the specific config file name and the action would be shell-command.  If the shell command is defined as a  list of shell commands, then each will be executed in order with each command after the first waiting on the previous command to finish before being executing.

Another notable item for the action is the ability to use the variables *$srcFile* and *$destFile*.  These are two special variables that when used will be filled with information from the modified/changed file. 

- $srcFile will be filled with the directory path and the file name that was modified/updated and triggered the action to be run.
- $destFile will be filled with the file name that is trimmed off of the $srcFile.

Thus if you wish to use this, say in a file copy bash command, then you would define it in the config to look like:

       "action" : {  "shell-command" : [
                "cp $srcFile $HOME/mywebpage/$destFile"
            ]
        } 

If the file that changed was $HOME/dev/importantCode/index.html then the resultant action would look like

    cp /theHomeDirectory/dev/importantCode/index.html /theHomeDirectory/mywebpage/index.html

### options
Options are ways to further refine what happens when the action is executed.  The possible options are:

- drop - To ignore events that occur while the action is still being executed to avoid multiple simultaneous actions taking place.

- recursive - Will take the directory from the pattern and use it as a top level directory and monitor all the directories recursively below that one.

### otherHosts
OtherHosts is a list of other hosts to run the action on instead of the local host.  This provides the ability to run the action on a different machine (ie, a running docker container or another instance/host).  This can be a list of other hosts if there are multiple hosts you want to affect by the one command and pattern.  If this is running from a container than the names will be the names of the other containers as identified by running the docker ps and getting the name from the names output column.

## History
- First release 11/10/2016

