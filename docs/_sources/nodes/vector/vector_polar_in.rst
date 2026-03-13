Vector Polar Input
==================

.. image:: https://user-images.githubusercontent.com/14288520/189424521-bb3833ee-d310-455e-a8e0-0992e82c43e5.png
  :target: https://user-images.githubusercontent.com/14288520/189424521-bb3833ee-d310-455e-a8e0-0992e82c43e5.png

Functionality
-------------

This node generates a vector from it's cylindrical or spherical coordinates. Angles can be measured in radians or in degrees.

Inputs & Parameters
-------------------

All parameters except for ``Coordinates`` and ``Angles mode`` can be specified using corresponding inputs.

The node will accept regular lists or lists of flat NumPy arrays

+-----------------+---------------+-------------+----------------------------------------------------+
| Parameter       | Type          | Default     | Description                                        |
+=================+===============+=============+====================================================+
| **Coordinates** | Cylindrical   | Cylindrical | Which coordinates system to use.                   |
|                 | or Spherical  |             |                                                    |
+-----------------+---------------+-------------+----------------------------------------------------+
| **Angles mode** | Radians or    | Radians     | Interpret input angles as specified in             |
|                 | Degrees       |             |                                                    |
|                 |               |             | radians or degrees.                                |
+-----------------+---------------+-------------+----------------------------------------------------+
| **rho**         | Float         | 0.0         | Rho coordinate.                                    |
+-----------------+---------------+-------------+----------------------------------------------------+
| **phi**         | Float         | 0.0         | Phi coordinate.                                    |
+-----------------+---------------+-------------+----------------------------------------------------+
| **z**           | Float         | 0.0         | Z coordinate. This input is used only              |
|                 |               |             |                                                    |
|                 |               |             | for cylindrical coordinates.                       |
+-----------------+---------------+-------------+----------------------------------------------------+
| **theta**       | Float         | 0.0         | Theta coordinate. This input is used only          |
|                 |               |             |                                                    |
|                 |               |             | for spherical coordinates.                         |
+-----------------+---------------+-------------+----------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **Output NumPy**: Get NumPy arrays in stead of regular lists (makes node faster)

Outputs
-------

This node has one output: **Vectors**. Inputs and outputs are vectorized, so if
you pass series of values to one of inputs, you will get series of vectors.

Examples of usage
-----------------

An archimedean spiral:

.. image:: https://user-images.githubusercontent.com/14288520/189424545-004559ba-eefc-49be-a549-b6087043d6be.png
  :target: https://user-images.githubusercontent.com/14288520/189424545-004559ba-eefc-49be-a549-b6087043d6be.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Logariphmic spiral:

.. image:: https://user-images.githubusercontent.com/14288520/189424571-3cff56bb-4eda-47e9-9841-98245d4d13c3.png
  :target: https://user-images.githubusercontent.com/14288520/189424571-3cff56bb-4eda-47e9-9841-98245d4d13c3.png

* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Exponential Sequence </nodes/number/exponential>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Helix:

.. image:: https://user-images.githubusercontent.com/14288520/189424592-e4778b09-4b79-4426-a03e-0d1058020dc0.png
  :target: https://user-images.githubusercontent.com/14288520/189424592-e4778b09-4b79-4426-a03e-0d1058020dc0.png

* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

With spherical coordinates, you can easily generate complex forms:

.. image:: https://user-images.githubusercontent.com/14288520/189424605-b48cad7c-1ef7-41fe-aa1b-62efbaf8938c.png
  :target: https://user-images.githubusercontent.com/14288520/189424605-b48cad7c-1ef7-41fe-aa1b-62efbaf8938c.png

* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* MUL X, SINE X, ADD X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/189424657-1c9cb7f7-18ef-49cd-a44e-0ef277832ff7.gif
  :target: https://user-images.githubusercontent.com/14288520/189424657-1c9cb7f7-18ef-49cd-a44e-0ef277832ff7.gif