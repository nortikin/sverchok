Wireframe
=========

Functionality
-------------

This node resembles Blender's native Wireframe modifier.

Inputs
------

*thickness* - thickness factor of wireframe

*offset* - offset the thickness along the normal

*vertices* - list of vertices

*polygons* - list of polygons

Parameters
----------

*Boundary* - creates wireframes on mesh island boundaries.

*Offset even* - every new edge will be of the same length.

*Offset relative* - scale offset value with the thickness.

*Replace* - replace original geometry with wireframe or add wireframe on top of the original mesh.

When no input is connected, *thickness* and *offset* can be changed as parameters.

Outputs
-------

*vertices* - list of vertices

*edges* - list of edges

*polygons* - list of polygons

Examples
--------
