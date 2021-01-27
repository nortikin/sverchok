:orphan:

Find UV Coordinate on Mesh
========

Functionality
-------------

outputs uvmap object wich can be used to visually understend where input vertices lie on uv texture.
Translates vectors from UV space to object local space.
Works most accurately on triangulated meshes. Quads are ok if not distorted much. Object must have UV layer unwraped.

Inputs
------

- **Point on UV** points in 1x1 unit UV texture space (look on uvmap object to know where to place them)

Outputs
-------

- **Point on mesh**. Points on UV transformed to local space of object.
- **UVMapVert**. vertices of uvmap object.
- **UVMapPoly**. polygons of uvmap object.

Example of usage
----------------
.. image:: https://user-images.githubusercontent.com/22656834/37982776-f237ce18-320a-11e8-93eb-84e143e8a6c2.png
