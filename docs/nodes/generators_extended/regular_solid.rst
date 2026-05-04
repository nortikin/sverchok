Regular Solid
=============

.. image:: https://user-images.githubusercontent.com/14288520/191001959-df7d4dbf-ca59-4a95-8a3f-a6d8c9fc208d.png
  :target: https://user-images.githubusercontent.com/14288520/191001959-df7d4dbf-ca59-4a95-8a3f-a6d8c9fc208d.png

Functionality
-------------

This node is a port to the Regular Solid functions (by dreampainter) now part of the 'Extra Mesh Objects' Add-on that can be downloaded from the "Get Extensions" panel in the Blender properties
(https://archive.blender.org/wiki/index.php/Extensions:2.6/Py/Scripts/Add_Mesh/Add_Solid/)

It creates Platonic, Archimedean or Catalan solids


Inputs & Parameters
-------------------

+-------------------+-----------------------------------------------+
| Name              | Descriptor                                    |
+===================+===============================================+
| Preset            | Parameters for some hard names                |
+-------------------+-----------------------------------------------+
| Source            | Starting point of your solid                  |
+-------------------+-----------------------------------------------+
| Snub              | Create the snub version                       |
+-------------------+-----------------------------------------------+
| Dual              | Create the dual of the current solid          |
+-------------------+-----------------------------------------------+
| Keep Size         | Keep the whole solid at a constant size       |
+-------------------+-----------------------------------------------+
| Size              | Radius of the sphere through the vertices     |
+-------------------+-----------------------------------------------+
| Vertex Truncation | Amount of vertex truncation                   |
+-------------------+-----------------------------------------------+
| Edge Truncation   | Amount of edge truncation                     |
+-------------------+-----------------------------------------------+

When list are used as input many solids will be created


Outputs
-------

Vertices, Edges and Polygons of the mesh or meshes.


Examples 
--------
Some of the shapes that can be generated:

.. image:: https://user-images.githubusercontent.com/14288520/191015511-d24fbed2-628a-461c-9d94-e1677fee3205.png
  :target: https://user-images.githubusercontent.com/14288520/191015511-d24fbed2-628a-461c-9d94-e1677fee3205.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Add: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Variations of the cube:

.. image:: https://user-images.githubusercontent.com/14288520/191018476-2a9b6d67-e94d-4d68-909d-8cbca6ae3032.png
  :target: https://user-images.githubusercontent.com/14288520/191018476-2a9b6d67-e94d-4d68-909d-8cbca6ae3032.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Add: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`


Notes
-----

As this node takes functions form the 'Extra Mesh Objects' add-on it wont work if the add-on is not installed, please download it before using the node
