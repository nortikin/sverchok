Component Analyzer
=================

Functionality
-------------

This node allows to get the related data to mesh elements (vertices, edges and faces)

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Faces**

Parameters
----------

This node has the following parameters:

- **Mode**. This parameter defines what elements are you interested: Vertices, Edges or Faces.
- **Operator**. Criteria type to apply. Supported criteria set depends on Mode:

  * For **Vertices** supported criteria are:

    * **Normal**. Vertices with similar normal vector.
    * **Adjacent edges num**: Number of Adjacent edges
    * **Adjacent faces num**: Number of adjacent faces
    * **Adjacent edges**: Adjacent edges
    * **Adjacent faces**: Adjacent faces
    * **Sharpness**: Curvature of mesh in vertex
    * **Is Boundary**: Is Vertex on mesh borders
    * **Is Manifold**: Is Vertex part of the Manifold
    * **Is Wire**: Is vertex only connected by edges
    * **'Matrix ZY**: Matrix, Z in normal, Y up
    * **Matrix YX**: Matrix, Y in normal, X up
    * **Matrix XZ**: Matrix, X in normal, Z up

  * For **Edges**, supported criteria are:

    * **Geometry**. Geometry of each edge. (explode)
    * **Length**. Edge length
    * **Direction**.  'Normalized Direction
    * **Normal**. Edge Normal
    * **Face Angle**. Edges faces angle
    * **Is Boundary**.  Is Edge on mesh borders
    * **Is Contiguous**. Is Edge contiguous
    * **Is Convex**. Is Edge Convex
    * **Is Manifold**. Is Edge part of the Manifold
    * **Is Wire**. Has no related faces
    * **Sharpness**. Average of curvature of mesh in edges vertices.
    * **Center**. Edges Midpoint.
    * **Origin**. Edges first point.
    * **End**. Edges End point.
    * **Adjacent faces**. Adjacent faces.
    * **Adjacent faces Num**. Adjacent faces number
    * **Matrix Center Z**. Matrix in center of edge. Z axis on edge. Y up
    * **Matrix Center Z'**. Matrix in center of edge. Z axis on edge. Z in normal
    * **Matrix Center X'**. Matrix in center of edge. X axis on edge. Z in normal

  * For **Faces**, supported criteria are:

    * **Geometry**. Geometry of each face. (explode)
    * **Area**. Area of faces
    * **Sides**. Sides of faces
    * **Perimeter**. Perimeter of faces
    * **Normal**. Normal of faces
    * **Normal Absolute**. Median Center + Normal
    * **Center Bounds**. Center of bounding box of faces
    * **Center Median**. Mean of vertices of each face
    * **Center Median Weighted**. Mean of vertices of each face weighted by edges length
    * **Tangent edge**. Face tangent based on longest edge
    * **Tangent edge diagonal**. Face tangent based on the edge farthest from any vertex.
    * **Tangent edge pair**. Face tangent based on the two longest disconnected edges.
    * **Tangent vert diagonal**. Face tangent based on the two most distant vertices.
    * **Edges**. Face Edges.
    * **Matrix**. Matrix in median center of face. Z axis on normal. X to first corner.
    * **Matrix Median Align**. Matrix in median center of face. Z axis on normal. X aligned with first edge.
    * **Matrix p0 Align**. Matrix in first corner of face. Z axis on normal. X aligned with first edge.

Outputs
-------

This node has the following outputs:

- **Mask**. This indicates elements selected by the node. This mask is to be applied to vertices, edges or faces, depending on selected mode.
- **Vertices**. Selected vertices. This output is only available in **Vertices** mode.
- **Edges**. Selected edges. This output is only available in **Edges** mode.
- **Faces**. Selected faces. This output is only available in **Faces** mode.

Examples of usage
-----------------

Select faces with similar normal vector. Originally selected faces are marked with red color.

.. image:: https://cloud.githubusercontent.com/assets/284644/25073036/6cabd4da-22ff-11e7-9880-143d8af4b8c9.png

Select faces with similar area. Originally selected faces are marked with red color.

.. image:: https://cloud.githubusercontent.com/assets/284644/25073037/6ce11f50-22ff-11e7-8744-f5aefb616f23.png

Select edges with direction similar to selected edges. Originally selected edges are marked with orange color.

.. image:: https://cloud.githubusercontent.com/assets/284644/25073037/6ce11f50-22ff-11e7-8744-f5aefb616f23.png
