Euler
=====

This node creates a transformation Matrix by defining the angles with X, Y and Z and the rotation order.

On the right-click menu there is a "Flat Output" toggle. While active (as it is by default)
it will join the first level to output a regular matrix list ([M,M,..]) that can be
plugged to any other node. If it is disabled the node will keep the original structure
outputting a list of matrix lists ([[M,M,..],[M,M,..],..]).
