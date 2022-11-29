Separate Loose Parts
====================

.. image:: https://user-images.githubusercontent.com/14288520/199338722-345e55b5-1aef-4332-8f4e-901b25d6045f.png
  :target: https://user-images.githubusercontent.com/14288520/199338722-345e55b5-1aef-4332-8f4e-901b25d6045f.png

Functionality
-------------

Split a mesh into unconnected parts in a pure topological operation.

.. image:: https://user-images.githubusercontent.com/14288520/199342753-4a038cb3-e353-4c60-8c77-77bdb854f92d.png
  :target: https://user-images.githubusercontent.com/14288520/199342753-4a038cb3-e353-4c60-8c77-77bdb854f92d.png

Input & Output
--------------

+--------+-----------+-------------------------------------------+
| socket | name      | Description                               |
+========+===========+===========================================+    
| input  | Vertices  | Inputs vertices                           |
+--------+-----------+-------------------------------------------+
| input  | Poly Edge | Polygon or Edge data                      |
+--------+-----------+-------------------------------------------+
| output | Vertices  | Vertices for each mesh part               |
+--------+-----------+-------------------------------------------+
| output | Poly Edge | Corresponding mesh data                   |
+--------+-----------+-------------------------------------------+

Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/619340/4186249/46e799f2-375f-11e4-8fab-4bf1776b244a.png
  :target: https://cloud.githubusercontent.com/assets/619340/4186249/46e799f2-375f-11e4-8fab-4bf1776b244a.png
  :alt: separate-looseDemo1.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Modifiers->Modifier Change-> :doc:`Mesh Join </nodes/modifier_change/mesh_join_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/199344180-850a0af5-5174-464a-b89d-cc8099176051.png
  :target: https://user-images.githubusercontent.com/14288520/199344180-850a0af5-5174-464a-b89d-cc8099176051.png

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Analyzers-> :doc:`Select Mesh Elements </nodes/analyzer/mesh_select_mk2>`
* Modifiers->Modifier Change-> :doc:`Mask Vertices </nodes/modifier_change/vertices_mask>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* List->List Main-> :doc:`List Decompose </nodes/list_main/decompose>`
* NOT: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Notes
-----

Note that it doesn't take double vertices into account.
There is no guarantee about the order of the outputs
