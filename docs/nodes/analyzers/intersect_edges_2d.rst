Intersect edges 2D
==================

.. image:: https://user-images.githubusercontent.com/28003269/66367695-49973500-e9a6-11e9-9ff2-a97d68ac8510.png

Functionality
-------------
This node just finds intersections of edges.

There are some limitation in implementation of this node:

- According the name of the node it can work in 2d space particularly on 'XY' surface. Z coordinate just ignores by the node.
- It can handle big number of edges but if there are too much intersection the performance can slow down dramatically. For example if each input edge intersect with every others. In this case only few edges can be handled by this node.
- Overlapping of edges will lead to stopping of node working.
- Overlapping of points and point with edge does not lead to error but also such case does not takes in account by the algorithm and does not recognize as intersection.

Inputs
------

- **Verts** - just vertices
- **Edges** - just edges

Outputs
-------

- **Intersections** - points of intersection of edges
- **Involved edges** - list of edges which produce the intersection in order of intersection points

Further developing of the node
------------------------------

There are some improvements which can be done for the algorithm:

- increase robustness of algorithm in case when edges overlapping to each other
- take in account overlapping of points
- add accuracy parameter (because float numbers are compear with each other)
- add in existing 'intersect edges' node new mode with this algorithm which would merge all edges in one mesh with taking in account intersections.

Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/60796378-4e1d3900-a17e-11e9-86de-9209e0d8c51e.gif