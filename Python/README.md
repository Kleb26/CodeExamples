Brief descriptions and requirements of each script given below,
format (all scripts require default anaconda 3 packages):

Name [requirements {runnable yes/no}]:  
description.

3d_img_grabber [custom module and .Net drivers {No}]:  
Driver code (wrapper around .Net Assembly) to control a camera and translation stage to sync their operation to capture 3D image
stack from microscope.

LockInMaster [Python drivers {No}]:  
Driver code to control a lock-in amplifier for experiment. Code is extensively documented for future use with other researchers.
Code manages driving device and dealing with large (>100GB) data sets (storing + processing/management).

QuitableRun [LockInMaster {No}]:  
Example of multicore script in Python. Script runs the data capture in 'LockInMaster' in a subprocess so that the long process may
be terminated if desired without data loss.

Violet [{Yes-nothing executes on run}]:  
Personal use code. Code manages a tabletop RPG character. Example of nice class usage.

doppler cooling [Python2.7 and custom modules {No}]:  
Final script for simulating doppler cooling within Hydrogen. Also contains functions for data analysis and plotting.
