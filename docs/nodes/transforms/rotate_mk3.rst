Rotate
======

Functionality
-------------

This node is used to make general rotation over geometry. It works directly over vertices, not with matrixes. Just like Blender, it offers 3 different types of rotation:

=============  =================================================
Axis Rotation   Based on axis (X, Y, Z) and a rotation angle (W)
=============  =================================================

======================= ===========================================================================
Type of Rotation         Description
======================= ===========================================================================
Axis Rotation            Based on axis (X, Y, Z) and a rotation angle (W)
Euler Rotation           Using Euler Gimbal: 3 axis with a hierarchical relationship between them
Quaternion rotation      Based on four values (X, Y, Z, W). W value will avoid X, Y, Z rotation
======================= ===========================================================================

If you want to learn deeply about all this types of rotation, visit this link: http://wiki.blender.org/index.php/User:Pepribal/Ref/Appendices/Rotation


Axis Rotation
-------------

This mode let us define an axis (X, y, Z), a center point and a rotation angle (W), in degrees, around the defined axis.

Inputs
^^^^^^

All inputs are vectorized and they will accept single or multiple values.
There is four inputs:

- **Vertices**
- **Center**
- **Axis**
- **Angle**

Parameters
^^^^^^^^^^

All parameters except **Vertices** has a default value. **Angle** can be given by the node or an external input.


+----------------+---------------+-----------------+----------------------------------------------------+
| Param          | Type          | Default         | Description                                        |
+================+===============+=================+====================================================+
| **Vertices**   | Vertices      | none            | vertices to rotate                                 |
+----------------+---------------+-----------------+----------------------------------------------------+
| **Center**     | Vertices      | (0.0, 0.0, 0.0) | point to place the rotation axis                   |
+----------------+---------------+-----------------+----------------------------------------------------+
| **Axis**       | Vector        | (0.0, 0.0, 1.0) | axis around which rotation will be done            |
+----------------+---------------+-----------------+----------------------------------------------------+
| **Angle**      | Float         | 0.00            | angle in degrees to make rotation                  |
+----------------+---------------+-----------------+----------------------------------------------------+

Outputs
^^^^^^^

**Vertices**.

Example of usage
^^^^^^^^^^^^^^^^

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/rotate/rotate_vectors_blender_sverchok_example_1.png
  :alt: AxisRotationDemo1.PNG

In this example we use axis rotation to rotate a torus around the X axis 45 degrees .


Euler Rotation
--------------

This mode is used to perform Euler rotations, refered to an Eular gimbal. A gimbal is a set of 3 axis that have a hierarchical relationship between them.

Inputs
^^^^^^

All inputs are vectorized and they will accept single or multiple values.
There is four inputs:

- **Vertices**
- **X**
- **Y**
- **Z**

Parameters
^^^^^^^^^^

All parameters except **Vertices** has a default value. **X**, **Y** and **Z** can be given by the node or an external input.


+----------------+---------------+-----------------+-----------------------------------------------------+
| Param          | Type          | Default         | Description                                         |
+================+===============+=================+=====================================================+
| **Vertices**   | Vertices      | none            | vertices to rotate                                  |
+----------------+---------------+-----------------+-----------------------------------------------------+
| **X**          | Float         | 0.00            | value to X axis rotation                            |
+----------------+---------------+-----------------+-----------------------------------------------------+
| **Y**          | Float         | 0.00            | value to Y axis rotation                            |
+----------------+---------------+-----------------+-----------------------------------------------------+
| **Z**          | Float         | 0.00            | value to Z axis rotation                            |
+----------------+---------------+-----------------+-----------------------------------------------------+
| **Order**      | Enum          | XYZ             | order of the hierarchical relationship between axis |
+----------------+---------------+-----------------+-----------------------------------------------------+

Outputs
^^^^^^^

**Vertices**

Example of usage
^^^^^^^^^^^^^^^^

.. image::https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/rotate/rotate_vectors_blender_sverchok_example_2.png
  :alt: EulerRotationDemo1.PNG
.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/rotate/rotate_vectors_blender_sverchok_example_3.png
  :alt: EulerRotationDemo2.PNG

In the first example we use Euler rotation rotate the vertices of a line to create a 3d spiral
The second is more complex, with multiple inputs in Y and Z to create a complex geometry from just one line.


Quaternion Rotation
-------------------

In this mode rotation is defined by 4 values (X, Y, Z, W), but it works in a different way than Axis Rotation. The important thing is the relation between all four values. For example, X value rotate the object around X axis up to 180 degrees. The effect of W is to avoid that rotation and leave the element with zero rotation.
The final rotation is a combination of all four values.

Inputs
^^^^^^

All inputs are vectorized and they will accept single or multiple values.
There is five inputs:

- **Vertices**
- **X**
- **Y**
- **Z**
- **W**

Parameters
^^^^^^^^^^

All parameters except **Vertices** has a default value. **X**, **Y**, **Z** and **W** can be given by the node or an external input.


+----------------+---------------+-----------------+-----------------------------------------------------+
| Param          | Type          | Default         | Description                                         |
+================+===============+=================+=====================================================+
| **Vertices**   | Vertices      | none            | vertices to rotate                                  |
+----------------+---------------+-----------------+-----------------------------------------------------+
| **X**          | Float         | 0.00            | value to X axis rotation                            |
+----------------+---------------+-----------------+-----------------------------------------------------+
| **Y**          | Float         | 0.00            | value to Y axis rotation                            |
+----------------+---------------+-----------------+-----------------------------------------------------+
| **Z**          | Float         | 0.00            | value to Z axis rotation                            |
+----------------+---------------+-----------------+-----------------------------------------------------+
| **W**          | Float         | 1.00            | value to Z axis rotation                            |
+----------------+---------------+-----------------+-----------------------------------------------------+

Outputs
^^^^^^^

**Vertices**.

Example of usage
^^^^^^^^^^^^^^^^

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/rotate/rotate_vectors_blender_sverchok_example_4.png
  :alt: QuatRotationDemo1.PNG

As we can see in this example, we try to rotate the plan 45 degrees and then set W with multiple values, each higher than before, but the plane is never get to rotate 180 degrees.

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Output NumPy arrays in stead of regular lists (makes the node faster when you input one rotation value for each set of vertices)

**List Match**: Define how list with different lengths should be matched
