Diamond Mesh
============

Functionality
-------------

This node generates a new (rhomboidal / diamond-like) mesh, by replacing each
edge of original mesh by a rhombus (connecting centers of two incidential
faces). This can give interesting topology, especially in combination with
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

- **Vertices**. Vertices of the diamond mesh.
- **Edges**. Edges of the diamond mesh.
- **Faces**. Faces of the diamond mesh.

Examples of Usage
-----------------

The simplest example — diamond mesh for a plane / grid:

.. image:: https://user-images.githubusercontent.com/284644/74258086-92c21180-4d17-11ea-8837-d57c52a4c7dd.png

Diamond mesh for a cube:

.. image:: https://user-images.githubusercontent.com/284644/74258156-b1c0a380-4d17-11ea-8fec-9e6f03ea7932.png

In combination with "dual mesh" node:

.. image:: https://user-images.githubusercontent.com/284644/74258160-b2f1d080-4d17-11ea-87ac-578ce4d2f3ca.png

In another combination with "dual mesh" node:

.. image:: https://user-images.githubusercontent.com/284644/74258165-b38a6700-4d17-11ea-8041-5e58351c1c17.png

