Curve Extremes
==============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/bad8c870-51b7-4373-8094-7d8ac68c73d0
  :target: https://github.com/nortikin/sverchok/assets/14288520/bad8c870-51b7-4373-8094-7d8ac68c73d0

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node searches for points on the curve, where the specified scalar field
reaches it's minimal or maximum value. Most often this node is used with the
"Coordinate scalar field" node, to find, for example, points of the curve with
minimal Z coordinate.

Note that this node searches for extremes by use of numerical methods, so it
may be not very fast. In cases when you can find the points in question
analytically (by writing down all formulas for your field and your curve), it
will be much faster to calculate points by formulas. This node, in turn, is
most useful when you do not know exact formulas for the curve and / or for the
scalar field - for example, if they were defined by approximation.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/0066bb85-784f-40d3-a670-14283253b33b
  :target: https://github.com/nortikin/sverchok/assets/14288520/0066bb85-784f-40d3-a670-14283253b33b

* Fields-> :doc:`Coordinate Scalar Field </nodes/field/coordinate_scalar_field>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

Inputs
------

This node has the following inputs:

* **Curve**. The curve to find extremes on. This input is mandatory.
* **Field**. The scalar field in question. This input is mandatory.
* **MaxPoints**. This defines the maximum points the node will be able to find.
  To find more than one extreme point, the node splits the curve in N segments,
  and searches for single extreme point in each of them. If the curve and / or
  scalar field have very complex form, you may have to set this input to a
  number much higher than the expected number of extreme points. The default
  value is 1.

Parameters
----------

This node has the following parameters:

* **Direction**. This defines what kind of extreme points it is required to
  find. The available values are **Min** and **Max**. The default option is
  **Max**.
* **On fail**. This parameter is available in the N panel only. This defines what the node should do if it was not able to find the extreme point for a particular input curve. The available options are:

   * **Fail**. The node will raise an exception (become red).
   * **Skip**. The node will skip processing such curve, but will process all
     other curves in the input list (if there are more than one curve).

  The default option is **Fail**.

Outputs
-------

This node has the following outputs:

* **Point**. Extreme point in 3D space.
* **T**. Curve's T parameter, corresponding to the extreme point.

Example of usage
----------------

Find the point on a curve which has the maximum value of Y coordinate:

.. image:: https://user-images.githubusercontent.com/284644/86952365-5383d980-c16c-11ea-84d3-75830c0dbc75.png
  :target: https://user-images.githubusercontent.com/284644/86952365-5383d980-c16c-11ea-84d3-75830c0dbc75.png

* Curves-> :doc:`Build NURBS Curve </nodes/curve/nurbs_curve>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Fields-> :doc:`Coordinate Scalar Field </nodes/field/coordinate_scalar_field>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`