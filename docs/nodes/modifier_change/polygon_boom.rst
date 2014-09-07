Polygon Boom
============

Functionality
-------------

The vertices of each polygon will be placed into separate lists. If polygons share vertices then the coordinates are duplicates into new vertices. The end result will be a nested list of polygons with each their own unique vertices. This facilitates rotation on a polygon around an arbitrary points without affecting the vertices of other polygons in the list.

Inputs & Outputs
----------------

Lists of Vertices and Edge/Polygon lists. The type of data in the *edg_pol* output socket content depends on the what kind of input is passed to *edge_pol* input socket. If you input edges only, that's what the output will be.

Examples
--------

The Box on default settings is a Cube with 6 polygons and each vertex is shared by three polygons. Polygon Boom separates the polygons into seperate coordinate lists (vertices).

.. image:: PolygonBoomDemo1.PNG