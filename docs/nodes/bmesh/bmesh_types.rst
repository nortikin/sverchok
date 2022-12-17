BMesh Types
===============

.. image:: https://user-images.githubusercontent.com/74725748/208011439-5a1947f5-eb64-4db0-88eb-c9efcc83c4aa.png

Functionality
-------------
This is a simple packaging of the bmesh.types module. This module is the cornerstone of 
the BMESH object. You can access the elements of the BMESH object through this module 
and The corresponding method, such as accessing the vertex of BMESH, the neighbors of the 
side...
This is an introduction to this module on the Blender website：
https://docs.blender.org/api/3.3/bmesh.types.html

Mod
1. This module is divided into these seven types
.. image::https://user-images.githubusercontent.com/74725748/208013050-f5ea366c-003a-40b3-868e-5c01f611532c.png
2. Each type has the corresponding class
.. image::https://user-images.githubusercontent.com/74725748/208013237-e7eb515f-09ba-4f94-932f-4bbe12e85fcb.png
3. Each class has some corresponding methods
.. image::https://user-images.githubusercontent.com/74725748/208013876-bf55c29a-bebf-434d-a004-9c13851d07a4.png

Inputs
------
The input depends on the mode selected, and each socket has a corresponding interpretation

Outputs
-------

- **return** - Some handlers will return some useful data

Examples
--------

**Get the volume of the BMESH object**

.. image:: https://user-images.githubusercontent.com/74725748/208014346-abcbd246-2367-4216-a8f0-c997cfa3cb8b.png
