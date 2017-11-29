Vector Sort
===========

Functionality
-------------

This Node sort the sequence of index according to python sort, with different criteria.

Inputs
------

**Vertices** - vertices lists (vectors, tuple)

**PolyEdge** - polygons/edges as integer lists

Optional inputs
^^^^^^^^^^^^^^^

**Base point** - vector

**Mat** - matrix

**Index Data** -


Parameters
----------

+----------------+---------------+-------------+----------------------------------------------------+
| Param          | Type          | Default     | Description                                        |
+================+===============+=============+====================================================+
| **Vertices**   | Vector        |             | vertices from nodes generators or lists (in, out)  |
+----------------+---------------+-------------+----------------------------------------------------+
| **PolyEdge**   | Int           |             | index of polygons or edges     (in, out)           |
+----------------+---------------+-------------+----------------------------------------------------+
| **Sortmode**   | XYZ, Dist,    | XYZ         | will sort the index according to different criteria|
|                | Axis, User    |             |                                                    |
+----------------+---------------+-------------+----------------------------------------------------+
| **Item order** | Int           |             | output the index sequence                          |
+----------------+---------------+-------------+----------------------------------------------------+


Outputs
-------

**Vertices** - list of Vectors (tuples)

**PolyEdge** - polygons/edges as integer value of index of polygons/edges

**Item order** - sorted list of vertices

Example of usage
----------------

Example with an Hilbert 3d node and polyline viewer with Vector sort set to Dist:

.. image:: https://cloud.githubusercontent.com/assets/1275858/24357298/7c3e0f6a-12fd-11e7-9852-0d800ec51742.png

link to pull request: https://github.com/nortikin/sverchok/pull/88
