Index Viewer
============

Functionality
-------------

This node's primary purpose is for display the index information of geometry and topology, it will draw the indices of ``Vertices``, ``Edges``, and ``Faces`` 

- Vertex indices are drawn on the locations of the vertices
- Edge indices are drawn on midpoint of the Edge
- Face indices are drawn at the average location of the Vertices associated with the face.

Additionally 
- the input geometry can be transformed using the Matrix socket.
- the Node can draw arbitrary (non renderable) text into the 3dview at the location of incoming verts. There must be a one-to-one supply of vertices and text to draw, else the node will decide where to draw the excess text elements.

.. image:: https://user-images.githubusercontent.com/619340/127735798-4c3a4222-28ce-418a-b3f0-13c8149a590c.png

- (available from N Panel) the Node can display the Object index associated with the element ( the first object, first index will be drawn as ``0: 0`` )

Because it can be difficult to read indices when there are many geometric elements visible there is an option to draw a small background under the text element.

- (using the Ghost icon in the Node UI) if you attach verts + faces, you can also hide backfacing indices from being displayed. Adding the faces information gives the node enough information to detect what can be seen directly by the viewport "eye" location.

.. image:: https://user-images.githubusercontent.com/619340/127735702-7db6c27a-9f59-4ad4-83f8-44fe96fcbd0c.png





