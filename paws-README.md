# Description:
paws is a tool that makes it easier to connect to and work with AWS EC2 instances.  First, it uses the aws cli tool to query an account for running ec2-instances.  Next, it either returns a list of instances, connects to an individual instance, or runs commands on one or more of them.

Caution is advised!  (A good sanity check before running any command is using the -l option to see which hosts you're targeting).

## Setup:

You'll need to install awscli and pdsh if you haven't already.  For OS X, you can install both with homebrew, which can be installed with:
`/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`

```
brew install awscli
```
and
```
brew install --with-genders pdsh
```

You'll also need to configure the aws cli tool.  You can run `aws configure` for interactive setup, where you'll need to provide your AWS credentials a default region and a profile name.  For more info, see http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

Key management:
With this version of paws, the name of the key for the host that you select 
Finally, you'll need to tell paws where to find your SSH keys.  You can create a symlink that points to whatever directory the .pem files are stored in, (or you can create a new directory and copy them to it).  Note: the name of the directory or symlink you create must match the aws cli profile name.  For example, if you had a profile with the name 'main-account' and had SSH keys names prod.pem and dev.pem stored at '/aws/keys', to symlink to the location of your keys, from the main paws directory, first create and cd to the paws/.ssh directory (`mkdir .ssh && cd .ssh`) and then run `ln -s /aws/keys main-account`.

Also add the PAWS directory to your $PATH so that it can be run as a command.

If you run `ls -al .ssh`, you should see 'main-account -> /aws/keys', and running `ls -al .ssh/main-account/` should show both dev.pem and prod.pem.

## Usage:
* **List all instances, or instances and their tags:**  
   `paws [-p PROFILE] {-l | -L}`  
    -p	aws cli PROFILE  
    -l	no argument, returns a list of all instances  
    -L	no argument, returns a list of all instances and their tags  

* **Connect to a host interactively:**  
   `paws [-p PROFILE] -c`  
   -p	aws cli PROFILE  
   -c	no argument, displays a list of hosts and prompts for selection  

* **Connect to a specified host:**  
   `paws [-p PROFILE] -c HOST`  
   -p	aws cli PROFILE  
   -c	aws Name to log into with SSH  

* **Run a command on one or more instances in parallel, using a list of names:**  
   `paws [-p PROFILE] -x HOST1,HOST2 '<COMMAND>'`  
   -p	aws cli PROFILE 
   -x	list of hosts, separated by commas  

* **Run a command on one or more instances in parallel, using tags:**  
   `paws [-p PROFILE] -t KEY=VALUE '<COMMAND>'`  
   -p	aws cli PROFILE  
   -t	tag KEY and VALUE pairs, in the form of KEY=VALUE  

* **Run a command on all instances in parallel:**  
   `paws [-p PROFILE] '<COMMAND>'`  
   -p	aws cli PROFILE  

## Examples:
  * List tags for all instances for the default account:  `paws -L`  
  * Interactively connect to an instance for the client1 account:  `paws -p client1 -c`  
  * Connect to the web1 instance for the client1 account:  `paws -p client1 -c web1`  
  * Run the 'hostname' command on all instances for the client1 account:  `paws -p client1 'hostname'`  
  * Run the 'ls' command on the web1 and web2 instances for the client1 account:  `paws -p client1 -x web1,web2 'ls'`  
  * Run the 'w' command on instances tagged as Env=dev for the client1 account:  `paws -p client1 -t Env=dev 'w'`  
  * Run the 'date' command on instances tagged as Name=db1 for the default account:  `paws -t Name=db1 'date'` 

## Note:
For bulk commands to run you will either need to configure ssh to not prompt for unknown hosts, or add all possible hosts to known_hosts.

An easy way to check for this is to issue an informational command such as
  * `paws -p client1 'cat /var/run/reboot-required'`

If there are any errors then you'll need to either connect to each host that has an error (to add to the known_hosts file) or configure ssh to not prompt for a new host. To do the latter add this line to the end of the ~/.ssh/config:
  * `Host *
      StrictHostKeyChecking no`
