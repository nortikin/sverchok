Spiral
========

.. image:: https://user-images.githubusercontent.com/14288520/191084536-e7475066-51ff-4ff9-aebe-2110f12541fe.png
  :target: https://user-images.githubusercontent.com/14288520/191084536-e7475066-51ff-4ff9-aebe-2110f12541fe.png

.. image:: https://user-images.githubusercontent.com/14288520/191089772-4456ac0b-8fca-4780-a56d-881d4c24001c.png
  :target: https://user-images.githubusercontent.com/14288520/191089772-4456ac0b-8fca-4780-a56d-881d4c24001c.png

Functionality
-------------

Generates various types of spirals: Archimedean, Logarithmic, Spherical, Cornu (Euler), Ovoidal, Exo (to coin the term) and Spirangle.

All spirals are defined as smooth curves (given enough curve resolution per turn) except the Spirangle spiral, which is a polygonal type of spiral.

Most of the spirals are 2D and some are 3D, but any of the 2D spirals can be turned into 3D by setting the height parameter to a non-zero value.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Exterior Radius** **[1]**
- **Interior Radius** **[1]**
- **Exponent**        **[2]**
- **Turns**
- **Turn Resolution**
- **Scale**           **[3]**
- **Height**          **[4]**
- **Phase**           **[5]**
- **Arms**

Notes:

* **[1]** : For some spirals the Exterior/Interior radii are repurposed to represent other spiral parameters like spherical (3D) radius, spiral length (Cornu) etc.
* **[2]** : For some spirals the exponent setting is repurposed to alter spiral shape in some way.
* **[3]** : For some spirals the scale settings affect xy radii, while for others it scales xyz radii.
* **[4]** : For some spirals the height setting spreads the spiral along z, for other it is ignored (e.g. spherical spiral has a predefined height to define a sphere)
* **[5]** : The phase angle is in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.


Parameters
----------

All settings except **Spiral Type**, **Flip**, **Separate** and **Preset** can be given by the node or an external input.

+----------------------+--------------+-------------+-----------------------------------------------+
| Param                | Type         | Default [1] | Description                                   |
+======================+==============+=============+===============================================+
| **Spiral Type**      | Enum:        | Archimedean | Type of the spiral. Each type is defined by   |
|                      |              |             |                                               |
|                      | * Archimedean|             | a unique formula (See "Spiral Type" section   |
|                      |              |             |                                               |
|                      | * Logarithmic|             | for details).                                 |
|                      | * Spherical  |             |                                               |
|                      | * Ovoidal    |             |                                               |
|                      | * Cornu      |             |                                               |
|                      | * Exo        |             |                                               |
|                      | * Spirangle  |             |                                               |
+----------------------+--------------+-------------+-----------------------------------------------+
| **Flip**             |  Bool        |   False     | Flip the direction of the spiral from counter |
|                      |              |             |                                               |
|                      |              |             | clockwise to clockwise.                       |
+----------------------+--------------+-------------+-----------------------------------------------+
| **Separate**         |  Bool        |   False     | Separate the arms of the spiral into distinct |
|                      |              |             |                                               |
|                      |              |             | lists of vertices and edges.                  |
+----------------------+--------------+-------------+-----------------------------------------------+
| **Exterior Radius**  |  Float       |   0.1       | Exterior radius of the spiral.                |
+----------------------+--------------+-------------+-----------------------------------------------+
| **Interior Radius**  |  Float       |   0.0       | Interior radius of the spiral.                |
+----------------------+--------------+-------------+-----------------------------------------------+
| **Exponent**         |  Float       |   1.0       | Exponent, attenuator, slope.                  |
+----------------------+--------------+-------------+-----------------------------------------------+
| **Turns**            |  Int         |   7         | Number of turns in the spiral (>= 1).         |
+----------------------+--------------+-------------+-----------------------------------------------+
| **Turn Resolution**  |  Int         |   100       | Number of points in one turn (>= 3).          |
+----------------------+--------------+-------------+-----------------------------------------------+
| **Scale**            |  Float       |   1.00      | Scale the radii of the spiral.                |
+----------------------+--------------+-------------+-----------------------------------------------+
| **Height**           |  Float       |   0.0       | Height of the 3D spiral (2D if height = 0).   |
+----------------------+--------------+-------------+-----------------------------------------------+
| **Phase**            |  float       |   0.0       | Phase around the spiral center. **[2]**       |
+----------------------+--------------+-------------+-----------------------------------------------+
| **Arms**             |  Int         |   1         | Number of arms in the spiral.                 |
+----------------------+--------------+-------------+-----------------------------------------------+

Notes:

* **[1]** : The default values for the spiral settings listed above correspond to the **Archimedean** preset, which is the default preset when creating a new spiral node (see Presets section).
* **[2]** : Phase angle is given by default in DEGREES. The Property Panel has option to set angle units as: RADIANS, DEGREES or UNITIES.


Spiral Types
------------
**Archimedean**
The general Archimedean spirals are given by the formula:

  r = a + b * theta ^ (1/c)

where different value of c define certain known spirals:

  c =  1.0 : Archimedean spiral
  c =  2.0 : Parabolic spiral (Fermat)
  c = -1.0 : Hyperbolic spiral
  c = -2.0 : Lituus spiral

http://mathworld.wolfram.com/ArchimedeanSpiral.html
https://en.wikipedia.org/wiki/Archimedean_spiral

