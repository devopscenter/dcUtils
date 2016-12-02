This document describes the intended sequence of using the devops.center framework.

### High level flow for a brand new installation:

    - Use git to clone devops.center dcUtils
    - Change directory to dcUtils
    - Optional create a local directory that will be the base for the appliction
      directory structure
    - Create the application by using manageApp.py with the create command using a
      base directory path to be used to put the application directory structure in
          This will do create a git repository and it once it is working will need
          to be pushed to github so others can join the development.
    - Change directory to the newly created directory structure and navigate to the 
      appName-utils/environments directory.  
    - Edit the personal.env file and modify the dcUtils variable to point to the 
      location where you cloned the devops.center/dcUtils directory
    - Change to the devops.center dcUtils and run the deployenv.sh script to set
      up the environment for the application.
    - Modify the docker-compose.yml as necessary  
    - Execute start.sh

### High level flow for joining development already in progress

    - Use git to clone devops.center dcUtils
    - Change directory to dcUtils
    - Optional create a local directory that will be the base for the appliction
      directory structure
    - Join the application by using manageApp.py with the join command using a
      base directory path to be used to put the application directory structure in
          This will do a git clone of the already existing repository
    - Change directory to the newly created directory structure and navigate to the 
      appName-utils/environments directory.  
    - Edit the personal.env file and modify the dcUtils variable to point to the 
      location where you cloned the devops.center/dcUtils directory
    - Change to the devops.center dcUtils and run the deployenv.sh script to set
      up the environment for the application.
    - Modify the docker-compose.yml as necessary  
    - Execute start.sh

#### Clone devops.center dcUtils
The devops.center application framework is manipulated by the scripts that are found
in the devopscenter/dcUtils repository on github.com. Use git to clone that 
repsitory to somewhere on your local machine.  Make note the location as this will
be used later.

#### Create the local directory structure
In order for the devops.center framework to keep track of the files associated with
an application it is required that a directory be identified/created to house the
application directory structure.  This will be the base directory for any/all 
of the applications that will be created. Make note of this location as this will
be used in the next step

#### *(new applications)* Create the application
In order to create a new application the script manageApp.py needs to be run.  This
script is located in the devops.center dcUtils directory.  So, you will need to change
directory to this location.  This is the location that you clone the dcUtils 
repository in to. 

Once there execute the script (from within dcUtils):

    ./manageApp.py -a appName -d /local/base/directory -c create

where the options are:

    -a appName                   # the appliation name you have chosen
    -d /local/base/directory     # local directory you identified/created to house
                                 # the application(s) directory structure
    -c create                    # the command of create

#### *(existing applications)* Join the development
If there is already an existing application repository and you will be joining 
in on the development, then you will run the manageApp.py script with the same options
except the command to run will be join. This will clone the application respoitory
from github.  So, the arguments would be:

    -a appName                   # the appliation name you have chosen
    -d /local/base/directory     # local directory you identified/created to house
                                 # the application(s) directory structure
    -c join                      # the command of create

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
file.  At least, change the peronal.env file, modifying the dcUTILS variable to point
to where you cloned the devops.center dcUtils respoitory.

#### Run deployenv.sh
After you have the environment files how you want them, than it is time to collect all
of them and create one file to be used for the session that you will run the application
in.  This process will take the common.env file and merge it with the specific env file.
This will take the variables defined in the env specific file and overwrite any dupicate
settings found in the common.env. All other variables will be added to a resultant file.
Then it will then take that resultant file and merge it with the personal.env.  This
will take the variables define in the personal.env file and overwrite any duplicate
settings found the resultant file.   And any new variables will be added. 

The end result is one file that has all the variables in all three env files merged
together, with any duplicated variables having the value in the last env file that it
was found in.  The resultant file will then be placed in the directory:

    /baseDirectory/appName/appName-utils/environments/.generatedEnvFiles

The script and arguments to set up this environment file is(from within dcUtils):

    deployenv.sh --type TYPE --env ENV --customerAppName CUSTOMER_APP_NAME

where the options are:

    --type TYPE                          # TYPE is one of instance or docker 
    --env ENV                            # ENV is one of local, dev, staging, prod
    --customerAppName CUSTOMER_APP_NAME  # appliation name you have wish to configure
                                         # the environment for

For local development the options will be --type docker --env local  and then 
whatever you have as the appName will be the value for the customerAppName argument
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


