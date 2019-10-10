Formula Node Mk3
================

Functionality
-------------

This node allows one to evaluate (almost) arbitrary Python expressions, using inputs as variables.
It is possible to calculate numeric values, construct lists, tuples, vertices and matrices.

The node allows to evaluate up to 4 formulas for each set of input values.

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
- Python type conversions: tuple, list.

This restriction is for security reasons. However, Python's ecosystem does not guarantee that noone can call some unsafe operations by using some sort of language-level hacks. So, please be warned that usage of this node with JSON definition obtained from unknown or untrusted source can potentially harm your system or data.

Examples of valid expressions are:

* 1.0
* x
* x+1
* 0.75*X + 0.25*Y
* R * sin(phi)

Inputs
------

Set of inputs for this node depends on used formulas. Each variable used in formula becomes one input. If there are no variables used in formula, then this node will have no inputs.

Parameters
----------

This node has the following parameters:

- **Dimensions**. This parameter is available in the N panel only. It defines how many formulas the node will allow to specify and evaluate. Default value is 1. Maximum value is 4.
- **Formula 1** to **Formula 4** input boxes. Formulas theirselve. If no formula is specified, then nothing will be calculated for this dimension. Number of formula input boxes is defined by **Dimensions** parameter.
- **Separate**. If the flag is set, then for each combination of input values, list of values calculated by formula is enclosed in separate list. Usually you will want to uncheck this if you are using only one formula. Usually you will want to check this if you are using more than one formula. Other combinations can be of use in specific cases. Unchecked by default.
- **Wrap**. If checked, then the whole output of the node will be enclosed in additional brackets. Checked by default.

For example, let's consider the following setup:

.. image:: https://user-images.githubusercontent.com/284644/53962080-00c78700-410c-11e9-9563-855fca16537a.png

Then the following combinations of flags are possible:

+-----------+-----------+--------------------+
| Separate  | Wrap      | Result             |
+===========+===========+====================+
| Checked   | Checked   | [[[1, 3], [2, 4]]] |
+-----------+-----------+--------------------+
| Checked   | Unchecked | [[1, 3], [2, 4]]   |
+-----------+-----------+--------------------+
| Unchecked | Checked   | [[1, 3, 2, 4]]     |
+-----------+-----------+--------------------+
| Unchecked | Unchecked | [1, 3, 2, 4]       |
+-----------+-----------+--------------------+

Outputs
-------

**Result** - what we got as result.  

Usage examples
--------------

.. image:: https://user-images.githubusercontent.com/284644/53965898-dbd71200-4113-11e9-83c7-cb3c7ced8c1e.png

.. image:: https://user-images.githubusercontent.com/284644/53967764-9f0d1a00-4117-11e9-92e3-a047dbd2981b.png

