Vector Polar Output
===================

*destination after Beta: Vector*

Functionality
-------------

This node decomposes a vector to it's cylindrical or spherical coordinates.  Angles can be measured in radians or in degrees.

Parameters
----------

This node has the following parameters:

- **Coordinates**. Cylindrical or Spherical. Default mode is Cylindrical.
- **Angles mode**. Should this node output angles measured in radians or in degrees. By default Radians.

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes node faster)

Inputs
------

This node has one input: **Vectors**  Inputs and outputs are vectorized, so if
you pass series of vectors to input, you will get series of values on outputs.

The node will accept regular lists or lists of NumPy arrays if the arrays have two axis arrays with shape [n,3]

Outputs
-------

This node has the following outputs:

- **rho**. Rho coordinate.
- **phi**. Phi coordinate.
- **z**. Z coordinate. This output is used only for Cylindrical coordinates.
- **theta**. Theta coordinate. This output is used only for Spherical coordinates.

Examples of usage
-----------------

Cube push-up:

.. image:: https://cloud.githubusercontent.com/assets/284644/5841825/d0c494aa-a1c1-11e4-9c36-4c94076ba8d7.png
