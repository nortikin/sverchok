Duplicate along Edge
====================

*destination after Beta: Modifier Change*

Functionality
-------------

This node creates an array of copies of one (donor) mesh and aligns it along given recipient segment (edge). Count of objects in array can be specified by user or detected automatically, based on size of donor mesh and length of recipient edge. Donor mesh can be scaled automatically to fill all length of recipient edge.

Donor objects are rotated so that specified axis of object is aligned to recipient edge.

This node also can output transformation matrices, which should be applied to donor object to be aligned along recipient edge. By default, this node already applies that matrices to donor object; but you can turn this off, and apply matrices to donor object in another node, or apply them to different objects.

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of the donor mesh. The node will produce nothing if this input is not connected.
- **Edges**. Edges of the donor mesh.
- **Polygons**. Faces of the donor mesh.
- **Vertex1**. First vertex of recipient edge. This input is used only when "Fixed" input mode is used (see description of ``Input mode`` parameter below).
- **Vertex2**. Second vertex of recipient edge. This input is used only when "Fixed" input mode is used.
- **VerticesR**. Vertices of the recipient mesh. This input is used only when "Edges" input mode is used.
- **EdgesR**. Edges of the recipient mesh. These edges will be actually used as recipient edges.  This input is used only when "Edges" input mode is used.
- **Count**. Number of objects in array. This input is used only in "Count" scaling mode (see description of ``Scale mode`` parameter below).
- **Padding**. Portion of the recipient edge length that should be left empty from both sides. Default value of zero means fill whole available length.

Parameters
----------

This node has the following parameters:

+------------------+----------------+-------------+------------------------------------------------------------------+
| Parameter        | Type           | Default     | Description                                                      |
+==================+================+=============+==================================================================+
| **Scaling mode** | Count or Up    | Count       | * Count: specify number of objects in array. Objects scale will  |
|                  |                |             |   be calculated so that copies will fill length of recipient     |
|                  |                |             |   edge.                                                          |
|                  | or Down or     |             | * Up: count is determined automatically from length of recipient |
|                  |                |             |   edge and size of donor mesh, and meshes are scaled only up     |
|                  |                |             |   (for example, if donor mesh is 1 unit long, and recipient edge |
|                  |                |             |   is 3.6 units, then there will be 3 meshes scaled to be 1.2     |
|                  |                |             |   units long each).                                              |
|                  | Off            |             | * Down: the same as Up, but meshes are scaled only down.         |
|                  |                |             | * Off: the same as Up, but meshes are not scaled, so there will  |
|                  |                |             |   be some empty space between copies.                            |
+------------------+----------------+-------------+------------------------------------------------------------------+
| **Orientation**  | X or Y or Z    | X           | Which axis of donor object should be aligned to direction of the |
|                  |                |             | recipient edge.                                                  |
+------------------+----------------+-------------+------------------------------------------------------------------+
| **Input mode**   | Edges or Fixed | Edges       | * Edges: recipient edges will be determined as all edges from    |
|                  |                |             |   the ``EdgesR`` input between vertices from ``VerticesR``       |
|                  |                |             |   input.                                                         |
|                  |                |             | * Fixed: recipient edge will be determied as an edge between the |
|                  |                |             |   edge from ``Vertex1`` input and the vertex from ``Vertex2``    |
|                  |                |             |   input.                                                         |
+------------------+----------------+-------------+------------------------------------------------------------------+
| **Scale all      | Bool           | False       | If False, then donor object  will be scaled only along axis      |
| axes**           |                |             | is aligned with recipient edge direction. If True, objects will  |
|                  |                |             | be scaled along all axes (by the same factor).                   |
+------------------+----------------+-------------+------------------------------------------------------------------+
| **Apply          | Bool           | True        | Whether to apply calculated matrices to created objects.         |
| matrces**        |                |             |                                                                  |
+------------------+----------------+-------------+------------------------------------------------------------------+
| **Count**        | Int            | 3           | Number of objects in array. This parameter can be determined     |
|                  |                |             | from the corresponding input. It is used only in "Count" scaling |
|                  |                |             | mode.                                                            |
+------------------+----------------+-------------+------------------------------------------------------------------+
| **Padding**      | Float          | 0.0         | Portion of the recipient edge length that should be left empty   |
|                  |                |             | from both sides. Default value of zero means fill whole length   |
|                  |                |             | available. Maximum value 0.49 means use only central 1% of edge. |
+------------------+----------------+-------------+------------------------------------------------------------------+

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Polygons**
- **Matrices**. Matrices that should be applied to created objects to align them along recipient edge. By default, this node already applies these matrices, so you do not need to do it second time.

This node will output something only when ``Vertices`` or ``Matrices`` output is connected.

Examples of usage
-----------------

Cylinders duplicated along the segment between two specified points:

.. image:: https://cloud.githubusercontent.com/assets/284644/5741079/bcfcd4e2-9c2a-11e4-9f89-95ba59be8bd9.png

Spheres duplicated along the edges of Box:

.. image:: https://cloud.githubusercontent.com/assets/284644/5741080/bd30e0ac-9c2a-11e4-95f3-aa075ef3d7eb.png

You can also find more examples and some discussion `in the development thread <https://github.com/portnov/sverchok/issues/6>`_.

