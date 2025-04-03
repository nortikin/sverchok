Cubic Spline
============

.. image:: https://user-images.githubusercontent.com/14288520/205740441-4b970495-ef77-4916-ba20-b5568561b26f.png
  :target: https://user-images.githubusercontent.com/14288520/205740441-4b970495-ef77-4916-ba20-b5568561b26f.png

Functionality
-------------

This node generates a cubic spline interpolating curve, i.e. a 3rd degree curve
which goes through the specified vertices. The curve can be closed or not.

.. image:: https://user-images.githubusercontent.com/14288520/205741368-e370239f-f1b2-43c4-b95f-27383ed13e76.png
  :target: https://user-images.githubusercontent.com/14288520/205741368-e370239f-f1b2-43c4-b95f-27383ed13e76.png

Curve domain is always from 0 to 1. The parametrization depends on **Metrics** parameter.

Inputs
------

This node has the following input:

* **Vertices**. The points through which it is required to plot the curve. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Cyclic**. If checked, the node will generate a cyclic (closed) curve. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205743604-3fed44aa-206d-4451-a488-6fee3f77ff9b.gif
  :target: https://user-images.githubusercontent.com/14288520/205743604-3fed44aa-206d-4451-a488-6fee3f77ff9b.gif

* **Metric**. This parameter is available in the N panel only. This defines the
  metric used to calculate curve's T parameter values corresponding to
  specified curve points. The available values are:

   * Manhattan
   * Euclidean
   * Points (just number of points from the beginning)
   * Chebyshev
   * Centripetal (square root of Euclidean distance)
   * X, Y, Z axis - use distance along one of coordinate axis, ignore others.

The default value is Euclidean.

Outputs
-------

This node has the following output:

* **Curve**. The generated curve.

Examples of usage
-----------------

Smooth curve through some random points:

.. image:: https://user-images.githubusercontent.com/14288520/205749474-98594e52-fd19-4028-87a7-08a410d3d9f1.png
  :target: https://user-images.githubusercontent.com/14288520/205749474-98594e52-fd19-4028-87a7-08a410d3d9f1.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

The same with **Cyclic** checked:

.. image:: https://user-images.githubusercontent.com/14288520/205750094-34acab3d-0694-42c8-a4e2-a68af47c064e.png
  :target: https://user-images.githubusercontent.com/14288520/205750094-34acab3d-0694-42c8-a4e2-a68af47c064e.png

These examples had Metric set to Euclidean (default). Since **Eval Curve** node
generates evenly-distributed values of the T parameter, the number of points at
each segment is proportional to the distance between points. The next example
is with Metric set to Points:

.. image:: https://user-images.githubusercontent.com/14288520/205750802-a21cf9e4-9919-4bee-b52d-08bc4396c4f0.png
  :target: https://user-images.githubusercontent.com/14288520/205750802-a21cf9e4-9919-4bee-b52d-08bc4396c4f0.png

In this case, number of points at each segment is the same.

