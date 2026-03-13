Polyline
========

.. image:: https://user-images.githubusercontent.com/14288520/205451607-4a09d62e-15e8-412f-9a4c-14d652981457.png
  :target: https://user-images.githubusercontent.com/14288520/205451607-4a09d62e-15e8-412f-9a4c-14d652981457.png

Functionality
-------------

This node generates a polyline (polygonal chain), i.e. a curve consisting of
segments of straight lines between the specified points. The polyline may be
closed or not.

.. image:: https://user-images.githubusercontent.com/14288520/205452066-af0ab9ef-75b9-454a-8c90-b0290b6bda0c.png
  :target: https://user-images.githubusercontent.com/14288520/205452066-af0ab9ef-75b9-454a-8c90-b0290b6bda0c.png

Curve domain / parameterization specifics: depends on **Metrics** parameter.
Curve domain will be equal to sum of distanes between the control points (in
the order they are provided) in the specified metric. For example, if
**Metric** is set to **Points**, then curve domain will be from 0 to number of
points.

Inputs
------

This node has the following input:

* **Vertices**. The points through which it is required to plot the curve. This input is mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/205452363-1875511b-302b-4c97-8fbe-9cbfbd4bc202.png
  :target: https://user-images.githubusercontent.com/14288520/205452363-1875511b-302b-4c97-8fbe-9cbfbd4bc202.png

Parameters
----------

This node has the following parameters:

* **Cyclic**. If checked, the node will generate a cyclic (closed) curve. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205452583-094906f8-8daf-4aa7-a3a3-a11d28cb708f.png
  :target: https://user-images.githubusercontent.com/14288520/205452583-094906f8-8daf-4aa7-a3a3-a11d28cb708f.png

* **Concatenate**. If checked, the node will generate one Curve object that
  passes through all provided vertices. Otherwise, the node will generate a
  separate Curve object for each edge. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/205452985-cb3246e4-489f-404f-a63d-b6d13aee138c.png
  :target: https://user-images.githubusercontent.com/14288520/205452985-cb3246e4-489f-404f-a63d-b6d13aee138c.png

* **Metric**. This parameter is available in the N panel only. This defines the
  metric used to calculate curve's T parameter values corresponding to
  specified curve points. The available values are:

   * Manhattan
   * Euclidean
   * Points (just number of points from the beginning)
   * Chebyshev.

The default value is Euclidean.

Outputs
-------

This node has the following output:

* **Curve**. The generated curve.

Examples of usage
-----------------

Polyline through some random points:

.. image:: https://user-images.githubusercontent.com/14288520/205453940-22304865-7d62-443f-8dca-e118c5306b82.png
  :target: https://user-images.githubusercontent.com/14288520/205453940-22304865-7d62-443f-8dca-e118c5306b82.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Viz-> :doc:`Viewer Draw Surface </nodes/viz/viewer_draw_surface>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

The same with **Cyclic** checked:

.. image:: https://user-images.githubusercontent.com/14288520/205454065-0c79131f-4aa0-4973-a102-3e7de086b449.gif
  :target: https://user-images.githubusercontent.com/14288520/205454065-0c79131f-4aa0-4973-a102-3e7de086b449.gif

---------

These examples had Metric set to Euclidean (default). Since **Eval Curve** node
generates evenly-distributed values of the T parameter, the number of points at
each segment is proportional to the distance between points. The next example
is with Metric set to Points.

In this case, number of points at each segment is the same.

.. image:: https://user-images.githubusercontent.com/14288520/205454380-60a00da5-e605-4f59-a376-6dae078af756.png
  :target: https://user-images.githubusercontent.com/14288520/205454380-60a00da5-e605-4f59-a376-6dae078af756.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Viz-> :doc:`Viewer Draw Surface </nodes/viz/viewer_draw_surface>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
