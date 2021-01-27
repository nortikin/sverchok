Rotation difference
===================

.. image:: https://user-images.githubusercontent.com/28003269/72435157-ded07380-37b6-11ea-9ec3-7f8e0b20afda.png

Functionality
-------------

Creates quaternion which produce rotation from first to second given points.
It can be alternative of `normal matrix` node. Meanwhile last one can work only with limited number of axis 
the `rotation difference` node can work with arbitrary axises.

Category
--------

Quaternions -> Rotation difference

Inputs
------

- **Verts_A** - vertices (start of rotation)
- **Verts_B** - vertices (end of rotation)

Outputs
-------

- **Quaternions** - rotation difference between given points

Parameters
----------

+--------------------------+-------+--------------------------------------------------------------------------------+
| Parameters               | Type  | Description                                                                    |
+==========================+=======+================================================================================+
| Flat output              | bool  | Put all quaternions into flat list                                             |
+--------------------------+-------+--------------------------------------------------------------------------------+

Usage
-----

First vector of the node is initial direction of monkey head, second one is direction of empty object:

.. image:: https://user-images.githubusercontent.com/28003269/72435614-ecd2c400-37b7-11ea-80f2-176a0d1df5ee.png
.. image:: https://user-images.githubusercontent.com/28003269/72435623-f52aff00-37b7-11ea-984a-e0d0d4b14013.gif

Also it is possible to make movements of monkey head more natural by applying Z component separately:

.. image:: https://user-images.githubusercontent.com/28003269/72444577-b7cf6d00-37c9-11ea-8052-0be2fa3de938.png
.. image:: https://user-images.githubusercontent.com/28003269/72444896-43e19480-37ca-11ea-87c8-326b5c63e6b5.gif