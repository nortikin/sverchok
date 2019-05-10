Regular Solid
=============

Functionality
-------------

This node is a port to the Regular Solid functions (by dreampainter) now part of the Extra Objects Add-on bundled with Blender
https://archive.blender.org/wiki/index.php/Extensions:2.6/Py/Scripts/Add_Mesh/Add_Solid/

When list are used as input many solids will be created

Inputs & Parameters
-------------------

+-------------------+---------------------------------------------------------------------------------------+
| name              | descriptor                                                                            | 
+===================+=======================================================================================+
| Preset            | number of segments for each corner                                                    |
+-------------------+---------------------------------------------------------------------------------------+
| Source            | Starting point of your solid|
+-------------------+---------------------------------------------------------------------------------------+
| Snub              | Create the snub version                                                                       |
+-------------------+---------------------------------------------------------------------------------------+
| Dual              | cycle or open                                                                         |
+-------------------+---------------------------------------------------------------------------------------+
| Keep Size         | cycle or open                                                                         |
+-------------------+---------------------------------------------------------------------------------------+
| Size              | Radius of the sphere through the vertices                                                          |
+-------------------+---------------------------------------------------------------------------------------+
| Vertex Truncation | Amount of vertex truncation                     |
+-------------------+---------------------------------------------------------------------------------------+
| Edge Truncation   | Amount of edge truncation |
+-------------------+---------------------------------------------------------------------------------------+


Outputs
-------

verts and edges, representing the modified polyline with newly curved corners.


Examples and Notes
--------

see the thread:  https://github.com/nortikin/sverchok/pull/2290
