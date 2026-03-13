List Decompose
==============

.. image:: https://user-images.githubusercontent.com/14288520/187529767-1291c5cd-40cd-45b6-a44c-78c02e8c33c5.png
    :target: https://user-images.githubusercontent.com/14288520/187529767-1291c5cd-40cd-45b6-a44c-78c02e8c33c5.png

Functionality
-------------

Inverse to list join node. Separate list at some level of data to several sockets. Sockets count the same as items count in exact level.

Inputs
------

- **data** - adaptable socket

Parameters
----------

+----------------+---------------+-------------+----------------------------------------------------------+
| Parameter      | Type          | Default     | Description                                              |
+================+===============+=============+==========================================================+
| **level**      | Int           | 1           | Level of data to operate.                                |
+----------------+---------------+-------------+----------------------------------------------------------+
| **Count**      | Int           | 1           | Output sockets' count. defined manually or with Auto set |
+----------------+---------------+-------------+----------------------------------------------------------+
| **Auto set**   | Button        |             | Calculate output sockets' count based on data count on   |
|                |               |             | chosen level                                             |
+----------------+---------------+-------------+----------------------------------------------------------+

Outputs
-------

* **data** - multisocket


Example of usage
----------------

**Decomposed simple list in 2 level:**

.. image::  https://user-images.githubusercontent.com/14288520/187661007-c9b8a9c2-d62c-4d32-9f3b-c9326ec411a5.png
    :target: https://user-images.githubusercontent.com/14288520/187661007-c9b8a9c2-d62c-4d32-9f3b-c9326ec411a5.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

**Use 'Auto set' button:**

1. Set Level
2. Press Auto set

.. image:: https://user-images.githubusercontent.com/14288520/187530201-2c9fa567-486e-49d6-9c7c-8138b5dfcbe1.png
    :target: https://user-images.githubusercontent.com/14288520/187530201-2c9fa567-486e-49d6-9c7c-8138b5dfcbe1.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

**Decompose list of Bezier Curves:**

.. image:: https://user-images.githubusercontent.com/14288520/187531176-a495c440-f76b-49a4-adc5-5bd66e65a869.png
    :target: https://user-images.githubusercontent.com/14288520/187531176-a495c440-f76b-49a4-adc5-5bd66e65a869.png

* Curves->Bezier-> :doc:`Bezier Spline (Curve) </nodes/curve/bezier_spline>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/197343084-8d8eac6d-e364-48a4-9125-b5cd739e77b9.png
  :target: https://user-images.githubusercontent.com/14288520/197343084-8d8eac6d-e364-48a4-9125-b5cd739e77b9.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Generator->Generators Extended-> :doc:`Triangle </nodes/generators_extended/triangle>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`