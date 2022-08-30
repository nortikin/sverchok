Scalar Field Formula
====================

Functionality
-------------

This node generates a Scalar Field, defined by some user-provided formula.

The formula should map the coordinates of the point in 3D space (in one of supported coordinate systems) into some number.

It is possible to use additional parameters in the formula, they will become inputs of the node.

It is also possible to use the value of some other Scalar Field in the same point in the formula.

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

This restriction is for security reasons. However, Python's ecosystem does not guarantee that no one can call some unsafe operations by using some sort of language-level hacks. So, please be warned that usage of this node with JSON definition obtained from unknown or untrusted source can potentially harm your system or data.

Examples of valid expressions are:

* 1.0
* x
* x+1
* 0.75*X + 0.25*Y
* R * sin(phi)

Inputs
------

This node has the following input:

* **Field**. A scalar field, whose values can be used in the formula. This input is required only if the formula involves the **V** variable. (see example below)

Each variable used in the formula, except for `V` and the coordinate variables, also becomes additional input.

The following variables are considered to be point coordinates:

* For Cartesian mode: `x`, `y` and `z`;
* For Cylindrical mode: `rho`, `phi` and `z`;
* For Spherical mode: `rho`, `phi` and `theta`.

Parameters
----------

This node has the following parameters:

* **Input**. This defines the coordinate system being used. The available
  values are **Carhtesian**, **Cylindrical** and **Spherical**. The default
  value is **Cartesian**.
* **Formula**. The formula which defines the scalar field. The default formula
  is `x*x + y*y + z*z`.
* **Vectorize**. This parameter is available in the N panel only. If enabled,
  then to evaluate formulas for a series of input values, the node will use
  NumPy functions to perform several computations at a time; otherwise, the
  formulas will be evaluated separately for each input value. The use of
  vectorization usually makes computations a lot faster (2x to 100x). The
  parameter is enabled by default. If you experience some kind of troubles with
  calculating some of functions (errors or not good enough precision), you can
  disable this parameter.

Outputs
-------

This node has the following output:

* **Field**. The generated scalar field.

Examples of usage
-----------------

Use the scalar field, defined by formula in in cylindrical coordinates, to scale some spheres:

.. image:: https://user-images.githubusercontent.com/284644/79490204-ef9eb880-8035-11ea-810d-59f9a98ebd5f.png

The same formula in spherical coordinates:

.. image:: https://user-images.githubusercontent.com/284644/79490196-ee6d8b80-8035-11ea-874a-1d126b5c46b1.png

Using the Field input with V:

.. image:: https://user-images.githubusercontent.com/284644/137736317-e1296d38-6e9a-412f-8bbf-531998dae0f8.png
