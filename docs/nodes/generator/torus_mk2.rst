Torus
========

Functionality
-------------

This node generates torus like meshes.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Major Radius**     [1]
- **Minor Radius**     [1]
- **Exterior Radius**  [2]
- **Interior Radius**  [2]
- **Revolution Sections**
- **Spin Sections**
- **Revolution Phase** [3]
- **Spin Phase**       [3]
- **Revolution Exponent**
- **Spin Exponent**
- **Spin Twist**

Notes:
[1] : Major/Minor radii are available when Major/Minor mode is elected.
[2] : Exterior/Interior radii are available when Exterior/Interior mode is elected.
[3] : The phase angles are in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.

Parameters
----------

The MODE parameter allows to switch between Major/Minor and Exterior/Interior
radii values. The input socket values for the two radii are interpreted as such
based on the current mode.

All parameters except **mode** and **Separate** can be given by the node or an external input.

+-------------------------+----------+----------+---------------------------------------------------+
| Param                   |  Type    |  Default |  Description                                      |
+=========================+==========+==========+===================================================+
| **Major Radius**        |  Float   |  1.00    |  Major radius of the torus [1]                    |
+-------------------------+----------+----------+---------------------------------------------------+
| **Minor Radius**        |  Float   |  0.25    |  Minor radius of the torus [1]                    |
+-------------------------+----------+----------+---------------------------------------------------+
| **Exterior Radius**     |  Float   |  1.25    |  Exterior radius of the torus [2]                 |
+-------------------------+----------+----------+---------------------------------------------------+
| **Interior Radius**     |  Float   |  0.75    |  Interior radius of the torus [2]                 |
+-------------------------+----------+----------+---------------------------------------------------+
| **Revolution Sections** |  Int     |  32      |  Number of sections around torus center           |
+-------------------------+----------+----------+---------------------------------------------------+
| **Spin Sections**       |  Int     |  16      |  Number of sections around torus tube             |
+-------------------------+----------+----------+---------------------------------------------------+
| **Revolution Phase**    |  Float   |  0.00    |  Phase revolution sections by a angle amount [4]  |
+-------------------------+----------+----------+---------------------------------------------------+
| **Spin Phase**          |  Float   |  0.00    |  Phase spin sections by a angle amount [4]        |
+-------------------------+----------+----------+---------------------------------------------------+
| **Revolution Exponent** |  Float   |  1.00    |  Exponent of the revolution profile [5]           |
+-------------------------+----------+----------+---------------------------------------------------+
| **Spin Exponent**       |  Float   |  1.00    |  Exponent of the spin profile [5]                 |
+-------------------------+----------+----------+---------------------------------------------------+
| **Spin Twist**          |  Int     |  0       |  Twist spin sections by this increment amount [3] |
+-------------------------+----------+----------+---------------------------------------------------+
| **Separate**            |  Bolean  |  False   |  Grouping vertices by V direction                 |
+-------------------------+----------+----------+---------------------------------------------------+

Notes:
[1] : Major/Minor radii are available when Major/Minor mode is elected.
[2] : Exterior/Interior radii are available when Exterior/Interior mode is elected.
[3] : When the twist has the same value as the spin sections the torus tube makes a full twist.
[4] : Phase angles are given by default in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.
[5] : The exponents alter the circular profiles inwards or outwards to make a starrish or a squarish shape.

Extra Parameters
----------------
A set of extra parameters are available on the property panel.
These parameters do not receive external input.

+------------------+----------+---------+--------------------------------------+
| Extra Param      | Type     | Default | Description                          |
+==================+==========+=========+======================================+
| **Angle Units**  | Enum     | DEGREES | Interprets the angle values based on |
|                  |  RADIANS |         | the selected angle units:            |
|                  |  DEGREES |         |   Radians = 0 - 2pi                  |
|                  |  UNITIES |         |   Degrees = 0 - 360                  |
|                  |          |         |   Unities = 0 - 1                    |
+------------------+----------+---------+--------------------------------------+

Outputs
-------

**Vertices**, **Edges**, **Polygons** and **Normals**
All outputs will be generated when connected.


Example of usage
----------------

