Ellipse
=======

.. image:: https://user-images.githubusercontent.com/14288520/190974205-bf333be6-f17b-41eb-b277-32c57a059e8f.png
  :target: https://user-images.githubusercontent.com/14288520/190974205-bf333be6-f17b-41eb-b277-32c57a059e8f.png

.. image:: https://user-images.githubusercontent.com/14288520/190987328-1580d339-8a75-436a-8f91-3bcfa5764af2.png
  :target: https://user-images.githubusercontent.com/14288520/190987328-1580d339-8a75-436a-8f91-3bcfa5764af2.png

Functionality
-------------
The ellipse node creates ellipses given a set of main parameters: major/minor radii, eccentricity, focal length. Additional parameters allow you to tweak the ellipse curve: phase, rotation, scale and x/y exponents.

Super Ellipse formula:

(x/a)^n + (y/b)^m = 1

Different values of the x and y exponents (n and m) generate various shapes such
as: astroid, square/rhombus, circle/ellipse, squircle/rectellipse.

astroid: 0 < n,m < 1
square/diamond: n/m = 1
circle/ellipse: n/m = 2
squircle/rectellipse: n/m > 2

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
- **Exponent X**
- **Exponent Y**

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
- Focal Length is a float with value in the range [0.0, a]
- Number of vertices is an integer with value >= 3
- Scale is a float with values >= 0.0


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
| **Exponent X**   | Float  | 2.0     | Exponent modulating the curve X direction. [5]             |
+------------------+--------+---------+------------------------------------------------------------+
| **Exponent Y**   | Float  | 2.0     | Exponent modulating the curve Y direction. [5]             |
+------------------+--------+---------+------------------------------------------------------------+

Notes:
[1] : The Minor Radius is available in **ab** mode
[2] : The Eccentricity is available in **ae** mode
[3] : The Focal Length is available in **ac** mode
[4] : Angles are given by default in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.
[5] : Various combinations of the XY exponents generate different super ellipse curves (e.g. eX = eY = 2 the shape is an ellipse)

Extra Parameters
----------------
A set of extra parameters are available on the property panel.
These parameters do not receive external input.

+------------------+----------+---------+--------------------------------------+
| Extra Param      | Type     | Default | Description                          |
+==================+==========+=========+======================================+
| **Angle Units**  | Enum     | DEGREES | Interprets the angle values based on |
|                  |  RADIANS |         | the selected angle units:            |
|                  |  DEGREES |         | Radians = 0 - 2pi                    |
|                  |  UNITIES |         | Degrees = 0 - 360                    |
|                  |          |         | Unities = 0 - 1                      |
+------------------+----------+---------+--------------------------------------+


Outputs
-------
Outputs will be generated when connected.

**Verts**, **Edges**, **Polys**
These are the vertices, edges and polygons of the ellipse.

**F1**, **F2**
These are the locations of the ellipse foci.


Presets
-------
A set of super ellipse configuration **presets** is available for convenience. Once a preset is selected the super ellipse settings are updated with the preset values and the user can modify the settings to further alter the super ellipse shape.

Note: once a setting is altered (after selecting a preset) the preset selection is cleared from the preset drop-down indicating that the new setting configuration is no longer the one corresponding to the previously selected preset.

+------------------+-----+-----+-----+-----+-----+
| Preset           | R   | r   | eX  | eY  | N   |
+==================+=====+=====+=====+=====+=====+
| **STAR**         | 1.0 | 1.0 | 0.3 | 0.3 | 200 |
+------------------+-----+-----+-----+-----+-----+
| **ASTROID**      | 1.0 | 1.0 | 0.6 | 0.6 | 200 |
+------------------+-----+-----+-----+-----+-----+
| **DIAMOND**      | 1.0 | 0.6 | 1.0 | 1.0 | 100 |
+------------------+-----+-----+-----+-----+-----+
| **EYELENS**      | 1.0 | 0.6 | 2.0 | 1.0 | 100 |
+------------------+-----+-----+-----+-----+-----+
| **SQUARE**       | 1.0 | 1.0 | 1.0 | 1.0 | 100 |
+------------------+-----+-----+-----+-----+-----+
| **CIRCLE**       | 1.0 | 1.0 | 2.0 | 2.0 | 100 |
+------------------+-----+-----+-----+-----+-----+
| **ELLIPSE**      | 1.0 | 0.6 | 2.0 | 2.0 | 100 |
+------------------+-----+-----+-----+-----+-----+
| **SQUIRCLE**     | 1.0 | 1.0 | 4.0 | 4.0 | 100 |
+------------------+-----+-----+-----+-----+-----+
| **HYPOELLIPSE**  | 1.0 | 0.6 | 1.5 | 1.5 | 100 |
+------------------+-----+-----+-----+-----+-----+
| **HYPERELLIPSE** | 1.0 | 0.6 | 2.5 | 2.5 | 100 |
+------------------+-----+-----+-----+-----+-----+
| **RECTELLIPSE**  | 1.0 | 0.6 | 4.0 | 4.0 | 100 |
+------------------+-----+-----+-----+-----+-----+


Example of usage
----------------


Reference
---------
https://mathworld.wolfram.com/Superellipse.html
https://en.wikipedia.org/wiki/Superellipse
https://en.wikipedia.org/wiki/Ellipse


