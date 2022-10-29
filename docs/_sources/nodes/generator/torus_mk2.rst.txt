Torus
========

.. image:: https://user-images.githubusercontent.com/14288520/188714711-643291b3-6234-4a66-8c1b-8382d6ae3bac.png
  :target: https://user-images.githubusercontent.com/14288520/188714711-643291b3-6234-4a66-8c1b-8382d6ae3bac.png

Functionality
-------------

This node generates torus like meshes.

.. image:: https://user-images.githubusercontent.com/14288520/191261409-2e7c851b-1fc3-4978-97f7-0fcad4763cea.png
  :target: https://user-images.githubusercontent.com/14288520/191261409-2e7c851b-1fc3-4978-97f7-0fcad4763cea.png

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Major Radius** - Radius from the torus origin to the center of the cross section **[1]**
- **Minor Radius** - Radius of the torus' cross section **[1]**
- **Revolution Sections** - Number of sections around the torus center
- **Spin Sections** - Number of sections around the torus tube
- **Revolution Phase** - Phase the revolution sections by this angle amount **[3]**
- **Spin Phase** - Phase the spin sections by this angle amount **[3]**
- **Revolution Exponent** - Exponent of the revolution profile
- **Spin Exponent** - Exponent of the spin profile
- **Spin Twist** - number of twists (start-end vertex shift)
- **Exterior Radius** - Exterior radius of the torus (farthest from the torus center) **[2]**
- **Interior Radius** - Interior radius of the torus (closest to the torus center) **[2]**

Notes:

* **[1]** : Major/Minor radii are available when Major/Minor mode is elected.
* **[2]** : Exterior/Interior radii are available when Exterior/Interior mode is selected.
* **[3]** : The phase angles are in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.

Parameters
----------

The MODE parameter allows to switch between Major/Minor and Exterior/Interior
radii values. The input socket values for the two radii are interpreted as such
based on the current mode.

All parameters except **mode** and **Separate** can be given by the node or an external input.

+-------------------------+----------+----------+------------------------------------------------------+
| Param                   |  Type    |  Default |  Description                                         |
+=========================+==========+==========+======================================================+
| **Major Radius**        |  Float   |  1.00    |  Major radius of the torus **[1]**                   |
+-------------------------+----------+----------+------------------------------------------------------+
| **Minor Radius**        |  Float   |  0.25    |  Minor radius of the torus **[1]**                   |
+-------------------------+----------+----------+------------------------------------------------------+
| **Exterior Radius**     |  Float   |  1.25    |  Exterior radius of the torus **[2]**                |
+-------------------------+----------+----------+------------------------------------------------------+
| **Interior Radius**     |  Float   |  0.75    |  Interior radius of the torus **[2]**                |
+-------------------------+----------+----------+------------------------------------------------------+
| **Revolution Sections** |  Int     |  32      |  Number of sections around torus center              |
+-------------------------+----------+----------+------------------------------------------------------+
| **Spin Sections**       |  Int     |  16      |  Number of sections around torus tube                |
+-------------------------+----------+----------+------------------------------------------------------+
| **Revolution Phase**    |  Float   |  0.00    |  Phase revolution sections by a angle amount **[4]** |
+-------------------------+----------+----------+------------------------------------------------------+
| **Spin Phase**          |  Float   |  0.00    |  Phase spin sections by a angle amount **[4]**       |
+-------------------------+----------+----------+------------------------------------------------------+
| **Revolution Exponent** |  Float   |  1.00    |  Exponent of the revolution profile **[5]**          |
+-------------------------+----------+----------+------------------------------------------------------+
| **Spin Exponent**       |  Float   |  1.00    |  Exponent of the spin profile **[5]**                |
+-------------------------+----------+----------+------------------------------------------------------+
| **Spin Twist**          |  Int     |  0       |  Twist spin sections by this increment amount **[3]**|
+-------------------------+----------+----------+------------------------------------------------------+
| **Separate**            |  Boolean |  False   |  Grouping vertices by V direction                    |
+-------------------------+----------+----------+------------------------------------------------------+

Notes:

* **[1]** : Major/Minor radii are available when Major/Minor mode is elected.
* **[2]** : Exterior/Interior radii are available when Exterior/Interior mode is elected.
* **[3]** : When the twist has the same value as the spin sections the torus tube makes a full twist.
* **[4]** : Phase angles are given by default in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.
* **[5]** : The exponents alter the circular profiles inwards or outwards to make a starrish or a squarish shape.

Extra Parameters
----------------
A set of extra parameters are available on the property panel.
These parameters do not receive external input.

+------------------+----------+---------+--------------------------------------+
| Extra Param      | Type     | Default | Description                          |
+==================+==========+=========+======================================+
| **Angle Units**  | Enum     | DEGREES | Interprets the angle values based on |
|                  |          |         | the selected angle units:            |
|                  |* RADIANS |         |                                      |
|                  |* DEGREES |         | * Radians = 0 - 2pi                  |
|                  |* UNITIES |         | * Degrees = 0 - 360                  |
|                  |          |         | * Unities = 0 - 1                    |
+------------------+----------+---------+--------------------------------------+

Outputs
-------

**Vertices**, **Edges**, **Polygons** and **Normals**
All outputs will be generated when connected.


Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/188714731-f669d332-df7d-4aa7-8036-e9ec416bf22f.png
  :target: https://user-images.githubusercontent.com/14288520/188714731-f669d332-df7d-4aa7-8036-e9ec416bf22f.png

.. image:: https://user-images.githubusercontent.com/14288520/188714763-6cd28cb9-0090-45ec-aa10-6f9c0dbe03f2.gif
  :target: https://user-images.githubusercontent.com/14288520/188714763-6cd28cb9-0090-45ec-aa10-6f9c0dbe03f2.gif