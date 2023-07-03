Marching Squares
================

.. image:: https://user-images.githubusercontent.com/14288520/209447787-335afcf4-26d8-40d5-bb71-2ea28f067475.png
  :target: https://user-images.githubusercontent.com/14288520/209447787-335afcf4-26d8-40d5-bb71-2ea28f067475.png

Dependencies
------------

This node requires SkImage_ library to work.

.. _SkImage: https://scikit-image.org/

Functionality
-------------

This node uses Marching Squares_ algorithm to find iso-lines of a scalar field,
i.e. lines in some plane, for which the scalar field has constant specified
value. The lines are generated as mesh - vertices and edges. You can use one of
interpolation nodes to build Curve objects from them.

.. _Squares: https://en.wikipedia.org/wiki/Marching_squares

.. image:: https://user-images.githubusercontent.com/14288520/209448129-feb46200-4ee7-4c05-b38b-1d23a44af5b3.png
  :target: https://user-images.githubusercontent.com/14288520/209448129-feb46200-4ee7-4c05-b38b-1d23a44af5b3.png

See also
--------

* Fields-> :doc:`Scalar Field Graph </nodes/field/scalar_field_graph>`

Inputs
------

This node has the following inputs:

* **Field**. Scalar field to build iso-curves for. This input can consume a
  list of scalar fields, or a list of lists of scalar fields. Nesting level of
  outputs will correspond to nesting level of data in this input. This input is
  mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/209448345-4b5f4812-b208-47ec-b7b7-fdb255a54838.png
  :target: https://user-images.githubusercontent.com/14288520/209448345-4b5f4812-b208-47ec-b7b7-fdb255a54838.png

.. image:: https://user-images.githubusercontent.com/14288520/209450533-6adb8f4c-cc72-4572-a4b4-382682dd58ac.png
  :target: https://user-images.githubusercontent.com/14288520/209450533-6adb8f4c-cc72-4572-a4b4-382682dd58ac.png

* **Value**. The value, for which the iso-curves should be built. The default
  value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/209451096-b9799be0-a461-4d2d-8d1f-a5fd3d2801cb.png
  :target: https://user-images.githubusercontent.com/14288520/209451096-b9799be0-a461-4d2d-8d1f-a5fd3d2801cb.png

.. image:: https://user-images.githubusercontent.com/14288520/209451130-a401dd2c-0038-4c72-9d44-7dbb54dab444.png
  :target: https://user-images.githubusercontent.com/14288520/209451130-a401dd2c-0038-4c72-9d44-7dbb54dab444.png

* **Samples**. Number of samples along X and Y axes. This defines the
  resolution of curves: the bigger is value, the more vertices will the node
  generate, and the more precise the curves will be. But higher resolution
  requires more computation time. The default value is 50.

.. image:: https://user-images.githubusercontent.com/14288520/209451249-1bb38dc6-4073-457b-abc8-7a0ef3b0f1fd.png
  :target: https://user-images.githubusercontent.com/14288520/209451249-1bb38dc6-4073-457b-abc8-7a0ef3b0f1fd.png

* **MinX**, **MaxX**, **MinY**, **MaxY**. Minimum and maximum values of X and Y
  coordinates to find the iso-curves in. Default values define the square
  ``[-1; +1] x [-1; +1]``.
* **Z**. The value of Z coordinate to generate the curves at. The default value
  is 0. So, by default, the node will use the section of scalar field by XOY
  plane to draw the iso-curves for.

https://gist.github.com/9699442f326876f6af21d8c305a0170c

.. image:: https://user-images.githubusercontent.com/14288520/209451424-705bfb2c-d783-4b59-be22-a9d7d8d59ea7.png
  :target: https://user-images.githubusercontent.com/14288520/209451424-705bfb2c-d783-4b59-be22-a9d7d8d59ea7.png

* **Matrix**. Reference frame to be used. X, Y and Z axes, which are used to
  section the scalar field, are defined by this matrix. By default, identity
  matrix is used, which means the global axes will be used.

https://gist.github.com/e5951d94d21dcb16193b985eb139b7da

.. image:: https://user-images.githubusercontent.com/14288520/209451649-d04a934c-7852-49d2-a8f7-589d3b679048.png
  :target: https://user-images.githubusercontent.com/14288520/209451649-d04a934c-7852-49d2-a8f7-589d3b679048.png

Parameters
----------

This node has the following parameters:

* **Flat output**. If checked, the node will generate a single flat list of
  objects (iso-curves) for all provided iso-values. Otherwise, the node will
  generate a separate list of objects for each iso-value. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/209451720-59f100ed-3425-44e5-b824-cee69a6275c9.png
  :target: https://user-images.githubusercontent.com/14288520/209451720-59f100ed-3425-44e5-b824-cee69a6275c9.png

* **Make faces**. If checked, the node will generate Faces for iso-curves that
  are closed within specified X/Y bounds. Unchecked by default.

Good results on a single value:

.. image:: https://user-images.githubusercontent.com/14288520/209451885-ebae5116-def0-4d21-be9f-4d0f0b3aa1b7.png
  :target: https://user-images.githubusercontent.com/14288520/209451885-ebae5116-def0-4d21-be9f-4d0f0b3aa1b7.png

On several values faces are overlapped:

.. image:: https://user-images.githubusercontent.com/14288520/209451930-6cbca798-a9a8-4e95-8152-13f7897c8776.png
  :target: https://user-images.githubusercontent.com/14288520/209451930-6cbca798-a9a8-4e95-8152-13f7897c8776.png

* **Connect boundary**. If checked, the node will connect pieces of the same
  curve, that was split because it was cut by specified X/Y bounds. Otherwise,
  several separate pieces will be generated in such case. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/209452147-4305cec0-d0f9-46f5-a77f-8ad81c600d29.png
  :target: https://user-images.githubusercontent.com/14288520/209452147-4305cec0-d0f9-46f5-a77f-8ad81c600d29.png

Example of usage
----------------

Build five planes parallel to XOY, and draw iso-lines of scalar field for seven different values:

.. image:: https://user-images.githubusercontent.com/14288520/209452338-a5a7579f-9d3a-44d6-9f62-86919f3cf90d.png
  :target: https://user-images.githubusercontent.com/14288520/209452338-a5a7579f-9d3a-44d6-9f62-86919f3cf90d.png

* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Main-> :doc:`List Match </nodes/list_main/match>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

It is hard to colorize values:

https://gist.github.com/96a7575ff899466965d5158bfe5e7301

.. image:: https://user-images.githubusercontent.com/14288520/209452397-addd6f24-9294-44b0-868b-83458b67db4a.png
  :target: https://user-images.githubusercontent.com/14288520/209452397-addd6f24-9294-44b0-868b-83458b67db4a.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Analyzers-> :doc:`Bounding Box </nodes/analyzer/bbox_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`
* List->List Struct-> :doc:`List First & Last </nodes/list_struct/start_end>`
* List-> :doc:`Filter Empty Objects </nodes/list_mutators/filter_empty_lists>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Scene-> :doc:`Frame Info </nodes/scene/frame_info_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/208299072-ae4c04db-cfe8-4c65-9ed5-495aba74b4df.gif
  :target: https://user-images.githubusercontent.com/14288520/208299072-ae4c04db-cfe8-4c65-9ed5-495aba74b4df.gif