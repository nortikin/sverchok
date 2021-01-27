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

- **Unique Edges** : When active the node will remove the doubled edges

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster)

Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/modifier_change/polygons_to_edges/blender_sverchok_parametric_polygons_to_edges.png
  :alt: Polygon_to_Edges_example
