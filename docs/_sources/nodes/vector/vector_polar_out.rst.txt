Vector Polar Output
===================

.. image:: https://user-images.githubusercontent.com/14288520/189432772-6652094e-5124-42b4-8f7d-858fb80ff6f7.png
  :target: https://user-images.githubusercontent.com/14288520/189432772-6652094e-5124-42b4-8f7d-858fb80ff6f7.png

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
    :target: https://cloud.githubusercontent.com/assets/284644/5841825/d0c494aa-a1c1-11e4-9c36-4c94076ba8d7.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/189432796-528d0c20-ab44-4b0d-af66-9a880dc15275.png
  :target: https://user-images.githubusercontent.com/14288520/189432796-528d0c20-ab44-4b0d-af66-9a880dc15275.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Vector-> :doc:`Vector Out </nodes/vector/vector_out>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`