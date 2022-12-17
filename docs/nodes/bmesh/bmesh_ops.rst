BMesh Ops
===============

.. image:: https://user-images.githubusercontent.com/74725748/207805773-2180255b-ac92-4882-b119-70a00316645b.png

Functionality
-------------
All functions within the Operators submodule of BMesh, which provides many convenient 
functions for working with bmesh objects，
This is an introduction to this module on the Blender website：
https://docs.blender.org/api/3.3/bmesh.ops.html

Mod
Contains all functions of the submodule
.. image::https://user-images.githubusercontent.com/74725748/206601200-7434443b-1c34-4d6e-87a1-a3dfeb2e1e1d.png
Each function node has a corresponding interpretation
.. image::https://user-images.githubusercontent.com/74725748/208007979-d0af0467-44f9-4abf-b147-f81298802a57.png

Inputs
------
The input depends on the mode selected, and each socket has a corresponding interpretation
.. image:https://user-images.githubusercontent.com/74725748/208009616-fb88992f-2998-42aa-8f4c-03e58ece6fb9.png

Outputs
-------
- **Bmesh** - The processed bmesh object
- **return** - Some handlers will return some useful data

Examples
--------

**Limited dissolution:**

.. image:: https://user-images.githubusercontent.com/74725748/208010937-b64cb9e7-aff3-47ad-8520-9194c005712c.png
