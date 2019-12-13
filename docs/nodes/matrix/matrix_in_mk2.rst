Matrix In
=========

This node creates a transformation Matrix by defining its Location, Scale and Rotation.
The rotation will be defined by rotation axis (vector) and angle or vector difference.

On the right-click menu the "Flat Output" toggle. While active (as it is by default)
it will join the first level to output a regular matrix list ([M,M,..]) that can be
plugged to any other node. If it is disabled the node will keep the original structure
outputting a list of matrix lists ([[M,M,..],[M,M,..],..]). 
