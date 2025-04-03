Simple Deformation
==================

.. image:: https://user-images.githubusercontent.com/14288520/193680193-6a977d2f-cb3d-4cc1-8b00-92396da23b87.png
  :target: https://user-images.githubusercontent.com/14288520/193680193-6a977d2f-cb3d-4cc1-8b00-92396da23b87.png

.. image:: https://user-images.githubusercontent.com/14288520/193679437-93e491be-fa8e-4854-87d7-279e7c4c3bc4.png
  :target: https://user-images.githubusercontent.com/14288520/193679437-93e491be-fa8e-4854-87d7-279e7c4c3bc4.png

Functionality
-------------

This node transforms vertices by one of deformations, similar to Blender's "Simple Deform" modifier.

Inputs
------

This node has the following inputs:

- **Vertices**
- **Origin**. This matrix defines origin and coordinate axis of deformation. Default value is identity matrix.
- **Angle**. Deformation angle. Available in **Twist**, **Bend** modes. 
- **Factor**. Deformation factor. Available in **Taper** mode.
- **Low limit**. Percentage value. Vertices below this limit will use the same transformation as vertices on the boundary.
- **High limit**. Percentage value. Vertices above this limit will use the same transformation as vertices on the boundary.

Parameters
----------

This node has the following parameters:

- **Mode**. Deformation mode. Supported modes are:

  - **Twist**
  - **Bend**
  - **Taper**

  These modes are similar to their namesakes in Blender's "Simple Deform" modifier.
- **Angle mode**. Defines which units are used for **Angle** input. Available values are **Radian** and **Degree**. Default is **Radian**. Available only in **Twist**, **Bend** modes.
- **Lock X**, **Lock Y**. If checked, then corresponding coordinates of vertices will not be changed. Note that this lock is applied to coordinates relative to **Origin**.

Outputs
-------

This node has one output: **Vertices**.

Examples of usage
-----------------

**Bend deformation:**

.. image:: https://user-images.githubusercontent.com/14288520/193681127-f44de94f-f8d0-4487-a02b-1a7e71ba344b.png
  :target: https://user-images.githubusercontent.com/14288520/193681127-f44de94f-f8d0-4487-a02b-1a7e71ba344b.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Twist deformation:**

.. image:: https://user-images.githubusercontent.com/14288520/193681663-77127709-8762-4f78-8f4d-4c64c98411b4.png
  :target: https://user-images.githubusercontent.com/14288520/193681663-77127709-8762-4f78-8f4d-4c64c98411b4.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Taper deformation:**

.. image:: https://user-images.githubusercontent.com/14288520/193681680-e1970271-4283-4cf0-96ed-e2d066209fd8.png
  :target: https://user-images.githubusercontent.com/14288520/193681680-e1970271-4283-4cf0-96ed-e2d066209fd8.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
