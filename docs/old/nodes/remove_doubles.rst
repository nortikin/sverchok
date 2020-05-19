:orphan:

Remove Doubles
==============

Functionality
-------------

This removes double vertices/edges/polygons, as do same-named command in blender

Inputs
------

- **Distance**
- **Vertices**
- **PolyEdge**
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.


Parameters
----------

+-----------+-----------+-----------+-------------------------------------------+
| Param     | Type      | Default   | Description                               |
+===========+===========+===========+===========================================+    
| Distance  | Float     | 0.001     | Maximum distance to weld vertices         |
+-----------+-----------+-----------+-------------------------------------------+

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Polygons**
- **Doubles**. Vertices, that were deleted.
- **FaceData**. List containing data items from the **FaceData** input, which
  contains one item for each output mesh face.

Examples of usage
-----------------

.. image:: https://cloud.githubusercontent.com/assets/5783432/18614934/f39a34ce-7da9-11e6-8d2d-88c934f14946.png
