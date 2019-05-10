Regular Solid
=============

Functionality
-------------

This node is a port to the Regular Solid functions (by dreampainter) now part of the Extra Objects Add-on bundled with Blender
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

.. image:: https://user-images.githubusercontent.com/10011941/57547653-3896b900-735f-11e9-8186-8e9491655bf4.png
  :alt: Regular_Solid_.png

Variations of the cube:

.. image:: https://user-images.githubusercontent.com/10011941/57547665-3df40380-735f-11e9-9112-ea8f2f4bc202.png
  :alt: Regular_Solid.png


