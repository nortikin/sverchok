Interpolate NURBS Surface
=========================

Dependencies
------------

This node can optionally use Geomdl_ and FreeCAD_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/
.. _FreeCAD: https://www.freecad.org/

Functionality
-------------

This node builds a NURBS_ Surface object, which goes through all specified points.

In fact, the generated curve always will be a non-rational curve, which means
that all weights will be equal to 1.

To build a NURBS surface, one needs an array of M x N points (like "3
rows by 4 points"). There are two modes of providing this array supported:

* You can provide a list of lists of points for each surface;
* Or you can provide a flat list of points, and instruct the node to
  subdivide it into sublists of N points each.


.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node has the following inputs:

* **Vertices**. Points to be interpolated. Depending on **Input mode**
  parameter, it expects either list of lists of control points per surface, or
  a flat list of control points per surface. This input is mandatory.
* **USize**. This input is only available when **Input mode** parameter is set
  to **Single list**. The number of control points in a row. The default value
  is 5.
* **Degree U**, **Degree V**. Available only when Geomdl_ or built-in Sverchok implementations used.

  Degree of the surface along U and V directions, correspondingly. The default value is 3.

Parameters
----------

This node has the following parameters:

* **Implementation**. This defines the implementation of NURBS mathematics to
  be used. The available options are:

  * **Geomdl**. Use Geomdl_ library. This option is available only when Geomdl
    package is installed.
  * **Sverchok**. Use built-in Sverchok implementation.
  * **FreeCAD**. Use FreeCAD_ library. This option is available only when FreeCAD
    package is installed. The resulting surface is of degree 3 and continuity C2 
    (except we use 2x2 or 2xN grid of Vertices) .
  
  In general (with large number of control points), built-in implementation
  should be faster; but Geomdl implementation is better tested.
  The default option is **Geomdl**, when it is available; otherwise, built-in
  implementation is used.

* **Centripetal**. This parameter is only available when **Implementation**
  parameter is set to **Geomdl**. Defines whether the node will use
  centripetal interpolation method. Unchecked by default.
* **Metric**. This parameter is available only when **Implementation**
  parameter is set to **Sverchok**. This defines the metric used to calculate
  surface's U, V parameter values corresponding to specified points. The
  available values are:
  
  * Manhattan
  * Euclidean
  * Points (just number of points from the beginning)
  * Chebyshev
  * Centripetal (square root of Euclidean distance).

  The default value is Euclidean.

* **Input mode**. The available values are:
  
  * **Single list**. The node expects a flat list of points for each surface.
    It will be subdivided into rows according to **USize** input value.
  
  * **Separate Lists**. The node expects a list of lists of points for each surface.
 
Outputs
-------

This node has the following outputs:

* **Surface**. The generated NURBS surface.
* **ControlPoints**. Control points of the generated NURBS surface.
* **KnotsU**, **KnotsV**. Knot vectors of the generated NURBS surface.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87576346-a91b3180-c6ea-11ea-926e-19b062672c48.png

