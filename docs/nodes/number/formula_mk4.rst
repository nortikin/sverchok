Formula Node Mk4
================

Functionality
-------------
Formula+ (this is very similar to mk3 with a few notable exceptions)

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
- Python type conversions: tuple, list, dict.

This restriction is for security reasons. However, Python's ecosystem does not guarantee that noone can call some unsafe operations by using some sort of language-level hacks. So, please be warned that usage of this node with JSON definition obtained from unknown or untrusted source can potentially harm your system or data.

Examples of valid expressions are:

* 1.0
* x
* x+1
* 0.75*X + 0.25*Y
* R * sin(phi)
* f-string formatting is possible. like:
   -  ``f"{x:04}"`` will return a zero padding of length 4 if positive numbers are passed in.


Inputs
------

- Set of inputs for this node depends on used formulas. Each variable used in formula becomes one input. If there are no variables used in formula, then this node will have no inputs.
- If you specify variables, and the node creates a socket for it, then you must connect a link into that socket, otherwise the node will return early and not process anything. (but it might still output from the previously cached result.
    - the node will warn you using a message to say that the UI is not fully connected.
    |ui_message|

Parameters
----------

This node has the following parameters:

- **Dimensions**. This parameter is available in the N panel only. It defines how many formulas the node will allow to specify and evaluate. Default value is 1. Maximum value is 4.
- **Formula 1** to **Formula 4** input boxes. Formulas theirselve. If no formula is specified, then nothing will be calculated for this dimension. Number of formula input boxes is defined by **Dimensions** parameter.
- **Split**. If the flag is set, then for each combination of input values, list of values calculated by formula is enclosed in separate list. Usually you will want to uncheck this if you are using only one formula. Usually you will want to check this if you are using more than one formula. Other combinations can be of use in specific cases. Unchecked by default.
- **Wrapping**. 
   -  ``-1``: removes an outer layer of square brackets
   -  ``.0``: does nothing to the output
   -  ``+1``: will wrap the output one more time.

For example, let's consider the following setup:

.. image:: https://user-images.githubusercontent.com/284644/53962080-00c78700-410c-11e9-9563-855fca16537a.png

Then the following combinations of flags are possible:


Outputs
-------

**Result** - what we got as result.  

Usage examples
--------------

see previous versions of formula node