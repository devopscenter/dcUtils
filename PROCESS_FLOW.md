This document describes the intended sequence of using the devops.center framework.
### Getting Started
The devops.center framework for creating applications is an easy way to minimize
the effort necessary to deploy the application while freeing up the developer
to focus more on the application code.  The environment provides a solid repeatable
framework that also makes it easy to move from one environment to another
(for example from dev->QA->production) using the same code in each
environment.  This is achieved by utilizing two packages dcStack and dcUtils.
dcUtils is described here.

### High level flow for a brand new installation:

    - Use git to clone devops.center dcUtils somewhere where you will have
      easy access to it.
    - Change directory to dcUtils
    - Optional create a local directory that will be the base for the application
      directory structure that will be created by manageApp.py. If you choose an
      existing directory note that you will have to provide the name of the
      application with each dcUtils command.
    - Create the application by using manageApp.py with the create command and a
      base directory path and an application name.  This will create a standardized
      directory structure that houses configurations and keys for the different
      environemnts that the application will run in.  There will be two main directories
      one for the frontend application and another for the utility configurations.
      Once it is determined to be an appropriate state the two directories can be pushed
      to a git repository.  This will put it in a state that others than can join in
      development on the code as explained in the Joining Development section
    - Change directory to the newly created directory structure and navigate to the
      appName-utils/environments directory.
    - Edit personal.env as appropriate
        make sure dcUTILS is pointing to the directory where you have pulled
            the dcUtils repo
    - Edit the local.env and add the SYSLOG_SERVER, SYSLOG_PORT and SYSLOG_PROTO
        definitions.  And add the PGPOOL_CONFIG_FILE as well
    - Change to the devops.center dcUtils and run the deployenv.sh script to set
      up the environment for the application.
    - Execute start.sh

### High level flow for joining development already in progress

    - Use git to clone devops.center dcUtils somewhere where you will have
      easy access to it.
    - Change directory to dcUtils
    - Optional create a local directory that will be the base for the application
      directory structure that will be created by manageApp.py. If you choose an
      existing directory note that you will have to provide the name of the
      application with each command.
    - Join the application by using manageApp.py with the join command using a
      base directory path to be used to put the application directory structure in
          This will do a git clone of the already existing app and utils repository
          for this application
    - The values in the configs are probably set appropriately as they were created
      by the original developer when the application was created.  The exception
      is the configs that are personal to the individual developer.  This is
      located in the app-name-utils/environments directory in the personal.env
      file
    - Change directory to the appName-utils/environments directory.
    - Edit the personal.env file and modify the dcUtils variable to point to the
      location where you cloned the devops.center/dcUtils directory
    - Change to the devops.center dcUtils directory and run deployenv.sh to set
      up the environment for the application.
    - Modify the docker-compose.yml as necessary
    - Execute start.sh

#### Clone devops.center dcUtils
The devops.center application framework is manipulated by the scripts that are found
in the devopscenter/dcUtils repository on github.com. Use git to clone that
repository to somewhere on your local machine.  Make note the location as this will
be used later.

#### Create the local directory structure
In order for the devops.center framework to keep track of the files associated with
an application it is required that a directory be identified/created to house the
application directory structure.  This will be the base directory for any/all
of the applications that will be created. Make note of this location as this will
be used in the next step
NOTE: if you choose to use an existing directory that has existing files in it,
you will need to add the --appName applicationName option to single out the
specific directory for your application.

#### *(new applications)* Create the application
In order to create a new application the script manageApp.py needs to be run.  This
script is located in the devops.center dcUtils directory.  So, you will need to change
directory to this location.  This is the location that you clone the dcUtils
repository in to.

Once there execute the script (from within dcUtils):

    ./manageApp.py -a appName -d /local/base/directory -c create

where the options are:

    -a appName                   # the application name you have chosen
    -d /local/base/directory     # local directory you identified/created to house
                                 # the application(s) directory structure
    -c create                    # the command of create

