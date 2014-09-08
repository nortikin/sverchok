Separate Loose Parts
====================

Functionality
-------------

Split a mesh into unconnected parts in a pure topologoical operation.

Input & Output
--------------

+--------+-----------+-------------------------------------------+
| socket | name      | Description                               |
+========+===========+===========================================+    
| input  | Vertices  | Inputs vertices                           |
+--------+-----------+-------------------------------------------+
| input  | Poly Edge | Polygon or Edge data                      |
+--------+-----------+-------------------------------------------+
| output | Vertices  | Vertices for each mesh part               |
+--------+-----------+-------------------------------------------+
| output | Poly Edge | Corresponding mesh data                   |
+--------+-----------+-------------------------------------------+

Examples
--------

.. image:: separate-looseDemo1.png

Notes
-------

Note that it doesn't take double vertices into account.
There is not gurantee about the order of the outputs
