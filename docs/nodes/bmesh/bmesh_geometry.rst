BMesh Geometry
===============

.. image:: https://user-images.githubusercontent.com/74725748/208014640-65d807b9-34b7-4186-a50e-33dc9d2db08a.png

Functionality
-------------
This is a simple packaging of the bmesh.geometry module. At present, there is only one function 
that is used to detect points.
This is an introduction to this module on the Blender website：
https://docs.blender.org/api/3.3/bmesh.geometry.html

Inputs
------

- **face** - (bmesh.types.BMFace) – The face to test.
- **point ** -(float triplet) – The point to test.

Outputs
-------

- **return** - True when the projection of the point is in the face.

Examples
--------

**Whether the projection of the point is in the face**

.. image:: https://user-images.githubusercontent.com/74725748/208039019-24711778-e1ef-44b1-88f8-ab93106481f3.png
