Lloyd 3D
========

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node uses Lloyd_ algorithm to redistribute a set of points in 3D space
(XOY plane) uniformly inside bounding box or bounding sphere.

Optionally, weighted Lloyd algorithm can be used, to put points more dense in
places to which higher weight is assigned.

.. _Lloyd: https://en.wikipedia.org/wiki/Lloyd%27s_algorithm

Inputs
------

This node has the following inputs:

* **Sites**. Initial points to be redistributed. This input is mandatory.
* **Clipping**. Clipping distance for Voronoi diagram. This value will be added
  to size of bounding box or sphere. The default value is 1.0.
* **Iterations**. Number of Lloyd's algorithm iterations. The default value is 3.
* **Weights**. Scalar Field object used to assign different weights for
  different places in 3D space. More points will be put in places which have
  bigger weight. This input is optional. If not connected, uniform Lloyd
  algorithm will be used.

Parameters
----------

This node has the following parameters:

* **Bounds mode**. This defines bounding shape of generated points. The available options are:

  * **Bounding box**
  * **Bounding sphere**.

  The default value is **Bounding box**.

Outputs
-------

This node has the following output:

* **Sites**. Redisrtibuted points.

Example of Usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/100535945-1dd8ad80-323f-11eb-981f-1d1743e1fd6b.png

