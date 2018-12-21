Quaternion In
-------------

Quaternion In node constructs quaternions based on various input components provided for a selected mode.


Modes
=====

The available **Modes** are: WXYZ, EULER, AXIS-ANGLE & MATRIX.

+============+================================================================+
| Mode       | Description                                                    |
+------------+----------------------------------------------------------------+
| WXYZ       | Converts W, X, Y, Z components into a quaternion. [1]          |
+------------+----------------------------------------------------------------+
| EULER      | Converts X, Y, Z Euler angles and an order of rotation         |
|            | into a quaternion. [2,3]                                       |
+------------+----------------------------------------------------------------+
| AXIS-ANGLE | Converts an Axis & an Angle of rotation into a quaternion. [2] |
+------------+----------------------------------------------------------------+
| MATRIX     | Converts an orthogonal 4x4 rotation matrix into a quaternion.  |
+============+================================================================+

Notes:
[1] : For WXYZ the node provides a "Normalize" option to generate a normalized quaternion.
[2] : For EULER and AXIS-ANGLE modes (which take angle input) the node provides an
angle unit conversion to let the angle values be converted to Radians, Degrees or Unities (0-1 range).
[3] : For EULER mode the node provides the option to select the Euler rotation order:
"XYZ", "XZY", "YXZ", "YZX", "ZXY" or "ZYX".


Inputs
======

The node takes a list of various components, based on the selected mode, and it
constructs the corresponding quaternions. The node is vectorized so the inputs take
a value or a list of values. When multiple lists are connected the node will
extend the length of the connected input lists to match the longest one before computing the list of output quaternions.

Based on the selected **Mode** the node makes available the corresponding input sockets:

+============+================================+
| Mode       | Input Sockets (types)          |
+------------+--------------------------------+
| WXYZ       | W, X, Y, Z  (floats)           |
+------------+--------------------------------+
| EULER      | X, Y, Z angles (floats)        |
+------------+--------------------------------+
| AXIS-ANGLE | Axis (Vector) & Angle (float)  |
+------------+--------------------------------+
| MATRIX     | Matrix (4x4 matrix)            |
+============+================================+


Outputs
=======

**Quaternions**

The node outputs a list of one ore more quaternions based on the given input.

The node only generates the quaternions when the output socket is connected.

