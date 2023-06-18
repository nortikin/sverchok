Surface Formula
===============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/36abea60-6920-4850-9ca9-8ee9a4592e7a
  :target: https://github.com/nortikin/sverchok/assets/14288520/36abea60-6920-4850-9ca9-8ee9a4592e7a

Functionality
-------------

This node generates a Surface, defined by some user-provided formula.

The formula should map the curve's U and V parameters into one of supported 3D coordinate systems: (X, Y, Z), (Rho, Phi, Z) or (Rho, Phi, Theta).

It is possible to use additional parameters in the formula, they will become inputs of the node.

Surface domain / parametrization specifics: defined by node settings.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d666e5e8-624a-411b-981d-7cd3ef81ed43
  :target: https://github.com/nortikin/sverchok/assets/14288520/d666e5e8-624a-411b-981d-7cd3ef81ed43

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

This node has the following inputs:

* **UMin**, **UMax**. Minimum and maximum values of the surface's U parameter.
* **VMin**, **VMax**. Minimum and maximum values of the surface's V parameter.

Each variable used in formulas, except for `u` and `v`, also becomes an additional input.

Parameters
----------

This node has the following parameters:

* **Formula 1**, **Formula 2**, **Formula 3**. Formulas for 3 components
  defining surface points in the used coordinate system. Default values define
  a torodial surface.
* **Output**. This defined the coordinate system being used, and thus it
  defines the exact meaning of formula parameters. The available modes are:

   * **Cartesian**. Three formulas will define correspondingly X, Y and Z coordinates.
   * **Cylindrical**. Three formulas will define correspondingly Rho, Phi and Z coordinates.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/993aed22-60d9-404f-b757-107dfdd94ed3
      :target: https://github.com/nortikin/sverchok/assets/14288520/993aed22-60d9-404f-b757-107dfdd94ed3

   * **Spherical**. Three formulas will define correspondingly Rho, Phi and Theta coordinates.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/9fe5db6f-6909-4235-bce8-418aaee8c5c8
      :target: https://github.com/nortikin/sverchok/assets/14288520/9fe5db6f-6909-4235-bce8-418aaee8c5c8

   The default mode is **Cartesian**.

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

* **Surface**. The generated surface.

Examples of usage
-----------------

The default parameters - a torus:

.. image:: https://user-images.githubusercontent.com/284644/79387280-d558d200-7f84-11ea-9a28-68b5299ce8ec.png
  :target: https://user-images.githubusercontent.com/284644/79387280-d558d200-7f84-11ea-9a28-68b5299ce8ec.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`

An example of cylindrical coordinates usage:

.. image:: https://user-images.githubusercontent.com/284644/79387284-d689ff00-7f84-11ea-922f-bf28efcd7e53.png
  :target: https://user-images.githubusercontent.com/284644/79387284-d689ff00-7f84-11ea-922f-bf28efcd7e53.png

* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`

An example with parameters:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f71d05b9-35c4-47b6-83c6-623c4d52eb31
  :target: https://github.com/nortikin/sverchok/assets/14288520/f71d05b9-35c4-47b6-83c6-623c4d52eb31

* Number-> :doc:`List Input </nodes/number/list_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
