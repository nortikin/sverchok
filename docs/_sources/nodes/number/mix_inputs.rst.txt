Mix Inputs
==========

Functionality
-------------

This node mixes two values of different types using a given factor, a selected interpolation and easing function.

For a factor of 0.0 it outputs the first value, for the factor of 1.0 it outputs the last value and for any other factor in between 0-1 it outputs an interpolated value between the first and second input value. An exception to this are the "Back" and "Elastic" interpolations which generate output values that are not strictly confined to the first-second value interval, but they will output values that start at first and end at second value.

Inputs & Parameters
-------------------

All parameters except for **Mode**, **Interpolation**, **Easing**, **Mirror** and **Swap** can be given by the node or an external input.

Based on the selected **Mode** the node changes the input and output socket types to match the corresponding type.

The node is vectorized so the inputs values (A/B) take either a single or a list of values. The node will extend the shortest list to match the longest list before mixing the values in the two lists.

The node has the following parameters:

+-------------------+--------------+-------------+-----------------------------------------------------+
| Parameter         | Type         | Default     | Description                                         |
+===================+==============+=============+=====================================================+
| **Mode**          | Enum:        | Float       | The type of inputs values to mix.                   |
|                   |  Int         |             |                                                     |
|                   |  Float       |             |                                                     |
|                   |  Vector      |             |                                                     |
|                   |  Color       |             |                                                     |
|                   |  Matrix      |             |                                                     |
|                   |  Quaternion  |             |                                                     |
+-------------------+--------------+-------------+-----------------------------------------------------+
| **Interpolation** | Enum:        | Linear      | Type of interpolation.                              |
|                   |  Linear      |             |   f(x) ~ x                                          |
|                   |  Sinusoidal  |             |   f(x) ~ sin(x)                                     |
|                   |  Quadratic   |             |   f(x) ~ x*2                                        |
|                   |  Cubic       |             |   f(x) ~ x^3                                        |
|                   |  Quadric     |             |   f(x) ~ x^4                                        |
|                   |  Quintic     |             |   f(x) ~ x^5                                        |
|                   |  Exponential |             |   f(x) ~ e^x                                        |
|                   |  Circular    |             |   f(x) ~ sqrt(1-x*x)                                |
|                   |  Back        |             |   f(x) ~ x*x*x - x*sin(x)                           |
|                   |  Bounce      |             |   f(x) ~ series of geometric progression parabolas  |
|                   |  Elastic     |             |   f(x) ~ sin(x) * e^x                               |
+-------------------+--------------+-------------+-----------------------------------------------------+
| **Easing**        | Enum         | Ease In-Out | Type of easing.                                     |
|                   |  Ease In     |             |  Ease In = slowly departs the starting value        |
|                   |  Ease Out    |             |  Ease Out = slowly approaches the ending value      |
|                   |  Ease In-Out |             |  Ease In-Out = slowly departs and approaches values |
+-------------------+--------------+-------------+-----------------------------------------------------+
| **Mirror**        | Bool         | False       | Mirror the mixing factor around 0.5.                |
+-------------------+--------------+-------------+-----------------------------------------------------+
| **Swap**          | Bool         | False       | Swap the two input values A and B.                  |
+-------------------+--------------+-------------+-----------------------------------------------------+
| **Factor**        | Float        | 0.5         | Mixing factor (between 0.0 and 1.0)                 |
+-------------------+--------------+-------------+-----------------------------------------------------+
| **A**             | Any type     |             | Starting value                                      |
+-------------------+--------------+-------------+-----------------------------------------------------+
| **B**             | Any type     |             | Ending value                                        |
+-------------------+--------------+-------------+-----------------------------------------------------+


Extra Parameters
----------------
For certain interpolation types the node provides extra parameters on the Property Panel.

* Exponential
  Extra parameters to adjust the base and the exponent of the exponential function. The Defaults are 2 and 10.0.

* Back
  Extra parameters to adjust the scale of the overshoot. The default is 1.0.

* Bounce
  Extra parameters to adjust the attenuation of the bounce and the number of bounces. The defaults are 0.5 and 4.

* Elastic
  Extra parameters to adjust the base and the exponent of the damping oscillation as well as the number of bounces (oscillations). The defaults are 1.6, 6.0 and 6.


Outputs
-------

Based on the selected **Mode** the node outputs the corresponding type value.


