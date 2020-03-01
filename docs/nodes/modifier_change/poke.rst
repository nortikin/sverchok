Poke Faces
==========

Functionality
-------------

This node splits each selected faces into a triangle fan, creating a new center
vertex and triangles between the original face edges and new center vertex. The
**Offset** parameter can be used to make spikes or depressions.

This node provides an interface to standard Blender_'s "Poke face" operator.
Please refer to Blender documentation for more details.

.. _Blender: https://docs.blender.org/manual/en/latest/modeling/meshes/editing/faces.html

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Polygons**
- **FaceMask**. The mask for faces to be poked. By default, all faces are considered.
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.

Parameters
----------

This node has the following parameters:

- **Poke Center**. This defines how the center of a face is calculated. The following options are available:

  - **Weighted Mean**.  Using the mean average weighted by edge length.
  - **Mean**.  Using the mean average.
  - **Bounds**.  Uses center of bounding box. 

   The default mode is **Weighted Mean**.

- **Offset Relative**. If checked, then the value of **Offset** parameter/input
  will be multiplied by the average length from the center to the face
  vertices. Unchecked by default.
- **Offset**. Poke offset. Defines the offset of the new center vertex along
  the face normal. This parameter can also be provided as input. The default
  value is 0.

Outputs
-------

This node has the following outputs:

- **Vertices**.
- **Edges**.
- **Faces**.
- **FaceData**. List containing data items from the **FaceData** input, which
  contains one item for each output mesh face.

Examples of usage
-----------------

Poke applied to a box:

.. image:: https://user-images.githubusercontent.com/284644/74262771-51cdfb00-4d1f-11ea-8b0d-9b31fb36380a.png

Applied to Icosphere:

.. image:: https://user-images.githubusercontent.com/284644/74262774-52ff2800-4d1f-11ea-94e7-6c295fdbdc55.png

Applied to only one face of the cube:

.. image:: https://user-images.githubusercontent.com/284644/74263493-c190b580-4d20-11ea-82bf-88e74a14aa87.png