**Logarithmic**
The logarithmic spirals are given by the formula:

  r = a + b * e ^ (c * theta)

For c = ln(Phi)/(Pi/2) the logarithmic spiral is a Fibonacci (golden) spiral.

https://en.wikipedia.org/wiki/Logarithmic_spiral

**Spherical**
The spherical spirals are given by the formula:

  x = a * cos(b * t) * cos(c * t)
  y = a * sin(b * t) * cos(c * t)
  z = a * sin(c * t)

where a, b, c are constants.

see: http://mathworld.wolfram.com/SphericalSpiral.html

**Cornu**
The Cornu spiral (also known as Euler spiral) is given the by the formula:

  x(L) = integral(cos(s^2), 0, L)
  y(L) = integral(sin(s^2), 0, L)

see: http://mathworld.wolfram.com/CornuSpiral.html
see: https://en.wikipedia.org/wiki/Euler_spiral

**Ovoidal**
The Ovoidal spiral is similar to the spherical spiral and its vertical cross section shape is given by the intersection of two circles of radius R which overlap by radius r, while the horizontal cross section is a circle of radius r.

Note: when R = r the ovoidal spiral is identical to the spherical spiral.

**Exo**
The Exo spiral is given by the formula:

  r = a + (b-a) / (1 + exp(-c * (t - 0.5)))

This spiral has its radius follow a sigmoid transition between an inner radius and an outer radius.

**Spirangle**
The Spirangle spiral is given by the formula:

  phi = phi + deltaPhi
  r = r + deltaR
  x = x + r * cos(phi)
  y = y + r * sin(phi)

where deltaPhi = 2*pi / N, and deltaR is a constant.

see: https://en.wikipedia.org/wiki/Spirangle

Outputs
-------

**Vertices** and **Edges**
All outputs will be generated when connected.

Note: for spirals with multiple arms the outputs consist of disjoint lists defining each arm.


Presets
-------
A set of spiral configuration presets is available for convenience. Once a preset is selected the spiral settings are updated with the preset values and the user can modify the settings to further alter the spiral shape.

Note: once a setting is altered (after selecting a preset) the preset selection is cleared from the preset drop-down indicating that the new setting configuration is no longer the one corresponding to the previously selected preset.

+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Preset        | type         |   R   |   r   |   e   |   t   |   N   |   s   |   h   |
+===============+==============+=======+=======+=======+=======+=======+=======+=======+
| Fibonacci     | Logarithmic  |  0.1  |  0.0  |**[1]**|   4   |  100  |  0.1  |  0.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Helix         | Logarithmic  |  1.0  |  1.0  |  0.0  |   7   |  100  |  1.0  |  7.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Archimedean   | Archimedean  |  0.1  |  0.0  |  1.0  |   7   |  100  |  1.0  |  0.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Conical       | Archimedean  |  0.1  |  0.0  |  1.0  |   7   |  100  |  1.0  |  10.0 |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Parabolic     | Archimedean  |  1.0  |  0.0  |  2.0  |   3   |  100  |  1.0  |  0.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Hyperbolic    | Archimedean  | 10.0  |  0.0  |  -1.0 |   11  |  100  |  2.0  |  0.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Lituus        | Archimedean  |  7.0  |  0.0  |  -2.0 |   11  |  100  |  1.0  |  0.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Spherical     | Spherical    |  5.0  |  0.0  |  0.0  |   11  |   55  |  1.0  |  0.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Ovoidal       | Ovoidal      |  11.0 |  4.0  |  0.0  |   7   |   55  |  1.0  |  0.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Cornu         | Cornu        |  1.0  |  0.0  |  0.0  |   7   |  111  |  5.0  |  0.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Exo           | Exo          |  5.0  |  1.0  |  13.0 |   11  |  101  |  1.0  |  0.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Spirangle SC  | Spirangle    |  1.0  |  0.0  |  0.0  |   8   |   4   |  1.0  |  0.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+
| Spirangle HX  | Spirangle    |  1.0  |  0.0  |  0.5  |   7   |   6   |  0.1  |  0.0  |
+---------------+--------------+-------+-------+-------+-------+-------+-------+-------+

Notes:

* **[1]** : Fibonacci spiral exponent is: ln(PHI)/(PI/2), where PHI is the golden ratio.
* **[2]** : The Spirangle SC and HX stand for Square/Constant and Hexa/Exponential, given the selected values.

The preset settings were selected for each type such that when switching from one preset to another the generated spirals are relatively the same size.


Extra Parameters
----------------
A set of extra parameters are available on the property panel. These parameters do not receive external input.

+-------------------------+------------+------------+-----------------------------------------------+
| Extra Param             |  Type      |  Default   |  Description                                  |
+=========================+============+============+===============================================+
| **Angle Units**         | Enum       | DEGREES    | Interprets the angle values based on          |
|                         |            |            |                                               |
|                         |            |            | the selected angle units:                     |
|                         | * RADIANS  |            |                                               |
|                         | * DEGREES  |            | * Radians = 0.0 - 2pi                         |
|                         | * UNITIES  |            | * Degrees = 0.0 - 360.0                       |
|                         |            |            | * Unities = 0.0 - 1.0                         |
+-------------------------+------------+------------+-----------------------------------------------+


Outputs
-------

**Vertices* and **Edges**
All outputs will be generated when connected.
When **Separate** is off the output generates a continuous list of vertices and edges (regardless of number of arms), otherwise it generates separate lists of vertices and edges for each arm.


Example of usage
----------------

