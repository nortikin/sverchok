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

Outputs
-------

A list of random unit vectors, or nested lists.

Examples
--------

Notes
-----

Seed is applied per output, not for the whole operation (Should this be changed?)
A unit vector has length of 1, a convex hull of random unit vectors will approximate a sphere with radius off 1.
