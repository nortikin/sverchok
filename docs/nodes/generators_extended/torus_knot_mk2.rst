Torus Knot
==========

Functionality
-------------

Torus Knot generator will create a torus knot based on its radii sets, curve resolution and phases.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Major Radius**      [1]
- **Minor Radius**      [1]
- **Exterior Radius**   [2]
- **Interior Radius**   [2]
- **Curve Resolution**
- **Revolution Phase**  [3]
- **Spin Phase**        [3]
- **Shift**

Notes:
[1] : Major/Minor radii are available when Major/Minor mode is elected.
[2] : Exterior/Interior radii are available when Exterior/Interior mode is elected.
[3] : The phase angles are in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.

Parameters
----------

The MODE parameter allows to switch between Major/Minor and Exterior/Interior radii values. The input socket values for the two radii are interpreted as such based on the current mode.

All parameters except **mode** can be given by the node or an external input.

+-------------------------+------------+------------+----------------------------------------------------+
| Param                   |  Type      |  Default   |  Description                                       |
+=========================+============+============+====================================================+
| **Major Radius**        |  Float     |  1.00      |  Major radius of the torus [1]                     |
+-------------------------+------------+------------+----------------------------------------------------+
| **Minor Radius**        |  Float     |  0.25      |  Minor radius of the torus [1]                     |
+-------------------------+------------+------------+----------------------------------------------------+
| **Exterior Radius**     |  Float     |  1.25      |  Exterior radius of the torus [2]                  |
+-------------------------+------------+------------+----------------------------------------------------+
| **Interior Radius**     |  Float     |  0.75      |  Interior radius of the torus [2]                  |
+-------------------------+------------+------------+----------------------------------------------------+
| **Curve Resolution**    |  Int       |  100       |  Number of vertices in a curve (per link)          |
+-------------------------+------------+------------+----------------------------------------------------+
| **Revolution Phase**    |  Float     |  0.00      |  Phase revolution vertices by a radian amount [3]  |
+-------------------------+------------+------------+----------------------------------------------------+
| **Spin Phase**          |  Float     |  0.00      |  Phase spin vertices by a radian amount [3]        |
+-------------------------+------------+------------+----------------------------------------------------+
| **Shift**               |  Float     |  0.00      |  Shift the points along the curve (0-1) [4]        |
+-------------------------+------------+------------+----------------------------------------------------+

Notes:
[1] : Major/Minor radii are available when Major/Minor mode is elected.
[2] : Exterior/Interior radii are available when Exterior/Interior mode is elected.
[3] : Phase angles are given by default in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.
[4] : shift = 0 for no shift, shift = 1 for a complete shift along the curve

Extra Parameters
----------------
A set of extra parameters are available on the property panel. These parameters do not receive external input.

+-------------------------+------------+------------+-----------------------------------------------+
| Extra Param             |  Type      |  Default   |  Description                                  |
+=========================+============+============+===============================================+
| **Angle Units**         | Enum       | DEGREES    | Interprets the angle values based on          |
|                         |  RADIANS   |            | the selected angle units:                     |
|                         |  DEGREES   |            |   Radians = 0 - 2pi                           |
|                         |  UNITIES   |            |   Degrees = 0 - 360                           |
|                         |            |            |   Unities = 0 - 1                             |
+-------------------------+------------+------------+-----------------------------------------------+
| **Adaptive Resolution** |  Bool      |  False     |  Adjusts curve resolution dynamically         |
+-------------------------+------------+------------+-----------------------------------------------+
| **Point Density**       |  Int       |  10        |  Number of points per unit length [1]         |
+-------------------------+------------+------------+-----------------------------------------------+
| **Multiple Links**      |  Bool      |  True      |  Generate multiple links in a degenerate knot |
+-------------------------+------------+------------+-----------------------------------------------+
| **Flip p**              |  Bool      |  False     |  Flip REVOLUTION direction (P)                |
+-------------------------+------------+------------+-----------------------------------------------+
| **Flip q**              |  Bool      |  False     |  Flip SPIN direction (Q)                      |
+-------------------------+------------+------------+-----------------------------------------------+
| **P multiplier**        |  Int       |  1         |  Multiplies the p count [2]                   |
+-------------------------+------------+------------+-----------------------------------------------+
| **Q multiplier**        |  Int       |  1         |  Multiplies the q count [2]                   |
+-------------------------+------------+------------+-----------------------------------------------+
| **Height**              |  Float     |  1.00      |  Scales the vertices along Z by this amount   |
+-------------------------+------------+------------+-----------------------------------------------+
| **Scale**               |  Float     |  1.00      |  Scales both radii by this amount             |
+-------------------------+------------+------------+-----------------------------------------------+
| **Normalize Tangents**  |  Bool      |  True      |  Normalize the TANGENT vectors [3]            |
+-------------------------+------------+------------+-----------------------------------------------+
| **Normalize Normals**   |  Bool      |  True      |  Normalize the NORMAL vectors [3]             |
+-------------------------+------------+------------+-----------------------------------------------+

Notes:
[1] : Used only when the Adaptive Resolution is on
[2] : Used without adaptive resolution these allow to create aliased torus knots resulting in all sorts of interesting shaped knots.
[3] : Turn off normalization to save computation whenever the output vectors do not need to be normalized.

Outputs
-------

**Vertices**, **Edges**, **Tangents** and **Normals**
All outputs will be generated when connected.


Example of usage
----------------

