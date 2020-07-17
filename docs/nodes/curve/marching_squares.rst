Marching Squares
================

Dependencies
------------

This node requires SkImage_ library to work.

.. _SkImage: https://scikit-image.org/

Functionality
-------------

This node uses Marching Squares_ algorithm to find iso-lines of a scalar field,
i.e. lines in some plane, for which the scalar field has constant specified
value. The lines are generated as mesh - vertices and edges. You can use one of
interpolation nodes to build Curve objects from them.

.. _Squares: https://en.wikipedia.org/wiki/Marching_squares

Inputs
------

This node has the following inputs:

* **Field**. Scalar field to build iso-curves for. This input is mandatory.
* **Value**. The value, for which the iso-curves should be built. The default
  value is 1.0.
* **Samples**. Number of samples along X and Y axes. This defines the
  resolution of curves: the bigger is value, the more vertices will the node
  generate, and the more precise the curves will be. But higher resolution
  requires more computation time. The default value is 50.
* **MinX**, **MaxX**, **MinY**, **MaxY**. Minimum and maximum values of X and Y
  coordinates to find the iso-curves in. Default values define the square
  ``[-1; +1] x [-1; +1]``.
* **Z**. The value of Z coordinate to generate the curves at. The default value
  is 0. So, by default, the node will use the section of scalar field by XOY
  plane to draw the iso-curves for.
* **Matrix**. Reference frame to be used. X, Y and Z axes, which are used to
  section the scalar field, are defined by this matrix. By default, identity
  matrix is used, which means the global axes will be used.

Parameters
----------

This node has the following parameters:

* **Make faces**. If checked, the node will generate Faces for iso-curves that
  are closed within specified X/Y bounds. Unchecked by default.
* **Counnect boundary**. If checked, the node will connect pieces of the same
  curve, that was split because it was cut by specified X/Y bounds. Otherwise,
  several separate pieces will be generated in such case. Checked by default.

Example of usage
----------------

Build five planes parallel to XOY, and draw iso-lines of scalar field for seven different values:

.. image:: https://user-images.githubusercontent.com/284644/87058898-14b05b00-c222-11ea-9d77-b84c9dc13266.png

