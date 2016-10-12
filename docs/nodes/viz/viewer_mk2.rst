Viewer Draw MKII
================

*destination after Beta: basic view*

Functionality
-------------

.. image:: https://cloud.githubusercontent.com/assets/619340/4320381/e0cd62b6-3f36-11e4-88ff-29eb165c72ad.png

Built on the core of the original ViewerDraw, this version allows all of the following features.

- Vertex Size (via N-Panel)
- Vertex Color
- Edge Width (via N-Panel)
- Edge Color
- Face shading: Flat vs Normal
- Vertex, Edges, Faces displays can be toggled.
- Defining Normal of Brigtness Source (via N-Panel)
- ``Faux Transparancy`` via dotted edges or checkered polygons.
- optional forced tesselation (via N-Panel) 
- bake and bake all. (via N-Panel, show bake interface is not on by default)

**draws using display lists**

Uses OpenGL display list to cache the drawing function. This optimizes for rotating the viewport around static geometry. Changing the geometry clears the display cache, with big geometry inputs you may notice some lag on the intial draw + cache.

**forced tesselation**

Allows better display for concave polygons, by turning all faces with more than 4 verts into triangles. In this mode Edges will still draw
the boundary of the original polygon and not the new tesselated polygon edges.

Inputs
------

verts + edg_pol + matrices


Parameters
----------

Some info here.

+----------+--------------------------------------------------------------------------------------+
| Feature  | info                                                                                 |
+==========+======================================================================================+
| verts    | verts list or nested verts list.                                                     |
+----------+--------------------------------------------------------------------------------------+
| edge_pol | edge lists or polygon lists, if the first member of any atomic list has two keys,    |
|          | the rest of the list is considered edges. If it finds 3 keys it assumes Faces.       |
|          | Some of the slowness in the algorithm is down to actively preventing invalid key     |
|          | access if you accidentally mix edges+faces input.                                    |
+----------+--------------------------------------------------------------------------------------+
| matrices | matrices can multiply the incoming vert+edg_pol geometry. 1 set of vert+edges can be |
|          | turned into 20 'clones' by passing 20 matrices. See example                          |
+----------+--------------------------------------------------------------------------------------+



Outputs
-------

Directly to 3d view. Baking produces proper meshes and objects.


Examples
--------

development thread: `has examples <https://github.com/nortikin/sverchok/issues/401>`_

.. image:: https://cloud.githubusercontent.com/assets/619340/4265296/4c9c2fb4-3c48-11e4-8999-051c56511720.png


Notes
-----

**Tips on usage**

The viewer will stay responsive on larger geometry when you hide elements of the representation, especially while making updates to the geometry. If you don't need to see vertices, edges, or faces *hide them*. (how often do you need to see all topology when doing regular modeling?). If you see faces you can probably hide edges and verts. 

System specs will play a big role in how well this scripted BGL drawing performs. Don't expect miracles, but if you are conscious about what you feed the Node it should perform quite well given the circumstances.

