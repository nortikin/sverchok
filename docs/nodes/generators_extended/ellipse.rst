Ellipse
=======

Functionality
-------------
The ellipse node creates ellipses given a set of main parameters: major/minor radii, eccentricity, focal length. Additional parameters allow you to tweak the ellipse curve: phase, rotation and scale.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Major Radius**
- **Minor Radius** [1]
- **Eccentricity** [2]
- **Focal Length** [3]
- **Num Verts**
- **Phase**        [4]
- **Rotation**     [4]
- **Scale**

Notes:
[1] : The Minor Radius is available in **ab** mode
[2] : The Eccentricity is available in **ae** mode
[3] : The Focal Length is available in **ac** mode
[4] : The angles are in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.

Parameters
----------

The **Mode** parameter allows to select one of the three modes of defining the ellipse: **ab**, **ae** and **ac**.

- In **ab** mode the ellipse is defined by the major radius (a) and minor radius (b).
- In **ae** mode the ellipse is defined by the major radius (a) and the eccentricity (e).
- In **ac** mode the ellipse is defined by the major radius (a) and the focal length (c).

Note: when switching modes the main ellipse parameters for the new mode are derived based on the main parameters of the previous mode as to keep the ellipse the same.

The **Centering** parameter lets you center the ellipse around one of its focal points F1 or F2 or around its center C.

All parameters except **Mode** and **Centering** can take values from the node itself or an external input.

The inputs are "sanitized" to restrict their values to valid domains:
- Major radius (a) and Minor radius (b) are floats with values >= 0.0 and b <= a
- Eccentricity is a float with value in the range [0.0, 1.0]
- Focal Length is a float with value in the reange [0.0, a]
- Number of vertices is an integer with value >= 3

+------------------+--------+---------+------------------------------------------------------------+
| Param            | Type   | Default | Description                                                |
+==================+========+=========+============================================================+
| **Major Radius** | Float  | 1.0     | Major radius of the ellipse                                |
+------------------+--------+---------+------------------------------------------------------------+
| **Minor Radius** | Float  | 0.8     | Minor radius of the ellipse [1]                            |
+------------------+--------+---------+------------------------------------------------------------+
| **Eccentricity** | Float  | 0.6     | Eccentricity of the ellipse [2]                            |
+------------------+--------+---------+------------------------------------------------------------+
| **Focal Length** | Float  | 0.6     | Distance between the center and one of the foci [3]        |
+------------------+--------+---------+------------------------------------------------------------+
| **Num Verts**    | Int    | 36      | Number of vertices in the ellipse                          |
+------------------+--------+---------+------------------------------------------------------------+
| **Phase**        | Float  | 0.0     | Phase the vertices along the ellipse around its center [4] |
+------------------+--------+---------+------------------------------------------------------------+
| **Rotation**     | Float  | 0.0     | Rotate the ellipse around its centering point [4]          |
+------------------+--------+---------+------------------------------------------------------------+
| **Scale**        | Float  | 1.0     | Scale the ellipse radii by this amount.                    |
+------------------+--------+---------+------------------------------------------------------------+

Notes:
[1] : The Minor Radius is available in **ab** mode
[2] : The Eccentricity is available in **ae** mode
[3] : The Focal Length is available in **ac** mode
[4] : Angles are given by default in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.


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
Outputs will be generated when connected.

**Verts**, **Edges**, **Polys**
These are the vertices, edges and polygons of the ellipse.

**F1**, **F2**
These are the locations of the ellipse foci.

Example of usage
----------------

