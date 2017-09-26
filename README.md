# Devops.Center: dcUtils

The devops.center framework for creating applications is an easy way to minimize
the effort necessary to deploy the application while freeing up the developer
to focus more on the application code.  The environment provides a solid repeatable
framework that also makes it easy to move from one environment to another
(for example from dev->QA->production) using the same code in each
environment.  This is achieved by utilizing the devops.center framework of which
one of the packages is dcUtils.  dcUtils is described here.

## TL&DR
To get the local development environment running
* [RUN-ME-FIRST.sh](README.md#installing)
* [run manageApp.py](README.md#new-applications-create-the-application) to join or create an application
* [update env files](README.md#edit-personalenv) as appropriate
* [run deployenv.sh](README.md#run-deployenvsh)
* [run start-dc-containers.sh](README.md#start-the-application)
Of course there is more to it than that, hence the rest of the documentation...

## High level flow for a brand new installation:

#### [execute RUN-ME-FIRST.sh](README.md#installing)
This script will step through a series of questions
that, with your answers, will set some initial defaults and create the necessary
user information within the cloud system.  

This will clone the devops.center dcUtils which has the scripts that you will
utilize to interact with the devops.center framework and the cloud instances
for your application.

One of the questions will ask where you will want to put your applications that
you will be building with the devops.center tools.  This will be the base directory
for the applications directory structure that will be created by manageApp.py

If you choose an existing directory then note that you will have to provide the name of the
application with each dcUtils command. By default the dcUtils scripts will search the base
directory for the application and it if finds other files or directories, then it
won't know what to do with them.  The script will error out and request that additional
arguments be passed to identify the application you want to work with.

RUN-ME-FIRST.sh will also set up the dcUTILS environment variable and put the
path to dcUtils in the $PATH environment variable. You will be prompted to put
the command to 'source ~/.dcConfig/settings' into your shell rc file.  Which rc
file you need to put it in will be dependent on which shell you execute on a normal
basis, when interacting with a command line (ie, bashrc or bash-profile for bash
or zshrc for zsh etc.).  Once this file is sourced, you can access any of the
scripts in dcUtils from anywhere on your local machine.  NOTE: it will also
add to the environment variable $PYTHONPATH, so if you utilize this variable you should
check it after the source command has been executed and adjust it if it needs it.

#### [Application creation](README.md#new-applications-create-the-application)
Create the application by using manageApp.py with the create command and
an application name.  This will create a standardized directory structure utilizing
the base directory identified from the RUN-ME-FIRST.sh script.  This directory
structure houses configurations and keys for the different environments that
the application will run in.  

There will be two main directories one for the application and another
for the utility configurations.  

Application development will be done within the frontend directory structure and
is free to use what ever file and directory structure that is required for your
application.  For the most part, the devops.center tools won't need to restrict
any of the contents of this directory.

The other directory is used for configurations and will be utilized by the
devops.center tools to set up and manage the application as it run in your different
environments.  These tools allow different configuration and keys per environment.
By keeping the configuration separate from the application code, the application
can be developed with a focus on business requirements.

Once the code is ready it can be pushed to a git repository. This will put it in
a state that other developers can join in development on the code as explained in
the Joining Development section.

#### Application joining
If the application has already been created and stored in a a git repository, and
there is need to have other developers utilize the work that has been done, then
they can do this by using the join command to manageApp.py.  This will clone
the code from a git repo and ensure that it is setup in the same standarized
way to be able to use the devops.center tools.

#### [Initial configuration](README.md#edit-personalenv)
What will be created after running manageApp.py will be a directory in the base
directory that will be the name the application (ie, the -a appName provided to
manageApp.py). Go to this directory and you will see several directories, two of
them being the main ones;  appName-utils and the directory for the frontend of
your application.  The appName-utils contains the configurations that are used
by the devops.center scripts and is the one that you will need to update with
some initial information.  So, change into the appName-utils directory.

The first file to address is the environments/local.env and ensure the
SYSLOG_SERVER, SYSLOG_PORT and SYSLOG_PROTO keys have appropriate values for your
environment.  By default all the output from the instances/containers channel all
their output to syslog and we have setup a single instance/container to handle
that syslog output.  This will utilize these key/value pairs to deposit the output
in a central location (we use papertrail).  If you use a different logging system
contact devops.center personnel for assistance.

There is a environmental file that holds key/value pairs that would be personal
to your local development environment that would be different from anyone else's
environment. The file is environments/personal.env.   This file will overwrite
any of the same key/value pairs that might be defined in one of the other env
files.  Also, this file will not be stored within the git repository so it won't
be used or overwritten by anyone else.

And add the PGPOOL_CONFIG_FILE as well.

Once the environment key/value pairs are set up they need to be combined into one
file that the other devops.center scripts will use.  This unified environment
file is created by running the devops.center script: [deployenv.sh](README.md#run-deployenvsh).

Once completed and the application code is at a point to run, you can start up
the local environment (using docker containers) by running the command:

    [start-dc-containers.sh](README.md#start-the-application)

### Prerequisites

What things you need to install the software and how to install them

    awscli

### Installing

#### run RUN-ME-FIRST.sh
The devops.center application framework is manipulated by the scripts that are
found in the devopscenter/dcUtils repository on github.com. This repository is
cloned during the initial install script:

    RUN-ME-FIRST.sh.

This script will be placed into a shared directory and you will execute it from
there.  It will ask a series of questions, what is your application name, what
do you want for your username to be in the cloud environment, what directory do
you want dcUtils cloned to, what directory do you want for your application
development, etc.   The last step to RUN-ME-FIRST.sh is that a line will need to
be added to your shell rc file, such that a couple of new environment variables
may be introduced to your command line environment.  You will need to determine
which rc file that you need to put this source command as it is dependent on
which shell you use when interacting with the command line in a terminal window.
The line to insert will be:

    source $HOME/.dcConfig/settings

It will add the dcUtils path to the $PATH variable, so that you can execute the
dcUtils scripts from anywhere within your local machine. It will also update
the PYTHONPATH variable, so if you use this variable, you will want to check it
after it has been updated.

#### *(new applications)* Create the application
In order to create a new application the script manageApp.py needs to be run.  This
script is located in the devops.center dcUtils directory.  The scripts can be accessed
from anywhere once the source command mentioned above is executed for your terminal
session.

Execute the script:

    manageApp.py -a appName -c create

where the options are:

    -a appName                   # the application name you have chosen
    -c create                    # the command of create

Doing a create will take the arguments and create a new directory in the base
directory and use the appName as the name of the directory.  The base directory
is then stored in .dcConfig/baseDirectory which will be created (if it doesn't exist)
in your $HOME directory.  (NOTE, the base directory is retrieved  by manageApp.py
from the ~/.dcConfig/settings that is created when you run RUN-ME-FIRST.sh).  

There will be prompt that you will need to answer about the frontend of the application.
In most applications the front end is implemented as a web page, so the default is
listed as the application name  with a suffix of -web attached to it.  This doesn't
have to be taken and you can provide any name you want.  Or, if you happen to already
have the front end code available in some other location on your machine then that
name can be used.  If you want to use an existing directory that houses the application
code, you will need to provide the full absolute path to that code at the prompt.
That location will be symbolically linked into this new directory structure.
Or, if you want to accept the default just hit return.

A last prompt will be to ask which devops.center unique stack name is to be used for
the web (and worker) component of the application.  This is the ID of the stack number
that contains the necessary code modules that you will need to use for your application.
You can look at the repository of available stacks and choose the one that best suits
your needs.

After that the directory structure will be built with the appName-utils fully
fleshed out with sane defaults.


#### *(existing applications)* Join the development
If there is already an existing application repository and you will be joining
in on the development, then you will run the manageApp.py script with the same options
except the command to run will be join. This will clone the application
repository from github.

Execute the script:

    manageApp.py -a appName -c create

where the options are:

    -a appName                   # the application name you have chosen
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
continue development on the application.


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

Of special note about these is the order in which they are read in; common, the environment
specific one and then the personal. If a variable appears in two of the env files, the one
in the file that is read in last will be the one with the value when it is written to the
appName-utils/environments/.genereratedEnvFile/dcEnv-appName-ENV file.

So, you can either update the environment specific file or you can do the personal.env
file.  

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

    deployenv.sh --type TYPE --env ENV --appName THE_APPLICATION_NAME

where the options are:

    --type TYPE                          # TYPE is one of instance or docker
    --env ENV                            # ENV is one of local, dev, staging, prod
    --appName THE_APPLICATION_NAME  # application name you have wish to configure
                                         # the environment for

For local development the options will be --type docker --env local (which are both
the default values so if you are building for this enviornment than you don't have to
specify the options) and then whatever you have as the appName will be the value for
the appName argument.  Also, if you only have one application then you don't have
to add that option as it will default to the one it finds in the baseDirectory.

#### Modify the docker-compose.yml
A basic template is provided for the docker-compose.yml and is placed in the directory:

    /baseDirectory/appName/appName-utils/config/local

This will need to reflect the services that you are using for the application.
Most likely the only thing you would have to do with these is to comment out a container
if you are not going to be using it for your local development if assistance is needed,
reach out to devops.center support.

#### Start the application
At this point all the necessary administrative duties have been addressed and starting
the application is as simple as using the command (from within dcUtils):

    start-dc-containers.sh

NOTE: if you have multiple applications in your base directory you will need to add
the --appName option to signify which one you are starting
This will start the containers for the application and run it with a user defined
network. There is a default network IP that is used, but this can be overwritten
by adding a line to the appName-utils/config/local/docker-subnet.conf.  It has
the following contents:

DOCKER_SUBNET_TO_USE=172.42.16.0/24

It is required to use the private address space and one that is not already in use
or routed by your development host.

#### Stop the application
And then to stop the application (from within dcUtils):

    stop-dc-containers.sh

NOTE: if you have multiple applications in your base directory you will need to add
the --appName option to signify which one you are stopping

### Multiple base directories - Work Spaces
By default the idea of working with the devops.center environment is that there is
one default workspace named: default.  This default workspace has a directory
associated with it, and one or more applications would reside side by side in this
directory.  By doing this, it is easier to automate setting up environment variables
specific to an application.  The framework knows this because the information is
written in: $HOME/.dcConfig/baseDirectory.  When you create your first application
this file will be constructed and the directory will placed into the file with the
workspace name set to 'default'.  

If you have the need or desire to support multiple workspaces (say you have two
customers or you just want to keep two or more applications separate), you can use
the --workspaceName (-w) option on any of the scripts and specify the workspace you
want to reference.  The script will read the $HOME/.dcConfig/baseDirectory file and
determine the base path for that name and use it appropriately.  You will need to
use the --baseDirectory (-d) option when building a new application with manageApp.py
and will also need the --workspaceName option.  This should be the only time you
would need to add the --baseDirectory option with manageApp.py

Also, if you are going to be doing a lot of work in this workspace you can use the
switchWorkspace.sh script to change the default workspace to this name.  Then you
would not have to give the --workspaceName option each time you execute a script.
To set the default to the new workspaceName execute:

    switchWorkspace.sh -n new-name

If you don't provide an option it will give you a help message and show you what the
current default workspace name is along with any other workspaces you have defined.
If you want to go back to the default unnamed workspace, enter the word "default" as the new name.


## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Authors

* **Bob Lozano** - *Initial work*
* **Josh NAME** - *Initial work*
* **Trey NAME** - *refinements for version 1*
* **Gregg Jensen** - *refinements and extension for version2*


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc
