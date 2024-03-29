Quaternion Out
--------------

.. image:: https://user-images.githubusercontent.com/14288520/189335341-65240d77-18aa-4af4-b172-2d2751693f81.png
  :target: https://user-images.githubusercontent.com/14288520/189335341-65240d77-18aa-4af4-b172-2d2751693f81.png

.. image:: https://user-images.githubusercontent.com/14288520/189335364-2e83b6cc-571a-4558-a48c-511a124a0be1.png
  :target: https://user-images.githubusercontent.com/14288520/189335364-2e83b6cc-571a-4558-a48c-511a124a0be1.png

Quaternion Out node converts a quaternion into various formats for a selected mode.

Modes
=====

The available **Modes** are: WXYZ, EULER, AXIS-ANGLE & MATRIX.

+---------------+----------------------------------------------------------------+
| Mode          | Description                                                    |
+===============+================================================================+
| WXYZ          | Converts a quaternion into its W, X, Y, Z components. **[1]**  |
+---------------+----------------------------------------------------------------+
| SCALAR-VECTOR | Converts a quaternion into its Scalar & Vector components.     |
|               | **[1]**                                                        |
+---------------+----------------------------------------------------------------+
| EULER         | Converts a quaternion into X, Y, Z angles corresponding        |
|               | to the Euler rotation given an Euler rotation order. **[2,3]** |
+---------------+----------------------------------------------------------------+
| AXIS-ANGLE    | Converts a quaternion into the Axis & Angle of rotation.       |
|               | **[2]**                                                        |
+---------------+----------------------------------------------------------------+
| MATRIX        | Converts a quaternion into an orthogonal 4x4 rotation matrix.  |
+---------------+----------------------------------------------------------------+

Notes:

* **[1]** : For WXYZ and SCALAR-VECTOR modes the node provides a "Normalize" option to normalize the input quaternion before outputting its components. All the other modes automatically normalize the quaternion.
* **[2]** : For EULER and AXIS-ANGLE modes, which output angles, the node provides an angle unit conversion to let the angle output values be converted to Radians (1.0-2pi), Degrees (1.0-360.0) or Unities (0.0-1.0 range).
* **[3]** : For EULER mode the node provides the option to select the Euler rotation order: "XYZ", "XZY", "YXZ", "YZX", "ZXY" or "ZYX".

Inputs
======

* **Quaternions** The node takes a list of (one or more) quaternions and based on the selected mode it converts the quaternions into the corresponding components.


Extra Parameters
================

A set of extra parameters are available on the property panel.
These parameters do not receive external input.

+------------------+-----------+---------+--------------------------------------+
| Extra Param      | Type      | Default | Description                          |
+==================+===========+=========+======================================+
| **Angle Units**  | Enum      | DEGREES | Interprets the angle values based on |
|                  |           |         | the selected angle units:            |
|                  |           |         |                                      |
|                  | * RADIANS |         | * Radians = 0.0 - 2pi                |
|                  | * DEGREES |         | * Degrees = 0.0 - 360.0              |
|                  | * UNITIES |         | * Unities = 0.0 - 1.0                |
+------------------+-----------+---------+--------------------------------------+


Outputs
=======

Based on the selected **Mode** the node makes available the corresponding output sockets:

+---------------+------------------------------------+
| Mode          | Output Sockets (types)             |
+===============+====================================+
| WXYZ          | W, X, Y, Z  (floats)               |
+---------------+------------------------------------+
| SCALAR-VECTOR | Scalar (float) & Vector (vector)   |
+---------------+------------------------------------+
| EULER         | X, Y, Z angles (floats) **[1]**    |
+---------------+------------------------------------+
| AXIS-ANGLE    | Axis (vector) & Angle (float)      |
|               | **[1]**                            |
+---------------+------------------------------------+
| MATRIX        | Matrix (4x4 matrix)                |
+---------------+------------------------------------+

Notes:

* **[1]** : The angles are by default in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.

The modes WXYZ and SCALAR-VECTOR are the same except the WXYZ mode outputs the components as 4 floats (W, X, Y and Z), while the SCALAR-VECTOR mode outputs the components as a scalar (W) and a vector (XYZ).

The node only generates the conversion when the output sockets are connected.