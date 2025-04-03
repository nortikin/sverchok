Curve Formula
=============

.. image:: https://user-images.githubusercontent.com/14288520/205702554-dd853e84-851a-437a-bb2c-7ceb56d234e6.png
  :target: https://user-images.githubusercontent.com/14288520/205702554-dd853e84-851a-437a-bb2c-7ceb56d234e6.png

Functionality
-------------

This node generates a curve, defined by some user-provided formula.

The formula should map the curve's T parameters into one of supported 3D coordinate systems: (X, Y, Z), (Rho, Phi, Z) or (Rho, Phi, Theta).

It is possible to use additional parameters in the formula, they will become inputs of the node.

Curve domain / parametrization specifics: defined by node settings.

.. image:: https://user-images.githubusercontent.com/14288520/205707613-de8d5100-d872-450a-a999-92c678021aca.png
  :target: https://user-images.githubusercontent.com/14288520/205707613-de8d5100-d872-450a-a999-92c678021aca.png

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

* **TMin**. Minimum value of the curve's T parameter (corresponding to the beginning of the curve). The default value is 0.0.
* **TMax**. Maximum value of the curve's T parameter (corresponding to the end of the curve). The default value is 2*pi.

.. image:: https://user-images.githubusercontent.com/14288520/205713440-6b3c6170-bfe0-44b9-8268-83eec5a69325.png
  :target: https://user-images.githubusercontent.com/14288520/205713440-6b3c6170-bfe0-44b9-8268-83eec5a69325.png

Parameters
----------

This node has the following parameters:

* **Formula 1**, **Formula 2**, **Formula 3**. Formulas for 3 components
  defining curve points in the used coordinate system. Default values define
  simple helix curve in the cartesian coordinates. Each variable used in formulas,
  except for `t`, also becomes an additional input. Example variable 'c':

.. image:: https://user-images.githubusercontent.com/14288520/205709029-bdc14a67-c9e4-4021-81c2-ecb613dbfb34.png
  :target: https://user-images.githubusercontent.com/14288520/205709029-bdc14a67-c9e4-4021-81c2-ecb613dbfb34.png

.. image:: https://user-images.githubusercontent.com/14288520/205708728-bcad3139-1681-4b7b-b396-e563e88ce442.gif
  :target: https://user-images.githubusercontent.com/14288520/205708728-bcad3139-1681-4b7b-b396-e563e88ce442.gif

Number-> :doc:`Number Range </nodes/number/number_range>`

* **Output**. This defined the coordinate system being used, and thus it
  defines the exact meaning of formula parameters. The available modes are:

   * **Cartesian**. Three formulas will define correspondingly X, Y and Z coordinates.
   * **Cylindrical**. Three formulas will define correspondingly Rho, Phi and Z coordinates.
   * **Spherical**. Three formulas will define correspondingly Rho, Phi and Theta coordinates.

   The default mode is **Cartesian**.

* **Vectorize**. This parameter is available in the N panel only. If enabled,
  then to evaluate formulas for a series of input values, the node will use
  NumPy functions to perform several computations at a time; otherwise, the
  formulas will be evaluated separately for each input value. The use of
  vectorization usually makes computations a lot faster (2x to 100x). The
  parameter is enabled by default. If you experience some kind of troubles with
  calculating some of functions (errors or not good enough precision), you can
  disable this parameter.

.. image:: https://user-images.githubusercontent.com/14288520/205857380-728f7515-bdaa-477e-a70c-72c2d5eae51d.png
  :target: https://user-images.githubusercontent.com/14288520/205857380-728f7515-bdaa-477e-a70c-72c2d5eae51d.png

.. image:: https://user-images.githubusercontent.com/14288520/205712865-a3274f3b-b488-4686-bec3-0c425991e936.gif
  :target: https://user-images.githubusercontent.com/14288520/205712865-a3274f3b-b488-4686-bec3-0c425991e936.gif

Outputs
-------

This node has the following output:

* **Curve**. The generated curve.

Examples of usage
-----------------

The default example - a helix:

.. image:: https://user-images.githubusercontent.com/14288520/205733677-585957c5-51f2-41b9-b635-3396797e5659.png
  :target: https://user-images.githubusercontent.com/14288520/205733677-585957c5-51f2-41b9-b635-3396797e5659.png

* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Another example - Viviani's curve (an intersection of a sphere with a cylinder):

.. image:: https://user-images.githubusercontent.com/14288520/205734503-8a818e6f-b60c-43d4-a860-4db6c7e78cda.png
  :target: https://user-images.githubusercontent.com/14288520/205734503-8a818e6f-b60c-43d4-a860-4db6c7e78cda.png

* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

A spiral in spherical coordinates:

.. image:: https://user-images.githubusercontent.com/14288520/205735619-5edb0b81-d2a0-490e-b4de-e5692b87f0d5.png
  :target: https://user-images.githubusercontent.com/14288520/205735619-5edb0b81-d2a0-490e-b4de-e5692b87f0d5.png

* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
