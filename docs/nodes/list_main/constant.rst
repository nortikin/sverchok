Constant List
=============

Functionality
-------------

This node generates a list by repeating a single constant (integer or
floating-point) value. It is "vectorized", so by putting some lists to it's
inputs it is possible to make lists consisting of different numbers repeated
different count of times. Such lists can be useful as generated masks for some geometry.

Inputs
------

This node has the following inputs:

* **IntValue** or **FloatValue** - either integer or floating-point value to be
  repeated. The node expects data of nesting level of 0, 1, or 2 in this inputs
  (number, list of numbers, or list of lists of numbers). The default value is
  0 (or 0.0 in case floating-point mode is used).
* **Length**. Length of list to be generated. The node expects data of nesting
  level 0, 1 or 2 in this input (i.e. a number, a list of numbers, or a list of
  lists of numbers). The default value is 3.

Parameters
----------

This node has the following parameters:

* **Type**. This defines the type of the constant value. Available modes are
  **Integer** and **Float**. Depending on this parameter, either **IntValue**
  or **FloatValue** input / parameter will be used. The default type is
  **Integer**.
* **Output level**. This defines the nesting level of output list. Possible
  values are from 1 (list of numbers) to 3 (list of lists of lists of numbers).
  The default value is 2.

Outputs
-------

This node has the following output:

* **Data**. Generated list. Nesting level of data in this output will be equal
  to the value of the **Output level** parameter.

Examples of usage
-----------------

A simple example:

.. image:: https://user-images.githubusercontent.com/284644/74590945-286de180-5035-11ea-8c88-949ce11beb1c.png

If **Output level** would be 1 in this setup, the result would be `[0.06,
0.06, 0.06]`. If **Output level** would be 3, the result would be `[[[0.06,
0.06, 0.06]]]`.

More complex example:

.. image:: https://user-images.githubusercontent.com/284644/74590944-27d54b00-5035-11ea-8d62-6aeeac135e6e.png

If **Output level** would be 1 in this setup, the result would be `[1, 1, 1, 2,
2, 2, 2, 2]`. If **Output level** would be 3, the result would be `[[[1, 1, 1],
[2, 2, 2, 2, 2]]]`.

Another complex example:

.. image:: https://user-images.githubusercontent.com/284644/74590942-273cb480-5035-11ea-9ed7-84da04e3d590.png

If **Output level** would be 1 in this setup, the result would be `[1, 1, 1, 2,
2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 4]`. If **Output level** would be 2, the
result would be `[[1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3], [4, 4, 4, 4, 4]]`.

