Approximate NURBS Surface
=========================

Dependencies
------------

This node requires Geomdl_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/

Functionality
-------------

This node builds a NURBS_ Surface object, which approximates the given set of
points, i.e. goes as close to them as possible while remaining a smooth surface.

In fact, the generated surface always will be a non-rational surface, which means
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

* **Vertices**. Points to be approximated. Depending on **Input mode**
  parameter, it expects either list of lists of control points per surface, or
  a flat list of control points per surface. This input is mandatory.
* **USize**. This input is only available when **Input mode** parameter is set
  to **Single list**. The number of control points in a row. The default value
  is 5.
* **Degree U**, **Degree V**. Degree of the surface along U and V directions,
  correspondingly. The default value is 3.
* **PointsCntU**, **PointsCntV**. Number of control points to be used along U
  and V directions, correspondingly. These inputs are available only when
  **Specify points count** parameter is checked. Otherwise, the node will
  generate as many control points as it needs (which may be too many). The
  default value for these inputs (when they are available) is 5.

Parameters
----------

This node has the following parameters:

* **Centripetal**. This defines whether the node will use centripetal
  approximation method. Unchecked by default.
* **Input mode**. The available values are:

   * **Single list**. The node expects a flat list of points for each surface.
     It will be subdivided into rows according to **USize** input value.
   * **Separate Lists**. The node expects a list of lists of points for each
     surface.
 
* **Specify points count**. If checked, then the node allows you to specify the
  number of control points to generate in **PointsCntU**, **PointsCntV**
  inputs. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Surface**. The generated NURBS surface.
* **ControlPoints**. Control points of the generated NURBS surface.
* **KnotsU**, **KnotsV**. Knot vectors of the generated NURBS surface.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87575638-a3711c00-c6e9-11ea-86ed-9c49d80b0763.png

