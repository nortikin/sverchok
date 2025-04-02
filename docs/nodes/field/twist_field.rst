Twist / Whirld Field
====================

Functionality
-------------

This node generates a Vector Field, which does Twist or Whirl transformation of
some region of space, or combination of Twist and Whirl.

We call Twist a transformation which you get if you take some object, for
example a cube, then rotate one of it's sides (for example, bottom one) around
some axis, counterclockwise, and rotate the opposite side (top side, for
example) around the same axis clockwise.

Whirl transformation rotates all parts of object in the same direction, just
with different angle; the farther from whirl axis, the bigger is rotation
angle.

Both Twist and Whirl transformation require some axis for rotation. This axis
can be defined by a point, through which the axis goes, and the direction
vector.

Inputs
------

This node has the following inputs:

* **Center**. Rotation center; a point on twist / whirl axis. The default value
  is the origin, `(0, 0, 0)`.
* **Axis**. Direction vector of the twist / whirl axis. The default value is Z
  axis, `(0, 0, 1)`.
* **TwistAngle**. This is not exactly an angle, but a coefficient, which
  defines the force of twist transformation. More specifically, the plane lying
  at distance of 1 from rotation center in direction of rotation axis, will be
  rotated by angle specified in this input; plane passing through rotation
  center will not be rotated by twist transformation; all other planes
  perpendicular to rotation axis will be rotated on an angle proportional to
  distance from rotation center. The value is specified in radians. The default
  value is `pi/2`.
* **WhirlAngle**. Similar to previous input, this is not exactly an angle, but
  a coefficient, which defines the force of whirl transformation. More
  specifically, points at distance 1 from rotation axis will be rotated by
  angle specified in this input. All other points will be rotated by angle
  which is proportional to distance from rotation axis. The value is specified
  in radians. The default value is 0.
* **MinZ**, **MaxZ**. These inputs are available only when **Use Min Z** /
  **Use Max Z** parameters are enabled. Both twist and whirl transformation
  will stop at these distances from rotation center along rotation axis.
  Positive direction of rotation axis is the one defined by **Axis** input. The
  default values are 0.0 and 1.0, correspondingly.
* **MinR**, **MaxR**. These inputs are available only when **Use Min R** /
  **Use Max R** parameters are enabled. Both twist and whirl transformations
  will be ceased for points which have distance from rotation axis below
  **MinR** or above **MaxR** values. The default values are 0.0 and 1.0.

Parameters
----------

This node has the following parameters:

* **Use Min Z**, **Use Max Z**. If enabled, these parameters will allow to
  define a part of space along rotation axis which will be transformed; space
  outside this area will not be twisted any further.
* **Use Min R**, **Use Max R**. If enabled, these parameters allow to define a
  (cylindrical) part of space in terms of distance from rotation axis, which
  should be transformed; outside this area, the space will not be twisted any
  further.

Outputs
-------

This node has the following output:

* **Field**. The generated vector field.

Examples of usage
-----------------

Example of Twist transformation:

.. image:: https://github.com/user-attachments/assets/edb22301-0dd3-492b-abea-a20a2f2ee772
  :target: https://github.com/user-attachments/assets/edb22301-0dd3-492b-abea-a20a2f2ee772

Example of Whirl transformation:

.. image:: https://github.com/user-attachments/assets/3467f0e7-884a-496e-9516-133d3c5596f4
  :target: https://github.com/user-attachments/assets/3467f0e7-884a-496e-9516-133d3c5596f4

Twist and Whirl combined:

.. image:: https://github.com/user-attachments/assets/0b351703-97ae-4960-9f86-42f7c2825c0b
  :target: https://github.com/user-attachments/assets/0b351703-97ae-4960-9f86-42f7c2825c0b

