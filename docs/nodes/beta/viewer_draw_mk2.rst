Viewer Draw MKII
===========

*destination after Beta: basic view*

Functionality
-------------

Built on the core of the original ViewerDraw, this version allows all of the following features.

- Vertex Size
- Vertex Color
- Edge Width
- Edge Color
- Face shading: Flat vs Normal
- Vertex, Edges, Faces displays can be toggled.
- Defining Normal of Brigtness Source (N panel)
- ``Faux Transparancy`` via dotted edges or checkered polygons.
- bake and bake all.

Uses OpenGL display list to cache the drawing function. This optimizes viewport rotation speeds and behaviour. 
Changing the geometry clears the display cache, with big geometry inputs you may notice some lag on the intial draw + cache.

Inputs
------

verts + edg_pol + matrices

Parameters
----------

========= ================
Feature   info
========= ================
verts     verts list of nested verts list.
--------- ----------------
edge_pol  edge lists or polygon lists, if the first member of any atomic list has two keys, the rest of the list is considered edges. If it finds 3 keys it assumes Faces. Some of the slowness in the algorithm is down to actively preventing invalid key access if you accidentally mix edges+faces input.
--------- ----------------
matrices  matrices can multiply the incoming vert+edg_pol geometry. 1 set of vert+edges can be turned into 20 'clones' by passing 20 matrices. See example
--------- ----------------


Outputs
-------

Examples
--------

Notes
-----