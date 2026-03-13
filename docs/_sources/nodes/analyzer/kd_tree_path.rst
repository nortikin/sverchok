KDT Closest Path
=================

.. image:: https://user-images.githubusercontent.com/14288520/196288317-b722f118-7e59-4013-9e1e-6208b5aa587f.png
  :target: https://user-images.githubusercontent.com/14288520/196288317-b722f118-7e59-4013-9e1e-6208b5aa587f.png

.. image:: https://user-images.githubusercontent.com/14288520/196291396-d6aab023-7dc5-410e-8563-bb0ab74123a6.png
  :target: https://user-images.githubusercontent.com/14288520/196291396-d6aab023-7dc5-410e-8563-bb0ab74123a6.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

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

* **Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups 
* **Match List Local**: Define how list with different lengths should be matched. Refers to the matching of max distances and vertices

Outputs
-------

- Edges, which can connect the pool of incoming Vertices to make a path.

Examples
--------

Creating paths in a random vector field.

.. image:: https://user-images.githubusercontent.com/14288520/196292568-b402cab3-db88-4c0c-9126-54034366266e.png
  :target: https://user-images.githubusercontent.com/14288520/196292568-b402cab3-db88-4c0c-9126-54034366266e.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Vector-> :doc:`Vector Rewire </nodes/vector/vector_rewire>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Find the best starting index to make the minimum path by starting at every vertex and comparing the path lengths and taking the shortest one.

.. image:: https://user-images.githubusercontent.com/14288520/196377705-41e926f3-87c6-41d7-ace0-53436f6c642b.png
  :target: https://user-images.githubusercontent.com/14288520/196377705-41e926f3-87c6-41d7-ace0-53436f6c642b.png

* Number-> :doc:`A Number </nodes/number/numbers>`
* EQUAL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Analyzers-> :doc:`Path Length </nodes/analyzer/path_length_2>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* List->List Struct-> :doc:`List Levels </nodes/list_struct/levels>`
* List->List Main-> :doc:`List Math </nodes/list_main/func>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

Find a coherent short path among shuffled vertices.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/kd_tree_path/KDT_closest_path_examples2.png
  :target: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/kd_tree_path/KDT_closest_path_examples2.png
  :alt: parametric_sverchok_KDT_closest_path_examples2.png

* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`