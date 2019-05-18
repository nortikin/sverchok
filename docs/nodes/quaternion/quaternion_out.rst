Quaternion Out
--------------

Quaternion Out node converts a quaternion into various formats for a selected mode.

Modes
=====

The available **Modes** are: WXYZ, EULER, AXIS-ANGLE & MATRIX.

+===============+================================================================+
| Mode          | Description                                                    |
+===============+================================================================+
| WXYZ          | Converts a quaternion into its W, X, Y, Z components. [1]      |
+---------------+----------------------------------------------------------------+
| SCALAR-VECTOR | Converts a quaternion into its Scalar & Vector components. [1] |
+---------------+----------------------------------------------------------------+
| EULER         | Converts a quaternion into X, Y, Z angles corresponding        |
|               | to the Euler rotation given an Euler rotation order. [2,3]     |
+---------------+----------------------------------------------------------------+
| AXIS-ANGLE    | Converts a quaternion into the Axis & Angle of rotation. [2]   |
+---------------+----------------------------------------------------------------+
| MATRIX        | Converts a quaternion into an orthogonal 4x4 rotation matrix...|
+===============+================================================================+

Notes:
[1] : For WXYZ and SCALAR-VECTOR modes the node provides a "Normalize" option to normalize the input quaternion before outputting its components. All the other modes automatically normalize the quaternion.
[2] : For EULER and AXIS-ANGLE modes, which output angles, the node provides an
angle unit conversion to let the angle output values be converted to Radians,
Degrees or Unities (0-1 range).
[3] : For EULER mode the node provides the option to select the Euler rotation order:
"XYZ", "XZY", "YXZ", "YZX", "ZXY" or "ZYX".

Inputs
======

**Quaternions**
The node takes a list of (one or more) quaternions and based on the selected mode
it converts the quaternions into the corresponding components.


Outputs
=======

Based on the selected **Mode** the node makes available the corresponding output sockets:

+===============+==================================+
| Mode          | Output Sockets (types)           |
+===============+==================================+
| WXYZ          | W, X, Y, Z  (floats)             |
+---------------+----------------------------------+
| SCALAR-VECTOR | Scalar (float) & Vector (vector) |
+---------------+----------------------------------+
| EULER         | X, Y, Z angles (floats)          |
+---------------+----------------------------------+
| AXIS-ANGLE    | Axis (vector) & Angle (float)    |
+---------------+----------------------------------+
| MATRIX        | Matrix (4x4 matrix)              |
+===============+==================================+

The modes WXYZ and SCALAR-VECTOR are the same except the WXYZ mode outputs the components as 4 floats (W, X, Y and Z), while the SCALAR-VECTOR mode outputs the components as a scalar (W) and a vector (XYZ).

The node only generates the conversion when the output sockets are connected.

