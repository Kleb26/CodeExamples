Brief descriptions and requirements of each script given below,
format (all scripts only run within the unity environment for their respective project):

Name [VR project]:  
description.

AIMoveController [Star Wars game]:  
Class applied to all enemies to give basic movement. Includes staying within set range from player, randomised movement to give 'dodging'/
dynamic feel, stand up from prone (physics based) code.

ForceGestureManager [Star Wars game]:  
Master class that contains flags for force powers and manages power usage (i.e. so only one triggers). Also polls controllers (velocity) to
check for simple gestures that activates powers.

State [Microscope Visualisation]:  
Master class governing controller mode. Controls changing between modes and contains int variable indicating the mode. Also controls 
input for slice selection in its mode and what slices are visible.

VR_scale [Microscope Visualisation]:  
Manages the scaling mode. Scales the slice stack in the VR space. Takes controller input for scaling, both individual and combined.
Manages scale resetting as well as a save and load function for a set scale.
