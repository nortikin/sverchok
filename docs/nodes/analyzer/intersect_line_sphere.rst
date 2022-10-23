Compass 3D
==========

.. image:: https://user-images.githubusercontent.com/14288520/195917641-85144e87-fe75-44ec-b913-15e27ca0bb12.png
  :target: https://user-images.githubusercontent.com/14288520/195917641-85144e87-fe75-44ec-b913-15e27ca0bb12.png

Functionality
-------------

The node is designed to get the intersection between a sphere and one endless straight line.

This problem has three possible solutions:

* No intersection: the distance of the center of the sphere to the line is bigger than its radius
* One intersection: the line is tangent to the sphere.
* Two intersections: the line passes through the sphere intersecting it surface in two points.

.. image:: https://user-images.githubusercontent.com/14288520/195960052-a486aec0-46e6-46e5-87f2-b711e7821ee4.png
  :target: https://user-images.githubusercontent.com/14288520/195960052-a486aec0-46e6-46e5-87f2-b711e7821ee4.png

The line by two vector creating one segment.

Inputs / Parameters
-------------------

+---------------------+-------------+----------------------------------------------------------------------+
| Param               | Type        | Description                                                          |
+=====================+=============+======================================================================+
| **Vertices**        | Vector      | Points to calculate                                                  |
+---------------------+-------------+----------------------------------------------------------------------+
| **Edges**           | Int List    | Edges data to define the segments (to define the line)               |
+---------------------+-------------+----------------------------------------------------------------------+
| **Center**          | Vectors     | It will get the first and last vertices's to define the line segment |
+---------------------+-------------+----------------------------------------------------------------------+
| **Radius**          | Float       | Radius of the intersecting sphere                                    |
+---------------------+-------------+----------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **Output NumPy**: to get NumPy arrays in stead of regular lists (makes the node faster). Only in the NumPy implementation.
* **Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (one line per group)
* **Match List Local**: Define how list with different lengths should be matched. Refers to the matching of tolerances and vertices

Outputs
-------

* **Intersect Line**: Returns True if the there is valid intersection.
* **Intersection A**: Returns the intersection nearer to the end point of the segment. In case of no intersection returns the closest point on the line.
* **Intersection B**: Returns the intersection nearer to the start point of the segment. In case of no intersection returns the closest point on the line.
* **Int. A in segment**: Returns True if A intersection is over the segment.
* **Int. B in segment**: Returns True if B intersection is over the segment.
* **First in segment**: Returns the first valid value between Int. A, Int. B and Closest point.
* **Int. with segment**: Returns True if the closest point is between the input vertices.
* **All Segment int.**: Returns a flat list of all the intersections.

.. image:: https://user-images.githubusercontent.com/14288520/195949749-057d2a92-9b12-4ea6-b8aa-58e544a7a822.png
  :target: https://user-images.githubusercontent.com/14288520/195949749-057d2a92-9b12-4ea6-b8aa-58e544a7a822.png

Verbose
-------

*Line and Segment are out of sphere*

.. image:: https://user-images.githubusercontent.com/14288520/195958709-712fd929-5da7-4029-80b0-b829d3d76208.png
  :target: https://user-images.githubusercontent.com/14288520/195958709-712fd929-5da7-4029-80b0-b829d3d76208.png

*Line and Segment Tangent of sphere*

.. image:: https://user-images.githubusercontent.com/14288520/195958740-80d5a288-79f6-4336-87cd-c7222c3379a5.png
  :target: https://user-images.githubusercontent.com/14288520/195958740-80d5a288-79f6-4336-87cd-c7222c3379a5.png

*Line and Segment Intersect the Sphere*

.. image:: https://user-images.githubusercontent.com/14288520/195958795-e7fdbb33-633d-430b-8b20-33cb2b8d1a61.png
  :target: https://user-images.githubusercontent.com/14288520/195958795-e7fdbb33-633d-430b-8b20-33cb2b8d1a61.png

*Segment inside Sphere. A and B out of Segment*

.. image:: https://user-images.githubusercontent.com/14288520/195959237-eb2f01cc-4756-429b-b1b3-d1647b810f64.png
  :target: https://user-images.githubusercontent.com/14288520/195959237-eb2f01cc-4756-429b-b1b3-d1647b810f64.png

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/195959580-fbdc4a8e-41d7-4a0f-9ade-160251622bb2.png
  :target: https://user-images.githubusercontent.com/14288520/195959580-fbdc4a8e-41d7-4a0f-9ade-160251622bb2.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/195980664-a29a1a9d-2610-4db2-8283-e57df5887e50.gif
  :target: https://user-images.githubusercontent.com/14288520/195980664-a29a1a9d-2610-4db2-8283-e57df5887e50.gif

---------

In this example the node is used to join one arc with one line with segments of 6 units.

.. image:: https://user-images.githubusercontent.com/14288520/195960897-48104eb0-6a91-4af6-8811-fd4c40e280e4.png
  :target: https://user-images.githubusercontent.com/14288520/195960897-48104eb0-6a91-4af6-8811-fd4c40e280e4.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/195961010-6ab30506-ad7c-4384-bd66-f36a059b07a4.gif
  :target: https://user-images.githubusercontent.com/14288520/195961010-6ab30506-ad7c-4384-bd66-f36a059b07a4.gif

.. image:: https://user-images.githubusercontent.com/14288520/195978009-bbec6def-f094-485f-8279-8e4af70ece78.gif
  :target: https://user-images.githubusercontent.com/14288520/195978009-bbec6def-f094-485f-8279-8e4af70ece78.gif

---------

In this example the node is used find all intersections of one sphere over the edges of a cylinder.

.. image:: https://user-images.githubusercontent.com/14288520/195978818-0414734d-eb59-4bdf-a1c7-853f380701c4.png
  :target: https://user-images.githubusercontent.com/14288520/195978818-0414734d-eb59-4bdf-a1c7-853f380701c4.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/195979176-2f5ac939-a2d8-48ef-99d3-1a9627a3c84b.gif
  :target: https://user-images.githubusercontent.com/14288520/195979176-2f5ac939-a2d8-48ef-99d3-1a9627a3c84b.gif

*Warning*: Intersection Points are not sorted:

.. image:: https://user-images.githubusercontent.com/14288520/195980406-f55c4cc7-f803-4b1f-9fae-f1b4c2243f7b.png
  :target: https://user-images.githubusercontent.com/14288520/195980406-f55c4cc7-f803-4b1f-9fae-f1b4c2243f7b.png

---------

In this example the node is used to simulate a mechanism. The yellow line keeps constant length while connects a moving point with a horizontal rail

.. image:: https://user-images.githubusercontent.com/14288520/195979716-a2a0c1f4-04be-4ba2-b34f-a37b65396e86.png
  :target: https://user-images.githubusercontent.com/14288520/195979716-a2a0c1f4-04be-4ba2-b34f-a37b65396e86.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector Interpolation </nodes/vector/interpolation_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/195979727-1d220d9c-77d5-4828-a526-ddf109a916f0.gif
  :target: https://user-images.githubusercontent.com/14288520/195979727-1d220d9c-77d5-4828-a526-ddf109a916f0.gif