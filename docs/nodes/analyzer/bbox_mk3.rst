Bounding Box
============

.. image:: https://user-images.githubusercontent.com/14288520/194720618-63fa358e-1532-4afd-aaeb-8d51afc4b40b.png
  :target: https://user-images.githubusercontent.com/14288520/194720618-63fa358e-1532-4afd-aaeb-8d51afc4b40b.png

Functionality
-------------

Generates a special ordered *bounding box* from incoming Vertices.

Inputs
------

**Vertices**, or a nested list of vertices that represent separate objects.

Parameters
----------

2D / 3D: The 2D implementation works over the XY plane always outputting 0 in the Z coordinate, and instead of a box produces a rectangle.

Min, Max and Size: Chose which outputs you want the node to display.

Outputs
-------

+----------+-----------+----------------------------------------------------------------------------+
| Output   | Type      | Description                                                                |
+==========+===========+============================================================================+
| Vertices | Vectors   | One or more sets of Bounding Box vertices.                                 |
+----------+-----------+----------------------------------------------------------------------------+
| Edges    | Key Lists | One or more sets of Edges corresponding to the Vertices of the same index. |
+----------+-----------+----------------------------------------------------------------------------+
| Mean     | Vectors   | Arithmetic averages of the incoming sets of vertices.                      |
+----------+-----------+----------------------------------------------------------------------------+
| Center   | Matrix    | Represents the *Center* of the bounding box; the average of its vertices.  |
|          |           |                                                                            |
|          |           | The scale of the matrix would make a box with size of 1 unit to match the  |
|          |           |                                                                            |
|          |           | size the desired bounding box.                                             |
+----------+-----------+----------------------------------------------------------------------------+
| Min X    | Scalar    | Minimum value on the X axis.                                               |
+----------+-----------+----------------------------------------------------------------------------+
| Min Y    | Scalar    | Minimum value on the Y axis.                                               |
+----------+-----------+----------------------------------------------------------------------------+
| Min Z    | Scalar    | Minimum value on the Z axis.                                               |
+----------+-----------+----------------------------------------------------------------------------+
| Max X    | Scalar    | Maximum value on the X axis.                                               |
+----------+-----------+----------------------------------------------------------------------------+
| Max Y    | Scalar    | Maximum value on the Y axis.                                               |
+----------+-----------+----------------------------------------------------------------------------+
| Max Z    | Scalar    | Maximum value on the Z axis.                                               |
+----------+-----------+----------------------------------------------------------------------------+
| Size X   | Scalar    | Size on the X axis.                                                        |
+----------+-----------+----------------------------------------------------------------------------+
| Size Y   | Scalar    | Size on the Y axis.                                                        |
+----------+-----------+----------------------------------------------------------------------------+
| Size Z   | Scalar    | Size on the Z axis.                                                        |
+----------+-----------+----------------------------------------------------------------------------+


See also
--------

* Analyzers-> :doc:`Diameter </nodes/analyzer/diameter>`


Examples
--------

**Bounding Box:**

.. image:: https://user-images.githubusercontent.com/14288520/194720834-1842e08d-50e8-4152-b987-4233e3541e8a.png
  :target: https://user-images.githubusercontent.com/14288520/194720834-1842e08d-50e8-4152-b987-4233e3541e8a.png

* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Bounding Box with several objects:**

.. image:: https://user-images.githubusercontent.com/14288520/194721530-8ceca99a-eae9-436e-b069-ad0961894c86.png
  :target: https://user-images.githubusercontent.com/14288520/194721530-8ceca99a-eae9-436e-b069-ad0961894c86.png

* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

**Mean: Average of incoming set of Vertices**

.. image:: https://user-images.githubusercontent.com/14288520/194722095-b9f90455-cd8f-487e-a259-a511b65f95d1.png
  :target: https://user-images.githubusercontent.com/14288520/194722095-b9f90455-cd8f-487e-a259-a511b65f95d1.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/194722181-e30fb712-a2ac-4161-aac9-581a23f6faac.png
  :target: https://user-images.githubusercontent.com/14288520/194722181-e30fb712-a2ac-4161-aac9-581a23f6faac.png

* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Center: Average of the Bounding Box**

.. image:: https://user-images.githubusercontent.com/14288520/194722001-00255d7d-09d6-40e5-969b-bb75f22e3015.png
  :target: https://user-images.githubusercontent.com/14288520/194722001-00255d7d-09d6-40e5-969b-bb75f22e3015.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/194722439-61630150-5cb0-439a-83d8-44fb79e8f957.png
  :target: https://user-images.githubusercontent.com/14288520/194722439-61630150-5cb0-439a-83d8-44fb79e8f957.png

* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

**2D Mode: produces rectangles at z = 0**

.. image:: https://user-images.githubusercontent.com/14288520/194723335-d1a6dd58-fc50-4b0d-a08d-a264a88daf64.png
  :target: https://user-images.githubusercontent.com/14288520/194723335-d1a6dd58-fc50-4b0d-a08d-a264a88daf64.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Notes
-----

GitHub issue tracker discussion about this node `here1 <https://github.com/nortikin/sverchok/issues/161>`_
and `here2 <https://github.com/nortikin/sverchok/pull/2575>`__
