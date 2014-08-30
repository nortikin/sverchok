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

Polygons to Edges
-----------------

Mesh Join
---------

Remove Doubles
--------------
Uses ``bmesh.remove_doubles`` to remove any vertices that are within a certain distance of eachother.

Delete Loose
------------

Separate Loose Parts
--------------------

Mask Vertices
-------------

Fill Holes
----------

Intersect Edges
---------------
Operates on Edge based geometry only and will create new vertices on all intersections of the given geometry. 
This operation is a recursive process and its speed is directly proportional to the number of intersecting 
edges passed into it. The algorithm is not optimized for large edges counts, but tends to work well anyway.



Modifier Make
=============

UV Connection
Adaptive Polygons
Adaptive Edges
Cross Section
Bisect
Solidify
Wireframe
Delaunay 2D
Voronoi 2D
Convex Hull

Lathe
-----
Uses ``bmesh.spin`` operator to perform 3d Screw / Lathe operations. The docs for bmesh.spin should 
suffice to explain the details.
