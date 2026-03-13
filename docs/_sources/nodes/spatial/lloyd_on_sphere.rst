Lloyd on Sphere
===============

.. image:: https://user-images.githubusercontent.com/14288520/202800864-8c2b7767-d748-46cc-9817-0c23e80dc699.png
  :target: https://user-images.githubusercontent.com/14288520/202800864-8c2b7767-d748-46cc-9817-0c23e80dc699.png

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

.. image:: https://user-images.githubusercontent.com/14288520/202802127-3ae8c392-6f8f-4122-9e1b-a5eaded79f03.png
  :target: https://user-images.githubusercontent.com/14288520/202802127-3ae8c392-6f8f-4122-9e1b-a5eaded79f03.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Note that the distribution is very unregular. Now we apply "Lloyd on Sphere" node:

.. image:: https://user-images.githubusercontent.com/14288520/202803212-748a4d11-8054-4cc9-9791-c79d32cef6ae.png
  :target: https://user-images.githubusercontent.com/14288520/202803212-748a4d11-8054-4cc9-9791-c79d32cef6ae.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/202803190-5106f5d6-177b-471b-b839-01d6367afa03.gif
  :target: https://user-images.githubusercontent.com/14288520/202803190-5106f5d6-177b-471b-b839-01d6367afa03.gif

---------

Density of distribution can be controlled with a scalar field - in this example, by absolute value of Z coordinate:

.. image:: https://user-images.githubusercontent.com/14288520/202804854-9c58b26e-148f-4055-a9db-9082f3e495a2.png
  :target: https://user-images.githubusercontent.com/14288520/202804854-9c58b26e-148f-4055-a9db-9082f3e495a2.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Fields-> :doc:`Coordinate Scalar Field </nodes/field/coordinate_scalar_field>`
* Fields-> :doc:`Scalar Field Math </nodes/field/scalar_field_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/202804718-b87b02db-d756-4e81-a5a6-1683d0f8292a.gif
  :target: https://user-images.githubusercontent.com/14288520/202804718-b87b02db-d756-4e81-a5a6-1683d0f8292a.gif