Intersect Edges
===============

.. image:: https://user-images.githubusercontent.com/28003269/67563530-f48f4900-f731-11e9-9441-25d3708e0502.png

Functionality
-------------

The node is designed for finding intersections of inputs edges and returns mesh based on intersection result.

This node contains several algorithm of finding edge intersections:

**Initial algorithm:**

The code is straight out of TinyCAD plugin's XALL operator, which is part of Blender Contrib distributions.

It operates on Edge based geometry only and will create new vertices on all intersections of the given geometry. 
This node goes through a recursive process (divide and conquer) and its speed is directly proportional to the 
number of intersecting edges passed into it. The algorithm is not optimized for large edges counts, but tends 
to work well in most cases. 

**Sweep line algorithm** *- for 2D mode only*

This algorithm is based on `sweep line <https://en.wikipedia.org/wiki/Sweep_line_algorithm>`_ approach:

It can handle big number of edges but if there are too much intersection the performance can slow down dramatically.
For example if each input edge intersect with every others. In this case only few edges can be handled by this node.

- The algorithm does not produce double points.
- It is less robust and can give an error.
- For this algorithm epsilon parameter on N panel is more important. If you get an error you can try to change the parameter to fix.

Difference between algorithm can be shown in some corner cases for example, intersection of 10 boxes by little angle:

.. image:: https://user-images.githubusercontent.com/28003269/67559745-9ad75080-f72a-11e9-9ce6-da1ed027cdef.gif

Prefix 2D means that the node expects from input any kind of flatten mesh
but it does not mean that the mesh should only lay on XY surface.
Input mesh can below or above XY surface or even can be tilted relative one.

The algorithm of finding new intersection is like this:

It takes two edges, removes Z coordinates and finds their intersection.
But after intersection is found it projects intersection point back onto one of the given edges.
This means that input mesh still should be flat but it can be located in space however you like.
Only location of input flatten mesh along Z coordinate will bring the error.

Inputs
------

Verts and Edges only. Warning: Does not support faces, or Vectorized (nested lists) input

*Note: sweep algorithm is vectorized* 


Parameters N-panel
------------------

Epsilon - For comparing float figures. Does not effect on performance.


Outputs
-------

Vertices and Edges, the mesh does not preserve any old vertex or edge index ordering due to the Hashing algorithm used for fast intersection lookups.


Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/619340/2811581/16032c72-ce26-11e3-9055-925d2cd03719.png

See the progress of how this node came to life `here <https://github.com/nortikin/sverchok/issues/109>`_ (gifs, screenshots)