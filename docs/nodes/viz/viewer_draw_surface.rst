Viewer Draw Surface
===================

Functionality
-------------

This node displays Surface objects in the 3D View, using opengl. The node is
intended to be a fast way to show you the result of your node tree. 

For NURBS and NURBS-like surfaces, the node can also additionally display
control points and control net edges. For non-NURBS curves, the node just does
not try to display these attributes.

This node is automatically created when you select "Connect Viewer Draw" from
right-click menu for nodes which have Surface output. Also this node pops up as a
"temporal viewer". when you perform control-click on such a node.

Inputs
------

This node has the following inputs:

* **Surface**. The surface object(s) to be displayed. This input is mandatory.
* **Resolution U**, **Resolution V**. Resolution to display the surface, along
  U and V parameters. The default value is 50.

Parameters
----------

This node has one main parameter:

* **Show**. The node displays something only when this parameter is enabled.

Most of arameters of this node are groupped in rows; for each type of
information this node can display, there are three parameters: whether to
display it, the color to be used, and point size / line width to be used.

The parameters of the node are (in this order):

* **Display Vertices**, **Vertices Color**, **Vertices Size**. Control display
  of points on the surface (number of points along U and V parameters are
  controlled by **Resolution U**, **Resolution V** inputs). Display of points
  is disabled by default.
* **Display Edges**, **Edges Color**, **Edges Line Width**. Control display of
  edges on the curve (edges between points). Display of edges is disabled by
  default.
* **Display Surface**, **Surface Color**. Control display of the surface
  itself. The surface is shown by default.
* **Display Control Points**, **Control Points Color**, **Control Points
  Size**. Control display of surface's control points, for NURBS and NURBS-like
  surfaces. Control points are not shown by default.
* **Display Control Net**, **Control Net Color**, **Control Net Line Width**.
  Control display of surface's control net (edges between control points), for
  NURBS and NURBS-like surfaces. Control net is not displayed by default.

Outputs
-------

This node has no outputs.

Example of Usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/189537929-2be26995-0cb3-4063-9531-8ca0f955e155.png

