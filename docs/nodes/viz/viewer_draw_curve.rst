Viewer Draw Curve
=================

Functionality
-------------

This node displays Curve objects in the 3D View, using opengl. The node is
intended to be a fast way to show you the result of your node tree. 

For NURBS and NURBS-like curves, the node can also additionally display:
control points, control polygon edges, curve node points. For non-NURBS curves,
the node just does not try to display these attributes.

This node is automatically created when you select "Connect Viewer Draw" from
right-click menu for nodes which have Curve output. Also this node pops up as a
"temporal viewer". when you perform control-click on such a node.

Inputs
------

This node has the following inputs:

* **Curve**. The curve object(s) to be displayed. This input is mandatory.
* **Resolution**. Resolution for displaying the curve. The default value is 50.

Parameters
----------

This node has one main parameter:

* **Show**. The node displays something only when this parameter is enabled.

Most of arameters of this node are groupped in rows; for each type of
information this node can display, there are three parameters: whether to
display it, the color to be used, and point size / line width to be used.

The parameters of the node are (in this order):

* **Display Vertices**, **Vertices Color**, **Vertices Size**. Control display
  of points on the curve (number of points is conrtolled by **Resolution**
  parameter). Display of points is disabled by default.
* **Display Curve Line**, **Curve Line Color**, **Curve Line Width**. Control
  display of the curve itself (more precisely, the edges between curve points).
  Curve line is shown by default.
* **Display Control Points**, **Control Points Color**, **Control Points
  Size**. Control display of curve's control points, for NURBS and NURBS-like
  curves. Control points are not shown by default.
* **Display Control Polygon**, **Control Polygon Color**, **Control Polygon
  Line Width**. Control display of curve's control polygon (edges between
  control points), for NURBS and NURBS-like curves. Control polygon is not
  shown by default.
* **Display Node Points**, **Node Points Color**, **Node Points Size**. Control
  display of curve's node points, for NURBS and NURBS-like curves. Nodes are
  not shown by default.

Outputs
-------

This node has no outputs.

Example of Usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/189537925-b8d72553-5650-4d18-9fcc-507f70801dff.png

