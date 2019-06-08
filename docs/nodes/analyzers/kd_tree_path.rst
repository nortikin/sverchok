KDT Closest Path
=================

Functionality
-------------

Using a K-dimensional Tree it will create a path starting at the desired index joining each vertex to the closest free vertex. If no vertex is found in the desired range the path will break and will start a new path at the next unused vertex.


Inputs / Parameter
-------------------

+--------------+---------+-----------------------------------------------------------+
| Name         | Type    | Description                                               |  
+==============+=========+===========================================================+
| Verts        | Vectors | Vertices to make path                                     |   
+--------------+---------+-----------------------------------------------------------+
| Max Distance | float   | Maximum Distance to accept a pair                         |
+--------------+---------+-----------------------------------------------------------+
| Start Index  | Int     | Vert index where path will start                          |
+--------------+---------+-----------------------------------------------------------+
| Cyclic       | Boolean | Enable to join the first and last vertices                |
+--------------+---------+-----------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups 

**Match List Local**: Define how list with different lengths should be matched. Refers to the matching of max distances and vertices

Outputs
-------

- Edges, which can connect the pool of incoming Vertices to make a path.

Examples
--------

Creating paths in a random vector field.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/kd_tree_path/KDT_closest_path_examples.png
  :alt: Blender_sverchok_KDT_closest_path_examples.png

Find the best starting index to make the minimum path by starting at every vertex and comparing the path lengths and taking the shortest one.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/kd_tree_path/KDT_closest_path_examples1.png
  :alt: procedural_sverchok_KDT_closest_path_examples1.png

Find a coherent short path among shuffled vertices.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/kd_tree_path/KDT_closest_path_examples2.png
  :alt: parametric_sverchok_KDT_closest_path_examples2.png

