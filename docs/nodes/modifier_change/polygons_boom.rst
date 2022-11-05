Polygon Boom
============

.. image:: https://user-images.githubusercontent.com/14288520/199933464-1a02da12-0610-410a-bedd-6f9858910fd4.png
  :target: https://user-images.githubusercontent.com/14288520/199933464-1a02da12-0610-410a-bedd-6f9858910fd4.png

Functionality
-------------

The vertices of each polygon will be placed into separate lists. If polygons share vertices then the coordinates are duplicates into new vertices. The end result will be a nested list of polygons with each their own unique vertices. This facilitates rotation of a polygon around an arbitrary points without affecting the vertices of other polygons in the list.

.. image:: https://user-images.githubusercontent.com/14288520/199933485-f6739a95-4291-4038-9f23-a3354934e061.png
  :target: https://user-images.githubusercontent.com/14288520/199933485-f6739a95-4291-4038-9f23-a3354934e061.png

Inputs & Outputs
----------------

Lists of Vertices and Edge/Polygon lists. The type of data in the *edg_pol* output socket content depends on the what kind of input is passed to *edge_pol* input socket. If you input edges only, that's what the output will be.

Examples
--------

The Box on default settings is a Cube with 6 polygons and each vertex is shared by three polygons. Polygon Boom separates the polygons into separate coordinate lists (vertices).

.. image:: https://user-images.githubusercontent.com/14288520/199938143-589364ca-5128-4657-969a-69c10803920d.png
  :target: https://user-images.githubusercontent.com/14288520/199938143-589364ca-5128-4657-969a-69c10803920d.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`