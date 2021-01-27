Map Range
=========

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
| Old Min           | old minimun value             |
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

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster).

**List Match**: Define how list with different lengths should be matched.


Examples
--------

Basic example:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_1.png

Basic example with clamping:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_2.png

Example with variable lacunarity node:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_3.png

In this example we need to map in the range to the visible values (0.0, 1.0).
The with the *List Limits* activated the node will find the minimum and maximum values of the incoming list and use them as Old Min and Old Max

This node will accept any list shape (vectorized):

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_4.png

This node will accept flat Numpy arrays and can will out them if *Output Numpy* is activated:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Range%20Map/map_range_sverchok_example_5.png
