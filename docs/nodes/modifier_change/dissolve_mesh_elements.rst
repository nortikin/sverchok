Dissolve mesh elements
======================

.. image:: https://user-images.githubusercontent.com/28003269/89492228-2d307880-d7c2-11ea-9a4a-ab12e7dd699a.png

Functionality
-------------
Dissolve will remove the geometry and fill in the surrounding geometry. 
Instead of removing the geometry, which may leave holes that you have to fill in again.

Category
--------

Modifiers -> Modifier change -> Dissolve mesh elements

Inputs
------

- **Verts** - vertices of given mesh(es)
- **Edges** - edges of given mesh(es)
- **Faces** - faces of given mesh(es)
- **Mask** - mask of vertices, edges or faces which should be dissolved

Parameters
----------

- **Mode** 
   - Verts - Remove the vertex, merging all surrounding faces. In the case of two edges, merging them into a single edge
   - Edges - Removes edges sharing two faces (joining those faces)
   - Faces - Merges regions of faces that share edges into a single face

- **Use face split** When dissolving vertices into surrounding faces, you can often end up with very large, uneven n-gons. The face split option limits dissolve to only use the corners of the faces connected to the vertex.

- **Use boundary tear** Split off face corners instead of merging faces.

- **Use verts** Undocumented

.. image:: https://user-images.githubusercontent.com/28003269/89491528-87303e80-d7c0-11ea-99ad-63335902a996.png

*1) Original mesh. 2) Face Split: Off, Tear Boundaries: Off. 3) Face Split: On, Tear Boundaries: Off. 
4) Face Split: On/Off, Tear Boundaries: On.*

Outputs
-------

- **Verts** - vertices of dissolved mesh
- **Edges** - edges of dissolved mesh
- **Faces** - faces of dissolved mesh
- **Verts ind** - vertices indexes of mesh before dissolving operation
- **Edges ind** - edges indexes of mesh before dissolving operation
- **Faces ind** - faces indexes of mesh before dissolving operation
- **Loops ind** - loops indexes of mesh before dissolving operation

*Note: `Index` sockets can map data of mesh elements from mesh before operation to mesh after operation. 
For mapping operation `list item` node can be used.*

.. image:: https://user-images.githubusercontent.com/28003269/89492923-d88dfd00-d7c3-11ea-974c-440472e0bb92.png

Examples
--------

**Dissolve random edges**

.. image:: https://user-images.githubusercontent.com/28003269/89445808-af8a4f80-d764-11ea-8d00-66c8d58f7519.gif

**Dissolve all edges except vertical and horizontal**

.. image:: https://user-images.githubusercontent.com/28003269/89520787-70eda700-d7ef-11ea-9a61-b2e8d8b9fd74.gif
.. image:: https://user-images.githubusercontent.com/28003269/89520841-8531a400-d7ef-11ea-9c2d-67d43caeb09a.png

**Dissolve faces by area**

.. image:: https://user-images.githubusercontent.com/28003269/89521871-561c3200-d7f1-11ea-8c5b-6e1e38b4549b.gif
.. image:: https://user-images.githubusercontent.com/28003269/89521875-56b4c880-d7f1-11ea-98e4-a79ff30fecb0.png
