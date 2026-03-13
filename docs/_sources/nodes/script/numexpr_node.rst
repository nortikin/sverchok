Num Expression
==============

Functionality
-------------

This node is currently fastest way to evaluate an expression. For best
performance the node should get NumPy arrays. But vectorization is slow as
it is for any other node in Sverchok, so make sure that you have all numbers in
a single object if performance is important.

The node is based on `NumExpr library`_. It supports next operators:

    * Bitwise operators (and, or, not, xor): :code:`&, |, ~, ^`
    * Comparison operators: :code:`<, <=, ==, !=, >=, >`
    * Unary arithmetic operators: :code:`-`
    * Binary arithmetic operators: :code:`+, -, *, /, **, %, <<, >>`

Supported functions:

    * :code:`where(bool, number1, number2): number` -- number1 if the bool condition
      is true, number2 otherwise.
    * :code:`{sin,cos,tan}(float|complex): float|complex` -- trigonometric sine,
      cosine or tangent.
    * :code:`{arcsin,arccos,arctan}(float|complex): float|complex` -- trigonometric
      inverse sine, cosine or tangent.
    * :code:`arctan2(float1, float2): float` -- trigonometric inverse tangent of
      float1/float2.
    * :code:`{sinh,cosh,tanh}(float|complex): float|complex` -- hyperbolic sine,
      cosine or tangent.
    * :code:`{arcsinh,arccosh,arctanh}(float|complex): float|complex` -- hyperbolic
      inverse sine, cosine or tangent.
    * :code:`{log,log10,log1p}(float|complex): float|complex` -- natural, base-10 and
      log(1+x) logarithms.
    * :code:`{exp,expm1}(float|complex): float|complex` -- exponential and exponential
      minus one.
    * :code:`sqrt(float|complex): float|complex` -- square root.
    * :code:`abs(float|complex): float|complex`  -- absolute value.
    * :code:`conj(complex): complex` -- conjugate value.
    * :code:`{real,imag}(complex): float` -- real or imaginary part of complex.
    * :code:`complex(float, float): complex` -- complex from real and imaginary
      parts.
    * :code:`contains(np.str, np.str): bool` -- returns True for every string in :code:`op1` that
      contains :code:`op2`.
    * :code:`{floor}(float): float` -- returns the greatest integer less than or
      equal to x.
    * :code:`{ceil}(float): float` -- returns the least integer greater than or
      equal to x

Reduction functions:

  * :code:`sum(number, axis=None)`: Sum of array elements over a given axis.
    Negative axis are not supported.
  * :code:`prod(number, axis=None)`: Product of array elements over a given axis.
    Negative axis are not supported.
  * :code:`{min,max}(number, axis=None)`: Find minimum/maximum value over a given axis.
    Negative axis are not supported.

*Note:* because of internal limitations, reduction operations must appear the
last in the stack.  If not, it will be issued an error like::

    >>> ne.evaluate('sum(1)*(-1)')
    RuntimeError: invalid program: reduction operations must occur last

The node automatically generates sockets for each variable in an input formula.
The type of sockets can be either float/int or vector. The type of generated
socket is dependent on the name of the variable. To generate vector type the
variable should statr with upper ``V`` letter. Any other variable names will
generate float/int type. The order of sockets is dependent on variable names.
They are sorted in alphabetical order. The output type is vector if there is
at least one input vector type. Variable names should be Pythonic.

.. _NumExpr library: https://numexpr.readthedocs.io/projects/NumExpr3/en/latest/user_guide.html

Inputs
------

Variable number of inputs depending on the input formula.

Outputs
-------

- Result

Examples
--------

.. figure:: https://user-images.githubusercontent.com/28003269/210037965-560e2d6b-3563-4efc-9be3-da35bdf3b049.png
   :target: https://user-images.githubusercontent.com/28003269/210037965-560e2d6b-3563-4efc-9be3-da35bdf3b049.png

   Round a value according to given step.
