Number Range
============

Functionality
-------------

Generates sequences of numbers, the node offers different number types and different methods to create the sequence.


Inputs and Parameters
---------------------

+--------------+------------+------------------------------------------------------------------------------------------------+
| Parameter    | Type       | Description                                                                                    |
+==============+============+================================================================================================+
|*Number Type* | Enum       | Float: Decimal numbers. (Double precision float: sign bit, 11 bits exponent, 52 bits mantissa) |
|              |            | Int: Integer numbers (Integer from -9223372036854775808 to 9223372036854775807)                |
+--------------+------------+------------------------------------------------------------------------------------------------+
|*Range Type*  | Enum       | Range: Set start, step and stop.                                                               |
|              |            | Count: Set start, stop and count number (divisions).                                           |
|              |            | Step: Set start, step and count number.                                                        |
+--------------+------------+------------------------------------------------------------------------------------------------+
| *Start*      | Float/ Int | value to start at                                                                              |
+--------------+------------+------------------------------------------------------------------------------------------------+
| *Step*       | Float/ Int | value of the skip distance to the next value. The Step value is considered the absolute        |
|              |            | difference between successive numbers.                                                         |
+--------------+------------+------------------------------------------------------------------------------------------------+
| *Stop*       | Float/ Int | Last value or limit of the range. If this value is lower than the start value then the         |
|              |            | sequence will be of descending values.                                                         |
+--------------+------------+------------------------------------------------------------------------------------------------+
| *Count*      | Float/ Int | Number of values to produce.                                                                   |
|              |            | **Never negative** - negative produces an empty list                                           |
+--------------+------------+------------------------------------------------------------------------------------------------+


Outputs
-------

Integers only, in list form.

Examples
--------

**Non-vectorized**

Int Range

::

    intRange(0,1,10)
    >>> [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    intRange(0,2,10)
    >>> [0, 2, 4, 6, 8]

    intRange(-4,1,6)
    >>> [-4, -3, -2, -1, 0, 1, 2, 3, 4, 5]

    intRange(2,1,-4)
    >>> [2, 1, 0, -1, -2, -3]

Count Range

::

    countRange(0,1,5)
    >>> [0, 1, 2, 3, 4]

    countRange(0,2,5)
    >>> [0, 2, 4, 6, 8]

    countRange(-4,1,6)
    >>> [-4, -3, -2, -1, 0, 1]

    countRange(2,1,4)
    >>> [2, 3, 4, 5]

**Vectorized**

`Progress Thread <https://github.com/nortikin/sverchok/issues/156>`_ in the issue tracker shows several examples.

.. image:: https://cloud.githubusercontent.com/assets/619340/4163189/29d5fb56-34e4-11e4-9b00-baa15a8ddf00.png
