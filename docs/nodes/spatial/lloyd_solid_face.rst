Lloyd on Solid Face
===================

.. image:: https://user-images.githubusercontent.com/14288520/202818473-83fa1801-84e2-4814-adb2-36df0c1e2474.png
  :target: https://user-images.githubusercontent.com/14288520/202818473-83fa1801-84e2-4814-adb2-36df0c1e2474.png

Dependencies
------------

This node requires both SciPy_ and FreeCAD_ libraries to work.

.. _SciPy: https://scipy.org/
.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node uses Lloyd_ algorithm to redistribute a set of points on the Solid
Face object (i.e. a Surface trimmed by some Curve). If provided points do not
lie in / on the Solid Face object, they will be projected to it first.  

To generate Lloyd distribution on the surface of a Solid Face, Voronoi diagram is
generated in the region of space, defined by some maximum distance from the
surface (layer of some thickness). Thickness of this layer can affect resulting
distribution slightly.  

Optionally, weighted Lloyd algorithm can be used, to put points more dense in
places to which higher weight is assigned.

Solid Face object can be created with nodes from "Make Face" submenu (such as
"Face from Curve"); also any NURBS or NURBS-like surface can be used as a Solid
Face.

.. image:: https://user-images.githubusercontent.com/14288520/202818639-8128af91-b99f-4688-9d19-e44a0b30d4e0.png
  :target: https://user-images.githubusercontent.com/14288520/202818639-8128af91-b99f-4688-9d19-e44a0b30d4e0.png

.. _Lloyd: https://en.wikipedia.org/wiki/Lloyd%27s_algorithm

Inputs
------

This node has the following inputs:

* **SolidFace**. Solid Face object, on which the points are to be distributed.
  This input is mandatory.
* **Sites**. Initial points to be redistributed. This input is mandatory.
* **Thickness**. This input is available only when **Mode** parameter is set to
  **Surface**. Thickness of region where Voronoi diagram is generated. The
  default value is 1.0.
* **Iterations**. Number of Lloyd's algorithm iterations. The default value is 3.
* **Weights**. Scalar Field object used to assign different weights for
  different places in 3D space. More points will be put in places which have
  bigger weight. This input is optional. If not connected, uniform Lloyd
  algorithm will be used.

Outputs
-------

This node has the following outputs:

* **Sites**. Redisrtibuted points in 3D space.
* **UVPoints**. Redistributed points in U/V space of the surface. Z coordinate
  of these points will always be zero.
