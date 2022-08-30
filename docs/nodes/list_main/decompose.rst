List Decompose
==============

.. image:: https://user-images.githubusercontent.com/14288520/187529767-1291c5cd-40cd-45b6-a44c-78c02e8c33c5.png

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

- **data** - multisocket


Example of usage
----------------

**Decomposed simple list in 2 level:**

.. image::  https://cloud.githubusercontent.com/assets/5783432/18610849/4b14c4fc-7d38-11e6-90ac-6dcad29b0a7d.png

**Use 'Auto set' button:**

1. Set Level
2. Press Auto set

.. image:: https://user-images.githubusercontent.com/14288520/187530201-2c9fa567-486e-49d6-9c7c-8138b5dfcbe1.png

**Decompose list of Bezier Curves:**

.. image:: https://user-images.githubusercontent.com/14288520/187531176-a495c440-f76b-49a4-adc5-5bd66e65a869.png