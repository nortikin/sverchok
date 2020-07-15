Interpolate NURBS Surface
=========================

Dependencies
------------

This node requires Geomdl_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/

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
* **Degree U**, **Degree V**. Degree of the surface along U and V directions,
  correspondingly. The default value is 3.

Paramters
---------

This node has the following paramters:

* **Centripetal**. This defines whether the node will use centripetal
  interpolation method. Unchecked by default.
* **Input mode**. The available values are:

   * **Single list**. The node expects a flat list of points for each surface.
     It will be subdivided into rows according to **USize** input value.
   * **Separate Lists**. The node expects a list of lists of points for each
     surface.
 
Outputs
-------

This node has the following outputs:

* **Surface**. The generated NURBS surface.
* **ControlPoints**. Control points of the generated NURBS surface.
* **KnotsU**, **KnotsV**. Knot vectors of the generated NURBS surface.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87576346-a91b3180-c6ea-11ea-926e-19b062672c48.png

