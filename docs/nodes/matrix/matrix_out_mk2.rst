Matrix Out
==========

.. image:: https://user-images.githubusercontent.com/14288520/189547490-4e7e7879-dfbb-4622-850b-6a8845f6956e.png
  :target: https://user-images.githubusercontent.com/14288520/189547490-4e7e7879-dfbb-4622-850b-6a8845f6956e.png

Functionality
-------------

Matrix Out node converts a 4x4 matrix into its location, rotation and scale components. The rotation component can be represented in various formats: quaternion, axis-angle or Euler angles.


Modes
-----

The available **Modes** are: EULER, AXIS-ANGLE & QUATERNION. These specify
how the output *rotation component* of the matrix is going to be represented.

Regardless of the selected mode the node always outputs the **Location** and the **Scale** components of the 4x4 matrix.

+------------+---------------------------------------------------------------------------------------+
| Mode       | Description                                                                           |
+============+=======================================================================================+
| EULER      | Converts the rotation component of the matrix into X, Y, Z angles                     |
|            |                                                                                       |
|            | corresponding to the Euler rotation given an Euler rotation order. **[1,2]**          |
+------------+---------------------------------------------------------------------------------------+
| AXIS-ANGLE | Converts the rotation component of the matrix into the Axis & Angle                   |
|            | of rotation. **[1]**                                                                  |
+------------+---------------------------------------------------------------------------------------+
| QUATERNION | Converts the rotation component of the matrix into a quaternion.                      |
+------------+---------------------------------------------------------------------------------------+

Notes:

* **[1]** : For EULER and AXIS-ANGLE modes, which output angles, the node provides an angle unit conversion to let the angle output values be converted to Radians, Degrees or Unities (0-1 range).
* **[2]** : For EULER mode the node provides the option to select the Euler rotation order: "XYZ", "XZY", "YXZ", "YZX", "ZXY" or "ZYX".


Inputs
------

* **Matrix** The node takes a list of (one or more) matrices and based on the selected mode it converts the matrices into the corresponding components.


Extra Parameters
----------------
A set of extra parameters are available on the property panel.
These parameters do not receive external input.

+-----------------+----------+---------+--------------------------------------+
| Extra Param     | Type     | Default | Description                          |
+=================+==========+=========+======================================+
| **Angle Units** | Enum     | DEGREES | Interprets the angle values based on |
|                 |          |         |                                      |
|                 |          |         | the selected angle units:            |
|                 | * RADIANS|         |                                      |
|                 | * DEGREES|         | * Radians = 0 - 2pi                  |
|                 | * UNITIES|         | * Degrees = 0 - 360                  |
|                 |          |         | * Unities = 0 - 1                    |
+-----------------+----------+---------+--------------------------------------+


Outputs
-------

Based on the selected **Mode** the node makes available the corresponding output sockets:

+------------+-----------------------------------------+
| Mode       | Output Sockets (types)                  |
+============+=========================================+
| <any>      | Location and Scale components (vectors) |
+------------+-----------------------------------------+
| EULER      | X, Y, Z angles (floats) [1]             |
+------------+-----------------------------------------+
| AXIS-ANGLE | Axis (vector) & Angle (float) [1]       |
+------------+-----------------------------------------+
| QUATERNION | Quaternion                              |
+------------+-----------------------------------------+

Notes:
[1] : The angles are by default in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.

The node only generates the conversion when the output sockets are connected.

