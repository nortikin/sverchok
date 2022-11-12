Barycentric Transform
=====================

.. image:: https://user-images.githubusercontent.com/14288520/191480063-8fa7e15d-1638-4c88-be8c-fcf9e5018e35.png
  :target: https://user-images.githubusercontent.com/14288520/191480063-8fa7e15d-1638-4c88-be8c-fcf9e5018e35.png

Functionality
-------------

The node is coded to perform the transformation of one or many vertices according to the relation of two triangles

Eaxh triangle is defined by three vectors.


Inputs / Parameters
-------------------


+----------------------+-------------+----------------------------------------------------------------------+
| Param                | Type        | Description                                                          |
+======================+=============+======================================================================+
| **Vertices**         | Vertices    | Points to calculate                                                  |
+----------------------+-------------+----------------------------------------------------------------------+
| **Edg_Pol**          | Int Lists   | Edges or pols of the input Vertices (optional)                       |
+----------------------+-------------+----------------------------------------------------------------------+
| **Verts Tri Source** | Vertices    | It will get the first and last vertices's to define the line segment |
+----------------------+-------------+----------------------------------------------------------------------+
| **Verts Tri Target** | Float       | Minimal distance to accept one point is intersecting.                |
+----------------------+-------------+----------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Implementation**: Choose between MathUtils (Faster transforming light meshes) and NumPy (Faster transforming heavy meshes)

**Output NumPy**: to get NumPy arrays in stead of regular lists (makes the node faster). Only in the NumPy implementation.

**Match List**: Define how list with different lengths should be matched. Refers to the matching of groups (one tris couple per group)

Outputs
-------

**Vertices**: Transformed vectors.

**Edg_Pol**: A matched copy of the input Edg_Pol data.


Example of usage
----------------

The node can be used to place geometry over triangular faces.

.. image:: https://user-images.githubusercontent.com/14288520/191495780-406666a4-bc4d-4621-9620-fdff0ea1c574.png
  :target: https://user-images.githubusercontent.com/14288520/191495780-406666a4-bc4d-4621-9620-fdff0ea1c574.png

* Generator-> :doc:`Cricket </nodes/generator/cricket>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Modifiers->Modifier Change-> :doc:`Polygon Boom </nodes/modifier_change/polygons_boom>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The List Match option can offer different output combinations, in this case Cyclic is used

.. image:: https://user-images.githubusercontent.com/14288520/191519778-704fb127-c913-4be2-93c6-d8838d563d7d.png
  :target: https://user-images.githubusercontent.com/14288520/191519778-704fb127-c913-4be2-93c6-d8838d563d7d.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Modifiers->Modifier Change-> :doc:`Polygon Boom </nodes/modifier_change/polygons_boom>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

Custom triangular Tessellation in this case Cyclic is used to alternate between the input geometry

.. image:: https://user-images.githubusercontent.com/14288520/191517586-499375dd-1dad-4fa0-9a65-dc622f7ad7a5.png
  :target: https://user-images.githubusercontent.com/14288520/191517586-499375dd-1dad-4fa0-9a65-dc622f7ad7a5.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Modifiers->Modifier Change-> :doc:`Polygon Boom </nodes/modifier_change/polygons_boom>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`