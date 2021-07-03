Lloyd on Sphere
===============

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node uses Lloyd_ algorithm to redistribute a set of points on a sphereical
surface uniformly. If provided vertices are not lying on a sphere, they will be
projected to the sphere first.

Optionally, weighted Lloyd algorithm can be used, to put points more dense in
places to which higher weight is assigned.

.. _Lloyd: https://en.wikipedia.org/wiki/Lloyd%27s_algorithm

Inputs
------

This node has the following inputs:

* **Sites**. The points to be redistributed. This input is mandatory.
* **Center**. The center of the sphere. The default value is ``(0, 0, 0)``
  (global origin).
* **Radius**. Radius of the sphere. The default value is 1.0.
* **Iterations**. Number of Lloyd's algorithm iterations. The default value is
  3.
* **Weights**. Scalar Field object used to assign different weights for
  different places in 3D space. More points will be put in places which have
  bigger weight. This input is optional. If not connected, uniform Lloyd
  algorithm will be used.

Outputs
-------

This node has the following output:

* **Sites**. Redistributed points on the sphere.

Example of Usage
----------------

Let's start with boxes distributed randomly on a sphere:

.. image:: https://user-images.githubusercontent.com/284644/100536534-229f6080-3243-11eb-99d7-99494d3207aa.png

Note that the distribution is very unregular. Now we apply "Lloyd on Sphere" node:

.. image:: https://user-images.githubusercontent.com/284644/100536535-2337f700-3243-11eb-8884-c4d0ec9070eb.png

Density of distribution can be controlled with a scalar field - in this example, by absolute value of Z coordinate:

.. image:: https://user-images.githubusercontent.com/284644/100536623-a8231080-3243-11eb-8199-eb800dd2043b.png

