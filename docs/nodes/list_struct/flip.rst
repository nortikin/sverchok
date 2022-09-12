List Flip
=========

.. image:: https://user-images.githubusercontent.com/14288520/187999003-a4180572-59d1-47ed-9d02-839bbb58115a.png
  :target: https://user-images.githubusercontent.com/14288520/187999003-a4180572-59d1-47ed-9d02-839bbb58115a.png

Functionality
-------------

Flips the data on selected level.

[[[1,2,3],[4,5,6],[7,8,9]],[[3,3,3],[1,1,1],[8,8,8]]] (two objects, three vertices)

with level 2 turns to:

[[[1, 2, 3], [3, 3, 3]], [[4, 5, 6], [1, 1, 1]], [[7, 8, 9], [8, 8, 8]]] (three objects, two vertices)

with level 3 turns to:

[[1, 4, 7], [2, 5, 8], [3, 6, 9], [3, 1, 8], [3, 1, 8], [3, 1, 8]] (six objects with three digits)

last example is not straight result, more as deviation.
Ideally Flip has to work with preserving data levels and with respect to other levels structure.
But for now working level is 2

Inputs
------

* **data** - data to flip

Properties
----------

* **level** - level to deal with

Outputs
-------

* **data** - flipped data

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189832406-cbcd682e-268a-4cae-989c-5d9c06659089.png
  :target: https://user-images.githubusercontent.com/14288520/189832406-cbcd682e-268a-4cae-989c-5d9c06659089.png
  :alt: flip

* Script-> :doc:`Formula </nodes/script/formula_mk5>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`