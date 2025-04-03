Float to Integer
================

.. image:: https://user-images.githubusercontent.com/14288520/189150410-6de52cf6-21d4-4d08-8d2c-e756107ef937.png
  :target: https://user-images.githubusercontent.com/14288520/189150410-6de52cf6-21d4-4d08-8d2c-e756107ef937.png

Functionality
-------------

Converts incoming *Float* values to the nearest whole number *(Integer)*. Accepts lists and preserves levels of nestedness.

Inputs
------

A `float`, alone or in a list

Outputs
-------

An `int`, alone or in a list

Examples
--------

::

    1.0 becomes 1
    -1.9 becomes -2
    4.3 becomes 4
    4.7 becomes 5

    [1.0, 3.0, 2.4, 5.7] becomes [1, 3, 2, 6]

.. image:: https://user-images.githubusercontent.com/14288520/189150447-83ba97de-78c0-4be7-8453-7bfedad60d69.png
  :target: https://user-images.githubusercontent.com/14288520/189150447-83ba97de-78c0-4be7-8453-7bfedad60d69.png

* Number-> :doc:`A Number </nodes/number/numbers>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`