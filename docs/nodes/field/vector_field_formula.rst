Vector Field Formula
====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c1363f46-6308-4af9-bbf9-78dd8e9d0e24
  :target: https://github.com/nortikin/sverchok/assets/14288520/c1363f46-6308-4af9-bbf9-78dd8e9d0e24

Functionality
-------------

This node generates a Vector Field, defined by some user-provided formula.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c730fd5c-3dbc-4924-a2e0-afab3d433dfd
  :target: https://github.com/nortikin/sverchok/assets/14288520/c730fd5c-3dbc-4924-a2e0-afab3d433dfd

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Fields-> :doc:`Evaluate Vector Field </nodes/field/vector_field_eval>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

The formula should map the coordinates of the point in 3D space into some vector in 3D space. Both original points and the resulting vector can be expressed in one of supported coordinate systems.

It is possible to use additional parameters in the formula, they will become inputs of the node.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ec94eedb-297a-47df-b6ab-44b7e64674c0
  :target: https://github.com/nortikin/sverchok/assets/14288520/ec94eedb-297a-47df-b6ab-44b7e64674c0

It is also possible to use the value of some other Vector Field in the same point in the formula.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b985b80c-969a-4ad2-b8b1-cf4250b22f37
  :target: https://github.com/nortikin/sverchok/assets/14288520/b985b80c-969a-4ad2-b8b1-cf4250b22f37

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

* **Field**. A vector field, whose values can be used in the formula. This
  input is required only if the formula involves the **V** variable.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/60d44880-034b-4930-bc6b-9c2f597aa6b7
      :target: https://github.com/nortikin/sverchok/assets/14288520/60d44880-034b-4930-bc6b-9c2f597aa6b7

Each variable used in the formula, except for `V` and the coordinate variables,
also becomes additional input.

The following variables are considered to be point coordinates:

* For Cartesian input mode: `x`, `y` and `z`;

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/e11482bd-17b8-492a-ac78-bc8487be779f
      :target: https://github.com/nortikin/sverchok/assets/14288520/e11482bd-17b8-492a-ac78-bc8487be779f
    
    * Generator->Generatots Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`

* For Cylindrical input mode: `rho`, `phi` and `z`;

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/ac2b5633-138a-4832-b477-d069bd7d580f
      :target: https://github.com/nortikin/sverchok/assets/14288520/ac2b5633-138a-4832-b477-d069bd7d580f

    * Generator->Generatots Extended-> :doc:`Spiral </nodes/generators_extended/spiral_mk2>`

* For Spherical input mode: `rho`, `phi` and `theta`.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/fd3bdcd0-c0b5-4808-b9b3-ce165b600124
      :target: https://github.com/nortikin/sverchok/assets/14288520/fd3bdcd0-c0b5-4808-b9b3-ce165b600124

    * Generator->Generators Extended :doc:`Torus Knot </nodes/generators_extended/torus_knot_mk2>`

`V` variable in formulas stands for NumPy array of shape ``(3,)``, which
represents the value of field passed in the **Field** input, in the appropriate
point in space. So, `V[0]` is X coordinate of that field's value, `V[1]` is
it's Y coordinate, and `V[2]` is Z coordinate.

Parameters
----------

This node has the following parameters:

* **Input**. This defines the coordinate system being used for the input
  points. The available values are **Carhtesian**, **Cylindrical** and
  **Spherical**. The default value is **Cartesian**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/351ed6d0-1bbc-4527-a581-3e57a1e4214e
      :target: https://github.com/nortikin/sverchok/assets/14288520/351ed6d0-1bbc-4527-a581-3e57a1e4214e

* **Formula1**, **Formula2**, **Formula3**. Three formulas defining the
  respective coordinate / components of the resulting vectors: X, Y, Z, or Rho,
  Phi, Z, or Rho, Phi, Theta, depending on the **Output** parameter. The
  default formulas are `-y`, `x` and `z`, which defines the field which rotates
  the whole space 90 degrees around the Z axis.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/66ab7f3a-619a-465b-967e-2c9175c6d216
      :target: https://github.com/nortikin/sverchok/assets/14288520/66ab7f3a-619a-465b-967e-2c9175c6d216

    * Fields-> :doc:`Vector Field Math </nodes/field/vector_field_math>`
    * Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`

* **Output**. This defines the coordinate system in which the resulting vectors
  are expressed. The available values are **Carhtesian**, **Cylindrical** and
  **Spherical**. The default value is **Cartesian**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/1ece7076-a9b2-4502-b860-087f23c61e00
      :target: https://github.com/nortikin/sverchok/assets/14288520/1ece7076-a9b2-4502-b860-087f23c61e00

* **Vectorize**. This parameter is available in the N panel only. If enabled,
  then to evaluate formulas for a series of input values, the node will use
  NumPy functions to perform several computations at a time; otherwise, the
  formulas will be evaluated separately for each input value. The use of
  vectorization usually makes computations a lot faster (2x to 100x). The
  parameter is enabled by default. If you experience some kind of troubles with
  calculating some of functions (errors or not good enough precision), you can
  disable this parameter.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/3e4476c5-5319-48ab-bb77-21bdbba6c271
      :target: https://github.com/nortikin/sverchok/assets/14288520/3e4476c5-5319-48ab-bb77-21bdbba6c271

Outputs
-------

This node has the following output:

* **Field**. The generated vector field.

Examples of usage
-----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/3270c50d-098c-45bb-891a-caa183aeb927
  :target: https://github.com/nortikin/sverchok/assets/14288520/3270c50d-098c-45bb-891a-caa183aeb927

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Fields-> :doc:`Vector Field Math </nodes/field/vector_field_math>`
* Fields-> :doc:`Evaluate Vector Field </nodes/field/vector_field_eval>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Some vector field defined by a formula in Spherical coordinates:

.. image:: https://user-images.githubusercontent.com/284644/79491540-0a722c80-8038-11ea-914f-0221e5e75f68.png
  :target: https://user-images.githubusercontent.com/284644/79491540-0a722c80-8038-11ea-914f-0221e5e75f68.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Similar field applied to some box:

.. image:: https://user-images.githubusercontent.com/284644/79491547-0ba35980-8038-11ea-89fc-063982ea65cd.png
  :target: https://user-images.githubusercontent.com/284644/79491547-0ba35980-8038-11ea-89fc-063982ea65cd.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Example of V variable usage:

.. image:: https://user-images.githubusercontent.com/284644/137764029-bf397e56-5558-48bd-97a9-f8031d72a1c0.png
  :target: https://user-images.githubusercontent.com/284644/137764029-bf397e56-5558-48bd-97a9-f8031d72a1c0.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`