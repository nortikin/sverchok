-----------------------
Modifiers Make & Change
-----------------------

Sverchok Nodes are generally named according to their most obvious behaviour. Some nodes offer quite a bit more
functionality than their name suggests and deserve a few words of clarification.

Modifier Change
===============

These modifiers deform, reorganize, or reconstruct data. Some modifiers could be placed in the Modifier Make section
too, but at some point we had to pick a category to fill the menus.

Polygon Boom
------------
any non obvious behaviour?

Polygons to Edges
-----------------
All polygons are essentially a list of indices that describe which vertices make up the sides of the polygon. 
This node reduces each polygon to its constituent edge loops.

Mesh Join
---------
This is like ``Ctrl+J`` in 3d View, it merges nested Vertex and Poly lists together.

Remove Doubles
--------------
Uses ``bmesh.remove_doubles`` to remove any vertices that are within a certain distance of eachother.

Delete Loose
------------
Throughputs the mesh minus any unattached Vertices, 
any non obvious behaviour?

Separate Loose Parts
--------------------
any non obvious behaviour?

Mask Vertices
-------------
any non obvious behaviour?

Fill Holes
----------
any non obvious behaviour?

Intersect Edges
---------------
Operates on Edge based geometry only and will create new vertices on all intersections of the given geometry. 
This operation is a recursive process and its speed is directly proportional to the number of intersecting 
edges passed into it. The algorithm is not optimized for large edges counts, but tends to work well anyway.



Modifier Make
=============

UV Connection
-------------

Adaptive Polygons
-----------------

Adaptive Edges
--------------

Cross Section
-------------

Bisect
------

Solidify
--------

Wireframe
---------

Delaunay 2D
-----------

Voronoi 2D
----------

Convex Hull
-----------
Creates a list of Faces and Edges from an incoming list of Vertices. This can be useful to skin a simple cloud of points. Any internal points to the system will be rejected.

Lathe
-----
Uses ``bmesh.spin`` operator to perform 3d Screw / Lathe operations. The docs for bmesh.spin should 
suffice to explain the details.
