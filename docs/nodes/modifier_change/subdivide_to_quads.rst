Subdivide to Quads
==================

Functionality
-------------

Subdivide polygon faces to quads, similar to subdivision surface modifier.

Inputs
------

This node has the following inputs:

- **Vertices**
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

Use of Vert Map output:

.. image:: https://user-images.githubusercontent.com/10011941/116822057-19614980-ab7d-11eb-8e97-4b2b3c453656.png

Use of Vert Data Dict:

.. image:: https://user-images.githubusercontent.com/10011941/116845901-7560b800-abe7-11eb-9a20-9a53ddeb8c5f.png

Use of Face Data Dict:

.. image:: https://user-images.githubusercontent.com/10011941/116822473-3434bd80-ab7f-11eb-8c2a-d228b4168d17.png

Rock from a Tetrahedron:

.. image:: https://user-images.githubusercontent.com/10011941/116846820-81e61000-abe9-11eb-9ce1-c323c1e1915f.png
