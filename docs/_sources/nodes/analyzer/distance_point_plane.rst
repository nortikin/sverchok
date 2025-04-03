Distance Point Plane
====================

.. image:: https://user-images.githubusercontent.com/14288520/195645023-96031605-bbf2-463a-998c-a31456a83435.png
  :target: https://user-images.githubusercontent.com/14288520/195645023-96031605-bbf2-463a-998c-a31456a83435.png

Functionality
-------------

The node is designed to find the distance between a point and one plane.

The plane is defined by three points.

As extra results you can get from the node:

- If the point is in the triangle.
- If point is in the plane. 
- Closest point in the plane. 
- If the closest point is inside the triangle.

Inputs / Parameters
-------------------

+---------------------+-------------+---------------------------------------------------------------------------------------------+
| Param               | Type        | Description                                                                                 |
+=====================+=============+=============================================================================================+
| **Vertices**        | Vertices    | Points to calculate                                                                         |
+---------------------+-------------+---------------------------------------------------------------------------------------------+
| **Verts Plane**     | Vertices    | It will get the first three vertices of the input list to define the triangle and the plane |
+---------------------+-------------+---------------------------------------------------------------------------------------------+
| **Tolerance**       | Float       | Minimal distance to accept one point is intersecting.                                       |
+---------------------+-------------+---------------------------------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **Implementation**: Choose between MathUtils and NumPy (Usually faster)
* **Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). Only in the NumPy implementation.
* **Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (one plane per group)
* **Match List Local**: Define how list with different lengths should be matched. Refers to the matching of tolerances and vertices

Outputs
-------

* **Distance**: Distance to the line.
* **In Triangle**: Returns True if the point  coplanar and inside the triangle formed by the input vertices
* **In Plane**: Returns True if point is in the same plane as with input vertices.
* **Closest Point**: Returns the closest point in the plane
* **Closest in Triangle**: Returns true if the closest point is in the same plane as with input vertices.
* **Side**: True if Source Point on Normal side.

.. image:: https://user-images.githubusercontent.com/14288520/195653818-3861a5ef-f779-4628-abcf-db26a06df34e.png
  :target: https://user-images.githubusercontent.com/14288520/195653818-3861a5ef-f779-4628-abcf-db26a06df34e.png

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/195654774-7c278f64-e216-4403-b4de-f27f8f61aa95.png
  :target: https://user-images.githubusercontent.com/14288520/195654774-7c278f64-e216-4403-b4de-f27f8f61aa95.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator->Generators Extended-> :doc:`Triangle </nodes/generators_extended/triangle>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Analyzers-> :ref:`Component Analyzer/Faces/Normal <FACES_NORMAL>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

In this example the node is used to split the points depending of the side of the plane. Also the ones that are near to the plane (under intersection tolerance).

.. image:: https://user-images.githubusercontent.com/14288520/195657305-504c0e5f-a837-4e2e-9e7d-c7ec868b95fe.png
  :target: https://user-images.githubusercontent.com/14288520/195657305-504c0e5f-a837-4e2e-9e7d-c7ec868b95fe.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Generator->Generators Extended-> :doc:`Triangle </nodes/generators_extended/triangle>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

It can be used to project the geometry over a plane.

.. image:: https://user-images.githubusercontent.com/14288520/195660504-00f1f663-e877-469f-ac22-aa6534168dfa.png
  :target: https://user-images.githubusercontent.com/14288520/195660504-00f1f663-e877-469f-ac22-aa6534168dfa.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator->Generators Extended-> :doc:`Triangle </nodes/generators_extended/triangle>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/195661216-8c41af36-4cd5-4127-9514-af86db2816dd.gif
  :target: https://user-images.githubusercontent.com/14288520/195661216-8c41af36-4cd5-4127-9514-af86db2816dd.gif