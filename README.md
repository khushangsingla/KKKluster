# KKKluster
A clustering plan for running various types of workloads

##  Running Instructions
Running instructions are provided in the `testing` directory

**Please use the scripts present inside `Debugging done` commit instead of the latest commmit to run the cluster**

## Components

- `fs-setup`

    This directory contains the filesystem setup details.
- `interface`
    
    This directory contains the user interface requirements.
- `k8s_setup`
    
    All the scripts for setting up k8s are in this directory.
- `monitoring_setup`
    
    This contains the tools and instructions for setting up the monitoring of all the servers.
- `os_setup`
    
    This contains the scripts for maintaining uniformity among all the servers.
- `testing`
    
    This directory contains the testing setup.

## Objectives
- Minimize the amount of control that users can exercise
- Users will only provide docker image and a list of commands
- Resources allocated to users should depend on their priority
- Maximixe the CPU usage across all machines


