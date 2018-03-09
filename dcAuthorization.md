# devops.center: dcAuthorization

The dcAuthorization server provides another layer of security for accessing AWS based instances. When creating
instances, devops.center will remove access ports from all the security groups (except 80 for web
servers) which allows access to the instances. Before the user can request access they have to register
their user information with the main security administrator for the company.  Then when they want to access
an instance, the will request an opening be made for them by running an access script. Once the opening has
been made, they can use their normal tools to access the instance.  This opening will automatically timeout
and be closed after a default length of time (initially 12 hours).



### General Process Overview

As a new customer, one person will be identified as the main security administrator. This person will be
responsible for registering the users at their company by having a specific login on the authentication server.
To register, a user will provide certain pieces of information which include:
- the users IAM user name
- the dcauthor public key (created when they run the RUN-ME-FIRST.sh to set up the devops.center framwork on their machine)
- the device name where they will be coming from
- the destination instance name(s)

The admin will then set up that information in a security table.  And then, before the user wants to access the 
instance, they will run an access script to create an opening to the instance.  The access script will take the users
information and passes it along to the dcAuthorization server to check it against the security table.  If 
successful a personalized opening will be created to allow them to access the instance.  This only creates an 
opening, it does not connect them to the instance.  For that, they will use their normal tools to access the 
instance (**).  The personalized opening will be closed automatically by default within 12 hours, or the user can
manually close it by running the access script again with the appropriate option.

** The tool used will still need to provide a security key to access the instance, as this will be the direct connection to
the instance.  

*NOTE:* The dcAuthorization server will be created by the devops.center team during the new customer on-boarding process.

### Registration Process
The user provides:
1. Each user needs to run RUN-ME-FIRST.sh so that they are set up for running the devops.center 
   framework, but also because it sets up a pair of security keys that are to be used with the authorization process.
   The keys have a specific name and is placed in the ~/.ssh/devops.center directory.  The key names will have the
   structure: 
    - dcauthor-IAMUSER_NAME-key.pub
    - dcauthor-IAMUSER_NAME-key.pem

    Where IAMUSER_NAME is the name selected as their AWS IAM user name when RUN-ME_FIRST.sh was run.

2. The user will then need to provide the dcauthor-IAMUSER_NAME-key.pub to the main security administrator
   identified for the company.  How the user gets this file to the administrator will be customer dependent.
   The administrator will then need to copy this file over to the authorization server.

3. Another piece of information that the user needs to pass to the administrator is the hostname of
   the device that they will be accessing the AWS instance with.  Usually this is just the result
   of running the command `hostname` on your machine.

4. The last piece of information the user has to provide is the instance(s) they will be accessing

### Access to the instance

The user wants to access an instance

1. Run the script `dcInstanceAccess.sh` (found in dcUtils but can be executed from anywhere) to create an opening to allow
   the user to use ssh to login to the instance:

   `dcInstanceAccess.sh  -c create  -p profile -r region  ExampleApp-dev-web4 22`

    - profile is the company name in your aws config files 
    - region is the region name the instance is in (default is us-west-2)
    - ExampleApp-dev-web4 is an example of an instance name. Use the one that you want to access as the second to last argument
    - 22 is an example of the port that you want to access.  22 would indicate that you want to use ssh to access the instance

    Assuming dcInstanceAccess.sh returns with Success, continue on.  Otherwise you will have to engage the security
    administrator to determine the problem.  

2. Use the devops.center tool `paws` to access the instance

    `paws -p profile [-r region] -c ExampleApp-dev-web4`

    - profile is the company name in your aws config files 
    - region is the region name the instance is in (optional if the instance is the default you have defined in your aws config)
    - ExampleApp-dev-web4 is an example of an instance name.

3. By default the opening will be closed after a maximum amount of time, which by default is 12 hours. If the user
   has finished with the connection they can close it themselves by running the dcInstanceAccess.sh script again with the command of delete.

   `dcInstanceAccess.sh  -c delete  -p devops.center -r us-west-2  ExampleApp-dev-web4 22`

    This can also be achieved by passing the -t option with the number of seconds that you are going to be using 
    the connection when you use the create command.  That way there is only one command to run.


