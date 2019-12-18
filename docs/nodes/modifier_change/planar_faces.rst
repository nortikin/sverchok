Make Faces Planar
=================

Functionality
-------------

This node adjusts the positions of mesh vertices, trying to make all it's faces
planar (flat). Obviously, this makes sense only for meshes with Quad and/or
NGon faces.

This node implements standard Blender_'s function "Make Planar Faces". Please
refer to Blender documentation for more details.

.. _Blender: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/cleanup.html#make-planar-faces

Inputs
------

This node has the following inputs:

- **Vertices**. This input is mandatory.
- **Edges**.
- **Faces**. This input is mandatory.
- **FaceMask**. The mask for faces to be considered. By default, all faces are considered.
- **Iterations**. Number of times to repeat the operation. The default value is
  1. This input can also be specified as a parameter. This input expects one
  value per input mesh.
- **Factor**. Distance to move the vertices each iteration. The default value
  is 0.5. This input can also be specified as a parameter. This input expects
  one value per input mesh.

Parameters
----------

This node has no parameters.

Outputs
-------

This node has the following outputs:

- **Vertices**.
- **Edges**.
- **Faces**.
