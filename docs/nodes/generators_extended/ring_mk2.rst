Ring
====

Functionality
-------------

Ring generator will create a 2D ring based on its radii sets, number of sections and phase.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Major Radius**    [1]
- **Minor Radius**    [1]
- **Exterior Radius** [2]
- **Interior Radius** [2]
- **Radial Sections**
- **Circular Sections**
- **Start Angle**     [3]
- **End Angle**       [3]
- **Phase**           [3]

Notes:
[1] : Major/Minor radii are available when Major/Minor mode is elected.
[2] : Exterior/Interior radii are available when Exterior/Interior mode is elected.
[3] : The angles are in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.

Parameters
----------

The MODE parameter allows to switch between Major/Minor and Exterior/Interior
radii values. The input socket values for the two radii are interpreted as such
based on the current mode.

All parameters except **Mode** and **Separate** can be given by the node or an external input.

+------------------------+-----------+-----------+---------------------------------------------+
| Param                  |  Type     |  Default  |  Description                                |
+========================+===========+===========+=============================================+
| **Major Radius**       |  Float    |  1.00     |  Major radius of the ring [1]               |
+------------------------+-----------+-----------+---------------------------------------------+
| **Minor Radius**       |  Float    |  0.25     |  Minor radius of the ring [1]               |
+------------------------+-----------+-----------+---------------------------------------------+
| **Exterior Radius**    |  Float    |  1.25     |  Exterior radius of the ring [2]            |
+------------------------+-----------+-----------+---------------------------------------------+
| **Interior Radius**    |  Float    |  0.75     |  Interior radius of the ring [2]            |
+------------------------+-----------+-----------+---------------------------------------------+
| **Radial Sections**    |  Int      |  32       |  Number of sections around the ring center  |
+------------------------+-----------+-----------+---------------------------------------------+
| **Circular Sections**  |  Int      |  3        |  Number of sections accross the ring band   |
+------------------------+-----------+-----------+---------------------------------------------+
| **Start Angle**        |  Float    |  0        |  Start angle of the ring [3][4]             |
+------------------------+-----------+-----------+---------------------------------------------+
| **End Angle**          |  Float    |  360      |  End angle of the ring [3][4]               |
+------------------------+-----------+-----------+---------------------------------------------+
| **Phase**              |  Float    |  0.00     |  Phase of the radial sections [3]           |
+------------------------+-----------+-----------+---------------------------------------------+
| **Separate**           |  Bolean   |  False    |  Grouping vertices by V direction           |
+------------------------+-----------+-----------+---------------------------------------------+

Notes:
[1] : Major/Minor radii are available when Major/Minor mode is elected.
[2] : Exterior/Interior radii are available when Exterior/Interior mode is elected.
[3] : Angles are given by default in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.
[4] : When start and end angle (modulo 2pi) are equal, the ring is closed (no duplicate verts are created)

Extra Parameters
----------------
Property panel has extra parameters to tweak the ring.

**Subdivide Circular**
With this parameter the circular sections can be subdivided to give smoother circles while the circular sections may be low.

Outputs
-------

**Vertices**, **Edges** and **Polygons**.
All outputs will be generated when connected.


Example of usage
----------------

