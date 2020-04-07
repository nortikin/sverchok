particles MK2
=============

This node has Object socket input, from which to obtain the particle system.

The other inputs (Velocity, Location, Size) are for setting the particles found in that system.

The output sockets `Out Location` and `Out Velocity` can be used to pipe the values currently found at each particle of the system found at `Object socket` input - into the current node tree.

The Filter Death parameter can be used to Filter out (from the output socket) those particles that are declared dead by the particle system.