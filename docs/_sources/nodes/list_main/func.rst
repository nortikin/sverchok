List Math
=========

.. image:: https://user-images.githubusercontent.com/14288520/187527983-9ecef862-b83b-460e-bc7a-eda13ca91252.png
  :target: https://user-images.githubusercontent.com/14288520/187527983-9ecef862-b83b-460e-bc7a-eda13ca91252.png

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

**Wrap:** Adds one level of wrapping (output becomes [output])

Outputs
-------

The output is always going to be a number, integer or float, depending on the input list.

* You can try to use this node with vectors, but it isn't going to work properly. For operations with vectors you should use **Vector Math** node.

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/187716616-57161d36-4b66-4680-b5bc-e94304944c46.png
  :alt: ListMathDemo1.PNG
  :target: https://user-images.githubusercontent.com/14288520/187716616-57161d36-4b66-4680-b5bc-e94304944c46.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Text-> :doc:`Data Shape </nodes/text/shape>`

In this example the node shows all the possible outputs.
