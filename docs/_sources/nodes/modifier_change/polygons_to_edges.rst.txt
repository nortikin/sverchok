Polygons to Edges
=================

Functionality
-------------

Each polygon is defined by a closed chain of vertices which form the edges of the polygon. The edges of each polygon can be extracted. If a polygon is defined by a list of vertex indices (keys) as ``[3,5,11,23]`` then automatically the edge keys can be inferred as ``[[3,5],[5,11],[11,23],[23,3]]``. Note here that the last key closes the edge loop and reconnects with the first key in the sequence.


Input & Output
--------------

+--------+-------+-------------------------------------------+
| socket | name  | Description                               |
+========+=======+===========================================+
| input  | pols  | Polygons                                  |
+--------+-------+-------------------------------------------+
| output | edges | The edges from which the polygon is built |
+--------+-------+-------------------------------------------+

Parameters
----------

- **Regular Polygons: Activate when the incoming list of polygons has constant number of sides to make the node faster.

- **Unique Edges** : When active the node will remove the doubled edges

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster with regular polygon list or when the polygon lists are NumPy arrays)

Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/modifier_change/polygons_to_edges/blender_sverchok_parametric_polygons_to_edges.png
  :alt: Polygon_to_Edges_example

Notes
-------

If you feed this node geometry and don't get the expected output, try a subset of the input geometry and hook
the output up to a *debug node*. Seeing what the output really is helps get an understanding for how this Node has interpreted the data. Also view the incoming data to see if it's what you think it is, perhaps it has unexpected extra nesting or wrapping.

Doesn't currently work on Plane Generator, or any generator which expresses key lists using *tuples*.

.. image:: https://cloud.githubusercontent.com/assets/619340/4186196/c89d4510-375e-11e4-86d3-c606a0a3e920.PNG
  :alt: Poly2EdgeDemo2.PNG
