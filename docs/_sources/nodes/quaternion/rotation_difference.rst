Rotation difference
===================

.. image:: https://user-images.githubusercontent.com/14288520/189345318-1bf5f65b-f500-47d7-a987-71fa066b824d.png
  :target: https://user-images.githubusercontent.com/14288520/189345318-1bf5f65b-f500-47d7-a987-71fa066b824d.png

Functionality
-------------

Creates quaternion which produce rotation from first to second given points.
It can be alternative of `normal matrix` node. Meanwhile last one can work only with limited number of axis 
the `rotation difference` node can work with arbitrary axes.

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
    :target: https://user-images.githubusercontent.com/28003269/72435614-ecd2c400-37b7-11ea-80f2-176a0d1df5ee.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Matrix-> :doc:`Matrix Out </nodes/matrix/matrix_out_mk2>`
* Quaternion-> :doc:`Quaternion Out </nodes/quaternion/quaternion_out_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`


.. image:: https://user-images.githubusercontent.com/28003269/72435623-f52aff00-37b7-11ea-984a-e0d0d4b14013.gif
    :target: https://user-images.githubusercontent.com/28003269/72435623-f52aff00-37b7-11ea-984a-e0d0d4b14013.gif

Also it is possible to make movements of monkey head more natural by applying Z component separately:

.. image:: https://user-images.githubusercontent.com/28003269/72444577-b7cf6d00-37c9-11ea-8052-0be2fa3de938.png
    :target: https://user-images.githubusercontent.com/28003269/72444577-b7cf6d00-37c9-11ea-8052-0be2fa3de938.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Component-Wise: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Quaternion-> :doc:`Quaternion Out </nodes/quaternion/quaternion_out_mk2>`
* Quaternion Multiply: Quaternion-> :doc:`Quaternion Math </nodes/quaternion/quaternion_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/28003269/72444896-43e19480-37ca-11ea-87c8-326b5c63e6b5.gif
    :target: https://user-images.githubusercontent.com/28003269/72444896-43e19480-37ca-11ea-87c8-326b5c63e6b5.gif