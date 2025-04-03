Random Vector
=============

.. image:: https://user-images.githubusercontent.com/14288520/188725644-dcc097af-0738-4b4c-9c3c-0e21fb748691.png
  :target: https://user-images.githubusercontent.com/14288520/188725644-dcc097af-0738-4b4c-9c3c-0e21fb748691.png

Functionality
-------------

Produces a list of random unit vectors from a seed value.


Inputs & Parameters
-------------------

+------------+-------------------------------------------------------------------------+
| Parameters | Description                                                             |
+============+=========================================================================+
| Count      | Number of random vectors numbers to spit out                            |
+------------+-------------------------------------------------------------------------+
| Seed       | Accepts float values, they are hashed into *Integers* internally.       |
+------------+-------------------------------------------------------------------------+
| Scale      | Scales vertices on some value *Floats*.                                 |
+------------+-------------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **Simplify Output**: Method to keep output data suitable for most of the rest of the Sverchok nodes
  
  - None: Do not perform any change on the data. Only for advanced users
  - Flat: It will flat the output to keep vectors list in Level 3 (regular vector list)

* **Match List**: Define how list with different lengths should be matched ('Short', 'Repeat Last' or 'Cycle')
* **Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). Available for Vertices, Edges and Pols

Outputs
-------

A list of random unit vectors, or nested lists.

Examples
--------

Notes
-----

Seed is applied per output, not for the whole operation
A unit vector has length of 1, a convex hull of random unit vectors will approximate a sphere with radius off 1.

Remark
------

For random numeric list see:

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>` (int/float, range)
* Number-> :doc:`Random </nodes/number/random>` (float, count, 0-1)

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/188726666-1a155458-74f1-443e-bc3b-854f6b2fdf22.gif
  :target: https://user-images.githubusercontent.com/14288520/188726666-1a155458-74f1-443e-bc3b-854f6b2fdf22.gif

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://cloud.githubusercontent.com/assets/5783432/19576172/09c7d264-9723-11e6-86fc-3b6acd0b5d53.png
  :target: https://cloud.githubusercontent.com/assets/5783432/19576172/09c7d264-9723-11e6-86fc-3b6acd0b5d53.png
  :alt: randomvector1.PNG


.. image:: https://cloud.githubusercontent.com/assets/5783432/19576267/666a5ad2-9723-11e6-93df-7f0fbfb712e2.png
  :target: https://cloud.githubusercontent.com/assets/5783432/19576267/666a5ad2-9723-11e6-93df-7f0fbfb712e2.png
  :alt: randomvector2.PNG
