Triangle
========

.. image:: https://user-images.githubusercontent.com/14288520/191045694-9fcb8f28-be7d-4473-a068-f79bcb5bef81.png
  :target: https://user-images.githubusercontent.com/14288520/191045694-9fcb8f28-be7d-4473-a068-f79bcb5bef81.png


Functionality
-------------

The node is designed to generate triangles from various combinations of vertices, sides length and angles.

Inputs / Parameters
-------------------


+------------+---------+-------------------------------------------------------------------------+
| Param      | Type    | Description                                                             |
+============+=========+=========================================================================+
| **Mode**   | Enum    | Choose how you want to define the triangle:                             |
|            |         |                                                                         |
|            |         | * A_c_Alpha_Beta: One Vertex, the contiguous side length and two angles |
|            |         | * A_B_Alpha_Beta: Two Vertex and two angles                             |
|            |         | * A_b_c_Alpha: One Vertex, two contiguous sides' length and one angle   |
|            |         | * A_B_b_Alpha: Two Vertex, one side length and one angle                |
|            |         | * A_a_b_c: One Vertex, and length of the three sides                    |
|            |         | * A_B_a_b Two Vertex, and length of the two sides                       |
|            |         | * A_B_C : Three Vertex                                                  |
+------------+---------+-------------------------------------------------------------------------+
| **A**      | Vector  | Vertex A of the triangle                                                |
+------------+---------+-------------------------------------------------------------------------+
| **B**      | Vector  | Vertex B of the triangle                                                |
+------------+---------+-------------------------------------------------------------------------+
| **C**      | Vector  | Vertex C of the triangle                                                |
+------------+---------+-------------------------------------------------------------------------+
| **a**      | Float   | Normal of the plane B                                                   |
+------------+---------+-------------------------------------------------------------------------+
| **b**      | Float   | Normal of the plane B                                                   |
+------------+---------+-------------------------------------------------------------------------+
| **c**      | Float   | Normal of the plane B                                                   |
+------------+---------+-------------------------------------------------------------------------+
| **Alpha**  | Float   | Normal of the plane B                                                   |
+------------+---------+-------------------------------------------------------------------------+
| **Beta**   | Float   | Normal of the plane B                                                   |
+------------+---------+-------------------------------------------------------------------------+


Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Join Last level**: Join (mesh join) last level of triangles (default set to False)

**Remove Doubles**: Remove doubles of the joined triangles (only active when "Join Last Level" is True)

**Tolerance**: Removing Doubles Tolerance (only active when "Remove Doubles" is True)

**Flat output**: Flatten output by list-joining level 1 and unwrapping it (default set to True)

**Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (level 1)

**Match List Local**: Define how list with different lengths should be matched. Refers to the matching inside groups (level 2)


Outputs
-------

**Vertices**: Vertex of triangles

**Edges**: Edges of triangles

**Faces**: Polygon data of the triangles

Example of usage
----------------

Three ways of getting the same triangle from different inputs

.. image:: https://user-images.githubusercontent.com/14288520/191047575-8345d4c7-2891-4dfa-b7c1-3a6b22147344.png
  :target: https://user-images.githubusercontent.com/14288520/191047575-8345d4c7-2891-4dfa-b7c1-3a6b22147344.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The node can be used to generate more complex shapes, note that "join last level" is activated the N-Panel

.. image:: https://user-images.githubusercontent.com/14288520/191052089-3490928b-0bc1-44ad-a4c7-998c081da04b.png
  :target: https://user-images.githubusercontent.com/14288520/191052089-3490928b-0bc1-44ad-a4c7-998c081da04b.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* CAD-> :doc:`Inset Special </nodes/CAD/inset_special_mk2>`
* List->List Struct-> :doc:`List Shift </nodes/list_struct/shift_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Advanced example using the node to generate structural ribbons

* old example

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators_extended/Triangle/triangle_node_sverchok_example_02.png
  :alt: sverchok_triangle_node_example2.png

* restore the old example with a new version of nodes

.. image:: https://user-images.githubusercontent.com/14288520/191064494-53646309-446e-46bc-94f3-178cd4419ed6.png
  :target: https://user-images.githubusercontent.com/14288520/191064494-53646309-446e-46bc-94f3-178cd4419ed6.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* SIN, MUL, ADD: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`