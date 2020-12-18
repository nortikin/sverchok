List Math
=========

Functionality
-------------

This nodes offers some operations to make over list, meaning a group of numbers.

Inputs
------

It will operate only with list of single numbers, not tuples or vectors.

Parameters
----------

**Level:** Set the level at which to observe the List.
**Function:** Select the type of operation.

=================== ======================================
Tables              description
=================== ======================================
Sum                 sum of all the elements of the list
Average             average of element at selected level
Maximum             Maximum value of the list
Minimum             Minimum value of the list
Cumulative Sum      Cumulative sum of elements in the list
Logical OR          Return True if any value in the list is logical True
Logical AND         Return True if all values in the list are logical True
=================== ======================================

**Warp:** Adds one level of warping (output becomes [output])

Outputs
-------

The output is always going to be a number, integer or float, depending on the input list.

* You can try to use this node with vectors, but it isn't going to work properly. For operations with vectors you should use **Vector Math** node.

Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/5990821/4191546/dd4edc6e-378e-11e4-8015-8f66ec59b68e.png
  :alt: ListMathDemo1.PNG

In this example the node shows all the possible outputs.
