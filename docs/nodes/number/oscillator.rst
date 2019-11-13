Oscillator
==========

Functionality
-------------

This node creates a oscillation signal from a lineal range.


Inputs & Parameters
-------------------

All parameters except for **Mode** can be given by the node or an external input.
This node has the following parameters:

+----------------+----------+-----------------------------------------------------------------------+
| Parameter      | Type     | Description                                                           |
+================+==========+=======================================================================+
| **Mode**       | Enum     | Sine, Square, Saw, Triangle, Custom                                   |
+----------------+----------+-----------------------------------------------------------------------+
| **Value**      | Float    | Point(s) in time to evaluate                                          |
+----------------+----------+-----------------------------------------------------------------------+
| **Amplitude**  | Float    | Amplitude of the wave                                                 |
+----------------+----------+-----------------------------------------------------------------------+
| **Period**     | Float    | Time (Value) to make a full cycle of the wave. If you want to use the |
|                |          | frequency as input remember that 1/frequency = period                 |
+----------------+----------+-----------------------------------------------------------------------+
| **Phase**      | Float    | Starting Phase of the wave                                            |
+----------------+----------+-----------------------------------------------------------------------+
| **Offset**     | Float    | Value added the wave                                                  |
+----------------+----------+-----------------------------------------------------------------------+
| **Wave**       | Vertices | On Custom mode you can input a path of points (more than 1 vector)    |
|                |          | to create a custom wave. The node will evaluate the Y value           |
+----------------+----------+-----------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Wave Interpolation**: (On Custom mode) Define how the wave should be interpolated (Linear or Cubic)

**Wave Knots Mode**: (On Custom mode) Define how the wave knots should be interpolated (Manhattan, Euclidan, Points or Chebyshev)

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster)

**List Match**: Define how list with different lengths should be matched



Outputs
-------

This node has one output: **Out**.

Inputs and outputs are vectorized, so if series of values is passed to one of
inputs, then this node will produce several sequences.

Example of usage
----------------

Generating basic waves:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Oscillator/Oscillator_example_01.png

The "Wave" mode allows you to use a custom wave shape:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Oscillator/Oscillator_example_02.png

As with the musical synths you can create complex waves out of mixing the basics:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Oscillator/Oscillator_example_03.png

Surface modeled by a combination of Oscillator nodes.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/number/Oscillator/Oscillator_example_04.png
