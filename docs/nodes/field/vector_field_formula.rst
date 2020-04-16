Vector Field Formula
====================

Functionality
-------------

This node generates a Vector Field, defined by some user-provided formula.

The formula should map the coordinates of the point in 3D space into some vector in 3D space. Both original points and the resulting vector can be expressed in one of supported coordinate systems.

It is possible to use additional parameters in the formula, they will become inputs of the node.

It is also possible to use the value of some other Vector Field in the same point in the formula.

Expression syntax
-----------------

Syntax being used for formulas is standard Python's syntax for expressions. 
For exact syntax definition, please refer to https://docs.python.org/3/reference/expressions.html.

In short, you can use usual mathematical operations (`+`, `-`, `*`, `/`, `**` for power), numbers, variables, parenthesis, and function call, such as `sin(x)`.

One difference with Python's syntax is that you can call only restricted number of Python's functions. Allowed are:

- Functions from math module:
  - acos, acosh, asin, asinh, atan, atan2,
        atanh, ceil, copysign, cos, cosh, degrees,
        erf, erfc, exp, expm1, fabs, factorial, floor,
        fmod, frexp, fsum, gamma, hypot, isfinite, isinf,
        isnan, ldexp, lgamma, log, log10, log1p, log2, modf,
        pow, radians, sin, sinh, sqrt, tan, tanh, trunc;
- Constants from math module: pi, e;
- Additional functions: abs, sign;
- From mathutlis module: Vector, Matrix;
- Python type conversions: tuple, list, dict.

This restriction is for security reasons. However, Python's ecosystem does not guarantee that noone can call some unsafe operations by using some sort of language-level hacks. So, please be warned that usage of this node with JSON definition obtained from unknown or untrusted source can potentially harm your system or data.

Examples of valid expressions are:

* 1.0
* x
* x+1
* 0.75*X + 0.25*Y
* R * sin(phi)

Inputs
------

This node has the following input:

* **Field**. A vector field, whose values can be used in the formula. This
  input is required only if the formula involves the **V** variable.

Each variable used in the formula, except for `V` and the coordinate variables, also becomes additional input.

The following variables are considered to be point coordinates:

* For Carthesian input mode: `x`, `y` and `z`;
* For Cylindrical input mode: `rho`, `phi` and `z`;
* For Spherical input mode: `rho`, `phi` and `theta`.

Parameters
----------

This node has the following parameters:

* **Input**. This defines the coordinate system being used for the input
  points. The available values are **Carhtesian**, **Cylindrical** and
  **Spherical**. The default value is **Carthesian**.
* **Formula1**, **Formula2**, **Formula3**. Three formulas defining the
  respective coordinate / components of the resulting vectors: X, Y, Z, or Rho,
  Phi, Z, or Rho, Phi, Theta, depending on the **Output** parameter. The
  default formulas are `-y`, `x` and `z`, which defines the field which rotates
  the whole space 90 degrees around the Z axis.
* **Output**. This defines the coordinate system in which the resulting vectors
  are expressed. The available values are **Carhtesian**, **Cylindrical** and
  **Spherical**. The default value is **Carthesian**.

Outputs
-------

This node has the following output:

* **Field**. The generated vector field.

Examples of usage
-----------------

Some vector field defined by a formula in Spherical coordinates:

.. image:: https://user-images.githubusercontent.com/284644/79491540-0a722c80-8038-11ea-914f-0221e5e75f68.png

Similar field applied to some box:

.. image:: https://user-images.githubusercontent.com/284644/79491547-0ba35980-8038-11ea-89fc-063982ea65cd.png


