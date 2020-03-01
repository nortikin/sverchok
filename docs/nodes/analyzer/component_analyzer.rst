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

    * **Normal**. Vertices normal vector.
    * **Matrix ZY**: Matrix aligned with normal.
    * **Sharpness**: Curvature of mesh in vertex.
    * **Adjacent Edges**: Adjacent edges.
    * **Adjacent Faces**: Adjacent faces.
    * **Adjacent Edges num**: Number of Adjacent edges.
    * **Adjacent Faces num**: Number of adjacent faces.
    * **Is Boundary**: Is Vertex on mesh borders.
    * **Is Interior**: Is Vertex on mesh interior.
    * **Is Manifold**: Is Vertex part of the Manifold.
    * **Is Wire**: Is vertex only connected by edges.


  * For **Edges**, supported criteria are:

    * **Geometry**. Geometry of each edge. (explode).
    * **Direction**.  Normalized edge direction.
    * **Center**. Edges Midpoint.
    * **Origin**. Edges first point.
    * **End**. Edges End point.
    * **Normal**. Edge Normal
    * **Matrix**. Matrix aligned with edge.
    * **Matrix Normal**. Matrix aligned with edge and edge normal (needs faces).
    * **Length**. Edge length.
    * **Sharpness**. Average of curvature of mesh in edges vertices.
    * **Face Angle**. Edges faces angle.
    * **Inverted**. Reversed edges.
    * **Adjacent faces**. Adjacent faces.
    * **Adjacent faces Num**. Adjacent faces number.
    * **Is Boundary**.  Is Edge on mesh borders.
    * **Is Contiguous**. Is Edge contiguous.
    * **Is Convex**. Is Edge Convex.
    * **Is Manifold**. Is Edge part of the Manifold.
    * **Is Wire**. Has no related faces.

  * For **Faces**, supported criteria are:

    * **Geometry**. Geometry of each face. (explode)
    * **Center**.
       * **Center Bounds**. Center of bounding box of faces.
       * **Center Median**. Mean of vertices of each face.
       * **Center Median Weighted**. Mean of vertices of each face weighted by edges length.
    * **Normal**. Normal of faces.
    * **Normal Absolute**. Median Center + Normal.
    * **Tangent**.
       * **Tangent edge**. Face tangent based on longest edge.
       * **Tangent edge diagonal**. Face tangent based on the edge farthest from any vertex.
       * **Tangent edge pair**. Face tangent based on the two longest disconnected edges.
       * **Tangent vert diagonal**. Face tangent based on the two most distant vertices.
    * **Matrix**. Matrix aligned with face.
    * **Area**. Area of faces
    * **Perimeter**. Perimeter of faces
    * **Sides**. Sides of faces
    * **Neighbor Faces Num**. Number of Faces that share a edge with face
    * **Adjacent Faces Num**. Number of Faces that share a vertex with face.
    * **Sharpness**. Average of curvature of mesh in faces vertices
    * **Inverse**. Reversed Polygons (Flipped).
    * **Edges**. Face Edges.
    * **Adjacent Faces**. Faces that share a edge with face.
    * **Neighbor Faces**. Faces that share a vertex with face.
    * **Is Boundary**. Is the face boundary or interior


* **Output Parameters**: Depending on output nature (if offers multiple results per component or single result) the node offers one of this parameters.

  * **Split Output**. Split the result to get one object per result *[[0, 1], [2]] --> [[0], [1], [2]]*
  * **Wrap Output**. Keeps original data shape *[Matrix, Matrix, Matrix] --> [[Matrix, Matrix], [Matrix]]*


Example of usage
----------------

Component Matrix:

.. image:: https://user-images.githubusercontent.com/10011941/71564525-ffec5100-2aa1-11ea-9fda-d9605ff3812f.png

Component Sharpness:

.. image:: https://user-images.githubusercontent.com/10011941/71564638-61adba80-2aa4-11ea-9c1f-c1f5551287cf.png

Adjacent Edges, Faces Angle and Neibor Faces Num:

.. image:: https://user-images.githubusercontent.com/10011941/71564682-134ceb80-2aa5-11ea-9b97-15891503f39c.png

Edge Tools:

.. image:: https://user-images.githubusercontent.com/10011941/71649567-37f8cb80-2d10-11ea-8cfc-aca8958750c8.png
