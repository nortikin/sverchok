Matrix In
=========

.. image:: https://user-images.githubusercontent.com/14288520/189546077-7329965e-3c8e-40e8-8917-e54d80b0dc32.png
  :target: https://user-images.githubusercontent.com/14288520/189546077-7329965e-3c8e-40e8-8917-e54d80b0dc32.png

Functionality
-------------

This node creates homogeneous 4x4 matrices out of translation, scale and rotation components.
The rotation component can be generated based on various input formats, selectable by one of the supported modes: Quaternion, Axis + Angle or Euler Angles.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Location**
- **Scale**
- **Quaternion** [1]
- **Axis**       [2]
- **Angle**      [2,4]
- **Angle X**    [3,4]
- **Angle Y**    [3,4]
- **Angle Z**    [3,4]

Notes:

* [1] : Input is available when "Quaternion" mode is selected
* [2] : Inputs are available when "Axis Angle" mode is selected
* [3] : Inputs are available when "Euler Angles" mode is selected
* [4] : The angles are in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.

The node accepts as inputs either lists of items (vectors, numbers, quaternions), such as: [[v, v, v]], [[a, a, a]], [[q, q, q]]. in which case it would generate a set of matrices: [[m, m, m]], but it also accepts lists of lists of items, such as [[v, v], [v, v, v]], in which case it will produce a set of matrices: [[m, m], [m, m, m]].


Parameters
----------

The **Mode** parameter allows to switch between "Quaternion", "Axis Angle" and "Euler Angles". The input sockets for the rotation are updated to reflect the selected mode.

All parameters except **Mode**, **Angle Units** and **Flat Output** can be given by the node or an external input.

+-----------------+----------------+--------------+-------------------------------------------------------+
| Param           | Type           | Default      | Description                                           |
+=================+================+==============+=======================================================+
| **Mode**        | Enum           | Axis Angle   | Specifies how the rotation component is               |
|                 |                |              |                                                       |
|                 | * Quaternion   |              | provided to the node as an input.                     |
|                 | * Axis Angle   |              |                                                       |
|                 | * Euler Angles |              |                                                       |
+-----------------+----------------+--------------+-------------------------------------------------------+
| **Location**    |  Vector        | (0, 0, 0)    | The translation component of the matrix.              |
+-----------------+----------------+--------------+-------------------------------------------------------+
| **Scale**       |  Vector        | (1, 1, 1)    | The scale component of the matrix.                    |
+-----------------+----------------+--------------+-------------------------------------------------------+
| **Angle Units** | Enum           | Deg          | Specifies the units for the angle values. **[1]**     |
|                 |                |              |                                                       |
|                 | * Deg          |              |                                                       |
|                 | * Rad          |              |                                                       |
|                 | * Uni          |              |                                                       |
+-----------------+----------------+--------------+-------------------------------------------------------+
| **Quaternion**  |  Quaternion    | (1, 0, 0, 0) | The rotation component given as a                     |
|                 |                |              |                                                       |
|                 |                |              | quaternion. **[2]**                                   |
+-----------------+----------------+--------------+-------------------------------------------------------+
| **Axis**        |  Vector        | (0, 0, 1)    | The axis of rotation.                                 |
+-----------------+----------------+--------------+-------------------------------------------------------+
| **Angle**       |  Float         | 0.0          | The rotation angle about the given rotation           |
|                 |                |              |                                                       |
|                 |                |              | axis. **[4]**                                         |
+-----------------+----------------+--------------+-------------------------------------------------------+
| **Euler Order** | Enum           | XYZ          | Specifies the order of the euler angle rotations.     |
|                 |                |              |                                                       |
|                 | * XYZ          |              |                                                       |
|                 | * XZY          |              |                                                       |
|                 | * YXZ          |              |                                                       |
|                 | * YZX          |              |                                                       |
|                 | * ZXY          |              |                                                       |
|                 | * ZYX          |              |                                                       |
+-----------------+----------------+--------------+-------------------------------------------------------+
| **Angle X**     | Float          | 0.0          | The angle of rotation about the X axis. **[3][4]**    |
+-----------------+----------------+--------------+-------------------------------------------------------+
| **Angle Y**     | Float          | 0.0          | The angle of rotation about the Y axis. **[3][4]**    |
+-----------------+----------------+--------------+-------------------------------------------------------+
| **Angle Z**     | Float          | 0.0          | The angle of rotation about the Z axis. **[3][4]**    |
+-----------------+----------------+--------------+-------------------------------------------------------+

NOTES:

* **[1]** : The "Angle Units" parameter is available for "Axis Angle" and "Euler Angle" modes. When switching the units the angle values are converted to the selected unit. Connected angle inputs are also considered to have the selected angle units.
* **[2]** : The quaternion is expected to be normalized (corresponding to a rotation matrix). If it is not normalized, the result is undefined.
* **[3]** : The XYZ angle parameters are available for "Euler Angle" mode. The order of applying these rotations is given by the "Euler Order" parameter.
* **[4]** : Angles are given by default in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.

Extra Parameters
----------------
A set of extra parameters are available on the property panel.
These parameters do not receive external input.

+------------------+----------+---------+----------------------------------------+
| Extra Param      | Type     | Default | Description                            |
+==================+==========+=========+========================================+
| **Flat Output**  | Bool     | True    | Flattens the matrix output [#1]_ [#2]_ |
+------------------+----------+---------+----------------------------------------+
| **Angle Units**  | Enum     | DEGREES | Interprets the angle values based on   |
|                  |          |         |                                        |
|                  |          |         | the selected angle units:              |
|                  |          |         |                                        |
|                  | * RADIANS|         | * Radians = 0.0 - 2pi                  |
|                  | * DEGREES|         | * Degrees = 0.0 - 360.0                |
|                  | * UNITIES|         | * Unities = 0.0 - 1.0                  |
+------------------+----------+---------+----------------------------------------+

NOTES:

.. [#1] When the flag is enabled the node will join the first level list of
   matrices in the output and generate a list of matrices: [M, M, ... , M].
   When the flag is disabled the node will keep the structure matching the
   input structure and generate the output as a list of list of matrices:
   [[M, M, ... , M], ..., [M, M, ... , M]].

.. [#2] The "Flat Output" option can be toggle via the right-click menu as well.


Outputs
-------

**Matrices**
The output is a list of one or multiple 4x4 homogeneous matrices, based on the given input.

All outputs will be generated only when output socket is connected.


Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/189546149-4a603282-7346-48d5-9491-5a043eac51dc.png
  :target: https://user-images.githubusercontent.com/14288520/189546149-4a603282-7346-48d5-9491-5a043eac51dc.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/189546359-8f061a85-72aa-44bf-8dde-70c386cace6c.gif
  :target: https://user-images.githubusercontent.com/14288520/189546359-8f061a85-72aa-44bf-8dde-70c386cace6c.gif

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`