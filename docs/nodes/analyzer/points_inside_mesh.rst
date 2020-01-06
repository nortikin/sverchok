Points Inside Mesh
==================

Functionality
-------------

The node determines if points are inside a mesh. I has two modes, 2D and 3D

In the 2D mode will determine if points are inside the polygons of the input mesh.

  * When inputting points or verts with different z coordinates the projection to the mesh will be done using the "Plane "Normal" input, for a vertical projection it should be (0,0,1) or (0,0,-1).

  * With the Limit Projection checkbox activated the points which are farther than "Max Distance" will be evaluated as out of the mesh

In the 3D mode will determine if a list of probe points are inside an associated manifold boundary mesh (verts, faces). It analyses for each of the probe points whether it is located inside or outside of the boundary mesh.

  *It offers two algorithms Regular is faster, Multisample more precise

  * Warning. This is only a first implementation, likely it will be more correct after a few iterations.

see https://github.com/nortikin/sverchok/pull/1703

Examples of use
---------------

.. image:: https://user-images.githubusercontent.com/10011941/71828078-eea6d400-30a1-11ea-8b12-618479a5ef32.png

.. image:: https://user-images.githubusercontent.com/10011941/71828631-fa46ca80-30a2-11ea-97ee-a5a3475b4fc6.png

.. image:: https://user-images.githubusercontent.com/10011941/71829174-4b0af300-30a4-11ea-992e-1f1e5b04fbc3.png

.. image::  https://user-images.githubusercontent.com/10011941/71830943-244ebb80-30a8-11ea-93ca-404eeea91799.png
