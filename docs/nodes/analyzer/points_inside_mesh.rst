Points Inside Mesh
==================

Functionality
-------------

The node determines if points are inside a mesh. I has two modes, 2D and 3D

In the 2D mode will determine if points are inside the polygons of the input mesh.

  * When inputting points or verts with different z coordinates the projection to the mesh will be done using the Plane "Normal Input", for a vertical projection it should be (0,0,1) or (0,0,-1).

  * With the Limit Projection checkbox activated the points which are farther than "Max Distance" will be evaluated as out of the mesh

In the 3D mode will determine if a list of probe points are inside an associated manifold boundary mesh (verts, faces). It analyses for each of the probe points whether it is located inside or outside of the boundary mesh.

  *It offers two algorithms Regular is faster, Multisample more precise

  * Warning. This is only a first implementation, likely it will be more correct after a few iterations.

see https://github.com/nortikin/sverchok/pull/1703

Examples of use
---------------
