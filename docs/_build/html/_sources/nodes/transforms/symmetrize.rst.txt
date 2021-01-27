Symmetrize
==========

Functionality
-------------

This node performs the standard Blender's "Symmetrize" transformation on the
mesh. In general, it takes one half of the mesh, mirrors it relative to some
plane, and then joins these two halfs together. Please refer to Blender_
documentation for more precise description of the transformation.

.. _Blender: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/basics/symmetry.html#symmetrize

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of the input mesh.
- **Edges**. Edges of the input mesh.
- **Polygons**. Faces of the input mesh.
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.
- **Matrix**. Transformation space matrix. This defines what exactly X, Y and Z
  axis will mean. The default value is identity matrix, which means X, Y and Z
  axes will coincide with global X, Y and Z coordinate axes. This input is
  expected to contain one matrix per input mesh. Optional input.

Parameters
----------

This node has the following parameters:

- **Direction**. Transformation direction. This defines which half of the mesh
  will be taken and where it will be mirrored to. The following directions are:

   - **-X to +X**
   - **+X to -X**
   - **-Y to +Y**
   - **+Y to -Y**
   - **-Z to +Z**
   - **+Z to -Z**

   The default value is **-X to +X**. Note that X, Y and Z directions are
   defined by the **Matrix** input.

- **Merge Distance**. The vertices in this range will be snapped to the plane
  of symmetry. The default value is 0.001.

Outputs
-------

This node has the following outputs:

- **Vertices**. Output mesh vertices.
- **Edges**. Output mesh edges.
- **Polygons**. Output mesh polygons.
- **FaceData**. List containing data items from the **FaceData** input, which
  contains one item for each output mesh face.

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/284644/70862260-ca9d1a80-1f5b-11ea-8b60-eaedb1a1c134.png

.. image:: https://user-images.githubusercontent.com/284644/70862414-f1f4e700-1f5d-11ea-9aba-b3091a38ca41.png

.. image:: https://user-images.githubusercontent.com/284644/70867189-81b58800-1f94-11ea-8d17-463571e781ec.png

