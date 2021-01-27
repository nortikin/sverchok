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
|*Range Type*  | Enum       | Range: Define range by setting start, step and stop.                                           |
|              |            | Count: Define range by setting start, stop and count number (divisions).                       |
|              |            | Step: Define range by setting start, step and count number.                                    |
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

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster)

**List Match**: Define how list with different lengths should be matched

**Flat Output**: Keeps the output list depth

Outputs
-------

Range: Lists of sequences

Examples
--------

.. image:: https://user-images.githubusercontent.com/10011941/69128534-cdb40080-0aac-11ea-887d-721f4c785ebd.png

With the 'Flat Output' activated the output will be [[..],[..],...] and it can be plugged to another Number Range Node.

.. image:: https://user-images.githubusercontent.com/10011941/69128863-72ced900-0aad-11ea-8f3b-d65c47e970f8.png
