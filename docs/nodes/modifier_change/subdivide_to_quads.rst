Subdivide to Quads
==================

Functionality
-------------

Subdivide polygon faces to quads, similar to subdivision surface modifier.

Inputs
------

This node has the following inputs:

- **Vertrices**
- **Polygons**.
- **Iterations**. Subdivision levels.
- **Normal Displace**. Displacement along normal (value per iteration)
- **Center Random**. Random Displacement on face plane (value per iteration).
- **Normal Random**. Random Displacement along normal (value per iteration)
- **Random Seed**
- **Smooth**. Smooth Factor (value per iteration)
- **Vert Data Dict** Dictionary with the attributes you want to spread through the new vertices.
  The resultant values will be the interpolation of the input values. Accepts Scalars, Vectors and Colors

- **Face Data Dict** Dictionary with the attributes you want to spread through the new faces.
  The resultant values will be a copy of the base values.


Advanced parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). Available for Vertices, Edges and Pols and Vert Map

Outputs
-------

This node has the following outputs:

- **Vertices**. All vertices of resulting mesh.
- **Edges**. All edges of resulting mesh.
- **Faces**. All faces of resulting mesh.
- **Vert Map**. List containing a integer related to the order the verts where created (See example Below)
  contains one item for each output mesh face.
- **Vert Data Dict**. Dictionary with the new vertices attributes.
- **Face Data Dict**. Dictionary with the new faces attributes.

Performance Note
----------------

The algorithm under this node is fully written in NumPy and the node will perform faster
if the input values (verts, polygons, vert and face attributes..) are NumPy arrays

Examples of usage
-----------------

The simplest example, subdivide a cube:

.. image:: https://cloud.githubusercontent.com/assets/284644/25096716/476682dc-23c3-11e7-8788-624be2573d3b.png

Subdivide one face of a cube, with smoothing:

.. image:: https://cloud.githubusercontent.com/assets/284644/25096718/47976654-23c3-11e7-8da8-87ea420d8355.png

Subdivide a cube, with smooth falloff type = Smooth:

.. image:: https://cloud.githubusercontent.com/assets/284644/25096717/4794fed2-23c3-11e7-8c53-28fb1d18b69d.png

Subdivide a torus, with smooth falloff type = Sphere:

.. image:: https://cloud.githubusercontent.com/assets/284644/25096721/479a2c72-23c3-11e7-9012-612ce3fd1039.png
