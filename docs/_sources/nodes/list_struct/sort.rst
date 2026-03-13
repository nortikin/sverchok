List Sort
=========

.. image:: https://user-images.githubusercontent.com/14288520/187995646-ed8c3c53-3fad-4882-9175-6cf9bd037bf3.png
  :target: https://user-images.githubusercontent.com/14288520/187995646-ed8c3c53-3fad-4882-9175-6cf9bd037bf3.png

Functionality
-------------

Sort items from list. It should accept any type of data from Sverchok: Vertices, Strings (Edges, Polygons), Matrix, Curves, Surfaces, Fields or Blender data.

The node will sort the data based on the keys list. I not keys list is supplied the node will sort the data based in the data itself, note that this is only possible with numeric data.

Inputs
------

* **Data**: Any kind of data.
* **Keys**: List with the  desired order of the data (new positions)

Parameters
----------

* **Level:** Set the level at which to observe the List. Level 1 is top level (totally zoomed out), higher levels get more granular (zooming in) until no higher level is found (atomic). The node will just sort the data at the level selected.

Outputs
-------

* **Data**: Sorted data. Depends on incoming data and can be nested.

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/188199920-cae91075-e413-4804-b4f7-4759986d9242.png
  :target: https://user-images.githubusercontent.com/14288520/188199920-cae91075-e413-4804-b4f7-4759986d9242.png

* List->List Struct-> :doc:`List Shuffle </nodes/list_struct/shuffle>`
* Text-> :doc:`Simple Text </nodes/text/simple_text>`
* Text-> :doc:`String Tools </nodes/text/string_tools>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/188199934-419325ec-3eb8-453f-8040-66b430a9c445.png
  :target: https://user-images.githubusercontent.com/14288520/188199934-419325ec-3eb8-453f-8040-66b430a9c445.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Simple Text </nodes/text/simple_text>`
* Text-> :doc:`String Tools </nodes/text/string_tools>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`



Sorting a list of random numbers:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/list_struct/sort/list_sort_sverchok_blender_example_00.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/list_struct/sort/list_sort_sverchok_blender_example_00.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Viz-> :doc:`Viewer 2D </nodes/viz/viewer_2d>`

Sorting a List of Objects:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/list_struct/sort/list_sort_sverchok_blender_example_01.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/list_struct/sort/list_sort_sverchok_blender_example_01.png

* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`


Sorting faces based on theirs center Z coordinate:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/list_struct/sort/list_sort_sverchok_blender_example_02.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/list_struct/sort/list_sort_sverchok_blender_example_02.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* CA: Faces Center: Analyzers-> :doc:`Component Analyzer </nodes/analyzer/component_analyzer>`
* Vector-> :doc:`Vector Out </nodes/vector/vector_out>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Examples of sorting at different levels:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/list_struct/sort/list_sort_sverchok_blender_example_03.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/list_struct/sort/list_sort_sverchok_blender_example_03.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* List->List Struct-> :doc:`List Reverse </nodes/list_struct/reverse>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`