Polygons to Edges
=================

Functionality
-------------

Each polygon is defined by a closed chain of vertices which form the edges of the polygon. The edges of each polygon can be extracted. If a polygon is defined by a list of vertex indices (keys) as ``[3,5,11,23]`` then automatically the edge keys can be inferred as ``[[3,5],[5,11],[11,23],[23,3]]``. Note here that the last key closes the edge loop and reconnects with the first key in the sequence.

Inputs
------

Parameters
----------

Outputs
-------

Examples
--------

Notes
-------