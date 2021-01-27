Scalar Math
===========

Functionality
-------------

This node can transform incoming values by a selected function (trigonometric,
or other mathematical function, and also provide some useful math constants)

Inputs & Parameters
-------------------

**float** or **int**

This node will accept lists of flat NumPy arrays [Not available for GCD or Round-N]

+---------------+------------------------+
| **class**     | **type**               |
+---------------+------------------------+
| Trig          | Sine, Cosine,          |
|               | Tangent, Arcsine,      |
|               | Arccosine, Arctangent, |
|               | acosh, asinh, atanh,   |
|               | cosh, sinh, tanh.      |
+---------------+------------------------+
| Math          | Squareroot, Negate,    |
|               | Degrees, Radians,      |
|               | Absolute, Ceiling,     |
|               | Round, Round N, Fmod   |
|               | modulo, floor,         |
|               | Exponent, log,         |
|               | log1p,log10,           |
|               | Add, Subtract, Multiply|
|               | Divide, Int Division,  |
|               | x-1, x+1, x * 2,       |
|               | x/2, x ** 2, **,       |
|               | Min, Max, Mean, GCD    |
+---------------+------------------------+
| constants     | pi, e, phi, tau.       |
+---------------+------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Input 1 Type**: offers int / float selection for socket 1.

**Input 2 Type**: offers int / float selection for socket 2.

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). [Not available for GCD or Round-N]

**List Match**: Define how list with different lengths should be matched.  [Not available for GCD or Round-N]


Outputs
-------

**float** or **int**
