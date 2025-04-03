Embed Mesh
===============

.. image:: https://user-images.githubusercontent.com/74725748/204120088-03599881-59d5-4f6c-b7de-3b90b1f620cc.png

Functionality
-------------
Embed mesh B on mesh A into mesh A, and in simple terms, you will get the structure of mesh B on mesh A


Inputs
------

- **VertsA** - vertices of mesh A
- **EdgesA** - edges of mesh A
- **FacesA** - faces of mesh A
- **VertsB** - vertices of mesh B
- **EdgesB** - edges of mesh B
- **FacesB** - faces of mesh B
- **Index**  - Specifies on which face of mesh A each point of mesh B is on

Outputs
-------

- **Verts** - vertices of new mesh
- **Edges** - edges of new mesh
- **Faces** - faces of new mesh
- **Index** - Index of the B-edge structure of the mesh on the new mesh

Modes
-----

None

N panel
-------

- **Epsilon** - For nearness tests; number of figures after coma

Examples
--------

**knife project(with raycaster node):**

.. image:: https://user-images.githubusercontent.com/74725748/204120874-005aa169-166a-466d-bd07-aa5e8a35ed77.png

**mesh bool(with Nearest Point on Mesh):**

.. image:: https://user-images.githubusercontent.com/74725748/204191959-202a40ea-e7ab-4994-875f-c7160a4fdf6a.png
