Map Range
=========

.. image:: https://user-images.githubusercontent.com/14288520/189152416-91fa5117-b41f-45f1-a9b1-18af806c62a9.png
  :target: https://user-images.githubusercontent.com/14288520/189152416-91fa5117-b41f-45f1-a9b1-18af806c62a9.png

This node map all the incoming values in the desired range.

Input and Output
^^^^^^^^^^^^^^^^
All the values except clamp, may be floats or int.

+-------------------+-------------------------------+
| socket            | description                   |
+===================+===============================+
| **inputs**        |                               |
+-------------------+-------------------------------+
| value             | incoming float values         |
+-------------------+-------------------------------+
| Old Min           | old minimum value             |
+-------------------+-------------------------------+
| Old Max           | old maximum value             |
+-------------------+-------------------------------+
| New Min           | new minimum value             |
+-------------------+-------------------------------+
| New Max           | new maximum value             |
+-------------------+-------------------------------+
| List limits       | get Old Min and Old Max from  |
|                   | the Min and Max of Value list |
+-------------------+-------------------------------+
| Clamp             | clamp the values if they are  |
|                   | outside the range             |
+-------------------+-------------------------------+
| **outputs**       |                               |
+-------------------+-------------------------------+
| value             | outcoming values              |
+-------------------+-------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster).
* **List Match**: Define how list with different lengths should be matched.


Examples
--------

Basic example:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_1.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_1.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Basic example with clamping:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_2.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_2.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Example with variable lacunarity node:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_3.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_3.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* List->List Main-> :doc:`List Math </nodes/list_main/func>`
* Vector-> :doc:`Variable Lacunarity </nodes/vector/variable_lacunarity>`
* Viz-> :doc:`Texture Viewer Lite </nodes/viz/viewer_texture_lite>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

In this example we need to map in the range to the visible values (0.0, 1.0).
The with the *List Limits* activated the node will find the minimum and maximum values of the incoming list and use them as Old Min and Old Max

This node will accept any list shape (vectorized):

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_4.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_4.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

This node will accept flat Numpy arrays and can will out them if *Output Numpy* is activated:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_5.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_5.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`