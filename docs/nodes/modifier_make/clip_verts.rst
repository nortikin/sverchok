Clip Vertices
=============

Functionality
-------------

This node cuts off (clips, truncates) all vertices of original mesh, by cutting
each edge in half, and then connecting centers of all edges incidential to each
vertex, to produce new faces. Please refer to usage examples for better
understanding.

This can give interesting topology, especially in combination with
"dual mesh" and/or "triangulate" and/or "join triangles" and/or "limited
dissolve" nodes.

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of original mesh. This input is mandatory.
- **Edges**. Edges of original mesh.
- **Faces**. Faces of original mesh. This input is mandatory.

Outputs
-------

This node has the following outputs:

- **Vertices**. Vertices of the new mesh.
- **Edges**. Edges of the new mesh.
- **Faces**. Faces of the new mesh.

Examples of Usage
-----------------

Clip a simple plane / grid:

.. image:: https://user-images.githubusercontent.com/284644/74450509-fb3bfa80-4e9f-11ea-9acb-f40c44ae2f3d.png

Clip vertices of a cube:

.. image:: https://user-images.githubusercontent.com/284644/74450490-f6774680-4e9f-11ea-8504-85d9a7902b52.png

Applied to a cylinder:

.. image:: https://user-images.githubusercontent.com/284644/74450506-faa36400-4e9f-11ea-85c5-6899bcaef782.png


Applied to Suzanne:

.. image:: https://user-images.githubusercontent.com/284644/74450498-f8d9a080-4e9f-11ea-9ee2-dbbb0914eb53.png

