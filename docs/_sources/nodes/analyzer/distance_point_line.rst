Distance Point Line
===================

.. image:: https://user-images.githubusercontent.com/14288520/195555169-5c1b254b-27f8-48b4-9e9c-21c5056ca9e9.png
  :target: https://user-images.githubusercontent.com/14288520/195555169-5c1b254b-27f8-48b4-9e9c-21c5056ca9e9.png

Functionality
-------------

The node is designed to get the distance between a point and one endless straight line.

The line is defined by a segment of two vectors.

As an extra results you can get:

- If the point is in the line
- If the point is in the segment
- Which is the closest point in the line
- If the closest point is in the segment

.. image:: https://user-images.githubusercontent.com/14288520/195613198-9e6514b3-dd12-4a20-a356-63d9f2ecb6a5.png
  :target: https://user-images.githubusercontent.com/14288520/195613198-9e6514b3-dd12-4a20-a356-63d9f2ecb6a5.png

Inputs / Parameters
-------------------


+---------------------+-------------+----------------------------------------------------------------------+
| Param               | Type        | Description                                                          |
+=====================+=============+======================================================================+
| **Vertices**        | Vertices    | Points to calculate                                                  |
+---------------------+-------------+----------------------------------------------------------------------+
| **Line Vertices**   | Vertices    | It will get the first and last vertices's to define the line segment |
+---------------------+-------------+----------------------------------------------------------------------+
| **Tolerance**       | Float       | Minimal distance to accept one point is intersecting.                |
+---------------------+-------------+----------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **Implementation**: Choose between MathUtils and NumPy (Usually faster)
* **Output NumPy**: to get NumPy arrays in stead of regular lists (makes the node faster). Only in the NumPy implementation.
* **Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (one line per group)
* **Match List Local**: Define how list with different lengths should be matched. Refers to the matching of tolerances and vertices


Outputs
-------

* **Distance**: Distance to the line.
* **In Segment**: Returns True if point distance is less than tolerance and the point is between the input vertices.
* **In Line**: Returns True if point distance is less than tolerance with input vertices.
* **Closest Point**: Returns the closest point in the line.
* **Closest in Segment**: Returns True if the closest point is between the input vertices.


Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/195602111-9092dc72-b78d-4cf0-9413-a31dc6a96e24.png
  :target: https://user-images.githubusercontent.com/14288520/195602111-9092dc72-b78d-4cf0-9413-a31dc6a96e24.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* Analyzers-> :ref:`Component Analyzer/Edges/Center <EDGES_CENTER>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Text-> :doc:`String Tools </nodes/text/string_tools>`

.. image:: https://user-images.githubusercontent.com/14288520/195618979-c50985ac-ccb5-4de7-bab6-a701a176e6cd.gif
  :target: https://user-images.githubusercontent.com/14288520/195618979-c50985ac-ccb5-4de7-bab6-a701a176e6cd.gif

---------

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_line/distance_point_line_sverchok_blender.png
  :target: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_line/distance_point_line_sverchok_blender.png
  :alt: Distance_point_line_procedural.PNG

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

It can be used to create perpendicular lines from input points

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_line/distance_point_line_sverchok_blender_perpendicular_to_line.png
  :target: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_line/distance_point_line_sverchok_blender_perpendicular_to_line.png
  :alt: Sverchok_Distance_point_line.PNG

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

In this example the node is used to separate the points which are at less than two units from the line.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_line/distance_point_line_sverchok_blender_procedural.png
  :target: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/distance_point_line/distance_point_line_sverchok_blender_procedural.png
  :alt: Blender_distance_point_line.PNG

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

In this example the Inset Polygon node gets the inset and distance inputs from the distance of the polygon to the line.

.. image:: https://user-images.githubusercontent.com/14288520/195623831-73dd3212-c282-4aa1-816b-ab8d6175d5dc.png
  :target: https://user-images.githubusercontent.com/14288520/195623831-73dd3212-c282-4aa1-816b-ab8d6175d5dc.png
  :alt: Sverchok_Distance_polygon_line.PNG

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* CAD-> :doc:`Inset Special </nodes/CAD/inset_special_mk2>`
* MUL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

This example uses the node to scale geometry along a custom axis.

.. image:: https://user-images.githubusercontent.com/14288520/195638114-3671af20-5b9a-42aa-a09b-7ab95d1e89ce.png
  :target: https://user-images.githubusercontent.com/14288520/195638114-3671af20-5b9a-42aa-a09b-7ab95d1e89ce.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Vector-> :doc:`Vector Lerp </nodes/vector/lerp>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/195638831-57568578-6e86-4b94-8263-d4ebaeeccf22.gif
  :target: https://user-images.githubusercontent.com/14288520/195638831-57568578-6e86-4b94-8263-d4ebaeeccf22.gif
