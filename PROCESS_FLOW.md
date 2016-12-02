This document describes the intended sequence of using the devops.center framework.

The high level flow for a brand new installation:
    - use git to clone devops.center/dcUtils
    - cd dcUtils
    - optional create a local directory that will be the base for the appliction
      directory structure
    - create the appliation using manageApp.py with the create command using a
      base directory path to be used to put the application directory structure in
    - cd to the newly created directory structure and navigate to the 
      appName-utils/environments directory.  
    - edit the personal.env file and modify the dcUtils variable to point to the 
      location where you cloned the devops.center/dcUtils directory
    - change to the devops.center/dcUtils and run the deployenv.sh script to set
      up the environment for the application.
    - modify the docker-compose.yml as necessary  
    - execute start.sh

When creating a new 
