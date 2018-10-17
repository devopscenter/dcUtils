# devops.center Additional Documentation
This file contains additional documenation regarding the devops.center framework including information
about the environment and the commands that interact with it.

#### RUN-ME-FIRST.sh
What RUN-ME-FIRST.sh, initialization script to set up the devops.center environment to support the framework.

#### manageApp.py
To create or join an application.
The basic options to create application, probably done with or by a devops.center engineer.  This will create the application named quasar 

    manageApp.py -a quasar -c create

and to join an already existing application development.  
NOTE: Join is the default action
manageApp.py -a quasar

basic create that sets up an application in a new workspace a workspace name
NOTE: see the switchworkspace.sh section below for more information about workspaces

    manageApp.py -w WOW -a quasar -c create

to add a new environment name for those that don't use the basic dev, staging, prod
the command to create an environment called devprod:
manageApp.py -a quasar -c update -o "newEnv=devprod"

NOTE: make sure you run deployenv.sh after adding the new environment like:

    deployenv.sh -e devprod

#### deployenv.sh
To create an common environment from the app-utils/environment files.  There is a common.env that will define a key/value pair that will be the same in any environemnt (ie, dev, staging, prod etc.) there is a ENV.env (where ENV is one of dev, staging, prod etc) that is used to define key/value pairs specific to that environment.  Usually, the keys in this file will be repeated in each of the other ENV.env files but will have different values that are representative of that environment. Finally there is a personal.env file that can be used to define keys that are specific to the user for that environment.  This is for running locally and is not shared in the git repository. The script deployenv.sh will collect all those env files and put them together for a specific environment, reading in a specific order with the each potentially overriding what was defined in the previous file.  The order of reading is common.env, ENV.env and then personal.env. The local.env file is for a local development environment that uses docker containers and is the default option deployenv.sh

otherwise if you want to build the default application for a specific environment (ie, dev):

    deployenv.sh -e dev


#### start-dc-containers.sh 
When running the application in a local development environment (ie docker containers on your development machine) the way to start all of the containers is with the command start-dc-containres.sh.  This will set up an separate network for each of the containres to run within, such that all containers will be able to communicate to each other via normal network commands.  Just like when run in real instances.  As with other scripts just provide the name of the application to run.

    start-dc-containers.sh -a quasar


#### stop-dc-contianers.sh
And to stop the containres from running.

    stop-dc-containers.sh -a quasar

#### enter-container.py
Once the containers are running in your local development environment, this command will allow you to get to a bash prompt on a specific container.
No arguments are necessary, the script will go out and search for the containers you have running and give a list for you to pick from.  Just select the number beside the container you want to enter.

    enter-container.py

#### paws
Once you have instances running (ie, not the local development enviroment), paws
will allow you to log into the instance.  This script is a wrapper around ssh 
that provides options to select an instance from a set of instances, or it can be used to execute a command on a set of instances that are grouped by certain tags.
There is a paws-README.md in this directory that provides more details about this script.


#### pawscp
An off shoot from paws that uses the same grouping mechanism as paws, but speciallizes in copying files from your local development machine to your instances is pawscp.

#### switchWorkspace.sh
For the most common use of the deveops.center environment and framework, when a
customer has a set of applications they are rooted in a one development base
directory.  But there may be need to separate out those applications into separate
root directories, and for this we have provided workspaces.  While it is just a
different name, it is the key for the devops.center scripts to look in a different
base directory for applications defined there.  For example if a developer is
doing development on applications in two different sections of the company that
are functionally separate, then a workspace set up for each section in the company
could keep the applications separate. 

To see the current workspace and what workspaces have been set up (run with no options):

    switchWorkspace.sh

to actually change it, use the -n and give it a valid workspace name

    switchWorkspace.sh -n sales

