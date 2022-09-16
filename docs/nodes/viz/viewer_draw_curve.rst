Viewer Draw Curve
=================

.. image:: https://user-images.githubusercontent.com/14288520/190132455-a3a2b98a-bd6e-495e-86bc-181dd7ca1ad8.png
  :target: https://user-images.githubusercontent.com/14288520/190132455-a3a2b98a-bd6e-495e-86bc-181dd7ca1ad8.png

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

Most of parameters of this node are groupped in rows; for each type of
information this node can display, there are three parameters: whether to
display it, the color to be used, and point size / line width to be used.

The parameters of the node are (in this order):

* **Display Vertices**, **Vertices Color**, **Vertices Size**. Control display
  of points on the curve (number of points is conrtolled by **Resolution**
  parameter). Display of points is disabled by default.

.. image:: https://user-images.githubusercontent.com/14288520/190182798-35670d4f-1d74-41bc-8b5d-01ba98d3130a.png
  :target: https://user-images.githubusercontent.com/14288520/190182798-35670d4f-1d74-41bc-8b5d-01ba98d3130a.png

-------------

* **Display Curve Line**, **Curve Line Color**, **Curve Line Width**. Control
  display of the curve itself (more precisely, the edges between curve points).
  Curve line is shown by default.

.. image:: https://user-images.githubusercontent.com/14288520/190168448-b0691bc4-392f-4f83-bb5b-926da7b64b8e.png
  :target: https://user-images.githubusercontent.com/14288520/190168448-b0691bc4-392f-4f83-bb5b-926da7b64b8e.png

-------------

* **Display Control Points**, **Control Points Color**, **Control Points
  Size**. Control display of curve's control points, for NURBS and NURBS-like
  curves. Control points are not shown by default.

.. image:: https://user-images.githubusercontent.com/14288520/190171362-e1193750-3fec-4964-8af6-7e8b0de158f9.png
  :target: https://user-images.githubusercontent.com/14288520/190171362-e1193750-3fec-4964-8af6-7e8b0de158f9.png

-------------

* **Display Control Polygon**, **Control Polygon Color**, **Control Polygon
  Line Width**. Control display of curve's control polygon (edges between
  control points), for NURBS and NURBS-like curves. Control polygon is not
  shown by default.

.. image:: https://user-images.githubusercontent.com/14288520/190172536-af4307dd-c342-4e73-9936-0e1f58cd68b6.png
  :target: https://user-images.githubusercontent.com/14288520/190172536-af4307dd-c342-4e73-9936-0e1f58cd68b6.png

-------------

* **Display Node Points**, **Node Points Color**, **Node Points Size**. Control
  display of curve's node points, for NURBS and NURBS-like curves. Nodes are
  not shown by default.

.. image:: https://user-images.githubusercontent.com/14288520/190176111-16a43da1-2fd4-4b1c-bf74-78712bcd6a3f.png
  :target: https://user-images.githubusercontent.com/14288520/190176111-16a43da1-2fd4-4b1c-bf74-78712bcd6a3f.png

Operators
---------

This node has the following buttons:

* **BAKE**. Create mesh objects in Blender scene according to curves being displayed.
* **Align**. Zoom and position 3D view so that generated object is in the center.

Outputs
-------

This node has no outputs.

Example of Usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/190133906-61748350-414f-4d3e-8e71-2bd6be30597c.png
  :target: https://user-images.githubusercontent.com/14288520/190133906-61748350-414f-4d3e-8e71-2bd6be30597c.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Curves->NURBS-> :doc:`Approximate NURBS Curve </nodes/curve/approximate_nurbs_curve>`