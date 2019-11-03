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
| **Mode**       | Enum     | Sine, Square, Saw, Triangle, Wave, Absolute, Negate                   |
+----------------+----------+-----------------------------------------------------------------------+
| **Value**      | Float    | Point(s) in time to evaluate                                          |
+----------------+----------+-----------------------------------------------------------------------+
| **Amplitude**  | Float    | Amplitude of the wave                                                 |
+----------------+----------+-----------------------------------------------------------------------+
| **Period**     | Float    | Time (Value) to make a full cycle  of the wave                        |
+----------------+----------+-----------------------------------------------------------------------+
| **Phase**      | Float    | Starting Phase of the wave                                            |
+----------------+----------+-----------------------------------------------------------------------+
| **Offset**     | Float    | Value added the wave                                                  |
+----------------+----------+-----------------------------------------------------------------------+
| **Wave**       | Vertices | On Wave mode you can input a path of points (more than 1) to create   |
|                |          | a custom wave. The node will evaluate the Y value                     |
+----------------+----------+-----------------------------------------------------------------------+

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