Doing a create will take the arguments and create a new directory in the base
directory and use the appName as the name of the directory.  The base directory
is stored in .dcConfig/baseDirectory which will be created (if it doesn't exist)
in your $HOME directory.

There will be prompt that you will need to answer about the frontend of the application.
In most applications the front end is implemented as a web page, so the default is
listed as the application name  with a suffix of -web attached to it.  This doesn't
have to be taken and you can provide any name you want.  Or, if you happen to already
have the front end code available in some other location on your machine then that
name can be used.  You will need to provide the full absolute path to that code at
the prompt and that location will be symbolically linked to this directory structure.
Or, if you want to accept the default just hit return.

A last prompt will be to ask which devops.center unique stack name is to be used for
the web (and worker) component of the application.  This is the ID of the stack number
that contains the necessary code modules that you will need to use for your application.
You can look at the repository of available stacks and choose the one that best suits
your needs.

After that the directory structure will be built with the applicationName-utils fully
fleshed out with sane defaults.


#### *(existing applications)* Join the development
If there is already an existing application repository and you will be joining
in on the development, then you will run the manageApp.py script with the same options
except the command to run will be join. This will clone the application
repository
from github.  So, the arguments would be:

    -a appName                   # the application name you have chosen
    -d /local/base/directory     # local directory you identified/created to house
                                 # the application(s) directory structure
    -c join                      # the command for joining an existing development
                                 # effort
    --appPath                     # repository for an existing app directory
    --utilsPath                   # repository for an existing utils directory

The use case for using the join command is to add a developer to a an existing
application development effort.  There would be an initial developer that will
create the application framework by running manageApp.py with a create and will
subsequently create a repository for each of the application directory and the
utils directory.  They probably would have set up the configurations and may
have done work on setting up the application and then checked it all in.  Then
a new developer comes along to assist, and they will run the manageApp.py on
their development machine with a  command of join.  They will enter the appPath
repository name for the --appPath parameter and the utilsPath for the --utilsPath
parameter.  The appPath and utilsPath can EITHER be a git repo URL or an absolute
path to an existing application or utils directory that you already have.  This 
will create the application directory structure to allow the new devleoper to 
begin from a known point in the code.


#### Edit personal.env
There are several environment files that are used to set up a session for an application.
There is a common.env that is provided by the devops.center framework and resides in
the dcUtils/environment directory.  These are settings that are geared more for the
devops.center framework and probably will not be overwritten or changed.  Then there
is a environment specific file that is located in the appName/appName-utils/environments
directory. This environment specific file allows you to define settings that are
associated with that environment (possibly being different between environments).

And then there is the personal.env file.  This is where you can put the settings that
you would like to be specific to your development and meant to be different from others
on your team.  This will will be ignored when working with git.

So, you can either update the environment specific file or you can do the personal.env
file.  At least, change the personal.env file, modifying the dcUTILS variable to point
to where you cloned the devops.center dcUtils repository.

#### Run deployenv.sh
After you have the environment files how you want them, than it is time to collect all
of them and create one file to be used for the session that you will run the application
in.  This process will take the common.env file and merge it with the specific env file.
This will take the variables defined in the env specific file and overwrite any duplicate
settings found in the common.env. All other variables will be added to a resultant file.
Then it will then take that resultant file and merge it with the personal.env.  This
will take the variables define in the personal.env file and overwrite any duplicate
settings found the resultant file.   And any new variables will be added.

The end result is one file that has all the variables in all three env files merged
together, with any duplicated variables having the value in the last env file that it
was found in.  The resultant file will then be placed in the directory:

    /baseDirectory/appName/appName-utils/environments/.generatedEnvFiles

The script and arguments to set up this environment file is(from within dcUtils):

    deployenv.sh --type TYPE --env ENV --appName CUSTOMER_APP_NAME

where the options are:

    --type TYPE                          # TYPE is one of instance or docker
    --env ENV                            # ENV is one of local, dev, staging, prod
    --appName CUSTOMER_APP_NAME  # application name you have wish to configure
                                         # the environment for

For local development the options will be --type docker --env local  and then
whatever you have as the appName will be the value for the appName argument
This will create containers that make up the application and run on your local
machine.

#### Modify the docker-compose.yml
A basic template is provided for the docker-compose.yml and is placed in the directory:

    /baseDirectory/appName/appName-utils/config/local

This will will need to reflect the services that you are using for the application. If
assistance is needed, reach out to devops.center support.

#### Start the application
At this point all the necessary administrative duties have been addressed and starting
the application is as simple as using the command (from within dcUtils):

    ./start.sh

#### Stop the application
And then to stop the application (from within dcUtils):

    ./stop.sh

#### Additional information on the internals of dcUtils
- process_dc_env.py
NOTE: This script will take the key/value pairs from the environment files and
make them available to the running script's environment.  The process that is
used to get those key/value pairs into the environment may have an impact on
values that have spaces in them.  In order to selectively isolate the items for
the value with spaces, the value is quoted.  So, there is a possibility that
the downstream use/access to these values may need to be aware of these quotes
and strip them if necessary.  This is intended to be used by either shell
scripts of python scripts.  See the test scripts in ${dcUTILS}/tests for
examples of each type of script and the usage.

- $HOME/.dcConfig/baseDirectory
This file provides the base directory for the applications that are created
using the devops.center framework.

- additional workspaces and switchWorkspace.sh

- appName/.dcMapDir

- appName/environments/.generatedEnvFiles

- unique stack name
