Lloyd 3D
========

.. image:: https://user-images.githubusercontent.com/14288520/202770272-e3256501-f4c1-4393-8ae9-464c2804fead.png
  :target: https://user-images.githubusercontent.com/14288520/202770272-e3256501-f4c1-4393-8ae9-464c2804fead.png

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

.. image:: https://user-images.githubusercontent.com/14288520/202794664-d44e94b0-de0a-4712-938d-805ca00f7d1f.gif
  :target: https://user-images.githubusercontent.com/14288520/202794664-d44e94b0-de0a-4712-938d-805ca00f7d1f.gif

Inputs
------

This node has the following inputs:

* **Sites**. Initial points to be redistributed. This input is mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/202796059-1b124063-5977-48a0-a2a1-d88b845e8894.png
  :target: https://user-images.githubusercontent.com/14288520/202796059-1b124063-5977-48a0-a2a1-d88b845e8894.png

* **Clipping**. Clipping distance for Voronoi diagram. This value will be added
  to size of bounding box or sphere. The default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/202797248-3c10c478-db02-4271-b082-77c834985b5d.gif
  :target: https://user-images.githubusercontent.com/14288520/202797248-3c10c478-db02-4271-b082-77c834985b5d.gif

* **Iterations**. Number of Lloyd's algorithm iterations. The default value is 3.

.. image:: https://user-images.githubusercontent.com/14288520/202796545-27303108-9532-45d8-91c9-6e50cb53f212.gif
  :target: https://user-images.githubusercontent.com/14288520/202796545-27303108-9532-45d8-91c9-6e50cb53f212.gif

* **Weights**. Scalar Field object used to assign different weights for
  different places in 3D space. More points will be put in places which have
  bigger weight. This input is optional. If not connected, uniform Lloyd
  algorithm will be used.

.. image:: https://user-images.githubusercontent.com/14288520/202799380-4a66f4f5-23b5-4fa5-b041-f20259807169.gif
  :target: https://user-images.githubusercontent.com/14288520/202799380-4a66f4f5-23b5-4fa5-b041-f20259807169.gif

Parameters
----------

This node has the following parameters:

* **Bounds mode**. This defines bounding shape of generated points. The available options are:

  * **Bounding box**
  * **Bounding sphere**.

  The default value is **Bounding box**.

.. image:: https://user-images.githubusercontent.com/14288520/202795295-d642f1ae-e544-4dcb-9fc0-0cf6d8e56aa2.png
  :target: https://user-images.githubusercontent.com/14288520/202795295-d642f1ae-e544-4dcb-9fc0-0cf6d8e56aa2.png

Outputs
-------

This node has the following output:

* **Sites**. Redisrtibuted points.

Example of Usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/202798423-78027419-5703-49a3-a38d-49fb20a98ee9.png
  :target: https://user-images.githubusercontent.com/14288520/202798423-78027419-5703-49a3-a38d-49fb20a98ee9.png

* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`