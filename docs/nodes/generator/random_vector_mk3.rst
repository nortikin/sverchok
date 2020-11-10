Random Vector
=============

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

**Simplify Output**: Method to keep output data suitable for most of the rest of the Sverchok nodes
  - None: Do not perform any change on the data. Only for advanced users
  - Flat: It will flat the output to keep vectors list in Level 3 (regular vector list)

**Match List**: Define how list with different lengths should be matched ('Short', 'Repeat Last' or 'Cycle')

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). Available for Vertices, Edges and Pols

Outputs
-------

A list of random unit vectors, or nested lists.

Examples
--------

Notes
-----

Seed is applied per output, not for the whole operation
A unit vector has length of 1, a convex hull of random unit vectors will approximate a sphere with radius off 1.

Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/5783432/19576172/09c7d264-9723-11e6-86fc-3b6acd0b5d53.png
  :alt: randomvector1.PNG
.. image:: https://cloud.githubusercontent.com/assets/5783432/19576267/666a5ad2-9723-11e6-93df-7f0fbfb712e2.png
  :alt: randomvector2.PNG
