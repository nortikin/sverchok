Polygons to Edges
=================

.. image:: https://user-images.githubusercontent.com/14288520/199974343-7df85c98-c882-421e-8d5d-ce1d45e4e1d4.png
  :target: https://user-images.githubusercontent.com/14288520/199974343-7df85c98-c882-421e-8d5d-ce1d45e4e1d4.png

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

.. image:: https://user-images.githubusercontent.com/14288520/201473890-64aad2fc-bae9-4dc8-a792-70530a34f444.png
  :target: https://user-images.githubusercontent.com/14288520/201473890-64aad2fc-bae9-4dc8-a792-70530a34f444.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* CAD-> :doc:`Inset Special </nodes/CAD/inset_special_mk2>`
* CV Eta: Viz-> :doc:`Curve Viewer </nodes/viz/viewer_curves>`