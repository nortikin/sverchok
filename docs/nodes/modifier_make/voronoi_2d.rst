Voronoi 2D and Delaunay
=======================

This is a spartan note. Both these nodes are written in the same file so both online/offline help files will point into this file.

Bugs?
The most recent mention of a bug for the Delaunay Node is that you must ensure that your input mesh has no doubles (co-location vertices). Else you will get an edge with zero distance for which the voronoi diagram will fail to compute (due to division by zero)

