Twist along Curve Field
=======================

Functionality
-------------

This node generates a vector field, which does a generic type of space
transformation. It is similar to what "Bend Along Curve Field" node does, but
rotation of space around the curve is controlled by user, not calculated by
some algorithm. So with this node you can generate a field that does a
combination of two transformations: 1) bending along some curve, and 2)
arbitrary twisting around that curve.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to bend and twist around. This input is mandatory.
* **Matrices**. This input is available and mandatory only when **Input**
  parameter is set to **Matrices**. This input should contain a list of
  matrices, that specify rotation of space around the curve. Locations of
  matrices define places on the curve where corresponding rotation should be
  done.
* **Quaternions**. This input is availale and mandatory only when **Input**
  parameter is set to **Quaternions**. This input should contain a lsit of
  quaternions, which define rotation of space around the curve. Locations of
  these rotations on the curve are defined by values in **T**/**Length** input.
* **Vectors**. This input is available and mandatory only when **Input**
  parameter is set to **Track Vectors**. This input should contain a list of
  vectors, which point in a direction to which tracking axis must be rotated.
  Locations of these rotations on the curve are defined by values in
  **T**/**Length** input.
* **T**/**Length**. This input is available and mandatory when **Input**
  parameter is set to **Quaternions** or **Track Vectors**. Values define
  places on the curve where corresponding rotations should be placed. If
  **Parametrization** parameter is set to **Curve Parameter**, then this input
  should contain curve T parameter values; otherwise, this input should contain
  arc length parameters (lengths from the beginning on the curve).
* **LengthResolution**. This input is available and mandatory only when
  **Parametrization** parameter is set to **Curve Length**. This defines the
  resolution used to calculate curve lengths. Higher values give more
  precision, but take more time to calculate. The default value is 50.

Parameters
----------

This node has the following parameters:

* **Input**. This defines how rotations around the curve will be specified. The
  available options are:

  * **Matrices**. The user provides a list of matrices. Locations of matrices
    in 3D space define locations on the curve where rotations should be placed.
    One of matrix axes (called orientation axis, see **Orientation** parameter
    below) is supposed to be directed along the curve, but not necessarily
    precisely. Rotation of the matrix along orientation curve define the
    rotaiton of the space around the curve. Scale and skew components of
    matrices are ignored.
  * **Quaternions**. The user provides a list of quaternions, which define
    rotations around the curve. Places of these rotations along the curve are
    defined by values in **T**/**Length** input.
  * **Track Vectors**. The user provides a list of vectors, which define
    directions where "tracking axis" should look to. Rotations are always done
    around curve tangent vectors. The places on the curve where these rotations
    should be placed are defined by values in **T**/**Length** input.

  The default option is **Matrices**.

* **Parametrization**. This defines what type of curve parametrization should
  be used. This also defines the part of 3D space which will be bent and
  rotated around the curve. The available options are:

  * **Curve Parameter**. Original coordinates in 3D space along axis specified
    in **Orientation** parameter will be used as curve T parameters. So, for
    example, if curve domain is from 0 to 1, then the part of space which will
    be bent is from 0 to 1 along orientation axis.
  * **Curve Length**. Original coordinates in 3D space along orientation axis
    will be used as curve arc length parameters (length of parts of curve from
    beginning of the curve). So, for example, if curve length is 11.5, then the
    part of space to be bent will be from 0 to 11.5 along orientation axis.

  The default option is **Curve Parameter**.

* **Orientation**. This parameter defines which axis of original 3D space
  should be bent along the curve. The default value is **Z**.
* **Track Axis**. This parameter is only available when **Input** parameter is
  set to **Track Vectors**. This defines which axis of original 3D space should
  be looking along user-provided tracking vectors after rotations. Tracking
  axis must not coincide with orientation axis. The default option is **X**.
* **Interpolation**. This defines the type of interpolation between
  user-provided rotations of the space. The available options are **Linear**
  and **Spline**. The default option is **Spline**.

Outputs
-------

This node has the following output:

* **Field**. The generated vector field.

Examples of Usage
-----------------

Example nodes setup:

.. image:: https://github.com/user-attachments/assets/f699e348-5f7d-4e1f-a3e2-9cd3d3ea8348
  :target: https://github.com/user-attachments/assets/f699e348-5f7d-4e1f-a3e2-9cd3d3ea8348

Result:

.. image:: https://github.com/user-attachments/assets/f0aced76-351a-4adb-99ab-3485506c1d9e
  :target: https://github.com/user-attachments/assets/f0aced76-351a-4adb-99ab-3485506c1d9e

Same, but with Linear interpolation mode:

.. image:: https://github.com/user-attachments/assets/bfa083e6-27f2-49b1-98d2-b5b1132dc651
  :target: https://github.com/user-attachments/assets/bfa083e6-27f2-49b1-98d2-b5b1132dc651

Example setup for Matrices input mode:

.. image:: https://github.com/user-attachments/assets/723ad29f-f6a9-49dc-ae7b-2df595815e19
  :target: https://github.com/user-attachments/assets/723ad29f-f6a9-49dc-ae7b-2df595815e19

Result:

.. image:: https://github.com/user-attachments/assets/008d709e-4b2f-4ad5-aa12-6ba1f353892f
  :target: https://github.com/user-attachments/assets/008d709e-4b2f-4ad5-aa12-6ba1f353892f

