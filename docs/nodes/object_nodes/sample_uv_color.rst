Sample UV texture color on Mesh
========

Functionality
-------------

Takes vector in local object space and returns color of corresponding pixel on UV map.
Works most accurately on triangulated meshes. Quads are ok if not distorted much. Object must have UV layer unwraped.

Inputs
------

- **Point on mesh** points placed near to, or on surface of object.

Outputs
-------

- **Color on UV**. Color of pixel on UV texture related to given vector.

Example of usage
----------------
.. image:: https://user-images.githubusercontent.com/22656834/38020888-d5358dc0-3294-11e8-83c8-0204378ea6db.png
