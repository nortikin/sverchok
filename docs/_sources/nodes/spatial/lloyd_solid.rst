Lloyd in Solid
==============

.. image:: https://user-images.githubusercontent.com/14288520/202816210-8d58c278-477c-4592-9274-b0425da1893c.png
  :target: https://user-images.githubusercontent.com/14288520/202816210-8d58c278-477c-4592-9274-b0425da1893c.png

Dependencies
------------

This node requires both SciPy_ and FreeCAD_ libraries to work.

.. _SciPy: https://scipy.org/
.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node uses Lloyd_ algorithm to redistribute a set of points either within
the volume of a Solid object, or on the surface of a Solid object. If provided
points do not lie in / on the Solid object, they will be projected to it first.

To generate Lloyd distribution on the surface of a Solid, Voronoi diagram is
generated in the region of space, defined by some maximum distance from the
surface (layer of some thickness). Thickness of this layer can affect resulting
distribution slightly.  

Optionally, weighted Lloyd algorithm can be used, to put points more dense in
places to which higher weight is assigned.

.. _Lloyd: https://en.wikipedia.org/wiki/Lloyd%27s_algorithm

Inputs
------

This node has the following inputs:

* **Solid**. Solid object, inside / on which the points are to be distributed.
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

Parameters
----------

This node has the following parameters:

* **Mode**. This defines where points will be distributed. The available options are:

  * **Volume**. Points will be distributed within the volume of the Solid object.
  * **Surface**. Points will be distributed on the surface of the Solid object.

  The default option is **Volume**.

* **Accuracy**. This parameter is available in the N panel only. This defines
  the accuracy of defining whether the point lies on the surface of the body.
  The higher the value, the more precise this process is. The default value is
  5.

Outputs
-------

This node has the following output:

* **Sites**. Redisrtibuted points.

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/202818068-bb50dc61-42cf-40f4-870b-b4ac03880286.png
  :target: https://user-images.githubusercontent.com/14288520/202818068-bb50dc61-42cf-40f4-870b-b4ac03880286.png
